"""
Adversarial Reviewer - Red Team Validation

A skeptical reviewer that actively looks for problems in extracted data.
Unlike neutral validation which checks "is this complete?", adversarial
review assumes there ARE problems and tries to find them.

This catches issues that neutral validation misses by:
- Questioning suspicious patterns
- Looking for missing information that should exist
- Identifying numbers that don't make sense
- Flagging gaps in coverage
- Challenging evidence quality
"""

import json
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from enum import Enum
from datetime import datetime

import anthropic

from models.validation_models import (
    ValidationFlag, FlagSeverity, FlagCategory, generate_flag_id
)

logger = logging.getLogger(__name__)


# =============================================================================
# DATA CLASSES
# =============================================================================

class FindingType(Enum):
    """Types of adversarial findings."""
    MISSING_DATA = "missing_data"
    INCONSISTENCY = "inconsistency"
    SUSPICIOUS_VALUE = "suspicious_value"
    COVERAGE_GAP = "coverage_gap"
    EVIDENCE_QUALITY = "evidence_quality"


@dataclass
class AdversarialFinding:
    """A finding from adversarial review."""
    finding_type: FindingType
    description: str
    affected_facts: List[str]
    suggested_action: str
    confidence: float  # How confident the reviewer is this is a real issue
    severity: str = "warning"  # info, warning, error

    def to_dict(self) -> Dict[str, Any]:
        return {
            "finding_type": self.finding_type.value,
            "description": self.description,
            "affected_facts": self.affected_facts,
            "suggested_action": self.suggested_action,
            "confidence": self.confidence,
            "severity": self.severity
        }


@dataclass
class AdversarialReviewResult:
    """Result of adversarial review for a domain."""
    domain: str
    findings: List[AdversarialFinding] = field(default_factory=list)
    summary: str = ""
    review_timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "domain": self.domain,
            "findings": [f.to_dict() for f in self.findings],
            "summary": self.summary,
            "review_timestamp": self.review_timestamp.isoformat(),
            "finding_count": len(self.findings)
        }


# =============================================================================
# ADVERSARIAL PROMPTS
# =============================================================================

ADVERSARIAL_SYSTEM_PROMPT = """You are a SKEPTICAL reviewer for IT due diligence data extraction.
Your job is to FIND PROBLEMS - assume there ARE issues and look for them.

Be harsh but fair. Question everything. Trust nothing at face value.

Focus on:
1. MISSING DATA - What should be here but isn't?
2. INCONSISTENCIES - What doesn't add up?
3. SUSPICIOUS VALUES - What numbers seem wrong, too round, or unrealistic?
4. COVERAGE GAPS - What topics aren't addressed that should be?
5. EVIDENCE QUALITY - Are claims supported? Is evidence vague or specific?

For each issue found, provide:
- Clear description of the problem
- Why it matters for due diligence
- Specific suggestion for how to fix it
- Confidence level (0.0-1.0) that this is a real issue

DO NOT BE NICE. The purpose is to catch errors before they reach stakeholders.
False flags are acceptable - missing real problems is not."""

