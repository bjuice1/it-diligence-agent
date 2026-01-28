"""
Domain Validator - Layer 2 Validation

Performs thorough validation at the domain level after category validation.
Uses Sonnet model for deeper analysis including:
1. Cross-category consistency within domain
2. Headcount and cost sanity checks
3. Missing critical information detection
4. Data quality assessment

This layer catches issues that span multiple categories.
"""

import json
import re
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

import anthropic

from models.validation_models import (
    ValidationFlag, FlagSeverity, FlagCategory, generate_flag_id
)

logger = logging.getLogger(__name__)


# =============================================================================
# CONFIGURATION
# =============================================================================

DEFAULT_MODEL = "claude-3-5-sonnet-20241022"  # Use Sonnet for thorough validation
MAX_DOCUMENT_EXCERPT = 15000
COMPLETENESS_THRESHOLD = 0.70  # Below this = requires rerun


# =============================================================================
# RESULT MODELS
# =============================================================================

@dataclass
class DomainValidationResult:
    """Result of validating an entire domain."""
    domain: str
    is_valid: bool
    completeness_score: float  # 0.0 - 1.0
    quality_score: float       # 0.0 - 1.0

    # Facts summary
    total_facts: int = 0
    facts_by_category: Dict[str, int] = field(default_factory=dict)

    # Issues found
    missing_items: List[Dict[str, Any]] = field(default_factory=list)
    inconsistencies: List[Dict[str, Any]] = field(default_factory=list)
    quality_issues: List[Dict[str, Any]] = field(default_factory=list)

    # Recommendations
    recommendations: List[str] = field(default_factory=list)
    requires_rerun: bool = False
    rerun_guidance: Optional[str] = None

    # Flags generated
    flags: List[ValidationFlag] = field(default_factory=list)

    # Timing
    validation_time_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "domain": self.domain,
            "is_valid": self.is_valid,
            "completeness_score": self.completeness_score,
            "quality_score": self.quality_score,
            "total_facts": self.total_facts,
            "missing_items_count": len(self.missing_items),
            "inconsistencies_count": len(self.inconsistencies),
            "requires_rerun": self.requires_rerun,
            "rerun_guidance": self.rerun_guidance,
            "flags_count": len(self.flags),
            "recommendations": self.recommendations,
            "validation_time_ms": self.validation_time_ms
        }


# =============================================================================
# DOMAIN VALIDATOR CLASS
# =============================================================================

