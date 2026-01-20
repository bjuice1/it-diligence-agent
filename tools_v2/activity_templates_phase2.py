"""
Activity Templates V2 - Phase 2: Network & Security

Phase 2: Carveout Network & Security
- Network Workstream (WAN, LAN, DNS, firewall)
- Security Workstream (endpoint, SIEM, vulnerability)
- Perimeter Workstream (VPN, proxy, web filtering)

Each activity template includes:
- name: Activity name
- description: What this activity involves
- activity_type: "implementation", "operational", "license", "operational_runrate"
- cost_model: How cost is calculated
- timeline_months: Duration range
- requires_tsa: Whether TSA is typically needed
- tsa_duration: TSA duration if applicable
- prerequisites: What must happen first
- outputs: Deliverables
- notes: Implementation considerations

Cost Anchor Sources:
- Market rates from network/security vendors
- MSP and MSSP pricing
- Historical deal data
- Industry benchmarks
"""

from typing import Dict, List, Any

# Import shared modifiers from Phase 1
from tools_v2.activity_templates_v2 import COMPLEXITY_MULTIPLIERS, INDUSTRY_MODIFIERS

# =============================================================================
# PHASE 2: NETWORK WORKSTREAM
# =============================================================================

NETWORK_TEMPLATES = {
    "parent_dependency": [
        # -----------------------------------------------------------------
        # ASSESSMENT & DESIGN
        # -----------------------------------------------------------------
        {
            "id": "NET-001",
            "name": "Network architecture assessment",
            "description": "Document current network topology, dependencies, and requirements for standalone operations",
            "activity_type": "implementation",
            "phase": "assessment",
            "base_cost": (30000, 75000),
            "timeline_months": (0.5, 1.5),
            "requires_tsa": False,
            "prerequisites": [],
            "outputs": ["Network topology diagram", "Dependency map", "Circuit inventory", "IP addressing scheme"],
            "notes": "Critical first step - informs all network separation activities",
        },
        {
            "id": "NET-002",
            "name": "WAN circuit inventory",
            "description": "Inventory all WAN circuits, contracts, and SLAs",
            "activity_type": "implementation",
            "phase": "assessment",
            "base_cost": (15000, 35000),
            "timeline_months": (0.25, 0.5),
            "requires_tsa": False,
            "prerequisites": ["NET-001"],
            "outputs": ["Circuit inventory", "Contract summary", "SLA requirements", "Bandwidth utilization"],
        },
        {
            "id": "NET-003",
            "name": "IP addressing and DNS analysis",
            "description": "Analyze IP addressing scheme, DNS infrastructure, and DHCP requirements",
            "activity_type": "implementation",
            "phase": "assessment",
            "base_cost": (20000, 45000),
            "timeline_months": (0.5, 1),
            "requires_tsa": False,
            "prerequisites": ["NET-001"],
            "outputs": ["IP address inventory", "DNS zone inventory", "DHCP scope analysis", "Addressing conflicts"],
        },
        {
            "id": "NET-004",
            "name": "Firewall rule analysis",
            "description": "Document firewall rules, policies, and traffic flows",
            "activity_type": "implementation",
            "phase": "assessment",
            "per_site_cost": (3000, 8000),
            "base_cost": (15000, 35000),
            "timeline_months": (0.5, 1.5),
            "requires_tsa": False,
            "prerequisites": ["NET-001"],
            "outputs": ["Firewall rule inventory", "Traffic flow documentation", "Rule optimization recommendations"],
            "notes": "Complexity varies significantly by rule count and documentation quality",
        },
        {
            "id": "NET-005",
            "name": "Network target architecture design",
            "description": "Design target-state network architecture for standalone operations",
            "activity_type": "implementation",
            "phase": "design",
            "base_cost": (50000, 125000),
            "timeline_months": (1, 2),
            "requires_tsa": False,
            "prerequisites": ["NET-001", "NET-002", "NET-003", "NET-004"],
            "outputs": ["Target network architecture", "Addressing scheme", "Routing design", "Security zones"],
        },
        # -----------------------------------------------------------------
        # WAN IMPLEMENTATION
        # -----------------------------------------------------------------
        {
            "id": "NET-010",
            "name": "MPLS circuit provisioning",
            "description": "Procure and provision MPLS circuits for WAN connectivity",
            "activity_type": "implementation",
            "phase": "build",
            "per_site_cost": (8000, 20000),
            "timeline_months": (2, 4),
            "requires_tsa": True,
            "tsa_duration": (3, 6),
            "prerequisites": ["NET-005"],
            "outputs": ["MPLS circuits", "Carrier contracts", "SLA documentation"],
            "notes": "Lead times for MPLS can be 60-90 days; often critical path",
        },
        {
            "id": "NET-011",
            "name": "SD-WAN deployment",
            "description": "Deploy SD-WAN overlay network for site connectivity",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (40000, 100000),
            "per_site_cost": (3000, 8000),
            "timeline_months": (1, 3),
            "requires_tsa": True,
            "tsa_duration": (2, 4),
            "prerequisites": ["NET-005"],
            "outputs": ["SD-WAN fabric", "Policy configuration", "Application prioritization"],
            "notes": "Increasingly common alternative to MPLS; faster deployment",
        },
        {
            "id": "NET-012",
            "name": "Internet circuit provisioning",
            "description": "Procure internet circuits for each site",
            "activity_type": "implementation",
            "phase": "build",
            "per_site_cost": (2000, 6000),
            "timeline_months": (1, 3),
            "requires_tsa": True,
            "tsa_duration": (2, 4),
            "prerequisites": ["NET-005"],
            "outputs": ["Internet circuits", "ISP contracts", "Redundancy configuration"],
        },
        {
            "id": "NET-013",
            "name": "WAN circuit migration/cutover",
            "description": "Execute migration from parent WAN to standalone circuits",
            "activity_type": "implementation",
            "phase": "build",
            "per_site_cost": (2000, 5000),
            "timeline_months": (1, 2),
            "requires_tsa": True,
            "tsa_duration": (1, 3),
            "prerequisites": ["NET-010", "NET-011", "NET-012"],
            "outputs": ["Migrated circuits", "Cutover validation", "Performance baseline"],
        },
        # -----------------------------------------------------------------
        # LAN IMPLEMENTATION
        # -----------------------------------------------------------------
        {
            "id": "NET-020",
            "name": "LAN switch configuration",
            "description": "Configure or replace LAN switches for standalone operations",
            "activity_type": "implementation",
            "phase": "build",
            "per_site_cost": (5000, 15000),
            "timeline_months": (1, 2),
            "requires_tsa": False,
            "prerequisites": ["NET-005"],
            "outputs": ["Configured switches", "VLAN design", "Port assignments"],
        },
        {
            "id": "NET-021",
            "name": "VLAN segmentation implementation",
            "description": "Implement network segmentation via VLANs",
            "activity_type": "implementation",
            "phase": "build",
            "per_site_cost": (3000, 8000),
            "timeline_months": (0.5, 1.5),
            "requires_tsa": False,
            "prerequisites": ["NET-020"],
            "outputs": ["VLAN configuration", "Inter-VLAN routing", "Segmentation policies"],
        },
        {
            "id": "NET-022",
            "name": "Wireless infrastructure deployment",
            "description": "Deploy or reconfigure wireless infrastructure",
            "activity_type": "implementation",
            "phase": "build",
            "per_site_cost": (8000, 25000),
            "timeline_months": (1, 2),
            "requires_tsa": False,
            "prerequisites": ["NET-005"],
            "outputs": ["Wireless deployment", "Controller configuration", "SSID design", "Guest network"],
        },
        {
            "id": "NET-023",
            "name": "Network access control (NAC) implementation",
            "description": "Implement 802.1X or other NAC solution",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (35000, 90000),
            "timeline_months": (1, 3),
            "requires_tsa": False,
            "prerequisites": ["NET-020", "NET-022"],
            "outputs": ["NAC deployment", "Authentication policies", "Posture assessment", "Guest provisioning"],
            "notes": "Often deferred post-Day 1 due to complexity",
        },
        # -----------------------------------------------------------------
        # SECURITY CONTROLS
        # -----------------------------------------------------------------
        {
            "id": "NET-030",
            "name": "Firewall deployment",
            "description": "Deploy firewall infrastructure at network perimeter and internal zones",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (40000, 100000),
            "per_site_cost": (5000, 15000),
            "timeline_months": (1, 2),
            "requires_tsa": False,
            "prerequisites": ["NET-005"],
            "outputs": ["Firewall deployment", "Base rule set", "Management configuration"],
        },
        {
            "id": "NET-031",
            "name": "Firewall rule migration",
            "description": "Migrate and optimize firewall rules from parent environment",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (25000, 75000),
            "timeline_months": (1, 3),
            "requires_tsa": True,
            "tsa_duration": (2, 4),
            "prerequisites": ["NET-030", "NET-004"],
            "outputs": ["Migrated rules", "Rule optimization", "Testing validation"],
            "notes": "Often underestimated - legacy rules may be undocumented",
        },
        {
            "id": "NET-032",
            "name": "IDS/IPS implementation",
            "description": "Deploy intrusion detection/prevention system",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (30000, 80000),
            "timeline_months": (0.5, 1.5),
            "requires_tsa": False,
            "prerequisites": ["NET-030"],
            "outputs": ["IDS/IPS deployment", "Signature tuning", "Alert integration"],
        },
        {
            "id": "NET-033",
            "name": "Network segmentation enforcement",
            "description": "Implement micro-segmentation or zero-trust network controls",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (50000, 150000),
            "timeline_months": (2, 4),
            "requires_tsa": False,
            "prerequisites": ["NET-030", "NET-021"],
            "outputs": ["Segmentation policies", "Application-aware rules", "East-west traffic control"],
            "notes": "Advanced capability - often post-Day 1 initiative",
        },
        # -----------------------------------------------------------------
        # DNS & SERVICES
        # -----------------------------------------------------------------
        {
            "id": "NET-040",
            "name": "DNS infrastructure deployment",
            "description": "Deploy DNS servers and configure zones",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (20000, 50000),
            "timeline_months": (0.5, 1),
            "requires_tsa": False,
            "prerequisites": ["NET-005"],
            "outputs": ["DNS servers", "Zone configuration", "Forwarding rules"],
        },
        {
            "id": "NET-041",
            "name": "DNS zone separation",
            "description": "Separate DNS zones from parent and establish standalone DNS",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (15000, 40000),
            "per_domain_cost": (2000, 5000),
            "timeline_months": (0.5, 1.5),
            "requires_tsa": True,
            "tsa_duration": (2, 4),
            "prerequisites": ["NET-040"],
            "outputs": ["Separated zones", "Record migration", "Delegation updates"],
        },
        {
            "id": "NET-042",
            "name": "DHCP infrastructure deployment",
            "description": "Deploy and configure DHCP services",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (10000, 25000),
            "per_site_cost": (1000, 3000),
            "timeline_months": (0.25, 0.75),
            "requires_tsa": False,
            "prerequisites": ["NET-005"],
            "outputs": ["DHCP servers", "Scope configuration", "Reservations"],
        },
        {
            "id": "NET-043",
            "name": "NTP/time services configuration",
            "description": "Configure time synchronization infrastructure",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (5000, 15000),
            "timeline_months": (0.25, 0.5),
            "requires_tsa": False,
            "prerequisites": ["NET-005"],
            "outputs": ["NTP servers", "Time sync policies", "Stratum configuration"],
        },
        {
            "id": "NET-044",
            "name": "Certificate services deployment",
            "description": "Deploy PKI/certificate authority infrastructure",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (30000, 80000),
            "timeline_months": (1, 2),
            "requires_tsa": False,
            "prerequisites": ["NET-005"],
            "outputs": ["PKI infrastructure", "Certificate templates", "Enrollment services", "CRL/OCSP"],
            "notes": "Critical for internal SSL, device auth, and code signing",
        },
        # -----------------------------------------------------------------
        # OPERATIONS
        # -----------------------------------------------------------------
        {
            "id": "NET-050",
            "name": "Network monitoring deployment",
            "description": "Deploy network monitoring and alerting tools",
            "activity_type": "implementation",
            "phase": "operations",
            "base_cost": (20000, 50000),
            "timeline_months": (0.5, 1),
            "requires_tsa": False,
            "prerequisites": ["NET-020", "NET-030"],
            "outputs": ["Monitoring platform", "SNMP configuration", "Alert rules", "Dashboards"],
        },
        {
            "id": "NET-051",
            "name": "Network documentation and runbooks",
            "description": "Create operational documentation for network infrastructure",
            "activity_type": "implementation",
            "phase": "operations",
            "base_cost": (15000, 35000),
            "timeline_months": (0.5, 1),
            "requires_tsa": False,
            "prerequisites": ["NET-050"],
            "outputs": ["Network documentation", "Runbooks", "Escalation procedures"],
        },
    ],
}

