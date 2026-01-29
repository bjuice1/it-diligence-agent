# Deal Lens Architecture - Design Document

## Overview

This document captures the architectural thinking around how the IT Due Diligence system handles different deal types, perspectives, and industry considerations.

---

## Current Scope: Buy-Side Due Diligence

**The system is designed for buy-side IT due diligence.** Sell-side (VDD, seller prep) will be a separate implementation with different outputs, workflows, and considerations.

### Buy-Side Deal Types Supported

| Deal Type | Key Question | Primary Lenses |
|-----------|--------------|----------------|
| **Bolt-on Acquisition** | "How do we integrate?" | Day 1 Continuity, Synergy Opportunity, Cost Driver |
| **Platform Acquisition** | "Can this be our new foundation?" | Day 1 Continuity, Scalability, Cost Driver |
| **Carve-out (Buy-side)** | "How do we stand alone?" | Day 1 Continuity, TSA Exposure, Separation Complexity |
| **Merger** | "How do we combine?" | Day 1 Continuity, Synergy Opportunity, Separation Complexity |

### What Buy-Side Cares About

1. **Risk identification** - What could go wrong post-close?
2. **Cost visibility** - What will this cost to run/integrate?
3. **Day 1 readiness** - Will the business operate on close?
4. **Integration complexity** - How hard is this to absorb?
5. **TSA exposure** (for carve-outs) - What services need transition agreements?

---

## Deal Type Implementation

### Current State

The system captures `deal_type` in:
- Upload form (`bolt_on`, `carve_out`)
- Deal model (database)
- Session context (passed to analysis)
- Narrative synthesis (affects output framing)

### How Deal Type Should Affect Analysis

#### 1. Lens Weighting

Different deal types should weight M&A lenses differently:

```
LENS_WEIGHTS_BY_DEAL_TYPE = {
    "bolt_on": {
        "day_1_continuity": 1.0,      # Always critical
        "synergy_opportunity": 1.2,    # Elevated - integration value
        "cost_driver": 1.0,
        "tsa_exposure": 0.5,           # Less relevant unless shared services
        "separation_complexity": 0.3   # Rarely applies
    },
    "carve_out": {
        "day_1_continuity": 1.0,      # Always critical
        "synergy_opportunity": 0.5,    # Less relevant
        "cost_driver": 1.0,
        "tsa_exposure": 1.5,           # ELEVATED - primary concern
        "separation_complexity": 1.5   # ELEVATED - primary concern
    }
}
```

#### 2. Severity Adjustment

Same finding, different severity based on deal type:

| Finding | Bolt-on Severity | Carve-out Severity |
|---------|------------------|-------------------|
| "AD integrated with parent" | Medium (integration project) | **Critical** (Day 1 blocker) |
| "Shared ERP instance" | Medium (migration needed) | **Critical** (TSA required) |
| "No DR site" | High (risk) | High (risk) |
| "Legacy app on unsupported OS" | High (security risk) | Medium (inherit the problem) |

#### 3. Question Generation

Deal type should drive what questions are asked:

**Bolt-on specific:**
- "What systems overlap with buyer's existing stack?"
- "Where are the integration touchpoints?"
- "What licenses can be consolidated?"

**Carve-out specific:**
- "What services come from parent/corporate?"
- "What is the TSA runway for each service?"
- "What standalone capability exists today?"

### Implementation Plan

**Phase 1: Severity Multipliers** (Low effort, high impact)
- Add `deal_type_severity_multiplier()` function
- Apply to risk scoring when deal_type indicates carve-out + shared service pattern

**Phase 2: Lens Weighting** (Medium effort)
- Weight findings by lens relevance for deal type
- Surface TSA-lens findings more prominently for carve-outs

**Phase 3: Dynamic Question Generation** (Future)
- Generate deal-type-specific open questions
- Customize data requests based on deal type

---

## Industry Considerations

### Why Industry Matters

Industry is **not cosmetic metadata** - it should drive:

1. **Compliance weighting** - Which regulations apply?
2. **Benchmark selection** - What are peer comparisons?
3. **Risk calibration** - What's "normal" for this industry?
4. **Technology expectations** - What capabilities are table stakes?

### Industry-Specific Considerations Inventory

The plan is to build an **Industry Considerations Inventory** that drives analysis behavior:

