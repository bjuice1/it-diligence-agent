"""
Narrative Synthesis Prompt (v2 Architecture)

Transforms domain findings and function stories into a cohesive executive narrative.
This is the "story layer" that makes analysis IC-ready.

Output Structure:
1. Executive Summary (5-7 bullets)
2. How the IT Organization is Built (2-3 paragraphs)
3. Team-by-Team Story (function stories)
4. M&A Lens: Day-1 + TSA + Separation
5. Benchmarks & Operating Posture
6. Risks and Synergies Tables
"""

from typing import Dict, List, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime


# =============================================================================
# NARRATIVE OUTPUT STRUCTURE
# =============================================================================

@dataclass
class ExecutiveNarrative:
    """The complete executive narrative output."""
    company_name: str
    deal_type: str

    # Section 1: Executive Summary
    executive_summary: List[str]  # 5-7 bullets

    # Section 2: Organization Structure
    org_structure_narrative: str  # 2-3 paragraphs

    # Section 3: Team Stories
    team_stories: List[Dict]  # Function stories in order

    # Section 4: M&A Lens
    mna_lens_section: Dict[str, Any]  # TSA, Day-1, Separation

    # Section 5: Benchmarks
    benchmark_statements: List[str]  # 4-6 statements

    # Section 6: Tables
    risks_table: List[Dict]  # Risk rows
    synergies_table: List[Dict]  # Synergy rows

    # Metadata
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    version: str = "1.0"

    def to_dict(self) -> Dict:
        return asdict(self)

    def to_markdown(self) -> str:
        """Render the full narrative as markdown."""
        md = f"# IT Operating Model Narrative ({self.company_name})\n\n"

        # Section 1: Executive Summary
        md += "## 1) Executive Summary\n\n"
        for bullet in self.executive_summary:
            md += f"- {bullet}\n"
        md += "\n"

        # Section 2: Organization Structure
        md += "## 2) How the IT Organization is Built\n\n"
        md += self.org_structure_narrative + "\n\n"

        # Section 3: Team Stories
        md += "## 3) Team-by-Team Story\n\n"
        for story in self.team_stories:
            md += f"### {story.get('function_name', 'Unknown')}\n\n"
            md += f"**What they do day-to-day**: {story.get('day_to_day', '')}\n\n"
            md += "**What they likely do well**:\n"
            for s in story.get('strengths', []):
                md += f"- {s}\n"
            md += "\n**Where they're likely constrained**:\n"
            for c in story.get('constraints', []):
                md += f"- {c}\n"
            md += "\n**Key dependencies & handoffs**:\n"
            md += f"- *Upstream*: {', '.join(story.get('upstream_dependencies', []))}\n"
            md += f"- *Downstream*: {', '.join(story.get('downstream_dependents', []))}\n"
            md += f"\n**M&A Implication**: {story.get('mna_implication', '')}\n\n"

        # Section 4: M&A Lens
        md += "## 4) M&A Lens: Day-1 + TSA + Separation\n\n"
        mna = self.mna_lens_section

        if mna.get('tsa_exposed_functions'):
            md += "### TSA-Exposed Functions\n"
            for func in mna['tsa_exposed_functions']:
                md += f"- {func}\n"
            md += "\n"

        if mna.get('day_1_requirements'):
            md += "### Day-1 Requirements\n"
            for req in mna['day_1_requirements']:
                md += f"- {req}\n"
            md += "\n"

        if mna.get('separation_considerations'):
            md += "### Separation Considerations\n"
            for consideration in mna['separation_considerations']:
                md += f"- {consideration}\n"
            md += "\n"

        # Section 5: Benchmarks
        md += "## 5) Benchmarks & Operating Posture\n\n"
        for statement in self.benchmark_statements:
            md += f"- {statement}\n"
        md += "\n"

        # Section 6: Tables
        md += "## 6) Risks and Synergies\n\n"

        md += "### Risks\n\n"
        md += "| Risk | Why it matters | Likely impact | Mitigation |\n"
        md += "|------|----------------|---------------|------------|\n"
        for risk in self.risks_table:
            md += f"| {risk.get('risk', '')} | {risk.get('why_it_matters', '')} | {risk.get('likely_impact', '')} | {risk.get('mitigation', '')} |\n"
        md += "\n"

        md += "### Synergies / Opportunities\n\n"
        md += "| Opportunity | Why it matters | Value mechanism | First step |\n"
        md += "|-------------|----------------|-----------------|------------|\n"
        for syn in self.synergies_table:
            md += f"| {syn.get('opportunity', '')} | {syn.get('why_it_matters', '')} | {syn.get('value_mechanism', '')} | {syn.get('first_step', '')} |\n"

        return md


