# CloudServe Technologies — Document 2: Application Inventory & Platform Architecture

> **Entity:** TARGET
> **Purpose:** Complete application portfolio for M&A technical due diligence
> **Coverage:** Core SaaS platform (8 microservices) + Internal business apps (18) + Dev tools (12)

---

## 1) Application Portfolio Summary

| Metric | Value |
|---|---:|
| **Total applications** | **38** |
| **Core platform components** | 8 (microservices) |
| **Business applications** | 18 (SaaS subscriptions) |
| **Development tools** | 12 (DevOps, monitoring, testing) |
| **Annual app cost** | **$2,331,500** |
| **Hosting model** | 100% Cloud (AWS + SaaS) |

---

## 2) Application Cost Breakdown by Category

| Category | Count | Annual Cost |
|---|---:|---:|
| Infrastructure | 9 | $150,000 (8 internal + Datadog) |
| CRM | 3 | $428,000 |
| ERP | 1 | $180,000 |
| Finance | 4 | $200,000 |
| HCM | 2 | $144,000 |
| Collaboration | 3 | $168,000 |
| DevOps | 9 | $170,000 |
| Productivity | 3 | $36,000 |
| Security | 5 | $598,000 |
| Database | 1 | $285,000 |
| BI/Analytics | 1 | $32,500 |

---

## 3) Full Application Inventory (38 Applications)

### Column Definitions
- **Application:** Application name
- **Vendor:** Vendor or "Internal" for custom-built
- **Category:** Business function category
- **Version:** Current version or "Evergreen" for SaaS
- **Hosting:** Cloud, SaaS, or Internal (AWS-hosted)
- **Users:** Active user count or deployment scope
- **Annual Cost:** Annual licensing/subscription cost
- **Criticality:** CRITICAL, HIGH, MEDIUM, LOW
- **Entity:** Target or Buyer
- **Contract End:** Contract expiration date (YYYY-MM format)
- **Notes:** Integration dependencies, gaps, risks

---

