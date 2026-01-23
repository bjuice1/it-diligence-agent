"""
LLM-Powered Reasoning Engine

This module provides the ACTUAL reasoning capability - using an LLM to:
1. Interpret facts (what does this mean?)
2. Derive implications (what does this imply for the deal?)
3. Identify activities (what needs to be done?)
4. Estimate costs (based on the specific situation)

The rule-based engine (reasoning_engine.py) provides:
- Structure and templates
- Cost anchors and formulas
- Output formatting

This module provides:
- The actual "thinking" about facts
- Context-aware interpretation
- Novel situation handling

Cost model:
- Batch facts together (one call per analysis, not per fact)
- Cache reasoning for unchanged facts
- Only re-reason when facts change
"""

import json
import hashlib
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


# =============================================================================
# REASONING PROMPTS
# =============================================================================

FACT_INTERPRETATION_PROMPT = """You are an expert IT M&A advisor analyzing due diligence findings.

## Deal Context
Deal Type: {deal_type}
{deal_context}

## Your Task
Analyze these extracted facts and determine:
1. What each fact MEANS for the deal
2. What DEPENDENCIES or RISKS it reveals
3. What ACTIVITIES would be required

## Facts to Analyze
{facts_formatted}

## Output Format
For each significant finding, provide:
```json
{{
    "considerations": [
        {{
            "fact_ids": ["F-001", "F-002"],  // Which facts support this
            "workstream": "identity|email|infrastructure|network|security|applications|service_desk",
            "finding": "What we found (1 sentence)",
            "implication": "What it means for the deal (1-2 sentences)",
            "criticality": "critical|high|medium|low",
            "activities_needed": [
                {{
                    "name": "Activity name",
                    "description": "What needs to be done",
                    "why_needed": "Because [fact], we need to [action]",
                    "requires_tsa": true/false,
                    "tsa_duration_months": [min, max] or null
                }}
            ]
        }}
    ],
    "quantitative_context": {{
        "user_count": number or null,
        "app_count": number or null,
        "site_count": number or null,
        "server_count": number or null
    }},
    "key_risks": [
        "Risk 1",
        "Risk 2"
    ],
    "information_gaps": [
        "What we don't know but need to"
    ]
}}
```

Focus on:
- Parent/shared service dependencies (for carveouts)
- Technology mismatches with buyer (for acquisitions)
- Day-1 critical services
- Technical debt and risks
- TSA requirements

Be specific. Don't list generic activities - derive them from the actual facts.
"""


ACTIVITY_COSTING_PROMPT = """You are an expert IT M&A advisor estimating costs for separation/integration activities.

## Context
Deal Type: {deal_type}
User Count: {user_count:,}
{additional_context}

## Activities to Estimate
{activities_formatted}

## Your Task
For each activity, provide a cost estimate with reasoning:

```json
{{
    "activity_estimates": [
        {{
            "activity_name": "Name from input",
            "cost_range": [low, high],
            "timeline_months": [min, max],
            "cost_reasoning": "Why this cost range (reference market rates, complexity factors)",
            "assumptions": ["Assumption 1", "Assumption 2"],
            "cost_drivers": ["What could push cost higher", "What could reduce cost"]
        }}
    ],
    "total_range": [total_low, total_high],
    "confidence": "high|medium|low",
    "confidence_reasoning": "Why this confidence level"
}}
```

Use these market anchors as starting points:
- User migration: $15-40 per user
- Application SSO integration: $2,000-8,000 per app
- Email migration: $20-50 per mailbox
- Infrastructure migration (VM): $500-2,000 per server
- Network separation: $50,000-200,000 per site
- Identity platform standup: $75,000-200,000 base

Adjust based on:
- Complexity (legacy systems, custom integrations)
- Scale (economies or diseconomies of scale)
- Industry (regulated industries add 20-50%)
- Timeline pressure (rushed = higher cost)
"""


# =============================================================================
# LLM REASONING CLASS
# =============================================================================

@dataclass
class ReasonedConsideration:
    """A consideration derived by LLM reasoning."""
    fact_ids: List[str]
    workstream: str
    finding: str
    implication: str
    criticality: str
    activities_needed: List[Dict]


@dataclass
class ReasonedOutput:
    """Output from LLM reasoning."""
    considerations: List[ReasonedConsideration]
    quantitative_context: Dict[str, Any]
    key_risks: List[str]
    information_gaps: List[str]

    # Metadata
    facts_analyzed: int
    reasoning_hash: str  # For cache invalidation
    llm_cost: float
    timestamp: str


