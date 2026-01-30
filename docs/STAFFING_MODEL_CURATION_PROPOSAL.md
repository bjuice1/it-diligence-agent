# Staffing Model Curation System

> **Purpose**: Enable team members to build and maintain industry-specific IT staffing models that power the analysis engine
> **Status**: Proposal
> **Date**: January 2026

---

## Executive Summary

The IT Due Diligence tool currently uses generic benchmarks for staffing analysis. This proposal outlines a system where **your team becomes the curator** of industry-specific, size-appropriate, vendor-aware staffing models. This creates:

1. **A proprietary data asset** - Models built from real deal experience
2. **A training methodology** - Staff learn industry patterns while building models
3. **Better analysis outputs** - Industry-appropriate comparisons, not generic benchmarks
4. **A competitive moat** - Knowledge captured in structured, reusable form

---

## The Problem with Generic Benchmarks

| Issue | Impact |
|-------|--------|
| "Insurance IT" ≠ "Manufacturing IT" | Wrong role expectations, missed risks |
| Size matters differently by industry | 500-person insurer needs different IT than 500-person manufacturer |
| Vendor patterns are industry-specific | Insurance uses Duck Creek, Manufacturing uses SAP - comparing across industries is noise |
| MSP dependency varies by vertical | Insurance heavily outsources claims processing; manufacturing outsources help desk |
| Regulatory burden shapes staffing | Healthcare IT is 30% compliance; retail IT is 5% |

**Current state**: The system has basic benchmark profiles but they're not granular enough to provide industry-specific insights.

---

## The Proposed Model Architecture

### Dimension 1: Industry Vertical

Each industry has distinct IT patterns:

| Industry | Typical Core Systems | Key IT Roles | Common MSP Patterns |
|----------|---------------------|--------------|---------------------|
| **Insurance** | Duck Creek, Guidewire, Majesco | Policy Admin, Claims, Actuarial Systems | Claims processing, call center |
| **Manufacturing** | SAP, Oracle ERP, MES systems | ERP Admin, MES, SCADA/OT | Help desk, network |
| **Healthcare** | Epic, Cerner, Meditech | EHR Admin, HL7/FHIR Integration | Clinical app support |
| **Retail** | POS, e-commerce, WMS | Omnichannel, Inventory, Loyalty | Store systems, e-commerce |
| **Financial Services** | Core banking, trading platforms | Quant systems, risk, compliance | Back office processing |
| **Professional Services** | PSA, time tracking, billing | Project systems, collaboration | Infrastructure |

### Dimension 2: Organization Size

Size thresholds where IT structure changes:

| Size Band | Revenue | Typical IT Headcount | IT Structure |
|-----------|---------|---------------------|--------------|
| **Startup** | <$10M | 1-3 | Generalists, heavy SaaS |
| **SMB** | $10M-$100M | 5-15 | Functional leads emerge |
| **Mid-Market** | $100M-$500M | 20-50 | Specialist roles, security team |
| **Enterprise** | $500M-$2B | 50-150 | Full IT org, governance |
| **Large Enterprise** | >$2B | 150+ | Multiple IT domains, PMO |

### Dimension 3: Complexity Factors

Modifiers that affect staffing needs:

| Factor | Staffing Impact | Example |
|--------|-----------------|---------|
| **Multi-ERP** | +20-40% apps team | Dual NetSuite + SAP |
| **M&A History** | +15-25% integration burden | 3+ acquisitions in 5 years |
| **Regulatory Burden** | +30-50% security/compliance | HIPAA, SOX, PCI |
| **Geographic Distribution** | +10-20% infrastructure | 10+ locations |
| **24/7 Operations** | +50-100% support | Manufacturing, healthcare |
| **Custom Development** | +30-50% apps team | In-house systems |

### Dimension 4: Vendor/MSP Patterns

Expected vendor stacks by industry:

```
Insurance Mid-Market:
  Core Systems: Duck Creek OR Guidewire OR Majesco
  ERP: NetSuite OR SAP (rare: Oracle)
  HCM: Workday OR ADP
  CRM: Salesforce (usually)
  Security: CrowdStrike OR SentinelOne, Okta

  Typical MSP Pattern:
    - Claims processing: 10-20 FTE equivalent
    - Help desk: 5-10 FTE equivalent
    - Network/infrastructure: 3-5 FTE equivalent
```

---

## How Staff Build These Models

