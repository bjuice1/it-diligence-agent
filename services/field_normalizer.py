"""
Centralized Field Normalization for Application Inventory Data.

Resolves inconsistency between field names used by different data sources
(FactStore, InventoryStore, extraction prompts). All inventory builders
should use these functions instead of hardcoding field lookups.

B2 FIX: Enhanced with type coercion and logging for unrecognized categories.
"""

from typing import Any, Optional, Dict
from datetime import datetime
import re
import logging

logger = logging.getLogger(__name__)

# Track unrecognized categories for debugging
_unrecognized_categories = {}


# =============================================================================
# FIELD ALIASES: canonical_name -> list of known aliases
# =============================================================================

FIELD_ALIASES: Dict[str, list] = {
    'criticality': ['criticality', 'business_criticality', 'app_criticality', 'importance', 'business_impact', 'priority_level'],
    'deployment': ['deployment', 'hosting', 'deployment_model', 'deploy_type', 'hosting_model', 'infrastructure_type'],
    'user_count': ['user_count', 'users', 'num_users', 'number_of_users', 'user_base', 'active_users', 'licensed_users'],
    'vendor': ['vendor', 'provider', 'manufacturer', 'publisher', 'vendor_name', 'software_vendor'],
    'version': ['version', 'app_version', 'release', 'current_version', 'software_version'],
    'annual_cost': ['annual_cost', 'cost', 'annual_spend', 'license_cost', 'yearly_cost', 'total_cost', 'subscription_cost'],
    'contract_end': ['contract_end', 'contract_end_date', 'contract_expiry', 'renewal_date', 'end_date'],
    'description': ['description', 'purpose', 'function', 'use_case', 'business_purpose'],
    'owner': ['owner', 'business_owner', 'app_owner', 'system_owner', 'responsible_party'],
    'support_model': ['support_model', 'support', 'support_type', 'maintenance', 'support_tier'],
}


# =============================================================================
# CATEGORY NORMALIZATION: raw extraction category -> canonical AppCategory value
# =============================================================================

CATEGORY_NORMALIZATION: Dict[str, str] = {
    # Pass-through for known good categories
    'erp': 'erp',
    'crm': 'crm',
    'custom': 'custom',
    'saas': 'saas',
    'hcm': 'hcm',
    'integration': 'integration',
    'database': 'database',
    'vertical': 'vertical',
    'other': 'other',
    'productivity': 'productivity',
    'finance': 'finance',

    # Industry-specific / vertical
    'policy_administration': 'vertical',
    'claims_management': 'vertical',
    'billing': 'vertical',
    'underwriting': 'vertical',
    'actuarial': 'vertical',
    'reinsurance': 'vertical',
    'loan_origination': 'vertical',
    'trading': 'vertical',
    'portfolio_management': 'vertical',
    'patient_management': 'vertical',
    'ehr': 'vertical',
    'emr': 'vertical',
    'practice_management': 'vertical',

    # CRM variants
    'crm_agency_management': 'crm',
    'agency_management': 'crm',
    'customer_management': 'crm',
    'sales': 'crm',

    # HCM / HR variants
    'hr': 'hcm',
    'hr_hcm': 'hcm',
    'payroll': 'hcm',
    'human_resources': 'hcm',
    'talent_management': 'hcm',
    'benefits': 'hcm',

    # Analytics / Database
    'analytics': 'database',
    'analytics_actuarial': 'database',
    'data_analytics': 'database',
    'reporting': 'database',
    'business_intelligence': 'database',
    'bi': 'database',
    'data_warehouse': 'database',

    # SaaS / Productivity
    'collaboration': 'saas',
    'email_communication': 'saas',
    'email': 'saas',
    'communication': 'saas',
    'document_management': 'saas',
    'content_management': 'saas',
    'project_management': 'saas',

    # IT tools
    'it_service_management': 'saas',
    'itsm': 'saas',
    'monitoring': 'other',
    'devops': 'other',

    # Security / Identity
    'identity_access': 'other',
    'security': 'other',
    'backup_dr': 'other',
    'disaster_recovery': 'other',

    # Finance
    'accounting': 'finance',
    'financial_reporting': 'finance',
    'general_ledger': 'finance',
    'accounts_payable': 'finance',
    'accounts_receivable': 'finance',
    'treasury': 'finance',

    # Integration
    'middleware': 'integration',
    'api': 'integration',
    'etl': 'integration',
    'data_integration': 'integration',
}


