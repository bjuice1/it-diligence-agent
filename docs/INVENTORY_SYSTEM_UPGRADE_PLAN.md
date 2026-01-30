# IT Diligence Agent: Inventory System Upgrade Plan

> **Purpose:** Transform the system from universal LLM extraction to structured inventory ingestion + intelligent analysis
> **Created:** 2025-01-29
> **Status:** Planning

---

## Executive Summary

### The Problem
The current system uses LLM discovery for all inputs, including structured data from ToltIQ exports. This causes:
- Missed items (LLM probabilistically skips rows)
- Inconsistent extraction (different results on re-runs)
- Wrong details in reports
- Unnecessary cost/latency for deterministic data

### The Solution
Separate **structured inventory ingestion** (deterministic) from **unstructured fact extraction** (LLM), then enhance with an **application intelligence layer** that enriches inventory items with context.

### The Outcome
- 100% reliable inventory ingestion from Word/Excel/Markdown
- Enriched inventory items with industry context and flags
- Preserved LLM path for meeting notes and unstructured docs
- Reasoning layer cites both inventory items and extracted facts
- Clean reports with accurate data

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              INPUT LAYER                                     │
├─────────────────────────────────┬───────────────────────────────────────────┤
│     Structured Inventories      │        Unstructured Documents             │
│     (ToltIQ exports)            │        (Meeting notes, PDFs)              │
│                                 │                                           │
│  • Excel workbooks              │  • Interview transcripts                  │
│  • Word docs with tables        │  • Policy documents                       │
│  • CSV files                    │  • General IT narratives                  │
│  • Markdown tables              │                                           │
└────────────────┬────────────────┴─────────────────────┬─────────────────────┘
                 │                                       │
                 ▼                                       ▼
┌─────────────────────────────────┐   ┌───────────────────────────────────────┐
│         FILE ROUTER             │   │                                       │
│                                 │   │                                       │
│  • Detect file format           │   │                                       │
│  • Parse tables vs prose        │   │                                       │
│  • Auto-detect inventory type   │   │                                       │
│  • Validate schema              │   │                                       │
└────────────────┬────────────────┘   │                                       │
                 │                     │                                       │
                 ▼                     │                                       │
┌─────────────────────────────────┐   │                                       │
│     INVENTORY STORE             │   │          FACT STORE                   │
│                                 │   │                                       │
│  I-APP-001: Duck Creek Policy   │   │  F-CYBER-001: "CTO stated             │
│    vendor: Duck Creek           │   │    migration planned for Q3"          │
│    version: 12                  │   │    evidence: "We're targeting..."     │
│    cost: $546,257               │   │    source: meeting_notes.txt          │
│    enrichment:                  │   │                                       │
│      category: "industry_std"   │   │  Immutable, evidence-backed           │
│      note: "Major insurance     │   │                                       │
│             policy admin"       │   │                                       │
│                                 │   │                                       │
│  Editable, enriched with        │   │                                       │
│  application intelligence       │   │                                       │
└────────────────┬────────────────┘   └─────────────────────┬─────────────────┘
                 │                                           │
                 └─────────────────────┬─────────────────────┘
                                       │
                                       ▼
                 ┌─────────────────────────────────────────────┐
                 │           APPLICATION INTELLIGENCE          │
                 │                                             │
                 │  For each inventory item:                   │
                 │  • "Industry standard" (Salesforce, SAP)    │
                 │  • "Expected for vertical" (Duck Creek      │
                 │     for insurance)                          │
                 │  • "Niche/uncommon" (needs investigation)   │
                 │  • "Unknown" (custom or obscure - flag it)  │
                 │  • Major system confirmation                │
                 └─────────────────────┬───────────────────────┘
                                       │
                                       ▼
                 ┌─────────────────────────────────────────────┐
                 │            REASONING LAYER                  │
                 │                                             │
                 │  Receives:                                  │
                 │  • Enriched inventory (batched if large)    │
                 │  • Extracted facts                          │
                 │                                             │
                 │  Produces:                                  │
                 │  • Risks (citing I-XXX and F-XXX)           │
                 │  • Work items with costs                    │
                 │  • Strategic considerations                 │
                 └─────────────────────┬───────────────────────┘
                                       │
                                       ▼
                 ┌─────────────────────────────────────────────┐
                 │              OUTPUT LAYER                   │
                 │                                             │
                 │  • HTML Report                              │
                 │  • Excel Export (inventory sheets)          │
                 │  • Investment Thesis                        │
                 │  • VDR Requests                             │
                 │  • Cost Summaries                           │
                 └─────────────────────────────────────────────┘
