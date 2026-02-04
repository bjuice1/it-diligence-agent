# Buyer-Aware Reasoning: Fix Plan (1-15 Points)

**Created:** 2026-02-04
**Based On:** AUDIT_FINDINGS_buyer_aware_reasoning.md
**Status:** Ready to implement

---

## Executive Summary

**Good News:** System is 85% complete. Only 2 blockers prevent all features from working.

**Critical Path:** Fix blockers #1 and #2 = Full functionality restored (2h 45min)

**Total Scope:** 15 points organized into 4 phases

---

## PHASE 1: CRITICAL BLOCKERS (2h 45min)
*Must complete before any buyer-aware features will work*

### 1. Create Buyer-Aware Inventory Formatter ⚠️ BLOCKER
**Priority:** CRITICAL
**Effort:** 2 hours
**Impact:** Enables ALL buyer-aware features

**Task:**
Add new function to `stores/fact_store.py` that formats BOTH target and buyer facts together.

**Implementation:**
```python
def format_for_reasoning_with_buyer_context(self, domain: str) -> str:
    """
    Format facts for reasoning with BOTH target and buyer context.

    Returns inventory in two-section format:
    1. TARGET COMPANY INVENTORY (primary focus)
    2. BUYER COMPANY REFERENCE (read-only context)
    """
    with self._lock:
        target_facts = [f for f in self.facts if f.domain == domain and f.entity == "target"]
        buyer_facts = [f for f in self.facts if f.domain == domain and f.entity == "buyer"]

        lines = []

        # Section 1: TARGET INVENTORY
        lines.append("## TARGET COMPANY INVENTORY\n")
        lines.append(f"Entity: TARGET")
        lines.append(f"Total Facts: {len(target_facts)}")
        lines.append(f"Gaps Identified: {len([g for g in self.gaps if g.domain == domain])}\n")

        # Format target facts by category...
        lines.extend(self._format_facts_by_category(target_facts, "TARGET"))

        # Section 2: BUYER REFERENCE (if buyer facts exist)
        if buyer_facts:
            lines.append("\n" + "="*70)
            lines.append("\n## BUYER COMPANY REFERENCE (Read-Only Context)\n")
            lines.append("⚠️ PURPOSE: Understand integration implications and overlaps ONLY.")
            lines.append("⚠️ DO NOT: Create risks, work items, or recommendations FOR the buyer.\n")
            lines.append(f"Entity: BUYER")
            lines.append(f"Total Facts: {len(buyer_facts)}\n")

            # Format buyer facts by category...
            lines.extend(self._format_facts_by_category(buyer_facts, "BUYER"))

            # Add analysis guardrails
            lines.append("\n" + "="*70)
            lines.append("\n## ANALYSIS GUARDRAILS\n")
            lines.append("1. TARGET FOCUS: All findings must be about the target company")
            lines.append("2. ANCHOR RULE: If citing buyer facts, MUST also cite target facts")
            lines.append("3. INTEGRATION CONTEXT: Use buyer data ONLY to inform integration complexity")
            lines.append("4. EVIDENCE CHAIN: Every finding traces to specific fact IDs\n")

        return "\n".join(lines)

def _format_facts_by_category(self, facts: List[Fact], entity_label: str) -> List[str]:
    """Helper to format facts grouped by category."""
    lines = []
    by_category = {}
    for fact in facts:
        if fact.category not in by_category:
            by_category[fact.category] = []
        by_category[fact.category].append(fact)

    for category, category_facts in by_category.items():
        lines.append(f"\n### {category.upper()}")
        for fact in category_facts:
            lines.append(f"\n**{fact.fact_id}**: {fact.item}")
            if fact.details:
                details_str = ", ".join(f"{k}={v}" for k, v in fact.details.items())
                lines.append(f"- Details: {details_str}")
            lines.append(f"- Status: {fact.status}")
            lines.append(f"- Entity: {entity_label}")

    return lines
```

**File:** `stores/fact_store.py`
**After line:** 1793 (after existing `format_for_reasoning()`)

**Test:**
```python
# Quick test
fact_store = FactStore()
inventory = fact_store.format_for_reasoning_with_buyer_context("applications")
assert "## TARGET COMPANY INVENTORY" in inventory
assert "## BUYER COMPANY REFERENCE" in inventory
assert "F-TGT-" in inventory
assert "F-BYR-" in inventory
```

---

### 2. Update Reasoning Agents to Use Buyer-Aware Formatter ⚠️ BLOCKER
**Priority:** CRITICAL
**Effort:** 15 minutes
**Impact:** Routes buyer facts to reasoning agents

