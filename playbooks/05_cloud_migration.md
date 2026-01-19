# Cloud Migration Playbook (AWS / Azure / GCP)

## Overview

Cloud migration is foundational to IT modernization and often a key integration requirement in M&A. Understanding upstream and downstream dependencies is critical for sequencing workloads and avoiding business disruption.

**Typical Duration:** 12-36 months (enterprise-wide)
**Cost Range:** $1M-$20M+ (depends on scope)
**Risk Level:** High (business continuity, data integrity)

---

## Migration Strategy Decision Tree

```
                        ┌────────────────────────┐
                        │ What are you migrating? │
                        └───────────┬────────────┘
                                    │
        ┌───────────────────────────┼───────────────────────────┐
        │                           │                           │
        ▼                           ▼                           ▼
┌───────────────┐           ┌───────────────┐           ┌───────────────┐
│ Applications  │           │ Infrastructure│           │ Data/Storage  │
│               │           │               │           │               │
│ (workloads)   │           │ (VMs, servers)│           │ (files, DBs)  │
└───────┬───────┘           └───────┬───────┘           └───────┬───────┘
        │                           │                           │
        ▼                           ▼                           ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        THE 7 R's OF MIGRATION                            │
├─────────────┬─────────────┬─────────────┬─────────────┬─────────────────┤
│  REHOST     │  REPLATFORM │  REFACTOR   │  REPURCHASE │  RETAIN         │
│  (Lift &    │  (Lift &    │  (Re-       │  (Replace   │  (Keep          │
│   Shift)    │   Optimize) │   architect)│   with SaaS)│   on-prem)      │
├─────────────┼─────────────┼─────────────┼─────────────┼─────────────────┤
│ • Move as-is│ • Minor     │ • Cloud-    │ • Buy vs    │ • Not suitable  │
│ • Fastest   │   changes   │   native    │   build     │ • Compliance    │
│ • No code   │ • Managed   │ • Rewrite   │ • Retire    │ • Latency       │
│   change    │   services  │ • Containers│   legacy    │ • Cost          │
├─────────────┼─────────────┼─────────────┼─────────────┼─────────────────┤
│ Risk: Low   │ Risk: Med   │ Risk: High  │ Risk: Med   │ Risk: Ongoing   │
│ Benefit: Low│ Benefit: Med│ Benefit:High│ Benefit: Med│ Benefit: None   │
└─────────────┴─────────────┴─────────────┴─────────────┴─────────────────┘
                                    +
                    ┌───────────────┴───────────────┐
                    │  RETIRE       │  RELOCATE     │
                    │  (Sunset)     │  (Move DC)    │
                    └───────────────┴───────────────┘
```

---

## Dependency Map

```
                    ┌─────────────────────────────────────────────────────────┐
                    │              UPSTREAM DEPENDENCIES                       │
                    │  (Must be complete BEFORE cloud migration)               │
                    └─────────────────────────────────────────────────────────┘
                                              │
        ┌─────────────────┬──────────────────┼──────────────────┬─────────────────┐
        ▼                 ▼                  ▼                  ▼                 ▼
┌───────────────┐ ┌───────────────┐ ┌───────────────┐ ┌───────────────┐ ┌───────────────┐
│ Network       │ │  Identity     │ │  Application  │ │  Security     │ │  Data         │
│ Foundation    │ │  Foundation   │ │  Discovery    │ │  Framework    │ │  Assessment   │
│               │ │               │ │               │ │               │ │               │
│ - Connectivity│ │ - Cloud IAM   │ │ - Inventory   │ │ - Cloud sec   │ │ - Data class  │
│ - DNS         │ │ - Federation  │ │ - Dependencies│ │ - Compliance  │ │ - Privacy     │
│ - Routing     │ │ - SSO         │ │ - Compatibility│ - Logging     │ │ - Residency   │
└───────────────┘ └───────────────┘ └───────────────┘ └───────────────┘ └───────────────┘
                                              │
                    ┌─────────────────────────────────────────────────────────┐
                    │                  CLOUD MIGRATION                         │
                    │                                                          │
                    │  Assess → Plan → Migrate (waves) → Optimize → Govern    │
                    └─────────────────────────────────────────────────────────┘
                                              │
        ┌─────────────────┬──────────────────┼──────────────────┬─────────────────┐
        ▼                 ▼                  ▼                  ▼                 ▼
┌───────────────┐ ┌───────────────┐ ┌───────────────┐ ┌───────────────┐ ┌───────────────┐
│ Data Center   │ │  Application  │ │  Cost         │ │  Operations   │ │  DR/BCP       │
│ Decommission  │ │  Modernization│ │  Optimization │ │  Model        │ │  Update       │
│               │ │               │ │               │ │               │ │               │
│ - Contract end│ │ - Containers  │ │ - Reserved    │ │ - Cloud ops   │ │ - New DR      │
│ - Hardware    │ │ - Serverless  │ │   instances   │ │ - Monitoring  │ │   strategy    │
│ - Lease exit  │ │ - Microservices│ - Right-sizing│ │ - Automation  │ │ - Multi-region│
└───────────────┘ └───────────────┘ └───────────────┘ └───────────────┘ └───────────────┘
                    │              DOWNSTREAM DEPENDENCIES                     │
                    │  (Enabled/required after cloud migration)                │
                    └─────────────────────────────────────────────────────────┘
```

