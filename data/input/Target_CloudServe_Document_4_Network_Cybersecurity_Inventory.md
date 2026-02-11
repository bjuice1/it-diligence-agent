# CloudServe Technologies — Document 4: Network & Cybersecurity Inventory

> **Entity:** TARGET
> **Purpose:** Network architecture and security controls baseline for M&A technical due diligence
> **Coverage:** Network topology, security tools, compliance status, vulnerability management

---

## 1) Network Architecture Summary

| Component | Description |
|---|---|
| **Network model** | Cloud-native (AWS VPC) |
| **Primary connectivity** | AWS Direct Connect (1 Gbps) to Seattle office |
| **Remote access** | AWS Client VPN (150 users) + Tailscale (50 engineering) |
| **VPCs** | 4 VPCs (prod, non-prod, shared, EU prod) |
| **Inter-VPC** | AWS Transit Gateway (hub-and-spoke) |
| **Internet egress** | NAT Gateways (6 across AZs) |
| **DNS** | Route53 (public & private zones) |

---

## 2) VPC Network Inventory

| VPC Name | Region | CIDR Block | Subnets | Purpose | Connectivity |
|---|---|---|---:|---|---|
| cloudserve-prod-vpc | us-east-1 | 10.10.0.0/16 | 12 (4 public, 8 private) | Production workloads | Transit Gateway, Direct Connect |
| cloudserve-nonprod-vpc | us-east-1 | 10.20.0.0/16 | 9 (3 public, 6 private) | Dev/staging | Transit Gateway |
| cloudserve-shared-vpc | us-east-1 | 10.0.0.0/16 | 6 (2 public, 4 private) | Shared services (VPN, DNS) | Transit Gateway |
| cloudserve-prod-euw1-vpc | eu-west-1 | 10.30.0.0/16 | 6 (2 public, 4 private) | EU DR workloads | VPC peering to us-east-1 prod |

---

## 3) Network Security Controls

### Firewall & Access Control

| Control Type | Technology | Coverage | Notes |
|---|---|---|---|
| **Cloud firewall** | AWS Security Groups | All resources | 347 security group rules across VPCs |
| **Web application firewall** | AWS WAF | CloudFront, ALBs | 12 WAF rules (OWASP Top 10) |
| **Network ACLs** | AWS NACLs | All subnets | Mostly default ACLs; limited custom rules |
| **DDoS protection** | AWS Shield Standard | All resources | **GAP:** Shield Advanced NOT enabled ($3K/mo) |

### Network Segmentation

| Segment | Purpose | Access Control |
|---|---|---|
| **Public subnets** | Load balancers, NAT gateways | Open to internet (443, 80) |
| **Private app subnets** | EKS worker nodes, app servers | No direct internet; outbound via NAT |
| **Private data subnets** | RDS, Aurora, ElastiCache | No internet; app subnet access only |
| **Management subnet** | Bastion hosts, VPN endpoints | MFA required, IP whitelisting |

---

## 4) Remote Access & VPN

| Solution | Purpose | Users | MFA | Monthly Cost |
|---|---|---:|---|---:|
| **AWS Client VPN** | Employee remote access to AWS | 150 | ✅ Okta MFA | $3,000 |
| **Tailscale** | Peer-to-peer VPN for engineers | 50 | ✅ SSO via Okta | $500 |
| **Bastion hosts** | SSH access to private instances | 12 admins | ✅ SSH keys + MFA | $200 |

**Gap:** No formal jump box/bastion host policy; engineers have direct SSH access with keys (no session recording).

---

## 5) Security Tool Inventory

