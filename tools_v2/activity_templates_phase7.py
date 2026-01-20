"""
Activity Templates V2 - Phase 7: Operational Run-Rate

Phase 7: Ongoing IT Operational Costs
- Infrastructure Operations (cloud, hosting, maintenance)
- Application Support & Maintenance
- IT Staffing / Personnel
- Managed Services (outsourced IT)
- Support Contracts & Maintenance Agreements

IMPORTANT: Phase 7 costs are ANNUAL/RECURRING, not one-time.
These represent the ongoing cost to operate standalone IT.

Key considerations:
- Lost shared services/economies of scale from parent
- Minimum viable IT organization
- Cloud vs. on-prem cost models
- Managed services vs. in-house trade-offs
- Contract renewals and vendor negotiations

Each activity template includes:
- name: Cost category name
- description: What this cost covers
- cost_type: "annual", "monthly", "per_fte"
- cost_model: How cost is calculated
- scaling_factors: What drives cost changes
- notes: Optimization considerations
"""

from typing import Dict, List, Any

# Import shared modifiers from Phase 1
from tools_v2.activity_templates_v2 import COMPLEXITY_MULTIPLIERS, INDUSTRY_MODIFIERS

# =============================================================================
# PHASE 7: INFRASTRUCTURE OPERATIONS
# =============================================================================

INFRASTRUCTURE_OPS_TEMPLATES = {
    "run_rate": [
        # -----------------------------------------------------------------
        # CLOUD INFRASTRUCTURE
        # -----------------------------------------------------------------
        {
            "id": "OPS-INF-001",
            "name": "Cloud infrastructure - IaaS compute",
            "description": "Annual cloud compute costs (VMs, containers, serverless)",
            "activity_type": "operational",
            "phase": "run_rate",
            "cost_type": "annual",
            "per_vm_cost": (1200, 6000),  # Annual per VM, varies by size
            "base_cost": (25000, 75000),  # Minimum platform costs
            "timeline_months": (12, 12),
            "requires_tsa": False,
            "scaling_factors": ["VM count", "Instance sizes", "Reserved vs on-demand"],
            "outputs": ["Cloud compute capacity", "Auto-scaling", "High availability"],
            "notes": "Reserved instances can reduce costs 30-60%",
        },
        {
            "id": "OPS-INF-002",
            "name": "Cloud infrastructure - Storage",
            "description": "Annual cloud storage costs (block, file, object)",
            "activity_type": "operational",
            "phase": "run_rate",
            "cost_type": "annual",
            "per_tb_cost": (200, 1200),  # Annual per TB, varies by tier
            "base_cost": (10000, 30000),
            "timeline_months": (12, 12),
            "requires_tsa": False,
            "scaling_factors": ["Storage volume", "Performance tier", "Redundancy level"],
            "outputs": ["Cloud storage", "Backup storage", "Archive storage"],
            "notes": "Tiered storage and lifecycle policies reduce costs",
        },
        {
            "id": "OPS-INF-003",
            "name": "Cloud infrastructure - Networking",
            "description": "Annual cloud networking costs (egress, VPN, load balancers)",
            "activity_type": "operational",
            "phase": "run_rate",
            "cost_type": "annual",
            "base_cost": (30000, 120000),
            "per_site_cost": (3000, 12000),  # Per connected site
            "timeline_months": (12, 12),
            "requires_tsa": False,
            "scaling_factors": ["Data egress", "VPN connections", "Load balancer count"],
            "outputs": ["Cloud connectivity", "Load balancing", "CDN"],
            "notes": "Egress costs often underestimated",
        },
        {
            "id": "OPS-INF-004",
            "name": "Cloud infrastructure - PaaS services",
            "description": "Annual PaaS costs (databases, messaging, caching)",
            "activity_type": "operational",
            "phase": "run_rate",
            "cost_type": "annual",
            "base_cost": (50000, 200000),
            "per_database_cost": (6000, 36000),  # Per managed database
            "timeline_months": (12, 12),
            "requires_tsa": False,
            "scaling_factors": ["Database count", "Performance tier", "Data volume"],
            "outputs": ["Managed databases", "Message queues", "Redis/caching"],
            "notes": "PaaS reduces ops overhead but can be costly at scale",
        },
        {
            "id": "OPS-INF-005",
            "name": "Cloud infrastructure - Security services",
            "description": "Annual cloud security service costs",
            "activity_type": "operational",
            "phase": "run_rate",
            "cost_type": "annual",
            "base_cost": (20000, 80000),
            "per_user_cost": (5, 20),
            "timeline_months": (12, 12),
            "requires_tsa": False,
            "scaling_factors": ["User count", "Security features", "Compliance requirements"],
            "outputs": ["WAF", "DDoS protection", "Key vault", "Security Center"],
        },
        # -----------------------------------------------------------------
        # ON-PREMISES / COLOCATION
        # -----------------------------------------------------------------
        {
            "id": "OPS-INF-010",
            "name": "Colocation / datacenter hosting",
            "description": "Annual colocation or datacenter space costs",
            "activity_type": "operational",
            "phase": "run_rate",
            "cost_type": "annual",
            "base_cost": (60000, 300000),  # Per cabinet/cage
            "per_kw_cost": (8000, 15000),  # Per kW of power
            "timeline_months": (12, 12),
            "requires_tsa": False,
            "scaling_factors": ["Rack count", "Power consumption", "Cooling requirements"],
            "outputs": ["Datacenter space", "Power", "Cooling", "Physical security"],
            "notes": "Typically 3-5 year contracts with annual escalators",
        },
        {
            "id": "OPS-INF-011",
            "name": "Hardware maintenance and support",
            "description": "Annual hardware maintenance contracts (servers, storage, network)",
            "activity_type": "operational",
            "phase": "run_rate",
            "cost_type": "annual",
            "per_server_cost": (1000, 4000),  # Annual maintenance per server
            "base_cost": (20000, 60000),
            "timeline_months": (12, 12),
            "requires_tsa": False,
            "scaling_factors": ["Server count", "Storage arrays", "Network equipment"],
            "outputs": ["Hardware support", "Parts replacement", "On-site service"],
            "notes": "Typically 15-20% of hardware cost annually",
        },
        {
            "id": "OPS-INF-012",
            "name": "Hardware refresh reserve",
            "description": "Annual reserve for hardware replacement (5-year cycle)",
            "activity_type": "operational",
            "phase": "run_rate",
            "cost_type": "annual",
            "per_server_cost": (2000, 6000),  # 20% of replacement cost
            "base_cost": (25000, 75000),
            "timeline_months": (12, 12),
            "requires_tsa": False,
            "scaling_factors": ["Hardware age", "Refresh cycle", "Criticality"],
            "outputs": ["Refresh budget", "Lifecycle planning"],
            "notes": "Plan for 5-year refresh cycle; allocate 20% annually",
        },
        # -----------------------------------------------------------------
        # NETWORK OPERATIONS
        # -----------------------------------------------------------------
        {
            "id": "OPS-INF-020",
            "name": "WAN circuit costs",
            "description": "Annual WAN/MPLS/SD-WAN circuit costs",
            "activity_type": "operational",
            "phase": "run_rate",
            "cost_type": "annual",
            "per_site_cost": (6000, 36000),  # Per site, varies by bandwidth
            "base_cost": (20000, 60000),  # Core/hub costs
            "timeline_months": (12, 12),
            "requires_tsa": False,
            "scaling_factors": ["Site count", "Bandwidth", "Circuit type"],
            "outputs": ["WAN connectivity", "Internet access", "Redundancy"],
            "notes": "SD-WAN can reduce costs 20-40% vs traditional MPLS",
        },
        {
            "id": "OPS-INF-021",
            "name": "Internet bandwidth costs",
            "description": "Annual internet connectivity costs",
            "activity_type": "operational",
            "phase": "run_rate",
            "cost_type": "annual",
            "per_site_cost": (2400, 12000),  # Per site
            "base_cost": (12000, 48000),  # Primary datacenter/cloud egress
            "timeline_months": (12, 12),
            "requires_tsa": False,
            "scaling_factors": ["Bandwidth", "Redundancy", "DDoS protection"],
            "outputs": ["Internet access", "Redundant paths"],
        },
        {
            "id": "OPS-INF-022",
            "name": "Voice/telephony services",
            "description": "Annual voice and telephony costs",
            "activity_type": "operational",
            "phase": "run_rate",
            "cost_type": "annual",
            "per_user_cost": (120, 360),  # Per user per year
            "base_cost": (15000, 50000),  # Platform/trunk costs
            "timeline_months": (12, 12),
            "requires_tsa": False,
            "scaling_factors": ["User count", "Call volume", "Contact center needs"],
            "outputs": ["Voice services", "Conferencing", "Contact center"],
            "notes": "Teams/cloud PBX typically cheaper than traditional",
        },
        # -----------------------------------------------------------------
        # BACKUP AND DR
        # -----------------------------------------------------------------
        {
            "id": "OPS-INF-030",
            "name": "Backup infrastructure operations",
            "description": "Annual backup infrastructure and storage costs",
            "activity_type": "operational",
            "phase": "run_rate",
            "cost_type": "annual",
            "per_tb_cost": (100, 400),  # Per TB protected
            "base_cost": (30000, 100000),
            "timeline_months": (12, 12),
            "requires_tsa": False,
            "scaling_factors": ["Data volume", "Retention period", "Backup frequency"],
            "outputs": ["Backup capacity", "Offsite replication", "Tape/archive"],
        },
        {
            "id": "OPS-INF-031",
            "name": "Disaster recovery operations",
            "description": "Annual DR site and replication costs",
            "activity_type": "operational",
            "phase": "run_rate",
            "cost_type": "annual",
            "base_cost": (75000, 300000),
            "per_vm_cost": (500, 2000),  # Per VM replicated
            "timeline_months": (12, 12),
            "requires_tsa": False,
            "scaling_factors": ["RTO/RPO requirements", "VM count", "Data volume"],
            "outputs": ["DR site", "Replication", "Failover capability"],
            "notes": "Cloud DR can significantly reduce costs vs dedicated site",
        },
    ],
}