# =============================================================================
# SYNTHESIS PROMPT
# =============================================================================

NARRATIVE_SYNTHESIS_PROMPT = """You are an IT diligence narrative writer for a Private Equity M&A deal.
Your job is to convert structured findings into a cohesive, client-ready narrative.

## RULES

1. **Only state as FACT what is explicitly in the inputs.** If you infer, label it as "Inference:" and keep it reasonable.
2. **Use a consulting tone**: clear, decisive, not fluffy, not academic.
3. **Tie observations to M&A implications**: Day-1 continuity, TSA risks, separation complexity, synergy opportunities, and cost drivers.
4. **If there are citations** (e.g., F-APP-001), keep them attached to the statements they support.
5. **Output must follow the exact structure** below - no extra sections.

## DEAL CONTEXT

{deal_context}

## INPUT: DOMAIN FINDINGS

{domain_findings}

## INPUT: FUNCTION STORIES

{function_stories}

## INPUT: FACTS INVENTORY SUMMARY

{facts_summary}

## REQUIRED OUTPUT STRUCTURE

Generate a narrative with these EXACT sections:

### 1) Executive Summary (5-7 bullets)

Cover:
- Org shape and operating posture (lean vs. layered, run vs. change heavy)
- Where cost/headcount is concentrated and why that matters
- 3-5 key risks (prioritized by deal impact)
- 3-5 key synergy opportunities (if acquisition) or TSA considerations (if carveout)

Format: Bulleted list, 5-7 items total. Each bullet should be 1-2 sentences max.

### 2) How the IT Organization is Built (2-3 paragraphs)

Write prose describing:
- Whether the org is lean vs. layered
- Whether it feels "run/operate" heavy vs "change/project" heavy
- What this implies about business model and CapEx/project intensity
- Key observations about outsourcing vs in-house capability

Format: 2-3 narrative paragraphs. No bullets. Consulting tone.

### 3) Team-by-Team Story

For EACH function identified in the input, write:
- **What they do day-to-day**: [2-3 sentences]
- **What they likely do well**: [1-2 strengths]
- **Where they're likely constrained**: [1-2 risks/bottlenecks]
- **Key dependencies**: Upstream and downstream
- **M&A Implication**: [1-2 sentences on Day-1/TSA/separation relevance]

Cover ALL functions from the function_stories input. Do not skip any.

### 4) M&A Lens: Day-1 + TSA + Separation

Based on deal type ({deal_type}), provide:

**TSA-Exposed Functions**: List functions likely requiring transition services
**Day-1 Requirements**: What MUST work on Day 1 for business continuity
**Separation Considerations**: 5-8 action-oriented bullets for the deal team

For carveouts, emphasize TSA and separation.
For acquisitions, emphasize Day-1 and integration.

### 5) Benchmarks & Operating Posture (4-6 statements)

Provide directional benchmark statements WITHOUT using external data.
Format examples:
- "Relative concentration in Applications (35% of IT) suggests project intensity..."
- "Outsourcing at 40% in Infrastructure implies TSA complexity for..."
- "The IT-to-employee ratio appears lean, indicating..."

ALL inferences must be labeled: "Inference: [reasoning]"

### 6) Risks and Synergies Tables

**Risks Table** (minimum 5 rows):
| Risk | Why it matters | Likely impact | Mitigation |

**Synergies Table** (minimum 3 rows for acquisitions, or TSA Considerations for carveouts):
| Opportunity | Why it matters | Value mechanism | First step |

Populate ALL columns. Do not leave cells empty.

## QUALITY CHECKLIST

Before finalizing, verify:
- [ ] Executive Summary has exactly 5-7 bullets
- [ ] Organization narrative is 2-3 paragraphs (prose, not bullets)
- [ ] ALL functions from input are covered in Team Stories
- [ ] M&A Lens section has at least 5 separation considerations
- [ ] Benchmark statements are directional (no fabricated external stats)
- [ ] Risks table has at least 5 rows with all columns populated
- [ ] Synergies table has at least 3 rows with all columns populated
- [ ] All inferences are labeled
- [ ] Citations are preserved where present
"""