# =============================================================================
# PHASE 2: SECURITY WORKSTREAM
# =============================================================================

SECURITY_TEMPLATES = {
    "parent_dependency": [
        # -----------------------------------------------------------------
        # ASSESSMENT & DESIGN
        # -----------------------------------------------------------------
        {
            "id": "SEC-001",
            "name": "Security architecture assessment",
            "description": "Assess current security controls, tools, and processes",
            "activity_type": "implementation",
            "phase": "assessment",
            "base_cost": (35000, 85000),
            "timeline_months": (0.5, 1.5),
            "requires_tsa": False,
            "prerequisites": [],
            "outputs": ["Security inventory", "Control mapping", "Gap analysis", "Risk assessment"],
        },
        {
            "id": "SEC-002",
            "name": "Security tool inventory",
            "description": "Inventory all security tools, licenses, and configurations",
            "activity_type": "implementation",
            "phase": "assessment",
            "base_cost": (15000, 35000),
            "timeline_months": (0.25, 0.75),
            "requires_tsa": False,
            "prerequisites": ["SEC-001"],
            "outputs": ["Tool inventory", "License status", "Configuration baseline", "Contract review"],
        },
        {
            "id": "SEC-003",
            "name": "Compliance requirements mapping",
            "description": "Map regulatory and compliance requirements for standalone operations",
            "activity_type": "implementation",
            "phase": "assessment",
            "base_cost": (25000, 60000),
            "timeline_months": (0.5, 1),
            "requires_tsa": False,
            "prerequisites": ["SEC-001"],
            "outputs": ["Compliance matrix", "Control requirements", "Gap identification", "Remediation plan"],
            "notes": "Critical for regulated industries (financial services, healthcare)",
        },
        {
            "id": "SEC-004",
            "name": "Security architecture design",
            "description": "Design target-state security architecture",
            "activity_type": "implementation",
            "phase": "design",
            "base_cost": (50000, 120000),
            "timeline_months": (1, 2),
            "requires_tsa": False,
            "prerequisites": ["SEC-001", "SEC-002", "SEC-003"],
            "outputs": ["Security architecture", "Tool selection", "Control framework", "Implementation roadmap"],
        },
        # -----------------------------------------------------------------
        # ENDPOINT SECURITY
        # -----------------------------------------------------------------
        {
            "id": "SEC-010",
            "name": "EDR platform deployment",
            "description": "Deploy endpoint detection and response solution",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (30000, 75000),
            "per_endpoint_cost": (10, 30),
            "timeline_months": (1, 2),
            "requires_tsa": True,
            "tsa_duration": (2, 4),
            "prerequisites": ["SEC-004"],
            "outputs": ["EDR deployment", "Policy configuration", "Alert tuning", "Response playbooks"],
        },
        {
            "id": "SEC-011",
            "name": "Antivirus/antimalware migration",
            "description": "Migrate or deploy antivirus solution for standalone environment",
            "activity_type": "implementation",
            "phase": "build",
            "per_endpoint_cost": (5, 15),
            "timeline_months": (0.5, 1.5),
            "requires_tsa": True,
            "tsa_duration": (2, 4),
            "prerequisites": ["SEC-004"],
            "outputs": ["AV deployment", "Definition management", "Exclusion policies"],
            "notes": "May be bundled with EDR in modern deployments",
        },
        {
            "id": "SEC-012",
            "name": "Device encryption enforcement",
            "description": "Implement full disk encryption (BitLocker, FileVault)",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (15000, 40000),
            "per_endpoint_cost": (5, 15),
            "timeline_months": (0.5, 1.5),
            "requires_tsa": False,
            "prerequisites": ["SEC-004"],
            "outputs": ["Encryption deployment", "Key management", "Recovery procedures"],
        },
        {
            "id": "SEC-013",
            "name": "Mobile device management deployment",
            "description": "Deploy MDM/UEM solution for mobile devices",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (25000, 60000),
            "per_device_cost": (10, 25),
            "timeline_months": (1, 2),
            "requires_tsa": True,
            "tsa_duration": (2, 4),
            "prerequisites": ["SEC-004"],
            "outputs": ["MDM platform", "Device policies", "App management", "Conditional access"],
        },
        {
            "id": "SEC-014",
            "name": "Endpoint hardening implementation",
            "description": "Implement endpoint hardening standards (CIS benchmarks)",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (30000, 70000),
            "timeline_months": (1, 2),
            "requires_tsa": False,
            "prerequisites": ["SEC-004"],
            "outputs": ["Hardening standards", "GPO/MDM policies", "Compliance reporting"],
        },
        # -----------------------------------------------------------------
        # SECURITY OPERATIONS
        # -----------------------------------------------------------------
        {
            "id": "SEC-020",
            "name": "SIEM platform deployment",
            "description": "Deploy security information and event management platform",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (75000, 200000),
            "timeline_months": (2, 4),
            "requires_tsa": True,
            "tsa_duration": (3, 6),
            "prerequisites": ["SEC-004"],
            "outputs": ["SIEM deployment", "Log sources", "Correlation rules", "Dashboards"],
            "notes": "Major investment - consider cloud SIEM vs on-prem",
        },
        {
            "id": "SEC-021",
            "name": "Log aggregation configuration",
            "description": "Configure log collection from all security-relevant sources",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (25000, 60000),
            "timeline_months": (1, 2),
            "requires_tsa": False,
            "prerequisites": ["SEC-020"],
            "outputs": ["Log collection", "Parsing rules", "Retention policies", "Archive configuration"],
        },
        {
            "id": "SEC-022",
            "name": "Security alert tuning",
            "description": "Tune SIEM alerts to reduce false positives",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (20000, 50000),
            "timeline_months": (1, 3),
            "requires_tsa": False,
            "prerequisites": ["SEC-020", "SEC-021"],
            "outputs": ["Tuned alerts", "Threshold optimization", "False positive reduction"],
            "notes": "Ongoing activity - initial tuning takes 2-3 months",
        },
        {
            "id": "SEC-023",
            "name": "SOC procedures development",
            "description": "Develop security operations procedures and playbooks",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (25000, 60000),
            "timeline_months": (1, 2),
            "requires_tsa": False,
            "prerequisites": ["SEC-020"],
            "outputs": ["SOC procedures", "Incident playbooks", "Escalation procedures", "Reporting templates"],
        },
        {
            "id": "SEC-024",
            "name": "Security orchestration (SOAR) deployment",
            "description": "Deploy security orchestration, automation and response platform",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (50000, 150000),
            "timeline_months": (2, 4),
            "requires_tsa": False,
            "prerequisites": ["SEC-020"],
            "outputs": ["SOAR platform", "Automated playbooks", "Integration configuration"],
            "notes": "Advanced capability - often post-Day 1 enhancement",
        },
        # -----------------------------------------------------------------
        # VULNERABILITY MANAGEMENT
        # -----------------------------------------------------------------
        {
            "id": "SEC-030",
            "name": "Vulnerability scanner deployment",
            "description": "Deploy vulnerability scanning infrastructure",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (30000, 75000),
            "timeline_months": (0.5, 1.5),
            "requires_tsa": False,
            "prerequisites": ["SEC-004"],
            "outputs": ["Scanner deployment", "Scan policies", "Credential configuration"],
        },
        {
            "id": "SEC-031",
            "name": "Baseline vulnerability assessment",
            "description": "Execute initial vulnerability scan and establish baseline",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (20000, 50000),
            "timeline_months": (0.5, 1),
            "requires_tsa": False,
            "prerequisites": ["SEC-030"],
            "outputs": ["Baseline scan results", "Risk prioritization", "Remediation plan"],
        },
        {
            "id": "SEC-032",
            "name": "Vulnerability remediation program",
            "description": "Establish ongoing vulnerability remediation process",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (25000, 60000),
            "timeline_months": (1, 2),
            "requires_tsa": False,
            "prerequisites": ["SEC-031"],
            "outputs": ["Remediation process", "SLA definitions", "Exception handling", "Reporting"],
        },
        {
            "id": "SEC-033",
            "name": "Patch management implementation",
            "description": "Implement patch management process and tooling",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (30000, 70000),
            "timeline_months": (1, 2),
            "requires_tsa": False,
            "prerequisites": ["SEC-004"],
            "outputs": ["Patch management tool", "Patch policies", "Testing procedures", "Deployment automation"],
        },
        # -----------------------------------------------------------------
        # IDENTITY SECURITY (complements Identity workstream)
        # -----------------------------------------------------------------
        {
            "id": "SEC-040",
            "name": "Privileged access management (PAM) deployment",
            "description": "Deploy PAM solution for privileged account security",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (75000, 200000),
            "timeline_months": (2, 4),
            "requires_tsa": True,
            "tsa_duration": (3, 6),
            "prerequisites": ["SEC-004"],
            "outputs": ["PAM platform", "Privileged account vault", "Session recording", "Just-in-time access"],
            "notes": "Critical for compliance and security - high value target",
        },
        {
            "id": "SEC-041",
            "name": "Service account vault implementation",
            "description": "Implement secure storage and rotation for service accounts",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (35000, 85000),
            "per_account_cost": (100, 300),
            "timeline_months": (1, 2),
            "requires_tsa": True,
            "tsa_duration": (2, 4),
            "prerequisites": ["SEC-040"],
            "outputs": ["Service account vault", "Password rotation", "API integration"],
        },
        {
            "id": "SEC-042",
            "name": "Access review implementation",
            "description": "Implement periodic access review process",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (25000, 60000),
            "timeline_months": (1, 2),
            "requires_tsa": False,
            "prerequisites": ["SEC-004"],
            "outputs": ["Access review process", "Review campaigns", "Attestation workflow", "Remediation process"],
        },
        {
            "id": "SEC-043",
            "name": "Identity governance platform deployment",
            "description": "Deploy IGA platform for identity lifecycle management",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (100000, 300000),
            "timeline_months": (3, 6),
            "requires_tsa": False,
            "prerequisites": ["SEC-004"],
            "outputs": ["IGA platform", "Provisioning workflows", "Role management", "Certification campaigns"],
            "notes": "Major initiative - often post-Day 1 for complex environments",
        },
        # -----------------------------------------------------------------
        # DATA SECURITY
        # -----------------------------------------------------------------
        {
            "id": "SEC-050",
            "name": "Data loss prevention deployment",
            "description": "Deploy DLP solution for sensitive data protection",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (50000, 150000),
            "timeline_months": (2, 4),
            "requires_tsa": True,
            "tsa_duration": (3, 6),
            "prerequisites": ["SEC-004"],
            "outputs": ["DLP platform", "Policy configuration", "Incident workflow", "User notification"],
        },
        {
            "id": "SEC-051",
            "name": "Data classification implementation",
            "description": "Implement data classification labels and policies",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (30000, 75000),
            "timeline_months": (1, 3),
            "requires_tsa": False,
            "prerequisites": ["SEC-050"],
            "outputs": ["Classification taxonomy", "Labeling policies", "User training", "Automated classification"],
        },
        {
            "id": "SEC-052",
            "name": "Encryption key management",
            "description": "Implement enterprise key management solution",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (40000, 100000),
            "timeline_months": (1, 2),
            "requires_tsa": False,
            "prerequisites": ["SEC-004"],
            "outputs": ["Key management platform", "Key hierarchy", "Rotation policies", "Recovery procedures"],
        },
    ],
    "security_gap": [
        # Additional activities specific to security gap remediation
        {
            "id": "SEC-060",
            "name": "Security gap remediation assessment",
            "description": "Detailed assessment of security gaps requiring remediation",
            "activity_type": "implementation",
            "phase": "assessment",
            "base_cost": (25000, 60000),
            "timeline_months": (0.5, 1),
            "requires_tsa": False,
            "prerequisites": ["SEC-001"],
            "outputs": ["Gap analysis", "Risk ranking", "Remediation roadmap", "Quick wins identification"],
        },
        {
            "id": "SEC-061",
            "name": "Security quick wins implementation",
            "description": "Implement high-impact, low-effort security improvements",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (20000, 50000),
            "timeline_months": (0.5, 1),
            "requires_tsa": False,
            "prerequisites": ["SEC-060"],
            "outputs": ["Implemented controls", "Risk reduction metrics", "Updated baseline"],
        },
        {
            "id": "SEC-062",
            "name": "Penetration testing",
            "description": "Execute penetration test of new environment",
            "activity_type": "implementation",
            "phase": "validation",
            "base_cost": (40000, 100000),
            "timeline_months": (0.5, 1),
            "requires_tsa": False,
            "prerequisites": ["SEC-004"],
            "outputs": ["Pen test report", "Finding remediation", "Attestation"],
            "notes": "Often required for compliance and risk validation",
        },
    ],
}

