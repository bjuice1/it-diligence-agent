# Security Remediation Playbook

## Overview

Security remediation is frequently a Day 1 priority in M&A transactions. Buyers often discover security gaps during due diligence that must be addressed before integration. This playbook maps dependencies for common security remediation workstreams.

**Typical Duration:** 6-18 months (initial remediation), ongoing thereafter
**Cost Range:** $500K-$5M+ (depends on scope)
**Risk Level:** Critical (business continuity, reputation, compliance)

---

## Security Remediation Priority Framework

```
                            REMEDIATION PRIORITY MATRIX

                    EXPLOITABILITY
                    Low                 Medium              High
                ┌─────────────────┬─────────────────┬─────────────────┐
        High    │                 │                 │                 │
                │   PLAN          │   IMPORTANT     │   CRITICAL      │
                │   90+ days      │   30-90 days    │   0-30 days     │
    IMPACT      │                 │                 │                 │
                ├─────────────────┼─────────────────┼─────────────────┤
        Medium  │                 │                 │                 │
                │   BACKLOG       │   PLAN          │   IMPORTANT     │
                │   Future        │   90+ days      │   30-90 days    │
                │                 │                 │                 │
                ├─────────────────┼─────────────────┼─────────────────┤
        Low     │                 │                 │                 │
                │   ACCEPT        │   BACKLOG       │   PLAN          │
                │   Risk accepted │   Future        │   90+ days      │
                │                 │                 │                 │
                └─────────────────┴─────────────────┴─────────────────┘

CRITICAL: Internet-exposed vulnerabilities, active threats, compliance deadlines
IMPORTANT: Internal network risks, elevated privilege risks, audit findings
PLAN: Technical debt, best practice gaps, optimization opportunities
BACKLOG: Minor issues, future improvements
ACCEPT: Documented risk acceptance with mitigation controls
```

---

## Dependency Map

```
                    ┌─────────────────────────────────────────────────────────┐
                    │              UPSTREAM DEPENDENCIES                       │
                    │  (Must be complete BEFORE security remediation)          │
                    └─────────────────────────────────────────────────────────┘
                                              │
        ┌─────────────────┬──────────────────┼──────────────────┬─────────────────┐
        ▼                 ▼                  ▼                  ▼                 ▼
┌───────────────┐ ┌───────────────┐ ┌───────────────┐ ┌───────────────┐ ┌───────────────┐
│ Asset         │ │  Vulnerability│ │  Identity     │ │  Network      │ │  Security     │
│ Inventory     │ │  Assessment   │ │  Inventory    │ │  Visibility   │ │  Tooling      │
│               │ │               │ │               │ │               │ │               │
│ - All systems │ │ - Vuln scans  │ │ - All accounts│ │ - Network map │ │ - EDR/XDR     │
│ - All apps    │ │ - Pen test    │ │ - Service acct│ │ - Traffic flow│ │ - SIEM        │
│ - All data    │ │ - Config audit│ │ - Privileged  │ │ - Segmentation│ │ - Vulnerability│
└───────────────┘ └───────────────┘ └───────────────┘ └───────────────┘ └───────────────┘
                                              │
                    ┌─────────────────────────────────────────────────────────┐
                    │                SECURITY REMEDIATION                      │
                    │                                                          │
                    │  Critical → High → Medium → Low → Ongoing Ops           │
                    └─────────────────────────────────────────────────────────┘
                                              │
        ┌─────────────────┬──────────────────┼──────────────────┬─────────────────┐
        ▼                 ▼                  ▼                  ▼                 ▼
┌───────────────┐ ┌───────────────┐ ┌───────────────┐ ┌───────────────┐ ┌───────────────┐
│ Integration   │ │  Compliance   │ │  Insurance    │ │  Security     │ │  Operational  │
│ Enablement    │ │  Certification│ │  Renewal      │ │  Operations   │ │  Efficiency   │
│               │ │               │ │               │ │               │ │               │
│ - Network     │ │ - SOC 2       │ │ - Cyber       │ │ - 24x7 SOC    │ │ - Automation  │
│   connection  │ │ - ISO 27001   │ │   insurance   │ │ - Incident    │ │ - Self-service│
│ - Trust       │ │ - PCI DSS     │ │ - D&O         │ │   response    │ │ - Policy as   │
│   establishment│ - HIPAA       │ │ - Coverage    │ │ - Threat intel│ │   code        │
└───────────────┘ └───────────────┘ └───────────────┘ └───────────────┘ └───────────────┘
                    │              DOWNSTREAM DEPENDENCIES                     │
                    │  (Enabled/required after security remediation)           │
                    └─────────────────────────────────────────────────────────┘
```

