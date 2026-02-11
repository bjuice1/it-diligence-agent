# CloudServe Technologies — Document 3: Infrastructure & Hosting Inventory

> **Entity:** TARGET
> **Purpose:** Complete infrastructure baseline for M&A technical due diligence
> **Hosting Model:** 100% AWS Cloud (no on-premises data centers)

---

## 1) Infrastructure Summary

| Metric | Value |
|---|---:|
| **Cloud provider** | AWS (primary and only) |
| **Primary region** | us-east-1 (N. Virginia) |
| **Secondary region** | eu-west-1 (Ireland) - warm standby |
| **AWS accounts** | **9** (multi-account strategy) |
| **Annual cloud spend** | **$4,800,000** ($400K/month) |
| **Compute model** | Kubernetes (EKS) + Lambda |
| **Data centers** | **0** (cloud-native) |
| **Corporate office** | Seattle, WA (120 employees on-site) |

---

## 2) AWS Account Structure

| Account Name | Account ID | Purpose | Environment | Monthly Cost |
|---|---|---|---|---:|
| cloudserve-prod | 123456789012 | Production workloads | Production | $185,000 |
| cloudserve-staging | 234567890123 | Staging environment | Non-Prod | $62,000 |
| cloudserve-dev | 345678901234 | Development environment | Non-Prod | $28,000 |
| cloudserve-shared-services | 456789012345 | Shared infra (VPN, DNS, Transit Gateway) | Shared | $38,000 |
| cloudserve-data | 567890123456 | Data warehouse (Snowflake on AWS) | Production | $45,000 |
| cloudserve-security | 678901234567 | Security tools (GuardDuty, WAF, logs) | Shared | $15,000 |
| cloudserve-sandbox-1 | 789012345678 | Engineering sandbox | Non-Prod | $8,000 |
| cloudserve-sandbox-2 | 890123456789 | Engineering sandbox | Non-Prod | $6,000 |
| cloudserve-sandbox-3 | 901234567890 | Engineering sandbox | Non-Prod | $13,000 |

---

## 3) AWS Cost Breakdown by Service

| Service Category | Description | Monthly Cost | Annual Cost |
|---|---|---:|---:|
| **Compute** | EC2, EKS (47 nodes), Lambda (millions of invocations) | $145,000 | $1,740,000 |
| **Database** | RDS PostgreSQL (multi-AZ), Aurora, DynamoDB | $112,000 | $1,344,000 |
| **Storage** | S3 (18TB), EBS (120TB across environments), EFS | $48,000 | $576,000 |
| **Networking** | VPC, Transit Gateway, Direct Connect (1Gbps), NAT Gateway | $38,000 | $456,000 |
| **CDN & Edge** | CloudFront (CDN for customer assets) | $32,000 | $384,000 |
| **Security** | WAF, GuardDuty, Secrets Manager, Shield Standard | $15,000 | $180,000 |
| **Monitoring** | CloudWatch, CloudTrail, X-Ray | $10,000 | $120,000 |

**Total:** $400,000/month = **$4,800,000/year**

---

## 4) Compute Infrastructure

### Kubernetes (EKS) Clusters

| Cluster Name | Region | Environment | Node Count | Instance Type | Monthly Cost |
|---|---|---|---:|---|---:|
| cloudserve-prod-use1 | us-east-1 | Production | 28 | m6i.2xlarge | $95,000 |
| cloudserve-prod-euw1 | eu-west-1 | DR/Secondary | 8 | m6i.2xlarge | $28,000 |
| cloudserve-staging | us-east-1 | Staging | 8 | m6i.xlarge | $12,000 |
| cloudserve-dev | us-east-1 | Development | 3 | m6i.large | $3,000 |

**Total EKS nodes:** 47 across all environments

### Lambda Functions

| Usage | Description | Monthly Invocations | Monthly Cost |
|---|---|---:|---:|
| **API Gateway backends** | Serverless API endpoints | 45M | $8,000 |
| **Event processing** | SNS/SQS event handlers | 120M | $12,000 |
| **Scheduled jobs** | Cron-like batch processing | 2M | $400 |

---

## 5) Database Infrastructure

| Database | Type | Purpose | Size | Environment | Monthly Cost |
|---|---|---|---:|---|---:|
| **cloudserve-prod-pg** | RDS PostgreSQL 15 | Customer data (multi-tenant) | 8TB | Production (multi-AZ) | $42,000 |
| **cloudserve-prod-aurora** | Aurora PostgreSQL | Read replicas for analytics | 6TB | Production (3 replicas) | $38,000 |
| **cloudserve-analytics** | RDS PostgreSQL 15 | Internal analytics | 2.5TB | Production | $18,000 |
| **cloudserve-sessions** | DynamoDB | Session storage (high throughput) | 800GB | Production | $8,000 |
| **cloudserve-cache** | ElastiCache Redis | Application caching | N/A | Production (cluster mode) | $6,000 |