class DomainValidator:
    """
    Layer 2 Validator - validates entire domain after category checks.

    Performs deeper analysis using Sonnet model to catch:
    - Cross-category consistency issues
    - Missing critical information
    - Data quality problems
    - Numerical inconsistencies
    """

    def __init__(self, api_key: str, model: str = DEFAULT_MODEL):
        """
        Initialize the domain validator.

        Args:
            api_key: Anthropic API key
            model: Model to use (default: Sonnet for thorough validation)
        """
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model

    # =========================================================================
    # MAIN VALIDATION METHOD
    # =========================================================================

    def validate(
        self,
        domain: str,
        document_text: str,
        facts: List[Dict[str, Any]],
        gaps: Optional[List[Dict[str, Any]]] = None
    ) -> DomainValidationResult:
        """
        Validate an entire domain's extraction.

        Args:
            domain: Domain name (organization, infrastructure, etc.)
            document_text: Source document text
            facts: All facts extracted for this domain
            gaps: Optional list of identified gaps

        Returns:
            DomainValidationResult with comprehensive assessment
        """
        # Route to domain-specific validator
        if domain == "organization":
            return self.validate_organization(document_text, facts, gaps)
        elif domain == "infrastructure":
            return self.validate_infrastructure(document_text, facts, gaps)
        elif domain == "applications":
            return self.validate_applications(document_text, facts, gaps)
        elif domain == "network":
            return self.validate_network(document_text, facts, gaps)
        elif domain == "security":
            return self.validate_security(document_text, facts, gaps)
        else:
            # Generic validation for unknown domains
            return self._validate_generic(domain, document_text, facts, gaps)

    # =========================================================================
    # ORGANIZATION DOMAIN VALIDATOR
    # =========================================================================

    def validate_organization(
        self,
        document_text: str,
        facts: List[Dict[str, Any]],
        gaps: Optional[List[Dict[str, Any]]] = None
    ) -> DomainValidationResult:
        """Validate organization domain extraction."""
        import time
        start_time = time.time()

        result = DomainValidationResult(
            domain="organization",
            is_valid=True,
            completeness_score=1.0,
            quality_score=1.0,
            total_facts=len(facts)
        )

        # Categorize facts
        facts_by_category = self._categorize_facts(facts)
        result.facts_by_category = {
            cat: len(cat_facts) for cat, cat_facts in facts_by_category.items()
        }

        # Check 1: Team extraction completeness
        central_it_facts = facts_by_category.get("central_it", [])
        team_count = len(central_it_facts)

        if team_count < 5:
            result.completeness_score -= 0.2
            result.recommendations.append(
                f"Only {team_count} teams extracted. Expected 5-7 for typical IT org."
            )
            result.flags.append(ValidationFlag(
                flag_id=generate_flag_id(),
                severity=FlagSeverity.WARNING,
                category=FlagCategory.COMPLETENESS,
                message=f"Low team count: {team_count} teams extracted",
                suggestion="Review document for additional IT teams/departments"
            ))

        # Check 2: Headcount consistency
        headcount_check = self._check_headcount_consistency(
            document_text, central_it_facts, facts
        )
        if headcount_check["has_issue"]:
            result.completeness_score -= 0.15
            result.inconsistencies.append(headcount_check)
            result.flags.append(ValidationFlag(
                flag_id=generate_flag_id(),
                severity=FlagSeverity.ERROR,
                category=FlagCategory.CONSISTENCY,
                message=headcount_check["message"],
                suggestion=headcount_check.get("suggestion", "Verify headcount figures")
            ))

        # Check 3: Required categories present
        required_categories = ["central_it"]
        for cat in required_categories:
            if cat not in facts_by_category or not facts_by_category[cat]:
                result.completeness_score -= 0.15
                result.recommendations.append(f"Missing required category: {cat}")

        # Check 4: Leadership captured
        leadership_facts = facts_by_category.get("leadership", [])
        if not leadership_facts:
            result.completeness_score -= 0.1
            result.flags.append(ValidationFlag(
                flag_id=generate_flag_id(),
                severity=FlagSeverity.WARNING,
                category=FlagCategory.COMPLETENESS,
                message="No IT leadership roles extracted",
                suggestion="Look for CIO, VP IT, IT Director mentions in document"
            ))

        # Check 5: Cost sanity (if costs present)
        cost_check = self._check_cost_sanity(central_it_facts)
        if cost_check["has_issue"]:
            result.quality_score -= 0.1
            result.quality_issues.append(cost_check)
            result.flags.append(ValidationFlag(
                flag_id=generate_flag_id(),
                severity=FlagSeverity.WARNING,
                category=FlagCategory.CONSISTENCY,
                message=cost_check["message"],
                suggestion=cost_check.get("suggestion", "Review cost figures")
            ))

        # Check 6: LLM deep validation
        llm_result = self._llm_validate_organization(document_text, facts)
        self._merge_llm_findings(result, llm_result)

        # Calculate final scores
        result.completeness_score = max(0.0, result.completeness_score)
        result.quality_score = max(0.0, result.quality_score)

        # Determine if rerun needed
        result.requires_rerun = result.completeness_score < COMPLETENESS_THRESHOLD
        if result.requires_rerun:
            result.rerun_guidance = self._generate_rerun_guidance(result)
            result.is_valid = False

        result.validation_time_ms = (time.time() - start_time) * 1000

        logger.info(
            f"Organization validation: completeness={result.completeness_score:.2f}, "
            f"quality={result.quality_score:.2f}, rerun={result.requires_rerun}"
        )

        return result

    def _check_headcount_consistency(
        self,
        document_text: str,
        team_facts: List[Dict[str, Any]],
        all_facts: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Check if extracted headcounts match stated totals."""
        # Calculate total from extracted teams
        total_extracted = 0
        for fact in team_facts:
            details = fact.get("details", {})
            headcount = details.get("headcount", 0)
            if isinstance(headcount, str):
                # Parse numeric value from string
                match = re.search(r'(\d+)', str(headcount))
                if match:
                    headcount = int(match.group(1))
                else:
                    headcount = 0
            total_extracted += int(headcount) if headcount else 0

        # Try to find stated total in document
        stated_total = self._find_stated_headcount(document_text, all_facts)

        if stated_total and total_extracted:
            ratio = total_extracted / stated_total
            if ratio < 0.8:
                return {
                    "has_issue": True,
                    "message": (
                        f"Headcount mismatch: extracted teams sum to {total_extracted} "
                        f"but document states {stated_total} total IT headcount"
                    ),
                    "extracted_total": total_extracted,
                    "stated_total": stated_total,
                    "ratio": ratio,
                    "suggestion": "Some teams may be missing from extraction"
                }
            elif ratio > 1.2:
                return {
                    "has_issue": True,
                    "message": (
                        f"Headcount exceeds total: extracted teams sum to {total_extracted} "
                        f"but document states {stated_total}"
                    ),
                    "extracted_total": total_extracted,
                    "stated_total": stated_total,
                    "ratio": ratio,
                    "suggestion": "Check for duplicate team entries or double-counting"
                }

        return {"has_issue": False}

    def _find_stated_headcount(
        self,
        document_text: str,
        facts: List[Dict[str, Any]]
    ) -> Optional[int]:
        """Find stated total IT headcount from document or facts."""
        # Check facts for total headcount
        for fact in facts:
            item = fact.get("item", "").lower()
            if "total" in item and ("headcount" in item or "fte" in item):
                details = fact.get("details", {})
                value = details.get("headcount") or details.get("value")
                if value:
                    match = re.search(r'(\d+)', str(value))
                    if match:
                        return int(match.group(1))

        # Search document for stated totals
        patterns = [
            r'total(?:\s+IT)?\s+headcount[:\s]+(\d+)',
            r'(\d+)\s+(?:total\s+)?IT\s+(?:staff|personnel|employees|FTEs)',
            r'IT\s+organization\s+of\s+(\d+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, document_text, re.IGNORECASE)
            if match:
                return int(match.group(1))

        return None

    def _check_cost_sanity(
        self,
        team_facts: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Check if cost per person makes sense."""
        for fact in team_facts:
            details = fact.get("details", {})
            headcount = details.get("headcount", 0)
            cost = details.get("personnel_cost", 0)

            if isinstance(headcount, str):
                match = re.search(r'(\d+)', str(headcount))
                headcount = int(match.group(1)) if match else 0

            if isinstance(cost, str):
                # Parse cost string ($1.2M, $500K, etc.)
                cost = self._parse_cost_string(cost)

            if headcount and headcount > 0 and cost and cost > 0:
                cost_per_person = cost / headcount

                # Sanity check: $40K - $300K per person is reasonable
                if cost_per_person < 40000:
                    return {
                        "has_issue": True,
                        "message": (
                            f"Unusually low cost per person for '{fact.get('item')}': "
                            f"${cost_per_person:,.0f}/person"
                        ),
                        "suggestion": "Verify cost figure - may be missing zeros or wrong unit"
                    }
                elif cost_per_person > 300000:
                    return {
                        "has_issue": True,
                        "message": (
                            f"Unusually high cost per person for '{fact.get('item')}': "
                            f"${cost_per_person:,.0f}/person"
                        ),
                        "suggestion": "Verify cost figure - may include non-personnel costs"
                    }

        return {"has_issue": False}

    def _parse_cost_string(self, cost_str: str) -> float:
        """Parse cost string like '$1.2M' or '$500K' to numeric value."""
        if not cost_str:
            return 0.0

        cost_str = str(cost_str).upper().replace(",", "").replace("$", "")

        multiplier = 1
        if "M" in cost_str:
            multiplier = 1_000_000
            cost_str = cost_str.replace("M", "")
        elif "K" in cost_str:
            multiplier = 1_000
            cost_str = cost_str.replace("K", "")

        try:
            return float(cost_str) * multiplier
        except ValueError:
            return 0.0

    def _llm_validate_organization(
        self,
        document_text: str,
        facts: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Use LLM for deep validation of organization extraction."""
        facts_summary = self._summarize_facts(facts)

        prompt = f"""
You are validating an IT organization extraction from a due diligence document.

DOCUMENT EXCERPT:
{document_text[:MAX_DOCUMENT_EXCERPT]}

EXTRACTED FACTS SUMMARY:
{facts_summary}

VALIDATION TASKS:
1. Are all IT teams/departments mentioned in the document captured?
2. Do the headcount numbers match what's stated?
3. Is the organizational structure complete (leadership, reporting)?
4. Are there any obvious gaps or inconsistencies?

Respond in JSON:
{{
    "overall_assessment": "complete" | "partial" | "incomplete",
    "confidence": 0.0-1.0,
    "missing_items": [
        {{"item": "...", "category": "...", "evidence": "quote from doc"}}
    ],
    "inconsistencies": [
        {{"description": "...", "affected_facts": ["..."]}}
    ],
    "recommendations": ["..."],
    "notes": "..."
}}
"""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )

            return self._parse_llm_response(response.content[0].text)

        except Exception as e:
            logger.error(f"LLM validation failed: {e}")
            return {"error": str(e)}

    # =========================================================================
    # INFRASTRUCTURE DOMAIN VALIDATOR
    # =========================================================================

    def validate_infrastructure(
        self,
        document_text: str,
        facts: List[Dict[str, Any]],
        gaps: Optional[List[Dict[str, Any]]] = None
    ) -> DomainValidationResult:
        """Validate infrastructure domain extraction."""
        import time
        start_time = time.time()

        result = DomainValidationResult(
            domain="infrastructure",
            is_valid=True,
            completeness_score=1.0,
            quality_score=1.0,
            total_facts=len(facts)
        )

        facts_by_category = self._categorize_facts(facts)
        result.facts_by_category = {
            cat: len(cat_facts) for cat, cat_facts in facts_by_category.items()
        }

        # Check 1: Required categories present
        required_categories = ["hosting", "compute"]
        for cat in required_categories:
            if cat not in facts_by_category or not facts_by_category[cat]:
                result.completeness_score -= 0.15
                result.recommendations.append(f"Missing required category: {cat}")
                result.flags.append(ValidationFlag(
                    flag_id=generate_flag_id(),
                    severity=FlagSeverity.WARNING,
                    category=FlagCategory.COMPLETENESS,
                    message=f"No {cat} information extracted",
                    suggestion=f"Look for {cat} details in document"
                ))

        # Check 2: DR/Backup documented
        backup_facts = facts_by_category.get("backup_dr", [])
        if not backup_facts:
            result.completeness_score -= 0.1
            result.flags.append(ValidationFlag(
                flag_id=generate_flag_id(),
                severity=FlagSeverity.WARNING,
                category=FlagCategory.COMPLETENESS,
                message="No backup/DR information extracted",
                suggestion="Look for backup, disaster recovery, or business continuity details"
            ))

        # Check 3: Server count sanity
        compute_facts = facts_by_category.get("compute", [])
        server_check = self._check_server_counts(compute_facts)
        if server_check["has_issue"]:
            result.quality_score -= 0.1
            result.quality_issues.append(server_check)

        # Check 4: LLM validation
        llm_result = self._llm_validate_infrastructure(document_text, facts)
        self._merge_llm_findings(result, llm_result)

        # Calculate final scores
        result.completeness_score = max(0.0, result.completeness_score)
        result.quality_score = max(0.0, result.quality_score)

        result.requires_rerun = result.completeness_score < COMPLETENESS_THRESHOLD
        if result.requires_rerun:
            result.rerun_guidance = self._generate_rerun_guidance(result)
            result.is_valid = False

        result.validation_time_ms = (time.time() - start_time) * 1000

        return result

    def _check_server_counts(
        self,
        compute_facts: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Check if server counts make sense."""
        total_servers = 0
        for fact in compute_facts:
            details = fact.get("details", {})
            count = details.get("count", 0)
            if isinstance(count, str):
                match = re.search(r'(\d+)', str(count))
                count = int(match.group(1)) if match else 0
            total_servers += int(count) if count else 0

        if total_servers > 10000:
            return {
                "has_issue": True,
                "message": f"Very high server count: {total_servers}",
                "suggestion": "Verify this is accurate - may be VMs not physical"
            }

        return {"has_issue": False}

    def _llm_validate_infrastructure(
        self,
        document_text: str,
        facts: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Use LLM for infrastructure validation."""
        facts_summary = self._summarize_facts(facts)

        prompt = f"""
You are validating an IT infrastructure extraction from a due diligence document.

DOCUMENT EXCERPT:
{document_text[:MAX_DOCUMENT_EXCERPT]}

EXTRACTED FACTS:
{facts_summary}

VALIDATION TASKS:
1. Are all data centers and hosting locations captured?
2. Are server/VM counts accurate?
3. Is storage and backup infrastructure documented?
4. Are there any critical gaps?

Respond in JSON:
{{
    "overall_assessment": "complete" | "partial" | "incomplete",
    "confidence": 0.0-1.0,
    "missing_items": [{{"item": "...", "category": "...", "evidence": "..."}}],
    "inconsistencies": [{{"description": "..."}}],
    "recommendations": ["..."]
}}
"""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )
            return self._parse_llm_response(response.content[0].text)
        except Exception as e:
            logger.error(f"LLM validation failed: {e}")
            return {"error": str(e)}

    # =========================================================================
    # APPLICATIONS DOMAIN VALIDATOR
    # =========================================================================

    def validate_applications(
        self,
        document_text: str,
        facts: List[Dict[str, Any]],
        gaps: Optional[List[Dict[str, Any]]] = None
    ) -> DomainValidationResult:
        """Validate applications domain extraction."""
        import time
        start_time = time.time()

        result = DomainValidationResult(
            domain="applications",
            is_valid=True,
            completeness_score=1.0,
            quality_score=1.0,
            total_facts=len(facts)
        )

        facts_by_category = self._categorize_facts(facts)
        result.facts_by_category = {
            cat: len(cat_facts) for cat, cat_facts in facts_by_category.items()
        }

        # Check 1: ERP captured (most orgs have one)
        erp_facts = facts_by_category.get("erp", [])
        if not erp_facts:
            result.completeness_score -= 0.1
            result.recommendations.append("No ERP system extracted - verify if org has one")

        # Check 2: Major categories covered or gaps noted
        important_categories = ["erp", "crm", "custom"]
        categories_present = sum(
            1 for cat in important_categories
            if facts_by_category.get(cat)
        )
        if categories_present == 0:
            result.completeness_score -= 0.2
            result.flags.append(ValidationFlag(
                flag_id=generate_flag_id(),
                severity=FlagSeverity.WARNING,
                category=FlagCategory.COMPLETENESS,
                message="No major application categories captured",
                suggestion="Look for ERP, CRM, or custom application mentions"
            ))

        # Check 3: LLM validation
        llm_result = self._llm_validate_applications(document_text, facts)
        self._merge_llm_findings(result, llm_result)

        result.completeness_score = max(0.0, result.completeness_score)
        result.quality_score = max(0.0, result.quality_score)

        result.requires_rerun = result.completeness_score < COMPLETENESS_THRESHOLD
        if result.requires_rerun:
            result.rerun_guidance = self._generate_rerun_guidance(result)
            result.is_valid = False

        result.validation_time_ms = (time.time() - start_time) * 1000

        return result

    def _llm_validate_applications(
        self,
        document_text: str,
        facts: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Use LLM for applications validation."""
        facts_summary = self._summarize_facts(facts)

        prompt = f"""
You are validating an applications extraction from a due diligence document.

DOCUMENT EXCERPT:
{document_text[:MAX_DOCUMENT_EXCERPT]}

EXTRACTED FACTS:
{facts_summary}

VALIDATION TASKS:
1. Are major applications (ERP, CRM) captured?
2. Are custom/proprietary applications documented?
3. Are key SaaS applications listed?
4. Are there any obvious gaps?

Respond in JSON:
{{
    "overall_assessment": "complete" | "partial" | "incomplete",
    "confidence": 0.0-1.0,
    "missing_items": [{{"item": "...", "category": "...", "evidence": "..."}}],
    "recommendations": ["..."]
}}
"""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )
            return self._parse_llm_response(response.content[0].text)
        except Exception as e:
            logger.error(f"LLM validation failed: {e}")
            return {"error": str(e)}

    # =========================================================================
    # NETWORK & SECURITY VALIDATORS (Similar pattern)
    # =========================================================================

    def validate_network(
        self,
        document_text: str,
        facts: List[Dict[str, Any]],
        gaps: Optional[List[Dict[str, Any]]] = None
    ) -> DomainValidationResult:
        """Validate network domain extraction."""
        import time
        start_time = time.time()

        result = DomainValidationResult(
            domain="network",
            is_valid=True,
            completeness_score=1.0,
            quality_score=1.0,
            total_facts=len(facts)
        )

        facts_by_category = self._categorize_facts(facts)
        result.facts_by_category = {
            cat: len(cat_facts) for cat, cat_facts in facts_by_category.items()
        }

        # Check WAN connectivity
        wan_facts = facts_by_category.get("wan", [])
        if not wan_facts:
            result.completeness_score -= 0.15
            result.flags.append(ValidationFlag(
                flag_id=generate_flag_id(),
                severity=FlagSeverity.WARNING,
                category=FlagCategory.COMPLETENESS,
                message="No WAN/connectivity information extracted",
                suggestion="Look for MPLS, internet, bandwidth mentions"
            ))

        result.requires_rerun = result.completeness_score < COMPLETENESS_THRESHOLD
        result.validation_time_ms = (time.time() - start_time) * 1000

        return result

    def validate_security(
        self,
        document_text: str,
        facts: List[Dict[str, Any]],
        gaps: Optional[List[Dict[str, Any]]] = None
    ) -> DomainValidationResult:
        """Validate security domain extraction."""
        import time
        start_time = time.time()

        result = DomainValidationResult(
            domain="security",
            is_valid=True,
            completeness_score=1.0,
            quality_score=1.0,
            total_facts=len(facts)
        )

        facts_by_category = self._categorize_facts(facts)
        result.facts_by_category = {
            cat: len(cat_facts) for cat, cat_facts in facts_by_category.items()
        }

        # Check critical security categories
        critical_categories = ["endpoint_security", "perimeter"]
        for cat in critical_categories:
            if cat not in facts_by_category or not facts_by_category[cat]:
                result.completeness_score -= 0.15
                result.flags.append(ValidationFlag(
                    flag_id=generate_flag_id(),
                    severity=FlagSeverity.WARNING,
                    category=FlagCategory.COMPLETENESS,
                    message=f"No {cat.replace('_', ' ')} information extracted",
                    suggestion=f"Look for {cat.replace('_', ' ')} details"
                ))

        result.requires_rerun = result.completeness_score < COMPLETENESS_THRESHOLD
        result.validation_time_ms = (time.time() - start_time) * 1000

        return result

    # =========================================================================
    # GENERIC VALIDATOR
    # =========================================================================

    def _validate_generic(
        self,
        domain: str,
        document_text: str,
        facts: List[Dict[str, Any]],
        gaps: Optional[List[Dict[str, Any]]] = None
    ) -> DomainValidationResult:
        """Generic validation for unknown domains."""
        import time
        start_time = time.time()

        result = DomainValidationResult(
            domain=domain,
            is_valid=True,
            completeness_score=0.8,  # Assume partial without specific checks
            quality_score=0.8,
            total_facts=len(facts)
        )

        if len(facts) == 0:
            result.completeness_score = 0.0
            result.is_valid = False
            result.requires_rerun = True

        result.validation_time_ms = (time.time() - start_time) * 1000

        return result

    # =========================================================================
    # HELPER METHODS
    # =========================================================================

    def _categorize_facts(
        self,
        facts: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Group facts by category."""
        by_category: Dict[str, List[Dict[str, Any]]] = {}
        for fact in facts:
            category = fact.get("category", "unknown")
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(fact)
        return by_category

    def _summarize_facts(self, facts: List[Dict[str, Any]]) -> str:
        """Create summary of facts for LLM prompt."""
        if not facts:
            return "No facts extracted."

        by_category = self._categorize_facts(facts)
        summary_parts = []

        for category, cat_facts in by_category.items():
            items = [f.get("item", "Unknown") for f in cat_facts[:10]]
            summary_parts.append(
                f"**{category}** ({len(cat_facts)} items): {', '.join(items)}"
                + ("..." if len(cat_facts) > 10 else "")
            )

        return "\n".join(summary_parts)

    def _parse_llm_response(self, response_text: str) -> Dict[str, Any]:
        """Parse LLM JSON response."""
        try:
            if "```" in response_text:
                parts = response_text.split("```")
                if len(parts) >= 2:
                    json_part = parts[1]
                    if json_part.startswith("json"):
                        json_part = json_part[4:]
                    response_text = json_part.strip()

            return json.loads(response_text)

        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse LLM response: {e}")
            return {
                "overall_assessment": "unknown",
                "confidence": 0.5,
                "parse_error": str(e)
            }

    def _merge_llm_findings(
        self,
        result: DomainValidationResult,
        llm_result: Dict[str, Any]
    ):
        """Merge LLM findings into validation result."""
        # Missing items
        missing_items = llm_result.get("missing_items", [])
        if missing_items:
            result.missing_items.extend(missing_items)
            # Adjust score based on missing items
            result.completeness_score -= min(0.3, len(missing_items) * 0.05)

        # Inconsistencies
        inconsistencies = llm_result.get("inconsistencies", [])
        if inconsistencies:
            result.inconsistencies.extend(inconsistencies)
            result.quality_score -= min(0.2, len(inconsistencies) * 0.05)

        # Recommendations
        recommendations = llm_result.get("recommendations", [])
        result.recommendations.extend(recommendations)

        # Overall assessment
        assessment = llm_result.get("overall_assessment", "unknown")
        if assessment == "incomplete":
            result.completeness_score -= 0.2
        elif assessment == "partial":
            result.completeness_score -= 0.1

        # LLM confidence
        llm_confidence = llm_result.get("confidence", 0.7)
        if llm_confidence < 0.6:
            result.quality_score -= 0.1

    def _generate_rerun_guidance(
        self,
        result: DomainValidationResult
    ) -> str:
        """Generate guidance for re-extraction."""
        guidance_parts = []

        if result.missing_items:
            items = [m.get("item", "?") for m in result.missing_items[:5]]
            guidance_parts.append(f"Missing: {', '.join(items)}")

        if result.inconsistencies:
            guidance_parts.append(
                f"{len(result.inconsistencies)} inconsistencies found"
            )

        if result.recommendations:
            guidance_parts.append(result.recommendations[0])

        return " | ".join(guidance_parts) if guidance_parts else "Re-extract with more thorough analysis"


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def validate_domain(
    api_key: str,
    domain: str,
    document_text: str,
    facts: List[Dict[str, Any]],
    gaps: Optional[List[Dict[str, Any]]] = None
) -> DomainValidationResult:
    """Convenience function for domain validation."""
    validator = DomainValidator(api_key=api_key)
    return validator.validate(
        domain=domain,
        document_text=document_text,
        facts=facts,
        gaps=gaps
    )
