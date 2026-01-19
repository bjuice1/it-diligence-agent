# Active Directory Consolidation Playbook

## Overview

Active Directory is the foundational identity layer for most enterprises. In M&A scenarios, AD consolidation is typically the first major integration milestone because nearly every other system depends on it. Get this wrong, and everything downstream fails.

**Typical Duration:** 6-18 months (varies by complexity)
**Cost Range:** $200K-$2M+ (depends on user count, forest complexity)
**Risk Level:** Critical (business-stopping if failed)

---

## Dependency Map

```
                    ┌─────────────────────────────────────────────────────────┐
                    │              UPSTREAM DEPENDENCIES                       │
                    │  (Must be complete/assessed BEFORE consolidation)        │
                    └─────────────────────────────────────────────────────────┘
                                              │
        ┌─────────────────┬──────────────────┼──────────────────┬─────────────────┐
        ▼                 ▼                  ▼                  ▼                 ▼
┌───────────────┐ ┌───────────────┐ ┌───────────────┐ ┌───────────────┐ ┌───────────────┐
│ Network       │ │  AD Health    │ │  Application  │ │  Security     │ │  Governance   │
│ Connectivity  │ │  Assessment   │ │  Inventory    │ │  Posture      │ │  Decisions    │
│               │ │               │ │               │ │               │ │               │
│ - Site-to-   │ │ - Replication │ │ - LDAP-bound  │ │ - Admin audit │ │ - Target      │
│   site VPN   │ │ - DC health   │ │ - Kerberos    │ │ - GPO review  │ │   architecture│
│ - Latency    │ │ - Schema      │ │ - Service     │ │ - Privileged  │ │ - Naming      │
│ - DNS        │ │ - FSMO roles  │ │   accounts    │ │   accounts    │ │   convention  │
└───────────────┘ └───────────────┘ └───────────────┘ └───────────────┘ └───────────────┘
                                              │
                    ┌─────────────────────────────────────────────────────────┐
                    │           ACTIVE DIRECTORY CONSOLIDATION                 │
                    │                                                          │
                    │  Trust → Pilot → User Migration → App Cutover → Cleanup │
                    └─────────────────────────────────────────────────────────┘
                                              │
        ┌─────────────────┬──────────────────┼──────────────────┬─────────────────┐
        ▼                 ▼                  ▼                  ▼                 ▼
┌───────────────┐ ┌───────────────┐ ┌───────────────┐ ┌───────────────┐ ┌───────────────┐
│ Application   │ │  M365/Azure   │ │  Legacy DC    │ │  Group Policy │ │  Security     │
│ Re-pointing   │ │  AD Changes   │ │  Decommission │ │  Consolidation│ │  Hardening    │
│               │ │               │ │               │ │               │ │               │
│ - LDAP update │ │ - AAD Connect │ │ - DC demotion │ │ - GPO merge   │ │ - Tiered      │
│ - Kerberos    │ │ - Hybrid ID   │ │ - DNS cleanup │ │ - Settings    │ │   admin       │
│ - Service acct│ │ - SSO reconfig│ │ - Trust remove│ │   standardize │ │ - PAM/PIM     │
└───────────────┘ └───────────────┘ └───────────────┘ └───────────────┘ └───────────────┘
                    │              DOWNSTREAM DEPENDENCIES                     │
                    │  (Cannot complete until AD consolidation finishes)       │
                    └─────────────────────────────────────────────────────────┘
```

---

## AD Consolidation Strategy Decision Tree

```
                        ┌────────────────────────┐
                        │ Both companies have AD? │
                        └───────────┬────────────┘
                                   Yes
                                    │
                        ┌───────────▼────────────┐
                        │ Same schema version?    │
                        └───────────┬────────────┘
                              Yes   │   No
                    ┌───────────────┴────────────────┐
                    │                                │
         ┌──────────▼──────────┐          ┌─────────▼─────────┐
         │ Forest Trust First   │          │ Schema upgrade    │
         │ (preserve autonomy)  │          │ then Trust        │
         └──────────┬──────────┘          └─────────┬─────────┘
                    │                                │
         ┌──────────▼──────────────────────────────▼──────────┐
         │            CONSOLIDATION APPROACH                    │
         └──────────────────────┬──────────────────────────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
    ┌─────────▼────────┐ ┌────▼─────┐ ┌────────▼─────────┐
    │  MIGRATION       │ │  MERGE   │ │  PARALLEL        │
    │  (Restructure)   │ │  (Absorb)│ │  (Long-term)     │
    │                  │ │          │ │                  │
    │  Target users    │ │ Add DCs  │ │  Trust-based     │
    │  move to buyer   │ │ to buyer │ │  coexistence     │
    │  forest          │ │ domain   │ │  indefinitely    │
    │                  │ │          │ │                  │
    │  Clean break     │ │ Fastest  │ │  Risk mitigation │
    │  New SIDs        │ │ SID hist │ │  Complexity      │
    └──────────────────┘ └──────────┘ └──────────────────┘
```

