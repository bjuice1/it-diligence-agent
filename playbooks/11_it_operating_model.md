# IT Operating Model Playbook

## Overview

The IT Operating Model defines how IT delivers services to the business - the structure, processes, sourcing, and governance. In M&A, operating model alignment is often underestimated but determines long-term integration success. Technology can be changed; culture and operating models are harder.

**Typical Duration:** 12-24 months (full transformation)
**Cost Range:** $1M-$10M+ (depends on scope of change)
**Risk Level:** High (organizational change is hard)

---

## IT Operating Model Components

```
                        IT OPERATING MODEL FRAMEWORK

    ┌─────────────────────────────────────────────────────────────────────┐
    │                         STRATEGY & GOVERNANCE                        │
    │  • IT strategy alignment with business                              │
    │  • Investment governance (portfolio management)                      │
    │  • Architecture governance                                          │
    │  • Risk and compliance                                              │
    └─────────────────────────────────────────────────────────────────────┘
                                    │
    ┌───────────────────────────────┼───────────────────────────────┐
    │                               │                               │
    ▼                               ▼                               ▼
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│   ORGANIZATION  │       │    PROCESSES    │       │    SOURCING     │
│                 │       │                 │       │                 │
│ • Structure     │       │ • ITSM (ITIL)   │       │ • Insource      │
│ • Roles/skills  │       │ • Project mgmt  │       │ • Outsource     │
│ • Reporting     │       │ • Change mgmt   │       │ • MSP/staff aug │
│ • Locations     │       │ • Agile/DevOps  │       │ • Offshore      │
└─────────────────┘       └─────────────────┘       └─────────────────┘
                                    │
    └───────────────────────────────┼───────────────────────────────┘
                                    │
    ┌─────────────────────────────────────────────────────────────────────┐
    │                         SERVICE DELIVERY                             │
    │  • Infrastructure services      • Application services              │
    │  • End user services            • Security services                 │
    │  • Data services                • Cloud services                    │
    └─────────────────────────────────────────────────────────────────────┘
```

---

## Dependency Map

```
                    ┌─────────────────────────────────────────────────────────┐
                    │              UPSTREAM DEPENDENCIES                       │
                    │  (Must be complete BEFORE operating model integration)   │
                    └─────────────────────────────────────────────────────────┘
                                              │
        ┌─────────────────┬──────────────────┼──────────────────┬─────────────────┐
        ▼                 ▼                  ▼                  ▼                 ▼
┌───────────────┐ ┌───────────────┐ ┌───────────────┐ ┌───────────────┐ ┌───────────────┐
│ Business      │ │  Current      │ │  Integration  │ │  Retention    │ │  Governance   │
│ Strategy      │ │  State        │ │  Philosophy   │ │  Decisions    │ │  Framework    │
│               │ │  Assessment   │ │               │ │               │ │               │
│ - Deal thesis │ │ - Org chart   │ │ - Absorb vs   │ │ - Key staff   │ │ - Decision    │
│ - Synergy     │ │ - Headcount   │ │   best-of-both│ │   identified  │ │   rights      │
│   targets     │ │ - Skills      │ │ - Autonomy vs │ │ - Packages    │ │ - Escalation  │
│ - Timeline    │ │ - Processes   │ │   integration │ │   planned     │ │   paths       │
└───────────────┘ └───────────────┘ └───────────────┘ └───────────────┘ └───────────────┘
                                              │
                    ┌─────────────────────────────────────────────────────────┐
                    │           OPERATING MODEL INTEGRATION                    │
                    │                                                          │
                    │  Design → Announce → Transition → Stabilize → Optimize  │
                    └─────────────────────────────────────────────────────────┘
                                              │
        ┌─────────────────┬──────────────────┼──────────────────┬─────────────────┐
        ▼                 ▼                  ▼                  ▼                 ▼
┌───────────────┐ ┌───────────────┐ ┌───────────────┐ ┌───────────────┐ ┌───────────────┐
│ Technical     │ │  Vendor       │ │  Process      │ │  Culture      │ │  Cost         │
│ Integration   │ │  Consolidation│ │  Standardiz.  │ │  Integration  │ │  Optimization │
│               │ │               │ │               │ │               │ │               │
│ - System      │ │ - Contract    │ │ - Common      │ │ - Ways of     │ │ - Synergy     │
│   consolidation││   alignment   │ │   processes   │ │   working     │ │   realization │
│ - Tool        │ │ - Support     │ │ - Tooling     │ │ - Team        │ │ - Headcount   │
│   standardiz. │ │   model       │ │   alignment   │ │   building    │ │   right-sizing│
└───────────────┘ └───────────────┘ └───────────────┘ └───────────────┘ └───────────────┘
                    │              DOWNSTREAM DEPENDENCIES                     │
                    │  (Enabled after operating model defined)                 │
                    └─────────────────────────────────────────────────────────┘
```

