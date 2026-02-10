"""
Base Reasoning Agent for V2 Architecture

Reasoning agents analyze facts from the FactStore and produce findings.
They use the more capable Sonnet model since analysis requires deeper reasoning.

Key Responsibilities:
- Analyze facts in context of the deal
- Identify risks with fact citations
- Create strategic considerations
- Produce phased work items
- Every finding MUST cite supporting facts
"""

import anthropic
from typing import Dict, List, Optional, Any
from abc import ABC, abstractmethod
import json
import logging
from time import time
from dataclasses import dataclass

from stores.fact_store import FactStore
from tools_v2.reasoning_tools import (
    REASONING_TOOLS,
    execute_reasoning_tool,
    ReasoningStore
)

# Import cost estimation, rate limiter, circuit breaker, and temperature
try:
    from config_v2 import (
        estimate_cost,
        API_RATE_LIMIT_SEMAPHORE_SIZE,
        API_RATE_LIMIT_PER_MINUTE,
        REASONING_TEMPERATURE
    )
    from tools_v2.rate_limiter import APIRateLimiter
    from tools_v2.circuit_breaker import CircuitBreaker, CircuitBreakerConfig, CircuitBreakerOpenError
except ImportError:
    def estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
        return 0.0
    API_RATE_LIMIT_SEMAPHORE_SIZE = 3
    API_RATE_LIMIT_PER_MINUTE = 40
    REASONING_TEMPERATURE = 0.0  # Default to deterministic
    APIRateLimiter = None
    CircuitBreaker = None
    CircuitBreakerConfig = None
    CircuitBreakerOpenError = Exception


@dataclass
class ReasoningMetrics:
    """Track reasoning agent execution metrics"""
    api_calls: int = 0
    tool_calls: int = 0
    tokens_used: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    execution_time: float = 0.0
    iterations: int = 0
    risks_identified: int = 0
    work_items_created: int = 0
    recommendations_made: int = 0
    facts_cited: int = 0
    errors: int = 0
    estimated_cost: float = 0.0  # Running cost estimate in USD


