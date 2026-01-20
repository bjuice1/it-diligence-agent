# IT Due Diligence Activity Inventory

**Total Activities: 395**
**Phases Complete: 6 of 10**
**Last Updated: January 2026**

---

## Summary by Phase

| Phase | Description | Activities | Cost Range (1,500 users) |
|-------|-------------|------------|--------------------------|
| 1 | Core Infrastructure | 70 | $2.8M - $8.1M |
| 2 | Network & Security | 67 | $2.4M - $6.3M |
| 3 | Applications | 94 | $9.8M - $32.9M |
| 4 | Data & Migration | 61 | $4.6M - $13.3M |
| 5 | Licensing | 53 | $2.8M - $8.9M |
| 6 | Integration (Buyer) | 50 | $2.2M - $6.4M |
| **Total** | | **395** | **$24.5M - $75.8M** |

---

## Phase 1: Core Infrastructure (70 Activities)

### Identity Workstream (25 Activities)

| ID | Activity | Cost Model | TSA |
|----|----------|------------|-----|
| IDN-001 | Identity architecture assessment | Base: $25K-$50K | No |
| IDN-002 | Directory services inventory | Base: $15K-$35K | No |
| IDN-003 | SSO application mapping | Per app: $500-$1,500 | No |
| IDN-004 | MFA requirements analysis | Base: $10K-$25K | No |
| IDN-005 | Identity architecture design | Base: $40K-$100K | No |
| IDN-010 | Azure AD tenant provisioning | Base: $30K-$75K | No |
| IDN-011 | Okta org provisioning | Base: $35K-$85K | No |
| IDN-012 | On-premises AD forest standup | Base: $50K-$120K | No |
| IDN-013 | Hybrid identity configuration | Base: $25K-$60K | No |
| IDN-014 | Identity governance setup | Base: $20K-$50K | No |
| IDN-020 | User account migration | Per user: $15-$40 | Yes (3-6 mo) |
| IDN-021 | Group and distribution list migration | Base + per group: $50-$150 | Yes (2-4 mo) |
| IDN-022 | Service account migration | Per account: $500-$2,000 | Yes (3-6 mo) |
| IDN-023 | Password sync/reset coordination | Per user: $2-$8 | Yes (1-2 mo) |
| IDN-030 | SAML/OIDC SSO reconfiguration - Standard | Per app: $2K-$5K | Yes (2-4 mo) |
| IDN-031 | SAML/OIDC SSO reconfiguration - Complex | Per app: $5K-$15K | Yes (3-6 mo) |
| IDN-032 | Legacy application authentication | Per app: $8K-$25K | Yes (3-6 mo) |
| IDN-033 | MFA enrollment campaign | Per user: $5-$15 | No |
| IDN-034 | Conditional access policy implementation | Base: $20K-$50K | No |
| IDN-040 | Identity parallel running | Base: $30K-$75K | Yes (2-4 mo) |
| IDN-041 | Authentication cutover | Base: $25K-$60K | No |
| IDN-042 | Post-migration identity support | Base: $20K-$50K | No |
| IDN-043 | Identity decommissioning | Base: $15K-$35K | No |

### Email Workstream (22 Activities)

| ID | Activity | Cost Model | TSA |
|----|----------|------------|-----|
| EML-001 | Email environment assessment | Base: $20K-$45K | No |
| EML-002 | Mailbox inventory and sizing | Base: $10K-$25K | No |
| EML-003 | Shared resource mapping | Base: $8K-$20K | No |
| EML-004 | Mail flow analysis | Base: $12K-$30K | No |
| EML-005 | Email security configuration review | Base: $10K-$25K | No |
| EML-006 | Email platform design | Base: $25K-$60K | No |
| EML-010 | M365 tenant email configuration | Base: $25K-$60K | No |
| EML-011 | Google Workspace provisioning | Base: $25K-$55K | No |
| EML-012 | Domain configuration | Base + per domain: $1K-$3K | No |
| EML-013 | Mail routing configuration | Base: $15K-$40K | No |
| EML-014 | Email security policy configuration | Base: $15K-$40K | No |
| EML-015 | Email archiving and retention setup | Base: $20K-$50K | No |
| EML-020 | Mailbox migration - Staged | Per user: $20-$50 | Yes (2-4 mo) |
| EML-021 | Mailbox migration - Cutover | Per user: $15-$35 | Yes (1-2 mo) |
| EML-022 | Archive mailbox migration | Per user: $10-$30 | Yes (2-4 mo) |
| EML-023 | Public folder migration | Base: $20K-$60K | Yes (2-4 mo) |
| EML-024 | Shared mailbox migration | Per mailbox: $200-$500 | Yes (2-3 mo) |
| EML-025 | Calendar and contact migration | Per user: $5-$15 | Yes (1-2 mo) |
| EML-026 | Resource mailbox migration | Per resource: $150-$400 | Yes (1-2 mo) |
| EML-030 | Cross-tenant free/busy configuration | Base: $15K-$35K | Yes (3-6 mo) |
| EML-031 | Mail forwarding configuration | Base: $8K-$20K | Yes (3-6 mo) |
| EML-032 | Address book synchronization | Base: $10K-$30K | Yes (3-6 mo) |
| EML-040 | MX record cutover | Base: $10K-$25K | No |
| EML-041 | Email client reconfiguration | Per user: $5-$20 | No |
| EML-042 | Post-migration email support | Base: $15K-$40K | No |

