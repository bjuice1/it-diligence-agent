"""
Shared Prompt Components for IT Due Diligence Agents

These components are imported by all domain agents to ensure consistent
anti-hallucination measures and evidence requirements.
"""

from .evidence_requirements import get_evidence_requirements, EVIDENCE_REQUIREMENTS
from .hallucination_guardrails import get_hallucination_guardrails, HALLUCINATION_GUARDRAILS
from .gap_over_guess import get_gap_over_guess, GAP_OVER_GUESS
from .confidence_calibration import get_confidence_calibration, CONFIDENCE_CALIBRATION
from .entity_distinction import ENTITY_DISTINCTION_PROMPT, ENTITY_DISTINCTION_SHORT
from .complexity_signals import (
    COMPLEXITY_SIGNALS,
    INDUSTRY_SIGNALS,
    get_complexity_signals_for_domain,
    get_industry_signals,
    calculate_ai_weight,
    get_signal_prompt_injection
)
from .mna_framing import (
    MNA_LENSES,
    STATEMENT_TYPES,
    MNA_FRAMING_PROMPT_BLOCK,
    get_mna_framing_prompt,
    get_lens_definition,
    get_all_lens_ids,
    get_lens_for_deal_type,
    validate_mna_lens,
    get_statement_type_guidance
)
from .reasoning_quality import get_reasoning_quality_prompt, REASONING_QUALITY_BLOCK
from .function_story_template import (
    FunctionStory,
    FUNCTION_DOMAIN_MAP,
    STRENGTH_SIGNALS,
    CONSTRAINT_SIGNALS,
    DEPENDENCY_MAP,
    get_functions_for_domain,
    get_all_functions,
    get_function_details,
    get_upstream_dependencies,
    get_downstream_dependents,
    detect_strength_signals,
    detect_constraint_signals,
    get_story_prompt,
    get_day1_critical_functions,
    get_tsa_likely_functions
)
from .benchmark_generator import (
    BenchmarkType,
    BenchmarkPattern,
    BENCHMARK_PATTERNS,
    SAFE_LANGUAGE,
    UNSAFE_LANGUAGE,
    generate_benchmarks,
    validate_benchmark_safety,
    analyze_team_concentration,
    analyze_outsourcing,
    analyze_ratios,
    analyze_posture,
    analyze_maturity_signals,
    get_benchmark_mna_context
)
from .function_deep_dive import (
    MaturityLevel,
    FunctionReviewCriteria,
    INFRASTRUCTURE_FUNCTIONS,
    APPLICATIONS_FUNCTIONS,
    ORGANIZATION_FUNCTIONS,
    CYBERSECURITY_FUNCTIONS,
    IDENTITY_FUNCTIONS,
    NETWORK_FUNCTIONS,
    get_function_criteria,
    get_all_criteria,
    assess_function_completeness,
    get_cross_domain_dependencies,
    get_mna_questions,
)
from .strategic_cost_assessment import (
    DealComplexity,
    CompanyProfile,
    DealProfile,
    COST_DRIVER_PATTERNS,
    DEAL_TYPE_CONSIDERATIONS,
    calculate_complexity_score,
    estimate_total_separation_cost,
    identify_cost_drivers,
    generate_strategic_assessment,
    get_strategic_assessment_prompt,
)
from .deal_implications import (
    DealImplication,
    CARVEOUT_IMPLICATIONS,
    ACQUISITION_IMPLICATIONS,
    get_implications_for_deal_type,
    match_facts_to_implications,
    get_implication_prompt_injection,
)
from .industry_application_considerations import (
    INDUSTRY_APPLICATION_CONSIDERATIONS,
    detect_industry_from_text,
    get_industry_considerations,
    get_all_industries,
    inject_industry_into_discovery_prompt,
    assess_industry_application_gaps,
    get_industry_prompt_summary,
)


def get_all_shared_guidance() -> str:
    """
    Return all shared guidance components concatenated.
    Use this in domain prompts to include all anti-hallucination measures.
    """
    return "\n\n".join([
        EVIDENCE_REQUIREMENTS,
        HALLUCINATION_GUARDRAILS,
        GAP_OVER_GUESS,
        CONFIDENCE_CALIBRATION
    ])