| Application | Vendor | Category | Version | Hosting | Users | Annual Cost | Criticality | Entity | Contract End | Notes |
|---|---|---|---|---|---:|---:|---|---|---|---|
| **CORE SAAS PLATFORM COMPONENTS** |
| API Gateway Service | Internal | infrastructure | v3.2 | AWS (EKS) | — | $0 | CRITICAL | target | — | Kong API Gateway; customer-facing |
| Authentication Service | Internal | infrastructure | v2.8 | AWS (EKS) | — | $0 | CRITICAL | target | — | Auth0 integration; multi-tenant |
| Customer Data Service | Internal | infrastructure | v4.1 | AWS (EKS) | — | $0 | CRITICAL | target | — | PostgreSQL backend; PII storage |
| Messaging Service | Internal | infrastructure | v2.5 | AWS (EKS) | — | $0 | CRITICAL | target | — | SQS + SNS; event-driven arch |
| Analytics Engine | Internal | infrastructure | v1.9 | AWS (EKS) | — | $0 | HIGH | target | — | Customer usage analytics |
| Workflow Orchestration | Internal | infrastructure | v3.0 | AWS (EKS) | — | $0 | HIGH | target | — | Temporal.io based |
| Notification Service | Internal | infrastructure | v2.2 | AWS (Lambda) | — | $0 | MEDIUM | target | — | Email/SMS/push notifications |
| Billing & Metering | Internal | infrastructure | v1.7 | AWS (EKS) | — | $0 | HIGH | target | — | Usage-based billing; integrates Stripe |
| **CRM & SALES** |
| Salesforce Sales Cloud | Salesforce | crm | Enterprise | SaaS | 87 | $245,000 | HIGH | target | 2025-10 | Primary CRM; custom objects |
| Outreach.io | Outreach | crm | Evergreen | SaaS | 42 | $126,000 | MEDIUM | target |2025-06 | Sales automation |
| Gong | Gong | crm | Evergreen | SaaS | 35 | $57,000 | LOW | target |2025-12 | Call recording & analysis |
| **FINANCE & ERP** |
| NetSuite | Oracle | erp | 2024.1 | SaaS | 28 | $180,000 | CRITICAL | target |2026-03 | Financial system of record |
| Stripe | Stripe | finance | API | SaaS | — | $0 | CRITICAL | target |Evergreen | Revenue processing; usage-based fees |
| Bill.com | Bill.com | finance | Evergreen | SaaS | 12 | $24,000 | MEDIUM | target |2025-08 | AP workflow |
| Expensify | Expensify | finance | Evergreen | SaaS | 412 | $18,000 | LOW | target |2025-04 | Employee expenses |
| Adaptive Insights | Workday | finance | 2024 | SaaS | 8 | $158,000 | HIGH | target |2025-11 | Financial planning |
| **HR & COLLABORATION** |
| BambooHR | BambooHR | hcm | Evergreen | SaaS | 412 | $48,000 | HIGH | target |2025-07 | HR system of record |
| Rippling | Rippling | hcm | Evergreen | SaaS | 412 | $96,000 | HIGH | target |2026-01 | Payroll processing |
| Google Workspace | Google | collaboration | Enterprise | SaaS | 412 | $82,000 | CRITICAL | target |2025-09 | Email, docs, drive |
| Slack | Slack | collaboration | Enterprise Grid | SaaS | 412 | $72,000 | HIGH | target |2025-05 | Primary communication |
| Zoom | Zoom | collaboration | Business | SaaS | 412 | $14,000 | MEDIUM | target |2025-03 | Video meetings |
| **DEVELOPMENT & DEVOPS** |
| GitHub Enterprise | GitHub | devops | Enterprise Cloud | SaaS | 92 | $23,000 | CRITICAL | target |2026-02 | Source code + CI/CD |
| Datadog | Datadog | infrastructure | Enterprise | SaaS | 67 | $150,000 | CRITICAL | target |2025-03 | APM, logs, metrics |
| PagerDuty | PagerDuty | devops | Enterprise | SaaS | 45 | $18,000 | HIGH | target |2025-05 | On-call & alerting |
| Terraform Cloud | HashiCorp | devops | Team | SaaS | 18 | $48,000 | HIGH | target |2025-08 | Infrastructure as code |
| ArgoCD | Argo Project | devops | v2.9 | AWS (EKS) | — | $0 | HIGH | target |— | Kubernetes deployments |
| Snyk | Snyk | security | Enterprise | SaaS | 92 | $78,000 | MEDIUM | target |2025-06 | Dependency scanning |
| Postman | Postman | devops | Enterprise | SaaS | 65 | $18,000 | MEDIUM | target |2025-10 | API development |
| Jira Software | Atlassian | productivity | Premium | SaaS | 124 | $12,000 | HIGH | target |2025-04 | Agile project mgmt |
| Confluence | Atlassian | productivity | Premium | SaaS | 124 | $6,000 | MEDIUM | target |2025-04 | Wiki & knowledge base |
| Figma | Figma | productivity | Professional | SaaS | 12 | $18,000 | LOW | target |2025-07 | Product design |
| LaunchDarkly | LaunchDarkly | devops | Enterprise | SaaS | 92 | $45,000 | MEDIUM | target |2025-09 | Feature management |
| Sentry | Sentry | devops | Business | SaaS | 92 | $18,000 | MEDIUM | target |2025-11 | Application errors |
| **SECURITY & COMPLIANCE** |
| Okta | Okta | security | Workforce Identity | SaaS | 412 | $98,000 | CRITICAL | target |2025-06 | Primary IdP |
| CrowdStrike Falcon | CrowdStrike | security | Evergreen | SaaS | 412 | $87,000 | CRITICAL | target |2025-11 | EDR platform |
| Wiz | Wiz | security | Enterprise | SaaS | 15 | $125,000 | HIGH | target |2025-02 | CSPM + CWPP; contract ending soon |
| Vanta | Vanta | security | Business | SaaS | 8 | $210,000 | HIGH | target |2025-08 | SOC 2 compliance mgmt |
| **DATA & ANALYTICS** |
| Snowflake | Snowflake | database | Enterprise | SaaS | 24 | $285,000 | HIGH | target |2026-01 | Analytics data warehouse |
| Looker | Google | bi_analytics | Enterprise | SaaS | 48 | $32,500 | MEDIUM | target |2025-09 | Business intelligence |

---

## 4) Application Risk Flags

| Application | Risk | Description | Impact |
|---|---|---|---|
| Wiz | **Contract expiring soon** | Contract ends 2025-02 (2 months) | Cloud security visibility gap if not renewed |
| Datadog | **Contract expiring soon** | Contract ends 2025-03 (3 months) | Loss of observability; operational blindness |
| Zoom | **Contract expiring soon** | Contract ends 2025-03 (3 months) | Low impact (can switch to Google Meet) |
| Expensify | **Contract expiring soon** | Contract ends 2025-04 (4 months) | Low impact (manual AP workaround available) |
| Salesforce | **High cost** | $245K/year for 87 users | Potential overlap with buyer CRM |
| Datadog | **High cost** | $150K/year; cost per host increasing | Potential consolidation with buyer monitoring |
| Snowflake | **High cost** | $285K/year; storage costs growing | Data warehouse optimization opportunity |