### Infrastructure Workstream (23 Activities)

| ID | Activity | Cost Model | TSA |
|----|----------|------------|-----|
| INF-001 | Infrastructure discovery and inventory | Base: $25K-$60K | No |
| INF-002 | Application-to-infrastructure mapping | Base: $20K-$50K | No |
| INF-003 | Storage assessment and planning | Base: $15K-$40K | No |
| INF-004 | Backup and DR assessment | Base: $15K-$35K | No |
| INF-005 | Target infrastructure architecture design | Base: $40K-$100K | No |
| INF-010 | Cloud landing zone deployment | Base: $75K-$200K | No |
| INF-011 | On-premises datacenter buildout | Base: $150K-$400K | No |
| INF-012 | Network connectivity setup | Base: $30K-$80K | No |
| INF-013 | Security baseline implementation | Base: $25K-$60K | No |
| INF-014 | Monitoring and alerting setup | Base: $20K-$50K | No |
| INF-015 | Backup infrastructure deployment | Base: $30K-$80K | No |
| INF-016 | Disaster recovery setup | Base: $50K-$150K | No |
| INF-020 | VM migration - Lift and shift | Per VM: $500-$1,500 | Yes (3-6 mo) |
| INF-021 | VM migration - Replatform | Per VM: $1K-$3K | Yes (3-6 mo) |
| INF-022 | Physical server migration | Per server: $2K-$6K | Yes (3-6 mo) |
| INF-023 | Database migration | Per database: $3K-$15K | Yes (3-6 mo) |
| INF-024 | Storage migration | Per TB: $200-$600 | Yes (3-6 mo) |
| INF-025 | Application migration | Per app: $5K-$25K | Yes (3-6 mo) |
| INF-030 | Operations runbook development | Base: $20K-$50K | No |
| INF-031 | Operations team training | Base: $15K-$40K | No |
| INF-032 | Support transition | Base: $15K-$35K | No |
| INF-033 | Legacy infrastructure decommissioning | Per server: $200-$500 | No |

---

## Phase 2: Network & Security (67 Activities)

### Network Workstream (25 Activities)

| ID | Activity | Cost Model | TSA |
|----|----------|------------|-----|
| NET-001 | Network architecture assessment | Base: $30K-$75K | No |
| NET-002 | WAN circuit inventory | Base: $15K-$35K | No |
| NET-003 | IP addressing and DNS analysis | Base: $20K-$45K | No |
| NET-004 | Firewall rule analysis | Base + per site: $3K-$8K | No |
| NET-005 | Network target architecture design | Base: $50K-$125K | No |
| NET-010 | MPLS circuit provisioning | Per site: $8K-$20K | Yes (3-6 mo) |
| NET-011 | SD-WAN deployment | Base + per site: $3K-$8K | Yes (2-4 mo) |
| NET-012 | Internet circuit provisioning | Per site: $2K-$6K | Yes (2-4 mo) |
| NET-013 | WAN circuit migration/cutover | Per site: $2K-$5K | Yes (1-3 mo) |
| NET-020 | LAN switch configuration | Per site: $5K-$15K | No |
| NET-021 | VLAN segmentation implementation | Per site: $3K-$8K | No |
| NET-022 | Wireless infrastructure deployment | Per site: $8K-$25K | No |
| NET-023 | Network access control (NAC) implementation | Base: $35K-$90K | No |
| NET-030 | Firewall deployment | Base + per site: $5K-$15K | No |
| NET-031 | Firewall rule migration | Base: $25K-$75K | Yes (2-4 mo) |
| NET-032 | IDS/IPS implementation | Base: $30K-$80K | No |
| NET-033 | Network segmentation enforcement | Base: $50K-$150K | No |
| NET-040 | DNS infrastructure deployment | Base: $20K-$50K | No |
| NET-041 | DNS zone separation | Base + per domain: $2K-$5K | Yes (2-4 mo) |
| NET-042 | DHCP infrastructure deployment | Base + per site: $1K-$3K | No |
| NET-043 | NTP/time services configuration | Base: $5K-$15K | No |
| NET-044 | Certificate services deployment | Base: $30K-$80K | No |
| NET-050 | Network monitoring deployment | Base: $20K-$50K | No |
| NET-051 | Network documentation and runbooks | Base: $15K-$35K | No |

### Security Workstream (28 Activities)

