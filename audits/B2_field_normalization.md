# Audit B2: App Inventory Field Normalization

## Status: PARTIALLY IMPLEMENTED ✓
## Priority: MEDIUM (Tier 2 - Data Integrity)
## Complexity: Medium
## Review Score: 8.2/10 (GPT review, Feb 8 2026)
## Implementation Date: Feb 8, 2026

---

## 1. Problem Statement

**Symptom:** Missing attributes (vendor, version, user_count, criticality) in app inventory even when source documents contain this data.

**User Impact:**
- Incomplete app data in reports
- Empty columns in app tables
- Missing critical decision-making info
- Appears extraction is broken

**Expected Behavior:** All app attributes from source documents should appear in UI and reports, regardless of field name variations in source.

---

## 2. Decision: Normalize at Ingestion (GPT FEEDBACK)

### Rule: Normalize as early as possible (at fact/inventory creation)

**Why NOT display-time only:**
- Mismatches across exports, APIs, scoring, downstream analytics
- Every consumer must re-normalize
- Inconsistent behavior across views

**Implementation:**
1. Normalize fields when writing to FactStore/InventoryStore
2. Store canonical field names only
3. Keep display-time normalization as safety net (not primary)

---

## 3. Canonical ApplicationRecord Schema (GPT FEEDBACK)

### Single Contract (all app data flows through this):

```python
@dataclass
class ApplicationRecord:
    """Canonical application schema - system contract."""

    # Identity
    id: str                      # UUID
    name: str                    # Application name
    deal_id: str
    entity: str                  # 'target' or 'buyer'

    # Categorical
    category: str                # Normalized: erp, crm, hcm, database, saas, security, integration, vertical, other

    # Vendor/Product
    vendor: Optional[str]        # Normalized from vendor/provider/manufacturer
    version: Optional[str]       # Normalized from version/app_version/release

    # Usage
    deployment: Optional[str]    # cloud, on-prem, hybrid, saas
    user_count: Optional[int]    # Numeric, parsed from "1,200" etc.
    criticality: Optional[str]   # High, Medium, Low (normalized)

    # Financial
    annual_cost: Optional[float] # Numeric, parsed from "$250k" etc.
    contract_end: Optional[date] # ISO date

    # Ownership
    owner: Optional[str]
    support_model: Optional[str]

    # Provenance
    source_document_id: str
    source_store: str            # 'fact_store' or 'inventory_store'
    confidence: float            # 0.0 - 1.0

    # Tracking
    created_at: datetime
    updated_at: datetime
```

### Rules:
- **Empty vs Unknown vs Null:**
  - `None` = field not present in source (truly missing)
  - Don't default to "Unknown" too early
  - Let UI render blanks as `—`
- **Types enforced:** `user_count` is int, `annual_cost` is float, `contract_end` is date

---

## 4. FactStore vs InventoryStore Merge (GPT FEEDBACK - CRITICAL)

### The Problem:
> "Mutually exclusive, never merged" — this is the real landmine

Aliasing won't fix blank columns if stores overwrite each other.

### Merge Strategy:

**Primary Key for matching:**
```python
# Best: explicit application_id (UUID)
# Fallback: (entity, normalized_name, vendor)
# Weak fallback: (entity, name)
```

**Merge Precedence:**
| Field | Prefer InventoryStore | Prefer FactStore |
|-------|----------------------|------------------|
| vendor | ✓ (structured table) | |
| version | ✓ (structured table) | |
| user_count | ✓ (structured table) | |
| annual_cost | ✓ (structured table) | |
| criticality | | ✓ (narrative context) |
| deployment | ✓ | |
| description | | ✓ (richer narrative) |

**Merge Function:**

