"""
Narrative Review Prompt (v2 Architecture)

Validates narrative output against executive standards before final delivery.
Checks completeness, M&A framing, evidence discipline, actionability, and tone.

Output: ReviewResult with pass/fail, scores, issues, and improvement suggestions
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field, asdict
from enum import Enum
from datetime import datetime


# =============================================================================
# REVIEW CRITERIA DEFINITIONS
# =============================================================================

class IssueSeverity(Enum):
    """Severity levels for review issues."""
    CRITICAL = "critical"  # Must fix before delivery
    MAJOR = "major"        # Should fix, impacts quality
    MINOR = "minor"        # Nice to fix, polish item


@dataclass
class ReviewIssue:
    """A specific issue found during review."""
    section: str
    issue: str
    severity: IssueSeverity
    suggestion: str
    evidence: str = ""  # Specific text that caused the issue

    def to_dict(self) -> Dict:
        return {
            "section": self.section,
            "issue": self.issue,
            "severity": self.severity.value,
            "suggestion": self.suggestion,
            "evidence": self.evidence
        }


@dataclass
class SectionScore:
    """Score for a narrative section."""
    section_name: str
    score: float  # 0-100
    max_score: float = 100.0
    issues: List[ReviewIssue] = field(default_factory=list)
    passed: bool = True

    def to_dict(self) -> Dict:
        return {
            "section_name": self.section_name,
            "score": self.score,
            "max_score": self.max_score,
            "issues": [i.to_dict() for i in self.issues],
            "passed": self.passed
        }


@dataclass
class ReviewResult:
    """Complete review result for a narrative."""
    overall_pass: bool
    score: float  # 0-100
    section_scores: Dict[str, SectionScore]
    issues: List[ReviewIssue]
    improvements: List[str]
    reviewed_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict:
        return {
            "overall_pass": self.overall_pass,
            "score": self.score,
            "section_scores": {k: v.to_dict() for k, v in self.section_scores.items()},
            "issues": [i.to_dict() for i in self.issues],
            "improvements": self.improvements,
            "reviewed_at": self.reviewed_at
        }

    def get_critical_issues(self) -> List[ReviewIssue]:
        return [i for i in self.issues if i.severity == IssueSeverity.CRITICAL]

    def get_summary(self) -> str:
        """Get a human-readable summary."""
        status = "PASS" if self.overall_pass else "FAIL"
        critical = len(self.get_critical_issues())
        total = len(self.issues)
        return f"Review {status} (Score: {self.score:.0f}/100, Issues: {total}, Critical: {critical})"


# =============================================================================
# REVIEW CRITERIA
# =============================================================================

NARRATIVE_REVIEW_CRITERIA = {
    "completeness": {
        "executive_summary_bullet_count": {"min": 5, "max": 7},
        "team_stories_coverage": "all teams in inventory",
        "risks_minimum": 5,
        "synergies_minimum": 3,
        "separation_considerations_minimum": 5,
        "benchmark_statements_minimum": 4,
        "org_structure_paragraphs": {"min": 2, "max": 4}
    },
    "mna_framing": {
        "every_risk_has_mna_lens": True,
        "every_synergy_has_value_mechanism": True,
        "day_1_explicitly_addressed": True,
        "tsa_explicitly_addressed_if_carveout": True,
        "separation_explicitly_addressed_if_divestiture": True
    },
    "evidence_discipline": {
        "facts_cited": True,
        "inferences_labeled": True,
        "no_fabricated_specifics": True,
        "gap_flags_present_where_applicable": True
    },
    "actionability": {
        "mitigations_are_specific": True,
        "first_steps_are_actionable": True,
        "separation_considerations_are_action_oriented": True,
        "timelines_are_realistic": True
    },
    "tone": {
        "consulting_tone": True,
        "not_academic": True,
        "decisive_not_hedging": True,
        "no_filler_phrases": True
    }
}


# Academic/filler phrases to flag
ACADEMIC_PHRASES = [
    "it is important to note",
    "it should be noted",
    "in conclusion",
    "furthermore",
    "moreover",
    "thus",
    "hence",
    "therefore it can be concluded",
    "the research shows",
    "studies indicate",
    "literature suggests"
]

HEDGING_PHRASES = [
    "it might be",
    "perhaps",
    "it could potentially",
    "there is a possibility",
    "it is conceivable",
    "one might argue",
    "it remains to be seen",
    "time will tell"
]

FILLER_PHRASES = [
    "going forward",
    "at the end of the day",
    "in terms of",
    "with respect to",
    "it is what it is",
    "needless to say",
    "as previously mentioned",
    "as stated earlier"
]

# Value mechanism keywords for synergies
VALUE_MECHANISMS = [
    "cost elimination",
    "cost avoidance",
    "efficiency gain",
    "capability gain",
    "consolidat",
    "eliminate",
    "reduce",
    "avoid",
    "leverage"
]

# Action-oriented keywords for mitigations
ACTION_KEYWORDS = [
    "implement",
    "deploy",
    "establish",
    "create",
    "conduct",
    "perform",
    "execute",
    "negotiate",
    "assess",
    "evaluate",
    "document",
    "define",
    "plan",
    "schedule",
    "assign",
    "hire",
    "train"
]


# =============================================================================
# REVIEW PROMPT
# =============================================================================

NARRATIVE_REVIEW_PROMPT = """You are a quality reviewer for IT due diligence narratives.
Your job is to validate the narrative meets executive standards before delivery.