| ID | Activity | Cost Model | TSA |
|----|----------|------------|-----|
| SEC-001 | Security architecture assessment | Base: $35K-$85K | No |
| SEC-002 | Security tool inventory | Base: $15K-$35K | No |
| SEC-003 | Compliance requirements mapping | Base: $25K-$60K | No |
| SEC-004 | Security architecture design | Base: $50K-$120K | No |
| SEC-010 | EDR platform deployment | Base + per endpoint: $10-$30 | Yes (2-4 mo) |
| SEC-011 | Antivirus/antimalware migration | Per endpoint: $5-$15 | Yes (2-4 mo) |
| SEC-012 | Device encryption enforcement | Base + per endpoint: $5-$15 | No |
| SEC-013 | Mobile device management deployment | Base + per device: $10-$25 | Yes (2-4 mo) |
| SEC-014 | Endpoint hardening implementation | Base: $30K-$70K | No |
| SEC-020 | SIEM platform deployment | Base: $75K-$200K | Yes (3-6 mo) |
| SEC-021 | Log aggregation configuration | Base: $25K-$60K | No |
| SEC-022 | Security alert tuning | Base: $20K-$50K | No |
| SEC-023 | SOC procedures development | Base: $25K-$60K | No |
| SEC-024 | Security orchestration (SOAR) deployment | Base: $50K-$150K | No |
| SEC-030 | Vulnerability scanner deployment | Base: $30K-$75K | No |
| SEC-031 | Baseline vulnerability assessment | Base: $20K-$50K | No |
| SEC-032 | Vulnerability remediation program | Base: $25K-$60K | No |
| SEC-033 | Patch management implementation | Base: $30K-$70K | No |
| SEC-040 | Privileged access management (PAM) deployment | Base: $75K-$200K | Yes (3-6 mo) |
| SEC-041 | Service account vault implementation | Base + per account: $100-$300 | Yes (2-4 mo) |
| SEC-042 | Access review implementation | Base: $25K-$60K | No |
| SEC-043 | Identity governance platform deployment | Base: $100K-$300K | No |
| SEC-050 | Data loss prevention deployment | Base: $50K-$150K | Yes (3-6 mo) |
| SEC-051 | Data classification implementation | Base: $30K-$75K | No |
| SEC-052 | Encryption key management | Base: $40K-$100K | No |
| SEC-060 | Security gap remediation assessment | Base: $25K-$60K | No |
| SEC-061 | Security quick wins implementation | Base: $20K-$50K | No |
| SEC-062 | Penetration testing | Base: $40K-$100K | No |

### Perimeter Workstream (14 Activities)

| ID | Activity | Cost Model | TSA |
|----|----------|------------|-----|
| PER-001 | Perimeter security assessment | Base: $25K-$55K | No |
| PER-002 | Perimeter architecture design | Base: $35K-$80K | No |
| PER-010 | VPN infrastructure deployment | Base: $30K-$80K | Yes (2-4 mo) |
| PER-011 | VPN user migration | Per user: $5-$15 | Yes (2-4 mo) |
| PER-012 | Site-to-site VPN configuration | Per site: $3K-$8K | Yes (2-4 mo) |
| PER-013 | Zero trust network access (ZTNA) deployment | Base + per user: $10-$30 | Yes (2-4 mo) |
| PER-020 | Secure web gateway deployment | Base: $35K-$90K | Yes (2-4 mo) |
| PER-021 | Web proxy configuration | Base: $15K-$40K | No |
| PER-022 | Cloud access security broker (CASB) deployment | Base: $50K-$150K | Yes (3-6 mo) |
| PER-023 | DNS security deployment | Base: $15K-$40K | No |
| PER-030 | Email security gateway deployment | Base + per user: $3-$10 | Yes (2-4 mo) |
| PER-031 | Email authentication configuration | Base + per domain: $1K-$3K | No |
| PER-032 | Anti-phishing protection deployment | Base: $20K-$50K | No |
| PER-040 | SASE platform deployment | Base + per user: $20-$60 | Yes (3-6 mo) |
| PER-041 | Perimeter service migration | Base: $40K-$100K | Yes (2-4 mo) |

---

## Phase 3: Applications (94 Activities)

### ERP Workstream (21 Activities)

| ID | Activity | Cost Model | TSA |
|----|----------|------------|-----|
| ERP-001 | ERP landscape assessment | Base: $50K-$125K | No |
| ERP-002 | ERP data segmentation analysis | Base: $40K-$100K | No |
| ERP-003 | ERP integration mapping | Base + per integration: $1K-$3K | No |
| ERP-004 | ERP customization inventory | Base: $30K-$80K | No |
| ERP-005 | ERP license entitlement analysis | Base: $20K-$50K | No |
| ERP-006 | ERP separation strategy design | Base: $75K-$200K | No |
| ERP-010 | SAP system copy and carve | Base: $200K-$500K | Yes (6-12 mo) |
| ERP-011 | SAP new instance implementation | Base: $500K-$2M | Yes (12-24 mo) |
| ERP-012 | SAP data migration | Base: $100K-$300K | Yes (6-12 mo) |
| ERP-013 | SAP integration rebuild | Base + per integration: $5K-$20K | Yes (6-12 mo) |
| ERP-014 | SAP custom development migration | Base: $75K-$250K | Yes (6-12 mo) |
| ERP-020 | Oracle EBS/Cloud instance separation | Base: $200K-$600K | Yes (6-12 mo) |
| ERP-021 | Oracle data extraction and migration | Base: $100K-$300K | Yes (6-12 mo) |
| ERP-030 | NetSuite account separation | Base: $75K-$200K | Yes (3-6 mo) |
| ERP-031 | Dynamics 365 F&O tenant separation | Base: $100K-$300K | Yes (6-12 mo) |
| ERP-032 | Dynamics GP/NAV migration | Base: $50K-$150K | Yes (3-6 mo) |
| ERP-040 | ERP functional testing | Base: $50K-$150K | No |
| ERP-041 | ERP integration testing | Base: $40K-$100K | No |
| ERP-042 | ERP performance testing | Base: $30K-$80K | No |
| ERP-043 | ERP user acceptance testing | Base: $25K-$75K | No |
| ERP-044 | ERP cutover planning and execution | Base: $50K-$150K | No |
| ERP-045 | ERP hypercare support | Base: $40K-$120K | No |

