# IT Due Diligence Analysis Summary

Generated: 2026-01-07 08:54:04

## Domain Summaries

### Infrastructure
- Complexity: very_high
- Cost Range: $2.5M-$5M
- Timeline: 12-18 months
- Summary: TargetCo operates as a fully integrated business unit within ParentCo's infrastructure, requiring complete separation across all domains. The environment includes 650 users, 620 devices, and 110-130 servers all managed through ParentCo systems. This is a classic carve-out scenario with high complexity due to shared Azure AD tenant, network infrastructure, and enterprise applications. Integration with BuyerCo's Azure environment offers some alignment opportunities but separation timeline will be 12-18 months minimum.

### Network
- Complexity: very_high
- Cost Range: $500K-$1.5M
- Timeline: 12-18 months for full integration
- Summary: TargetCo operates entirely on ParentCo's shared network infrastructure with no independent network architecture. This creates significant separation complexity requiring comprehensive discovery, Day 1 connectivity planning, and likely IP renumbering. The lack of network documentation represents a critical gap that must be addressed immediately.

### Cybersecurity
- Complexity: very_high
- Cost Range: $800K-$1.8M
- Timeline: 12-18 months
- Summary: TargetCo operates with complete dependency on ParentCo's security infrastructure including Azure AD, CrowdStrike EDR, Microsoft Sentinel SIEM, and centralized SOC. While the underlying security stack appears enterprise-grade, the complete dependency creates significant separation risk and requires comprehensive security capability buildout post-acquisition.

### Cross-Domain
- Complexity: very_high
- Cost Range: $4.5M-$8.5M
- Timeline: 18-24 months
- Summary: Project Atlas represents a very high complexity carve-out requiring separation of TargetCo from completely shared ParentCo infrastructure. Critical path dependencies across Azure AD, network, and security domains create 18-24 month minimum timeline with $4.5M-$8.5M estimated cost. Significant technical discovery gaps and sequential dependencies present material risks to timeline and budget.

## Top Risks

### R-002: Shared ERP/CRM/HCM platform separation
- **Severity**: critical
- **Likelihood**: high
- **Domain**: cross-domain
- **Mitigation**: Detailed application dependency mapping, TSA agreements, phased migration approach, consider platform replacement vs separation

### R-004: Security tooling and monitoring gaps during transition
- **Severity**: critical
- **Likelihood**: high
- **Domain**: cybersecurity
- **Mitigation**: Accelerated security tool deployment, TSA for security services, temporary managed security services

### R-005: Network separation from ParentCo may cause business disruption
- **Severity**: critical
- **Likelihood**: high
- **Domain**: network
- **Mitigation**: Establish temporary network connectivity before separation, plan phased cutover approach, and ensure Day 1 connectivity requirements are met

### R-008: Complete dependency on ParentCo security infrastructure and expertise
- **Severity**: critical
- **Likelihood**: high
- **Domain**: cybersecurity
- **Mitigation**: Develop comprehensive security separation plan with interim managed security services and accelerated security capability buildout

### R-012: Critical path timeline risk due to sequential dependencies across all domains
- **Severity**: critical
- **Likelihood**: medium
- **Domain**: cross-domain
- **Mitigation**: Establish dedicated integration PMO, negotiate extended TSA terms upfront, begin identity separation planning immediately post-close

### R-001: Azure AD tenant separation complexity
- **Severity**: high
- **Likelihood**: high
- **Domain**: infrastructure
- **Mitigation**: Early planning for phased user migration, TSA for identity services during transition, automated provisioning tools

### R-003: Network infrastructure separation complexity
- **Severity**: high
- **Likelihood**: high
- **Domain**: network
- **Mitigation**: Network discovery and documentation, parallel network buildout, phased cutover approach

### R-006: IP address conflicts between TargetCo and BuyerCo networks
- **Severity**: high
- **Likelihood**: high
- **Domain**: network
- **Mitigation**: Immediate IP address discovery and conflict analysis, plan IP renumbering if needed, consider NAT as temporary solution

### R-009: Identity and access management separation complexity
- **Severity**: high
- **Likelihood**: high
- **Domain**: cybersecurity
- **Mitigation**: Detailed IAM migration planning with phased approach, temporary federation, and comprehensive user communication

### R-010: Security monitoring and SIEM data loss during transition
- **Severity**: high
- **Likelihood**: high
- **Domain**: cybersecurity
- **Mitigation**: Implement new SIEM instance before separation, export critical historical data, and establish new log sources and detection rules

## Critical Knowledge Gaps

- **G-001**: Specific cloud platform details for TargetCo workloads
  - Why needed: Need to understand if TargetCo runs on Azure (matching buyer) or other platforms to estimate migration complexity and costs
  - Suggested source: Technical assessment of current hosting platforms and cloud resource inventory