---

## Upstream Dependencies (Prerequisites)

### 1. Network Foundation
**Must complete before:** First workload migration

| Dependency | Why Required | Blocking Risk |
|------------|--------------|---------------|
| Cloud connectivity (ExpressRoute/Direct Connect) | Private network to cloud | Data over internet |
| DNS strategy | Name resolution | Service discovery fails |
| IP address planning | Avoid conflicts | Routing issues |
| Firewall rules | Allow cloud traffic | Blocked workloads |
| Hybrid network architecture | Cloud + on-prem coexistence | Connectivity gaps |

**Complexity Signals:**
- "No ExpressRoute/Direct Connect" → Public internet dependency
- "Overlapping IP ranges" → Re-addressing required
- "Legacy DNS (WINS)" → Modernization needed
- "Strict firewall rules" → Extensive change requests
- "Multiple data centers" → Complex routing

**Dependency Chain:**
```
Physical connectivity → VPN/ExpressRoute → DNS → Firewall rules → Workload migration
```

### 2. Identity Foundation
**Must complete before:** Any application migration

| Dependency | Why Required | Blocking Risk |
|------------|--------------|---------------|
| Cloud identity platform | Authentication | No access |
| Federation/SSO configured | Single sign-on | User friction |
| Service principals/accounts | Automation | Manual operations |
| RBAC model designed | Authorization | Security gaps |
| Privileged access management | Admin access | Security risk |

**Complexity Signals:**
- "No Azure AD / AWS IAM Identity Center" → Setup required
- "Legacy LDAP authentication" → Modernization needed
- "No service principal governance" → Security risk
- "Shared admin accounts" → PAM implementation
- "Multiple identity sources" → Federation complexity

**Dependency Chain:**
```
Identity platform → Federation → RBAC design → Service principals → Workload migration
```

### 3. Application Discovery & Dependency Mapping
**Must complete before:** Migration wave planning

| Dependency | Why Required | Blocking Risk |
|------------|--------------|---------------|
| Complete application inventory | Know what exists | Missing workloads |
| Dependency mapping | Understand relationships | Migration sequence wrong |
| Performance baselines | Success criteria | Can't validate |
| Licensing assessment | Cloud licensing rights | Compliance risk |
| Compatibility analysis | Cloud readiness | Migration failures |

**Complexity Signals:**
- "No CMDB" → Extended discovery
- "Unknown dependencies" → Discovery tools needed
- "Homegrown applications" → Compatibility uncertainty
- "Licensed per-socket" → BYOL vs cloud licensing
- "32-bit applications" → May not migrate

**Application Dependency Categories:**
```
┌─────────────────────────────────────────────────────────────────┐
│                    APPLICATION DEPENDENCIES                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  UPSTREAM DEPENDENCIES        DOWNSTREAM DEPENDENCIES           │
│  (What this app needs)        (What needs this app)             │
│                                                                  │
│  ┌─────────────────┐          ┌─────────────────┐               │
│  │ • Database      │          │ • Reporting     │               │
│  │ • File share    │          │ • Integration   │               │
│  │ • Authentication│          │ • User apps     │               │
│  │ • API services  │          │ • Batch jobs    │               │
│  │ • Middleware    │          │ • Downstream    │               │
│  │ • Batch jobs    │          │   systems       │               │
│  └─────────────────┘          └─────────────────┘               │
│                                                                  │
│  MUST MIGRATE FIRST           CAN'T MIGRATE UNTIL THIS DONE     │
└─────────────────────────────────────────────────────────────────┘
```

### 4. Security Framework
**Must complete before:** Any production workload

| Dependency | Why Required | Blocking Risk |
|------------|--------------|---------------|
| Cloud security architecture | Secure by design | Vulnerabilities |
| Compliance controls mapped | Regulatory requirements | Audit failures |
| Logging/monitoring strategy | Visibility | Security blindness |
| Encryption standards | Data protection | Data exposure |
| Incident response for cloud | Operational security | Breach response |

