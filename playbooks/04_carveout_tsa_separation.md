# Carveout & TSA Separation Playbook

## Overview

IT carveouts (divestitures) are among the most complex M&A scenarios. The divested business must separate from parent company shared services while maintaining business continuity, typically under a Transition Services Agreement (TSA). This playbook maps the critical dependencies for Day 1 readiness and TSA exit.

**Typical Duration:** 12-24 months (6-9 months to Day 1, 6-18 months TSA)
**Cost Range:** $5M-$50M+ (depends on entanglement depth)
**Risk Level:** Critical (business continuity at stake)

---

## Carveout Lifecycle

```
                    PARENT COMPANY ENVIRONMENT
┌──────────────────────────────────────────────────────────────────────────────┐
│                                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │ Shared ERP   │  │ Shared       │  │ Shared       │  │ Shared       │    │
│  │ (SAP/Oracle) │  │ Active Dir   │  │ Network      │  │ Data Center  │    │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘    │
│         │                 │                 │                 │            │
│         │    DIVESTED BUSINESS UNIT (ENTANGLED)              │            │
│         │  ┌─────────────────────────────────────────────────┐│            │
│         └──┤  • Users on shared AD                           ├┘            │
│            │  • Transactions in shared ERP                   │             │
│            │  • Apps in shared data center                   │             │
│            │  • Network on parent infrastructure             │             │
│            └─────────────────────────────────────────────────┘             │
└──────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ SEPARATION
                                    ▼
┌────────────────────────────┐    ┌────────────────────────────────────────────┐
│        TSA PERIOD          │    │           STANDALONE ENVIRONMENT           │
│                            │    │                                            │
│  • Parent provides services│    │  ┌──────────────┐  ┌──────────────┐       │
│  • Monthly fees            │───►│  │ New ERP      │  │ New          │       │
│  • Exit milestones         │    │  │ Instance     │  │ Active Dir   │       │
│  • Typically 6-18 months   │    │  └──────────────┘  └──────────────┘       │
│                            │    │  ┌──────────────┐  ┌──────────────┐       │
│                            │    │  │ New          │  │ New/Cloud    │       │
│                            │    │  │ Network      │  │ Data Center  │       │
│                            │    │  └──────────────┘  └──────────────┘       │
└────────────────────────────┘    └────────────────────────────────────────────┘
```

---

## Dependency Map

```
                    ┌─────────────────────────────────────────────────────────┐
                    │              UPSTREAM DEPENDENCIES                       │
                    │  (Must be complete BEFORE separation can begin)          │
                    └─────────────────────────────────────────────────────────┘
                                              │
        ┌─────────────────┬──────────────────┼──────────────────┬─────────────────┐
        ▼                 ▼                  ▼                  ▼                 ▼
┌───────────────┐ ┌───────────────┐ ┌───────────────┐ ┌───────────────┐ ┌───────────────┐
│ Entanglement  │ │  TSA          │ │  Day 1        │ │  Data         │ │  Standalone   │
│ Assessment    │ │  Negotiation  │ │  Requirements │ │  Separation   │ │  Architecture │
│               │ │               │ │               │ │               │ │               │
│ - Shared      │ │ - Scope       │ │ - Legal entity│ │ - What data   │ │ - Target      │
│   systems     │ │ - Duration    │ │ - Banking     │ │   moves       │ │   state       │
│ - Data flows  │ │ - Exit terms  │ │ - Compliance  │ │ - Privacy     │ │ - Cloud vs    │
│ - Dependencies│ │ - Costs       │ │ - Operations  │ │ - Ownership   │ │   on-prem     │
└───────────────┘ └───────────────┘ └───────────────┘ └───────────────┘ └───────────────┘
                                              │
                    ┌─────────────────────────────────────────────────────────┐
                    │                    CARVEOUT PROGRAM                       │
                    │                                                          │
                    │  Day 1 Prep → Day 1 → TSA Operations → TSA Exit         │
                    └─────────────────────────────────────────────────────────┘
                                              │
        ┌─────────────────┬──────────────────┼──────────────────┬─────────────────┐
        ▼                 ▼                  ▼                  ▼                 ▼
┌───────────────┐ ┌───────────────┐ ┌───────────────┐ ┌───────────────┐ ┌───────────────┐
│ Standalone    │ │  Staff        │ │  Vendor       │ │  Data         │ │  Parent       │
│ IT Ops        │ │  Transition   │ │  Contracts    │ │  Migration    │ │  Disentangle  │
│               │ │               │ │               │ │               │ │               │
│ - Own IT team │ │ - IT staff    │ │ - License     │ │ - ERP data    │ │ - Remove      │
│ - Support     │ │   transfer    │ │   transfer    │ │ - Files       │ │   access      │
│   contracts   │ │ - Training    │ │ - New         │ │ - Historical  │ │ - Clean up    │
│ - Tools       │ │ - Knowledge   │ │   contracts   │ │   records     │ │   remnants    │
└───────────────┘ └───────────────┘ └───────────────┘ └───────────────┘ └───────────────┘
                    │              DOWNSTREAM DEPENDENCIES                     │
                    │  (Cannot complete until carveout/TSA finishes)           │
                    └─────────────────────────────────────────────────────────┘
```