- **G-002**: Server operating systems, versions, and age distribution
  - Why needed: Critical for identifying end-of-life systems requiring immediate attention and estimating migration/refresh costs
  - Suggested source: Server inventory report with OS versions, patch levels, and hardware age

- **G-003**: Data center locations and lease terms
  - Why needed: Need to understand physical infrastructure commitments, lease expiration dates, and exit costs for separation planning
  - Suggested source: Facilities contracts and data center lease agreements

- **G-004**: Storage capacity, platforms, and data volumes
  - Why needed: Essential for estimating data migration costs, timeline, and storage platform consolidation requirements
  - Suggested source: Storage inventory with capacity utilization, growth rates, and platform details

- **G-005**: Complete network topology and architecture documentation
  - Why needed: Cannot assess network separation complexity, IP addressing schemes, or integration approach without understanding current network design
  - Suggested source: Request detailed network diagrams, IP addressing schemes, and site connectivity maps from ParentCo IT

- **G-006**: IP address scheme and DHCP/DNS configuration details
  - Why needed: IP conflicts are the #1 network integration blocker - must understand current addressing to plan integration and identify conflicts with BuyerCo
  - Suggested source: Technical assessment with ParentCo network team to document IP ranges, DHCP scopes, and DNS zones

- **G-007**: Physical site locations and WAN connectivity details
  - Why needed: Need to understand which sites TargetCo operates from and how they connect to plan Day 1 connectivity and new circuit requirements
  - Suggested source: Site survey and facilities documentation from TargetCo operations team

- **G-008**: Firewall rules and security zone configuration
  - Why needed: Document mentions ParentCo-managed network security controls but no details on firewall architecture, rules, or security zones that will need migration
  - Suggested source: Firewall configuration export and security architecture documentation from ParentCo security team

- **G-009**: Security assessment results and penetration testing reports
  - Why needed: Cannot assess actual security posture without understanding vulnerabilities, control effectiveness, and risk exposure
  - Suggested source: Request recent security assessments, penetration test reports, and vulnerability scan results from ParentCo

- **G-010**: Compliance certifications and audit reports
  - Why needed: SOC 2 and ISO alignment mentioned but no certification details provided. Need to understand compliance scope and any findings
  - Suggested source: Request SOC 2 Type II reports, ISO certifications, and any compliance audit findings

## Key Work Items

### W-001: Infrastructure Discovery and Dependency Mapping
- Domain: infrastructure
- Effort: 6-8 weeks
- Cost: $150K-$250K
- Phase: day_1

### W-002: Azure AD Tenant Separation and User Migration
- Domain: infrastructure
- Effort: 8-12 weeks
- Cost: $200K-$400K
- Phase: 0_90_days

### W-003: Server Infrastructure Migration
- Domain: infrastructure
- Effort: 16-24 weeks
- Cost: $800K-$1.5M
- Phase: 90_180_days

### W-004: Network Infrastructure Separation
- Domain: network
- Effort: 10-14 weeks
- Cost: $300K-$600K
- Phase: 0_90_days

### W-005: Device Management Integration
- Domain: infrastructure
- Effort: 6-10 weeks
- Cost: $150K-$300K
- Phase: 90_180_days

### W-006: TSA Infrastructure Services Setup
- Domain: cross-domain
- Effort: 4-6 weeks
- Cost: $100K-$200K
- Phase: day_1

### W-007: Network Discovery and Documentation
- Domain: network
- Effort: 4-6 weeks
- Cost: $50K-$100K
- Phase: day_1

### W-008: IP Address Conflict Analysis and Resolution Planning
- Domain: network
- Effort: 2-3 weeks
- Cost: $25K-$50K
- Phase: day_1

### W-009: Day 1 Connectivity Solution Design and Implementation
- Domain: network
- Effort: 6-8 weeks
- Cost: $100K-$250K
- Phase: day_1

### W-010: Network Security Migration and Firewall Configuration
- Domain: network
- Effort: 4-6 weeks
- Cost: $75K-$150K
- Phase: 0_90_days

### W-011: Permanent WAN Connectivity Implementation
- Domain: network
- Effort: 12-16 weeks
- Cost: $200K-$500K
- Phase: 90_180_days

### W-012: Comprehensive Security Assessment
- Domain: cybersecurity
- Effort: 6-8 weeks
- Cost: $75K-$150K
- Phase: day_1

### W-013: Identity and Access Management Migration
- Domain: cybersecurity
- Effort: 8-12 weeks
- Cost: $150K-$300K
- Phase: 0_90_days

### W-014: Security Operations Center (SOC) Establishment
- Domain: cybersecurity
- Effort: 12-16 weeks
- Cost: $200K-$500K
- Phase: 0_90_days