class BaseReasoningAgent(ABC):
    """
    Base class for reasoning agents in the V2 architecture.

    Reasoning agents:
    1. Receive facts from FactStore (output of Discovery phase)
    2. Analyze facts in deal context
    3. Produce findings with fact citations
    4. Store results in ReasoningStore

    Key principle: Every finding must cite supporting facts.
    This creates traceable evidence chains.

    Uses Sonnet model for deeper reasoning capability.
    """

    def __init__(
        self,
        fact_store: FactStore,
        api_key: str,
        model: str = "claude-sonnet-4-20250514",
        max_tokens: int = 8192,
        max_iterations: int = 40  # Allow thorough analysis - completion prompts prevent infinite loops
    ):
        if not api_key:
            raise ValueError("API key must be provided")

        self.client = anthropic.Anthropic(api_key=api_key)
        self.fact_store = fact_store
        self.reasoning_store = ReasoningStore(fact_store=fact_store)
        self.tools = REASONING_TOOLS
        self.model = model
        self.max_tokens = max_tokens
        self.max_iterations = max_iterations

        # State
        self.messages: List[Dict] = []
        self.reasoning_complete: bool = False

        # Metrics
        self.metrics = ReasoningMetrics()
        self.start_time: Optional[float] = None

        # Logging
        self.logger = logging.getLogger(f"reasoning.{self.domain}")
        
        # Rate limiting
        if APIRateLimiter:
            self.rate_limiter = APIRateLimiter.get_instance(
                max_concurrent=API_RATE_LIMIT_SEMAPHORE_SIZE,
                requests_per_minute=API_RATE_LIMIT_PER_MINUTE
            )
        else:
            self.rate_limiter = None
        
        # Circuit breaker for API failures
        if CircuitBreaker:
            from config_v2 import CIRCUIT_BREAKER_FAILURE_THRESHOLD, CIRCUIT_BREAKER_TIMEOUT
            self.circuit_breaker = CircuitBreaker(
                config=CircuitBreakerConfig(
                    failure_threshold=CIRCUIT_BREAKER_FAILURE_THRESHOLD,
                    timeout=CIRCUIT_BREAKER_TIMEOUT,
                    expected_exception=anthropic.APIError
                )
            )
        else:
            self.circuit_breaker = None

    @property
    @abstractmethod
    def domain(self) -> str:
        """Return the domain name (infrastructure, network, etc.)"""
        pass

    @property
    @abstractmethod
    def system_prompt(self) -> str:
        """Return the reasoning prompt template for this domain"""
        pass

    def reason(self, deal_context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Run reasoning on facts in the FactStore.

        Args:
            deal_context: Context about the deal (buyer info, transaction type, etc.)

        Returns:
            Dict with reasoning results including:
            - risks: List of identified risks with fact citations
            - strategic_considerations: List of strategic observations
            - work_items: List of phased work items
            - recommendations: List of recommendations
            - evidence_chains: Traceability data
            - metrics: Execution metrics
        """
        self.start_time = time()
        self.logger.info(f"Starting {self.domain.upper()} reasoning")
        print(f"\n{'='*60}")
        print(f"Reasoning: {self.domain.upper()}")
        print(f"{'='*60}")

        # Get facts for this domain
        domain_facts = self.fact_store.get_domain_facts(self.domain)
        print(f"Input: {domain_facts['fact_count']} facts, {domain_facts['gap_count']} gaps")

        if domain_facts['fact_count'] == 0:
            self.logger.warning(f"No facts found for {self.domain}")
            print(f"[WARN] No facts to reason about for {self.domain}")
            return {
                "domain": self.domain,
                "findings": self.reasoning_store.get_all_findings(),
                "metrics": {},
                "warning": "No facts available for reasoning"
            }

        try:
            # Build prompt with facts injected (BUYER-AWARE FIX 2026-02-04)
            # Extract overlaps from deal_context if available
            overlaps = (deal_context or {}).get('overlaps', [])

            # Use buyer-aware formatter (includes target + buyer facts + overlaps)
            inventory_text = self.fact_store.format_for_reasoning_with_buyer_context(
                self.domain,
                overlaps=overlaps
            )

            system_prompt = self._build_system_prompt(inventory_text, deal_context or {})

            # Build initial user message
            user_message = self._build_user_message(deal_context or {})
            self.messages = [{"role": "user", "content": user_message}]

            # Reasoning loop
            iteration = 0
            while not self.reasoning_complete and iteration < self.max_iterations:
                iteration += 1
                self.metrics.iterations = iteration
                print(f"\n--- Iteration {iteration} ---")

                try:
                    # Call model with injected prompt
                    response = self._call_model(system_prompt)

                    # Process response
                    self._process_response(response)

                    if self.reasoning_complete:
                        print(f"\n[OK] {self.domain.upper()} reasoning complete after {iteration} iterations")
                        break

                except Exception as e:
                    self.metrics.errors += 1
                    self.logger.error(f"Error in iteration {iteration}: {e}", exc_info=True)
                    if iteration >= self.max_iterations:
                        raise

            if not self.reasoning_complete:
                print(f"\n[WARN] Max iterations ({self.max_iterations}) reached")
                self.logger.warning("Max iterations reached without completion")

            # Calculate execution time
            if self.start_time:
                self.metrics.execution_time = time() - self.start_time

            # Get findings
            findings = self.reasoning_store.get_all_findings()

            # Update metrics
            self.metrics.risks_identified = findings["summary"]["risks"]
            self.metrics.work_items_created = findings["summary"]["work_items"]
            self.metrics.recommendations_made = findings["summary"]["recommendations"]

            # Count cited facts
            cited_facts = set()
            for risk in self.reasoning_store.risks:
                cited_facts.update(risk.based_on_facts)
            for sc in self.reasoning_store.strategic_considerations:
                cited_facts.update(sc.based_on_facts)
            for wi in self.reasoning_store.work_items:
                cited_facts.update(wi.triggered_by)
                cited_facts.update(wi.based_on_facts)
            for rec in self.reasoning_store.recommendations:
                cited_facts.update(rec.based_on_facts)
            self.metrics.facts_cited = len(cited_facts)

            # Calculate citation coverage
            citation_coverage = (self.metrics.facts_cited / domain_facts['fact_count'] * 100
                               if domain_facts['fact_count'] > 0 else 0)

            print("\nReasoning Results:")
            print(f"  Risks: {self.metrics.risks_identified}")
            print(f"  Strategic considerations: {findings['summary']['strategic_considerations']}")
            print(f"  Work items: {self.metrics.work_items_created}")
            print(f"  Recommendations: {self.metrics.recommendations_made}")
            print(f"  Facts cited: {self.metrics.facts_cited}/{domain_facts['fact_count']} ({citation_coverage:.0f}%)")
            print(f"  API calls: {self.metrics.api_calls}")
            print(f"  Tokens: {self.metrics.input_tokens} in, {self.metrics.output_tokens} out")
            print(f"  Estimated cost: ${self.metrics.estimated_cost:.4f}")
            print(f"  Time: {self.metrics.execution_time:.1f}s")

            return {
                "domain": self.domain,
                "findings": findings,
                "citation_coverage": citation_coverage,
                "uncited_facts": [f["fact_id"] for f in domain_facts["facts"]
                                 if f["fact_id"] not in cited_facts],
                "metrics": {
                    "api_calls": self.metrics.api_calls,
                    "tool_calls": self.metrics.tool_calls,
                    "tokens_used": self.metrics.tokens_used,
                    "execution_time": self.metrics.execution_time,
                    "iterations": self.metrics.iterations,
                    "facts_cited": self.metrics.facts_cited,
                    "estimated_cost": self.metrics.estimated_cost
                }
            }

        except Exception as e:
            self.logger.error(f"Reasoning failed: {e}", exc_info=True)
            raise

    def _build_system_prompt(self, inventory_text: str, deal_context: Dict) -> str:
        """Build the system prompt with inventory and context injected"""
        # Get the template from subclass
        template = self.system_prompt

        # Inject inventory
        if "{inventory}" in template:
            prompt = template.replace("{inventory}", inventory_text)
        else:
            # Append inventory if no placeholder
            prompt = template + f"\n\n## INVENTORY\n\n{inventory_text}"

        # Inject deal context
        if "{deal_context}" in prompt:
            # Check if we have a formatted prompt context from DDSession
            if deal_context and "_prompt_context" in deal_context:
                # Use the pre-formatted, deal-type-aware context
                context_str = deal_context["_prompt_context"]
            elif deal_context:
                # Fall back to JSON formatting
                context_str = json.dumps(deal_context, indent=2)
            else:
                context_str = "No specific deal context provided."
            prompt = prompt.replace("{deal_context}", context_str)

        return prompt

    def _build_user_message(self, deal_context: Dict) -> str:
        """Build the user message to start reasoning"""
        parts = [
            "Based on the inventory provided in the system prompt, please:",
            "",
            "1. Analyze the facts and identify risks (use identify_risk)",
            "2. Note strategic considerations for the deal (use create_strategic_consideration)",
            "3. Create phased work items (use create_work_item)",
            "4. Provide recommendations (use create_recommendation)",
            "",
            "CRITICAL: Every finding MUST cite the fact IDs that support it.",
            "Use the based_on_facts/triggered_by fields to link findings to evidence.",
            "",
            "IMPORTANT: When you have finished analyzing all the facts and created your findings,",
            f"you MUST call complete_reasoning() to signal completion of the {self.domain} domain.",
            "Do not continue generating findings indefinitely - call complete_reasoning when done."
        ]

        if deal_context:
            parts.insert(0, f"## Deal Context\n{json.dumps(deal_context, indent=2)}\n")

        return "\n".join(parts)

    def _call_model(self, system_prompt: str) -> anthropic.types.Message:
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
                # Acquire rate limiter before making API call
                if self.rate_limiter:
                    if not self.rate_limiter.acquire(timeout=API_RATE_LIMITER_TIMEOUT):
                        raise TimeoutError("Rate limiter timeout: could not acquire API call slot")

                try:
                    # CRITICAL: temperature=0 for deterministic, consistent scoring
                    # Use prompt caching to reduce token costs on repeated iterations
                    # The system prompt is sent as a cached block - subsequent calls
                    # in the same session reuse the cache at 90% token discount
                    response = self.client.messages.create(
                        model=self.model,
                        max_tokens=effective_max_tokens,  # Use clamped value
                        temperature=REASONING_TEMPERATURE,  # Deterministic analysis
                        system=[{
                            "type": "text",
                            "text": system_prompt,
                            "cache_control": {"type": "ephemeral"}
                        }],
                        tools=self.tools,
                        messages=self.messages,
                        timeout=timeout_seconds  # Add timeout to prevent hanging
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
                    text_preview = block.text[:200] + "..." if len(block.text) > 200 else block.text
                    print(f"  {text_preview}")
                assistant_content.append({"type": "text", "text": block.text})

            elif block.type == "tool_use":
                tool_name = block.name
                tool_input = block.input
                tool_id = block.id

                self.metrics.tool_calls += 1
                print(f"  Tool: {tool_name}")

                # Execute tool
                try:
                    result = execute_reasoning_tool(
                        tool_name=tool_name,
                        tool_input=tool_input,
                        reasoning_store=self.reasoning_store
                    )

                    # Log result
                    if result.get("status") == "success":
                        # Log the ID and key info
                        for key in ["risk_id", "consideration_id", "work_item_id", "recommendation_id"]:
                            if key in result:
                                title = tool_input.get("title", "")[:40]
                                print(f"    -> {result[key]}: {title}")
                                break
                        else:
                            print(f"    -> {result.get('message', 'OK')[:60]}")
                    else:
                        print(f"    -> [ERROR] {result.get('message', 'Unknown error')}")

                    # Check for reasoning complete
                    if tool_name == "complete_reasoning":
                        self.reasoning_complete = True

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
            # Check if we have findings - if so, prompt to complete
            findings_count = (
                len(self.reasoning_store.risks) +
                len(self.reasoning_store.work_items) +
                len(self.reasoning_store.strategic_considerations) +
                len(self.reasoning_store.recommendations)
            )
            if findings_count > 0:
                print("  [INFO] Findings generated - prompting to complete")
                self.messages.append({
                    "role": "user",
                    "content": f"You have generated {findings_count} findings. If your analysis is complete, "
                              "call complete_reasoning() now. If you have more findings to add, continue."
                })
            else:
                print("  [WARN] No tool calls - prompting to continue")
                self.messages.append({
                    "role": "user",
                    "content": "Please continue your analysis. Use identify_risk, create_strategic_consideration, "
                              "create_work_item, and create_recommendation to record findings. "
                              "Call complete_reasoning when done."
                })

        # If we've made many tool calls without completing, remind about completion
        if self.metrics.tool_calls >= 8 and not self.reasoning_complete:
            findings_count = (
                len(self.reasoning_store.risks) +
                len(self.reasoning_store.work_items) +
                len(self.reasoning_store.strategic_considerations) +
                len(self.reasoning_store.recommendations)
            )
            if findings_count >= 5 and tool_results:
                # Add a gentle reminder
                self.messages.append({
                    "role": "user",
                    "content": f"You have created {findings_count} findings. Remember to call complete_reasoning() "
                              "when you have finished your analysis."
                })

    def get_metrics(self) -> ReasoningMetrics:
        """Get execution metrics"""
        return self.metrics

    def get_reasoning_store(self) -> ReasoningStore:
        """Get the reasoning store with all findings"""
        return self.reasoning_store

    def get_evidence_chain(self, finding_id: str) -> Dict[str, Any]:
        """Get the full evidence chain for a finding"""
        return self.reasoning_store.get_evidence_chain(finding_id)
