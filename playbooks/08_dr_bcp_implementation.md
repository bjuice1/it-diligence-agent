# DR/BCP Implementation Playbook

## Overview

Disaster Recovery (DR) and Business Continuity Planning (BCP) gaps are among the most common findings in IT due diligence. Whether the target has no DR, untested DR, or inadequate DR, remediation is typically required post-close. This playbook maps dependencies for DR/BCP programs.

**Typical Duration:** 6-18 months (full implementation)
**Cost Range:** $500K-$5M+ (depends on scope and RTO/RPO requirements)
**Risk Level:** High (business survival at stake)

---

## DR Maturity Assessment

```
                            DR MATURITY LEVELS

    Level 0              Level 1              Level 2              Level 3
    ─────────────────    ─────────────────    ─────────────────    ─────────────────
    NO DR                BASIC DR             TESTED DR            MATURE DR

    • No backup site     • DR site exists     • Annual DR test     • Quarterly tests
    • Tape backup only   • Replication        • Documented         • Automated
    • No RTO/RPO         • RTO >24hr          • RTO 4-24hr         • RTO <4hr
    • No plan            • Basic runbooks     • Playbooks exist    • Orchestration
    • Hope for best      • Manual failover    • Semi-automated     • Push-button

    RISK: Critical       RISK: High           RISK: Medium         RISK: Lower
    COST: $$$$           COST: $$$            COST: $$             COST: $
    (Build from          (Improve/test)       (Optimize)           (Maintain)
     scratch)
```

---

## Dependency Map

```
                    ┌─────────────────────────────────────────────────────────┐
                    │              UPSTREAM DEPENDENCIES                       │
                    │  (Must be complete BEFORE DR implementation)             │
                    └─────────────────────────────────────────────────────────┘
                                              │
        ┌─────────────────┬──────────────────┼──────────────────┬─────────────────┐
        ▼                 ▼                  ▼                  ▼                 ▼
┌───────────────┐ ┌───────────────┐ ┌───────────────┐ ┌───────────────┐ ┌───────────────┐
│ Business      │ │  Asset        │ │  Data         │ │  Network      │ │  Recovery     │
│ Impact        │ │  Inventory    │ │  Classification│ │  Connectivity │ │  Site/Cloud   │
│ Analysis      │ │               │ │               │ │               │ │               │
│               │ │               │ │               │ │               │ │               │
│ - RTO/RPO     │ │ - All systems │ │ - Critical    │ │ - DR network  │ │ - DR location │
│ - Critical    │ │ - Dependencies│ │   data        │ │ - Bandwidth   │ │ - Capacity    │
│   processes   │ │ - Recovery    │ │ - Replication │ │ - Failover    │ │ - Contracts   │
│ - Priorities  │ │   order       │ │   requirements│ │   path        │ │               │
└───────────────┘ └───────────────┘ └───────────────┘ └───────────────┘ └───────────────┘
                                              │
                    ┌─────────────────────────────────────────────────────────┐
                    │               DR/BCP IMPLEMENTATION                      │
                    │                                                          │
                    │  Design → Build → Test → Document → Operate             │
                    └─────────────────────────────────────────────────────────┘
                                              │
        ┌─────────────────┬──────────────────┼──────────────────┬─────────────────┐
        ▼                 ▼                  ▼                  ▼                 ▼
┌───────────────┐ ┌───────────────┐ ┌───────────────┐ ┌───────────────┐ ┌───────────────┐
│ Ransomware    │ │  Compliance   │ │  Insurance    │ │  Cloud        │ │  Operational  │
│ Resilience    │ │  Certification│ │  Validation   │ │  Migration    │ │  Confidence   │
│               │ │               │ │               │ │               │ │               │
│ - Immutable   │ │ - SOC 2       │ │ - Cyber       │ │ - Multi-region│ │ - Tested      │
│   backups     │ │ - ISO 22301   │ │   policy      │ │   deployment  │ │   recovery    │
│ - Air-gapped  │ │ - Industry    │ │ - Coverage    │ │ - Native DR   │ │ - Staff       │
│   copies      │ │   specific    │ │   validation  │ │   services    │ │   trained     │
└───────────────┘ └───────────────┘ └───────────────┘ └───────────────┘ └───────────────┘
                    │              DOWNSTREAM DEPENDENCIES                     │
                    │  (Enabled after DR/BCP implementation)                   │
                    └─────────────────────────────────────────────────────────┘
```

