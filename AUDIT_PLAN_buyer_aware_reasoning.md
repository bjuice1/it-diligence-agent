# Buyer-Aware Reasoning: Comprehensive System Audit Plan

**Created:** 2026-02-04
**Purpose:** Identify all gaps in buyer-aware reasoning implementation before creating fix plan
**Scope:** End-to-end pipeline from document intake to findings output

---

## Audit Methodology

### Audit Approach
1. **Code Inspection**: Review actual implementation vs planned architecture
2. **Data Flow Tracing**: Follow facts from extraction → storage → reasoning → output
3. **Test Results Analysis**: Examine actual test outputs to identify failures
4. **Integration Points**: Check handoffs between components

### Success Criteria
- All buyer-aware features working end-to-end
- Reasoning agents receive and use buyer facts
- Overlap analysis generates specific comparisons
- Findings properly use new fields (target_action, integration_option, overlap_id)
- Entity separation maintained throughout pipeline

---

## AUDIT CHECKLIST

## Phase 1: Fact Extraction & Storage

### 1.1 Document Separation ✅ FIXED
**Status:** WORKING (fixed in analysis_runner.py:548)

**Check:**
- [x] `_separate_documents_by_entity()` checks explicit `entity` field first
- [x] Falls back to filename patterns correctly
- [x] Test showed: "1 TARGET, 1 BUYER" (correct)

**Evidence:** Test run showed correct separation

---

### 1.2 Fact ID Convention ✅ WORKING
**Status:** IMPLEMENTED

**Check:**
- [x] `_generate_fact_id()` includes entity prefix (F-TGT vs F-BYR)
- [x] `_generate_gap_id()` includes entity prefix (GAP-TGT vs GAP-BYR)
- [x] Test showed: 62 F-TGT facts, 46 F-BYR facts

**Evidence:** facts_20260204_085920.json shows correct prefixes

**Location:** stores/fact_store.py:593, 697

---

### 1.3 Entity Tagging ✅ WORKING
**Status:** IMPLEMENTED

**Check:**
- [x] Facts stored with `entity` field (target/buyer)
- [x] Phase 1 extracts TARGET facts only
- [x] Phase 2 extracts BUYER facts only

**Evidence:** Test showed correct entity counts by phase

---

## Phase 2: Fact Formatting for Reasoning

### 2.1 format_for_reasoning() Function ❌ ISSUE IDENTIFIED
**Status:** ONLY FORMATS ONE ENTITY AT A TIME

**Check:**
- [ ] Current function signature: `format_for_reasoning(domain, entity="target")`
- [ ] Only returns facts for ONE entity
- [ ] No function that combines TARGET + BUYER facts

**Issue:** Reasoning agents don't receive buyer facts because:
1. `format_for_reasoning()` only formats one entity
2. Reasoning agents call it with default `entity="target"`
3. Buyer facts never reach reasoning prompts

**Location:** stores/fact_store.py:1793

**What's Missing:**
```python
# PLANNED but NOT IMPLEMENTED:
def format_for_reasoning_with_buyer_context(self, domain: str) -> str:
    """
    Format facts with BOTH target and buyer context.

    Returns:
        ## TARGET COMPANY INVENTORY
        [TARGET facts]

        ## BUYER COMPANY REFERENCE
        [BUYER facts]
    """
```

---

### 2.2 Reasoning Agent Invocation ❌ ISSUE IDENTIFIED
**Status:** DOESN'T REQUEST BUYER FACTS

**Check:**
- [ ] `run_reasoning_for_domain()` calls `agent.reason(deal_context)`
- [ ] Agent's `reason()` method uses `format_for_reasoning()` with default entity
- [ ] No logic to include buyer facts

**Location:** web/analysis_runner.py:1086-1136

**Issue:** Even if we fix `format_for_reasoning()`, reasoning agents don't know to use the buyer-aware version

---

## Phase 3: Reasoning Tools & Validation

### 3.1 OverlapCandidate Dataclass ✅ IMPLEMENTED
**Status:** DEFINED

**Check:**
- [x] `OverlapCandidate` class exists
- [x] Has all required fields (overlap_id, domain, overlap_type, etc.)
- [x] Validation method exists

**Location:** tools_v2/reasoning_tools.py

**Test Needed:** Check if it's actually USED by reasoning agents

---

### 3.2 generate_overlap_map Tool ❌ NEEDS VERIFICATION
**Status:** UNKNOWN - NEEDS AUDIT

**Checks Required:**
- [ ] Does `generate_overlap_map` tool exist in reasoning_tools.py?
- [ ] Is it registered in REASONING_TOOLS list?
- [ ] Can reasoning agents actually call it?
- [ ] Does it return OverlapCandidate objects?

**Location to Check:** tools_v2/reasoning_tools.py

---

### 3.3 Runtime Validation ❓ NEEDS VERIFICATION
**Status:** CODE EXISTS, UNCLEAR IF ACTIVE

