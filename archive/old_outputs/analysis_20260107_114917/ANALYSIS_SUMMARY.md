# IT Due Diligence Analysis Summary

Generated: 2026-01-07 11:59:59

## Domain Summaries

### Network
- Complexity: medium
- Cost Range: $900K-$1.6M
- Timeline: 12-18 months for full integration
- Summary: National Mutual operates a distributed network across 12 locations with concentrated Chicago data centers and AWS cloud infrastructure. Significant knowledge gaps exist around WAN architecture and IP addressing. Security platforms show partial alignment with buyer. Geographic concentration creates standalone risk requiring mitigation.

### Cross-Domain
- Complexity: high
- Cost Range: $4M-$6M
- Timeline: 18-24 months
- Summary: National Mutual presents a high-complexity integration requiring comprehensive platform migrations across all domains. While the target has strong SaaS adoption and reasonable IT investment, complete platform mismatch with buyer environment creates 18-24 month integration timeline. Geographic concentration in Chicago adds immediate business continuity risk requiring urgent attention.

## Top Risks

### R-001: Geographic concentration with both data centers in Chicago creates single point of failure for regional disasters
- **Severity**: high
- **Likelihood**: low
- **Domain**: infrastructure
- **Mitigation**: Establish geographically separated DR site or migrate critical workloads to multi-region cloud deployment

### R-004: Cloud platform mismatch between target (AWS) and buyer (Azure primary) creates integration complexity
- **Severity**: high
- **Likelihood**: high
- **Domain**: infrastructure
- **Mitigation**: Develop phased migration strategy, consider multi-cloud approach for transition period, assess application portability

### R-006: Geographic concentration of data centers in single metro area (Chicago)
- **Severity**: high
- **Likelihood**: low
- **Domain**: network
- **Mitigation**: Establish geographically diverse DR site outside Chicago metro area, implement cloud-based DR capabilities

### R-008: RSA SecurID MFA platform approaching end-of-life with potential support discontinuation
- **Severity**: high
- **Likelihood**: high
- **Domain**: cybersecurity
- **Mitigation**: Accelerate migration to modern MFA solution (Microsoft Authenticator, Duo, or Okta) with phased rollout plan

### R-011: CyberArk PAM version 13.2 on-premises may have unpatched vulnerabilities and limited cloud integration
- **Severity**: high
- **Likelihood**: medium
- **Domain**: cybersecurity
- **Mitigation**: Upgrade to latest CyberArk version, implement cloud PAM capabilities, establish regular patching schedule

### R-012: 41 AWS accounts create significant cloud security governance and compliance challenges
- **Severity**: high
- **Likelihood**: high
- **Domain**: cybersecurity
- **Mitigation**: Implement AWS Organizations, centralized security controls, cloud security posture management (CSPM), account consolidation strategy

### R-014: Cross-domain dependency: Network connectivity establishment must precede AWS to Azure cloud migration
- **Severity**: high
- **Likelihood**: high
- **Domain**: cross-domain
- **Mitigation**: Network connectivity (WI-010) must complete before cloud migration execution (WI-006) can begin

### R-015: Cross-domain dependency: Identity integration (Azure AD) must complete before security tool migrations can begin
- **Severity**: high
- **Likelihood**: high
- **Domain**: cross-domain
- **Mitigation**: Security access provisioning (WI-015) must complete before infrastructure discovery (WI-001) and cloud migration planning can begin

### R-016: Cross-domain dependency: MFA migration affects all system access and must coordinate with infrastructure migrations
- **Severity**: high
- **Likelihood**: high
- **Domain**: cross-domain
- **Mitigation**: MFA migration (WI-017) should complete before major infrastructure migrations begin, or be carefully coordinated to avoid access disruptions

### R-017: Cross-domain dependency: SIEM migration requires network connectivity and affects security monitoring during infrastructure changes
- **Severity**: high
- **Likelihood**: high
- **Domain**: cross-domain
- **Mitigation**: SIEM migration (WI-018) must maintain security monitoring capability throughout infrastructure migration period

