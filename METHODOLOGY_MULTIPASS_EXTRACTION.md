# Multi-Pass Extraction Methodology
## IT Due Diligence Agent - Exhaustive Fact Extraction System

---

## Executive Summary

This document defines the **Multi-Pass Extraction System** designed to capture exhaustive, granular facts from IT due diligence source documents. The system replaces single-pass extraction (limited to ~30 facts per domain) with a three-pass architecture capable of extracting 500+ line-item facts with full traceability.

**Key Principle:** Every statement in the final diligence report must trace back to a granular fact, and every granular fact must trace back to a source quote.

---

## The Problem

### Current State (Single-Pass)

```
┌─────────────────────────────────────────────────────────────────┐
│  Document Input                                                  │
│  "The company runs 47 EC2 instances across 3 regions,           │
│   23 S3 buckets, 8 RDS databases, and 12 Lambda functions..."   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  Single-Pass Extraction (30 iteration limit)                    │
│                                                                  │
│  Output: 1 fact                                                  │
│  "AWS cloud infrastructure with multiple services"              │
└─────────────────────────────────────────────────────────────────┘
```

**What's Lost:**
- 47 EC2 instances (count)
- 3 regions (geographic distribution)
- 23 S3 buckets (storage inventory)
- 8 RDS databases (database inventory)
- 12 Lambda functions (serverless inventory)

### Target State (Multi-Pass)

```
┌─────────────────────────────────────────────────────────────────┐
│  Same Document Input                                             │
└─────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
   ┌─────────┐          ┌─────────┐          ┌─────────┐
   │ Pass 1  │          │ Pass 2  │          │ Pass 3  │
   │ Systems │          │ Details │          │ Validate│
   └─────────┘          └─────────┘          └─────────┘
        │                     │                     │
        ▼                     ▼                     ▼
   ┌─────────┐          ┌─────────┐          ┌─────────┐
   │ 1 fact  │          │ 5 facts │          │ Verified│
   │ "AWS"   │          │ w/counts│          │ Complete│
   └─────────┘          └─────────┘          └─────────┘
```

**Output: 6 facts with full granularity**

---

## L1: High-Level Architecture

### Three-Pass Extraction Model

| Pass | Name | Purpose | Output Type |
|------|------|---------|-------------|
| **Pass 1** | System Discovery | Identify WHAT exists | Platforms, vendors, major systems |
| **Pass 2** | Detail Extraction | Capture HOW MUCH/MANY | Counts, versions, configs, costs |
| **Pass 3** | Validation | Verify CONSISTENCY | Reconciliation flags, completeness |

### Data Flow

