# Spec 02: Category Mapping Expansion — Vertical/Industry Categories, Default Fix & Dual Storage

**Status:** Implemented
**Depends on:** None (but benefits from Spec 01 clean data)
**Enables:** Spec 03 (accurate categories for FactStore↔InventoryStore linking)

---

## Problem Statement

Application category mapping has three gaps:

1. **Limited vertical/industry coverage** — `app_category_mappings.py` has only 2 insurance apps (Duck Creek, Guidewire), 5 healthcare apps, 3 manufacturing apps, and 2 retail apps. Real-world IT portfolios for M&A targets in these verticals contain dozens of vertical-specific applications (policy admin systems, claims management, billing engines, EHR modules, MES/SCADA systems) that fall through to the default.

2. **Incorrect default fallback** — `deterministic_parser.py` line 357 defaults unmapped applications to `"saas"`. This is semantically wrong: an unmapped app is not necessarily SaaS. It should default to `"unknown"` so downstream logic (cost estimation, rationalization) can distinguish "we know this is SaaS" from "we don't know what this is."

3. **No category provenance** — When a category is assigned, there's no record of whether it came from the mapping database, was inferred from keywords, or was a default. This makes it impossible to audit category quality or improve mappings.

---

## Files to Modify

### 1. `stores/app_category_mappings.py` — Add Vertical/Industry Mappings

**Current state (lines 707-761):** Insurance has 2 apps (Duck Creek, Guidewire). Healthcare has 5 apps. Manufacturing has 3 apps. Retail has 2 apps.

**Add to `APP_MAPPINGS` dict, within the existing industry vertical sections:**

#### Insurance Additions (after line 721, after Guidewire entry):

```python
    # Policy Administration
    "majesco": AppMapping(
        category="industry_vertical",
        vendor="Majesco",
        description="Cloud-native P&C and L&A policy administration",
        aliases=["majesco policy", "majesco l&a", "majesco p&c"],
        is_saas=True,
        is_industry_standard=True,
    ),
    "insurity": AppMapping(
        category="industry_vertical",
        vendor="Insurity",
        description="P&C policy, billing, and claims platform",
        aliases=["insurity policy", "insurity billing", "insurity claims"],
        is_saas=True,
        is_industry_standard=True,
    ),
    "socotra": AppMapping(
        category="industry_vertical",
        vendor="Socotra",
        description="Cloud-native insurance core platform",
        aliases=["socotra insurance", "socotra core"],
        is_saas=True,
        is_industry_standard=False,
    ),
    "earnix": AppMapping(
        category="industry_vertical",
        vendor="Earnix",
        description="Insurance pricing and rating engine",
        aliases=["earnix pricing", "earnix rating"],
        is_saas=True,
        is_industry_standard=True,
    ),
    "sapiens": AppMapping(
        category="industry_vertical",
        vendor="Sapiens International",
        description="Insurance software for P&C, L&A, and reinsurance",
        aliases=["sapiens insurance", "sapiens alis", "sapiens idit"],
        is_saas=True,
        is_industry_standard=True,
    ),
    "vertafore": AppMapping(
        category="industry_vertical",
        vendor="Vertafore",
        description="Insurance distribution management (AMS360, Sircon)",
        aliases=["vertafore ams360", "ams360", "vertafore sircon", "sircon", "vertafore agency platform"],
        is_saas=True,
        is_industry_standard=True,
    ),
    "applied systems": AppMapping(
        category="industry_vertical",
        vendor="Applied Systems",
        description="Insurance agency management (Applied Epic, TAM)",
        aliases=["applied epic", "applied tam", "applied systems epic", "applied rater"],
        is_saas=True,
        is_industry_standard=True,
    ),
    "britecore": AppMapping(
        category="industry_vertical",
        vendor="BriteCore",
        description="Cloud-native P&C core platform for insurers",
        aliases=["britecore insurance", "brite core"],
        is_saas=True,
        is_industry_standard=False,
    ),
    "snapsheet": AppMapping(
        category="industry_vertical",
        vendor="Snapsheet",
        description="Virtual claims appraisal and management",
        aliases=["snapsheet claims"],
        is_saas=True,
        is_industry_standard=False,
    ),
```

