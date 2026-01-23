"""
Deal-Type Narrative Templates

Provides deal-type-specific narrative templates for:
- Acquisitions (synergy + integration focus)
- Carveouts (TSA + separation focus)
- Divestitures (clean separation focus)

Each template extends the base narrative structure with deal-type-specific
sections, emphasis, and output formats.
"""

from typing import Dict, Any, List
from dataclasses import dataclass
from enum import Enum

from .acquisition_narrative_template import (
    ACQUISITION_TEMPLATE,
    ACQUISITION_EMPHASIS,
    get_acquisition_prompt_additions
)
from .carveout_narrative_template import (
    CARVEOUT_TEMPLATE,
    CARVEOUT_EMPHASIS,
    TSA_SERVICES_TEMPLATE,
    ENTANGLEMENT_TEMPLATE,
    STANDALONE_SCORECARD_TEMPLATE,
    get_carveout_prompt_additions
)
from .divestiture_narrative_template import (
    DIVESTITURE_TEMPLATE,
    DIVESTITURE_EMPHASIS,
    get_divestiture_prompt_additions
)


class DealType(Enum):
    """Supported deal types with their characteristics."""
    ACQUISITION = "acquisition"
    CARVEOUT = "carveout"
    DIVESTITURE = "divestiture"

    @classmethod
    def from_string(cls, value: str) -> 'DealType':
        """Convert string to DealType, with flexible matching."""
        normalized = value.lower().replace('_', '').replace('-', '').replace(' ', '')
        mapping = {
            'acquisition': cls.ACQUISITION,
            'bolton': cls.ACQUISITION,
            'platform': cls.ACQUISITION,
            'carveout': cls.CARVEOUT,
            'carve_out': cls.CARVEOUT,
            'spinoff': cls.CARVEOUT,
            'divestiture': cls.DIVESTITURE,
            'sale': cls.DIVESTITURE,
            'disposal': cls.DIVESTITURE
        }
        return mapping.get(normalized, cls.ACQUISITION)


@dataclass
class DealTypeConfig:
    """Configuration for a specific deal type."""
    deal_type: DealType
    primary_lens: List[str]
    key_question: str
    day_1_focus: str
    tsa_emphasis: str  # low, medium, high
    synergy_emphasis: str  # low, medium, high, n/a
    separation_emphasis: str  # low, medium, high
    required_sections: List[str]
    optional_sections: List[str]
    risk_table_columns: List[str]
    opportunity_table_columns: List[str]


# Deal type configurations
DEAL_TYPE_CONFIGS = {
    DealType.ACQUISITION: DealTypeConfig(
        deal_type=DealType.ACQUISITION,
        primary_lens=["synergy_opportunity", "day_1_continuity"],
        key_question="How do we integrate?",
        day_1_focus="Connectivity to buyer systems and operations",
        tsa_emphasis="low",
        synergy_emphasis="high",
        separation_emphasis="low",
        required_sections=[
            "executive_summary",
            "org_structure_narrative",
            "team_stories",
            "mna_lens_section",
            "benchmark_statements",
            "risks_table",
            "synergies_table"
        ],
        optional_sections=[
            "integration_timeline",
            "synergy_quantification"
        ],
        risk_table_columns=["risk", "why_it_matters", "likely_impact", "mitigation"],
        opportunity_table_columns=["opportunity", "why_it_matters", "value_mechanism", "first_step"]
    ),
    DealType.CARVEOUT: DealTypeConfig(
        deal_type=DealType.CARVEOUT,
        primary_lens=["tsa_exposure", "separation_complexity"],
        key_question="How do we stand alone?",
        day_1_focus="Standalone operations without parent dependencies",
        tsa_emphasis="high",
        synergy_emphasis="low",
        separation_emphasis="high",
        required_sections=[
            "executive_summary",
            "org_structure_narrative",
            "team_stories",
            "mna_lens_section",
            "benchmark_statements",
            "risks_table",
            "tsa_services_inventory",
            "entanglement_assessment",
            "standalone_readiness_scorecard"
        ],
        optional_sections=[
            "synergies_table"
        ],
        risk_table_columns=["risk", "why_it_matters", "separation_impact", "mitigation"],
        opportunity_table_columns=["tsa_service", "provider", "duration_estimate", "monthly_cost", "exit_complexity"]
    ),
    DealType.DIVESTITURE: DealTypeConfig(
        deal_type=DealType.DIVESTITURE,
        primary_lens=["separation_complexity", "cost_driver"],
        key_question="How do we cleanly separate?",
        day_1_focus="Minimal disruption to RemainCo operations",
        tsa_emphasis="medium",
        synergy_emphasis="n/a",
        separation_emphasis="high",
        required_sections=[
            "executive_summary",
            "org_structure_narrative",
            "team_stories",
            "mna_lens_section",
            "benchmark_statements",
            "risks_table",
            "separation_considerations"
        ],
        optional_sections=[
            "remainco_impact_assessment",
            "data_separation_plan",
            "contract_assignment_tracker"
        ],
        risk_table_columns=["risk", "why_it_matters", "remainco_impact", "mitigation"],
        opportunity_table_columns=["separation_item", "complexity", "approach", "timeline"]
    )
}