# =============================================================================
# PHASE 7: APPLICATION SUPPORT
# =============================================================================

APPLICATION_SUPPORT_TEMPLATES = {
    "run_rate": [
        # -----------------------------------------------------------------
        # ERP SUPPORT
        # -----------------------------------------------------------------
        {
            "id": "OPS-APP-001",
            "name": "ERP annual maintenance and support",
            "description": "Annual ERP vendor maintenance and support fees",
            "activity_type": "operational",
            "phase": "run_rate",
            "cost_type": "annual",
            "base_cost": (100000, 500000),  # Varies greatly by ERP and size
            "per_user_cost": (500, 2000),  # Per named user
            "timeline_months": (12, 12),
            "requires_tsa": False,
            "scaling_factors": ["User count", "Modules licensed", "Support tier"],
            "outputs": ["Vendor support", "Patches", "Updates", "Bug fixes"],
            "notes": "Typically 18-22% of license cost; SAP/Oracle higher",
        },
        {
            "id": "OPS-APP-002",
            "name": "ERP hosting and infrastructure",
            "description": "Annual ERP hosting costs (cloud or on-prem)",
            "activity_type": "operational",
            "phase": "run_rate",
            "cost_type": "annual",
            "base_cost": (75000, 400000),
            "timeline_months": (12, 12),
            "requires_tsa": False,
            "scaling_factors": ["System size", "Performance requirements", "HA/DR"],
            "outputs": ["ERP infrastructure", "Database hosting", "Application servers"],
        },
        {
            "id": "OPS-APP-003",
            "name": "ERP application management",
            "description": "Annual cost for ERP administration and management",
            "activity_type": "operational",
            "phase": "run_rate",
            "cost_type": "annual",
            "base_cost": (150000, 500000),  # 1-3 FTEs typically
            "timeline_months": (12, 12),
            "requires_tsa": False,
            "scaling_factors": ["Complexity", "Customization level", "User count"],
            "outputs": ["Basis/admin support", "Performance tuning", "User support"],
            "notes": "Can be outsourced to reduce costs",
        },
        # -----------------------------------------------------------------
        # CRM SUPPORT
        # -----------------------------------------------------------------
        {
            "id": "OPS-APP-010",
            "name": "CRM subscription and support",
            "description": "Annual CRM subscription costs (Salesforce, Dynamics, etc.)",
            "activity_type": "operational",
            "phase": "run_rate",
            "cost_type": "annual",
            "per_user_cost": (1200, 4800),  # Per user per year
            "base_cost": (20000, 60000),  # Platform/admin costs
            "timeline_months": (12, 12),
            "requires_tsa": False,
            "scaling_factors": ["User count", "Edition", "Add-ons"],
            "outputs": ["CRM platform", "Support", "Updates"],
            "notes": "Salesforce: $75-300/user/month depending on edition",
        },
        {
            "id": "OPS-APP-011",
            "name": "CRM administration and customization",
            "description": "Annual CRM administration and enhancement costs",
            "activity_type": "operational",
            "phase": "run_rate",
            "cost_type": "annual",
            "base_cost": (75000, 200000),
            "timeline_months": (12, 12),
            "requires_tsa": False,
            "scaling_factors": ["Customization level", "Integration count", "User count"],
            "outputs": ["Admin support", "Report development", "Minor enhancements"],
        },
        # -----------------------------------------------------------------
        # HCM/PAYROLL SUPPORT
        # -----------------------------------------------------------------
        {
            "id": "OPS-APP-020",
            "name": "HCM/HRIS subscription and support",
            "description": "Annual HCM platform costs (Workday, SuccessFactors, etc.)",
            "activity_type": "operational",
            "phase": "run_rate",
            "cost_type": "annual",
            "per_employee_cost": (100, 400),  # Per employee per year
            "base_cost": (30000, 100000),
            "timeline_months": (12, 12),
            "requires_tsa": False,
            "scaling_factors": ["Employee count", "Modules", "Geographies"],
            "outputs": ["HCM platform", "Support", "Updates"],
        },
        {
            "id": "OPS-APP-021",
            "name": "Payroll processing fees",
            "description": "Annual payroll processing costs",
            "activity_type": "operational",
            "phase": "run_rate",
            "cost_type": "annual",
            "per_employee_cost": (200, 600),  # Per employee per year
            "base_cost": (15000, 50000),
            "timeline_months": (12, 12),
            "requires_tsa": False,
            "scaling_factors": ["Employee count", "Pay frequency", "Complexity"],
            "outputs": ["Payroll processing", "Tax filing", "Direct deposit"],
        },
        {
            "id": "OPS-APP-022",
            "name": "Benefits administration",
            "description": "Annual benefits administration platform costs",
            "activity_type": "operational",
            "phase": "run_rate",
            "cost_type": "annual",
            "per_employee_cost": (40, 150),  # Per employee per year
            "base_cost": (15000, 40000),
            "timeline_months": (12, 12),
            "requires_tsa": False,
            "scaling_factors": ["Employee count", "Benefit complexity", "Carrier count"],
            "outputs": ["Benefits enrollment", "Carrier feeds", "Compliance"],
        },
        # -----------------------------------------------------------------
        # CUSTOM APPLICATION SUPPORT
        # -----------------------------------------------------------------
        {
            "id": "OPS-APP-030",
            "name": "Custom application maintenance",
            "description": "Annual maintenance for custom/bespoke applications",
            "activity_type": "operational",
            "phase": "run_rate",
            "cost_type": "annual",
            "per_app_cost": (15000, 75000),  # Per application
            "base_cost": (50000, 150000),
            "timeline_months": (12, 12),
            "requires_tsa": False,
            "scaling_factors": ["Application count", "Complexity", "Technology age"],
            "outputs": ["Bug fixes", "Minor enhancements", "Security patches"],
            "notes": "Typically 15-20% of development cost annually",
        },
        {
            "id": "OPS-APP-031",
            "name": "Application enhancement budget",
            "description": "Annual budget for application enhancements and improvements",
            "activity_type": "operational",
            "phase": "run_rate",
            "cost_type": "annual",
            "base_cost": (100000, 500000),
            "timeline_months": (12, 12),
            "requires_tsa": False,
            "scaling_factors": ["Business requirements", "Technical debt", "Growth"],
            "outputs": ["New features", "Improvements", "Modernization"],
        },
        # -----------------------------------------------------------------
        # SAAS SUBSCRIPTIONS
        # -----------------------------------------------------------------
        {
            "id": "OPS-APP-040",
            "name": "Productivity SaaS (M365/Google Workspace)",
            "description": "Annual productivity suite subscription",
            "activity_type": "operational",
            "phase": "run_rate",
            "cost_type": "annual",
            "per_user_cost": (150, 450),  # Per user per year
            "timeline_months": (12, 12),
            "requires_tsa": False,
            "scaling_factors": ["User count", "License tier", "Add-ons"],
            "outputs": ["Email", "Office apps", "Collaboration", "Storage"],
            "notes": "M365 E3: ~$400/user/year, E5: ~$600/user/year",
        },
        {
            "id": "OPS-APP-041",
            "name": "Collaboration tools (Slack, Teams, Zoom)",
            "description": "Annual collaboration platform costs",
            "activity_type": "operational",
            "phase": "run_rate",
            "cost_type": "annual",
            "per_user_cost": (50, 200),  # Per user per year
            "base_cost": (10000, 30000),
            "timeline_months": (12, 12),
            "requires_tsa": False,
            "scaling_factors": ["User count", "Features", "Meeting capacity"],
            "outputs": ["Chat", "Video conferencing", "Screen sharing"],
        },
        {
            "id": "OPS-APP-042",
            "name": "Line of business SaaS subscriptions",
            "description": "Annual LOB SaaS application costs (aggregated)",
            "activity_type": "operational",
            "phase": "run_rate",
            "cost_type": "annual",
            "per_app_cost": (5000, 50000),  # Per SaaS app
            "base_cost": (25000, 100000),
            "timeline_months": (12, 12),
            "requires_tsa": False,
            "scaling_factors": ["Application count", "User counts", "Features"],
            "outputs": ["SaaS applications", "Vendor support", "Updates"],
        },
    ],
}