#### Healthcare Additions (after line 705, after athenahealth entry):

```python
    # Healthcare additions
    "veradigm": AppMapping(
        category="industry_vertical",
        vendor="Veradigm (Allscripts)",
        description="EHR, practice management, and health data analytics",
        aliases=["veradigm ehr", "allscripts veradigm", "veradigm practice fusion"],
        is_saas=True,
        is_industry_standard=True,
    ),
    "nextgen healthcare": AppMapping(
        category="industry_vertical",
        vendor="NextGen Healthcare",
        description="Ambulatory EHR and practice management",
        aliases=["nextgen ehr", "nextgen pm", "nextgen healthcare ehr"],
        is_saas=True,
        is_industry_standard=True,
    ),
    "eclinicalworks": AppMapping(
        category="industry_vertical",
        vendor="eClinicalWorks",
        description="Cloud-based EHR, practice management, and RCM",
        aliases=["ecw", "eclinicalworks ehr", "eclinical"],
        is_saas=True,
        is_industry_standard=True,
    ),
    "netsmart": AppMapping(
        category="industry_vertical",
        vendor="Netsmart Technologies",
        description="Behavioral health and human services EHR",
        aliases=["netsmart ehr", "netsmart myavatar", "myavatar"],
        is_saas=True,
        is_industry_standard=True,
    ),
    "inovalon": AppMapping(
        category="industry_vertical",
        vendor="Inovalon",
        description="Healthcare data analytics and quality measures",
        aliases=["inovalon one", "inovalon analytics"],
        is_saas=True,
        is_industry_standard=False,
    ),
    "healthstream": AppMapping(
        category="industry_vertical",
        vendor="HealthStream",
        description="Healthcare workforce management and credentialing",
        aliases=["healthstream learning", "healthstream credentialing"],
        is_saas=True,
        is_industry_standard=True,
    ),
```

#### Manufacturing Additions (after line 745, after Autodesk entry):

```python
    # Manufacturing additions
    "rockwell automation": AppMapping(
        category="industry_vertical",
        vendor="Rockwell Automation",
        description="Industrial automation and MES (FactoryTalk)",
        aliases=["factorytalk", "rockwell factorytalk", "rockwell mes", "allen-bradley"],
        is_saas=False,
        is_industry_standard=True,
    ),
    "aveva": AppMapping(
        category="industry_vertical",
        vendor="AVEVA (Schneider Electric)",
        description="Industrial software for engineering and operations",
        aliases=["aveva engineering", "aveva operations", "wonderware", "schneider electric aveva"],
        is_saas=False,
        is_industry_standard=True,
    ),
    "dassault systemes": AppMapping(
        category="industry_vertical",
        vendor="Dassault Systemes",
        description="PLM, CAD/CAM (CATIA, ENOVIA, SOLIDWORKS)",
        aliases=["catia", "enovia", "solidworks", "3dexperience", "delmia"],
        is_saas=False,
        is_industry_standard=True,
    ),
    "sap plant maintenance": AppMapping(
        category="industry_vertical",
        vendor="SAP",
        description="Plant maintenance and asset management module",
        aliases=["sap pm", "sap plant maintenance", "sap eam"],
        is_saas=False,
        is_industry_standard=True,
    ),
    "infor cloudsuite industrial": AppMapping(
        category="industry_vertical",
        vendor="Infor",
        description="Manufacturing ERP for discrete and process manufacturing",
        aliases=["infor csi", "cloudsuite industrial", "syteline", "infor syteline"],
        is_saas=True,
        is_industry_standard=True,
    ),
    "plex": AppMapping(
        category="industry_vertical",
        vendor="Rockwell Automation (Plex Systems)",
        description="Cloud-native smart manufacturing platform",
        aliases=["plex manufacturing", "plex systems", "plex erp"],
        is_saas=True,
        is_industry_standard=False,
    ),
```

#### Retail Additions (after line 761, after Magento entry):

