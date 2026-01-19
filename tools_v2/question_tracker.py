"""
Question Tracker - Open vs Closed Questions

Tracks which must-answer questions have been addressed by extracted facts
and which remain open (gaps requiring follow-up).
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple
from enum import Enum
import re


class QuestionStatus(Enum):
    """Status of a must-answer question."""
    OPEN = "open"           # No facts address this
    PARTIAL = "partial"     # Some relevant facts but not fully answered
    CLOSED = "closed"       # Clearly answered by facts
    GAP_FLAGGED = "gap"     # Explicitly flagged as a gap


@dataclass
class TrackedQuestion:
    """A question being tracked for coverage."""
    question_id: str
    domain: str
    function: str
    question_text: str
    status: QuestionStatus = QuestionStatus.OPEN
    supporting_facts: List[str] = field(default_factory=list)
    confidence: float = 0.0  # 0-1 confidence that question is answered
    notes: str = ""


@dataclass
class QuestionCoverage:
    """Coverage summary for a domain/function."""
    domain: str
    function: str
    total_questions: int
    closed: int
    partial: int
    open: int
    gap_flagged: int
    coverage_pct: float


class QuestionTracker:
    """
    Tracks must-answer questions and their coverage by extracted facts.

    Usage:
        tracker = QuestionTracker()
        tracker.load_questions_from_criteria()
        tracker.match_facts_to_questions(fact_store)
        report = tracker.get_coverage_report()
    """

    def __init__(self):
        self.questions: Dict[str, TrackedQuestion] = {}
        self._fact_index: Dict[str, Set[str]] = {}  # keyword -> question_ids

    def load_questions_from_criteria(self):
        """Load must-answer questions from function_deep_dive criteria."""
        try:
            from prompts.shared.function_deep_dive import get_all_criteria
            all_criteria = get_all_criteria()

            q_id = 0
            for domain, functions in all_criteria.items():
                for func_name, criteria in functions.items():
                    for question in criteria.must_answer_questions:
                        q_id += 1
                        question_id = f"Q-{domain[:3].upper()}-{q_id:03d}"

                        self.questions[question_id] = TrackedQuestion(
                            question_id=question_id,
                            domain=domain,
                            function=func_name,
                            question_text=question
                        )

                        # Index keywords for matching
                        self._index_question(question_id, question)

            return len(self.questions)
        except ImportError:
            return 0

    def _index_question(self, question_id: str, question_text: str):
        """Index question keywords for fact matching."""
        # Extract key terms (nouns, technical terms)
        words = re.findall(r'\b[A-Za-z][a-z]{2,}\b', question_text.lower())
        # Filter common words
        stopwords = {'what', 'where', 'when', 'how', 'many', 'much', 'does', 'have',
                     'are', 'the', 'for', 'and', 'with', 'this', 'that', 'from'}
        keywords = [w for w in words if w not in stopwords]

        for kw in keywords:
            if kw not in self._fact_index:
                self._fact_index[kw] = set()
            self._fact_index[kw].add(question_id)

    def match_facts_to_questions(self, fact_store) -> int:
        """Match extracted facts to questions and update status."""
        matches_found = 0

        for fact in fact_store.facts:
            content = fact.content.lower()
            domain = fact.domain

            # Find potentially matching questions
            matching_questions = set()
            words = re.findall(r'\b[a-z]{3,}\b', content)

            for word in words:
                if word in self._fact_index:
                    matching_questions.update(self._fact_index[word])

            # Score each potential match
            for q_id in matching_questions:
                question = self.questions.get(q_id)
                if not question:
                    continue

                # Must be same domain
                if question.domain != domain:
                    continue

                # Calculate relevance score
                q_words = set(re.findall(r'\b[a-z]{3,}\b', question.question_text.lower()))
                f_words = set(words)
                overlap = len(q_words & f_words)
                score = overlap / max(len(q_words), 1)

                if score > 0.3:  # Threshold for relevance
                    question.supporting_facts.append(fact.fact_id)
                    question.confidence = max(question.confidence, min(score, 1.0))
                    matches_found += 1

        # Update statuses based on matches
        self._update_statuses()

        return matches_found

    def match_gaps_to_questions(self, fact_store) -> int:
        """Match flagged gaps to questions."""
        gaps_matched = 0

        for gap in fact_store.gaps:
            content = gap.description.lower()
            domain = gap.domain

            # Find matching questions
            for q_id, question in self.questions.items():
                if question.domain != domain:
                    continue

                q_words = set(re.findall(r'\b[a-z]{3,}\b', question.question_text.lower()))
                g_words = set(re.findall(r'\b[a-z]{3,}\b', content))
                overlap = len(q_words & g_words)

                if overlap >= 2:  # At least 2 keyword matches
                    question.status = QuestionStatus.GAP_FLAGGED
                    question.notes = f"Gap flagged: {gap.description[:100]}"
                    gaps_matched += 1

        return gaps_matched

    def _update_statuses(self):
        """Update question statuses based on supporting facts."""
        for question in self.questions.values():
            if question.status == QuestionStatus.GAP_FLAGGED:
                continue  # Don't override explicit gaps

            if len(question.supporting_facts) == 0:
                question.status = QuestionStatus.OPEN
            elif question.confidence >= 0.6:
                question.status = QuestionStatus.CLOSED
            else:
                question.status = QuestionStatus.PARTIAL

    def get_coverage_report(self) -> Dict[str, any]:
        """Get comprehensive coverage report."""
        # Overall stats
        total = len(self.questions)
        closed = sum(1 for q in self.questions.values() if q.status == QuestionStatus.CLOSED)
        partial = sum(1 for q in self.questions.values() if q.status == QuestionStatus.PARTIAL)
        open_q = sum(1 for q in self.questions.values() if q.status == QuestionStatus.OPEN)
        gaps = sum(1 for q in self.questions.values() if q.status == QuestionStatus.GAP_FLAGGED)

        # By domain
        by_domain = {}
        for question in self.questions.values():
            if question.domain not in by_domain:
                by_domain[question.domain] = {
                    "total": 0, "closed": 0, "partial": 0, "open": 0, "gap": 0
                }
            by_domain[question.domain]["total"] += 1
            by_domain[question.domain][question.status.value] += 1

        # By function
        by_function = {}
        for question in self.questions.values():
            key = f"{question.domain}:{question.function}"
            if key not in by_function:
                by_function[key] = {
                    "domain": question.domain,
                    "function": question.function,
                    "total": 0, "closed": 0, "partial": 0, "open": 0, "gap": 0
                }
            by_function[key]["total"] += 1
            by_function[key][question.status.value] += 1

        return {
            "summary": {
                "total_questions": total,
                "closed": closed,
                "partial": partial,
                "open": open_q,
                "gap_flagged": gaps,
                "coverage_pct": (closed + partial * 0.5) / max(total, 1) * 100
            },
            "by_domain": by_domain,
            "by_function": by_function
        }

    def get_open_questions(self, domain: Optional[str] = None) -> List[TrackedQuestion]:
        """Get list of open (unanswered) questions."""
        questions = [
            q for q in self.questions.values()
            if q.status in (QuestionStatus.OPEN, QuestionStatus.GAP_FLAGGED)
        ]

        if domain:
            questions = [q for q in questions if q.domain == domain]

        return sorted(questions, key=lambda x: (x.domain, x.function))

    def get_closed_questions(self, domain: Optional[str] = None) -> List[TrackedQuestion]:
        """Get list of closed (answered) questions with supporting facts."""
        questions = [
            q for q in self.questions.values()
            if q.status in (QuestionStatus.CLOSED, QuestionStatus.PARTIAL)
        ]

        if domain:
            questions = [q for q in questions if q.domain == domain]

        return sorted(questions, key=lambda x: -x.confidence)

    def get_vdr_requests_for_open_questions(self) -> List[Dict]:
        """Generate VDR requests for open questions."""
        requests = []

        for question in self.get_open_questions():
            requests.append({
                "question_id": question.question_id,
                "domain": question.domain,
                "function": question.function,
                "question": question.question_text,
                "suggested_documents": _suggest_documents_for_question(question),
                "priority": "high" if question.status == QuestionStatus.GAP_FLAGGED else "medium"
            })

        return requests

    def format_for_display(self) -> str:
        """Format coverage report for display."""
        report = self.get_coverage_report()
        summary = report["summary"]

        lines = [
            "=" * 60,
            "QUESTION COVERAGE REPORT",
            "=" * 60,
            "",
            f"Overall Coverage: {summary['coverage_pct']:.1f}%",
            f"  Closed:      {summary['closed']:3d} questions",
            f"  Partial:     {summary['partial']:3d} questions",
            f"  Open:        {summary['open']:3d} questions",
            f"  Gap Flagged: {summary['gap_flagged']:3d} questions",
            f"  Total:       {summary['total_questions']:3d} questions",
            "",
            "BY DOMAIN:",
            "-" * 40,
        ]

        for domain, stats in report["by_domain"].items():
            pct = (stats["closed"] + stats["partial"] * 0.5) / max(stats["total"], 1) * 100
            lines.append(f"  {domain:20s}: {pct:5.1f}% ({stats['closed']}/{stats['total']} closed)")

        lines.extend([
            "",
            "OPEN QUESTIONS REQUIRING FOLLOW-UP:",
            "-" * 40,
        ])

        for q in self.get_open_questions()[:10]:  # Top 10
            status_icon = "⚠️" if q.status == QuestionStatus.GAP_FLAGGED else "❓"
            lines.append(f"  {status_icon} [{q.domain}] {q.question_text[:60]}...")

        if len(self.get_open_questions()) > 10:
            lines.append(f"  ... and {len(self.get_open_questions()) - 10} more open questions")

        return "\n".join(lines)


def _suggest_documents_for_question(question: TrackedQuestion) -> List[str]:
    """Suggest documents that might answer a question."""
    suggestions = []

    # Map keywords to document types
    keyword_docs = {
        "headcount": ["IT Organization Chart", "IT Budget", "HR Data"],
        "vendor": ["Vendor Contracts", "MSP Agreements", "Service Agreements"],
        "license": ["Software License Inventory", "Enterprise Agreements", "Renewal Schedule"],
        "disaster": ["DR Plan", "BCP Documentation", "DR Test Results"],
        "security": ["Security Assessment", "Audit Reports", "Compliance Certifications"],
        "application": ["Application Inventory", "CMDB Extract", "Architecture Diagrams"],
        "infrastructure": ["Infrastructure Inventory", "Data Center Documentation", "Cloud Bills"],
        "contract": ["Vendor Contracts", "Master Agreements", "Renewal Schedule"],
        "cost": ["IT Budget", "Cost Allocation", "Vendor Invoices"],
    }

    q_lower = question.question_text.lower()
    for keyword, docs in keyword_docs.items():
        if keyword in q_lower:
            suggestions.extend(docs)

    return list(set(suggestions))[:3]  # Top 3 unique


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    'QuestionStatus',
    'TrackedQuestion',
    'QuestionCoverage',
    'QuestionTracker',
]
