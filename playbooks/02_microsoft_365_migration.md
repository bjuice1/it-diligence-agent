# Microsoft 365 Migration Playbook

## Overview

Microsoft 365 migrations are foundational to modern workplace transformations. They touch nearly every system and user, making dependency management critical for M&A integration success.

**Typical Duration:** 3-12 months (varies by complexity)
**Cost Range:** $50-500 per user (migration) + licensing
**Risk Level:** High (business continuity impact)

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
│ Active        │ │  DNS &        │ │  Network      │ │  Mail Flow    │ │  Application  │
│ Directory     │ │  Domain       │ │  Readiness    │ │  Assessment   │ │  Inventory    │
│               │ │               │ │               │ │               │ │               │
│ - AD health   │ │ - Domain own  │ │ - Bandwidth   │ │ - Current MX  │ │ - SMTP apps   │
│ - AAD Connect │ │ - DNS control │ │ - Proxy/FW    │ │ - Routing     │ │ - OAuth apps  │
│ - UPN suffix  │ │ - SPF/DKIM    │ │ - Endpoints   │ │ - Mail flow   │ │ - Legacy auth │
└───────────────┘ └───────────────┘ └───────────────┘ └───────────────┘ └───────────────┘
                                              │
                    ┌─────────────────────────────────────────────────────────┐
                    │              MICROSOFT 365 MIGRATION                     │
                    │                                                          │
                    │  Assessment → Pilot → Mailbox → SharePoint → Teams      │
                    └─────────────────────────────────────────────────────────┘
                                              │
        ┌─────────────────┬──────────────────┼──────────────────┬─────────────────┐
        ▼                 ▼                  ▼                  ▼                 ▼
┌───────────────┐ ┌───────────────┐ ┌───────────────┐ ┌───────────────┐ ┌───────────────┐
│ Legacy Mail   │ │  Security     │ │  Application  │ │  Collaboration│ │  Compliance   │
│ Decommission  │ │  Enablement   │ │  Integration  │ │  Rollout      │ │  Config       │
│               │ │               │ │               │ │               │ │               │
│ - Exchange    │ │ - MFA rollout │ │ - SSO repoint │ │ - Teams       │ │ - Retention   │
│   shutdown    │ │ - CA policies │ │ - API updates │ │ - SharePoint  │ │ - DLP         │
│ - Licenses    │ │ - Defender    │ │ - SMTP relay  │ │ - OneDrive    │ │ - eDiscovery  │
└───────────────┘ └───────────────┘ └───────────────┘ └───────────────┘ └───────────────┘
                    │              DOWNSTREAM DEPENDENCIES                     │
                    │  (Cannot complete until migration finishes)              │
                    └─────────────────────────────────────────────────────────┘
