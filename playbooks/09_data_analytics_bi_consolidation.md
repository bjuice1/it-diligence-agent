# Data Analytics & BI Consolidation Playbook

## Overview

Data analytics and business intelligence consolidation is often overlooked in M&A IT planning, yet it's critical for financial consolidation, management reporting, and realizing synergies. Without unified reporting, executives can't see the combined business.

**Typical Duration:** 6-18 months (full consolidation)
**Cost Range:** $300K-$3M+ (depends on scope)
**Risk Level:** Medium-High (impacts decision-making, financial close)

---

## Why BI Consolidation Matters in M&A

```
                    THE BI CONSOLIDATION PROBLEM

    BUYER                                      TARGET
    ┌─────────────────────┐                   ┌─────────────────────┐
    │  Data Warehouse     │                   │  Data Warehouse     │
    │  (Snowflake)        │                   │  (SQL Server)       │
    │                     │                   │                     │
    │  ┌───────────────┐  │                   │  ┌───────────────┐  │
    │  │ Revenue: $50M │  │                   │  │ Revenue: $20M │  │
    │  │ Customers: 5K │  │                   │  │ Customers: 2K │  │
    │  │ Margin: 35%   │  │                   │  │ Margin: ???   │  │
    │  └───────────────┘  │                   │  └───────────────┘  │
    │                     │                   │                     │
    │  Power BI           │                   │  Tableau            │
    │  Dashboards         │                   │  Reports            │
    └─────────────────────┘                   └─────────────────────┘
              │                                         │
              │         EXECUTIVE QUESTION:             │
              │    "What's our combined revenue?"       │
              │    "How many total customers?"          │
              │    "What's consolidated margin?"        │
              │                                         │
              └────────────────────┬────────────────────┘
                                   │
                                   ▼
                    ┌─────────────────────────────────┐
                    │        MANUAL CONSOLIDATION     │
                    │     (Excel, reconciliation)     │
                    │                                 │
                    │  • Time consuming               │
                    │  • Error prone                  │
                    │  • Different definitions        │
                    │  • No drill-down                │
                    │  • Delayed close                │
                    └─────────────────────────────────┘
```

---

## Dependency Map

```
                    ┌─────────────────────────────────────────────────────────┐
                    │              UPSTREAM DEPENDENCIES                       │
                    │  (Must be complete BEFORE BI consolidation)              │
                    └─────────────────────────────────────────────────────────┘
                                              │
        ┌─────────────────┬──────────────────┼──────────────────┬─────────────────┐
        ▼                 ▼                  ▼                  ▼                 ▼
┌───────────────┐ ┌───────────────┐ ┌───────────────┐ ┌───────────────┐ ┌───────────────┐
│ Source System │ │  Data         │ │  KPI/Metric   │ │  Network      │ │  BI Platform  │
│ Stability     │ │  Governance   │ │  Definitions  │ │  Connectivity │ │  Decision     │
│               │ │               │ │               │ │               │ │               │
│ - ERP stable  │ │ - Data owners │ │ - Common      │ │ - Data        │ │ - Target BI   │
│ - No major    │ │ - Quality     │ │   definitions │ │   replication │ │   platform    │
│   migrations  │ │   standards   │ │ - Hierarchies │ │ - ETL         │ │ - Licensing   │
│ - Consistent  │ │ - Lineage     │ │ - Mapping     │ │   connectivity│ │ - Skills      │
└───────────────┘ └───────────────┘ └───────────────┘ └───────────────┘ └───────────────┘
                                              │
                    ┌─────────────────────────────────────────────────────────┐
                    │              BI CONSOLIDATION                            │
                    │                                                          │
                    │  Assess → Design → Build → Migrate → Optimize           │
                    └─────────────────────────────────────────────────────────┘
                                              │
        ┌─────────────────┬──────────────────┼──────────────────┬─────────────────┐
        ▼                 ▼                  ▼                  ▼                 ▼
┌───────────────┐ ┌───────────────┐ ┌───────────────┐ ┌───────────────┐ ┌───────────────┐
│ Financial     │ │  Executive    │ │  Operational  │ │  Legacy BI    │ │  Self-Service │
│ Consolidation │ │  Dashboards   │ │  Reporting    │ │  Retirement   │ │  Analytics    │
│               │ │               │ │               │ │               │ │               │
│ - Combined    │ │ - Single      │ │ - Business    │ │ - Tool        │ │ - User        │
│   financials  │ │   view        │ │   unit        │ │   sunset      │ │   adoption    │
│ - Close       │ │ - KPI         │ │   reports     │ │ - License     │ │ - Training    │
│   process     │ │   alignment   │ │ - Self-service│ │   savings     │ │ - Governance  │
└───────────────┘ └───────────────┘ └───────────────┘ └───────────────┘ └───────────────┘
                    │              DOWNSTREAM DEPENDENCIES                     │
                    │  (Enabled after BI consolidation)                        │
                    └─────────────────────────────────────────────────────────┘
```