**Task:**
Change ONE LINE in base reasoning agent to call new formatter.

**Implementation:**
```python
# File: agents_v2/base_reasoning_agent.py
# Line: ~188

# BEFORE:
inventory_str = self.fact_store.format_for_reasoning(self.domain)

# AFTER:
inventory_str = self.fact_store.format_for_reasoning_with_buyer_context(self.domain)
```

**File:** `agents_v2/base_reasoning_agent.py`
**Line:** 188

**Test:**
Run reasoning agent and check if prompt contains both TARGET and BUYER sections.

---

### 3. Verify Tool Execution Path ✅ VERIFICATION ONLY
**Priority:** HIGH
**Effort:** 30 minutes
**Impact:** Confirms validation rules are enforced

**Task:**
Verify that `execute_reasoning_tool()` calls `validate_finding_entity_rules()` for all finding tools.

**Check:**
```python
# File: tools_v2/reasoning_tools.py
# Around line: 2800-2850

# Should see:
if tool_name in FINDING_TOOLS:
    validation_result = validate_finding_entity_rules(tool_name, tool_input)
    if not validation_result["valid"]:
        return {
            "status": "validation_error",
            "message": "Finding rejected due to entity rule violations...",
            "errors": validation_result["errors"]
        }
```

**Expected:** Already implemented (audit confirmed this exists)

**Action:** Document that this is working, no code changes needed.

---

## PHASE 2: DATABASE & PERSISTENCE (3 hours)
*Ensures buyer-aware findings are saved correctly*

### 4. Add New Fields to Database Schema 🔧 MAJOR
**Priority:** HIGH
**Effort:** 1.5 hours
**Impact:** Persists buyer-aware findings to database

**Task:**
Add missing fields to WorkItem model in database schema.

**Implementation:**
```python
# File: storage/models.py
# In WorkItem class (around line 374-404)

class WorkItem(Base):
    __tablename__ = 'work_items'

    # ... existing fields ...

    # ADD THESE NEW FIELDS:
    target_action = Column(Text, nullable=True)  # What TARGET must do
    integration_option = Column(Text, nullable=True)  # Buyer-dependent path
    integration_related = Column(Boolean, default=False)  # Auto-tagged if buyer facts cited
    overlap_id = Column(String(50), nullable=True)  # References OverlapCandidate

    # Fact citation tracking
    target_facts_cited = Column(ARRAY(String), nullable=True)  # F-TGT-xxx IDs
    buyer_facts_cited = Column(ARRAY(String), nullable=True)   # F-BYR-xxx IDs
```

**Migration:**
```bash
# Create migration
alembic revision --autogenerate -m "Add buyer-aware fields to work_items"

# Apply migration
alembic upgrade head
```

**Files:**
- `storage/models.py` (WorkItem class)
- Generate migration file via alembic

---

### 5. Update Database Writer to Persist New Fields 🔧
**Priority:** MEDIUM
**Effort:** 1 hour
**Impact:** Ensures new fields are actually written to DB

**Task:**
Update `persist_to_database()` or writer functions to include new fields.

**Check locations:**
- `services/database_writer.py` (if exists)
- `web/analysis_runner.py` (persist functions)

**Implementation:**
Ensure WorkItem serialization includes:
- target_action
- integration_option
- integration_related
- overlap_id
- target_facts_cited
- buyer_facts_cited

---

### 6. Verify JSON Export Includes New Fields ✅
**Priority:** LOW
**Effort:** 30 minutes
**Impact:** Ensures JSON exports are complete

**Task:**
Check that `session.save_to_files()` exports include all new fields.

**Files:**
- `tools_v2/session.py` (save_to_files method)

**Test:**
After fixes, check findings JSON has populated new fields.

---

## PHASE 3: INTEGRATION TESTING (4 hours)
*Validates end-to-end functionality*

### 7. Create Unit Test for Buyer-Aware Formatter 🧪
**Priority:** HIGH
**Effort:** 1 hour
**Impact:** Prevents regression

**Task:**
Create test file: `tests/test_buyer_aware_formatting.py`