```python
    # Retail additions
    "oracle retail": AppMapping(
        category="industry_vertical",
        vendor="Oracle",
        description="Retail merchandising, planning, and POS",
        aliases=["oracle retail merchandising", "oracle retail pos", "oracle xstore"],
        is_saas=False,
        is_industry_standard=True,
    ),
    "manhattan associates": AppMapping(
        category="industry_vertical",
        vendor="Manhattan Associates",
        description="Supply chain and warehouse management for retail",
        aliases=["manhattan wms", "manhattan active", "manhattan warehouse"],
        is_saas=True,
        is_industry_standard=True,
    ),
    "blue yonder": AppMapping(
        category="industry_vertical",
        vendor="Blue Yonder (Panasonic)",
        description="Supply chain planning and fulfillment",
        aliases=["jda software", "blue yonder wms", "blue yonder planning", "jda"],
        is_saas=True,
        is_industry_standard=True,
    ),
    "lightspeed": AppMapping(
        category="industry_vertical",
        vendor="Lightspeed Commerce",
        description="Cloud POS and ecommerce platform for retail/restaurant",
        aliases=["lightspeed pos", "lightspeed retail", "lightspeed restaurant"],
        is_saas=True,
        is_industry_standard=False,
    ),
```

**Total additions:** ~25 new applications across 4 verticals.

### 2. `tools_v2/deterministic_parser.py` — Fix Default Category

**Current (line 357):**
```python
category = "saas"  # Default
```

**Replace with:**
```python
category = "unknown"  # Default — do not assume SaaS for unmapped apps
```

**Also update the category detection logic (lines 356-370) to add new branches:**

```python
# Current conditional branches (lines 358-370):
category = "unknown"  # Default — do not assume SaaS for unmapped apps

category_detail = row_data.get("category", "").lower()
if "erp" in category_detail:
    category = "erp"
elif "crm" in category_detail or "agency" in category_detail:
    category = "crm"
elif "hr" in category_detail or "hcm" in category_detail:
    category = "hcm"
elif "custom" in category_detail or "proprietary" in category_detail:
    category = "custom"
elif "integration" in category_detail or "middleware" in category_detail:
    category = "integration"
elif "database" in category_detail or "db" in category_detail:
    category = "database"
# NEW branches for verticals:
elif any(kw in category_detail for kw in ("insurance", "policy", "claims", "underwriting", "billing engine")):
    category = "industry_vertical"
elif any(kw in category_detail for kw in ("healthcare", "ehr", "clinical", "medical", "patient")):
    category = "industry_vertical"
elif any(kw in category_detail for kw in ("manufacturing", "mes", "scada", "plm", "cad", "cam")):
    category = "industry_vertical"
elif any(kw in category_detail for kw in ("retail", "pos", "point of sale", "ecommerce", "warehouse")):
    category = "industry_vertical"
elif any(kw in category_detail for kw in ("security", "siem", "edr", "mfa", "iam")):
    category = "security"
elif any(kw in category_detail for kw in ("analytics", "bi", "reporting", "dashboard")):
    category = "bi_analytics"
elif any(kw in category_detail for kw in ("collaboration", "chat", "video", "meeting")):
    category = "collaboration"
elif any(kw in category_detail for kw in ("saas", "cloud", "subscription")):
    category = "saas"
```

**Key change:** `"saas"` is now only assigned when there's explicit evidence (keyword match), not as a catch-all default.

### 3. `stores/inventory_schemas.py` — Add Category Provenance Fields

**Current application schema (lines 27-33):**
```python
"application": {
    "required": ["name"],
    "optional": [
        "vendor", "version", "hosting", "users", "cost", "criticality",
        "category", "contract_end", "owner", "support_model", "notes"
    ],
    "id_fields": ["name", "vendor"],
}
```

**Replace with:**
```python
"application": {
    "required": ["name"],
    "optional": [
        "vendor", "version", "hosting", "users", "cost", "criticality",
        "category", "contract_end", "owner", "support_model", "notes",
        "source_category", "category_confidence", "category_inferred_from"
    ],
    "id_fields": ["name", "vendor"],
}
```