---

## Upstream Dependencies (Prerequisites)

### 1. Entanglement Assessment
**Must complete before:** TSA negotiation and architecture

| Dependency | Why Required | Blocking Risk |
|------------|--------------|---------------|
| Shared system inventory | Understand separation scope | Unknown scope |
| Data flow mapping | Know what data moves/copies | Data gaps |
| Integration inventory | Understand touchpoints | Broken processes |
| User access audit | Who has access to what | Access issues |
| Cost allocation baseline | Current IT cost to divested unit | TSA pricing |

**Entanglement Levels:**
```
Level 1 - Minimal           Level 2 - Moderate          Level 3 - Deep
─────────────────────       ─────────────────────       ─────────────────────
• Separate ERP instance     • Shared ERP, separate      • Shared ERP instance
• Own email domain            company codes             • Intercompany data
• Separate network          • Shared AD forest          • Shared processes
• Own applications          • Some shared apps          • Common masters
                            • Network peering           • Fully integrated

Separation: 3-6 months      Separation: 6-12 months     Separation: 12-24 months
```

**Complexity Signals:**
- "Single SAP instance for all BUs" → Deep entanglement
- "Shared master data" → Data separation challenge
- "Common customer records" → Ownership disputes
- "Intercompany transactions daily" → Complex cutover
- "Divested unit has no IT staff" → Stranded costs

### 2. TSA Negotiation & Terms
**Must complete before:** Day 1 planning

| Dependency | Why Required | Blocking Risk |
|------------|--------------|---------------|
| TSA scope defined | What parent provides | Uncosted services |
| Duration agreed | Exit timeline | Indefinite dependency |
| Exit milestones | Triggers for service end | No offramp |
| Pricing model | Monthly fees | Budget uncertainty |
| Extension terms | If milestones slip | Penalty costs |
| SLAs defined | Performance expectations | Quality disputes |

**TSA Scope Categories:**
| Category | Typical Services | Typical Duration |
|----------|-----------------|------------------|
| Infrastructure | Data center, network, hosting | 12-18 months |
| Applications | ERP, email, core apps | 12-24 months |
| End User | Helpdesk, desktop support | 6-12 months |
| Security | SOC, IAM, compliance | 12-18 months |
| Data | Reporting, analytics, BI | 6-12 months |

**Complexity Signals:**
- "TSA terms not negotiated" → Blocked program
- "No exit milestones" → Indefinite dependency
- "Parent unwilling to extend" → Aggressive timeline
- "Cost plus pricing" → Budget uncertainty

### 3. Day 1 Requirements
**Must complete before:** Close

| Dependency | Why Required | Blocking Risk |
|------------|--------------|---------------|
| Legal entity setup | Operating structure | Cannot transact |
| Banking relationships | Treasury operations | No cash flow |
| Compliance requirements | Regulatory obligations | Legal risk |
| Insurance coverage | Risk management | Exposure |
| Basic IT operations | Business continuity | Operations halt |