**Total Database Cost:** $112,000/month = **$1,344,000/year**

### Database Backup & Recovery

| Database | Backup Frequency | Retention | Recovery Tested |
|---|---|---|---|
| cloudserve-prod-pg | Daily automated snapshots | 30 days | ❌ Last test: 8 months ago |
| cloudserve-prod-aurora | Continuous backups | 30 days | ❌ Last test: 8 months ago |
| cloudserve-analytics | Daily automated snapshots | 7 days | ❌ Never tested |

---

## 6) Storage Infrastructure

| Storage Type | Usage | Capacity | Monthly Cost |
|---|---|---:|---:|
| **S3 - Customer assets** | Customer-uploaded files, documents | 12TB | $24,000 |
| **S3 - Backups** | Database backups, logs, archives | 6TB | $6,000 |
| **EBS - Production** | EKS persistent volumes | 80TB | $12,000 |
| **EBS - Non-prod** | Dev/staging persistent volumes | 40TB | $4,000 |
| **EFS - Shared storage** | Shared file system for apps | 500GB | $2,000 |

**Total Storage Cost:** $48,000/month = **$576,000/year**

---

## 7) Network Architecture

### VPC Structure

| VPC | Region | Purpose | CIDR Block |
|---|---|---|---|
| cloudserve-prod-vpc | us-east-1 | Production workloads | 10.10.0.0/16 |
| cloudserve-nonprod-vpc | us-east-1 | Dev/staging workloads | 10.20.0.0/16 |
| cloudserve-shared-vpc | us-east-1 | Shared services | 10.0.0.0/16 |
| cloudserve-prod-euw1-vpc | eu-west-1 | EU production (DR) | 10.30.0.0/16 |

### Connectivity

| Connection Type | Description | Bandwidth | Monthly Cost |
|---|---|---|---:|
| **AWS Direct Connect** | Seattle office → us-east-1 | 1 Gbps | $15,000 |
| **AWS Client VPN** | Remote employee access | 150 concurrent users | $3,000 |
| **Tailscale** | Peer-to-peer VPN (engineering) | 50 users | $500 |
| **Transit Gateway** | VPC interconnectivity (4 VPCs) | N/A | $8,000 |
| **NAT Gateways** | Outbound internet (6 AZs × $45/mo) | N/A | $4,500 |

### CDN & Edge

| Service | Purpose | Monthly Cost |
|---|---|---:|
| **AWS CloudFront** | CDN for web assets, API responses | $28,000 |
| **Fastly** | Additional CDN for EU customers | $7,000 |

**Total Networking Cost:** $38,000/month (not including CDN) = **$456,000/year**

---

## 8) Security Infrastructure

| Service | Purpose | Monthly Cost | Annual Cost |
|---|---|---:|---:|
| **AWS WAF** | Web application firewall | $4,000 | $48,000 |
| **AWS Shield Standard** | DDoS protection (free tier) | $0 | $0 |
| **AWS GuardDuty** | Threat detection | $5,000 | $60,000 |
| **AWS Secrets Manager** | Secrets storage & rotation | $2,000 | $24,000 |
| **AWS Security Hub** | Security posture management | $1,500 | $18,000 |
| **VPC Flow Logs** | Network traffic logging | $2,500 | $30,000 |

**Gap Identified:** AWS Shield Standard (free) does NOT protect against Layer 7 DDoS attacks. Shield Advanced ($3K/month) recommended but not deployed.

---

## 9) Monitoring & Observability

| Service | Purpose | Monthly Cost | Annual Cost |
|---|---|---:|---:|
| **AWS CloudWatch** | Logs, metrics, alarms | $6,000 | $72,000 |
| **AWS CloudTrail** | Audit logs (all API calls) | $2,000 | $24,000 |
| **AWS X-Ray** | Distributed tracing | $2,000 | $24,000 |

**Note:** Primary observability is via Datadog ($312K/year, see Document 2), not native AWS tools.

---

## 10) Disaster Recovery Configuration

| Item | Value |
|---|---|
| **DR strategy** | Warm standby (eu-west-1) |
| **DR region** | eu-west-1 (Ireland) |
| **DR EKS cluster** | 8 nodes (scaled to 28 during failover) |
| **DR database** | Aurora cross-region replica (asynchronous) |
| **RPO (Recovery Point Objective)** | 4 hours (based on replication lag) |
| **RTO (Recovery Time Objective)** | 8 hours (manual runbook execution) |
| **Last DR test** | 14 months ago (Q4 2023) |
| **DR test outcome** | ❌ **FAILED** - RTO target missed (12 hours actual) |

### DR Test Failure Root Causes