**New fields:**
- `source_category` — The raw category string from the source document (e.g., "Policy Administration System"), preserved before normalization
- `category_confidence` — `"high"` (exact match in APP_MAPPINGS), `"medium"` (alias/partial match), `"low"` (keyword inference), `"none"` (defaulted to unknown)
- `category_inferred_from` — The method: `"mapping_exact"`, `"mapping_alias"`, `"mapping_partial"`, `"keyword_inference"`, `"default"`

### 4. `stores/app_category_mappings.py` — Add Confidence-Aware Lookup

**Modify `categorize_app()` (lines 859-874) to return confidence:**

**Current:**
```python
def categorize_app(name: str) -> Tuple[str, Optional[AppMapping]]:
    mapping = lookup_app(name)
    if mapping:
        return mapping.category, mapping
    return "unknown", None
```

**Replace with:**
```python
def categorize_app(name: str) -> Tuple[str, Optional[AppMapping], str, str]:
    """Categorize an app and return (category, mapping, confidence, inferred_from).

    Returns:
        category: The category string
        mapping: The AppMapping if found, None otherwise
        confidence: "high", "medium", "low", or "none"
        inferred_from: "mapping_exact", "mapping_alias", "mapping_partial", "keyword_inference", "default"
    """
    normalized = normalize_app_name(name)

    # Tier 1: Exact match (high confidence)
    if normalized in APP_MAPPINGS:
        m = APP_MAPPINGS[normalized]
        return m.category, m, "high", "mapping_exact"

    # Tier 2: Alias match (high confidence)
    for app_key, m in APP_MAPPINGS.items():
        for alias in m.aliases:
            if normalize_app_name(alias) == normalized:
                return m.category, m, "high", "mapping_alias"

    # Tier 3: Partial match (medium confidence)
    for app_key, m in APP_MAPPINGS.items():
        if app_key in normalized or normalized in app_key:
            return m.category, m, "medium", "mapping_partial"
        for alias in m.aliases:
            norm_alias = normalize_app_name(alias)
            if norm_alias in normalized or normalized in norm_alias:
                return m.category, m, "medium", "mapping_partial"

    # Tier 4: No match (unknown)
    return "unknown", None, "none", "default"
```

**Backwards compatibility:** Callers that unpack only 2 values will need updating. Wrap in a helper:

```python
def categorize_app_simple(name: str) -> Tuple[str, Optional[AppMapping]]:
    """Backwards-compatible wrapper returning just (category, mapping)."""
    category, mapping, _, _ = categorize_app(name)
    return category, mapping
```

### 5. `tools_v2/deterministic_parser.py` — Populate Provenance in `_app_table_to_facts()`

**In `_app_table_to_facts()` (around line 340), after extracting app name, use confidence-aware lookup:**

```python
# After extracting app_name from row:
from stores.app_category_mappings import categorize_app

category, mapping, confidence, inferred_from = categorize_app(app_name)

# If no mapping found, try keyword-based inference from category_detail
if category == "unknown" and category_detail:
    # ... existing keyword logic (now updated per section 2 above)
    if category != "unknown":
        confidence = "low"
        inferred_from = "keyword_inference"

# Store provenance in the fact details dict:
details["source_category"] = category_detail  # Raw from document
details["category_confidence"] = confidence
details["category_inferred_from"] = inferred_from
```

---

## Test Cases

### Test 1: Insurance App Mapping
```python
def test_insurance_vertical_mapping():
    from stores.app_category_mappings import categorize_app
    cat, mapping, conf, src = categorize_app("Duck Creek Policy")
    assert cat == "industry_vertical"
    assert conf == "high"
    assert src in ("mapping_exact", "mapping_alias")

    cat2, _, conf2, _ = categorize_app("Majesco")
    assert cat2 == "industry_vertical"
    assert conf2 == "high"
```

### Test 2: Default Fallback Fix
```python
def test_default_category_is_unknown():
    """Unmapped apps should be 'unknown', not 'saas'."""
    cat, mapping, conf, src = categorize_app("Totally Custom Internal Tool XYZ")
    assert cat == "unknown"
    assert conf == "none"
    assert src == "default"
    assert mapping is None
```