### CRM Workstream (15 Activities)

| ID | Activity | Cost Model | TSA |
|----|----------|------------|-----|
| CRM-001 | CRM landscape assessment | Base: $25K-$60K | No |
| CRM-002 | CRM data ownership analysis | Base: $20K-$50K | No |
| CRM-003 | CRM separation strategy design | Base: $30K-$75K | No |
| CRM-010 | Salesforce org provisioning | Base: $40K-$100K | No |
| CRM-011 | Salesforce configuration migration | Base: $50K-$150K | Yes (3-6 mo) |
| CRM-012 | Salesforce data migration | Base + per record: $0.05-$0.20 | Yes (3-6 mo) |
| CRM-013 | Salesforce integration rebuild | Base + per integration: $3K-$12K | Yes (3-6 mo) |
| CRM-014 | Salesforce AppExchange app migration | Per app: $2K-$8K | No |
| CRM-020 | Dynamics 365 CE environment provisioning | Base: $35K-$90K | No |
| CRM-021 | Dynamics CRM solution migration | Base: $40K-$120K | Yes (3-6 mo) |
| CRM-022 | Dynamics CRM data migration | Base: $30K-$80K | Yes (3-6 mo) |
| CRM-030 | HubSpot account separation | Base: $20K-$50K | Yes (2-4 mo) |
| CRM-031 | Zoho CRM separation | Base: $15K-$40K | Yes (2-4 mo) |
| CRM-040 | CRM testing and validation | Base: $25K-$60K | No |
| CRM-041 | CRM user training | Base + per user: $50-$150 | No |
| CRM-042 | CRM cutover and hypercare | Base: $20K-$50K | No |

### HR/HCM Workstream (17 Activities)

| ID | Activity | Cost Model | TSA |
|----|----------|------------|-----|
| HCM-001 | HR/HCM landscape assessment | Base: $30K-$75K | No |
| HCM-002 | HR data separation analysis | Base: $20K-$50K | No |
| HCM-003 | Payroll and benefits analysis | Base: $25K-$60K | No |
| HCM-004 | HR/HCM separation strategy design | Base: $35K-$85K | No |
| HCM-010 | Workday tenant provisioning | Base: $100K-$300K | Yes (6-12 mo) |
| HCM-011 | Workday configuration and customization | Base: $150K-$400K | Yes (6-12 mo) |
| HCM-012 | Workday data migration | Base + per employee: $100-$300 | Yes (6-12 mo) |
| HCM-020 | ADP implementation | Base + per employee: $30-$100 | Yes (3-6 mo) |
| HCM-021 | ADP data migration | Base + per employee: $50-$150 | Yes (3-6 mo) |
| HCM-030 | UKG Pro implementation | Base + per employee: $40-$120 | Yes (6-9 mo) |
| HCM-031 | UKG time and attendance setup | Base: $30K-$80K | Yes (3-6 mo) |
| HCM-040 | SAP SuccessFactors tenant provisioning | Base: $100K-$250K | Yes (6-12 mo) |
| HCM-041 | SuccessFactors Employee Central migration | Base + per employee: $75-$200 | Yes (6-12 mo) |
| HCM-050 | Payroll provider setup | Base + per employee: $20-$60 | Yes (3-6 mo) |
| HCM-051 | Benefits administration setup | Base + per employee: $15-$50 | Yes (3-6 mo) |
| HCM-052 | 401(k)/retirement plan setup | Base: $20K-$50K | Yes (3-6 mo) |
| HCM-060 | HR/HCM parallel payroll testing | Base: $20K-$50K | Yes (2-3 mo) |
| HCM-061 | HR/HCM cutover and go-live | Base: $25K-$60K | No |
| HCM-062 | HR/HCM hypercare support | Base: $20K-$50K | No |

### Custom Applications Workstream (19 Activities)

| ID | Activity | Cost Model | TSA |
|----|----------|------------|-----|
| APP-001 | Custom application portfolio assessment | Base: $30K-$75K | No |
| APP-002 | Application disposition analysis | Base + per app: $500-$2K | No |
| APP-003 | Application separation strategy | Base: $40K-$100K | No |
| APP-010 | Simple application migration | Per app: $5K-$15K | Yes (2-4 mo) |
| APP-011 | Moderate application migration | Per app: $15K-$50K | Yes (3-6 mo) |
| APP-012 | Complex application migration | Per app: $50K-$150K | Yes (6-12 mo) |
| APP-013 | Legacy application modernization | Per app: $75K-$300K | Yes (6-18 mo) |
| APP-020 | Application retirement - Simple | Per app: $3K-$10K | No |
| APP-021 | Application retirement - Complex | Per app: $10K-$35K | Yes (2-4 mo) |
| APP-030 | Integration platform standup | Base: $50K-$150K | No |
| APP-031 | API gateway deployment | Base: $30K-$80K | No |
| APP-032 | Integration rebuild - Per integration | Per integration: $3K-$15K | Yes (3-6 mo) |
| APP-040 | Application testing coordination | Base: $25K-$75K | No |
| APP-041 | End-to-end process testing | Base: $30K-$80K | No |
| APP-050 | Application technology assessment | Base + per app: $2K-$6K | No |
| APP-051 | Application refactoring | Per app: $25K-$100K | Yes (3-6 mo) |