__all__ = [
    # Evidence and anti-hallucination
    'get_evidence_requirements',
    'get_hallucination_guardrails',
    'get_gap_over_guess',
    'get_confidence_calibration',
    'get_all_shared_guidance',
    'EVIDENCE_REQUIREMENTS',
    'HALLUCINATION_GUARDRAILS',
    'GAP_OVER_GUESS',
    'CONFIDENCE_CALIBRATION',
    'ENTITY_DISTINCTION_PROMPT',
    'ENTITY_DISTINCTION_SHORT',
    # Complexity signals
    'COMPLEXITY_SIGNALS',
    'INDUSTRY_SIGNALS',
    'get_complexity_signals_for_domain',
    'get_industry_signals',
    'calculate_ai_weight',
    'get_signal_prompt_injection',
    # M&A Framing (Phase 1)
    'MNA_LENSES',
    'STATEMENT_TYPES',
    'MNA_FRAMING_PROMPT_BLOCK',
    'get_mna_framing_prompt',
    'get_lens_definition',
    'get_all_lens_ids',
    'get_lens_for_deal_type',
    'validate_mna_lens',
    'get_statement_type_guidance',
    # Reasoning Quality
    'get_reasoning_quality_prompt',
    'REASONING_QUALITY_BLOCK',
    # Function Story Templates (Phase 3)
    'FunctionStory',
    'FUNCTION_DOMAIN_MAP',
    'STRENGTH_SIGNALS',
    'CONSTRAINT_SIGNALS',
    'DEPENDENCY_MAP',
    'get_functions_for_domain',
    'get_all_functions',
    'get_function_details',
    'get_upstream_dependencies',
    'get_downstream_dependents',
    'detect_strength_signals',
    'detect_constraint_signals',
    'get_story_prompt',
    'get_day1_critical_functions',
    'get_tsa_likely_functions',
    # Benchmark Generator (Phase 7)
    'BenchmarkType',
    'BenchmarkPattern',
    'BENCHMARK_PATTERNS',
    'SAFE_LANGUAGE',
    'UNSAFE_LANGUAGE',
    'generate_benchmarks',
    'validate_benchmark_safety',
    'analyze_team_concentration',
    'analyze_outsourcing',
    'analyze_ratios',
    'analyze_posture',
    'analyze_maturity_signals',
    'get_benchmark_mna_context',
    # Function Deep Dive (Quality Enhancement)
    'MaturityLevel',
    'FunctionReviewCriteria',
    'INFRASTRUCTURE_FUNCTIONS',
    'APPLICATIONS_FUNCTIONS',
    'ORGANIZATION_FUNCTIONS',
    'CYBERSECURITY_FUNCTIONS',
    'IDENTITY_FUNCTIONS',
    'NETWORK_FUNCTIONS',
    'get_function_criteria',
    'get_all_criteria',
    'assess_function_completeness',
    'get_cross_domain_dependencies',
    'get_mna_questions',
    # Strategic Cost Assessment
    'DealComplexity',
    'CompanyProfile',
    'DealProfile',
    'COST_DRIVER_PATTERNS',
    'DEAL_TYPE_CONSIDERATIONS',
    'calculate_complexity_score',
    'estimate_total_separation_cost',
    'identify_cost_drivers',
    'generate_strategic_assessment',
    'get_strategic_assessment_prompt',
    # Deal Implications
    'DealImplication',
    'CARVEOUT_IMPLICATIONS',
    'ACQUISITION_IMPLICATIONS',
    'get_implications_for_deal_type',
    'match_facts_to_implications',
    'get_implication_prompt_injection',
    # Industry Application Considerations
    'INDUSTRY_APPLICATION_CONSIDERATIONS',
    'detect_industry_from_text',
    'get_industry_considerations',
    'get_all_industries',
    'inject_industry_into_discovery_prompt',
    'assess_industry_application_gaps',
    'get_industry_prompt_summary',
]
