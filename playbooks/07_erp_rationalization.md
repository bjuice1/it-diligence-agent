# ERP Rationalization (Dual/Multiple ERP) Playbook

## Overview

Running multiple ERP systems is one of the most expensive IT operational challenges. Whether inherited through M&A or organic growth, dual/multiple ERP environments create complexity, duplication, and risk. This playbook addresses the upstream and downstream dependencies for ERP rationalization programs.

**Typical Duration:** 18-48 months (full consolidation)
**Cost Range:** $10M-$100M+ (depends on scope)
**Risk Level:** Critical (business operations at stake)

---

## ERP Rationalization Decision Framework

```
                    ┌────────────────────────────────────────┐
                    │     CURRENT STATE: MULTIPLE ERPs       │
                    └───────────────────┬────────────────────┘
                                        │
                    ┌───────────────────▼────────────────────┐
                    │     DECISION DRIVERS                    │
                    │                                         │
                    │  • Cost of dual operations             │
                    │  • Business process harmonization      │
                    │  • Data/reporting consolidation        │
                    │  • Technical debt (EOL systems)        │
                    │  • M&A integration requirements        │
                    └───────────────────┬────────────────────┘
                                        │
        ┌───────────────────────────────┼───────────────────────────────┐
        │                               │                               │
        ▼                               ▼                               ▼
┌───────────────────┐       ┌───────────────────┐       ┌───────────────────┐
│    CONSOLIDATE    │       │    BEST-OF-BREED  │       │    COEXISTENCE    │
│    (One ERP)      │       │    (Hybrid)       │       │    (Parallel)     │
├───────────────────┤       ├───────────────────┤       ├───────────────────┤
│                   │       │                   │       │                   │
│ • Single system   │       │ • Keep strengths  │       │ • Maintain both   │
│ • Full migration  │       │   from each ERP   │       │ • Integration     │
│ • One version     │       │ • Integration     │       │   layer           │
│   of truth        │       │   middleware      │       │ • Accept dual     │
│ • Simplified ops  │       │ • Best-fit modules│       │   cost            │
│                   │       │                   │       │                   │
│ Risk: High        │       │ Risk: Medium      │       │ Risk: Low         │
│ Cost: Highest     │       │ Cost: Medium      │       │ Cost: Ongoing     │
│ Timeline: Longest │       │ Timeline: Medium  │       │ Timeline: Quick   │
└───────────────────┘       └───────────────────┘       └───────────────────┘
```

---

## Common Dual ERP Scenarios

### Scenario 1: M&A Integration (Most Common)

```
     BUYER                              TARGET
┌──────────────────┐              ┌──────────────────┐
│     SAP S/4      │              │   Oracle EBS     │
│                  │              │                  │
│  • Finance       │              │  • Finance       │
│  • HR            │              │  • HR            │
│  • Supply Chain  │              │  • Manufacturing │
│  • Sales         │              │  • Distribution  │
└────────┬─────────┘              └────────┬─────────┘
         │                                  │
         │       POST-ACQUISITION           │
         │                                  │
         └──────────────┬───────────────────┘
                        │
            ┌───────────▼───────────┐
            │  INTEGRATION OPTIONS  │
            ├───────────────────────┤
            │ A. Migrate target to  │
            │    buyer's SAP        │
            │                       │
            │ B. Migrate buyer to   │
            │    target's Oracle    │
            │                       │
            │ C. New ERP for both   │
            │    (greenfield)       │
            │                       │
            │ D. Integration layer  │
            │    (coexistence)      │
            └───────────────────────┘
```

### Scenario 2: Organic Growth (Legacy + Modern)

```
┌─────────────────────────────────────────────────────────────────┐
│                        TYPICAL PATTERN                           │
│                                                                  │
│   LEGACY ERP                          MODERN ERP                │
│   (Division A)                        (Division B)               │
│                                                                  │
│   ┌──────────────┐                   ┌──────────────┐           │
│   │ AS/400 / JDE │                   │ SAP / Oracle │           │
│   │              │                   │    Cloud     │           │
│   │ • 20+ years  │                   │              │           │
│   │ • Stable     │                   │ • 5 years    │           │
│   │ • COBOL      │                   │ • Growing    │           │
│   │ • Key person │                   │ • Modern     │           │
│   │   dependent  │                   │   skills     │           │
│   └──────────────┘                   └──────────────┘           │
│                                                                  │
│   CHALLENGE: Key person risk + EOL technology vs cost to migrate│
└─────────────────────────────────────────────────────────────────┘
```