---

## Operating Model Archetypes

### Centralized Model
```
┌─────────────────────────────────────────────────────────────────┐
│                         CORPORATE IT                             │
│                                                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │ Infrastructure│  │ Applications│  │   Security  │             │
│  │   Team       │  │    Team     │  │    Team     │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
│                                                                  │
│                    All IT staff report to CIO                    │
│                    Standard processes company-wide               │
│                    Economies of scale                            │
└─────────────────────────────────────────────────────────────────┘
              │                │                │
              ▼                ▼                ▼
         Business A       Business B       Business C
         (Served by       (Served by       (Served by
          central IT)      central IT)      central IT)

PROS: Efficiency, standardization, cost control
CONS: Less agile, business may feel underserved
BEST FOR: Homogeneous businesses, cost focus
```

### Federated Model
```
┌─────────────────────────────────────────────────────────────────┐
│                      CORPORATE IT (Small)                        │
│            • Strategy  • Architecture  • Security                │
│            • Governance  • Shared infrastructure                 │
└─────────────────────────────────────────────────────────────────┘
              │                │                │
              ▼                ▼                ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│   Business A    │  │   Business B    │  │   Business C    │
│      IT         │  │      IT         │  │      IT         │
│                 │  │                 │  │                 │
│ • App dev       │  │ • App dev       │  │ • App dev       │
│ • Support       │  │ • Support       │  │ • Support       │
│ • Local needs   │  │ • Local needs   │  │ • Local needs   │
└─────────────────┘  └─────────────────┘  └─────────────────┘

PROS: Business-responsive, agile, autonomy
CONS: Duplication, inconsistency, higher cost
BEST FOR: Diverse businesses, different needs
```

### Hybrid Model
```
┌─────────────────────────────────────────────────────────────────┐
│                      SHARED SERVICES                             │
│            • Infrastructure  • Security  • Network               │
│            • Helpdesk  • Procurement                             │
└─────────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              │               │               │
              ▼               ▼               ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│   Business A    │  │   Business B    │  │   Business C    │
│   (Embedded IT) │  │   (Embedded IT) │  │   (Embedded IT) │
│                 │  │                 │  │                 │
│ • Business apps │  │ • Business apps │  │ • Business apps │
│ • Data/analytics│  │ • Data/analytics│  │ • Data/analytics│
│ • Digital       │  │ • Digital       │  │ • Digital       │
└─────────────────┘  └─────────────────┘  └─────────────────┘

PROS: Balance of efficiency and responsiveness
CONS: Coordination complexity, matrix reporting
BEST FOR: Large enterprises, diverse but connected
```

---

## M&A Operating Model Scenarios

### Scenario 1: Buyer Absorbs Target
```
BEFORE                              AFTER
──────                              ─────
Buyer IT: 100 staff                 Buyer IT: 110 staff (+10%)
Target IT: 30 staff                 Target IT: 0 staff

• Target org dissolved
• Target staff either join buyer or exit
• Buyer processes become standard
• Buyer tools become standard
• Integration complexity: HIGH
• Synergy potential: HIGH
```

### Scenario 2: Target Operates Independently
```
BEFORE                              AFTER
──────                              ─────
Buyer IT: 100 staff                 Buyer IT: 100 staff
Target IT: 30 staff                 Target IT: 30 staff (separate)

• Target IT remains intact
• Minimal process changes
• Governance alignment only
• Integration complexity: LOW
• Synergy potential: LOW
```

### Scenario 3: Best-of-Both Integration
```
BEFORE                              AFTER
──────                              ─────
Buyer IT: 100 staff                 Combined IT: 95-105 staff
Target IT: 30 staff                 (select from both)

• New combined org structure
• Best processes from each
• Joint tool rationalization
• Integration complexity: HIGHEST
• Synergy potential: MODERATE
```

---

## DD Document Signals to Detect

### Organizational Structure Signals
| Signal | Implication | Integration Complexity |
|--------|-------------|----------------------|
| "IT reports to CFO" | Cost-center mentality | May resist investment |
| "IT reports to CEO" | Strategic view | Better resourced |
| "Decentralized IT" | Federated model | Consolidation opportunity |
| "Shared services" | Centralized model | Already efficient |
| "Shadow IT" | Governance gaps | Hidden complexity |

### Staffing Signals
| Signal | Implication | Action |
|--------|-------------|--------|
| "Lean IT team" | Under-resourced | Technical debt likely |
| "Heavy contractors" | Flexible but fragile | Knowledge risk |
| "Offshore team" | Cost optimization | Coordination needs |
| "No dedicated security" | Security gaps | Hire or outsource |
| "Key person risk" | Knowledge concentration | Retention critical |