```python
def merge_application_records(
    fact_apps: List[ApplicationRecord],
    inventory_apps: List[ApplicationRecord]
) -> List[ApplicationRecord]:
    """
    Merge applications from both stores with field-level precedence.

    - Match by (entity, normalized_name, vendor) or (entity, name)
    - InventoryStore preferred for structured fields
    - FactStore preferred for narrative/qualitative fields
    - Keep provenance: track where each field came from
    """
    merged = {}

    # Index inventory apps (preferred for structured fields)
    for app in inventory_apps:
        key = _make_match_key(app)
        merged[key] = app

    # Merge fact apps
    for app in fact_apps:
        key = _make_match_key(app)

        if key in merged:
            # Field-level merge
            existing = merged[key]
            merged[key] = _merge_fields(existing, app)
        else:
            merged[key] = app

    return list(merged.values())


def _make_match_key(app: ApplicationRecord) -> tuple:
    """Create matching key for deduplication."""
    name_normalized = app.name.lower().strip()
    vendor_normalized = (app.vendor or '').lower().strip()
    return (app.entity, name_normalized, vendor_normalized)


def _merge_fields(inventory_app, fact_app) -> ApplicationRecord:
    """Merge two records with field-level precedence."""
    return ApplicationRecord(
        id=inventory_app.id,
        name=inventory_app.name,
        deal_id=inventory_app.deal_id,
        entity=inventory_app.entity,

        # Structured fields: prefer inventory
        vendor=inventory_app.vendor or fact_app.vendor,
        version=inventory_app.version or fact_app.version,
        user_count=inventory_app.user_count or fact_app.user_count,
        annual_cost=inventory_app.annual_cost or fact_app.annual_cost,
        deployment=inventory_app.deployment or fact_app.deployment,
        contract_end=inventory_app.contract_end or fact_app.contract_end,

        # Qualitative fields: prefer fact
        criticality=fact_app.criticality or inventory_app.criticality,
        owner=fact_app.owner or inventory_app.owner,
        category=fact_app.category or inventory_app.category,

        # Provenance
        source_document_id=inventory_app.source_document_id,
        source_store='merged',
        confidence=max(inventory_app.confidence, fact_app.confidence),

        created_at=min(inventory_app.created_at, fact_app.created_at),
        updated_at=datetime.utcnow(),
    )
```

---

## 5. Root Causes Identified

### 5.1 Field Name Inconsistency
Different code paths use different names for same concept:
| Concept | Variations Used |
|---------|-----------------|
| Criticality | `criticality`, `business_criticality`, `app_criticality` |
| Deployment | `deployment`, `hosting`, `deployment_model` |
| User count | `user_count`, `users`, `num_users` |
| Vendor | `vendor`, `provider`, `manufacturer`, `publisher` |
| Version | `version`, `app_version`, `release` |
| Cost | `annual_cost`, `cost`, `annual_spend`, `license_cost` |

### 5.2 Category Fragmentation
Only ~9 categories recognized. Industry-specific ones fall through:
| Missing Categories | Should Map To |
|-------------------|---------------|
| `policy_administration` | `vertical` |
| `claims_management` | `vertical` |
| `billing` | `erp` or `vertical` |
| `analytics` | `database` |
| `it_service_management` | `saas` |
| `document_management` | `saas` |

### 5.3 Competing Data Sources
- `FactStore` - facts from discovery agents
- `InventoryStore` - structured app inventory
- These are mutually exclusive, never merged ← **MUST FIX**

### 5.4 No Field Enrichment
- If field not found on first pass, stays blank forever
- No secondary lookup or normalization

---

## 6. Files to Investigate

### Primary Files:
| File | What to Look For |
|------|------------------|
| `services/applications_bridge.py` | Field lookups in `build_applications_inventory()` |
| `tools_v2/presentation.py` | Field lookups in `_build_app_landscape_html()` |
| `web/app.py` | `applications_overview()` route |