### SaaS Workstream (22 Activities)

| ID | Activity | Cost Model | TSA |
|----|----------|------------|-----|
| SAS-001 | SaaS discovery and inventory | Base: $20K-$50K | No |
| SAS-002 | SaaS contract analysis | Base + per contract: $500-$1,500 | No |
| SAS-003 | SaaS data classification | Base + per app: $500-$2K | No |
| SAS-004 | SaaS separation strategy | Base: $20K-$50K | No |
| SAS-010 | SaaS account provisioning - Simple | Per app: $1K-$3K | Yes (1-3 mo) |
| SAS-011 | SaaS account provisioning - Complex | Per app: $5K-$20K | Yes (2-4 mo) |
| SAS-012 | SaaS user provisioning | Per user: $5-$20 + per app: $500-$2K | Yes (2-4 mo) |
| SAS-013 | SaaS data migration | Per app: $3K-$15K | Yes (2-4 mo) |
| SAS-014 | SaaS SSO reconfiguration | Per app: $1K-$4K | Yes (2-4 mo) |
| SAS-020 | SaaS contract assignment | Per contract: $1K-$4K | No |
| SAS-021 | SaaS new contract negotiation | Per contract: $2K-$8K | No |
| SAS-022 | SaaS contract termination | Per contract: $500-$2K | No |
| SAS-030 | SaaS data export | Per app: $1K-$5K | Yes (1-3 mo) |
| SAS-031 | SaaS historical data archival | Per app: $2K-$8K | No |
| SAS-032 | SaaS data deletion verification | Per app: $500-$2K | No |
| SAS-040 | Collaboration tools migration (Slack/Teams) | Base + per user: $10-$30 | Yes (3-6 mo) |
| SAS-041 | Project management tools migration | Base + per user: $15-$40 | Yes (2-4 mo) |
| SAS-042 | Document management migration | Base + per user: $10-$25 | Yes (3-6 mo) |
| SAS-043 | Business intelligence tools migration | Base: $30K-$100K | Yes (3-6 mo) |
| SAS-050 | SaaS license true-up | Base + per app: $1K-$4K | No |
| SAS-051 | SaaS license optimization | Base: $15K-$40K | No |

---

## Phase 4: Data & Migration (61 Activities)

### Database Workstream (22 Activities)

| ID | Activity | Cost Model | TSA |
|----|----------|------------|-----|
| DAT-001 | Database landscape assessment | Base: $30K-$75K | No |
| DAT-002 | Database schema analysis | Base + per database: $1.5K-$4K | No |
| DAT-003 | Database dependency mapping | Base + per database: $1K-$3K | No |
| DAT-004 | Data classification and sensitivity analysis | Base + per database: $2K-$5K | No |
| DAT-005 | Database separation strategy design | Base: $40K-$100K | No |
| DAT-010 | SQL Server database migration - Simple | Per database: $3K-$8K | Yes (2-4 mo) |
| DAT-011 | SQL Server database migration - Complex | Per database: $10K-$30K | Yes (3-6 mo) |
| DAT-012 | SQL Server Always On/clustering migration | Per database: $15K-$40K | Yes (3-6 mo) |
| DAT-013 | SQL Server to Azure SQL migration | Per database: $8K-$25K | Yes (3-6 mo) |
| DAT-020 | Oracle database migration - Simple | Per database: $5K-$15K | Yes (3-6 mo) |
| DAT-021 | Oracle database migration - Complex | Per database: $20K-$60K | Yes (6-12 mo) |
| DAT-022 | Oracle to PostgreSQL migration | Per database: $25K-$75K | Yes (6-12 mo) |
| DAT-023 | Oracle to AWS RDS migration | Per database: $15K-$45K | Yes (3-6 mo) |
| DAT-030 | MySQL/MariaDB database migration | Per database: $2K-$8K | Yes (2-4 mo) |
| DAT-031 | PostgreSQL database migration | Per database: $2K-$8K | Yes (2-4 mo) |
| DAT-032 | NoSQL database migration (MongoDB, Cosmos) | Per database: $5K-$15K | Yes (2-4 mo) |
| DAT-040 | Data warehouse separation assessment | Base: $30K-$80K | No |
| DAT-041 | Data warehouse migration | Base: $100K-$300K | Yes (6-12 mo) |
| DAT-042 | Cloud data platform migration (Snowflake/Databricks) | Base + per TB: $500-$1,500 | Yes (6-12 mo) |
| DAT-050 | Database migration validation | Base + per database: $1.5K-$4K | No |
| DAT-051 | Database cutover execution | Base + per database: $2K-$6K | No |

### File Data Workstream (17 Activities)