---

## 5) Platform Architecture Notes

### Multi-Tenant SaaS Architecture

| Component | Description | Data Isolation Model |
|---|---|---|
| **Tenant isolation** | Logical separation via tenant_id column | Row-level security in PostgreSQL |
| **Data residency** | All data in us-east-1 (US customers) | **GAP:** No EU data residency for GDPR |
| **Customer databases** | Shared database schema (not database-per-tenant) | Performance risk at scale |
| **API rate limiting** | Per-tenant rate limits in API Gateway | Kong rate limiting plugin |

### Integration Points

| Integration | Description | Risk |
|---|---|---|
| **Auth0 (embedded)** | Customer user authentication | Vendor dependency; migration complexity |
| **Stripe** | Payment processing & webhooks | Financial data dependency |
| **Twilio** | SMS notifications | Service reliability dependency |
| **SendGrid** | Email delivery | Deliverability dependency |
| **Segment** | Customer analytics | Data pipeline dependency |

### Technical Debt Identified

| Issue | Description | Impact | Estimated Fix Cost |
|---|---|---|---|
| **No EU data residency** | All data in US region | GDPR compliance risk | $250K-500K (new region setup) |
| **Shared database schema** | Single database for all tenants | Scale/performance limits | $500K-1M (re-architecture) |
| **Incomplete API documentation** | ~60% of endpoints documented | Customer integration friction | $50K-100K (documentation sprint) |
| **Auth0 vendor lock-in** | Deep integration with Auth0 | Migration complexity if buyer uses different IdP | $200K-400K (re-platform auth) |

---

## 6) Application Disposition Recommendations (Preliminary)

| Application | Day 1 Disposition | Day 100 Target | Rationale |
|---|---|---|---|
| Core Platform (8) | **Keep** | Keep | Revenue-generating; strategic asset |
| Salesforce | **Evaluate** | Replace or Consolidate | Potential overlap with buyer CRM |
| NetSuite | **Keep** | Evaluate | Financial SOR; complex migration |
| GitHub | **Keep** | Evaluate | Buyer uses GitLab; potential consolidation |
| Datadog | **Keep** | Replace | Buyer uses Splunk; eventual migration |
| Okta | **Keep** | Replace | Buyer uses Azure AD; phased migration |
| CrowdStrike | **Keep** | Align | Validate against buyer endpoint security |
| Wiz | **Renew** | Align | Contract ending; align with buyer CSPM |
| Google Workspace | **Keep** | Migrate | Buyer uses Microsoft 365; 12-month migration |
| Snowflake | **Keep** | Evaluate | High cost; assess buyer data warehouse |

---

## 7) Documentation Gaps & VDR Requests

| Gap | Information Needed | Purpose |
|---|---|---|
| **API integration list** | Complete list of customer-facing API integrations | Assess carve-out complexity |
| **Auth0 configuration** | Tenant configuration, custom rules, MFA settings | Plan IdP migration |
| **Stripe integration details** | Webhook configurations, subscription logic | Understand revenue dependencies |
| **Vendor contract details** | Full contracts for top 10 vendors by spend | Validate termination clauses, liability |
| **Platform SLAs** | Customer SLA commitments (uptime, support) | Assess operational risk |
| **Data retention policies** | Customer data retention & deletion workflows | GDPR/CCPA compliance validation |

---

## 8) Cost Optimization Opportunities

| Opportunity | Description | Estimated Annual Savings |
|---|---|---:|
| **Salesforce license optimization** | Right-size licenses; 87 users at $2,800/user/year | $40K-60K |
| **Datadog cost optimization** | Reduce log retention, optimize host counts | $60K-90K |
| **Snowflake storage optimization** | Archive old data, optimize queries | $50K-80K |
| **SaaS license cleanup** | Remove inactive users across all apps | $30K-50K |

---

## 9) Consistency Validation

| Fact | Value | Matches Document 1? |
|---|---:|---|
| Total applications | 38 | ✅ Yes |
| Annual app cost | $2,331,500 | ✅ Yes |
| Core platform components | 8 | ✅ Yes |
| Business applications | 18 | ✅ Yes |
| Development tools | 12 | ✅ Yes |

---

**END OF DOCUMENT 2**
