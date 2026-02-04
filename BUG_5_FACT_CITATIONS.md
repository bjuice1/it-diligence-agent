# Bug #5: Fact Citations Not Populated

**Discovered:** 2026-02-04 12:59 (after Test #4)
**Status:** ✅ FIXED
**Severity:** High (breaks buyer-aware field population)

---

## Problem

After fixing Bugs #1-4, all 6 reasoning domains completed successfully and generated 58 findings with buyer context. However, the buyer-aware fields were NOT populated:

```json
{
  "integration_related": false,
  "overlap_id": null,
  "buyer_facts_cited": [],
  "target_facts_cited": []
}
```

**But** the findings clearly cited buyer facts in their `reasoning` field text:
- "I observed Target's Oracle ERP Cloud 23C (F-TGT-APP-001) compared to **buyer's** Oracle ERP Cloud 23D (F-BYR-APP-001)"
- 26 unique buyer fact IDs (F-BYR-xxx) found across findings

---

## Root Cause

The reasoning tools create finding objects directly from LLM tool call parameters:

```python
# tools_v2/reasoning_tools.py:799
risk = Risk(**kwargs)  # kwargs comes from LLM tool call
```

The LLM provides `based_on_facts` parameter (a combined list), but NOT the separate `target_facts_cited` and `buyer_facts_cited` arrays. Since these fields have `default_factory=list`, they remain empty `[]`.

**Why this happened:**
1. The dataclasses HAVE these fields defined
2. The validation code EXTRACTS buyer/target facts from based_on_facts
3. But validation stores them as `_buyer_facts_cited` (underscore prefix) which is marked as "internal tracking" and deliberately NOT applied to the finding
4. The execution code (add_risk, add_work_item, etc.) doesn't extract these facts before creating the objects

---

## Impact

**Test #4 Results (Before Fix):**
```
✅ All 6 reasoning domains completed
✅ 58 findings generated (26 risks, 13 strategic considerations, 15 work items, 4 recommendations)
✅ Findings reference buyer facts in reasoning text (26 unique F-BYR-xxx IDs cited)
❌ buyer_facts_cited: 0/58 populated (all empty arrays)
❌ target_facts_cited: 0/58 populated (all empty arrays)
❌ integration_related: 0% true (should be ~30%)
❌ overlap_id: 0% populated (should be ~20%)
```

Without these fields populated:
- Can't filter findings by integration-related status
- Can't trace findings back to specific buyer facts
- Can't link findings to overlap analysis
- Buyer-aware reasoning appears broken to users

---

## Fix

Added logic to extract target and buyer facts from `based_on_facts` and populate the entity-specific fields before creating finding objects.

**Modified:** `tools_v2/reasoning_tools.py`

### Fix #1: add_risk() - Lines 795-803

```python
validation = self.validate_fact_citations(based_on, fail_fast=fail_fast)
if validation.get("invalid") and not fail_fast:
    logger.warning(f"Risk {risk_id} cites unknown IDs: {validation['invalid']}")

# Populate entity-specific fact citation fields from based_on_facts
target_facts = [f for f in based_on if "TGT" in f.upper()]
buyer_facts = [f for f in based_on if "BYR" in f.upper()]
kwargs["target_facts_cited"] = target_facts
kwargs["buyer_facts_cited"] = buyer_facts

risk = Risk(**kwargs)
```

### Fix #2: add_strategic_consideration() - Lines 823-831

```python
validation = self.validate_fact_citations(based_on)
if validation.get("invalid"):
    logger.warning(f"Strategic consideration {sc_id} cites unknown IDs: {validation['invalid']}")

# Populate entity-specific fact citation fields from based_on_facts
target_facts = [f for f in based_on if "TGT" in f.upper()]
buyer_facts = [f for f in based_on if "BYR" in f.upper()]
kwargs["target_facts_cited"] = target_facts
kwargs["buyer_facts_cited"] = buyer_facts

sc = StrategicConsideration(**kwargs)
```

### Fix #3: add_work_item() - Lines 850-858

```python
validation = self.validate_fact_citations(all_ids)
if validation.get("invalid"):
    logger.warning(f"Work item {wi_id} cites unknown IDs: {validation['invalid']}")

# Populate entity-specific fact citation fields from triggered_by and based_on_facts
target_facts = [f for f in all_ids if "TGT" in f.upper()]
buyer_facts = [f for f in all_ids if "BYR" in f.upper()]
kwargs["target_facts_cited"] = target_facts
kwargs["buyer_facts_cited"] = buyer_facts

# Validate cost estimate - fail fast instead of silent default
```

### Fix #4: add_recommendation() - Lines 892-900

```python
validation = self.validate_fact_citations(based_on)
if validation.get("invalid"):
    logger.warning(f"Recommendation {rec_id} cites unknown IDs: {validation['invalid']}")

# Populate entity-specific fact citation fields from based_on_facts
target_facts = [f for f in based_on if "TGT" in f.upper()]
buyer_facts = [f for f in based_on if "BYR" in f.upper()]
kwargs["target_facts_cited"] = target_facts
kwargs["buyer_facts_cited"] = buyer_facts

rec = Recommendation(**kwargs)
```

---

## Testing

### Test #5 (After Fix)
**Started:** 2026-02-04 13:01 (task b988d35)
**Expected:** buyer_facts_cited and target_facts_cited arrays populated

**Verification commands:**
```bash
# Check buyer fact citations
cat output/findings_[latest].json | jq '[.risks[], .work_items[], .strategic_considerations[]] |
  [.[] | select((.buyer_facts_cited | length) > 0)] | length'

# Expected: >20 findings with buyer_facts_cited populated

# Check target fact citations
cat output/findings_[latest].json | jq '[.risks[], .work_items[], .strategic_considerations[]] |
  [.[] | select((.target_facts_cited | length) > 0)] | length'

# Expected: >40 findings with target_facts_cited populated

# Sample a finding
cat output/findings_[latest].json | jq '.risks[0] |
  {finding_id, buyer_facts_cited, target_facts_cited}'
```

---

## Lessons Learned

1. **Dataclass defaults are silent:** If a field has `default_factory=list`, it will be `[]` unless explicitly set. No error is raised.

2. **LLM tool schemas must match code expectations:** The LLM was never asked to provide `target_facts_cited` or `buyer_facts_cited` separately because the tool schema only defines `based_on_facts`. The code must extract these.

3. **Validation vs Execution separation:** Validation code extracted these facts but marked them as "internal" (`_buyer_facts_cited`). Execution code must also extract them for actual use.

4. **Test at the field level, not just completion:** Test #4 verified all domains completed, but didn't check individual field population until after completion.

---

## Related

- Bug #1: Missing config/__init__.py (import error)
- Bug #2: Undefined output_folder (file not saved)
- Bug #3: JSON serialization (overlap objects not serializable)
- Bug #4: Dict vs object access (overlap formatter compatibility)
- **Bug #5: Fact citations not populated (THIS BUG)**

All 5 bugs now fixed. Test #5 running to verify complete buyer-aware reasoning functionality.

---

**Status:** Fix applied, Test #5 in progress (ETA 13:15)
