# SD-WAN & Network Modernization Playbook

## Overview

SD-WAN (Software-Defined Wide Area Network) has become the standard approach for enterprise network modernization. In M&A scenarios, SD-WAN can accelerate integration by enabling faster site connectivity and simplifying network management. This playbook covers SD-WAN adoption and network modernization dependencies.

**Typical Duration:** 6-12 months (enterprise-wide deployment)
**Cost Range:** $500K-$3M (depends on site count)
**Risk Level:** Medium (business continuity during transition)

---

## Traditional MPLS vs SD-WAN

```
                    TRADITIONAL MPLS                    SD-WAN

    ┌─────────┐      ┌─────────┐      ┌─────────┐    ┌─────────┐
    │ Site A  │      │ Site B  │      │ Site A  │    │ Site B  │
    └────┬────┘      └────┬────┘      └────┬────┘    └────┬────┘
         │                │                │              │
         │    Private     │                │   Internet   │
         └───────┬────────┘                └──────┬───────┘
                 │                                │
         ┌───────▼────────┐              ┌───────▼────────┐
         │   MPLS Cloud   │              │   SD-WAN       │
         │   (Carrier)    │              │  Controller    │
         └───────┬────────┘              └───────┬────────┘
                 │                                │
    ┌────────────┴────────────┐      ┌───────────┴────────────┐
    │                         │      │                        │
    ▼                         ▼      ▼                        ▼
┌─────────┐              ┌─────────┐ ┌─────────┐         ┌─────────┐
│  HQ     │              │   DC    │ │   HQ    │         │  Cloud  │
└─────────┘              └─────────┘ └─────────┘         └─────────┘

MPLS Characteristics:              SD-WAN Characteristics:
• Predictable performance          • Flexible transport (internet, MPLS, LTE)
• Expensive ($500-2K/site/mo)      • Lower cost (internet is cheap)
• Long lead times (45-90 days)     • Fast deployment (14-30 days)
• Carrier-dependent                • Application-aware routing
• No direct cloud access           • Direct cloud connectivity
• Complex changes                  • Centralized management
```

---

## Dependency Map

```
                    ┌─────────────────────────────────────────────────────────┐
                    │              UPSTREAM DEPENDENCIES                       │
                    │  (Must be complete BEFORE SD-WAN deployment)             │
                    └─────────────────────────────────────────────────────────┘
                                              │
        ┌─────────────────┬──────────────────┼──────────────────┬─────────────────┐
        ▼                 ▼                  ▼                  ▼                 ▼
┌───────────────┐ ┌───────────────┐ ┌───────────────┐ ┌───────────────┐ ┌───────────────┐
│ Internet      │ │  Security     │ │  Application  │ │  Site         │ │  SD-WAN       │
│ Circuits      │ │  Architecture │ │  Requirements │ │  Assessment   │ │  Platform     │
│               │ │               │ │               │ │               │ │  Selection    │
│ - Primary     │ │ - Firewall    │ │ - Bandwidth   │ │ - Current     │ │               │
│ - Backup      │ │ - SASE/SSE    │ │ - Latency     │ │   connectivity│ │ - Vendor      │
│ - Quality     │ │ - Zero trust  │ │ - QoS needs   │ │ - Power/space │ │ - Features    │
└───────────────┘ └───────────────┘ └───────────────┘ └───────────────┘ └───────────────┘
                                              │
                    ┌─────────────────────────────────────────────────────────┐
                    │              SD-WAN DEPLOYMENT                            │
                    │                                                          │
                    │  Pilot → Deploy Waves → Migrate Traffic → Optimize      │
                    └─────────────────────────────────────────────────────────┘
                                              │
        ┌─────────────────┬──────────────────┼──────────────────┬─────────────────┐
        ▼                 ▼                  ▼                  ▼                 ▼
┌───────────────┐ ┌───────────────┐ ┌───────────────┐ ┌───────────────┐ ┌───────────────┐
│ MPLS          │ │  Cloud        │ │  M&A Site     │ │  Security     │ │  Operational  │
│ Termination   │ │  Connectivity │ │  Integration  │ │  Consolidation│ │  Efficiency   │
│               │ │               │ │               │ │               │ │               │
│ - Contract    │ │ - Direct to   │ │ - Fast site   │ │ - Unified     │ │ - Single pane │
│   exit        │ │   cloud       │ │   onboarding  │ │   security    │ │ - Automation  │
│ - Cost        │ │ - Performance │ │ - Template    │ │ - SASE        │ │ - Analytics   │
│   savings     │ │   improvement │ │   deployment  │ │   integration │ │               │
└───────────────┘ └───────────────┘ └───────────────┘ └───────────────┘ └───────────────┘
                    │              DOWNSTREAM DEPENDENCIES                     │
                    │  (Enabled after SD-WAN deployment)                       │
                    └─────────────────────────────────────────────────────────┘
```

