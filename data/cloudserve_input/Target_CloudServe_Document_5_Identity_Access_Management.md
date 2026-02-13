# CloudServe Technologies — Document 5: Identity & Access Management Inventory

> **Entity:** TARGET
> **Purpose:** Identity and access management baseline for M&A technical due diligence
> **Coverage:** Workforce identity, customer identity, privileged access, access governance

---

## 1) IAM Architecture Summary

| Component | Solution | Coverage | Annual Cost |
|---|---|---|---:|
| **Workforce IdP** | Okta | 412 employees | $98,000 |
| **Customer IdP** | Auth0 (embedded in platform) | 1,847 enterprise customers | Included in AWS costs |
| **MFA** | Okta Verify | 85% of workforce | Included in Okta |
| **SSO** | Okta SSO | 12 applications | Included in Okta |
| **Privileged Access** | CyberArk (limited) | 15 admin users | $42,000 |
| **Cloud IAM** | AWS IAM + AWS SSO | All 9 AWS accounts | Included in AWS |

**Total IAM Cost:** $140,000/year (Okta + CyberArk)

---

## 2) Workforce Identity (Okta)

### Okta Deployment Details

| Component | Configuration | Notes |
|---|---|---|
| **Okta edition** | Workforce Identity (Enterprise) | 412 licensed users |
| **MFA methods** | Okta Verify, SMS, Voice | Okta Verify is primary |
| **MFA enforcement** | Required for admin/engineering, optional for business users | **Gap:** 15% of users opt out |
| **SSO integrations** | 12 apps (see table below) | Limited SSO adoption |
| **Lifecycle mgmt** | BambooHR integration (auto-provisioning) | Deprovisioning automated |
| **Password policy** | 12 char min, complexity required, 90-day rotation (admins only) | Business users: no rotation |
| **Session timeout** | 8 hours (web), 30 days (mobile) | No adaptive authentication |

### Okta SSO-Enabled Applications

| Application | SSO Type | MFA Required | Provisioning | Deprovisioning |
|---|---|---|---|---|
| AWS (all accounts) | SAML | ✅ Yes | ✅ Automatic | ✅ Automatic |
| Google Workspace | SAML | ✅ Yes | ✅ Automatic | ✅ Automatic |
| GitHub | SAML | ✅ Yes | ✅ Automatic | ✅ Automatic |
| Salesforce | SAML | ❌ No | ⚠️ Manual | ⚠️ Manual |
| Slack | SAML | ❌ No | ✅ Automatic | ✅ Automatic |
| Datadog | SAML | ❌ No | ⚠️ Manual | ⚠️ Manual |
| PagerDuty | SAML | ✅ Yes | ✅ Automatic | ✅ Automatic |
| NetSuite | SAML | ❌ No | ⚠️ Manual | ⚠️ Manual |
| BambooHR | SAML | ❌ No | N/A (HR source) | N/A |
| Jira | SAML | ❌ No | ✅ Automatic | ✅ Automatic |
| Confluence | SAML | ❌ No | ✅ Automatic | ✅ Automatic |
| Zoom | SAML | ❌ No | ⚠️ Manual | ⚠️ Manual |

**Gap:** Only 50% of apps have automated provisioning/deprovisioning. Manual processes create orphaned account risk.

---

## 3) MFA Coverage Analysis

| User Segment | Total Users | MFA Enabled | MFA Coverage | Notes |
|---|---:|---:|---:|---|
| **Executives** | 8 | 8 | 100% | Required |
| **Engineering** | 92 | 92 | 100% | Required |
| **IT/Security** | 17 | 17 | 100% | Required |
| **Sales** | 87 | 68 | 78% | Optional (19 opt-outs) |
| **Marketing** | 42 | 32 | 76% | Optional (10 opt-outs) |
| **Finance** | 28 | 25 | 89% | Optional (3 opt-outs) |
| **HR** | 12 | 12 | 100% | Required (access to PII) |
| **Customer Success** | 98 | 72 | 73% | Optional (26 opt-outs) |
| **Other** | 28 | 24 | 86% | Varies |
| **TOTAL** | **412** | **350** | **85%** | **62 users without MFA** |

**Risk:** 62 users (15%) not using MFA, primarily in sales/marketing/CS. Credential compromise risk.

---

## 4) Customer Identity (Auth0)

### Auth0 Configuration