# =============================================================================
# PHASE 7: IT STAFFING
# =============================================================================

IT_STAFFING_TEMPLATES = {
    "run_rate": [
        # -----------------------------------------------------------------
        # IT LEADERSHIP
        # -----------------------------------------------------------------
        {
            "id": "OPS-STF-001",
            "name": "IT leadership (CIO/CTO/VP)",
            "description": "Annual cost for IT executive leadership",
            "activity_type": "operational",
            "phase": "run_rate",
            "cost_type": "annual",
            "base_cost": (250000, 500000),  # 1 senior leader fully loaded
            "timeline_months": (12, 12),
            "requires_tsa": False,
            "scaling_factors": ["Organization size", "IT complexity", "Strategic importance"],
            "outputs": ["IT strategy", "Vendor relationships", "Budget management"],
            "notes": "May be fractional for smaller organizations",
        },
        {
            "id": "OPS-STF-002",
            "name": "IT management (Directors/Managers)",
            "description": "Annual cost for IT management layer",
            "activity_type": "operational",
            "phase": "run_rate",
            "cost_type": "annual",
            "per_fte_cost": (150000, 250000),
            "base_cost": (150000, 250000),  # Minimum 1 manager
            "timeline_months": (12, 12),
            "requires_tsa": False,
            "scaling_factors": ["IT team size", "Span of control", "Workstream count"],
            "outputs": ["Team leadership", "Project oversight", "Operations management"],
        },
        # -----------------------------------------------------------------
        # INFRASTRUCTURE TEAM
        # -----------------------------------------------------------------
        {
            "id": "OPS-STF-010",
            "name": "Infrastructure/platform engineers",
            "description": "Annual cost for infrastructure engineering team",
            "activity_type": "operational",
            "phase": "run_rate",
            "cost_type": "annual",
            "per_fte_cost": (120000, 200000),
            "timeline_months": (12, 12),
            "requires_tsa": False,
            "scaling_factors": ["Infrastructure complexity", "Cloud vs on-prem", "Automation level"],
            "outputs": ["Infrastructure management", "Cloud operations", "Automation"],
            "notes": "Typical ratio: 1 engineer per 50-100 VMs",
        },
        {
            "id": "OPS-STF-011",
            "name": "Network engineers",
            "description": "Annual cost for network engineering team",
            "activity_type": "operational",
            "phase": "run_rate",
            "cost_type": "annual",
            "per_fte_cost": (110000, 180000),
            "timeline_months": (12, 12),
            "requires_tsa": False,
            "scaling_factors": ["Network complexity", "Site count", "Security requirements"],
            "outputs": ["Network management", "Firewall management", "WAN operations"],
            "notes": "Typical ratio: 1 engineer per 5-10 sites",
        },
        {
            "id": "OPS-STF-012",
            "name": "Database administrators",
            "description": "Annual cost for database administration team",
            "activity_type": "operational",
            "phase": "run_rate",
            "cost_type": "annual",
            "per_fte_cost": (120000, 200000),
            "timeline_months": (12, 12),
            "requires_tsa": False,
            "scaling_factors": ["Database count", "Database complexity", "Performance requirements"],
            "outputs": ["Database management", "Performance tuning", "Backup/recovery"],
            "notes": "Typical ratio: 1 DBA per 20-40 databases",
        },
        # -----------------------------------------------------------------
        # SECURITY TEAM
        # -----------------------------------------------------------------
        {
            "id": "OPS-STF-020",
            "name": "Security engineers/analysts",
            "description": "Annual cost for security team",
            "activity_type": "operational",
            "phase": "run_rate",
            "cost_type": "annual",
            "per_fte_cost": (130000, 220000),
            "timeline_months": (12, 12),
            "requires_tsa": False,
            "scaling_factors": ["Compliance requirements", "Threat landscape", "Security tooling"],
            "outputs": ["Security monitoring", "Incident response", "Vulnerability management"],
            "notes": "Often supplemented with managed SOC services",
        },
        {
            "id": "OPS-STF-021",
            "name": "Identity and access management",
            "description": "Annual cost for IAM specialists",
            "activity_type": "operational",
            "phase": "run_rate",
            "cost_type": "annual",
            "per_fte_cost": (120000, 200000),
            "timeline_months": (12, 12),
            "requires_tsa": False,
            "scaling_factors": ["User count", "Application count", "Compliance requirements"],
            "outputs": ["Access provisioning", "SSO management", "Access reviews"],
        },
        # -----------------------------------------------------------------
        # APPLICATION TEAM
        # -----------------------------------------------------------------
        {
            "id": "OPS-STF-030",
            "name": "Application developers",
            "description": "Annual cost for application development team",
            "activity_type": "operational",
            "phase": "run_rate",
            "cost_type": "annual",
            "per_fte_cost": (120000, 200000),
            "timeline_months": (12, 12),
            "requires_tsa": False,
            "scaling_factors": ["Custom app count", "Enhancement needs", "Technology stack"],
            "outputs": ["Application development", "Bug fixes", "Enhancements"],
        },
        {
            "id": "OPS-STF-031",
            "name": "Application support analysts",
            "description": "Annual cost for application support team",
            "activity_type": "operational",
            "phase": "run_rate",
            "cost_type": "annual",
            "per_fte_cost": (80000, 140000),
            "timeline_months": (12, 12),
            "requires_tsa": False,
            "scaling_factors": ["Application count", "User count", "Complexity"],
            "outputs": ["Application support", "Configuration", "User assistance"],
        },
        {
            "id": "OPS-STF-032",
            "name": "Integration/middleware specialists",
            "description": "Annual cost for integration team",
            "activity_type": "operational",
            "phase": "run_rate",
            "cost_type": "annual",
            "per_fte_cost": (120000, 200000),
            "timeline_months": (12, 12),
            "requires_tsa": False,
            "scaling_factors": ["Integration count", "Complexity", "Real-time requirements"],
            "outputs": ["Integration management", "API support", "Data flows"],
        },
        # -----------------------------------------------------------------
        # END USER SUPPORT
        # -----------------------------------------------------------------
        {
            "id": "OPS-STF-040",
            "name": "Help desk / service desk",
            "description": "Annual cost for service desk team",
            "activity_type": "operational",
            "phase": "run_rate",
            "cost_type": "annual",
            "per_fte_cost": (60000, 100000),
            "timeline_months": (12, 12),
            "requires_tsa": False,
            "scaling_factors": ["User count", "Support hours", "Ticket volume"],
            "outputs": ["Tier 1 support", "Incident management", "Request fulfillment"],
            "notes": "Typical ratio: 1 analyst per 75-150 users",
        },
        {
            "id": "OPS-STF-041",
            "name": "Desktop/endpoint support",
            "description": "Annual cost for desktop support team",
            "activity_type": "operational",
            "phase": "run_rate",
            "cost_type": "annual",
            "per_fte_cost": (65000, 110000),
            "timeline_months": (12, 12),
            "requires_tsa": False,
            "scaling_factors": ["User count", "Site count", "Device types"],
            "outputs": ["Desktop support", "Device deployment", "On-site support"],
            "notes": "Typical ratio: 1 tech per 150-250 users",
        },
        # -----------------------------------------------------------------
        # PROJECT/PMO
        # -----------------------------------------------------------------
        {
            "id": "OPS-STF-050",
            "name": "Project managers / PMO",
            "description": "Annual cost for IT project management",
            "activity_type": "operational",
            "phase": "run_rate",
            "cost_type": "annual",
            "per_fte_cost": (110000, 180000),
            "timeline_months": (12, 12),
            "requires_tsa": False,
            "scaling_factors": ["Project portfolio", "Change volume", "Vendor management"],
            "outputs": ["Project delivery", "Resource coordination", "Status reporting"],
        },
        {
            "id": "OPS-STF-051",
            "name": "Business analysts",
            "description": "Annual cost for IT business analysts",
            "activity_type": "operational",
            "phase": "run_rate",
            "cost_type": "annual",
            "per_fte_cost": (100000, 160000),
            "timeline_months": (12, 12),
            "requires_tsa": False,
            "scaling_factors": ["Enhancement backlog", "Business complexity", "Documentation needs"],
            "outputs": ["Requirements", "Process documentation", "Testing support"],
        },
    ],
}

