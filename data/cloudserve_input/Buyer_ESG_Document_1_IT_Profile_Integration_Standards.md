# Enterprise Solutions Group (ESG) — Buyer Document 1: IT Profile & Integration Standards

> **Entity:** BUYER
> **Purpose:** Buyer IT landscape and integration standards for M&A due diligence planning
> **Company:** Enterprise Solutions Group (ESG) - Acquirer

---

## 1) Company Overview

| Item | Value |
|---|---|
| **Company** | Enterprise Solutions Group (ESG) |
| **Industry** | Enterprise software (ERP, CRM, HCM, vertical solutions) |
| **Annual revenue** | **$12.4B** (85% recurring, 15% services) |
| **Employees** | **24,500** (global) |
| **IT headcount** | **2,100** (includes corporate IT + product engineering) |
| **Headquarters** | Redmond, WA |
| **Global presence** | 45 countries, 120 offices |
| **Cloud strategy** | Azure-first, multi-cloud secondary (AWS for acquisitions) |

---

## 2) M&A Integration Philosophy

| Principle | Description |
|---|---|
| **"Run then transform"** | Stabilize operations Day 1-100, then integrate Day 100+ |
| **Platform autonomy** | Acquired platforms maintain technical autonomy for 12-18 months |
| **Corporate standards** | Security, identity, compliance enforced immediately |
| **Tool consolidation** | Gradual migration to ESG standard tools (12-24 month timeline) |
| **Data governance** | Acquired data migrates to ESG data lake (phased approach) |

---

## 3) ESG IT Budget & Scale

| Metric | Value |
|---|---:|
| **Annual IT budget** | **$2.1B** (17% of revenue) |
| **Cloud spend (Azure)** | **$650M/year** |
| **Cloud spend (AWS)** | **$180M/year** (legacy acquisitions) |
| **Cloud spend (GCP)** | **$45M/year** (limited use) |
| **SaaS tooling** | **$285M/year** (enterprise-wide) |
| **Data center footprint** | **6 core DCs** (Tier 3+), phasing out by 2027 |
| **Personnel costs** | **$1.2B/year** (IT + engineering) |

---

## 4) ESG Technology Standards

### Cloud Strategy

| Standard | Technology | Notes |
|---|---|---|
| **Primary cloud** | Microsoft Azure | 70% of workloads |
| **Secondary cloud** | AWS | 25% of workloads (acquisitions) |
| **Tertiary cloud** | GCP | 5% of workloads (analytics only) |
| **Cloud-first mandate** | All new workloads must be cloud-native | No new on-prem deployments |
| **Data center exit** | All DCs closed by 2027 | Migration to Azure in progress |

### Infrastructure Standards

| Standard | Technology | Required? |
|---|---|---|
| **Container orchestration** | Azure Kubernetes Service (AKS) | Preferred; EKS accepted for acquisitions |
| **Infrastructure as code** | Terraform (primary), ARM templates (Azure-native) | Required for all infra |
| **Observability** | Splunk Enterprise (on-prem + cloud) | Required; Datadog allowed temporarily |
| **Networking** | Azure Virtual WAN, ExpressRoute | Required for Azure; Direct Connect for AWS |

---

## 5) ESG Application Standards

### Enterprise Applications (Corporate IT)

| Category | Standard Application | Replacement Policy for Acquisitions |
|---|---|---|
| **ERP** | SAP S/4HANA (cloud) | Replace within 24 months |
| **CRM** | Microsoft Dynamics 365 Sales | Replace within 18 months |
| **HCM** | Workday HCM | Replace within 12 months |
| **Finance** | SAP S/4HANA + BlackLine | Replace within 24 months |
| **Collaboration** | Microsoft 365 E5 | Replace within 6 months |
| **Communication** | Microsoft Teams | Replace within 6 months |
| **Email** | Exchange Online (M365) | Replace within 6 months |

**Note:** Acquired companies must migrate to ESG standard apps per timeline above.

---

## 6) ESG Security & Compliance Standards

### Security Requirements (Non-Negotiable)

| Requirement | Standard | Enforcement |
|---|---|---|
| **Endpoint security** | CrowdStrike Falcon (EDR) | Day 1 deployment required |
| **SIEM** | Splunk Enterprise Security | Integration within 90 days |
| **CSPM** | Microsoft Defender for Cloud | Integration within 90 days |
| **SAST/DAST** | Checkmarx (SAST), Veracode (DAST) | Integration within 180 days |
| **Vulnerability management** | Qualys | Integration within 90 days |
| **MFA** | Required for all users | 100% coverage within 30 days |
| **PAM** | CyberArk (enterprise deployment) | Admin access within 60 days |

### Compliance Certifications (Required)

