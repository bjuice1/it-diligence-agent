"""
Simple data models for IT DD Synthesizer.
These hold the structured data parsed from Tolt outputs.
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict
from datetime import datetime


@dataclass
class Application:
    """Application from Tolt inventory export."""
    id: str = ""
    name: str = ""
    vendor: str = ""
    category: str = ""
    hosting: str = ""  # On-Premise, SaaS, Cloud, Hybrid, Unknown
    criticality: str = ""  # Critical, High, Medium, Low, Unknown
    version: str = ""
    user_count: str = ""
    eol_status: str = ""  # Populated by EOL lookup
    eol_date: str = ""
    source: str = ""  # Source document
    notes: str = ""

    # Populated during synthesis
    technical_debt: List[str] = field(default_factory=list)
    risks: List[str] = field(default_factory=list)


@dataclass
class Risk:
    """Risk finding."""
    id: str = ""
    title: str = ""
    description: str = ""
    severity: str = ""  # Critical, High, Medium, Low
    domain: str = ""  # Applications, Infrastructure, Security, etc.
    category: str = ""  # Standalone Viability, Integration, Cost, Compliance
    evidence: str = ""
    mitigation: str = ""
    cost_estimate: str = ""
    source: str = ""


@dataclass
class FollowUpQuestion:
    """Question for management session."""
    id: str = ""
    question: str = ""
    why_it_matters: str = ""
    priority: str = ""  # Must Have, Important, Nice to Have
    target: str = ""  # CIO, IT Ops, Management, etc.
    domain: str = ""


@dataclass
class CostItem:
    """Cost line item."""
    id: str = ""
    category: str = ""  # Integration, Remediation, Catch-up, Ongoing
    description: str = ""
    low_estimate: int = 0
    high_estimate: int = 0
    timing: str = ""  # Pre-close, Day 1, 90 Days, Year 1
    driver: str = ""  # What risk/finding drives this cost
    assumptions: str = ""


@dataclass
class DomainSummary:
    """Summary for a single domain."""
    domain: str = ""
    maturity: str = ""  # Low, Medium, High
    key_findings: List[str] = field(default_factory=list)
    risk_count: int = 0
    critical_risks: int = 0
    top_risks: List[str] = field(default_factory=list)
    open_questions: List[str] = field(default_factory=list)


@dataclass
class SynthesisResult:
    """Complete synthesis output."""
    # Metadata
    target_company: str = ""
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    # Inventories
    applications: List[Application] = field(default_factory=list)

    # Findings
    risks: List[Risk] = field(default_factory=list)
    questions: List[FollowUpQuestion] = field(default_factory=list)

    # Summaries
    domain_summaries: Dict[str, DomainSummary] = field(default_factory=dict)

    # Costs
    cost_items: List[CostItem] = field(default_factory=list)
    total_one_time_low: int = 0
    total_one_time_high: int = 0
    total_ongoing_low: int = 0
    total_ongoing_high: int = 0

    # Scores
    overall_maturity: str = ""
    integration_complexity: str = ""  # Low, Medium, High, Very High
    standalone_viable: str = ""  # Yes, With Constraints, No

    # Executive summary components
    overall_assessment: str = ""
    key_findings: List[str] = field(default_factory=list)
    critical_risks: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