### Model Curation Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│                    MODEL CURATION PROCESS                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   1. EXPERIENCE INPUT                                           │
│      ↓                                                          │
│      Staff member completes a deal in [Industry] [Size]         │
│      ↓                                                          │
│   2. PATTERN CAPTURE                                            │
│      ↓                                                          │
│      "This $200M insurer had these roles, vendors, MSPs..."     │
│      ↓                                                          │
│   3. MODEL UPDATE                                               │
│      ↓                                                          │
│      Update insurance_mid_market.json with observed patterns    │
│      ↓                                                          │
│   4. VALIDATION                                                 │
│      ↓                                                          │
│      Senior team member reviews, approves model changes         │
│      ↓                                                          │
│   5. DEPLOYMENT                                                 │
│      ↓                                                          │
│      Model available for next deal analysis                     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Model File Structure

```json
{
  "model_id": "insurance_mid_market_v2",
  "industry": "insurance",
  "size_band": "mid_market",
  "revenue_range": {"min": 100000000, "max": 500000000},
  "employee_range": {"min": 200, "max": 1500},

  "curated_by": ["analyst_jsmith", "director_mjones"],
  "last_updated": "2026-01-30",
  "deals_informing_model": 12,
  "confidence": "high",

  "expected_roles": [
    {
      "role": "CIO/IT Director",
      "category": "leadership",
      "expected_count": {"min": 1, "max": 1},
      "notes": "Always present at this size"
    },
    {
      "role": "Policy Admin Lead",
      "category": "applications",
      "expected_count": {"min": 1, "max": 3},
      "notes": "Critical for insurance core systems"
    },
    {
      "role": "Claims Systems Lead",
      "category": "applications",
      "expected_count": {"min": 1, "max": 2},
      "notes": "May be outsourced - check MSP patterns"
    },
    {
      "role": "Security Manager",
      "category": "security",
      "expected_count": {"min": 1, "max": 1},
      "notes": "Required for regulatory compliance"
    }
  ],

  "expected_vendors": {
    "core_policy": ["Duck Creek", "Guidewire", "Majesco", "Custom"],
    "core_claims": ["Duck Creek", "Guidewire", "ClaimCenter", "Custom"],
    "erp": ["NetSuite", "SAP S/4HANA", "Oracle"],
    "hcm": ["Workday", "ADP", "UKG"],
    "crm": ["Salesforce", "Dynamics 365"],
    "edr": ["CrowdStrike", "SentinelOne", "Carbon Black"],
    "identity": ["Okta", "Microsoft Entra", "Ping"]
  },

  "expected_msp_patterns": [
    {
      "function": "Claims Processing Support",
      "typical_fte_equivalent": {"min": 5, "max": 20},
      "common_providers": ["TCS", "Cognizant", "Infosys", "Industry-specific"],
      "risk_if_missing": "Claims backlog risk"
    },
    {
      "function": "Help Desk/Service Desk",
      "typical_fte_equivalent": {"min": 3, "max": 10},
      "common_providers": ["Kyndryl", "HCL", "Wipro"],
      "risk_if_missing": "User support gaps"
    }
  ],

  "staffing_ratios": {
    "it_to_employee": {"min": 0.02, "typical": 0.03, "max": 0.05},
    "security_to_it": {"min": 0.05, "typical": 0.10, "max": 0.15},
    "apps_to_it": {"min": 0.25, "typical": 0.35, "max": 0.45}
  },

  "red_flags": [
    "No dedicated security role at this size",
    "Single person dependency on core policy system",
    "No documented claims processing backup",
    "ERP managed by single contractor"
  ],

  "green_flags": [
    "Dedicated compliance/audit liaison",
    "Cross-trained policy/claims team",
    "Documented MSP SLAs with performance metrics"
  ]
}
```

---

## Learning Methodology for Staff

### Why Building Models Trains Analysts

| Activity | What They Learn |
|----------|-----------------|
| **Filling in expected roles** | What matters in this industry, what's optional |
| **Defining vendor patterns** | What "normal" looks like, spotting outliers |
| **Setting MSP expectations** | Where outsourcing is common vs. risky |
| **Writing red/green flags** | Pattern recognition for risk identification |
| **Reviewing peer models** | Cross-industry knowledge transfer |

### Tiered Model Curation Roles

```
APPRENTICE CURATOR
├── Can propose additions to existing models
├── Must have supervisor approval
└── Learning phase: first 3-6 months

CERTIFIED CURATOR
├── Can update models independently
├── Can create new models with peer review
└── Demonstrated accuracy over 5+ deals

MASTER CURATOR
├── Approves model changes
├── Resolves conflicting observations
├── Sets model quality standards
└── Trains new curators
```

### Gamification Elements (Optional)

