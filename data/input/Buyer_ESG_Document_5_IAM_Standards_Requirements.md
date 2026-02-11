# Enterprise Solutions Group (ESG) — Buyer Document 5: Identity & Access Management Standards

> **Entity:** BUYER
> **Purpose:** ESG IAM standards and requirements for acquisition integration

---

## 1) ESG IAM Architecture (Standard)

| Component | Technology | Coverage | Notes |
|---|---|---|
| **Workforce IdP** | Azure AD (Microsoft Entra ID) | 24,500 employees | Enterprise E5 licenses |
| **Customer IdP** | Azure AD B2C | Product platforms | Multi-tenant SaaS |
| **MFA** | Azure AD MFA (Authenticator app) | 100% of users | Enforced via Conditional Access |
| **SSO** | Azure AD SSO | 180+ enterprise apps | SAML, OIDC, WS-Fed |
| **PAM** | CyberArk Privileged Access Manager | 1,200 privileged users | Full enterprise deployment |
| **IGA** | SailPoint IdentityIQ | All identity lifecycle | Automated provisioning/deprovisioning |

---

## 2) ESG IAM Requirements for Acquisitions

### Day 1-30 (Immediate)

| Requirement | Standard | CloudServe State | Action |
|---|---|---|---|
| **MFA enforcement** | 100% of users | 85% (62 users without MFA) | Enforce MFA for all users (30 days) |
| **Privileged access** | All admins in PAM | 15 users in CyberArk (26 not covered) | Expand CyberArk coverage (60 days) |
| **Azure AD federation** | SSO to ESG apps | Not configured | Implement federation (30 days) |
| **Password policy** | Azure AD policy | Okta policy (aligned) | Validate alignment (30 days) |

### Day 30-180 (Integration Phase)

| Requirement | Standard | Timeline | Notes |
|---|---|---|
| **Okta → Azure AD migration** | Full migration | 6-12 months | Phased approach (100 users/week) |
| **Auth0 → Azure AD B2C** | Platform IdP migration | 18-24 months | Complex (embedded in product) |
| **Automated provisioning** | SailPoint IGA | 6 months | Onboard to ESG SailPoint |
| **Access certifications** | Quarterly reviews | 6 months | Align to ESG certification cadence |

---

## 3) ESG Azure AD Configuration (Standard)

### Conditional Access Policies (Mandatory)

| Policy | Conditions | Controls | Enforcement |
|---|---|---|---|
| **Require MFA for all users** | All users, all apps | MFA required | Enforced (no exceptions) |
| **Block legacy authentication** | All users, all apps | Block legacy auth protocols | Enforced |
| **Require compliant device** | All users, corporate data | Device compliance via Intune | Enforced |
| **Require approved app** | Mobile access, corporate apps | Approved mobile apps only | Enforced |
| **Block risky sign-ins** | High-risk sign-ins | Block or require MFA + password change | Enforced |
| **Geo-blocking** | Sign-ins from blocked countries | Block access | Enforced (configurable list) |

**CloudServe Integration:** Apply ESG Conditional Access policies to CloudServe users within 30 days of Azure AD federation.

---

## 4) ESG MFA Standards

| Requirement | Standard | CloudServe State |
|---|---|---|
| **MFA method** | Azure AD Authenticator app (preferred) | Okta Verify (aligned concept) |
| **Backup MFA** | SMS, voice call | SMS, voice (aligned) |
| **Hardware tokens** | YubiKey (executives, high-risk users) | ❌ Not deployed |
| **Passwordless** | Windows Hello, FIDO2 | ❌ Not deployed |
| **MFA coverage** | 100% (no exceptions) | ⚠️ 85% (15% gap) |

**Requirement:** Enforce 100% MFA coverage within 30 days (62 users need MFA enrollment).

---

## 5) ESG Privileged Access Management (PAM) Standards

| Standard | Technology | CloudServe State |
|---|---|---|
| **PAM platform** | CyberArk Enterprise | CyberArk (limited - 15 users) |
| **Coverage** | All privileged users (1,200 at ESG) | ⚠️ GAP: 26 privileged users not covered |
| **Session recording** | All admin sessions | ✅ Enabled for 15 users |
| **Password vaulting** | All privileged credentials | ✅ Enabled for covered users |
| **Just-in-time access** | Required for production access | ❌ Not implemented |
| **Privileged analytics** | CyberArk DNA (behavioral analytics) | ❌ Not deployed |