```
┌──────────────────────────────────────────────────────────────────────────┐
│                         MULTI-PASS EXTRACTION                             │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│   SOURCE DOCUMENTS                                                        │
│   ┌─────────┐ ┌─────────┐ ┌─────────┐                                    │
│   │ IT Deck │ │ Sec Rpt │ │ Vendor  │                                    │
│   │  .pdf   │ │  .pdf   │ │  List   │                                    │
│   └────┬────┘ └────┬────┘ └────┬────┘                                    │
│        └───────────┼───────────┘                                          │
│                    ▼                                                      │
│   ┌────────────────────────────────────────────────────────────────────┐ │
│   │                     PASS 1: SYSTEM DISCOVERY                        │ │
│   │   "What platforms, vendors, and systems exist?"                     │ │
│   │                                                                     │ │
│   │   Output: System Registry                                           │ │
│   │   ┌─────────────────────────────────────────────────────────────┐  │ │
│   │   │ SYS-001: AWS Cloud Platform                                  │  │ │
│   │   │ SYS-002: NetSuite ERP                                        │  │ │
│   │   │ SYS-003: Salesforce CRM                                      │  │ │
│   │   │ SYS-004: On-Prem Data Center (Dallas)                        │  │ │
│   │   │ ...                                                          │  │ │
│   │   └─────────────────────────────────────────────────────────────┘  │ │
│   └────────────────────────────────────────────────────────────────────┘ │
│                    │                                                      │
│                    ▼                                                      │
│   ┌────────────────────────────────────────────────────────────────────┐ │
│   │                     PASS 2: DETAIL EXTRACTION                       │ │
│   │   "For each system, extract counts, versions, configs, costs"      │ │
│   │                                                                     │ │
│   │   Output: Granular Facts Store (Line Items)                         │ │
│   │   ┌─────────────────────────────────────────────────────────────┐  │ │
│   │   │ GF-001: AWS EC2 Instances | Count: 47 | Regions: 3          │  │ │
│   │   │ GF-002: AWS S3 Buckets | Count: 23 | Total Size: 4.2 TB     │  │ │
│   │   │ GF-003: AWS RDS Databases | Count: 8 | Engine: PostgreSQL   │  │ │
│   │   │ GF-004: AWS Lambda Functions | Count: 12 | Runtime: Python  │  │ │
│   │   │ GF-005: NetSuite Users | Count: 145 | License: Enterprise   │  │ │
│   │   │ GF-006: NetSuite Customizations | Count: 87 | Type: Scripts │  │ │
│   │   │ ...                                                          │  │ │
│   │   └─────────────────────────────────────────────────────────────┘  │ │
│   └────────────────────────────────────────────────────────────────────┘ │
│                    │                                                      │
│                    ▼                                                      │
│   ┌────────────────────────────────────────────────────────────────────┐ │
│   │                     PASS 3: VALIDATION                              │ │
│   │   "Does the detail data reconcile with summary statements?"        │ │
│   │                                                                     │ │
│   │   Output: Validation Report                                         │ │
│   │   ┌─────────────────────────────────────────────────────────────┐  │ │
│   │   │ ✓ AWS: Summary says "cloud infrastructure" - 4 detail items │  │ │
│   │   │ ✓ NetSuite: Summary says "ERP system" - 2 detail items      │  │ │
│   │   │ ⚠ Salesforce: Summary says "200 users" - Detail shows 187   │  │ │
│   │   │ ✗ Data Center: Summary mentioned - No details extracted     │  │ │
│   │   └─────────────────────────────────────────────────────────────┘  │ │
│   └────────────────────────────────────────────────────────────────────┘ │
│                                                                           │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## L2: Pass Specifications

### Pass 1: System Discovery

**Objective:** Create a registry of all systems, platforms, and technologies mentioned in source documents.

**Extraction Focus:**
- Platform names (AWS, Azure, NetSuite, Salesforce)
- Vendor names (Microsoft, Oracle, Cisco)
- System categories (ERP, CRM, HRIS, Security)
- Infrastructure components (Data centers, Networks, Cloud regions)

**Output Schema:**
```json
{
  "system_id": "SYS-a3f2",
  "name": "AWS Cloud Platform",
  "category": "cloud_infrastructure",
  "vendor": "Amazon Web Services",
  "domain": "infrastructure",
  "first_mentioned": "IT Overview Deck, Page 3",
  "evidence_quote": "The company operates primarily on AWS...",
  "status": "documented"
}
```

**Iteration Limit:** 50 per domain (increased from 30)

**Success Criteria:**
- All major systems mentioned in docs are captured
- Each system has at least one evidence quote
- No duplicate systems (hash-based ID prevents this)

---

### Pass 2: Detail Extraction

**Objective:** For each system identified in Pass 1, extract granular line-item facts.

**Extraction Focus:**
- **Counts:** Number of instances, users, licenses, records
- **Versions:** Software versions, release dates, patch levels
- **Configurations:** Settings, customizations, integrations
- **Capacities:** Storage sizes, throughput, limits
- **Costs:** License costs, cloud spend, support fees
- **Dates:** Implementation dates, renewal dates, EOL dates

**Output Schema:**
```json
{
  "granular_fact_id": "GF-b7c1",
  "parent_system_id": "SYS-a3f2",
  "fact_type": "count",
  "item": "EC2 Instances",
  "value": 47,
  "unit": "instances",
  "context": {
    "regions": ["us-east-1", "us-west-2", "eu-west-1"],
    "instance_types": "mixed (t3, m5, c5)"
  },
  "evidence_quote": "...47 EC2 instances across 3 regions...",
  "source_document": "IT Overview Deck.pdf",
  "source_page": 12,
  "extracted_at": "2026-01-18T19:30:00Z"
}
```

**Iteration Limit:** 100 per domain

**Fact Types:**
| Type | Description | Example |
|------|-------------|---------|
| `count` | Numeric quantity | 47 EC2 instances |
| `version` | Software version | NetSuite 2024.1 |
| `capacity` | Size/throughput | 4.2 TB storage |
| `cost` | Dollar amount | $45,000/month |
| `date` | Temporal reference | Renewal: March 2027 |
| `config` | Setting/option | MFA enabled |
| `status` | State indicator | Active, Deprecated |
| `integration` | Connection | Salesforce ↔ NetSuite |

---

### Pass 3: Validation & Reconciliation

**Objective:** Cross-check granular facts against summary statements; flag inconsistencies.

**Validation Checks:**

1. **Count Reconciliation**
   - Summary: "approximately 50 servers"
   - Detail sum: 47 servers
   - Variance: 6% → ✓ PASS (within 15% tolerance)

2. **Coverage Check**
   - Systems mentioned in summaries: 12
   - Systems with granular details: 10
   - Coverage: 83% → ✓ PASS (above 80% threshold)

3. **Orphan Detection**
   - Granular facts without parent system: Flag for review
   - Systems without any granular facts: Flag as gap

4. **Consistency Check**
   - Same item mentioned in multiple places
   - Values should match or variance explained

**Output Schema:**
```json
{
  "validation_id": "VAL-001",
  "check_type": "count_reconciliation",
  "system_id": "SYS-a3f2",
  "summary_statement": "approximately 50 EC2 instances",
  "detail_sum": 47,
  "variance_pct": 6.0,
  "threshold_pct": 15.0,
  "status": "pass",
  "notes": "Within acceptable tolerance"
}
```

---

## L3: Implementation Details

### 3.1 Granular Facts Store

**New File:** `tools_v2/granular_facts_store.py`

**Data Structure:**
```python
@dataclass
class GranularFact:
    granular_fact_id: str      # GF-xxxx (hash-based)
    parent_system_id: str      # Links to System Registry
    domain: str                # infrastructure, applications, etc.
    category: str              # servers, databases, users, etc.
    fact_type: str             # count, version, capacity, cost, etc.
    item: str                  # What this fact describes
    value: Any                 # The actual value (number, string, etc.)
    unit: Optional[str]        # instances, users, TB, USD, etc.
    context: Dict[str, Any]    # Additional context (regions, types, etc.)
    evidence_quote: str        # Exact quote from source
    source_document: str       # Filename
    source_page: Optional[int] # Page number if available
    confidence: float          # 0.0 to 1.0
    extracted_at: str          # ISO timestamp
