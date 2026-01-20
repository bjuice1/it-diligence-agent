# IT Due Diligence Reasoning Methodology

## Overview

This document describes the methodology behind our IT Due Diligence reasoning engine - a system designed to think like an expert IT M&A advisor. The core principle is that **every output must be explainable through a chain of reasoning**, not just pattern matching or lookup tables.

## The Problem We're Solving

Traditional IT due diligence tools suffer from several limitations:

1. **Black box outputs** - "The cost is $5M" with no explanation of why
2. **Generic buckets** - One-size-fits-all estimates that don't reflect actual company situations
3. **No deal-type awareness** - Same analysis for carveouts and acquisitions when they're fundamentally different
4. **Missing the "so what"** - Facts without implications

Our methodology addresses these by building a system that:
- **Reasons through facts** to derive implications
- **Understands deal context** to apply appropriate logic
- **Derives specific activities** from identified gaps
- **Explains every output** with traceable reasoning

---

## The Reasoning Chain

The engine follows a structured reasoning process:

```
                    INPUTS
                      │
        ┌─────────────┼─────────────┐
        │             │             │
    Document      Meeting       Deal Context
     Facts         Notes       (type, buyer)
        │             │             │
        └─────────────┼─────────────┘
                      │
                      ▼
            ┌─────────────────┐
            │  PATTERN        │
            │  RECOGNITION    │
            │                 │
            │ • Parent deps   │
            │ • Tech stack    │
            │ • Gaps/risks    │
            │ • Quantities    │
            └────────┬────────┘
                     │
                     ▼
            ┌─────────────────┐
            │  CONSIDERATION  │
            │  GENERATION     │
            │                 │
            │ What we found   │
            │ + What it means │
            │ + Why it matters│
            └────────┬────────┘
                     │
                     ▼
            ┌─────────────────┐
            │  DEAL-TYPE      │
            │  LOGIC          │
            │                 │
            │ Carveout →      │
            │   Separation    │
            │ Acquisition →   │
            │   Integration   │
            └────────┬────────┘
                     │
                     ▼
            ┌─────────────────┐
            │  ACTIVITY       │
            │  DERIVATION     │
            │                 │
            │ Gap → Activity  │
            │ + Why needed    │
            │ + Cost          │
            │ + Timeline      │
            │ + TSA impact    │
            └────────┬────────┘
                     │
                     ▼
                  OUTPUTS
            ┌─────────────────┐
            │ • Activities    │
            │ • Costs         │
            │ • TSA needs     │
            │ • Timeline      │
            │ • Narrative     │
            └─────────────────┘
```

---

## Core Concepts

### 1. Facts vs. Considerations

**Facts** are raw information extracted from documents or provided by users:
```
FACT: "Users authenticate through parent Azure AD with federated SSO"
```

**Considerations** are derived insights that explain what the fact means:
```
CONSIDERATION:
  Finding: "Identity services are provided by parent"
  Implication: "Post-separation, target will need standalone identity platform"
  Why Critical: "Without identity services, users cannot authenticate to ANY system. Business stops."
```

The transformation from fact to consideration is where expert reasoning begins.

### 2. Deal-Type Awareness

The same fact has different implications depending on deal type:

| Fact | Carveout Implication | Acquisition Implication |
|------|---------------------|------------------------|
| "Uses Gmail" | Need to provision standalone email or migrate | Need to migrate to buyer's M365 (if buyer uses Microsoft) |
| "Parent provides identity" | Must build standalone identity platform | Integrate users into buyer's directory |
| "Hosted in parent data center" | Must migrate to standalone infrastructure | Connect to buyer's infrastructure |

The engine applies **different reasoning paths** based on deal type.

### 3. Activity Derivation (Not Lookup)

We don't simply look up "identity separation = $500K". Instead, we derive activities:

```
CONSIDERATION: Identity services provided by parent
        ↓
DEAL TYPE: Carveout
        ↓
DERIVED ACTIVITIES:
  1. Design standalone identity architecture
     Why: Must have target state design before building
     Cost: $50K-120K

  2. Provision new identity platform
     Why: Required before users can be migrated
     Cost: $75K-200K
     TSA: Yes (3-6 months)

  3. Migrate 2,500 user accounts
     Why: Users must exist in new directory before cutover
     Cost: $15-40 per user = $37.5K-100K
     TSA: Yes (3-6 months)

  4. Reconfigure SSO for 45 applications
     Why: Apps must point to new identity provider
     Cost: $2K-8K per app = $90K-360K
     TSA: Yes (3-6 months)

TOTAL: $252.5K - $780K (derived from specific activities, not a bucket)
```

### 4. The "Why Needed" Chain

Every activity traces back to facts through a reasoning chain:

```
FACT: "Users authenticate through parent Azure AD"
  ↓
CONSIDERATION: "Identity services provided by parent"
  ↓
IMPLICATION: "Post-separation, target needs standalone identity"
  ↓
ACTIVITY: "Migrate 2,500 user accounts"
  ↓
WHY NEEDED: "Because identity services are provided by parent.
             Without identity, users cannot authenticate.
             Business stops."
```

This chain makes every cost explainable.

---

## Deal Type Logic

### Carveout / Divestiture

**Key Characteristic**: Target must BUILD standalone capabilities

**Reasoning Pattern**:
1. Identify parent dependencies (what parent provides today)
2. For each dependency, derive separation activities
3. Identify TSA requirements (bridge until standalone)
4. Calculate TSA exit costs

**Typical TSA Services**:
- Identity & Authentication (Day-1 Critical)
- Email & Collaboration (Day-1 Critical)
- Infrastructure & Hosting (Day-1 Critical)
- Network Services (Day-1 Critical)
- Security Monitoring (Day-1 Critical)
- IT Support (Day-1 Important)
- ERP Services (Day-1 Important)

### Acquisition

**Key Characteristic**: Target moves INTO buyer's environment

**Reasoning Pattern**:
1. Identify target's technology stack
2. Compare to buyer's technology stack
3. Identify mismatches requiring migration
4. Derive integration activities
5. Identify synergy opportunities

**Technology Mismatch Examples**:
```
Target: Gmail          →  Migration: Gmail to M365
Buyer: Microsoft 365   →  Why: Unified collaboration required

Target: AWS            →  Migration: AWS to Azure (or multi-cloud)
Buyer: Azure           →  Why: Operational efficiency, cost optimization

Target: Okta           →  Migration: Okta to Azure AD
Buyer: Azure AD        →  Why: Single identity platform
```

**Key Difference from Carveout**:
- Less TSA required (buyer provides destination)
- Focus on migration/integration, not building standalone
- Synergy opportunities from consolidation

---

## Milestone Framework

### Day 1 (Close)

**Critical Question**: Can business operate the moment the deal closes?

**Day-1 Critical Services**:
- Users can log in (Identity)
- Email works (Communication)
- Critical applications accessible (Applications)
- Network connectivity maintained (Network)
- Security monitoring active (Security)

**For Carveouts**: These services come from TSA
**For Acquisitions**: Buyer may already provide these

### Day 100

**Critical Question**: Have we exited critical TSAs and established baseline?

**Typical Day-100 Milestones**:
- Identity separation/integration complete
- Email migration complete
- Network separation/integration complete
- Security baseline established
- Service desk transition complete

### Year 1

**Critical Question**: Is separation/integration substantially complete?

**Typical Year-1 Milestones**:
- All TSAs exited
- ERP separation/consolidation complete
- Application rationalization complete
- Optimized run-rate achieved

---

## Cost Derivation Methodology

### Principle: Anchored Estimation with Fact-Based Adjustments

We use **market-based anchors** (defensible benchmarks) adjusted by **fact-based modifiers** (company-specific):

```
BASE COST (from market anchor)
  × QUANTITY (from extracted facts)
  × ADJUSTMENTS (from identified patterns)
  = DERIVED COST
```

