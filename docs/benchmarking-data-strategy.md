# Benchmarking Data Strategy

**Purpose:** Define the approach for sourcing, validating, maintaining, and governing benchmark data used in the IT DD tool for commercial client engagements.

---

## 1. Current State Assessment

### 1.1 What Benchmark Data Exists Today

The tool currently contains hardcoded benchmark data across several files:

| Data Category | Location | Examples |
|--------------|----------|----------|
| **Cost Anchors** | `tools_v2/cost_model.py` | Per-user licensing ($180-400), app migration ($10K-600K), identity separation ($100K-2M) |
| **Volume Discounts** | `tools_v2/cost_model.py` | 5-45% discount curves by quantity tier |
| **Regional Multipliers** | `tools_v2/cost_model.py` | India: 0.35x, US West: 1.15x, UK: 1.10x |
| **Industry Modifiers** | `tools_v2/activity_templates_v2.py` | Healthcare: 1.25x, Financial Services: 1.3x, Government: 1.4x |
| **Complexity Multipliers** | `tools_v2/activity_templates_v2.py` | Simple: 0.7x, Complex: 1.5x, Highly Complex: 2.0x |
| **Run-Rate Anchors** | `tools_v2/cost_model.py` | M365 E3: $396-432/user/yr, Cloud hosting: $6K-18K/server/yr |
| **Timeline Drivers** | `tools_v2/cost_model.py` | Identity separation: 3-6 months, ERP separation: 9-18 months |
| **Risk Flag Impacts** | `tools_v2/cost_model.py` | Technical debt: +10-20%, Compliance gaps: +$200K-1M |

### 1.2 Current Limitations

| Issue | Impact | Risk Level |
|-------|--------|------------|
| **No source attribution** | Can't defend numbers to clients | HIGH |
| **Hardcoded values** | Requires code change to update | MEDIUM |
| **No update process** | Data goes stale over time | HIGH |
| **Missing industry depth** | Generic across verticals | MEDIUM |
| **No PwC proprietary data** | Not leveraging firm assets | HIGH |
| **No regional variation** | US-centric defaults | MEDIUM |

---

## 2. Benchmark Data Categories

### 2.1 Category Taxonomy

```
BENCHMARK DATA
├── COST BENCHMARKS
│   ├── One-Time Costs
│   │   ├── Separation/Migration (per user, per app, per site)
│   │   ├── Integration (buyer-side)
│   │   └── TSA Exit (standalone capability build)
│   ├── Run-Rate Costs
│   │   ├── Licensing (M365, ERP, SaaS portfolio)
│   │   ├── Infrastructure (cloud, network, DC)
│   │   ├── Security (tools, MDR/SOC)
│   │   └── Support (MSP, internal IT FTE)
│   └── Adjustment Factors
│       ├── Volume discounts
│       ├── Regional multipliers
│       └── Complexity/industry modifiers
│
├── STAFFING BENCHMARKS
│   ├── IT Headcount Ratios
│   │   ├── IT FTE per 100 employees (by industry)
│   │   ├── IT FTE per $100M revenue (by industry)
│   │   └── IT FTE by function breakdown
│   ├── Compensation
│   │   ├── By role and level
│   │   ├── By geography
│   │   └── FTE vs contractor premium
│   └── Outsourcing
│       ├── Typical MSP ratios
│       └── Offshore/nearshore mix
│
├── OPERATIONAL BENCHMARKS
│   ├── IT Spend
│   │   ├── IT spend as % revenue (by industry)
│   │   ├── Spend by category breakdown
│   │   └── Capital vs operating ratio
│   ├── Application Portfolio
│   │   ├── Apps per 100 employees
│   │   ├── SaaS vs on-prem mix
│   │   └── ERP penetration
│   └── Infrastructure
│       ├── Cloud adoption %
│       ├── Servers per 100 users
│       └── Sites per 1000 employees
│
└── TIMELINE BENCHMARKS
    ├── Workstream Durations
    │   ├── Identity separation
    │   ├── ERP migration
    │   ├── Network cutover
    │   └── Application migration
    └── Deal Phase Durations
        ├── Sign-to-close typical
        ├── TSA typical duration
        └── Full separation timeline
```