---

## Upstream Dependencies (Prerequisites)

### 1. Source System Stability
**Must complete before:** Data integration design

| Dependency | Why Required | If Missing |
|------------|--------------|------------|
| ERP stable (not mid-migration) | Data model consistency | Moving target |
| No major system changes pending | Report continuity | Rework required |
| Data extraction possible | Source accessibility | Can't get data |
| Source documentation | Understand data model | Mapping errors |

**Complexity Signals:**
- "ERP migration in progress" → Wait until complete
- "Multiple ERPs" → Complex data harmonization
- "Custom ERP fields" → Mapping required
- "Real-time reporting needs" → Different architecture

### 2. Data Governance Foundation
**Must complete before:** Data integration

| Dependency | Why Required | If Missing |
|------------|--------------|------------|
| Data owners identified | Decision authority | No accountability |
| Data quality baseline | Know issues | Bad data in reports |
| Data lineage documented | Trust in data | Unexplained discrepancies |
| Master data strategy | Consistent dimensions | Customer/product mismatch |

**Complexity Signals:**
- "No data governance" → Governance program first
- "Poor data quality" → Data cleansing effort
- "No data dictionary" → Discovery required
- "Different customer IDs" → Master data mapping

### 3. KPI & Metric Definitions
**Must complete before:** Report design

| Dependency | Why Required | If Missing |
|------------|--------------|------------|
| Common definitions agreed | Apples-to-apples | Misleading reports |
| Calculation methods aligned | Consistent metrics | Different numbers |
| Hierarchy structures mapped | Drill-down works | Navigation breaks |
| Business sign-off | Stakeholder agreement | Rework |

**Example: "Revenue" Definition Challenge**
```
BUYER DEFINITION                    TARGET DEFINITION
─────────────────────              ─────────────────────
Revenue = Gross - Returns          Revenue = Net of discounts
Recognized at shipment             Recognized at delivery
USD only                           Local currency + FX
Includes services                  Products only

RESULT: Same word, different numbers
SOLUTION: Define "Combined Revenue" with explicit rules
```

### 4. Network Connectivity
**Must complete before:** Data pipeline build

| Dependency | Why Required | If Missing |
|------------|--------------|------------|
| Network path to source systems | ETL can extract | No data flow |
| Sufficient bandwidth | Large data volumes | Slow/failed loads |
| Security/firewall rules | Data transfer allowed | Blocked pipelines |
| VPN/encryption | Secure transfer | Compliance risk |

### 5. BI Platform Decision
**Must complete before:** Build phase

| Dependency | Why Required | If Missing |
|------------|--------------|------------|
| Target BI platform selected | Know what to build for | Wasted effort |
| Licensing procured | Users can access | Blocked access |
| Skills available | Build capability | Hiring/training |
| Infrastructure ready | Platform deployed | Nowhere to deploy |

---

## Downstream Dependencies (Enabled After BI Consolidation)

### 1. Financial Consolidation
**Blocked until:** Unified financial data model

| Dependency | Why Blocked | Impact of Delay |
|------------|-------------|-----------------|
| Combined financial statements | Different CoA structures | Manual consolidation |
| Accelerated close | Data not unified | Slow close cycle |
| Segment reporting | Inconsistent dimensions | Manual reconciliation |
| Audit support | Multiple sources | Audit complexity |

### 2. Executive Dashboards
**Blocked until:** KPIs defined and data integrated

| Dependency | Why Blocked | Impact of Delay |
|------------|-------------|-----------------|
| Single version of truth | Multiple data sources | Conflicting reports |
| Combined KPIs | Different definitions | Misleading metrics |
| Board reporting | No consolidated view | Manual preparation |

### 3. Operational Reporting
**Blocked until:** Data pipelines established

| Dependency | Why Blocked | Impact of Delay |
|------------|-------------|-----------------|
| Business unit reports | Data not integrated | Siloed reporting |
| Self-service analytics | Platform not unified | Multiple tools |
| Operational metrics | Different definitions | Inconsistent tracking |

### 4. Legacy BI Retirement
**Blocked until:** Users migrated to new platform

| Dependency | Why Blocked | Impact of Delay |
|------------|-------------|-----------------|
| Tool retirement | Users still dependent | Continued licensing |
| License optimization | Multiple platforms | Double cost |
| Support consolidation | Multiple tools to support | Operational overhead |

---

## BI Platform Consolidation Scenarios

### Scenario 1: Same Platform (e.g., both use Power BI)
```
Complexity: Lower
Approach: Content migration + data model alignment
Timeline: 3-6 months

Tasks:
├── Align data sources
├── Standardize semantic models
├── Migrate reports/dashboards
├── Consolidate workspaces
└── Retire duplicate content
```

### Scenario 2: Different Platforms (e.g., Tableau → Power BI)
```
Complexity: Higher
Approach: Rebuild reports on target platform
Timeline: 6-12 months

Tasks:
├── Inventory all reports/dashboards
├── Prioritize for migration
├── Rebuild in target platform
├── User training
├── Parallel run
└── Retire legacy platform
```