---

## Upstream Dependencies (Prerequisites)

### 1. Business Impact Analysis (BIA)
**Must complete before:** DR design

| Dependency | Why Required | If Missing |
|------------|--------------|------------|
| RTO defined | Know recovery time target | No design target |
| RPO defined | Know data loss tolerance | Wrong backup frequency |
| Critical processes identified | Know what to protect | Wrong priorities |
| Process dependencies mapped | Recovery sequence | Wrong order recovery |
| Business sign-off | Alignment on targets | Rework later |

**BIA Output Requirements:**

| Process/System | RTO | RPO | Priority | Dependencies |
|----------------|-----|-----|----------|--------------|
| Example: ERP | 4 hr | 1 hr | Critical | Database, network, AD |
| Example: Email | 2 hr | 15 min | High | M365, network |
| Example: Website | 1 hr | 24 hr | Medium | Web servers, CDN |

**Complexity Signals:**
- "No BIA exists" → Must complete before DR design
- "RTO not defined" → Business decision required
- "Different RTO by system" → Tiered DR architecture
- "Zero RPO required" → Synchronous replication cost

### 2. Asset Inventory & Dependencies
**Must complete before:** Recovery planning

| Dependency | Why Required | If Missing |
|------------|--------------|------------|
| Complete system inventory | Know what to recover | Systems forgotten |
| Application dependencies | Recovery sequence | Apps fail on recovery |
| Database dependencies | Data consistency | Corrupted recovery |
| External dependencies | Third-party planning | Incomplete recovery |
| Recovery order documented | Sequenced failover | Chaos during DR |

**Dependency Mapping Example:**
```
                    RECOVERY DEPENDENCY CHAIN

    Layer 1: Infrastructure (First)
    ├── Network/DNS
    ├── Active Directory
    └── Core databases

    Layer 2: Platform (Second)
    ├── Application servers
    ├── Middleware
    └── Integration services

    Layer 3: Applications (Third)
    ├── ERP
    ├── CRM
    └── Customer-facing apps

    Layer 4: Ancillary (Last)
    ├── Reporting
    ├── Dev/test
    └── Non-critical systems
```

### 3. Data Classification & Replication
**Must complete before:** Backup/replication design

| Dependency | Why Required | If Missing |
|------------|--------------|------------|
| Data classification | Know criticality | Wrong protection levels |
| Data volumes known | Size replication | Bandwidth issues |
| Change rates understood | Replication frequency | RPO violations |
| Retention requirements | Backup retention | Compliance gaps |
| Data locations mapped | Know what to replicate | Data gaps |

### 4. Network Connectivity to DR Site
**Must complete before:** Replication setup

| Dependency | Why Required | If Missing |
|------------|--------------|------------|
| DR site connectivity | Replication path | No data sync |
| Sufficient bandwidth | Support replication load | RPO violations |
| Failover network path | Users reach DR site | Recovery fails |
| DNS failover strategy | Name resolution | Apps unreachable |

### 5. Recovery Site/Cloud Established
**Must complete before:** Build phase

| Dependency | Why Required | If Missing |
|------------|--------------|------------|
| DR location selected | Know where to recover | No destination |
| Capacity provisioned | Resources available | Recovery fails |
| Contracts in place | Colo, cloud, or owned | No infrastructure |
| Licensing for DR | Software rights | Compliance issues |

---

## Downstream Dependencies (Enabled After DR Implementation)

### 1. Ransomware Resilience
**Blocked until:** Backup architecture implemented

| Dependency | Why Blocked | Impact of Delay |
|------------|-------------|-----------------|
| Immutable backups | Need backup infrastructure | Ransom or data loss |
| Air-gapped copies | Requires backup design | Backups encrypted too |
| Recovery testing | Need DR capability | Unknown if recovery works |
| Incident response | Needs recovery option | Pay ransom or lose data |

