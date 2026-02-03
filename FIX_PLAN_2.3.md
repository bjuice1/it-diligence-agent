# IT Due Diligence Agent - Version 2.3 Fix Plan

**Created:** 2026-02-03
**Updated:** 2026-02-03
**Status:** ✅ COMPLETE (6/6 Phases Complete)
**Priority Legend:** 🔴 Critical | 🟠 High | 🟡 Medium | 🟢 Low

---

## Overview

Version 2.3 addresses six key reliability and data integrity issues identified across the codebase. The fixes are organized into phases with dependencies.

### Phase Summary

| Phase | Name | Status | Tests |
|-------|------|--------|-------|
| Phase 1/6 | Deal Isolation | ✅ COMPLETE | 25/25 |
| Phase 2+4 | Presentation Reliability | ✅ COMPLETE | 13/13 (+3 skipped) |
| Phase 3 | App Ingestion & Category Mapping | ✅ COMPLETE | 37/37 |
| Phase 5 | Document Parsing & Preprocessing | ✅ COMPLETE | 43/43 |
| Phase 6 | Cost Estimation Determinism | ✅ COMPLETE | 30/30 |

**Total Tests Passing:** 148 new tests

---

## PHASE 1/6: DEAL ISOLATION (Critical)

**Status:** ✅ COMPLETE
**Tests:** 25/25 passing

### Problem
Multi-deal contamination risk - facts, inventory items, and documents could bleed across deals without proper scoping.

### Solution
Add `deal_id` to all data stores with content-based ID generation that includes deal context.

### Files Modified

| File | Changes |
|------|---------|
| `stores/fact_store.py` | Added `deal_id` to Fact, Gap, OpenQuestion; updated FactStore with deal scoping |
| `stores/inventory_item.py` | Added `deal_id` field to InventoryItem dataclass |
| `stores/inventory_store.py` | Added deal_id support, classmethod `load()` |
| `stores/document_store.py` | Added deal_id to Document dataclass |
| `stores/id_generator.py` | Updated ID generation to include deal_id |

### New Files

| File | Purpose |
|------|---------|
| `scripts/migrate_deal_isolation.py` | Migration script for existing data |
| `tests/test_deal_isolation.py` | 25 comprehensive tests |

### Key Changes

```python
# FactStore now requires deal_id
store = FactStore(deal_id="deal_123")

# Or provide per-fact
store.add_fact(
    category="applications",
    content="SAP ERP v7.5",
    deal_id="deal_123"  # Required
)

# ID generation includes deal_id for cross-deal uniqueness
# Same content in different deals = different IDs
```

---

## PHASE 2+4: PRESENTATION RELIABILITY

**Status:** ✅ COMPLETE
**Tests:** 13 passed, 3 skipped (Flask integration)

### Problem
1. Dashboard 500 errors when `risk_summary` missing
2. Mermaid org charts failing on special characters in names

### Solution
1. Add defensive template coding with Jinja `|default` filters
2. Improve `_sanitize_id()` to handle all special characters

### Files Modified

| File | Changes |
|------|---------|
| `web/app.py` | Added `risk_summary` to dashboard summary dict (lines 1150-1159) |
| `web/templates/dashboard.html` | Added defensive `|default({})` patterns |
| `streamlit_app/views/organization/org_chart.py` | Improved `_sanitize_id()` function |
| `requirements.txt` | Added `streamlit-mermaid>=0.2.0` |

### New Files

| File | Purpose |
|------|---------|
| `tests/test_presentation_smoke.py` | 16 smoke tests for presentation layer |

### Key Changes

```python
# _sanitize_id now handles:
# - Parentheses: "John (CTO)" → "John_CTO"
# - Apostrophes: "Jane's Team" → "Janes_Team"
# - Numbers at start: "123_team" → "n123_team"
# - Empty/None values: "" → "unknown"
# - All special chars removed via regex

# Dashboard summary always includes risk_summary
summary = {
    'risk_summary': raw_summary.get('risk_summary', {
        'critical': 0, 'high': 0, 'medium': 0, 'low': 0, 'total': 0
    }),
}
```

---

## PHASE 3: APP INGESTION & CATEGORY MAPPING

**Status:** ✅ COMPLETE
**Tests:** 37/37 passing

### Problem
Application inventory ingestion doesn't map standard apps (Salesforce, SAP) to proper IT DD categories.

### Solution
1. Created comprehensive app category mappings (106+ apps)
2. Auto-categorization during file ingestion
3. Category validation and normalization in enrichment
4. Local lookup before LLM calls (cost savings)