### Secondary Files:
| File | What to Look For |
|------|------------------|
| `stores/app_category_mappings.py` | Category definitions |
| `tools_v2/deterministic_parser.py` | Field extraction from tables |
| `stores/inventory_store.py` | InventoryStore structure |
| `stores/fact_store.py` | FactStore details field |

---

## 7. Audit Steps

### Phase 1: Map Current Field Usage
- [ ] 1.1 Grep for all `details.get(` patterns
- [ ] 1.2 List all field names currently used
- [ ] 1.3 Compare to field names in test documents
- [ ] 1.4 Identify mismatches

### Phase 2: Map Current Categories
- [ ] 2.1 Find category list in `app_category_mappings.py`
- [ ] 2.2 List categories in test documents
- [ ] 2.3 Identify missing category mappings
- [ ] 2.4 Design expanded category map

### Phase 3: Design Normalizer
- [ ] 3.1 Create `FIELD_ALIASES` mapping
- [ ] 3.2 Create `CATEGORY_NORMALIZATION` mapping
- [ ] 3.3 Design `normalize_detail()` function with type coercion
- [ ] 3.4 Design `normalize_category()` function

### Phase 4: Implement Merge
- [ ] 4.1 Create `merge_application_records()` function
- [ ] 4.2 Define matching key strategy
- [ ] 4.3 Define field-level precedence rules
- [ ] 4.4 Track provenance per field

### Phase 5: Implement & Test
- [ ] 5.1 Create `services/field_normalizer.py`
- [ ] 5.2 Refactor `applications_bridge.py` to use it + merge
- [ ] 5.3 Update `presentation.py` to use it
- [ ] 5.4 Test with documents using various field names

---

## 8. Solution Design

### New File: `services/field_normalizer.py`