## REVIEW CRITERIA

### 1. COMPLETENESS

Check these minimums:
- Executive summary: 5-7 bullets (CRITICAL if outside range)
- Team stories: Must cover ALL teams identified in the inventory
- Risks table: At least 5 rows with all columns populated
- Synergies/opportunities table: At least 3 rows
- Separation considerations: At least 5 action items
- Benchmark statements: At least 4 directional statements
- Org structure narrative: 2-4 paragraphs of prose

### 2. M&A FRAMING

Verify these requirements:
- Every risk has an explicit M&A lens (Day-1, TSA, Separation, Synergy, Cost)
- Every synergy has a value mechanism (cost elimination, avoidance, capability gain, efficiency)
- Day-1 requirements are explicitly listed
- If carveout: TSA services are inventoried
- If divestiture: RemainCo impact is addressed

### 3. EVIDENCE DISCIPLINE

Check for:
- Facts have citations (F-XXX-###)
- Inferences are labeled with "Inference:" prefix
- No fabricated specifics (invented statistics, made-up vendor names, fake costs)
- Gaps are flagged where information is missing

RED FLAGS for fabrication:
- Specific percentages without citation
- Vendor names not in source documents
- Cost figures not derived from facts
- Industry benchmarks presented as fact

### 4. ACTIONABILITY

Verify:
- Mitigations are SPECIFIC (not "improve security" but "implement MFA for privileged accounts")
- First steps are ACTIONABLE (clear owner, clear action, achievable)
- Separation considerations use action verbs (implement, establish, conduct, etc.)
- Timelines are realistic and specific

### 5. TONE

Flag issues with:
- Academic language (see list below)
- Excessive hedging (see list below)
- Filler phrases (see list below)
- Passive voice overuse
- Non-committal statements

Academic phrases to flag: {academic_phrases}
Hedging phrases to flag: {hedging_phrases}
Filler phrases to flag: {filler_phrases}

## NARRATIVE TO REVIEW

{narrative}

## DEAL CONTEXT

{deal_context}

## EXPECTED OUTPUT FORMAT

Return a JSON object with this structure:

```json
{{
    "overall_pass": true/false,
    "score": 0-100,
    "section_scores": {{
        "executive_summary": {{"score": X, "passed": true/false, "issues": [...]}},
        "org_structure": {{"score": X, "passed": true/false, "issues": [...]}},
        "team_stories": {{"score": X, "passed": true/false, "issues": [...]}},
        "mna_lens": {{"score": X, "passed": true/false, "issues": [...]}},
        "benchmarks": {{"score": X, "passed": true/false, "issues": [...]}},
        "risks_synergies": {{"score": X, "passed": true/false, "issues": [...]}}
    }},
    "issues": [
        {{
            "section": "section_name",
            "issue": "description of issue",
            "severity": "critical|major|minor",
            "suggestion": "how to fix",
            "evidence": "specific text that caused issue"
        }}
    ],
    "improvements": [
        "Specific improvement suggestion 1",
        "Specific improvement suggestion 2"
    ]
}}
```

## SCORING GUIDE

- 90-100: Excellent, ready for IC
- 80-89: Good, minor polish needed
- 70-79: Acceptable, some improvements needed
- 60-69: Needs work, several issues
- Below 60: Significant revision required

CRITICAL issues automatically fail the review.
More than 3 MAJOR issues should fail the review.

## SEVERITY DEFINITIONS

- **CRITICAL**: Missing required section, fabricated data, completely wrong framing
- **MAJOR**: Incomplete section, missing M&A lens, non-actionable mitigations
- **MINOR**: Tone issues, minor formatting, polish items

Now review the narrative and provide your assessment.
"""


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_review_prompt(narrative: str, deal_context: Dict) -> str:
    """Build the complete review prompt."""
    import json

    return NARRATIVE_REVIEW_PROMPT.format(
        narrative=narrative,
        deal_context=json.dumps(deal_context, indent=2),
        academic_phrases=", ".join(ACADEMIC_PHRASES[:5]),
        hedging_phrases=", ".join(HEDGING_PHRASES[:5]),
        filler_phrases=", ".join(FILLER_PHRASES[:5])
    )


def check_completeness(narrative: Dict) -> List[ReviewIssue]:
    """Check narrative completeness against criteria."""
    issues = []
    criteria = NARRATIVE_REVIEW_CRITERIA["completeness"]

    # Executive summary bullets
    exec_summary = narrative.get("executive_summary", [])
    bullet_count = len(exec_summary)
    min_bullets = criteria["executive_summary_bullet_count"]["min"]
    max_bullets = criteria["executive_summary_bullet_count"]["max"]

    if bullet_count < min_bullets:
        issues.append(ReviewIssue(
            section="executive_summary",
            issue=f"Executive summary has {bullet_count} bullets (minimum {min_bullets} required)",
            severity=IssueSeverity.CRITICAL,
            suggestion=f"Add {min_bullets - bullet_count} more bullets covering key findings"
        ))
    elif bullet_count > max_bullets:
        issues.append(ReviewIssue(
            section="executive_summary",
            issue=f"Executive summary has {bullet_count} bullets (maximum {max_bullets})",
            severity=IssueSeverity.MINOR,
            suggestion="Consolidate bullets to stay within 5-7 range"
        ))

    # Risks table
    risks = narrative.get("risks_table", [])
    if len(risks) < criteria["risks_minimum"]:
        issues.append(ReviewIssue(
            section="risks_synergies",
            issue=f"Only {len(risks)} risks identified (minimum {criteria['risks_minimum']})",
            severity=IssueSeverity.MAJOR,
            suggestion="Identify additional risks from domain findings"
        ))

    # Check for empty cells in risks
    for i, risk in enumerate(risks):
        for col in ["risk", "why_it_matters", "likely_impact", "mitigation"]:
            if not risk.get(col):
                issues.append(ReviewIssue(
                    section="risks_synergies",
                    issue=f"Risk row {i+1} missing '{col}'",
                    severity=IssueSeverity.MAJOR,
                    suggestion=f"Populate the '{col}' column for all risks"
                ))

    # Synergies table
    synergies = narrative.get("synergies_table", [])
    if len(synergies) < criteria["synergies_minimum"]:
        issues.append(ReviewIssue(
            section="risks_synergies",
            issue=f"Only {len(synergies)} synergies identified (minimum {criteria['synergies_minimum']})",
            severity=IssueSeverity.MAJOR,
            suggestion="Identify additional synergy opportunities"
        ))

    # Team stories
    team_stories = narrative.get("team_stories", [])
    if len(team_stories) == 0:
        issues.append(ReviewIssue(
            section="team_stories",
            issue="No team stories provided",
            severity=IssueSeverity.CRITICAL,
            suggestion="Generate team stories for all identified functions"
        ))

    # Separation considerations
    mna_lens = narrative.get("mna_lens_section", {})
    sep_considerations = mna_lens.get("separation_considerations", [])
    if len(sep_considerations) < criteria["separation_considerations_minimum"]:
        issues.append(ReviewIssue(
            section="mna_lens",
            issue=f"Only {len(sep_considerations)} separation considerations (minimum {criteria['separation_considerations_minimum']})",
            severity=IssueSeverity.MAJOR,
            suggestion="Add more specific, action-oriented separation considerations"
        ))

    # Benchmark statements
    benchmarks = narrative.get("benchmark_statements", [])
    if len(benchmarks) < criteria["benchmark_statements_minimum"]:
        issues.append(ReviewIssue(
            section="benchmarks",
            issue=f"Only {len(benchmarks)} benchmark statements (minimum {criteria['benchmark_statements_minimum']})",
            severity=IssueSeverity.MAJOR,
            suggestion="Add directional benchmark statements based on inventory data"
        ))

    # Org structure narrative
    org_narrative = narrative.get("org_structure_narrative", "")
    if len(org_narrative) < 200:
        issues.append(ReviewIssue(
            section="org_structure",
            issue="Organization structure narrative is too brief",
            severity=IssueSeverity.MAJOR,
            suggestion="Expand to 2-3 paragraphs covering lean vs. layered, run vs. change, and implications"
        ))

    return issues


def check_evidence_discipline(narrative_text: str) -> List[ReviewIssue]:
    """Check for evidence discipline issues."""
    issues = []

    # Check for unlabeled inferences
    inference_indicators = [
        "likely", "probably", "suggests", "indicates", "appears",
        "seems", "typically", "generally", "usually"
    ]

    lines = narrative_text.split('\n')
    for i, line in enumerate(lines):
        line_lower = line.lower()

        # Check if line has inference indicators but no "Inference:" label
        has_inference_indicator = any(ind in line_lower for ind in inference_indicators)
        has_inference_label = "inference:" in line_lower

        if has_inference_indicator and not has_inference_label and len(line) > 50:
            # Check if it's a fact with citation
            has_citation = "(f-" in line_lower or "(gap)" in line_lower

            if not has_citation:
                issues.append(ReviewIssue(
                    section="evidence_discipline",
                    issue="Potential unlabeled inference",
                    severity=IssueSeverity.MINOR,
                    suggestion="Label inferences with 'Inference:' prefix",
                    evidence=line[:100] + "..." if len(line) > 100 else line
                ))

    # Check for potentially fabricated specifics
    import re

    # Specific percentages without citation
    pct_pattern = r'\d{1,3}%'
    percentages = re.findall(pct_pattern, narrative_text)
    if len(percentages) > 5:
        # Check if they have citations nearby
        for match in re.finditer(pct_pattern, narrative_text):
            context = narrative_text[max(0, match.start()-50):min(len(narrative_text), match.end()+50)]
            if "(f-" not in context.lower() and "inference" not in context.lower():
                issues.append(ReviewIssue(
                    section="evidence_discipline",
                    issue="Specific percentage may lack citation",
                    severity=IssueSeverity.MAJOR,
                    suggestion="Ensure all specific statistics have fact citations or are labeled as inferences",
                    evidence=context
                ))
                break  # Only flag once

    return issues


def check_tone(narrative_text: str) -> List[ReviewIssue]:
    """Check for tone issues."""
    issues = []
    text_lower = narrative_text.lower()

    # Check for academic phrases
    for phrase in ACADEMIC_PHRASES:
        if phrase in text_lower:
            issues.append(ReviewIssue(
                section="tone",
                issue=f"Academic phrase detected: '{phrase}'",
                severity=IssueSeverity.MINOR,
                suggestion="Replace with more direct, consulting language"
            ))

    # Check for hedging phrases
    for phrase in HEDGING_PHRASES:
        if phrase in text_lower:
            issues.append(ReviewIssue(
                section="tone",
                issue=f"Hedging phrase detected: '{phrase}'",
                severity=IssueSeverity.MINOR,
                suggestion="Be more decisive - state findings with confidence"
            ))

    # Check for filler phrases
    for phrase in FILLER_PHRASES:
        if phrase in text_lower:
            issues.append(ReviewIssue(
                section="tone",
                issue=f"Filler phrase detected: '{phrase}'",
                severity=IssueSeverity.MINOR,
                suggestion="Remove filler phrases for more concise writing"
            ))

    return issues


def check_actionability(narrative: Dict) -> List[ReviewIssue]:
    """Check if mitigations and recommendations are actionable."""
    issues = []

    # Check risk mitigations
    risks = narrative.get("risks_table", [])
    for i, risk in enumerate(risks):
        mitigation = risk.get("mitigation", "").lower()
        has_action_verb = any(verb in mitigation for verb in ACTION_KEYWORDS)

        if mitigation and not has_action_verb:
            issues.append(ReviewIssue(
                section="risks_synergies",
                issue=f"Risk {i+1} mitigation may not be actionable",
                severity=IssueSeverity.MINOR,
                suggestion="Use action verbs (implement, establish, conduct, etc.)",
                evidence=risk.get("mitigation", "")[:100]
            ))

    # Check synergy first steps
    synergies = narrative.get("synergies_table", [])
    for i, syn in enumerate(synergies):
        first_step = syn.get("first_step", "").lower()
        has_action_verb = any(verb in first_step for verb in ACTION_KEYWORDS)

        if first_step and not has_action_verb:
            issues.append(ReviewIssue(
                section="risks_synergies",
                issue=f"Synergy {i+1} first step may not be actionable",
                severity=IssueSeverity.MINOR,
                suggestion="Use action verbs (implement, establish, conduct, etc.)",
                evidence=syn.get("first_step", "")[:100]
            ))

    # Check synergy value mechanisms
    for i, syn in enumerate(synergies):
        value_mech = syn.get("value_mechanism", "").lower()
        has_value_mech = any(mech in value_mech for mech in VALUE_MECHANISMS)

        if value_mech and not has_value_mech:
            issues.append(ReviewIssue(
                section="risks_synergies",
                issue=f"Synergy {i+1} missing clear value mechanism",
                severity=IssueSeverity.MAJOR,
                suggestion="Specify value mechanism: cost elimination, cost avoidance, capability gain, or efficiency gain",
                evidence=syn.get("value_mechanism", "")[:100]
            ))

    # Check separation considerations are action-oriented
    mna_lens = narrative.get("mna_lens_section", {})
    sep_considerations = mna_lens.get("separation_considerations", [])
    for i, consideration in enumerate(sep_considerations):
        consideration_lower = consideration.lower()
        has_action_verb = any(verb in consideration_lower for verb in ACTION_KEYWORDS)

        if not has_action_verb:
            issues.append(ReviewIssue(
                section="mna_lens",
                issue=f"Separation consideration {i+1} may not be action-oriented",
                severity=IssueSeverity.MINOR,
                suggestion="Start with action verb (Establish, Implement, Conduct, etc.)",
                evidence=consideration[:100]
            ))

    return issues


def run_local_review(narrative: Dict, narrative_text: str) -> ReviewResult:
    """
    Run local (non-LLM) review checks.

    This is faster and doesn't require API calls.
    """
    all_issues = []

    # Run all checks
    all_issues.extend(check_completeness(narrative))
    all_issues.extend(check_evidence_discipline(narrative_text))
    all_issues.extend(check_tone(narrative_text))
    all_issues.extend(check_actionability(narrative))

    # Calculate scores
    section_scores = {}
    sections = ["executive_summary", "org_structure", "team_stories",
                "mna_lens", "benchmarks", "risks_synergies", "evidence_discipline", "tone"]

    for section in sections:
        section_issues = [i for i in all_issues if i.section == section]
        critical_count = len([i for i in section_issues if i.severity == IssueSeverity.CRITICAL])
        major_count = len([i for i in section_issues if i.severity == IssueSeverity.MAJOR])
        minor_count = len([i for i in section_issues if i.severity == IssueSeverity.MINOR])

        score = 100 - (critical_count * 30) - (major_count * 15) - (minor_count * 5)
        score = max(0, score)

        section_scores[section] = SectionScore(
            section_name=section,
            score=score,
            issues=section_issues,
            passed=critical_count == 0 and major_count < 2
        )

    # Calculate overall score
    total_score = sum(s.score for s in section_scores.values()) / len(section_scores)

    # Determine pass/fail
    critical_count = len([i for i in all_issues if i.severity == IssueSeverity.CRITICAL])
    major_count = len([i for i in all_issues if i.severity == IssueSeverity.MAJOR])
    overall_pass = critical_count == 0 and major_count <= 3

    # Generate improvements
    improvements = []
    if critical_count > 0:
        improvements.append(f"Address {critical_count} critical issue(s) before delivery")
    if major_count > 0:
        improvements.append(f"Fix {major_count} major issue(s) to improve quality")

    # Add specific improvement suggestions based on patterns
    if any(i.section == "evidence_discipline" for i in all_issues):
        improvements.append("Review all inferences and ensure proper labeling")
    if any(i.section == "tone" for i in all_issues):
        improvements.append("Revise language to be more direct and consulting-oriented")
    if any("actionable" in i.issue.lower() for i in all_issues):
        improvements.append("Make mitigations and recommendations more specific and actionable")

    return ReviewResult(
        overall_pass=overall_pass,
        score=total_score,
        section_scores=section_scores,
        issues=all_issues,
        improvements=improvements
    )


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Data classes
    'IssueSeverity',
    'ReviewIssue',
    'SectionScore',
    'ReviewResult',
    # Criteria
    'NARRATIVE_REVIEW_CRITERIA',
    'ACADEMIC_PHRASES',
    'HEDGING_PHRASES',
    'FILLER_PHRASES',
    'VALUE_MECHANISMS',
    'ACTION_KEYWORDS',
    # Prompt
    'NARRATIVE_REVIEW_PROMPT',
    'get_review_prompt',
    # Check functions
    'check_completeness',
    'check_evidence_discipline',
    'check_tone',
    'check_actionability',
    'run_local_review'
]