```

---

## Upstream Dependencies (Prerequisites)

### 1. Active Directory Foundation
**Must complete before:** Azure AD Connect setup

| Dependency | Why Required | Blocking Risk |
|------------|--------------|---------------|
| AD health assessment | Sync errors if AD unhealthy | Failed sync |
| UPN suffix configuration | Users need routable UPN | Sign-in failures |
| Azure AD Connect planning | Sync topology decision | Duplicate accounts |
| Password hash sync or federation | Authentication method | No access |
| Duplicate/stale object cleanup | Sync errors | Migration blocks |

**Complexity Signals:**
- "Multiple AD forests" → +40% complexity
- "No Azure AD Connect" → +2-4 weeks setup
- "Federation with ADFS" → Migration path decision
- "Non-routable UPN (company.local)" → UPN change required
- "No AD admins" → Knowledge gap risk

### 2. DNS & Domain Ownership
**Must complete before:** Tenant configuration

| Dependency | Why Required | Blocking Risk |
|------------|--------------|---------------|
| Domain ownership verified | Required for M365 setup | Blocked |
| DNS management access | MX record changes | Mail flow break |
| SPF record control | Email deliverability | Spam/reject |
| DKIM/DMARC preparation | Security requirements | Phishing risk |
| Autodiscover planning | Client configuration | Outlook failures |

**Complexity Signals:**
- "Domain managed by external party" → Coordination delays
- "No DNS admin access" → Blocked migration
- "Multiple email domains" → +10% per domain
- "SPF record at 10 lookup limit" → Optimization needed

### 3. Network Readiness
**Must complete before:** Pilot migration

| Dependency | Why Required | Blocking Risk |
|------------|--------------|---------------|
| Bandwidth assessment | M365 is bandwidth-heavy | Poor performance |
| Proxy/firewall rules | M365 endpoints | Blocked services |
| Split tunneling decision | VPN architecture | Performance |
| ExpressRoute evaluation | Large enterprises | Latency issues |
| Endpoint connectivity | O365 URLs/IPs | Service outages |

**Complexity Signals:**
- "All traffic through proxy" → Performance impact
- "No bandwidth to cloud" → Infrastructure upgrade
- "Strict firewall" → Extensive rule changes
- "Remote sites on slow links" → Phased approach needed

### 4. Current Mail Flow Assessment
**Must complete before:** Migration planning

| Dependency | Why Required | Blocking Risk |
|------------|--------------|---------------|
| Current MX records | Understand mail routing | Mail loss |
| Mail flow rules | Must recreate in EXO | Policy loss |
| Distribution groups | Migration scope | Delivery failures |
| Shared mailboxes | Special handling | Access loss |
| Public folders | Complex migration | Data loss |
| Journaling/archiving | Compliance requirements | Regulatory risk |

**Complexity Signals:**
- "On-premises Exchange 2010 or older" → Hybrid complexity
- "Public folders with 1TB+ data" → Extended timeline
- "Complex mail flow rules (50+)" → Manual recreation
- "Third-party archiving (Mimecast, Proofpoint)" → Integration work
- "SMTP relay dependencies" → Application changes needed

### 5. Application Inventory
**Must complete before:** Migration cutover

| Dependency | Why Required | Blocking Risk |
|------------|--------------|---------------|
| SMTP relay applications | Must configure relay | App email failures |
| OAuth/SAML applications | Authentication changes | App access lost |
| Legacy auth applications | Basic auth deprecation | App failures |
| Calendar integrations | Room/resource bookings | Scheduling breaks |
| Custom Outlook add-ins | Compatibility check | Productivity loss |

**Complexity Signals:**
- "Applications using basic auth" → App modernization required
- "Legacy ERP sending email" → SMTP relay configuration
- "100+ apps using OAuth" → Significant SSO work
- "Custom Outlook COM add-ins" → Compatibility testing

---

## Downstream Dependencies (Blocked Until Complete)

### 1. Legacy Mail System Decommissioning
**Blocked until:** All mailboxes migrated + coexistence validated

| Dependency | Why Blocked | Impact of Delay |
|------------|-------------|-----------------|
| Exchange server shutdown | Hybrid dependency | Double infrastructure |
| Exchange licensing end | Need fallback | Continued cost |
| Hardware reclamation | Servers still in use | Data center cost |
| Support contract end | Need support for hybrid | Vendor fees |

**Typical Timeline:** 3-6 months post-migration

### 2. Security Enhancement Rollout
**Blocked until:** Users on M365 + identity stable

| Dependency | Why Blocked | Impact of Delay |
|------------|-------------|-----------------|
| MFA enforcement | Need M365 authentication | Security gap |
| Conditional Access | Requires Azure AD Premium | No zero trust |
| Microsoft Defender | Needs mailbox migration | Security gap |
| Data Loss Prevention | Needs content in M365 | Compliance gap |
| Sensitivity labels | Content must be migrated | Classification gap |

**Typical Timeline:** Begins immediately post-migration

### 3. Application Integration Updates
**Blocked until:** M365 tenant and DNS stable

| Dependency | Why Blocked | Impact of Delay |
|------------|-------------|-----------------|
| SSO reconfiguration | New IdP endpoint | Dual sign-on |
| SMTP relay cutover | Mail routing must be final | Delayed app migration |
| Graph API integration | Tenant must be production | App features blocked |
| Teams app deployment | Requires active tenant | Collaboration delays |

**Typical Timeline:** 1-3 months post-migration

### 4. Collaboration Platform Rollout
**Blocked until:** Core M365 services stable

| Dependency | Why Blocked | Impact of Delay |
|------------|-------------|-----------------|
| Teams deployment | Needs identity and mail | Delayed collaboration |
| SharePoint migration | Requires tenant setup | Content stuck on-prem |
| OneDrive rollout | Needs identity sync | File sync issues |
| Power Platform | Requires M365 foundation | Automation delayed |

**Typical Timeline:** Begins during/after mail migration

### 5. Compliance & Governance Configuration
**Blocked until:** Content migrated to M365

| Dependency | Why Blocked | Impact of Delay |
|------------|-------------|-----------------|
| Retention policies | Content must be in M365 | Compliance gap |
| eDiscovery configuration | Data must be searchable | Legal risk |
| Information barriers | Teams/groups must exist | Data leak risk |
| Audit logging | Activity must be in M365 | Audit trail gap |

**Typical Timeline:** 1-2 months post-migration

---

## M&A Integration Scenarios

### Scenario 1: Tenant-to-Tenant Migration (Acquisition)
```
Target Tenant  ──────────────────────────►  Buyer Tenant
   │                                              │
   ├─ Mailboxes ────────────────────────────────► Mailboxes
   ├─ OneDrive ─────────────────────────────────► OneDrive
   ├─ SharePoint ───────────────────────────────► SharePoint
   ├─ Teams ────────────────────────────────────► Teams
   └─ Azure AD objects ─────────────────────────► Azure AD
