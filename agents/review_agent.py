"""
Review Agent for IT Diligence Analysis

Reviews domain agent findings BEFORE coordinator synthesis to ensure:
- Findings are well-supported by evidence
- Severity/priority ratings are justified
- No obvious gaps or inconsistencies
- Quality gate before human review

QUESTION WORKFLOW INTEGRATION:
- Checks if open questions have been answered by new findings
- Creates questions from high-priority gaps without questions
- Links findings to related questions
- Closes questions when evidence is found

This is NOT a summarizer - it's a critical reviewer that validates work.
"""
import anthropic
import json
import logging
import re
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime

from config import ANTHROPIC_API_KEY, MODEL, MAX_TOKENS

logger = logging.getLogger(__name__)


@dataclass
class ReviewResult:
    """Result of reviewing a single finding"""
    finding_id: str
    finding_type: str  # risk, gap, work_item, etc.
    validation_status: str  # validated, needs_evidence, overstated, understated, flagged
    original_severity: Optional[str] = None
    recommended_severity: Optional[str] = None
    confidence_score: float = 0.0  # 0-1 how confident in this finding
    evidence_quality: str = "unknown"  # strong, moderate, weak, missing
    review_notes: str = ""
    issues_found: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)


@dataclass
class QuestionAction:
    """Action taken on a question during review"""
    question_id: str
    action: str  # created, closed, updated, linked
    reason: str
    related_finding_id: Optional[str] = None
    old_status: Optional[str] = None
    new_status: Optional[str] = None


@dataclass
class ReviewAgentMetrics:
    """Track review agent execution"""
    api_calls: int = 0
    findings_reviewed: int = 0
    findings_validated: int = 0
    findings_flagged: int = 0
    findings_adjusted: int = 0
    execution_time: float = 0.0
    # Question workflow metrics
    questions_reviewed: int = 0
    questions_closed: int = 0
    questions_created: int = 0
    questions_linked: int = 0
    gaps_without_questions: int = 0


