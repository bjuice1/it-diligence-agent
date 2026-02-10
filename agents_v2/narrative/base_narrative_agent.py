"""
Base Narrative Agent for Investment Thesis Generation.

Narrative agents synthesize facts and reasoning findings into presentation-ready
content for PE buyers. They write in a candid, partner-level tone.

Key Responsibilities:
- Transform technical findings into business-relevant narratives
- Provide the "So What" for each domain
- Highlight key considerations and cost implications
- Maintain candid, practical tone throughout
"""

import anthropic
from typing import Dict, List, Optional, Any
from abc import ABC, abstractmethod
import json
import logging
from time import time
from dataclasses import dataclass

from stores.fact_store import FactStore
from tools_v2.reasoning_tools import ReasoningStore, COST_RANGE_VALUES
from tools_v2.narrative_tools import (
    NARRATIVE_TOOLS,
    execute_narrative_tool,
    NarrativeStore,
    DomainNarrative
)

# Import cost estimation, rate limiting config, and temperature
try:
    from config_v2 import (
        estimate_cost,
        API_RATE_LIMIT_SEMAPHORE_SIZE,
        API_RATE_LIMIT_PER_MINUTE,
        NARRATIVE_TEMPERATURE
    )
except ImportError:
    def estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
        return 0.0
    API_RATE_LIMIT_SEMAPHORE_SIZE = 5
    API_RATE_LIMIT_PER_MINUTE = 50
    NARRATIVE_TEMPERATURE = 0.1  # Slight variation for prose

# Import rate limiter
try:
    from tools_v2.rate_limiter import APIRateLimiter
except ImportError:
    APIRateLimiter = None


@dataclass
class NarrativeMetrics:
    """Track narrative agent execution metrics."""
    api_calls: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    execution_time: float = 0.0
    iterations: int = 0
    estimated_cost: float = 0.0


