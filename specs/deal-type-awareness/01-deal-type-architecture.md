# Deal Type Architecture & Data Flow

**Document:** 01-deal-type-architecture.md
**Purpose:** Define deal type taxonomy, entity semantics for all deal structures, and end-to-end data flow from UI → prompts → recommendations
**Status:** Foundation document - blocks all others
**Date:** 2026-02-11

---

## Overview

This document establishes the foundational architecture for deal-type awareness across the IT Due Diligence Agent. It resolves the critical issue identified in Audit1 where the system recommends consolidation synergies regardless of deal type, producing incorrect recommendations for carve-outs and divestitures.

**Core Problem:** System currently treats all deals as acquisitions, recommending "consolidate to buyer platform" even when target is separating FROM buyer.

**Core Solution:** Thread deal_type through entire pipeline with conditional logic at each decision point.

---

## Architecture

### System-Wide Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ Phase 1: Deal Creation (UI)                                      │
│ ┌──────────────┐                                                │
│ │ User selects │ → deal_type: "acquisition" | "carveout" |      │
│ │  deal_type   │              "divestiture"                     │
│ └──────────────┘                                                │
│        ↓                                                         │
│ ┌──────────────────────────────────────────────────────────┐   │
│ │ Database: deals table                                     │   │
│ │   - deal_type VARCHAR(50) NOT NULL                        │   │
│ │   - Enforced at insert via validation                     │   │
│ └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│ Phase 2: Analysis Context Building                              │
│ ┌──────────────────────────────────────────────────────────┐   │
│ │ deal_context dict:                                        │   │
│ │   {                                                       │   │
│ │     "deal_id": "...",                                     │   │
│ │     "deal_type": "carveout",  ← Propagated everywhere    │   │
│ │     "target_name": "...",                                 │   │
│ │     "buyer_name": "..."                                   │   │
│ │   }                                                       │   │
│ └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│ Phase 3: Reasoning (6 Domain Agents)                            │
│                                                                  │
│ ┌────────────────────────────────────────────────────────┐     │
│ │ Prompt Injection (Doc 03)                              │     │
│ │                                                         │     │
│ │ IF deal_type == "acquisition":                          │     │
│ │   → "Focus on: Synergy, Day-1, Cost"                    │     │
│ │   → "Ignore: TSA, Separation"                           │     │
│ │                                                         │     │
│ │ IF deal_type == "carveout":                             │     │
│ │   → "Focus on: TSA, Separation, Day-1"                  │     │
│ │   → "Ignore: Synergy (not applicable)"                  │     │
│ │                                                         │     │
│ │ IF deal_type == "divestiture":                          │     │
│ │   → "Focus on: Separation, RemainCo Impact"             │     │
│ │   → "Ignore: Synergy"                                   │     │
│ └────────────────────────────────────────────────────────┘     │
│                          ↓                                      │
│ ┌────────────────────────────────────────────────────────┐     │
│ │ LLM produces findings with correct M&A lens            │     │
│ │   - Risks tied to relevant lens                        │     │
│ │   - Work items appropriate for deal type               │     │
│ │   - Recommendations align with deal strategy           │     │
│ └────────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│ Phase 4: Cost Calculation                                       │
│                                                                  │
│ ┌────────────────────────────────────────────────────────┐     │
│ │ Synergy Engine (Doc 02)                                │     │
│ │                                                         │     │
│ │ _identify_synergies(deal_type)                         │     │
│ │   IF deal_type == "acquisition":                        │     │
│ │     → _calculate_consolidation_synergies()              │     │
│ │   ELSE IF deal_type in ["carveout", "divestiture"]:     │     │
│ │     → _calculate_separation_costs()                     │     │
│ └────────────────────────────────────────────────────────┘     │
│                          ↓                                      │
│ ┌────────────────────────────────────────────────────────┐     │
│ │ Cost Engine (Doc 04)                                   │     │
│ │                                                         │     │
│ │ calculate_deal_costs(drivers, deal_type)               │     │
│ │   → Work item multipliers adjusted by deal type        │     │
│ │      (e.g., Identity Separation 2x higher for carveout)│     │
│ └────────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│ Phase 5: Narrative Synthesis                                    │
│                                                                  │
│ ┌────────────────────────────────────────────────────────┐     │
│ │ get_template_for_deal_type(deal_type)                  │     │
│ │   → Routes to correct template:                        │     │
│ │      - acquisition_narrative_template.py               │     │
│ │      - carveout_narrative_template.py                  │     │
│ │      - divestiture_narrative_template.py               │     │
│ └────────────────────────────────────────────────────────┘     │
│                          ↓                                      │
│ ┌────────────────────────────────────────────────────────┐     │
│ │ Final narrative has correct framing:                   │     │
│ │   - Acquisition: "Integration Assessment"              │     │
│ │   - Carveout: "Standalone Readiness Assessment"        │     │
│ │   - Divestiture: "Clean Separation Assessment"         │     │
│ └────────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────┘
```

---

## Deal Type Taxonomy

### Supported Deal Types

| deal_type Value | Display Name | Strategic Direction | Primary M&A Lenses | Key Question |
|-----------------|--------------|---------------------|-------------------|--------------|
| `"acquisition"` | Acquisition (Bolt-On/Platform) | **Integration** - Absorb target into buyer | Synergy Opportunity, Day-1 Continuity, Cost Driver | "How do we integrate?" |
| `"carveout"` | Carve-Out (Spin-Off) | **Separation** - Extract target from parent to operate standalone | TSA Exposure, Separation Complexity, Day-1 Continuity | "How do we stand alone?" |
| `"divestiture"` | Divestiture (Asset Sale) | **Clean Separation** - Remove target from seller with minimal disruption to RemainCo | Separation Complexity, Cost Driver, RemainCo Impact | "How do we cleanly separate?" |

**Database Constraint:** `deal_type VARCHAR(50) NOT NULL DEFAULT 'acquisition'`

**Validation Rule:** Must be one of `['acquisition', 'carveout', 'divestiture']`

**Aliases Accepted (normalized to canonical value):**
- Acquisition: `'bolt_on'`, `'platform'`, `'acquisition'`
- Carveout: `'carve_out'`, `'carve-out'`, `'spinoff'`, `'spin-off'`, `'carveout'`
- Divestiture: `'sale'`, `'disposal'`, `'divestiture'`

---

## Entity Semantics by Deal Type

**Critical Ambiguity Resolved:** The meaning of "buyer" and "target" changes based on deal type.

### Acquisition (Standard Case)

```
Entity Semantics:
  buyer   = Acquiring company (absorbing the target)
  target  = Company being acquired (absorbed into buyer)