| ID | Activity | Cost Model | TSA |
|----|----------|------------|-----|
| FIL-001 | File data landscape assessment | Base: $20K-$50K | No |
| FIL-002 | File data ownership analysis | Base: $15K-$40K | No |
| FIL-003 | File data classification | Base + per TB: $500-$1,500 | No |
| FIL-004 | File migration strategy design | Base: $25K-$60K | No |
| FIL-010 | Windows file share migration | Base + per TB: $200-$600 | Yes (2-4 mo) |
| FIL-011 | NAS/SAN file migration | Base + per TB: $150-$400 | Yes (2-4 mo) |
| FIL-012 | File share to cloud migration (Azure Files/FSx) | Base + per TB: $300-$800 | Yes (3-6 mo) |
| FIL-020 | SharePoint site inventory and planning | Base + per site: $500-$1,500 | No |
| FIL-021 | SharePoint Online migration - Standard sites | Per site: $1.5K-$4K | Yes (3-6 mo) |
| FIL-022 | SharePoint Online migration - Complex sites | Per site: $4K-$12K | Yes (3-6 mo) |
| FIL-023 | SharePoint on-premises to Online migration | Base + per site: $2K-$6K | Yes (3-6 mo) |
| FIL-030 | OneDrive migration | Base + per user: $10-$30 | Yes (2-4 mo) |
| FIL-031 | Box/Dropbox migration | Base + per user: $15-$40 | Yes (2-4 mo) |
| FIL-032 | Google Drive migration | Base + per user: $15-$40 | Yes (2-4 mo) |
| FIL-040 | Permission mapping and remediation | Base + per TB: $300-$800 | No |
| FIL-041 | Shortcut and link remediation | Base + per user: $5-$15 | No |

### Archival Workstream (13 Activities)

| ID | Activity | Cost Model | TSA |
|----|----------|------------|-----|
| ARC-001 | Data retention requirements analysis | Base: $20K-$50K | No |
| ARC-002 | Historical data analysis | Base: $15K-$40K | No |
| ARC-003 | Archive strategy design | Base: $25K-$60K | No |
| ARC-010 | Archive platform deployment | Base: $30K-$80K | No |
| ARC-011 | Email archive migration | Base + per user: $20-$60 | Yes (3-6 mo) |
| ARC-012 | File archive migration | Base + per TB: $100-$300 | Yes (2-4 mo) |
| ARC-013 | Database archive/historical data extraction | Base + per database: $3K-$10K | Yes (3-6 mo) |
| ARC-020 | Legal hold transfer | Base: $20K-$50K | Yes (2-4 mo) |
| ARC-021 | eDiscovery platform setup | Base: $30K-$80K | No |
| ARC-022 | Retention policy implementation | Base: $15K-$40K | No |
| ARC-030 | Legacy data cleanup | Base + per TB: $200-$500 | No |
| ARC-031 | Data deduplication | Base + per TB: $100-$300 | No |

### Migration Tooling Workstream (11 Activities)

| ID | Activity | Cost Model | TSA |
|----|----------|------------|-----|
| MIG-001 | Migration tooling assessment | Base: $15K-$40K | No |
| MIG-002 | Migration automation strategy | Base: $20K-$50K | No |
| MIG-010 | SharePoint migration tool deployment | Base: $15K-$40K | No |
| MIG-011 | Database migration tool deployment | Base: $15K-$40K | No |
| MIG-012 | File migration tool deployment | Base: $10K-$30K | No |
| MIG-013 | Cloud migration tool deployment (Azure Migrate/AWS MGN) | Base: $20K-$50K | No |
| MIG-020 | Migration wave planning | Base: $25K-$60K | No |
| MIG-021 | Migration runbook development | Base: $20K-$50K | No |
| MIG-022 | Migration monitoring and reporting | Base: $15K-$40K | No |
| MIG-030 | Migration validation framework | Base: $20K-$50K | No |
| MIG-031 | Data quality remediation | Base: $25K-$75K | No |
| MIG-032 | Post-migration validation | Base: $20K-$50K | No |

---

## Phase 5: Licensing (53 Activities)

### Microsoft Licensing Workstream (16 Activities)

| ID | Activity | Cost Model | TSA |
|----|----------|------------|-----|
| LIC-MS-001 | Microsoft licensing assessment | Base: $25K-$60K | No |
| LIC-MS-002 | Microsoft EA/enrollment analysis | Base: $15K-$40K | No |
| LIC-MS-003 | Microsoft license deployment analysis | Base + per user: $5-$15 | No |
| LIC-MS-010 | M365 license strategy design | Base: $20K-$50K | No |
| LIC-MS-011 | M365 license procurement | Per user: $150-$400 (annual) | No |
| LIC-MS-012 | M365 license assignment and activation | Base + per user: $5-$15 | No |
| LIC-MS-020 | Azure subscription strategy | Base: $15K-$40K | No |
| LIC-MS-021 | Azure subscription transfer/creation | Base: $20K-$50K | Yes (2-4 mo) |
| LIC-MS-022 | Azure reserved instance transfer | Base: $10K-$30K | No |
| LIC-MS-023 | Azure Hybrid Benefit analysis | Base: $10K-$25K | No |
| LIC-MS-030 | Windows Server licensing assessment | Base: $15K-$40K | No |
| LIC-MS-031 | Windows Server license procurement | Per server: $500-$2K | No |
| LIC-MS-032 | CAL procurement and assignment | Per user: $30-$100 | No |
| LIC-MS-040 | EA negotiation support | Base: $30K-$80K | No |
| LIC-MS-041 | EA partial transfer execution | Base: $20K-$50K | Yes (3-6 mo) |
| LIC-MS-042 | CSP/NCE migration | Base + per user: $10-$30 | No |

### Database Licensing Workstream (11 Activities)

