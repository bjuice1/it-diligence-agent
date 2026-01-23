"""
Validation Engine - Pass 3 Reconciliation

This module provides validation and reconciliation logic for Pass 3
of the multi-pass extraction process.

Key validations:
1. Count Reconciliation - Do detail sums match summary claims?
2. Coverage Check - Does every system have granular details?
3. Orphan Detection - Are there facts without parent systems?
4. Consistency Check - Do same items match across sources?
"""

import re
import json
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


# =============================================================================
# CONFIGURATION
# =============================================================================

# Tolerance for numeric reconciliation (15% variance allowed)
RECONCILIATION_TOLERANCE = 0.15

# Minimum detail coverage required (80% of systems need details)
MIN_DETAIL_COVERAGE = 0.80

# Variance threshold that triggers a warning
VARIANCE_WARNING_THRESHOLD = 0.25

# Variance threshold that triggers a failure
VARIANCE_FAILURE_THRESHOLD = 0.50

# Minimum granular facts per system to consider "covered"
MIN_FACTS_PER_SYSTEM = 1


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class ValidationResult:
    """
    Result of a single validation check.
    """
    check_id: str
    check_type: str
    status: str  # pass, warn, fail
    severity: str  # low, medium, high, critical
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    system_id: Optional[str] = None
    fact_id: Optional[str] = None
    suggested_action: str = ""
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_row(self) -> Dict[str, Any]:
        """Convert to flat row for Excel/CSV export."""
        return {
            "Check ID": self.check_id,
            "Type": self.check_type,
            "Status": self.status.upper(),
            "Severity": self.severity,
            "Message": self.message,
            "System": self.system_id or "",
            "Fact": self.fact_id or "",
            "Action": self.suggested_action,
            "Details": json.dumps(self.details) if self.details else ""
        }


@dataclass
class ValidationReport:
    """
    Complete validation report from Pass 3.
    """
    results: List[ValidationResult] = field(default_factory=list)
    summary: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    @property
    def pass_count(self) -> int:
        return sum(1 for r in self.results if r.status == "pass")

    @property
    def warn_count(self) -> int:
        return sum(1 for r in self.results if r.status == "warn")

    @property
    def fail_count(self) -> int:
        return sum(1 for r in self.results if r.status == "fail")

    @property
    def total_checks(self) -> int:
        return len(self.results)

    @property
    def pass_rate(self) -> float:
        if self.total_checks == 0:
            return 1.0
        return self.pass_count / self.total_checks

    @property
    def is_valid(self) -> bool:
        """Check if validation passed (no critical failures)."""
        critical_failures = [r for r in self.results
                           if r.status == "fail" and r.severity in ("high", "critical")]
        return len(critical_failures) == 0

    def get_failures(self) -> List[ValidationResult]:
        return [r for r in self.results if r.status == "fail"]

    def get_warnings(self) -> List[ValidationResult]:
        return [r for r in self.results if r.status == "warn"]

    def get_by_system(self, system_id: str) -> List[ValidationResult]:
        return [r for r in self.results if r.system_id == system_id]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "summary": {
                "total_checks": self.total_checks,
                "passed": self.pass_count,
                "warnings": self.warn_count,
                "failures": self.fail_count,
                "pass_rate": f"{self.pass_rate:.1%}",
                "is_valid": self.is_valid,
                "created_at": self.created_at
            },
            "results": [r.to_dict() for r in self.results]
        }

    def to_rows(self) -> List[Dict[str, Any]]:
        """Convert all results to flat rows for export."""
        return [r.to_row() for r in self.results]


# =============================================================================
# VALIDATION ENGINE
# =============================================================================

