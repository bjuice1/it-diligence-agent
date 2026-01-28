# IT Due Diligence System: Critical Architecture Analysis

**Date:** 2026-01-26
**Purpose:** Document system vulnerabilities, strengths, and architectural considerations before further development.

---

## Executive Summary

The system has a sound architectural intent but critical implementation gaps that could result in:
- **Wrong information** being presented as fact
- **Inability to trace** conclusions back to evidence
- **Data corruption** from entity confusion (target vs buyer)

This document catalogs these issues to inform architectural decisions.

---

## Three Funnel Framework

The system should operate as three sequential funnels:

```
FUNNEL 1: LOGGING          FUNNEL 2: ANALYSIS           FUNNEL 3: FINANCE
(Data Collection)          (Understanding)              (Cost Impact)

Facts ──────────────────►  Environment Description  ──► Run Rate
LLM Outputs ────────────►  Risk Analysis            ──► One-Time Costs
Inventories ────────────►  Deal Considerations
Analysis Conclusions ───►  (Benchmarks - future)
```

---

## Funnel 1: Logging — Critical Issues

### Issue 1.1: Source Document Attribution Lost

**Location:** `base_discovery_agent.py:175`, `discovery_tools.py:492`

**Problem:**
```python
# Set ONCE at discovery start
self.current_document_name = document_name

# Only injected if condition met
if tool_name == "create_inventory_entry" and self.current_document_name:
    tool_input["source_document"] = self.current_document_name
```

**Impact:**
- Multi-document analysis → all facts attributed to first document
- Cannot prove which document substantiated which fact
- Partner audit fails

**Severity:** CRITICAL

---

### Issue 1.2: Entity Defaults Silently to Target

**Location:** `discovery_tools.py:501-503`

**Problem:**
```python
if entity not in ("target", "buyer"):
    logger.warning(f"Invalid entity '{entity}', defaulting to 'target'")
    entity = "target"  # SILENT DEFAULT
```

**Impact:**
- Buyer profile with typo (`entity="Buyer"`) → all facts marked as target
- Entire analysis conflates two companies
- Deal team makes decisions on corrupted data

**Severity:** CRITICAL

---

### Issue 1.3: Evidence Quotes Never Validated

**Location:** `discovery_tools.py:542-546`

**Problem:**
```python
if ENABLE_FACT_VALIDATION and exact_quote:
    logger.debug(f"Evidence quote provided: {exact_quote[:50]}...")
    # This validation would need to be done post-discovery with document text
    # ^^^ DEFERRED AND NEVER DONE
```

**Impact:**
- LLM can fabricate quotes
- No downstream validation catches this
- Evidence chain is unverified

**Severity:** HIGH

---

### Issue 1.4: No LLM Call Context Stored

**Location:** `reasoning_tools.py:198-280`

**Problem:** Finding classes (Risk, WorkItem, etc.) store `based_on_facts` but NOT:
- Which LLM model created it
- What temperature was used
- Which prompt version
- Which iteration of the loop
- Full facts text shown to LLM

**Impact:**
- Cannot reproduce findings
- Cannot audit prompt versions
- Cannot debug inconsistent outputs

**Severity:** HIGH

---

### Issue 1.5: Fact Modifications Not Timestamped

**Location:** `fact_store.py:116, 454`

**Problem:**
```python
updated_at: str = ""  # Field exists but NEVER SET
# ...
fact.confidence_score = fact.calculate_confidence()  # No updated_at trigger
```

**Impact:**
- Cannot tell when facts were changed
- Reasoning may use stale facts
- No audit trail of modifications

**Severity:** MEDIUM

---

### Issue 1.6: Duplicate Merge Silently Skips

**Location:** `fact_store.py:1276-1279`

**Problem:**
```python
if fact.fact_id in existing_fact_ids:
    counts["duplicates"] += 1
    logger.warning(f"Duplicate fact ID during merge: {fact.fact_id}")
    continue  # SKIPS THE FACT ENTIRELY
```

**Impact:**
- Better evidence version may be lost
- No record of which version was kept
- Data quality degrades silently

**Severity:** MEDIUM

---

## Funnel 2: Analysis — Critical Issues

### Issue 2.1: Citation Validation OFF by Default

**Location:** `reasoning_tools.py:474-477`

**Problem:**
```python
try:
    from config_v2 import ENABLE_CITATION_VALIDATION
    fail_fast = ENABLE_CITATION_VALIDATION
except ImportError:
    fail_fast = False  # DEFAULTS TO FALSE
```

**Impact:**
- Findings can cite non-existent facts (F-FAKE-999)
- Only warning logged, processing continues
- Reports contain unsupported conclusions

**Severity:** CRITICAL

---

### Issue 2.2: FactStore Can Be None (Complete Bypass)

**Location:** `reasoning_tools.py:445-448`

**Problem:**
```python
if not self.fact_store:
    if fail_fast and fact_ids:
        raise ValueError("...")
    return {"valid": fact_ids, "invalid": [], "validation_rate": 1.0}
    # ^^^ ALL FACTS MARKED VALID IF NO STORE
```

**Impact:**
- If FactStore initialization fails, ALL citations pass
- Complete bypass of evidence verification
- Findings appear valid but have no backing

**Severity:** CRITICAL

---

### Issue 2.3: Conflict Detection Only Checks Vendor

**Location:** `fact_store.py:693-768`

**Problem:**
```python
if target_vendor and buyer_vendor and target_vendor != buyer_vendor:
    conflicts.append({"conflict_type": "vendor_mismatch"})
# Missing: version, deployment, user count, criticality mismatches
```

**Impact:**
- "No conflicts found" when major differences exist
- Version mismatches missed (target v2019, buyer v2016)
- Deployment mismatches missed (on-prem vs cloud)