### 2.2 Priority Ranking

| Category | Priority | Rationale |
|----------|----------|-----------|
| One-Time Cost Anchors | P1 | Directly in client deliverables |
| Industry Modifiers | P1 | Affects all estimates |
| IT Spend Benchmarks | P1 | Key client question |
| Staffing Ratios | P2 | Organization analysis |
| Run-Rate Costs | P2 | Ongoing cost estimates |
| Timeline Benchmarks | P2 | Planning credibility |
| Regional Multipliers | P3 | Refinement |
| Volume Discounts | P3 | Refinement |

---

## 3. Data Sourcing Strategy

### 3.1 Source Hierarchy

| Source Type | Examples | Defensibility | Update Effort |
|-------------|----------|---------------|---------------|
| **PwC Proprietary** | Deal databases, internal benchmarks, practice expertise | HIGHEST | Annual/Continuous |
| **Licensed Research** | Gartner, Forrester, IDC, ISG | HIGH | Annual subscription |
| **Public Authoritative** | BLS, government data, vendor published pricing | HIGH | Check annually |
| **Industry Associations** | ITFMA, Gartner Peer Insights, vendor communities | MEDIUM | Check annually |
| **Vendor Pricing** | Microsoft, AWS, Oracle published pricing | HIGH | Check quarterly |
| **Practitioner Expertise** | SME validation, deal experience | MEDIUM | Continuous |

### 3.2 Recommended Sources by Category

#### Cost Benchmarks

| Data Point | Recommended Source | Backup Source |
|------------|-------------------|---------------|
| Microsoft licensing | Microsoft published pricing | PwC licensing practice |
| ERP licensing | Vendor price lists, PwC ERP practice | Gartner TCO studies |
| Cloud infrastructure | AWS/Azure/GCP calculators | ISG benchmarks |
| Security tooling | Vendor pricing, Gartner MQ reports | PwC cyber practice |
| Migration costs | PwC deal database | ISG, Gartner |
| MSP pricing | ISG outsourcing benchmarks | PwC managed services |

#### Staffing Benchmarks

| Data Point | Recommended Source | Backup Source |
|------------|-------------------|---------------|
| IT/employee ratios | Gartner IT Key Metrics | PwC deal database |
| IT spend % revenue | Gartner IT Spending | Deloitte CIO survey |
| Compensation data | Radford, Mercer | BLS, Levels.fyi |
| Offshore rates | ISG, Everest Group | PwC GDC data |

#### Operational Benchmarks

| Data Point | Recommended Source | Backup Source |
|------------|-------------------|---------------|
| Cloud adoption | Flexera State of Cloud | Gartner |
| Application counts | Productiv, Zylo | PwC deal database |
| SaaS spend | Gartner SaaS forecast | Flexera |

### 3.3 PwC Proprietary Data Opportunity

**High-value internal sources to pursue:**

1. **Deal Database**
   - Historical carve-out/acquisition cost actuals
   - Anonymized and aggregated
   - Strongest defensibility

2. **Practice Benchmarks**
   - Technology consulting delivery metrics
   - Managed services pricing
   - Implementation cost actuals

3. **Global Delivery Center Data**
   - Actual offshore/nearshore rates
   - Productivity metrics
   - Role-level rates

4. **Alliance Partnerships**
   - Microsoft, SAP, Oracle, Salesforce pricing
   - Partner discount structures

**Action:** Engage with Deals practice leadership to understand data access, anonymization requirements, and approval process.

---

## 4. Data Architecture

### 4.1 Current State (Hardcoded)

```python
# Current: Values embedded in Python code
COST_ANCHORS = {
    "license_microsoft": {
        "name": "Microsoft License Transition",
        "unit": "per_user",
        "anchor": (180, 400),
        "description": "Standalone M365 E3/E5 vs parent EA pricing"
    },
    ...
}
```