### New Files

| File | Purpose |
|------|---------|
| `stores/app_category_mappings.py` | 106+ standard app mappings with categories, vendors, aliases |
| `tests/test_app_categorization.py` | 37 comprehensive tests |

### Files Modified

| File | Changes |
|------|---------|
| `tools_v2/file_router.py` | Added `_auto_categorize_app()` function, auto-categorizes during table processing |
| `tools_v2/enrichment/inventory_reviewer.py` | Added local lookup, category validation/normalization functions |

### Key Features

```python
# App category mappings
from stores.app_category_mappings import lookup_app, categorize_app

mapping = lookup_app("Salesforce")  # Returns AppMapping with category, vendor, description
category, mapping = categorize_app("SAP")  # Returns ("erp", AppMapping)

# Auto-categorization in file router
# Happens automatically during ingest_file() for application inventory

# Category validation in enrichment
from tools_v2.enrichment.inventory_reviewer import validate_category, normalize_category

validate_category("erp")  # True
normalize_category("HR")  # "hcm"
normalize_category("accounting")  # "finance"
```

### Categories Defined

| Category | Description |
|----------|-------------|
| erp | Enterprise Resource Planning (SAP, Oracle, NetSuite) |
| crm | Customer Relationship Management (Salesforce, HubSpot) |
| hcm | Human Capital Management (Workday, ADP, BambooHR) |
| finance | Financial Management (QuickBooks, Concur) |
| collaboration | Communication & Collaboration (Teams, Slack, Zoom) |
| productivity | Office & Productivity (Microsoft 365, Google Workspace) |
| security | Security & Identity (Okta, CrowdStrike, Zscaler) |
| infrastructure | Infrastructure & Platform (AWS, Azure, VMware) |
| database | Database Systems (Oracle DB, SQL Server, Snowflake) |
| devops | Development & Operations (GitHub, Jira, ServiceNow) |
| bi_analytics | Business Intelligence (Tableau, Power BI) |
| industry_vertical | Industry-Specific (Epic, Guidewire, Duck Creek) |
| custom | Custom/In-house Built |
| unknown | Requires investigation |

---

## PHASE 5: DOCUMENT PARSING & PREPROCESSING

**Status:** ✅ COMPLETE
**Tests:** 43/43 passing

### Problem
1. Private-use Unicode chars (U+E000-U+F8FF) corrupting output
2. Citation artifacts (filecite) appearing in processed text
3. Tables split mid-row during chunking
4. Inconsistent numeric parsing ($1,234 vs 1234 vs "N/A")

### Solution
Create preprocessing and parsing utilities in `tools_v2/`.

### New Files

| File | Purpose |
|------|---------|
| `tools_v2/document_preprocessor.py` | Text cleaning: PUA removal, citation cleanup, whitespace normalization |
| `tools_v2/numeric_normalizer.py` | Numeric parsing: currency, counts, percentages, null handling |
| `tools_v2/table_chunker.py` | Table-aware chunking: preserve table integrity, repeat headers |
| `tools_v2/table_parser.py` | Deterministic Markdown table parsing |
| `tools_v2/__init__.py` | Updated with Phase 5 exports |
| `tests/test_document_parsing.py` | 43 comprehensive tests |

### Key Features

```python
# Document Preprocessing
from tools_v2 import preprocess_document
clean = preprocess_document(dirty_text)  # Removes PUA, filecite, control chars

# Numeric Normalization
from tools_v2 import normalize_numeric, normalize_cost
normalize_numeric("$1,234.56")  # → 1234.56
normalize_numeric("N/A")        # → None
normalize_numeric("~500")       # → 500

# Table-Aware Chunking
from tools_v2 import chunk_document
chunks = chunk_document(text, max_chunk_size=4000)
# Tables never split mid-row; large tables repeat headers

# Table Parsing
from tools_v2 import parse_table
table = parse_table(markdown_table)
# Returns ParsedTable with headers, rows (normalized), raw_rows
```

---

## PHASE 6: COST ESTIMATION DETERMINISM

**Status:** ✅ COMPLETE
**Tests:** 30/30 passing

### Problem
Cost estimates vary on identical inputs due to:
1. Non-deterministic fact matching order
2. No caching for repeated calculations
3. Inconsistent rule application order

### Solution
1. Deterministic fact normalization and sorting
2. Cost estimate cache with content-based keys
3. Rules sorted by rule_id for consistent processing
4. Input hash for reproducibility verification