### Scenario 3: Multiple Platforms (e.g., Tableau + Qlik + Power BI)
```
Complexity: Highest
Approach: Rationalization + standardization
Timeline: 12-18 months

Tasks:
├── Full inventory across platforms
├── Rationalization decision (keep/retire)
├── Standard platform selection
├── Phased migration
├── Extended parallel run
└── Multi-platform retirement
```

---

## DD Document Signals to Detect

### BI Platform Signals
| Signal | Implication | Integration Complexity |
|--------|-------------|----------------------|
| "Same BI tool as buyer" | Consolidation easier | Lower |
| "Different BI platforms" | Migration required | Medium-High |
| "Multiple BI tools" | Rationalization needed | High |
| "Legacy reporting (Crystal, SSRS)" | Modernization opportunity | Medium |
| "Excel-based reporting" | No BI platform | Build from scratch |

### Data Warehouse Signals
| Signal | Implication | Complexity |
|--------|-------------|------------|
| "Modern cloud DW (Snowflake, Databricks)" | Easier integration | Lower |
| "On-prem SQL Server DW" | Migration consideration | Medium |
| "No data warehouse" | Source system reporting | Data integration first |
| "Multiple data warehouses" | Consolidation needed | High |
| "SAP BW" / "Oracle OBIEE" | ERP-specific; vendor lock-in | Medium-High |

### Data Quality Signals
| Signal | Implication | Action |
|--------|-------------|--------|
| "Data quality issues" | Cleansing before consolidation | Extend timeline |
| "No data governance" | Governance program needed | Foundational work |
| "Multiple sources of truth" | Master data work | Data reconciliation |
| "Manual reconciliation" | Current pain point | Automation opportunity |

### Reporting Signals
| Signal | Implication | Impact |
|--------|-------------|--------|
| "Spreadmart" / "Excel reporting" | Uncontrolled analytics | Governance needed |
| "Hundreds of reports" | Rationalization opportunity | Extended discovery |
| "Real-time reporting" | Architecture complexity | Higher cost |
| "Regulatory reporting" | Compliance requirements | Careful migration |

---

## Cost Estimation Signals

| Factor | Impact | Typical Cost |
|--------|--------|--------------|
| BI platform licensing | Per-user cost | $10-75/user/month |
| Data warehouse | Storage + compute | $1K-50K/month |
| Report count | Migration effort | $2-10K per complex report |
| ETL pipelines | Data integration | $5-20K per source |
| Data quality remediation | Cleansing effort | $50-200K |
| Training | User adoption | $500-2K per user |
| Platform migration | Rebuild effort | 1.5-3x new build |

**Typical Budget Ranges:**

| Scenario | Implementation | Annual Run Rate |
|----------|----------------|-----------------|
| Small (100 users, 1 platform) | $200-500K | $50-150K |
| Medium (500 users, 2 platforms) | $500K-1.5M | $150-400K |
| Large (1000+ users, multiple platforms) | $1.5-3M+ | $400K-1M+ |

---

## Common Failure Modes

1. **No KPI Alignment** - Combined reports show conflicting numbers
2. **Source System Changes** - ERP migration invalidates BI work
3. **Data Quality Ignored** - Garbage in, garbage out
4. **No Data Governance** - No ownership, no accountability
5. **Platform War** - Political battle over which tool wins
6. **Scope Creep** - "While we're at it" syndrome
7. **User Resistance** - Attachment to legacy reports
8. **Performance Issues** - Consolidated data too slow
9. **Security Gaps** - Wrong people see sensitive data
10. **Training Neglected** - Tool deployed, users can't use it

---

## M&A Due Diligence Checklist

| Question | Red Flag Answer | Cost Impact |
|----------|-----------------|-------------|
| What BI platform? | "Excel" / "None" | Build from scratch |
| Same BI as buyer? | Different | Migration required |
| Data warehouse exists? | No | Data integration first |
| How many reports? | "Hundreds" | Rationalization effort |
| Data quality? | "Issues known" | Cleansing required |
| KPI definitions documented? | No | Discovery + alignment |
| Who owns data governance? | "No one" | Governance program |
| Real-time requirements? | Yes | Architecture complexity |
| Regulatory reporting? | Yes | Careful migration |

---

## BI Consolidation Sequencing

```
Month:  1   2   3   4   5   6   7   8   9  10  11  12
        │   │   │   │   │   │   │   │   │   │   │   │

Assessment  ████│
& Inventory     │
                │
KPI/Metric      ████████│
Alignment               │
                        │
Data            ████████████████│
Integration                     │
                                │
Executive               ████████████│
Dashboards                          │
(Priority reports)                  │
                                    │
User Migration                  ████████████████│
& Training                                      │
                                                │
Legacy                                      ████████
Retirement
```

---

*Playbook Version: 1.0*
*Last Updated: January 2026*