**Problems:**
- Requires code deployment to update
- No audit trail
- No versioning
- No source attribution

### 4.2 Target State (Externalized)

```
┌─────────────────────────────────────────────────────────────┐
│                    BENCHMARK DATA STORE                      │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ cost_       │  │ staffing_   │  │ timeline_   │         │
│  │ benchmarks  │  │ benchmarks  │  │ benchmarks  │         │
│  │ .json       │  │ .json       │  │ .json       │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
│                                                              │
│  ┌─────────────────────────────────────────────────┐       │
│  │ METADATA PER DATA POINT:                         │       │
│  │ - value (low, high) or value                    │       │
│  │ - unit (per_user, per_app, fixed, etc.)        │       │
│  │ - source (Gartner 2025, PwC Deal DB, etc.)     │       │
│  │ - source_date (2025-01-15)                     │       │
│  │ - valid_through (2026-01-15)                   │       │
│  │ - confidence (high, medium, low)               │       │
│  │ - notes (any caveats or context)               │       │
│  │ - last_validated_by (analyst name)             │       │
│  └─────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    BENCHMARK SERVICE                         │
│  - load_benchmarks(category)                                │
│  - get_cost_anchor(key, industry, region)                   │
│  - get_staffing_ratio(metric, industry)                     │
│  - validate_freshness()                                      │
│  - audit_log(access)                                         │
└─────────────────────────────────────────────────────────────┘
```

### 4.3 Data Schema (Target)

```json
{
  "benchmark_id": "cost_microsoft_licensing_e3",
  "category": "cost_benchmarks",
  "subcategory": "licensing",
  "name": "Microsoft 365 E3 Annual Licensing",
  "value": {
    "low": 396,
    "high": 432,
    "typical": 420
  },
  "unit": "per_user_annual",
  "currency": "USD",
  "source": {
    "primary": "Microsoft Published Pricing",
    "url": "https://www.microsoft.com/en-us/microsoft-365/enterprise/office-365-e3",
    "date": "2025-10-01",
    "notes": "List price before volume discounts"
  },
  "applicability": {
    "industries": ["all"],
    "regions": ["north_america"],
    "company_size": ["all"]
  },
  "adjustments": {
    "volume_discount_curve": "per_user",
    "industry_modifier_applies": false
  },
  "metadata": {
    "created_at": "2025-10-15",
    "created_by": "benchmark_admin",
    "last_validated": "2025-10-15",
    "validated_by": "john.smith@pwc.com",
    "valid_through": "2026-04-01",
    "confidence": "high",
    "change_history": [
      {"date": "2025-10-15", "change": "Initial entry", "by": "benchmark_admin"}
    ]
  }
}
```

### 4.4 Migration Path

| Phase | Scope | Effort |
|-------|-------|--------|
| **Phase A** | Extract current hardcoded values to JSON files | 1-2 weeks |
| **Phase B** | Add source attribution to existing values | 2-3 weeks |
| **Phase C** | Build benchmark service layer | 2-3 weeks |
| **Phase D** | Create admin UI for updates | 3-4 weeks |
| **Phase E** | Integrate licensed/proprietary data | Ongoing |

---

## 5. Governance Model

### 5.1 Roles & Responsibilities

| Role | Responsibility | Suggested Owner |
|------|---------------|-----------------|
| **Benchmark Owner** | Overall data quality, source decisions | Senior Director, Deals |
| **Data Steward** | Day-to-day maintenance, updates | Manager, IT DD Practice |
| **Industry SMEs** | Validate industry-specific benchmarks | Practice SMEs |
| **Technical Admin** | System access, deployment | Development team |

### 5.2 Update Cadence

| Data Category | Review Cadence | Trigger for Ad-Hoc Update |
|--------------|----------------|---------------------------|
| Vendor Pricing | Quarterly | Price change announcement |
| Cost Anchors | Semi-annually | Significant market shift |
| Industry Modifiers | Annually | New research published |
| Regional Multipliers | Annually | Currency/labor shifts |
| Staffing Ratios | Annually | New Gartner/research release |