### New Files

| File | Purpose |
|------|---------|
| `tools_v2/cost_cache.py` | Cost estimate caching with deterministic hashing |
| `tests/test_cost_determinism.py` | 30 comprehensive tests |

### Files Modified

| File | Changes |
|------|---------|
| `tools_v2/cost_model.py` | Added cache integration, sorted rules, normalized facts, deterministic input hash |

### Key Changes

```python
# CostModel now sorts rules and normalizes facts
class CostModel:
    def __init__(self, use_cache: bool = True, cache_ttl: int = None):
        # Rules sorted by rule_id for deterministic processing
        self.rules = sorted(ADJUSTMENT_RULES, key=lambda r: r.rule_id)

    def _normalize_facts(self, facts: List[Dict]) -> List[Dict]:
        # Sort by content for deterministic matching
        normalized.sort(key=lambda f: f.get("content", "").lower())
        return normalized

# CostEstimateCache provides caching
from tools_v2.cost_cache import get_cost_cache

cache = get_cost_cache()
cached = cache.get(user_count=1500, deal_type="carveout", facts=facts)
if cached:
    return cached

# After calculation:
cache.set(estimate, user_count=1500, deal_type="carveout", facts=facts)

# Methodology now indicates determinism
result["methodology"] = "anchored_estimation_v2.1_deterministic"
```

---

## IMPLEMENTATION ORDER

```
Phase 1/6 (Deal Isolation) ✅
    ↓
Phase 2+4 (Presentation) ✅
    ↓
Phase 5 (Document Parsing) ✅
    ↓
Phase 3 (App Ingestion) ✅
    ↓
Phase 6 (Cost Determinism) ✅  ← COMPLETE
```

**V2.3 RELEASE READY** - All 6 phases implemented with 148 tests passing.

---

## TEST COMMANDS

```bash
# Run all 2.3 tests (148 tests)
python -m pytest tests/test_deal_isolation.py tests/test_presentation_smoke.py tests/test_document_parsing.py tests/test_app_categorization.py tests/test_cost_determinism.py -v

# Run specific phase
python -m pytest tests/test_deal_isolation.py -v      # Phase 1/6 (25 tests)
python -m pytest tests/test_presentation_smoke.py -v  # Phase 2+4 (16 tests)
python -m pytest tests/test_document_parsing.py -v    # Phase 5 (43 tests)
python -m pytest tests/test_app_categorization.py -v  # Phase 3 (37 tests)
python -m pytest tests/test_cost_determinism.py -v    # Phase 6 (30 tests)

# Verify imports work
python -c "from tools_v2 import preprocess_document, normalize_numeric, chunk_document, parse_table; print('OK')"
python -c "from stores.app_category_mappings import lookup_app, categorize_app; print('OK')"
python -c "from tools_v2.cost_cache import get_cost_cache, CostEstimateCache; print('OK')"
```

---

## SUCCESS CRITERIA

### Phase 1/6 (Deal Isolation) ✅
- [x] All stores include deal_id field
- [x] ID generation includes deal_id for uniqueness
- [x] Migration script handles existing data
- [x] 25 tests passing

### Phase 2+4 (Presentation) ✅
- [x] Dashboard loads without 500 errors on missing data
- [x] Mermaid charts render with special characters in names
- [x] Templates use defensive |default patterns
- [x] 13 tests passing

### Phase 5 (Document Parsing) ✅
- [x] PUA characters removed from all output
- [x] Citation artifacts cleaned
- [x] Tables never split mid-row
- [x] Numeric values consistently normalized
- [x] 43 tests passing

### Phase 3 (App Ingestion) ✅
- [x] Standard apps auto-categorized (106+ mappings)
- [x] Unknown apps flagged for review
- [x] Categories validated against schema
- [x] Local lookup before LLM (cost savings)
- [x] 37 tests passing

### Phase 6 (Cost Determinism) ✅
- [x] Same input produces same cost estimate
- [x] Facts normalized and sorted before processing
- [x] Rules processed in consistent order (sorted by rule_id)
- [x] Caching for repeated calculations
- [x] Deterministic input hash for verification
- [x] 30 tests passing

---

## VERSION HISTORY

| Date | Changes |
|------|---------|
| 2026-02-03 | Created plan, completed all 6 phases (148 tests total) |

---

*V2.3 COMPLETE: All phases implemented for data integrity, presentation reliability, processing determinism, and cost estimation consistency.*