**Day 1 Minimum Viable IT:**
```
MUST HAVE (Day 1)           SHOULD HAVE (Day 1-30)      CAN WAIT (TSA)
─────────────────────       ─────────────────────       ─────────────────────
• Email working             • Own email domain          • ERP separation
• Network connectivity      • New AD/identity           • App migration
• ERP access (via TSA)      • Basic security            • Data migration
• Core app access           • Helpdesk                  • Full independence
• Phone/communications      • Endpoint management
```

**Complexity Signals:**
- "Close in 30 days" → Compressed Day 1 prep
- "Regulatory requirements unclear" → Compliance risk
- "No treasury function" → Banking setup needed
- "Divested unit in multiple countries" → Multi-jurisdiction

### 4. Data Separation & Ownership
**Must complete before:** Architecture finalization

| Dependency | Why Required | Blocking Risk |
|------------|--------------|---------------|
| Data ownership determined | Legal rights | Disputes |
| Privacy requirements | GDPR, CCPA, etc. | Compliance violations |
| Historical data access | Audit requirements | Regulatory risk |
| Master data split | Customer, vendor, material | Duplicate/orphan records |
| IP data separation | Trade secrets, proprietary | Legal exposure |

**Data Separation Scenarios:**
| Data Type | Complexity | Approach |
|-----------|------------|----------|
| Transactional (orders, invoices) | Medium | Copy to divested |
| Master data (customers, vendors) | High | Clone + dedup |
| Historical/Archive | Medium | Copy with retention |
| Shared customers | Very High | Determine ownership |
| Intercompany eliminated | Medium | Clean up pre-close |

**Complexity Signals:**
- "Shared customer master" → Ownership negotiation
- "No data classification" → Discovery needed
- "Multi-country data" → Privacy complexity
- "Litigation hold on data" → Legal constraints

### 5. Standalone Architecture Design
**Must complete before:** Build activities

| Dependency | Why Required | Blocking Risk |
|------------|--------------|---------------|
| Target state architecture | Know what to build | Rework |
| Cloud vs on-prem decision | Infrastructure approach | Stranded investment |
| Application strategy | Build, buy, migrate | Timeline uncertainty |
| Integration architecture | How systems connect | Data flow gaps |
| Security architecture | Compliance requirements | Security gaps |

**Architecture Decisions:**
```
                        STANDALONE ARCHITECTURE OPTIONS

┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  OPTION A: Lift & Shift          OPTION B: Modernize           OPTION C:   │
│  (Replicate parent)              (Cloud-first)                 Hybrid      │
│                                                                             │
│  ┌─────────────┐                ┌─────────────┐               ┌──────────┐ │
│  │ On-prem DC  │                │    Cloud    │               │ Cloud    │ │
│  │ Same stack  │                │ AWS/Azure   │               │ + On-prem│ │
│  │ as parent   │                │ New apps    │               │ Mix      │ │
│  └─────────────┘                └─────────────┘               └──────────┘ │
│                                                                             │
│  Pros:                          Pros:                          Pros:       │
│  • Fastest (known)              • Future-proof                 • Flexible  │
│  • Lower risk                   • Scalable                     • Staged    │
│  • Staff familiar               • Lower capex                              │
│                                                                             │
│  Cons:                          Cons:                          Cons:       │
│  • Technical debt               • Learning curve               • Complex   │
│  • Capex heavy                  • Longer timeline              • Two envs  │
│  • May need refresh             • Change risk                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## TSA Exit Sequencing

### Typical Exit Order (Lowest to Highest Dependency)

```
                                    TSA EXIT SEQUENCE

Month:  1   2   3   4   5   6   7   8   9  10  11  12  13  14  15  16  17  18
        │   │   │   │   │   │   │   │   │   │   │   │   │   │   │   │   │   │

End User    ████████████│ EXIT
Services                │
(Helpdesk)              │
                        │
Collaboration       ████████████████│ EXIT
(Email, Teams)                      │
                                    │
