# IT DD Agent: Value Proposition & Differentiation

**Purpose:** Articulate what this system does that a VDR parser backed by models doesn't do

**Created:** 2026-02-04
**Status:** Draft for team discussion

---

## The Core Question

**What does the IT DD Agent do that ToltIQ (or any VDR parser + LLM) doesn't do?**

### Quick Answer
- **VDR Parsers:** Extract facts from documents
- **IT DD Agent:** Reasons about those facts in M&A context and generates deal-ready insights

---

## The Value Chain

```
┌────────────────────────────────────────────────────────────────────┐
│                        FULL VALUE CHAIN                             │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│   TOLTIQ / PARSER     ──►    IT DD AGENT    ──►    DEAL OUTPUT     │
│   (Data Extraction)          (Reasoning)           (Decisions)     │
│                                                                    │
│   "SAP exists"               "SAP is 80%           "Migration      │
│   "500 users"                 of transactions"     risk $2-4M      │
│   "$1.2M license"            "Heavy custom"        18-24 mo        │
│   "2 admins"                 "Key person risk"     Retention pkg"  │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

---

## Key Differentiators

### 1. M&A Context Engine (Not Generic IT Assessment)

**What VDR Parsers Do:**
- Extract: "Target uses CrowdStrike endpoint protection"
- Extract: "Buyer uses Carbon Black endpoint protection"

**What IT DD Agent Adds:**
- **M&A Framing:** "Endpoint tool mismatch creates Day-1 consolidation decision"
- **Options Analysis:**
  - Option A: Extend both platforms ($50K/yr duplicative cost)
  - Option B: Migrate target to Carbon Black ($75-150K one-time, 90-day effort)
- **Deal Lens:** Maps to "Day-1 Continuity" + "Cost Driver"

**Every finding maps to M&A lenses:**
- Day-1 Continuity
- TSA Exposure
- Separation Complexity
- Synergy Opportunity
- Cost Driver

---

### 2. Multi-Document Reasoning (Pattern Detection)

**What VDR Parsers Do:**
- Process each document independently
- Return: List of facts per document

**What IT DD Agent Adds:**
- **Connects insights across documents:**

**Example Pattern:**
```
Application Inventory:
  → "Guidewire PolicyCenter"

Security Assessment:
  → "Legacy authentication methods in use"

Org Chart:
  → "2 Guidewire administrators"

IT DD AGENT SYNTHESIZES:
  → "Critical dependency on 2-person team for application serving 80%
     of policy workflows, combined with authentication gaps requiring
     immediate remediation ($50-75K, 30-day timeline, HIGH priority)"
```

**Value:** Surfaces risks that aren't visible in any single document

---

### 3. Pre-Built Assumptions (Opportunity Cost Savings)

**What VDR Parsers Provide:**
- Data you manually analyze to build assumptions

**What IT DD Agent Provides:**
- **Pre-built, editable assumptions** you refine

**Examples:**
- "Cloud migration cost: $X-Y based on current on-prem footprint of Z servers"
- "ERP consolidation timeline: 18-24 months given customization level (247 custom ABAP programs)"
- "Key person retention packages needed for 3 individuals ($150-200K total)"
- "TSA duration estimate: 12-18 months for infrastructure services"

**Time Saved:** 10-15 hours per deal building initial assumptions from scratch

**Opportunity Cost:** Team focuses on validating/refining assumptions, not grinding through data to create them

---

### 4. Initial Report Materials (Draft Language)

**What VDR Parsers Provide:**
- Data dumps
- You write the memo/report from scratch

**What IT DD Agent Provides:**
- **Draft language and structure** you refine
- Risk descriptions with mitigation approaches
- Work items with phased timelines
- Cost narratives benchmarked to industry

**Example Output:**
```
RISK: High ERP Concentration with Customization Complexity

The target relies on SAP S/4HANA as the primary ERP platform, handling
approximately 80% of financial transactions across the organization. The
system contains 247 custom ABAP programs developed over 15 years, with
limited documentation and knowledge concentrated in a single developer
approaching retirement.

M&A IMPLICATION:
- TSA Exposure: Critical dependency requiring extended seller support
- Migration Complexity: $2-4M cost, 18-24 month timeline
- Key Person Risk: Retention package required ($100-150K)

