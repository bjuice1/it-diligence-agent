"""
Base Discovery Agent for V2 Architecture

Discovery agents extract facts from documents into the FactStore.
They use the cheaper/faster Haiku model since extraction is simpler than reasoning.

Key Responsibilities:
- Extract structured facts with evidence
- Flag gaps where information is missing
- NO analysis or conclusions - just document what exists
"""

import anthropic
from typing import Dict, List, Optional, Any
from abc import ABC, abstractmethod
import json
import logging
from time import time
from dataclasses import dataclass

from stores.fact_store import FactStore
from tools_v2.discovery_tools import DISCOVERY_TOOLS, execute_discovery_tool
from tools_v2.discovery_logger import DiscoveryLogger
from tools_v2.deterministic_parser import preprocess_document as deterministic_preprocess

# Import cost estimation, rate limiter, circuit breaker, and temperature
try:
    from config_v2 import (
        estimate_cost,
        API_RATE_LIMIT_SEMAPHORE_SIZE,
        API_RATE_LIMIT_PER_MINUTE,
        DISCOVERY_TEMPERATURE
    )
    from tools_v2.rate_limiter import APIRateLimiter
    from tools_v2.circuit_breaker import CircuitBreaker, CircuitBreakerConfig, CircuitBreakerOpenError
except ImportError:
    def estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
        return 0.0
    API_RATE_LIMIT_SEMAPHORE_SIZE = 3
    API_RATE_LIMIT_PER_MINUTE = 40
    DISCOVERY_TEMPERATURE = 0.0  # Default to deterministic
    APIRateLimiter = None
    CircuitBreaker = None
    CircuitBreakerConfig = None
    CircuitBreakerOpenError = Exception


@dataclass
class DiscoveryMetrics:
    """Track discovery agent execution metrics"""
    api_calls: int = 0
    tool_calls: int = 0
    tokens_used: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    execution_time: float = 0.0
    iterations: int = 0
    facts_extracted: int = 0
    gaps_flagged: int = 0
    errors: int = 0
    estimated_cost: float = 0.0  # Running cost estimate in USD