# =============================================================================
# PHASE 7: MANAGED SERVICES
# =============================================================================

MANAGED_SERVICES_TEMPLATES = {
    "run_rate": [
        # -----------------------------------------------------------------
        # INFRASTRUCTURE MANAGED SERVICES
        # -----------------------------------------------------------------
        {
            "id": "OPS-MSP-001",
            "name": "Managed infrastructure services",
            "description": "Outsourced infrastructure management (MSP)",
            "activity_type": "operational",
            "phase": "run_rate",
            "cost_type": "annual",
            "per_vm_cost": (600, 2400),  # Per VM per year
            "base_cost": (50000, 150000),  # Base management fee
            "timeline_months": (12, 12),
            "requires_tsa": False,
            "scaling_factors": ["VM count", "SLA requirements", "Coverage hours"],
            "outputs": ["24x7 monitoring", "Incident response", "Patch management"],
            "notes": "Often more cost-effective than in-house for smaller orgs",
        },
        {
            "id": "OPS-MSP-002",
            "name": "Managed cloud services",
            "description": "Cloud management and optimization services",
            "activity_type": "operational",
            "phase": "run_rate",
            "cost_type": "annual",
            "base_cost": (60000, 200000),  # Percentage of cloud spend typical
            "timeline_months": (12, 12),
            "requires_tsa": False,
            "scaling_factors": ["Cloud spend", "Complexity", "Multi-cloud"],
            "outputs": ["Cloud operations", "Cost optimization", "Architecture guidance"],
        },
        {
            "id": "OPS-MSP-003",
            "name": "Managed network services",
            "description": "Outsourced network management",
            "activity_type": "operational",
            "phase": "run_rate",
            "cost_type": "annual",
            "per_site_cost": (3000, 12000),
            "base_cost": (30000, 100000),
            "timeline_months": (12, 12),
            "requires_tsa": False,
            "scaling_factors": ["Site count", "Network complexity", "SLA requirements"],
            "outputs": ["Network monitoring", "Change management", "Troubleshooting"],
        },
        # -----------------------------------------------------------------
        # SECURITY MANAGED SERVICES
        # -----------------------------------------------------------------
        {
            "id": "OPS-MSP-010",
            "name": "Managed SOC / security monitoring",
            "description": "Outsourced security operations center",
            "activity_type": "operational",
            "phase": "run_rate",
            "cost_type": "annual",
            "base_cost": (100000, 400000),
            "per_endpoint_cost": (30, 100),
            "timeline_months": (12, 12),
            "requires_tsa": False,
            "scaling_factors": ["Endpoint count", "Log volume", "Compliance requirements"],
            "outputs": ["24x7 monitoring", "Threat detection", "Incident response"],
            "notes": "More cost-effective than building internal SOC for most orgs",
        },
        {
            "id": "OPS-MSP-011",
            "name": "Managed EDR/MDR services",
            "description": "Managed endpoint detection and response",
            "activity_type": "operational",
            "phase": "run_rate",
            "cost_type": "annual",
            "per_endpoint_cost": (100, 300),
            "base_cost": (25000, 75000),
            "timeline_months": (12, 12),
            "requires_tsa": False,
            "scaling_factors": ["Endpoint count", "Response SLA", "Hunting services"],
            "outputs": ["Endpoint monitoring", "Threat hunting", "Remediation"],
        },
        {
            "id": "OPS-MSP-012",
            "name": "Managed vulnerability services",
            "description": "Outsourced vulnerability management",
            "activity_type": "operational",
            "phase": "run_rate",
            "cost_type": "annual",
            "base_cost": (40000, 150000),
            "per_asset_cost": (20, 80),  # Per scanned asset
            "timeline_months": (12, 12),
            "requires_tsa": False,
            "scaling_factors": ["Asset count", "Scan frequency", "Remediation support"],
            "outputs": ["Vulnerability scanning", "Reporting", "Remediation guidance"],
        },
        # -----------------------------------------------------------------
        # END USER MANAGED SERVICES
        # -----------------------------------------------------------------
        {
            "id": "OPS-MSP-020",
            "name": "Managed service desk",
            "description": "Outsourced help desk / service desk",
            "activity_type": "operational",
            "phase": "run_rate",
            "cost_type": "annual",
            "per_user_cost": (200, 600),  # Per user per year
            "base_cost": (30000, 100000),
            "timeline_months": (12, 12),
            "requires_tsa": False,
            "scaling_factors": ["User count", "Coverage hours", "SLA requirements"],
            "outputs": ["Tier 1-2 support", "Ticket management", "Knowledge base"],
            "notes": "Follow-the-sun model available for 24x7 at lower cost",
        },
        {
            "id": "OPS-MSP-021",
            "name": "Managed desktop services",
            "description": "Outsourced desktop/endpoint management",
            "activity_type": "operational",
            "phase": "run_rate",
            "cost_type": "annual",
            "per_endpoint_cost": (150, 450),  # Per endpoint per year
            "base_cost": (25000, 75000),
            "timeline_months": (12, 12),
            "requires_tsa": False,
            "scaling_factors": ["Endpoint count", "Device types", "Management level"],
            "outputs": ["Device management", "Patching", "Software deployment"],
        },
        # -----------------------------------------------------------------
        # APPLICATION MANAGED SERVICES
        # -----------------------------------------------------------------
        {
            "id": "OPS-MSP-030",
            "name": "Managed application services",
            "description": "Application management services (AMS)",
            "activity_type": "operational",
            "phase": "run_rate",
            "cost_type": "annual",
            "per_app_cost": (20000, 100000),  # Per managed application
            "base_cost": (50000, 150000),
            "timeline_months": (12, 12),
            "requires_tsa": False,
            "scaling_factors": ["Application count", "Complexity", "SLA requirements"],
            "outputs": ["Application support", "Monitoring", "Minor enhancements"],
        },
        {
            "id": "OPS-MSP-031",
            "name": "Managed ERP services",
            "description": "Outsourced ERP support and management",
            "activity_type": "operational",
            "phase": "run_rate",
            "cost_type": "annual",
            "base_cost": (150000, 600000),
            "timeline_months": (12, 12),
            "requires_tsa": False,
            "scaling_factors": ["ERP complexity", "User count", "Customization level"],
            "outputs": ["Basis support", "Functional support", "Development"],
        },
    ],
}