```

---

## Data Models

### InventoryItem

```python
@dataclass
class InventoryItem:
    # Identity
    item_id: str              # I-APP-a3f2 (content-hashed, stable)
    inventory_type: str       # application, infrastructure, organization, vendor
    entity: str               # target, buyer

    # Core Data (flexible schema per type)
    data: Dict[str, Any]      # {name, vendor, version, cost, ...}
                              # Missing fields = None or "N/A"

    # Source Tracking
    source_file: str          # Original file this came from
    source_type: str          # "import" or "manual"

    # Enrichment (from Application Intelligence)
    enrichment: Dict[str, Any]  # {
                                #   category: "industry_standard" | "vertical_specific" |
                                #             "niche" | "unknown" | "custom"
                                #   note: "Major insurance policy admin system"
                                #   confidence: "high" | "medium" | "low"
                                #   flag: None | "investigate" | "confirm"
                                # }

    # Status
    status: str               # active, removed
    removal_reason: str       # If removed, why

    # Timestamps
    created_at: datetime
    modified_at: datetime
    modified_by: str
```

### Inventory Schemas

```python
INVENTORY_SCHEMAS = {
    "application": {
        "required": ["name"],
        "optional": ["vendor", "version", "hosting", "users", "cost",
                     "criticality", "category", "contract_end", "notes"],
        "id_fields": ["name", "vendor"],  # Used for content-hashing
    },
    "infrastructure": {
        "required": ["name"],  # hostname, server name, etc.
        "optional": ["type", "os", "ip", "location", "environment",
                     "cpu", "memory", "storage", "notes"],
        "id_fields": ["name", "environment"],
    },
    "organization": {
        "required": ["role"],
        "optional": ["team", "department", "headcount", "fte",
                     "salary", "location", "reports_to", "notes"],
        "id_fields": ["role", "team"],
    },
    "vendor": {
        "required": ["vendor_name"],
        "optional": ["contract_type", "services", "start_date", "end_date",
                     "renewal_date", "acv", "tcv", "owner", "notes"],
        "id_fields": ["vendor_name", "contract_type"],
    }
}
```

### Fact (Simplified)

```python
@dataclass
class Fact:
    fact_id: str              # F-CYBER-a3f2 (content-hashed)
    domain: str               # infrastructure, network, cybersecurity, etc.
    category: str
    observation: str          # What was observed

    # Evidence (required)
    evidence: Dict[str, str]  # {exact_quote, source_section}
    source_document: str

    # Context
    entity: str               # target, buyer
    confidence: float         # 0.0-1.0

    # Timestamps
    created_at: datetime

    # Immutable - no edit fields
```

---

## ID Generation Strategy

### Content-Based Hashing

All IDs are generated from content hash to ensure stability across re-imports:

```python
def generate_item_id(inventory_type: str, data: Dict, entity: str) -> str:
    """
    Generate stable ID from content hash.

    Same item always gets same ID, regardless of import order.
    """
    schema = INVENTORY_SCHEMAS[inventory_type]
    id_fields = schema["id_fields"]

    # Build content string from key fields
    parts = [inventory_type, entity]
    for field in id_fields:
        value = data.get(field, "")
        parts.append(str(value).lower().strip())

    content = "|".join(parts)
    hash_val = hashlib.sha256(content.encode()).hexdigest()[:6]

    prefix = INVENTORY_PREFIXES[inventory_type]  # APP, INFRA, ORG, VENDOR
    return f"I-{prefix}-{hash_val}"
```

### ID Prefixes

| Type | Prefix | Example |
|------|--------|---------|
| Application | I-APP | I-APP-a3f291 |
| Infrastructure | I-INFRA | I-INFRA-b7c82f |
| Organization | I-ORG | I-ORG-c9d123 |
| Vendor | I-VENDOR | I-VENDOR-e2f456 |
| Fact | F-{DOMAIN} | F-CYBER-f1a789 |

---

## Application Intelligence Layer

### Purpose

Enrich each inventory item with context that helps reasoning and reporting:

1. **Categorize** - Is this app industry standard, vertical-specific, niche, or unknown?
2. **Contextualize** - What does this app do? Why might it matter for the deal?
3. **Flag** - Should someone investigate or confirm this?

### Categories

| Category | Description | Example |
|----------|-------------|---------|
| `industry_standard` | Ubiquitous across industries | Salesforce, Microsoft 365, SAP |
| `vertical_specific` | Common in this industry | Duck Creek (insurance), Epic (healthcare) |
| `niche` | Uncommon, specialized | Small vendor, limited market presence |
| `unknown` | Can't identify, needs research | "CustomApp123", obscure vendor |
| `custom` | Built in-house | "Internal Claims Portal" |

### Enrichment Process

```python
def enrich_inventory_item(item: InventoryItem, industry: str) -> InventoryItem:
    """
    Enrich inventory item with application intelligence.

    Uses:
    1. Known vendor/product reference database
    2. Industry-specific expectations
    3. LLM for unknown items (optional)
    """
    name = item.data.get("name", "")
    vendor = item.data.get("vendor", "")

    # Check reference database first
    known_app = lookup_known_application(name, vendor)

    if known_app:
        item.enrichment = {
            "category": known_app.category,
            "note": known_app.description,
            "confidence": "high",
            "flag": None
        }
    elif is_likely_custom(name, vendor):
        item.enrichment = {
            "category": "custom",
            "note": "Appears to be custom/in-house application",
            "confidence": "medium",
            "flag": "confirm"
        }
    else:
        item.enrichment = {
            "category": "unknown",
            "note": "Unable to identify - may be niche or custom",
            "confidence": "low",
            "flag": "investigate"
        }

    return item
