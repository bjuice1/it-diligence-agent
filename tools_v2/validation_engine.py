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

# Quote validation threshold (Point 81)
QUOTE_VALIDATION_THRESHOLD = 0.85  # Fuzzy match threshold

# Anomaly detection thresholds (Point 84)
ANOMALY_THRESHOLDS = {
    "numeric_outlier_zscore": 2.5,  # Z-score for numeric outliers
    "text_length_outlier": 3.0,     # Standard deviations for text length
    "confidence_outlier": 0.3       # Facts below this confidence flagged
}

# Consistency check factors (Point 83)
CONSISTENCY_WEIGHTS = {
    "evidence_coverage": 0.25,
    "cross_reference": 0.25,
    "domain_balance": 0.20,
    "fact_quality": 0.30
}


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

    # =========================================================================
    # EVIDENCE QUOTE VALIDATION (Point 81)
    # =========================================================================

    def validate_evidence_quotes(
        self,
        facts: List[Any],
        source_documents: Dict[str, str],
        threshold: float = QUOTE_VALIDATION_THRESHOLD
    ) -> List[ValidationResult]:
        """
        Validate that evidence quotes exist in source documents (Point 81).

        Args:
            facts: List of facts with evidence quotes
            source_documents: Dict of filename -> content
            threshold: Fuzzy match threshold (0-1)

        Returns:
            List of ValidationResult for each fact
        """
        results = []

        for fact in facts:
            # Get evidence quote
            evidence = getattr(fact, 'evidence', {}) or {}
            quote = evidence.get('exact_quote', '')
            source_doc = getattr(fact, 'source_document', '')

            if not quote:
                results.append(ValidationResult(
                    check_id=self._next_check_id(),
                    check_type="quote_validation",
                    status="warn",
                    severity="low",
                    message=f"Fact {getattr(fact, 'fact_id', 'unknown')} has no evidence quote",
                    fact_id=getattr(fact, 'fact_id', None),
                    suggested_action="Add evidence quote for traceability"
                ))
                continue

            if not source_doc or source_doc not in source_documents:
                results.append(ValidationResult(
                    check_id=self._next_check_id(),
                    check_type="quote_validation",
                    status="warn",
                    severity="medium",
                    message=f"Source document '{source_doc}' not available for validation",
                    fact_id=getattr(fact, 'fact_id', None),
                    details={"source_document": source_doc},
                    suggested_action="Verify source document is included in analysis"
                ))
                continue

            # Check if quote exists in document
            doc_content = source_documents[source_doc].lower()
            quote_lower = quote.lower()

            # Exact match
            if quote_lower in doc_content:
                results.append(ValidationResult(
                    check_id=self._next_check_id(),
                    check_type="quote_validation",
                    status="pass",
                    severity="low",
                    message=f"Evidence quote verified in {source_doc}",
                    fact_id=getattr(fact, 'fact_id', None)
                ))
            else:
                # Fuzzy match
                similarity = self._calculate_quote_similarity(quote_lower, doc_content)

                if similarity >= threshold:
                    results.append(ValidationResult(
                        check_id=self._next_check_id(),
                        check_type="quote_validation",
                        status="pass",
                        severity="low",
                        message=f"Evidence quote fuzzy-matched ({similarity:.0%})",
                        fact_id=getattr(fact, 'fact_id', None),
                        details={"similarity": similarity, "threshold": threshold}
                    ))
                else:
                    results.append(ValidationResult(
                        check_id=self._next_check_id(),
                        check_type="quote_validation",
                        status="fail" if similarity < 0.5 else "warn",
                        severity="high" if similarity < 0.5 else "medium",
                        message=f"Evidence quote not found in source ({similarity:.0%} match)",
                        fact_id=getattr(fact, 'fact_id', None),
                        details={
                            "quote_preview": quote[:100],
                            "similarity": similarity,
                            "source_document": source_doc
                        },
                        suggested_action="Verify quote accuracy or update source reference"
                    ))

        return results

    def _calculate_quote_similarity(self, quote: str, document: str) -> float:
        """Calculate similarity between quote and document content."""
        # Simple approach: check word overlap
        quote_words = set(quote.split())
        if not quote_words:
            return 0.0

        # Find consecutive word matches
        best_match = 0
        doc_words = document.split()

        for i in range(len(doc_words)):
            matches = 0
            for j, word in enumerate(quote.split()):
                if i + j < len(doc_words) and doc_words[i + j] == word:
                    matches += 1
            if matches > best_match:
                best_match = matches

        return best_match / len(quote_words) if quote_words else 0.0

    # =========================================================================
    # CROSS-REFERENCE VALIDATION (Point 82)
    # =========================================================================

    def validate_cross_references(
        self,
        findings: List[Any],
        fact_store
    ) -> List[ValidationResult]:
        """
        Validate that fact IDs referenced in findings exist (Point 82).

        Args:
            findings: List of findings with fact citations
            fact_store: FactStore to validate against

        Returns:
            List of ValidationResult
        """
        results = []
        all_fact_ids = set(fact_store.get_all_citable_ids())

        for finding in findings:
            # Get cited fact IDs
            cited_ids = getattr(finding, 'supporting_facts', []) or []
            if hasattr(finding, 'fact_citations'):
                cited_ids.extend(finding.fact_citations)

            if not cited_ids:
                results.append(ValidationResult(
                    check_id=self._next_check_id(),
                    check_type="cross_reference",
                    status="warn",
                    severity="medium",
                    message=f"Finding has no fact citations",
                    details={"finding_id": getattr(finding, 'id', 'unknown')},
                    suggested_action="Add supporting fact references"
                ))
                continue

            # Validate each cited ID
            valid_ids = [fid for fid in cited_ids if fid in all_fact_ids]
            invalid_ids = [fid for fid in cited_ids if fid not in all_fact_ids]

            if invalid_ids:
                results.append(ValidationResult(
                    check_id=self._next_check_id(),
                    check_type="cross_reference",
                    status="fail",
                    severity="high",
                    message=f"Finding cites {len(invalid_ids)} non-existent fact IDs",
                    details={
                        "finding_id": getattr(finding, 'id', 'unknown'),
                        "invalid_ids": invalid_ids,
                        "valid_ids": valid_ids
                    },
                    suggested_action="Correct invalid fact references"
                ))
            else:
                results.append(ValidationResult(
                    check_id=self._next_check_id(),
                    check_type="cross_reference",
                    status="pass",
                    severity="low",
                    message=f"All {len(valid_ids)} fact citations valid",
                    details={"finding_id": getattr(finding, 'id', 'unknown')}
                ))

        return results

    # =========================================================================
    # CONSISTENCY SCORING (Point 83)
    # =========================================================================

    def calculate_consistency_score(
        self,
        fact_store,
        findings: List[Any] = None
    ) -> Dict[str, Any]:
        """
        Score overall analysis consistency (Point 83).

        Returns score 0-100 with breakdown.
        """
        scores = {}

        # Evidence coverage score
        facts = fact_store.facts
        facts_with_evidence = sum(
            1 for f in facts
            if f.evidence and f.evidence.get('exact_quote')
        )
        evidence_rate = facts_with_evidence / len(facts) if facts else 0
        scores['evidence_coverage'] = evidence_rate * 100

        # Cross-reference score (if findings provided)
        if findings:
            valid_citations = 0
            total_citations = 0
            all_fact_ids = set(fact_store.get_all_citable_ids())

            for finding in findings:
                cited = getattr(finding, 'supporting_facts', []) or []
                total_citations += len(cited)
                valid_citations += sum(1 for c in cited if c in all_fact_ids)

            if total_citations > 0:
                scores['cross_reference'] = (valid_citations / total_citations) * 100
            else:
                scores['cross_reference'] = 0
        else:
            scores['cross_reference'] = 100  # No findings to validate

        # Domain balance score
        domain_counts = {}
        for fact in facts:
            domain_counts[fact.domain] = domain_counts.get(fact.domain, 0) + 1

        if domain_counts:
            avg_count = sum(domain_counts.values()) / len(domain_counts)
            variance = sum((c - avg_count) ** 2 for c in domain_counts.values())
            std_dev = (variance / len(domain_counts)) ** 0.5 if domain_counts else 0
            # Higher balance = lower std dev relative to avg
            balance_ratio = 1 - (std_dev / avg_count) if avg_count > 0 else 0
            scores['domain_balance'] = max(0, balance_ratio * 100)
        else:
            scores['domain_balance'] = 0

        # Fact quality score (based on confidence)
        confidence_scores = [
            f.confidence_score if hasattr(f, 'confidence_score') else 0.5
            for f in facts
        ]
        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
        scores['fact_quality'] = avg_confidence * 100

        # Weighted total
        total_score = sum(
            scores[k] * CONSISTENCY_WEIGHTS.get(k, 0.25)
            for k in scores
        )

        return {
            'total_score': round(total_score, 1),
            'grade': self._score_to_grade(total_score),
            'breakdown': {k: round(v, 1) for k, v in scores.items()},
            'weights': CONSISTENCY_WEIGHTS.copy()
        }

    def _score_to_grade(self, score: float) -> str:
        """Convert numeric score to letter grade."""
        if score >= 90:
            return "A"
        elif score >= 80:
            return "B"
        elif score >= 70:
            return "C"
        elif score >= 60:
            return "D"
        else:
            return "F"

    # =========================================================================
    # ANOMALY DETECTION (Point 84)
    # =========================================================================

    def detect_anomalies(self, fact_store) -> List[ValidationResult]:
        """
        Flag unusual findings for human review (Point 84).

        Detects:
        - Numeric outliers (z-score)
        - Text length outliers
        - Low confidence facts
        - Unusual patterns
        """
        results = []
        facts = fact_store.facts

        # Detect low confidence facts
        low_conf = [
            f for f in facts
            if hasattr(f, 'confidence_score')
            and f.confidence_score < ANOMALY_THRESHOLDS['confidence_outlier']
        ]
        if low_conf:
            results.append(ValidationResult(
                check_id=self._next_check_id(),
                check_type="anomaly_detection",
                status="warn",
                severity="medium",
                message=f"{len(low_conf)} facts with low confidence scores",
                details={
                    "fact_ids": [f.fact_id for f in low_conf[:10]],
                    "threshold": ANOMALY_THRESHOLDS['confidence_outlier']
                },
                suggested_action="Review low-confidence facts for accuracy"
            ))

        # Detect facts with unusually long or short items
        item_lengths = [len(f.item) for f in facts]
        if item_lengths:
            avg_len = sum(item_lengths) / len(item_lengths)
            variance = sum((l - avg_len) ** 2 for l in item_lengths) / len(item_lengths)
            std_dev = variance ** 0.5

            if std_dev > 0:
                outliers = [
                    f for f in facts
                    if abs(len(f.item) - avg_len) / std_dev > ANOMALY_THRESHOLDS['text_length_outlier']
                ]
                if outliers:
                    results.append(ValidationResult(
                        check_id=self._next_check_id(),
                        check_type="anomaly_detection",
                        status="warn",
                        severity="low",
                        message=f"{len(outliers)} facts with unusual item lengths",
                        details={
                            "fact_ids": [f.fact_id for f in outliers[:10]],
                            "avg_length": avg_len,
                            "std_dev": std_dev
                        },
                        suggested_action="Review unusually long/short fact items"
                    ))

        # Detect domain imbalance
        domain_counts = {}
        for f in facts:
            domain_counts[f.domain] = domain_counts.get(f.domain, 0) + 1

        if domain_counts:
            avg_count = sum(domain_counts.values()) / len(domain_counts)
            for domain, count in domain_counts.items():
                if count < avg_count * 0.25:  # Less than 25% of average
                    results.append(ValidationResult(
                        check_id=self._next_check_id(),
                        check_type="anomaly_detection",
                        status="warn",
                        severity="medium",
                        message=f"Domain '{domain}' has unusually few facts ({count})",
                        details={
                            "domain": domain,
                            "fact_count": count,
                            "average": avg_count
                        },
                        suggested_action=f"Investigate low coverage in {domain} domain"
                    ))

        if not results:
            results.append(ValidationResult(
                check_id=self._next_check_id(),
                check_type="anomaly_detection",
                status="pass",
                severity="low",
                message="No anomalies detected"
            ))

        return results

    # =========================================================================
    # QA REPORT GENERATION (Point 85)
    # =========================================================================

    def generate_qa_report(
        self,
        fact_store,
        findings: List[Any] = None,
        source_documents: Dict[str, str] = None
    ) -> Dict[str, Any]:
        """
        Generate comprehensive QA report for analysis (Point 85).

        Returns complete quality assessment with recommendations.
        """
        report_sections = {}

        # 1. Consistency scoring
        report_sections['consistency'] = self.calculate_consistency_score(
            fact_store, findings
        )

        # 2. Evidence validation
        evidence_results = []
        if source_documents:
            evidence_results = self.validate_evidence_quotes(
                fact_store.facts, source_documents
            )
        report_sections['evidence_validation'] = {
            'total_checked': len(evidence_results),
            'passed': sum(1 for r in evidence_results if r.status == 'pass'),
            'warnings': sum(1 for r in evidence_results if r.status == 'warn'),
            'failures': sum(1 for r in evidence_results if r.status == 'fail')
        }

        # 3. Cross-reference validation
        xref_results = []
        if findings:
            xref_results = self.validate_cross_references(findings, fact_store)
        report_sections['cross_reference'] = {
            'total_checked': len(xref_results),
            'passed': sum(1 for r in xref_results if r.status == 'pass'),
            'failures': sum(1 for r in xref_results if r.status == 'fail')
        }

        # 4. Anomaly detection
        anomaly_results = self.detect_anomalies(fact_store)
        report_sections['anomalies'] = {
            'total_detected': sum(1 for r in anomaly_results if r.status != 'pass'),
            'results': [r.to_dict() for r in anomaly_results]
        }

        # 5. Coverage analysis
        doc_coverage = fact_store.get_document_coverage()
        report_sections['coverage'] = {
            'documents_analyzed': doc_coverage.get('total_documents', 0),
            'domains_covered': doc_coverage.get('coverage_summary', {}).get('total_domain_count', 0),
            'categories_covered': doc_coverage.get('coverage_summary', {}).get('total_category_count', 0)
        }

        # 6. Duplicate analysis
        duplicates = fact_store.find_duplicates()
        report_sections['duplicates'] = {
            'potential_duplicates': len(duplicates),
            'duplicate_pairs': duplicates[:10]  # First 10
        }

        # 7. Gap analysis
        gap_analysis = fact_store.analyze_gaps()
        report_sections['gaps'] = {
            'total_gaps': gap_analysis.get('total_gaps', 0),
            'critical_gaps': gap_analysis.get('critical_gaps', 0),
            'high_gaps': gap_analysis.get('high_gaps', 0)
        }

        # 8. Confidence summary
        confidence = fact_store.get_confidence_summary()
        report_sections['confidence'] = confidence

        # Generate overall assessment
        overall_score = report_sections['consistency']['total_score']
        overall_grade = report_sections['consistency']['grade']

        # Generate recommendations
        recommendations = []
        if report_sections['evidence_validation']['failures'] > 0:
            recommendations.append("Review and correct evidence quotes that failed validation")
        if report_sections['cross_reference']['failures'] > 0:
            recommendations.append("Fix invalid fact citations in findings")
        if report_sections['duplicates']['potential_duplicates'] > 5:
            recommendations.append("Review and deduplicate similar facts")
        if report_sections['gaps']['critical_gaps'] > 0:
            recommendations.append("Address critical information gaps")
        if confidence.get('distribution', {}).get('low_confidence_under_50', 0) > 10:
            recommendations.append("Improve evidence for low-confidence facts")

        return {
            'generated_at': datetime.utcnow().isoformat(),
            'overall_score': overall_score,
            'overall_grade': overall_grade,
            'sections': report_sections,
            'recommendations': recommendations,
            'summary': f"Analysis quality: {overall_grade} ({overall_score:.0f}/100)"
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