| ID | Activity | Cost Model | TSA |
|----|----------|------------|-----|
| LIC-DB-001 | Oracle licensing assessment | Base: $40K-$100K | No |
| LIC-DB-002 | Oracle ULA analysis | Base: $25K-$60K | No |
| LIC-DB-003 | Oracle processor/NUP calculation | Base + per database: $2K-$5K | No |
| LIC-DB-004 | Oracle license negotiation support | Base: $50K-$150K | Yes (6-12 mo) |
| LIC-DB-005 | Oracle license transfer execution | Base: $25K-$60K | Yes (3-6 mo) |
| LIC-DB-006 | Oracle audit defense preparation | Base: $30K-$80K | No |
| LIC-DB-010 | SQL Server licensing assessment | Base: $20K-$50K | No |
| LIC-DB-011 | SQL Server license procurement | Base + per core: $2K-$8K | No |
| LIC-DB-012 | SQL Server edition optimization | Base + per database: $3K-$10K | No |
| LIC-DB-020 | PostgreSQL/MySQL enterprise support | Base + per database: $2K-$8K | No |
| LIC-DB-021 | MongoDB/NoSQL licensing | Base + per database: $5K-$20K | No |

### Infrastructure Licensing Workstream (9 Activities)

| ID | Activity | Cost Model | TSA |
|----|----------|------------|-----|
| LIC-INF-001 | VMware licensing assessment | Base: $20K-$50K | No |
| LIC-INF-002 | VMware license procurement | Base + per CPU: $2K-$6K | No |
| LIC-INF-003 | VMware to alternative platform assessment | Base: $25K-$60K | No |
| LIC-INF-010 | Backup software licensing assessment | Base: $15K-$40K | No |
| LIC-INF-011 | Backup software license procurement | Base + per VM: $50-$200 | No |
| LIC-INF-020 | Monitoring tools licensing | Base + per server: $100-$500 | No |
| LIC-INF-021 | ITSM/ServiceNow licensing | Base + per user: $50-$200 | No |
| LIC-INF-030 | Network equipment licensing | Base + per device: $200-$1K | No |
| LIC-INF-031 | Security tools licensing | Base + per user: $30-$100 + per endpoint: $20-$80 | No |

### Application Licensing Workstream (13 Activities)

| ID | Activity | Cost Model | TSA |
|----|----------|------------|-----|
| LIC-APP-001 | ERP licensing assessment | Base: $30K-$80K | No |
| LIC-APP-002 | SAP license transfer negotiation | Base: $50K-$150K | Yes (6-12 mo) |
| LIC-APP-003 | Oracle ERP licensing | Base: $40K-$120K | Yes (6-12 mo) |
| LIC-APP-004 | Dynamics 365 licensing | Base + per user: $100-$300 | No |
| LIC-APP-010 | Salesforce licensing assessment | Base: $15K-$40K | No |
| LIC-APP-011 | Salesforce license procurement | Base + per user: $150-$400 | No |
| LIC-APP-020 | Specialty software inventory | Base + per app: $500-$2K | No |
| LIC-APP-021 | Specialty software license transfer | Base + per app: $2K-$8K | Yes (2-4 mo) |
| LIC-APP-022 | Specialty software new procurement | Base + per app: $5K-$25K | No |
| LIC-APP-030 | Development tools licensing | Base + per developer: $500-$2K | No |
| LIC-APP-031 | DevOps platform licensing | Base + per user: $20-$50 | No |
| LIC-APP-040 | Parent software agreement analysis | Base: $25K-$60K | No |
| LIC-APP-041 | Volume discount impact analysis | Base: $15K-$40K | No |

### License Compliance Workstream (4 Activities)

| ID | Activity | Cost Model | TSA |
|----|----------|------------|-----|
| LIC-CMP-001 | Software asset management setup | Base: $30K-$80K | No |
| LIC-CMP-002 | License compliance remediation | Base: $25K-$75K | No |
| LIC-CMP-003 | License optimization program | Base: $30K-$80K | No |
| LIC-CMP-004 | License contract consolidation | Base: $20K-$50K | No |

---

## Phase 6: Integration - Buyer Side (50 Activities)

### Integration Planning Workstream (7 Activities)

| ID | Activity | Cost Model | TSA |
|----|----------|------------|-----|
| INT-001 | IT integration assessment | Base: $50K-$125K | No |
| INT-002 | Technology stack comparison | Base: $30K-$75K | No |
| INT-003 | Integration complexity scoring | Base: $20K-$50K | No |
| INT-004 | Synergy identification and validation | Base: $35K-$85K | No |
| INT-005 | Integration strategy design | Base: $50K-$125K | No |
| INT-006 | Integration roadmap development | Base: $30K-$75K | No |
| INT-007 | Integration governance setup | Base: $25K-$60K | No |

### Technology Integration Workstream (18 Activities)