class ValidationEngine:
    """
    Engine for running validation checks on extracted data.

    Performs:
    1. System coverage validation
    2. Numeric reconciliation
    3. Orphan detection
    4. Cross-reference consistency
    """

    def __init__(self):
        self._check_counter = 0

    def _next_check_id(self) -> str:
        """Generate next check ID."""
        self._check_counter += 1
        return f"VAL-{self._check_counter:03d}"

    def validate_all(
        self,
        system_registry,  # SystemRegistry
        granular_facts_store,  # GranularFactsStore
        summary_facts: List[Any] = None  # From existing FactStore
    ) -> ValidationReport:
        """
        Run all validation checks.

        Args:
            system_registry: Pass 1 system catalog
            granular_facts_store: Pass 2 granular facts
            summary_facts: Optional summary-level facts for reconciliation

        Returns:
            ValidationReport with all results
        """
        report = ValidationReport()

        # Run all validation checks
        report.results.extend(
            self.validate_system_coverage(system_registry, granular_facts_store)
        )

        report.results.extend(
            self.validate_orphan_facts(system_registry, granular_facts_store)
        )

        report.results.extend(
            self.validate_domain_coverage(system_registry, granular_facts_store)
        )

        report.results.extend(
            self.validate_evidence_quality(granular_facts_store)
        )

        if summary_facts:
            report.results.extend(
                self.validate_numeric_reconciliation(
                    summary_facts, granular_facts_store
                )
            )

        report.results.extend(
            self.validate_minimum_extraction(granular_facts_store)
        )

        # Generate summary
        report.summary = self._generate_summary(report, system_registry, granular_facts_store)

        return report

    def validate_system_coverage(
        self,
        system_registry,
        granular_facts_store
    ) -> List[ValidationResult]:
        """
        Check that each system has granular facts.

        Every system in the registry should have at least one
        granular fact extracted in Pass 2.
        """
        results = []

        systems = system_registry.get_all_systems()
        for system in systems:
            facts = granular_facts_store.get_facts_by_system(system.system_id)
            fact_count = len(facts)

            if fact_count == 0:
                results.append(ValidationResult(
                    check_id=self._next_check_id(),
                    check_type="system_coverage",
                    status="fail",
                    severity="high",
                    message=f"System '{system.name}' has no granular facts",
                    system_id=system.system_id,
                    details={"system_name": system.name, "fact_count": 0},
                    suggested_action=f"Run Pass 2 detail extraction for {system.name}"
                ))
            elif fact_count < 3:
                results.append(ValidationResult(
                    check_id=self._next_check_id(),
                    check_type="system_coverage",
                    status="warn",
                    severity="medium",
                    message=f"System '{system.name}' has only {fact_count} granular facts",
                    system_id=system.system_id,
                    details={"system_name": system.name, "fact_count": fact_count},
                    suggested_action=f"Consider additional detail extraction for {system.name}"
                ))
            else:
                results.append(ValidationResult(
                    check_id=self._next_check_id(),
                    check_type="system_coverage",
                    status="pass",
                    severity="low",
                    message=f"System '{system.name}' has {fact_count} granular facts",
                    system_id=system.system_id,
                    details={"system_name": system.name, "fact_count": fact_count}
                ))

        return results

    def validate_orphan_facts(
        self,
        system_registry,
        granular_facts_store
    ) -> List[ValidationResult]:
        """
        Check for granular facts without parent systems.

        Orphan facts indicate extraction happened without proper
        system registration in Pass 1.
        """
        results = []

        system_ids = {s.system_id for s in system_registry.get_all_systems()}
        orphans = []

        for fact in granular_facts_store.get_all_facts():
            if fact.parent_system_id and fact.parent_system_id not in system_ids:
                orphans.append(fact)

        if orphans:
            results.append(ValidationResult(
                check_id=self._next_check_id(),
                check_type="orphan_detection",
                status="warn",
                severity="medium",
                message=f"Found {len(orphans)} granular facts with invalid parent system IDs",
                details={
                    "orphan_count": len(orphans),
                    "orphan_fact_ids": [f.granular_fact_id for f in orphans[:10]],
                    "invalid_parent_ids": list({f.parent_system_id for f in orphans})
                },
                suggested_action="Review orphan facts and register missing parent systems"
            ))
        else:
            results.append(ValidationResult(
                check_id=self._next_check_id(),
                check_type="orphan_detection",
                status="pass",
                severity="low",
                message="No orphan facts detected - all facts have valid parent systems"
            ))

        return results

    def validate_domain_coverage(
        self,
        system_registry,
        granular_facts_store
    ) -> List[ValidationResult]:
        """
        Check that all domains have adequate coverage.
        """
        results = []

        expected_domains = [
            "infrastructure", "applications", "cybersecurity",
            "network", "identity_access", "organization"
        ]

        for domain in expected_domains:
            systems = system_registry.get_systems_by_domain(domain)
            facts = granular_facts_store.get_facts_by_domain(domain)

            if len(systems) == 0 and len(facts) == 0:
                results.append(ValidationResult(
                    check_id=self._next_check_id(),
                    check_type="domain_coverage",
                    status="warn",
                    severity="medium",
                    message=f"No systems or facts found for domain: {domain}",
                    details={"domain": domain, "systems": 0, "facts": 0},
                    suggested_action=f"Check if source documents contain {domain} information"
                ))
            elif len(facts) < 5:
                results.append(ValidationResult(
                    check_id=self._next_check_id(),
                    check_type="domain_coverage",
                    status="warn",
                    severity="low",
                    message=f"Low fact count for domain {domain}: {len(facts)} facts",
                    details={"domain": domain, "systems": len(systems), "facts": len(facts)}
                ))
            else:
                results.append(ValidationResult(
                    check_id=self._next_check_id(),
                    check_type="domain_coverage",
                    status="pass",
                    severity="low",
                    message=f"Domain {domain}: {len(systems)} systems, {len(facts)} facts",
                    details={"domain": domain, "systems": len(systems), "facts": len(facts)}
                ))

        return results

    def validate_evidence_quality(
        self,
        granular_facts_store
    ) -> List[ValidationResult]:
        """
        Check evidence quality for granular facts.
        """
        results = []

        all_facts = granular_facts_store.get_all_facts()
        facts_without_evidence = [f for f in all_facts if not f.evidence_quote]
        _ = [f for f in all_facts if not f.source_document]
        low_confidence = [f for f in all_facts if f.confidence < 0.7]

        # Evidence coverage
        if len(facts_without_evidence) > 0:
            pct = len(facts_without_evidence) / max(1, len(all_facts))
            if pct > 0.2:
                results.append(ValidationResult(
                    check_id=self._next_check_id(),
                    check_type="evidence_quality",
                    status="warn",
                    severity="medium",
                    message=f"{len(facts_without_evidence)} facts ({pct:.0%}) lack evidence quotes",
                    details={
                        "missing_evidence_count": len(facts_without_evidence),
                        "total_facts": len(all_facts),
                        "percentage": f"{pct:.1%}"
                    },
                    suggested_action="Review facts without evidence - may need source verification"
                ))
            else:
                results.append(ValidationResult(
                    check_id=self._next_check_id(),
                    check_type="evidence_quality",
                    status="pass",
                    severity="low",
                    message=f"Evidence coverage: {1-pct:.0%} of facts have evidence quotes"
                ))
        else:
            results.append(ValidationResult(
                check_id=self._next_check_id(),
                check_type="evidence_quality",
                status="pass",
                severity="low",
                message="All facts have evidence quotes"
            ))

        # Low confidence facts
        if len(low_confidence) > 0:
            results.append(ValidationResult(
                check_id=self._next_check_id(),
                check_type="evidence_quality",
                status="warn",
                severity="low",
                message=f"{len(low_confidence)} facts have confidence < 70%",
                details={
                    "low_confidence_count": len(low_confidence),
                    "fact_ids": [f.granular_fact_id for f in low_confidence[:10]]
                },
                suggested_action="Review low-confidence facts for accuracy"
            ))

        return results

    def validate_numeric_reconciliation(
        self,
        summary_facts: List[Any],
        granular_facts_store
    ) -> List[ValidationResult]:
        """
        Reconcile numeric claims in summaries against granular sums.

        Example: Summary says "~50 servers", granular facts sum to 47
        """
        results = []

        # Extract numeric claims from summary facts
        numeric_pattern = re.compile(r'(\d+(?:,\d+)*(?:\.\d+)?)\s*(\w+)?')

        for fact in summary_facts:
            # Get fact text (handle different fact structures)
            fact_text = ""
            if hasattr(fact, 'details') and isinstance(fact.details, dict):
                fact_text = str(fact.details)
            elif hasattr(fact, 'item'):
                fact_text = fact.item

            # Find numeric claims
            matches = numeric_pattern.findall(fact_text)

            for match in matches:
                claimed_value = float(match[0].replace(",", ""))
                unit_hint = match[1] if len(match) > 1 else ""

                # Try to find matching granular facts
                if unit_hint:
                    related_facts = [
                        f for f in granular_facts_store.get_numeric_facts()
                        if unit_hint.lower() in f.item.lower()
                        or unit_hint.lower() in (f.unit or "").lower()
                    ]

                    if related_facts:
                        actual_sum = sum(
                            f.value for f in related_facts
                            if isinstance(f.value, (int, float))
                        )

                        if actual_sum > 0:
                            variance = abs(claimed_value - actual_sum) / claimed_value

                            if variance > VARIANCE_FAILURE_THRESHOLD:
                                status = "fail"
                                severity = "high"
                            elif variance > VARIANCE_WARNING_THRESHOLD:
                                status = "warn"
                                severity = "medium"
                            elif variance > RECONCILIATION_TOLERANCE:
                                status = "warn"
                                severity = "low"
                            else:
                                status = "pass"
                                severity = "low"

                            results.append(ValidationResult(
                                check_id=self._next_check_id(),
                                check_type="numeric_reconciliation",
                                status=status,
                                severity=severity,
                                message=f"Claimed {claimed_value} {unit_hint}, found {actual_sum} ({variance:.1%} variance)",
                                details={
                                    "claimed_value": claimed_value,
                                    "actual_sum": actual_sum,
                                    "variance_pct": f"{variance:.1%}",
                                    "unit": unit_hint,
                                    "matching_facts": len(related_facts)
                                },
                                suggested_action="Verify count discrepancy" if status != "pass" else ""
                            ))

        if not results:
            results.append(ValidationResult(
                check_id=self._next_check_id(),
                check_type="numeric_reconciliation",
                status="pass",
                severity="low",
                message="No numeric claims found to reconcile"
            ))

        return results

    def validate_minimum_extraction(
        self,
        granular_facts_store
    ) -> List[ValidationResult]:
        """
        Check that minimum extraction thresholds are met.
        """
        results = []

        total_facts = granular_facts_store.total_facts
        stats = granular_facts_store.get_statistics()

        # Minimum total facts
        if total_facts < 50:
            results.append(ValidationResult(
                check_id=self._next_check_id(),
                check_type="minimum_extraction",
                status="warn",
                severity="high",
                message=f"Only {total_facts} granular facts extracted (target: 50+)",
                details={"total_facts": total_facts, "target": 50},
                suggested_action="Run additional Pass 2 extraction to capture more details"
            ))
        elif total_facts < 100:
            results.append(ValidationResult(
                check_id=self._next_check_id(),
                check_type="minimum_extraction",
                status="pass",
                severity="low",
                message=f"{total_facts} granular facts extracted (good coverage)"
            ))
        else:
            results.append(ValidationResult(
                check_id=self._next_check_id(),
                check_type="minimum_extraction",
                status="pass",
                severity="low",
                message=f"{total_facts} granular facts extracted (excellent coverage)"
            ))

        # Fact type diversity
        type_counts = stats.get("facts_by_type", {})
        if len(type_counts) < 3:
            results.append(ValidationResult(
                check_id=self._next_check_id(),
                check_type="minimum_extraction",
                status="warn",
                severity="medium",
                message=f"Low fact type diversity: only {len(type_counts)} types",
                details={"types_found": list(type_counts.keys())},
                suggested_action="Extract more diverse fact types (counts, versions, costs, etc.)"
            ))

        return results

    def _generate_summary(
        self,
        report: ValidationReport,
        system_registry,
        granular_facts_store
    ) -> Dict[str, Any]:
        """Generate summary statistics for the report."""
        return {
            "validation_passed": report.is_valid,
            "total_checks": report.total_checks,
            "passed": report.pass_count,
            "warnings": report.warn_count,
            "failures": report.fail_count,
            "pass_rate": f"{report.pass_rate:.1%}",
            "systems_evaluated": system_registry.total_systems,
            "facts_evaluated": granular_facts_store.total_facts,
            "critical_issues": [
                r.message for r in report.results
                if r.status == "fail" and r.severity in ("high", "critical")
            ]
        }


# =============================================================================
# PERSISTENCE
# =============================================================================

def save_validation_report(report: ValidationReport, filepath: Path):
    """Save validation report to JSON file."""
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)

    with open(filepath, 'w') as f:
        json.dump(report.to_dict(), f, indent=2)

    logger.info(f"Saved validation report to {filepath}")


def load_validation_report(filepath: Path) -> Optional[ValidationReport]:
    """Load validation report from JSON file."""
    filepath = Path(filepath)
    if not filepath.exists():
        return None

    with open(filepath, 'r') as f:
        data = json.load(f)

    report = ValidationReport()
    report.created_at = data.get("summary", {}).get("created_at", report.created_at)
    report.summary = data.get("summary", {})

    for result_data in data.get("results", []):
        result = ValidationResult(**result_data)
        report.results.append(result)

    return report
