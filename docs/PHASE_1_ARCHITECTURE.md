# Phase 1: Foundation & Architecture Documentation

**Version:** 1.0
**Created:** Phase 1 of 115-Point Enhancement Plan
**Purpose:** Establish architectural foundation for all enhancements

---

## 1. AnalysisStore Class Structure (Point 1)

### Core Data Structure

The `AnalysisStore` class (defined in `tools/analysis_tools.py` at line 1890) is a dataclass that serves as the central storage for all analysis findings.

```
AnalysisStore
├── Application Inventory (Phase 4)
│   ├── applications: List[Dict]              # Target company apps
│   ├── capability_coverage: List[Dict]       # 13 capability areas
│   ├── buyer_applications: List[Dict]        # Buyer's apps (Phase 12)
│   └── application_overlaps: List[Dict]      # Target vs Buyer (Phase 12)
│
├── Four-Lens Framework
│   ├── current_state: List[Dict]             # Lens 1
│   ├── risks: List[Dict]                     # Lens 2
│   ├── strategic_considerations: List[Dict]  # Lens 3
│   ├── work_items: List[Dict]                # Lens 4
│   └── recommendations: List[Dict]           # Lens 4
│
├── Supporting Data
│   ├── assumptions: List[Dict]
│   ├── gaps: List[Dict]
│   ├── questions: List[Dict]
│   ├── domain_summaries: Dict[str, Dict]
│   └── reasoning_chains: Dict[str, List[Dict]]
│
├── Metadata
│   ├── run_id: Optional[str]
│   ├── document_ids: List[str]
│   ├── executive_summary: Optional[Dict]
│   └── _id_counters: Dict[str, int]         # ID generation
│
└── Database (Optional)
    ├── _db: Any                              # Database connection
    └── _repository: Any                      # Repository instance
```

### Extension Points for New Data Types

To add new data types to AnalysisStore:

1. **Add storage field** in the class definition:
   ```python
   new_data_type: List[Dict] = field(default_factory=list)
   ```

2. **Add ID counter** in `_id_counters`:
   ```python
   "new_type": 0  # Counter initialization
   ```

3. **Add ID prefix** in `_next_id()`:
   ```python
   "new_type": "NT"  # e.g., NT-001, NT-002
   ```

4. **Add handler** in `execute_tool()`:
   ```python
   elif tool_name == "record_new_type":
       # Duplicate check, defaults, storage
   ```

5. **Add getter methods** for retrieval and filtering.

### Current ID Prefixes

| Type | Prefix | Example |
|------|--------|---------|
| application | APP | APP-001 |
| capability | CAP | CAP-001 |
| buyer_application | BAPP | BAPP-001 |
| overlap | OVL | OVL-001 |
| assumption | A | A-001 |
| gap | G | G-001 |
| question | Q | Q-001 |
| risk | R | R-001 |
| work_item | WI | WI-001 |
| recommendation | REC | REC-001 |
| current_state | CS | CS-001 |
| strategic_consideration | SC | SC-001 |

### Planned New ID Prefixes (for Enhancement Plan)

| Type | Prefix | Example | Phase |
|------|--------|---------|-------|
| business_context | BC | BC-001 | 7-8 |
| eol_assessment | EOL | EOL-001 | 9-10 |
| technical_debt | TD | TD-001 | 9-10 |
| contract | CON | CON-001 | 11-12 |

---

## 2. Current Enum Patterns (Point 2)

### Enum Naming Convention

All enums follow this pattern:
- **UPPERCASE_SNAKE_CASE** for the variable name
- **Title_Case_With_Underscores** for enum values
- Values are Python lists of strings (not Python Enum classes)

### Enum Categories

#### A. Domain & Framework Enums