```

### Reference Database Structure

```python
KNOWN_APPLICATIONS = {
    "salesforce": {
        "category": "industry_standard",
        "description": "Leading CRM platform",
        "verticals": ["all"],
    },
    "duck creek": {
        "category": "vertical_specific",
        "description": "Insurance policy administration system",
        "verticals": ["insurance"],
    },
    "epic": {
        "category": "vertical_specific",
        "description": "Healthcare EMR system",
        "verticals": ["healthcare"],
    },
    # ... hundreds more
}

INDUSTRY_EXPECTATIONS = {
    "insurance": {
        "expected_apps": ["policy_admin", "claims_management", "billing",
                         "actuarial", "agency_portal"],
        "common_vendors": ["duck creek", "guidewire", "majesco"],
    },
    "healthcare": {
        "expected_apps": ["emr", "pacs", "rcm", "patient_portal"],
        "common_vendors": ["epic", "cerner", "meditech"],
    },
    # ... other industries
}
```

---

## Missing Data Handling

### On Import

When inventory data has missing fields:

```python
def normalize_inventory_row(row: Dict, schema: Dict) -> Dict:
    """
    Normalize row data, marking missing fields appropriately.
    """
    normalized = {}

    for field in schema["required"]:
        value = row.get(field)
        if not value or value.strip() == "":
            # Required field missing - this is a problem
            normalized[field] = None
            normalized[f"_{field}_missing"] = True
        else:
            normalized[field] = value.strip()

    for field in schema["optional"]:
        value = row.get(field)
        if not value or value.strip() == "" or value.lower() in ["n/a", "tbd", "-", "unknown"]:
            normalized[field] = None  # Explicitly None, not empty string
        else:
            normalized[field] = value.strip()

    return normalized
```

### In Reports

Report generator handles missing data gracefully:

```python
def format_inventory_value(value: Any, field: str) -> str:
    """Format inventory value for display."""
    if value is None:
        return "—"  # Em dash for missing
    if field == "cost" and isinstance(value, (int, float)):
        return f"${value:,.0f}"
    return str(value)
```

### Gap Generation from Missing Data

```python
def analyze_inventory_completeness(inventory_store: InventoryStore) -> List[Gap]:
    """
    Generate gaps from incomplete inventory data.
    """
    gaps = []

    for inv_type in ["application", "infrastructure", "organization", "vendor"]:
        items = inventory_store.get_items(inv_type)

        if not items:
            gaps.append(Gap(
                category=inv_type,
                description=f"No {inv_type} inventory provided",
                importance="high"
            ))
            continue

        # Check for missing critical fields
        schema = INVENTORY_SCHEMAS[inv_type]
        missing_counts = defaultdict(int)

        for item in items:
            for field in schema["optional"]:
                if item.data.get(field) is None:
                    missing_counts[field] += 1

        # Flag significant gaps
        total = len(items)
        for field, count in missing_counts.items():
            if count / total > 0.5:  # More than 50% missing
                gaps.append(Gap(
                    category=inv_type,
                    description=f"{count}/{total} {inv_type} items missing '{field}'",
                    importance="medium"
                ))

    return gaps
```

---

## Large Inventory Handling (Batching)

### Problem

500+ inventory items won't fit in a single reasoning context.

### Solution

Batch processing with summary injection:

```python
def prepare_inventory_for_reasoning(
    inventory_store: InventoryStore,
    batch_size: int = 50
) -> List[ReasoningContext]:
    """
    Prepare inventory for reasoning in manageable batches.

    Returns list of contexts, each with:
    - Overall summary (always included)
    - Batch of detailed items
    - Batch metadata
    """
    contexts = []

    # Generate overall summary (always included)
    summary = generate_inventory_summary(inventory_store)

    # Get all items sorted by criticality/importance
    all_items = inventory_store.get_all_items(sort_by="criticality")

    # Batch items
    for i in range(0, len(all_items), batch_size):
        batch = all_items[i:i + batch_size]

        contexts.append(ReasoningContext(
            summary=summary,
            items=batch,
            batch_number=i // batch_size + 1,
            total_batches=(len(all_items) + batch_size - 1) // batch_size,
            batch_focus=categorize_batch(batch)  # e.g., "critical apps", "infrastructure"
        ))

    return contexts