| Component | Configuration | Notes |
|---|---|---|
| **Auth0 tenant** | Production (cloudserve.auth0.com) | Single tenant for all environments |
| **Authentication methods** | Username/password, SSO (SAML/OIDC), social login | Customer choice |
| **MFA for end customers** | ✅ Available (optional for customers to enable) | 35% of customers enable MFA |
| **Passwordless** | ❌ Not enabled | Potential future capability |
| **User database** | Auth0 database (not custom DB) | 1.8M end-user accounts |
| **Session management** | JWT tokens, 24-hour expiration | Refresh tokens enabled |

### Customer SSO Integrations

| Integration Type | Count | Notes |
|---|---:|---|
| **SAML integrations** | 287 | Enterprise customers with own IdP |
| **OIDC integrations** | 54 | Modern SSO customers |
| **Social login** | Disabled | Not offered to enterprise customers |

**Technical Debt:** Auth0 embedded in platform; migration to alternative IdP (e.g., buyer's Azure AD B2C) would be complex.

---

## 5) Privileged Access Management (PAM)

### CyberArk Deployment (Limited)

| Component | Status | Notes |
|---|---|---|
| **Deployment scope** | 15 users (IT admins, SREs, security team) | **Gap:** Not all privileged users covered |
| **Covered systems** | Production AWS accounts, production databases | Dev/staging not covered |
| **Session recording** | ✅ Enabled | For AWS Console, SSH sessions |
| **Password vaulting** | ✅ Enabled | Database passwords, API keys |
| **Password rotation** | ⚠️ Partial | Automated for AWS, manual for databases |
| **Privileged elevation** | ⚠️ Limited | Just-in-time access not implemented |

### Privileged User Inventory

| Role | Count | PAM Coverage | Notes |
|---|---:|---|---|
| **CTO / VP Engineering** | 2 | ✅ Yes | Full admin access |
| **SRE Lead** | 1 | ✅ Yes | Infrastructure admin |
| **Senior SREs** | 6 | ✅ Yes | Infrastructure access |
| **Security Engineers** | 5 | ✅ Yes | Security tool admin |
| **Database Admins** | 3 | ✅ Yes | DB admin access |
| **DevOps Engineers** | 8 | ❌ No | **Gap:** Deploy access without PAM |
| **Platform Engineers** | 18 | ❌ No | **Gap:** Some have admin rights without PAM |

**Gap:** 26 users with privileged access NOT covered by PAM. Risk of unaudited admin activity.

---

## 6) AWS IAM Structure

### AWS SSO (Identity Center) Configuration

| Component | Status | Notes |
|---|---|---|
| **AWS SSO enabled** | ✅ Yes | Centralized access to all 9 accounts |
| **Identity source** | Okta (external IdP) | SAML federation |
| **Permission sets** | 12 predefined permission sets | Based on role/team |
| **MFA required** | ✅ Yes (via Okta) | Enforced at Okta layer |

### AWS IAM Permission Sets

| Permission Set | Description | User Count | Accounts |
|---|---|---:|---|
| **AdministratorAccess** | Full admin rights | 8 | All accounts |
| **PowerUserAccess** | Admin without IAM changes | 15 | Prod, shared services |
| **DeveloperAccess** | Deploy + read-only infra | 45 | All accounts |
| **ReadOnlyAccess** | View-only | 22 | All accounts |
| **SREAccess** | Infrastructure admin | 12 | Prod, shared services |
| **SecurityAuditor** | Security tools + read-only | 5 | All accounts |
| **DataEngineerAccess** | Data services admin | 6 | Data account |
| **SandboxFullAccess** | Full access (sandboxes only) | 35 | Sandbox accounts only |

### AWS IAM Users (Non-SSO)

| Account Type | Count | Purpose | Gap |
|---|---:|---|---|
| **Service accounts** | 24 | CI/CD, automation, monitoring | ✅ Managed via Terraform |
| **Legacy IAM users** | 8 | **Gap:** Should be migrated to SSO | ⚠️ Technical debt |
| **Root accounts** | 9 | One per AWS account (emergency only) | ✅ MFA enabled, keys stored in CyberArk |

**Gap:** 8 legacy IAM users still exist (should be using SSO). Risk of ungoverned access.

---

## 7) Access Governance & Reviews

### Access Review Process

| Review Type | Frequency | Owner | Last Review | Status |
|---|---|---|---|---|
| **Okta user access** | Quarterly | IT Ops | 2 months ago | ✅ On track |
| **AWS IAM access** | Quarterly | Security team | 4 months ago | ⚠️ Overdue |
| **GitHub team access** | Quarterly | Engineering managers | 3 months ago | ✅ On track |
| **Database access** | Quarterly | Database admins | **8 months ago** | 🔴 Overdue |
| **Privileged access (PAM)** | Monthly | Security team | 1 month ago | ✅ On track |

**Gap:** AWS and database access reviews are overdue. Risk of privilege creep and orphaned accounts.

### Orphaned Account Detection

| System | Last Scan | Orphaned Accounts Found | Remediated |
|---|---|---:|---|
| **Okta** | 2 months ago | 3 | ✅ All deprovisioned |
| **AWS IAM** | 4 months ago | 8 (legacy users) | ⚠️ 0 (not remediated) |
| **GitHub** | 3 months ago | 2 | ✅ All removed |
| **Salesforce** | 6 months ago | 5 | ⚠️ 2 still active |
| **NetSuite** | **Never scanned** | Unknown | N/A |

**Gap:** No automated orphaned account detection. Manual reviews miss accounts in apps without SSO.

---

## 8) Role-Based Access Control (RBAC)

### Defined Roles

| Role | Description | User Count | Systems | Notes |
|---|---|---:|---|---|
| **Employee** | Standard business user | 412 | Okta, Google Workspace, Slack | Default role |
| **Engineer** | Software developer | 92 | + GitHub, AWS (dev), Datadog | Code commit rights |
| **SRE** | Infrastructure engineer | 12 | + AWS (prod), Kubernetes, PAM | Infrastructure admin |
| **Security Engineer** | Security specialist | 5 | + Security tools, AWS (all), PAM | Security admin |
| **IT Admin** | IT operations | 8 | + Okta admin, all SaaS apps | User management |
| **Manager** | People manager | 48 | + BambooHR, performance tools | Team data access |
| **Finance** | Finance team | 28 | + NetSuite, Bill.com, Expensify | Financial data access |
| **Executive** | C-level / VP | 8 | + All systems (read-only + approvals) | Strategic visibility |

**Gap:** RBAC defined but not consistently enforced across all systems. Some apps use manual group assignments.

---

## 9) Identity Lifecycle Management

### Onboarding Process

| Step | Automation | Average Time | Gap |
|---|---|---|---|
| **HR entry (BambooHR)** | Manual (HR creates user) | Day -3 (before start) | N/A |
| **Okta account creation** | ✅ Automated (BambooHR trigger) | Day -2 | ✅ Good |
| **Core app provisioning** | ✅ Automated (Okta workflows) | Day -2 | ✅ Good |
| **AWS access provisioning** | ⚠️ Semi-automated (manager request + IT approval) | Day 1-3 | ⚠️ Delay risk |
| **GitHub team assignment** | ⚠️ Manual (eng manager) | Day 1-5 | ⚠️ Delay |
| **Equipment provisioning** | ⚠️ Manual (IT ships laptop) | Day -5 to Day 1 | ⚠️ Sometimes late |

### Offboarding Process

| Step | Automation | Average Time | Gap |
|---|---|---|---|
| **HR termination (BambooHR)** | Manual (HR updates status) | Day 0 (termination day) | N/A |
| **Okta account deactivation** | ✅ Automated (BambooHR trigger) | Within 1 hour | ✅ Good |
| **Core app deprovisioning** | ✅ Automated (Okta workflows) | Within 1 hour | ✅ Good |
| **AWS access revocation** | ✅ Automated (SSO tied to Okta) | Within 1 hour | ✅ Good |
| **Manual app revocation** | ⚠️ Manual (IT checklist) | Day 0-3 | ⚠️ Risk of missed apps |
| **Equipment return** | ⚠️ Manual (IT tracks) | Week 1-4 | ⚠️ Tracking issues |

**Gap:** Apps without SSO/auto-deprovisioning (Salesforce, Datadog, NetSuite) require manual revocation. Risk of delayed access removal.

---

## 10) Password Management

### Password Policies

| System | Min Length | Complexity | Rotation | Lockout | Notes |
|---|---:|---|---|---|---|
| **Okta** | 12 chars | ✅ Required | 90 days (admins), none (users) | 5 attempts | Industry standard |
| **AWS root accounts** | 16 chars | ✅ Required | 90 days | N/A | Stored in CyberArk |
| **Database accounts** | 16 chars | ✅ Required | 90 days | N/A | Stored in CyberArk |
| **Service accounts** | 32 chars | ✅ Required | Never (API keys) | N/A | Secrets Manager |

### Password Manager

| Tool | Purpose | Users | Notes |
|---|---|---:|---|
| **1Password** | Employee password manager | 412 | Company-wide deployment |
| **CyberArk** | Privileged credential vault | 15 | Admin/root passwords |
| **AWS Secrets Manager** | App secrets & API keys | N/A | Automated rotation |

---

## 11) Third-Party Identity Risks

| Third Party | Access Type | User Count | MFA | Last Review | Risk |
|---|---|---:|---|---|---|
| **CGI (MSP)** | VPN + limited AWS | 4 | ❌ No | 6 months ago | 🟠 MEDIUM (no MFA) |
| **Offshore contractors (QA)** | GitHub, AWS (dev), Jira | 8 | ✅ Yes | 3 months ago | 🟡 LOW |
| **Security auditors** | Read-only AWS, Okta logs | 2 | ✅ Yes | 1 month ago | 🟢 LOW |
| **SOC 2 auditor** | Vanta, Okta logs, AWS | 2 | ✅ Yes | 2 months ago | 🟢 LOW |

**Gap:** MSP (CGI) does not use MFA for VPN access. Risk of credential compromise.

---

## 12) IAM Gaps & Risks

| Gap/Risk | Description | Severity | Estimated Fix Cost |
|---|---|---|---|
| **MFA coverage gap** | 15% of workforce (62 users) not using MFA | 🟠 MEDIUM | $10K-20K (enforce policy + training) |
| **PAM coverage gap** | 26 privileged users not in CyberArk | 🟠 MEDIUM | $50K-100K (expand PAM deployment) |
| **Manual provisioning apps** | 6 apps require manual user provisioning | 🟡 LOW | $30K-50K (Okta workflow automation) |
| **Orphaned account risk** | No automated detection for non-SSO apps | 🟡 LOW | $20K-40K (IGA tool or scripts) |
| **AWS legacy IAM users** | 8 legacy IAM users should use SSO | 🟡 LOW | $5K-10K (migration project) |
| **MSP no MFA** | Third-party MSP access without MFA | 🟠 MEDIUM | $0 (policy enforcement) |
| **Access review delays** | AWS/DB reviews overdue (4-8 months) | 🟡 LOW | $0 (process adherence) |

---

## 13) Integration with Buyer IAM Standards

| Target State | Buyer State | Gap/Integration Need |
|---|---|---|
| **Workforce IdP:** Okta | **Workforce IdP:** Azure AD | Migrate users to Azure AD or federate |
| **Customer IdP:** Auth0 | **Customer IdP:** Azure AD B2C | Complex migration (embedded in platform) |
| **PAM:** CyberArk (limited) | **PAM:** CyberArk (full deployment) | Expand coverage to match buyer standards |
| **MFA:** 85% coverage | **MFA:** 100% required | Enforce MFA for all users |
| **Cloud IAM:** AWS IAM | **Cloud IAM:** Azure AD + AWS IAM | Hybrid identity strategy |

**Migration Complexity:** Auth0 → Azure AD B2C migration is HIGH complexity (6-12 months, $200K-400K).

---

## 14) IAM Technical Debt

| Issue | Description | Impact | Estimated Fix Cost |
|---|---|---|---|
| **Auth0 vendor lock-in** | Customer auth deeply integrated | Platform migration complexity | $200K-400K (re-platform) |
| **Manual app provisioning** | 50% of apps not auto-provisioned | Orphaned account risk | $30K-50K (automation) |
| **No IGA tool** | Manual access reviews, no certifications | Compliance risk | $100K-200K (SailPoint/Saviynt) |
| **Incomplete RBAC** | RBAC defined but not enforced | Privilege creep | $50K-100K (RBAC enforcement) |

---

## 15) Documentation Gaps & VDR Requests

| Gap | Information Needed | Purpose |
|---|---|---|
| **Okta configuration export** | Full Okta tenant configuration | Understand policies, rules, integrations |
| **AWS IAM policies** | All IAM roles, policies, permission sets | Security review, least privilege validation |
| **Privileged user list** | Complete list of users with admin rights | Validate PAM coverage |
| **Access review reports** | Last 4 quarters of access review results | Assess governance maturity |
| **Third-party access list** | All vendors/contractors with system access | Third-party risk assessment |

---

## 16) Consistency Validation

| Fact | Value | Matches Document 1? |
|---|---:|---|
| Workforce IdP | Okta | ✅ Yes |
| Customer IdP | Auth0 | ✅ Yes |
| MFA coverage | 85% | ✅ Yes |
| SSO integrations | 12 apps | ✅ Yes |
| Privileged access tool | CyberArk (15 users) | ✅ Yes |

---

**END OF DOCUMENT 5**