# =============================================================================
# PHASE 2: PERIMETER WORKSTREAM
# =============================================================================

PERIMETER_TEMPLATES = {
    "parent_dependency": [
        # -----------------------------------------------------------------
        # ASSESSMENT & DESIGN
        # -----------------------------------------------------------------
        {
            "id": "PER-001",
            "name": "Perimeter security assessment",
            "description": "Assess current perimeter controls and remote access capabilities",
            "activity_type": "implementation",
            "phase": "assessment",
            "base_cost": (25000, 55000),
            "timeline_months": (0.5, 1),
            "requires_tsa": False,
            "prerequisites": [],
            "outputs": ["Perimeter inventory", "Remote access assessment", "External exposure review"],
        },
        {
            "id": "PER-002",
            "name": "Perimeter architecture design",
            "description": "Design target-state perimeter and remote access architecture",
            "activity_type": "implementation",
            "phase": "design",
            "base_cost": (35000, 80000),
            "timeline_months": (0.5, 1.5),
            "requires_tsa": False,
            "prerequisites": ["PER-001"],
            "outputs": ["Perimeter design", "Zero trust roadmap", "SASE evaluation"],
        },
        # -----------------------------------------------------------------
        # VPN & REMOTE ACCESS
        # -----------------------------------------------------------------
        {
            "id": "PER-010",
            "name": "VPN infrastructure deployment",
            "description": "Deploy remote access VPN infrastructure",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (30000, 80000),
            "timeline_months": (1, 2),
            "requires_tsa": True,
            "tsa_duration": (2, 4),
            "prerequisites": ["PER-002"],
            "outputs": ["VPN deployment", "Split tunnel policies", "MFA integration", "Client deployment"],
        },
        {
            "id": "PER-011",
            "name": "VPN user migration",
            "description": "Migrate users from parent VPN to standalone",
            "activity_type": "implementation",
            "phase": "migration",
            "per_user_cost": (5, 15),
            "timeline_months": (0.5, 1.5),
            "requires_tsa": True,
            "tsa_duration": (2, 4),
            "prerequisites": ["PER-010"],
            "outputs": ["Migrated VPN users", "Client deployment", "User communication"],
        },
        {
            "id": "PER-012",
            "name": "Site-to-site VPN configuration",
            "description": "Configure site-to-site VPN tunnels",
            "activity_type": "implementation",
            "phase": "build",
            "per_site_cost": (3000, 8000),
            "timeline_months": (0.5, 1.5),
            "requires_tsa": True,
            "tsa_duration": (2, 4),
            "prerequisites": ["PER-002"],
            "outputs": ["S2S VPN tunnels", "Routing configuration", "Failover testing"],
        },
        {
            "id": "PER-013",
            "name": "Zero trust network access (ZTNA) deployment",
            "description": "Deploy ZTNA solution for modern remote access",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (50000, 150000),
            "per_user_cost": (10, 30),
            "timeline_months": (2, 4),
            "requires_tsa": True,
            "tsa_duration": (2, 4),
            "prerequisites": ["PER-002"],
            "outputs": ["ZTNA platform", "Application connectors", "Policy configuration", "User onboarding"],
            "notes": "Modern alternative to VPN - increasingly common",
        },
        # -----------------------------------------------------------------
        # WEB SECURITY
        # -----------------------------------------------------------------
        {
            "id": "PER-020",
            "name": "Secure web gateway deployment",
            "description": "Deploy secure web gateway for internet access control",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (35000, 90000),
            "timeline_months": (1, 2),
            "requires_tsa": True,
            "tsa_duration": (2, 4),
            "prerequisites": ["PER-002"],
            "outputs": ["SWG deployment", "URL filtering", "SSL inspection", "Policy configuration"],
        },
        {
            "id": "PER-021",
            "name": "Web proxy configuration",
            "description": "Configure web proxy and filtering policies",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (15000, 40000),
            "timeline_months": (0.5, 1),
            "requires_tsa": False,
            "prerequisites": ["PER-020"],
            "outputs": ["Proxy policies", "Category filtering", "Exception handling", "Bypass rules"],
        },
        {
            "id": "PER-022",
            "name": "Cloud access security broker (CASB) deployment",
            "description": "Deploy CASB for SaaS security and visibility",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (50000, 150000),
            "timeline_months": (2, 4),
            "requires_tsa": True,
            "tsa_duration": (3, 6),
            "prerequisites": ["PER-002"],
            "outputs": ["CASB deployment", "SaaS discovery", "Policy enforcement", "DLP integration"],
            "notes": "Critical for SaaS-heavy environments",
        },
        {
            "id": "PER-023",
            "name": "DNS security deployment",
            "description": "Deploy DNS-based security filtering",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (15000, 40000),
            "timeline_months": (0.5, 1),
            "requires_tsa": False,
            "prerequisites": ["PER-002"],
            "outputs": ["DNS security", "Category filtering", "Threat intelligence integration"],
        },
        # -----------------------------------------------------------------
        # EMAIL SECURITY
        # -----------------------------------------------------------------
        {
            "id": "PER-030",
            "name": "Email security gateway deployment",
            "description": "Deploy email security gateway (SEG)",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (30000, 80000),
            "per_user_cost": (3, 10),
            "timeline_months": (1, 2),
            "requires_tsa": True,
            "tsa_duration": (2, 4),
            "prerequisites": ["PER-002"],
            "outputs": ["SEG deployment", "Mail flow configuration", "Policy setup", "Quarantine management"],
        },
        {
            "id": "PER-031",
            "name": "Email authentication configuration",
            "description": "Configure SPF, DKIM, DMARC for email authentication",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (10000, 25000),
            "per_domain_cost": (1000, 3000),
            "timeline_months": (0.5, 1),
            "requires_tsa": False,
            "prerequisites": ["PER-030"],
            "outputs": ["SPF records", "DKIM signing", "DMARC policy", "Reporting configuration"],
        },
        {
            "id": "PER-032",
            "name": "Anti-phishing protection deployment",
            "description": "Deploy advanced anti-phishing and impersonation protection",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (20000, 50000),
            "timeline_months": (0.5, 1.5),
            "requires_tsa": False,
            "prerequisites": ["PER-030"],
            "outputs": ["Phishing protection", "Brand impersonation rules", "User reporting", "Training integration"],
        },
        # -----------------------------------------------------------------
        # SASE/CONSOLIDATION
        # -----------------------------------------------------------------
        {
            "id": "PER-040",
            "name": "SASE platform deployment",
            "description": "Deploy converged SASE platform (Zscaler, Palo Alto, etc.)",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (100000, 300000),
            "per_user_cost": (20, 60),
            "timeline_months": (3, 6),
            "requires_tsa": True,
            "tsa_duration": (3, 6),
            "prerequisites": ["PER-002"],
            "outputs": ["SASE deployment", "Unified policy", "Global PoP integration"],
            "notes": "Consolidates SWG, CASB, ZTNA, firewall - major transformation",
        },
        {
            "id": "PER-041",
            "name": "Perimeter service migration",
            "description": "Migrate from point solutions to SASE platform",
            "activity_type": "implementation",
            "phase": "migration",
            "base_cost": (40000, 100000),
            "timeline_months": (2, 4),
            "requires_tsa": True,
            "tsa_duration": (2, 4),
            "prerequisites": ["PER-040"],
            "outputs": ["Migrated services", "Decommissioned legacy", "Unified management"],
        },
    ],
}