```python
INDUSTRY_CONSIDERATIONS = {
    "financial_services": {
        "compliance_frameworks": ["SOX", "PCI-DSS", "GLBA", "FFIEC"],
        "elevated_domains": ["cybersecurity", "identity"],
        "benchmark_peer_set": "financial_services",
        "regulatory_severity_multiplier": 1.5,  # Compliance gaps are more severe
        "typical_it_spend_pct": "5-8% of revenue",
        "key_questions": [
            "SOX control environment maturity?",
            "PCI scope and compliance status?",
            "Regulatory exam findings?"
        ]
    },
    "healthcare": {
        "compliance_frameworks": ["HIPAA", "HITRUST", "state privacy laws"],
        "elevated_domains": ["cybersecurity", "applications"],  # PHI handling
        "benchmark_peer_set": "healthcare",
        "regulatory_severity_multiplier": 1.5,
        "typical_it_spend_pct": "3-5% of revenue",
        "key_questions": [
            "HIPAA compliance program maturity?",
            "PHI data mapping and controls?",
            "BAA inventory and management?"
        ]
    },
    "manufacturing": {
        "compliance_frameworks": ["industry-specific", "export controls"],
        "elevated_domains": ["infrastructure", "network"],  # OT/IT convergence
        "benchmark_peer_set": "manufacturing",
        "regulatory_severity_multiplier": 1.0,
        "typical_it_spend_pct": "1-3% of revenue",
        "key_questions": [
            "OT/IT segmentation?",
            "Plant floor systems integration?",
            "Supply chain system dependencies?"
        ]
    },
    "retail": {
        "compliance_frameworks": ["PCI-DSS", "state privacy"],
        "elevated_domains": ["applications", "infrastructure"],  # E-commerce, POS
        "benchmark_peer_set": "retail",
        "regulatory_severity_multiplier": 1.2,
        "typical_it_spend_pct": "2-4% of revenue",
        "key_questions": [
            "PCI scope and compliance?",
            "E-commerce platform scalability?",
            "POS system architecture?"
        ]
    },
    "technology": {
        "compliance_frameworks": ["SOC2", "ISO27001", "GDPR"],
        "elevated_domains": ["applications", "cybersecurity"],
        "benchmark_peer_set": "technology",
        "regulatory_severity_multiplier": 1.0,
        "typical_it_spend_pct": "10-20% of revenue",  # IT IS the product
        "key_questions": [
            "Product security posture?",
            "DevSecOps maturity?",
            "Customer data handling?"
        ]
    }
}
```

### How Industry Drives Analysis

1. **Compliance gaps are weighted by industry**
   - "No SOX controls" in financial_services = Critical
   - "No SOX controls" in manufacturing = Low (unless public company)

2. **Benchmarks are industry-specific**
   - IT spend as % of revenue varies dramatically by industry
   - Staffing ratios differ (tech companies have more developers)

3. **Domain elevation**
   - Healthcare elevates cybersecurity findings (PHI exposure)
   - Manufacturing elevates infrastructure/network (OT concerns)

4. **Question generation**
   - Industry-specific questions added to data requests
   - Open questions reflect industry context

### Implementation Plan

**Phase 1: Industry Inventory Definition** (This document)
- Define the data structure
- Capture key considerations per industry

**Phase 2: Compliance Weighting**
- Apply `regulatory_severity_multiplier` to compliance-related findings
- Auto-detect compliance framework gaps based on industry

**Phase 3: Benchmark Integration**
- Connect industry to benchmark peer sets
- Use in cost and staffing comparisons

**Phase 4: Dynamic Question Generation**
- Add industry-specific questions to data requests
- Surface in "Open Questions" based on missing industry-specific facts

---

## Relationship to Benchmarks

The Industry Considerations Inventory works alongside the Benchmark system:

```
Industry Selection
       │
       ▼
┌──────────────────┐     ┌──────────────────┐
│ Industry         │────▶│ Benchmark        │
│ Considerations   │     │ Peer Set         │
│ Inventory        │     │                  │
└──────────────────┘     └──────────────────┘
       │                        │
       ▼                        ▼
┌──────────────────┐     ┌──────────────────┐
│ Compliance       │     │ Cost/Staffing    │
│ Weighting        │     │ Comparisons      │
└──────────────────┘     └──────────────────┘
       │                        │
       └────────────┬───────────┘
                    ▼
            ┌──────────────────┐
            │ Contextualized   │
            │ Findings         │
            └──────────────────┘
```

---

## What's NOT Wrong with Industry as "Metadata"

Capturing industry even before full implementation is valuable:

1. **Future-proofing** - Data is there when we implement weighting
2. **Narrative context** - Reports reference industry appropriately
3. **Benchmark selection** - Even manual benchmark selection uses it
4. **Audit trail** - Knowing what industry was selected for analysis

The critique should be: "Industry doesn't YET drive behavior" not "Industry is cosmetic."

---

## Forward Plan

### Immediate (Current Sprint)
- [x] Document deal lens architecture (this document)
- [ ] Complete database integration testing
- [ ] Fix remaining UI issues (Mermaid rendering, etc.)

### Near-Term (Next Sprint)
- [ ] Implement `deal_type_severity_multiplier()` for carve-out detection
- [ ] Create `INDUSTRY_CONSIDERATIONS` inventory file
- [ ] Wire industry to compliance weighting

### Medium-Term
- [ ] Benchmark peer set selection by industry
- [ ] Industry-specific question generation
- [ ] Deal-type specific data request templates

### Future (Sell-Side)
- [ ] Separate sell-side implementation
- [ ] TSA service catalog generator
- [ ] RemainCo impact analysis
- [ ] Data room readiness assessment

---

## Summary

The system has **good architectural bones** for deal-type and industry awareness:

| Capability | Status | Notes |
|------------|--------|-------|
| Deal type capture | ✅ Implemented | Stored in DB, passed to analysis |
| Deal type in prompts | ✅ Implemented | Carve-out patterns in domain prompts |
| Deal type lens weighting | ⚠️ Designed | Not yet implemented |
| Deal type severity adjustment | ⚠️ Designed | Not yet implemented |
| Industry capture | ✅ Implemented | Stored in DB, passed to analysis |
| Industry considerations inventory | ⚠️ Designed | Not yet implemented |
| Industry compliance weighting | ⚠️ Designed | Not yet implemented |
| Industry benchmarks | ⚠️ Designed | Partially implemented |

**The path forward is clear: implement the weighting and inventory systems to make the captured metadata drive analysis behavior.**

---

*Document created: 2026-01-28*
*Last updated: 2026-01-28*