| Tool | Vendor | Category | Coverage | Annual Cost | Contract End | Notes |
|---|---|---|---|---:|---|---|
| **CrowdStrike Falcon** | CrowdStrike | Endpoint Detection & Response (EDR) | 412 endpoints (all employees) | $87,000 | 2025-11 | Laptops, servers, containers |
| **Wiz** | Wiz | Cloud Security Posture Management (CSPM) | All 9 AWS accounts | $125,000 | **2025-02** | **Contract ending in 2 months** |
| **Snyk** | Snyk | Code & dependency scanning | All repos (GitHub) | $78,000 | 2025-06 | Scans PRs, container images |
| **AWS GuardDuty** | AWS | Threat detection | All 9 AWS accounts | $60,000 | Evergreen | Detects anomalies, threats |
| **AWS WAF** | AWS | Web application firewall | CloudFront, ALBs | $48,000 | Evergreen | OWASP Top 10 rules |
| **Vanta** | Vanta | Compliance automation | Full IT environment | $210,000 | 2025-08 | SOC 2 compliance mgmt |

**Total Security Tooling Cost:** $608,000/year

---

## 6) Vulnerability Management

| Process | Frequency | Tool | Coverage | Gap |
|---|---|---|---|---|
| **Code scanning** | Every PR | Snyk | 100% of repos | ✅ Good coverage |
| **Container scanning** | Every build | Snyk + ECR scanning | All images | ✅ Good coverage |
| **Cloud config scanning** | Continuous | Wiz | All AWS accounts | ⚠️ Wiz contract expiring |
| **Network vulnerability scanning** | Monthly | AWS Inspector | EC2 instances only | ❌ No external vuln scanning |
| **Penetration testing** | Annual | External firm (Bishop Fox) | Web app + APIs | Last test: 6 months ago |

### Vulnerability Remediation SLAs

| Severity | SLA | Actual Performance | Status |
|---|---|---|---|
| **Critical** | 7 days | 12 days (average) | ⚠️ Missing SLA |
| **High** | 30 days | 45 days (average) | ⚠️ Missing SLA |
| **Medium** | 90 days | 120 days (average) | ⚠️ Missing SLA |
| **Low** | Best effort | No tracking | ❌ No tracking |

**Gap:** Vulnerability remediation SLAs defined but not consistently met; backlog of 87 open vulnerabilities (12 critical, 34 high).

---

## 7) Security Incident Response

| Component | Status | Notes |
|---|---|---|
| **Incident response plan** | ✅ Documented | Last updated: 9 months ago |
| **IR runbooks** | ⚠️ Partial | 60% of scenarios documented |
| **IR team** | ✅ Defined | 5 responders (on-call rotation) |
| **IR testing** | ❌ Not tested | No tabletop exercises conducted |
| **SIEM** | ⚠️ Limited | Datadog Security Monitoring (not full SIEM) |
| **Log retention** | 90 days | CloudWatch logs; CloudTrail 1 year |

**Gap:** No dedicated SIEM (Splunk, Sentinel, etc.); relying on Datadog Security Monitoring which is not purpose-built for security operations.

---

## 8) Compliance & Certifications

### Current Compliance Status

| Framework | Status | Last Audit | Next Audit | Cost | Notes |
|---|---|---|---|---:|---|
| **SOC 2 Type II** | ✅ Certified | 8 months ago (2024-06) | **2025-06** (4 months) | $85,000 | Managed by Vanta |
| **ISO 27001** | ❌ Not certified | N/A | N/A | N/A | **Gap:** Enterprise customers requesting |
| **GDPR** | ⚠️ Self-assessed | N/A | N/A | N/A | **Gap:** No formal audit |
| **CCPA** | ⚠️ Self-assessed | N/A | N/A | N/A | **Gap:** No formal audit |
| **PCI-DSS** | ✅ Not applicable | N/A | N/A | N/A | No card data (Stripe handles) |

### Compliance Gaps

| Gap | Description | Risk | Estimated Fix Cost |
|---|---|---|---|
| **SOC 2 renewal urgency** | Renewal audit due in 4 months | 🔴 HIGH | $100K-150K (accelerated audit) |
| **ISO 27001 missing** | 30% of enterprise customers require ISO | 🟠 MEDIUM | $200K-300K (initial certification) |
| **GDPR audit** | Self-assessed only; no formal audit | 🟠 MEDIUM | $75K-125K (GDPR audit) |
| **CCPA audit** | Self-assessed only; no formal audit | 🟡 LOW | $50K-75K (CCPA audit) |