# =============================================================================
# COMBINED TEMPLATES FOR PHASE 2
# =============================================================================

def get_phase2_templates() -> Dict[str, Dict[str, List[Dict]]]:
    """Get all Phase 2 templates organized by category and workstream."""
    return {
        "parent_dependency": {
            "network": NETWORK_TEMPLATES["parent_dependency"],
            "security": SECURITY_TEMPLATES["parent_dependency"],
            "perimeter": PERIMETER_TEMPLATES["parent_dependency"],
        },
        "security_gap": {
            "security": SECURITY_TEMPLATES.get("security_gap", []),
        },
    }


def get_phase2_activity_by_id(activity_id: str) -> Dict:
    """Look up a Phase 2 activity by its ID."""
    all_templates = get_phase2_templates()

    for category, workstreams in all_templates.items():
        for workstream, activities in workstreams.items():
            for activity in activities:
                if activity.get("id") == activity_id:
                    return activity

    return None


def calculate_phase2_activity_cost(
    activity: Dict,
    user_count: int = 1000,
    site_count: int = 5,
    endpoint_count: int = None,
    device_count: int = None,
    account_count: int = 50,
    domain_count: int = 3,
    complexity: str = "moderate",
    industry: str = "standard",
) -> tuple:
    """
    Calculate cost range for a Phase 2 activity based on quantities and modifiers.

    Returns: (low, high, formula)
    """
    endpoint_count = endpoint_count or int(user_count * 1.5)  # Avg 1.5 devices per user
    device_count = device_count or int(user_count * 0.5)  # Mobile devices

    # Get complexity and industry multipliers
    complexity_mult = COMPLEXITY_MULTIPLIERS.get(complexity, 1.0)
    industry_mult = INDUSTRY_MODIFIERS.get(industry, 1.0)
    combined_mult = complexity_mult * industry_mult

    # Calculate base cost
    if "base_cost" in activity:
        low, high = activity["base_cost"]
        formula = f"Base: ${low:,.0f}-${high:,.0f}"

        # Add per-unit costs if present
        if "per_site_cost" in activity:
            per_low, per_high = activity["per_site_cost"]
            low += per_low * site_count
            high += per_high * site_count
            formula += f" + {site_count} sites × ${per_low:,}-${per_high:,}"

        if "per_user_cost" in activity:
            per_low, per_high = activity["per_user_cost"]
            low += per_low * user_count
            high += per_high * user_count
            formula += f" + {user_count:,} users × ${per_low}-${per_high}"

        if "per_endpoint_cost" in activity:
            per_low, per_high = activity["per_endpoint_cost"]
            low += per_low * endpoint_count
            high += per_high * endpoint_count
            formula += f" + {endpoint_count:,} endpoints × ${per_low}-${per_high}"

        if "per_device_cost" in activity:
            per_low, per_high = activity["per_device_cost"]
            low += per_low * device_count
            high += per_high * device_count
            formula += f" + {device_count:,} devices × ${per_low}-${per_high}"

        if "per_account_cost" in activity:
            per_low, per_high = activity["per_account_cost"]
            low += per_low * account_count
            high += per_high * account_count
            formula += f" + {account_count} accounts × ${per_low:,}-${per_high:,}"

        if "per_domain_cost" in activity:
            per_low, per_high = activity["per_domain_cost"]
            low += per_low * domain_count
            high += per_high * domain_count
            formula += f" + {domain_count} domains × ${per_low:,}-${per_high:,}"

    elif "per_site_cost" in activity:
        per_low, per_high = activity["per_site_cost"]
        low = per_low * site_count
        high = per_high * site_count
        formula = f"{site_count} sites × ${per_low:,}-${per_high:,}"

    elif "per_user_cost" in activity:
        per_low, per_high = activity["per_user_cost"]
        low = per_low * user_count
        high = per_high * user_count
        formula = f"{user_count:,} users × ${per_low}-${per_high}"

    elif "per_endpoint_cost" in activity:
        per_low, per_high = activity["per_endpoint_cost"]
        low = per_low * endpoint_count
        high = per_high * endpoint_count
        formula = f"{endpoint_count:,} endpoints × ${per_low}-${per_high}"

    else:
        low, high = 0, 0
        formula = "Unknown cost model"

    # Apply modifiers
    if combined_mult != 1.0:
        low = int(low * combined_mult)
        high = int(high * combined_mult)
        formula += f" × {combined_mult:.2f} ({complexity}/{industry})"

    return (int(low), int(high), formula)


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    'NETWORK_TEMPLATES',
    'SECURITY_TEMPLATES',
    'PERIMETER_TEMPLATES',
    'get_phase2_templates',
    'get_phase2_activity_by_id',
    'calculate_phase2_activity_cost',
]