**Check:**
- [ ] `validate_finding_entity_rules()` function exists (we saw it)
- [ ] Is it actually called before tool execution?
- [ ] Does it enforce the 5 rules:
  - RULE 1: Buyer facts require target facts (ANCHOR)
  - RULE 2: Auto-tag integration_related if buyer facts cited
  - RULE 3: Check for "Buyer should..." language (SCOPE)
  - RULE 4: Work items should have target focus
  - RULE 5: Warn about legacy fact IDs

**Location:** tools_v2/reasoning_tools.py (validation function exists)

**Test:** Check if findings were rejected during test run (none were)

---

### 3.4 Enhanced Dataclass Fields ✅ DEFINED, ❌ NOT USED
**Status:** FIELDS EXIST BUT NOT POPULATED

**Check:**
- [x] WorkItem has `target_action` field
- [x] WorkItem has `integration_option` field
- [x] WorkItem has `integration_related` field
- [x] WorkItem has `overlap_id` field
- [x] WorkItem has `target_facts_cited` field
- [x] WorkItem has `buyer_facts_cited` field

**Test Results:**
- ❌ 0/12 work items have ANY of these fields populated
- ❌ No findings cite buyer facts

**Conclusion:** Fields exist but reasoning agents don't use them

---

## Phase 4: Reasoning Prompts

### 4.1 Prompt Updates ✅ IMPLEMENTED
**Status:** ALL 6 PROMPTS UPDATED

**Check:**
- [x] Applications prompt updated
- [x] Infrastructure prompt updated
- [x] Identity & Access prompt updated
- [x] Cybersecurity prompt updated
- [x] Network prompt updated
- [x] Organization prompt updated

**Each includes:**
- [x] STEP 1: Generate Overlap Map section
- [x] Domain-specific overlap types table
- [x] 3-Layer Output Structure
- [x] Buyer Context Rules
- [x] PE Concerns table with realistic costs

**Location:** prompts/v2_*_reasoning_prompt.py

**Issue:** Prompts are updated, but agents never receive buyer facts to act on them!

---

### 4.2 Prompt Variable Substitution ❓ NEEDS VERIFICATION
**Status:** UNKNOWN

**Checks Required:**
- [ ] How does `{inventory}` get replaced in prompts?
- [ ] Does it call `format_for_reasoning()` or another function?
- [ ] Is there logic to use buyer-aware formatting?