def get_deal_type_config(deal_type: str) -> DealTypeConfig:
    """Get configuration for a deal type."""
    dt = DealType.from_string(deal_type)
    return DEAL_TYPE_CONFIGS[dt]


def get_template_for_deal_type(deal_type: str) -> Dict[str, Any]:
    """
    Get the appropriate narrative template for a deal type.

    Returns a dict with:
    - template: The main prompt template
    - emphasis: Key areas to emphasize
    - additional_sections: Any deal-type-specific sections
    - config: The DealTypeConfig object
    """
    dt = DealType.from_string(deal_type)
    config = DEAL_TYPE_CONFIGS[dt]

    if dt == DealType.ACQUISITION:
        return {
            "template": ACQUISITION_TEMPLATE,
            "emphasis": ACQUISITION_EMPHASIS,
            "additional_sections": {},
            "prompt_additions": get_acquisition_prompt_additions(),
            "config": config
        }
    elif dt == DealType.CARVEOUT:
        return {
            "template": CARVEOUT_TEMPLATE,
            "emphasis": CARVEOUT_EMPHASIS,
            "additional_sections": {
                "tsa_services": TSA_SERVICES_TEMPLATE,
                "entanglement": ENTANGLEMENT_TEMPLATE,
                "standalone_scorecard": STANDALONE_SCORECARD_TEMPLATE
            },
            "prompt_additions": get_carveout_prompt_additions(),
            "config": config
        }
    elif dt == DealType.DIVESTITURE:
        return {
            "template": DIVESTITURE_TEMPLATE,
            "emphasis": DIVESTITURE_EMPHASIS,
            "additional_sections": {},
            "prompt_additions": get_divestiture_prompt_additions(),
            "config": config
        }
    else:
        # Default to acquisition
        return {
            "template": ACQUISITION_TEMPLATE,
            "emphasis": ACQUISITION_EMPHASIS,
            "additional_sections": {},
            "prompt_additions": get_acquisition_prompt_additions(),
            "config": DEAL_TYPE_CONFIGS[DealType.ACQUISITION]
        }


def get_executive_summary_framing(deal_type: str, company_name: str) -> str:
    """Get deal-type-specific executive summary framing."""
    dt = DealType.from_string(deal_type)
    config = DEAL_TYPE_CONFIGS[dt]

    framings = {
        DealType.ACQUISITION: f"""## Executive Summary: {company_name} IT Integration Assessment

This assessment evaluates {company_name}'s IT organization through an **integration lens**,
focusing on synergy opportunities, Day-1 operational continuity, and integration complexity.

**Key Question**: {config.key_question}
**Primary Focus**: {', '.join(config.primary_lens)}
""",
        DealType.CARVEOUT: f"""## Executive Summary: {company_name} IT Carveout Assessment

This assessment evaluates {company_name}'s IT organization through a **separation lens**,
focusing on TSA requirements, standalone readiness, and separation complexity.

**Key Question**: {config.key_question}
**Primary Focus**: {', '.join(config.primary_lens)}
""",
        DealType.DIVESTITURE: f"""## Executive Summary: {company_name} IT Divestiture Assessment

This assessment evaluates {company_name}'s IT organization through a **clean separation lens**,
focusing on RemainCo impact minimization, data separation, and contract assignment.

**Key Question**: {config.key_question}
**Primary Focus**: {', '.join(config.primary_lens)}
"""
    }

    return framings.get(dt, framings[DealType.ACQUISITION])