| Enum | Purpose | Values |
|------|---------|--------|
| `ALL_DOMAINS` | Analysis domains | infrastructure, network, cybersecurity, applications, organization, identity_access, cross-domain |
| `CAPABILITY_AREAS` | Business capabilities | 13 areas (finance_accounting, human_resources, etc.) |
| `EVIDENCE_TYPES` | Source evidence classification | direct_statement, logical_inference, pattern_based |
| `CONFIDENCE_LEVELS` | Finding confidence | high, medium, low |
| `GAP_TYPES` | Gap categorization | missing_document, incomplete_detail, unclear_statement, unstated_critical |

#### B. Application Inventory Enums

| Enum | Purpose | Values Count |
|------|---------|--------------|
| `APPLICATION_CATEGORIES` | App classification | 18 categories |
| `HOSTING_MODELS` | Deployment model | 7 (includes Unknown) |
| `SUPPORT_STATUS` | Vendor support | 7 (includes Unknown) |
| `LICENSE_TYPES` | Licensing model | 8 (includes Unknown) |
| `CUSTOMIZATION_LEVELS` | Customization degree | 7 (includes Unknown) |
| `DISCOVERY_SOURCES` | How app was found | 8 sources |
| `BUSINESS_CRITICALITY` | Business importance | 5 (includes Unknown) |

#### C. Data Classification Enums

| Enum | Purpose | Values Count |
|------|---------|--------------|
| `PII_TYPES` | PII categories | 16 types |
| `PHI_TYPES` | PHI categories (HIPAA) | 10 types |
| `PCI_TYPES` | PCI data types | 8 types |
| `DATA_RESIDENCY_LOCATIONS` | Data locations | 12 (includes Unknown) |

#### D. Buyer Comparison Enums

| Enum | Purpose | Values |
|------|---------|--------|
| `OVERLAP_TYPES` | Target vs Buyer | Same_Product, Same_Category_Different_Vendor, Target_Only, Complementary, Unknown |
| `BUYER_APP_SOURCE` | Info source | 6 sources |

#### E. Capability Coverage Enums

| Enum | Purpose | Values Count |
|------|---------|--------------|
| `COVERAGE_STATUS` | Documentation coverage | 5 |
| `BUSINESS_RELEVANCE` | Relevance to business | 5 |
| `QUESTION_TARGETS` | Who to ask | 11 targets |
| `CAPABILITY_MATURITY` | Maturity level | 5 (includes Unknown) |
| `INTEGRATION_COMPLEXITY` | Complexity level | 5 (includes Unknown) |

### Consistency Standards for New Enums

1. **Always include "Unknown"** for fields where information may not be available
2. **Use Title_Case_With_Underscores** for values
3. **Keep values semantic and self-documenting**
4. **Document each enum with a comment block explaining its purpose**
5. **Group related enums together with section headers**

---

## 3. Existing Tools Map (Point 3)

### Tool Categories and Relationships

```
ANALYSIS_TOOLS (List in analysis_tools.py)
│
├── APPLICATION INVENTORY TOOLS
│   ├── record_application          → AnalysisStore.applications
│   ├── record_capability_coverage  → AnalysisStore.capability_coverage
│   ├── record_buyer_application    → AnalysisStore.buyer_applications
│   └── record_application_overlap  → AnalysisStore.application_overlaps
│
├── FOUR-LENS FRAMEWORK TOOLS
│   ├── create_current_state_entry  → AnalysisStore.current_state
│   ├── identify_risk               → AnalysisStore.risks
│   ├── create_strategic_consideration → AnalysisStore.strategic_considerations
│   ├── create_work_item            → AnalysisStore.work_items
│   └── create_recommendation       → AnalysisStore.recommendations
│
├── SUPPORTING TOOLS
│   ├── log_assumption              → AnalysisStore.assumptions
│   ├── flag_gap                    → AnalysisStore.gaps
│   └── flag_question               → AnalysisStore.questions
│
├── COMPLETION TOOLS
│   ├── complete_analysis           → AnalysisStore.domain_summaries
│   └── create_executive_summary    → AnalysisStore.executive_summary
│
└── CROSS-DOMAIN TOOLS
    └── identify_cross_domain_dependency → AnalysisStore.risks (as cross-domain)
```

