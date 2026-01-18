# IT Due Diligence Analysis Summary

Generated: 2026-01-05 20:11:08

## Domain Summaries

### Infrastructure
- Complexity: very_high
- Cost Range: $3M-$7M
- Timeline: 18-24 months
- Summary: TargetCo operates as a fully integrated business unit within ParentCo's infrastructure with complete dependency on parent systems including Azure AD, shared ERP/CRM/HCM platforms, and centralized IT operations. This creates a complex separation scenario requiring comprehensive infrastructure buildout and migration affecting 650 users, 620 devices, and 110-130 servers.

### Network
- Complexity: very_high
- Cost Range: $500K-$1.5M
- Timeline: 12-18 months
- Summary: TargetCo operates entirely on ParentCo's shared network infrastructure with no independent network assets, requiring complete network separation and buildout. Critical gaps exist in network topology, IP addressing, and connectivity details. Major risks include IP conflicts, circuit lead times, and DNS dependencies.

### Cybersecurity
- Complexity: very_high
- Cost Range: $1M-$2M first year, $500K-$800K annually
- Timeline: 12-18 months for full security independence
- Summary: TargetCo operates with complete dependency on ParentCo's security infrastructure including Azure AD, CrowdStrike EDR, Microsoft Sentinel SIEM, and centralized SOC. While this provides enterprise-grade security currently, it creates significant carve-out complexity requiring comprehensive security infrastructure rebuild. The 650 users and 620 endpoints will need complete identity migration and new security tooling stack.

### Cross-Domain
- Complexity: very_high
- Cost Range: $6M-$12M over 18-24 months
- Timeline: 18-24 months
- Summary: Project Atlas represents a very high complexity integration requiring complete separation of TargetCo from ParentCo's IT infrastructure. With 650 users, 620 devices, and 110-130 servers operating on fully shared systems, the integration demands comprehensive buildout across infrastructure, network, and cybersecurity domains. Critical path dependencies create an 18-24 month timeline with significant cost implications.

## Top Risks

### R-001: Complete dependency on ParentCo infrastructure creates complex separation requirements
- **Severity**: critical
- **Likelihood**: high
- **Domain**: cross-domain
- **Mitigation**: Negotiate extended TSA (18-24 months), phase migration approach, consider hybrid model initially

### R-005: Complete network separation required from ParentCo with no independent network infrastructure
- **Severity**: critical
- **Likelihood**: high
- **Domain**: network
- **Mitigation**: Immediately begin network discovery and circuit ordering process; establish temporary connectivity solutions for Day 1

### R-009: Complete dependency on ParentCo security infrastructure creates carve-out complexity
- **Severity**: critical
- **Likelihood**: high
- **Domain**: cybersecurity
- **Mitigation**: Establish standalone security infrastructure before carve-out or negotiate extended TSA for security services

### R-014: Cumulative critical path timeline risk - three long-lead dependencies create 18+ month integration timeline
- **Severity**: critical
- **Likelihood**: high
- **Domain**: cross-domain
- **Mitigation**: Negotiate minimum 18-month TSA, begin long-lead procurement immediately upon LOI, establish parallel workstreams where possible

### R-015: Complete business disruption risk during Day 1 cutover
- **Severity**: critical
- **Likelihood**: medium
- **Domain**: cross-domain
- **Mitigation**: Phased migration approach, maintain dual connectivity during transition, comprehensive Day 1 readiness testing

### R-002: Azure AD tenant mismatch between ParentCo and BuyerCo
- **Severity**: high
- **Likelihood**: high
- **Domain**: infrastructure
- **Mitigation**: Plan phased identity migration, implement identity bridging solutions, extensive testing of SSO integrations

### R-003: Shared ERP/CRM/HCM platforms require data separation and potential system replacement
- **Severity**: high
- **Likelihood**: high
- **Domain**: infrastructure
- **Mitigation**: Assess data separation feasibility, evaluate BuyerCo system capacity for integration, consider phased approach

### R-004: Key person dependency risk for infrastructure knowledge
- **Severity**: high
- **Likelihood**: medium
- **Domain**: infrastructure
- **Mitigation**: Immediate knowledge transfer sessions, documentation creation, retention bonuses for key ParentCo IT staff

### R-006: IP address conflicts between TargetCo and BuyerCo environments
- **Severity**: high
- **Likelihood**: high
- **Domain**: network
- **Mitigation**: Immediate IP address discovery and conflict analysis; prepare IP renumbering plan with NAT as temporary solution

### R-007: WAN circuit lead times may delay integration timeline
- **Severity**: high
- **Likelihood**: medium
- **Domain**: network
- **Mitigation**: Order circuits immediately upon deal announcement; establish temporary VPN connectivity for Day 1

## Critical Knowledge Gaps

