"""
Category Validator - Layer 1 Validation

Validates extraction completeness at the category level.
Uses a combination of:
1. Deterministic checks (field presence, item counts)
2. LLM validation (comparing extracted items to document)

This is the first validation layer - fast and focused on obvious gaps.
"""

import json
import re
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

import anthropic

from tools_v2.category_checkpoints import (
    CategoryCheckpoint,
    get_checkpoints_for_domain,
    get_checkpoint,
    DOMAIN_CHECKPOINTS
)
from models.validation_models import (
    ValidationFlag, FlagSeverity, FlagCategory, generate_flag_id
)

logger = logging.getLogger(__name__)


# =============================================================================
# CONFIGURATION
# =============================================================================

DEFAULT_MODEL = "claude-3-5-haiku-20241022"  # Fast model for category checks
MAX_DOCUMENT_EXCERPT = 12000  # Max chars to send to LLM
CONFIDENCE_THRESHOLD_PASS = 0.85  # Above this = pass without LLM
CONFIDENCE_THRESHOLD_RETRY = 0.60  # Below this = definitely retry


# =============================================================================
# RESULT MODELS
# =============================================================================

@dataclass
class CategoryValidationResult:
    """Result of validating a single category."""
    domain: str
    category: str
    is_complete: bool
    confidence: float

    # Details
    extracted_count: int = 0
    expected_min: int = 0
    expected_max: int = 0

    # Issues found
    missing_fields: List[Dict[str, Any]] = field(default_factory=list)
    missing_items: List[Dict[str, Any]] = field(default_factory=list)
    incorrect_items: List[Dict[str, Any]] = field(default_factory=list)

    # Flags generated
    flags: List[ValidationFlag] = field(default_factory=list)

    # Recommendation
    recommendation: str = "pass"  # "pass", "retry", "manual"
    rerun_guidance: Optional[str] = None

    # Timing
    validation_time_ms: float = 0.0
    used_llm: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "domain": self.domain,
            "category": self.category,
            "is_complete": self.is_complete,
            "confidence": self.confidence,
            "extracted_count": self.extracted_count,
            "expected_min": self.expected_min,
            "expected_max": self.expected_max,
            "missing_items_count": len(self.missing_items),
            "recommendation": self.recommendation,
            "rerun_guidance": self.rerun_guidance,
            "flags_count": len(self.flags),
            "validation_time_ms": self.validation_time_ms,
            "used_llm": self.used_llm
        }


@dataclass
class DomainCategoryValidationReport:
    """Summary of category validation for an entire domain."""
    domain: str
    total_categories: int
    categories_complete: int = 0
    categories_incomplete: int = 0
    categories_skipped: int = 0

    # Results by category
    results: Dict[str, CategoryValidationResult] = field(default_factory=dict)

    # Aggregated issues
    all_missing_items: List[Dict[str, Any]] = field(default_factory=list)
    all_flags: List[ValidationFlag] = field(default_factory=list)

    # Overall
    overall_completeness: float = 0.0
    requires_rerun: bool = False
    rerun_categories: List[str] = field(default_factory=list)

    # Timing
    total_time_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "domain": self.domain,
            "total_categories": self.total_categories,
            "categories_complete": self.categories_complete,
            "categories_incomplete": self.categories_incomplete,
            "overall_completeness": self.overall_completeness,
            "requires_rerun": self.requires_rerun,
            "rerun_categories": self.rerun_categories,
            "total_missing_items": len(self.all_missing_items),
            "total_flags": len(self.all_flags),
            "total_time_ms": self.total_time_ms
        }


# =============================================================================
# CATEGORY VALIDATOR CLASS
# =============================================================================