---

## Upstream Dependencies (Prerequisites)

### 1. Internet Circuit Readiness
**Must complete before:** SD-WAN appliance deployment

| Dependency | Why Required | If Missing |
|------------|--------------|------------|
| Primary internet circuit | SD-WAN transport | No connectivity |
| Backup circuit (recommended) | Redundancy | Single point of failure |
| Sufficient bandwidth | Application performance | Degraded experience |
| Low latency | Real-time applications | Voice/video issues |

**Circuit Lead Times:**
| Circuit Type | Lead Time | Notes |
|--------------|-----------|-------|
| Business internet (existing provider) | 7-14 days | Fastest |
| New provider | 14-30 days | Depends on area |
| Fiber (new build) | 45-90 days | If fiber not available |
| LTE/5G backup | 1-7 days | Ships with device |

### 2. Security Architecture Decision
**Must complete before:** SD-WAN design

| Dependency | Why Required | If Missing |
|------------|--------------|------------|
| Firewall strategy | Security inspection | Security gaps |
| SASE/SSE decision | Cloud security | Multiple tools |
| Zero trust alignment | Access policy | Inconsistent security |
| Compliance requirements | Regulatory needs | Compliance gaps |

**Security Models:**
```
OPTION 1: SD-WAN + On-prem Firewall    OPTION 2: SD-WAN + SASE (Cloud Security)
─────────────────────────────          ─────────────────────────────────────────

Site ──► SD-WAN ──► Firewall ──► Apps  Site ──► SD-WAN ──► SASE Cloud ──► Apps

• Traditional approach                 • Modern approach
• Keep existing firewalls             • Retire branch firewalls
• Complexity remains                  • Simplified architecture
• Higher cost                         • Security as a service
```

### 3. Application Requirements
**Must complete before:** QoS configuration

| Dependency | Why Required | If Missing |
|------------|--------------|------------|
| Bandwidth by application | Right-size circuits | Over/under provisioned |
| Latency requirements | Circuit selection | Poor voice/video |
| QoS classification | Traffic prioritization | Business apps degraded |
| Cloud application inventory | Direct access design | Inefficient routing |

### 4. Site Assessment
**Must complete before:** Hardware deployment

| Dependency | Why Required | If Missing |
|------------|--------------|------------|
| Current connectivity inventory | Migration planning | Surprises |
| Power/space/cooling | Appliance installation | Blocked install |
| On-site support availability | Installation logistics | Deployment delays |
| Site criticality | Prioritization | Wrong deployment order |

### 5. SD-WAN Platform Selection
**Must complete before:** Procurement

| Dependency | Why Required | If Missing |
|------------|--------------|------------|
| Vendor selected | Procurement | Project blocked |
| Features validated | Requirements met | Gaps discovered |
| Integration requirements | Security tools | Incompatibility |
| Support model | Operations | No support plan |

**Major SD-WAN Vendors:**
| Vendor | Strengths | Considerations |
|--------|-----------|----------------|
| Cisco (Viptela/Meraki) | Enterprise integration | Higher cost |
| VMware (VeloCloud) | Multi-cloud | VMware ecosystem |
| Palo Alto (Prisma SD-WAN) | Security integration | Security-first |
| Fortinet | Integrated security | Mid-market focus |
| Zscaler | SASE/zero trust | Cloud-first |

---

## Downstream Dependencies (Enabled After SD-WAN)

### 1. MPLS Contract Termination
**Blocked until:** SD-WAN carrying production traffic

| Dependency | Why Blocked | Impact of Delay |
|------------|-------------|-----------------|
| MPLS circuit cancellation | Sites still dependent | Continued cost |
| Carrier contract exit | Traffic still on MPLS | Contract penalties |
| WAN cost savings | Can't terminate | Savings delayed |

**Typical Savings:** 30-50% reduction in WAN costs

### 2. Cloud Direct Connectivity
**Blocked until:** SD-WAN deployed at sites

| Dependency | Why Blocked | Impact of Delay |
|------------|-------------|-----------------|
| Direct to AWS/Azure | No SD-WAN path | Hair-pinning through DC |
| SaaS performance | Routing through DC | Poor M365/Salesforce |
| Branch-to-cloud | No local breakout | Latency |

### 3. M&A Site Integration
**Blocked until:** SD-WAN standardized

| Dependency | Why Blocked | Impact of Delay |
|------------|-------------|-----------------|
| Fast site onboarding | No standard approach | Slow integration |
| Acquired site connectivity | Different WAN | Long provisioning |
| Network standardization | Multiple architectures | Ongoing complexity |

**M&A Integration Benefit:**
```
WITHOUT SD-WAN:                        WITH SD-WAN:
─────────────────                      ─────────────
New site integration: 45-90 days       New site integration: 7-14 days
• Order MPLS circuit (45-90 days)      • Order internet (7-14 days)
• Configure carrier routing            • Ship SD-WAN appliance
• Extend firewall policies             • Zero-touch provisioning
• Manual configuration                 • Template-based config
```

