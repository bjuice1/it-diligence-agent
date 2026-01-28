"""
Validation Report Generator

Generates comprehensive reports on validation status:
- Summary reports for quick review
- Detailed reports for deep-dive
- Audit reports for compliance
- Export to various formats
"""

import json
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path

from models.validation_models import (
    ValidationStatus, FlagSeverity, FlagCategory,
    FactValidationState, DomainValidationState
)
from stores.validation_store import ValidationStore
from stores.correction_store import CorrectionStore
from stores.audit_store import AuditStore, AuditAction

logger = logging.getLogger(__name__)


# =============================================================================
# REPORT DATA CLASSES
# =============================================================================

@dataclass
class ValidationSummaryReport:
    """Summary report for quick review."""
    generated_at: datetime
    overall_confidence: float
    total_facts: int
    facts_validated: int
    facts_flagged: int
    facts_reviewed: int
    facts_confirmed: int
    facts_corrected: int
    facts_rejected: int
    flags_by_severity: Dict[str, int]
    domains: Dict[str, Dict[str, Any]]
    recommendations: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "generated_at": self.generated_at.isoformat(),
            "overall_confidence": self.overall_confidence,
            "total_facts": self.total_facts,
            "facts_validated": self.facts_validated,
            "facts_flagged": self.facts_flagged,
            "facts_reviewed": self.facts_reviewed,
            "facts_confirmed": self.facts_confirmed,
            "facts_corrected": self.facts_corrected,
            "facts_rejected": self.facts_rejected,
            "flags_by_severity": self.flags_by_severity,
            "domains": self.domains,
            "recommendations": self.recommendations
        }


@dataclass
class DetailedValidationReport:
    """Detailed report with per-domain breakdown."""
    summary: ValidationSummaryReport
    domain_details: Dict[str, 'DomainReport']
    cross_domain_findings: List[Dict[str, Any]]
    flagged_facts: List[Dict[str, Any]]
    correction_history: List[Dict[str, Any]]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "summary": self.summary.to_dict(),
            "domain_details": {k: v.to_dict() for k, v in self.domain_details.items()},
            "cross_domain_findings": self.cross_domain_findings,
            "flagged_facts": self.flagged_facts,
            "correction_history": self.correction_history
        }


@dataclass
class DomainReport:
    """Report for a single domain."""
    domain: str
    total_facts: int
    facts_by_category: Dict[str, int]
    confidence_score: float
    flags_count: int
    critical_flags: int
    reviewed_count: int
    category_completeness: Dict[str, float]
    top_issues: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "domain": self.domain,
            "total_facts": self.total_facts,
            "facts_by_category": self.facts_by_category,
            "confidence_score": self.confidence_score,
            "flags_count": self.flags_count,
            "critical_flags": self.critical_flags,
            "reviewed_count": self.reviewed_count,
            "category_completeness": self.category_completeness,
            "top_issues": self.top_issues
        }


@dataclass
class AuditReport:
    """Report of all actions taken."""
    generated_at: datetime
    session_id: Optional[str]
    total_actions: int
    actions_by_type: Dict[str, int]
    actions_by_user: Dict[str, int]
    corrections_made: List[Dict[str, Any]]
    flags_resolved: List[Dict[str, Any]]
    timeline: List[Dict[str, Any]]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "generated_at": self.generated_at.isoformat(),
            "session_id": self.session_id,
            "total_actions": self.total_actions,
            "actions_by_type": self.actions_by_type,
            "actions_by_user": self.actions_by_user,
            "corrections_made": self.corrections_made,
            "flags_resolved": self.flags_resolved,
            "timeline": self.timeline
        }


# =============================================================================
# VALIDATION REPORT GENERATOR
# =============================================================================

