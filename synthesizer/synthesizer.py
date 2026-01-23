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
    # PHASE 5 IMPROVEMENTS (Points 86-90)
    # =========================================================================

    def generate_coherent_narrative(self, section_order: Optional[List[str]] = None) -> str:
        """
        Point 86: Generate a coherent narrative with smooth transitions.

        Creates a flowing narrative that connects sections logically.

        Args:
            section_order: Optional custom order for sections

        Returns:
            Markdown-formatted narrative string
        """
        default_order = [
            "executive_summary",
            "critical_risks",
            "domain_analysis",
            "integration_impact",
            "recommendations",
            "next_steps"
        ]
        order = section_order or default_order

        # Transition phrases for narrative flow
        transitions = {
            "executive_summary": "",
            "critical_risks": "Building on the overall assessment, the following critical risks require immediate attention:",
            "domain_analysis": "Looking deeper into each domain, the analysis reveals:",
            "integration_impact": "From an integration perspective, these findings have significant implications:",
            "recommendations": "Based on the identified risks and analysis, we recommend the following actions:",
            "next_steps": "To move forward effectively, the deal team should focus on:"
        }

        sections = []

        for section in order:
            transition = transitions.get(section, "")
            content = self._generate_section_content(section)

            if content:
                if transition:
                    sections.append(f"\n{transition}\n\n{content}")
                else:
                    sections.append(content)

        return "\n".join(sections)

    def _generate_section_content(self, section: str) -> str:
        """Generate content for a specific narrative section."""
        if section == "executive_summary":
            return self._generate_exec_summary_section()
        elif section == "critical_risks":
            return self._generate_critical_risks_section()
        elif section == "domain_analysis":
            return self._generate_domain_analysis_section()
        elif section == "integration_impact":
            return self._generate_integration_impact_section()
        elif section == "recommendations":
            return self._generate_recommendations_section()
        elif section == "next_steps":
            return self._generate_next_steps_section()
        return ""

    def _generate_exec_summary_section(self) -> str:
        """Generate executive summary section."""
        assessment = self.result.overall_assessment or "Assessment pending"
        critical_count = len([r for r in self.result.risks if r.severity == "Critical"])
        high_count = len([r for r in self.result.risks if r.severity == "High"])

        return f"""## Executive Summary

**Overall IT Assessment:** {assessment}

The IT due diligence review of {self.target_company} identified {len(self.result.risks)} risks across {len(self.result.domain_summaries)} domains. Of these, {critical_count} are critical and {high_count} are high severity.

**Estimated One-Time Integration Cost:** ${self.result.total_one_time_low:,.0f} - ${self.result.total_one_time_high:,.0f}
"""

    def _generate_critical_risks_section(self) -> str:
        """Generate critical risks section."""
        critical = [r for r in self.result.risks if r.severity == "Critical"]
        if not critical:
            return "### Critical Risks\n\nNo critical risks identified."

        lines = ["### Critical Risks\n"]
        for i, risk in enumerate(critical[:5], 1):
            lines.append(f"{i}. **{risk.title}** ({risk.domain})")
            lines.append(f"   - {risk.description}")
            if risk.mitigation:
                lines.append(f"   - *Mitigation:* {risk.mitigation}")
            lines.append("")

        return "\n".join(lines)

    def _generate_domain_analysis_section(self) -> str:
        """Generate domain analysis section."""
        lines = ["### Domain Analysis\n"]

        for domain, summary in self.result.domain_summaries.items():
            status_icon = "🔴" if summary.critical_risks > 0 else "🟡" if summary.risk_count > 3 else "🟢"
            lines.append(f"**{domain}** {status_icon}")
            lines.append(f"- {summary.risk_count} risks identified ({summary.critical_risks} critical)")
            if summary.top_risks:
                lines.append(f"- Key issues: {', '.join(summary.top_risks[:2])}")
            lines.append("")

        return "\n".join(lines)

    def _generate_integration_impact_section(self) -> str:
        """Generate integration impact section."""
        return f"""### Integration Impact

**Cost Impact:** The estimated integration costs of ${self.result.total_one_time_low:,.0f} - ${self.result.total_one_time_high:,.0f} should be factored into deal economics.

**Timeline Considerations:** Critical risks require immediate attention to ensure Day 1 readiness. Technical debt items may extend the integration timeline.

**Resource Requirements:** Based on the scope of findings, dedicated integration resources will be needed across infrastructure, applications, and security domains.
"""

    def _generate_recommendations_section(self) -> str:
        """Generate recommendations section."""
        lines = ["### Key Recommendations\n"]

        # Prioritize recommendations based on risk severity
        prioritized = sorted(self.result.risks, key=lambda r: (
            {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}.get(r.severity, 4)
        ))

        for i, risk in enumerate(prioritized[:5], 1):
            if risk.mitigation:
                lines.append(f"{i}. {risk.mitigation}")

        return "\n".join(lines)

    def _generate_next_steps_section(self) -> str:
        """Generate next steps section."""
        lines = ["### Next Steps\n"]

        # Generate actionable next steps
        if self.result.questions:
            lines.append("**Information Requests:**")
            for q in self.result.questions[:3]:
                lines.append(f"- {q.question}")
            lines.append("")

        lines.append("**Immediate Actions:**")
        lines.append("1. Review and validate critical risks with target IT team")
        lines.append("2. Develop Day 1 readiness checklist")
        lines.append("3. Finalize TSA scope and duration estimates")

        return "\n".join(lines)

    def generate_one_page_executive_summary(self) -> str:
        """
        Point 87: Auto-generate a 1-page executive summary.

        Creates a concise executive summary suitable for leadership review.

        Returns:
            Markdown-formatted one-page summary
        """
        critical_risks = [r for r in self.result.risks if r.severity == "Critical"]
        high_risks = [r for r in self.result.risks if r.severity == "High"]

        # Determine overall rating
        if len(critical_risks) > 3:
            rating = "🔴 HIGH RISK"
            rating_text = "Significant concerns requiring deal structure consideration"
        elif len(critical_risks) > 0:
            rating = "🟠 MODERATE RISK"
            rating_text = "Material issues identified but manageable with proper planning"
        elif len(high_risks) > 5:
            rating = "🟡 LOW-MODERATE RISK"
            rating_text = "Some issues require attention but no deal-breakers"
        else:
            rating = "🟢 LOW RISK"
            rating_text = "IT posture is generally sound"

        summary = f"""# IT Due Diligence Executive Summary
## {self.target_company}
*Generated: {datetime.now().strftime('%B %d, %Y')}*

---

## Overall Assessment: {rating}

{rating_text}

| Metric | Value |
|--------|-------|
| Total Risks | {len(self.result.risks)} |
| Critical | {len(critical_risks)} |
| High | {len(high_risks)} |
| Estimated Cost | ${self.result.total_one_time_low:,.0f} - ${self.result.total_one_time_high:,.0f} |

---

## Top 3 Critical Findings

"""
        # Add top findings
        for i, risk in enumerate(critical_risks[:3], 1):
            summary += f"**{i}. {risk.title}**\n"
            summary += f"- {risk.description[:150]}{'...' if len(risk.description) > 150 else ''}\n"
            summary += f"- *Impact:* {risk.severity} | *Domain:* {risk.domain}\n\n"

        if not critical_risks:
            summary += "*No critical findings identified.*\n\n"

        # Domain summary table
        summary += """---

## Domain Summary

| Domain | Risk Count | Critical | Status |
|--------|------------|----------|--------|
"""
        for domain, ds in self.result.domain_summaries.items():
            status = "🔴" if ds.critical_risks > 0 else "🟡" if ds.risk_count > 3 else "🟢"
            summary += f"| {domain} | {ds.risk_count} | {ds.critical_risks} | {status} |\n"

        # Key recommendations
        summary += """
---

## Key Recommendations

"""
        recommendations = [r.mitigation for r in self.result.risks if r.mitigation and r.severity in ["Critical", "High"]][:4]
        for i, rec in enumerate(recommendations, 1):
            summary += f"{i}. {rec}\n"

        summary += """
---

*This summary is auto-generated from detailed IT due diligence analysis. See full report for complete findings and evidence.*
"""
        return summary

    def prioritize_findings(self, findings: Optional[List] = None) -> List[Dict]:
        """
        Point 88: Prioritize findings with most important first.

        Uses multi-factor scoring:
        - Severity weight (40%)
        - Business impact (25%)
        - Confidence level (20%)
        - Actionability (15%)

        Args:
            findings: Optional list of findings (uses self.result.risks if None)

        Returns:
            List of findings sorted by priority score
        """
        items = findings if findings else self.result.risks

        severity_scores = {"Critical": 1.0, "High": 0.75, "Medium": 0.5, "Low": 0.25}

        prioritized = []
        for item in items:
            severity = getattr(item, 'severity', 'Medium')
            severity_score = severity_scores.get(severity, 0.5)

            # Business impact based on domain criticality
            domain = getattr(item, 'domain', 'Unknown')
            domain_weights = {
                "Security": 1.0,
                "Infrastructure": 0.9,
                "Applications": 0.8,
                "Identity": 0.85,
                "Network": 0.7,
                "IT Organization": 0.6
            }
            impact_score = domain_weights.get(domain, 0.5)

            # Has mitigation = more actionable
            has_mitigation = bool(getattr(item, 'mitigation', None))
            actionability_score = 0.8 if has_mitigation else 0.3

            # Confidence based on evidence
            has_evidence = bool(getattr(item, 'evidence', None))
            confidence_score = 0.9 if has_evidence else 0.5

            # Calculate composite score
            priority_score = (
                0.40 * severity_score +
                0.25 * impact_score +
                0.20 * confidence_score +
                0.15 * actionability_score
            )

            prioritized.append({
                "finding": item,
                "priority_score": round(priority_score, 3),
                "rank": 0,  # Will be set after sorting
                "score_breakdown": {
                    "severity": severity_score,
                    "business_impact": impact_score,
                    "confidence": confidence_score,
                    "actionability": actionability_score
                }
            })

        # Sort by priority score descending
        prioritized.sort(key=lambda x: x["priority_score"], reverse=True)

        # Assign ranks
        for i, item in enumerate(prioritized, 1):
            item["rank"] = i

        return prioritized

    def score_recommendation_actionability(self, recommendations: Optional[List] = None) -> List[Dict]:
        """
        Point 89: Score how actionable each recommendation is.

        Actionability factors:
        - Specificity (clear what to do)
        - Feasibility (realistic to implement)
        - Timeline clarity (when to do it)
        - Resource clarity (who/what needed)
        - Measurability (success criteria)

        Args:
            recommendations: List of recommendation strings or objects

        Returns:
            List of recommendations with actionability scores
        """
        items = recommendations if recommendations else [r.mitigation for r in self.result.risks if r.mitigation]

        # Keywords indicating actionability
        action_verbs = ["implement", "deploy", "upgrade", "migrate", "establish", "create", "configure", "enable", "disable", "replace", "remove", "install"]
        timeline_words = ["immediately", "before", "within", "by", "prior to", "day 1", "day 100", "post-close"]
        resource_words = ["vendor", "team", "consultant", "staff", "budget", "resource"]
        measurable_words = ["complete", "achieve", "reduce", "increase", "ensure", "verify", "confirm"]

        scored = []
        for item in items:
            text = str(item).lower() if item else ""

            # Calculate component scores
            has_action = any(verb in text for verb in action_verbs)
            has_timeline = any(word in text for word in timeline_words)
            has_resource = any(word in text for word in resource_words)
            has_measurable = any(word in text for word in measurable_words)

            # Specificity based on length and detail
            specificity = min(1.0, len(text) / 200) if text else 0

            # Calculate overall actionability
            actionability_score = (
                0.30 * (1.0 if has_action else 0.2) +
                0.20 * (1.0 if has_timeline else 0.3) +
                0.15 * (1.0 if has_resource else 0.4) +
                0.15 * (1.0 if has_measurable else 0.3) +
                0.20 * specificity
            )

            # Determine actionability level
            if actionability_score >= 0.7:
                level = "High"
            elif actionability_score >= 0.5:
                level = "Medium"
            else:
                level = "Low"

            scored.append({
                "recommendation": item,
                "actionability_score": round(actionability_score, 2),
                "actionability_level": level,
                "has_action_verb": has_action,
                "has_timeline": has_timeline,
                "has_resource_clarity": has_resource,
                "has_measurable_outcome": has_measurable,
                "suggestions": self._generate_actionability_suggestions(
                    has_action, has_timeline, has_resource, has_measurable
                )
            })

        # Sort by actionability score
        scored.sort(key=lambda x: x["actionability_score"], reverse=True)
        return scored

    def _generate_actionability_suggestions(
        self, has_action: bool, has_timeline: bool,
        has_resource: bool, has_measurable: bool
    ) -> List[str]:
        """Generate suggestions to improve recommendation actionability."""
        suggestions = []
        if not has_action:
            suggestions.append("Add specific action verb (e.g., 'Deploy', 'Configure', 'Migrate')")
        if not has_timeline:
            suggestions.append("Add timeline (e.g., 'within 30 days', 'by Day 100')")
        if not has_resource:
            suggestions.append("Specify responsible party or required resources")
        if not has_measurable:
            suggestions.append("Add success criteria or measurable outcome")
        return suggestions

    def generate_timeline_visualization(self, work_items: Optional[List[Dict]] = None) -> str:
        """
        Point 90: Generate visual timeline of work items by phase.

        Creates an ASCII/text-based timeline visualization.

        Args:
            work_items: Optional list of work items with phase info

        Returns:
            Text-based timeline visualization
        """
        # Use passed work items or generate from risks
        if work_items:
            items = work_items
        else:
            # Convert risks to work items
            items = []
            for risk in self.result.risks:
                phase = "Day_1" if risk.severity == "Critical" else "Day_100" if risk.severity == "High" else "Post_100"
                items.append({
                    "title": risk.title,
                    "phase": phase,
                    "priority": risk.severity,
                    "domain": risk.domain
                })

        # Group by phase
        by_phase = {"Day_1": [], "Day_100": [], "Post_100": []}
        for item in items:
            phase = item.get("phase", "Day_100")
            if phase in by_phase:
                by_phase[phase].append(item)

        # Generate visualization
        timeline = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                        INTEGRATION TIMELINE                                   ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  DAY 1                    DAY 100                   POST-100                 ║