class ReviewAgent:
    """
    Reviews domain agent findings for quality before coordinator synthesis.

    Key responsibilities:
    1. Validate each finding against document evidence
    2. Check severity/priority ratings are justified
    3. Flag weak or unsupported findings
    4. Identify gaps in analysis
    5. Suggest improvements

    QUESTION WORKFLOW:
    6. Review open questions against new findings
    7. Close questions that have been answered
    8. Create questions from gaps that need client input
    9. Link findings to related questions

    This creates accountability - findings must pass review before synthesis.
    """

    def __init__(self, store=None, repository=None, run_id: str = None):
        if not ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY must be set")

        self.client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        self.store = store
        self.repository = repository
        self.run_id = run_id
        self.metrics = ReviewAgentMetrics()
        self.review_results: List[ReviewResult] = []
        self.question_actions: List[QuestionAction] = []

    def get_system_prompt(self) -> str:
        return """You are a Senior IT Due Diligence Quality Reviewer. Your job is to critically review findings from domain analysts BEFORE they go to final synthesis.

You are NOT a summarizer. You are a critical reviewer who validates work quality.

For each finding you review, you must assess:

1. **Evidence Quality**: Is the finding supported by specific evidence from the document?
   - STRONG: Direct quotes or explicit statements support this
   - MODERATE: Reasonable inference from available information
   - WEAK: Speculative or loosely connected to evidence
   - MISSING: No clear evidence provided

2. **Severity/Priority Justification**: Is the rating appropriate?
   - CRITICAL: Business-stopping, immediate action required
   - HIGH: Significant impact, must address in integration
   - MEDIUM: Notable concern, should address
   - LOW: Minor issue, address if time permits

3. **Completeness**: Does the finding have enough detail to be actionable?

4. **Consistency**: Does this align with other findings? Any contradictions?

Your output for each finding should include:
- validation_status: "validated" | "needs_evidence" | "overstated" | "understated" | "flagged"
- confidence_score: 0.0-1.0 (how confident are you in this finding)
- evidence_quality: "strong" | "moderate" | "weak" | "missing"
- recommended_severity: only if different from original
- issues_found: list of problems identified
- suggestions: list of improvements

Be rigorous but fair. Flag issues but don't be unnecessarily harsh.
The goal is ensuring humans receive well-validated findings, not perfect findings."""

    def review(self, document_text: str, findings: Dict[str, List],
               deal_context: Dict = None) -> Dict[str, Any]:
        """
        Review all findings against the document AND manage question workflow.

        Args:
            document_text: Original document for evidence validation
            findings: Dict with risks, gaps, work_items, etc.
            deal_context: Optional context about the deal

        Returns:
            Dict with review results, summary, question actions, and updated findings
        """
        from time import time
        start_time = time()

        self.review_results = []
        self.question_actions = []

        # Build review prompt with findings and document excerpt
        review_prompt = self._build_review_prompt(document_text, findings, deal_context)

        logger.info("Starting quality review of domain findings...")

        try:
            response = self.client.messages.create(
                model=MODEL,
                max_tokens=MAX_TOKENS,
                system=self.get_system_prompt(),
                messages=[{"role": "user", "content": review_prompt}]
            )
            self.metrics.api_calls += 1

            # Parse review response
            self._parse_review_response(response.content[0].text, findings)

        except Exception as e:
            logger.error(f"Review agent error: {e}")
            self._create_fallback_review(findings)

        # QUESTION WORKFLOW INTEGRATION
        question_results = {}
        if self.repository and self.run_id:
            logger.info("Running question workflow integration...")
            question_results = self._run_question_workflow(document_text, findings)

        self.metrics.execution_time = time() - start_time

        # Compile results
        return {
            'review_results': self.review_results,
            'summary': self._generate_review_summary(),
            'metrics': {
                'api_calls': self.metrics.api_calls,
                'findings_reviewed': self.metrics.findings_reviewed,
                'findings_validated': self.metrics.findings_validated,
                'findings_flagged': self.metrics.findings_flagged,
                'findings_adjusted': self.metrics.findings_adjusted,
                'execution_time': self.metrics.execution_time,
                # Question metrics
                'questions_reviewed': self.metrics.questions_reviewed,
                'questions_closed': self.metrics.questions_closed,
                'questions_created': self.metrics.questions_created,
                'questions_linked': self.metrics.questions_linked,
                'gaps_without_questions': self.metrics.gaps_without_questions
            },
            'flagged_items': [r for r in self.review_results if r.validation_status == 'flagged'],
            'needs_evidence': [r for r in self.review_results if r.validation_status == 'needs_evidence'],
            'adjusted_items': [r for r in self.review_results if r.recommended_severity and r.recommended_severity != r.original_severity],
            # Question workflow results
            'question_actions': self.question_actions,
            'question_summary': question_results
        }

    def _run_question_workflow(self, document_text: str, findings: Dict) -> Dict:
        """
        Run the full question workflow integration.

        1. Get all open questions for this run
        2. Check if any findings answer open questions
        3. Create questions from high-priority gaps
        4. Link findings to related questions

        Returns:
            Dict with question workflow summary
        """
        results = {
            'questions_checked': 0,
            'questions_closed': 0,
            'questions_created': 0,
            'gaps_needing_questions': 0,
            'actions': []
        }

        try:
            # 1. Get open questions
            open_questions = self._get_open_questions()
            results['questions_checked'] = len(open_questions)
            self.metrics.questions_reviewed = len(open_questions)

            # 2. Check if findings answer any open questions
            if open_questions and findings:
                closed = self._check_questions_against_findings(open_questions, findings, document_text)
                results['questions_closed'] = closed

            # 3. Create questions from high-priority gaps without questions
            gaps = findings.get('gaps', [])
            if gaps:
                created, gaps_needing = self._create_questions_from_gaps(gaps)
                results['questions_created'] = created
                results['gaps_needing_questions'] = gaps_needing

            # 4. Compile actions
            results['actions'] = [
                {
                    'question_id': a.question_id,
                    'action': a.action,
                    'reason': a.reason,
                    'related_finding_id': a.related_finding_id
                }
                for a in self.question_actions
            ]

        except Exception as e:
            logger.error(f"Question workflow error: {e}")
            results['error'] = str(e)

        return results

    def _get_open_questions(self) -> List[Dict]:
        """Get all open (non-answered, non-closed) questions for this run."""
        try:
            conn = self.repository.db.connect()
            rows = conn.execute(
                """SELECT * FROM questions
                   WHERE run_id = ? AND status NOT IN ('answered', 'closed')
                   ORDER BY priority DESC, created_at""",
                (self.run_id,)
            ).fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error fetching open questions: {e}")
            return []

    def _check_questions_against_findings(self, questions: List[Dict],
                                          findings: Dict, document_text: str) -> int:
        """
        Check if any open questions have been answered by findings or document content.

        Uses LLM to determine if question has been answered.

        Returns:
            Number of questions closed
        """
        closed_count = 0

        # Build context from findings
        findings_text = self._summarize_findings_for_matching(findings)

        # For efficiency, batch questions and check with single API call
        if not questions:
            return 0

        prompt = f"""You are checking if any of these open questions have been answered by new information.

## Document Content (excerpt)
{document_text[:8000]}

## Current Findings Summary
{findings_text}

## Open Questions to Check
"""
        for i, q in enumerate(questions, 1):
            prompt += f"""
{i}. [{q.get('priority', 'medium').upper()}] {q.get('question_text', '')}
   Context: {q.get('context', 'N/A')}
   Question ID: {q.get('question_id', 'N/A')}
"""

        prompt += """

## Your Task
For each question, determine if it has been answered by the document or findings.

Return a JSON array:
```json
[
  {
    "question_id": "Q-xxx",
    "answered": true|false,
    "answer_found": "The specific answer if found, or null",
    "evidence": "Where the answer was found (document section or finding ID)",
    "confidence": 0.0-1.0
  }
]
```

Only mark as answered if you have HIGH CONFIDENCE (>0.8) the question is clearly answered.
Be conservative - it's better to leave a question open than close it prematurely."""

        try:
            response = self.client.messages.create(
                model=MODEL,
                max_tokens=4096,
                messages=[{"role": "user", "content": prompt}]
            )
            self.metrics.api_calls += 1

            # Parse response
            response_text = response.content[0].text
            json_match = re.search(r'\[[\s\S]*?\]', response_text)
            if json_match:
                results = json.loads(json_match.group())

                for result in results:
                    if result.get('answered') and result.get('confidence', 0) >= 0.8:
                        question_id = result.get('question_id')
                        answer = result.get('answer_found', 'Answer found in document/findings')
                        evidence = result.get('evidence', '')

                        # Close the question
                        if self._close_question(question_id, answer, evidence):
                            closed_count += 1
                            self.metrics.questions_closed += 1

                            # Record action
                            self.question_actions.append(QuestionAction(
                                question_id=question_id,
                                action='closed',
                                reason=f"Answered by findings: {evidence[:100]}",
                                old_status='open',
                                new_status='answered'
                            ))

        except Exception as e:
            logger.error(f"Error checking questions against findings: {e}")

        return closed_count

    def _close_question(self, question_id: str, answer: str, evidence: str) -> bool:
        """Close a question by updating its status and answer."""
        try:
            conn = self.repository.db.connect()
            conn.execute(
                """UPDATE questions
                   SET status = 'answered',
                       answer_text = ?,
                       answer_source = ?,
                       answered_date = ?,
                       answered_by = 'ReviewAgent'
                   WHERE question_id = ?""",
                (answer, f"Auto-detected: {evidence}", datetime.now().isoformat(), question_id)
            )
            conn.commit()
            logger.info(f"Closed question {question_id} - answered by findings")
            return True
        except Exception as e:
            logger.error(f"Error closing question {question_id}: {e}")
            return False

    def _create_questions_from_gaps(self, gaps: List[Dict]) -> tuple:
        """
        Create questions from high-priority gaps that don't have corresponding questions.

        Returns:
            Tuple of (questions_created, gaps_needing_questions)
        """
        created = 0
        gaps_needing = 0

        # Get existing questions to avoid duplicates
        existing_questions = self._get_all_questions()
        existing_texts = {q.get('question_text', '').lower() for q in existing_questions}

        # Also check for gaps already linked to questions
        existing_gap_ids = {q.get('related_gap_id') for q in existing_questions if q.get('related_gap_id')}

        for gap in gaps:
            gap_id = gap.get('id', '')
            gap_text = gap.get('gap', gap.get('gap_description', ''))
            priority = gap.get('priority', 'medium')
            domain = gap.get('domain', 'general')
            why_needed = gap.get('why_needed', '')

            # Skip if gap already has a question
            if gap_id in existing_gap_ids:
                continue

            # Only auto-create for high/critical priority gaps
            if priority.lower() not in ['high', 'critical']:
                continue

            gaps_needing += 1
            self.metrics.gaps_without_questions += 1

            # Generate question text from gap
            question_text = self._generate_question_from_gap(gap_text, why_needed)

            # Skip if similar question exists
            if question_text.lower() in existing_texts:
                continue

            # Create the question
            try:
                from storage.models import generate_id, now_iso
                question_id = generate_id('Q')

                conn = self.repository.db.connect()
                conn.execute(
                    """INSERT INTO questions
                       (question_id, run_id, question_text, priority, domain,
                        context, status, related_gap_id, created_at, source)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (question_id, self.run_id, question_text, priority, domain,
                     f"Auto-generated from gap: {gap_text[:200]}", 'draft', gap_id,
                     now_iso(), 'review_agent')
                )
                conn.commit()

                created += 1
                self.metrics.questions_created += 1

                # Record action
                self.question_actions.append(QuestionAction(
                    question_id=question_id,
                    action='created',
                    reason=f"Generated from gap {gap_id}",
                    related_finding_id=gap_id,
                    new_status='draft'
                ))

                logger.info(f"Created question {question_id} from gap {gap_id}")

            except Exception as e:
                logger.error(f"Error creating question from gap {gap_id}: {e}")

        return created, gaps_needing

    def _generate_question_from_gap(self, gap_text: str, why_needed: str) -> str:
        """Generate a question text from a gap description."""
        # Simple transformation - could be enhanced with LLM
        gap_lower = gap_text.lower()

        if 'not provided' in gap_lower or 'missing' in gap_lower or 'no information' in gap_lower:
            # Turn "X not provided" into "Can you provide X?"
            subject = gap_text.replace('not provided', '').replace('Not provided', '')
            subject = subject.replace('missing', '').replace('Missing', '')
            subject = subject.replace('no information on', '').replace('No information on', '')
            subject = subject.strip(' -:.')
            return f"Can you provide information about {subject}?"
        elif 'unclear' in gap_lower:
            subject = gap_text.replace('unclear', '').replace('Unclear', '').strip(' -:.')
            return f"Can you clarify {subject}?"
        else:
            # Generic question format
            return f"Regarding '{gap_text[:100]}' - can you provide more details or documentation?"

    def _get_all_questions(self) -> List[Dict]:
        """Get all questions for this run."""
        try:
            conn = self.repository.db.connect()
            rows = conn.execute(
                "SELECT * FROM questions WHERE run_id = ?",
                (self.run_id,)
            ).fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error fetching questions: {e}")
            return []

    def _summarize_findings_for_matching(self, findings: Dict) -> str:
        """Create a summary of findings for question matching."""
        lines = []

        for finding_type, items in findings.items():
            if not isinstance(items, list) or not items:
                continue
            lines.append(f"\n## {finding_type.title()}")
            for item in items[:20]:  # Limit for context window
                if finding_type == 'risks':
                    lines.append(f"- {item.get('risk', item.get('risk_description', 'N/A'))}")
                elif finding_type == 'gaps':
                    lines.append(f"- {item.get('gap', item.get('gap_description', 'N/A'))}")
                elif finding_type == 'assumptions':
                    lines.append(f"- {item.get('assumption', item.get('assumption_text', 'N/A'))}")
                elif finding_type == 'current_state':
                    lines.append(f"- {item.get('item', item.get('description', 'N/A'))}")
                elif finding_type == 'work_items':
                    lines.append(f"- {item.get('title', 'N/A')}: {item.get('description', 'N/A')[:100]}")

        return '\n'.join(lines)

    def _build_review_prompt(self, document_text: str, findings: Dict,
                             deal_context: Dict = None) -> str:
        """Build the review prompt with findings and document context."""

        # Truncate document if too long (keep first and last portions)
        max_doc_length = 15000
        if len(document_text) > max_doc_length:
            half = max_doc_length // 2
            doc_excerpt = document_text[:half] + "\n\n[...document truncated...]\n\n" + document_text[-half:]
        else:
            doc_excerpt = document_text

        prompt = f"""# Quality Review Request

## Context
{json.dumps(deal_context, indent=2) if deal_context else "Standard IT due diligence review"}

## Source Document (for evidence validation)
```
{doc_excerpt}
```

## Findings to Review

Please review each finding below. For each one, provide your assessment in JSON format.

"""
        # Add risks
        if findings.get('risks'):
            prompt += "### RISKS\n"
            for i, risk in enumerate(findings['risks'], 1):
                prompt += f"""
**Risk {i}** (ID: {risk.get('id', 'N/A')})
- Description: {risk.get('risk', risk.get('risk_description', 'N/A'))}
- Severity: {risk.get('severity', 'N/A')}
- Likelihood: {risk.get('likelihood', 'N/A')}
- Domain: {risk.get('domain', 'N/A')}
- Impact: {risk.get('impact', risk.get('impact_description', 'N/A'))}
- Mitigation: {risk.get('mitigation', 'N/A')}
- Evidence/Source: {risk.get('source_evidence', risk.get('evidence', 'Not specified'))}
"""

        # Add gaps
        if findings.get('gaps'):
            prompt += "\n### KNOWLEDGE GAPS\n"
            for i, gap in enumerate(findings['gaps'], 1):
                prompt += f"""
**Gap {i}** (ID: {gap.get('id', 'N/A')})
- Description: {gap.get('gap', gap.get('gap_description', 'N/A'))}
- Priority: {gap.get('priority', 'N/A')}
- Why Needed: {gap.get('why_needed', 'N/A')}
- Domain: {gap.get('domain', 'N/A')}
"""

        # Add work items
        if findings.get('work_items'):
            prompt += "\n### WORK ITEMS\n"
            for i, item in enumerate(findings['work_items'], 1):
                prompt += f"""
**Work Item {i}** (ID: {item.get('id', 'N/A')})
- Title: {item.get('title', 'N/A')}
- Description: {item.get('description', 'N/A')}
- Phase: {item.get('timeline_phase', item.get('phase', 'N/A'))}
- Effort: {item.get('effort_estimate', 'N/A')}
- Cost: {item.get('cost_estimate_range', 'N/A')}
- Domain: {item.get('domain', 'N/A')}
"""

        # Add assumptions
        if findings.get('assumptions'):
            prompt += "\n### ASSUMPTIONS\n"
            for i, assumption in enumerate(findings['assumptions'], 1):
                prompt += f"""
**Assumption {i}** (ID: {assumption.get('id', 'N/A')})
- Assumption: {assumption.get('assumption', assumption.get('assumption_text', 'N/A'))}
- Confidence: {assumption.get('confidence', 'N/A')}
- Impact if Wrong: {assumption.get('impact_if_wrong', 'N/A')}
- Domain: {assumption.get('domain', 'N/A')}
"""

        prompt += """

## Your Task

Review each finding above and provide your assessment. Return a JSON array with one object per finding:

```json
[
  {
    "finding_id": "R-INFRA-001",
    "finding_type": "risk",
    "validation_status": "validated|needs_evidence|overstated|understated|flagged",
    "confidence_score": 0.85,
    "evidence_quality": "strong|moderate|weak|missing",
    "original_severity": "high",
    "recommended_severity": "high",  // only include if different
    "issues_found": ["issue 1", "issue 2"],
    "suggestions": ["suggestion 1"],
    "review_notes": "Brief explanation of your assessment"
  }
]
```

Also provide an overall assessment:
- Overall quality score (0-100)
- Key concerns across all findings
- Recommendations before this goes to executives

Be thorough but concise. Focus on substantive issues, not formatting nitpicks."""

        return prompt

    def _parse_review_response(self, response_text: str, findings: Dict) -> Dict:
        """Parse the review response and extract assessments."""

        # Try to extract JSON from response
        try:
            # Look for JSON array in response
            json_match = re.search(r'\[[\s\S]*?\](?=\s*(?:Also|Overall|$|\n\n[A-Z]))', response_text)
            if json_match:
                reviews = json.loads(json_match.group())
                for review in reviews:
                    result = ReviewResult(
                        finding_id=review.get('finding_id', 'unknown'),
                        finding_type=review.get('finding_type', 'unknown'),
                        validation_status=review.get('validation_status', 'unknown'),
                        original_severity=review.get('original_severity'),
                        recommended_severity=review.get('recommended_severity'),
                        confidence_score=float(review.get('confidence_score', 0.5)),
                        evidence_quality=review.get('evidence_quality', 'unknown'),
                        review_notes=review.get('review_notes', ''),
                        issues_found=review.get('issues_found', []),
                        suggestions=review.get('suggestions', [])
                    )
                    self.review_results.append(result)
                    self.metrics.findings_reviewed += 1

                    if result.validation_status == 'validated':
                        self.metrics.findings_validated += 1
                    elif result.validation_status == 'flagged':
                        self.metrics.findings_flagged += 1

                    if result.recommended_severity and result.recommended_severity != result.original_severity:
                        self.metrics.findings_adjusted += 1

        except json.JSONDecodeError as e:
            logger.warning(f"Could not parse review JSON: {e}")
            # Create basic reviews for all findings
            self._create_fallback_review(findings)

        # Also try to extract overall assessment
        overall = {}
        if "overall quality" in response_text.lower():
            # Try to find quality score
            score_match = re.search(r'(?:overall|quality)[^\d]*(\d+)', response_text.lower())
            if score_match:
                overall['quality_score'] = int(score_match.group(1))

        return {'reviews': self.review_results, 'overall': overall}

    def _create_fallback_review(self, findings: Dict) -> Dict:
        """Create basic review results if parsing fails."""

        for finding_type, items in findings.items():
            if not isinstance(items, list):
                continue
            for item in items:
                result = ReviewResult(
                    finding_id=item.get('id', 'unknown'),
                    finding_type=finding_type.rstrip('s'),  # risks -> risk
                    validation_status='needs_review',
                    confidence_score=0.5,
                    evidence_quality='unknown',
                    review_notes='Automated review could not be completed - manual review recommended'
                )
                self.review_results.append(result)
                self.metrics.findings_reviewed += 1

        return {'reviews': self.review_results, 'overall': {}}

    def _generate_review_summary(self) -> Dict:
        """Generate summary statistics from review results."""

        total = len(self.review_results)
        if total == 0:
            return {'message': 'No findings to review'}

        validated = sum(1 for r in self.review_results if r.validation_status == 'validated')
        flagged = sum(1 for r in self.review_results if r.validation_status == 'flagged')
        needs_evidence = sum(1 for r in self.review_results if r.validation_status == 'needs_evidence')
        overstated = sum(1 for r in self.review_results if r.validation_status == 'overstated')
        understated = sum(1 for r in self.review_results if r.validation_status == 'understated')

        avg_confidence = sum(r.confidence_score for r in self.review_results) / total

        evidence_dist = {}
        for r in self.review_results:
            eq = r.evidence_quality
            evidence_dist[eq] = evidence_dist.get(eq, 0) + 1

        return {
            'total_reviewed': total,
            'validated': validated,
            'flagged': flagged,
            'needs_evidence': needs_evidence,
            'overstated': overstated,
            'understated': understated,
            'validation_rate': validated / total if total > 0 else 0,
            'average_confidence': avg_confidence,
            'evidence_quality_distribution': evidence_dist,
            'quality_assessment': self._assess_overall_quality(validated, flagged, needs_evidence, total)
        }

    def _assess_overall_quality(self, validated: int, flagged: int,
                                 needs_evidence: int, total: int) -> str:
        """Provide overall quality assessment."""

        if total == 0:
            return "No findings to assess"

        validation_rate = validated / total
        flag_rate = flagged / total

        if validation_rate >= 0.8 and flag_rate <= 0.1:
            return "HIGH QUALITY - Findings are well-supported and ready for executive review"
        elif validation_rate >= 0.6 and flag_rate <= 0.2:
            return "ACCEPTABLE - Most findings validated, some need additional evidence"
        elif flag_rate >= 0.3:
            return "NEEDS WORK - Significant issues found, recommend addressing flagged items"
        else:
            return "MODERATE - Review flagged items and strengthen evidence where noted"


def review_findings(document_text: str, findings: Dict,
                    deal_context: Dict = None, repository=None,
                    run_id: str = None) -> Dict[str, Any]:
    """
    Convenience function to run review on findings.

    Args:
        document_text: Original document
        findings: Dict with risks, gaps, work_items, etc.
        deal_context: Optional deal context
        repository: Optional repository for question workflow
        run_id: Optional run ID for question workflow

    Returns:
        Review results dict
    """
    agent = ReviewAgent(repository=repository, run_id=run_id)
    return agent.review(document_text, findings, deal_context)