# =============================================================================
# PHASE 7: SUPPORT CONTRACTS & MAINTENANCE
# =============================================================================

SUPPORT_CONTRACTS_TEMPLATES = {
    "run_rate": [
        # -----------------------------------------------------------------
        # SOFTWARE MAINTENANCE
        # -----------------------------------------------------------------
        {
            "id": "OPS-SUP-001",
            "name": "Microsoft EA/subscription renewal",
            "description": "Annual Microsoft licensing and support",
            "activity_type": "operational",
            "phase": "run_rate",
            "cost_type": "annual",
            "per_user_cost": (200, 600),  # Per user for M365 + other MS
            "base_cost": (25000, 100000),  # Server, Azure, etc.
            "timeline_months": (12, 12),
            "requires_tsa": False,
            "scaling_factors": ["User count", "License mix", "Azure consumption"],
            "outputs": ["M365 licenses", "Windows licenses", "Support"],
        },
        {
            "id": "OPS-SUP-002",
            "name": "Oracle support renewal",
            "description": "Annual Oracle maintenance and support",
            "activity_type": "operational",
            "phase": "run_rate",
            "cost_type": "annual",
            "base_cost": (50000, 500000),  # Highly variable
            "timeline_months": (12, 12),
            "requires_tsa": False,
            "scaling_factors": ["License count", "Products licensed", "Options/packs"],
            "outputs": ["Support access", "Patches", "Updates"],
            "notes": "Typically 22% of net license cost; hard to reduce",
        },
        {
            "id": "OPS-SUP-003",
            "name": "SAP support renewal",
            "description": "Annual SAP maintenance and support",
            "activity_type": "operational",
            "phase": "run_rate",
            "cost_type": "annual",
            "base_cost": (100000, 800000),  # Highly variable
            "timeline_months": (12, 12),
            "requires_tsa": False,
            "scaling_factors": ["User count", "Modules", "Enterprise vs Standard"],
            "outputs": ["Support access", "Notes", "Upgrades"],
            "notes": "Typically 17-22% of license value annually",
        },
        {
            "id": "OPS-SUP-004",
            "name": "VMware support renewal",
            "description": "Annual VMware support and subscription",
            "activity_type": "operational",
            "phase": "run_rate",
            "cost_type": "annual",
            "per_cpu_cost": (500, 2000),  # Per CPU socket
            "base_cost": (15000, 50000),
            "timeline_months": (12, 12),
            "requires_tsa": False,
            "scaling_factors": ["CPU count", "Edition", "Additional products"],
            "outputs": ["SnS coverage", "Updates", "Support"],
        },
        {
            "id": "OPS-SUP-005",
            "name": "Database support (SQL Server)",
            "description": "Annual SQL Server support and maintenance",
            "activity_type": "operational",
            "phase": "run_rate",
            "cost_type": "annual",
            "per_core_cost": (400, 1600),  # Per core, varies by edition
            "base_cost": (10000, 40000),
            "timeline_months": (12, 12),
            "requires_tsa": False,
            "scaling_factors": ["Core count", "Edition", "SA coverage"],
            "outputs": ["Software Assurance", "Updates", "Support"],
        },
        # -----------------------------------------------------------------
        # SECURITY TOOLS
        # -----------------------------------------------------------------
        {
            "id": "OPS-SUP-010",
            "name": "Security tool subscriptions",
            "description": "Annual security software subscriptions (EDR, SIEM, etc.)",
            "activity_type": "operational",
            "phase": "run_rate",
            "cost_type": "annual",
            "per_user_cost": (50, 200),
            "per_endpoint_cost": (30, 120),
            "base_cost": (30000, 100000),
            "timeline_months": (12, 12),
            "requires_tsa": False,
            "scaling_factors": ["Endpoint count", "Features", "Data volume"],
            "outputs": ["Security tools", "Updates", "Threat intel"],
        },
        {
            "id": "OPS-SUP-011",
            "name": "Firewall/network security maintenance",
            "description": "Annual firewall and network security subscriptions",
            "activity_type": "operational",
            "phase": "run_rate",
            "cost_type": "annual",
            "per_device_cost": (1000, 5000),  # Per firewall/device
            "base_cost": (15000, 50000),
            "timeline_months": (12, 12),
            "requires_tsa": False,
            "scaling_factors": ["Device count", "Feature sets", "Throughput"],
            "outputs": ["Firmware updates", "Threat signatures", "Support"],
        },
        # -----------------------------------------------------------------
        # INFRASTRUCTURE TOOLS
        # -----------------------------------------------------------------
        {
            "id": "OPS-SUP-020",
            "name": "Backup software maintenance",
            "description": "Annual backup software support and subscription",
            "activity_type": "operational",
            "phase": "run_rate",
            "cost_type": "annual",
            "per_tb_cost": (50, 200),  # Per TB protected
            "base_cost": (15000, 50000),
            "timeline_months": (12, 12),
            "requires_tsa": False,
            "scaling_factors": ["Data volume", "Features", "Workload types"],
            "outputs": ["Software updates", "Support", "Cloud integration"],
        },
        {
            "id": "OPS-SUP-021",
            "name": "Monitoring tool subscriptions",
            "description": "Annual monitoring and observability tools",
            "activity_type": "operational",
            "phase": "run_rate",
            "cost_type": "annual",
            "per_host_cost": (200, 1000),  # Per monitored host
            "base_cost": (20000, 80000),
            "timeline_months": (12, 12),
            "requires_tsa": False,
            "scaling_factors": ["Host count", "Metrics volume", "Retention"],
            "outputs": ["Monitoring", "Alerting", "Dashboards"],
            "notes": "Datadog, New Relic, Splunk can be expensive at scale",
        },
        {
            "id": "OPS-SUP-022",
            "name": "ITSM platform subscription",
            "description": "Annual ITSM/ServiceNow subscription",
            "activity_type": "operational",
            "phase": "run_rate",
            "cost_type": "annual",
            "per_user_cost": (600, 2400),  # Per fulfiller user
            "base_cost": (30000, 100000),
            "timeline_months": (12, 12),
            "requires_tsa": False,
            "scaling_factors": ["Fulfiller count", "Modules", "Integrations"],
            "outputs": ["ITSM platform", "Workflows", "Reporting"],
        },
        # -----------------------------------------------------------------
        # VENDOR SUPPORT AGREEMENTS
        # -----------------------------------------------------------------
        {
            "id": "OPS-SUP-030",
            "name": "Network vendor support (Cisco, etc.)",
            "description": "Annual network equipment support contracts",
            "activity_type": "operational",
            "phase": "run_rate",
            "cost_type": "annual",
            "per_device_cost": (300, 2000),  # Per network device
            "base_cost": (15000, 50000),
            "timeline_months": (12, 12),
            "requires_tsa": False,
            "scaling_factors": ["Device count", "Support tier", "Coverage hours"],
            "outputs": ["TAC support", "Software updates", "RMA"],
            "notes": "SmartNet/similar typically 10-15% of hardware cost",
        },
        {
            "id": "OPS-SUP-031",
            "name": "Storage vendor support",
            "description": "Annual storage hardware support contracts",
            "activity_type": "operational",
            "phase": "run_rate",
            "cost_type": "annual",
            "per_tb_cost": (100, 500),  # Per TB capacity
            "base_cost": (20000, 80000),
            "timeline_months": (12, 12),
            "requires_tsa": False,
            "scaling_factors": ["Capacity", "Array count", "Support tier"],
            "outputs": ["Hardware support", "Firmware", "Parts"],
        },
    ],
}