---

## Common Remediation Workstreams

### 1. Endpoint Protection (EDR/XDR Deployment)

**Dependencies:**

```
UPSTREAM                          EDR DEPLOYMENT                    DOWNSTREAM
─────────────────────────────────────────────────────────────────────────────────
                                        │
Asset inventory ────────────────────────┤
(Know all endpoints)                    │
                                        │
Network access ─────────────────────────┤──────────────► SOC operations
(Agent deployment)                      │                (Monitoring)
                                        │
Admin credentials ──────────────────────┤──────────────► Threat hunting
(Installation rights)                   │                (Detection)
                                        │
Change management ──────────────────────┤──────────────► Incident response
(Approval process)                      │                (Containment)
                                        │
```

| Upstream Dependency | Why Needed | If Missing |
|---------------------|------------|------------|
| Asset inventory | Know what to protect | Gaps in coverage |
| Network access | Deploy agents | Deployment blocked |
| Admin credentials | Install agents | Cannot deploy |
| AV/legacy removal | Conflicts | Agent failures |

| Downstream Enabled | Why Important | Impact |
|-------------------|---------------|--------|
| SOC monitoring | Detection capability | No visibility |
| Threat hunting | Proactive detection | Reactive only |
| Incident response | Containment | Slow response |
| Compliance evidence | Audit requirements | Audit findings |

**Complexity Signals:**
- "No asset inventory" → +30% discovery effort
- "Legacy AV entrenched" → Removal complexity
- "Air-gapped systems" → Separate deployment
- "Linux/Mac estate" → Multi-platform licensing

---

### 2. Identity & Access Management (MFA/SSO)

**Dependencies:**

```
UPSTREAM                          MFA/SSO DEPLOYMENT                DOWNSTREAM
─────────────────────────────────────────────────────────────────────────────────
                                        │
Identity inventory ─────────────────────┤
(All users, service accounts)           │
                                        │
Active Directory health ────────────────┤──────────────► Conditional Access
(Foundation stable)                     │                (Policy enforcement)
                                        │
Application inventory ──────────────────┤──────────────► SSO integration
(What needs SSO)                        │                (App onboarding)
                                        │
Network connectivity ───────────────────┤──────────────► Zero trust
(Cloud identity access)                 │                (Network posture)
                                        │
User communication ─────────────────────┤──────────────► Password-less
(Change management)                     │                (Future state)
                                        │
```

| Upstream Dependency | Why Needed | If Missing |
|---------------------|------------|------------|
| Identity inventory | Know all accounts | Service accounts break |
| AD health | SSO foundation | Sync failures |
| App inventory | Know what to integrate | Gaps |
| Network to cloud | Azure AD/Okta access | Blocked |
| User comms | Adoption | Help desk surge |

| Downstream Enabled | Why Important | Impact |
|-------------------|---------------|--------|
| Conditional Access | Context-aware security | Static access |
| SSO for apps | User experience | Password fatigue |
| Zero trust | Modern security | Perimeter-based |
| Compliance | Audit requirements | Findings |

**Complexity Signals:**
- "No SSO platform" → Platform selection + deployment
- "500+ service accounts" → Major service account effort
- "Legacy apps (no SAML)" → App modernization or exclusion
- "Users in 10+ countries" → Time zone coordination

**Typical Sequence:**
```
1. Identity inventory (2-4 weeks)
2. Platform deployment (4-8 weeks)
3. Pilot users (2-4 weeks)
4. Phased rollout (8-16 weeks)
5. Service account remediation (4-12 weeks)
6. Legacy app integration (ongoing)
```

---

### 3. Vulnerability Management & Patching

**Dependencies:**

```
UPSTREAM                          PATCH MANAGEMENT                  DOWNSTREAM
─────────────────────────────────────────────────────────────────────────────────
                                        │
Asset inventory ────────────────────────┤
(All systems)                           │
                                        │
Vulnerability scans ────────────────────┤──────────────► Compliance
(Know what to patch)                    │                (Patch metrics)
                                        │
Test environments ──────────────────────┤──────────────► Risk reduction
(Validate patches)                      │                (Vuln metrics)
                                        │
Change windows ─────────────────────────┤──────────────► Automation
(Maintenance periods)                   │                (Auto-patching)
                                        │
Backup/recovery ────────────────────────┤──────────────► EOL remediation
(Rollback capability)                   │                (Upgrade path)
                                        │
```

