"""
Open Questions Generator

Generates industry-specific and gap-driven questions for the deal team.
These questions surface critical areas that need validation during diligence.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class QuestionPriority(Enum):
    """Priority levels for diligence questions."""
    CRITICAL = "critical"  # Must answer before close
    IMPORTANT = "important"  # Should answer during diligence
    NICE_TO_HAVE = "nice_to_have"  # Helpful but not blocking


class QuestionCategory(Enum):
    """Categories of diligence questions."""
    REGULATORY = "regulatory"
    OPERATIONAL = "operational"
    FINANCIAL = "financial"
    TECHNICAL = "technical"
    INTEGRATION = "integration"
    SECURITY = "security"
    COMPLIANCE = "compliance"
    STAFFING = "staffing"


@dataclass
class OpenQuestion:
    """A question for the deal team to investigate."""
    question: str
    priority: QuestionPriority
    category: QuestionCategory
    rationale: str  # Why this question matters
    based_on_facts: List[str] = field(default_factory=list)  # Fact IDs that triggered this
    based_on_gaps: List[str] = field(default_factory=list)  # Gap IDs that triggered this
    industry_specific: bool = False  # Is this industry-specific?
    deal_type_specific: bool = False  # Is this deal-type-specific?
    suggested_sources: List[str] = field(default_factory=list)  # Where to find answers

    def to_dict(self) -> Dict[str, Any]:
        return {
            "question": self.question,
            "priority": self.priority.value,
            "category": self.category.value,
            "rationale": self.rationale,
            "based_on_facts": self.based_on_facts,
            "based_on_gaps": self.based_on_gaps,
            "industry_specific": self.industry_specific,
            "deal_type_specific": self.deal_type_specific,
            "suggested_sources": self.suggested_sources,
        }


# Industry-specific question banks
INDUSTRY_QUESTIONS = {
    "financial_services": [
        OpenQuestion(
            question="What were the findings from the most recent regulatory exam (OCC, FDIC, state)?",
            priority=QuestionPriority.CRITICAL,
            category=QuestionCategory.REGULATORY,
            rationale="Regulatory exam findings directly impact deal risk and may require remediation budgets",
            industry_specific=True,
            suggested_sources=["Regulatory exam reports", "Board minutes", "Management responses"],
        ),
        OpenQuestion(
            question="Are there any open MRAs (Matters Requiring Attention) or consent orders?",
            priority=QuestionPriority.CRITICAL,
            category=QuestionCategory.REGULATORY,
            rationale="Open regulatory actions may require resolution before close or affect deal structure",
            industry_specific=True,
            suggested_sources=["Regulatory correspondence", "Legal counsel", "Compliance officer"],
        ),
        OpenQuestion(
            question="What is the status of SOX IT general controls - any material weaknesses or significant deficiencies?",
            priority=QuestionPriority.CRITICAL,
            category=QuestionCategory.COMPLIANCE,
            rationale="SOX control deficiencies affect audit opinions and may signal IT control gaps",
            industry_specific=True,
            suggested_sources=["External audit reports", "SOX testing results", "Internal audit"],
        ),
        OpenQuestion(
            question="When was the last BSA/AML independent review and what were the findings?",
            priority=QuestionPriority.CRITICAL,
            category=QuestionCategory.COMPLIANCE,
            rationale="BSA/AML deficiencies are a top regulatory concern and can result in severe penalties",
            industry_specific=True,
            suggested_sources=["BSA audit reports", "SAR filing statistics", "Compliance program docs"],
        ),
        OpenQuestion(
            question="What is the core banking system platform, version, and support status?",
            priority=QuestionPriority.CRITICAL,
            category=QuestionCategory.TECHNICAL,
            rationale="Core banking is the foundation - unsupported versions create regulatory and operational risk",
            industry_specific=True,
            suggested_sources=["IT inventory", "Vendor contracts", "IT leadership"],
        ),
        OpenQuestion(
            question="What is the PCI-DSS compliance status and scope?",
            priority=QuestionPriority.IMPORTANT,
            category=QuestionCategory.COMPLIANCE,
            rationale="PCI non-compliance can result in fines and card network restrictions",
            industry_specific=True,
            suggested_sources=["PCI ROC/SAQ", "QSA reports", "Cardholder data inventory"],
        ),
        OpenQuestion(
            question="How are segregation of duties enforced in key financial systems?",
            priority=QuestionPriority.IMPORTANT,
            category=QuestionCategory.COMPLIANCE,
            rationale="SOD is a fundamental control for financial systems - gaps indicate control weaknesses",
            industry_specific=True,
            suggested_sources=["Access control matrices", "SOX testing", "IT audit reports"],
        ),
        OpenQuestion(
            question="What is the FFIEC cybersecurity assessment maturity level and any identified gaps?",
            priority=QuestionPriority.IMPORTANT,
            category=QuestionCategory.SECURITY,
            rationale="FFIEC CAT is the regulatory standard for financial institution cybersecurity",
            industry_specific=True,
            suggested_sources=["FFIEC CAT results", "Cybersecurity program docs", "Board reports"],
        ),
    ],
    "healthcare": [
        OpenQuestion(
            question="When was the last HIPAA risk assessment and what were the findings?",
            priority=QuestionPriority.CRITICAL,
            category=QuestionCategory.COMPLIANCE,
            rationale="HIPAA risk assessment is required and findings indicate compliance posture",
            industry_specific=True,
            suggested_sources=["HIPAA risk assessment report", "Privacy officer", "Remediation plans"],
        ),
        OpenQuestion(
            question="Have there been any PHI breaches or OCR complaints in the past 3 years?",
            priority=QuestionPriority.CRITICAL,
            category=QuestionCategory.COMPLIANCE,
            rationale="Breach history indicates security posture and potential ongoing liability",
            industry_specific=True,
            suggested_sources=["Breach notification records", "OCR correspondence", "Legal counsel"],
        ),
        OpenQuestion(
            question="What is the BAA inventory status - are all vendors with PHI access covered?",
            priority=QuestionPriority.CRITICAL,
            category=QuestionCategory.COMPLIANCE,
            rationale="Missing BAAs create compliance gaps and shared liability exposure",
            industry_specific=True,
            suggested_sources=["Vendor inventory", "BAA tracker", "Privacy officer"],
        ),
        OpenQuestion(
            question="What EMR/EHR system is used and what is its support status?",
            priority=QuestionPriority.CRITICAL,
            category=QuestionCategory.TECHNICAL,
            rationale="EMR is the clinical foundation - migrations are high-risk, multi-year projects",
            industry_specific=True,
            suggested_sources=["IT inventory", "Vendor contracts", "CMIO/CIO"],
        ),
        OpenQuestion(
            question="How is PHI access logged and monitored?",
            priority=QuestionPriority.IMPORTANT,
            category=QuestionCategory.SECURITY,
            rationale="Access logging is a HIPAA requirement and critical for breach detection",
            industry_specific=True,
            suggested_sources=["Audit log configuration", "SIEM dashboards", "Privacy officer"],
        ),
        OpenQuestion(
            question="What is the status of Meaningful Use / MIPS attestation?",
            priority=QuestionPriority.IMPORTANT,
            category=QuestionCategory.COMPLIANCE,
            rationale="Failed attestation affects Medicare reimbursement",
            industry_specific=True,
            suggested_sources=["CMS attestation records", "Quality team", "Revenue cycle"],
        ),
    ],
    "manufacturing": [
        OpenQuestion(
            question="Is the OT network segmented from the IT network?",
            priority=QuestionPriority.CRITICAL,
            category=QuestionCategory.SECURITY,
            rationale="Flat networks with OT and IT commingled create critical security exposure",
            industry_specific=True,
            suggested_sources=["Network diagrams", "OT team", "Security assessments"],
        ),
        OpenQuestion(
            question="What is the age and support status of production control systems (PLCs, SCADA)?",
            priority=QuestionPriority.CRITICAL,
            category=QuestionCategory.TECHNICAL,
            rationale="Unsupported OT systems cannot be patched and create safety/security risks",
            industry_specific=True,
            suggested_sources=["OT asset inventory", "Maintenance records", "Plant engineers"],
        ),
        OpenQuestion(
            question="What quality certifications are held (ISO 9001, IATF 16949, AS9100)?",
            priority=QuestionPriority.CRITICAL,
            category=QuestionCategory.COMPLIANCE,
            rationale="Certification status affects customer relationships and market access",
            industry_specific=True,
            suggested_sources=["Certification records", "Audit reports", "Quality team"],
        ),
        OpenQuestion(
            question="Are there any open OSHA citations or EPA violations?",
            priority=QuestionPriority.CRITICAL,
            category=QuestionCategory.COMPLIANCE,
            rationale="Open citations indicate safety/environmental issues and potential liability",
            industry_specific=True,
            suggested_sources=["OSHA records", "EPA correspondence", "EHS team"],
        ),
        OpenQuestion(
            question="What MES (Manufacturing Execution System) is used and how integrated is it?",
            priority=QuestionPriority.IMPORTANT,
            category=QuestionCategory.TECHNICAL,
            rationale="MES maturity indicates production visibility and traceability capability",
            industry_specific=True,
            suggested_sources=["IT inventory", "Plant operations", "Production reports"],
        ),
    ],
    "defense_contractor": [
        OpenQuestion(
            question="What is the current CMMC certification level and target level?",
            priority=QuestionPriority.CRITICAL,
            category=QuestionCategory.COMPLIANCE,
            rationale="CMMC certification is required for DoD contracts - non-compliance = loss of contracts",
            industry_specific=True,
            suggested_sources=["CMMC assessment", "SPRS score", "Contracts team"],
        ),
        OpenQuestion(
            question="Is there a current NIST 800-171 SSP and POA&M?",
            priority=QuestionPriority.CRITICAL,
            category=QuestionCategory.COMPLIANCE,
            rationale="SSP and POA&M are required for CUI handling and CMMC readiness",
            industry_specific=True,
            suggested_sources=["SSP document", "POA&M tracker", "FSO/ISSO"],
        ),
        OpenQuestion(
            question="Are there any CUI spillage incidents in the past 2 years?",
            priority=QuestionPriority.CRITICAL,
            category=QuestionCategory.SECURITY,
            rationale="CUI incidents indicate control gaps and may affect contract eligibility",
            industry_specific=True,
            suggested_sources=["Incident reports", "FSO records", "Contracting officer"],
        ),
        OpenQuestion(
            question="What is the facility clearance level and any recent issues?",
            priority=QuestionPriority.CRITICAL,
            category=QuestionCategory.COMPLIANCE,
            rationale="FCL status directly affects ability to perform classified work",
            industry_specific=True,
            suggested_sources=["DCSA records", "FSO", "Security clearance database"],
        ),
    ],
}

# Carve-out specific questions
CARVEOUT_QUESTIONS = [
    OpenQuestion(
        question="What IT services does the target currently receive from the parent company?",
        priority=QuestionPriority.CRITICAL,
        category=QuestionCategory.OPERATIONAL,
        rationale="Parent-provided services must be replaced or covered by TSA",
        deal_type_specific=True,
        suggested_sources=["IT leadership", "Shared services agreements", "Cost allocations"],
    ),
    OpenQuestion(
        question="What is the anticipated TSA duration and cost for each IT service?",
        priority=QuestionPriority.CRITICAL,
        category=QuestionCategory.FINANCIAL,
        rationale="TSA costs and duration directly affect deal economics and integration timeline",
        deal_type_specific=True,
        suggested_sources=["Deal team", "IT leadership", "Finance"],
    ),
    OpenQuestion(
        question="Can the target operate on Day 1 without parent support? What are the gaps?",
        priority=QuestionPriority.CRITICAL,
        category=QuestionCategory.OPERATIONAL,
        rationale="Day 1 readiness determines whether business can continue without disruption",
        deal_type_specific=True,
        suggested_sources=["IT leadership", "Operations team", "Separation planning docs"],
    ),
    OpenQuestion(
        question="Are there shared systems where data needs to be carved out?",
        priority=QuestionPriority.CRITICAL,
        category=QuestionCategory.TECHNICAL,
        rationale="Data separation is often complex and can delay close",
        deal_type_specific=True,
        suggested_sources=["IT architects", "Data owners", "ERP team"],
    ),
    OpenQuestion(
        question="What contracts are in the parent's name that need to be transferred or replaced?",
        priority=QuestionPriority.IMPORTANT,
        category=QuestionCategory.FINANCIAL,
        rationale="Contract assignment affects costs and may require vendor consent",
        deal_type_specific=True,
        suggested_sources=["Procurement", "Legal", "Vendor contracts"],
    ),
    OpenQuestion(
        question="Is the target on the parent's enterprise agreements (Microsoft, SAP, Oracle)?",
        priority=QuestionPriority.IMPORTANT,
        category=QuestionCategory.FINANCIAL,
        rationale="Loss of enterprise pricing typically increases license costs 1.5-2x",
        deal_type_specific=True,
        suggested_sources=["IT procurement", "License inventory", "Parent IT"],
    ),
]


class OpenQuestionGenerator:
    """Generates open questions based on industry, deal type, facts, and gaps."""

    def __init__(self, industry: Optional[str] = None, sub_industry: Optional[str] = None,
                 deal_type: str = "bolt_on"):
        self.industry = industry
        self.sub_industry = sub_industry
        self.deal_type = deal_type

    def generate_questions(self, facts: List[Any] = None, gaps: List[Any] = None) -> List[OpenQuestion]:
        """
        Generate all relevant open questions.

        Args:
            facts: List of extracted facts (for context-aware questions)
            gaps: List of identified gaps (for gap-driven questions)

        Returns:
            List of OpenQuestion objects, sorted by priority
        """
        questions = []

        # Add industry-specific questions
        questions.extend(self.get_industry_questions())

        # Add deal-type specific questions (carve-out)
        if self.deal_type == "carve_out":
            questions.extend(CARVEOUT_QUESTIONS)

        # Add gap-driven questions
        if gaps:
            questions.extend(self.generate_gap_questions(gaps))

        # Sort by priority
        priority_order = {
            QuestionPriority.CRITICAL: 0,
            QuestionPriority.IMPORTANT: 1,
            QuestionPriority.NICE_TO_HAVE: 2,
        }
        questions.sort(key=lambda q: priority_order.get(q.priority, 99))

        return questions

    def get_industry_questions(self) -> List[OpenQuestion]:
        """Get questions specific to the configured industry."""
        if not self.industry:
            return []

        return INDUSTRY_QUESTIONS.get(self.industry, [])

    def generate_gap_questions(self, gaps: List[Any]) -> List[OpenQuestion]:
        """Generate questions based on identified gaps."""
        questions = []

        for gap in gaps:
            # Extract gap details
            gap_text = getattr(gap, 'item', str(gap)) if hasattr(gap, 'item') else str(gap)
            gap_id = getattr(gap, 'id', None)
            domain = getattr(gap, 'domain', 'unknown')

            # Generate a question from the gap
            question = OpenQuestion(
                question=f"Can you provide documentation for: {gap_text}?",
                priority=QuestionPriority.IMPORTANT,
                category=self._categorize_gap(gap_text, domain),
                rationale=f"This information was not found in provided documents but is needed for complete assessment",
                based_on_gaps=[gap_id] if gap_id else [],
                industry_specific=False,
                suggested_sources=["IT leadership", "Operations team", "Documentation repository"],
            )
            questions.append(question)

        return questions

    def _categorize_gap(self, gap_text: str, domain: str) -> QuestionCategory:
        """Determine the category for a gap-driven question."""
        gap_lower = gap_text.lower()

        if any(term in gap_lower for term in ['security', 'vulnerability', 'threat', 'cyber']):
            return QuestionCategory.SECURITY
        elif any(term in gap_lower for term in ['compliance', 'audit', 'regulation', 'sox', 'hipaa']):
            return QuestionCategory.COMPLIANCE
        elif any(term in gap_lower for term in ['cost', 'budget', 'spend', 'license']):
            return QuestionCategory.FINANCIAL
        elif any(term in gap_lower for term in ['staff', 'team', 'fte', 'headcount']):
            return QuestionCategory.STAFFING
        elif domain in ['infrastructure', 'network', 'applications']:
            return QuestionCategory.TECHNICAL
        else:
            return QuestionCategory.OPERATIONAL

    def get_regulatory_questions(self) -> List[OpenQuestion]:
        """Get regulatory-focused questions for the industry."""
        if not self.industry:
            return []

        industry_qs = INDUSTRY_QUESTIONS.get(self.industry, [])
        return [q for q in industry_qs if q.category == QuestionCategory.REGULATORY]


def generate_open_questions_for_deal(
    industry: Optional[str],
    sub_industry: Optional[str],
    deal_type: str,
    gaps: List[Any] = None
) -> List[Dict[str, Any]]:
    """
    Convenience function to generate open questions for a deal.

    Returns list of question dicts ready for JSON serialization.
    """
    generator = OpenQuestionGenerator(
        industry=industry,
        sub_industry=sub_industry,
        deal_type=deal_type
    )

    questions = generator.generate_questions(gaps=gaps)
    return [q.to_dict() for q in questions]
