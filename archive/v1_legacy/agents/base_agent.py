"""
Base Agent for IT Diligence Analysis

Implements the core agentic loop using Anthropic's native tool_use.
Domain-specific agents inherit from this and provide their own system prompts.
"""
import anthropic
from typing import Dict, List, Optional, Any
from abc import ABC, abstractmethod
import json
import logging
from pathlib import Path
from datetime import datetime
from time import time
from dataclasses import dataclass
from difflib import SequenceMatcher

# Try to import tenacity for retry logic, but make it optional
try:
    from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
    HAS_TENACITY = True
except ImportError:
    HAS_TENACITY = False
    # Create dummy decorator if tenacity not available
    def retry(*args, **kwargs):
        def decorator(func):
            return func
        return decorator
    def stop_after_attempt(*args):
        return None
    def wait_exponential(*args, **kwargs):
        return None
    def retry_if_exception_type(*args):
        return None

from config import ANTHROPIC_API_KEY, MODEL, MAX_TOKENS, MAX_TOOL_ITERATIONS, TEMPERATURE
from tools.analysis_tools import ANALYSIS_TOOLS, AnalysisStore


@dataclass
class AgentMetrics:
    """Track agent execution metrics"""
    api_calls: int = 0
    tool_calls: int = 0
    tokens_used: int = 0
    execution_time: float = 0.0
    iterations: int = 0
    errors: int = 0
    retries: int = 0
    duplicates_detected: int = 0