class BaseNarrativeAgent(ABC):
    """
    Base class for narrative agents that generate presentation content.

    Each domain narrative agent:
    1. Receives facts, risks, and work items for its domain
    2. Synthesizes into a coherent narrative
    3. Produces structured content for the presentation

    Uses Sonnet model for quality narrative generation.
    """

    def __init__(
        self,
        fact_store: FactStore,
        reasoning_store: ReasoningStore,
        narrative_store: NarrativeStore,
        api_key: str,
        model: str = "claude-sonnet-4-20250514",
        max_tokens: int = 4096,
        max_iterations: int = 5
    ):
        if not api_key:
            raise ValueError("API key must be provided")

        self.client = anthropic.Anthropic(api_key=api_key)
        self.fact_store = fact_store
        self.reasoning_store = reasoning_store
        self.narrative_store = narrative_store
        self.tools = NARRATIVE_TOOLS
        self.model = model
        self.max_tokens = max_tokens
        self.max_iterations = max_iterations

        # State
        self.messages: List[Dict] = []
        self.narrative_complete: bool = False

        # Metrics
        self.metrics = NarrativeMetrics()
        self.start_time: Optional[float] = None

        # Logging
        self.logger = logging.getLogger(f"narrative.{self.domain}")
        
        # Rate limiting
        if APIRateLimiter:
            self.rate_limiter = APIRateLimiter.get_instance(
                max_concurrent=API_RATE_LIMIT_SEMAPHORE_SIZE,
                requests_per_minute=API_RATE_LIMIT_PER_MINUTE
            )
        else:
            self.rate_limiter = None

    @property
    @abstractmethod
    def domain(self) -> str:
        """Return the domain name (infrastructure, network, etc.)"""
        pass

    @property
    @abstractmethod
    def domain_title(self) -> str:
        """Return the display title for this domain."""
        pass

    @property
    @abstractmethod
    def narrative_guidance(self) -> str:
        """Return domain-specific guidance for narrative generation."""
        pass

    def generate(self) -> Optional[DomainNarrative]:
        """
        Generate the narrative for this domain.

        Returns:
            DomainNarrative with structured content for presentation.
        """
        self.start_time = time()
        self.logger.info(f"Starting {self.domain.upper()} narrative generation")
        print(f"\n{'='*60}")
        print(f"Narrative: {self.domain.upper()}")
        print(f"{'='*60}")

        # Gather domain data
        domain_data = self._gather_domain_data()

        if not domain_data['facts'] and not domain_data['risks']:
            self.logger.warning(f"No data for {self.domain} narrative")
            print(f"[WARN] No data available for {self.domain} narrative")
            return None

        print(f"Input: {len(domain_data['facts'])} facts, {len(domain_data['risks'])} risks, "
              f"{len(domain_data['work_items'])} work items")

        try:
            # Build system prompt
            system_prompt = self._build_system_prompt(domain_data)

            # Build user message
            user_message = self._build_user_message(domain_data)
            self.messages = [{"role": "user", "content": user_message}]

            # Generation loop (usually completes in 1-2 iterations)
            iteration = 0
            while not self.narrative_complete and iteration < self.max_iterations:
                iteration += 1
                self.metrics.iterations = iteration

                response = self._call_model(system_prompt)
                self._process_response(response)

                if self.narrative_complete:
                    print(f"\n[OK] {self.domain.upper()} narrative complete")
                    break

        except Exception as e:
            self.logger.error(f"Narrative generation failed: {e}")
            print(f"[ERROR] Narrative generation failed: {e}")
            return None

        # Calculate metrics
        self.metrics.execution_time = time() - self.start_time
        print(f"Time: {self.metrics.execution_time:.1f}s | "
              f"Tokens: {self.metrics.input_tokens + self.metrics.output_tokens} | "
              f"Cost: ${self.metrics.estimated_cost:.4f}")

        return self.narrative_store.get_domain_narrative(self.domain)

    def _gather_domain_data(self) -> Dict[str, Any]:
        """Gather all data needed for narrative generation."""
        # Facts
        facts = [f for f in self.fact_store.facts if f.domain == self.domain]
        gaps = [g for g in self.fact_store.gaps if g.domain == self.domain]

        # Reasoning findings
        risks = [r for r in self.reasoning_store.risks if r.domain == self.domain]
        work_items = [w for w in self.reasoning_store.work_items if w.domain == self.domain]

        # Calculate costs
        domain_cost_low = 0
        domain_cost_high = 0
        for wi in work_items:
            cost_range = COST_RANGE_VALUES.get(wi.cost_estimate, {'low': 0, 'high': 0})
            domain_cost_low += cost_range['low']
            domain_cost_high += cost_range['high']

        return {
            'facts': facts,
            'gaps': gaps,
            'risks': risks,
            'work_items': work_items,
            'cost_low': domain_cost_low,
            'cost_high': domain_cost_high
        }

    def _build_system_prompt(self, domain_data: Dict) -> str:
        """Build the system prompt for narrative generation."""

        return f"""You are a senior IT due diligence partner writing an investment thesis presentation for PE buyers.

YOUR ROLE:
You're presenting {self.domain_title} findings to a PE deal team. Be candid - like a Big Four partner
explaining what they're actually taking on. Not salesy, not alarmist - just practical and direct.

TONE GUIDANCE:
- WRONG: "The target has a robust, enterprise-grade infrastructure..."
- RIGHT: "They're running on two colocated data centers with aging VMware. You'll need to decide
  if you're modernizing or migrating to cloud."

- WRONG: "There are some minor gaps in documentation..."
- RIGHT: "We don't have visibility into their network architecture. That's 4 VDR requests you'll
  need answers on before you can plan Day 1."

- WRONG: "The cybersecurity posture is generally aligned with best practices..."
- RIGHT: "No PAM solution, no documented incident response plan. If you're in a regulated industry
  or need cyber insurance, this is Day 1 work."

AVOID ABSOLUTE CLAIMS:
- WRONG: "PAM and IGA aren't optional - cyber insurance and regulatory compliance demand it."
- RIGHT: "PAM and IGA are typically required to meet buyer security baselines and audit expectations.
  Exact requirements depend on your regulatory context and insurance requirements."

When making claims about requirements, use conditional language unless you have specific evidence:
- "typically required for..." instead of "mandatory"
- "most buyers expect..." instead of "you must"
- "likely needed if..." instead of "required"

DOMAIN: {self.domain_title}

{self.narrative_guidance}

YOUR TASK:
Generate narrative content for the {self.domain_title} slide in the investment thesis presentation.
Use the write_domain_narrative tool to record your narrative, then complete_narrative when done.

REQUIREMENTS:
1. "So What" - One sentence capturing THE key implication. What will the buyer deal with?
2. Considerations - 3-5 key points with specific details where available
3. Narrative - 2-3 paragraphs telling the story. What's there, what works, what doesn't, what they'll do.
4. Cost Summary - What this domain will cost the buyer
5. Cite specific facts (F-XXX-NNN) that support your narrative

The output will be shown to investment committee. Make it count."""

    def _build_user_message(self, domain_data: Dict) -> str:
        """Build the user message with domain data."""

        # Format facts
        facts_text = ""
        if domain_data['facts']:
            facts_text = "## FACTS\n"
            for f in domain_data['facts']:
                details_str = json.dumps(f.details) if f.details else "N/A"
                evidence_str = f.evidence.get('exact_quote', 'N/A') if f.evidence else 'N/A'
                source_str = f.evidence.get('source_section', '') if f.evidence else ''
                facts_text += f"\n**{f.fact_id}**: {f.item}\n"
                facts_text += f"  Category: {f.category} | Status: {f.status}\n"
                facts_text += f"  Details: {details_str}\n"
                facts_text += f"  Evidence: \"{evidence_str}\"\n"
                if source_str:
                    facts_text += f"  Source: {source_str}\n"

        # Format gaps
        gaps_text = ""
        if domain_data['gaps']:
            gaps_text = "\n## INFORMATION GAPS\n"
            for g in domain_data['gaps']:
                gaps_text += f"\n**{g.gap_id}** [{g.importance.upper()}]: {g.description}\n"

        # Format risks
        risks_text = ""
        if domain_data['risks']:
            risks_text = "\n## IDENTIFIED RISKS\n"
            for r in domain_data['risks']:
                risks_text += f"\n**{r.finding_id}** [{r.severity.upper()}]: {r.title}\n"
                risks_text += f"  {r.description}\n"
                risks_text += f"  Mitigation: {r.mitigation}\n"
                if r.based_on_facts:
                    risks_text += f"  Based on: {', '.join(r.based_on_facts)}\n"

        # Format work items
        work_items_text = ""
        if domain_data['work_items']:
            work_items_text = "\n## WORK ITEMS\n"
            for w in domain_data['work_items']:
                cost_range = COST_RANGE_VALUES.get(w.cost_estimate, {'low': 0, 'high': 0})
                work_items_text += f"\n**{w.finding_id}** [{w.phase}]: {w.title}\n"
                work_items_text += f"  Cost: ${cost_range['low']:,.0f} - ${cost_range['high']:,.0f}\n"
                work_items_text += f"  Owner: {w.owner_type} | Priority: {w.priority}\n"

        # Cost summary
        cost_text = "\n## DOMAIN COST SUMMARY\n"
        cost_text += f"Total estimated cost for {self.domain_title}: "
        cost_text += f"${domain_data['cost_low']:,.0f} - ${domain_data['cost_high']:,.0f}\n"

        return f"""Generate the investment thesis narrative for {self.domain_title}.

Here is the data for this domain:

{facts_text}
{gaps_text}
{risks_text}
{work_items_text}
{cost_text}

Now write the narrative using the write_domain_narrative tool. Be candid and practical.
After writing the narrative, use complete_narrative to finish."""

    def _call_model(self, system_prompt: str) -> Any:
        """Call the Claude API with timeout and rate limiting."""
        self.metrics.api_calls += 1
        from config_v2 import API_TIMEOUT_SECONDS, API_RATE_LIMITER_TIMEOUT
        timeout_seconds = API_TIMEOUT_SECONDS

        # Acquire rate limiter before making API call
        if self.rate_limiter:
            if not self.rate_limiter.acquire(timeout=API_RATE_LIMITER_TIMEOUT):
                raise TimeoutError("Rate limiter timeout: could not acquire API call slot")
        
        try:
            # Use low temperature for more consistent narrative output
            # Use prompt caching to reduce token costs on repeated iterations
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=NARRATIVE_TEMPERATURE,  # Low temp for consistent prose
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

        # Track token usage
        self.metrics.input_tokens += response.usage.input_tokens
        self.metrics.output_tokens += response.usage.output_tokens

        # Log cache statistics if available
        cache_created = getattr(response.usage, 'cache_creation_input_tokens', 0)
        cache_read = getattr(response.usage, 'cache_read_input_tokens', 0)
        if cache_created or cache_read:
            self.logger.info(f"Prompt cache: created={cache_created}, read={cache_read} tokens")

        self.metrics.estimated_cost += estimate_cost(
            self.model,
            response.usage.input_tokens,
            response.usage.output_tokens
        )

        return response

    def _process_response(self, response: Any):
        """Process the model response."""
        tool_results = []

        for block in response.content:
            if block.type == "text":
                # Log any text output
                if block.text.strip():
                    self.logger.debug(f"Model text: {block.text[:100]}...")

            elif block.type == "tool_use":
                tool_name = block.name
                tool_input = block.input

                print(f"  Tool: {tool_name}")

                # Execute tool with error handling
                try:
                    result = execute_narrative_tool(
                        tool_name=tool_name,
                        tool_input=tool_input,
                        narrative_store=self.narrative_store,
                        domain=self.domain
                    )
                except Exception as e:
                    self.logger.error(f"Tool execution failed: {tool_name}: {e}")
                    result = {
                        "status": "error",
                        "message": f"Tool execution failed: {e}"
                    }

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps(result)
                })

                # Log errors but continue (allow model to retry)
                if result.get("status") == "error":
                    self.logger.warning(f"Tool error: {result.get('message')}")
                    print(f"    [WARN] {result.get('message')}")

                # Check for completion
                if result.get("status") == "complete":
                    self.narrative_complete = True

        # Add assistant response and tool results to messages
        self.messages.append({"role": "assistant", "content": response.content})
        if tool_results:
            self.messages.append({"role": "user", "content": tool_results})