| Upstream Dependency | Why Needed | If Missing |
|---------------------|------------|------------|
| Asset inventory | Know what to patch | Unknown systems |
| Vulnerability scans | Prioritize patches | No prioritization |
| Test environments | Validate patches | Production risk |
| Change windows | Schedule patching | Business disruption |
| Backup/recovery | Rollback if failed | Stuck on bad patch |

| Downstream Enabled | Why Important | Impact |
|-------------------|---------------|--------|
| Compliance metrics | Audit evidence | Findings |
| Risk metrics | Risk reduction | Unmeasured risk |
| Automated patching | Operational efficiency | Manual effort |
| EOL remediation | Technical debt reduction | Unsupported systems |

**Complexity Signals:**
- "1000+ outstanding patches" → Extended timeline
- "No test environment" → Higher risk patching
- "24x7 operations" → Limited windows
- "Legacy systems (EOL)" → Upgrade not patch

---

### 4. Network Segmentation

**Dependencies:**

```
UPSTREAM                          NETWORK SEGMENTATION              DOWNSTREAM
─────────────────────────────────────────────────────────────────────────────────
                                        │
Network inventory ──────────────────────┤
(All devices, subnets)                  │
                                        │
Traffic flow analysis ──────────────────┤──────────────► Zero trust
(Understand patterns)                   │                (Micro-seg)
                                        │
Application dependencies ───────────────┤──────────────► Compliance
(What talks to what)                    │                (PCI zones)
                                        │
Firewall capacity ──────────────────────┤──────────────► Breach containment
(Can handle rules)                      │                (Lateral movement)
                                        │
Change management ──────────────────────┤──────────────► OT security
(Test and rollback)                     │                (IT/OT separation)
                                        │
```

| Upstream Dependency | Why Needed | If Missing |
|---------------------|------------|------------|
| Network inventory | Know what to segment | Gaps |
| Traffic flow analysis | Understand dependencies | Break applications |
| App dependencies | Not break connections | Outages |
| Firewall capacity | Handle rule explosion | Performance |
| Change management | Controlled rollout | Disruption |

| Downstream Enabled | Why Important | Impact |
|-------------------|---------------|--------|
| Zero trust / micro-seg | Modern architecture | Flat network risk |
| Compliance zones | PCI, HIPAA | Audit scope |
| Breach containment | Limit blast radius | Lateral movement |
| OT separation | Critical infrastructure | IT/OT convergence risk |

**Complexity Signals:**
- "Flat network" → Complete redesign
- "1000+ firewall rules" → Rule rationalization first
- "No traffic visibility" → Discovery tools needed
- "Legacy applications" → Unknown dependencies
- "Manufacturing/OT" → IT/OT separation critical

---

### 5. Backup & Disaster Recovery

**Dependencies:**

```
UPSTREAM                          DR IMPLEMENTATION                 DOWNSTREAM
─────────────────────────────────────────────────────────────────────────────────
                                        │
Asset inventory ────────────────────────┤
(What to protect)                       │
                                        │
Business impact analysis ───────────────┤──────────────► Ransomware resilience
(RTO/RPO requirements)                  │                (Recovery capability)
                                        │
Data classification ────────────────────┤──────────────► Compliance
(Criticality)                           │                (Data protection)
                                        │
Network/storage capacity ───────────────┤──────────────► Business continuity
(Replication bandwidth)                 │                (Operational resilience)
                                        │
DR site/cloud ──────────────────────────┤──────────────► Insurance
(Recovery location)                     │                (Coverage validation)
                                        │
```

| Upstream Dependency | Why Needed | If Missing |
|---------------------|------------|------------|
| Asset inventory | Know what to backup | Gaps in protection |
| BIA (RTO/RPO) | Recovery requirements | Wrong priorities |
| Data classification | Prioritize critical | Equal treatment |
| Network capacity | Replication bandwidth | Sync failures |
| DR site | Recovery location | Nowhere to recover |

| Downstream Enabled | Why Important | Impact |
|-------------------|---------------|--------|
| Ransomware resilience | Recovery vs ransom | Pay or lose data |
| Compliance | Data protection evidence | Audit findings |
| Business continuity | Operational resilience | Extended outage |
| Insurance | Coverage validation | Claim denial |

**Complexity Signals:**
- "No offsite backup" → Critical gap
- "No DR site" → Recovery location needed
- "RTO undefined" → BIA required
- "Tape-based backup" → Modernization
- "No DR testing" → Untested recovery

---

## M&A Security Remediation Priorities

### Day 1 - Week 1: Critical & Visibility

