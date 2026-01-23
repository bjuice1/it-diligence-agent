"""
Narrative Review Agent

Validates narrative output against executive standards before final delivery.
Runs both local (fast) checks and optional LLM-based (thorough) review.

Input: ExecutiveNarrative or narrative dict
Output: ReviewResult with pass/fail, scores, issues, and suggestions
"""

import anthropic
from typing import Dict, List, Optional, Any
import json
import logging
from time import time

from prompts.v2_narrative_review_prompt import (
    ReviewResult,
    ReviewIssue,
    SectionScore,
    IssueSeverity,
    get_review_prompt,
    run_local_review,
    check_completeness
)

# Import rate limiter if available
try:
    from config_v2 import estimate_cost
except ImportError:
    def estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
        return 0.0


logger = logging.getLogger(__name__)


class NarrativeReviewAgent:
    """
    Agent that reviews narrative output for quality before delivery.

    Supports two modes:
    1. Local review (fast, no API calls) - checks structure, completeness, tone
    2. LLM review (thorough, uses API) - deep content analysis

    Use local review for quick validation, LLM review for final QA.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-sonnet-4-20250514",
        max_tokens: int = 4096
    ):
        """
        Initialize the review agent.

        Args:
            api_key: Anthropic API key (only needed for LLM review)
            model: Model to use for LLM review
            max_tokens: Max tokens for LLM response
        """
        self.api_key = api_key
        self.model = model
        self.max_tokens = max_tokens
        self.logger = logging.getLogger("narrative_review")

        # Only create client if API key provided
        self.client = None
        if api_key:
            self.client = anthropic.Anthropic(api_key=api_key)

        # Metrics
        self.metrics = {
            "reviews_completed": 0,
            "api_calls": 0,
            "input_tokens": 0,
            "output_tokens": 0,
            "estimated_cost": 0.0,
            "execution_time": 0.0
        }

    def review(
        self,
        narrative: Dict,
        deal_context: Dict,
        use_llm: bool = False
    ) -> ReviewResult:
        """
        Review a narrative for quality.

        Args:
            narrative: Narrative dict (from ExecutiveNarrative.to_dict())
            deal_context: Deal context dict
            use_llm: If True, use LLM for deep review (slower, more thorough)

        Returns:
            ReviewResult with pass/fail, scores, issues, and suggestions
        """
        start_time = time()
        company_name = deal_context.get('company_name', 'Target Company')
        deal_type = deal_context.get('deal_type', 'acquisition')

        self.logger.info(f"Starting narrative review for {company_name}")
        print(f"\n{'='*60}")
        print(f"Narrative Review: {company_name}")
        print(f"Mode: {'LLM (thorough)' if use_llm else 'Local (fast)'}")
        print(f"{'='*60}")

        try:
            # Convert narrative to markdown for text-based checks
            narrative_text = self._narrative_to_text(narrative)

            # Run local review (always)
            print("Running local checks...")
            local_result = run_local_review(narrative, narrative_text)

            # Run LLM review if requested
            llm_result = None
            if use_llm and self.client:
                print("Running LLM review...")
                llm_result = self._run_llm_review(narrative_text, deal_context)

                # Merge LLM issues into local result
                if llm_result:
                    local_result = self._merge_results(local_result, llm_result)

            # Deal-type specific checks
            deal_type_issues = self._check_deal_type_requirements(
                narrative, deal_type
            )
            local_result.issues.extend(deal_type_issues)

            # Recalculate overall pass after all checks
            critical_count = len(local_result.get_critical_issues())
            major_count = len([i for i in local_result.issues
                             if i.severity == IssueSeverity.MAJOR])
            local_result.overall_pass = critical_count == 0 and major_count <= 3

            # Update metrics
            self.metrics["reviews_completed"] += 1
            self.metrics["execution_time"] = time() - start_time

            # Print summary
            print(f"\n{local_result.get_summary()}")
            if local_result.issues:
                print("\nTop issues:")
                for issue in sorted(local_result.issues,
                                   key=lambda x: x.severity.value)[:5]:
                    print(f"  [{issue.severity.value.upper()}] {issue.section}: {issue.issue}")

            return local_result

        except Exception as e:
            self.logger.error(f"Review failed: {e}")
            # Return a failed result
            return ReviewResult(
                overall_pass=False,
                score=0,
                section_scores={},
                issues=[ReviewIssue(
                    section="review_error",
                    issue=f"Review failed: {str(e)}",
                    severity=IssueSeverity.CRITICAL,
                    suggestion="Fix the error and re-run review"
                )],
                improvements=["Review could not be completed due to error"]
            )

    def review_markdown(
        self,
        narrative_markdown: str,
        deal_context: Dict,
        use_llm: bool = False
    ) -> ReviewResult:
        """
        Review a narrative from its markdown representation.

        Useful when you only have the markdown output.
        """
        # Parse markdown back to structure (basic parsing)
        narrative = self._parse_markdown_to_structure(narrative_markdown)
        return self.review(narrative, deal_context, use_llm)

    def quick_check(self, narrative: Dict) -> Dict[str, Any]:
        """
        Perform a quick completeness check without full review.

        Returns a simple dict with pass/fail and issue count.
        """
        issues = check_completeness(narrative)
        critical_count = len([i for i in issues if i.severity == IssueSeverity.CRITICAL])

        return {
            "pass": critical_count == 0,
            "issue_count": len(issues),
            "critical_count": critical_count,
            "issues": [i.issue for i in issues]
        }

    def _narrative_to_text(self, narrative: Dict) -> str:
        """Convert narrative dict to text for analysis."""
        parts = []

        # Executive summary
        parts.append("## Executive Summary")
        for bullet in narrative.get("executive_summary", []):
            parts.append(f"- {bullet}")

        # Org structure
        parts.append("\n## Organization Structure")
        parts.append(narrative.get("org_structure_narrative", ""))

        # Team stories
        parts.append("\n## Team Stories")
        for story in narrative.get("team_stories", []):
            parts.append(f"\n### {story.get('function_name', 'Unknown')}")
            parts.append(f"Day-to-day: {story.get('day_to_day', '')}")
            parts.append("Strengths: " + ", ".join(story.get('strengths', [])))
            parts.append("Constraints: " + ", ".join(story.get('constraints', [])))
            parts.append(f"M&A Implication: {story.get('mna_implication', '')}")

        # M&A Lens
        parts.append("\n## M&A Lens")
        mna = narrative.get("mna_lens_section", {})
        if mna.get("tsa_exposed_functions"):
            parts.append("TSA-Exposed: " + ", ".join(mna["tsa_exposed_functions"]))
        if mna.get("day_1_requirements"):
            parts.append("Day-1: " + ", ".join(mna["day_1_requirements"]))
        if mna.get("separation_considerations"):
            parts.append("Separation Considerations:")
            for item in mna["separation_considerations"]:
                parts.append(f"- {item}")

        # Benchmarks
        parts.append("\n## Benchmarks")
        for statement in narrative.get("benchmark_statements", []):
            parts.append(f"- {statement}")

        # Risks
        parts.append("\n## Risks")
        for risk in narrative.get("risks_table", []):
            parts.append(f"- {risk.get('risk', '')}: {risk.get('mitigation', '')}")

        # Synergies
        parts.append("\n## Synergies")
        for syn in narrative.get("synergies_table", []):
            parts.append(f"- {syn.get('opportunity', '')}: {syn.get('first_step', '')}")

        return "\n".join(parts)

    def _run_llm_review(
        self,
        narrative_text: str,
        deal_context: Dict
    ) -> Optional[ReviewResult]:
        """Run LLM-based review for deeper analysis."""
        if not self.client:
            return None

        try:
            prompt = get_review_prompt(narrative_text, deal_context)

            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=0,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            # Track metrics
            self.metrics["api_calls"] += 1
            self.metrics["input_tokens"] += response.usage.input_tokens
            self.metrics["output_tokens"] += response.usage.output_tokens
            self.metrics["estimated_cost"] += estimate_cost(
                self.model,
                response.usage.input_tokens,
                response.usage.output_tokens
            )

            # Parse response
            response_text = response.content[0].text
            return self._parse_llm_response(response_text)

        except Exception as e:
            self.logger.error(f"LLM review failed: {e}")
            return None

    def _parse_llm_response(self, response_text: str) -> Optional[ReviewResult]:
        """Parse LLM response into ReviewResult."""
        try:
            # Find JSON in response
            import re
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if not json_match:
                return None

            data = json.loads(json_match.group())

            # Convert to ReviewResult
            issues = []
            for issue_data in data.get("issues", []):
                issues.append(ReviewIssue(
                    section=issue_data.get("section", "unknown"),
                    issue=issue_data.get("issue", ""),
                    severity=IssueSeverity(issue_data.get("severity", "minor")),
                    suggestion=issue_data.get("suggestion", ""),
                    evidence=issue_data.get("evidence", "")
                ))

            section_scores = {}
            for section, score_data in data.get("section_scores", {}).items():
                section_scores[section] = SectionScore(
                    section_name=section,
                    score=score_data.get("score", 0),
                    passed=score_data.get("passed", True),
                    issues=[]
                )

            return ReviewResult(
                overall_pass=data.get("overall_pass", False),
                score=data.get("score", 0),
                section_scores=section_scores,
                issues=issues,
                improvements=data.get("improvements", [])
            )

        except Exception as e:
            self.logger.error(f"Failed to parse LLM response: {e}")
            return None

    def _merge_results(
        self,
        local_result: ReviewResult,
        llm_result: ReviewResult
    ) -> ReviewResult:
        """Merge local and LLM review results."""
        # Combine issues, avoiding duplicates
        existing_issues = {(i.section, i.issue) for i in local_result.issues}
        for issue in llm_result.issues:
            if (issue.section, issue.issue) not in existing_issues:
                local_result.issues.append(issue)

        # Combine improvements
        existing_improvements = set(local_result.improvements)
        for improvement in llm_result.improvements:
            if improvement not in existing_improvements:
                local_result.improvements.append(improvement)

        # Average scores
        if llm_result.score > 0:
            local_result.score = (local_result.score + llm_result.score) / 2

        return local_result

    def _check_deal_type_requirements(
        self,
        narrative: Dict,
        deal_type: str
    ) -> List[ReviewIssue]:
        """Check deal-type-specific requirements."""
        issues = []
        deal_type_lower = deal_type.lower()

        mna_lens = narrative.get("mna_lens_section", {})

        if "carveout" in deal_type_lower or "carve" in deal_type_lower:
            # Carveout must have TSA services
            tsa = mna_lens.get("tsa_exposed_functions", [])
            if len(tsa) < 3:
                issues.append(ReviewIssue(
                    section="mna_lens",
                    issue=f"Carveout narrative should identify TSA-exposed functions (found {len(tsa)})",
                    severity=IssueSeverity.MAJOR,
                    suggestion="Identify functions likely requiring transition services"
                ))

            # Check for standalone readiness discussion
            sep_considerations = mna_lens.get("separation_considerations", [])
            standalone_mentions = sum(1 for c in sep_considerations
                                     if "standalone" in c.lower() or "independent" in c.lower())
            if standalone_mentions < 2:
                issues.append(ReviewIssue(
                    section="mna_lens",
                    issue="Carveout should address standalone readiness",
                    severity=IssueSeverity.MAJOR,
                    suggestion="Add considerations for achieving standalone operations"
                ))

        elif "divestiture" in deal_type_lower or "divest" in deal_type_lower:
            # Divestiture should address RemainCo
            sep_considerations = mna_lens.get("separation_considerations", [])
            remainco_mentions = sum(1 for c in sep_considerations
                                   if "remainco" in c.lower() or "remain" in c.lower())
            if remainco_mentions < 2:
                issues.append(ReviewIssue(
                    section="mna_lens",
                    issue="Divestiture should address RemainCo impact",
                    severity=IssueSeverity.MAJOR,
                    suggestion="Add considerations for RemainCo operations post-divestiture"
                ))

        elif "acquisition" in deal_type_lower or "bolt" in deal_type_lower:
            # Acquisition should emphasize synergies
            synergies = narrative.get("synergies_table", [])
            if len(synergies) < 3:
                issues.append(ReviewIssue(
                    section="risks_synergies",
                    issue=f"Acquisition narrative should identify synergy opportunities (found {len(synergies)})",
                    severity=IssueSeverity.MAJOR,
                    suggestion="Identify at least 3 synergy opportunities with value mechanisms"
                ))

            # Check for integration discussion
            day_1 = mna_lens.get("day_1_requirements", [])
            if len(day_1) < 3:
                issues.append(ReviewIssue(
                    section="mna_lens",
                    issue="Acquisition should list Day-1 integration requirements",
                    severity=IssueSeverity.MAJOR,
                    suggestion="Identify critical Day-1 requirements for business continuity"
                ))

        return issues

    def _parse_markdown_to_structure(self, markdown: str) -> Dict:
        """Basic parsing of markdown back to structure."""
        # This is a simplified parser - in production would be more robust
        narrative = {
            "executive_summary": [],
            "org_structure_narrative": "",
            "team_stories": [],
            "mna_lens_section": {
                "tsa_exposed_functions": [],
                "day_1_requirements": [],
                "separation_considerations": []
            },
            "benchmark_statements": [],
            "risks_table": [],
            "synergies_table": []
        }

        current_section = None
        lines = markdown.split('\n')

        for line in lines:
            line_lower = line.lower()

            # Detect sections
            if '## 1)' in line or 'executive summary' in line_lower:
                current_section = 'executive_summary'
            elif '## 2)' in line or 'organization' in line_lower:
                current_section = 'org_structure'
            elif '## 3)' in line or 'team' in line_lower:
                current_section = 'team_stories'
            elif '## 4)' in line or 'm&a lens' in line_lower:
                current_section = 'mna_lens'
            elif '## 5)' in line or 'benchmark' in line_lower:
                current_section = 'benchmarks'
            elif '## 6)' in line or 'risk' in line_lower:
                current_section = 'risks'

            # Parse content based on section
            elif current_section == 'executive_summary' and line.startswith('- '):
                narrative["executive_summary"].append(line[2:].strip())

            elif current_section == 'org_structure' and line.strip():
                narrative["org_structure_narrative"] += line + "\n"

            elif current_section == 'benchmarks' and line.startswith('- '):
                narrative["benchmark_statements"].append(line[2:].strip())

        return narrative

    def get_metrics(self) -> Dict:
        """Get review metrics."""
        return self.metrics.copy()


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def create_review_agent(api_key: Optional[str] = None) -> NarrativeReviewAgent:
    """Factory function to create review agent."""
    return NarrativeReviewAgent(api_key=api_key)


def quick_review(narrative: Dict, deal_context: Dict) -> ReviewResult:
    """Convenience function for quick local review."""
    agent = NarrativeReviewAgent()
    return agent.review(narrative, deal_context, use_llm=False)


__all__ = [
    'NarrativeReviewAgent',
    'create_review_agent',
    'quick_review'
]