DOMAIN_REVIEW_PROMPTS = {
    "organization": """Review this IT ORGANIZATION extraction for problems:

EXTRACTED FACTS:
{facts_json}

DOCUMENT EXCERPT:
{document_excerpt}

Look specifically for:
- Missing teams that should exist (e.g., where's the help desk? security team?)
- Headcounts that don't add up to stated totals
- Suspiciously round numbers (exactly 10, 50, 100 people)
- Missing leadership roles
- Vague outsourcing arrangements
- Budget figures that seem too high or too low
- Teams without clear ownership or headcount

Return a JSON array of findings. Each finding needs:
- "type": "missing_data", "inconsistency", "suspicious_value", "coverage_gap", or "evidence_quality"
- "description": Clear problem statement
- "affected_facts": List of fact_ids or "general"
- "suggested_action": How to fix
- "confidence": 0.0-1.0
- "severity": "info", "warning", or "error"

If no issues found (unlikely), return empty array. Return ONLY valid JSON.""",

    "infrastructure": """Review this IT INFRASTRUCTURE extraction for problems:

EXTRACTED FACTS:
{facts_json}

DOCUMENT EXCERPT:
{document_excerpt}

Look specifically for:
- Missing critical infrastructure (no backup? no DR?)
- Server counts that seem too low for stated company size
- No mention of cloud when modern company
- Hosting details too vague
- Missing storage information
- No virtualization mentioned
- Age of equipment not specified
- Missing monitoring/management tools

Return a JSON array of findings with type, description, affected_facts, suggested_action, confidence, severity.
Return ONLY valid JSON.""",

    "applications": """Review this APPLICATIONS extraction for problems:

EXTRACTED FACTS:
{facts_json}

DOCUMENT EXCERPT:
{document_excerpt}

Look specifically for:
- Missing core business applications (no ERP? no CRM?)
- Vague application descriptions
- No version/age information
- Missing integration details
- Too few applications for company size
- No mention of custom development
- Missing SaaS inventory
- License counts not specified

Return a JSON array of findings with type, description, affected_facts, suggested_action, confidence, severity.
Return ONLY valid JSON.""",

    "security": """Review this SECURITY extraction for problems:

EXTRACTED FACTS:
{facts_json}

DOCUMENT EXCERPT:
{document_excerpt}

Look specifically for:
- Missing basic security controls (AV? firewall?)
- No mention of identity management
- Missing compliance/audit information
- No incident response mentioned
- Vague security policies
- No vulnerability management
- Missing backup/recovery for security
- No security monitoring mentioned

Return a JSON array of findings with type, description, affected_facts, suggested_action, confidence, severity.
Return ONLY valid JSON.""",

    "network": """Review this NETWORK extraction for problems:

EXTRACTED FACTS:
{facts_json}

DOCUMENT EXCERPT:
{document_excerpt}

Look specifically for:
- Missing WAN/LAN details
- No remote access solution mentioned
- Vague network architecture
- Missing redundancy information
- No bandwidth/capacity details
- Missing DNS/DHCP information
- No network security mentioned
- No vendor/carrier details

Return a JSON array of findings with type, description, affected_facts, suggested_action, confidence, severity.
Return ONLY valid JSON."""
}


# =============================================================================
# ADVERSARIAL REVIEWER CLASS
# =============================================================================