def generate_inventory_summary(inventory_store: InventoryStore) -> str:
    """
    Generate high-level summary for context injection.
    """
    apps = inventory_store.get_items("application")
    infra = inventory_store.get_items("infrastructure")
    org = inventory_store.get_items("organization")
    vendors = inventory_store.get_items("vendor")

    # App summary
    app_summary = f"""
Applications: {len(apps)} total
  - Critical: {count_by_criticality(apps, 'critical')}
  - High: {count_by_criticality(apps, 'high')}
  - Total annual spend: ${sum_costs(apps):,.0f}
  - Top vendors: {top_vendors(apps, 5)}
  - Enrichment: {count_by_enrichment(apps)}
"""

    # Similar for other types...

    return app_summary + infra_summary + org_summary + vendor_summary
```

### Reasoning Flow with Batches

```python
async def run_batched_reasoning(
    inventory_store: InventoryStore,
    fact_store: FactStore,
    reasoning_store: ReasoningStore
):
    """
    Run reasoning across inventory batches, then consolidate.
    """
    contexts = prepare_inventory_for_reasoning(inventory_store)

    # Phase 1: Process each batch
    batch_results = []
    for ctx in contexts:
        result = await run_reasoning_on_context(ctx, fact_store)
        batch_results.append(result)

    # Phase 2: Consolidate findings
    # - Deduplicate risks that appear in multiple batches
    # - Aggregate costs
    # - Merge related findings
    consolidated = consolidate_reasoning_results(batch_results)

    # Phase 3: Cross-batch analysis
    # - Patterns across the full inventory
    # - Systemic issues
    cross_batch = run_cross_batch_analysis(consolidated, inventory_store)

    return merge_results(consolidated, cross_batch)
```

---

## Phase 1: Foundation

**Goal:** Create the data layer for the new model

**Duration:** 2-3 days

### Deliverables

#### 1.1 Create InventoryStore (`stores/inventory_store.py`)

```python
class InventoryStore:
    def __init__(self, storage_path: Optional[Path] = None):
        self.items: Dict[str, InventoryItem] = {}
        self.storage_path = storage_path
        self._lock = threading.Lock()

    # Core CRUD
    def add_item(self, inventory_type: str, data: Dict, entity: str,
                 source_file: str, source_type: str = "import") -> str
    def get_item(self, item_id: str) -> Optional[InventoryItem]
    def update_item(self, item_id: str, updates: Dict, modified_by: str) -> bool
    def remove_item(self, item_id: str, reason: str, removed_by: str) -> bool

    # Query
    def get_items(self, inventory_type: str = None, entity: str = None,
                  status: str = "active") -> List[InventoryItem]
    def get_items_by_enrichment(self, category: str) -> List[InventoryItem]
    def exists(self, item_id: str) -> bool
    def find_by_name(self, name: str, inventory_type: str) -> Optional[InventoryItem]

    # Aggregation
    def count(self, inventory_type: str = None) -> int
    def sum_costs(self, inventory_type: str = None) -> float
    def get_summary(self) -> Dict

    # Persistence
    def save(self, path: Path = None) -> None
    def load(self, path: Path) -> None

    # Merge/Import
    def merge_from(self, other: "InventoryStore", strategy: str = "add_new") -> MergeResult
```

#### 1.2 Content-Based ID Generation (`stores/id_generator.py`)

```python
def generate_inventory_id(inventory_type: str, data: Dict, entity: str) -> str
def generate_fact_id(domain: str, observation: str, entity: str) -> str
```

#### 1.3 Update FactStore

- Switch to content-based IDs
- Remove fields that don't apply to extracted facts
- Keep evidence requirements strict

#### 1.4 Schema Definitions (`config/inventory_schemas.py`)

```python
INVENTORY_SCHEMAS = {...}  # As defined above
INVENTORY_PREFIXES = {...}
REQUIRED_ENRICHMENT_FIELDS = {...}
```

### Tests

- [ ] Create InventoryStore, add items, verify IDs are stable
- [ ] Save/load InventoryStore, verify data integrity
- [ ] Content-hash IDs: same item → same ID across sessions
- [ ] Remove item, re-add → same ID restored

### Exit Criteria

- InventoryStore can store/retrieve all inventory types
- IDs are stable across saves/loads
- FactStore updated with content-based IDs

---

## Phase 2: Parsers & Router

**Goal:** Ingest any file format, route content appropriately

**Duration:** 3-4 days

### Deliverables

#### 2.1 Word Parser (`tools_v2/parsers/word_parser.py`)

```python
def parse_word_document(file_path: Path) -> ParseResult:
    """
    Extract tables and prose from Word document.

    Returns:
        ParseResult with:
        - tables: List[ParsedTable]
        - prose: str (remaining text)
        - metadata: document properties
    """