- **Model Contribution Score** - Track who adds most value
- **Accuracy Tracking** - Compare model predictions to deal outcomes
- **Industry Badges** - "Insurance Expert", "Manufacturing Certified"
- **Model Impact Metrics** - "Your update caught 3 risks in subsequent deals"

---

## How This Improves Analysis

### Current Analysis Flow

```
Documents → Extract Facts → Generic Benchmark → Generic Insights
```

### Proposed Analysis Flow

```
Documents → Extract Facts → Match to Curated Model → Industry-Specific Insights
                                    ↓
                          "For a $200M insurer..."
                                    ↓
                          "Missing Policy Admin Lead is a red flag"
                          "CrowdStrike + SentinelOne overlap is unusual"
                          "Claims MSP FTE looks light vs. typical"
```

### Example Output Improvement

**Before (Generic)**:
> "Target has 35 IT staff. Industry benchmark suggests 30-50 is typical."

**After (Curated Model)**:
> "For a $200M mid-market insurer, 35 IT staff is at the low end of typical (30-50). However, missing a dedicated Claims Systems Lead is a red flag - 90% of similar insurers have this role. The Claims MSP (Cognizant, 8 FTE equivalent) may be compensating, but this represents concentration risk."

---

## Integration with Existing System

### Files to Create/Modify

| File | Purpose |
|------|---------|
| `data/benchmarks/models/` | New directory for curated models |
| `services/model_matcher.py` | Match deals to appropriate models |
| `services/benchmark_service.py` | Extend to use curated models |
| `web/blueprints/models.py` | UI for model curation |
| `web/templates/models/` | Model editing interface |

### API for Model Curation

```python
# Load appropriate model for a deal
model = model_service.match_model(
    industry="insurance",
    revenue=200_000_000,
    employee_count=800,
    complexity_factors=["multi_erp", "regulated"]
)

# Compare actual inventory against model
comparison = model_service.compare(
    model=model,
    inventory=inventory_store,
    fact_store=fact_store
)

# Get model-specific insights
insights = comparison.get_insights()
# Returns: "Missing Claims Systems Lead", "MSP FTE below typical", etc.
```

---

## Staff Contribution Opportunities

This model curation system creates multiple ways for staff to contribute:

### 1. Model Building (Primary)
- Create new industry/size combinations
- Refine existing models based on deal experience
- Add red/green flag patterns

### 2. Pattern Validation
- Review model predictions against deal outcomes
- Flag models that need updating
- Identify emerging industry patterns

### 3. Quality Review
- Peer review model changes
- Resolve conflicting observations
- Maintain model consistency

### 4. Training Content
- Document "why" behind model decisions
- Create case studies from anonymized deals
- Build training materials for new curators

---

## Implementation Phases

### Phase 1: Foundation (2-4 weeks)
- [ ] Create model JSON schema
- [ ] Build 3-5 initial models from existing deal experience
- [ ] Create model matching logic
- [ ] Integrate with existing benchmark service

### Phase 2: Curation UI (4-6 weeks)
- [ ] Model viewing interface
- [ ] Model editing (with approval workflow)
- [ ] Model comparison view
- [ ] Curation activity tracking

### Phase 3: Staff Onboarding (Ongoing)
- [ ] Training materials for curators
- [ ] Curation guidelines document
- [ ] Quality metrics dashboard
- [ ] Feedback loop from deal outcomes

### Phase 4: Scale (6+ months)
- [ ] 20+ industry/size models
- [ ] Integration with deal intake workflow
- [ ] Automated model suggestions from deal data
- [ ] Model accuracy tracking and refinement

---

## Success Metrics

| Metric | Target | Why It Matters |
|--------|--------|----------------|
| **Models Created** | 20+ by EOY | Coverage across common deal types |
| **Staff Contributions** | 80%+ participate | Adoption and engagement |
| **Model-Specific Insights** | 5+ per deal | Value to end analysis |
| **Prediction Accuracy** | 70%+ flags validated | Model quality |
| **Time to Analysis** | -30% | Faster with industry context |

---

## Appendix: Example Models to Build First

Priority based on deal frequency and complexity:

1. **Insurance - Mid-Market** (This deal type)
2. **Manufacturing - Enterprise** (Complex ERP/OT)
3. **Healthcare - Mid-Market** (Regulatory heavy)
4. **Financial Services - Mid-Market** (Trading/risk systems)
5. **Professional Services - SMB** (PSA-centric)
6. **Retail - Enterprise** (Omnichannel complexity)
7. **Technology - Growth** (SaaS companies being acquired)

---

*Document created: January 2026*
*Author: System Analysis*
*Status: Ready for Review*