### Scenario 3: Divisional Autonomy

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                  │
│   CORPORATE HOLDING                                             │
│   ┌───────────────────────────────────────────────────────┐    │
│   │              Corporate Finance (Hyperion)              │    │
│   └───────────────────────────────────────────────────────┘    │
│              │                │                │                 │
│              ▼                ▼                ▼                 │
│   ┌──────────────┐ ┌──────────────┐ ┌──────────────┐           │
│   │ Division 1   │ │ Division 2   │ │ Division 3   │           │
│   │ SAP          │ │ Oracle       │ │ NetSuite     │           │
│   │              │ │              │ │              │           │
│   │ Manufacturing│ │ Services     │ │ E-commerce   │           │
│   └──────────────┘ └──────────────┘ └──────────────┘           │
│                                                                  │
│   CHALLENGE: Consolidated reporting, shared services            │
└─────────────────────────────────────────────────────────────────┘
```

---

## Dependency Map

```
                    ┌─────────────────────────────────────────────────────────┐
                    │              UPSTREAM DEPENDENCIES                       │
                    │  (Must be complete BEFORE ERP rationalization)           │
                    └─────────────────────────────────────────────────────────┘
                                              │
        ┌─────────────────┬──────────────────┼──────────────────┬─────────────────┐
        ▼                 ▼                  ▼                  ▼                 ▼
┌───────────────┐ ┌───────────────┐ ┌───────────────┐ ┌───────────────┐ ┌───────────────┐
│ Business      │ │  Data         │ │  Process      │ │  Integration  │ │  Technical    │
│ Strategy      │ │  Assessment   │ │  Mapping      │ │  Inventory    │ │  Assessment   │
│               │ │               │ │               │ │               │ │               │
│ - Target      │ │ - Data quality│ │ - Current     │ │ - All         │ │ - Platform    │
│   state       │ │ - Master data │ │   processes   │ │   interfaces  │ │   assessment  │
│ - Timeline    │ │ - Migration   │ │ - Future      │ │ - EDI         │ │ - Customization│
│ - Investment  │ │   scope       │ │   state       │ │ - Middleware  │ │   inventory   │
└───────────────┘ └───────────────┘ └───────────────┘ └───────────────┘ └───────────────┘
                                              │
                    ┌─────────────────────────────────────────────────────────┐
                    │                 ERP RATIONALIZATION                       │
                    │                                                          │
                    │  Plan → Foundation → Migration Waves → Optimization     │
                    └─────────────────────────────────────────────────────────┘
                                              │
        ┌─────────────────┬──────────────────┼──────────────────┬─────────────────┐
        ▼                 ▼                  ▼                  ▼                 ▼
┌───────────────┐ ┌───────────────┐ ┌───────────────┐ ┌───────────────┐ ┌───────────────┐
│ Legacy        │ │  License      │ │  Integration  │ │  Reporting    │ │  Shared       │
│ Decommission  │ │  Optimization │ │  Consolidation│ │  Unification  │ │  Services     │
│               │ │               │ │               │ │               │ │               │
│ - Sunset old  │ │ - Reduce dual │ │ - Single      │ │ - One BI      │ │ - Finance     │
│   systems     │ │   licensing   │ │   integration │ │   platform    │ │ - HR          │
│ - Archive     │ │ - Maintenance │ │   architecture│ │ - Consistent  │ │ - Procurement │
│ - Knowledge   │ │   consolidate │ │ - API         │ │   KPIs        │ │               │
└───────────────┘ └───────────────┘ └───────────────┘ └───────────────┘ └───────────────┘
                    │              DOWNSTREAM DEPENDENCIES                     │
                    │  (Enabled after ERP rationalization)                     │
                    └─────────────────────────────────────────────────────────┘