```python
"""
Field normalization for consistent attribute access across varying source formats.
"""
import re
from typing import Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Canonical name → list of aliases
FIELD_ALIASES = {
    'vendor': ['vendor', 'provider', 'manufacturer', 'publisher', 'software_vendor'],
    'version': ['version', 'app_version', 'release', 'release_version'],
    'criticality': ['criticality', 'business_criticality', 'app_criticality', 'importance'],
    'deployment': ['deployment', 'hosting', 'deployment_model', 'hosting_model'],
    'user_count': ['user_count', 'users', 'num_users', 'active_users', 'user_base'],
    'annual_cost': ['annual_cost', 'cost', 'annual_spend', 'license_cost', 'yearly_cost'],
    'contract_end': ['contract_end', 'contract_expiry', 'renewal_date', 'end_date'],
    'owner': ['owner', 'business_owner', 'app_owner', 'product_owner'],
    'support_model': ['support_model', 'support', 'support_type', 'maintenance'],
}

# Raw category → normalized category
CATEGORY_NORMALIZATION = {
    # Vertical/Industry-specific
    'policy_administration': 'vertical',
    'claims_management': 'vertical',
    'underwriting': 'vertical',
    'actuarial': 'vertical',
    'reinsurance': 'vertical',

    # CRM variants
    'crm': 'crm',
    'crm_agency_management': 'crm',
    'customer_management': 'crm',
    'sales': 'crm',

    # ERP variants
    'erp': 'erp',
    'finance': 'erp',
    'accounting': 'erp',
    'billing': 'erp',

    # HCM variants
    'hcm': 'hcm',
    'hr': 'hcm',
    'hr_hcm': 'hcm',
    'payroll': 'hcm',
    'workforce': 'hcm',

    # Database/Analytics variants
    'database': 'database',
    'analytics': 'database',
    'data_analytics': 'database',
    'bi': 'database',
    'reporting': 'database',
    'data_warehouse': 'database',

    # SaaS/Productivity variants
    'saas': 'saas',
    'productivity': 'saas',
    'collaboration': 'saas',
    'email': 'saas',
    'email_communication': 'saas',
    'document_management': 'saas',
    'it_service_management': 'saas',

    # Security variants
    'security': 'security',
    'identity': 'security',
    'iam': 'security',
    'cybersecurity': 'security',

    # Integration variants
    'integration': 'integration',
    'middleware': 'integration',
    'etl': 'integration',
    'api': 'integration',
}

# Criticality normalization
CRITICALITY_NORMALIZATION = {
    'high': 'High', 'critical': 'High', 'tier1': 'High', 'tier 1': 'High',
    'medium': 'Medium', 'moderate': 'Medium', 'tier2': 'Medium', 'tier 2': 'Medium',
    'low': 'Low', 'minor': 'Low', 'tier3': 'Low', 'tier 3': 'Low',
}

DEFAULT_CATEGORY = 'other'

# Track unrecognized for logging
_unrecognized_categories = {}
_unrecognized_fields = {}


def normalize_detail(details: dict, canonical_name: str, coerce_type: str = None) -> Any:
    """
    Look up a field value using canonical name and all its aliases.
    Optionally coerce to specific type.

    Args:
        details: Dictionary of app details
        canonical_name: The standard field name to look up
        coerce_type: Optional type coercion ('int', 'float', 'date')

    Returns:
        The value if found under any alias, else None (NOT 'Unknown')
    """
    if not details or not isinstance(details, dict):
        return None

    aliases = FIELD_ALIASES.get(canonical_name, [canonical_name])
    value = None

    for alias in aliases:
        if alias in details and details[alias]:
            value = details[alias]
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

    # Type coercion (GPT FEEDBACK)
    if coerce_type == 'int':
        return _parse_int(value)
    elif coerce_type == 'float':
        return _parse_float(value)
    elif coerce_type == 'date':
        return _parse_date(value)
    elif canonical_name == 'criticality':
        return _normalize_criticality(value)

    return value


def _parse_int(value) -> Optional[int]:
    """Parse integer from various formats: '1,200', '1200', etc."""
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        # Remove commas, spaces
        clean = re.sub(r'[,\s]', '', value)
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
        # Try common formats
        for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%Y/%m/%d']:
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
    return CRITICALITY_NORMALIZATION.get(clean, value)


def normalize_category(raw_category: str) -> str:
    """
    Normalize a raw category string to standard category.
    Logs unrecognized categories for review.
    """
    if not raw_category:
        return DEFAULT_CATEGORY

    # Clean and lowercase
    clean = raw_category.lower().strip().replace(' ', '_').replace('-', '_')

    # Direct lookup
    if clean in CATEGORY_NORMALIZATION:
        return CATEGORY_NORMALIZATION[clean]

    # Partial match
    for raw, normalized in CATEGORY_NORMALIZATION.items():
        if raw in clean or clean in raw:
            return normalized

    # Log unrecognized (GPT FEEDBACK - mandatory)
    _unrecognized_categories[clean] = _unrecognized_categories.get(clean, 0) + 1
    logger.warning(f"Unrecognized category: '{raw_category}' -> defaulting to 'other'")

    return DEFAULT_CATEGORY


def get_unrecognized_categories() -> dict:
    """Return top unrecognized categories with counts."""
    return dict(sorted(_unrecognized_categories.items(), key=lambda x: -x[1])[:10])


def get_unrecognized_fields() -> dict:
    """Return top unrecognized fields with counts."""
    return dict(sorted(_unrecognized_fields.items(), key=lambda x: -x[1])[:10])
```

---

## 9. Integration Points