║  (Close)                  (Stabilize)              (Optimize)               ║
║    │                         │                         │                     ║
║    ▼                         ▼                         ▼                     ║
"""

        # Add items to timeline
        max_items = max(len(by_phase["Day_1"]), len(by_phase["Day_100"]), len(by_phase["Post_100"]), 1)

        for i in range(min(max_items, 8)):  # Show up to 8 items
            d1 = by_phase["Day_1"][i]["title"][:18] if i < len(by_phase["Day_1"]) else ""
            d100 = by_phase["Day_100"][i]["title"][:18] if i < len(by_phase["Day_100"]) else ""
            post = by_phase["Post_100"][i]["title"][:18] if i < len(by_phase["Post_100"]) else ""

            timeline += f"║  • {d1:<18}     • {d100:<18}     • {post:<18}  ║\n"

        # Add counts
        timeline += f"""║                                                                              ║
║  [{len(by_phase['Day_1'])} items]               [{len(by_phase['Day_100'])} items]               [{len(by_phase['Post_100'])} items]              ║
╚══════════════════════════════════════════════════════════════════════════════╝

PHASE SUMMARY:
┌─────────────┬───────────┬──────────────────────────────────────────────────┐
│ Phase       │ Count     │ Focus                                            │
├─────────────┼───────────┼──────────────────────────────────────────────────┤
│ Day 1       │ {len(by_phase['Day_1']):>5}     │ Business continuity, critical systems            │
│ Day 100     │ {len(by_phase['Day_100']):>5}     │ Stabilization, technical debt reduction          │
│ Post-100    │ {len(by_phase['Post_100']):>5}     │ Optimization, synergy capture                    │
└─────────────┴───────────┴──────────────────────────────────────────────────┘
"""
        return timeline

    def generate_timeline_data(self, work_items: Optional[List[Dict]] = None) -> Dict:
        """
        Generate structured timeline data for UI visualization.

        Returns:
            Dict with timeline data suitable for charting
        """
        if work_items:
            items = work_items
        else:
            items = []
            for risk in self.result.risks:
                phase = "Day_1" if risk.severity == "Critical" else "Day_100" if risk.severity == "High" else "Post_100"
                items.append({
                    "id": risk.id,
                    "title": risk.title,
                    "phase": phase,
                    "priority": risk.severity,
                    "domain": risk.domain
                })

        # Group by phase
        by_phase = {
            "Day_1": {"items": [], "label": "Day 1 (Close)", "milestone": 0},
            "Day_100": {"items": [], "label": "Day 100 (Stabilize)", "milestone": 100},
            "Post_100": {"items": [], "label": "Post-100 (Optimize)", "milestone": 200}
        }

        for item in items:
            phase = item.get("phase", "Day_100")
            if phase in by_phase:
                by_phase[phase]["items"].append(item)

        # Sort items within each phase by priority
        priority_order = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}
        for phase_data in by_phase.values():
            phase_data["items"].sort(key=lambda x: priority_order.get(x.get("priority", "Medium"), 2))
            phase_data["count"] = len(phase_data["items"])

        return {
            "phases": by_phase,
            "total_items": len(items),
            "timeline_milestones": [
                {"day": 0, "label": "Close"},
                {"day": 30, "label": "Day 30"},
                {"day": 100, "label": "Day 100"},
                {"day": 200, "label": "Day 200+"}
            ]
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
