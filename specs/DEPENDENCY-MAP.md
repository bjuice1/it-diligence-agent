# Specification Dependency Map & Execution Strategy
**Date:** February 10, 2026
**Total Specifications:** 25 across 4 initiatives
**Purpose:** Define build order to avoid blockers and maximize parallel work

---

## Executive Summary

You have **25 specifications** across **4 major initiatives**. Building them in the wrong order will create blockers. This document maps dependencies and provides 3 execution strategies.

**Quick Answer - Critical Path (Must Do First):**
1. **Session Persistence** (BLOCKING: Users can't use system without it)
2. **Inventory Fix** (BLOCKING: Data quality affects all analysis)
3. **Analysis Depth Enhancement - Spec 05 MVP** (High user value, low dependencies)
4. Everything else (based on user feedback)

---

## Dependency Graph (Visual)

```
CRITICAL PATH (Do These First):
┌─────────────────────────────────────────────────────────────┐
│  SESSION PERSISTENCE (MUST BE FIRST)                        │
│  ├─ 01: User-Deal Association Schema                       │
│  ├─ 02: Deal Selection API                                 │
│  ├─ 03: Automatic Context Restoration                      │
│  └─ 04: Session Architecture Hardening                     │
│      └─ BLOCKS: Everything else (users can't log in)       │
└─────────────────────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────────────────────┐
│  INVENTORY FIX (DO SECOND)                                  │
│  ├─ 01: Pipeline Wiring                                    │
│  ├─ 02: LLM Fact Promotion                                 │
│  ├─ 03: Entity Enforcement                                 │
│  ├─ 04: UI Inventory Source Switch                         │
│  └─ 05: Reconciliation and Audit                           │
│      └─ BLOCKS: Analysis Depth (needs clean inventory)     │
│              Business Context (needs accurate data)        │
└─────────────────────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────────────────────┐
│  ANALYSIS DEPTH - MVP (DO THIRD)                           │
│  └─ 05-MVP: Explanatory UI Enhancement                     │
│      ├─ REQUIRES: Session Persistence (users logged in)    │
│      ├─ REQUIRES: Inventory Fix (data exists to display)   │
│      └─ BLOCKS: Nothing (standalone feature)               │
└─────────────────────────────────────────────────────────────┘

PARALLEL TRACKS (Can Do After Critical Path):
┌────────────────────────────┐  ┌────────────────────────────┐
│  ANALYSIS DEPTH (Full)     │  │  BUSINESS CONTEXT          │
│  ├─ 01: Resource Model     │  │  ├─ 01: Company Profile    │
│  ├─ 02: Calculator         │  │  ├─ 02: Industry Taxonomy  │
│  ├─ 03: Integration        │  │  ├─ 03: Template Dataset   │
│  ├─ 04: Hierarchy          │  │  ├─ 04: Benchmark Engine   │
│  ├─ 06: Reasoning Expand   │  │  └─ 05: Business UI        │
│  └─ 07: Feedback System    │  └─────────────────────────────┘
└────────────────────────────┘
```

---

## Detailed Dependency Matrix

### Session Persistence Fix (5 specs)

| Spec | Depends On | Blocks | Effort | Priority |
|------|-----------|---------|---------|----------|
| 00: Implementation Guide | None | All other specs (meta-doc) | 0 days | P0 |
| 01: User-Deal Schema | None | 02, 03 | 2 days | P0 |
| 02: Deal Selection API | 01 | 03 | 3 days | P0 |
| 03: Auto-Restore | 01, 02 | Nothing | 2 days | P0 |
| 04: Session Hardening | 01, 02 | Nothing | 3 days | P0 |

**Total Effort:** 10 days (2 weeks)

**Why P0:** Users cannot use the system if sessions break. This is the foundation.

**Status Check Needed:** Is this already done? (You mentioned it in git commits but didn't confirm it's deployed)

---

### Inventory Fix (5 specs)

| Spec | Depends On | Blocks | Effort | Priority |
|------|-----------|---------|---------|----------|
| 00: Build Manifest | None | Nothing (meta-doc) | 0 days | P1 |
| 01: Pipeline Wiring | Session Persistence | 02, 03, 04 | 3 days | P1 |
| 02: LLM Fact Promotion | 01 | 05 | 4 days | P1 |
| 03: Entity Enforcement | 01 | Analysis Depth (needs clean entities) | 3 days | P1 |
| 04: UI Source Switch | 01, 02, 03 | 05 | 2 days | P1 |
| 05: Reconciliation | 01-04 | Nothing | 3 days | P1 |

**Total Effort:** 15 days (3 weeks)

**Why P1:** Dirty inventory data breaks all analysis. Analysis Depth features display garbage if inventory is broken.

**Blocker:** Analysis Depth Spec 03 (Resource-Cost Integration) assumes clean inventory data with accurate app counts, infrastructure counts, etc.

---

### Analysis Depth Enhancement (9 specs)

#### Core Specs (User-Facing)

| Spec | Depends On | Blocks | Effort | Priority |
|------|-----------|---------|---------|----------|
| 00: Build Manifest | None | Nothing (meta-doc) | 0 days | P2 |
| 05-MVP: UI Enhancement | Session Persistence, Inventory Fix | Nothing | **2 weeks** | **P1 (HIGH VALUE)** |
| 05-Full: UI Enhancement | 01, 02, 03, 04 | Nothing | 3 weeks | P2 (defer) |
| 01: Resource Model | Inventory Fix | 02, 03 | 1.5 weeks | P2 |
| 02: Calculator | 01 | 03 | 1.5 weeks | P2 |
| 03: Integration | 01, 02 | 05-Full | 1 week | P2 |
| 04: Hierarchy | 01, 03 | 05-Full | 2 weeks | P2 |
| 06: Reasoning Expand | Inventory Fix | Nothing | 2 weeks | P2 |
| 07: Feedback System | None | Nothing | 2 weeks | P3 (defer) |
| 08: Testing | All above | Nothing | 1.5 weeks | P2 |

**Total Effort (MVP Path):** 2 weeks
**Total Effort (Full Path):** 13 weeks

**Critical Insight:** Spec 05-MVP is **standalone** - you can ship it without building Specs 01-04, 06-07.

---

### Business Context (6 specs)

| Spec | Depends On | Blocks | Effort | Priority |
|------|-----------|---------|---------|----------|
| 00: Build Manifest | None | Nothing (meta-doc) | 0 days | P3 |
| 01: Company Profile | Inventory Fix | 02, 03 | 1 week | P3 |
| 02: Industry Taxonomy | None | 03, 04 | 1 week | P3 |
| 03: Template Dataset | 01, 02 | 04 | 2 weeks | P3 |
| 04: Benchmark Engine | 03 | 05 | 1.5 weeks | P3 |
| 05: Business UI | 01-04 | Nothing | 1.5 weeks | P3 |
| 06: Testing | All above | Nothing | 1 week | P3 |

**Total Effort:** 8 weeks

**Why P3:** Business context is nice-to-have but not blocking user complaints. Defer until after Analysis Depth MVP ships and gets feedback.

---

### Root-Level Numbered Specs (7 specs)

These appear to be **legacy or alternative versions** of the initiative specs above. Let me map them:

| Spec | Initiative Equivalent | Status | Action |
|------|----------------------|---------|---------|
| 01: Preprocessing Unicode Fix | Inventory Fix 01 (part of it) | Redundant | Merge into Inventory Fix |
| 02: Category Mapping | Inventory Fix (part of pipeline) | Redundant | Already covered |
| 03: FactStore Linking | Inventory Fix 03 | Redundant | Already covered |
| 04: Entity Propagation | Inventory Fix 03 | Redundant | Already covered |
| 05: Cost Buildup Wiring | Analysis Depth 03 | Redundant | Already covered |
| 06: Reasoning Prompt Guidance | Analysis Depth 06 | Redundant | Already covered |
| 07: Validation & Testing | Multiple specs | Redundant | Covered in 08s |

**Recommendation:** **Ignore these 7 specs.** They're earlier versions or fragments of the organized initiative specs. Focus on the 4 initiatives (Session, Inventory, Analysis, Business).

---

## Execution Strategies (Choose One)

### STRATEGY A: Fastest User Value (RECOMMENDED)

**Goal:** Ship something users can see in 4 weeks

**Timeline:**
```
Week 1-2:   Session Persistence (if not done) OR Inventory Fix (if sessions done)
Week 3-4:   Analysis Depth - Spec 05 MVP
Week 5:     User feedback, decide next steps
```

**Deliverables:**
- Users can log in reliably (Session Persistence)
- Users see "why findings matter" (Spec 05 MVP)

**Risk:** Low (small scope, clear wins)

**Next Steps After Week 5:**
- If users love Spec 05 MVP → Build Spec 06 (Reasoning Expansion)
- If users want cost transparency → Build Specs 01-03 (Resource Model)
- If users want something else → Pivot

---

### STRATEGY B: Complete Analysis Depth First

**Goal:** Ship all Analysis Depth features before starting Business Context

**Timeline:**
```
Week 1-2:   Session Persistence (if needed)
Week 3-5:   Inventory Fix
Week 6-7:   Analysis Depth - Spec 05 MVP (ship, get feedback)
Week 8-9:   Analysis Depth - Spec 01 (Resource Model)
Week 10-11: Analysis Depth - Spec 02 (Calculator)
Week 12:    Analysis Depth - Spec 03 (Integration)
Week 13-14: Analysis Depth - Spec 04 (Hierarchy)
Week 15-16: Analysis Depth - Spec 06 (Reasoning)
Week 17-18: Analysis Depth - Spec 07 (Feedback)
Week 19:    Analysis Depth - Spec 08 (Testing)
```

**Total:** 19 weeks (4.5 months)

**Risk:** Medium (long timeline, no user validation until Week 19)

---

### STRATEGY C: Parallel Initiatives (Requires Help)

**Goal:** Build Analysis Depth AND Business Context simultaneously

**Timeline:**
```
Week 1-2:   Session Persistence (if needed)
Week 3-5:   Inventory Fix

PARALLEL TRACKS (Weeks 6-13):
  Track A (You):     Analysis Depth Specs 01-04
  Track B (Helper):  Business Context Specs 01-04

Week 14-15: Integration & testing
```

**Total:** 15 weeks (3.5 months)

**Risk:** High (coordination overhead, requires hiring help)

---

## Recommended Execution Plan (Detailed)

### Phase 0: Pre-Flight Check (1 Day)

**Tasks:**
1. ✅ **Verify Session Persistence is deployed and working**
   - Check Railway logs: Any "lost deal selection" errors?
   - Test: Log in, select deal, close browser, reopen → Deal still selected?
   - If broken → Phase 1 is Session Persistence
   - If working → Skip to Phase 2

2. ✅ **Verify Inventory Fix status**
   - Check: Are apps linking to infrastructure entities correctly?
   - Check: Do inventory counts match actual data?
   - If broken → Phase 2 is Inventory Fix
   - If working → Skip to Phase 3

3. ✅ **Check current user pain points**
   - Email 3-5 active users: "What's the #1 thing frustrating you?"
   - If "can't log in" → Session is P0
   - If "data is wrong" → Inventory is P0
   - If "need more context" → Analysis Depth is P1

---

### Phase 1: Foundation (2 Weeks) - ONLY IF NEEDED

**IF Session Persistence is broken:**
- Week 1-2: Implement Session Persistence Specs 01-04
- Deploy, verify sessions work
- THEN move to Phase 2

**IF Session Persistence is working:**
- Skip to Phase 2

---

### Phase 2: Data Quality (3 Weeks) - IF NEEDED

**IF Inventory is broken:**
- Week 1: Inventory Fix - Spec 01 (Pipeline Wiring)
- Week 2: Inventory Fix - Specs 02-03 (Fact Promotion + Entity Enforcement)
- Week 3: Inventory Fix - Specs 04-05 (UI Switch + Reconciliation)
- Deploy, verify inventory counts are accurate
- THEN move to Phase 3

**IF Inventory is clean:**
- Skip to Phase 3

---

### Phase 3: High-Value Feature (2 Weeks) - START HERE

**Implement Analysis Depth - Spec 05 MVP:**
- Week 1, Days 1-3: FindingCard component + inline reasoning
- Week 1, Days 4-5: CostBreakdownModal component
- Week 2, Days 1-2: API enhancements + wiring
- Week 2, Days 3-4: Testing + bug fixes
- Week 2, Day 5: Deploy to Railway

**Ship, announce to users, collect feedback for 1 week.**

---

### Phase 4: Decision Point (Week After Ship)

**Measure:**
- Click-through rate on "Explain This" button
- Click-through rate on "View Calculation" button
- User feedback (Google Form or email)

**Scenarios:**

**Scenario A: Users love it, want more depth**
→ Proceed to Phase 5 (Build Specs 01-04 for full Analysis Depth)

**Scenario B: Users don't use it**
→ Interview users, pivot to different feature

**Scenario C: Users want different things (cost accuracy, not explanations)**
→ Pivot to Business Context or Cost Engine improvements

---

### Phase 5: (CONDITIONAL) Full Analysis Depth (11 Weeks)

**Only do this if Phase 4 = Scenario A.**

- Week 1-2: Spec 01 (Resource Model)
- Week 3-4: Spec 02 (Calculator)
- Week 5: Spec 03 (Integration)
- Week 6-7: Spec 04 (Hierarchy)
- Week 8-9: Spec 06 (Reasoning Expansion)
- Week 10-11: Spec 07 (Feedback System)

**Ship full Analysis Depth suite.**

---

## Dependency Summary Table

| Initiative | Must Complete First | Blocks | Recommended Priority |
|-----------|-------------------|---------|---------------------|
| **Session Persistence** | Nothing | Everything (users can't use app) | **P0 - IF BROKEN** |
| **Inventory Fix** | Session Persistence | Analysis Depth, Business Context | **P1 - IF BROKEN** |
| **Analysis Depth - Spec 05 MVP** | Session + Inventory | Nothing | **P1 - HIGH VALUE** |
| **Analysis Depth - Full** | Spec 05 MVP + user validation | Nothing | P2 - Conditional |
| **Business Context** | Inventory Fix | Nothing | P3 - Defer |
| **Numbered Specs (01-07)** | N/A | Nothing | **P0 - IGNORE (redundant)** |

---

## Critical Path Duration

**Assuming Session + Inventory are already done:**
- Analysis Depth Spec 05 MVP: **2 weeks**
- User validation: **1 week**
- **Total to first user value: 3 weeks**

**Assuming Session + Inventory need to be built:**
- Session Persistence: 2 weeks
- Inventory Fix: 3 weeks
- Analysis Depth Spec 05 MVP: 2 weeks
- User validation: 1 week
- **Total to first user value: 8 weeks**

**Assuming you want full Analysis Depth (all 8 specs):**
- Session: 2 weeks
- Inventory: 3 weeks
- Analysis Depth (all): 13 weeks
- **Total: 18 weeks** (your original estimate was accurate!)

---

## Blocker Matrix (What Blocks What)

```
SESSION PERSISTENCE
  └─ BLOCKS → Inventory Fix (users can't access inventory)
     └─ BLOCKS → Analysis Depth (needs clean data)
        └─ BLOCKS → Business Context (needs accurate benchmarks)

If you skip Session Persistence and it's broken:
  → Users can't log in
  → Everything else is useless

If you skip Inventory Fix and data is dirty:
  → Analysis Depth displays wrong numbers
  → Business Context benchmarks are inaccurate
  → User trust erodes
```

---

## Quick Start Guide

**If you want to start coding TODAY:**

1. **Run Pre-Flight Check (30 min):**
   ```bash
   # Check sessions work
   # 1. Log into Railway app
   # 2. Select a deal
   # 3. Close browser completely
   # 4. Reopen, log in again
   # 5. Is deal still selected? YES → Sessions work | NO → Build Session Persistence first

   # Check inventory is clean
   # 1. Go to Applications page
   # 2. Pick an app
   # 3. Does it show correct infrastructure links? YES → Inventory works | NO → Build Inventory Fix first
   ```

2. **Choose Starting Point:**
   - If sessions broken → Start with Session Persistence Spec 01
   - If inventory dirty → Start with Inventory Fix Spec 01
   - If both work → **Start with Analysis Depth Spec 05 MVP** ← RECOMMENDED

3. **Clone the Spec 05 MVP I just wrote:**
   ```bash
   # It's in: specs/analysis-depth-enhancement/05-explanatory-ui-enhancement-MVP.md
   # Read it, start with Week 1 Day 1 (FindingCard component)
   # Claude Code will help you write it fast
   ```

4. **Ship in 2 weeks, get feedback, THEN decide what's next.**

---

## Files Created

**This Document:** `specs/DEPENDENCY-MAP.md`
**MVP Spec:** `specs/analysis-depth-enhancement/05-explanatory-ui-enhancement-MVP.md`

**Next Steps:**
1. Run Pre-Flight Check (verify Session + Inventory status)
2. If both work: Start coding Spec 05 MVP (use the MVP doc I created)
3. If broken: Start with Session Persistence or Inventory Fix first

**Want me to help with Pre-Flight Check?** I can:
- Review Railway logs to check session health
- Check database to verify inventory linking is working
- Help you decide which spec to start with

**What do you want to do next?**