**Complexity Signals:**
- "No cloud security team" → Skills gap
- "Compliance requirements (SOX, HIPAA, PCI)" → Control mapping
- "No SIEM integration" → Visibility gap
- "On-prem security tools only" → Cloud tooling needed
- "Air-gapped requirements" → Special architecture

### 5. Data Assessment
**Must complete before:** Data-heavy workload migration

| Dependency | Why Required | Blocking Risk |
|------------|--------------|---------------|
| Data classification | Know what's sensitive | Compliance risk |
| Data residency requirements | Where data can live | Regulatory violation |
| Data migration sizing | Transfer planning | Timeline impact |
| Backup/recovery requirements | Protection | Data loss |
| Data sovereignty | Legal requirements | Blocked regions |

**Complexity Signals:**
- "No data classification" → Discovery required
- "100+ TB to migrate" → Extended timeline, special transfer
- "GDPR/data residency" → Region constraints
- "Real-time data requirements" → Sync complexity
- "Multiple database platforms" → Migration tooling

---

## Migration Wave Planning

### Wave Sequencing Based on Dependencies

```
                            MIGRATION WAVE SEQUENCE

Wave 0: Foundation (No user workloads)
├── Network connectivity
├── Identity foundation
├── Security controls
├── Monitoring/logging
└── Landing zone setup

Wave 1: Low-Risk, Low-Dependency
├── Dev/test environments
├── Static websites
├── Standalone applications
└── File servers (read-only)

Wave 2: Moderate Complexity
├── Databases (non-critical)
├── Internal applications
├── Middleware platforms
└── Batch processing

Wave 3: Business Critical
├── Production databases
├── Customer-facing apps
├── ERP integrations
└── Core business systems

Wave 4: Complex/Sensitive
├── Legacy applications
├── High-compliance workloads
├── Real-time systems
└── Final on-prem exit
```

### Dependency-Based Sequencing Example