| Priority | Action | Dependency |
|----------|--------|------------|
| 1 | Deploy EDR (if missing) | Asset inventory |
| 2 | Enable MFA for admins | Identity inventory |
| 3 | Close internet-facing vulnerabilities | Vulnerability scan |
| 4 | Establish network monitoring | Network visibility |
| 5 | Verify backup integrity | Backup assessment |

### Week 2 - Month 1: High Priority

| Priority | Action | Dependency |
|----------|--------|------------|
| 6 | MFA for all users | Identity foundation |
| 7 | Critical patching | Asset inventory |
| 8 | Privileged access management | Identity baseline |
| 9 | Network trust establishment (to buyer) | Network segmentation |
| 10 | SIEM integration | Monitoring foundation |

### Month 1 - Month 3: Medium Priority

| Priority | Action | Dependency |
|----------|--------|------------|
| 11 | Full vulnerability remediation | Patching foundation |
| 12 | Network segmentation | Traffic analysis |
| 13 | SSO integration | MFA foundation |
| 14 | DR modernization | BIA complete |
| 15 | Compliance gap closure | Assessment complete |

---

## Cost Estimation Signals

| Factor | Impact | Multiplier |
|--------|--------|------------|
| User count | License costs | Per-user tooling |
| Endpoint count | EDR licensing | Per-endpoint |
| Vulnerability count | Remediation effort | 1.0x (<100), 1.5x (100-500), 2.0x (>500) |
| Compliance requirements | Framework mapping | 1.2x-1.5x |
| Legacy systems | Special handling | 1.3x-2.0x |
| 24x7 operations | Change windows | 1.2x-1.5x |
| No security team | Build capability | +$500K-1M |
| Recent breach | Accelerated timeline | 1.5x-2.0x |
| Insurance requirements | Minimum controls | +$100K-300K |

---

## M&A Due Diligence Checklist

### Pre-Deal Security Assessment

| Question | Red Flag Answer | Cost Impact |
|----------|-----------------|-------------|
| EDR deployed? | No / partial | +$50-100K |
| MFA enabled? | No / admins only | +$50-150K |
| Last vulnerability scan? | >6 months | Unknown risk |
| Critical patch backlog? | >30 days | +$100-300K |
| Last pen test? | >12 months / never | Assessment needed |
| Security team? | None / outsourced fully | +$300K-1M annually |
| SIEM deployed? | No | +$100-200K |
| Recent breach? | Yes | Extensive remediation |
| Cyber insurance? | No / lapsed | Procurement needed |
| DR tested? | No / >12 months | BCP/DR work |

### Integration Security Considerations

| Scenario | Risk | Recommendation |
|----------|------|----------------|
| Target has no security tools | High | Immediate deployment |
| Target breached recently | Very High | Forensic assessment |
| Different security vendors | Medium | Consolidation planning |
| Target more mature than buyer | Low | Leverage capabilities |
| Target PCI/HIPAA compliant | Positive | Maintain compliance |

---

## Common Failure Modes

1. **Asset Inventory Gaps** - Can't protect what you don't know
2. **Service Account Breaks** - MFA breaks batch jobs
3. **Patch Disruption** - Untested patches cause outages
4. **Segmentation Outages** - Unknown dependencies broken
5. **Tool Sprawl** - Multiple overlapping security tools
6. **Alert Fatigue** - SIEM floods with noise
7. **Change Resistance** - Users resist MFA/new controls
8. **Legacy Gaps** - EOL systems can't be patched
9. **Integration Rush** - Network connected before secured
10. **Insurance Gaps** - Controls not met, coverage denied

---

## Key Questions for Document Analysis

When analyzing IT DD documents, look for these security signals:

1. **Defensive Posture**
   - "EDR" / "endpoint protection" → Coverage question
   - "SIEM" / "SOC" → Monitoring capability
   - "MFA" / "multi-factor" → Identity security
   - "Vulnerability scan" → Hygiene practices

2. **Vulnerability Signals**
   - "Critical patches" / "backlog" → Patching debt
   - "EOL" / "end of life" / "unsupported" → Legacy risk
   - "Flat network" → Segmentation gap
   - "Penetration test" → When/findings

3. **Incident History**
   - "Breach" / "incident" / "ransomware" → Past events
   - "Forensic" → Investigation history
   - "Insurance claim" → Prior incidents
   - "Notification" → Regulatory impact

4. **Compliance Status**
   - "SOC 2" / "ISO 27001" → Certifications
   - "Audit findings" → Open issues
   - "PCI" / "HIPAA" → Regulated status
   - "Gap assessment" → Known issues

---

*Playbook Version: 1.0*
*Last Updated: January 2026*