# =============================================================================
# COMBINED TEMPLATES FOR PHASE 7
# =============================================================================

def get_phase7_templates() -> Dict[str, Dict[str, List[Dict]]]:
    """Get all Phase 7 templates organized by category and workstream."""
    return {
        "run_rate": {
            "infrastructure_ops": INFRASTRUCTURE_OPS_TEMPLATES["run_rate"],
            "application_support": APPLICATION_SUPPORT_TEMPLATES["run_rate"],
            "it_staffing": IT_STAFFING_TEMPLATES["run_rate"],
            "managed_services": MANAGED_SERVICES_TEMPLATES["run_rate"],
            "support_contracts": SUPPORT_CONTRACTS_TEMPLATES["run_rate"],
        },
    }


def get_phase7_activity_by_id(activity_id: str) -> Dict:
    """Look up a Phase 7 activity by its ID."""
    all_templates = get_phase7_templates()

    for category, workstreams in all_templates.items():
        for workstream, activities in workstreams.items():
            for activity in activities:
                if activity.get("id") == activity_id:
                    return activity

    return None


def calculate_phase7_activity_cost(
    activity: Dict,
    user_count: int = 1000,
    employee_count: int = None,
    vm_count: int = 100,
    server_count: int = 50,
    endpoint_count: int = None,
    database_count: int = 20,
    app_count: int = 30,
    site_count: int = 8,
    storage_tb: int = 50,
    cpu_count: int = 30,
    core_count: int = 100,
    device_count: int = 50,
    host_count: int = None,
    asset_count: int = None,
    kw_power: int = 20,
    fte_count: int = 1,
    complexity: str = "moderate",
    industry: str = "standard",
) -> tuple:
    """
    Calculate ANNUAL cost range for a Phase 7 activity based on quantities and modifiers.

    Returns: (low, high, formula)
    """
    # Default derived values
    employee_count = employee_count or user_count
    endpoint_count = endpoint_count or int(user_count * 1.3)
    host_count = host_count or (vm_count + server_count)
    asset_count = asset_count or (vm_count + server_count + endpoint_count)

    # Get complexity and industry multipliers
    complexity_mult = COMPLEXITY_MULTIPLIERS.get(complexity, 1.0)
    industry_mult = INDUSTRY_MODIFIERS.get(industry, 1.0)
    combined_mult = complexity_mult * industry_mult

    low, high = 0, 0
    formula_parts = []

    # Base cost
    if "base_cost" in activity:
        base_low, base_high = activity["base_cost"]
        low += base_low
        high += base_high
        formula_parts.append(f"Base: ${base_low:,.0f}-${base_high:,.0f}")

    # Per-unit costs (annual)
    if "per_user_cost" in activity:
        per_low, per_high = activity["per_user_cost"]
        low += per_low * user_count
        high += per_high * user_count
        formula_parts.append(f"{user_count:,} users × ${per_low}-${per_high}/yr")

    if "per_employee_cost" in activity:
        per_low, per_high = activity["per_employee_cost"]
        low += per_low * employee_count
        high += per_high * employee_count
        formula_parts.append(f"{employee_count:,} employees × ${per_low}-${per_high}/yr")

    if "per_vm_cost" in activity:
        per_low, per_high = activity["per_vm_cost"]
        low += per_low * vm_count
        high += per_high * vm_count
        formula_parts.append(f"{vm_count} VMs × ${per_low:,}-${per_high:,}/yr")

    if "per_server_cost" in activity:
        per_low, per_high = activity["per_server_cost"]
        low += per_low * server_count
        high += per_high * server_count
        formula_parts.append(f"{server_count} servers × ${per_low:,}-${per_high:,}/yr")

    if "per_endpoint_cost" in activity:
        per_low, per_high = activity["per_endpoint_cost"]
        low += per_low * endpoint_count
        high += per_high * endpoint_count
        formula_parts.append(f"{endpoint_count:,} endpoints × ${per_low}-${per_high}/yr")

    if "per_database_cost" in activity:
        per_low, per_high = activity["per_database_cost"]
        low += per_low * database_count
        high += per_high * database_count
        formula_parts.append(f"{database_count} databases × ${per_low:,}-${per_high:,}/yr")

    if "per_app_cost" in activity:
        per_low, per_high = activity["per_app_cost"]
        low += per_low * app_count
        high += per_high * app_count
        formula_parts.append(f"{app_count} apps × ${per_low:,}-${per_high:,}/yr")

    if "per_site_cost" in activity:
        per_low, per_high = activity["per_site_cost"]
        low += per_low * site_count
        high += per_high * site_count
        formula_parts.append(f"{site_count} sites × ${per_low:,}-${per_high:,}/yr")

    if "per_tb_cost" in activity:
        per_low, per_high = activity["per_tb_cost"]
        low += per_low * storage_tb
        high += per_high * storage_tb
        formula_parts.append(f"{storage_tb} TB × ${per_low:,}-${per_high:,}/yr")

    if "per_cpu_cost" in activity:
        per_low, per_high = activity["per_cpu_cost"]
        low += per_low * cpu_count
        high += per_high * cpu_count
        formula_parts.append(f"{cpu_count} CPUs × ${per_low:,}-${per_high:,}/yr")

    if "per_core_cost" in activity:
        per_low, per_high = activity["per_core_cost"]
        low += per_low * core_count
        high += per_high * core_count
        formula_parts.append(f"{core_count} cores × ${per_low:,}-${per_high:,}/yr")

    if "per_device_cost" in activity:
        per_low, per_high = activity["per_device_cost"]
        low += per_low * device_count
        high += per_high * device_count
        formula_parts.append(f"{device_count} devices × ${per_low:,}-${per_high:,}/yr")

    if "per_host_cost" in activity:
        per_low, per_high = activity["per_host_cost"]
        low += per_low * host_count
        high += per_high * host_count
        formula_parts.append(f"{host_count} hosts × ${per_low:,}-${per_high:,}/yr")

    if "per_asset_cost" in activity:
        per_low, per_high = activity["per_asset_cost"]
        low += per_low * asset_count
        high += per_high * asset_count
        formula_parts.append(f"{asset_count:,} assets × ${per_low}-${per_high}/yr")

    if "per_kw_cost" in activity:
        per_low, per_high = activity["per_kw_cost"]
        low += per_low * kw_power
        high += per_high * kw_power
        formula_parts.append(f"{kw_power} kW × ${per_low:,}-${per_high:,}/yr")

    if "per_fte_cost" in activity:
        per_low, per_high = activity["per_fte_cost"]
        low += per_low * fte_count
        high += per_high * fte_count
        formula_parts.append(f"{fte_count} FTE × ${per_low:,}-${per_high:,}/yr")

    formula = " + ".join(formula_parts) if formula_parts else "Unknown cost model"

    # Apply modifiers
    if combined_mult != 1.0:
        low = int(low * combined_mult)
        high = int(high * combined_mult)
        formula += f" × {combined_mult:.2f} ({complexity}/{industry})"

    return (int(low), int(high), formula)


