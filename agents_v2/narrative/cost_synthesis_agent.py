"""
Cost Synthesis Agent for Investment Thesis Generation.

This agent aggregates costs across all domains and generates a coherent
narrative about the integration cost picture for PE buyers.
"""

import anthropic
from typing import Dict, List, Optional, Any
import json
import logging
from time import time
from dataclasses import dataclass

from tools_v2.reasoning_tools import ReasoningStore, COST_RANGE_VALUES
from tools_v2.narrative_tools import (
    COST_SYNTHESIS_TOOLS,
    NarrativeStore,
    CostNarrative
)

# Import cost estimation, rate limiter, and temperature
try:
    from config_v2 import (
        estimate_cost,
        API_RATE_LIMIT_SEMAPHORE_SIZE,
        API_RATE_LIMIT_PER_MINUTE,
        NARRATIVE_TEMPERATURE
    )
    from tools_v2.rate_limiter import APIRateLimiter
except ImportError:
    def estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
        return 0.0
    API_RATE_LIMIT_SEMAPHORE_SIZE = 3
    API_RATE_LIMIT_PER_MINUTE = 40
    NARRATIVE_TEMPERATURE = 0.1  # Default for consistent narrative
    APIRateLimiter = None


@dataclass
class CostMetrics:
    """Track cost synthesis execution metrics."""
    api_calls: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    execution_time: float = 0.0
    iterations: int = 0
    estimated_cost: float = 0.0