**Requirement:** Expand CyberArk to all 41 privileged users (15 current + 26 gap) within 60 days.

---

## 6) ESG Identity Lifecycle Management (IGA)

| Process | ESG Standard (SailPoint) | CloudServe State |
|---|---|---|
| **Onboarding** | Automated via Workday integration | ⚠️ Semi-automated (BambooHR → Okta) |
| **Role-based provisioning** | SailPoint role catalog | ⚠️ Manual role assignments |
| **Automated deprovisioning** | Immediate (Workday termination → SailPoint) | ✅ Automated (BambooHR → Okta) |
| **Access certifications** | Quarterly manager attestations | ⚠️ GAP: Manual reviews, inconsistent |
| **Orphaned account detection** | Automated (SailPoint) | ⚠️ GAP: Manual scans only |
| **Separation of duties** | SailPoint SOD rules | ❌ Not implemented |

**Requirement:** Onboard CloudServe to ESG SailPoint IGA within 6 months.

---

## 7) ESG SSO Requirements

| Requirement | Standard | CloudServe State |
|---|---|---|
| **SSO protocol** | SAML 2.0 (preferred), OIDC | ✅ Aligned (Okta supports both) |
| **SSO coverage** | 100% of SaaS apps | ⚠️ 50% (12 apps SSO, 26 non-SSO) |
| **IdP** | Azure AD | Okta (migrate within 6-12 months) |
| **Federated access to ESG apps** | Required Day 1 | ⚠️ Not configured (implement within 30 days) |

**Day 1 Requirement:** Federate Okta with Azure AD (SAML) to enable CloudServe users to SSO into ESG apps.

---

## 8) ESG Cloud IAM Standards

### AWS IAM (for acquisitions)

| Standard | Requirement | CloudServe State |
|---|---|---|
| **AWS SSO** | Enabled, federated to Azure AD | ✅ Enabled (federated to Okta) |
| **MFA** | Required for all human users | ✅ Enforced via Okta |
| **IAM users** | Service accounts only (no human IAM users) | ⚠️ GAP: 8 legacy IAM users exist |
| **Root account** | MFA enabled, keys vaulted in CyberArk | ✅ MFA enabled, keys in CyberArk |
| **Permission sets** | Least privilege, ESG-approved sets | ⚠️ Custom permission sets (review required) |

**Requirement:** Migrate 8 legacy IAM users to AWS SSO within 90 days.

### Azure IAM (for future migration)

| Standard | Requirement | Future State (if migrating to Azure) |
|---|---|---|
| **Azure AD** | All user access via Azure AD | N/A (CloudServe is AWS-only currently) |
| **Managed identities** | For application authentication | N/A |
| **RBAC** | Azure RBAC for resource access | N/A |

---

## 9) Okta → Azure AD Migration Plan

### Migration Approach (Phased)

| Phase | Timeline | Activities | User Impact |
|---|---|---|---|
| **Phase 0: Federation** | Day 1-30 | Federate Okta ↔ Azure AD (SAML) | None (transparent SSO to ESG apps) |
| **Phase 1: Pilot** | Month 2-3 | Migrate 50 pilot users to Azure AD | Pilot users re-enroll MFA, new login flow |
| **Phase 2: Waves** | Month 4-9 | Migrate 100 users/week in waves | Users re-enroll MFA during migration |
| **Phase 3: Cutover** | Month 10-12 | Final cutover, decommission Okta | All users on Azure AD |

### Migration Dependencies

| Dependency | Description | Impact |
|---|---|---|
| **App SSO reconfiguration** | 12 apps need SAML update (Okta → Azure AD) | Medium effort |
| **MFA re-enrollment** | 350 users need to enroll in Azure AD MFA | User friction |
| **AWS SSO update** | Update federation from Okta to Azure AD | Low impact (backend change) |
| **Custom Okta workflows** | 6 provisioning workflows (migrate to SailPoint) | Medium effort |

**Estimated Cost:** $300K-500K (migration project + SailPoint integration)

---

## 10) Auth0 → Azure AD B2C Migration (Complex)

### Migration Complexity