Direction: target → buyer (target merges INTO buyer)

Example:
  Buyer: "TechCorp" (acquiring)
  Target: "StartupCo" (being acquired)

  Recommendation: "Consolidate StartupCo's Salesforce instance to TechCorp's instance"
  Correct? ✅ Yes - eliminate target system, use buyer system
```

### Carve-Out (Inverted Direction)

```
Entity Semantics:
  buyer   = NEW OWNER acquiring the carved-out unit
          (NOT the parent company - parent is not modeled)
  target  = Carved-out business unit (separating from parent)

Direction: target ← parent (target LEAVES parent, may join buyer)

Example:
  Buyer: "InvestorCo" (new owner, may not exist yet)
  Target: "DivisionX" (being carved out of ParentCo)
  Parent: "ParentCo" (NOT modeled as entity - appears in context only)

  Recommendation: "Stand up separate Salesforce instance for DivisionX"
  Correct? ✅ Yes - target needs standalone system, not consolidation
```

**Critical Rule for Carve-Outs:**
- **DO NOT recommend consolidation** of target → buyer
- **DO recommend standup** of target standalone capabilities
- **DO identify TSA services** needed from parent (not buyer)
- **Buyer inventory** may not even exist yet (greenfield new owner)

### Divestiture (Seller Perspective)

```
Entity Semantics:
  buyer   = Company acquiring the divested asset (acquirer side, may not be known)
  target  = Asset being divested (leaving the seller)