| Framework | Status at ESG | Requirement for Acquisitions |
|---|---|---|
| **SOC 2 Type II** | ✅ Certified (enterprise-wide) | Maintain or achieve within 6 months |
| **ISO 27001** | ✅ Certified (enterprise-wide) | Achieve within 12 months if not certified |
| **GDPR** | ✅ Compliant (audited annually) | Compliance audit within 90 days |
| **CCPA** | ✅ Compliant | Compliance audit within 90 days |
| **PCI-DSS** | ✅ Level 1 (where applicable) | If handling card data, certify within 12 months |
| **HIPAA** | ✅ Compliant (healthcare products) | If handling PHI, certify within 12 months |
| **FedRAMP** | ⚠️ In progress (Moderate) | Not required for acquisitions unless gov't customers |

---

## 7) ESG Identity & Access Management Standards

| Standard | Technology | Requirement |
|---|---|---|
| **Workforce IdP** | Azure AD (Entra ID) | Migrate within 12 months |
| **Customer IdP** | Azure AD B2C | Migrate within 18-24 months (platform-dependent) |
| **MFA** | Azure AD MFA (Authenticator app) | 100% coverage within 30 days |
| **SSO** | Azure AD SSO | All apps must support SSO |
| **PAM** | CyberArk Privileged Access Manager | All admin access within 60 days |
| **RBAC** | Azure AD role-based access control | Enforce within 90 days |
| **Conditional access** | Azure AD Conditional Access policies | Enforce within 90 days |

**Migration Timeline:** Okta → Azure AD migration typically takes 6-12 months (phased approach).

---

## 8) ESG Data Governance Standards

| Standard | Technology/Policy | Requirement |
|---|---|---|
| **Data lake** | Azure Data Lake Gen2 | Acquired data migrates within 12-18 months |
| **Data warehouse** | Synapse Analytics (Azure) | Snowflake allowed temporarily; migrate within 24 months |
| **BI platform** | Power BI (Microsoft) | Migrate from Looker/Tableau within 12 months |
| **Data classification** | Microsoft Purview | Enforce within 6 months |
| **DLP** | Microsoft Purview DLP | Enforce within 6 months |
| **Data residency** | Region-specific (GDPR/CCPA compliance) | EU data must remain in EU; validate within 90 days |

---

## 9) ESG Network & Connectivity Standards

| Standard | Technology | Requirement |
|---|---|---|
| **VPN** | Azure VPN Gateway | Replace non-Azure VPN within 12 months |
| **SD-WAN** | Azure Virtual WAN | Required for office connectivity |
| **Internet egress** | Azure Firewall + Zscaler (cloud proxy) | Integration within 90 days |
| **DDoS protection** | Azure DDoS Protection Standard | Required for all Azure resources |
| **Private connectivity** | ExpressRoute (Azure), Direct Connect (AWS) | Required for production workloads |

---

## 10) ESG Integration Milestones (Typical Timeline)

| Milestone | Timeline | Description |
|---|---|---|
| **Day 1 Close** | Deal close | Target operations continue as-is |
| **Day 1-30** | Month 1 | Security baseline (MFA, EDR, SIEM integration, vulnerability scanning) |
| **Day 30-90** | Months 2-3 | Identity integration (Azure AD federation), network connectivity |
| **Day 90-180** | Months 4-6 | Compliance certifications (ISO if needed), email/collaboration migration (M365) |
| **Day 180-365** | Months 7-12 | ERP/CRM migration planning, IdP migration (Okta → Azure AD) |
| **Day 365+** | Year 2+ | Platform modernization, cloud consolidation (AWS → Azure if needed) |

---

## 11) ESG M&A Integration Budget (Typical Allocation)

| Category | Typical Budget Range | Notes |
|---|---:|---|
| **Security remediation** | $200K - $1M | Depends on gaps (ISO, SIEM, PAM, etc.) |
| **Identity migration** | $300K - $800K | Okta → Azure AD, Auth0 → Azure AD B2C |
| **Infrastructure integration** | $500K - $2M | Networking, cloud account structure, monitoring |
| **Application migration** | $1M - $5M | ERP, CRM, collaboration tools |
| **Compliance & audit** | $150K - $500K | ISO, GDPR, SOC 2 audits |
| **Data migration** | $500K - $2M | Data lake, data warehouse, BI tools |
| **Personnel transition** | $200K - $1M | Retention bonuses, training |
| **TOTAL (Typical)** | **$2.85M - $12.3M** | Varies by acquisition size/complexity |

**For CloudServe acquisition:** Estimated $4M - $8M integration budget (mid-range complexity).

---

## 12) ESG Approved Vendor List (Key Categories)

### Cloud & Infrastructure

| Category | Approved Vendors | Notes |
|---|---|---|
| **Cloud (primary)** | Microsoft Azure | Strongly preferred |
| **Cloud (secondary)** | AWS | Accepted for acquisitions; eventual migration to Azure |
| **CDN** | Azure Front Door, Akamai | Fastly accepted temporarily |
| **Monitoring** | Splunk, Azure Monitor | Datadog allowed for 12 months |