- **G-001**: Specific hosting model breakdown (on-prem vs cloud percentages, data center locations)
  - Why needed: Critical for understanding separation complexity and migration scope - need to know what infrastructure needs to be carved out vs migrated
  - Suggested source: Technical assessment with ParentCo IT team, infrastructure inventory review

- **G-002**: Server operating systems, versions, and age distribution for 110-130 servers
  - Why needed: Essential for identifying EOL/EOS risks, migration complexity, and licensing requirements. Different OS versions have different migration paths and costs.
  - Suggested source: Server inventory export from ParentCo CMDB or asset management system

- **G-003**: Virtualization platform details (VMware vs Hyper-V vs cloud-native)
  - Why needed: Critical for migration planning - VMware has licensing implications post-Broadcom acquisition, different platforms require different migration tools and approaches
  - Suggested source: Infrastructure architecture documentation, hypervisor inventory

- **G-004**: Storage architecture, capacity, and data volumes
  - Why needed: Storage migration is often the most complex and time-consuming aspect of infrastructure separation. Need capacity for egress cost estimation and migration timeline planning.
  - Suggested source: Storage capacity reports, backup system reports

- **G-005**: TSA terms and duration for infrastructure services
  - Why needed: Critical for timeline planning and cost estimation. Infrastructure separation typically requires 12-24 months, need to ensure TSA covers this period.
  - Suggested source: Legal team review of purchase agreement TSA provisions

- **G-006**: Network architecture and connectivity requirements
  - Why needed: Need to understand network segmentation, bandwidth requirements, and connectivity dependencies to plan network separation and establish connectivity to BuyerCo environment
  - Suggested source: Network architecture documentation, bandwidth utilization reports

- **G-007**: Network topology and architecture details for TargetCo's current environment
  - Why needed: Critical for understanding separation requirements and Day 1 connectivity planning - need to know WAN architecture, site locations, circuit types, and network segmentation
  - Suggested source: Request network diagrams, site inventory, and circuit documentation from ParentCo IT team

- **G-008**: IP address scheme and VLAN assignments for TargetCo assets
  - Why needed: Essential for identifying IP conflicts with BuyerCo environment and planning network separation - conflicts will prevent Day 1 connectivity
  - Suggested source: IPAM system export or network documentation showing current IP allocations and subnet assignments

- **G-009**: WAN connectivity details including circuit types, carriers, and contract terms
  - Why needed: New circuits have 30-90 day lead times - must identify what connectivity needs to be ordered immediately to avoid timeline delays
  - Suggested source: Telecom contract review and site connectivity inventory from ParentCo

- **G-010**: DNS architecture and domain structure for TargetCo
  - Why needed: DNS integration is critical for application access and email functionality - need to understand current DNS zones and dependencies on ParentCo DNS infrastructure
  - Suggested source: DNS zone files and domain registration details from ParentCo IT

## Key Work Items

### W-001: Infrastructure Discovery and Dependency Mapping
- Domain: infrastructure
- Effort: 4-6 weeks
- Cost: $100K-$150K
- Phase: day_1

### W-002: Azure AD Tenant Migration Planning
- Domain: infrastructure
- Effort: 8-12 weeks
- Cost: $200K-$400K
- Phase: 0_90_days

### W-003: Server Migration to BuyerCo Environment
- Domain: infrastructure
- Effort: 16-24 weeks
- Cost: $800K-$1.5M
- Phase: 90_180_days

### W-004: Device Management Migration
- Domain: infrastructure
- Effort: 6-10 weeks
- Cost: $150K-$300K
- Phase: 0_90_days

### W-005: SaaS Application Migration and Reconfiguration
- Domain: infrastructure
- Effort: 12-16 weeks
- Cost: $300K-$600K
- Phase: 90_180_days

### W-006: Network Discovery and Documentation
- Domain: network
- Effort: 4-6 weeks
- Cost: $50K-$100K
- Phase: day_1

### W-007: WAN Circuit Procurement and Installation
- Domain: network
- Effort: 12-16 weeks
- Cost: $200K-$800K
- Phase: 0_90_days

### W-008: IP Address Conflict Analysis and Renumbering Plan
- Domain: network
- Effort: 6-8 weeks
- Cost: $75K-$200K
- Phase: 0_90_days

### W-009: Day 1 Temporary Connectivity Setup
- Domain: network
- Effort: 3-4 weeks
- Cost: $50K-$150K
- Phase: day_1

### W-010: DNS Migration and Domain Setup
- Domain: network
- Effort: 4-6 weeks
- Cost: $40K-$100K
- Phase: 0_90_days

### W-011: Network Security Infrastructure Deployment
- Domain: network
- Effort: 8-12 weeks
- Cost: $150K-$400K
- Phase: 90_180_days

### W-012: Identity Migration from ParentCo to BuyerCo Azure AD
- Domain: cybersecurity
- Effort: 8-12 weeks
- Cost: $150K-$300K
- Phase: 0_90_days

