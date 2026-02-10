# Analysis Reasoning V2 - Implementation Status

## Overview

This document tracks the buyer-aware reasoning system implementation. The core fix has been implemented - reasoning agents now receive both target and buyer facts.

---

## Implementation Status: COMPLETE ✅

### Test Results (2026-02-08)

**Test Configuration:**
- Target: National Mutual (1 document)
- Buyer: Atlantic International (1 document)
- 6 domains analyzed

**Results:**
| Metric | Value |
|--------|-------|
| Target Facts | 63 |
| Buyer Facts | 35 |
| Overlaps Generated | 23 |
| Buyer Fact Citations | 82 |
| Validation Warnings | 6 (all "Buyer should" scope warnings) |

**Reasoning Output by Domain:**
| Domain | Risks | Work Items | Facts Cited | Prompt Size |
|--------|-------|------------|-------------|-------------|
| Infrastructure | 3 | 3 | 9/12 (75%) | 15,169 tokens |
| Applications | 6 | 2 | 14/50 (28%) | 19,736 tokens |
| Organization | 3 | 4 | 11/14 (79%) | 14,175 tokens |
| Cybersecurity | 3 | 3 | 5/10 (50%) | 14,270 tokens |
| Network | 2 | 3 | 7/7 (100%) | 13,390 tokens |
| Identity | 4 | 3 | 5/5 (100%) | 13,774 tokens |

**Overlaps by Domain:**
- Infrastructure: 4 (AWS region, data center, DR, monitoring)
- Cybersecurity: 3 (endpoint, SIEM, security team)
- Applications: 13 (ERP, CRM, HCM, analytics, collaboration, etc.)
- Organization: 1 (team structure comparison)
- Identity: 2 (MFA platform, CyberArk deployment)

**Sample Finding (AWS Region Mismatch):**
```json
{
  "finding_id": "R-53a0",
  "title": "AWS Region Mismatch Creates Cross-Region Data Transfer Costs",
  "target_facts_cited": ["F-TGT-INFRA-003"],
  "buyer_facts_cited": ["F-BYR-INFRA-005"],
  "overlap_id": "OVL-INF-002",
  "integration_related": true,
  "mna_implication": "AWS region mismatch (us-east-1 vs us-east-2) requires either $200K-$500K migration investment or ongoing cross-region transfer costs"
}
```

---

## What Was Built

1. **`format_for_reasoning_with_buyer_context()`** - `stores/fact_store.py:1862`
   - Returns combined inventory with TARGET + BUYER sections
   - Includes overlap map if provided
   - Has guardrails to prevent entity confusion

2. **Reasoning agent integration** - `agents_v2/base_reasoning_agent.py:191-195`
   - Calls `format_for_reasoning_with_buyer_context()` instead of old formatter
   - Passes overlaps from deal_context

3. **Buyer context configuration** - `config/buyer_context_config.py`
   - All domains enabled for buyer facts
   - Per-domain limits configured (15-50 facts)

4. **Validation rules** - `tools_v2/reasoning_tools.py`
   - ANCHOR RULE: Buyer facts require target facts
   - SCOPE CHECK: Warns about "Buyer should" language
   - AUTO-TAG: Sets `integration_related=true` for buyer citations

---

## Known Issues

### Issue: Reasoning Phase Stuck on Large Document Sets
**Status:** FIXED (2026-02-08)

**Root Cause:**
Web UI was running reasoning sequentially for all 6 domains. With large fact sets, each domain takes 5-10+ minutes, making total time 30-60+ minutes.

**Fix Applied:**
Added parallel reasoning to `web/analysis_runner.py`:
- Uses `ThreadPoolExecutor` with max 3 concurrent workers
- 10-minute timeout per domain
- Thread-safe via `ReasoningStore._lock` (RLock)
- Falls back to sequential if `PARALLEL_REASONING=False`

**Expected Improvement:**
- 6 domains now run 3 at a time instead of 1 at a time
- ~50% reduction in total reasoning time

---

## Data Flow

```
Phase 1: Target Documents → Discovery → F-TGT-xxx facts
Phase 2: Buyer Documents → Discovery → F-BYR-xxx facts
Phase 3.5: Overlap Generation → OVL-xxx overlap candidates
Phase 3: Reasoning receives BOTH entity facts + overlaps
         └─ Generates findings citing both entities
         └─ Links to overlap IDs
         └─ Sets integration_related flags
```

---

## Inventory Format Sent to Reasoning

```
## TARGET COMPANY INVENTORY
Entity: TARGET
Total Facts: 63
[All F-TGT facts by category]

======================================================================

## BUYER COMPANY REFERENCE (Read-Only Context)
⚠️ PURPOSE: Understand integration implications ONLY
⚠️ DO NOT: Create risks/work items FOR the buyer
Entity: BUYER
Total Facts: 35
[All F-BYR facts by category]

======================================================================

## PRE-COMPUTED OVERLAP MAP
[23 overlap candidates with target/buyer summaries]

======================================================================

## ANALYSIS GUARDRAILS
1. TARGET FOCUS: All findings about target
2. ANCHOR RULE: Buyer facts require target facts
3. INTEGRATION CONTEXT: Use buyer for overlaps only
```

---

## Key Files

| File | Purpose |
|------|---------|
| `stores/fact_store.py:1862` | `format_for_reasoning_with_buyer_context()` |
| `agents_v2/base_reasoning_agent.py:191` | Calls buyer-aware formatter |
| `config/buyer_context_config.py` | Per-domain buyer fact config |
| `tools_v2/reasoning_tools.py` | Validation rules, OverlapCandidate dataclass |
| `output/overlaps_*.json` | Generated overlap maps |
| `output/findings_*.json` | Findings with buyer fact citations |