### 5.3 Validation Process

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ New/Updated  │────▶│ SME Review   │────▶│ Second       │────▶│ Deploy to    │
│ Data Point   │     │ (accuracy)   │     │ Reviewer     │     │ Production   │
└──────────────┘     └──────────────┘     │ (approval)   │     └──────────────┘
                                          └──────────────┘
                                                │
                                                ▼
                                          ┌──────────────┐
                                          │ Audit Log    │
                                          │ Entry        │
                                          └──────────────┘
```

### 5.4 Client-Facing Documentation

Every benchmark used in client deliverables should have:

1. **Source citation** - Where did this number come from?
2. **Date of source** - How current is this?
3. **Applicability notes** - Any caveats?
4. **Methodology note** - How was it applied?

Example footnote for deliverable:
> *Cost estimates based on PwC IT DD Benchmark Database (Q4 2025), incorporating Microsoft published pricing, Gartner IT Key Metrics Data, and PwC deal experience. Industry adjustment applied for healthcare (+25%) based on HIPAA compliance requirements.*

---

## 6. Implementation Roadmap

### Phase 1: Foundation (Weeks 1-4)

**Objective:** Extract and document current benchmarks

| Task | Owner | Deliverable |
|------|-------|-------------|
| Extract all hardcoded benchmarks to inventory | Dev | Spreadsheet of all values |
| Research defensible sources for each value | Data Steward | Source mapping |
| Create JSON schema for benchmark data | Dev | Schema definition |
| Convert cost_model.py anchors to JSON | Dev | cost_benchmarks.json |

### Phase 2: Attribution (Weeks 5-8)

**Objective:** Add source attribution and validation

| Task | Owner | Deliverable |
|------|-------|-------------|
| Validate/update Microsoft pricing | SME | Sourced values |
| Validate/update ERP pricing | SME | Sourced values |
| Validate/update cloud pricing | SME | Sourced values |
| Add source metadata to all records | Data Steward | Attributed JSON |
| Document methodology | Data Steward | Methodology doc |

### Phase 3: Service Layer (Weeks 9-12)

**Objective:** Build software infrastructure

| Task | Owner | Deliverable |
|------|-------|-------------|
| Build BenchmarkService class | Dev | Service code |
| Integrate with cost estimation | Dev | Updated cost_model.py |
| Add freshness validation | Dev | Warnings for stale data |
| Add audit logging | Dev | Access logs |

### Phase 4: Proprietary Data (Weeks 13-20)

**Objective:** Integrate PwC and licensed data

| Task | Owner | Deliverable |
|------|-------|-------------|
| Engage Deals practice on data access | Benchmark Owner | Data sharing agreement |
| Identify relevant Gartner/ISG reports | Data Steward | Licensed data inventory |
| Integrate proprietary cost actuals | Dev + SME | Enhanced benchmarks |
| Build industry-specific depth | SMEs | Industry overlays |

### Phase 5: Admin & Maintenance (Weeks 21-24)

**Objective:** Sustainable operations

| Task | Owner | Deliverable |
|------|-------|-------------|
| Build admin UI for updates | Dev | Admin interface |
| Create update workflow | Data Steward | Process doc |
| Train benchmark maintainers | Data Steward | Trained team |
| Establish review cadence | Benchmark Owner | Calendar |

---

## 7. Risk Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Can't get PwC proprietary data access | Medium | High | Start with public sources; escalate to leadership |
| Licensed data too expensive | Medium | Medium | Prioritize; negotiate firm-wide license |
| Data goes stale without process | High | High | Build freshness alerts; assign ownership |
| Benchmarks challenged by client | Medium | High | Strong source attribution; methodology doc |
| Regional/industry gaps | High | Medium | Phase coverage; disclose limitations |

---

## 8. Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| % of benchmarks with source attribution | 100% | Audit of benchmark store |
| Average data freshness | <12 months | Automated check |
| Client challenges to benchmarks | <5% of engagements | Feedback tracking |
| Time to update a benchmark | <2 business days | Process metric |
| Coverage by industry | 6 major industries | Benchmark inventory |

---

## 9. Immediate Actions

### This Week

1. [ ] **Identify Benchmark Owner** - Who in leadership will own this?
2. [ ] **Inventory current benchmarks** - Export all hardcoded values to spreadsheet
3. [ ] **Identify Gartner access** - Does PwC have firm-wide Gartner subscription?

### Next 2 Weeks

4. [ ] **Meet with Deals practice** - Discuss access to deal database
5. [ ] **Prioritize benchmarks** - Which 20 values matter most?
6. [ ] **Source top 20** - Find defensible sources for priority benchmarks

### Next Month

7. [ ] **Complete Phase 1** - All benchmarks extracted and documented
8. [ ] **Begin Phase 2** - Add attribution to priority benchmarks
9. [ ] **Draft methodology doc** - How benchmarks are applied

---

## Appendix A: Current Benchmark Inventory

### Cost Anchors (from cost_model.py)

| Key | Name | Current Value | Unit | Source Status |
|-----|------|--------------|------|---------------|
| license_microsoft | Microsoft License Transition | $180-400 | per_user | NEEDS SOURCE |
| license_erp | ERP License Transition | $1,500-4,000 | per_user | NEEDS SOURCE |
| vendor_contract_transition | Vendor Contract Transition | $15K-50K | per_vendor | NEEDS SOURCE |
| identity_separation | Identity Separation | $100K-2M | by_size | NEEDS SOURCE |
| app_migration_simple | App Migration (Simple) | $10K-40K | per_app | NEEDS SOURCE |
| app_migration_moderate | App Migration (Moderate) | $50K-150K | per_app | NEEDS SOURCE |
| app_migration_complex | App Migration (Complex) | $200K-600K | per_app | NEEDS SOURCE |
| erp_separation | ERP Separation | $500K-12M | by_size | NEEDS SOURCE |
| dc_migration | Data Center Migration | $200K-800K | per_dc | NEEDS SOURCE |
| cloud_migration | Cloud Migration | $3K-10K | per_server | NEEDS SOURCE |
| network_separation | Network Separation | $50K-1M | by_complexity | NEEDS SOURCE |
| security_remediation | Security Remediation | $50K-1.5M | by_gaps | NEEDS SOURCE |

### Industry Modifiers (from activity_templates_v2.py)

| Industry | Current Modifier | Source Status |
|----------|-----------------|---------------|
| Financial Services | 1.30x | NEEDS SOURCE |
| Healthcare | 1.25x | NEEDS SOURCE |
| Government | 1.40x | NEEDS SOURCE |
| Retail | 1.10x | NEEDS SOURCE |
| Manufacturing | 1.15x | NEEDS SOURCE |

### Regional Multipliers (from cost_model.py)

| Region | Current Modifier | Source Status |
|--------|-----------------|---------------|
| US East | 1.00x (base) | NEEDS SOURCE |
| US West | 1.15x | NEEDS SOURCE |
| India | 0.35x | NEEDS SOURCE |
| Eastern Europe | 0.50x | NEEDS SOURCE |
| UK | 1.10x | NEEDS SOURCE |

---

## Appendix B: Sample Source Attribution

**Before (current state):**
```python
"license_microsoft": {
    "anchor": (180, 400),
    "description": "Standalone M365 E3/E5 vs parent EA pricing"
}
```

**After (target state):**
```json
{
  "benchmark_id": "license_microsoft",
  "value": {"low": 180, "high": 400},
  "unit": "per_user_annual_delta",
  "source": {
    "primary": "Microsoft M365 Enterprise Pricing (E3: $36/user/mo, E5: $57/user/mo)",
    "url": "https://www.microsoft.com/en-us/microsoft-365/enterprise/compare-office-365-plans",
    "date": "2025-10-01",
    "calculation": "Delta represents loss of EA discount (typically 15-30%) plus per-seat vs. user-based licensing shift",
    "validated_by": "PwC Microsoft Alliance team"
  },
  "confidence": "high",
  "valid_through": "2026-04-01"
}
```