---

## Upstream Dependencies (Prerequisites)

### 1. Network Connectivity
**Must complete before:** Forest trust establishment

| Dependency | Why Required | Blocking Risk |
|------------|--------------|---------------|
| Site-to-site VPN/MPLS | AD replication needs connectivity | No communication |
| DNS resolution (cross-forest) | Name resolution for trust | Trust fails |
| Firewall rules (AD ports) | Replication traffic | Blocked replication |
| Latency <100ms | AD sensitive to latency | Sync failures |
| Bandwidth for replication | Initial sync + ongoing | Slow replication |

**Complexity Signals:**
- "No network connection to target" → Blocked until VPN
- "Sites connected by internet only" → Security concern
- "Target in different country" → Latency + compliance
- "Air-gapped network" → Manual/sneakernet approach

### 2. AD Health Assessment
**Must complete before:** Any consolidation activity

| Dependency | Why Required | Blocking Risk |
|------------|--------------|---------------|
| Replication health | Must be healthy before adding complexity | Replication storm |
| Domain controller health | OS/hardware status | Failures during migration |
| Schema version inventory | Compatibility check | Schema conflicts |
| FSMO role holders identified | Know what to migrate | Role confusion |
| Time synchronization | Kerberos requirement | Authentication failures |
| Tombstone lifetime | Object recovery window | Permanent data loss |

**Complexity Signals:**
- "Replication errors in Event Log" → Fix before proceeding
- "Windows Server 2008 DCs" → Upgrade required
- "Different forest functional levels" → Schema alignment
- "No documentation of FSMO holders" → Discovery work
- "Unknown number of DCs" → Rogue DC risk

### 3. Application Inventory
**Must complete before:** Migration planning

| Dependency | Why Required | Blocking Risk |
|------------|--------------|---------------|
| LDAP-bound applications | Must update connection strings | App failures |
| Kerberos-dependent apps | SPNs must migrate | Authentication breaks |
| Service accounts inventory | Must migrate or recreate | Service failures |
| Group memberships mapped | Authorization dependencies | Access loss |
| Certificate-based auth apps | PKI considerations | Auth failures |

**Complexity Signals:**
- "500+ service accounts" → Major migration effort
- "Applications hardcoded to DC names" → Application changes
- "Custom LDAP schema extensions" → Schema merge complexity
- "Unknown service account owners" → Orphan account risk
- "Legacy apps using NTLM" → Security + migration issues

### 4. Security Posture Assessment
**Must complete before:** Trust establishment

| Dependency | Why Required | Blocking Risk |
|------------|--------------|---------------|
| Privileged account audit | Know what's at risk | Lateral movement |
| GPO inventory | Understand security policies | Policy conflicts |
| Admin account count | Reduce before connecting | Attack surface |
| Password policy review | Alignment needed | User confusion |
| Kerberos delegation audit | Security risk assessment | Privilege escalation |

**Complexity Signals:**
- "50+ domain admins" → Immediate risk, remediation first
- "No PAM solution" → Privileged access risk
- "Password never expires enabled" → Compliance issue
- "Unconstrained delegation" → Critical security risk
- "Trust to unknown forests" → Transitive trust risk

### 5. Governance Decisions
**Must complete before:** Architecture design

| Dependency | Why Required | Blocking Risk |
|------------|--------------|---------------|
| Target forest architecture | Single vs multi-domain | Rework if wrong |
| Naming convention decisions | UPN, group names, OU structure | Confusion |
| OU structure design | Administrative boundaries | Delegation issues |
| Group strategy | Universal, global, domain local | Nested group issues |
| Retention of target brand | Separate domain vs absorb | Political issues |

**Complexity Signals:**
- "No decision on target architecture" → Project blocked
- "Political resistance to name changes" → Extended timeline
- "Multiple business units with autonomy" → Complex OU design
- "Regulatory requirement for separation" → Parallel forests

---

## Downstream Dependencies (Blocked Until Complete)

### 1. Application Re-pointing
**Blocked until:** Users migrated or trust established