### W-015: Endpoint Security Migration
- Domain: cybersecurity
- Effort: 4-6 weeks
- Cost: $50K-$100K
- Phase: 0_90_days

## Strategic Recommendations

### REC-001: Negotiate comprehensive TSA covering all infrastructure domains for 12-18 months
- Priority: critical
- Timing: pre_close
- Rationale: TargetCo is fully integrated into ParentCo infrastructure with no independent capabilities. Separation will require 12-18 months minimum, and business continuity depends on ParentCo services during transition.

### REC-002: Prioritize Azure AD tenant separation as critical path item
- Priority: critical
- Timing: day_1
- Rationale: Identity is foundational to all other systems. Delays in Azure AD migration will cascade to application access, device management, and security tool deployment. Both companies use Azure AD, creating opportunity for streamlined integration.

### REC-003: Conduct immediate infrastructure discovery to validate server counts and identify end-of-life systems
- Priority: high
- Timing: day_1
- Rationale: Server count range of 110-130 indicates uncertainty. Need precise inventory to identify Windows Server 2012 R2, legacy Linux, and other end-of-life systems requiring immediate attention and budget allocation.

### REC-004: Immediately initiate network discovery and site survey to understand TargetCo's network dependencies within ParentCo
- Priority: critical
- Timing: pre_close
- Rationale: TargetCo operates entirely on ParentCo's shared network infrastructure with no independent network architecture. Without understanding the current topology, IP schemes, and site connectivity, it's impossible to plan separation or integration approach

### REC-005: Begin WAN circuit planning and ordering process immediately upon deal announcement
- Priority: high
- Timing: pre_close
- Rationale: Telecom circuits have 30-90 day lead times and TargetCo will need new connectivity independent from ParentCo. Delaying circuit orders will extend integration timeline and increase temporary connectivity costs

### REC-006: Plan for IP address renumbering as likely requirement for network integration
- Priority: high
- Timing: first_90_days
- Rationale: Both organizations likely use common RFC1918 address ranges which typically conflict. IP conflicts prevent network integration and must be resolved before full connectivity can be established

### REC-007: Conduct immediate security assessment before deal close
- Priority: critical
- Timing: pre_close
- Rationale: TargetCo's security posture is completely dependent on ParentCo with no independent assessment available. Unknown vulnerabilities or security gaps could represent significant liability

### REC-008: Negotiate extended ParentCo security services transition period
- Priority: critical
- Timing: pre_close
- Rationale: Complete security dependency on ParentCo creates critical risk if services are terminated abruptly. Need 6-12 month transition period to build independent capabilities

### REC-009: Establish interim managed security services
- Priority: high
- Timing: day_1
- Rationale: Loss of ParentCo SOC and security expertise creates immediate security monitoring gap. MSSP can provide bridge capability during transition

### REC-010: Prioritize identity migration planning
- Priority: high
- Timing: first_90_days
- Rationale: IAM migration affects all 650 users and 45+ applications. Poor execution could disrupt business operations and create security gaps

### REC-011: Accelerate compliance certification timeline
- Priority: high
- Timing: first_90_days
- Rationale: Loss of ParentCo compliance scope could impact customer contracts and business opportunities. Independent certifications needed quickly

### REC-012: Negotiate minimum 24-month TSA with ParentCo covering all IT services
- Priority: critical
- Timing: pre_close
- Rationale: Given the complete integration of TargetCo into ParentCo systems and sequential dependencies across domains, 18-24 months will be required for safe separation. Standard 12-month TSAs are insufficient for this complexity level.

### REC-013: Establish dedicated integration PMO with experienced carve-out specialists
- Priority: critical
- Timing: day_1
- Rationale: The complexity of separating from shared Azure AD, network infrastructure, and security systems requires specialized expertise and dedicated program management to coordinate sequential dependencies and minimize business disruption.

### REC-014: Begin Azure AD separation planning immediately post-close as critical path item
- Priority: critical
- Timing: day_1
- Rationale: Azure AD tenant separation is the foundational dependency for all other integration work. Delays here cascade to network and security migrations, potentially extending timeline to 30+ months.

### REC-015: Conduct immediate comprehensive technical discovery across all domains
- Priority: high
- Timing: pre_close
- Rationale: Critical gaps exist in network topology, security configurations, and infrastructure dependencies. Without this information, cost estimates could be 50-100% higher and timeline could extend significantly.

### REC-016: Implement comprehensive change management and communication program
- Priority: high
- Timing: first_90_days
- Rationale: 650 users will experience significant changes to identity, network access, security tools, and core applications over 18-24 months. Without proper change management, productivity loss and employee satisfaction issues are likely.