class AdversarialReviewer:
    """
    Skeptical reviewer that actively looks for problems.

    Unlike neutral validation, this assumes there ARE issues
    and aggressively tries to find them.
    """

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514"):
        """
        Initialize the adversarial reviewer.

        Args:
            api_key: Anthropic API key
            model: Model to use (Sonnet for thorough review)
        """
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model

    def review_domain(
        self,
        domain: str,
        document_text: str,
        facts: List[Dict],
        max_excerpt_length: int = 15000
    ) -> AdversarialReviewResult:
        """
        Perform adversarial review of a domain's extracted facts.

        Args:
            domain: Domain being reviewed
            document_text: Original document text
            facts: Extracted facts for this domain
            max_excerpt_length: Max chars of document to include

        Returns:
            AdversarialReviewResult with findings
        """
        logger.info(f"Running adversarial review for {domain}")

        # Get domain-specific prompt
        prompt_template = DOMAIN_REVIEW_PROMPTS.get(
            domain,
            DOMAIN_REVIEW_PROMPTS["organization"]  # Default
        )

        # Prepare facts JSON
        facts_json = json.dumps([
            {
                "fact_id": f.get("fact_id", ""),
                "item": f.get("item", ""),
                "category": f.get("category", ""),
                "details": f.get("details", {}),
                "evidence": f.get("evidence", {}).get("exact_quote", "")[:200] if f.get("evidence") else ""
            }
            for f in facts
        ], indent=2)

        # Truncate document if needed
        document_excerpt = document_text[:max_excerpt_length]
        if len(document_text) > max_excerpt_length:
            document_excerpt += "\n\n[Document truncated...]"

        # Build prompt
        prompt = prompt_template.format(
            facts_json=facts_json,
            document_excerpt=document_excerpt
        )

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=3000,
                system=ADVERSARIAL_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}]
            )

            response_text = response.content[0].text.strip()
            raw_findings = self._parse_json_response(response_text)

            # Convert to AdversarialFinding objects
            findings = []
            for raw in raw_findings:
                try:
                    finding = AdversarialFinding(
                        finding_type=FindingType(raw.get("type", "coverage_gap")),
                        description=raw.get("description", ""),
                        affected_facts=raw.get("affected_facts", []),
                        suggested_action=raw.get("suggested_action", ""),
                        confidence=float(raw.get("confidence", 0.5)),
                        severity=raw.get("severity", "warning")
                    )
                    findings.append(finding)
                except (ValueError, KeyError) as e:
                    logger.warning(f"Could not parse finding: {e}")
                    continue

            # Filter low-confidence findings
            findings = [f for f in findings if f.confidence >= 0.4]

            logger.info(f"Adversarial review found {len(findings)} issues in {domain}")

            return AdversarialReviewResult(
                domain=domain,
                findings=findings,
                summary=self._generate_summary(domain, findings)
            )

        except Exception as e:
            logger.error(f"Adversarial review failed for {domain}: {e}")
            return AdversarialReviewResult(
                domain=domain,
                findings=[],
                summary=f"Review failed: {str(e)}"
            )

    def review_all_domains(
        self,
        fact_store,
        document_text: str
    ) -> Dict[str, AdversarialReviewResult]:
        """
        Review all domains.

        Args:
            fact_store: FactStore with all facts
            document_text: Original document

        Returns:
            Dict mapping domain -> AdversarialReviewResult
        """
        results = {}

        for domain in ["organization", "infrastructure", "applications", "network", "security"]:
            facts = self._get_domain_facts(fact_store, domain)
            if facts:
                results[domain] = self.review_domain(domain, document_text, facts)
            else:
                results[domain] = AdversarialReviewResult(
                    domain=domain,
                    findings=[],
                    summary="No facts to review"
                )

        return results

    def findings_to_flags(
        self,
        findings: List[AdversarialFinding]
    ) -> List[ValidationFlag]:
        """
        Convert adversarial findings to validation flags.

        Uses WARNING severity since findings are speculative.
        """
        flags = []

        severity_map = {
            "info": FlagSeverity.INFO,
            "warning": FlagSeverity.WARNING,
            "error": FlagSeverity.WARNING  # Cap at WARNING for adversarial
        }

        for finding in findings:
            # Only high-confidence findings become flags
            if finding.confidence >= 0.6:
                flag = ValidationFlag(
                    flag_id=generate_flag_id(),
                    severity=severity_map.get(finding.severity, FlagSeverity.WARNING),
                    category=FlagCategory.ADVERSARIAL,
                    message=f"[Adversarial] {finding.description}",
                    suggestion=finding.suggested_action
                )
                flags.append(flag)

        return flags

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

    def _parse_json_response(self, response_text: str) -> List[Dict]:
        """Parse JSON from LLM response."""
        # Handle markdown code blocks
        if "```" in response_text:
            parts = response_text.split("```")
            for part in parts:
                part = part.strip()
                if part.startswith("json"):
                    part = part[4:].strip()
                try:
                    result = json.loads(part)
                    if isinstance(result, list):
                        return result
                except json.JSONDecodeError:
                    continue

        # Try direct parse
        try:
            result = json.loads(response_text)
            return result if isinstance(result, list) else []
        except json.JSONDecodeError:
            return []

    def _generate_summary(self, domain: str, findings: List[AdversarialFinding]) -> str:
        """Generate a summary of adversarial review."""
        if not findings:
            return f"No significant issues found in {domain}"

        by_type = {}
        for f in findings:
            by_type.setdefault(f.finding_type.value, []).append(f)

        parts = [f"Found {len(findings)} potential issues in {domain}:"]
        for type_name, type_findings in by_type.items():
            parts.append(f"  - {type_name}: {len(type_findings)}")

        high_confidence = [f for f in findings if f.confidence >= 0.7]
        if high_confidence:
            parts.append(f"  ({len(high_confidence)} high-confidence)")

        return " ".join(parts)


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def create_adversarial_reviewer(api_key: str) -> AdversarialReviewer:
    """Create an adversarial reviewer instance."""
    return AdversarialReviewer(api_key=api_key)


def review_domain_adversarially(
    api_key: str,
    domain: str,
    document_text: str,
    facts: List[Dict]
) -> AdversarialReviewResult:
    """Convenience function to run adversarial review."""
    reviewer = AdversarialReviewer(api_key=api_key)
    return reviewer.review_domain(domain, document_text, facts)