```

---

## Upstream Dependencies (Prerequisites)

### 1. Business Strategy & Executive Alignment
**Must complete before:** Any technical work

| Dependency | Why Required | Blocking Risk |
|------------|--------------|---------------|
| Target state decision | Know where going | Wasted effort |
| Investment approval | Funding secured | Project stops |
| Timeline alignment | Business readiness | Disruption |
| Executive sponsorship | Change authority | Resistance |
| Business case | Justification | No support |

**Complexity Signals:**
- "No decision on target ERP" → Blocked
- "Competing executive priorities" → Political risk
- "Budget not approved" → Cannot staff
- "M&A uncertainty" → More acquisitions coming?

### 2. Data Assessment & Master Data Strategy
**Must complete before:** Migration planning

| Dependency | Why Required | Blocking Risk |
|------------|--------------|---------------|
| Data quality assessment | Know what to cleanse | Migration failures |
| Master data mapping | Customer, vendor, material | Duplicate records |
| Data ownership | Who decides | Disputes |
| Data migration scope | What moves, what archives | Scope creep |
| Historical data requirements | Retention needs | Compliance risk |

**Data Synchronization Challenge:**

```
     ERP A                              ERP B
┌──────────────┐                  ┌──────────────┐
│ CUSTOMER     │                  │ CUSTOMER     │
│ Master       │                  │ Master       │
│              │                  │              │
│ ID: 1001     │   SAME CUSTOMER  │ ID: A-500    │
│ Acme Corp    │◄────────────────►│ ACME         │
│ 123 Main St  │   DIFFERENT IDs  │ 123 Main     │
└──────────────┘                  └──────────────┘
                        │
                        ▼
            ┌───────────────────────┐
            │ MASTER DATA MGMT      │
            │ (MDM required before  │
            │  ERP consolidation)   │
            └───────────────────────┘
```

**Complexity Signals:**
- "No MDM platform" → Data rationalization effort
- "Different chart of accounts" → Finance mapping
- "Different item numbers" → Material mapping
- "No data governance" → Ownership disputes

### 3. Business Process Mapping
**Must complete before:** Fit-gap analysis

| Dependency | Why Required | Blocking Risk |
|------------|--------------|---------------|
| Current state processes | Understand both ERPs | Missed requirements |
| Future state design | Target operating model | Rework |
| Process harmonization | Align before migrate | Resistance |
| Process owners identified | Decision authority | Delays |
| Gap analysis | Custom development | Scope uncertainty |

**Process Harmonization Challenge:**

```
                    PROCESS HARMONIZATION

ERP A: Order-to-Cash              ERP B: Order-to-Cash
─────────────────────             ─────────────────────
1. Quote created                  1. Opportunity created
2. Order entered                  2. Quote from opportunity
3. Credit check                   3. Order from quote
4. Inventory allocated            4. Credit check (different rules)
5. Ship                          5. Pick → Pack → Ship
6. Invoice                       6. Invoice
7. Cash applied                  7. Cash applied (different matching)

                        │
                        ▼
            ┌───────────────────────┐
            │  HARMONIZED PROCESS   │
            │  (One way to do it)   │
            │                       │
            │  Requires business    │
            │  decisions before     │
            │  ERP work begins      │
            └───────────────────────┘