| Dependency | Why Blocked | Impact of Delay |
|------------|-------------|-----------------|
| LDAP connection string updates | Need target AD available | Dual maintenance |
| Service account migration | Accounts must exist in target | Service failures |
| Kerberos SPN updates | New realm/domain | Auth failures |
| RADIUS/NPS configuration | AD dependency | Network auth fails |

**Typical Timeline:** 3-6 months during/after migration

### 2. Microsoft 365 / Azure AD Changes
**Blocked until:** AD consolidation approach decided

| Dependency | Why Blocked | Impact of Delay |
|------------|-------------|-----------------|
| Azure AD Connect reconfiguration | Source AD changing | Sync errors |
| Hybrid identity updates | UPN changes | Sign-in issues |
| SSO reconfiguration | New IdP source | App access breaks |
| Conditional Access updates | New user objects | Policy gaps |

**Typical Timeline:** Parallel with AD consolidation

### 3. Legacy DC Decommissioning
**Blocked until:** All users/apps migrated

| Dependency | Why Blocked | Impact of Delay |
|------------|-------------|-----------------|
| DC demotion | Users still authenticating | Continued cost |
| DNS cleanup | Records still in use | Name resolution |
| Trust removal | May still need cross-forest | Connectivity loss |
| License termination | DCs still required | Windows Server cost |

**Typical Timeline:** 3-6 months post-migration

### 4. Group Policy Consolidation
**Blocked until:** OU structure finalized

| Dependency | Why Blocked | Impact of Delay |
|------------|-------------|-----------------|
| GPO merge/migration | OUs must exist | Inconsistent policy |
| Settings standardization | Target architecture needed | Configuration drift |
| Security baseline application | New structure required | Security gaps |
| GPO cleanup | Can't remove until migrated | GPO sprawl |

**Typical Timeline:** During and after migration

### 5. Security Hardening
**Blocked until:** Consolidation complete

| Dependency | Why Blocked | Impact of Delay |
|------------|-------------|-----------------|
| Tiered admin implementation | Need stable environment | Continued risk |
| PAM/PIM deployment | Admin accounts must be known | Privileged access risk |
| Credential hygiene | Ongoing changes block cleanup | Credential exposure |
| Trust cleanup | Migration dependency | Unnecessary trust paths |

**Typical Timeline:** 3-6 months post-consolidation

---

## Migration Approach Comparison

### Option A: User Migration (ADMT)
**Best for:** Full integration, clean break desired

```
Source Forest                           Target Forest
┌─────────────────┐                    ┌─────────────────┐
│ Domain A        │     ADMT           │ Domain X        │
│                 │ ───────────────►   │                 │
│ • Users         │  SID History       │ • Users (new)   │
│ • Groups        │  preserved         │ • Groups (new)  │
│ • Computers     │                    │ • Computers     │
│ • Service Accts │                    │ • Service Accts │
└─────────────────┘                    └─────────────────┘
```

| Pros | Cons |
|------|------|
| Clean architecture | User downtime during migration |
| No ongoing trust | All apps need re-pointing |
| Simplified management | SID history complications |
| Single directory | Service account coordination |

**Complexity Signals:**
- Simple: <1000 users, <50 apps
- Medium: 1000-5000 users, 50-200 apps
- Complex: >5000 users, >200 apps

### Option B: Domain Merge
**Best for:** Speed, buyer absorbing small target

```
Buyer Forest
┌────────────────────────────────────────┐
│ Buyer Domain                           │
│                                        │
│ ┌──────────────┐  ┌──────────────┐    │
│ │ Buyer DCs    │  │ New DCs      │    │
│ │              │  │ (ex-target)  │    │
│ └──────────────┘  └──────────────┘    │
│                                        │
│ All users in single domain             │
└────────────────────────────────────────┘
```

| Pros | Cons |
|------|------|
| Fastest approach | Must match schema exactly |
| Single domain simplicity | Target brand lost |
| No SID changes | GPO conflicts possible |
| Minimal app changes | Political resistance |

### Option C: Forest Trust (Long-term Coexistence)
**Best for:** Regulatory separation, gradual integration

```
┌─────────────────┐         ┌─────────────────┐
│ Buyer Forest    │◄───────►│ Target Forest   │
│                 │  Trust  │                 │
│ • Autonomous    │         │ • Autonomous    │
│ • Own policies  │         │ • Own policies  │
│ • Own admins    │         │ • Own admins    │
└─────────────────┘         └─────────────────┘
        │                           │
        └───────┬───────────────────┘
                │
        ┌───────▼───────┐
        │ Cross-forest  │
        │ resource      │
        │ access        │
        └───────────────┘
```