```

#### 2.2 Excel Parser (`tools_v2/parsers/excel_parser.py`)

```python
def parse_excel_workbook(file_path: Path) -> List[ParsedTable]:
    """
    Extract all sheets as tables.

    Handles:
    - Multiple sheets
    - Header row detection
    - Empty row/column trimming
    """
```

#### 2.3 Markdown Parser (`tools_v2/parsers/markdown_parser.py`)

```python
def parse_markdown(text: str) -> ParseResult:
    """
    Extract tables and prose from Markdown.
    """
```

#### 2.4 Inventory Type Detector (`tools_v2/parsers/type_detector.py`)

```python
def detect_inventory_type(headers: List[str]) -> Tuple[str, float]:
    """
    Auto-detect inventory type from column headers.

    Returns:
        (inventory_type, confidence)
        inventory_type: application, infrastructure, organization, vendor, unknown
        confidence: 0.0-1.0
    """
```

#### 2.5 Schema Validator (`tools_v2/parsers/schema_validator.py`)

```python
def validate_against_schema(table: ParsedTable, inventory_type: str) -> ValidationResult:
    """
    Validate table against expected schema.

    Returns:
        ValidationResult with:
        - is_valid: bool
        - missing_required: List[str]
        - missing_optional: Dict[str, int]  # field -> count
        - warnings: List[str]
    """
```

#### 2.6 File Router (`tools_v2/file_router.py`)

```python
def ingest_file(
    file_path: Path,
    inventory_store: InventoryStore,
    fact_store: FactStore,
    entity: str,
    run_llm_discovery: bool = True
) -> IngestResult:
    """
    Route file content appropriately.

    - Tables with known type → InventoryStore
    - Tables with unknown type → Log warning, optionally send to LLM
    - Prose → FactStore via LLM discovery (if enabled)

    Returns:
        IngestResult with:
        - inventory_items_added: int
        - facts_extracted: int
        - unknown_tables: List[TableInfo]  # For user review
        - validation_warnings: List[str]
        - errors: List[str]
    """
```

#### 2.7 Validation Output

After ingestion, display clear summary:

```
Ingested: ToltIQ_Analysis.docx

  Applications: 33 items loaded
    ✓ Matches stated total (33)
    ⚠ 5 items missing 'cost' field
    First 3: Duck Creek Policy, Majesco Policy, Guidewire ClaimCenter

  Infrastructure: 127 items loaded
    ✓ All required fields present

  Unknown tables: 1
    Table on page 4 (headers: Notes, Comments) - skipped

  Prose: 8 pages sent to LLM discovery
    → 12 facts extracted
```

#### 2.8 Re-Import Merge Logic

```python
def reimport_inventory(
    inventory_store: InventoryStore,
    new_file: Path,
    merge_strategy: str = "smart"
) -> MergeResult:
    """
    Re-import from updated source file.

    Strategies:
    - "add_new": Only add items not already present
    - "update": Add new, update existing (by ID match)
    - "smart": Add new, update existing, flag removed items

    Smart merge rules:
    - New in file → Add
    - In file and store, same data → Skip
    - In file and store, different data → Update (keep ID)
    - In store but not file, source="import" → Flag as "removed_from_source"
    - In store but not file, source="manual" → Keep (user added)
    - In store with status="removed" → Don't resurrect
    """
```

### Tests

- [ ] Parse Word doc with tables + prose → correct split
- [ ] Parse Excel with multiple sheets → all sheets extracted
- [ ] Detect inventory type from various header formats
- [ ] Validate schema → correct warnings for missing fields
- [ ] Unknown table type → logged, not silently dropped
- [ ] Re-import with changes → correct merge behavior
- [ ] Duplicate items → skipped with log

### Exit Criteria

- All file formats parse correctly (Word, Excel, Markdown, CSV)
- Inventory type auto-detection works with >90% accuracy
- Schema validation catches missing required fields
- Re-import merge logic handles all scenarios
- Clear validation output after ingestion

---

## Phase 3: Application Intelligence

**Goal:** Enrich inventory items with context and categorization

**Duration:** 2-3 days

### Deliverables

#### 3.1 Known Applications Database (`data/known_applications.json`)

```json
{
  "applications": {
    "salesforce": {
      "names": ["salesforce", "sfdc", "sales cloud", "service cloud"],
      "vendor": "Salesforce",
      "category": "industry_standard",
      "description": "Leading CRM platform",
      "verticals": ["all"]
    },
    "duck creek": {
      "names": ["duck creek", "duckcreek"],
      "vendor": "Duck Creek Technologies",
      "category": "vertical_specific",
      "description": "Insurance policy administration and billing platform",
      "verticals": ["insurance"]
    }
    // ... 200+ common enterprise applications
  }
}
```

#### 3.2 Industry Expectations (`data/industry_expectations.json`)

```json
{
  "insurance": {
    "expected_categories": [
      "policy_admin", "claims_management", "billing",
      "actuarial", "agency_portal", "reinsurance"
    ],
    "common_vendors": ["duck creek", "guidewire", "majesco", "sapiens"],
    "typical_app_count": {"min": 20, "max": 100},
    "typical_critical_apps": 5
  }
  // ... other industries
}
```

#### 3.3 Enrichment Engine (`tools_v2/enrichment/app_intelligence.py`)

```python
class ApplicationIntelligence:
    def __init__(self, industry: str = None):
        self.known_apps = load_known_applications()
        self.industry = industry
        self.industry_expectations = load_industry_expectations(industry)

    def enrich_item(self, item: InventoryItem) -> InventoryItem:
        """Add enrichment data to inventory item."""

    def enrich_batch(self, items: List[InventoryItem]) -> List[InventoryItem]:
        """Enrich multiple items, leveraging batch patterns."""

    def get_inventory_insights(self, items: List[InventoryItem]) -> InventoryInsights:
        """
        Generate insights about the inventory as a whole:
        - Missing expected categories for industry
        - Unusual patterns (too many of X, none of Y)
        - Vendor concentration risk
        - Unknown/custom app percentage
        """