**Location to Check:**
- agents_v2/reasoning/*.py (individual reasoning agents)
- Look for where prompts are constructed

---

## Phase 5: Tool Registration & Execution

### 5.1 Tool Registration ❓ NEEDS VERIFICATION
**Status:** UNKNOWN

**Checks Required:**
- [ ] Is `generate_overlap_map` in REASONING_TOOLS list?
- [ ] Are OVERLAP_TYPES enum values accessible to agents?
- [ ] Can agents see the new tool in their available tools?

**Location:** tools_v2/reasoning_tools.py

---

### 5.2 Tool Execution Flow ❓ NEEDS VERIFICATION
**Status:** UNKNOWN

**Checks Required:**
- [ ] Does `execute_reasoning_tool()` call `validate_finding_entity_rules()`?
- [ ] If validation fails, is the tool call rejected?
- [ ] Are error messages logged when validation fails?

**Test:** Check logs from test run for any validation rejections (likely none)

---

## Phase 6: Output & Persistence

### 6.1 Findings JSON Structure ✅ FIELDS PRESENT
**Status:** FIELDS DEFINED IN SCHEMA

**Check:**
- [x] Work items have new fields in JSON output
- [x] But all are empty/null in test output

**Evidence:** findings_20260204_085920.json shows fields exist but unpopulated

---

### 6.2 Database Persistence ❓ NEEDS VERIFICATION
**Status:** UNKNOWN

**Checks Required:**
- [ ] Do database tables have columns for new fields?
- [ ] Does `persist_to_database()` save new fields?
- [ ] Schema migrations run?

**Location to Check:**
- services/data_models.py (SQLAlchemy models)
- Database schema

---

## CRITICAL PATH ANALYSIS

### Root Cause Chain

```
1. Reasoning agents don't receive buyer facts
   ↓
2. Because format_for_reasoning() only returns target facts
   ↓
3. Because there's no function that combines target + buyer
   ↓
4. So even though prompts instruct "generate overlap map"...
   ↓
5. Agents have no buyer data to compare against
   ↓
6. Result: No overlap analysis, no buyer-aware features used
```

### Primary Issue
**The reasoning agents never see buyer facts, so all downstream features fail**

Even though we have:
- ✅ Correct fact extraction (both entities)
- ✅ Correct fact IDs (F-TGT/F-BYR)
- ✅ Updated prompts with buyer-aware instructions
- ✅ New dataclass fields
- ✅ Validation rules (probably)

None of it works because **the inventory passed to reasoning agents only contains TARGET facts**.

---

## AUDIT EXECUTION PLAN

### Step 1: Code Inspection (2 hours)
**Objective:** Trace the exact code path from fact storage to reasoning prompt

**Tasks:**
1. [ ] Find where reasoning agents construct their prompts
2. [ ] Identify what function provides the `{inventory}` content
3. [ ] Check if `generate_overlap_map` tool is registered
4. [ ] Verify `validate_finding_entity_rules()` is called during tool execution
5. [ ] Check database schema for new fields

**Files to Examine:**
- `agents_v2/reasoning/applications_reasoning.py` (example reasoning agent)
- `agents_v2/reasoning/base_reasoning_agent.py` (if exists - base class)
- `tools_v2/reasoning_tools.py` (tool registry)
- `stores/fact_store.py` (formatting functions)
- `services/data_models.py` (database schema)

---

### Step 2: Create Test Harness (1 hour)
**Objective:** Quick test to verify each component individually

**Tests:**
1. [ ] Test `format_for_reasoning()` - does it return only target facts?
2. [ ] Test if `generate_overlap_map` tool exists and is callable
3. [ ] Test if validation rules actually reject invalid findings
4. [ ] Test reasoning agent with manually constructed buyer-aware inventory

**Location:** Create `tests/test_buyer_aware_audit.py`

---

### Step 3: Log Analysis (30 min)
**Objective:** Review test run logs for hidden errors

**Tasks:**
1. [ ] Check for validation warnings/errors
2. [ ] Check for missing tool errors
3. [ ] Check if reasoning agents logged any buyer fact usage
4. [ ] Check for schema/persistence errors

**Log Location:** `output/logs/` from test run

---

### Step 4: Data Flow Diagram (1 hour)
**Objective:** Visualize actual vs intended data flow

**Create Diagrams:**
1. **Current (Broken) Flow:**
```
Documents → Phase 1 (TARGET) → FactStore (F-TGT-xxx)
         → Phase 2 (BUYER)  → FactStore (F-BYR-xxx)
         → Reasoning        → format_for_reasoning(entity="target")
                           → Agent receives ONLY F-TGT facts
                           → No overlap analysis possible
                           → Findings don't cite F-BYR facts
```

2. **Intended (Fixed) Flow:**
```
Documents → Phase 1 (TARGET) → FactStore (F-TGT-xxx)
         → Phase 2 (BUYER)  → FactStore (F-BYR-xxx)
         → Reasoning        → format_for_reasoning_with_buyer_context()
                           → Agent receives F-TGT + F-BYR facts
                           → Calls generate_overlap_map()
                           → Creates overlap candidates
                           → Findings cite both entities
                           → Uses target_action vs integration_option
```

---

### Step 5: Findings Summary (30 min)
**Objective:** Consolidate all issues into prioritized list

**Categories:**
1. **Blockers** - Prevent any buyer-aware features from working
2. **Major** - Prevent specific features from working
3. **Minor** - Reduce effectiveness but don't break functionality
4. **Nice-to-have** - Improvements beyond original plan

---

## EXPECTED AUDIT FINDINGS (Preliminary)

Based on initial test analysis, we expect to find:

### BLOCKERS 🔴
1. **No buyer-aware inventory formatting function**
   - Need: `format_for_reasoning_with_buyer_context()`
   - Impact: Reasoning agents never see buyer facts

2. **Reasoning agents don't request buyer context**
   - Need: Update agent invocation to use buyer-aware formatting
   - Impact: Even if function exists, not called

### MAJOR ISSUES 🟠
3. **generate_overlap_map tool may not exist**
   - Need: Verify tool implementation and registration
   - Impact: No structured overlap analysis

4. **Validation rules may not be enforced**
   - Need: Verify `validate_finding_entity_rules()` is called
   - Impact: No enforcement of entity separation rules

5. **Prompts updated but not effective**
   - Need: Agents need buyer facts to follow prompt instructions
   - Impact: Beautiful prompts, but no data to work with

### MINOR ISSUES 🟡
6. **Database schema may not have new fields**
   - Need: Check if migrations run
   - Impact: Can't persist buyer-aware findings to DB

7. **Test coverage gaps**
   - Need: Unit tests for buyer-aware features
   - Impact: Hard to verify fixes work

---

## AUDIT DELIVERABLE

**Output:** `AUDIT_FINDINGS_buyer_aware_reasoning.md`

**Contents:**
1. Executive summary (what's broken, why, impact)
2. Detailed findings by component
3. Root cause analysis
4. Prioritized issue list
5. Recommended fix sequence
6. Estimated effort per fix

**Then we create:** `FIX_PLAN_buyer_aware_reasoning.md` (1-15 point plan)

---

## AUDIT TIMELINE

| Phase | Duration | Output |
|-------|----------|--------|
| Code Inspection | 2 hours | Code paths documented |
| Test Harness | 1 hour | Component tests |
| Log Analysis | 30 min | Error patterns |
| Data Flow Diagram | 1 hour | Visual diagrams |
| Findings Summary | 30 min | AUDIT_FINDINGS.md |
| **TOTAL** | **5 hours** | Ready for fix plan |

---

## NEXT STEPS

1. **Run this audit** (execute steps 1-5)
2. **Review findings** with team
3. **Create fix plan** (1-15 points, prioritized)
4. **Implement fixes** in priority order
5. **Re-test** to verify all features working

---

*Ready to execute audit. Awaiting approval to proceed.*