class BaseDiscoveryAgent(ABC):
    """
    Base class for discovery agents in the V2 architecture.

    Discovery agents:
    1. Receive document text to analyze
    2. Extract structured facts with evidence
    3. Flag gaps where information is missing
    4. Store everything in the FactStore

    They do NOT:
    - Analyze or interpret findings
    - Draw conclusions
    - Make recommendations

    Uses Haiku model for cost efficiency (extraction is simpler than reasoning).
    """

    def __init__(
        self,
        fact_store: FactStore,
        api_key: str,
        model: str = None,
        max_tokens: int = None,
        max_iterations: int = None,
        target_name: Optional[str] = None,
        inventory_store: Optional[Any] = None,
    ):
        if not api_key:
            raise ValueError("API key must be provided")

        # Import config values - use them as defaults if not explicitly provided
        try:
            from config_v2 import (
                DISCOVERY_MODEL,
                DISCOVERY_MAX_TOKENS,
                DISCOVERY_MAX_ITERATIONS
            )
            model = model or DISCOVERY_MODEL
            max_tokens = max_tokens or DISCOVERY_MAX_TOKENS
            max_iterations = max_iterations or DISCOVERY_MAX_ITERATIONS
        except ImportError:
            # Fallback defaults if config not available
            model = model or "claude-3-5-haiku-20241022"
            max_tokens = max_tokens or 4096
            max_iterations = max_iterations or 30

        self.client = anthropic.Anthropic(api_key=api_key)
        self.fact_store = fact_store
        self.tools = DISCOVERY_TOOLS
        self.model = model
        self.max_tokens = max_tokens
        self.max_iterations = max_iterations
        self.target_name = target_name  # Name of the target company being analyzed
        self.inventory_store = inventory_store  # Optional InventoryStore for bidirectional linking (Spec 03)

        # State
        self.messages: List[Dict] = []
        self.discovery_complete: bool = False
        self.current_document_name: str = ""  # Track source document for fact traceability
        self.current_entity: str = "target"   # "target" or "buyer" - enforced on all fact creation
        self.current_analysis_phase: str = "target_extraction"  # "target_extraction" or "buyer_extraction"

        # Metrics
        self.metrics = DiscoveryMetrics()
        self.start_time: Optional[float] = None

        # Logging
        self.logger = logging.getLogger(f"discovery.{self.domain}")

        # Audit logger for .md trail
        try:
            from config_v2 import OUTPUT_DIR
            log_dir = OUTPUT_DIR / "logs"
        except ImportError:
            log_dir = None
        self.audit_logger = DiscoveryLogger(domain=self.domain, output_dir=log_dir)

        # Rate limiting
        if APIRateLimiter:
            self.rate_limiter = APIRateLimiter.get_instance(
                max_concurrent=API_RATE_LIMIT_SEMAPHORE_SIZE,
                requests_per_minute=API_RATE_LIMIT_PER_MINUTE
            )
        else:
            self.rate_limiter = None
        
        # Circuit breaker for API failures (can be disabled in config)
        try:
            from config_v2 import (
                CIRCUIT_BREAKER_ENABLED,
                CIRCUIT_BREAKER_FAILURE_THRESHOLD,
                CIRCUIT_BREAKER_TIMEOUT
            )
            if CircuitBreaker and CIRCUIT_BREAKER_ENABLED:
                self.circuit_breaker = CircuitBreaker(
                    config=CircuitBreakerConfig(
                        failure_threshold=CIRCUIT_BREAKER_FAILURE_THRESHOLD,
                        timeout=CIRCUIT_BREAKER_TIMEOUT,
                        expected_exception=anthropic.APIError
                    )
                )
            else:
                self.circuit_breaker = None
        except ImportError:
            self.circuit_breaker = None

    @property
    @abstractmethod
    def domain(self) -> str:
        """Return the domain name (infrastructure, network, etc.)"""
        pass

    @property
    @abstractmethod
    def system_prompt(self) -> str:
        """Return the discovery prompt for this domain"""
        pass

    @property
    def inventory_categories(self) -> List[str]:
        """Return the categories this domain should extract. Override in subclass."""
        return []

    def discover(
        self,
        document_text: str,
        document_name: str = "",
        entity: str = "target",
        analysis_phase: str = "target_extraction"
    ) -> Dict[str, Any]:
        """
        Run discovery on the provided document.

        Args:
            document_text: Text extracted from IT documents
            document_name: Filename of source document for fact traceability
            entity: "target" or "buyer" - enforced on all extracted facts
            analysis_phase: "target_extraction" or "buyer_extraction"

        Returns:
            Dict with discovery results including:
            - facts: List of extracted facts
            - gaps: List of identified gaps
            - metrics: Execution metrics
        """
        self.start_time = time()
        self.current_document_name = document_name  # Store for injection into tool calls
        self.current_entity = entity  # Store for enforcing entity on all facts
        self.current_analysis_phase = analysis_phase
        self.logger.info(f"Starting {self.domain.upper()} discovery from: {document_name or 'unknown'}")
        print(f"\n{'='*60}")
        print(f"Discovery: {self.domain.upper()}")
        print(f"{'='*60}")

        # Start audit logging
        self.audit_logger.start(
            document_name=document_name or "unknown",
            document_length=len(document_text)
        )

        # =================================================================
        # DETERMINISTIC PREPROCESSING - Extract tables WITHOUT LLM
        # =================================================================
        try:
            preprocess_result = deterministic_preprocess(
                document_text=document_text,
                fact_store=self.fact_store,
                entity=entity,
                source_document=document_name,
                inventory_store=self.inventory_store,
            )
            if preprocess_result.facts_created > 0:
                print(f"[DETERMINISTIC] Extracted {preprocess_result.facts_created} facts from tables")
                self.logger.info(f"Deterministic preprocessing: {preprocess_result.facts_created} facts from tables")

                # MONITORING: Track InventoryStore population for deduplication verification
                if self.inventory_store:
                    inv_count = len(self.inventory_store)
                    print(f"[INVENTORY] InventoryStore has {inv_count} items after parsing (entity={entity})")
                    self.logger.info(f"[INVENTORY] InventoryStore now has {inv_count} items after deterministic parse (entity={entity})")
                else:
                    print(f"[INVENTORY] WARNING: No InventoryStore attached - items not being deduplicated!")
                    self.logger.warning(f"[INVENTORY] No InventoryStore attached - items not being deduplicated")

            # Use remaining prose for LLM (tables already handled)
            remaining_text = preprocess_result.remaining_text or document_text
        except Exception as e:
            self.logger.warning(f"Deterministic preprocessing failed, using full text: {e}")
            remaining_text = document_text
        # =================================================================

        try:
            # Build initial user message (with remaining prose after table extraction)
            user_message = self._build_user_message(remaining_text)
            self.messages = [{"role": "user", "content": user_message}]

            # Discovery loop
            iteration = 0
            while not self.discovery_complete and iteration < self.max_iterations:
                iteration += 1
                self.metrics.iterations = iteration
                self.audit_logger.set_iteration(iteration)
                print(f"\n--- Iteration {iteration} ---")

                try:
                    # Call model
                    response = self._call_model()

                    # Process response
                    self._process_response(response)

                    if self.discovery_complete:
                        print(f"\n[OK] {self.domain.upper()} discovery complete after {iteration} iterations")
                        break

                except Exception as e:
                    self.metrics.errors += 1
                    self.logger.error(f"Error in iteration {iteration}: {e}", exc_info=True)
                    if iteration >= self.max_iterations:
                        raise

            if not self.discovery_complete:
                print(f"\n[WARN] Max iterations ({self.max_iterations}) reached")
                self.logger.warning("Max iterations reached without completion")

            # Calculate execution time
            if self.start_time:
                self.metrics.execution_time = time() - self.start_time

            # Get domain facts
            domain_facts = self.fact_store.get_domain_facts(self.domain)

            # Update metrics
            self.metrics.facts_extracted = domain_facts["fact_count"]
            self.metrics.gaps_flagged = domain_facts["gap_count"]

            print("\nDiscovery Results:")
            print(f"  Facts extracted: {self.metrics.facts_extracted}")
            print(f"  Gaps identified: {self.metrics.gaps_flagged}")
            print(f"  API calls: {self.metrics.api_calls}")
            print(f"  Tokens: {self.metrics.input_tokens} in, {self.metrics.output_tokens} out")
            print(f"  Estimated cost: ${self.metrics.estimated_cost:.4f}")
            print(f"  Time: {self.metrics.execution_time:.1f}s")

            # Finalize and save audit log
            self.audit_logger.finish(metrics=self.metrics)
            log_path = self.audit_logger.save()
            if log_path:
                print(f"  Audit log: {log_path}")

            return {
                "domain": self.domain,
                "facts": domain_facts["facts"],
                "gaps": domain_facts["gaps"],
                "categories": domain_facts["categories"],
                "metrics": {
                    "api_calls": self.metrics.api_calls,
                    "tool_calls": self.metrics.tool_calls,
                    "tokens_used": self.metrics.tokens_used,
                    "execution_time": self.metrics.execution_time,
                    "iterations": self.metrics.iterations,
                    "estimated_cost": self.metrics.estimated_cost
                }
            }

        except Exception as e:
            self.logger.error(f"Discovery failed: {e}", exc_info=True)
            raise

    def _build_user_message(self, document_text: str) -> str:
        """Build the user message with document content"""
        parts = []

        # Add phase-specific entity focus instructions
        parts.append("## CRITICAL: ENTITY FOCUS INSTRUCTIONS")
        parts.append("")

        if self.current_entity == "target":
            # Phase 1: Target extraction
            parts.append("You are analyzing **TARGET COMPANY** documents.")
            parts.append("All content below is from the TARGET company (the company being acquired).")
            parts.append("")
            parts.append("**IMPORTANT:** Every fact you extract MUST be about the TARGET company.")
            parts.append("Use `entity: 'target'` for all inventory entries.")
            if self.target_name:
                parts.append(f"**TARGET COMPANY NAME: {self.target_name}**")
        else:
            # Phase 2: Buyer extraction
            parts.append("You are analyzing **BUYER COMPANY** documents.")
            parts.append("All content below is from the BUYER company (the acquirer).")
            parts.append("")
            parts.append("**IMPORTANT:** Every fact you extract MUST be about the BUYER company.")
            parts.append("Use `entity: 'buyer'` for all inventory entries.")
            parts.append("")
            parts.append("If you see a section marked 'TARGET COMPANY FACTS (READ-ONLY REFERENCE)',")
            parts.append("that is context about what the TARGET has - do NOT extract facts from it.")
            parts.append("Only extract facts from the BUYER documents below that section.")
            if self.target_name:
                parts.append(f"**BUYER COMPANY NAME: {self.target_name}**")  # target_name is reused for buyer in Phase 2
        parts.append("")

        # Document content
        parts.append("## Document to Analyze")
        parts.append("")
        parts.append(document_text)
        parts.append("")

        # Task instructions - phase-specific
        parts.append("## Your Task")
        parts.append(f"Extract all {self.domain} information from the document above.")
        entity_label = "TARGET" if self.current_entity == "target" else "BUYER"
        parts.append(f"**Remember:** You are extracting {entity_label} company facts. Use `entity: '{self.current_entity}'` in each entry.")
        parts.append("Use create_inventory_entry for each fact you find.")
        parts.append("Use flag_gap for each expected item that is missing.")
        parts.append(f"Call complete_discovery when you have processed all {self.domain} categories.")

        if self.inventory_categories:
            parts.append("")
            parts.append(f"Required categories: {', '.join(self.inventory_categories)}")

        return "\n".join(parts)

    def _call_model(self) -> anthropic.types.Message:
        """Make API call to Claude with timeout and retry logic"""
        from config_v2 import API_MAX_RETRIES, API_TIMEOUT_SECONDS, API_RETRY_BACKOFF_BASE, API_RATE_LIMITER_TIMEOUT

        # Import model caps and clamp max_tokens to model limit
        try:
            from config_v2 import MODEL_OUTPUT_CAPS
            model_cap = MODEL_OUTPUT_CAPS.get(self.model, 8192)  # Default to 8192 if unknown
            effective_max_tokens = min(self.max_tokens, model_cap)
            if effective_max_tokens != self.max_tokens:
                self.logger.warning(f"Clamped max_tokens from {self.max_tokens} to {effective_max_tokens} (model limit)")
        except ImportError:
            effective_max_tokens = min(self.max_tokens, 8192)  # Safe default

        self.metrics.api_calls += 1
        max_retries = API_MAX_RETRIES
        timeout_seconds = API_TIMEOUT_SECONDS

        for attempt in range(max_retries):
            try:
                # Check circuit breaker
                if self.circuit_breaker and self.circuit_breaker.stats.state.value == "open":
                    raise CircuitBreakerOpenError(
                        "Circuit breaker is OPEN - API is consistently failing. "
                        "Please check API status or wait before retrying."
                    )
                
                # Acquire rate limiter before making API call
                if self.rate_limiter:
                    if not self.rate_limiter.acquire(timeout=API_RATE_LIMITER_TIMEOUT):
                        raise TimeoutError("Rate limiter timeout: could not acquire API call slot")
                
                try:
                    # Use circuit breaker to protect API call
                    # CRITICAL: temperature=0 for deterministic, consistent extraction
                    # Use prompt caching to reduce token costs on repeated iterations
                    cached_system = [{
                        "type": "text",
                        "text": self.system_prompt,
                        "cache_control": {"type": "ephemeral"}
                    }]
                    if self.circuit_breaker:
                        response = self.circuit_breaker.call(
                            self.client.messages.create,
                            model=self.model,
                            max_tokens=effective_max_tokens,  # Use clamped value
                            temperature=DISCOVERY_TEMPERATURE,  # Deterministic extraction
                            system=cached_system,
                            tools=self.tools,
                            messages=self.messages,
                            timeout=timeout_seconds
                        )
                    else:
                        response = self.client.messages.create(
                            model=self.model,
                            max_tokens=effective_max_tokens,  # Use clamped value
                            temperature=DISCOVERY_TEMPERATURE,  # Deterministic extraction
                            system=cached_system,
                            tools=self.tools,
                            messages=self.messages,
                            timeout=timeout_seconds
                        )
                finally:
                    # Always release rate limiter
                    if self.rate_limiter:
                        self.rate_limiter.release()

                # Track token usage and cost
                if hasattr(response, 'usage'):
                    self.metrics.input_tokens += response.usage.input_tokens
                    self.metrics.output_tokens += response.usage.output_tokens
                    self.metrics.tokens_used = self.metrics.input_tokens + self.metrics.output_tokens

                    # Log cache statistics if available (prompt caching)
                    cache_created = getattr(response.usage, 'cache_creation_input_tokens', 0)
                    cache_read = getattr(response.usage, 'cache_read_input_tokens', 0)
                    if cache_created or cache_read:
                        self.logger.info(f"Prompt cache: created={cache_created}, read={cache_read} tokens")

                    # Calculate running cost
                    self.metrics.estimated_cost = estimate_cost(
                        self.model,
                        self.metrics.input_tokens,
                        self.metrics.output_tokens
                    )

                return response

            except CircuitBreakerOpenError as e:
                self.metrics.errors += 1
                self.logger.error(f"Circuit breaker open: {e}")
                raise
            except anthropic.BadRequestError as e:
                # 400 errors are config bugs, NOT transient failures
                # Don't trip circuit breaker - fail fast with clear message
                self.metrics.errors += 1
                error_msg = str(e)
                if "max_tokens" in error_msg:
                    self.logger.error(f"CONFIG ERROR: max_tokens exceeds model limit. {error_msg}")
                    raise ValueError(f"Model token limit exceeded. Reduce max_tokens or use different model. Error: {error_msg}")
                else:
                    self.logger.error(f"Bad request (config error): {error_msg}")
                    raise ValueError(f"Invalid API request (check config): {error_msg}")
            except anthropic.RateLimitError:
                if attempt < max_retries - 1:
                    wait_time = API_RETRY_BACKOFF_BASE ** attempt
                    self.logger.warning(f"Rate limit hit, waiting {wait_time}s...")
                    import time as time_module
                    time_module.sleep(wait_time)
                else:
                    raise
            except anthropic.APIError as e:
                self.metrics.errors += 1
                self.logger.error(f"API error: {e}")
                # Circuit breaker will track this failure (5xx, timeouts)
                raise

    def _process_response(self, response: anthropic.types.Message):
        """Process Claude's response and handle tool calls"""
        assistant_content = []
        tool_results = []

        for block in response.content:
            if block.type == "text":
                if block.text.strip():
                    text_preview = block.text[:150] + "..." if len(block.text) > 150 else block.text
                    print(f"  {text_preview}")
                assistant_content.append({"type": "text", "text": block.text})

            elif block.type == "tool_use":
                tool_name = block.name
                tool_input = block.input
                tool_id = block.id

                self.metrics.tool_calls += 1
                print(f"  Tool: {tool_name}")

                # Inject source_document and ENFORCE entity for traceability and contamination prevention
                if tool_name == "create_inventory_entry":
                    tool_input = dict(tool_input)  # Make a copy

                    # Inject source document
                    if self.current_document_name:
                        tool_input["source_document"] = self.current_document_name

                    # CRITICAL: Enforce entity to prevent cross-contamination
                    # Override whatever the LLM provided - we control which entity is being analyzed
                    tool_input["entity"] = self.current_entity
                    tool_input["analysis_phase"] = self.current_analysis_phase

                    # Log if LLM tried to use wrong entity
                    llm_entity = tool_input.get("entity", "")
                    if llm_entity and llm_entity != self.current_entity:
                        self.logger.warning(
                            f"Entity override: LLM tried '{llm_entity}', enforced '{self.current_entity}'"
                        )

                # Execute tool
                try:
                    result = execute_discovery_tool(
                        tool_name=tool_name,
                        tool_input=tool_input,
                        fact_store=self.fact_store
                    )

                    # Log to audit trail
                    self.audit_logger.log_tool_call(
                        tool_name=tool_name,
                        tool_input=tool_input,
                        result=result
                    )

                    # Log result
                    if result.get("status") == "success":
                        if "fact_id" in result:
                            print(f"    -> {result['fact_id']}: {result.get('message', '')[:50]}")
                        elif "gap_id" in result:
                            print(f"    -> {result['gap_id']}: {result.get('message', '')[:50]}")
                        else:
                            print(f"    -> {result.get('message', 'OK')[:60]}")

                    # Check for discovery complete - ONLY if the tool succeeded
                    # Rejected completions (e.g., insufficient extraction) should NOT end discovery
                    if tool_name == "complete_discovery":
                        if result.get("status") == "success":
                            self.discovery_complete = True
                        elif result.get("status") == "rejected":
                            # Extraction incomplete - log and continue
                            reason = result.get("reason", "unknown")
                            self.logger.warning(f"complete_discovery REJECTED: {reason}")
                            print(f"    -> REJECTED: {result.get('message', 'Incomplete extraction')[:100]}...")

                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_id,
                        "content": json.dumps(result)
                    })

                except Exception as e:
                    self.metrics.errors += 1
                    self.logger.error(f"Tool execution error: {e}")
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_id,
                        "content": json.dumps({
                            "status": "error",
                            "message": str(e)
                        })
                    })

                assistant_content.append({
                    "type": "tool_use",
                    "id": tool_id,
                    "name": tool_name,
                    "input": tool_input
                })

        # Add assistant message
        self.messages.append({"role": "assistant", "content": assistant_content})

        # Add tool results
        if tool_results:
            self.messages.append({"role": "user", "content": tool_results})

        # Handle no tool calls
        if response.stop_reason == "end_turn" and not tool_results:
            print("  [WARN] No tool calls - prompting to continue")
            self.messages.append({
                "role": "user",
                "content": "Please continue extracting facts. Use create_inventory_entry for each finding, "
                          "flag_gap for missing information, and complete_discovery when done."
            })

    def get_metrics(self) -> DiscoveryMetrics:
        """Get execution metrics"""
        return self.metrics
