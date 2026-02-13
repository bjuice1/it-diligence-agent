# Enterprise Solutions Group (ESG) — Buyer Document 3: Infrastructure & Cloud Standards

> **Entity:** BUYER
> **Purpose:** ESG infrastructure standards and cloud strategy for integration planning

---

## 1) ESG Cloud Strategy

| Component | Standard | Policy |
|---|---|---|
| **Primary cloud** | Microsoft Azure | 70% of workloads; preferred for all new deployments |
| **Secondary cloud** | AWS | 25% of workloads (legacy acquisitions); accepted but not preferred |
| **Tertiary cloud** | GCP | 5% of workloads (analytics only); limited use |
| **Multi-cloud policy** | Azure-first, multi-cloud accepted | Acquisitions can remain on AWS for 12-24 months |
| **Data center exit** | Complete by 2027 | All on-prem workloads migrating to Azure |

---

## 2) ESG Azure Footprint

| Region | Purpose | Workload Types | Spend/Month |
|---|---|---:|---:|
| **East US** | Primary North America | All workload types | $28M |
| **West Europe** | Primary EMEA | All workload types | $18M |
| **Southeast Asia** | Primary APAC | All workload types | $6M |
| **UK South** | GDPR data residency | EU customer data | $4M |
| **Australia East** | APAC data residency | APAC customer data | $2M |

**Total Azure Spend:** $650M/year

---

## 3) ESG AWS Footprint (Legacy Acquisitions)

| Region | Purpose | Spend/Month |
|---|---|---:|
| **us-east-1** | Legacy acquisitions (3 companies) | $8M |
| **eu-west-1** | Legacy acquisitions (EMEA) | $4M |
| **ap-southeast-1** | Legacy acquisitions (APAC) | $3M |

**Total AWS Spend:** $180M/year
**Strategy:** Maintain for existing acquisitions; no new AWS deployments

---

## 4) CloudServe Infrastructure Integration Plan

| CloudServe State | ESG Standard | Integration Approach |
|---|---|---|
| **100% AWS (us-east-1, eu-west-1)** | Azure-first | **Allow AWS for 12-24 months, then evaluate migration** |
| **9 AWS accounts** | Azure subscription structure | Reorganize into ESG account hierarchy (within 90 days) |
| **EKS (Kubernetes)** | AKS (Azure Kubernetes Service) | **Accept EKS; eventual AKS migration (24+ months)** |
| **No on-prem** | Cloud-only | ✅ Aligned with ESG strategy |
| **Direct Connect (1 Gbps)** | ExpressRoute (Azure), Direct Connect (AWS) | Add ExpressRoute for ESG connectivity (within 90 days) |
| **Warm DR (eu-west-1)** | Multi-region active-active | Upgrade DR strategy (12-18 months) |

---

## 5) ESG Infrastructure Standards

| Standard | Technology | Requirement for Acquisitions |
|---|---|---|
| **Container orchestration** | AKS (Azure), EKS (AWS accepted) | Align within 24 months |
| **Infrastructure as Code** | Terraform (preferred), ARM templates | Required; validate compliance within 90 days |
| **Networking** | Azure Virtual WAN, ExpressRoute | Implement ExpressRoute within 90 days |
| **Observability** | Splunk (SIEM), Azure Monitor | Integrate Datadog logs to Splunk within 90 days |
| **Backup/DR** | Azure Backup, Site Recovery | Align DR strategy within 12 months |

---

## 6) ESG Network Connectivity Requirements

| Requirement | Standard | CloudServe Gap |
|---|---|---|
| **Private connectivity** | ExpressRoute (Azure), Direct Connect (AWS) | CloudServe has Direct Connect; needs ExpressRoute for ESG network |
| **VPN** | Azure VPN Gateway | CloudServe has AWS Client VPN + Tailscale; add Azure VPN |
| **SD-WAN** | Azure Virtual WAN | Not deployed; implement for ESG integration |
| **Internet egress** | Zscaler (cloud proxy) | Not deployed; implement for security policy alignment |

---

## 7) ESG Data Residency Requirements

| Region | Requirement | CloudServe State |
|---|---|---|
| **EU (GDPR)** | EU customer data must remain in EU region | ⚠️ GAP: All data in us-east-1; needs eu-west-1 data migration |
| **UK (GDPR)** | UK customer data in UK South | ⚠️ GAP: No UK region deployment |
| **APAC** | APAC data in APAC regions | ⚠️ GAP: No APAC region deployment |

**Integration Requirement:** Deploy EU/UK data residency within 6-12 months for GDPR compliance.

---

## 8) ESG Security Infrastructure Standards

| Standard | Technology | CloudServe State |
|---|---|---|
| **DDoS protection** | Azure DDoS Standard | ⚠️ CloudServe has AWS Shield Standard (free tier); needs upgrade |
| **WAF** | Azure WAF, Azure Front Door | CloudServe has AWS WAF; accepted temporarily |
| **Network segmentation** | Azure Virtual Network, NSGs | CloudServe has VPC + Security Groups; aligned |
| **Encryption at rest** | Azure Storage Encryption (AES-256) | ✅ CloudServe has AWS KMS; aligned |
| **Encryption in transit** | TLS 1.2+ | ✅ Aligned |

---

## 9) CloudServe Cost Optimization (ESG Recommendations)

| Opportunity | Description | Estimated Savings |
|---|---|---:|
| **Reserved Instances** | 3-year commitment for steady-state workloads | $500K-700K/year |
| **Savings Plans** | Compute Savings Plans | $200K-300K/year |
| **Right-sizing** | Optimize over-provisioned resources | $150K-200K/year |
| **S3 tiering** | Auto-archive cold data | $80K-120K/year |

**Total Potential Savings:** $930K-1.32M/year (19-28% reduction)

---

**END OF BUYER DOCUMENT 3**