class ValidationReportGenerator:
    """
    Generates validation reports from stores.

    Can generate:
    - Summary reports (quick overview)
    - Detailed reports (deep dive)
    - Audit reports (compliance)
    - Exports to Markdown, JSON
    """

    def __init__(
        self,
        validation_store: ValidationStore,
        correction_store: Optional[CorrectionStore] = None,
        audit_store: Optional[AuditStore] = None
    ):
        """
        Initialize the report generator.

        Args:
            validation_store: Store with validation states
            correction_store: Optional store with corrections
            audit_store: Optional store with audit log
        """
        self.validation_store = validation_store
        self.correction_store = correction_store
        self.audit_store = audit_store

    # =========================================================================
    # SUMMARY REPORT
    # =========================================================================

    def generate_summary_report(self) -> ValidationSummaryReport:
        """
        Generate a summary report.

        Returns:
            ValidationSummaryReport with key metrics
        """
        # Get overall stats
        overall_confidence = self.validation_store.get_overall_confidence()

        # Count facts by status
        all_states = self.validation_store.get_all_validation_states()

        total_facts = len(all_states)
        facts_validated = sum(
            1 for s in all_states.values()
            if s.status != ValidationStatus.EXTRACTED
        )
        facts_flagged = sum(
            1 for s in all_states.values()
            if len(s.ai_flags) > 0
        )
        facts_reviewed = sum(
            1 for s in all_states.values()
            if s.human_reviewed
        )
        facts_confirmed = sum(
            1 for s in all_states.values()
            if s.status == ValidationStatus.HUMAN_CONFIRMED
        )
        facts_corrected = sum(
            1 for s in all_states.values()
            if s.status == ValidationStatus.HUMAN_CORRECTED
        )
        facts_rejected = sum(
            1 for s in all_states.values()
            if s.status == ValidationStatus.HUMAN_REJECTED
        )

        # Count flags by severity
        flags_by_severity = {
            "critical": 0,
            "error": 0,
            "warning": 0,
            "info": 0
        }
        for state in all_states.values():
            for flag in state.ai_flags:
                if not flag.resolved:
                    severity = flag.severity.value if hasattr(flag.severity, 'value') else str(flag.severity)
                    if severity in flags_by_severity:
                        flags_by_severity[severity] += 1

        # Domain breakdown
        domains = {}
        domain_states = self.validation_store.get_all_domain_states()
        for domain, state in domain_states.items():
            domains[domain] = {
                "total_facts": state.total_facts,
                "validated": state.facts_validated,
                "flagged": state.facts_flagged,
                "reviewed": state.facts_human_reviewed,
                "confidence": state.overall_confidence
            }

        # Generate recommendations
        recommendations = self._generate_recommendations(
            overall_confidence, flags_by_severity, facts_reviewed, facts_flagged
        )

        return ValidationSummaryReport(
            generated_at=datetime.now(),
            overall_confidence=overall_confidence,
            total_facts=total_facts,
            facts_validated=facts_validated,
            facts_flagged=facts_flagged,
            facts_reviewed=facts_reviewed,
            facts_confirmed=facts_confirmed,
            facts_corrected=facts_corrected,
            facts_rejected=facts_rejected,
            flags_by_severity=flags_by_severity,
            domains=domains,
            recommendations=recommendations
        )

    # =========================================================================
    # DETAILED REPORT
    # =========================================================================

    def generate_detailed_report(self) -> DetailedValidationReport:
        """
        Generate a detailed report.

        Returns:
            DetailedValidationReport with full breakdown
        """
        summary = self.generate_summary_report()

        # Domain details
        domain_details = {}
        for domain in ["organization", "infrastructure", "applications", "network", "security"]:
            domain_details[domain] = self._generate_domain_report(domain)

        # Cross-domain findings
        cross_domain = self.validation_store.get_cross_domain_state()
        cross_domain_findings = []
        if cross_domain:
            for check in cross_domain.consistency_checks:
                if not check.get("is_consistent", True):
                    cross_domain_findings.append(check)

        # Flagged facts details
        flagged_facts = []
        for fact_id, state in self.validation_store.get_all_validation_states().items():
            if state.ai_flags:
                flagged_facts.append({
                    "fact_id": fact_id,
                    "status": state.status.value,
                    "confidence": state.ai_confidence,
                    "flags": [f.to_dict() for f in state.ai_flags if not f.resolved],
                    "human_reviewed": state.human_reviewed
                })

        # Correction history
        correction_history = []
        if self.correction_store:
            for correction in self.correction_store.get_all_corrections():
                correction_history.append(correction.to_dict())

        return DetailedValidationReport(
            summary=summary,
            domain_details=domain_details,
            cross_domain_findings=cross_domain_findings,
            flagged_facts=flagged_facts,
            correction_history=correction_history
        )

    def _generate_domain_report(self, domain: str) -> DomainReport:
        """Generate report for a single domain."""
        state = self.validation_store.get_domain_state(domain)

        # Get facts by category
        facts_by_category = {}
        all_states = self.validation_store.get_all_validation_states()
        for fact_id, fact_state in all_states.items():
            # Would need fact store to get category info
            pass

        # Count critical flags
        critical_flags = 0
        for flag in state.domain_flags:
            if flag.severity == FlagSeverity.CRITICAL:
                critical_flags += 1

        # Top issues
        top_issues = []
        for flag in state.domain_flags[:5]:
            top_issues.append(flag.message)

        return DomainReport(
            domain=domain,
            total_facts=state.total_facts,
            facts_by_category=facts_by_category,
            confidence_score=state.overall_confidence,
            flags_count=len(state.domain_flags),
            critical_flags=critical_flags,
            reviewed_count=state.facts_human_reviewed,
            category_completeness=state.category_completeness,
            top_issues=top_issues
        )

    # =========================================================================
    # AUDIT REPORT
    # =========================================================================

    def generate_audit_report(self) -> AuditReport:
        """
        Generate an audit report.

        Returns:
            AuditReport with all actions taken
        """
        if not self.audit_store:
            return AuditReport(
                generated_at=datetime.now(),
                session_id=None,
                total_actions=0,
                actions_by_type={},
                actions_by_user={},
                corrections_made=[],
                flags_resolved=[],
                timeline=[]
            )

        summary = self.audit_store.get_summary()

        # Get corrections
        corrections_made = []
        correction_entries = self.audit_store.get_audit_log(
            action=AuditAction.HUMAN_CORRECTED,
            limit=100
        )
        for entry in correction_entries:
            corrections_made.append({
                "timestamp": entry.timestamp.isoformat(),
                "fact_id": entry.fact_id,
                "user": entry.user,
                "original": entry.previous_state,
                "corrected": entry.new_state
            })

        # Get resolved flags
        flags_resolved = []
        flag_entries = self.audit_store.get_audit_log(
            action=AuditAction.FLAG_RESOLVED,
            limit=100
        )
        for entry in flag_entries:
            flags_resolved.append({
                "timestamp": entry.timestamp.isoformat(),
                "fact_id": entry.fact_id,
                "user": entry.user,
                "flag_id": entry.details.get("flag_id"),
                "note": entry.details.get("note")
            })

        # Build timeline
        timeline = []
        recent = self.audit_store.get_recent_activity(limit=50)
        for entry in recent:
            timeline.append({
                "timestamp": entry.timestamp.isoformat(),
                "action": entry.action.value,
                "fact_id": entry.fact_id,
                "user": entry.user,
                "details": entry.details
            })

        return AuditReport(
            generated_at=datetime.now(),
            session_id=self.audit_store.session_id,
            total_actions=summary.total_entries,
            actions_by_type=summary.by_action,
            actions_by_user=summary.by_user,
            corrections_made=corrections_made,
            flags_resolved=flags_resolved,
            timeline=timeline
        )

    # =========================================================================
    # EXPORT METHODS
    # =========================================================================

    def export_summary_markdown(self, filepath: Optional[Path] = None) -> str:
        """
        Export summary report as Markdown.

        Args:
            filepath: Optional path to save to

        Returns:
            Markdown string
        """
        report = self.generate_summary_report()

        md = f"""# Validation Summary Report

**Generated:** {report.generated_at.strftime("%Y-%m-%d %H:%M")}

## Overall Status

| Metric | Value |
|--------|-------|
| **Overall Confidence** | **{report.overall_confidence:.0%}** |
| Total Facts | {report.total_facts} |
| Validated | {report.facts_validated} |
| Flagged | {report.facts_flagged} |
| Human Reviewed | {report.facts_reviewed} |
| Confirmed | {report.facts_confirmed} |
| Corrected | {report.facts_corrected} |
| Rejected | {report.facts_rejected} |

## Flags by Severity

| Severity | Count |
|----------|-------|
| Critical | {report.flags_by_severity.get('critical', 0)} |
| Error | {report.flags_by_severity.get('error', 0)} |
| Warning | {report.flags_by_severity.get('warning', 0)} |
| Info | {report.flags_by_severity.get('info', 0)} |

## Domain Status

| Domain | Facts | Validated | Flagged | Reviewed | Confidence |
|--------|-------|-----------|---------|----------|------------|
"""
        for domain, stats in report.domains.items():
            md += f"| {domain} | {stats['total_facts']} | {stats['validated']} | {stats['flagged']} | {stats['reviewed']} | {stats['confidence']:.0%} |\n"

        md += """
## Recommendations

"""
        for rec in report.recommendations:
            md += f"- {rec}\n"

        if filepath:
            filepath.parent.mkdir(parents=True, exist_ok=True)
            with open(filepath, 'w') as f:
                f.write(md)

        return md

    def export_detailed_json(self, filepath: Path) -> bool:
        """
        Export detailed report as JSON.

        Args:
            filepath: Path to save to

        Returns:
            True if successful
        """
        try:
            report = self.generate_detailed_report()
            filepath.parent.mkdir(parents=True, exist_ok=True)
            with open(filepath, 'w') as f:
                json.dump(report.to_dict(), f, indent=2, default=str)
            return True
        except Exception as e:
            logger.error(f"Failed to export report: {e}")
            return False

    def export_audit_markdown(self, filepath: Optional[Path] = None) -> str:
        """
        Export audit report as Markdown.

        Args:
            filepath: Optional path to save to

        Returns:
            Markdown string
        """
        report = self.generate_audit_report()

        md = f"""# Validation Audit Report

**Generated:** {report.generated_at.strftime("%Y-%m-%d %H:%M")}
**Session ID:** {report.session_id or "N/A"}

## Summary

- **Total Actions:** {report.total_actions}
- **Corrections Made:** {len(report.corrections_made)}
- **Flags Resolved:** {len(report.flags_resolved)}

## Actions by Type

| Action | Count |
|--------|-------|
"""
        for action, count in sorted(report.actions_by_type.items(), key=lambda x: -x[1]):
            md += f"| {action} | {count} |\n"

        md += """
## Actions by User

| User | Count |
|------|-------|
"""
        for user, count in sorted(report.actions_by_user.items(), key=lambda x: -x[1]):
            md += f"| {user} | {count} |\n"

        md += """
## Corrections Made

"""
        for corr in report.corrections_made[:20]:
            md += f"- **{corr['timestamp']}** - {corr['user']} corrected fact {corr['fact_id']}\n"

        md += """
## Recent Activity

"""
        for item in report.timeline[:30]:
            md += f"- **{item['timestamp']}** - {item['action']}"
            if item.get('fact_id'):
                md += f" (fact: {item['fact_id']})"
            if item.get('user'):
                md += f" by {item['user']}"
            md += "\n"

        if filepath:
            filepath.parent.mkdir(parents=True, exist_ok=True)
            with open(filepath, 'w') as f:
                f.write(md)

        return md

    # =========================================================================
    # HELPER METHODS
    # =========================================================================

    def _generate_recommendations(
        self,
        confidence: float,
        flags: Dict[str, int],
        reviewed: int,
        flagged: int
    ) -> List[str]:
        """Generate actionable recommendations."""
        recommendations = []

        # Low confidence
        if confidence < 0.7:
            recommendations.append(
                "Overall confidence is below 70%. Review critical and error flags before proceeding."
            )

        # Critical flags
        if flags.get("critical", 0) > 0:
            recommendations.append(
                f"Address {flags['critical']} critical flag(s) immediately - these indicate likely extraction errors."
            )

        # Many flags not reviewed
        if flagged > 0 and reviewed < flagged * 0.5:
            recommendations.append(
                f"Only {reviewed}/{flagged} flagged facts have been reviewed. Complete human review for higher confidence."
            )

        # High error count
        if flags.get("error", 0) > 10:
            recommendations.append(
                f"{flags['error']} error flags detected. Consider re-running extraction with focused prompts."
            )

        # Good state
        if confidence >= 0.9 and flags.get("critical", 0) == 0 and flags.get("error", 0) == 0:
            recommendations.append(
                "Validation looks good. Proceed with confidence, but spot-check key figures."
            )

        return recommendations


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def create_report_generator(
    validation_store: ValidationStore,
    correction_store: Optional[CorrectionStore] = None,
    audit_store: Optional[AuditStore] = None
) -> ValidationReportGenerator:
    """Create a report generator instance."""
    return ValidationReportGenerator(
        validation_store=validation_store,
        correction_store=correction_store,
        audit_store=audit_store
    )


def generate_summary_report(validation_store: ValidationStore) -> ValidationSummaryReport:
    """Convenience function to generate summary report."""
    generator = ValidationReportGenerator(validation_store)
    return generator.generate_summary_report()