Identity                    ████████████████│ EXIT
(AD, SSO)                                   │
                                            │
Network                         ████████████████████│ EXIT
(WAN, Internet)                                     │
                                                    │
Security                            ████████████████████████│ EXIT
(SOC, IAM)                                                  │
                                                            │
Infrastructure                              ████████████████████████│ EXIT
(Hosting, DC)                                                       │
                                                                    │
ERP/Core                                            ████████████████████████│ EXIT
Applications
```

### Exit Dependencies (What Blocks What)

| To Exit This... | You Must First Complete... |
|-----------------|---------------------------|
| End User Services | New helpdesk contract |
| Email/Collaboration | New M365 tenant + migration |
| Identity | New AD + user migration |
| Network | New WAN + internet connectivity |
| Security | New SOC + security stack |
| Infrastructure | New hosting + app migration |
| ERP | New instance + data migration |

---

## Downstream Dependencies (Blocked Until TSA Exit)

### 1. Standalone IT Operations
**Blocked until:** TSA services transitioned

| Dependency | Why Blocked | Impact of Delay |
|------------|-------------|-----------------|
| Own IT team fully operational | TSA provides services | Extended TSA costs |
| Support contracts established | Parent providing support | No vendor relationships |
| Monitoring tools deployed | Using parent's tools | No visibility |
| Incident management process | Shared with parent | Process gaps |

### 2. Staff Transition
**Blocked until:** Separation agreement + systems ready

| Dependency | Why Blocked | Impact of Delay |
|------------|-------------|-----------------|
| IT staff transfer | Legal/HR process | Knowledge gaps |
| Training on new systems | Systems must exist | Operational risk |
| Knowledge transfer | Parent cooperation | Lost institutional knowledge |
| New org structure | Scope clarity | Role confusion |

### 3. Vendor Contract Transfer
**Blocked until:** Standalone entity + systems clear

| Dependency | Why Blocked | Impact of Delay |
|------------|-------------|-----------------|
| License transfer | Need to know what's needed | Compliance risk |
| New maintenance contracts | Architecture finalized | Support gaps |
| SaaS subscriptions | Tenant established | Service gaps |
| Hardware ownership | Asset inventory | Capital planning |

### 4. Data Migration
**Blocked until:** Target systems ready + data ownership agreed

| Dependency | Why Blocked | Impact of Delay |
|------------|-------------|-----------------|
| ERP data migration | New instance required | No historical data |
| File migration | New storage | Lost documents |
| Archive transfer | Retention requirements | Compliance risk |
| Analytics/BI data | New platform | No reporting |

### 5. Parent Disentanglement
**Blocked until:** All TSA services exited

| Dependency | Why Blocked | Impact of Delay |
|------------|-------------|-----------------|
| Remove divested user access | TSA access still needed | Ongoing access |
| Clean up shared accounts | Service accounts in use | Security risk |
| Delete divested data | Data still in use | Storage/compliance |
| Close TSA formally | Services still consumed | Continued fees |

---

## Cost Estimation Signals

| Factor | Impact | Multiplier |
|--------|--------|------------|
| Entanglement level | Overall complexity | 1.0x-3.0x |
| User count (divested) | Migration scope | 1.0x (<500), 1.5x (500-2K), 2.0x (>2K) |
| Shared ERP | Highest complexity driver | 1.5x-3.0x |
| Number of applications | Migration scope | +$50K per major app |
| Countries involved | Multi-jurisdiction | 1.2x per country |
| Timeline compression | Premium for speed | 1.3x-2.0x |
| TSA duration | Monthly fees | $500K-$2M/month typical |
| Greenfield vs lift/shift | Architecture choice | 0.8x vs 1.2x |
| Parent cooperation level | Execution risk | 1.0x-1.5x |

---

## M&A Due Diligence Checklist

### Pre-Deal Assessment (Buyer's Perspective)

| Question | Red Flag Answer | Cost Impact |
|----------|-----------------|-------------|
| Is there a shared ERP? | Yes, single instance | +$5-15M ERP separation |
| Shared Active Directory? | Yes, single forest | +$500K-1M AD separation |
| Does divested unit have IT staff? | No | +$1-2M to build IT org |
| What's the TSA duration cap? | 6 months or less | Aggressive timeline risk |
| Can TSA be extended? | No / unclear | Execution risk |
| Who owns customer data? | Unclear | Legal disputes |
| Are there shared vendors? | Yes, many | Contract negotiations |
| What's the parent's motivation? | Hostile / rushed | Cooperation risk |
| Historical data access? | Unclear | Compliance risk |
| Intercompany transactions? | High volume | Cutover complexity |

### Entanglement Assessment Matrix

| System | Dedicated | Shared-Separate | Fully Shared | Separation Effort |
|--------|-----------|-----------------|--------------|-------------------|
| ERP | ✓ Low | ◐ Medium | ✗ High | $2-15M |
| Email | ✓ Low | ◐ Medium | ✗ Medium | $200K-1M |
| Active Directory | ✓ Low | ◐ Medium | ✗ Medium | $300K-1M |
| Network | ✓ Low | ◐ Medium | ✗ Medium | $500K-2M |
| Data Center | ✓ Low | ◐ Medium | ✗ High | $1-5M |
| Security (SOC) | ✓ Low | ◐ Medium | ✗ Medium | $500K-1.5M |
| Helpdesk | ✓ Low | ◐ Low | ✗ Low | $100K-300K |

---

## Common Failure Modes

1. **Underestimated Entanglement** - "It's mostly separate" turns out to be deeply shared
2. **TSA Too Short** - 6 months TSA with 18 months of work
3. **No TSA Extension Clause** - Stuck if milestones slip
4. **Data Ownership Disputes** - Who owns shared customer records?
5. **Parent Uncooperative** - Minimal support during TSA
6. **Key Person Departure** - Staff with knowledge leave before transfer
7. **Hidden Integrations** - Unknown data flows discovered late
8. **Compliance Gaps** - Regulatory requirements not met at Day 1
9. **Stranded Costs** - Parent left with overhead when unit leaves
10. **Day 1 Not Ready** - Basic operations fail at close

---

## Key Questions for Document Analysis

When analyzing IT DD documents for carveouts, look for:

1. **Entanglement Indicators**
   - "Shared SAP instance" → Deep ERP entanglement
   - "Corporate Active Directory" → Identity separation needed
   - "Parent data center" → Infrastructure dependency
   - "Corporate network" → Network carveout required
   - "Single email domain" → Email separation needed

2. **TSA Signals**
   - "Transition services" → TSA exists/planned
   - "Service level agreement" → TSA terms defined
   - "Exit milestones" → Separation planning
   - "Monthly fee" / "cost allocation" → TSA pricing
   - "Extension clause" → Flexibility assessment

3. **Day 1 Risks**
   - "Legal entity formation" → Corporate structure
   - "Banking relationships" → Treasury readiness
   - "Standalone capability" → Day 1 viability
   - "Stranded costs" → Parent economics

4. **Data Separation Signals**
   - "Shared master data" → Ownership disputes
   - "Customer records" → Data split complexity
   - "Intercompany" → Transaction cleanup
   - "Historical data" → Archive approach

5. **Staffing Signals**
   - "IT staff transfer" → Knowledge continuity
   - "No dedicated IT" → Must build from scratch
   - "Shared services" → Stranded cost risk
   - "Knowledge transfer" → Documentation needs

---

## TSA Pricing Reference

| Service Category | Typical Monthly Cost | Notes |
|-----------------|---------------------|-------|
| ERP hosting + support | $50K-200K | Depends on complexity |
| Email/collaboration | $5-15 per user | M365-like services |
| Network services | $20K-100K | WAN, internet, security |
| Helpdesk | $50-100 per user | Tier 1-2 support |
| Data center/hosting | $50K-300K | Depends on footprint |
| Security services | $30K-100K | SOC, IAM, compliance |
| Application support | $10K-50K per app | Per major application |

**Total TSA Range:** $200K-$2M+ per month depending on scope

---

*Playbook Version: 1.0*
*Last Updated: January 2026*