### Process Signals
| Signal | Implication | Effort |
|--------|-------------|--------|
| "ITIL/ITSM implemented" | Process maturity | Lower integration |
| "No change management" | Process gaps | Process build required |
| "Agile/DevOps" | Modern practices | Potential best practice |
| "No project governance" | Delivery risk | Governance needed |
| "Manual processes" | Automation opportunity | Modernization |

### Sourcing Signals
| Signal | Implication | Consideration |
|--------|-------------|---------------|
| "Fully outsourced" | MSP dependent | Contract review |
| "Heavy outsourcing" | Knowledge external | Transition planning |
| "Insourced only" | Internal capability | May be expensive |
| "Same MSP as buyer" | Consolidation easy | Leverage volume |
| "Different MSP" | Contract alignment | Transition needed |

---

## Upstream Dependencies (Prerequisites)

### 1. Business Strategy Clarity
**Must complete before:** Operating model design

| Dependency | Why Required | If Missing |
|------------|--------------|------------|
| Deal thesis understood | Align IT model | Wrong approach |
| Synergy targets defined | Headcount decisions | No direction |
| Integration timeline | Pace of change | Can't plan |
| Autonomy decisions | Independence level | Org confusion |

### 2. Current State Assessment
**Must complete before:** Future state design

| Dependency | Why Required | If Missing |
|------------|--------------|------------|
| Org structure documented | Know what exists | Surprises |
| Headcount by function | Baseline | Can't plan |
| Skills inventory | Capability gaps | Wrong org design |
| Process maturity | Gaps identified | Process issues |

### 3. Key Retention Decisions
**Must complete before:** Org announcement

| Dependency | Why Required | If Missing |
|------------|--------------|------------|
| Critical staff identified | Retention focus | Key person loss |
| Retention packages planned | Stay incentives | Departures |
| Communication plan | Reduce anxiety | Rumor mill |

---

## Downstream Dependencies (Enabled After Operating Model)

### 1. Technical Integration
**Blocked until:** Org structure decided

| Dependency | Why Blocked | Impact of Delay |
|------------|-------------|-----------------|
| System consolidation | Who owns decisions | Stalled projects |
| Tool standardization | Which tool survives | Parallel investment |
| Process integration | Who defines process | Inconsistency |

### 2. Vendor Consolidation
**Blocked until:** Sourcing model decided

| Dependency | Why Blocked | Impact of Delay |
|------------|-------------|-----------------|
| MSP alignment | Who manages | Dual contracts |
| Contract negotiation | Volume leverage | Missed savings |
| Support model | Who to call | Confusion |

### 3. Cost Optimization
**Blocked until:** Org stabilized

| Dependency | Why Blocked | Impact of Delay |
|------------|-------------|-----------------|
| Headcount synergies | Reductions | Continued cost |
| Vendor consolidation | Rationalization | Duplicate spend |
| Tool rationalization | License savings | Over-licensing |

---

## Common Failure Modes

1. **No Clear Decision** - Ambiguity about target model creates paralysis
2. **Integration by Attrition** - Key people leave before knowledge transferred
3. **Culture Clash** - Different ways of working create friction
4. **Synergy Overreach** - Too aggressive headcount cuts harm delivery
5. **Communication Gaps** - Staff learn from rumors, not leadership
6. **Process War** - Fighting over whose process is better
7. **Tool War** - Fighting over whose tools survive
8. **Governance Vacuum** - No clear decision rights
9. **Shadow IT Explosion** - Business routes around unresponsive IT
10. **Retained Knowledge Loss** - Key people leave anyway

---

## M&A Due Diligence Checklist

| Question | Red Flag Answer | Impact |
|----------|-----------------|--------|
| IT org structure? | "Unclear" / "Complex matrix" | Difficult integration |
| IT headcount? | "Don't know exactly" | Hidden costs |
| IT reporting line? | "Multiple" / "Embedded" | Governance complexity |
| Outsourcing level? | "Heavily outsourced" | Knowledge external |
| Key person risks? | "Yes, several" | Retention critical |
| IT processes documented? | "Tribal knowledge" | Process gaps |
| Same MSP as buyer? | No | Contract alignment |
| IT budget? | "Hidden in business units" | True cost unknown |
| Recent IT turnover? | "High" | Morale/retention issue |

---

## Operating Model Transition Timeline

```
Month:  1   2   3   4   5   6   7   8   9  10  11  12
        │   │   │   │   │   │   │   │   │   │   │   │

Assessment  ████│
& Design        │
                │
Announcement    ████│
& Communication     │
                    │
Leadership          ████████│
Transition                  │
                            │
Process                 ████████████│
Integration                         │
                                    │
Tool                            ████████████│
Consolidation                               │
                                            │
Optimization                            ████████████
& Stabilization
```

---

*Playbook Version: 1.0*
*Last Updated: January 2026*