**Tests:**
```python
def test_format_with_buyer_context_includes_both_entities():
    """Verify formatter returns target AND buyer facts."""
    fact_store = FactStore()

    # Add target fact
    fact_store.add_fact(
        domain="applications",
        category="ERP",
        item="SAP S/4HANA",
        entity="target"
    )

    # Add buyer fact
    fact_store.add_fact(
        domain="applications",
        category="ERP",
        item="Oracle ERP Cloud",
        entity="buyer"
    )

    inventory = fact_store.format_for_reasoning_with_buyer_context("applications")

    assert "## TARGET COMPANY INVENTORY" in inventory
    assert "## BUYER COMPANY REFERENCE" in inventory
    assert "F-TGT-" in inventory
    assert "F-BYR-" in inventory
    assert "SAP S/4HANA" in inventory
    assert "Oracle ERP Cloud" in inventory

def test_format_without_buyer_facts_still_works():
    """Verify formatter works even if no buyer facts exist."""
    fact_store = FactStore()

    fact_store.add_fact(
        domain="applications",
        category="ERP",
        item="SAP S/4HANA",
        entity="target"
    )

    inventory = fact_store.format_for_reasoning_with_buyer_context("applications")

    assert "## TARGET COMPANY INVENTORY" in inventory
    assert "## BUYER COMPANY REFERENCE" not in inventory  # Should be omitted
```

---

### 8. Create Integration Test for Reasoning Pipeline 🧪
**Priority:** HIGH
**Effort:** 1.5 hours
**Impact:** Validates full pipeline

**Task:**
Create test file: `tests/test_buyer_aware_reasoning_pipeline.py`

**Test:**
```python
def test_reasoning_agent_receives_buyer_facts():
    """End-to-end test: reasoning agent gets both target and buyer facts."""

    # Setup
    session = create_test_session()
    fact_store = session.fact_store

    # Add target and buyer facts
    fact_store.add_fact(domain="applications", item="SAP", entity="target")
    fact_store.add_fact(domain="applications", item="Oracle", entity="buyer")

    # Run reasoning
    from agents_v2.reasoning.applications_reasoning import ApplicationsReasoningAgent
    agent = ApplicationsReasoningAgent(fact_store=fact_store, api_key=TEST_API_KEY)
    result = agent.reason(deal_context={})

    # Verify agent's prompt included buyer facts
    # (may need to add logging to capture prompt)
    assert agent._last_prompt_contained_buyer_facts  # Add this tracking

    # Verify findings cite buyer facts
    reasoning_store = agent.get_reasoning_store()
    buyer_aware_findings = [
        f for f in reasoning_store.work_items
        if f.buyer_facts_cited
    ]

    assert len(buyer_aware_findings) > 0, "Should have findings citing buyer facts"
```

---

### 9. Test Overlap Map Generation 🧪
**Priority:** MEDIUM
**Effort:** 1 hour
**Impact:** Validates overlap tool works

**Task:**
Test that reasoning agents can successfully call `generate_overlap_map`.

**Test:**
```python
def test_overlap_map_tool_execution():
    """Test that generate_overlap_map tool creates valid overlaps."""

    from tools_v2.reasoning_tools import execute_reasoning_tool

    tool_input = {
        "overlaps": [
            {
                "overlap_id": "OVL-APP-001",
                "domain": "applications",
                "overlap_type": "platform_mismatch",
                "target_fact_ids": ["F-TGT-APP-001"],
                "buyer_fact_ids": ["F-BYR-APP-001"],
                "target_summary": "Target uses SAP",
                "buyer_summary": "Buyer uses Oracle",
                "why_it_matters": "Platform consolidation required",
                "confidence": 0.9
            }
        ]
    }

    result = execute_reasoning_tool("generate_overlap_map", tool_input, {}, {})

    assert result["status"] == "success"
    assert len(result.get("overlaps_created", [])) == 1
```

---

### 10. Validation Rule Testing 🧪
**Priority:** MEDIUM
**Effort:** 30 minutes
**Impact:** Ensures rules enforce correctly

**Task:**
Test that validation rejects invalid findings.

**Test:**
```python
def test_validation_rejects_buyer_only_findings():
    """Test RULE 1: Buyer facts require target facts (ANCHOR)."""

    from tools_v2.reasoning_tools import validate_finding_entity_rules

    # Create finding with ONLY buyer facts (should fail)
    tool_input = {
        "title": "Test finding",
        "fact_ids": ["F-BYR-APP-001"]  # No target facts!
    }

    result = validate_finding_entity_rules("identify_risk", tool_input)

    assert result["valid"] == False
    assert "ENTITY_ANCHOR_VIOLATION" in result["errors"][0]

def test_validation_auto_tags_integration_related():
    """Test RULE 2: Auto-tag if buyer facts cited."""

    tool_input = {
        "title": "Test finding",
        "fact_ids": ["F-TGT-APP-001", "F-BYR-APP-001"],
        "tags": {}
    }

    result = validate_finding_entity_rules("create_work_item", tool_input)

    assert result["valid"] == True
    assert result["auto_tags"]["integration_related"] == True
```

