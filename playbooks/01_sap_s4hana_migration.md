# SAP S/4HANA Migration Playbook

## Overview

SAP S/4HANA migrations represent one of the highest-complexity, highest-cost IT transformation initiatives. This playbook maps dependencies critical for M&A due diligence and post-close planning.

**Typical Duration:** 18-36 months
**Cost Range:** $5M-$50M+ (varies by complexity)
**Risk Level:** Critical

---

## Dependency Map

```
                    ┌─────────────────────────────────────────────────────────┐
                    │              UPSTREAM DEPENDENCIES                       │
                    │  (Must be complete/assessed BEFORE migration starts)    │
                    └─────────────────────────────────────────────────────────┘
                                              │
        ┌─────────────────┬──────────────────┼──────────────────┬─────────────────┐
        ▼                 ▼                  ▼                  ▼                 ▼
┌───────────────┐ ┌───────────────┐ ┌───────────────┐ ┌───────────────┐ ┌───────────────┐
│ Data Quality  │ │  Network      │ │  Identity     │ │  Integration  │ │  Business     │
│ Assessment    │ │  Readiness    │ │  Foundation   │ │  Inventory    │ │  Process      │
│               │ │               │ │               │ │               │ │  Mapping      │
│ - Master data │ │ - Bandwidth   │ │ - AD/IAM      │ │ - EDI links   │ │ - Current vs  │
│ - Cleansing   │ │ - Latency     │ │ - SSO ready   │ │ - API catalog │ │   future      │
│ - Migration   │ │ - Cloud conn  │ │ - RBAC design │ │ - Middleware  │ │ - Gap analysis│
└───────────────┘ └───────────────┘ └───────────────┘ └───────────────┘ └───────────────┘
                                              │
                    ┌─────────────────────────────────────────────────────────┐
                    │                 SAP S/4HANA MIGRATION                    │
                    │                                                          │
                    │  Discovery → Prepare → Explore → Realize → Deploy → Run │
                    └─────────────────────────────────────────────────────────┘
                                              │
        ┌─────────────────┬──────────────────┼──────────────────┬─────────────────┐
        ▼                 ▼                  ▼                  ▼                 ▼
┌───────────────┐ ┌───────────────┐ ┌───────────────┐ ┌───────────────┐ ┌───────────────┐
│ Legacy        │ │  Reporting/   │ │  Integration  │ │  Training &   │ │  Audit &      │
│ Decommission  │ │  Analytics    │ │  Reconnection │ │  Change Mgmt  │ │  Compliance   │
│               │ │               │ │               │ │               │ │               │
│ - ECC sunset  │ │ - BW/4HANA    │ │ - EDI retest  │ │ - End user    │ │ - SOX retest  │
│ - Archive     │ │ - SAC setup   │ │ - API repoint │ │ - Support     │ │ - Audit trail │
│ - License end │ │ - Dashboards  │ │ - Middleware  │ │ - Hypercare   │ │ - Controls    │
└───────────────┘ └───────────────┘ └───────────────┘ └───────────────┘ └───────────────┘
                    │              DOWNSTREAM DEPENDENCIES                     │
                    │  (Cannot complete until migration finishes)              │
                    └─────────────────────────────────────────────────────────┘
```

---

## Upstream Dependencies (Prerequisites)

### 1. Data Quality & Master Data Management
**Must complete before:** Migration planning phase

| Dependency | Why Required | Blocking Risk |
|------------|--------------|---------------|
| Customer master data cleansed | S/4HANA has stricter data model | Migration failure |
| Vendor master data deduplicated | BP consolidation in S/4 | Duplicate records |
| Material master standardized | S/4 simplified data model | Conversion errors |
| Chart of accounts mapped | New GL requirements | Financial reporting broken |
| Data archiving complete | Reduce migration scope | Extended timeline |

**Complexity Signals:**
- "Multiple chart of accounts" → +30% effort
- "Custom data elements" → +20% effort
- "No MDM solution" → +40% effort
- "Acquired companies not integrated" → +50% effort

### 2. Network Infrastructure Readiness
**Must complete before:** Technical sandbox build

| Dependency | Why Required | Blocking Risk |
|------------|--------------|---------------|
| Bandwidth assessment | S/4 requires more bandwidth | Performance issues |
| Latency optimization | HANA sensitive to latency | User experience |
| Cloud connectivity | If S/4 Cloud or RISE | Project blocked |
| VPN/ExpressRoute | Hybrid scenarios | Security/connectivity |