```

#### 3.4 LLM Fallback for Unknown Apps

```python
async def enrich_unknown_apps_with_llm(
    items: List[InventoryItem],
    model: str = "claude-3-5-haiku"
) -> List[InventoryItem]:
    """
    Use LLM to research and categorize unknown applications.

    Batches items for efficiency.
    Only called for items with enrichment.category == "unknown".
    """
```

### Tests

- [ ] Known app lookup works (exact match, fuzzy match)
- [ ] Industry-specific apps detected correctly
- [ ] Unknown apps flagged appropriately
- [ ] Custom apps detected (naming patterns)
- [ ] Inventory insights generated correctly

### Exit Criteria

- 80%+ of common enterprise apps recognized
- Industry-specific expectations applied
- Unknown apps clearly flagged for investigation
- Insights generated about inventory patterns

---

## Phase 4: Pipeline Integration

**Goal:** Wire new data layer into existing pipeline

**Duration:** 3-4 days

### Deliverables

#### 4.1 Update Main Entry Point (`main_v2.py`)

```python
def main():
    # Initialize stores
    inventory_store = InventoryStore()
    fact_store = FactStore()

    # Phase 1: Ingest files
    for file in input_files:
        result = ingest_file(file, inventory_store, fact_store, entity)
        print_ingest_summary(result)

    # Phase 2: Enrich inventory
    enricher = ApplicationIntelligence(industry=args.industry)
    for item in inventory_store.get_items():
        enricher.enrich_item(item)

    # Phase 3: Generate inventory insights
    insights = enricher.get_inventory_insights(inventory_store.get_items())

    # Phase 4: Reasoning (batched for large inventories)
    contexts = prepare_inventory_for_reasoning(inventory_store)
    for ctx in contexts:
        run_reasoning_on_context(ctx, fact_store, reasoning_store)

    # Phase 5: Consolidate and continue...
```

#### 4.2 Update Reasoning Prompts

```python
REASONING_SYSTEM_PROMPT = """
You are analyzing IT due diligence data for an M&A transaction.

You have access to two types of source data:

1. INVENTORY ITEMS (I-XXX): Structured records from the target company
   - Applications (I-APP-XXX): Software systems with vendor, version, cost
   - Infrastructure (I-INFRA-XXX): Servers, VMs, network devices
   - Organization (I-ORG-XXX): Teams, roles, headcount
   - Vendors (I-VENDOR-XXX): Contracts, MSAs, renewals

   Each inventory item includes enrichment data indicating whether it's:
   - Industry standard (e.g., Salesforce, Microsoft 365)
   - Vertical-specific (e.g., Duck Creek for insurance)
   - Niche or unknown (flagged for investigation)

2. EXTRACTED FACTS (F-XXX): Observations from unstructured documents
   - Meeting notes, interview transcripts, policy documents
   - Each fact includes evidence (exact quote from source)

When creating risks, work items, or recommendations, cite your sources:
- Use I-APP-001 for inventory items
- Use F-CYBER-001 for extracted facts
- You may cite multiple sources for a single finding

{inventory_summary}

{batch_details}

{extracted_facts}
"""
```

#### 4.3 Update Citation Validation

```python
def validate_citation(citation: str, inventory_store: InventoryStore,
                      fact_store: FactStore) -> bool:
    """Validate that a citation references a real item."""
    if citation.startswith("I-"):
        return inventory_store.exists(citation)
    elif citation.startswith("F-"):
        return fact_store.exists(citation)
    return False