Direction: target → buyer (sold to external party)
          RemainCo ← target (removed from seller's operations)

Example:
  Buyer: "AcquirerCo" (may be unknown during diligence)
  Target: "AssetCo" (being sold)
  RemainCo: Seller's remaining business (NOT modeled as entity)

  Recommendation: "Separate AssetCo data from RemainCo ERP with minimal disruption"
  Correct? ✅ Yes - clean separation, protect RemainCo
```

**Critical Rule for Divestitures:**
- Focus on **RemainCo impact minimization** (seller's remaining business)
- **DO NOT recommend synergies** (buyer may not be known)
- **DO recommend clean data separation** and contract assignment

---

## M&A Lens Applicability by Deal Type

### The 5 M&A Lenses (from Existing Prompts)

| Lens | Core Question | When Applicable |
|------|---------------|-----------------|
| **Day-1 Continuity** | Will this prevent business operations on Day 1? | ALL deal types (universal) |
| **TSA Exposure** | Does this require transition services from seller? | Carveout (HIGH), Divestiture (MEDIUM), Acquisition (LOW) |
| **Separation Complexity** | How entangled is this with parent/other entities? | Carveout (HIGH), Divestiture (HIGH), Acquisition (LOW) |
| **Synergy Opportunity** | Where can we create value through consolidation? | Acquisition (HIGH), Carveout (N/A), Divestiture (N/A) |
| **Cost Driver** | What drives cost and how will the deal change it? | ALL deal types (universal) |

### Lens Emphasis Matrix

| Deal Type | Primary Lenses (MUST focus) | Secondary Lenses (Consider) | Ignore (Not applicable) |
|-----------|----------------------------|----------------------------|-------------------------|
| **Acquisition** | Synergy Opportunity, Day-1 Continuity | Cost Driver | TSA Exposure, Separation Complexity |
| **Carveout** | TSA Exposure, Separation Complexity, Day-1 Continuity | Cost Driver | Synergy Opportunity |
| **Divestiture** | Separation Complexity, Cost Driver | Day-1 Continuity, RemainCo Impact | Synergy Opportunity |

**Implementation:** This matrix drives prompt conditioning in Doc 03.

---

## Component Responsibilities

### UI Layer (Doc 05)
- **Responsibility:** Enforce deal_type selection before analysis starts
- **Input:** User selection from dropdown
- **Output:** deal_type stored in database, included in deal_context
- **Validation:** Client-side + server-side, prevent NULL values

### Analysis Runner (web/analysis_runner.py)
- **Responsibility:** Build deal_context dict and propagate to all agents
- **Input:** Deal record from database
- **Output:** deal_context dict with deal_type field
- **Current Status:** Already passes deal_type, but defaults to 'bolt_on' if missing (Doc 07 will fix)

### Reasoning Prompts (Doc 03)
- **Responsibility:** Inject deal-type-specific instructions into LLM prompts
- **Input:** deal_context dict with deal_type
- **Output:** Modified prompt emphasizing relevant lenses, de-emphasizing irrelevant
- **Implementation:** Conditional string injection in `get_*_reasoning_prompt()` functions

### Synergy Engine (Doc 02)
- **Responsibility:** Calculate consolidation synergies OR separation costs
- **Input:** deal_type parameter
- **Output:** List of SynergyOpportunity OR SeparationCost objects
- **Current Status:** Hardcoded to consolidation, no deal_type check (CRITICAL FIX)

### Cost Engine (Doc 04)
- **Responsibility:** Adjust work item costs based on deal structure
- **Input:** DealDrivers with deal_type field
- **Output:** CostEstimate with deal-type-adjusted multipliers
- **Current Status:** No deal_type awareness (enhancement)

### Narrative Synthesis (agents_v2/narrative_synthesis_agent.py)
- **Responsibility:** Route to correct template and framing
- **Input:** deal_type from deal_context
- **Output:** Narrative with acquisition/carveout/divestiture framing
- **Current Status:** Templates exist, need to verify routing works (investigate in this doc)

---

## Data Structures

### deal_context Dictionary (Canonical Format)

```python
deal_context = {
    "deal_id": str,              # Required: Unique deal identifier
    "deal_type": str,            # Required: "acquisition" | "carveout" | "divestiture"
    "target_name": str,          # Required: Target company name
    "buyer_name": str,           # Optional: Buyer company name (may be unknown)
    "industry": str,             # Optional: Industry classification
    "sub_industry": str,         # Optional: Sub-industry
    "employee_count": str,       # Optional: Range like "500-1000"
    "deal_value": str,           # Optional: Range like "$50M-100M"

    # Contextual fields (not stored in DB, computed)
    "target_doc_count": int,     # Number of target documents analyzed
    "buyer_doc_count": int,      # Number of buyer documents analyzed
}
```

**Validation:**
- `deal_id`: Must not be null
- `deal_type`: Must be one of allowed values, NOT NULL
- `target_name`: Must not be empty
- All other fields: Optional

### Database Schema (Already Exists)

```sql
-- From web/database.py:502-552
CREATE TABLE deals (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36),
    owner_id VARCHAR(36),

    -- Deal information
    name VARCHAR(255) NOT NULL DEFAULT '',
    target_name VARCHAR(255) NOT NULL,
    buyer_name VARCHAR(255) DEFAULT '',
    deal_type VARCHAR(50) DEFAULT 'acquisition',  -- CURRENT: Nullable with default
                                                   -- TARGET: NOT NULL (Doc 07 migration)
    industry VARCHAR(100) DEFAULT '',
    sub_industry VARCHAR(100) DEFAULT '',
    deal_value VARCHAR(50) DEFAULT '',

    -- Status tracking
    status VARCHAR(50) DEFAULT 'draft',
    ...
);
```

**Migration Path (Doc 07):**
1. Current: `deal_type VARCHAR(50) DEFAULT 'acquisition'` (allows NULL)
2. Interim: Set NOT NULL constraint, keep default
3. Final: Enforce at application level, remove default (fail fast if missing)

---

## Narrative Template Routing Investigation

**Question from Audit2:** Does narrative synthesis actually use `prompts/templates/*_template.py`?

**Investigation:**

```python
# From prompts/templates/__init__.py
def get_template_for_deal_type(deal_type: str) -> Dict[str, Any]:
    """Get the appropriate narrative template for a deal type."""
    dt = DealType.from_string(deal_type)
    config = DEAL_TYPE_CONFIGS[dt]

    if dt == DealType.ACQUISITION:
        return {
            "template": ACQUISITION_TEMPLATE,
            "emphasis": ACQUISITION_EMPHASIS,
            ...
        }
    elif dt == DealType.CARVEOUT:
        return {
            "template": CARVEOUT_TEMPLATE,
            "emphasis": CARVEOUT_EMPHASIS,
            "additional_sections": {
                "tsa_services": TSA_SERVICES_TEMPLATE,
                ...
            },
            ...
        }
    # ... etc
```

**Finding:** Template factory exists and is well-designed.

**Next Check:** Does `agents_v2/narrative_synthesis_agent.py` call this?

```bash
# Search for usage
grep -r "get_template_for_deal_type" agents_v2/
# Result: NOT FOUND in agents_v2/
```

**Status:** ⚠️ **Templates exist but are NOT wired up to narrative synthesis agent**

**Action Required:** Doc 03 must include wiring narrative synthesis to template factory.

**Implementation Location:**
- File: `agents_v2/narrative_synthesis_agent.py`
- Function: `generate_narrative()` or equivalent
- Change: Call `get_template_for_deal_type(deal_context['deal_type'])` and use returned template

---

## Dependencies

**Consumed By:**
- Doc 02 (Synergy Engine) - Needs entity semantics for carveouts
- Doc 03 (Reasoning Prompts) - Needs lens applicability matrix
- Doc 04 (Cost Engine) - Needs deal type taxonomy
- Doc 05 (UI Validation) - Needs allowed values and validation rules
- Doc 06 (Testing) - Needs all definitions for test case design
- Doc 07 (Migration) - Needs schema evolution path

**Depends On:** None (foundation document)

---

## Verification Strategy

### Unit Tests
1. Test `DealType.from_string()` with all aliases → normalizes correctly
2. Test deal_context validation → rejects invalid deal_types
3. Test entity semantics helper functions (if created) → returns correct direction

### Integration Tests
1. Create deal with each deal_type → stored correctly in database
2. Load deal and build deal_context → deal_type propagates to analysis
3. Pass deal_context to reasoning agent → receives correct value

### Manual Verification
1. Create 3 test deals (acquisition, carveout, divestiture) in UI
2. Verify database shows correct deal_type values
3. Check analysis logs show deal_context with correct deal_type
4. Confirm narrative uses correct template (after wiring implemented)

---

## Benefits

**Why This Architecture:**
1. **Single source of truth:** deal_type in database, propagated via deal_context everywhere
2. **Explicit over implicit:** No inferring deal type from documents, user selects explicitly
3. **Fail-fast validation:** Prevent analysis with missing/invalid deal_type
4. **Backward compatible:** Existing deals default to 'acquisition' until migrated
5. **Extensible:** Easy to add new deal types (e.g., "merger_of_equals") in future

**Alternatives Considered:**
- ❌ Infer deal type from documents using NLP → Too error-prone, user must confirm
- ❌ Allow NULL deal_type → Produces wrong recommendations silently
- ❌ Store deal_type in session only → Lost on page refresh, not persisted

---

## Expectations

### Success Criteria
- [ ] Deal type taxonomy documented with 3 supported values
- [ ] Entity semantics clarified for all 3 deal types (especially carveouts)
- [ ] M&A lens applicability matrix defined
- [ ] Data flow diagram shows deal_type propagation end-to-end
- [ ] Template routing investigated and documented
- [ ] All downstream documents can reference this as foundation

### Measurable Outcomes
- All 6 downstream docs reference this doc's definitions
- Zero ambiguity about what "buyer" and "target" mean in each deal type
- Template wiring issue identified and assigned to Doc 03

---

## Risks & Mitigations

### Technical Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| LLM ignores deal-type-specific instructions in prompt | Wrong recommendations despite conditioning | Medium | Doc 03 includes empirical testing with real prompts, tune instruction strength |
| Template routing not wired up | Narrative uses wrong framing despite correct internal logic | Medium | Doc 03 adds wiring, Doc 06 tests end-to-end |
| Entity semantics confusion for carveouts | Developers misunderstand buyer vs target direction | Low | This doc provides explicit examples, code comments reference this doc |
| Existing deals have NULL deal_type | Analysis crashes or produces wrong results | High | Doc 07 migration strategy handles gracefully with warnings |

### Implementation Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Downstream docs drift from this foundation | Inconsistent definitions across system | Medium | Explicit cross-references, review phase before implementation |
| Deal type validation inconsistently applied | Some code paths allow invalid values | Medium | Doc 05 enforces at UI + database, Doc 07 adds application-level validation |

---

## Results Criteria

### Acceptance Criteria (Must-Haves)
1. ✅ Three deal types defined with clear strategic direction
2. ✅ Entity semantics documented for each deal type with examples
3. ✅ M&A lens applicability matrix complete
4. ✅ End-to-end data flow diagram showing deal_type propagation
5. ✅ Database schema evolution path documented
6. ✅ Template routing status investigated and documented
7. ✅ All open questions from Audit2 resolved

### Success Metrics
- Downstream documents can be written without referring back to Audit1/Audit2
- Zero "TBD" or "TODO" placeholders in this document
- Implementation team understands entity semantics without further explanation

---

## Open Questions Resolution

### Q1: Entity semantics for carveouts - RESOLVED ✅

**Answer:** "buyer" = NEW OWNER (acquiring the carved-out unit), NOT the parent company.

**Rationale:**
- Parent company is not modeled as an entity (appears in context only)
- Buyer represents the future owner of the standalone target
- Target is the carved-out business unit

**Impact:** Synergy engine must NOT recommend consolidating target → buyer in carveouts. Instead, recommend standing up standalone capabilities for target.

### Q2: Existing deal distribution - DOCUMENTED ⚠️

**Default Assumption:** 70% acquisition, 20% carveout, 10% divestiture (industry standard for PE deals)

**Action:** Doc 07 migration will handle existing deals gracefully with default to 'acquisition' and warning message.

**Verification:** Query production database in Doc 07 if available.

### Q3: Narrative synthesis routing - INVESTIGATED ✅

**Finding:** Templates exist but NOT wired up to narrative synthesis agent.

**Action:** Doc 03 will add wiring call to `get_template_for_deal_type()`.

**Location:** `agents_v2/narrative_synthesis_agent.py`

### Q4: Deal type change mid-analysis - DOCUMENTED ⚠️

**Answer:** Invalidate analysis cache if deal_type changes, force re-run with warning.

**Implementation:** Doc 05 will add UI warning + cache invalidation logic.

**Rationale:** Cached recommendations may be incorrect for new deal type, safer to re-run.

---

## Next Steps

**Immediate Actions After This Doc:**
1. Proceed to Docs 02, 03, 04 (can be written in parallel)
2. Reference this doc's definitions in all downstream documents
3. Validate assumptions in Doc 06 testing phase

**Implementation Phase:**
1. Use this doc as source of truth for deal type semantics
2. Add code comments linking back to this doc's section numbers
3. Review this doc during code review to ensure alignment

---

**Document Status:** ✅ COMPLETE

**Version:** 1.0
**Last Updated:** 2026-02-11
**Cross-References:** Referenced by Docs 02-07