### 4. Security Consolidation
**Blocked until:** SD-WAN + SASE integrated

| Dependency | Why Blocked | Impact of Delay |
|------------|-------------|-----------------|
| Branch firewall retirement | Security still on branch | Continued cost |
| Unified security policy | Multiple platforms | Policy sprawl |
| SASE adoption | WAN not ready | Dual security |

---

## DD Document Signals to Detect

### Current WAN Signals
| Signal | Implication | SD-WAN Opportunity |
|--------|-------------|-------------------|
| "MPLS only" | Traditional WAN | Cost savings potential |
| "Single carrier" | Concentration risk | Multi-transport option |
| "High WAN costs" | Expensive MPLS | Significant savings |
| "Long provisioning times" | MPLS lead times | Agility improvement |
| "No direct cloud access" | Hair-pinning traffic | Performance improvement |

### SD-WAN Readiness Signals
| Signal | Implication | Complexity |
|--------|-------------|------------|
| "SD-WAN deployed" | Already modernized | Integration decision |
| "SD-WAN pilot" | In progress | Accelerate or align |
| "Internet at sites" | Ready for SD-WAN | Lower complexity |
| "MPLS contract expiring" | Natural transition point | Timing opportunity |
| "Same SD-WAN as buyer" | Consolidation easy | Lower |
| "Different SD-WAN vendors" | Platform decision | Medium |

### Site Connectivity Signals
| Signal | Implication | Action |
|--------|-------------|--------|
| "Remote/rural sites" | Limited internet options | LTE/5G backup |
| "Manufacturing sites" | OT/IT considerations | QoS critical |
| "Retail locations" | Many small sites | Template deployment |
| "International sites" | Regional considerations | Multi-region design |

---

## Cost Estimation

### SD-WAN Cost Components
| Component | Typical Cost | Notes |
|-----------|--------------|-------|
| SD-WAN appliance | $500-5K per site | Depends on throughput |
| SD-WAN license | $100-500/site/month | Subscription model |
| Internet circuits | $200-2K/site/month | Depends on bandwidth |
| Implementation services | $500-2K per site | Initial deployment |
| SASE (if applicable) | $5-15/user/month | Security-as-service |

### ROI Comparison
```
BEFORE (MPLS)                          AFTER (SD-WAN + Internet)
──────────────                         ─────────────────────────
50 sites @ $1,500/mo MPLS = $75K/mo   50 sites @ $500/mo internet = $25K/mo
                                       50 sites @ $200/mo SD-WAN = $10K/mo
Total: $75,000/month                   Total: $35,000/month

Savings: $40,000/month = $480K/year
Typical payback: 12-18 months
```

---

## Common Failure Modes

1. **Internet Quality Issues** - Cheap circuits = poor performance
2. **No Redundancy** - Single internet = site down on outage
3. **Security Gaps** - SD-WAN without firewall integration
4. **QoS Misconfiguration** - Voice/video quality issues
5. **Big Bang Deployment** - Too many sites at once
6. **Change Management Gap** - Users not prepared for changes
7. **MPLS Terminated Early** - SD-WAN not stable yet
8. **Vendor Lock-in** - Proprietary features trap
9. **Underestimated Bandwidth** - Applications need more
10. **OT/IT Conflict** - Manufacturing sites have special needs

---

## Deployment Approach

### Recommended Wave Strategy
```
Wave 0: Proof of Concept (2-4 weeks)
├── 2-3 non-critical sites
├── Validate platform
├── Test failover
└── Baseline performance

Wave 1: Pilot (4-6 weeks)
├── 5-10 sites including 1 critical
├── Production traffic
├── Monitoring established
└── Support processes tested

Wave 2-N: Production Rollout (2-4 sites/week)
├── Template-based deployment
├── Zero-touch where possible
├── Parallel MPLS during stabilization
└── MPLS termination after validation

Final: MPLS Termination
├── Site-by-site after SD-WAN stable
├── 30-day parallel run minimum
└── Carrier contract exit
```

---

## M&A Due Diligence Checklist

| Question | Red Flag Answer | Cost Impact |
|----------|-----------------|-------------|
| Current WAN technology? | "MPLS only" | Modernization opportunity |
| WAN monthly cost? | >$1K/site | Savings potential |
| SD-WAN deployed? | Different vendor than buyer | Platform decision |
| MPLS contract expiry? | 2+ years remaining | Exit penalties |
| Internet available at sites? | "No" / "Poor quality" | Circuit upgrades |
| Site count? | >100 | Extended deployment |
| International sites? | Yes | Multi-region complexity |
| Real-time applications? | Voice/video | QoS critical |

---

*Playbook Version: 1.0*
*Last Updated: January 2026*