```

**Storage Format:**
```
sessions/
└── {session_id}/
    ├── fact_store.json           # Existing summary facts
    ├── reasoning_store.json      # Existing risks/work items
    ├── system_registry.json      # NEW: Pass 1 output
    ├── granular_facts.json       # NEW: Pass 2 output
    ├── validation_report.json    # NEW: Pass 3 output
    └── exports/
        ├── granular_facts.xlsx   # Excel export
        ├── granular_facts.csv    # CSV export
        └── full_inventory.xlsx   # Combined workbook
```

---

### 3.2 Excel Export Structure

**Workbook: `full_inventory.xlsx`**

| Sheet Name | Contents |
|------------|----------|
| `Summary` | High-level metrics, pass statistics |
| `Systems` | System Registry from Pass 1 |
| `Infrastructure` | Granular facts for infra domain |
| `Applications` | Granular facts for apps domain |
| `Security` | Granular facts for security domain |
| `Organization` | Granular facts for org domain |
| `Validation` | Reconciliation results |
| `Gaps` | Items with missing details |

**Column Structure (Granular Facts sheets):**
```
| ID | System | Category | Item | Value | Unit | Evidence | Source | Page | Confidence |
```

---

### 3.3 Validation Pass Logic

```python
def validate_extraction(
    system_registry: List[System],
    granular_facts: List[GranularFact],
    summary_facts: List[Fact]
) -> ValidationReport:
    """
    Cross-check granular extraction against summaries.

    Returns:
        ValidationReport with pass/fail status and flags
    """

    results = []

    # Check 1: Every system should have granular details
    for system in system_registry:
        details = [gf for gf in granular_facts
                   if gf.parent_system_id == system.system_id]

        if len(details) == 0:
            results.append(ValidationResult(
                check="system_coverage",
                status="fail",
                message=f"System {system.name} has no granular details",
                severity="high"
            ))
        elif len(details) < 3:
            results.append(ValidationResult(
                check="system_coverage",
                status="warn",
                message=f"System {system.name} has only {len(details)} details",
                severity="medium"
            ))

    # Check 2: Numeric reconciliation
    for summary in summary_facts:
        if has_numeric_claim(summary):
            claimed_value = extract_number(summary)
            actual_sum = sum_granular_for_item(granular_facts, summary.item)

            variance = abs(claimed_value - actual_sum) / claimed_value

            if variance > VARIANCE_ALERT_THRESHOLD:
                results.append(ValidationResult(
                    check="count_reconciliation",
                    status="fail" if variance > 0.50 else "warn",
                    message=f"{summary.item}: claimed {claimed_value}, found {actual_sum}",
                    variance_pct=variance * 100
                ))

    # Check 3: Orphan detection
    for gf in granular_facts:
        if gf.parent_system_id not in [s.system_id for s in system_registry]:
            results.append(ValidationResult(
                check="orphan_detection",
                status="warn",
                message=f"Granular fact {gf.granular_fact_id} has no parent system"
            ))

    return ValidationReport(results=results)