# =============================================================================
# DEAL-TYPE SPECIFIC PROMPTS
# =============================================================================

DEAL_TYPE_EMPHASIS = {
    "acquisition": {
        "primary_lens": ["synergy_opportunity", "day_1_continuity"],
        "key_question": "How do we integrate?",
        "section_4_focus": "Integration and synergy realization",
        "table_6_focus": "Synergies table should emphasize value creation opportunities"
    },
    "carveout": {
        "primary_lens": ["tsa_exposure", "separation_complexity"],
        "key_question": "How do we stand alone?",
        "section_4_focus": "TSA requirements and standalone readiness",
        "table_6_focus": "Focus on TSA services inventory and exit complexity"
    },
    "divestiture": {
        "primary_lens": ["separation_complexity", "cost_driver"],
        "key_question": "How do we cleanly separate?",
        "section_4_focus": "Clean separation with minimal RemainCo disruption",
        "table_6_focus": "Focus on separation risks and data entanglement"
    }
}


# =============================================================================
# SECTION-SPECIFIC PROMPTS
# =============================================================================

EXECUTIVE_SUMMARY_PROMPT = """
Generate 5-7 executive summary bullets for {company_name} ({deal_type}).

Based on:
- Total IT headcount: {total_headcount}
- IT cost: {total_cost}
- Key risks: {key_risks}
- Key opportunities: {key_opportunities}
- Deal type implications: {deal_implications}

Format: Each bullet is 1-2 sentences. Cover org shape, cost concentration, top risks, top opportunities.
"""

ORG_STRUCTURE_PROMPT = """
Write 2-3 paragraphs describing how the IT organization is built.

Evidence:
- Team breakdown: {team_breakdown}
- Outsourcing percentage: {outsourcing_pct}
- Run vs change split: {run_change_split}

Address:
1. Lean vs layered (spans of control, hierarchy depth)
2. Run/operate vs change/project orientation
3. What this implies for the business model
4. Key observations about in-house vs outsourced capability

Tone: Consulting prose. Decisive. No hedging.
"""

MNA_LENS_PROMPT = """
Generate the M&A Lens section for a {deal_type}.

Key question: {key_question}

Based on findings:
- Day-1 critical functions: {day_1_functions}
- TSA-likely functions: {tsa_functions}
- Separation complexity signals: {separation_signals}

Generate:
1. TSA-Exposed Functions list
2. Day-1 Requirements list
3. 5-8 Separation Considerations (action-oriented bullets)

For {deal_type}, emphasize: {emphasis}
"""

BENCHMARK_PROMPT = """
Generate 4-6 benchmark statements based on:

- IT headcount: {headcount} ({headcount_pct}% of total employees)
- Applications team: {apps_pct}% of IT
- Infrastructure team: {infra_pct}% of IT
- Outsourcing: {outsourcing_pct}%
- Run vs Change: {run_pct}% run, {change_pct}% change

Rules:
- Use RELATIVE language ("suggests", "indicates", "appears")
- NO external statistics or industry benchmarks
- ALL inferences must be labeled "Inference:"
- Tie to M&A implications where possible
"""

RISKS_TABLE_PROMPT = """
Generate a risks table with at least 5 rows.

Input risks:
{risks}

For each risk, provide:
| Risk | Why it matters | Likely impact | Mitigation |

- "Why it matters" should connect to deal impact
- "Likely impact" should be specific (timeline, cost range, operational)
- "Mitigation" should be actionable

Prioritize by severity: critical first, then high, then medium.
"""