def normalize_detail(details: dict, canonical_name: str, coerce_type: str = None) -> Optional[Any]:
    """
    Look up a field by its canonical name, trying all known aliases.
    Optionally coerce to specific type.

    Args:
        details: The fact.details dictionary
        canonical_name: The canonical field name (e.g., 'criticality', 'deployment')
        coerce_type: Optional type coercion ('int', 'float', 'date')

    Returns:
        The first non-empty value found, optionally type-coerced, or None

    Example:
        >>> details = {'provider': 'Microsoft', 'num_users': '1,200'}
        >>> normalize_detail(details, 'vendor')
        'Microsoft'
        >>> normalize_detail(details, 'user_count', coerce_type='int')
        1200
    """
    if not details:
        return None

    aliases = FIELD_ALIASES.get(canonical_name, [canonical_name])
    value = None

    for alias in aliases:
        v = details.get(alias)
        if v is not None and str(v).strip():
            value = v
            break
        # Also try case-insensitive
        for key in details:
            if key.lower() == alias.lower() and details[key]:
                value = details[key]
                break
        if value:
            break

    if value is None:
        return None

    # B2 FIX: Type coercion
    if coerce_type == 'int':
        return _parse_int(value)
    elif coerce_type == 'float':
        return _parse_float(value)
    elif coerce_type == 'date':
        return _parse_date(value)
    elif canonical_name == 'criticality':
        return _normalize_criticality(value)

    return value


# =============================================================================
# TYPE COERCION HELPERS (B2 FIX)
# =============================================================================

def _parse_int(value) -> Optional[int]:
    """Parse integer from various formats: '1,200', '1200', '~1000', etc."""
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        clean = re.sub(r'[,\s~+]', '', value)
        try:
            return int(float(clean))
        except ValueError:
            return None
    return None


def _parse_float(value) -> Optional[float]:
    """Parse float from various formats: '$250k', '250,000', '$1.5M', etc."""
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        clean = value.upper().replace('$', '').replace(',', '').strip()
        multiplier = 1
        if clean.endswith('K'):
            multiplier = 1000
            clean = clean[:-1]
        elif clean.endswith('M'):
            multiplier = 1000000
            clean = clean[:-1]
        try:
            return float(clean) * multiplier
        except ValueError:
            return None
    return None


def _parse_date(value) -> Optional[str]:
    """Parse date to ISO format."""
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, str):
        for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%Y/%m/%d', '%B %d, %Y', '%b %d, %Y']:
            try:
                return datetime.strptime(value.strip(), fmt).date().isoformat()
            except ValueError:
                continue
    return None


def _normalize_criticality(value) -> Optional[str]:
    """Normalize criticality to High/Medium/Low."""
    if not value:
        return None
    clean = str(value).lower().strip()
    mapping = {
        'high': 'High', 'critical': 'High', 'tier1': 'High', 'tier 1': 'High', '1': 'High',
        'medium': 'Medium', 'moderate': 'Medium', 'tier2': 'Medium', 'tier 2': 'Medium', '2': 'Medium',
        'low': 'Low', 'minor': 'Low', 'tier3': 'Low', 'tier 3': 'Low', '3': 'Low',
    }
    return mapping.get(clean, value.title())


def normalize_category(raw_category: str) -> str:
    """
    Normalize a category string to a canonical value.
    Logs unrecognized categories for debugging.

    Args:
        raw_category: Raw category from extraction (e.g., 'policy_administration')

    Returns:
        Canonical category string (e.g., 'vertical')
    """
    if not raw_category:
        return 'other'

    key = raw_category.lower().strip().replace(' ', '_').replace('/', '_').replace('-', '_')

    # Direct lookup
    if key in CATEGORY_NORMALIZATION:
        return CATEGORY_NORMALIZATION[key]

    # Partial match for compound names
    for raw, normalized in CATEGORY_NORMALIZATION.items():
        if raw in key or key in raw:
            return normalized

    # B2 FIX: Log unrecognized categories
    _unrecognized_categories[key] = _unrecognized_categories.get(key, 0) + 1
    if _unrecognized_categories[key] == 1:  # Only log first occurrence
        logger.warning(f"B2: Unrecognized category: '{raw_category}' -> defaulting to 'other'")

    return 'other'


def get_unrecognized_categories() -> dict:
    """Return top unrecognized categories with counts for debugging."""
    return dict(sorted(_unrecognized_categories.items(), key=lambda x: -x[1])[:10])


def normalize_all_details(details: dict) -> dict:
    """
    Return a new dict with all fields resolved to canonical names.

    Useful for getting a clean view of what's available in a fact's details.

    Args:
        details: Raw details dict from a fact

    Returns:
        Dict with canonical field names as keys
    """
    if not details:
        return {}

    normalized = {}
    for canonical_name in FIELD_ALIASES:
        value = normalize_detail(details, canonical_name)
        if value is not None:
            normalized[canonical_name] = value

    # Pass through any fields not in aliases (don't lose data)
    known_aliases = set()
    for aliases in FIELD_ALIASES.values():
        known_aliases.update(aliases)

    for key, value in details.items():
        if key not in known_aliases and key not in normalized:
            normalized[key] = value

    return normalized