---

## 9) Security Policies & Procedures

| Policy | Status | Last Review | Coverage |
|---|---|---|---|
| **Information Security Policy** | ✅ Published | 12 months ago | All employees |
| **Acceptable Use Policy** | ✅ Published | 12 months ago | All employees |
| **Incident Response Policy** | ✅ Published | 9 months ago | IR team |
| **Data Classification Policy** | ⚠️ Draft | N/A | Not enforced |
| **Third-Party Risk Mgmt** | ❌ Missing | N/A | No formal TPRM program |
| **Encryption Standards** | ✅ Published | 18 months ago | All engineering |
| **Access Control Policy** | ✅ Published | 6 months ago | All employees |

**Gap:** Data classification policy exists but not enforced; no data labeling or DLP controls.

---

## 10) Encryption & Data Protection

| Data State | Encryption Status | Technology | Notes |
|---|---|---|---|
| **Data at rest** | ✅ Encrypted | AWS KMS (AES-256) | RDS, S3, EBS all encrypted |
| **Data in transit** | ✅ Encrypted | TLS 1.2+ | All customer-facing APIs |
| **Internal traffic** | ⚠️ Partial | TLS for external, plaintext for some internal services | **Gap:** East-west traffic not fully encrypted |
| **Backups** | ✅ Encrypted | AWS KMS | All backups encrypted |
| **Customer PII** | ✅ Encrypted | AES-256 + field-level encryption | Sensitive fields hashed/encrypted |

### Key Management

| Component | Status | Notes |
|---|---|---|
| **KMS** | AWS KMS (managed) | Customer master keys (CMKs) per environment |
| **Key rotation** | ✅ Enabled | Automatic annual rotation |
| **Secrets management** | AWS Secrets Manager | API keys, DB passwords |
| **Certificate management** | AWS Certificate Manager | TLS certificates auto-renewed |

---

## 11) Identity & Access Management (Summary)

> **See Document 5 for full IAM details.**

| Component | Status |
|---|---|
| **Primary IdP** | Okta (workforce) |
| **MFA coverage** | 85% (required for admin/eng, optional for business) |
| **SSO** | 12 apps SSO-enabled via Okta |
| **Privileged access** | CyberArk (15 users - limited deployment) |
| **Cloud access** | AWS IAM + SSO |

**Gap:** MFA not enforced for all users (85% coverage); 15% of workforce (business users) opt-out.

---

## 12) Security Monitoring & Logging

| Log Source | Destination | Retention | Alerting |
|---|---|---|---|
| **AWS CloudTrail** | S3 + CloudWatch | 1 year | ✅ GuardDuty alerts |
| **VPC Flow Logs** | S3 | 90 days | ⚠️ No automated alerting |
| **Application logs** | Datadog | 90 days | ✅ Custom alerts configured |
| **WAF logs** | S3 | 90 days | ⚠️ Limited alerting |
| **Auth logs (Okta)** | Okta + Datadog | 90 days | ✅ Brute force detection |
| **Endpoint logs (CrowdStrike)** | CrowdStrike cloud | 1 year | ✅ EDR alerts |

**Gap:** No centralized SIEM for correlated threat detection; logs spread across Datadog, CloudWatch, CrowdStrike, Okta.

---

## 13) Threat Intelligence & Detection

| Capability | Status | Tool | Notes |
|---|---|---|---|
| **Threat detection** | ✅ Enabled | AWS GuardDuty | Detects known threats, anomalies |
| **Threat intel feeds** | ❌ Not integrated | N/A | No third-party threat intel |
| **UEBA** | ❌ Not deployed | N/A | No user behavior analytics |
| **Deception tech** | ❌ Not deployed | N/A | No honeypots or deception |

---

## 14) Physical Security (Corporate Office)