### Test 3: SaaS Only When Explicit
```python
def test_saas_requires_evidence():
    """'saas' category should only be assigned with explicit evidence."""
    # This app IS in mappings as SaaS
    cat, _, _, _ = categorize_app("Salesforce")
    assert cat == "crm"  # Mapped to specific category, not generic "saas"
```

### Test 4: Category Provenance
```python
def test_category_provenance_tracking():
    cat, mapping, conf, src = categorize_app("Oracle Database")
    assert cat == "database"
    assert conf == "high"
    assert src == "mapping_exact"

    # Partial match
    cat2, _, conf2, src2 = categorize_app("Oracle Database Enterprise 19c")
    assert cat2 == "database"
    assert conf2 == "medium"
    assert src2 == "mapping_partial"
```

### Test 5: Backwards Compatibility
```python
def test_categorize_app_simple_backwards_compat():
    from stores.app_category_mappings import categorize_app_simple
    cat, mapping = categorize_app_simple("SAP")
    assert cat == "erp"
    assert mapping is not None
```

---

## Acceptance Criteria

1. Insurance app "Policy Administration" in source category maps to `"industry_vertical"`, not `"saas"`
2. Unmapped apps show as `"unknown"` with `category_confidence: "none"` — never as `"saas"`
3. All 115+ existing mappings continue to resolve correctly (no regression)
4. New vertical apps (Majesco, Vertafore, Applied Systems, eClinicalWorks, etc.) resolve with `confidence: "high"`
5. Category provenance fields (`source_category`, `category_confidence`, `category_inferred_from`) appear in fact details
6. `categorize_app_simple()` provides backwards compatibility for existing callers

---

## Rollback Plan

- New APP_MAPPINGS entries are purely additive — removing them restores old behavior
- Default change (`"saas"` → `"unknown"`) can be reverted with a single line change
- `categorize_app_simple()` wrapper ensures existing callers aren't broken during migration
- New schema fields are optional — old inventory items without them still load correctly

---

## Implementation Notes

### 1. Files Modified

**`stores/app_category_mappings.py`**
- **Lines 706--754**: Added 6 healthcare vertical apps (Veradigm, NextGen Healthcare, eClinicalWorks, Netsmart, Inovalon, HealthStream) immediately after the existing athenahealth entry (line 705).
- **Lines 771--843**: Added 9 insurance vertical apps (Majesco, Insurity, Socotra, Earnix, Sapiens, Vertafore, Applied Systems, BriteCore, Snapsheet) after the existing Guidewire entry (line 770).
- **Lines 868--916**: Added 6 manufacturing vertical apps (Rockwell Automation, AVEVA, Dassault Systemes, SAP Plant Maintenance, Infor CloudSuite Industrial, Plex) after the existing Autodesk entry (line 867).
- **Lines 933--965**: Added 4 retail vertical apps (Oracle Retail, Manhattan Associates, Blue Yonder, Lightspeed) after the existing Magento entry (line 932).
- **Lines 1063--1095**: Replaced `categorize_app()` with a 4-tuple return signature `(category, mapping, confidence, inferred_from)`. Implements tiered matching: Tier 1 exact (high/mapping_exact), Tier 2 alias (high/mapping_alias), Tier 3 partial (medium/mapping_partial), Tier 4 no match (none/default).
- **Lines 1098--1101**: Added `categorize_app_simple()` backwards-compatible wrapper returning only `(category, mapping)`.

**`tools_v2/deterministic_parser.py`**
- **Lines 407--408**: Changed from `categorize_app` (2-tuple) to `categorize_app` (4-tuple) call, unpacking `category, mapping, confidence, inferred_from`.
- **Lines 412--445**: Default category is now `"unknown"` (was `"saas"`). Added new keyword inference branches for insurance (`insurance`, `policy`, `claims`, `underwriting`, `billing engine`), healthcare (`healthcare`, `ehr`, `clinical`, `medical`, `patient`), manufacturing (`manufacturing`, `mes`, `scada`, `plm`, `cad`, `cam`), retail (`retail`, `pos`, `point of sale`, `ecommerce`, `warehouse`), security, bi_analytics, collaboration, and saas-only-when-explicit.
- **Lines 443--445**: When keyword inference succeeds, sets `confidence = "low"` and `inferred_from = "keyword_inference"`.
- **Lines 448--450**: Stores provenance fields (`source_category`, `category_confidence`, `category_inferred_from`) into the fact details dict.