### Security

| Category | Approved Vendors | Notes |
|---|---|---|
| **Endpoint security** | CrowdStrike Falcon | Mandatory |
| **SIEM** | Splunk Enterprise Security | Mandatory |
| **CSPM** | Microsoft Defender for Cloud | Mandatory for Azure; Wiz accepted for AWS |
| **PAM** | CyberArk | Mandatory |
| **Vulnerability scanning** | Qualys | Mandatory |

### Identity

| Category | Approved Vendors | Notes |
|---|---|---|
| **Workforce IdP** | Azure AD | Mandatory (Okta accepted for 12 months during migration) |
| **Customer IdP** | Azure AD B2C | Mandatory for new implementations |
| **MFA** | Azure AD MFA | Mandatory |

### Applications

| Category | Approved Vendors | Notes |
|---|---|---|
| **ERP** | SAP S/4HANA | Mandatory (NetSuite accepted temporarily) |
| **CRM** | Microsoft Dynamics 365 | Mandatory (Salesforce accepted temporarily) |
| **HCM** | Workday | Mandatory (BambooHR/Rippling must migrate) |
| **Collaboration** | Microsoft 365 | Mandatory (Google Workspace must migrate within 6 months) |

**Vendor Rationalization:** Non-approved vendors must have migration plan within 90 days of close.

---

## 13) ESG Integration Support Resources

| Resource | Description | Availability |
|---|---|---|
| **M&A Integration Team** | Dedicated team of 25 FTEs | Assigned to each acquisition |
| **Cloud migration CoE** | Azure/AWS migration specialists | Available for infrastructure migration |
| **Security integration team** | SIEM, PAM, CSPM integration experts | Day 1 security baseline support |
| **Identity migration team** | Azure AD migration specialists | Okta → Azure AD migration support |
| **Compliance team** | ISO, GDPR, SOC 2 audit support | Compliance gap closure assistance |

---

## 14) ESG Technical Due Diligence Focus Areas

| Focus Area | Key Questions | Acceptable Gaps | Red Flags |
|---|---|---|---|
| **Security** | SOC 2? ISO? SIEM? PAM? | SOC 2 only (ISO can be achieved post-close) | No SOC 2, data breaches in last 2 years |
| **Cloud** | Cloud-native? Multi-region? DR tested? | Single region OK (can expand) | On-prem only, no cloud strategy |
| **Identity** | MFA coverage? SSO? Privileged access? | 80%+ MFA OK (can enforce) | <50% MFA, no privileged access controls |
| **Compliance** | GDPR? CCPA? Data residency? | Self-assessed OK (can audit) | Non-compliant + customer contracts requiring compliance |
| **Architecture** | Multi-tenant? APIs? Scalability? | Monolith OK if decomposable | Unmaintainable tech stack, no documentation |

---

## 15) CloudServe Acquisition: Preliminary Gap Assessment

| Domain | Target State | ESG Standard | Gap Severity | Integration Effort |
|---|---|---|---|---|
| **Cloud** | AWS (100%) | Azure (primary) | 🟡 LOW-MEDIUM | Maintain AWS; eventual Azure migration (optional) |
| **IdP** | Okta | Azure AD | 🟠 MEDIUM | 6-12 month migration |
| **Customer IdP** | Auth0 | Azure AD B2C | 🔴 HIGH | 18-24 month migration (complex) |
| **SIEM** | None (Datadog) | Splunk | 🟠 MEDIUM | 90-day integration |
| **Compliance** | SOC 2 only | SOC 2 + ISO | 🟠 MEDIUM | 12-month ISO certification |
| **Collaboration** | Google Workspace | M365 | 🟡 LOW | 6-month migration |
| **ERP** | NetSuite | SAP S/4HANA | 🔴 HIGH | 24-month migration (complex) |
| **CRM** | Salesforce | Dynamics 365 | 🟠 MEDIUM | 18-month migration |

**Overall Integration Complexity:** MEDIUM-HIGH (primarily due to Auth0 and ERP migration complexity)

---

## 16) ESG Success Metrics for Acquisitions

| Metric | Target | Measurement |
|---|---|---|
| **Security baseline completion** | 100% within 30 days | MFA, EDR, SIEM integration |
| **Compliance certifications** | SOC 2 maintained, ISO within 12 months | Audit completion |
| **Identity integration** | Azure AD federation within 90 days | SSO to ESG apps |
| **Zero security incidents** | 0 breaches in first 12 months | SOC monitoring |
| **Cost synergies (vendor consolidation)** | 10-15% of target SaaS spend | Contract consolidation |
| **Employee retention** | 90%+ retention of key technical staff (first 12 months) | HR tracking |

---

**END OF BUYER DOCUMENT 1**