## Critical Knowledge Gaps

- **G-001**: Detailed AWS resource inventory and architecture diagrams
  - Why needed: Required to accurately estimate migration complexity and costs for AWS to Azure transition
  - Suggested source: Technical assessment with AWS cost and usage reports, architecture review

- **G-002**: Network topology and bandwidth utilization details
  - Why needed: Critical for planning network integration and estimating connectivity costs between environments
  - Suggested source: Network documentation review and technical interview with infrastructure team

- **G-003**: WAN connectivity architecture and providers
  - Why needed: Critical for Day 1 connectivity planning and understanding single points of failure. Need to know if MPLS, SD-WAN, or internet VPN, carrier contracts, and bandwidth per site.
  - Suggested source: Network architecture documentation, carrier contracts, or technical interview with infrastructure team

- **G-004**: LAN/switching infrastructure details
  - Why needed: Need to understand network equipment age, vendor, EOL status for security and operational risk assessment. Critical for determining refresh requirements.
  - Suggested source: Network inventory documentation or infrastructure team interview

- **G-005**: IP addressing scheme and DHCP/DNS architecture
  - Why needed: Essential for integration planning to identify IP conflicts with buyer (Atlantic International). DNS architecture affects email, authentication, and application integration.
  - Suggested source: Network documentation or technical assessment

- **G-006**: MFA coverage percentage and privileged account MFA status
  - Why needed: Critical for assessing account compromise risk and determining MFA rollout scope and urgency
  - Suggested source: Technical assessment of RSA SecurID deployment and Azure AD MFA configuration

- **G-007**: Compliance certifications held and regulatory requirements
  - Why needed: Insurance industry has specific regulatory requirements (state insurance regulations, NAIC, potentially SOX) that affect security controls and integration approach
  - Suggested source: Document request for compliance certifications, audit reports, and regulatory correspondence

## Key Work Items

### WI-001: Infrastructure Discovery and Assessment
- Domain: infrastructure
- Effort: 6-8 weeks
- Cost: $150K-$250K
- Phase: N/A

### WI-002: Establish Network Connectivity
- Domain: infrastructure
- Effort: 2-3 weeks
- Cost: $50K-$100K
- Phase: N/A

### WI-003: AWS to Azure Migration Strategy Development
- Domain: infrastructure
- Effort: 8-12 weeks
- Cost: $200K-$400K
- Phase: N/A

### WI-004: Data Center Consolidation Planning
- Domain: infrastructure
- Effort: 6-10 weeks
- Cost: $100K-$200K
- Phase: N/A

### WI-005: DR Architecture Redesign
- Domain: infrastructure
- Effort: 12-16 weeks
- Cost: $300K-$600K
- Phase: N/A

### WI-006: Cloud Workload Migration Execution
- Domain: infrastructure
- Effort: 20-30 weeks
- Cost: $1.5M-$3M
- Phase: N/A

### WI-007: Infrastructure Team Integration
- Domain: infrastructure
- Effort: 8-12 weeks
- Cost: $100K-$200K
- Phase: N/A

### WI-008: Network Discovery and Documentation
- Domain: network
- Effort: 4-6 weeks
- Cost: $50K-$75K
- Phase: N/A

### WI-009: IP Address Conflict Analysis and Remediation Planning
- Domain: network
- Effort: 2-3 weeks
- Cost: $25K-$40K
- Phase: N/A

### WI-010: Establish Secure Network Connectivity to Buyer
- Domain: network
- Effort: 3-4 weeks
- Cost: $40K-$80K
- Phase: N/A

### WI-011: SIEM Migration from QRadar to Microsoft Sentinel
- Domain: network
- Effort: 8-12 weeks
- Cost: $150K-$250K
- Phase: N/A