class LLMReasoningEngine:
    """
    LLM-powered reasoning engine.

    Uses Claude to actually THINK about facts and derive implications,
    rather than just pattern matching.
    """

    def __init__(self, model: str = "claude-sonnet-4-20250514"):
        """
        Initialize the reasoning engine.

        Args:
            model: Which Claude model to use
                   - claude-sonnet-4-20250514: Good balance of speed/quality
                   - claude-3-5-haiku-20241022: Faster, cheaper, slightly lower quality
        """
        self.model = model
        self._cache: Dict[str, ReasonedOutput] = {}

    def reason_about_facts(
        self,
        facts: List[Dict],
        deal_type: str,
        deal_context: Optional[str] = None,
        use_cache: bool = True,
    ) -> ReasonedOutput:
        """
        Use LLM to reason about facts and derive considerations.

        This is the core reasoning function that replaces pattern matching.

        Args:
            facts: List of facts from FactStore
            deal_type: "carveout", "acquisition", etc.
            deal_context: Additional context string
            use_cache: Whether to use cached reasoning for unchanged facts

        Returns:
            ReasonedOutput with considerations, activities, risks
        """
        # Compute hash of inputs for caching
        input_hash = self._compute_hash(facts, deal_type, deal_context)

        if use_cache and input_hash in self._cache:
            logger.info("Using cached reasoning")
            return self._cache[input_hash]

        # Format facts for prompt
        facts_formatted = self._format_facts(facts)

        # Build prompt
        prompt = FACT_INTERPRETATION_PROMPT.format(
            deal_type=deal_type,
            deal_context=deal_context or "No additional context provided",
            facts_formatted=facts_formatted,
        )

        # Call LLM
        response, cost = self._call_llm(prompt)

        # Parse response
        output = self._parse_reasoning_response(response, facts, input_hash, cost)

        # Cache result
        if use_cache:
            self._cache[input_hash] = output

        return output

    def estimate_costs(
        self,
        activities: List[Dict],
        deal_type: str,
        user_count: int,
        additional_context: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Use LLM to estimate costs for derived activities.

        Args:
            activities: List of activities from reasoning
            deal_type: Deal type
            user_count: Number of users
            additional_context: Any additional context

        Returns:
            Dict with cost estimates per activity
        """
        # Format activities
        activities_formatted = "\n".join([
            f"- {a['name']}: {a['description']}\n  Why needed: {a['why_needed']}"
            for a in activities
        ])

        prompt = ACTIVITY_COSTING_PROMPT.format(
            deal_type=deal_type,
            user_count=user_count,
            additional_context=additional_context or "",
            activities_formatted=activities_formatted,
        )

        response, cost = self._call_llm(prompt)

        # Parse response
        try:
            # Extract JSON from response
            import re
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                result = json.loads(json_match.group())
                result['llm_cost'] = cost
                return result
        except Exception as e:
            logger.error(f"Failed to parse cost response: {e}")

        return {"error": "Failed to parse response", "llm_cost": cost}

    def _call_llm(self, prompt: str) -> Tuple[str, float]:
        """Call the LLM and return response + cost."""
        import anthropic
        import os

        client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

        response = client.messages.create(
            model=self.model,
            max_tokens=4000,
            messages=[{"role": "user", "content": prompt}]
        )

        # Calculate cost
        input_tokens = response.usage.input_tokens
        output_tokens = response.usage.output_tokens

        # Pricing (as of 2024)
        if "sonnet" in self.model:
            cost = (input_tokens * 0.003 + output_tokens * 0.015) / 1000
        elif "haiku" in self.model:
            cost = (input_tokens * 0.00025 + output_tokens * 0.00125) / 1000
        else:
            cost = (input_tokens * 0.015 + output_tokens * 0.075) / 1000  # Opus pricing

        return response.content[0].text, cost

    def _format_facts(self, facts: List[Dict]) -> str:
        """Format facts for the prompt."""
        lines = []
        for f in facts:
            fact_id = f.get('fact_id', 'N/A')
            content = f.get('content', '')
            category = f.get('category', '')
            entity = f.get('entity', 'target')

            lines.append(f"[{fact_id}] ({entity.upper()}) {category}: {content}")

        return "\n".join(lines)

    def _compute_hash(self, facts: List[Dict], deal_type: str, context: Optional[str]) -> str:
        """Compute hash of inputs for caching."""
        content = json.dumps({
            'facts': sorted([f.get('fact_id', '') for f in facts]),
            'deal_type': deal_type,
            'context': context,
        }, sort_keys=True)
        return hashlib.md5(content.encode()).hexdigest()

    def _parse_reasoning_response(
        self,
        response: str,
        facts: List[Dict],
        input_hash: str,
        cost: float,
    ) -> ReasonedOutput:
        """Parse LLM response into structured output."""
        try:
            import re
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                data = json.loads(json_match.group())

                considerations = [
                    ReasonedConsideration(
                        fact_ids=c.get('fact_ids', []),
                        workstream=c.get('workstream', 'general'),
                        finding=c.get('finding', ''),
                        implication=c.get('implication', ''),
                        criticality=c.get('criticality', 'medium'),
                        activities_needed=c.get('activities_needed', []),
                    )
                    for c in data.get('considerations', [])
                ]

                return ReasonedOutput(
                    considerations=considerations,
                    quantitative_context=data.get('quantitative_context', {}),
                    key_risks=data.get('key_risks', []),
                    information_gaps=data.get('information_gaps', []),
                    facts_analyzed=len(facts),
                    reasoning_hash=input_hash,
                    llm_cost=cost,
                    timestamp=datetime.now().isoformat(),
                )

        except Exception as e:
            logger.error(f"Failed to parse reasoning response: {e}")

        # Return empty output on parse failure
        return ReasonedOutput(
            considerations=[],
            quantitative_context={},
            key_risks=["Parse error - manual review needed"],
            information_gaps=[],
            facts_analyzed=len(facts),
            reasoning_hash=input_hash,
            llm_cost=cost,
            timestamp=datetime.now().isoformat(),
        )


# =============================================================================
# HYBRID REASONING (LLM + Rules)
# =============================================================================

def run_hybrid_reasoning(
    fact_store: Any,
    deal_type: str,
    meeting_notes: Optional[str] = None,
    use_llm: bool = True,
    model: str = "claude-sonnet-4-20250514",
) -> Dict[str, Any]:
    """
    Run hybrid reasoning: LLM for interpretation, rules for structure/costing.

    This combines:
    - LLM reasoning: Interprets facts, derives considerations
    - Rule-based costing: Applies market anchors, scales by quantity
    - Rule-based structure: Formats output consistently

    Args:
        fact_store: FactStore with extracted facts
        deal_type: Deal type
        meeting_notes: Optional additional context
        use_llm: Whether to use LLM (False = pure rule-based fallback)
        model: Which model to use for LLM reasoning

    Returns:
        Complete reasoning output
    """
    from tools_v2.reasoning_integration import factstore_to_reasoning_format

    # Convert facts
    facts = factstore_to_reasoning_format(fact_store)

    total_cost = 0.0

    if use_llm:
        # Use LLM for actual reasoning
        engine = LLMReasoningEngine(model=model)

        # Step 1: Reason about facts
        reasoned = engine.reason_about_facts(
            facts=facts,
            deal_type=deal_type,
            deal_context=meeting_notes,
        )
        total_cost += reasoned.llm_cost

        # Step 2: Collect all activities from reasoning
        all_activities = []
        for consideration in reasoned.considerations:
            for activity in consideration.activities_needed:
                activity['workstream'] = consideration.workstream
                activity['triggered_by'] = consideration.fact_ids
                all_activities.append(activity)

        # Step 3: Estimate costs for activities
        user_count = reasoned.quantitative_context.get('user_count') or 1000

        if all_activities:
            cost_estimates = engine.estimate_costs(
                activities=all_activities,
                deal_type=deal_type,
                user_count=user_count,
                additional_context=meeting_notes,
            )
            total_cost += cost_estimates.get('llm_cost', 0)
        else:
            cost_estimates = {"activity_estimates": [], "total_range": [0, 0]}

        # Build output
        return {
            "deal_type": deal_type,
            "reasoning_method": "llm",
            "model": model,
            "considerations": [
                {
                    "fact_ids": c.fact_ids,
                    "workstream": c.workstream,
                    "finding": c.finding,
                    "implication": c.implication,
                    "criticality": c.criticality,
                }
                for c in reasoned.considerations
            ],
            "activities": cost_estimates.get("activity_estimates", []),
            "total_cost_range": cost_estimates.get("total_range", [0, 0]),
            "key_risks": reasoned.key_risks,
            "information_gaps": reasoned.information_gaps,
            "quantitative_context": reasoned.quantitative_context,
            "llm_cost": total_cost,
            "facts_analyzed": len(facts),
        }

    else:
        # Fall back to pure rule-based
        from tools_v2.reasoning_integration import run_reasoning_analysis
        result = run_reasoning_analysis(fact_store, deal_type, meeting_notes)
        result["reasoning_method"] = "rule_based"
        result["llm_cost"] = 0.0
        return result


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    'LLMReasoningEngine',
    'ReasonedConsideration',
    'ReasonedOutput',
    'run_hybrid_reasoning',
]