class CostSynthesisAgent:
    """
    Generates the cost synthesis narrative for the investment thesis.

    This agent:
    1. Aggregates all work items by phase, domain, and owner
    2. Identifies key cost drivers
    3. Produces a coherent narrative about the cost picture
    4. Notes assumptions and risks to estimates
    """

    def __init__(
        self,
        reasoning_store: ReasoningStore,
        narrative_store: NarrativeStore,
        api_key: str,
        model: str = "claude-sonnet-4-20250514",
        max_tokens: int = 4096,
        max_iterations: int = 3
    ):
        if not api_key:
            raise ValueError("API key must be provided")

        self.client = anthropic.Anthropic(api_key=api_key)
        self.reasoning_store = reasoning_store
        self.narrative_store = narrative_store
        self.tools = COST_SYNTHESIS_TOOLS
        self.model = model
        self.max_tokens = max_tokens
        self.max_iterations = max_iterations

        # State
        self.messages: List[Dict] = []
        self.synthesis_complete: bool = False

        # Metrics
        self.metrics = CostMetrics()
        self.start_time: Optional[float] = None

        # Logging
        self.logger = logging.getLogger("narrative.cost_synthesis")
        
        # Rate limiting
        if APIRateLimiter:
            self.rate_limiter = APIRateLimiter.get_instance(
                max_concurrent=API_RATE_LIMIT_SEMAPHORE_SIZE,
                requests_per_minute=API_RATE_LIMIT_PER_MINUTE
            )
        else:
            self.rate_limiter = None

    def generate(self) -> Optional[CostNarrative]:
        """
        Generate the cost synthesis narrative.

        Returns:
            CostNarrative with comprehensive cost analysis.
        """
        self.start_time = time()
        self.logger.info("Starting cost synthesis")
        print(f"\n{'='*60}")
        print("COST SYNTHESIS")
        print(f"{'='*60}")

        # Aggregate cost data
        cost_data = self._aggregate_costs()

        if cost_data['total']['high'] == 0:
            self.logger.warning("No cost data available")
            print("[WARN] No work items with costs to synthesize")
            return None

        print(f"Input: {cost_data['work_item_count']} work items across {len(cost_data['by_domain'])} domains")
        print(f"Total Range: ${cost_data['total']['low']:,.0f} - ${cost_data['total']['high']:,.0f}")

        try:
            # Build prompts
            system_prompt = self._build_system_prompt()
            user_message = self._build_user_message(cost_data)
            self.messages = [{"role": "user", "content": user_message}]

            # Generation loop
            iteration = 0
            while not self.synthesis_complete and iteration < self.max_iterations:
                iteration += 1
                self.metrics.iterations = iteration

                response = self._call_model(system_prompt)
                self._process_response(response, cost_data)

                if self.synthesis_complete:
                    print("\n[OK] Cost synthesis complete")
                    break

        except Exception as e:
            self.logger.error(f"Cost synthesis failed: {e}")
            print(f"[ERROR] Cost synthesis failed: {e}")
            return None

        # Metrics
        self.metrics.execution_time = time() - self.start_time
        print(f"Time: {self.metrics.execution_time:.1f}s | "
              f"Tokens: {self.metrics.input_tokens + self.metrics.output_tokens} | "
              f"Cost: ${self.metrics.estimated_cost:.4f}")

        return self.narrative_store.cost_narrative

    def _aggregate_costs(self) -> Dict[str, Any]:
        """Aggregate costs from all work items."""
        by_phase = {
            'Day_1': {'low': 0, 'high': 0, 'items': []},
            'Day_100': {'low': 0, 'high': 0, 'items': []},
            'Post_100': {'low': 0, 'high': 0, 'items': []}
        }
        by_domain = {}
        by_owner = {'buyer': {'low': 0, 'high': 0}, 'target': {'low': 0, 'high': 0}}

        for wi in self.reasoning_store.work_items:
            cost_range = COST_RANGE_VALUES.get(wi.cost_estimate, {'low': 0, 'high': 0})

            # By phase
            if wi.phase in by_phase:
                by_phase[wi.phase]['low'] += cost_range['low']
                by_phase[wi.phase]['high'] += cost_range['high']
                by_phase[wi.phase]['items'].append({
                    'id': wi.finding_id,
                    'title': wi.title,
                    'domain': wi.domain,
                    'cost_low': cost_range['low'],
                    'cost_high': cost_range['high'],
                    'priority': wi.priority
                })

            # By domain
            if wi.domain not in by_domain:
                by_domain[wi.domain] = {'low': 0, 'high': 0, 'count': 0}
            by_domain[wi.domain]['low'] += cost_range['low']
            by_domain[wi.domain]['high'] += cost_range['high']
            by_domain[wi.domain]['count'] += 1

            # By owner
            owner = wi.owner_type if wi.owner_type in by_owner else 'buyer'
            by_owner[owner]['low'] += cost_range['low']
            by_owner[owner]['high'] += cost_range['high']

        total = {
            'low': sum(p['low'] for p in by_phase.values()),
            'high': sum(p['high'] for p in by_phase.values())
        }

        # Identify top cost drivers (sorted by high estimate)
        all_items = []
        for phase in by_phase.values():
            all_items.extend(phase['items'])
        top_drivers = sorted(all_items, key=lambda x: x['cost_high'], reverse=True)[:5]

        return {
            'by_phase': by_phase,
            'by_domain': by_domain,
            'by_owner': by_owner,
            'total': total,
            'top_drivers': top_drivers,
            'work_item_count': len(self.reasoning_store.work_items)
        }

    def _build_system_prompt(self) -> str:
        """Build the system prompt for cost synthesis."""
        return """You are a senior IT due diligence partner synthesizing the cost picture for PE buyers.

YOUR ROLE:
Explain what this integration will cost in practical terms. Be specific about what's driving
the numbers and what could change them. This goes to the investment committee.

TONE:
- Direct and specific
- Acknowledge uncertainty where it exists
- Highlight what the buyer controls vs what's fixed
- Be clear about Day 1 vs discretionary spending

STRUCTURE YOUR NARRATIVE:
1. Lead with the total range and what drives it
2. Explain the phasing - what must happen when
3. Call out the top cost drivers specifically
4. Note key assumptions that underpin the estimates
5. Flag what could change the numbers

EXAMPLES OF GOOD COST NARRATIVE:

"The integration will cost between $4.5M and $8.2M over 18 months, with the majority
front-loaded in Day 1 security and access work.

Three items drive 60% of the cost: PAM implementation ($250K-$500K), ERP rationalization
($1M-$2M), and network redesign ($400K-$800K). The first is non-negotiable for cyber
insurance purposes. The ERP work depends on your platform decision - if you're keeping
both systems, add 40% to the estimate.

Key assumption: We're assuming the target IT team stays through Day 100. If there's
attrition, budget $150K-$300K for backfill and knowledge transfer.

Risk to estimates: Colocation contracts may have early termination penalties. We don't
have visibility into those terms - could add $500K if unfavorable."

Use the write_cost_narrative tool to record your narrative, then complete_cost_synthesis."""

    def _build_user_message(self, cost_data: Dict) -> str:
        """Build the user message with aggregated cost data."""
        # Phase breakdown
        phase_text = "## COST BY PHASE\n"
        for phase, data in cost_data['by_phase'].items():
            phase_text += f"\n### {phase.replace('_', ' ')}\n"
            phase_text += f"Total: ${data['low']:,.0f} - ${data['high']:,.0f}\n"
            if data['items']:
                phase_text += "Items:\n"
                for item in sorted(data['items'], key=lambda x: x['cost_high'], reverse=True)[:5]:
                    phase_text += f"  - {item['title']}: ${item['cost_low']:,.0f} - ${item['cost_high']:,.0f} ({item['domain']})\n"

        # Domain breakdown
        domain_text = "\n## COST BY DOMAIN\n"
        for domain, data in sorted(cost_data['by_domain'].items(), key=lambda x: x[1]['high'], reverse=True):
            domain_text += f"- {domain.replace('_', ' ').title()}: ${data['low']:,.0f} - ${data['high']:,.0f} ({data['count']} items)\n"

        # Owner breakdown
        owner_text = "\n## COST BY OWNER\n"
        for owner, data in cost_data['by_owner'].items():
            owner_text += f"- {owner.title()}: ${data['low']:,.0f} - ${data['high']:,.0f}\n"

        # Top drivers
        drivers_text = "\n## TOP COST DRIVERS\n"
        for i, item in enumerate(cost_data['top_drivers'], 1):
            drivers_text += f"{i}. {item['title']}: ${item['cost_low']:,.0f} - ${item['cost_high']:,.0f}\n"
            drivers_text += f"   Domain: {item['domain']} | Priority: {item['priority']}\n"

        # Total
        total_text = f"\n## TOTAL\n${cost_data['total']['low']:,.0f} - ${cost_data['total']['high']:,.0f}\n"
        total_text += f"Across {cost_data['work_item_count']} work items\n"

        return f"""Generate the cost synthesis narrative for the investment thesis.

Here is the aggregated cost data:

{phase_text}
{domain_text}
{owner_text}
{drivers_text}
{total_text}

Write a compelling cost narrative using write_cost_narrative, then complete_cost_synthesis."""

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
            # Use low temperature for consistent cost narrative output
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=NARRATIVE_TEMPERATURE,  # Low temp for consistent output
                system=system_prompt,
                tools=self.tools,
                messages=self.messages,
                timeout=timeout_seconds  # Add timeout to prevent hanging
            )

            self.metrics.input_tokens += response.usage.input_tokens
            self.metrics.output_tokens += response.usage.output_tokens
            self.metrics.estimated_cost += estimate_cost(
                self.model,
                response.usage.input_tokens,
                response.usage.output_tokens
            )

            return response
        finally:
            # Always release rate limiter
            if self.rate_limiter:
                self.rate_limiter.release()

    def _process_response(self, response: Any, cost_data: Dict):
        """Process the model response."""
        tool_results = []

        for block in response.content:
            if block.type == "text":
                if block.text.strip():
                    self.logger.debug(f"Model text: {block.text[:100]}...")

            elif block.type == "tool_use":
                tool_name = block.name
                tool_input = block.input

                print(f"  Tool: {tool_name}")

                if tool_name == "write_cost_narrative":
                    # Ensure list fields are actually lists (LLM sometimes returns strings)
                    def ensure_list(val):
                        if isinstance(val, str):
                            return [val] if val.strip() else []
                        if isinstance(val, list):
                            return val
                        return []

                    # Create the cost narrative
                    cost_narrative = CostNarrative(
                        total_range=cost_data['total'],
                        by_phase={k: {'low': v['low'], 'high': v['high'], 'count': len(v['items'])}
                                  for k, v in cost_data['by_phase'].items()},
                        by_domain=cost_data['by_domain'],
                        by_owner=cost_data['by_owner'],
                        executive_summary=tool_input['executive_summary'],
                        key_drivers=ensure_list(tool_input.get('key_drivers', [])),
                        assumptions=ensure_list(tool_input.get('assumptions', [])),
                        risks_to_estimates=ensure_list(tool_input.get('risks_to_estimates', []))
                    )
                    self.narrative_store.set_cost_narrative(cost_narrative)
                    result = {"status": "success", "message": "Cost narrative recorded."}

                elif tool_name == "complete_cost_synthesis":
                    result = {"status": "complete", "message": tool_input['total_range_summary']}
                    self.synthesis_complete = True

                else:
                    result = {"status": "error", "message": f"Unknown tool: {tool_name}"}

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps(result)
                })

        # Add to messages
        self.messages.append({"role": "assistant", "content": response.content})
        if tool_results:
            self.messages.append({"role": "user", "content": tool_results})
