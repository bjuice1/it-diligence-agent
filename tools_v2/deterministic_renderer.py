"""
Deterministic Renderer for IT Due Diligence Outputs

This module provides PURELY DETERMINISTIC rendering from JSON data.
No LLM calls are made during rendering - all output is computed from
the structured data in FactStore and ReasoningStore.

ARCHITECTURE:
  Stage A (Extraction): LLM extracts facts/risks/work items → JSON stores
  Stage B (Rendering): This module renders JSON → HTML/Markdown/Reports

This ensures consistency: same JSON input → same output, every time.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)


# =============================================================================
# DETERMINISTIC OUTPUT TEMPLATES
# =============================================================================

EXECUTIVE_SUMMARY_TEMPLATE = """
# {target_name} - IT Due Diligence Executive Summary

**Generated**: {timestamp}
**Complexity**: {complexity_label}
**Estimated Cost**: {cost_range}

## Bottom Line

{bottom_line}

## Key Metrics

| Metric | Count |
|--------|-------|
| Facts Extracted | {fact_count} |
| Information Gaps | {gap_count} |
| Risks Identified | {risk_count} |
| Work Items | {work_item_count} |

## Key Systems Identified

{key_systems_list}

## Top Risks

{top_risks_list}

## Cost Breakdown by Phase

| Phase | Cost Range | Work Items |
|-------|------------|------------|
{cost_by_phase_rows}

## Complexity Drivers

{complexity_drivers}

---
*Generated deterministically from structured data. No LLM interpretation in this output.*
"""

DOMAIN_SLIDE_TEMPLATE = """
## {domain_title}

**Facts**: {fact_count} | **Gaps**: {gap_count} | **Risks**: {risk_count} | **Work Items**: {work_item_count}

### Key Findings

{findings_list}

### Risks

{risks_list}

### Work Items

{work_items_list}

### Information Gaps

{gaps_list}
"""


@dataclass
class DeterministicOutput:
    """Container for deterministic output."""
    format: str  # "markdown" | "json" | "html"
    content: str
    metadata: Dict[str, Any]


def render_executive_summary_markdown(
    fact_store: Any,
    reasoning_store: Any,
    complexity_assessment: Dict[str, Any],
    cost_summary: Dict[str, Any],
    target_name: str = "Target Company"
) -> DeterministicOutput:
    """
    Render executive summary as Markdown - NO LLM CALLS.

    All text is computed from structured data using templates.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    # Key systems from facts
    key_systems = []
    for fact in list(fact_store.facts)[:10]:  # Top 10 facts
        if hasattr(fact, 'category') and fact.category in ['erp', 'hosting', 'cloud', 'crm']:
            key_systems.append(f"- **{fact.item}** ({fact.category})")

    key_systems_list = "\n".join(key_systems) if key_systems else "- No key systems identified"

    # Top risks
    top_risks = []
    risks = sorted(
        [r for r in reasoning_store.risks],
        key=lambda r: 0 if r.severity == 'critical' else (1 if r.severity == 'high' else 2)
    )[:5]
    for risk in risks:
        top_risks.append(f"- **[{risk.severity.upper()}]** {risk.title}")

    top_risks_list = "\n".join(top_risks) if top_risks else "- No critical/high risks identified"

    # Cost by phase rows
    cost_rows = []
    for phase, data in cost_summary.get('by_phase', {}).items():
        if data.get('count', 0) > 0:
            cost_rows.append(
                f"| {data.get('label', phase)} | {data.get('formatted', 'TBD')} | {data.get('count', 0)} |"
            )
    cost_by_phase_rows = "\n".join(cost_rows) if cost_rows else "| N/A | N/A | 0 |"

    # Complexity drivers
    drivers = complexity_assessment.get('key_drivers', [])
    complexity_drivers = "\n".join([f"- {d}" for d in drivers]) if drivers else "- No major complexity drivers"

    # Fill template
    content = EXECUTIVE_SUMMARY_TEMPLATE.format(
        target_name=target_name,
        timestamp=timestamp,
        complexity_label=complexity_assessment.get('label', 'Unknown'),
        cost_range=cost_summary.get('total', {}).get('formatted', 'TBD'),
        bottom_line=complexity_assessment.get('bottom_line', 'Assessment pending.'),
        fact_count=len(list(fact_store.facts)),
        gap_count=len(list(fact_store.gaps)),
        risk_count=len(list(reasoning_store.risks)),
        work_item_count=len(list(reasoning_store.work_items)),
        key_systems_list=key_systems_list,
        top_risks_list=top_risks_list,
        cost_by_phase_rows=cost_by_phase_rows,
        complexity_drivers=complexity_drivers
    )

    return DeterministicOutput(
        format="markdown",
        content=content,
        metadata={
            "rendered_at": timestamp,
            "renderer": "deterministic_renderer",
            "llm_calls": 0
        }
    )