def calculate_it_staffing_needs(
    user_count: int = 1000,
    vm_count: int = 100,
    database_count: int = 20,
    app_count: int = 30,
    site_count: int = 8,
    complexity: str = "moderate",
) -> Dict[str, tuple]:
    """
    Calculate recommended IT staffing based on environment size.

    Returns dict of role: (min_fte, max_fte, notes)
    """
    complexity_factor = {"simple": 0.7, "moderate": 1.0, "complex": 1.4, "highly_complex": 1.8}.get(complexity, 1.0)

    staffing = {
        "it_leadership": (1, 1, "CIO/VP IT - may be fractional for <500 users"),
        "it_management": (max(1, int(user_count / 500 * complexity_factor)),
                         max(2, int(user_count / 300 * complexity_factor)),
                         "Directors/Managers"),
        "infrastructure_engineers": (max(1, int(vm_count / 75 * complexity_factor)),
                                    max(2, int(vm_count / 40 * complexity_factor)),
                                    "Cloud/platform engineers"),
        "network_engineers": (max(1, int(site_count / 8 * complexity_factor)),
                             max(1, int(site_count / 4 * complexity_factor)),
                             "Network/firewall"),
        "database_administrators": (max(1, int(database_count / 30 * complexity_factor)),
                                   max(1, int(database_count / 15 * complexity_factor)),
                                   "DBAs"),
        "security_team": (max(1, int(user_count / 1000 * complexity_factor)),
                         max(2, int(user_count / 500 * complexity_factor)),
                         "Security engineers/analysts"),
        "application_developers": (max(1, int(app_count / 15 * complexity_factor)),
                                  max(2, int(app_count / 8 * complexity_factor)),
                                  "Developers"),
        "application_support": (max(1, int(app_count / 20 * complexity_factor)),
                               max(2, int(app_count / 10 * complexity_factor)),
                               "App support analysts"),
        "help_desk": (max(1, int(user_count / 150)),
                     max(2, int(user_count / 75)),
                     "Service desk analysts"),
        "desktop_support": (max(1, int(user_count / 200)),
                           max(2, int(user_count / 100)),
                           "Desktop technicians"),
        "project_managers": (max(1, int(user_count / 1000)),
                            max(2, int(user_count / 500)),
                            "PMs/BAs"),
    }

    return staffing


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    'INFRASTRUCTURE_OPS_TEMPLATES',
    'APPLICATION_SUPPORT_TEMPLATES',
    'IT_STAFFING_TEMPLATES',
    'MANAGED_SERVICES_TEMPLATES',
    'SUPPORT_CONTRACTS_TEMPLATES',
    'get_phase7_templates',
    'get_phase7_activity_by_id',
    'calculate_phase7_activity_cost',
    'calculate_it_staffing_needs',
]