SYNERGIES_TABLE_PROMPT = """
Generate a synergies table with at least 3 rows.

Deal type: {deal_type}
Input opportunities:
{opportunities}

For each opportunity, provide:
| Opportunity | Why it matters | Value mechanism | First step |

Value mechanisms:
- Cost elimination (remove duplicate spend)
- Cost avoidance (prevent future spend)
- Efficiency gain (do more with same)
- Capability gain (acquire what buyer lacks)

"First step" must be actionable and specific.
"""


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_synthesis_prompt(
    deal_context: Dict,
    domain_findings: Dict,
    function_stories: List[Dict],
    facts_summary: str
) -> str:
    """Build the complete synthesis prompt with all inputs."""
    import json

    deal_type = deal_context.get('deal_type', 'acquisition')

    return NARRATIVE_SYNTHESIS_PROMPT.format(
        deal_context=json.dumps(deal_context, indent=2),
        domain_findings=json.dumps(domain_findings, indent=2),
        function_stories=json.dumps(function_stories, indent=2),
        facts_summary=facts_summary,
        deal_type=deal_type
    )


def get_deal_type_emphasis(deal_type: str) -> Dict:
    """Get the emphasis configuration for a deal type."""
    return DEAL_TYPE_EMPHASIS.get(deal_type.lower(), DEAL_TYPE_EMPHASIS["acquisition"])


def validate_narrative(narrative: ExecutiveNarrative) -> Dict[str, Any]:
    """Validate a narrative against L3 expectations."""
    issues = []
    warnings = []

    # Check executive summary
    if len(narrative.executive_summary) < 5:
        issues.append("Executive summary has fewer than 5 bullets")
    elif len(narrative.executive_summary) > 7:
        warnings.append("Executive summary has more than 7 bullets")

    # Check org structure
    if len(narrative.org_structure_narrative) < 200:
        warnings.append("Org structure narrative may be too brief")

    # Check team stories
    if len(narrative.team_stories) == 0:
        issues.append("No team stories provided")

    # Check M&A lens
    mna = narrative.mna_lens_section
    sep_considerations = mna.get('separation_considerations', [])
    if len(sep_considerations) < 5:
        issues.append(f"Only {len(sep_considerations)} separation considerations (need 5+)")

    # Check benchmarks
    if len(narrative.benchmark_statements) < 4:
        issues.append(f"Only {len(narrative.benchmark_statements)} benchmark statements (need 4+)")

    # Check risks table
    if len(narrative.risks_table) < 5:
        issues.append(f"Only {len(narrative.risks_table)} risks (need 5+)")

    # Check synergies table
    if len(narrative.synergies_table) < 3:
        warnings.append(f"Only {len(narrative.synergies_table)} synergies (recommend 3+)")

    # Check for empty cells in tables
    for i, risk in enumerate(narrative.risks_table):
        for col in ['risk', 'why_it_matters', 'likely_impact', 'mitigation']:
            if not risk.get(col):
                issues.append(f"Risk row {i+1} missing '{col}'")

    for i, syn in enumerate(narrative.synergies_table):
        for col in ['opportunity', 'why_it_matters', 'value_mechanism', 'first_step']:
            if not syn.get(col):
                warnings.append(f"Synergy row {i+1} missing '{col}'")

    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "warnings": warnings,
        "score": max(0, 100 - (len(issues) * 15) - (len(warnings) * 5))
    }


def create_empty_narrative(company_name: str, deal_type: str) -> ExecutiveNarrative:
    """Create an empty narrative structure for population."""
    return ExecutiveNarrative(
        company_name=company_name,
        deal_type=deal_type,
        executive_summary=[],
        org_structure_narrative="",
        team_stories=[],
        mna_lens_section={
            "tsa_exposed_functions": [],
            "day_1_requirements": [],
            "separation_considerations": []
        },
        benchmark_statements=[],
        risks_table=[],
        synergies_table=[]
    )


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    'ExecutiveNarrative',
    'NARRATIVE_SYNTHESIS_PROMPT',
    'DEAL_TYPE_EMPHASIS',
    'EXECUTIVE_SUMMARY_PROMPT',
    'ORG_STRUCTURE_PROMPT',
    'MNA_LENS_PROMPT',
    'BENCHMARK_PROMPT',
    'RISKS_TABLE_PROMPT',
    'SYNERGIES_TABLE_PROMPT',
    'get_synthesis_prompt',
    'get_deal_type_emphasis',
    'validate_narrative',
    'create_empty_narrative'
]