class CategoryValidator:
    """
    Layer 1 Validator - validates extraction at the category level.

    Uses fast deterministic checks first, then LLM validation if needed.
    """

    def __init__(self, api_key: str, model: str = DEFAULT_MODEL):
        """
        Initialize the category validator.

        Args:
            api_key: Anthropic API key
            model: Model to use for LLM validation
        """
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model

    # =========================================================================
    # MAIN VALIDATION METHOD
    # =========================================================================

    def validate_category(
        self,
        domain: str,
        category: str,
        document_text: str,
        extracted_facts: List[Dict[str, Any]],
        force_llm: bool = False
    ) -> CategoryValidationResult:
        """
        Validate a single category's extraction.

        Args:
            domain: Domain name (organization, infrastructure, etc.)
            category: Category name within the domain
            document_text: Full or relevant excerpt of source document
            extracted_facts: List of facts extracted for this category
            force_llm: If True, always use LLM validation

        Returns:
            CategoryValidationResult with completeness assessment
        """
        import time
        start_time = time.time()

        # Get checkpoint for this category
        checkpoint = get_checkpoint(domain, category)
        if not checkpoint:
            logger.warning(f"No checkpoint defined for {domain}/{category}")
            return CategoryValidationResult(
                domain=domain,
                category=category,
                is_complete=True,
                confidence=0.5,
                recommendation="pass"
            )

        result = CategoryValidationResult(
            domain=domain,
            category=category,
            is_complete=False,
            confidence=0.0,
            extracted_count=len(extracted_facts),
            expected_min=checkpoint.min_expected_items,
            expected_max=checkpoint.max_expected_items
        )

        # Step 1: Deterministic pre-checks
        pre_check_result = self._run_deterministic_checks(
            extracted_facts, checkpoint, result
        )

        # If deterministic checks are conclusive, we might skip LLM
        if pre_check_result["skip_llm"] and not force_llm:
            result.is_complete = pre_check_result["is_complete"]
            result.confidence = pre_check_result["confidence"]
            result.recommendation = self._determine_recommendation(result)
            result.validation_time_ms = (time.time() - start_time) * 1000
            return result

        # Step 2: LLM validation for uncertain cases
        llm_result = self._run_llm_validation(
            domain, category, document_text, extracted_facts, checkpoint
        )
        result.used_llm = True

        # Merge LLM findings
        self._merge_llm_findings(result, llm_result)

        # Step 3: Determine final status
        result.is_complete = self._calculate_completeness(result, llm_result)
        result.confidence = llm_result.get("confidence", 0.7)
        result.recommendation = self._determine_recommendation(result)

        # Generate rerun guidance if needed
        if result.recommendation == "retry":
            result.rerun_guidance = self._generate_rerun_guidance(result)

        # Generate flags
        result.flags = self._generate_flags(result, checkpoint)

        result.validation_time_ms = (time.time() - start_time) * 1000

        logger.info(
            f"Category validation {domain}/{category}: "
            f"complete={result.is_complete}, conf={result.confidence:.2f}, "
            f"rec={result.recommendation}"
        )

        return result

    # =========================================================================
    # DETERMINISTIC CHECKS
    # =========================================================================

    def _run_deterministic_checks(
        self,
        extracted_facts: List[Dict[str, Any]],
        checkpoint: CategoryCheckpoint,
        result: CategoryValidationResult
    ) -> Dict[str, Any]:
        """
        Run fast deterministic checks before LLM.

        Returns dict with:
            skip_llm: Whether we can skip LLM validation
            is_complete: Whether category appears complete
            confidence: Confidence in the assessment
        """
        check_result = {
            "skip_llm": False,
            "is_complete": False,
            "confidence": 0.0
        }

        count = len(extracted_facts)
        min_expected = checkpoint.min_expected_items
        max_expected = checkpoint.max_expected_items

        # Check 1: Count within expected range
        if count >= min_expected:
            # Might be complete - check required fields
            missing_fields = self._check_required_fields(
                extracted_facts, checkpoint.required_fields
            )
            result.missing_fields = missing_fields

            if not missing_fields:
                # All required fields present, count is good
                check_result["is_complete"] = True
                check_result["confidence"] = 0.75

                # If count is well within range, high confidence
                if min_expected <= count <= max_expected:
                    check_result["confidence"] = 0.85
                    # Could skip LLM for high-confidence cases
                    if count >= min_expected * 1.5:
                        check_result["skip_llm"] = True
                        check_result["confidence"] = 0.90
            else:
                # Missing fields - need LLM to check
                check_result["confidence"] = 0.5

        # Check 2: Obviously incomplete (zero items for required category)
        if count == 0 and min_expected > 0:
            check_result["is_complete"] = False
            check_result["confidence"] = 0.95
            # Still use LLM to find what's missing

        # Check 3: Suspiciously high count
        if count > max_expected * 2:
            # Might have duplicates or over-extraction
            check_result["confidence"] = 0.5

        return check_result

    def _check_required_fields(
        self,
        facts: List[Dict[str, Any]],
        required_fields: List[str]
    ) -> List[Dict[str, Any]]:
        """Check if all required fields are present in extracted facts."""
        missing = []

        for i, fact in enumerate(facts):
            details = fact.get("details", {})
            fact_id = fact.get("fact_id", f"fact_{i}")

            for field in required_fields:
                # Check in details or top-level
                value = details.get(field) or fact.get(field)
                if not value or (isinstance(value, str) and not value.strip()):
                    missing.append({
                        "fact_id": fact_id,
                        "field": field,
                        "item": fact.get("item", "Unknown")
                    })

        return missing

    # =========================================================================
    # LLM VALIDATION
    # =========================================================================

    def _run_llm_validation(
        self,
        domain: str,
        category: str,
        document_text: str,
        extracted_facts: List[Dict[str, Any]],
        checkpoint: CategoryCheckpoint
    ) -> Dict[str, Any]:
        """
        Use LLM to validate extraction against document.

        Returns parsed LLM response with findings.
        """
        # Extract relevant document section
        document_excerpt = self._extract_relevant_section(
            document_text, category, checkpoint
        )

        # Format extracted items for prompt
        extracted_items = self._format_extracted_items(extracted_facts)

        # Build prompt from checkpoint template
        prompt = checkpoint.validation_prompt.format(
            document_excerpt=document_excerpt[:MAX_DOCUMENT_EXCERPT],
            extracted_items=extracted_items
        )

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            response_text = response.content[0].text
            return self._parse_validation_response(response_text)

        except Exception as e:
            logger.error(f"LLM validation failed for {domain}/{category}: {e}")
            return {
                "is_complete": False,
                "confidence": 0.5,
                "error": str(e)
            }

    def _extract_relevant_section(
        self,
        document_text: str,
        category: str,
        checkpoint: CategoryCheckpoint
    ) -> str:
        """
        Find the portion of document most relevant to this category.

        Uses keyword matching to find relevant paragraphs.
        """
        # Keywords based on category
        category_keywords = self._get_category_keywords(category)

        lines = document_text.split('\n')
        relevant_lines = []
        context_before = 3
        context_after = 5

        for i, line in enumerate(lines):
            line_lower = line.lower()
            if any(kw in line_lower for kw in category_keywords):
                # Add surrounding context
                start = max(0, i - context_before)
                end = min(len(lines), i + context_after + 1)
                for j in range(start, end):
                    if lines[j] not in relevant_lines:
                        relevant_lines.append(lines[j])

        if relevant_lines:
            return '\n'.join(relevant_lines)

        # Fallback: return first portion of document
        return document_text[:MAX_DOCUMENT_EXCERPT]

    def _get_category_keywords(self, category: str) -> List[str]:
        """Get search keywords for a category."""
        keyword_map = {
            # Organization
            "central_it": ["team", "department", "headcount", "staff", "fte", "personnel"],
            "leadership": ["cio", "vp", "director", "leader", "reports to", "chief"],
            "outsourcing": ["outsourc", "vendor", "managed service", "msp", "offshore"],
            "roles": ["role", "position", "analyst", "engineer", "developer", "admin"],
            "contractors": ["contractor", "contingent", "temporary", "consultant"],
            "governance": ["governance", "committee", "steering", "board", "process"],

            # Infrastructure
            "hosting": ["data center", "datacenter", "colocation", "colo", "hosting"],
            "compute": ["server", "vm", "virtual machine", "compute", "cpu", "core"],
            "storage": ["storage", "san", "nas", "disk", "tb", "petabyte"],
            "backup_dr": ["backup", "disaster recovery", "dr", "rpo", "rto", "recovery"],
            "cloud": ["aws", "azure", "gcp", "cloud", "iaas", "paas"],
            "virtualization": ["vmware", "hyper-v", "virtualization", "esxi", "vcenter"],
            "endpoints": ["desktop", "laptop", "workstation", "endpoint", "pc"],

            # Applications
            "erp": ["erp", "sap", "oracle", "dynamics", "netsuite", "enterprise resource"],
            "crm": ["crm", "salesforce", "dynamics", "customer relationship"],
            "saas": ["saas", "software as a service", "subscription", "cloud app"],
            "custom": ["custom", "in-house", "proprietary", "developed", "legacy"],
            "integration": ["integration", "middleware", "api", "esb", "mulesoft"],
            "database": ["database", "sql", "oracle", "postgres", "mongo", "db"],

            # Network
            "wan": ["wan", "mpls", "internet", "connectivity", "bandwidth", "circuit"],
            "lan": ["lan", "switch", "wireless", "wifi", "network"],
            "remote_access": ["vpn", "remote access", "citrix", "rds", "terminal"],
            "dns_dhcp": ["dns", "dhcp", "domain name", "ip address"],

            # Security
            "endpoint_security": ["antivirus", "edr", "endpoint protection", "crowdstrike", "defender"],
            "perimeter": ["firewall", "ips", "ids", "palo alto", "fortinet", "perimeter"],
            "identity": ["identity", "sso", "mfa", "active directory", "okta", "authentication"],
            "siem": ["siem", "splunk", "sentinel", "soc", "security monitoring"],
            "vulnerability": ["vulnerability", "scanning", "patch", "qualys", "tenable"],
            "email_security": ["email security", "spam", "proofpoint", "mimecast", "dlp"],
        }

        return keyword_map.get(category, [category.replace("_", " ")])

    def _format_extracted_items(self, facts: List[Dict[str, Any]]) -> str:
        """Format extracted facts for LLM prompt."""
        if not facts:
            return "No items extracted."

        items = []
        for fact in facts:
            item_name = fact.get("item", "Unknown")
            details = fact.get("details", {})

            detail_str = ", ".join(
                f"{k}: {v}" for k, v in details.items()
                if v and k not in ["item", "category"]
            )

            if detail_str:
                items.append(f"- {item_name} ({detail_str})")
            else:
                items.append(f"- {item_name}")

        return "\n".join(items)

    def _parse_validation_response(self, response_text: str) -> Dict[str, Any]:
        """Parse LLM response, handling markdown code blocks."""
        try:
            # Handle markdown code blocks
            if "```" in response_text:
                # Extract content between code blocks
                parts = response_text.split("```")
                if len(parts) >= 2:
                    json_part = parts[1]
                    # Remove language identifier if present
                    if json_part.startswith("json"):
                        json_part = json_part[4:]
                    response_text = json_part.strip()

            return json.loads(response_text)

        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse LLM response as JSON: {e}")
            # Try to extract key information from text
            return {
                "is_complete": "complete" in response_text.lower(),
                "confidence": 0.5,
                "parse_error": str(e),
                "raw_response": response_text[:500]
            }

    # =========================================================================
    # RESULT PROCESSING
    # =========================================================================

    def _merge_llm_findings(
        self,
        result: CategoryValidationResult,
        llm_result: Dict[str, Any]
    ):
        """Merge LLM findings into validation result."""
        # Missing items
        missing_items = llm_result.get("missing_items", [])
        if missing_items:
            result.missing_items.extend(missing_items)

        # Incorrect items
        incorrect_items = llm_result.get("incorrect_items", [])
        if incorrect_items:
            result.incorrect_items.extend(incorrect_items)

    def _calculate_completeness(
        self,
        result: CategoryValidationResult,
        llm_result: Dict[str, Any]
    ) -> bool:
        """Calculate if category is complete based on all findings."""
        # If LLM says complete and we have enough items
        if llm_result.get("is_complete", False):
            if result.extracted_count >= result.expected_min:
                return True

        # If we have missing items, not complete
        if result.missing_items:
            return False

        # If count is below minimum, not complete
        if result.extracted_count < result.expected_min:
            return False

        return True

    def _determine_recommendation(
        self,
        result: CategoryValidationResult
    ) -> str:
        """Determine recommendation based on validation result."""
        if result.is_complete and result.confidence >= CONFIDENCE_THRESHOLD_PASS:
            return "pass"

        if result.missing_items and len(result.missing_items) <= 5:
            return "retry"  # Few missing items - automated retry possible

        if result.extracted_count == 0 and result.expected_min > 0:
            return "retry"  # Nothing extracted but should have - retry

        if result.confidence < CONFIDENCE_THRESHOLD_RETRY:
            return "retry"

        if len(result.missing_items) > 5:
            return "retry"  # Still try automated first

        return "pass"

    def _generate_rerun_guidance(
        self,
        result: CategoryValidationResult
    ) -> str:
        """Generate specific guidance for re-extraction."""
        guidance_parts = []

        if result.missing_items:
            items_list = ", ".join(
                item.get("item", "Unknown") for item in result.missing_items[:5]
            )
            guidance_parts.append(f"Missing items to extract: {items_list}")

        if result.missing_fields:
            fields = set(mf["field"] for mf in result.missing_fields[:5])
            guidance_parts.append(f"Missing required fields: {', '.join(fields)}")

        if result.extracted_count < result.expected_min:
            guidance_parts.append(
                f"Only {result.extracted_count} items found, expected at least {result.expected_min}"
            )

        return " | ".join(guidance_parts) if guidance_parts else "Re-extract with more thorough search"

    def _generate_flags(
        self,
        result: CategoryValidationResult,
        checkpoint: CategoryCheckpoint
    ) -> List[ValidationFlag]:
        """Generate validation flags based on findings."""
        flags = []

        # Flag for missing items
        if result.missing_items:
            severity = (
                FlagSeverity.ERROR if checkpoint.importance == "critical"
                else FlagSeverity.WARNING
            )
            flags.append(ValidationFlag(
                flag_id=generate_flag_id(),
                severity=severity,
                category=FlagCategory.COMPLETENESS,
                message=(
                    f"Category '{result.category}' has {len(result.missing_items)} "
                    f"missing items identified by validation"
                ),
                suggestion=(
                    f"Missing: {', '.join(m.get('item', '?') for m in result.missing_items[:3])}"
                    + ("..." if len(result.missing_items) > 3 else "")
                )
            ))

        # Flag for missing required fields
        if result.missing_fields:
            flags.append(ValidationFlag(
                flag_id=generate_flag_id(),
                severity=FlagSeverity.WARNING,
                category=FlagCategory.COMPLETENESS,
                message=(
                    f"Category '{result.category}' has items missing required fields"
                ),
                suggestion=(
                    f"Check items for missing: "
                    f"{', '.join(set(mf['field'] for mf in result.missing_fields[:3]))}"
                )
            ))

        # Flag for low count
        if result.extracted_count < result.expected_min and checkpoint.importance in ["critical", "high"]:
            flags.append(ValidationFlag(
                flag_id=generate_flag_id(),
                severity=FlagSeverity.WARNING,
                category=FlagCategory.COMPLETENESS,
                message=(
                    f"Category '{result.category}' has only {result.extracted_count} items "
                    f"(expected at least {result.expected_min})"
                ),
                suggestion="Review document for additional items in this category"
            ))

        # Flag for incorrect items
        if result.incorrect_items:
            flags.append(ValidationFlag(
                flag_id=generate_flag_id(),
                severity=FlagSeverity.ERROR,
                category=FlagCategory.ACCURACY,
                message=(
                    f"Category '{result.category}' has {len(result.incorrect_items)} "
                    f"potentially incorrect items"
                ),
                suggestion="Review flagged items for accuracy"
            ))

        return flags

    # =========================================================================
    # BATCH VALIDATION
    # =========================================================================

    def validate_all_categories(
        self,
        domain: str,
        document_text: str,
        facts_by_category: Dict[str, List[Dict[str, Any]]]
    ) -> DomainCategoryValidationReport:
        """
        Validate all categories for a domain.

        Args:
            domain: Domain name
            document_text: Source document text
            facts_by_category: Dict mapping category name to list of facts

        Returns:
            DomainCategoryValidationReport with all results
        """
        import time
        start_time = time.time()

        checkpoints = get_checkpoints_for_domain(domain)

        report = DomainCategoryValidationReport(
            domain=domain,
            total_categories=len(checkpoints)
        )

        for category, checkpoint in checkpoints.items():
            category_facts = facts_by_category.get(category, [])

            result = self.validate_category(
                domain=domain,
                category=category,
                document_text=document_text,
                extracted_facts=category_facts
            )

            report.results[category] = result

            # Aggregate stats
            if result.is_complete:
                report.categories_complete += 1
            else:
                report.categories_incomplete += 1
                if result.recommendation == "retry":
                    report.rerun_categories.append(category)

            # Aggregate issues
            report.all_missing_items.extend(result.missing_items)
            report.all_flags.extend(result.flags)

        # Calculate overall completeness
        if report.total_categories > 0:
            report.overall_completeness = (
                report.categories_complete / report.total_categories
            )

        report.requires_rerun = len(report.rerun_categories) > 0
        report.total_time_ms = (time.time() - start_time) * 1000

        logger.info(
            f"Domain category validation for {domain}: "
            f"{report.categories_complete}/{report.total_categories} complete, "
            f"rerun needed: {report.requires_rerun}"
        )

        return report


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def validate_category(
    api_key: str,
    domain: str,
    category: str,
    document_text: str,
    extracted_facts: List[Dict[str, Any]]
) -> CategoryValidationResult:
    """Convenience function for single category validation."""
    validator = CategoryValidator(api_key=api_key)
    return validator.validate_category(
        domain=domain,
        category=category,
        document_text=document_text,
        extracted_facts=extracted_facts
    )


def validate_domain_categories(
    api_key: str,
    domain: str,
    document_text: str,
    facts_by_category: Dict[str, List[Dict[str, Any]]]
) -> DomainCategoryValidationReport:
    """Convenience function for domain-wide category validation."""
    validator = CategoryValidator(api_key=api_key)
    return validator.validate_all_categories(
        domain=domain,
        document_text=document_text,
        facts_by_category=facts_by_category
    )