**Complexity Signals:**
- "Single T1 line" → Critical blocker
- "No SD-WAN" → +15% network work
- "Manufacturing sites on MPLS" → +20% complexity
- "Cloud-first but no Azure ExpressRoute" → +2 months

### 3. Identity & Access Foundation
**Must complete before:** Security design phase

| Dependency | Why Required | Blocking Risk |
|------------|--------------|---------------|
| Active Directory stable | SAP IAS/IPS integration | Access failures |
| SSO infrastructure | Modern authentication | User friction |
| Role-based access designed | Fiori apps need clean RBAC | Security gaps |
| Segregation of duties mapped | SOX/audit requirements | Compliance failure |

**Complexity Signals:**
- "No centralized IAM" → +25% security work
- "Legacy LDAP only" → +15% effort
- "No SoD tooling" → Compliance risk
- "Multiple AD forests" → +30% identity work

### 4. Integration Inventory
**Must complete before:** Architecture phase

| Dependency | Why Required | Blocking Risk |
|------------|--------------|---------------|
| EDI partner inventory | Must retest all EDI | Order failures |
| API catalog | Point-to-point vs middleware | Integration breaks |
| Middleware assessment | BizTalk/MuleSoft/etc | Architecture decision |
| Batch job inventory | Z-jobs, interfaces | Data sync failures |

**Complexity Signals:**
- "500+ EDI trading partners" → +40% integration work
- "No middleware (point-to-point)" → +50% effort
- "Custom ABAP interfaces" → +30% per interface
- "Real-time integrations" → +25% complexity

### 5. Business Process Mapping
**Must complete before:** Fit-gap analysis

| Dependency | Why Required | Blocking Risk |
|------------|--------------|---------------|
| Current state documented | Baseline for S/4 fit-gap | Scope creep |
| Future state defined | Target operating model | Misaligned solution |
| Process owners identified | Decision-making | Project delays |
| Custom development inventory | ABAP assessment | Technical debt |

**Complexity Signals:**
- "No process documentation" → +20% discovery
- "Heavy customization (500+ Z-programs)" → +50% remediation
- "Multiple business units, different processes" → +30% harmonization

---

## Downstream Dependencies (Blocked Until Complete)

### 1. Legacy ERP Decommissioning
**Blocked until:** S/4 go-live + hypercare complete

| Dependency | Why Blocked | Impact of Delay |
|------------|-------------|-----------------|
| ECC shutdown | Must run parallel until stable | Double licensing |
| SAP license optimization | Can't reduce until ECC off | Cost overrun |
| Data archiving/retention | Legal hold on old system | Storage costs |
| Support contract termination | Need fallback option | Continued support fees |

**Typical Timeline:** 6-12 months post go-live

### 2. Reporting & Analytics Modernization
**Blocked until:** S/4 core tables stable

| Dependency | Why Blocked | Impact of Delay |
|------------|-------------|-----------------|
| BW/4HANA migration | Depends on S/4 extractors | Reporting gaps |
| SAP Analytics Cloud | Needs S/4 live connection | No real-time analytics |
| Custom reports | Table structure changed | Report failures |
| Management dashboards | KPI definitions change | Wrong metrics |

**Typical Timeline:** Begins 3-6 months post go-live

### 3. Integration Reconnection & Testing
**Blocked until:** S/4 integration layer deployed

| Dependency | Why Blocked | Impact of Delay |
|------------|-------------|-----------------|
| EDI partner testing | New IDoc formats | Order failures |
| API consumers | Endpoint changes | Integration breaks |
| Middleware reconfiguration | New adapters needed | Data flow stops |
| Third-party connections | CRM, WMS, TMS | Process breaks |

**Typical Timeline:** Last 3 months of project + 1 month post

### 4. Training & Organizational Change
**Blocked until:** Fiori apps configured

| Dependency | Why Blocked | Impact of Delay |
|------------|-------------|-----------------|
| End user training | Need final UI | Untrained users |
| Support model | New technology stack | Poor support |
| Documentation | Process changes | Tribal knowledge |
| Hypercare planning | Scope depends on changes | Unplanned costs |

**Typical Timeline:** 2-3 months before go-live