### Update `applications_bridge.py`:
```python
from services.field_normalizer import normalize_detail, normalize_category

def build_applications_inventory(fact_store, inventory_store, entity='target'):
    """Build app inventory by merging both stores."""

    # Get apps from FactStore
    fact_apps = []
    for fact in fact_store.get_facts_by_domain('applications'):
        if fact.entity != entity:
            continue
        details = fact.details or {}
        fact_apps.append(ApplicationRecord(
            id=fact.id,
            name=fact.item,
            vendor=normalize_detail(details, 'vendor'),
            version=normalize_detail(details, 'version'),
            criticality=normalize_detail(details, 'criticality'),
            deployment=normalize_detail(details, 'deployment'),
            user_count=normalize_detail(details, 'user_count', coerce_type='int'),
            annual_cost=normalize_detail(details, 'annual_cost', coerce_type='float'),
            category=normalize_category(fact.category),
            source_store='fact_store',
            ...
        ))

    # Get apps from InventoryStore
    inventory_apps = _build_from_inventory_store(inventory_store, entity)

    # Merge with field-level precedence
    return merge_application_records(fact_apps, inventory_apps)
```

### Update `presentation.py`:
```python
# In _build_app_landscape_html()
CATEGORY_ORDER = [
    'erp', 'crm', 'hcm', 'database', 'saas',
    'security', 'integration', 'vertical', 'other'  # Added vertical, other
]
```

---

## 10. Risk Assessment

| Risk | Mitigation |
|------|------------|
| Over-normalizing (wrong mappings) | Careful alias selection, test with real data |
| Performance overhead | Normalize once at ingestion, not display |
| Breaking existing reports | Additive change, doesn't remove data |
| Missing edge cases | Log unrecognized categories (mandatory) |
| Store merge conflicts | Field-level precedence rules, not record-level |

---

## 11. Definition of Done (GPT FEEDBACK)

### Must have:
- [ ] All apps have vendor populated (when in source under any alias)
- [ ] All apps have version populated (when in source)
- [ ] All apps have user_count populated (when in source)
- [ ] No apps in "Unknown" category when category exists in source
- [ ] Category distribution makes sense (not all in "other")
- [ ] Top 10 unrecognized categories logged with counts
- [ ] FactStore + InventoryStore merged correctly

### Tests:
- [ ] Alias resolution test: vendor found under "provider", "manufacturer"
- [ ] Category normalization test: policy_admin → vertical
- [ ] Type coercion test: "1,200" → 1200, "$250k" → 250000
- [ ] Merge test: fact + inventory app → single merged record

---

## 12. Success Criteria

- [ ] All 33 apps have vendor populated (when in source)
- [ ] All apps have version populated (when in source)
- [ ] All apps have user_count as integer (when in source)
- [ ] No apps in "Unknown" category when category exists in source
- [ ] Category distribution: vertical has insurance apps, other < 20%
- [ ] Blank columns show `—` not "Unknown"
- [ ] Unrecognized categories logged for future improvement

---

## 13. Questions Resolved

| Question | Decision |
|----------|----------|
| Log unrecognized fields/categories? | **Yes - mandatory** |
| Normalization at extraction or display? | **Extraction (ingestion time)** |
| Truly missing vs different-name? | Return `None`, not "Unknown" |
| Fuzzy matching for typos? | Not in v1 (keep simple) |
| Category per industry? | Not in v1 (single mapping) |

---

## 14. Dependencies

- A1 (App extraction) - FIXED, apps now extracting

## 15. Blocks

- Accurate app inventory reports
- Category-based visualizations
- Cost rollups by category

---

## 16. GPT Review Notes (Feb 8, 2026)

**Score: 8.2/10**

**Strengths:**
- Correctly identifies field name inconsistency as real issue
- Calls out category fragmentation and competing data sources
- Proposed field_normalizer.py approach is practical

**Improvements made based on feedback:**
1. Added "Decision: Normalize at Ingestion" - rule on when to normalize
2. Added "Canonical ApplicationRecord Schema" - single contract
3. Added "FactStore vs InventoryStore Merge" strategy (critical fix)
4. Added type coercion (int, float, date) to normalize_detail()
5. Don't default to "Unknown" - return None, UI shows `—`
6. Made logging unrecognized categories mandatory
7. Added criticality normalization (High/Med/Low)
8. Added merge_application_records() function with field-level precedence