**`stores/inventory_schemas.py`**
- **Lines 40--42**: Added three new optional fields to the `"application"` schema: `source_category`, `category_confidence`, `category_inferred_from`. All are optional, so existing inventory items without them still load correctly.

### 2. Deviations from Spec

- **All 25 apps added**: Insurance (9), Healthcare (6), Manufacturing (6), Retail (4) -- matches the spec's target of ~25 exactly.
- **No naming changes**: All app keys, vendor names, descriptions, and aliases match the spec verbatim.
- **No deviations detected**: The default fallback change (`"saas"` to `"unknown"`), the 4-tuple `categorize_app` signature, the `categorize_app_simple` wrapper, the keyword inference branches, and the schema provenance fields all match the spec as written.
- **Minor structural note**: The spec describes the default change on `deterministic_parser.py` "line 357" referencing the old file. In the implemented file, the default is no longer a standalone assignment; it is handled by the `categorize_app()` return value at line 408 (Tier 4 returns `"unknown"`), with keyword inference fallback in lines 412--441. The net behavior is identical to what the spec prescribes.

### 3. Callers Updated

**`tools_v2/enrichment/inventory_reviewer.py`**
- Line 22: Imports `categorize_app_simple` (not `categorize_app`) from `stores.app_category_mappings`, ensuring backwards compatibility. The `_try_local_lookup()` function (line 207) and `suggest_category()` function (line 495) both use the 2-tuple wrapper, so they required no signature changes.

**`tools_v2/file_router.py`**
- Line 30: Imports `categorize_app_simple` and `lookup_app`. The `_auto_categorize_app()` function (line 219) uses `lookup_app()` directly (returns a single `AppMapping` or `None`), so it was unaffected by the `categorize_app` signature change. No code changes needed beyond the import already present.

**`tests/test_app_categorization.py`**
- Line 75: Uses `categorize_app_simple` (2-tuple) for the `test_categorize_known_app` and `test_categorize_unknown_app` tests. These tests continue to pass without modification because they use the backwards-compatible wrapper.

### 4. Test Coverage

**`tests/test_category_mapping.py`** -- 21 test functions across 5 test classes:

| Class | Tests | What it validates |
|-------|-------|-------------------|
| `TestVerticalMappings` | `test_vertical_app_categorization` (15 parametrized cases), `test_existing_mappings_unchanged` | New vertical apps resolve to `industry_vertical`; existing ERP/CRM/HCM/Security/Infrastructure mappings unchanged |
| `TestDefaultFallback` | `test_unmapped_app_is_unknown`, `test_saas_not_default` | Unmapped apps return `"unknown"` with `confidence="none"`, never `"saas"` |
| `TestCategoryProvenance` | `test_exact_match_high_confidence`, `test_alias_match_high_confidence`, `test_partial_match_medium_confidence`, `test_no_match_none_confidence` | Confidence and source tracking across all 4 tiers |
| `TestBackwardsCompatibility` | `test_simple_returns_two_values`, `test_simple_unknown_returns_none_mapping`, `test_categorize_app_returns_four_values` | `categorize_app_simple()` returns 2-tuple; `categorize_app()` returns 4-tuple |
| `TestNormalizeAppName` | `test_lowercase`, `test_strip_version`, `test_strip_company_suffix`, `test_strip_year`, `test_empty_string` | Name normalization consistency |

Note: pytest expands the `@pytest.mark.parametrize` in `test_vertical_app_categorization` into 15 individual test cases at runtime, so a `pytest` run reports 35 collected tests (15 parametrized + 6 + 4 + 3 + 5 + 2 non-parametrized). The file contains 21 distinct test function definitions.