```

#### 4.4 Update Coverage Analysis

```python
def analyze_coverage(inventory_store: InventoryStore,
                    fact_store: FactStore,
                    industry: str) -> CoverageResult:
    """
    Analyze completeness of available data.

    Checks:
    - Required inventory types present
    - Industry-expected categories covered
    - Missing required fields in inventory
    - Key topics covered in facts
    """
```

#### 4.5 Batched Reasoning Implementation

```python
async def run_batched_reasoning(
    inventory_store: InventoryStore,
    fact_store: FactStore,
    reasoning_store: ReasoningStore,
    batch_size: int = 50
) -> ReasoningResult:
    """
    Run reasoning across batched inventory.
    """
```

### Tests

- [ ] Full pipeline runs with inventory + facts
- [ ] Reasoning correctly cites I-XXX and F-XXX
- [ ] Large inventory (500+ items) processes in batches
- [ ] Coverage analysis reflects new data model
- [ ] Cross-batch consolidation works correctly

### Exit Criteria

- Pipeline accepts new data model
- Reasoning prompts understand inventory vs facts
- Batching works for large inventories
- All downstream phases (synthesis, VDR) work

---

## Phase 5: Reports & Exports

**Goal:** Update all outputs to reflect new data model

**Duration:** 2-3 days

### Deliverables

#### 5.1 Update HTML Report

```html
<!-- Inventory Section -->
<section id="inventory">
  <h2>Application Inventory</h2>
  <div class="inventory-stats">
    <span>33 Applications</span>
    <span>$7.2M Annual Spend</span>
    <span>8 Critical</span>
  </div>

  <div class="enrichment-summary">
    <span class="industry-standard">18 Industry Standard</span>
    <span class="vertical">8 Insurance-Specific</span>
    <span class="unknown">4 Unknown (flagged)</span>
    <span class="custom">3 Custom</span>
  </div>

  <table class="inventory-table">
    <!-- Sortable, filterable inventory table -->
  </table>
</section>

<!-- Findings Section -->
<section id="findings">
  <!-- Each finding shows source type: Inventory vs Fact -->
  <div class="finding">
    <h3>EOL Platform Risk</h3>
    <div class="sources">
      <span class="inventory-source">I-APP-003: Oracle EBS</span>
      <span class="fact-source">F-INFRA-007: "CTO mentioned..."</span>
    </div>
  </div>
</section>
```

#### 5.2 Update Excel Export

**Sheets:**
1. **Summary** - Key metrics, totals
2. **Applications** - Full app inventory with enrichment
3. **Infrastructure** - Full infra inventory
4. **Organization** - Full org inventory
5. **Vendors** - Full vendor inventory
6. **Extracted Facts** - Observations from unstructured docs
7. **Risks** - With source citations
8. **Work Items** - With cost estimates and sources
9. **Gaps** - From coverage analysis

#### 5.3 Update Investment Thesis

- Pull metrics directly from inventory (accurate counts, costs)
- Show enrichment insights ("8 insurance-specific applications")
- Flag unknowns ("4 applications require investigation")

#### 5.4 Cost Aggregation

```python
def aggregate_costs(inventory_store: InventoryStore,
                   reasoning_store: ReasoningStore) -> CostSummary:
    """
    Aggregate costs from all sources.

    Returns:
        CostSummary with:
        - current_spend: From inventory (app costs, contract values)
        - remediation_estimate: From work items
        - synergy_potential: From buyer/target overlap analysis
    """
```

### Tests

- [ ] HTML report displays inventory correctly
- [ ] Excel has all inventory sheets with correct data
- [ ] Enrichment categories shown in reports
- [ ] Cost aggregation is accurate
- [ ] Source citations render correctly (I-XXX vs F-XXX)

### Exit Criteria

- All report types updated for new data model
- Inventory displayed cleanly with enrichment
- Costs aggregated from inventory + work items
- Unknown/flagged items highlighted

---

## Phase 6: Polish & Production Readiness (Post-MVP)

**Goal:** Add edit capabilities, change tracking, robustness

**Duration:** 2-3 days

**Note:** This phase is optional for MVP. MVP workflow is: fix source file → re-upload → re-run.

### Deliverables (Post-MVP)

#### 6.1 Edit Capabilities

```python
# Add to InventoryStore
def add_item_manual(self, inventory_type: str, data: Dict,
                   entity: str, added_by: str) -> str
def edit_item(self, item_id: str, updates: Dict, edited_by: str) -> bool
def remove_item(self, item_id: str, reason: str, removed_by: str) -> bool
def restore_item(self, item_id: str) -> bool
```

#### 6.2 Change Tracking

```python
@dataclass
class ChangeRecord:
    item_id: str
    action: str  # add, edit, remove, restore
    changes: Dict  # {field: {old: X, new: Y}}
    changed_by: str
    changed_at: datetime
    reason: str