### Tool Input Pattern

All tools follow a consistent schema pattern:

```python
{
    "name": "tool_name",
    "description": """Multi-line description with:
        - CRITICAL USAGE RULES
        - When to use
        - Required fields explanation""",
    "input_schema": {
        "type": "object",
        "properties": {
            # Field definitions with types, enums, descriptions
        },
        "required": ["list", "of", "required", "fields"]
    }
}
```

### Naming Conventions for New Tools (Point 6)

| Pattern | Purpose | Examples |
|---------|---------|----------|
| `record_*` | Capture structured data | record_application, record_contract |
| `assess_*` | Evaluate/analyze data | assess_application_eol, assess_technical_debt |
| `create_*` | Generate findings | create_current_state_entry, create_work_item |
| `flag_*` | Surface issues | flag_gap, flag_question |
| `log_*` | Record observations | log_assumption |
| `export_*` | Output generation | export_to_excel (function, not tool) |

---

## 4. Output Directory Structure (Point 4)

### Current Structure

```
/it-diligence-agent 2/
├── output/                    # Analysis outputs (existing)
│   ├── [run_id]/              # Per-run outputs
│   │   ├── findings.json
│   │   └── findings.xlsx
│   └── ...
│
├── docs/                      # Documentation (existing)
│   ├── APPLICATIONS_AGENT_COMPLETE_REFERENCE.md
│   ├── APPLICATION_REVIEW_PROCESS_WALKTHROUGH.md
│   ├── ENHANCEMENT_IMPLEMENTATION_PLAN.md
│   └── ...
│
└── tools/                     # Tool implementations (existing)
    ├── analysis_tools.py
    ├── excel_export.py        # Existing Excel export
    ├── costing_tools.py
    └── question_workflow.py
```

### Proposed Additions

```
/it-diligence-agent 2/
├── output/
│   └── [run_id]/
│       ├── findings.json
│       ├── findings.xlsx
│       ├── applications_inventory.xlsx   # NEW: Dedicated app export
│       ├── capability_matrix.xlsx        # NEW: Capability coverage
│       └── integration_analysis.xlsx     # NEW: Buyer comparison
│
├── docs/
│   ├── architecture/                     # NEW: Architecture docs
│   │   ├── PHASE_1_ARCHITECTURE.md
│   │   └── DATA_FLOW_DIAGRAMS.md
│   │
│   ├── methodology/                      # NEW: AI methodology
│   │   ├── AI_METHODOLOGY.md
│   │   ├── PROMPT_CHANGELOG.md
│   │   └── DOMAIN_SUMMARIES.md
│   │
│   └── ... (existing docs)
│
└── tools/
    ├── constants.py                      # NEW: Shared constants
    ├── export_tools.py                   # NEW: Enhanced exports
    └── ... (existing tools)
```

---

## 5. Shared Constants File (Point 5)

Create `/tools/constants.py` with cross-cutting values:

```python
"""
Shared Constants for IT Due Diligence Agent

Cross-cutting values used across multiple modules.
Centralizes "Unknown", "N/A", and other standard values.
"""

# =============================================================================
# UNKNOWN/N/A STANDARDS
# =============================================================================

# Standard "Unknown" value for enum fields
UNKNOWN = "Unknown"

# Standard "Not Applicable" value
NOT_APPLICABLE = "Not_Applicable"

# Standard "None" representation for optional strings
NONE_PROVIDED = "None_Provided"

# =============================================================================
# FIELD NOT DOCUMENTED MARKERS
# =============================================================================

# Use when a field couldn't be populated from available docs
FIELD_NOT_DOCUMENTED = "[Not documented]"

# Use when explicitly stated as not available
EXPLICITLY_UNAVAILABLE = "[Explicitly stated as unavailable]"

# =============================================================================
# PROMPT VERSIONING
# =============================================================================

PROMPT_VERSIONS = {
    "applications_prompt": "1.1",
    "identity_access_prompt": "1.0",
    "infrastructure_prompt": "1.0",
    "network_prompt": "1.0",
    "cybersecurity_prompt": "1.0",
    "organization_prompt": "1.0",
    "dd_reasoning_framework": "2.0"
}

# =============================================================================
# OUTPUT FORMATTING
# =============================================================================

# Excel column widths by type
EXCEL_COLUMN_WIDTHS = {
    "id": 10,
    "name": 30,
    "description": 50,
    "evidence": 60,
    "status": 15,
    "date": 12,
    "boolean": 8
}

# Severity/Priority color coding (hex)
SEVERITY_COLORS = {
    "critical": "FF0000",  # Red
    "high": "FFA500",      # Orange
    "medium": "FFFF00",    # Yellow
    "low": "90EE90"        # Light green
}

# =============================================================================
# VALIDATION THRESHOLDS
# =============================================================================

# Minimum quote length for evidence validation
MIN_QUOTE_LENGTH = 10

# Fuzzy match threshold for duplicate detection
DUPLICATE_THRESHOLD = 0.85

# Evidence density warning threshold (findings per 1000 chars)
EVIDENCE_DENSITY_WARNING = 2.0
```

---

## 6. Tool-to-AnalysisStore Data Flow Pattern (Point 7)

### Standard Flow

```
┌─────────────────┐
│   Agent calls   │
│   tool_name()   │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│     AnalysisStore.execute_tool()        │
│  ┌─────────────────────────────────┐    │
│  │ 1. Validate tool_input is dict  │    │
│  │ 2. Check for duplicates         │    │
│  │ 3. Generate unique ID           │    │
│  │ 4. Add timestamp                │    │
│  │ 5. Apply defaults               │    │
│  │ 6. Store in appropriate list    │    │
│  │ 7. Return status + ID           │    │
│  └─────────────────────────────────┘    │
└────────┬────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│           Storage Lists                  │
│  ┌──────────────┐  ┌──────────────┐     │
│  │ applications │  │    risks     │     │
│  │    [Dict]    │  │    [Dict]    │     │
│  └──────────────┘  └──────────────┘     │
│  ┌──────────────┐  ┌──────────────┐     │
│  │ capabilities │  │  work_items  │     │
│  │    [Dict]    │  │    [Dict]    │     │
│  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│         Retrieval Methods               │
│  get_application_inventory()            │
│  get_capability_summary()               │
│  get_standalone_risks()                 │
│  get_all_follow_up_questions()          │
│  validate_application_completeness()    │
└────────┬────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│         Export Functions                │
│  export_findings_to_excel()             │
│  (NEW) export_applications_to_excel()   │
│  (NEW) export_contracts_to_excel()      │
└─────────────────────────────────────────┘
```

### Adding a New Tool (Pattern)

```python
# 1. Define enum (if needed) at top of analysis_tools.py
NEW_ENUM = [
    "Value_One",
    "Value_Two",
    "Unknown"  # Always include
]

# 2. Add tool definition to ANALYSIS_TOOLS list
{
    "name": "record_new_type",
    "description": """Description with usage rules...""",
    "input_schema": {
        "type": "object",
        "properties": {
            "field_one": {"type": "string", "description": "..."},
            "field_two": {"type": "string", "enum": NEW_ENUM},
            "source_evidence": SOURCE_EVIDENCE_SCHEMA  # Reuse shared schema
        },
        "required": ["field_one", "source_evidence"]
    }
}

# 3. Add storage to AnalysisStore class
new_types: List[Dict] = field(default_factory=list)

# 4. Add ID counter
_id_counters: Dict[str, int] = field(default_factory=lambda: {
    # ... existing ...
    "new_type": 0
})

# 5. Add ID prefix in _next_id()
prefix = {
    # ... existing ...
    "new_type": "NT"
}

# 6. Add handler in execute_tool()
elif tool_name == "record_new_type":
    # Duplicate check
    for existing in self.new_types:
        if existing.get("field_one") == tool_input.get("field_one"):
            return {"status": "duplicate", "id": existing["id"], ...}

    # Create finding
    finding = {
        "id": self._next_id("new_type"),
        "timestamp": timestamp,
        **tool_input
    }

    # Apply defaults
    if "optional_field" not in finding:
        finding["optional_field"] = []

    # Store
    self.new_types.append(finding)
    return {"status": "recorded", "id": finding["id"], "type": "new_type"}

# 7. Add getter method
def get_new_types(self, filter_field: Optional[str] = None) -> List[Dict]:
    """Get new_types with optional filtering."""
    result = self.new_types.copy()
    if filter_field:
        result = [x for x in result if x.get("some_field") == filter_field]
    return result
```