### 2. Compliance Certification
**Blocked until:** DR tested and documented

| Dependency | Why Blocked | Impact of Delay |
|------------|-------------|-----------------|
| SOC 2 attestation | DR controls required | Audit findings |
| ISO 22301 (BCM) | Requires tested BCP | Certification blocked |
| Industry compliance | Often requires DR | Regulatory gaps |
| Customer audits | They ask for DR evidence | Customer concerns |

### 3. Cyber Insurance Validation
**Blocked until:** DR controls implemented

| Dependency | Why Blocked | Impact of Delay |
|------------|-------------|-----------------|
| Insurance application | Questions about DR | Higher premiums |
| Coverage validation | Need DR for claims | Claim denial risk |
| Policy renewal | DR often required | Coverage gaps |

### 4. Cloud Migration (Multi-Region)
**Blocked until:** DR strategy defined

| Dependency | Why Blocked | Impact of Delay |
|------------|-------------|-----------------|
| Multi-region deployment | Need DR architecture | Single region risk |
| Cloud-native DR | Requires DR design | Lift-shift only |
| Availability zones | DR strategy drives design | Suboptimal architecture |

---

## DR Architecture Options

### Option 1: Traditional DR Site (Active-Passive)
```
┌─────────────────────┐                    ┌─────────────────────┐
│   PRIMARY SITE      │                    │      DR SITE        │
│                     │                    │    (Passive)        │
│ ┌─────────────────┐ │    Replication     │ ┌─────────────────┐ │
│ │ Production      │ │ ──────────────────►│ │ Standby         │ │
│ │ Workloads       │ │    (Async)         │ │ Workloads       │ │
│ └─────────────────┘ │                    │ └─────────────────┘ │
│                     │                    │                     │
│ Active users        │                    │ Scaled down/off     │
└─────────────────────┘                    └─────────────────────┘

RTO: 4-24 hours (manual failover)
RPO: 15 min - 24 hours (depends on replication)
Cost: $$ (infrastructure at both sites)
```

### Option 2: Cloud-Based DR (DRaaS)
```
┌─────────────────────┐                    ┌─────────────────────┐
│   PRIMARY SITE      │                    │   CLOUD DR          │
│   (On-premises)     │                    │   (AWS/Azure)       │
│                     │                    │                     │
│ ┌─────────────────┐ │    Continuous      │ ┌─────────────────┐ │
│ │ Production      │ │ ──────────────────►│ │ Replicated      │ │
│ │ Workloads       │ │    Replication     │ │ Images/Data     │ │
│ └─────────────────┘ │                    │ └─────────────────┘ │
│                     │                    │                     │
│                     │                    │ Pay for storage     │
│                     │                    │ Compute on failover │
└─────────────────────┘                    └─────────────────────┘

RTO: 2-8 hours (orchestrated failover)
RPO: Minutes to hours
Cost: $ (pay for what you use)
```

### Option 3: Active-Active (High Availability)
```
┌─────────────────────┐                    ┌─────────────────────┐
│   SITE A            │                    │      SITE B         │
│   (Active)          │                    │     (Active)        │
│                     │    Synchronous     │                     │
│ ┌─────────────────┐ │◄──────────────────►│ ┌─────────────────┐ │
│ │ Workloads       │ │    Replication     │ │ Workloads       │ │
│ │ (50% traffic)   │ │                    │ │ (50% traffic)   │ │
│ └─────────────────┘ │                    │ └─────────────────┘ │
│                     │                    │                     │
│ ◄──── Global Load Balancer distributes traffic ────►          │
└─────────────────────┘                    └─────────────────────┘

RTO: Minutes (automatic failover)
RPO: Zero (synchronous)
Cost: $$$$ (full infrastructure at both sites)
```

---

## DD Document Signals to Detect