---

## PHASE 4: VERIFICATION & POLISH (2 hours)
*Confirms everything works end-to-end*

### 11. Run Full Two-Phase Analysis Test 🎯
**Priority:** CRITICAL
**Effort:** 30 minutes
**Impact:** Validates complete system

**Task:**
Re-run the same test we did before with National Mutual + Atlantic International.

**Success Criteria:**
- ✅ Document separation: 1 TARGET, 1 BUYER
- ✅ Facts extracted: ~60 TARGET, ~45 BUYER (F-TGT/F-BYR prefixes)
- ✅ Findings cite buyer facts: >0 findings with buyer_facts_cited populated
- ✅ Overlap analysis: >0 findings with overlap_id
- ✅ Integration tagging: >0 work items with integration_related=true
- ✅ Target vs integration fields: work items have both target_action AND integration_option

**Command:**
```bash
cd "/Users/JB/Documents/IT/IT DD Test 2/9.5/it-diligence-agent 2"
python3 run_test_analysis.py
```

**Validation Script:**
```python
# Check results
import json

with open('output/facts_LATEST.json') as f:
    facts = json.load(f)['facts']

with open('output/findings_LATEST.json') as f:
    findings = json.load(f)

buyer_facts = [f for f in facts if f['entity'] == 'buyer']
print(f"Buyer facts: {len(buyer_facts)}")  # Should be > 0

buyer_aware_findings = [
    w for w in findings['work_items']
    if w.get('buyer_facts_cited')
]
print(f"Buyer-aware findings: {len(buyer_aware_findings)}")  # Should be > 0

integration_findings = [
    w for w in findings['work_items']
    if w.get('integration_related')
]
print(f"Integration-related: {len(integration_findings)}")  # Should be > 0
```

---

### 12. Verify Specific Overlaps Are Detected 🎯
**Priority:** HIGH
**Effort:** 30 minutes
**Impact:** Confirms quality of overlap analysis

**Task:**
Manually check that specific known overlaps are surfaced in findings.

**Expected Overlaps from Test Documents:**
1. **AWS Region Mismatch:**
   - Target: AWS us-east-1
   - Buyer: AWS us-east-2
   - Should generate: infrastructure overlap finding

2. **Security Tool Differences:**
   - Target: CrowdStrike endpoint, IBM QRadar SIEM, RSA SecurID MFA
   - Buyer: Carbon Black endpoint, Microsoft Sentinel SIEM, Microsoft Authenticator MFA
   - Should generate: 3 cybersecurity overlap findings

3. **Team Size Disparity:**
   - Target: 121 IT staff
   - Buyer: 568 IT staff (4.7x larger)
   - Should generate: organization overlap finding

**Validation:**
Read findings JSON and check if these specific overlaps are mentioned.

---

### 13. Check Database Persistence ✅
**Priority:** MEDIUM
**Effort:** 15 minutes
**Impact:** Validates data is saved

**Task:**
Query database to verify new fields are persisted.

**SQL Check:**
```sql
-- Check work_items table has new columns
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'work_items'
  AND column_name IN (
    'target_action',
    'integration_option',
    'integration_related',
    'overlap_id',
    'target_facts_cited',
    'buyer_facts_cited'
  );

-- Check if data is actually populated
SELECT
  COUNT(*) as total_work_items,
  COUNT(target_action) as has_target_action,
  COUNT(integration_option) as has_integration_option,
  SUM(CASE WHEN integration_related THEN 1 ELSE 0 END) as integration_related_count,
  COUNT(overlap_id) as has_overlap_id
FROM work_items
WHERE run_id = 'LATEST_RUN_ID';
```

---

### 14. Review Reasoning Quality 🎯
**Priority:** MEDIUM
**Effort:** 30 minutes
**Impact:** Ensures outputs make sense

**Task:**
Manually review 5-10 findings to verify:
1. Overlap analysis is specific (not generic)
2. Target_action is clear and target-focused
3. Integration_option provides buyer-dependent alternative
4. Evidence chain is complete (cites both F-TGT and F-BYR facts)

**Sample Finding to Look For:**
```json
{
  "title": "ERP Platform Consolidation Required",
  "overlap_id": "OVL-APP-001",
  "integration_related": true,
  "target_action": "Target must maintain SAP S/4HANA through TSA period while preparing migration plan (18-24 month timeline)",
  "integration_option": "If buyer absorbs target financials into Oracle ERP Cloud, migrate target to Oracle ($2-4M, 18-24 months); if target remains separate, continue SAP with extended TSA ($400K/yr)",
  "target_facts_cited": ["F-TGT-APP-001", "F-TGT-APP-003"],
  "buyer_facts_cited": ["F-BYR-APP-001", "F-BYR-APP-002"],
  "reasoning": "Target relies on SAP S/4HANA (F-TGT-APP-001) with 247 custom programs (F-TGT-APP-003). Buyer standardized on Oracle ERP Cloud (F-BYR-APP-001) serving 4,272 users (F-BYR-APP-002). Platform mismatch creates..."
}
```

