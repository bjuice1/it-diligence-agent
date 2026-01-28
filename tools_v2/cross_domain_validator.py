"""
Cross-Domain Validator - Layer 3 Validation

Checks consistency across all domains after individual domain validation completes.
This catches issues that only become visible when looking at the full picture.

Key consistency checks:
- Headcount vs endpoints ratio
- Headcount vs application count
- Vendor consistency across domains
- Security team vs security tools
- Cost per head sanity
- Budget vs component costs
- Stated totals vs calculated totals
"""

import re
import json
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

import anthropic

from models.validation_models import (
    ValidationFlag, FlagSeverity, FlagCategory,
    CrossDomainValidationState, generate_flag_id
)

logger = logging.getLogger(__name__)


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class ConsistencyCheck:
    """Result of a single consistency check."""
    check_name: str
    domains_involved: List[str]
    is_consistent: bool
    expected_value: Any
    actual_value: Any
    discrepancy: Optional[str] = None
    severity: str = "medium"  # low, medium, high, critical

    def to_dict(self) -> Dict[str, Any]:
        return {
            "check_name": self.check_name,
            "domains_involved": self.domains_involved,
            "is_consistent": self.is_consistent,
            "expected_value": str(self.expected_value),
            "actual_value": str(self.actual_value),
            "discrepancy": self.discrepancy,
            "severity": self.severity
        }


@dataclass
class CrossDomainValidationResult:
    """Result of cross-domain validation."""
    is_consistent: bool
    overall_score: float
    checks: List[ConsistencyCheck] = field(default_factory=list)
    flags: List[ValidationFlag] = field(default_factory=list)
    llm_findings: List[Dict[str, Any]] = field(default_factory=list)
    summary: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_consistent": self.is_consistent,
            "overall_score": self.overall_score,
            "checks": [c.to_dict() for c in self.checks],
            "flags": [f.to_dict() for f in self.flags],
            "llm_findings": self.llm_findings,
            "summary": self.summary
        }


# =============================================================================
# CONFIGURATION
# =============================================================================

# Expected ranges for consistency checks
CONSISTENCY_THRESHOLDS = {
    "headcount_vs_endpoints": (20, 200),      # 20-200 endpoints per IT person
    "headcount_vs_apps": (0.5, 30),           # 0.5-30 apps per IT person
    "cost_per_head": (50000, 300000),         # $50K-$300K per IT person
    "it_spend_ratio": (0.02, 0.15),           # IT spend 2-15% of revenue
}


# =============================================================================
# CROSS-DOMAIN VALIDATOR CLASS
# =============================================================================