```

---

### 3.4 Multi-Pass Orchestrator

**New File:** `agents_v2/multipass_orchestrator.py`

```python
class MultiPassOrchestrator:
    """
    Orchestrates the three-pass extraction process.
    """

    def run_extraction(self, documents: List[Document]) -> ExtractionResult:
        """
        Execute all three passes in sequence.
        """

        # Pass 1: System Discovery
        print("=" * 60)
        print("PASS 1: SYSTEM DISCOVERY")
        print("=" * 60)
        system_registry = self.run_pass_1(documents)
        print(f"  → Discovered {len(system_registry)} systems")

        # Pass 2: Detail Extraction
        print("=" * 60)
        print("PASS 2: DETAIL EXTRACTION")
        print("=" * 60)
        granular_facts = self.run_pass_2(documents, system_registry)
        print(f"  → Extracted {len(granular_facts)} granular facts")

        # Pass 3: Validation
        print("=" * 60)
        print("PASS 3: VALIDATION & RECONCILIATION")
        print("=" * 60)
        validation_report = self.run_pass_3(system_registry, granular_facts)
        print(f"  → {validation_report.pass_count} passed, "
              f"{validation_report.warn_count} warnings, "
              f"{validation_report.fail_count} failures")

        return ExtractionResult(
            system_registry=system_registry,
            granular_facts=granular_facts,
            validation_report=validation_report
        )
```

---

## Metrics & Success Criteria

### Extraction Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Facts per document | 50+ | Count of granular facts / documents |
| System coverage | 100% | Systems with ≥1 granular fact |
| Detail depth | 5+ per system | Avg granular facts per system |
| Evidence rate | 100% | Facts with source quotes |
| Validation pass rate | 90%+ | Checks passed / total checks |

### Quality Gates

Before finalizing extraction:

1. **Minimum Facts:** At least 100 granular facts extracted
2. **Domain Coverage:** All 6 domains have facts
3. **Validation Pass Rate:** ≥85% of checks pass
4. **No Critical Failures:** Zero "fail" status on reconciliation

---

## User Access Points

### Streamlit UI Additions

1. **Granular Facts Tab**
   - Searchable, filterable table of all line-item facts
   - Group by system, domain, or fact type
   - Click to see source evidence

2. **Export Buttons**
   - "Download Excel" → Full workbook with all sheets
   - "Download CSV" → Flat file of all granular facts
   - "Download JSON" → Machine-readable format

3. **Validation Dashboard**
   - Pass/Warn/Fail counts
   - Clickable issues to review
   - "Fix suggestions" for common problems

4. **Reconciliation View**
   - Side-by-side: Summary claim vs. granular sum
   - Variance highlighting
   - Drill-down to source facts

---

## File Manifest

| File | Purpose | Status |
|------|---------|--------|
| `config_v2_updates.py` | New configuration settings | Created |
| `tools_v2/granular_facts_store.py` | Line-item facts storage | To Build |
| `tools_v2/system_registry.py` | Pass 1 system catalog | To Build |
| `tools_v2/validation_engine.py` | Pass 3 reconciliation | To Build |
| `tools_v2/excel_exporter.py` | Multi-sheet Excel export | To Build |
| `agents_v2/multipass_orchestrator.py` | Three-pass coordinator | To Build |
| `agents_v2/discovery/detail_extractor.py` | Pass 2 agent | To Build |

---

## Next Steps

1. **Build L3 Components** - Implement files listed above
2. **Integrate with Existing Pipeline** - Hook into main_v2.py
3. **Update Streamlit UI** - Add granular facts tab and exports
4. **Test with Sample Docs** - Verify 500+ facts extraction
5. **Create Golden Baseline** - For regression testing

---

*Document Created: January 18, 2026*
*Version: 1.0*
*Author: Claude Code (Opus 4.5)*