---

### 15. Document Changes & Update README 📝
**Priority:** LOW
**Effort:** 15 minutes
**Impact:** Team awareness

**Task:**
Update documentation to reflect buyer-aware reasoning capabilities.

**Files to Update:**
1. `README.md` - Add "Buyer-Aware Reasoning" feature section
2. `CHANGELOG.md` - Document the enhancement
3. `docs/ARCHITECTURE_OVERVIEW.md` - Update with two-phase architecture

**Content:**
```markdown
## Buyer-Aware Reasoning (NEW)

The system now supports two-phase analysis with buyer-aware reasoning:

**Phase 1:** Extract TARGET facts from target company documents
**Phase 2:** Extract BUYER facts from buyer company documents
**Phase 3:** Reasoning with overlap analysis

### Features
- Specific overlap detection (e.g., "Target SAP vs Buyer Oracle")
- Integration-focused findings with options
- Entity separation enforcement (target vs buyer lenses)
- Evidence chain tracing to both entities

### New Finding Fields
- `target_action`: What target must do (always required)
- `integration_option`: Buyer-dependent path (optional)
- `overlap_id`: References specific overlap
- `integration_related`: Auto-tagged when buyer facts cited
```

---

## IMPLEMENTATION SEQUENCE

### Day 1 (3 hours)
- [ ] Point 1: Create buyer-aware formatter (2h)
- [ ] Point 2: Update base reasoning agent (15min)
- [ ] Point 3: Verify validation is active (30min)
- [ ] Point 11: Run test to verify blockers fixed (30min)

**Checkpoint:** Buyer facts should reach reasoning agents

---

### Day 2 (4 hours)
- [ ] Point 4: Database schema updates (1.5h)
- [ ] Point 5: Update database writer (1h)
- [ ] Point 7: Unit tests for formatter (1h)
- [ ] Point 8: Integration test for pipeline (1.5h)

**Checkpoint:** End-to-end pipeline working with persistence

---

### Day 3 (3 hours)
- [ ] Point 9: Test overlap map tool (1h)
- [ ] Point 10: Validation rule tests (30min)
- [ ] Point 11: Full analysis test (30min)
- [ ] Point 12: Verify specific overlaps (30min)
- [ ] Point 13: Check database persistence (15min)
- [ ] Point 14: Review reasoning quality (30min)
- [ ] Point 15: Update documentation (15min)

**Checkpoint:** Full validation and documentation complete

---

## SUCCESS METRICS

After implementing all 15 points:

| Metric | Target | How to Measure |
|--------|--------|----------------|
| **Buyer facts in reasoning** | 100% of domains | Check agent prompts include BUYER section |
| **Overlap findings** | >5 per test run | Count findings with overlap_id |
| **Integration tagging** | >30% of work items | Count integration_related=true |
| **Buyer fact citations** | >10 findings | Count findings citing F-BYR facts |
| **Target vs integration fields** | >50% of work items | Check target_action + integration_option populated |
| **Database persistence** | 100% of fields | Query DB for new column data |
| **Test coverage** | >80% for new code | Run pytest with coverage |

---

## ROLLBACK PLAN

If issues arise:

1. **Revert Point 2** - Change base_reasoning_agent.py back to original formatter
2. **System returns to pre-buyer-aware state** - All original functionality intact
3. **Debug in isolation** - Test new formatter independently
4. **Re-apply when fixed** - Change back to buyer-aware formatter

No data loss risk - all changes are additive.

---

## EFFORT SUMMARY

| Phase | Points | Effort | Priority |
|-------|--------|--------|----------|
| Phase 1: Blockers | 1-3 | 2h 45min | CRITICAL |
| Phase 2: Database | 4-6 | 3h | HIGH |
| Phase 3: Testing | 7-10 | 4h | MEDIUM |
| Phase 4: Verification | 11-15 | 2h | VARIED |
| **TOTAL** | **15** | **~12h** | **3 days** |

**Critical Path:** 2h 45min to restore functionality
**Full Implementation:** 2-3 days for production-ready

---

*Ready to implement. Start with Phase 1 (Points 1-3) for immediate impact.*