| ID | Activity | Cost Model | TSA |
|----|----------|------------|-----|
| INT-010 | Identity integration assessment | Base: $25K-$60K | No |
| INT-011 | Directory trust/federation setup | Base: $30K-$75K | No (Day 1 Critical) |
| INT-012 | User migration to buyer identity | Base + per user: $20-$50 | No |
| INT-013 | SSO integration for target applications | Base + per app: $2K-$6K | No |
| INT-014 | Legacy identity decommission | Base: $20K-$50K | No |
| INT-020 | Email integration assessment | Base: $20K-$50K | No |
| INT-021 | Cross-tenant mail flow configuration | Base: $15K-$40K | No (Day 1 Critical) |
| INT-022 | Mailbox migration to buyer tenant | Base + per user: $25-$60 | No |
| INT-023 | Email domain consolidation | Base + per domain: $3K-$8K | No |
| INT-030 | Network interconnection | Base + per site: $3K-$10K | No (Day 1 Critical) |
| INT-031 | Workload migration to buyer platform | Base + per VM: $800-$2,500 | No |
| INT-032 | Infrastructure tool consolidation | Base: $30K-$80K | No (Cost Synergy) |
| INT-033 | Target datacenter exit | Base: $25K-$75K | No (Cost Synergy) |
| INT-040 | Application portfolio rationalization | Base + per app: $500-$1,500 | No (Cost Synergy) |
| INT-041 | ERP integration/consolidation | Base: $200K-$750K | No |
| INT-042 | CRM integration/consolidation | Base: $75K-$250K | No |
| INT-043 | Application retirement execution | Base + per app: $5K-$15K | No (Cost Synergy) |
| INT-044 | SaaS account consolidation | Base + per app: $2K-$8K | No (Cost Synergy) |

### Synergy Workstream (8 Activities)

| ID | Activity | Cost Model | TSA |
|----|----------|------------|-----|
| SYN-001 | IT cost synergy tracking setup | Base: $20K-$50K | No |
| SYN-002 | License consolidation execution | Base: $30K-$80K | No (Cost Synergy) |
| SYN-003 | Vendor consolidation execution | Base: $25K-$60K | No (Cost Synergy) |
| SYN-004 | Infrastructure consolidation | Base: $50K-$150K | No (Cost Synergy) |
| SYN-005 | IT organization optimization | Base: $40K-$100K | No (Cost Synergy) |
| SYN-010 | Cross-sell technology enablement | Base: $30K-$80K | No (Revenue Synergy) |
| SYN-011 | Data platform integration | Base: $75K-$200K | No (Capability Synergy) |
| SYN-012 | Technology capability transfer | Base: $40K-$120K | No (Capability Synergy) |

### Day 1 Readiness Workstream (12 Activities)

| ID | Activity | Cost Model | TSA |
|----|----------|------------|-----|
| D1-001 | Day 1 requirements gathering | Base: $20K-$50K | No (Day 1 Critical) |
| D1-002 | Day 1 checklist development | Base: $15K-$35K | No (Day 1 Critical) |
| D1-003 | Day 1 dress rehearsal | Base: $20K-$50K | No (Day 1 Critical) |
| D1-010 | Day 1 network connectivity | Base: $30K-$80K | No (Day 1 Critical) |
| D1-011 | Day 1 communication systems | Base: $15K-$40K | No (Day 1 Critical) |
| D1-020 | Day 1 access provisioning | Base + per user: $10-$30 | No (Day 1 Critical) |
| D1-021 | Day 1 shared services access | Base: $20K-$50K | No (Day 1 Critical) |
| D1-030 | Day 1 support model | Base: $15K-$40K | No (Day 1 Critical) |
| D1-031 | Day 1 war room setup | Base: $10K-$30K | No (Day 1 Critical) |
| D1-032 | Day 1 execution and support | Base: $25K-$75K | No (Day 1 Critical) |
| D1-040 | Post-Day 1 stabilization | Base: $30K-$80K | No |
| D1-041 | Integration transition to BAU | Base: $20K-$50K | No |

### TSA Management Workstream (5 Activities)

| ID | Activity | Cost Model | TSA |
|----|----------|------------|-----|
| TSA-001 | TSA requirements definition | Base: $25K-$60K | No |
| TSA-002 | TSA negotiation support | Base: $30K-$80K | No |
| TSA-003 | TSA governance setup | Base: $20K-$50K | No |
| TSA-004 | TSA exit planning | Base: $25K-$60K | No |
| TSA-005 | TSA exit execution | Base: $40K-$100K | No |

---

## Phases 7-10 (Pending)

| Phase | Description | Status |
|-------|-------------|--------|
| 7 | Operational Run-Rate | Not Started |
| 8 | Compliance & Regulatory | Not Started |
| 9 | Vendor & Contract | Not Started |
| 10 | Validation & Refinement | Not Started |

---

## Cost Model Legend

| Model Type | Description | Example |
|------------|-------------|---------|
| Base | Fixed cost range | Base: $25K-$50K |
| Per user | Scales with user count | Per user: $15-$40 |
| Per app | Scales with application count | Per app: $2K-$8K |
| Per VM | Scales with virtual machine count | Per VM: $500-$1,500 |
| Per server | Scales with physical/logical servers | Per server: $2K-$6K |
| Per database | Scales with database count | Per database: $3K-$15K |
| Per TB | Scales with storage volume | Per TB: $200-$600 |
| Per site | Scales with physical locations | Per site: $5K-$15K |
| Per endpoint | Scales with devices | Per endpoint: $10-$30 |
| Per integration | Scales with integration count | Per integration: $3K-$12K |

## Modifiers

| Complexity | Multiplier |
|------------|------------|
| Simple | 0.7x |
| Moderate | 1.0x |
| Complex | 1.5x |
| Highly Complex | 2.0x |

| Industry | Multiplier |
|----------|------------|
| Standard | 1.0x |
| Financial Services | 1.3x |
| Healthcare | 1.25x |
| Government | 1.4x |
| Retail | 1.1x |
| Manufacturing | 1.15x |

---

*Document Version: 1.0*
*Classification: PwC Internal - Proprietary Knowledge Base*