### DR Gap Signals
| Signal | Implication | Risk Level |
|--------|-------------|------------|
| "No DR" / "DR not documented" | Complete implementation needed | Critical |
| "DR never tested" | Unknown if recovery works | Critical |
| "Tape backup only" | Long RTO, manual recovery | High |
| "Single data center" | No geographic redundancy | High |
| "DR site 10 miles away" | Same disaster zone | Medium |
| "Annual DR test" | Infrequent validation | Medium |
| "RTO/RPO not defined" | No recovery targets | High |

### DR Capability Signals
| Signal | What It Indicates | Complexity |
|--------|-------------------|------------|
| "Hot site" / "warm site" | Some DR capability exists | Lower |
| "Replication" / "mirrored" | Data protection in place | Lower |
| "DRaaS" / "Zerto" / "SRM" | DR tooling deployed | Lower |
| "Quarterly DR test" | Mature testing program | Lower |
| "Automated failover" | Orchestration in place | Lower |

### Backup Signals
| Signal | Implication | Action |
|--------|-------------|--------|
| "Tape backup" | Long recovery time | Modernize |
| "No offsite backup" | Local disaster = total loss | Critical gap |
| "Backup not tested" | May not restore | Validate |
| "Veeam" / "Commvault" / "Rubrik" | Modern backup tooling | Good sign |
| "Cloud backup" | Offsite copy exists | Good sign |

---

## Cost Estimation Signals

| Factor | Impact | Typical Cost |
|--------|--------|--------------|
| RTO requirement | Architecture driver | <4hr = $$$, <1hr = $$$$ |
| RPO requirement | Replication technology | <15min = $$, <1hr = $ |
| Data volume | Storage + bandwidth | $0.02-0.10/GB/month |
| System count | Per-system protection | $500-2K/server/month |
| DR site type | Infrastructure cost | Colo > Cloud > None |
| Testing frequency | Operational cost | $10-50K per test |
| Orchestration | Automation tooling | $50-200K implementation |

**Typical DR Budget Ranges:**

| Scenario | Annual Cost | Implementation |
|----------|-------------|----------------|
| Small (50 servers, 4hr RTO) | $100-300K | $200-500K |
| Medium (200 servers, 2hr RTO) | $300K-1M | $500K-1.5M |
| Large (500+ servers, <1hr RTO) | $1-3M | $1.5-5M |

---

## Common Failure Modes

1. **No BIA** - DR designed without business input; wrong priorities
2. **Untested DR** - Assumed working but fails when needed
3. **Stale runbooks** - Documentation doesn't match reality
4. **Dependency gaps** - Apps recovered in wrong order
5. **Network overlooked** - Systems up but unreachable
6. **DNS forgotten** - Name resolution fails
7. **Licensing issues** - DR systems unlicensed
8. **Key person absence** - Only one person knows DR
9. **Backup corruption** - Backups exist but won't restore
10. **Same disaster zone** - DR site too close to primary

---

## DR Test Planning

### Test Types
| Test Type | Disruption | Confidence | Frequency |
|-----------|------------|------------|-----------|
| Tabletop exercise | None | Low | Quarterly |
| Component test | Low | Medium | Monthly |
| Parallel test | Low | High | Semi-annual |
| Full failover | High | Highest | Annual |

### Minimum Test Checklist
- [ ] Backup restore validation
- [ ] Network failover
- [ ] DNS cutover
- [ ] Application startup sequence
- [ ] Data integrity check
- [ ] User acceptance
- [ ] Failback procedure
- [ ] Time-to-recover measurement

---

## M&A Due Diligence Checklist

| Question | Red Flag Answer | Cost Impact |
|----------|-----------------|-------------|
| Does DR exist? | No | $500K-2M implementation |
| When was DR last tested? | Never / >12 months | Unknown capability |
| What is RTO/RPO? | "Not defined" | BIA required first |
| Where is DR site? | "Same building" | Not real DR |
| How is data replicated? | "Tape shipped weekly" | Long RPO, modernize |
| Who manages DR? | "No one specific" | Process gap |
| Is DR documented? | "Tribal knowledge" | Documentation needed |
| Are backups tested? | "No" / "Rarely" | Critical gap |

---

*Playbook Version: 1.0*
*Last Updated: January 2026*