class BaseAgent(ABC):
    """
    Base class for domain analysis agents.
    
    Each agent:
    1. Receives document text to analyze
    2. Has a domain-specific system prompt (playbook)
    3. Uses tools to record findings
    4. Runs until it calls complete_analysis or hits max iterations
    
    Improvements:
    - Error handling with retry logic
    - Logging and metrics tracking
    - Duplicate detection
    - Checkpointing capability
    - Output validation
    """
    
    def __init__(self, analysis_store: AnalysisStore):
        # Validate configuration
        if not ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY must be set in config or environment")
        if MAX_TOOL_ITERATIONS < 1:
            raise ValueError("MAX_TOOL_ITERATIONS must be >= 1")
        
        self.client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        self.store = analysis_store
        self.tools = ANALYSIS_TOOLS
        self.model = MODEL
        self.max_iterations = MAX_TOOL_ITERATIONS
        
        # Tracking
        self.messages: List[Dict] = []
        self.tool_calls_made: int = 0
        self.analysis_complete: bool = False

        # Reasoning chain capture - stores the logic flow
        self.reasoning_chain: List[Dict] = []
        self._current_reasoning: Optional[str] = None  # Holds reasoning until linked to finding

        # Metrics
        self.metrics = AgentMetrics()
        self.start_time: Optional[float] = None
        
        # Logging
        self.logger = logging.getLogger(f"agent.{self.domain}")
        self._setup_logging()
    
    def _setup_logging(self):
        """Configure logging for the agent.

        Note: We don't add handlers here - we rely on the root logger
        configured in main.py. This prevents double logging.
        """
        # Don't add handlers - use root logger's handler via propagation
        # This prevents double logging (once from agent handler, once from root)
        self.logger.setLevel(logging.INFO)
    
    @property
    @abstractmethod
    def domain(self) -> str:
        """Return the domain name (infrastructure, network, cybersecurity)"""
        pass
    
    @property
    @abstractmethod
    def system_prompt(self) -> str:
        """Return the domain-specific system prompt with analysis guidelines"""
        pass
    
    def analyze(self, document_text: str, deal_context: Optional[Dict] = None) -> Dict:
        """
        Run analysis on the provided document text.
        
        Args:
            document_text: Extracted text from IT documents
            deal_context: Optional context about the deal (transaction type, buyer info, etc.)
        
        Returns:
            Domain findings from the analysis store
        """
        self.start_time = time()
        self.logger.info(f"Starting {self.domain.upper()} analysis")
        print(f"\n{'='*60}")
        print(f"🔍 Starting {self.domain.upper()} Analysis")
        print(f"{'='*60}")
        
        try:
            # Build initial user message
            user_message = self._build_user_message(document_text, deal_context)
            self.messages = [{"role": "user", "content": user_message}]
            
            # Agentic loop
            iteration = 0
            while not self.analysis_complete and iteration < self.max_iterations:
                iteration += 1
                self.metrics.iterations = iteration
                print(f"\n--- Iteration {iteration} ---")
                self.logger.debug(f"Iteration {iteration}/{self.max_iterations}")
                
                try:
                    # Call Claude
                    response = self._call_model()
                    
                    # Process response
                    self._process_response(response)
                    
                    if self.analysis_complete:
                        print(f"\n✓ {self.domain.upper()} analysis complete after {iteration} iterations")
                        self.logger.info(f"Analysis complete after {iteration} iterations")
                        break
                
                except Exception as e:
                    self.metrics.errors += 1
                    self.logger.error(f"Error in iteration {iteration}: {e}", exc_info=True)
                    # Continue to next iteration instead of failing completely
                    if iteration >= self.max_iterations:
                        raise
            
            if not self.analysis_complete:
                print(f"\n⚠ Max iterations ({self.max_iterations}) reached without completion")
                self.logger.warning("Max iterations reached without completion")
            
            # Calculate execution time
            if self.start_time:
                self.metrics.execution_time = time() - self.start_time
            
            # Log metrics
            self.logger.info(f"Analysis metrics: {self.metrics}")
            print(f"\n📊 Metrics: {self.metrics.api_calls} API calls, {self.metrics.tool_calls} tool calls, "
                  f"{self.metrics.duplicates_detected} duplicates detected, "
                  f"{self.metrics.execution_time:.1f}s execution time")
            
            # Validate outputs
            validation = self._validate_outputs()
            if not validation["valid"]:
                self.logger.warning(f"Output validation issues: {validation['issues']}")
                if validation["issues"]:
                    print(f"\n⚠️  Validation issues: {', '.join(validation['issues'])}")
            if validation.get("warnings"):
                self.logger.warning(f"Output validation warnings: {validation['warnings']}")
            
            # Return domain findings
            return self.store.get_by_domain(self.domain)
        
        except Exception as e:
            self.logger.error(f"Analysis failed: {e}", exc_info=True)
            raise
    
    def _validate_outputs(self) -> Dict[str, Any]:
        """Validate analysis outputs for completeness"""
        issues = []
        warnings = []
        
        domain_findings = self.store.get_by_domain(self.domain)
        
        # Check for summary
        if not domain_findings.get("summary"):
            issues.append(f"Missing summary for {self.domain}")
        
        # Check critical risks have mitigations
        for risk in domain_findings.get("risks", []):
            if risk.get("severity") in ["critical", "high"]:
                mitigation = risk.get("mitigation", "")
                if not mitigation or len(mitigation) < 20:
                    warnings.append(f"Risk {risk['id']} lacks detailed mitigation")
        
        # Check work items have estimates
        for item in domain_findings.get("work_items", []):
            if not item.get("effort_estimate"):
                warnings.append(f"Work item {item['id']} missing effort estimate")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings
        }
    
    def save_checkpoint(self, checkpoint_path: Path):
        """Save current state for resumption"""
        checkpoint = {
            "domain": self.domain,
            "messages": self.messages,
            "tool_calls_made": self.tool_calls_made,
            "analysis_complete": self.analysis_complete,
            "metrics": {
                "api_calls": self.metrics.api_calls,
                "tool_calls": self.metrics.tool_calls,
                "tokens_used": self.metrics.tokens_used,
                "execution_time": self.metrics.execution_time,
                "iterations": self.metrics.iterations,
                "errors": self.metrics.errors,
                "retries": self.metrics.retries,
                "duplicates_detected": self.metrics.duplicates_detected
            },
            "timestamp": datetime.now().isoformat()
        }
        checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
        with open(checkpoint_path, 'w') as f:
            json.dump(checkpoint, f, indent=2)
        self.logger.info(f"Checkpoint saved to {checkpoint_path}")
        print(f"💾 Checkpoint saved to {checkpoint_path}")
    
    def load_checkpoint(self, checkpoint_path: Path):
        """Resume from checkpoint"""
        with open(checkpoint_path, 'r') as f:
            checkpoint = json.load(f)
        
        self.messages = checkpoint["messages"]
        self.tool_calls_made = checkpoint["tool_calls_made"]
        self.analysis_complete = checkpoint["analysis_complete"]
        
        # Restore metrics
        metrics_dict = checkpoint.get("metrics", {})
        self.metrics = AgentMetrics(**metrics_dict)
        
        self.logger.info(f"Checkpoint loaded from {checkpoint_path}")
        print(f"📂 Checkpoint loaded from {checkpoint_path}")
    
    def get_metrics(self) -> AgentMetrics:
        """Get execution metrics"""
        return self.metrics
    
    def _build_user_message(self, document_text: str, deal_context: Optional[Dict]) -> str:
        """Build the user message with document content and context"""
        parts = []

        # Check for incremental analysis mode
        incremental_context = None
        clean_deal_context = None

        if deal_context:
            # Extract incremental context if present
            incremental_context = deal_context.get('_incremental_context')

            # Create clean copy without internal fields for display
            clean_deal_context = {k: v for k, v in deal_context.items()
                                  if not k.startswith('_')}

        # Add deal context (without internal fields)
        if clean_deal_context:
            parts.append("## Deal Context")
            parts.append(json.dumps(clean_deal_context, indent=2))
            parts.append("")

        # Add incremental analysis instructions if in incremental mode
        if incremental_context:
            parts.append("## INCREMENTAL ANALYSIS MODE")
            parts.append("=" * 50)
            parts.append("")
            parts.append(incremental_context.get('instruction', ''))
            parts.append("")

            # Show existing risks summary
            if incremental_context.get('existing_risks'):
                parts.append("### Existing Risks Already Identified:")
                for i, risk in enumerate(incremental_context['existing_risks'], 1):
                    parts.append(f"  {i}. {risk}")
                parts.append("")

            # Show existing gaps summary
            if incremental_context.get('existing_gaps'):
                parts.append("### Existing Gaps Already Identified:")
                for i, gap in enumerate(incremental_context['existing_gaps'], 1):
                    parts.append(f"  {i}. {gap}")
                parts.append("")

            # Show existing assumptions summary
            if incremental_context.get('existing_assumptions'):
                parts.append("### Existing Assumptions Already Made:")
                for i, assumption in enumerate(incremental_context['existing_assumptions'], 1):
                    parts.append(f"  {i}. {assumption}")
                parts.append("")

            parts.append("### Your Focus in Incremental Mode:")
            parts.append("1. Look for NEW information not captured in existing findings above")
            parts.append("2. If you find evidence that VALIDATES an existing assumption, note it")
            parts.append("3. If you find evidence that CONTRADICTS an existing assumption, flag it as a risk")
            parts.append("4. If you find answers to existing gaps, record them as current state entries")
            parts.append("5. DO NOT repeat findings that already exist - focus on what's NEW")
            parts.append("")
            parts.append("=" * 50)
            parts.append("")

        parts.append("## Documents to Analyze")
        parts.append(document_text)
        parts.append("")
        parts.append("## Your Task")
        parts.append(f"Analyze the above documents through the {self.domain} lens.")
        parts.append("Use the provided tools to record all findings systematically.")

        if incremental_context:
            parts.append("Remember: This is INCREMENTAL analysis - focus on NEW findings only.")

        parts.append(f"Call complete_analysis when you have thoroughly analyzed all {self.domain}-related aspects.")

        return "\n".join(parts)
    
    def _call_model(self) -> anthropic.types.Message:
        """Make API call to Claude with retry logic"""
        return self._call_model_with_retry()
    
    def _call_model_with_retry(self) -> anthropic.types.Message:
        """Internal method with retry logic"""
        self.metrics.api_calls += 1
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=MAX_TOKENS,
                    temperature=TEMPERATURE,
                    system=self.system_prompt,
                    tools=self.tools,
                    messages=self.messages
                )
                
                # Track token usage if available
                if hasattr(response, 'usage'):
                    self.metrics.tokens_used += response.usage.input_tokens + response.usage.output_tokens
                
                return response
                
            except anthropic.RateLimitError as e:
                self.metrics.retries += 1
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    self.logger.warning(f"Rate limit hit (attempt {attempt + 1}/{max_retries}), waiting {wait_time}s...")
                    import time
                    time.sleep(wait_time)
                else:
                    self.metrics.errors += 1
                    self.logger.error(f"Rate limit error after {max_retries} attempts: {e}")
                    raise
                    
            except anthropic.APIConnectionError as e:
                self.metrics.retries += 1
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    self.logger.warning(f"Connection error (attempt {attempt + 1}/{max_retries}), waiting {wait_time}s...")
                    import time
                    time.sleep(wait_time)
                else:
                    self.metrics.errors += 1
                    self.logger.error(f"Connection error after {max_retries} attempts: {e}")
                    raise
                    
            except anthropic.APIError as e:
                self.metrics.errors += 1
                self.logger.error(f"API error: {e}")
                raise
    
    def _check_duplicate(self, tool_name: str, tool_input: Dict, threshold: float = 0.85) -> Optional[Dict]:
        """Check if this finding is a duplicate of an existing one"""
        if tool_name not in ["log_assumption", "identify_risk", "flag_gap"]:
            return None
        
        # Get existing findings of this type
        existing = []
        key_field = ""
        
        if tool_name == "log_assumption":
            existing = self.store.assumptions
            key_field = "assumption"
        elif tool_name == "identify_risk":
            existing = self.store.risks
            key_field = "risk"
        elif tool_name == "flag_gap":
            existing = self.store.gaps
            key_field = "gap"
        
        # Check same domain first
        domain = tool_input.get("domain")
        domain_findings = [f for f in existing if f.get("domain") == domain]
        
        new_text = tool_input.get(key_field, "").lower().strip()
        if not new_text:
            return None
        
        # Check similarity
        for existing_item in domain_findings:
            existing_text = existing_item.get(key_field, "").lower().strip()
            if not existing_text:
                continue
            
            similarity = SequenceMatcher(None, new_text, existing_text).ratio()
            if similarity > threshold:
                self.metrics.duplicates_detected += 1
                self.logger.info(f"Duplicate detected: {existing_item['id']} (similarity: {similarity:.2f})")
                return existing_item
        
        return None
    
    def _process_response(self, response: anthropic.types.Message):
        """Process Claude's response and handle tool calls with duplicate checking"""

        # Build assistant message content
        assistant_content = []
        tool_results = []

        # Collect all reasoning text from this response
        response_reasoning_parts = []

        for block in response.content:
            if block.type == "text":
                # Claude's reasoning/thinking - capture FULL text
                if block.text.strip():
                    # Store full reasoning for linking to findings
                    response_reasoning_parts.append(block.text.strip())

                    # Print truncated version for console readability
                    text_preview = block.text[:200] + "..." if len(block.text) > 200 else block.text
                    print(f"💭 {text_preview}")
                    self.logger.debug(f"Agent reasoning: {block.text}")
                assistant_content.append({"type": "text", "text": block.text})

            elif block.type == "tool_use":
                # Tool call
                tool_name = block.name
                tool_input = block.input
                tool_id = block.id

                self.tool_calls_made += 1
                self.metrics.tool_calls += 1
                print(f"🔧 Tool: {tool_name}")
                self.logger.info(f"Tool call: {tool_name}")

                # Check for duplicates before executing
                duplicate = self._check_duplicate(tool_name, tool_input)
                if duplicate:
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_id,
                        "content": json.dumps({
                            "status": "duplicate",
                            "id": duplicate["id"],
                            "message": f"Similar finding already exists: {duplicate['id']}"
                        })
                    })
                    print(f"   ⚠️  Duplicate detected: {duplicate['id']}")
                    assistant_content.append({
                        "type": "tool_use",
                        "id": tool_id,
                        "name": tool_name,
                        "input": tool_input
                    })
                    continue

                # Log key info from tool call
                self._log_tool_call(tool_name, tool_input)

                # Execute tool and capture reasoning chain
                try:
                    result = self.store.execute_tool(tool_name, tool_input)

                    # Link reasoning to this finding
                    if self._current_reasoning and result.get("status") == "recorded":
                        finding_id = result.get("id")
                        self._add_reasoning_entry(
                            finding_id=finding_id,
                            finding_type=result.get("type"),
                            tool_name=tool_name,
                            tool_input=tool_input,
                            reasoning=self._current_reasoning
                        )
                        # Clear reasoning after linking
                        self._current_reasoning = None

                    if tool_name == "complete_analysis":
                        self.analysis_complete = True

                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_id,
                        "content": json.dumps(result)
                    })
                except Exception as e:
                    self.metrics.errors += 1
                    self.logger.error(f"Tool execution error: {e}", exc_info=True)
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

        # Combine reasoning parts for this response (for cases with no tool calls)
        if response_reasoning_parts and self._current_reasoning is None:
            self._current_reasoning = "\n".join(response_reasoning_parts)
        
        # Add assistant message
        self.messages.append({"role": "assistant", "content": assistant_content})
        
        # Add tool results if any
        if tool_results:
            self.messages.append({"role": "user", "content": tool_results})
        
        # Check stop reason
        if response.stop_reason == "end_turn" and not tool_results:
            # Claude finished without tool calls - might be done or stuck
            print("⚠ Claude ended turn without tool calls")
            self.logger.warning("Claude ended turn without tool calls")
            # Prompt to continue or complete
            self.messages.append({
                "role": "user", 
                "content": "Please continue your analysis. Use tools to record findings, or call complete_analysis if you've finished analyzing all aspects."
            })
    
    def _log_tool_call(self, tool_name: str, tool_input: Dict):
        """Log tool call details"""
        if tool_name == "log_assumption":
            print(f"   📝 Assumption: {tool_input.get('assumption', '')[:80]}...")
        elif tool_name == "flag_gap":
            print(f"   ❓ Gap: {tool_input.get('gap', '')[:80]}...")
        elif tool_name == "identify_risk":
            print(f"   ⚠️  Risk [{tool_input.get('severity', '')}]: {tool_input.get('risk', '')[:60]}...")
        elif tool_name == "create_work_item":
            print(f"   📋 Work Item: {tool_input.get('title', '')}")
        elif tool_name == "create_recommendation":
            print(f"   💡 Recommendation: {tool_input.get('recommendation', '')[:60]}...")
        elif tool_name == "complete_analysis":
            print(f"   ✅ Analysis complete for {tool_input.get('domain', '')}")

    def _add_reasoning_entry(self, finding_id: str, finding_type: str, tool_name: str,
                             tool_input: Dict, reasoning: str):
        """
        Add a reasoning chain entry linking Claude's thinking to a specific finding.

        This captures the 'we saw X, therefore Y' logic for audit trails and explainability.
        """
        # Extract key observation from the finding
        observation_field_map = {
            "assumption": "assumption",
            "gap": "gap",
            "risk": "risk",
            "work_item": "title",
            "recommendation": "recommendation"
        }
        field_name = observation_field_map.get(finding_type, "description")
        finding_summary = tool_input.get(field_name, "")[:200]

        # Extract supporting evidence from tool input
        evidence_fields = ["basis", "trigger", "why_needed", "rationale", "description"]
        evidence = None
        for ef in evidence_fields:
            if ef in tool_input and tool_input[ef]:
                evidence = tool_input[ef]
                break

        entry = {
            "finding_id": finding_id,
            "finding_type": finding_type,
            "domain": self.domain,
            "timestamp": datetime.now().isoformat(),
            "reasoning_text": reasoning,
            "finding_summary": finding_summary,
            "evidence_from_finding": evidence,
            "iteration": self.metrics.iterations
        }

        self.reasoning_chain.append(entry)
        self.logger.debug(f"Reasoning chain entry added for {finding_id}")

    def get_reasoning_chain(self) -> List[Dict]:
        """Get the full reasoning chain for this agent's analysis"""
        return self.reasoning_chain

    def get_reasoning_for_finding(self, finding_id: str) -> Optional[Dict]:
        """Get the reasoning that led to a specific finding"""
        for entry in self.reasoning_chain:
            if entry["finding_id"] == finding_id:
                return entry
        return None