**Severity:** HIGH

---

### Issue 2.4: Duplicate Detection Uses Weak Heuristics

**Location:** `fact_store.py:1589-1617`

**Problem:**
```python
similarity = 0.5 * jaccard + 0.3 * category_match + 0.2 * details_sim
# "Exchange Server 2019" vs "MS Exchange" = low similarity (different strings)
```

**Impact:**
- Same application with different naming not detected
- Duplicates persist in inventory
- Analysis double-counts

**Severity:** HIGH

---

### Issue 2.5: No Bidirectional Evidence Queries

**Problem:** Can query fact by ID, but cannot:
- Find all facts containing a specific quote
- Find all findings citing a specific fact
- Trace from conclusion → fact → document → quote

**Impact:**
- Evidence chain only works forward, not backward
- Audit queries difficult
- Cannot verify citation accuracy

**Severity:** MEDIUM

---

## Funnel 3: Finance — Pre-requisites

Finance layer (Run Rate, One-Time Costs) not yet built, but will inherit all upstream problems.

**Must be true before building Finance:**

| Requirement | Current State | Risk if Not Fixed |
|-------------|---------------|-------------------|
| Entity (target/buyer) reliable | Defaults silently | Costs attributed to wrong company |
| Source document traceable | Can be lost | Cannot prove cost basis |
| Fact modifications timestamped | Not tracked | Using stale cost data |
| Evidence chain complete | Gaps exist | Cannot justify estimates |

---

## System Strengths

| Strength | Implementation | Value |
|----------|----------------|-------|
| Unique fact IDs | `F-{DOMAIN}-{SEQ}` | Enables citation tracking |
| Evidence quote field | `exact_quote` required | Intent to prove facts |
| Target/Buyer distinction | `entity` field | Right M&A architecture |
| Confidence scoring | Calculated per fact | Can flag weak facts |
| Domain organization | 6 specialized agents | Structured extraction |
| Verification workflow | `verification_status` fields | Human-in-loop ready |
| Gap tracking | Separate Gap entity | Explicit missing info |
| Two-phase architecture | Discovery → Reasoning | Clean separation |

---

## The Three Killer Problems

### 1. Entity Confusion
Buyer facts silently become target facts due to default behavior.

### 2. Broken Evidence Chain
Findings can cite non-existent facts with no enforcement.

### 3. Source Document Loss
Multi-document analysis loses document attribution.

---

## Session/State Management Issues

### Issue: Session Can Show Stale Data

**Location:** `web/session_store.py`, `web/app.py`

**Problem:**
- Session loads from most recent facts file
- No verification that file matches current analysis
- User sees old results thinking they're new

### Issue: Save/Load Not Atomic

**Location:** `fact_store.py:1332-1405`

**Problem:**
- `get_all_facts()` iterates without lock
- Discovery can add facts during save
- Partial state captured → corrupt file

### Issue: Session Timeout Causes Crashes

**Location:** `session_store.py:140-152`

**Problem:**
- Session expires after 24 hours
- FactStore reference deleted
- User interaction → crash (no graceful handling)

---

## File-by-File Critical Lines

### `/tools_v2/discovery_tools.py`
- **Line 488:** Silent default to target entity
- **Line 533:** Evidence validation only if status="documented"
- **Line 542-546:** Deferred validation never executed
- **Line 559-566:** Duplicate detection without logging

### `/tools_v2/fact_store.py`
- **Line 116:** `updated_at` field never set
- **Line 454:** Confidence update bypasses timestamp
- **Line 618-620:** `get_all_facts()` without lock (race condition)
- **Line 1276-1279:** Merge silently skips duplicates
- **Line 1668:** Deduplicate doesn't update ID counter

### `/tools_v2/reasoning_tools.py`
- **Line 359:** `fact_store` can be None
- **Line 445-448:** All citations valid if no FactStore
- **Line 474-477:** Validation permissive by default
- **Line 481:** Warning only for invalid citations

### `/web/session_store.py`
- **Line 99:** Fresh Session() created without verification
- **Line 126-132:** No error handling on file load

---

## Test Cases for Validation

```python
# Test 1: Multi-document source attribution
# Load docs A, B, C → verify facts show correct source

# Test 2: Invalid entity handling
# Pass entity="unknown" → should FAIL, not default

# Test 3: Citation validation
# Create finding citing F-FAKE-999 → should FAIL

# Test 4: Duplicate merge logging
# Merge stores with same fact → verify which kept AND logged

# Test 5: Session expiration graceful handling
# Let session timeout → try access → graceful error

# Test 6: Fact modification audit
# Change fact → updated_at timestamp must change

# Test 7: End-to-end evidence chain
# Trace: finding → facts → document → quote in PDF
```

---

## Decision Required: Fix vs Redesign

### Option A: Patch Critical Holes
- Make citation validation fail-fast
- Require entity validation (no defaults)
- Add source document verification
- Add LLM call logging

**Pros:** Faster, less disruption
**Cons:** Still fragile, gaps may remain

### Option B: Audit-First Redesign
- Every operation logs to append-only audit trail
- Facts are immutable (new versions, not modifications)
- Evidence chain is bidirectional and queryable
- Source document cryptographically linked

**Pros:** Bulletproof traceability
**Cons:** Significant rework

### Option C: Hybrid Approach
- Fix three killer problems immediately
- Add lightweight audit logging layer
- Extend to reasoning phase
- Build finance only after chain is solid

---

## Next Steps

1. Review this document
2. Decide on architectural approach
3. Define data flow requirements
4. Implement changes in priority order

---

*Document generated from system analysis on 2026-01-26*