| Factor | Complexity | Reason |
|---|---|---|
| **Embedded in platform** | 🔴 HIGH | Auth0 SDK deeply integrated in code |
| **1.8M customer accounts** | 🔴 HIGH | User migration at scale |
| **287 SAML integrations** | 🔴 HIGH | Customer SSO reconfigurations |
| **Custom authentication rules** | 🟠 MEDIUM | Auth0 rules → Azure AD B2C policies |
| **Multi-tenant architecture** | 🟠 MEDIUM | Tenant isolation requirements |

**Timeline:** 18-24 months (phased migration)
**Estimated Cost:** $200K-400K (engineering effort + testing + customer communications)

**ESG Recommendation:** Defer Auth0 migration for 18-24 months; prioritize workforce IdP (Okta) migration first.

---

## 11) ESG Access Governance Requirements

| Requirement | Standard | CloudServe State | Timeline |
|---|---|---|---|
| **Access certifications** | Quarterly (manager attestations) | ⚠️ Manual, inconsistent | Implement within 6 months (SailPoint) |
| **Privileged access reviews** | Monthly | ✅ Monthly (via CyberArk) | Aligned |
| **Orphaned account cleanup** | Automated detection + quarterly cleanup | ⚠️ Manual scans only | Implement within 6 months |
| **Separation of duties** | Automated SOD conflict detection | ❌ Not implemented | Implement within 12 months |
| **Role mining** | SailPoint role mining for RBAC | ❌ Not implemented | Implement within 12 months |

---

## 12) ESG Third-Party Identity Requirements

| Requirement | Standard | CloudServe State |
|---|---|---|
| **Vendor MFA** | Required for all vendor access | ⚠️ GAP: MSP (CGI) has no MFA |
| **Vendor JIT access** | Just-in-time access (CyberArk) | ❌ Not implemented |
| **Vendor account reviews** | Quarterly | ⚠️ GAP: Reviewed 6 months ago |
| **Vendor access logging** | All activity logged to SIEM | ⚠️ Partial (VPN logs only) |

**Requirement:** Enforce MFA for all vendor access within 30 days (immediate fix for MSP).

---

## 13) IAM Integration Timeline (CloudServe)

| Milestone | Timeline | Activities |
|---|---|---|
| **Day 1-30** | Month 1 | MFA 100% enforcement, Azure AD federation, MSP MFA fix |
| **Day 30-60** | Month 2 | CyberArk expansion (41 users), legacy IAM user cleanup |
| **Day 60-180** | Months 3-6 | Okta → Azure AD pilot (50 users), SailPoint onboarding |
| **Day 180-365** | Months 7-12 | Okta → Azure AD migration (all 412 users) |
| **Day 365+** | Year 2+ | Auth0 → Azure AD B2C migration (18-24 months) |

---

## 14) IAM Budget Estimate (CloudServe Integration)

| Category | One-Time Cost | Annual Recurring Cost |
|---|---:|---:|
| **Azure AD licenses (included in M365 E5)** | $0 | Included in ESG M365 enterprise agreement |
| **CyberArk expansion (26 additional users)** | $50K-100K | Included in ESG CyberArk license |
| **Okta → Azure AD migration** | $300K-500K | $0 (replace Okta, save $98K/year) |
| **SailPoint IGA integration** | $75K-150K | Included in ESG SailPoint license |
| **Auth0 → Azure AD B2C migration** | $200K-400K | $0 (replace Auth0, cost neutral) |
| **TOTAL** | **$625K-1.15M** | **-$98K/year (Okta license savings)** |

---

## 15) CloudServe IAM Gaps Summary

| Gap | Severity | Fix Timeline | Estimated Cost |
|---|---|---|---:|
| **MFA coverage (15% gap)** | 🟠 MEDIUM | 30 days | $10K-20K |
| **PAM coverage (26 users)** | 🟠 MEDIUM | 60 days | $50K-100K |
| **Legacy IAM users (8)** | 🟡 LOW | 90 days | $5K-10K |
| **No IGA tool** | 🟡 LOW | 6 months | $75K-150K |
| **Manual access reviews** | 🟡 LOW | 6 months | Included in IGA |
| **MSP no MFA** | 🟠 MEDIUM | 30 days | $0 (policy enforcement) |
| **Okta → Azure AD migration** | 🟠 MEDIUM | 6-12 months | $300K-500K |

**Total IAM Remediation Cost:** $440K-780K (one-time)

---

**END OF BUYER DOCUMENT 5**