```
                    Example: E-commerce Platform Migration

┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  WAVE 1: Database Layer           WAVE 2: Application Layer                │
│  (Must migrate first)             (Depends on database)                    │
│                                                                             │
│  ┌──────────────┐                 ┌──────────────┐                         │
│  │ Product DB   │◄────────────────│ Product      │                         │
│  │              │                 │ Service      │                         │
│  └──────────────┘                 └──────────────┘                         │
│                                          │                                  │
│  ┌──────────────┐                        │                                  │
│  │ Customer DB  │◄────────────────┬──────┘                                  │
│  │              │                 │                                         │
│  └──────────────┘                 │      WAVE 3: Frontend                   │
│                                   │      (Depends on services)              │
│  ┌──────────────┐                 │                                         │
│  │ Order DB     │◄───────┐        │      ┌──────────────┐                   │
│  │              │        │        │      │ Web Frontend │                   │
│  └──────────────┘        │        └─────►│              │                   │
│                          │               └──────────────┘                   │
│                          │                      │                           │
│                   ┌──────┴──────┐               │                           │
│                   │ Order       │◄──────────────┘                           │
│                   │ Service     │                                           │
│                   └─────────────┘                                           │
│                                                                             │
│  Sequence: DB → Services → Frontend                                         │
│  Reason: Frontend depends on services, services depend on databases        │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Downstream Dependencies (Enabled After Migration)

### 1. Data Center Decommissioning
**Blocked until:** All workloads migrated from DC

| Dependency | Why Blocked | Impact of Delay |
|------------|-------------|-----------------|
| Colocation contract exit | Workloads still hosted | Continued cost |
| Hardware disposal | Systems still in use | Asset depreciation |
| Network circuit termination | Traffic still flowing | WAN costs |
| Lease termination | Space occupied | Real estate cost |

**Typical Timeline:** 3-12 months post-final migration

### 2. Application Modernization
**Blocked until:** Workloads in cloud (rehost complete)

| Dependency | Why Blocked | Impact of Delay |
|------------|-------------|-----------------|
| Container adoption | Requires cloud foundation | Limited agility |
| Serverless migration | Cloud platform needed | Operational overhead |
| Microservices refactoring | Cloud-native foundation | Monolith maintenance |
| Managed services adoption | In-cloud first | Self-managed DBs |

**Typical Timeline:** 6-18 months post-rehost

### 3. Cost Optimization
**Blocked until:** Workloads running and baselined in cloud

| Dependency | Why Blocked | Impact of Delay |
|------------|-------------|-----------------|
| Reserved instance purchase | Need usage patterns | Paying on-demand |
| Right-sizing | Need performance data | Over-provisioned |
| Spot/preemptible instances | Need architecture changes | Higher costs |
| Storage tiering | Need access patterns | Hot storage costs |

**Typical Timeline:** 3-6 months post-migration per workload

### 4. Operations Model Transformation
**Blocked until:** Sufficient workloads in cloud

| Dependency | Why Blocked | Impact of Delay |
|------------|-------------|-----------------|
| Cloud operations team | Need workloads to operate | Skill gaps |
| Infrastructure as Code | Need cloud resources | Manual provisioning |
| GitOps/DevOps adoption | Need cloud pipelines | Slow deployments |
| SRE practices | Need cloud telemetry | Reactive operations |

**Typical Timeline:** Begins during migration, matures post-migration

### 5. DR/BCP Modernization
**Blocked until:** Primary workloads migrated

| Dependency | Why Blocked | Impact of Delay |
|------------|-------------|-----------------|
| Multi-region DR | Primary must be migrated | On-prem DR still |
| Cloud-native backup | Workloads must exist | Legacy backup |
| Cross-region replication | Data in cloud | DR gap |
| DR testing automation | Cloud DR architecture | Manual testing |

**Typical Timeline:** 3-6 months post-primary migration

---

## Cost Estimation Signals

| Factor | Impact | Multiplier |
|--------|--------|------------|
| Number of VMs | Migration effort | Base metric |
| Data volume | Transfer time | 1.0x (<10TB), 1.5x (10-100TB), 2.0x (>100TB) |
| Application count | Complexity | +$20-100K per app |
| Legacy applications | Compatibility work | 1.3x-2.0x |
| Compliance requirements | Control mapping | 1.2x-1.5x |
| 24x7 availability requirement | DR complexity | 1.3x-1.5x |
| Multi-cloud | Operational complexity | 1.5x-2.0x |
| Skills gap | Training/hiring | +$200K-500K |
| ExpressRoute/Direct Connect | Network foundation | +$50K-200K |
| Timeline compression | Premium | 1.3x-2.0x |

---

## M&A Due Diligence Checklist

### Pre-Deal Assessment

| Question | Red Flag Answer | Cost Impact |
|----------|-----------------|-------------|
| Current cloud footprint? | None | Ground-up cloud build |
| Cloud provider preference? | Different from buyer | Multi-cloud complexity |
| Cloud-ready applications? | Few / none | Modernization required |
| Data center lease expiry? | Soon | Timeline pressure |
| Compliance in cloud? | Not achieved | Control implementation |
| Cloud skills on staff? | None | Training / hiring |
| Network connectivity? | No ExpressRoute | Foundation work |
| Application documentation? | Poor | Extended discovery |
| Data volume? | 100+ TB | Migration complexity |
| Real-time requirements? | Yes, many | Sync complexity |

### Integration Considerations

| Scenario | Complexity | Recommendation |
|----------|------------|----------------|
| Both in same cloud | Lower | Consolidate accounts |
| Different cloud providers | High | Pick target, migrate |
| Target cloud-native, buyer on-prem | Medium | Leverage target expertise |
| Both on-prem | High | Joint cloud strategy |
| Target has cloud debt (lift-shift) | Medium | Optimization before integration |

---

## Common Failure Modes

1. **Network Not Ready** - Workloads migrated without ExpressRoute
2. **Dependencies Not Mapped** - Apps fail because DB not migrated
3. **Licensing Surprise** - BYOL not allowed, unexpected costs
4. **Performance Degradation** - Latency not considered
5. **Security Gaps** - Controls not replicated in cloud
6. **Cost Overruns** - On-demand pricing, no optimization
7. **Skills Gap** - Team can't operate cloud workloads
8. **Compliance Failure** - Controls not implemented before audit
9. **Big Bang Failure** - Too much migrated at once
10. **Stranded Costs** - On-prem not decommissioned

---

## Key Questions for Document Analysis

When analyzing IT DD documents, look for these cloud-related signals:

1. **Current State Indicators**
   - "On-premises data center" → Migration candidate
   - "AWS/Azure/GCP" → Existing cloud footprint
   - "Colocation" → DC exit opportunity
   - "ExpressRoute/Direct Connect" → Cloud connectivity exists

2. **Migration Readiness**
   - "Cloud strategy" → Planning done (maybe)
   - "Virtualization (VMware, Hyper-V)" → Rehost candidate
   - "Containerized" → Cloud-ready
   - "Mainframe" / "AS/400" → Complex migration

3. **Dependency Signals**
   - "Application inventory" → Discovery done
   - "CMDB" → Dependency mapping possible
   - "Custom applications" → Compatibility analysis needed
   - "Integration points" → Dependency complexity

4. **Cost Signals**
   - "Data center lease expiry" → Timeline driver
   - "Hardware refresh needed" → Migration vs refresh
   - "License renewals" → BYOL opportunity
   - "Colocation fees" → Exit savings

---

*Playbook Version: 1.0*
*Last Updated: January 2026*
