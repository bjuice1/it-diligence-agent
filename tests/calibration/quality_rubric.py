"""
Quality Rubric for Executive Narrative Scoring

Implements the scoring system defined in the game plan Phase 10.
Each dimension is scored 1-5, with weighted aggregation.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
import re


class ScoreLevel(Enum):
    """Score levels with descriptions."""
    EXCELLENT = 5
    GOOD = 4
    ACCEPTABLE = 3
    POOR = 2
    FAILING = 1


@dataclass
class DimensionScore:
    """Score for a single dimension."""
    dimension: str
    score: float  # 1-5
    weight: float  # percentage as decimal
    weighted_score: float  # score * weight
    details: str
    issues: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)


@dataclass
class RubricResult:
    """Complete scoring result for a narrative."""
    test_case_id: str
    overall_score: float  # 0-100
    passing: bool  # score >= 80
    dimension_scores: Dict[str, DimensionScore] = field(default_factory=dict)
    critical_issues: List[str] = field(default_factory=list)
    improvement_areas: List[str] = field(default_factory=list)
    strengths: List[str] = field(default_factory=list)


# =============================================================================
# DIMENSION WEIGHTS (from game plan)
# =============================================================================

DIMENSION_WEIGHTS = {
    "mna_framing": 0.25,      # 25% - Every finding connects to lens
    "evidence_discipline": 0.20,  # 20% - All cited, inferences labeled
    "actionability": 0.20,    # 20% - Specific, executable actions
    "narrative_flow": 0.15,   # 15% - Tells coherent story
    "completeness": 0.10,     # 10% - All sections, all teams
    "tone": 0.10,             # 10% - Consulting-ready
}


# =============================================================================
# SCORING CRITERIA
# =============================================================================

def score_mna_framing(narrative: Dict, deal_context: Dict) -> DimensionScore:
    """
    Score M&A framing quality.

    5 (Excellent): Every finding connects to lens
    3 (Acceptable): Most connect
    1 (Poor): Few connect
    """
    issues = []
    suggestions = []
    score = 5.0

    deal_type = deal_context.get("deal_type", "acquisition")

    # Check executive summary mentions deal implications
    exec_summary = narrative.get("executive_summary", [])
    deal_mentions = sum(1 for b in exec_summary if any(
        term in b.lower() for term in ["day-1", "day 1", "tsa", "separation", "synergy", "integration", "standalone"]
    ))

    if deal_mentions < 2:
        score -= 1.0
        issues.append("Executive summary lacks deal-type-specific implications")
        suggestions.append("Add 2-3 bullets explicitly addressing Day-1/TSA/synergy implications")

    # Check M&A lens section exists and is populated
    mna_section = narrative.get("mna_lens_section", {})

    if not mna_section:
        score -= 2.0
        issues.append("Missing M&A lens section entirely")
    else:
        # Check for required components based on deal type
        if deal_type in ["carveout", "carve_out"]:
            if not mna_section.get("tsa_exposed_functions"):
                score -= 0.5
                issues.append("Carveout missing TSA-exposed functions list")
            if len(mna_section.get("separation_considerations", [])) < 5:
                score -= 0.5
                issues.append(f"Only {len(mna_section.get('separation_considerations', []))} separation considerations (minimum 5)")

        if not mna_section.get("day_1_requirements"):
            score -= 0.5
            issues.append("Missing Day-1 requirements")

    # Check risks have M&A context
    risks = narrative.get("risks_table", [])
    risks_with_mna = sum(1 for r in risks if r.get("why_it_matters") and len(r["why_it_matters"]) > 10)

    if risks and risks_with_mna / len(risks) < 0.8:
        score -= 0.5
        issues.append(f"Only {risks_with_mna}/{len(risks)} risks have meaningful 'why it matters'")

    # Check synergies have value mechanisms
    synergies = narrative.get("synergies_table", [])
    synergies_with_mechanism = sum(1 for s in synergies if s.get("value_mechanism"))

    if synergies and synergies_with_mechanism / len(synergies) < 0.8:
        score -= 0.5
        issues.append(f"Only {synergies_with_mechanism}/{len(synergies)} synergies have value mechanisms")

    score = max(1.0, min(5.0, score))

    details = f"M&A framing score: {score}/5. Deal mentions in summary: {deal_mentions}."
    if mna_section:
        details += f" Separation considerations: {len(mna_section.get('separation_considerations', []))}."

    return DimensionScore(
        dimension="mna_framing",
        score=score,
        weight=DIMENSION_WEIGHTS["mna_framing"],
        weighted_score=score * DIMENSION_WEIGHTS["mna_framing"],
        details=details,
        issues=issues,
        suggestions=suggestions
    )


def score_evidence_discipline(narrative: Dict) -> DimensionScore:
    """
    Score evidence discipline.

    5 (Excellent): All cited, inferences labeled
    3 (Acceptable): Mostly cited
    1 (Poor): Unsupported claims
    """
    issues = []
    suggestions = []
    score = 5.0

    # Convert narrative to text for analysis
    narrative_text = _narrative_to_text(narrative)

    # Check for fact citations (F-DOMAIN-###)
    citation_pattern = r'\(F-[A-Z]+-\d{3}\)'
    citations = re.findall(citation_pattern, narrative_text)

    if len(citations) < 5:
        score -= 1.0
        issues.append(f"Only {len(citations)} fact citations found (minimum 5 expected)")
        suggestions.append("Add explicit citations (F-DOMAIN-###) to key claims")

    # Check for inference labels
    inference_count = narrative_text.lower().count("inference:")
    pattern_count = narrative_text.lower().count("pattern:")

    # Look for likely inferences that aren't labeled
    inference_words = ["likely", "probably", "suggests", "indicates", "appears", "seems"]
    unlabeled_inferences = sum(
        1 for word in inference_words
        if word in narrative_text.lower() and f"inference: {word}" not in narrative_text.lower()
    )

    if inference_count == 0 and unlabeled_inferences > 3:
        score -= 1.5
        issues.append(f"Found {unlabeled_inferences} potential unlabeled inferences")
        suggestions.append("Label inferences with 'Inference:' prefix")
    elif inference_count > 0 and unlabeled_inferences > inference_count * 2:
        score -= 0.5
        issues.append("Some inferences may be unlabeled")

    # Check for fabricated specifics (percentages, dollar amounts without citations)
    specific_pattern = r'(\d+%|\$[\d,]+[KMB]?)'
    specifics = re.findall(specific_pattern, narrative_text)

    # Each specific should ideally be near a citation
    # This is a heuristic check
    if len(specifics) > 10 and len(citations) < len(specifics) / 2:
        score -= 0.5
        issues.append("Many specific numbers without nearby citations")
        suggestions.append("Ensure specific figures are tied to cited facts")

    score = max(1.0, min(5.0, score))

    details = f"Evidence discipline score: {score}/5. Citations: {len(citations)}, Labeled inferences: {inference_count}."

    return DimensionScore(
        dimension="evidence_discipline",
        score=score,
        weight=DIMENSION_WEIGHTS["evidence_discipline"],
        weighted_score=score * DIMENSION_WEIGHTS["evidence_discipline"],
        details=details,
        issues=issues,
        suggestions=suggestions
    )


def score_actionability(narrative: Dict) -> DimensionScore:
    """
    Score actionability of recommendations.

    5 (Excellent): Specific, executable actions
    3 (Acceptable): Generally actionable
    1 (Poor): Vague
    """
    issues = []
    suggestions = []
    score = 5.0

    # Check risks have specific mitigations
    risks = narrative.get("risks_table", [])
    vague_mitigations = 0
    vague_terms = ["consider", "evaluate", "assess", "review", "look into", "think about"]

    for risk in risks:
        mitigation = risk.get("mitigation", "").lower()
        if not mitigation or len(mitigation) < 20:
            vague_mitigations += 1
        elif any(term in mitigation for term in vague_terms) and not any(
            action in mitigation for action in ["implement", "deploy", "hire", "migrate", "consolidate", "establish"]
        ):
            vague_mitigations += 1

    if risks and vague_mitigations / len(risks) > 0.3:
        score -= 1.0
        issues.append(f"{vague_mitigations}/{len(risks)} risk mitigations are vague")
        suggestions.append("Replace vague terms like 'consider' with specific actions")

    # Check synergies have actionable first steps
    synergies = narrative.get("synergies_table", [])
    vague_first_steps = 0

    for syn in synergies:
        first_step = syn.get("first_step", "").lower()
        if not first_step or len(first_step) < 15:
            vague_first_steps += 1
        elif first_step.startswith("consider") or first_step.startswith("evaluate"):
            vague_first_steps += 1

    if synergies and vague_first_steps / len(synergies) > 0.3:
        score -= 0.5
        issues.append(f"{vague_first_steps}/{len(synergies)} synergy first steps are vague")

    # Check separation considerations are action-oriented
    mna_section = narrative.get("mna_lens_section", {})
    sep_considerations = mna_section.get("separation_considerations", [])

    action_verbs = ["establish", "implement", "deploy", "migrate", "build", "create", "negotiate", "secure", "hire", "contract"]
    action_oriented = sum(
        1 for c in sep_considerations
        if any(verb in c.lower() for verb in action_verbs)
    )

    if sep_considerations and action_oriented / len(sep_considerations) < 0.6:
        score -= 0.5
        issues.append(f"Only {action_oriented}/{len(sep_considerations)} separation considerations are action-oriented")
        suggestions.append("Start separation considerations with action verbs")

    score = max(1.0, min(5.0, score))

    details = f"Actionability score: {score}/5."

    return DimensionScore(
        dimension="actionability",
        score=score,
        weight=DIMENSION_WEIGHTS["actionability"],
        weighted_score=score * DIMENSION_WEIGHTS["actionability"],
        details=details,
        issues=issues,
        suggestions=suggestions
    )


def score_narrative_flow(narrative: Dict) -> DimensionScore:
    """
    Score narrative coherence and flow.

    5 (Excellent): Tells coherent story
    3 (Acceptable): Readable
    1 (Poor): Disjointed
    """
    issues = []
    suggestions = []
    score = 5.0

    # Check executive summary provides overview
    exec_summary = narrative.get("executive_summary", [])
    if len(exec_summary) < 5:
        score -= 1.0
        issues.append(f"Executive summary has only {len(exec_summary)} bullets (need 5-7)")
    elif len(exec_summary) > 7:
        score -= 0.5
        issues.append(f"Executive summary has {len(exec_summary)} bullets (should be 5-7)")

    # Check for logical section progression
    required_sections = [
        "executive_summary",
        "org_structure_narrative",
        "team_stories",
        "mna_lens_section",
        "benchmark_statements",
        "risks_table"
    ]

    missing_sections = [s for s in required_sections if not narrative.get(s)]
    if missing_sections:
        score -= len(missing_sections) * 0.3
        issues.append(f"Missing sections: {', '.join(missing_sections)}")

    # Check org structure narrative exists and has substance
    org_narrative = narrative.get("org_structure_narrative", "")
    if not org_narrative:
        score -= 0.5
        issues.append("Missing org structure narrative")
    elif len(org_narrative) < 200:
        score -= 0.3
        issues.append("Org structure narrative is too brief")

    # Check team stories are present
    team_stories = narrative.get("team_stories", [])
    if len(team_stories) < 3:
        score -= 0.5
        issues.append(f"Only {len(team_stories)} team stories (minimum 3 expected)")

    score = max(1.0, min(5.0, score))

    details = f"Narrative flow score: {score}/5. Sections present: {len(required_sections) - len(missing_sections)}/{len(required_sections)}."

    return DimensionScore(
        dimension="narrative_flow",
        score=score,
        weight=DIMENSION_WEIGHTS["narrative_flow"],
        weighted_score=score * DIMENSION_WEIGHTS["narrative_flow"],
        details=details,
        issues=issues,
        suggestions=suggestions
    )


def score_completeness(narrative: Dict, test_case: Optional[Any] = None) -> DimensionScore:
    """
    Score completeness of narrative.

    5 (Excellent): All sections, all teams
    3 (Acceptable): Minor gaps
    1 (Poor): Major gaps
    """
    issues = []
    suggestions = []
    score = 5.0

    # Check executive summary bullet count
    exec_summary = narrative.get("executive_summary", [])
    if len(exec_summary) < 5:
        score -= 0.5
        issues.append(f"Executive summary: {len(exec_summary)} bullets (need 5-7)")

    # Check risks minimum
    risks = narrative.get("risks_table", [])
    if len(risks) < 5:
        score -= 0.5
        issues.append(f"Only {len(risks)} risks (minimum 5)")
        suggestions.append("Ensure at least 5 risks are identified across domains")

    # Check synergies minimum
    synergies = narrative.get("synergies_table", [])
    if len(synergies) < 3:
        score -= 0.5
        issues.append(f"Only {len(synergies)} synergies (minimum 3)")

    # Check separation considerations
    mna_section = narrative.get("mna_lens_section", {})
    sep_cons = mna_section.get("separation_considerations", [])
    if len(sep_cons) < 5:
        score -= 0.5
        issues.append(f"Only {len(sep_cons)} separation considerations (minimum 5)")

    # Check benchmark statements
    benchmarks = narrative.get("benchmark_statements", [])
    if len(benchmarks) < 4:
        score -= 0.3
        issues.append(f"Only {len(benchmarks)} benchmark statements (minimum 4)")

    # Check team stories coverage
    team_stories = narrative.get("team_stories", [])
    if test_case and hasattr(test_case, 'inventory'):
        expected_teams = _count_expected_teams(test_case.inventory)
        if len(team_stories) < expected_teams * 0.8:
            score -= 0.5
            issues.append(f"Only {len(team_stories)} team stories (expected ~{expected_teams})")
    elif len(team_stories) < 4:
        score -= 0.3
        issues.append(f"Only {len(team_stories)} team stories")

    score = max(1.0, min(5.0, score))

    details = f"Completeness score: {score}/5. Risks: {len(risks)}, Synergies: {len(synergies)}, Teams: {len(team_stories)}."

    return DimensionScore(
        dimension="completeness",
        score=score,
        weight=DIMENSION_WEIGHTS["completeness"],
        weighted_score=score * DIMENSION_WEIGHTS["completeness"],
        details=details,
        issues=issues,
        suggestions=suggestions
    )


def score_tone(narrative: Dict) -> DimensionScore:
    """
    Score tone appropriateness.

    5 (Excellent): Consulting-ready
    3 (Acceptable): Acceptable
    1 (Poor): Academic/fluffy
    """
    issues = []
    suggestions = []
    score = 5.0

    narrative_text = _narrative_to_text(narrative)
    text_lower = narrative_text.lower()

    # Check for academic language
    academic_terms = [
        "it is important to note",
        "it should be noted",
        "one might consider",
        "it is worth mentioning",
        "in conclusion",
        "furthermore",
        "moreover",
        "thus",
        "hence",
        "therefore it can be concluded"
    ]

    academic_count = sum(1 for term in academic_terms if term in text_lower)
    if academic_count > 3:
        score -= 0.5
        issues.append(f"Found {academic_count} academic phrases")
        suggestions.append("Use direct, consulting-style language")

    # Check for hedging language
    hedging_terms = [
        "might",
        "could potentially",
        "may or may not",
        "it is possible that",
        "there is a chance",
        "arguably"
    ]

    hedging_count = sum(1 for term in hedging_terms if term in text_lower)
    if hedging_count > 5:
        score -= 0.5
        issues.append(f"Excessive hedging language ({hedging_count} instances)")
        suggestions.append("Be more decisive - state positions clearly")

    # Check for fluffy/filler language
    filler_terms = [
        "very important",
        "extremely critical",
        "absolutely essential",
        "significantly impactful",
        "highly recommended"
    ]

    filler_count = sum(1 for term in filler_terms if term in text_lower)
    if filler_count > 3:
        score -= 0.3
        issues.append(f"Found {filler_count} filler phrases")

    # Positive: Check for consulting-style language
    consulting_terms = [
        "recommend",
        "priority",
        "immediate action",
        "key finding",
        "critical",
        "day-1",
        "workstream"
    ]

    consulting_count = sum(1 for term in consulting_terms if term in text_lower)
    if consulting_count < 5:
        score -= 0.3
        issues.append("Could use more consulting-style terminology")

    score = max(1.0, min(5.0, score))

    details = f"Tone score: {score}/5. Consulting terms: {consulting_count}, Academic: {academic_count}."

    return DimensionScore(
        dimension="tone",
        score=score,
        weight=DIMENSION_WEIGHTS["tone"],
        weighted_score=score * DIMENSION_WEIGHTS["tone"],
        details=details,
        issues=issues,
        suggestions=suggestions
    )


# =============================================================================
# MAIN SCORING FUNCTION
# =============================================================================

def score_narrative(
    narrative: Dict,
    test_case: Optional[Any] = None,
    deal_context: Optional[Dict] = None
) -> RubricResult:
    """
    Score a narrative against the quality rubric.

    Args:
        narrative: The generated narrative dict
        test_case: Optional TestCase for context
        deal_context: Deal context dict (deal_type, target_name, etc.)

    Returns:
        RubricResult with overall score and dimension breakdown
    """
    if deal_context is None:
        deal_context = {
            "deal_type": narrative.get("deal_type", "acquisition"),
            "target_name": narrative.get("company_name", "Target")
        }

    # Score each dimension
    dimension_scores = {}

    dimension_scores["mna_framing"] = score_mna_framing(narrative, deal_context)
    dimension_scores["evidence_discipline"] = score_evidence_discipline(narrative)
    dimension_scores["actionability"] = score_actionability(narrative)
    dimension_scores["narrative_flow"] = score_narrative_flow(narrative)
    dimension_scores["completeness"] = score_completeness(narrative, test_case)
    dimension_scores["tone"] = score_tone(narrative)

    # Calculate overall score (0-100)
    total_weighted = sum(ds.weighted_score for ds in dimension_scores.values())
    overall_score = total_weighted * 20  # Convert 5-point to 100-point scale

    # Determine pass/fail
    passing = overall_score >= 80

    # Collect critical issues (from dimensions scoring < 3)
    critical_issues = []
    for dim_name, dim_score in dimension_scores.items():
        if dim_score.score < 3:
            critical_issues.extend([f"[{dim_name}] {issue}" for issue in dim_score.issues])

    # Collect improvement areas (from all issues)
    improvement_areas = []
    for dim_score in dimension_scores.values():
        improvement_areas.extend(dim_score.suggestions)

    # Identify strengths (dimensions scoring >= 4)
    strengths = []
    for dim_name, dim_score in dimension_scores.items():
        if dim_score.score >= 4:
            strengths.append(f"{dim_name}: {dim_score.details}")

    return RubricResult(
        test_case_id=test_case.id if test_case else "manual",
        overall_score=round(overall_score, 1),
        passing=passing,
        dimension_scores=dimension_scores,
        critical_issues=critical_issues,
        improvement_areas=improvement_areas,
        strengths=strengths
    )


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _narrative_to_text(narrative: Dict) -> str:
    """Convert narrative dict to searchable text."""
    text_parts = []

    # Executive summary
    for bullet in narrative.get("executive_summary", []):
        text_parts.append(bullet)

    # Org structure
    text_parts.append(narrative.get("org_structure_narrative", ""))

    # Team stories
    for story in narrative.get("team_stories", []):
        text_parts.append(story.get("day_to_day", ""))
        text_parts.extend(story.get("strengths", []))
        text_parts.extend(story.get("constraints", []))
        text_parts.append(story.get("mna_implication", ""))

    # M&A lens
    mna = narrative.get("mna_lens_section", {})
    text_parts.extend(mna.get("tsa_exposed_functions", []))
    text_parts.extend(mna.get("day_1_requirements", []))
    text_parts.extend(mna.get("separation_considerations", []))

    # Benchmarks
    text_parts.extend(narrative.get("benchmark_statements", []))

    # Risks
    for risk in narrative.get("risks_table", []):
        text_parts.append(risk.get("risk", ""))
        text_parts.append(risk.get("why_it_matters", ""))
        text_parts.append(risk.get("mitigation", ""))

    # Synergies
    for syn in narrative.get("synergies_table", []):
        text_parts.append(syn.get("opportunity", ""))
        text_parts.append(syn.get("value_mechanism", ""))
        text_parts.append(syn.get("first_step", ""))

    return " ".join(text_parts)


def _count_expected_teams(inventory: Dict) -> int:
    """Count expected teams from inventory structure."""
    count = 0

    org = inventory.get("organization", {})
    structure = org.get("structure", {})
    teams = structure.get("teams", [])
    count += len(teams)

    # Add for apps teams if multiple ERPs
    apps = inventory.get("applications", {})
    if apps.get("erp_systems") and len(apps.get("erp_systems", [])) > 1:
        count += 1  # Extra for ERP complexity

    return max(count, 4)  # Minimum 4 expected


def format_rubric_result(result: RubricResult) -> str:
    """Format rubric result for display."""
    lines = []
    lines.append(f"=" * 60)
    lines.append(f"CALIBRATION RESULT: {result.test_case_id}")
    lines.append(f"=" * 60)
    lines.append("")
    lines.append(f"OVERALL SCORE: {result.overall_score}/100 {'✅ PASS' if result.passing else '❌ FAIL'}")
    lines.append("")
    lines.append("DIMENSION SCORES:")
    lines.append("-" * 40)

    for dim_name, dim_score in result.dimension_scores.items():
        status = "✅" if dim_score.score >= 3.5 else "⚠️" if dim_score.score >= 2.5 else "❌"
        lines.append(f"  {status} {dim_name}: {dim_score.score}/5 (weight: {dim_score.weight*100:.0f}%)")
        if dim_score.issues:
            for issue in dim_score.issues:
                lines.append(f"      - {issue}")

    if result.critical_issues:
        lines.append("")
        lines.append("CRITICAL ISSUES:")
        lines.append("-" * 40)
        for issue in result.critical_issues:
            lines.append(f"  ❌ {issue}")

    if result.improvement_areas:
        lines.append("")
        lines.append("IMPROVEMENT SUGGESTIONS:")
        lines.append("-" * 40)
        for suggestion in result.improvement_areas[:5]:  # Top 5
            lines.append(f"  → {suggestion}")

    if result.strengths:
        lines.append("")
        lines.append("STRENGTHS:")
        lines.append("-" * 40)
        for strength in result.strengths:
            lines.append(f"  ✅ {strength}")

    lines.append("")
    lines.append("=" * 60)

    return "\n".join(lines)


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    'ScoreLevel',
    'DimensionScore',
    'RubricResult',
    'DIMENSION_WEIGHTS',
    'score_narrative',
    'score_mna_framing',
    'score_evidence_discipline',
    'score_actionability',
    'score_narrative_flow',
    'score_completeness',
    'score_tone',
    'format_rubric_result',
]