```

**Key Dependencies:**
- Target domain must transfer to buyer tenant
- Cross-tenant migration tools required
- User rescheduling of recurring meetings
- External sharing links break

**Timeline:** 4-8 months

### Scenario 2: Coexistence During Integration
```
Target Tenant ◄──── Coexistence ────► Buyer Tenant
     │                  │                    │
     │              ┌───┴───┐               │
     │              │ GAL   │               │
     │              │ Sync  │               │
     │              │       │               │
     │              │ Free/ │               │
     │              │ Busy  │               │
     │              └───────┘               │
```

**Key Dependencies:**
- Organization relationship configured
- Azure AD B2B for cross-tenant access
- Shared address book sync
- Calendar free/busy lookup

**Timeline:** Indefinite (parallel operation)

### Scenario 3: Carveout (Divestiture)
```
Parent Tenant ─────────────────────────► New Standalone Tenant
     │                                         │
     ├─ Subset of mailboxes ──────────────────► Mailboxes
     ├─ Subset of OneDrive ───────────────────► OneDrive
     ├─ Carved-out SharePoint ────────────────► SharePoint
     └─ Subset of Azure AD ───────────────────► Azure AD
                                               │
                                     New domain purchased
```

**Key Dependencies:**
- New domain procurement
- License procurement for new tenant
- Data separation and extraction
- TSA for coexistence period

**Timeline:** 3-6 months + TSA period

---

## Cost Estimation Signals

| Factor | Impact | Multiplier |
|--------|--------|------------|
| User count | Base licensing + migration | 1.0x baseline |
| Mailbox size (avg) | Storage + migration time | 1.0x-1.5x |
| Public folders | Complex migration | +$50K-200K |
| Archive mailboxes | Additional migration | 1.2x |
| Third-party archive | Integration work | +$30K-100K |
| Multiple domains | Per-domain overhead | +10% per domain |
| Exchange version | 2010 vs 2016+ | 1.0x-1.4x |
| Hybrid duration | Extended coexistence | +$20K/month |
| Geographic spread | Scheduling complexity | 1.1x-1.3x |
| Compliance (legal hold) | Chain of custody | 1.2x-1.5x |

---

## Critical Path Analysis

```
Week:   1   2   3   4   5   6   7   8   9  10  11  12  13  14  15  16
        │   │   │   │   │   │   │   │   │   │   │   │   │   │   │   │