def render_findings_json(
    fact_store: Any,
    reasoning_store: Any,
    complexity_assessment: Dict[str, Any],
    cost_summary: Dict[str, Any],
    target_name: str = "Target Company"
) -> DeterministicOutput:
    """
    Render all findings as structured JSON - NO LLM CALLS.

    This is the canonical JSON export that can be used for:
    - Regression testing
    - External integrations
    - Audit trails
    """
    timestamp = datetime.now().isoformat()

    output = {
        "meta": {
            "target_name": target_name,
            "generated_at": timestamp,
            "renderer": "deterministic_renderer",
            "version": "2.1"
        },
        "summary": {
            "fact_count": len(list(fact_store.facts)),
            "gap_count": len(list(fact_store.gaps)),
            "risk_count": len(list(reasoning_store.risks)),
            "work_item_count": len(list(reasoning_store.work_items))
        },
        "complexity": complexity_assessment,
        "costs": cost_summary,
        "facts": [
            {
                "id": f.fact_id,
                "domain": f.domain,
                "category": f.category,
                "item": f.item,
                "status": f.status,
                "details": f.details,
                "entity": getattr(f, 'entity', 'target')
            }
            for f in fact_store.facts
        ],
        "gaps": [
            {
                "id": g.gap_id,
                "domain": g.domain,
                "description": g.description,
                "importance": g.importance
            }
            for g in fact_store.gaps
        ],
        "risks": [
            {
                "id": r.finding_id,
                "domain": r.domain,
                "title": r.title,
                "description": r.description,
                "severity": r.severity,
                "based_on_facts": r.based_on_facts
            }
            for r in reasoning_store.risks
        ],
        "work_items": [
            {
                "id": wi.finding_id,
                "domain": wi.domain,
                "title": wi.title,
                "description": wi.description,
                "phase": wi.phase,
                "cost_estimate": wi.cost_estimate,
                "owner_type": wi.owner_type,
                "triggered_by": wi.triggered_by
            }
            for wi in reasoning_store.work_items
        ]
    }

    return DeterministicOutput(
        format="json",
        content=json.dumps(output, indent=2),
        metadata={
            "rendered_at": timestamp,
            "renderer": "deterministic_renderer",
            "llm_calls": 0
        }
    )


def render_domain_slides_markdown(
    fact_store: Any,
    reasoning_store: Any,
    domains: List[str] = None
) -> Dict[str, DeterministicOutput]:
    """
    Render per-domain slides as Markdown - NO LLM CALLS.

    Returns a dict of domain -> DeterministicOutput.
    """
    if domains is None:
        domains = ['infrastructure', 'network', 'cybersecurity', 'applications', 'identity_access', 'organization']

    domain_titles = {
        'infrastructure': 'Infrastructure',
        'network': 'Network',
        'cybersecurity': 'Cybersecurity',
        'applications': 'Applications',
        'identity_access': 'Identity & Access',
        'organization': 'IT Organization'
    }

    outputs = {}

    for domain in domains:
        # Filter by domain
        domain_facts = [f for f in fact_store.facts if f.domain == domain]
        domain_gaps = [g for g in fact_store.gaps if g.domain == domain]
        domain_risks = [r for r in reasoning_store.risks if r.domain == domain]
        domain_wis = [wi for wi in reasoning_store.work_items if wi.domain == domain]

        # Build findings list
        findings = [f"- {f.item} ({f.category})" for f in domain_facts[:10]]
        findings_list = "\n".join(findings) if findings else "- No key findings"

        # Build risks list
        risks = [f"- **[{r.severity.upper()}]** {r.title}" for r in domain_risks]
        risks_list = "\n".join(risks) if risks else "- No risks identified"

        # Build work items list
        wis = [f"- [{wi.phase}] {wi.title} ({wi.cost_estimate})" for wi in domain_wis]
        work_items_list = "\n".join(wis) if wis else "- No work items"

        # Build gaps list
        gaps = [f"- [{g.importance.upper()}] {g.description}" for g in domain_gaps]
        gaps_list = "\n".join(gaps) if gaps else "- No information gaps"

        content = DOMAIN_SLIDE_TEMPLATE.format(
            domain_title=domain_titles.get(domain, domain),
            fact_count=len(domain_facts),
            gap_count=len(domain_gaps),
            risk_count=len(domain_risks),
            work_item_count=len(domain_wis),
            findings_list=findings_list,
            risks_list=risks_list,
            work_items_list=work_items_list,
            gaps_list=gaps_list
        )

        outputs[domain] = DeterministicOutput(
            format="markdown",
            content=content,
            metadata={
                "domain": domain,
                "renderer": "deterministic_renderer",
                "llm_calls": 0
            }
        )

    return outputs


def validate_deterministic_output(output: DeterministicOutput) -> bool:
    """
    Validate that output was generated deterministically.

    Checks the metadata to ensure no LLM calls were made.
    """
    return output.metadata.get("llm_calls", -1) == 0