### W-013: Standalone Security Infrastructure Deployment
- Domain: cybersecurity
- Effort: 12-16 weeks
- Cost: $400K-$800K
- Phase: 0_90_days

### W-014: Pre-Close Security Assessment
- Domain: cybersecurity
- Effort: 4-6 weeks
- Cost: $75K-$150K
- Phase: day_1

### W-015: Compliance Certification Establishment
- Domain: cybersecurity
- Effort: 6-9 months
- Cost: $100K-$250K
- Phase: 90_180_days

## Strategic Recommendations

### REC-001: Negotiate extended TSA period (18-24 months) for infrastructure services
- Priority: critical
- Timing: pre_close
- Rationale: Complete infrastructure separation from ParentCo will be complex and time-consuming. Standard 12-month TSA periods are insufficient for this scope of work.

### REC-002: Implement phased migration approach starting with non-critical systems
- Priority: high
- Timing: day_1
- Rationale: Given the complete dependency on ParentCo infrastructure, a big-bang migration approach would be too risky. Phased approach allows for learning and risk mitigation.

### REC-003: Establish dedicated integration PMO with ParentCo liaison
- Priority: high
- Timing: day_1
- Rationale: Complex separation requires strong coordination between BuyerCo and ParentCo teams. Dedicated PMO ensures proper governance and communication.

### REC-004: Immediately initiate network discovery and circuit ordering process
- Priority: critical
- Timing: pre_close
- Rationale: TargetCo has no independent network infrastructure and relies entirely on ParentCo. WAN circuits have 30-90 day lead times which will be critical path for integration timeline

### REC-005: Develop comprehensive IP address conflict mitigation strategy
- Priority: critical
- Timing: pre_close
- Rationale: Both organizations likely use common RFC1918 address ranges which will create conflicts preventing Day 1 connectivity. This is a common integration blocker that requires early planning

### REC-006: Establish temporary connectivity solutions for Day 1 business continuity
- Priority: high
- Timing: day_1
- Rationale: Given the complete network separation required and circuit lead times, temporary solutions will be essential to maintain business operations while permanent infrastructure is deployed

### REC-007: Negotiate extended Transition Services Agreement (TSA) for security services
- Priority: critical
- Timing: pre_close
- Rationale: TargetCo has complete dependency on ParentCo security infrastructure. Immediate separation would create critical security gaps. TSA provides time to establish independent security capabilities while maintaining protection.

### REC-008: Conduct comprehensive security due diligence before close
- Priority: critical
- Timing: pre_close
- Rationale: No security assessment data provided and unknown vulnerability posture creates significant risk. Security assessment will identify gaps, compliance issues, and remediation costs that could affect deal valuation.

### REC-009: Establish security integration budget of $1M-$2M for first year
- Priority: high
- Timing: pre_close
- Rationale: Complete security infrastructure carve-out required including identity migration, security tooling, SOC establishment, and compliance certification. Costs are significant due to enterprise-grade security requirements.

### REC-010: Prioritize identity integration as critical path item
- Priority: critical
- Timing: day_1
- Rationale: 650 users depend on ParentCo Azure AD for authentication and application access. Identity migration is prerequisite for most other integration activities and has highest user impact if delayed.

### REC-011: Verify cyber insurance coverage for acquisition integration period
- Priority: high
- Timing: pre_close
- Rationale: Security infrastructure transition creates elevated risk period. Current ParentCo coverage may not extend to carved-out entity, and BuyerCo coverage may not include acquisition activities.

### REC-012: Negotiate minimum 18-month TSA with ParentCo covering all IT services including infrastructure, network, and security operations
- Priority: critical
- Timing: pre_close
- Rationale: The complete dependency on ParentCo systems and the critical path timeline of 18+ months requires extended transition services. Shorter TSA terms create unacceptable business continuity risk.

### REC-013: Establish $2M integration contingency fund for unforeseen complexities and timeline extensions
- Priority: high
- Timing: pre_close
- Rationale: Very high complexity integration with significant unknowns (15 critical gaps identified) and complete system separation required. Historical experience shows 20-30% cost overruns on complex carve-outs.

### REC-014: Immediately begin WAN circuit procurement and Azure AD tenant setup upon LOI signing
- Priority: critical
- Timing: pre_close
- Rationale: WAN circuits have 12-16 week lead times and Azure AD tenant migration requires 8-12 weeks. These are critical path items that can begin before close to compress overall timeline.

### REC-015: Conduct comprehensive technical due diligence to fill 15 critical information gaps before final valuation
- Priority: high
- Timing: pre_close
- Rationale: Current assessment has low confidence due to significant unknowns in network topology, security posture, and infrastructure details. These gaps could materially impact integration costs and timeline.