class CrossDomainValidator:
    """
    Validates consistency across all domains.

    Runs after all individual domain validations complete.
    Catches issues that only appear when comparing across domains.
    """

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514"):
        """
        Initialize the cross-domain validator.

        Args:
            api_key: Anthropic API key
            model: Model to use for LLM validation
        """
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model

    # =========================================================================
    # MAIN VALIDATION METHOD
    # =========================================================================

    def validate_all(
        self,
        fact_store,
        document_text: str
    ) -> CrossDomainValidationResult:
        """
        Run all cross-domain consistency checks.

        Args:
            fact_store: FactStore with all extracted facts
            document_text: Original document text

        Returns:
            CrossDomainValidationResult with all findings
        """
        logger.info("Running cross-domain consistency validation")

        # Gather facts by domain
        org_facts = self._get_domain_facts(fact_store, "organization")
        infra_facts = self._get_domain_facts(fact_store, "infrastructure")
        app_facts = self._get_domain_facts(fact_store, "applications")
        network_facts = self._get_domain_facts(fact_store, "network")
        security_facts = self._get_domain_facts(fact_store, "security")

        checks = []
        flags = []

        # Run deterministic consistency checks
        check1 = self._check_headcount_vs_endpoints(org_facts, infra_facts)
        checks.append(check1)
        if not check1.is_consistent:
            flags.append(self._check_to_flag(check1))

        check2 = self._check_headcount_vs_apps(org_facts, app_facts)
        checks.append(check2)
        if not check2.is_consistent:
            flags.append(self._check_to_flag(check2))

        check3 = self._check_vendor_consistency(org_facts, infra_facts, app_facts)
        checks.append(check3)
        if not check3.is_consistent:
            flags.append(self._check_to_flag(check3))

        check4 = self._check_security_team_vs_tools(org_facts, security_facts)
        checks.append(check4)
        if not check4.is_consistent:
            flags.append(self._check_to_flag(check4))

        check5 = self._check_cost_per_head(org_facts)
        checks.append(check5)
        if not check5.is_consistent:
            flags.append(self._check_to_flag(check5))

        check6 = self._check_budget_vs_components(org_facts, infra_facts, app_facts)
        checks.append(check6)
        if not check6.is_consistent:
            flags.append(self._check_to_flag(check6))

        check7 = self._check_stated_vs_calculated_totals(org_facts, document_text)
        checks.append(check7)
        if not check7.is_consistent:
            flags.append(self._check_to_flag(check7))

        # Run LLM holistic review
        llm_findings = self._llm_holistic_review(
            org_facts, infra_facts, app_facts, security_facts, document_text
        )

        # Convert LLM findings to flags
        for finding in llm_findings:
            flag = ValidationFlag(
                flag_id=generate_flag_id(),
                severity=FlagSeverity(finding.get("severity", "warning")),
                category=FlagCategory.CROSS_DOMAIN,
                message=finding.get("message", "Cross-domain issue detected"),
                suggestion=finding.get("suggestion")
            )
            flags.append(flag)

        # Calculate overall score
        passed_checks = sum(1 for c in checks if c.is_consistent)
        overall_score = passed_checks / len(checks) if checks else 1.0

        # Determine if consistent
        is_consistent = overall_score >= 0.7 and not any(
            c.severity == "critical" and not c.is_consistent for c in checks
        )

        # Generate summary
        summary = self._generate_summary(checks, llm_findings)

        logger.info(
            f"Cross-domain validation complete: {passed_checks}/{len(checks)} checks passed, "
            f"{len(llm_findings)} LLM findings"
        )

        return CrossDomainValidationResult(
            is_consistent=is_consistent,
            overall_score=overall_score,
            checks=checks,
            flags=flags,
            llm_findings=llm_findings,
            summary=summary
        )

    # =========================================================================
    # CONSISTENCY CHECKS
    # =========================================================================

    def _check_headcount_vs_endpoints(
        self,
        org_facts: List[Dict],
        infra_facts: List[Dict]
    ) -> ConsistencyCheck:
        """Check if endpoint count is reasonable relative to IT headcount."""
        headcount = self._get_total_headcount(org_facts)
        endpoints = self._get_endpoint_count(infra_facts)

        if not headcount or not endpoints:
            return ConsistencyCheck(
                check_name="Headcount vs. Endpoints Ratio",
                domains_involved=["organization", "infrastructure"],
                is_consistent=True,  # Can't check without data
                expected_value="20-200 endpoints per IT person",
                actual_value="Unable to calculate (missing data)",
                severity="low"
            )

        ratio = endpoints / headcount
        min_ratio, max_ratio = CONSISTENCY_THRESHOLDS["headcount_vs_endpoints"]
        is_reasonable = min_ratio <= ratio <= max_ratio

        return ConsistencyCheck(
            check_name="Headcount vs. Endpoints Ratio",
            domains_involved=["organization", "infrastructure"],
            is_consistent=is_reasonable,
            expected_value=f"{min_ratio}-{max_ratio} endpoints per IT person",
            actual_value=f"{ratio:.1f} endpoints per IT person ({endpoints} endpoints / {headcount} IT staff)",
            discrepancy=None if is_reasonable else f"Ratio {ratio:.1f} is outside expected range",
            severity="medium" if not is_reasonable else "low"
        )

    def _check_headcount_vs_apps(
        self,
        org_facts: List[Dict],
        app_facts: List[Dict]
    ) -> ConsistencyCheck:
        """Check if application count is reasonable relative to IT headcount."""
        headcount = self._get_total_headcount(org_facts)
        app_count = len(app_facts)

        if not headcount:
            return ConsistencyCheck(
                check_name="Headcount vs. Applications Ratio",
                domains_involved=["organization", "applications"],
                is_consistent=True,
                expected_value="0.5-30 apps per IT person",
                actual_value="Unable to calculate (missing headcount)",
                severity="low"
            )

        ratio = app_count / headcount
        min_ratio, max_ratio = CONSISTENCY_THRESHOLDS["headcount_vs_apps"]
        is_reasonable = min_ratio <= ratio <= max_ratio

        return ConsistencyCheck(
            check_name="Headcount vs. Applications Ratio",
            domains_involved=["organization", "applications"],
            is_consistent=is_reasonable,
            expected_value=f"{min_ratio}-{max_ratio} apps per IT person",
            actual_value=f"{ratio:.2f} apps per IT person ({app_count} apps / {headcount} IT staff)",
            discrepancy=None if is_reasonable else f"Ratio {ratio:.2f} is outside expected range",
            severity="medium" if not is_reasonable else "low"
        )

    def _check_vendor_consistency(
        self,
        org_facts: List[Dict],
        infra_facts: List[Dict],
        app_facts: List[Dict]
    ) -> ConsistencyCheck:
        """Check if vendors mentioned in org appear in other domains."""
        org_vendors = self._extract_vendors(org_facts)
        infra_vendors = self._extract_vendors(infra_facts)
        app_vendors = self._extract_vendors(app_facts)

        all_tech_vendors = infra_vendors | app_vendors

        # Check if org-mentioned vendors appear elsewhere
        org_only_vendors = org_vendors - all_tech_vendors

        # Filter out common non-tech vendors
        non_tech_keywords = {"consulting", "staffing", "recruitment", "legal", "accounting"}
        tech_org_vendors = {
            v for v in org_only_vendors
            if not any(kw in v.lower() for kw in non_tech_keywords)
        }

        is_consistent = len(tech_org_vendors) <= 2  # Allow some discrepancy

        return ConsistencyCheck(
            check_name="Vendor Consistency Across Domains",
            domains_involved=["organization", "infrastructure", "applications"],
            is_consistent=is_consistent,
            expected_value="Vendors in org should appear in tech domains",
            actual_value=f"{len(tech_org_vendors)} vendor(s) in org not found in tech domains: {', '.join(list(tech_org_vendors)[:5])}",
            discrepancy=None if is_consistent else "Some org-mentioned vendors not documented in technical domains",
            severity="low"
        )

    def _check_security_team_vs_tools(
        self,
        org_facts: List[Dict],
        security_facts: List[Dict]
    ) -> ConsistencyCheck:
        """Check if security team exists, security tools should be documented."""
        # Check if security team mentioned in org
        has_security_team = any(
            "security" in str(f.get("item", "")).lower() or
            "security" in str(f.get("category", "")).lower()
            for f in org_facts
        )

        # Check if security tools documented
        has_security_tools = len(security_facts) > 0

        is_consistent = not has_security_team or has_security_tools

        return ConsistencyCheck(
            check_name="Security Team vs. Security Tools",
            domains_involved=["organization", "security"],
            is_consistent=is_consistent,
            expected_value="If security team exists, security tools should be documented",
            actual_value=f"Security team: {'Yes' if has_security_team else 'No'}, Security tools: {'Yes' if has_security_tools else 'No'}",
            discrepancy=None if is_consistent else "Security team mentioned but no security tools documented",
            severity="high" if not is_consistent else "low"
        )

    def _check_cost_per_head(self, org_facts: List[Dict]) -> ConsistencyCheck:
        """Check if cost per IT person is reasonable."""
        headcount = self._get_total_headcount(org_facts)
        total_cost = self._get_total_cost(org_facts)

        if not headcount or not total_cost:
            return ConsistencyCheck(
                check_name="Cost Per IT Person",
                domains_involved=["organization"],
                is_consistent=True,
                expected_value="$50K-$300K per IT person",
                actual_value="Unable to calculate (missing data)",
                severity="low"
            )

        cost_per_head = total_cost / headcount
        min_cost, max_cost = CONSISTENCY_THRESHOLDS["cost_per_head"]
        is_reasonable = min_cost <= cost_per_head <= max_cost

        return ConsistencyCheck(
            check_name="Cost Per IT Person",
            domains_involved=["organization"],
            is_consistent=is_reasonable,
            expected_value=f"${min_cost:,}-${max_cost:,} per IT person",
            actual_value=f"${cost_per_head:,.0f} per IT person (${total_cost:,.0f} / {headcount})",
            discrepancy=None if is_reasonable else f"Cost per head ${cost_per_head:,.0f} is outside expected range",
            severity="high" if cost_per_head < min_cost * 0.5 or cost_per_head > max_cost * 1.5 else "medium"
        )

    def _check_budget_vs_components(
        self,
        org_facts: List[Dict],
        infra_facts: List[Dict],
        app_facts: List[Dict]
    ) -> ConsistencyCheck:
        """Check if sum of component costs approximates total budget."""
        total_budget = self._get_total_cost(org_facts)

        # Sum up component costs
        component_costs = 0
        for facts in [org_facts, infra_facts, app_facts]:
            for fact in facts:
                details = fact.get("details", {})
                for key in ["cost", "annual_cost", "budget", "spend"]:
                    if key in details:
                        cost = self._parse_cost(details[key])
                        if cost:
                            component_costs += cost

        if not total_budget:
            return ConsistencyCheck(
                check_name="Budget vs. Component Costs",
                domains_involved=["organization", "infrastructure", "applications"],
                is_consistent=True,
                expected_value="Component costs should approximate total budget",
                actual_value="Unable to calculate (no total budget found)",
                severity="low"
            )

        if component_costs == 0:
            return ConsistencyCheck(
                check_name="Budget vs. Component Costs",
                domains_involved=["organization", "infrastructure", "applications"],
                is_consistent=True,
                expected_value="Component costs should approximate total budget",
                actual_value="No component costs extracted",
                severity="low"
            )

        ratio = component_costs / total_budget
        is_reasonable = 0.5 <= ratio <= 1.5  # Within 50% of total

        return ConsistencyCheck(
            check_name="Budget vs. Component Costs",
            domains_involved=["organization", "infrastructure", "applications"],
            is_consistent=is_reasonable,
            expected_value="Component costs within 50% of total budget",
            actual_value=f"Components: ${component_costs:,.0f}, Budget: ${total_budget:,.0f} (ratio: {ratio:.2f})",
            discrepancy=None if is_reasonable else f"Component costs differ significantly from total budget",
            severity="medium"
        )

    def _check_stated_vs_calculated_totals(
        self,
        org_facts: List[Dict],
        document_text: str
    ) -> ConsistencyCheck:
        """Check if stated headcount total matches sum of teams."""
        # Find stated total in document
        stated_total = self._find_stated_headcount(document_text)

        # Calculate total from teams
        calculated_total = 0
        for fact in org_facts:
            if fact.get("category") == "central_it":
                details = fact.get("details", {})
                for key in ["headcount", "fte", "staff_count", "team_size"]:
                    if key in details:
                        calculated_total += self._parse_numeric(details[key])
                        break

        if not stated_total:
            return ConsistencyCheck(
                check_name="Stated vs. Calculated Headcount",
                domains_involved=["organization"],
                is_consistent=True,
                expected_value="Stated total should match sum of teams",
                actual_value=f"No stated total found. Calculated: {calculated_total}",
                severity="low"
            )

        difference = abs(stated_total - calculated_total)
        tolerance = max(5, stated_total * 0.1)  # 10% or 5, whichever is larger
        is_consistent = difference <= tolerance

        return ConsistencyCheck(
            check_name="Stated vs. Calculated Headcount",
            domains_involved=["organization"],
            is_consistent=is_consistent,
            expected_value=f"Stated total ({stated_total}) should match sum of teams",
            actual_value=f"Stated: {stated_total}, Calculated: {calculated_total}, Difference: {difference}",
            discrepancy=None if is_consistent else f"Headcount mismatch of {difference}",
            severity="high" if difference > stated_total * 0.2 else "medium"
        )

    # =========================================================================
    # LLM HOLISTIC REVIEW
    # =========================================================================

    def _llm_holistic_review(
        self,
        org_facts: List[Dict],
        infra_facts: List[Dict],
        app_facts: List[Dict],
        security_facts: List[Dict],
        document_text: str
    ) -> List[Dict[str, Any]]:
        """Use LLM to perform holistic review across all domains."""
        # Build summary for LLM
        summary = self._build_domain_summary(
            org_facts, infra_facts, app_facts, security_facts
        )

        prompt = f"""You are reviewing extracted IT due diligence data for cross-domain consistency.

Here is a summary of what was extracted from each domain:

{summary}

Your job is to identify:
1. Logical inconsistencies between domains
2. Missing coverage that should exist given other data
3. Data quality issues visible only when comparing domains
4. Suspicious patterns (things that don't make sense together)

Return a JSON array of findings. Each finding should have:
- "type": "inconsistency", "missing_coverage", "data_quality", or "suspicious"
- "message": Clear description of the issue
- "domains_involved": List of domains involved
- "severity": "info", "warning", "error", or "critical"
- "suggestion": How to resolve

Only include genuine issues. If everything looks consistent, return an empty array.

Return ONLY valid JSON, no other text."""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )

            response_text = response.content[0].text.strip()
            findings = self._parse_json_response(response_text)

            return findings if isinstance(findings, list) else []

        except Exception as e:
            logger.error(f"LLM holistic review failed: {e}")
            return []

    def _build_domain_summary(
        self,
        org_facts: List[Dict],
        infra_facts: List[Dict],
        app_facts: List[Dict],
        security_facts: List[Dict]
    ) -> str:
        """Build a summary of all domains for LLM review."""
        summary = "## ORGANIZATION DOMAIN\n"
        summary += f"- Total facts: {len(org_facts)}\n"
        summary += f"- Headcount: {self._get_total_headcount(org_facts) or 'Not found'}\n"
        summary += f"- Budget: ${self._get_total_cost(org_facts):,.0f}\n" if self._get_total_cost(org_facts) else "- Budget: Not found\n"
        summary += f"- Teams: {', '.join(set(f.get('item', '') for f in org_facts if f.get('category') == 'central_it'))[:200]}\n"

        summary += "\n## INFRASTRUCTURE DOMAIN\n"
        summary += f"- Total facts: {len(infra_facts)}\n"
        summary += f"- Categories: {', '.join(set(f.get('category', '') for f in infra_facts))}\n"
        summary += f"- Key items: {', '.join(set(f.get('item', '') for f in infra_facts)[:10])}\n"

        summary += "\n## APPLICATIONS DOMAIN\n"
        summary += f"- Total facts: {len(app_facts)}\n"
        summary += f"- Categories: {', '.join(set(f.get('category', '') for f in app_facts))}\n"
        summary += f"- Key applications: {', '.join(set(f.get('item', '') for f in app_facts)[:10])}\n"

        summary += "\n## SECURITY DOMAIN\n"
        summary += f"- Total facts: {len(security_facts)}\n"
        summary += f"- Categories: {', '.join(set(f.get('category', '') for f in security_facts))}\n"
        summary += f"- Key tools: {', '.join(set(f.get('item', '') for f in security_facts)[:10])}\n"

        return summary

    # =========================================================================
    # HELPER METHODS
    # =========================================================================

    def _get_domain_facts(self, fact_store, domain: str) -> List[Dict]:
        """Get all facts for a domain."""
        if hasattr(fact_store, 'get_facts_by_domain'):
            facts = fact_store.get_facts_by_domain(domain)
            return [f.to_dict() if hasattr(f, 'to_dict') else f for f in facts]
        elif hasattr(fact_store, 'facts'):
            return [
                f.to_dict() if hasattr(f, 'to_dict') else f
                for f in fact_store.facts
                if (f.domain if hasattr(f, 'domain') else f.get('domain')) == domain
            ]
        return []

    def _get_total_headcount(self, org_facts: List[Dict]) -> int:
        """Get total IT headcount from organization facts."""
        # First look for explicit total
        for fact in org_facts:
            item = fact.get("item", "").lower()
            if "total" in item and "headcount" in item:
                details = fact.get("details", {})
                for key in ["headcount", "total", "count"]:
                    if key in details:
                        return self._parse_numeric(details[key])

        # Sum from teams
        total = 0
        for fact in org_facts:
            if fact.get("category") == "central_it":
                details = fact.get("details", {})
                for key in ["headcount", "fte", "staff_count", "team_size"]:
                    if key in details:
                        total += self._parse_numeric(details[key])
                        break

        return total

    def _get_endpoint_count(self, infra_facts: List[Dict]) -> int:
        """Get endpoint/server count from infrastructure facts."""
        total = 0
        for fact in infra_facts:
            details = fact.get("details", {})
            for key in ["count", "endpoint_count", "server_count", "quantity"]:
                if key in details:
                    total += self._parse_numeric(details[key])

        return total if total > 0 else None

    def _get_total_cost(self, org_facts: List[Dict]) -> float:
        """Get total IT cost/budget from organization facts."""
        for fact in org_facts:
            item = fact.get("item", "").lower()
            category = fact.get("category", "").lower()

            if "budget" in item or "budget" in category or "cost" in item:
                details = fact.get("details", {})
                for key in ["budget", "total", "cost", "annual_cost", "spend"]:
                    if key in details:
                        cost = self._parse_cost(details[key])
                        if cost and cost > 100000:  # Reasonable IT budget
                            return cost

        return 0

    def _extract_vendors(self, facts: List[Dict]) -> set:
        """Extract vendor names from facts."""
        vendors = set()
        vendor_keys = ["vendor", "provider", "supplier", "partner", "manufacturer"]

        for fact in facts:
            details = fact.get("details", {})
            for key in vendor_keys:
                if key in details:
                    vendor = str(details[key]).strip()
                    if vendor and len(vendor) > 2:
                        vendors.add(vendor.lower())

            # Also check item names for vendor mentions
            item = fact.get("item", "")
            if " - " in item:
                potential_vendor = item.split(" - ")[0].strip()
                if len(potential_vendor) > 2:
                    vendors.add(potential_vendor.lower())

        return vendors

    def _find_stated_headcount(self, document_text: str) -> Optional[int]:
        """Find explicitly stated headcount total in document."""
        patterns = [
            r"total\s+(?:IT\s+)?(?:head)?count\s*(?:of|is|:)?\s*(\d+)",
            r"(\d+)\s+(?:IT\s+)?(?:employees?|staff|FTEs?|people)",
            r"IT\s+(?:organization|team)\s+(?:of|with)\s+(\d+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, document_text, re.IGNORECASE)
            if match:
                return int(match.group(1))

        return None

    def _parse_numeric(self, value: Any) -> int:
        """Parse a numeric value from various formats."""
        if value is None:
            return 0
        if isinstance(value, (int, float)):
            return int(value)
        if isinstance(value, str):
            # Remove commas and extract number
            clean = re.sub(r'[^\d.]', '', value.replace(',', ''))
            try:
                return int(float(clean))
            except ValueError:
                pass
        return 0

    def _parse_cost(self, value: Any) -> float:
        """Parse a cost value from various formats."""
        if value is None:
            return 0.0
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            value = value.upper().replace(",", "").replace("$", "").strip()

            multiplier = 1
            if "M" in value or "MM" in value:
                multiplier = 1_000_000
                value = value.replace("MM", "").replace("M", "")
            elif "K" in value:
                multiplier = 1_000
                value = value.replace("K", "")
            elif "B" in value:
                multiplier = 1_000_000_000
                value = value.replace("B", "")

            try:
                return float(value) * multiplier
            except ValueError:
                pass

        return 0.0

    def _parse_json_response(self, response_text: str) -> Any:
        """Parse JSON from LLM response."""
        # Handle markdown code blocks
        if "```" in response_text:
            parts = response_text.split("```")
            for part in parts:
                part = part.strip()
                if part.startswith("json"):
                    part = part[4:].strip()
                try:
                    return json.loads(part)
                except json.JSONDecodeError:
                    continue

        # Try direct parse
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            return []

    def _check_to_flag(self, check: ConsistencyCheck) -> ValidationFlag:
        """Convert a failed consistency check to a validation flag."""
        severity_map = {
            "low": FlagSeverity.INFO,
            "medium": FlagSeverity.WARNING,
            "high": FlagSeverity.ERROR,
            "critical": FlagSeverity.CRITICAL
        }

        return ValidationFlag(
            flag_id=generate_flag_id(),
            severity=severity_map.get(check.severity, FlagSeverity.WARNING),
            category=FlagCategory.CROSS_DOMAIN,
            message=f"{check.check_name}: {check.discrepancy or check.actual_value}",
            suggestion=f"Expected: {check.expected_value}"
        )

    def _generate_summary(
        self,
        checks: List[ConsistencyCheck],
        llm_findings: List[Dict]
    ) -> str:
        """Generate a summary of cross-domain validation."""
        passed = sum(1 for c in checks if c.is_consistent)
        failed = len(checks) - passed

        summary = f"Cross-domain validation: {passed}/{len(checks)} checks passed"

        if failed > 0:
            failed_checks = [c.check_name for c in checks if not c.is_consistent]
            summary += f". Failed: {', '.join(failed_checks)}"

        if llm_findings:
            summary += f". {len(llm_findings)} additional issue(s) found by holistic review."

        return summary


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def create_cross_domain_validator(api_key: str) -> CrossDomainValidator:
    """Create a cross-domain validator instance."""
    return CrossDomainValidator(api_key=api_key)


def validate_cross_domain(
    api_key: str,
    fact_store,
    document_text: str
) -> CrossDomainValidationResult:
    """Convenience function to run cross-domain validation."""
    validator = CrossDomainValidator(api_key=api_key)
    return validator.validate_all(fact_store, document_text)