| Issue | Description | Status |
|---|---|---|
| **Runbook outdated** | DR runbooks not updated after architecture changes | ⚠️ Not remediated |
| **DNS cutover delay** | Route53 health check misconfiguration | ⚠️ Not remediated |
| **EKS scaling slow** | Node auto-scaling took 4 hours (config issue) | ⚠️ Not remediated |
| **Database replication lag** | Aurora replica lagged by 6 hours (unexpected) | ⚠️ Not remediated |

**Recommendation:** Execute new DR test BEFORE deal close; allocate $50K-100K for runbook remediation and testing.

---

## 11) Infrastructure Gaps & Risks

| Gap/Risk | Description | Severity | Estimated Fix Cost |
|---|---|---|---|
| **No EU data residency** | All customer data in us-east-1; GDPR risk | 🔴 HIGH | $250K-500K (new region build) |
| **DR capability unproven** | Last test failed; RTO/RPO unvalidated | 🔴 HIGH | $50K-100K (test + remediation) |
| **No multi-region production** | Single region for production (us-east-1 only) | 🟠 MEDIUM | $200K-400K (true active-active) |
| **No Shield Advanced** | Vulnerable to Layer 7 DDoS attacks | 🟠 MEDIUM | $36K/year (Shield Advanced) |
| **Backup testing** | Database restores not regularly tested | 🟠 MEDIUM | $20K-40K (testing program) |
| **AWS account sprawl** | 9 accounts with inconsistent tagging/governance | 🟡 LOW | $30K-50K (governance cleanup) |
| **No cost optimization** | No Reserved Instances or Savings Plans | 🟡 LOW | $800K-1.2M/year savings opportunity |

---

## 12) Cost Optimization Opportunities

| Opportunity | Description | Estimated Annual Savings |
|---|---|---:|
| **Reserved Instances (RI)** | 3-year RI for EKS nodes (60% of fleet) | $500K-700K |
| **Savings Plans** | Compute Savings Plans for Lambda/Fargate | $200K-300K |
| **S3 Intelligent-Tiering** | Auto-archive cold data | $80K-120K |
| **RDS RI** | 3-year RI for RDS databases | $300K-450K |
| **Right-sizing** | Downsize over-provisioned instances | $150K-200K |

**Total Potential Savings:** $1.23M - $1.77M/year (26-37% reduction in AWS spend)

---

## 13) Integration with Buyer Infrastructure

| Consideration | Target State | Buyer State | Gap/Risk |
|---|---|---|---|
| **Cloud provider** | AWS | Azure (primary), AWS (secondary) | Integration complexity; cross-cloud networking |
| **Kubernetes** | EKS (AWS) | AKS (Azure) | Different K8s distributions; potential re-platform |
| **Monitoring** | Datadog | Splunk | Tool consolidation; migration effort |
| **IdP** | Okta | Azure AD | Identity integration; SSO complexity |
| **VPN** | AWS Client VPN + Tailscale | Azure VPN | Network connectivity redesign |

---

## 14) Infrastructure Technical Debt

| Issue | Description | Impact | Estimated Fix Cost |
|---|---|---|---|
| **No IaC coverage** | ~40% of infra not in Terraform | Drift risk, manual changes | $100K-200K (IaC completion) |
| **Inconsistent tagging** | Cost allocation tags missing on 30% of resources | Financial visibility gap | $20K-40K (tagging project) |
| **No auto-scaling policies** | Manual scaling for most workloads | Operational burden, cost inefficiency | $50K-100K (auto-scaling implementation) |
| **Logging gaps** | VPC Flow Logs only on prod VPC | Security blind spots | $10K-20K (enable logging) |

---

## 15) Documentation Gaps & VDR Requests

| Gap | Information Needed | Purpose |
|---|---|---|
| **Network diagrams** | Complete network architecture diagrams | Understand connectivity, segmentation |
| **DR runbooks** | Current DR runbooks (even if outdated) | Assess recovery capability, plan updates |
| **IAM policies** | AWS IAM roles and policies (export) | Security review, least privilege validation |
| **Cost allocation** | 12-month AWS Cost Explorer report | Understand cost trends, optimization opportunities |
| **Reserved Instances** | Current RI/Savings Plan coverage | Assess cost optimization maturity |
| **Incident history** | Infrastructure incident log (last 12 months) | Assess reliability, identify patterns |

---

## 16) Consistency Validation

| Fact | Value | Matches Document 1? |
|---|---:|---|
| Cloud provider | AWS | ✅ Yes |
| AWS accounts | 9 | ✅ Yes |
| Annual AWS spend | $4,800,000 | ✅ Yes |
| Primary region | us-east-1 | ✅ Yes |
| Secondary region | eu-west-1 | ✅ Yes |
| DR strategy | Warm standby | ✅ Yes |
| RPO / RTO | 4h / 8h | ✅ Yes |
| Data centers | 0 | ✅ Yes |

---

**END OF DOCUMENT 3**