### WI-012: MFA Migration from RSA SecurID to Microsoft Authenticator
- Domain: network
- Effort: 6-8 weeks
- Cost: $75K-$125K
- Phase: N/A

### WI-013: AWS Region Consolidation Planning
- Domain: network
- Effort: 4-6 weeks
- Cost: $40K-$60K
- Phase: N/A

### WI-014: Data Center Consolidation and Geographic Diversification
- Domain: network
- Effort: 12-18 months
- Cost: $500K-$1M
- Phase: N/A

### WI-015: Security Access Provisioning and Identity Integration
- Domain: cybersecurity
- Effort: 3-4 weeks
- Cost: $75K-$125K
- Phase: N/A

## Strategic Recommendations

### REC-001: Negotiate extended TSA for infrastructure services to provide buffer during complex cloud migration
- Priority: high
- Timing: pre_close
- Rationale: AWS to Azure migration is complex and high-risk. Extended TSA provides safety net and allows for proper planning and testing without business disruption

### REC-002: Conduct immediate geographic DR risk assessment and implement interim mitigation
- Priority: critical
- Timing: day_1
- Rationale: Both data centers in Chicago creates unacceptable business continuity risk that exists today and will persist through integration

### REC-003: Augment target's cloud engineering capacity immediately post-close
- Priority: high
- Timing: day_1
- Rationale: Single cloud engineer is insufficient for $3.38M AWS environment and upcoming migration complexity. Key person risk threatens integration execution

### REC-004: Prioritize network discovery and documentation as first critical activity post-close
- Priority: critical
- Timing: day_1
- Rationale: Multiple critical knowledge gaps exist around WAN architecture, IP addressing, and LAN infrastructure. Without this baseline, integration planning cannot proceed safely and Day 1 connectivity risks are elevated.

### REC-005: Negotiate extended support contracts for RSA SecurID and IBM QRadar during transition period
- Priority: high
- Timing: pre_close
- Rationale: Both platforms will be migrated to buyer standards (Microsoft Authenticator and Sentinel) but need to remain operational during transition. Extended support ensures security continuity.

### REC-006: Establish geographic DR capability outside Chicago metro area as risk mitigation priority
- Priority: high
- Timing: first_90_days
- Rationale: Both data centers in Chicago create unacceptable geographic concentration risk. Buyer's distributed infrastructure provides opportunity to improve resilience while achieving integration synergies.

### REC-007: Negotiate extended TSA for shared services with minimum 18-month term and 6-month extension option
- Priority: critical
- Timing: pre_close
- Rationale: Cross-domain dependencies create 18-24 month integration timeline. Geographic concentration in Chicago and platform mismatches require careful sequencing that cannot be rushed

### REC-008: Establish dedicated integration budget of $4M-$6M with 25% contingency for platform migrations
- Priority: critical
- Timing: pre_close
- Rationale: Complete platform mismatch across infrastructure (AWS->Azure), security (RSA->Microsoft, Splunk->Sentinel), and network requires significant investment. Geographic concentration adds DR complexity

### REC-009: Retain key target IT personnel through 24-month retention packages, especially cloud engineer and security team
- Priority: high
- Timing: pre_close
- Rationale: Only 1 cloud engineer supporting $3.38M AWS environment and complex security platform migrations create key person dependency. Knowledge loss would significantly increase integration risk and cost

### REC-010: Accelerate geographic diversification by establishing East Coast presence before Chicago data center consolidation
- Priority: high
- Timing: first_90_days
- Rationale: Both data centers in Chicago create unacceptable single point of failure for $500M revenue company. Must establish geographic diversity before consolidating to buyer's infrastructure

### REC-011: Engage Microsoft as strategic partner for comprehensive platform migration support
- Priority: high
- Timing: pre_close
- Rationale: Buyer's Azure/Microsoft 365 environment aligns with target's partial Microsoft adoption. Microsoft can provide migration credits, technical resources, and accelerated timelines for Azure, Sentinel, and MFA migrations