def validate_narrative_for_deal_type(narrative: Dict, deal_type: str) -> Dict[str, Any]:
    """
    Validate a narrative against deal-type-specific requirements.

    Returns validation results with issues and warnings.
    """
    dt = DealType.from_string(deal_type)
    config = DEAL_TYPE_CONFIGS[dt]

    issues = []
    warnings = []

    # Check required sections
    for section in config.required_sections:
        if section not in narrative or not narrative[section]:
            issues.append(f"Missing required section for {dt.value}: {section}")

    # Deal-type-specific validations
    if dt == DealType.CARVEOUT:
        # Carveout must have TSA inventory
        tsa = narrative.get('tsa_services_inventory', [])
        if len(tsa) < 3:
            issues.append(f"Carveout requires at least 3 TSA services (found {len(tsa)})")

        # Must have entanglement assessment
        entanglement = narrative.get('entanglement_assessment', [])
        if len(entanglement) < 3:
            warnings.append(f"Carveout should have entanglement assessment (found {len(entanglement)} items)")

        # Must have standalone scorecard
        scorecard = narrative.get('standalone_readiness_scorecard', [])
        if len(scorecard) < 5:
            warnings.append(f"Standalone readiness scorecard should cover key capabilities (found {len(scorecard)})")

    elif dt == DealType.ACQUISITION:
        # Acquisition should emphasize synergies
        synergies = narrative.get('synergies_table', [])
        if len(synergies) < 3:
            warnings.append(f"Acquisition should identify at least 3 synergy opportunities (found {len(synergies)})")

        # Check for integration timeline consideration
        mna_lens = narrative.get('mna_lens_section', {})
        if not mna_lens.get('integration_considerations'):
            warnings.append("Acquisition should include integration timeline considerations")

    elif dt == DealType.DIVESTITURE:
        # Divestiture should address RemainCo impact
        mna_lens = narrative.get('mna_lens_section', {})
        sep_considerations = mna_lens.get('separation_considerations', [])

        remainco_mentions = sum(1 for c in sep_considerations if 'remainco' in c.lower() or 'remain' in c.lower())
        if remainco_mentions < 2:
            warnings.append("Divestiture should explicitly address RemainCo impact (minimal mentions found)")

    # Calculate score
    score = 100 - (len(issues) * 15) - (len(warnings) * 5)

    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "warnings": warnings,
        "score": max(0, score),
        "deal_type": dt.value,
        "required_sections_checked": len(config.required_sections)
    }


__all__ = [
    # Enums and configs
    'DealType',
    'DealTypeConfig',
    'DEAL_TYPE_CONFIGS',
    # Factory functions
    'get_deal_type_config',
    'get_template_for_deal_type',
    'get_executive_summary_framing',
    'validate_narrative_for_deal_type',
    # Acquisition
    'ACQUISITION_TEMPLATE',
    'ACQUISITION_EMPHASIS',
    'get_acquisition_prompt_additions',
    # Carveout
    'CARVEOUT_TEMPLATE',
    'CARVEOUT_EMPHASIS',
    'TSA_SERVICES_TEMPLATE',
    'ENTANGLEMENT_TEMPLATE',
    'STANDALONE_SCORECARD_TEMPLATE',
    'get_carveout_prompt_additions',
    # Divestiture
    'DIVESTITURE_TEMPLATE',
    'DIVESTITURE_EMPHASIS',
    'get_divestiture_prompt_additions'
]