| Control | Status | Notes |
|---|---|---|
| **Office location** | Seattle, WA | 120 employees on-site |
| **Badge access** | ✅ Implemented | HID badge system |
| **Visitor management** | ✅ Implemented | Front desk check-in |
| **CCTV** | ✅ Implemented | 24 cameras, 30-day retention |
| **Server room** | N/A | No on-prem servers (100% cloud) |

---

## 15) Security Risks & Remediation

| Risk | Description | Severity | Estimated Fix Cost |
|---|---|---|---|
| **Wiz contract expiring** | CSPM tool contract ends in 2 months | 🔴 HIGH | $125K/year renewal OR $150K migration to alternative |
| **SOC 2 renewal urgency** | Audit due in 4 months; delays risk customer attrition | 🔴 HIGH | $100K-150K (accelerated audit) |
| **No ISO 27001** | Enterprise customers requiring certification | 🟠 MEDIUM | $200K-300K (initial cert + ongoing) |
| **MFA coverage gap** | 15% of workforce not using MFA | 🟠 MEDIUM | $10K-20K (policy enforcement + training) |
| **Vuln remediation SLA misses** | 87 open vulnerabilities, SLAs not met | 🟠 MEDIUM | $50K-100K (dedicated vuln mgmt resource) |
| **No SIEM** | No centralized security event mgmt | 🟠 MEDIUM | $150K-250K (Splunk/Sentinel deployment) |
| **Data classification unenforced** | Policy exists but no DLP or enforcement | 🟡 LOW | $75K-125K (DLP implementation) |

---

## 16) Security Technical Debt

| Issue | Description | Impact | Estimated Fix Cost |
|---|---|---|---|
| **East-west traffic encryption** | Internal service-to-service traffic not encrypted | Security risk if VPC compromised | $100K-200K (service mesh like Istio) |
| **No external vuln scanning** | Only AWS Inspector (internal); no external scans | Blind to external attack surface | $30K-50K/year (Qualys/Tenable) |
| **Bastion host gaps** | No session recording or centralized audit | Compliance risk, insider threat | $50K-100K (privileged access gateway) |
| **IR tabletop exercises** | No IR testing conducted | Unknown response capability | $20K-40K (annual exercises) |

---

## 17) Integration with Buyer Security Standards

| Target State | Buyer State | Gap/Integration Need |
|---|---|---|
| **CSPM:** Wiz | **CSPM:** Microsoft Defender for Cloud | Tool migration or dual-tool operation |
| **EDR:** CrowdStrike | **EDR:** CrowdStrike (aligned) | ✅ No gap |
| **SIEM:** None (Datadog) | **SIEM:** Splunk Enterprise Security | Deploy Splunk or integrate logs |
| **IdP:** Okta | **IdP:** Azure AD | Identity integration/migration |
| **Compliance:** SOC 2 | **Compliance:** SOC 2 + ISO 27001 | Close ISO gap |

---

## 18) Documentation Gaps & VDR Requests

| Gap | Information Needed | Purpose |
|---|---|---|
| **Network diagrams** | Detailed VPC architecture diagrams | Understand network segmentation, data flows |
| **Security group rules** | Export of all security group rules | Validate least privilege, identify overly permissive rules |
| **Penetration test report** | Last pentest report (6 months ago) | Review findings, validate remediation |
| **Vulnerability scan reports** | Last 3 months of vulnerability scans | Assess security posture, open vulnerabilities |
| **Incident log** | Security incident log (last 12 months) | Understand threat landscape, IR effectiveness |
| **WAF rules** | Current WAF rule configuration | Validate protection coverage |

---

## 19) Consistency Validation

| Fact | Value | Matches Document 1? |
|---|---:|---|
| Endpoint security | CrowdStrike Falcon | ✅ Yes |
| CSPM tool | Wiz | ✅ Yes |
| SIEM | Datadog Security Monitoring | ✅ Yes |
| SOC 2 status | Certified (renewal in 4 months) | ✅ Yes |
| ISO 27001 status | Not certified | ✅ Yes |
| Penetration testing | Last test: 6 months ago | ✅ Yes |

---

**END OF DOCUMENT 4**
