"""
Core Synthesizer - Parses Tolt outputs and creates structured findings.

This is the main orchestration module that:
1. Parses CSV/text inputs from Tolt
2. Assigns consistent IDs
3. Runs EOL lookups
4. Calculates costs
5. Produces SynthesisResult for reporting
"""
import csv
import re
from io import StringIO
from typing import List, Dict, Optional
from datetime import datetime

from .models import (
    Application, Risk, FollowUpQuestion, CostItem,
    DomainSummary, SynthesisResult
)
from .eol_data import lookup_eol, is_eol_risk
from .cost_engine import calculate_costs


class ITDDSynthesizer:
    """Main synthesizer class."""

    def __init__(self, target_company: str = "Target Company"):
        self.target_company = target_company
        self.result = SynthesisResult(target_company=target_company)

        # ID counters
        self._counters = {
            "app": 0,
            "risk": 0,
            "question": 0,
            "cost": 0,
        }

    def _next_id(self, prefix: str) -> str:
        """Generate next ID for a type."""
        self._counters[prefix] = self._counters.get(prefix, 0) + 1
        prefixes = {"app": "APP", "risk": "R", "question": "Q", "cost": "COST"}
        return f"{prefixes.get(prefix, prefix.upper())}-{self._counters[prefix]:03d}"

    # =========================================================================
    # Input Parsers
    # =========================================================================

    def parse_applications_csv(self, csv_content: str) -> List[Application]:
        """
        Parse application inventory from CSV.

        Expected columns (flexible matching):
        - name/application/app name
        - vendor
        - category/type
        - hosting/hosting model
        - criticality/business criticality
        - version
        - user count/users
        - source/source document
        """
        apps = []
        reader = csv.DictReader(StringIO(csv_content))

        # Normalize column names
        def find_col(row: Dict, options: List[str]) -> str:
            for opt in options:
                for key in row.keys():
                    if opt.lower() in key.lower():
                        return row[key] or ""
            return ""

        for row in reader:
            app = Application(
                id=self._next_id("app"),
                name=find_col(row, ["name", "application", "app"]),
                vendor=find_col(row, ["vendor"]),
                category=find_col(row, ["category", "type"]),
                hosting=find_col(row, ["hosting", "hosting model", "deployment"]),
                criticality=find_col(row, ["criticality", "business criticality", "priority"]),
                version=find_col(row, ["version"]),
                user_count=find_col(row, ["user", "users", "user count"]),
                source=find_col(row, ["source", "document"]),
            )

            # Run EOL lookup
            eol_info = lookup_eol(app.name, app.version)
            if not eol_info and app.vendor:
                eol_info = lookup_eol(f"{app.vendor} {app.name}", app.version)

            if eol_info:
                app.eol_status = eol_info["status"]
                app.eol_date = eol_info["eol"]

            if app.name:  # Only add if we have a name
                apps.append(app)

        self.result.applications = apps
        return apps

    def parse_risks_csv(self, csv_content: str) -> List[Risk]:
        """
        Parse risks from CSV.

        Expected columns:
        - title/risk/risk title
        - description
        - severity/risk level
        - domain/area/category
        - evidence/source
        - mitigation/recommendation
        """
        risks = []
        reader = csv.DictReader(StringIO(csv_content))

        def find_col(row: Dict, options: List[str]) -> str:
            for opt in options:
                for key in row.keys():
                    if opt.lower() in key.lower():
                        return row[key] or ""
            return ""

        for row in reader:
            risk = Risk(
                id=self._next_id("risk"),
                title=find_col(row, ["title", "risk title", "risk"]),
                description=find_col(row, ["description", "details"]),
                severity=self._normalize_severity(find_col(row, ["severity", "risk level", "level"])),
                domain=find_col(row, ["domain", "area", "category"]),
                evidence=find_col(row, ["evidence", "source", "quote"]),
                mitigation=find_col(row, ["mitigation", "recommendation", "remediation"]),
            )

            if risk.title:
                risks.append(risk)

        self.result.risks = risks
        return risks

    def parse_questions_csv(self, csv_content: str) -> List[FollowUpQuestion]:
        """Parse follow-up questions from CSV."""
        questions = []
        reader = csv.DictReader(StringIO(csv_content))

        def find_col(row: Dict, options: List[str]) -> str:
            for opt in options:
                for key in row.keys():
                    if opt.lower() in key.lower():
                        return row[key] or ""
            return ""

        for row in reader:
            q = FollowUpQuestion(
                id=self._next_id("question"),
                question=find_col(row, ["question"]),
                why_it_matters=find_col(row, ["why", "matters", "reason"]),
                priority=find_col(row, ["priority"]),
                target=find_col(row, ["target", "who", "audience"]),
                domain=find_col(row, ["domain", "area"]),
            )

            if q.question:
                questions.append(q)

        self.result.questions = questions
        return questions

    def _normalize_severity(self, severity: str) -> str:
        """Normalize severity to standard values."""
        s = severity.lower().strip()
        if s in ["critical", "crit", "1"]:
            return "Critical"
        elif s in ["high", "h", "2"]:
            return "High"
        elif s in ["medium", "med", "m", "moderate", "3"]:
            return "Medium"
        elif s in ["low", "l", "4"]:
            return "Low"
        return severity.title() if severity else "Medium"

    # =========================================================================
    # Text Parsers (for pasted content)
    # =========================================================================

    def parse_applications_text(self, text: str) -> List[Application]:
        """
        Parse applications from plain text or markdown table.
        Attempts to extract structured data from less structured input.
        """
        apps = []

        # Try to detect markdown table
        if "|" in text:
            lines = text.strip().split("\n")
            header_line = None
            for i, line in enumerate(lines):
                if "|" in line and "---" not in line:
                    if header_line is None:
                        header_line = i
                        headers = [h.strip().lower() for h in line.split("|") if h.strip()]
                    else:
                        values = [v.strip() for v in line.split("|") if v.strip()]
                        if len(values) >= len(headers):
                            row = dict(zip(headers, values))
                            app = Application(
                                id=self._next_id("app"),
                                name=row.get("application", row.get("name", "")),
                                vendor=row.get("vendor", ""),
                                category=row.get("category", row.get("type", "")),
                                hosting=row.get("hosting", ""),
                                criticality=row.get("criticality", ""),
                                version=row.get("version", ""),
                            )

                            # EOL lookup
                            eol_info = lookup_eol(app.name, app.version)
                            if eol_info:
                                app.eol_status = eol_info["status"]
                                app.eol_date = eol_info["eol"]

                            if app.name:
                                apps.append(app)

        self.result.applications.extend(apps)
        return apps

    # =========================================================================
    # Analysis Functions
    # =========================================================================

    def generate_eol_risks(self) -> List[Risk]:
        """Generate risk entries for applications with EOL issues."""
        eol_risks = []

        for app in self.result.applications:
            if app.eol_status in ["Past_EOL", "Approaching_EOL"]:
                severity = "Critical" if app.eol_status == "Past_EOL" else "High"
                risk = Risk(
                    id=self._next_id("risk"),
                    title=f"{app.name} {app.eol_status.replace('_', ' ')}",
                    description=f"{app.name} (version {app.version or 'unknown'}) is {app.eol_status.replace('_', ' ').lower()}. EOL date: {app.eol_date}.",
                    severity=severity,
                    domain="Applications",
                    category="Technical Debt",
                    evidence=f"Version: {app.version}, EOL: {app.eol_date}",
                    mitigation=f"Plan upgrade or migration path",
                )
                eol_risks.append(risk)
                self.result.risks.append(risk)

        return eol_risks

    def calculate_all_costs(self) -> Dict:
        """Calculate costs for all risks."""
        cost_result = calculate_costs(self.result.risks)
        self.result.cost_items = cost_result["items"]
        self.result.total_one_time_low = cost_result["total_low"]
        self.result.total_one_time_high = cost_result["total_high"]
        return cost_result

    def generate_domain_summaries(self) -> Dict[str, DomainSummary]:
        """Generate summary for each domain."""
        domains = ["Applications", "Infrastructure", "Network", "Security", "Identity", "IT Organization"]

        for domain in domains:
            domain_risks = [r for r in self.result.risks if domain.lower() in r.domain.lower()]
            critical = [r for r in domain_risks if r.severity == "Critical"]

            summary = DomainSummary(
                domain=domain,
                risk_count=len(domain_risks),
                critical_risks=len(critical),
                top_risks=[r.title for r in domain_risks[:3]],
            )
            self.result.domain_summaries[domain] = summary

        return self.result.domain_summaries

    def generate_executive_summary(self) -> Dict:
        """Generate executive summary components."""
        # Overall assessment
        critical_count = len([r for r in self.result.risks if r.severity == "Critical"])
        high_count = len([r for r in self.result.risks if r.severity == "High"])

        if critical_count > 3:
            self.result.overall_assessment = "Problematic - Significant issues requiring attention"
        elif critical_count > 0:
            self.result.overall_assessment = "Concerning - Critical issues identified"
        elif high_count > 5:
            self.result.overall_assessment = "Manageable - Multiple high-priority items"
        else:
            self.result.overall_assessment = "Clean - No critical issues identified"

        # Key findings
        self.result.key_findings = [r.title for r in self.result.risks if r.severity in ["Critical", "High"]][:5]

        # Critical risks
        self.result.critical_risks = [r.title for r in self.result.risks if r.severity == "Critical"]

        return {
            "assessment": self.result.overall_assessment,
            "key_findings": self.result.key_findings,
            "critical_risks": self.result.critical_risks,
        }

    # =========================================================================
    # Main Synthesis
    # =========================================================================

    def synthesize(self) -> SynthesisResult:
        """Run full synthesis pipeline."""
        # Generate EOL risks from applications
        self.generate_eol_risks()

        # Calculate costs
        self.calculate_all_costs()

        # Generate summaries
        self.generate_domain_summaries()
        self.generate_executive_summary()

        # Update timestamp
        self.result.generated_at = datetime.now().isoformat()

        return self.result