### Example:

```
Activity: Migrate user accounts
Base Anchor: $15-40 per user (market benchmark)
Quantity: 2,500 users (extracted from facts)
Adjustments:
  - Financial services (+20%): Regulatory complexity
  - Large scale (+15%): >2000 users

Calculation:
  Low:  $15 × 2,500 × 1.20 × 1.15 = $51,750
  High: $40 × 2,500 × 1.20 × 1.15 = $138,000
```

### Why This Matters

1. **Defensible**: Based on market benchmarks, not made-up numbers
2. **Traceable**: Every adjustment links to a specific fact
3. **Reproducible**: Same inputs produce same outputs
4. **Explainable**: Can show exactly why estimate is X, not Y

---

## Meeting Notes Integration

Meeting notes allow users to refine the AI's analysis with contextual information:

```python
meeting_notes = '''
Buyer confirmed this is a carveout - target will operate standalone
Parent wants clean separation within 12 months
TSA budget is limited - buyer prefers shorter TSAs
45 applications integrated with parent SSO
Target has 25TB of data in parent storage
'''
```

The engine:
1. Parses meeting notes into fact-like statements
2. Extracts quantitative information (45 apps, 25TB)
3. Applies contextual constraints (shorter TSAs)
4. Adjusts reasoning accordingly

This allows the expert's judgment to refine the automated analysis.

---

## Output Structure

### Executive Summary
High-level findings with key numbers:
- Deal type and scope
- Key findings (what we found → what it means)
- Total cost estimate
- TSA summary
- Critical timeline

### Workstream Breakdown
For each workstream:
- Status (major change, minor change, no change)
- Activities with reasoning
- Cost estimate
- Timeline
- TSA requirements

### Detailed Narrative
For each activity:
- What it is
- Why it's needed (traced to facts)
- Cost range
- Dependencies
- TSA impact

### Traceability
- Input hash (for reproducibility verification)
- Fact IDs linked to activities
- Consideration IDs linked to reasoning

---

## What Makes This Different

| Traditional Approach | Our Methodology |
|---------------------|-----------------|
| "Identity separation costs $500K" | "Identity separation costs $252K-780K because: 2,500 users × $15-40/user for migration + $50-120K for design + ..." |
| Same estimate for all deals | Different logic for carveout vs acquisition |
| Generic buckets | Derived from specific activities |
| No explanation | Full reasoning chain |
| Static lookup tables | Dynamic derivation from facts |
| AI-generated numbers | Market anchors + fact-based adjustments |

---

## Implementation Files

| File | Purpose |
|------|---------|
| `reasoning_engine.py` | Core reasoning logic |
| `deal_framework.py` | Deal type and milestone definitions |
| `workstream_model.py` | Workstream-based activity templates |
| `cost_model.py` | Cost anchors and adjustment rules |

---

## Future Enhancements

1. **Learning from feedback**: Incorporate actual deal outcomes to refine estimates
2. **Industry-specific patterns**: More nuanced logic for healthcare, financial services, etc.
3. **Integration playbooks**: Buyer-specific integration patterns
4. **Risk quantification**: Probability-weighted cost scenarios
5. **Timeline optimization**: Critical path analysis with resource constraints

---

## Conclusion

This methodology represents a fundamental shift in how IT due diligence analysis is performed. By building a system that **reasons through facts** rather than simply looking up values, we create outputs that are:

- **Explainable**: Every cost traces to activities, which trace to considerations, which trace to facts
- **Defensible**: Based on market benchmarks, not AI hallucination
- **Deal-aware**: Different logic for different deal types
- **Refinable**: Meeting notes allow expert judgment to guide the analysis
- **Reproducible**: Same inputs produce same outputs (deterministic reasoning)

The goal is not to replace expert judgment, but to **codify expert reasoning** so that every analysis reflects how a seasoned IT M&A advisor would think through the problem.