AD      ████████│
Prep            │
                │
DNS         ████████│
Setup               │
                    │
Network     ████████████│
Config                  │
                        │
Pilot           ░░░░░░░░████│
Migration                   │
                            │
Batch                   ████████████████████│
Migration                                   │
                                           │
Security                            ████████████████│
Rollout                                             │
                                                    │
Collaboration                               ████████████████
Rollout

Legacy                                              ░░░░░░░░░░
Decommission
```

---

## M&A Due Diligence Checklist

### Pre-Deal Assessment

| Question | Red Flag Answer | Cost Impact |
|----------|-----------------|-------------|
| Current email platform? | Lotus Notes, GroupWise | +$100-200/user |
| Exchange version? | 2010 or older | +40% migration cost |
| Mailbox count? | >10,000 | Extended timeline |
| Average mailbox size? | >10GB | Storage + migration time |
| Public folder usage? | Yes, heavy | +$50K-200K |
| Third-party archiving? | Yes | Integration work |
| Tenant already exists? | Yes (buyer integration) | Tenant-to-tenant migration |
| Geographic presence? | Global | Multi-phase approach |
| Compliance requirements? | Legal hold, eDiscovery | Chain of custody work |
| Domain count? | >5 | +10% per domain |

### Integration Considerations

| Scenario | Complexity | Recommendation |
|----------|------------|----------------|
| Target on M365, buyer on M365 | Medium | Tenant-to-tenant migration |
| Target on Exchange, buyer on M365 | Medium-High | Standard migration |
| Target on Lotus Notes | Very High | Consider specialist partner |
| Target on Google Workspace | Medium | G Suite migration tools |
| Target on M365, buyer on-prem | Unusual | Evaluate buyer modernization |

---

## Common Failure Modes

1. **DNS Changes Without Testing** - MX record change causes mail loss
2. **Public Folder Underestimation** - Migration takes weeks, not days
3. **Application Dependencies Missed** - Line-of-business email breaks
4. **Network Not Ready** - Poor Outlook/Teams performance
5. **No Hybrid Period** - Big bang causes support surge
6. **Legacy Auth Not Addressed** - Apps break after security policies
7. **Change Management Neglected** - Users frustrated with new UI
8. **License Mismatch** - Features unavailable after migration

---

## Key Questions for Document Analysis

When analyzing IT DD documents, look for these M365-related signals:

1. **Current Platform Indicators**
   - "Exchange 2010/2013" → End of support, migration urgent
   - "Lotus Notes" / "HCL Notes" → High-complexity migration
   - "Google Workspace" / "G Suite" → Cross-platform migration
   - "Office 365 already" → Tenant-to-tenant scenario

2. **Complexity Signals**
   - "Public folders" → Extended timeline
   - "Shared mailboxes" → Special handling
   - "Archive solution" (Mimecast, Proofpoint) → Integration work
   - "Legal hold" / "litigation" → Chain of custody requirements

3. **Infrastructure Dependencies**
   - "Single forest" → Simpler, "multiple forests" → Complex
   - "Hybrid Exchange" → Existing M365 relationship
   - "ADFS" → Federation decision
   - "Proxy for all traffic" → Performance concern

4. **M&A Signals**
   - "Keep separate" → Coexistence approach
   - "Full integration" → Tenant-to-tenant
   - "Carveout" → New tenant creation
   - "TSA" → Extended coexistence period

---

*Playbook Version: 1.0*
*Last Updated: January 2026*