MITIGATION:
1. Negotiate 18-month TSA with knowledge transfer provisions
2. Engage SAP migration consultant for assessment (Day 1-30)
3. Execute retention agreement with lead developer pre-close
4. Document critical customizations during TSA period

COST ESTIMATE: $2.2M - $4.1M (one-time) + $200K/yr (extended TSA)
```

**Time Saved:** 8-12 hours per deal writing initial draft

---

### 5. Evidence-Backed Reasoning (Transparency & Auditability)

**What VDR Parsers Provide:**
- Extracted facts
- No reasoning chain

**What IT DD Agent Provides:**
- **Every conclusion traces to source**

**Evidence Chain Example:**
```
RISK: R-APP-001
  ↓
BASED ON FACTS:
  - F-APP-001: "SAP S/4HANA serves as core ERP..."
  - F-APP-003: "247 custom ABAP programs..."
  - F-APP-007: "$586K annual license cost..."
  - F-ORG-012: "Single developer, 15-year tenure..."
  ↓
SOURCE DOCUMENTS:
  - Application_Inventory.xlsx, Row 12
  - IT_Assessment.docx, Page 8
  - Org_Chart.xlsx, Applications Team

EXACT QUOTE: "SAP S/4HANA serves as our core ERP platform
with approximately 500 active users and handles 80% of
financial transactions..."
```

**Value:**
- **IC-ready:** Investment committee can trace any finding to source
- **Validatable:** Confirm in management presentations
- **No black box:** Transparent AI reasoning

---

### 6. Buyer-Aware Integration Analysis (Overlap Detection)

**What VDR Parsers Provide:**
- Target facts only
- Generic "integration will be needed"

**What IT DD Agent Provides (once fixed):**
- **Specific overlap analysis:** "Target SAP vs Buyer Oracle ERP"
- **Integration options:** Migrate, co-exist, or replace
- **Comparison-based reasoning:**
  - "Target 2-person IT team vs Buyer 568-person IT org"
  - "Target AWS us-east-1 vs Buyer AWS us-east-2 (region mismatch!)"
  - "Target CrowdStrike vs Buyer Carbon Black (tool consolidation opportunity)"

**Value:** Surfaces specific integration complexities, not generic statements

---

## ROI Quantification

### Time Savings Per Deal

| Activity | Traditional Approach | With IT DD Agent | Time Saved |
|----------|---------------------|------------------|------------|
| **Reading documents** | 40-60 hours | 2-3 hours (review) | 38-57 hours |
| **Building assumptions** | 15-20 hours | 3-5 hours (refine) | 10-15 hours |
| **Writing initial report** | 12-16 hours | 2-4 hours (edit) | 8-12 hours |
| **Creating cost model** | 8-12 hours | 1-2 hours (export) | 6-10 hours |
| **TOTAL** | **75-108 hours** | **8-14 hours** | **62-94 hours** |

**Per-Deal Value:**
- At $200/hr consultant rate: **$12,400 - $18,800** savings
- At $300/hr senior rate: **$18,600 - $28,200** savings

### Opportunity Cost (Non-Quantifiable)

**What the team does with saved time:**
- Focus on high-judgment validation (not data grinding)
- Deeper diligence on critical issues
- More deals processed with same headcount
- Faster deal velocity (competitive advantage in auctions)

---

## Comparison Matrix

| Feature | VDR Parser + LLM | IT DD Agent ("The Brain") |
|---------|------------------|---------------------------|
| **Data Extraction** | ✅ Finds information in documents | ✅ Finds information in documents |
| **Multi-Doc Reasoning** | ❌ Each document processed independently | ✅ Connects patterns across documents |
| **M&A Framing** | ❌ Generic IT findings | ✅ Every finding maps to deal lens |
| **Evidence Chain** | ❌ Facts without reasoning | ✅ Traces to exact source quotes |
| **Deal-Ready Outputs** | ❌ Data dumps for you to analyze | ✅ Cost center, risk register, work items |
| **Initial Assumptions** | ❌ You build from scratch | ✅ Pre-built, editable assumptions |
| **Report Language** | ❌ You write from blank page | ✅ Draft language you refine |
| **Integration Analysis** | ❌ Target-only view | ✅ Target vs Buyer overlaps |
| **Consistency** | ❌ Consultant-dependent quality | ✅ Standardized M&A methodology |

---

## Use Case Examples

### Use Case 1: ERP Consolidation Decision

**VDR Parser Output:**
- Target uses SAP S/4HANA
- Buyer uses Oracle ERP Cloud
- Target has 500 SAP users
- Buyer has 4,272 Oracle users

**IT DD Agent Output:**
```
OVERLAP: Target SAP S/4HANA vs Buyer Oracle ERP Cloud