---

## 7. Test Plan Template (Point 8)

### Template for Each Phase

```markdown
# Test Plan: Phase [N] - [Phase Name]

## Scope
- What functionality is being added/modified

## Pre-requisites
- Existing tests pass (baseline: 246 tests)
- Dependencies installed

## Test Categories

### A. Unit Tests (tools/tests/test_phase_N.py)

| Test ID | Test Name | Description | Expected Result |
|---------|-----------|-------------|-----------------|
| N.1 | test_new_enum_values | Verify enum contains expected values | All values present |
| N.2 | test_new_tool_required_fields | Verify required fields enforced | Error on missing |
| N.3 | test_new_tool_storage | Verify data stored correctly | Data retrievable |
| N.4 | test_new_tool_id_generation | Verify unique IDs generated | Sequential IDs |
| N.5 | test_duplicate_detection | Verify duplicates caught | Returns existing ID |

### B. Integration Tests

| Test ID | Test Name | Description | Expected Result |
|---------|-----------|-------------|-----------------|
| N.10 | test_tool_to_store_flow | End-to-end tool execution | Data in store |
| N.11 | test_export_includes_new_data | Export contains new data | New tab/columns |

### C. Edge Cases

| Test ID | Test Name | Description | Expected Result |
|---------|-----------|-------------|-----------------|
| N.20 | test_unknown_values_handled | Unknown enum values work | Stored as Unknown |
| N.21 | test_empty_optional_fields | Optional fields can be empty | No errors |

## Validation Commands

```bash
# Run all tests
pytest tests/ -v

# Run specific phase tests
pytest tests/test_phase_N.py -v

# Run with coverage
pytest tests/ --cov=tools --cov-report=term-missing
```

## Success Criteria
- [ ] All existing tests pass (246+)
- [ ] All new tests pass
- [ ] No regressions in existing functionality
- [ ] Coverage maintained or improved
```

---

## 8. Existing Excel Export Analysis

The existing `tools/excel_export.py` provides:

- **export_findings_to_excel()**: Main export function
- Worksheets: Summary, Risks, Gaps, Work Items, Recommendations, Questions, Assumptions
- Professional formatting with openpyxl
- Conditional formatting for severity/priority

### Gap Analysis for Enhancement Plan

The current export does NOT include:
- Applications tab (dedicated inventory)
- Capability Coverage matrix
- Buyer Applications
- Overlap Analysis
- Contracts (to be added)
- EOL Assessments (to be added)

Phase 4-6 will extend this or create new export functions.

---

## Summary

Phase 1 establishes:

| Point | Deliverable | Status |
|-------|-------------|--------|
| 1 | AnalysisStore structure documented | ✓ |
| 2 | Enum patterns documented | ✓ |
| 3 | Tools mapped | ✓ |
| 4 | Output directory defined | ✓ |
| 5 | Constants file designed | ✓ |
| 6 | Naming conventions established | ✓ |
| 7 | Data flow documented | ✓ |
| 8 | Test plan template created | ✓ |

**Next Phase:** Phase 2-3 - Unknown/N/A Handling