```

**Complexity Signals:**
- "Each division does it differently" → Harmonization effort
- "Processes not documented" → Extended discovery
- "Heavy customization (Z-programs, extensions)" → Remediation
- "Regulatory differences by region" → Cannot fully harmonize

### 4. Integration Inventory
**Must complete before:** Architecture design

| Dependency | Why Required | Blocking Risk |
|------------|--------------|---------------|
| All interfaces documented | Migration scope | Broken integrations |
| EDI trading partners | Partner testing | Order failures |
| Middleware assessment | Integration approach | Architecture decision |
| API inventory | Modern integrations | Service disruption |
| Batch job dependencies | Timing requirements | Data sync issues |

**Integration Complexity Matrix:**

| From/To | ERP A | ERP B | External | Complexity |
|---------|-------|-------|----------|------------|
| ERP A | - | High (intercompany) | 50 interfaces | Complex |
| ERP B | High | - | 30 interfaces | Moderate |
| External | CRM, WMS, TMS | BI, Banks | Partners | High |

**Complexity Signals:**
- "500+ interfaces between systems" → Major integration work
- "Real-time intercompany" → Complex cutover
- "No middleware (point-to-point)" → Architecture investment
- "Custom file formats" → Transformation work

### 5. Technical Platform Assessment
**Must complete before:** Target architecture

| Dependency | Why Required | Blocking Risk |
|------------|--------------|---------------|
| Platform health (both ERPs) | Understand current state | Surprises |
| Customization inventory | Migration scope | Underestimated effort |
| Version/support status | EOL timeline | Forced timeline |
| Skills assessment | Team capabilities | Staffing gaps |
| Infrastructure assessment | Hosting approach | Capacity issues |

**Complexity Signals:**
- "1000+ custom objects" → Extensive remediation
- "EOL in 12 months" → Timeline pressure
- "No internal expertise" → Partner dependency
- "Different databases (Oracle vs SQL)" → Additional complexity

---

## Downstream Dependencies (Enabled After Rationalization)

### 1. Legacy ERP Decommissioning
**Blocked until:** All users/data migrated

| Dependency | Why Blocked | Impact of Delay |
|------------|-------------|-----------------|
| System shutdown | Users still transacting | Dual operations cost |
| License termination | Contractual obligations | Continued payments |
| Infrastructure reclamation | Systems in use | DC costs |
| Support contract end | Need fallback | Vendor fees |
| Knowledge transition | Staff still supporting | Stranded expertise |

**Typical Timeline:** 6-12 months post-migration

### 2. License Optimization
**Blocked until:** User migration complete

| Dependency | Why Blocked | Impact of Delay |
|------------|-------------|-----------------|
| License consolidation | Users on both systems | Double licensing |
| Named user optimization | Need final user count | Over-licensed |
| Module consolidation | Need final scope | Unused modules |
| Maintenance reduction | Both systems maintained | 20%+ savings delayed |

**Typical Timeline:** Immediately post-migration

### 3. Integration Architecture Consolidation
**Blocked until:** Single ERP target state

| Dependency | Why Blocked | Impact of Delay |
|------------|-------------|-----------------|
| Single integration layer | Two ERP targets | Dual maintenance |
| API standardization | Different data models | Integration complexity |
| Middleware consolidation | Different middleware | License costs |
| Partner re-onboarding | Two connection points | Partner confusion |

**Typical Timeline:** 3-6 months post-migration

### 4. Reporting & Analytics Unification
**Blocked until:** Data consolidated

| Dependency | Why Blocked | Impact of Delay |
|------------|-------------|-----------------|
| Single BI platform | Two data sources | Reconciliation effort |
| Consistent KPIs | Different definitions | Misleading metrics |
| Executive dashboards | Multiple sources | Manual consolidation |
| Financial consolidation | Different CoA | Close cycle extended |

**Typical Timeline:** 6-12 months post-migration

### 5. Shared Services Enablement
**Blocked until:** Processes harmonized

| Dependency | Why Blocked | Impact of Delay |
|------------|-------------|-----------------|
| Finance shared services | Different processes | Cannot centralize |
| HR shared services | Different HR systems | Dual payroll |
| Procurement centralization | Different P2P | No leverage |
| IT consolidation | Different platforms | Dual support |

**Typical Timeline:** 12-24 months post-migration

---

## Cost Estimation Signals

| Factor | Impact | Multiplier |
|--------|--------|------------|
| User count (combined) | Migration scope | Base metric |
| Transaction volume | Data migration | 1.0x-1.5x |
| Customization count | Remediation effort | 1.3x-2.5x |
| Integration count | Interface work | +$20K-100K per interface |
| Process differences | Harmonization | 1.2x-1.8x |
| Data quality | Cleansing effort | 1.2x-1.5x |
| Legacy complexity | Special handling | 1.5x-2.5x |
| Geographic spread | Coordination | 1.2x-1.5x |
| Regulatory requirements | Compliance | 1.2x-1.5x |
| Timeline pressure | Premium | 1.3x-2.0x |

**Typical Range by Scenario:**

| Scenario | Users | Timeline | Cost Range |
|----------|-------|----------|------------|
| Small M&A (absorb target) | <500 | 12-18 months | $2-5M |
| Medium M&A (equal size) | 500-2000 | 18-30 months | $5-20M |
| Large M&A | 2000-10000 | 24-48 months | $20-50M |
| Enterprise consolidation | 10000+ | 36-60 months | $50-100M+ |

---

## M&A Due Diligence Checklist

### Pre-Deal Assessment

| Question | Red Flag Answer | Cost Impact |
|----------|-----------------|-------------|
| What ERPs exist? | Multiple (2+) | Rationalization cost |
| ERP version/support? | EOL / unsupported | Forced timeline |
| Customization level? | Heavy (500+ objects) | Remediation |
| Integration count? | High (200+) | Interface work |
| Data quality? | Poor / unknown | Cleansing effort |
| Process documentation? | None | Discovery work |
| Key person dependency? | Yes (legacy ERP) | Knowledge risk |
| Chart of accounts? | Different | Finance mapping |
| Master data governance? | None | MDM investment |
| Transaction volume? | High | Migration complexity |

### Integration Decision Factors

| Factor | Favor Consolidation | Favor Coexistence |
|--------|---------------------|-------------------|
| Deal type | Full acquisition | Joint venture |
| Timeline | Long-term ownership | Uncertain hold |
| Synergy targets | High cost savings | Low savings target |
| Business similarity | Same industry | Different industries |
| Regulatory | Same requirements | Different requirements |
| Geographic | Same regions | Different regions |

---

## Common Failure Modes

1. **No Business Decision** - Technical team waiting for direction
2. **Underestimated Customization** - Discovered mid-migration
3. **Data Quality Ignored** - Migration failures due to bad data
4. **Process Not Harmonized** - Trying to migrate chaos
5. **Integration Forgotten** - External systems break
6. **Testing Compressed** - Go-live issues
7. **Training Neglected** - Users can't operate
8. **Parallel Run Too Short** - Issues after legacy shutdown
9. **Key Person Departure** - Legacy knowledge lost
10. **Scope Creep** - "While we're at it..." syndrome

---

## Key Questions for Document Analysis

When analyzing IT DD documents, look for these ERP signals:

1. **Multiple ERP Indicators**
   - "SAP" and "Oracle" in same document → Dual ERP
   - "JD Edwards" / "AS/400" / "legacy ERP" → Modernization candidate
   - "Acquired company's system" → Integration decision
   - "Divisional systems" → Consolidation opportunity

2. **Complexity Signals**
   - "Intercompany transactions" → Integration complexity
   - "Different chart of accounts" → Finance harmonization
   - "Custom development" / "modifications" → Remediation scope
   - "Different item numbers" → Master data mapping

3. **Risk Indicators**
   - "Key person" / "tribal knowledge" → Legacy risk
   - "EOL" / "unsupported" → Forced timeline
   - "No documentation" → Extended discovery
   - "Integration issues" → Current pain points

4. **Cost Signals**
   - "Dual maintenance" → Ongoing cost
   - "License true-up" → Compliance risk
   - "Support contracts" → Multiple vendor fees
   - "Two data centers" → Infrastructure duplication

---

## Timeline Example: M&A ERP Consolidation

```
Month:  1   3   6   9  12  15  18  21  24  27  30  33  36
        │   │   │   │   │   │   │   │   │   │   │   │   │
Assessment  ████│
& Planning      │
                │
Data        ████████████│
Preparation             │
                        │
Process             ████████████████│
Harmonization                       │
                                    │
Foundation                  ████████████│
(Target ERP)                            │
                                        │
Wave 1:                         ████████████│
Finance/HR                                  │
                                            │
Wave 2:                                 ████████████│
Supply Chain                                        │
                                                    │
Wave 3:                                         ████████████│
Manufacturing                                               │
                                                            │
Legacy                                                  ████████│
Decommission                                                    │
                                                                │
Optimization                                                ████████
& Shared Svcs
```

---

*Playbook Version: 1.0*
*Last Updated: January 2026*