| Pros | Cons |
|------|------|
| Minimal disruption | Ongoing complexity |
| Preserved autonomy | Two directories to manage |
| Gradual migration | Trust security risks |
| Regulatory compliance | Nested group limitations |

---

## Cost Estimation Signals

| Factor | Impact | Multiplier |
|--------|--------|------------|
| User count | Migration effort | 1.0x (<1K), 1.5x (1-5K), 2.0x (>5K) |
| Forest count | Complexity | 1.0x (1), 1.5x (2), 2.0x+ (3+) |
| Domain count | Trust complexity | 1.0x per domain |
| DC count | Infrastructure work | +$10K per DC |
| Application count | Re-pointing effort | 1.2x per 50 apps |
| Service accounts | Migration effort | 1.1x per 100 accounts |
| Geographic spread | Coordination | 1.2x-1.5x |
| Schema extensions | Merge complexity | 1.3x-2.0x |
| GPO count | Policy work | 1.1x per 50 GPOs |
| Compliance requirements | Documentation | 1.2x-1.5x |

---

## M&A Due Diligence Checklist

### Pre-Deal Assessment

| Question | Red Flag Answer | Cost Impact |
|----------|-----------------|-------------|
| How many AD forests? | >2 | +50% per forest |
| Forest functional level? | 2008 or lower | Upgrade required |
| Schema extensions? | Yes, custom | Merge complexity |
| Domain admin count? | >20 | Security remediation |
| Service account inventory? | None | Discovery work |
| GPO count? | >200 | Policy rationalization |
| DC count? | >20 | Extended decommission |
| Trust relationships? | Unknown | Discovery + risk |
| Azure AD Connect? | No | Setup required |
| Replication healthy? | Unknown/No | Fix before migration |

### Integration Considerations

| Scenario | Complexity | Recommendation |
|----------|------------|----------------|
| Single forest each, same version | Lower | Migration or merge |
| Multiple forests, different versions | High | Staged approach |
| Target has custom schema | High | Schema analysis first |
| Target larger than buyer | Political | Joint governance model |
| Regulatory separation required | Ongoing | Long-term trust |

---

## Common Failure Modes

1. **Network Not Ready** - Trust establishment fails, replication broken
2. **Service Account Orphans** - Apps fail when accounts don't migrate
3. **SID History Issues** - Token bloat, access problems
4. **Schema Conflicts** - Custom extensions cause merge failures
5. **GPO Conflicts** - Inconsistent user experience
6. **DNS Cleanup Missed** - Name resolution failures post-migration
7. **Privileged Access Not Addressed** - Security incident during migration
8. **Application Dependencies Unknown** - Unexpected outages
9. **User Communication Gaps** - Password/UPN change confusion
10. **Rollback Not Planned** - No recovery path if migration fails

---

## Key Questions for Document Analysis

When analyzing IT DD documents, look for these AD-related signals:

1. **Architecture Indicators**
   - "Multiple forests" → Complex consolidation
   - "Single domain" → Simpler scenario
   - "Resource forest" → Application dependencies
   - "DMZ forest" → Security architecture

2. **Health Signals**
   - "Replication issues" → Fix before migration
   - "Legacy DCs" (2008/2012) → Upgrade needed
   - "FSMO role issues" → Infrastructure cleanup
   - "Schema version" → Compatibility check

3. **Security Concerns**
   - "Domain admins" count → Attack surface
   - "Service accounts" → Migration scope
   - "Privileged access" → PAM requirements
   - "Trust relationships" → Security review

4. **M&A Signals**
   - "Previous acquisitions not integrated" → Technical debt
   - "Subsidiary has own AD" → Multiple forests
   - "Partner access via trust" → External dependencies
   - "Contractor accounts" → Cleanup scope

---

## Timeline Example: Medium Complexity

```
Month:  1   2   3   4   5   6   7   8   9  10  11  12
        │   │   │   │   │   │   │   │   │   │   │   │
Discovery   ████│
& Planning      │
                │
Network     ████████│
Connectivity        │
                    │
Trust               ████│
Establishment           │
                        │
Pilot                   ████████│
Migration                       │
(100 users)                     │
                                │
App Assessment          ████████████████│
& Planning                              │
                                        │
Batch Migration                     ████████████████│
(remaining users)                                   │
                                                    │
App Cutover                                 ████████████│
                                                        │
DC Decommission                                     ████████
& Cleanup
```

---

*Playbook Version: 1.0*
*Last Updated: January 2026*