class InventoryStore:
    def get_change_history(self, item_id: str = None) -> List[ChangeRecord]
```

#### 6.3 Freshness Tracking

```python
# Warn when reasoning is stale
if inventory_store.last_modified > reasoning_store.generated_at:
    print("⚠️ Inventory changed since last analysis. Re-run reasoning?")
```

#### 6.4 Interactive Mode Updates

```
> list apps
Applications (33 total):
  I-APP-001: Duck Creek Policy [CRITICAL] - Duck Creek v12
  I-APP-002: Majesco Policy [CRITICAL] - Majesco v2023.2
  ...

> show I-APP-001
Application: Duck Creek Policy
  Vendor: Duck Creek
  Version: 12
  Cost: $546,257
  Enrichment: vertical_specific ("Insurance policy admin")
  Status: active
  Source: ToltIQ_Apps.xlsx (import)

> remove I-APP-005 "Deprecated per CTO call"
Removed I-APP-005: Legacy Claims Tool
  Reason: Deprecated per CTO call

> add app "New Claims Portal" vendor="Acme" cost=50000
Added I-APP-034: New Claims Portal
  Source: manual
```

### Exit Criteria (Post-MVP)

- Users can add/edit/remove inventory items
- All changes tracked with audit trail
- Stale reasoning warnings work
- Interactive commands functional

---

## File Structure

```
it-diligence-agent/
├── stores/
│   ├── inventory_store.py     # NEW: InventoryStore
│   ├── fact_store.py          # UPDATED: Content-based IDs
│   └── id_generator.py        # NEW: Shared ID generation
│
├── tools_v2/
│   ├── parsers/
│   │   ├── word_parser.py     # NEW
│   │   ├── excel_parser.py    # NEW
│   │   ├── markdown_parser.py # NEW (from deterministic_parser.py)
│   │   ├── type_detector.py   # NEW
│   │   └── schema_validator.py # NEW
│   │
│   ├── enrichment/
│   │   ├── app_intelligence.py # NEW
│   │   ├── known_apps.py       # NEW: Reference DB loader
│   │   └── industry_expectations.py # NEW
│   │
│   ├── file_router.py         # NEW
│   ├── inventory_context.py   # NEW: Prepare for reasoning
│   └── ...existing tools...
│
├── data/
│   ├── known_applications.json  # NEW
│   └── industry_expectations.json # NEW
│
├── config/
│   ├── inventory_schemas.py   # NEW
│   └── ...existing config...
│
├── prompts/
│   └── v2_*_reasoning_prompt.py # UPDATED: Handle I- and F- citations
│
└── docs/
    └── INVENTORY_SYSTEM_UPGRADE_PLAN.md  # This document
```

---

## Migration Notes

### Existing Runs

- Existing fact-based runs remain valid (archived)
- New runs use new data model
- No migration of old data required

### Backward Compatibility

- Keep old FactStore interface working for transition period
- Discovery agents still work for unstructured docs
- Gradual adoption: can run old or new pipeline

### Rollback Plan

- Keep old code in separate branch
- Feature flag to toggle between old/new pipeline
- If issues arise, revert to old pipeline

---

## Success Metrics

| Metric | Before | After |
|--------|--------|-------|
| Inventory extraction accuracy | ~95% (LLM variance) | 100% (deterministic) |
| Re-run consistency | Variable | Identical |
| Time to ingest 100 apps | ~60s (LLM) | <1s (parse) |
| Cost to ingest 100 apps | ~$0.02 | $0.00 |
| Unknown apps flagged | No | Yes |
| Industry context | Limited | Full |
| Edit without re-run | No | Yes (post-MVP) |

---

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Header detection fails | Medium | Medium | Fallback to LLM, user review |
| Unknown apps not researched | Low | Low | LLM fallback for enrichment |
| Large inventory OOMs reasoning | Low | High | Batching, summarization |
| Reasoning prompts confused | Medium | Medium | Clear instructions, testing |
| Re-import loses manual edits | Medium | Medium | Smart merge logic, warnings |

---

## Timeline Summary

| Phase | Focus | Duration | MVP? |
|-------|-------|----------|------|
| 1 | Foundation (InventoryStore, IDs) | 2-3 days | Yes |
| 2 | Parsers & Router | 3-4 days | Yes |
| 3 | Application Intelligence | 2-3 days | Yes |
| 4 | Pipeline Integration | 3-4 days | Yes |
| 5 | Reports & Exports | 2-3 days | Yes |
| 6 | Edit & Polish | 2-3 days | No (post-MVP) |

**MVP Total: 12-17 days**
**Full System: 14-20 days**

---

## Next Steps

1. Review and approve this plan
2. Start Phase 1: Create InventoryStore with content-based IDs
3. Test foundation before proceeding to parsers

---

*Document version: 1.0*
*Last updated: 2025-01-29*