### 5. Audit & Compliance Recertification
**Blocked until:** S/4 controls implemented

| Dependency | Why Blocked | Impact of Delay |
|------------|-------------|-----------------|
| SOX control testing | New system = retest | Audit findings |
| Access recertification | New roles/authorizations | Compliance gap |
| Audit trail validation | New logging structure | Regulatory risk |
| Process control validation | Changed processes | Control gaps |

**Typical Timeline:** Begins at go-live, 3-6 months to certify

---

## Critical Path Analysis

```
Month:  1   2   3   4   5   6   7   8   9  10  11  12  13  14  15  16  17  18
        │   │   │   │   │   │   │   │   │   │   │   │   │   │   │   │   │   │
Data    ████████████│
Quality             │
                    │
Network     ████████│
Prep                │
                    │
Identity        ████████████│
Foundation                  │
                            │
Integration     ████████████████│
Inventory                       │
                                │
S/4 CORE        ░░░░░░░░░░░░░░░░████████████████████████████████│
                Prep            │ Explore    │ Realize   │Deploy│
                                │            │           │      │
Legacy                                                          │████████████
Decommission

Reporting                                                   ░░░░████████████
Migration
```

---

## M&A Due Diligence Checklist

### Pre-Deal Assessment

| Question | Red Flag Answer | Cost Impact |
|----------|-----------------|-------------|
| What SAP version? | ECC 6.0 EHP < 5 | +$2-5M |
| When is license expiry? | <18 months | Timeline pressure |
| How many Z-programs? | >300 | +$1-3M remediation |
| Is there an S/4 roadmap? | No/stalled | Start from scratch |
| How many integration points? | >200 | +$1-2M integration |
| Who is the SAP support partner? | None/in-house only | Resourcing risk |
| Are business processes documented? | No | +$500K discovery |
| Is there a test environment? | No/broken | +$300K infrastructure |

### Integration Considerations (Buyer + Target)

| Scenario | Complexity | Recommendation |
|----------|------------|----------------|
| Both on S/4HANA (same version) | Lower | Consolidate quickly |
| Both on S/4HANA (different versions) | Medium | Align versions first |
| One S/4, one ECC | High | Migrate target to S/4 |
| Both on ECC | Highest | Combined S/4 program |
| Target on Oracle/other | Very High | Full reimplementation |

---

## Cost Estimation Signals

| Factor | Base Impact | Multiplier |
|--------|-------------|------------|
| Company size (users) | Per-user licensing | 1.0x-2.0x |
| Industry complexity | Manufacturing > Services | 1.0x-1.5x |
| Geographic spread | Multi-country | 1.2x-1.8x |
| Customization level | Z-programs, enhancements | 1.0x-2.0x |
| Data volume | >10TB | 1.2x-1.5x |
| Integration complexity | Interfaces count | 1.0x-1.5x |
| Change readiness | Culture/history | 1.0x-1.3x |

---

## Common Failure Modes

1. **Data Quality Underestimated** - 40% of projects delayed by data issues
2. **Integration Scope Creep** - "We forgot about that interface"
3. **Business Engagement Lacking** - IT-led without business ownership
4. **Custom Code Remediation** - Z-programs not assessed early
5. **Testing Compressed** - Go-live pressure reduces test cycles
6. **Change Management Neglected** - Users reject new system
7. **Parallel Run Too Short** - Issues discovered after ECC shutdown

---

## Key Questions for Document Analysis

When analyzing IT DD documents, look for these SAP-related signals:

1. **Version and Support Status**
   - "SAP ECC 6.0" → End of mainstream maintenance
   - "Enhancement Pack X" → Determines upgrade path
   - "Maintenance extension" → Indicates delay/cost

2. **Technical Debt Indicators**
   - "Custom development" / "Z-programs" → Remediation needed
   - "OSS notes backlog" → Technical debt
   - "Basis support outsourced" → Knowledge gap

3. **Business Process Signals**
   - "Multiple instances" → Consolidation needed
   - "Different processes by BU" → Harmonization effort
   - "Acquired companies on separate SAP" → Integration work

4. **Integration Red Flags**
   - "Point-to-point interfaces" → Middleware investment
   - "EDI" / "trading partners" → Regression testing
   - "Custom middleware" → Migration risk

---

*Playbook Version: 1.0*
*Last Updated: January 2026*