ANALYSIS:
- Platform mismatch creates consolidation decision point
- Target's 247 custom ABAP programs complicate migration
- Buyer's Oracle platform 8.5x larger user base (standardization pull)

INTEGRATION OPTIONS:
1. Migrate Target to Oracle ($2-4M, 18-24 months)
   - Pros: Single platform, buyer standard
   - Cons: High cost, business disruption, custom code rewrite

2. Co-exist on separate platforms ($200-400K/yr ongoing)
   - Pros: Lower short-term cost, minimal disruption
   - Cons: Duplicative licenses, integration complexity

3. Sunset Target SAP gradually (hybrid approach)
   - Pros: Phased risk, business continuity
   - Cons: Extended timeline, dual-platform period

RECOMMENDATION: Option 3 - Phased migration over 24 months
COST ESTIMATE: $2.8M - $4.5M (one-time) + $300K/yr (interim dual-platform)
```

### Use Case 2: Key Person Risk

**VDR Parser Output:**
- John Smith, SAP Administrator, 15 years tenure
- Jane Doe, Network Engineer, 12 years tenure

**IT DD Agent Output:**
```
RISK: Critical Knowledge Concentration (3 individuals)

PATTERN DETECTED ACROSS DOCUMENTS:
- John Smith (SAP Admin, 15yr) manages 247 custom ABAP programs
  + Application Inventory shows: "Sole developer for SAP customizations"
  + Org Chart shows: No backup or junior team member
  + Security doc shows: "Admin access concentrated in 1 account"

- Jane Doe (Network Eng, 12yr) manages all WAN/MPLS configurations
  + Infrastructure doc: "Primary contact for Verizon MPLS"
  + No documentation for firewall policies

- Mike Johnson (DBA, 18yr) approaching retirement (age 63)
  + Controls all production database access
  + Oracle licensing knowledge undocumented

M&A IMPLICATION:
- Immediate departure risk (retirement, better offer, integration stress)
- Knowledge transfer timeline: 6-12 months minimum per person
- Retention packages required to secure continuity

MITIGATION:
1. Pre-close retention agreements ($150-200K total)
2. Knowledge transfer plan (30-90 day sprints per system)
3. Documentation requirements in TSA
4. Buyer team shadowing during first 90 days

COST: $450-650K (retention + knowledge transfer + documentation)
```

---

## Positioning Statement

**We are not a VDR parser.**

We are the **reasoning layer** that sits on top of data extraction tools (like ToltIQ) and transforms facts into deal-ready insights using an M&A-specific reasoning engine.

**Value Proposition:**
- **Speed:** Days instead of weeks
- **Consistency:** Standardized M&A methodology, not consultant-dependent
- **Transparency:** Evidence-backed reasoning, IC-ready
- **Completeness:** Cost center + risk register + work items in one pass
- **Integration-aware:** Buyer vs Target overlap analysis (not just target assessment)

**Bottom Line:**
ToltIQ gets data out of documents.
The IT DD Agent turns that data into deal decisions.

---

## Open Questions for Discussion

1. **Pricing Model:** How do we charge for this vs. ToltIQ extraction?
   - Per-deal flat fee?
   - Subscription for unlimited deals?
   - Tiered based on deal complexity?

2. **Integration Strategy:**
   - Standalone product?
   - Add-on to ToltIQ?
   - White-label for consulting firms?

3. **Market Positioning:**
   - "AI Due Diligence Platform"?
   - "M&A Reasoning Engine"?
   - "Deal Intelligence System"?

4. **Competitive Moat:**
   - Proprietary M&A reasoning framework?
   - Domain-specific prompts and validation rules?
   - Evidence chain/auditability as differentiator?

---

## Next Steps

- [ ] Validate time savings estimates with real deal data
- [ ] Create 2-3 detailed use case examples for sales
- [ ] Draft IC presentation deck highlighting differentiation
- [ ] Consider pilot program with PE firm to gather testimonials
- [ ] Quantify "opportunity cost" benefits more concretely

---

*This document is a living draft. Update as we refine positioning.*
