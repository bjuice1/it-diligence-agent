"""
Activity Templates V2 - Phase 5: Licensing

Phase 5: Software Licensing Deep Dive
- Microsoft Licensing (M365, Azure, Windows Server, EA)
- Database Licensing (Oracle, SQL Server, PostgreSQL)
- Infrastructure Licensing (VMware, Backup, Virtualization)
- Application Licensing (ERP, CRM, Specialty Software)

Licensing is often a major cost driver and risk area in carveouts.
Key considerations:
- Transfer rights (can licenses move to new entity?)
- True-up requirements
- Audit risk
- New procurement needs
- Volume discount impacts

Each activity template includes:
- name: Activity name
- description: What this activity involves
- activity_type: "implementation", "license", "assessment"
- cost_model: How cost is calculated
- timeline_months: Duration range
- requires_tsa: Whether TSA is typically needed
- tsa_duration: TSA duration if applicable
- prerequisites: What must happen first
- outputs: Deliverables
- notes: Implementation considerations

Cost Anchor Sources:
- Microsoft LSP/LAR pricing
- Oracle LMS audit experience
- VMware partner pricing
- Historical deal negotiations
"""

from typing import Dict, List

# Import shared modifiers from Phase 1
from tools_v2.activity_templates_v2 import COMPLEXITY_MULTIPLIERS, INDUSTRY_MODIFIERS

# =============================================================================
# PHASE 5: MICROSOFT LICENSING
# =============================================================================

MICROSOFT_LICENSE_TEMPLATES = {
    "license_issue": [
        # -----------------------------------------------------------------
        # ASSESSMENT
        # -----------------------------------------------------------------
        {
            "id": "LIC-MS-001",
            "name": "Microsoft licensing assessment",
            "description": "Comprehensive assessment of Microsoft licensing position and entitlements",
            "activity_type": "assessment",
            "phase": "assessment",
            "base_cost": (25000, 60000),
            "timeline_months": (0.5, 1.5),
            "requires_tsa": False,
            "prerequisites": [],
            "outputs": ["License inventory", "Entitlement analysis", "Compliance position", "Gap analysis"],
            "notes": "Critical for understanding transfer rights and true-up exposure",
        },
        {
            "id": "LIC-MS-002",
            "name": "Microsoft EA/enrollment analysis",
            "description": "Analyze Enterprise Agreement terms, transfer provisions, and termination rights",
            "activity_type": "assessment",
            "phase": "assessment",
            "base_cost": (15000, 40000),
            "timeline_months": (0.25, 0.75),
            "requires_tsa": False,
            "prerequisites": ["LIC-MS-001"],
            "outputs": ["EA summary", "Transfer provisions", "Termination analysis", "True-up obligations"],
        },
        {
            "id": "LIC-MS-003",
            "name": "Microsoft license deployment analysis",
            "description": "Analyze actual deployment vs. entitlements for compliance",
            "activity_type": "assessment",
            "phase": "assessment",
            "base_cost": (20000, 50000),
            "per_user_cost": (5, 15),
            "timeline_months": (0.5, 1),
            "requires_tsa": False,
            "prerequisites": ["LIC-MS-001"],
            "outputs": ["Deployment inventory", "Compliance gaps", "Over/under licensing", "Remediation needs"],
        },
        # -----------------------------------------------------------------
        # M365 LICENSING
        # -----------------------------------------------------------------
        {
            "id": "LIC-MS-010",
            "name": "M365 license strategy design",
            "description": "Design M365 licensing strategy for standalone entity",
            "activity_type": "license",
            "phase": "design",
            "base_cost": (20000, 50000),
            "timeline_months": (0.5, 1),
            "requires_tsa": False,
            "prerequisites": ["LIC-MS-001"],
            "outputs": ["License strategy", "SKU selection", "Cost model", "Procurement approach"],
        },
        {
            "id": "LIC-MS-011",
            "name": "M365 license procurement",
            "description": "Procure M365 licenses for standalone entity",
            "activity_type": "license",
            "phase": "build",
            "per_user_cost": (150, 400),  # Annual cost, varies by SKU
            "timeline_months": (0.25, 0.75),
            "requires_tsa": False,
            "prerequisites": ["LIC-MS-010"],
            "outputs": ["M365 licenses", "Tenant assignment", "License keys"],
            "notes": "Cost is annual; E3 ~$400/user, E5 ~$600/user, Business Premium ~$250/user",
        },
        {
            "id": "LIC-MS-012",
            "name": "M365 license assignment and activation",
            "description": "Assign and activate M365 licenses for users",
            "activity_type": "implementation",
            "phase": "migration",
            "per_user_cost": (5, 15),
            "base_cost": (10000, 25000),
            "timeline_months": (0.5, 1),
            "requires_tsa": False,
            "prerequisites": ["LIC-MS-011"],
            "outputs": ["Assigned licenses", "Activation verification", "Feature enablement"],
        },
        # -----------------------------------------------------------------
        # AZURE LICENSING
        # -----------------------------------------------------------------
        {
            "id": "LIC-MS-020",
            "name": "Azure subscription strategy",
            "description": "Design Azure subscription and billing strategy",
            "activity_type": "license",
            "phase": "design",
            "base_cost": (15000, 40000),
            "timeline_months": (0.25, 0.75),
            "requires_tsa": False,
            "prerequisites": ["LIC-MS-001"],
            "outputs": ["Subscription design", "Billing model", "Reserved instance strategy"],
        },
        {
            "id": "LIC-MS-021",
            "name": "Azure subscription transfer/creation",
            "description": "Transfer or create Azure subscriptions for standalone entity",
            "activity_type": "license",
            "phase": "build",
            "base_cost": (20000, 50000),
            "timeline_months": (0.5, 1),
            "requires_tsa": True,
            "tsa_duration": (2, 4),
            "prerequisites": ["LIC-MS-020"],
            "outputs": ["Azure subscriptions", "Billing setup", "RBAC configuration"],
        },
        {
            "id": "LIC-MS-022",
            "name": "Azure reserved instance transfer",
            "description": "Transfer or re-purchase Azure reserved instances",
            "activity_type": "license",
            "phase": "migration",
            "base_cost": (10000, 30000),
            "timeline_months": (0.25, 0.75),
            "requires_tsa": False,
            "prerequisites": ["LIC-MS-021"],
            "outputs": ["Transferred RIs", "New RI purchases", "Savings analysis"],
        },
        {
            "id": "LIC-MS-023",
            "name": "Azure Hybrid Benefit analysis",
            "description": "Analyze and optimize Azure Hybrid Benefit utilization",
            "activity_type": "license",
            "phase": "assessment",
            "base_cost": (10000, 25000),
            "timeline_months": (0.25, 0.5),
            "requires_tsa": False,
            "prerequisites": ["LIC-MS-001"],
            "outputs": ["AHB analysis", "Optimization opportunities", "License mobility assessment"],
        },
        # -----------------------------------------------------------------
        # WINDOWS SERVER / CAL
        # -----------------------------------------------------------------
        {
            "id": "LIC-MS-030",
            "name": "Windows Server licensing assessment",
            "description": "Assess Windows Server licensing requirements",
            "activity_type": "assessment",
            "phase": "assessment",
            "base_cost": (15000, 40000),
            "timeline_months": (0.25, 0.75),
            "requires_tsa": False,
            "prerequisites": ["LIC-MS-001"],
            "outputs": ["Server inventory", "Core counts", "Datacenter vs Standard analysis", "CAL requirements"],
        },
        {
            "id": "LIC-MS-031",
            "name": "Windows Server license procurement",
            "description": "Procure Windows Server licenses",
            "activity_type": "license",
            "phase": "build",
            "per_server_cost": (500, 2000),  # Varies by Datacenter vs Standard, core count
            "timeline_months": (0.25, 0.5),
            "requires_tsa": False,
            "prerequisites": ["LIC-MS-030"],
            "outputs": ["Server licenses", "License keys", "SA coverage"],
        },
        {
            "id": "LIC-MS-032",
            "name": "CAL procurement and assignment",
            "description": "Procure and assign Client Access Licenses",
            "activity_type": "license",
            "phase": "build",
            "per_user_cost": (30, 100),  # Per user CAL
            "timeline_months": (0.25, 0.5),
            "requires_tsa": False,
            "prerequisites": ["LIC-MS-030"],
            "outputs": ["User CALs", "Device CALs", "RDS CALs"],
        },
        # -----------------------------------------------------------------
        # EA TRANSITION
        # -----------------------------------------------------------------
        {
            "id": "LIC-MS-040",
            "name": "EA negotiation support",
            "description": "Support negotiation of new or transferred EA",
            "activity_type": "license",
            "phase": "build",
            "base_cost": (30000, 80000),
            "timeline_months": (1, 3),
            "requires_tsa": False,
            "prerequisites": ["LIC-MS-002"],
            "outputs": ["EA negotiation", "Term optimization", "Discount structure"],
            "notes": "Significant savings opportunity through proper negotiation",
        },
        {
            "id": "LIC-MS-041",
            "name": "EA partial transfer execution",
            "description": "Execute partial transfer of EA entitlements",
            "activity_type": "license",
            "phase": "migration",
            "base_cost": (20000, 50000),
            "timeline_months": (1, 2),
            "requires_tsa": True,
            "tsa_duration": (3, 6),
            "prerequisites": ["LIC-MS-040"],
            "outputs": ["Transfer agreement", "Entitlement documentation", "True-up settlement"],
        },
        {
            "id": "LIC-MS-042",
            "name": "CSP/NCE migration",
            "description": "Migrate to Cloud Solution Provider or New Commerce Experience",
            "activity_type": "license",
            "phase": "migration",
            "base_cost": (15000, 40000),
            "per_user_cost": (10, 30),
            "timeline_months": (0.5, 1.5),
            "requires_tsa": False,
            "prerequisites": ["LIC-MS-010"],
            "outputs": ["CSP setup", "License migration", "Billing transition"],
        },
    ],
}

# =============================================================================
# PHASE 5: DATABASE LICENSING
# =============================================================================

DATABASE_LICENSE_TEMPLATES = {
    "license_issue": [
        # -----------------------------------------------------------------
        # ORACLE
        # -----------------------------------------------------------------
        {
            "id": "LIC-DB-001",
            "name": "Oracle licensing assessment",
            "description": "Comprehensive Oracle licensing position assessment",
            "activity_type": "assessment",
            "phase": "assessment",
            "base_cost": (40000, 100000),
            "timeline_months": (1, 2),
            "requires_tsa": False,
            "prerequisites": [],
            "outputs": ["License inventory", "Deployment analysis", "Compliance position", "Options/packs usage"],
            "notes": "Critical - Oracle audits are common post-transaction",
        },
        {
            "id": "LIC-DB-002",
            "name": "Oracle ULA analysis",
            "description": "Analyze Unlimited License Agreement terms and certification requirements",
            "activity_type": "assessment",
            "phase": "assessment",
            "base_cost": (25000, 60000),
            "timeline_months": (0.5, 1),
            "requires_tsa": False,
            "prerequisites": ["LIC-DB-001"],
            "outputs": ["ULA analysis", "Certification strategy", "Deployment maximization"],
        },
        {
            "id": "LIC-DB-003",
            "name": "Oracle processor/NUP calculation",
            "description": "Calculate processor and Named User Plus requirements",
            "activity_type": "assessment",
            "phase": "assessment",
            "per_database_cost": (2000, 5000),
            "base_cost": (15000, 40000),
            "timeline_months": (0.5, 1),
            "requires_tsa": False,
            "prerequisites": ["LIC-DB-001"],
            "outputs": ["Processor calculations", "NUP calculations", "Virtualization impact", "Cloud licensing"],
        },
        {
            "id": "LIC-DB-004",
            "name": "Oracle license negotiation support",
            "description": "Support Oracle license negotiation for standalone entity",
            "activity_type": "license",
            "phase": "build",
            "base_cost": (50000, 150000),
            "timeline_months": (2, 6),
            "requires_tsa": True,
            "tsa_duration": (6, 12),
            "prerequisites": ["LIC-DB-001", "LIC-DB-003"],
            "outputs": ["License agreement", "Support contracts", "Discount negotiation"],
            "notes": "Oracle negotiations are complex - significant savings opportunity",
        },
        {
            "id": "LIC-DB-005",
            "name": "Oracle license transfer execution",
            "description": "Execute Oracle license transfer to new entity",
            "activity_type": "license",
            "phase": "migration",
            "base_cost": (25000, 60000),
            "timeline_months": (1, 3),
            "requires_tsa": True,
            "tsa_duration": (3, 6),
            "prerequisites": ["LIC-DB-004"],
            "outputs": ["Transfer agreement", "New CSI numbers", "Support transfer"],
        },
        {
            "id": "LIC-DB-006",
            "name": "Oracle audit defense preparation",
            "description": "Prepare for potential Oracle audit post-transaction",
            "activity_type": "assessment",
            "phase": "assessment",
            "base_cost": (30000, 80000),
            "timeline_months": (0.5, 1.5),
            "requires_tsa": False,
            "prerequisites": ["LIC-DB-001"],
            "outputs": ["Audit readiness", "Documentation package", "Remediation plan"],
        },
        # -----------------------------------------------------------------
        # SQL SERVER
        # -----------------------------------------------------------------
        {
            "id": "LIC-DB-010",
            "name": "SQL Server licensing assessment",
            "description": "Assess SQL Server licensing requirements and compliance",
            "activity_type": "assessment",
            "phase": "assessment",
            "base_cost": (20000, 50000),
            "timeline_months": (0.5, 1),
            "requires_tsa": False,
            "prerequisites": [],
            "outputs": ["SQL inventory", "Edition analysis", "Core calculations", "SA status"],
        },
        {
            "id": "LIC-DB-011",
            "name": "SQL Server license procurement",
            "description": "Procure SQL Server licenses for standalone entity",
            "activity_type": "license",
            "phase": "build",
            "per_core_cost": (2000, 8000),  # Varies by edition
            "base_cost": (15000, 40000),
            "timeline_months": (0.5, 1),
            "requires_tsa": False,
            "prerequisites": ["LIC-DB-010"],
            "outputs": ["SQL licenses", "SA enrollment", "License keys"],
            "notes": "Standard ~$4K/2-core, Enterprise ~$15K/2-core",
        },
        {
            "id": "LIC-DB-012",
            "name": "SQL Server edition optimization",
            "description": "Optimize SQL Server editions (Enterprise to Standard where possible)",
            "activity_type": "implementation",
            "phase": "build",
            "per_database_cost": (3000, 10000),
            "base_cost": (15000, 40000),
            "timeline_months": (1, 3),
            "requires_tsa": False,
            "prerequisites": ["LIC-DB-010"],
            "outputs": ["Edition analysis", "Downgrade assessment", "Migration plan", "Cost savings"],
        },
        # -----------------------------------------------------------------
        # OTHER DATABASES
        # -----------------------------------------------------------------
        {
            "id": "LIC-DB-020",
            "name": "PostgreSQL/MySQL enterprise support",
            "description": "Establish enterprise support for open source databases",
            "activity_type": "license",
            "phase": "build",
            "per_database_cost": (2000, 8000),  # Annual support
            "base_cost": (10000, 30000),
            "timeline_months": (0.25, 0.75),
            "requires_tsa": False,
            "prerequisites": [],
            "outputs": ["Support contracts", "SLA coverage", "Vendor relationship"],
        },
        {
            "id": "LIC-DB-021",
            "name": "MongoDB/NoSQL licensing",
            "description": "Establish licensing for NoSQL databases",
            "activity_type": "license",
            "phase": "build",
            "per_database_cost": (5000, 20000),  # Varies by edition
            "base_cost": (10000, 30000),
            "timeline_months": (0.25, 0.75),
            "requires_tsa": False,
            "prerequisites": [],
            "outputs": ["Database licenses", "Support contracts", "Cloud vs on-prem analysis"],
        },
    ],
}

# =============================================================================
# PHASE 5: INFRASTRUCTURE LICENSING
# =============================================================================

INFRASTRUCTURE_LICENSE_TEMPLATES = {
    "license_issue": [
        # -----------------------------------------------------------------
        # VMWARE
        # -----------------------------------------------------------------
        {
            "id": "LIC-INF-001",
            "name": "VMware licensing assessment",
            "description": "Assess VMware licensing position and requirements",
            "activity_type": "assessment",
            "phase": "assessment",
            "base_cost": (20000, 50000),
            "timeline_months": (0.5, 1),
            "requires_tsa": False,
            "prerequisites": [],
            "outputs": ["VMware inventory", "CPU socket counts", "Edition analysis", "Support status"],
        },
        {
            "id": "LIC-INF-002",
            "name": "VMware license procurement",
            "description": "Procure VMware licenses for standalone environment",
            "activity_type": "license",
            "phase": "build",
            "per_cpu_cost": (2000, 6000),  # Per CPU socket, varies by edition
            "base_cost": (15000, 40000),
            "timeline_months": (0.5, 1),
            "requires_tsa": False,
            "prerequisites": ["LIC-INF-001"],
            "outputs": ["VMware licenses", "Support contracts", "License keys"],
            "notes": "vSphere Standard ~$1.5K/CPU, Enterprise Plus ~$4.5K/CPU",
        },
        {
            "id": "LIC-INF-003",
            "name": "VMware to alternative platform assessment",
            "description": "Assess alternatives to VMware (Hyper-V, Nutanix, cloud)",
            "activity_type": "assessment",
            "phase": "assessment",
            "base_cost": (25000, 60000),
            "timeline_months": (0.5, 1.5),
            "requires_tsa": False,
            "prerequisites": ["LIC-INF-001"],
            "outputs": ["Alternative analysis", "TCO comparison", "Migration assessment", "Recommendation"],
            "notes": "Often considered due to VMware cost increases",
        },
        # -----------------------------------------------------------------
        # BACKUP SOFTWARE
        # -----------------------------------------------------------------
        {
            "id": "LIC-INF-010",
            "name": "Backup software licensing assessment",
            "description": "Assess backup software licensing (Veeam, Commvault, Veritas)",
            "activity_type": "assessment",
            "phase": "assessment",
            "base_cost": (15000, 40000),
            "timeline_months": (0.25, 0.75),
            "requires_tsa": False,
            "prerequisites": [],
            "outputs": ["Backup license inventory", "Capacity analysis", "Contract terms"],
        },
        {
            "id": "LIC-INF-011",
            "name": "Backup software license procurement",
            "description": "Procure backup software licenses",
            "activity_type": "license",
            "phase": "build",
            "per_vm_cost": (50, 200),  # Per VM or per TB
            "base_cost": (15000, 40000),
            "timeline_months": (0.25, 0.75),
            "requires_tsa": False,
            "prerequisites": ["LIC-INF-010"],
            "outputs": ["Backup licenses", "Support contracts", "Capacity planning"],
        },
        # -----------------------------------------------------------------
        # MONITORING / MANAGEMENT
        # -----------------------------------------------------------------
        {
            "id": "LIC-INF-020",
            "name": "Monitoring tools licensing",
            "description": "License monitoring tools (SCOM, Datadog, Splunk, etc.)",
            "activity_type": "license",
            "phase": "build",
            "per_server_cost": (100, 500),  # Per node/server
            "base_cost": (15000, 40000),
            "timeline_months": (0.25, 0.75),
            "requires_tsa": False,
            "prerequisites": [],
            "outputs": ["Monitoring licenses", "Agent deployment", "Dashboard setup"],
        },
        {
            "id": "LIC-INF-021",
            "name": "ITSM/ServiceNow licensing",
            "description": "License ITSM platform for standalone operations",
            "activity_type": "license",
            "phase": "build",
            "per_user_cost": (50, 200),  # Per fulfiller user
            "base_cost": (30000, 80000),
            "timeline_months": (0.5, 1.5),
            "requires_tsa": False,
            "prerequisites": [],
            "outputs": ["ITSM licenses", "Instance provisioning", "Module selection"],
        },
        # -----------------------------------------------------------------
        # NETWORK / SECURITY
        # -----------------------------------------------------------------
        {
            "id": "LIC-INF-030",
            "name": "Network equipment licensing",
            "description": "License network equipment (Cisco DNA, Meraki, etc.)",
            "activity_type": "license",
            "phase": "build",
            "per_device_cost": (200, 1000),
            "base_cost": (15000, 40000),
            "timeline_months": (0.25, 0.75),
            "requires_tsa": False,
            "prerequisites": [],
            "outputs": ["Network licenses", "Support contracts", "Smart account setup"],
        },
        {
            "id": "LIC-INF-031",
            "name": "Security tools licensing",
            "description": "License security tools (firewalls, EDR, SIEM)",
            "activity_type": "license",
            "phase": "build",
            "per_user_cost": (30, 100),  # Varies by tool
            "per_endpoint_cost": (20, 80),
            "base_cost": (25000, 75000),
            "timeline_months": (0.5, 1),
            "requires_tsa": False,
            "prerequisites": [],
            "outputs": ["Security licenses", "Subscription setup", "Deployment keys"],
        },
    ],
}

# =============================================================================
# PHASE 5: APPLICATION LICENSING
# =============================================================================

APPLICATION_LICENSE_TEMPLATES = {
    "license_issue": [
        # -----------------------------------------------------------------
        # ERP LICENSING
        # -----------------------------------------------------------------
        {
            "id": "LIC-APP-001",
            "name": "ERP licensing assessment",
            "description": "Assess ERP licensing position (SAP, Oracle, Dynamics)",
            "activity_type": "assessment",
            "phase": "assessment",
            "base_cost": (30000, 80000),
            "timeline_months": (0.5, 1.5),
            "requires_tsa": False,
            "prerequisites": [],
            "outputs": ["ERP license inventory", "Named user analysis", "Module entitlements", "Indirect access risk"],
        },
        {
            "id": "LIC-APP-002",
            "name": "SAP license transfer negotiation",
            "description": "Negotiate SAP license transfer or new agreement",
            "activity_type": "license",
            "phase": "build",
            "base_cost": (50000, 150000),
            "timeline_months": (2, 6),
            "requires_tsa": True,
            "tsa_duration": (6, 12),
            "prerequisites": ["LIC-APP-001"],
            "outputs": ["SAP agreement", "User type optimization", "Indirect access resolution"],
            "notes": "SAP licensing is complex - indirect access is major risk area",
        },
        {
            "id": "LIC-APP-003",
            "name": "Oracle ERP licensing",
            "description": "License Oracle ERP for standalone entity",
            "activity_type": "license",
            "phase": "build",
            "base_cost": (40000, 120000),
            "timeline_months": (2, 4),
            "requires_tsa": True,
            "tsa_duration": (6, 12),
            "prerequisites": ["LIC-APP-001"],
            "outputs": ["Oracle ERP licenses", "Application user rights", "Support contracts"],
        },
        {
            "id": "LIC-APP-004",
            "name": "Dynamics 365 licensing",
            "description": "License Dynamics 365 for standalone entity",
            "activity_type": "license",
            "phase": "build",
            "per_user_cost": (100, 300),  # Per user per month
            "base_cost": (20000, 50000),
            "timeline_months": (0.5, 1.5),
            "requires_tsa": False,
            "prerequisites": ["LIC-APP-001"],
            "outputs": ["D365 licenses", "Module selection", "User assignment"],
        },
        # -----------------------------------------------------------------
        # CRM LICENSING
        # -----------------------------------------------------------------
        {
            "id": "LIC-APP-010",
            "name": "Salesforce licensing assessment",
            "description": "Assess Salesforce licensing and contract terms",
            "activity_type": "assessment",
            "phase": "assessment",
            "base_cost": (15000, 40000),
            "timeline_months": (0.25, 0.75),
            "requires_tsa": False,
            "prerequisites": [],
            "outputs": ["License inventory", "Edition analysis", "Add-on usage", "Contract terms"],
        },
        {
            "id": "LIC-APP-011",
            "name": "Salesforce license procurement",
            "description": "Procure Salesforce licenses for standalone entity",
            "activity_type": "license",
            "phase": "build",
            "per_user_cost": (150, 400),  # Per user per month
            "base_cost": (15000, 40000),
            "timeline_months": (0.5, 1.5),
            "requires_tsa": False,
            "prerequisites": ["LIC-APP-010"],
            "outputs": ["Salesforce org", "User licenses", "Add-on licenses"],
            "notes": "Professional ~$75/user, Enterprise ~$150/user, Unlimited ~$300/user",
        },
        # -----------------------------------------------------------------
        # SPECIALTY SOFTWARE
        # -----------------------------------------------------------------
        {
            "id": "LIC-APP-020",
            "name": "Specialty software inventory",
            "description": "Inventory specialty and line-of-business applications",
            "activity_type": "assessment",
            "phase": "assessment",
            "per_app_cost": (500, 2000),
            "base_cost": (20000, 50000),
            "timeline_months": (0.5, 1),
            "requires_tsa": False,
            "prerequisites": [],
            "outputs": ["Software inventory", "License types", "Transfer rights", "Support status"],
        },
        {
            "id": "LIC-APP-021",
            "name": "Specialty software license transfer",
            "description": "Execute license transfers for specialty software",
            "activity_type": "license",
            "phase": "migration",
            "per_app_cost": (2000, 8000),
            "base_cost": (15000, 40000),
            "timeline_months": (1, 3),
            "requires_tsa": True,
            "tsa_duration": (2, 4),
            "prerequisites": ["LIC-APP-020"],
            "outputs": ["Transfer agreements", "New license keys", "Support contracts"],
        },
        {
            "id": "LIC-APP-022",
            "name": "Specialty software new procurement",
            "description": "Procure new licenses where transfer not possible",
            "activity_type": "license",
            "phase": "build",
            "per_app_cost": (5000, 25000),
            "base_cost": (20000, 60000),
            "timeline_months": (1, 3),
            "requires_tsa": False,
            "prerequisites": ["LIC-APP-020"],
            "outputs": ["New licenses", "Installation media", "Support contracts"],
        },
        # -----------------------------------------------------------------
        # DEVELOPMENT TOOLS
        # -----------------------------------------------------------------
        {
            "id": "LIC-APP-030",
            "name": "Development tools licensing",
            "description": "License development tools (Visual Studio, JetBrains, etc.)",
            "activity_type": "license",
            "phase": "build",
            "per_developer_cost": (500, 2000),
            "base_cost": (10000, 30000),
            "timeline_months": (0.25, 0.75),
            "requires_tsa": False,
            "prerequisites": [],
            "outputs": ["Dev tool licenses", "Subscription setup", "License server"],
        },
        {
            "id": "LIC-APP-031",
            "name": "DevOps platform licensing",
            "description": "License DevOps platforms (Azure DevOps, GitHub Enterprise, GitLab)",
            "activity_type": "license",
            "phase": "build",
            "per_user_cost": (20, 50),  # Per user per month
            "base_cost": (15000, 40000),
            "timeline_months": (0.25, 0.75),
            "requires_tsa": False,
            "prerequisites": [],
            "outputs": ["DevOps licenses", "Organization setup", "Pipeline configuration"],
        },
    ],
    "parent_dependency": [
        # Activities for when licensing is tied to parent
        {
            "id": "LIC-APP-040",
            "name": "Parent software agreement analysis",
            "description": "Analyze parent's software agreements for carveout rights",
            "activity_type": "assessment",
            "phase": "assessment",
            "base_cost": (25000, 60000),
            "timeline_months": (0.5, 1),
            "requires_tsa": False,
            "prerequisites": [],
            "outputs": ["Agreement inventory", "Transfer provisions", "Termination rights", "Volume discount impact"],
        },
        {
            "id": "LIC-APP-041",
            "name": "Volume discount impact analysis",
            "description": "Analyze impact of losing parent's volume discounts",
            "activity_type": "assessment",
            "phase": "assessment",
            "base_cost": (15000, 40000),
            "timeline_months": (0.25, 0.75),
            "requires_tsa": False,
            "prerequisites": ["LIC-APP-040"],
            "outputs": ["Discount analysis", "Cost impact", "Negotiation strategy"],
        },
    ],
}

# =============================================================================
# PHASE 5: LICENSE COMPLIANCE & OPTIMIZATION
# =============================================================================

LICENSE_COMPLIANCE_TEMPLATES = {
    "license_issue": [
        {
            "id": "LIC-CMP-001",
            "name": "Software asset management setup",
            "description": "Establish SAM capability for standalone entity",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (30000, 80000),
            "timeline_months": (1, 3),
            "requires_tsa": False,
            "prerequisites": [],
            "outputs": ["SAM tool deployment", "Discovery agents", "License tracking", "Compliance reporting"],
        },
        {
            "id": "LIC-CMP-002",
            "name": "License compliance remediation",
            "description": "Remediate license compliance gaps identified in assessment",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (25000, 75000),
            "timeline_months": (1, 3),
            "requires_tsa": False,
            "prerequisites": [],
            "outputs": ["Compliance remediation", "True-up purchases", "Deployment cleanup"],
        },
        {
            "id": "LIC-CMP-003",
            "name": "License optimization program",
            "description": "Optimize licensing to reduce costs",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (30000, 80000),
            "timeline_months": (2, 4),
            "requires_tsa": False,
            "prerequisites": [],
            "outputs": ["Optimization analysis", "Harvesting unused licenses", "Edition downgrades", "Cloud optimization"],
            "notes": "Typically identifies 15-30% savings opportunity",
        },
        {
            "id": "LIC-CMP-004",
            "name": "License contract consolidation",
            "description": "Consolidate multiple license contracts for efficiency",
            "activity_type": "license",
            "phase": "build",
            "base_cost": (20000, 50000),
            "timeline_months": (1, 3),
            "requires_tsa": False,
            "prerequisites": [],
            "outputs": ["Consolidated contracts", "Simplified management", "Renewal alignment"],
        },
    ],
}

# =============================================================================
# COMBINED TEMPLATES FOR PHASE 5
# =============================================================================

def get_phase5_templates() -> Dict[str, Dict[str, List[Dict]]]:
    """Get all Phase 5 templates organized by category and workstream."""
    return {
        "license_issue": {
            "microsoft": MICROSOFT_LICENSE_TEMPLATES["license_issue"],
            "database": DATABASE_LICENSE_TEMPLATES["license_issue"],
            "infrastructure": INFRASTRUCTURE_LICENSE_TEMPLATES["license_issue"],
            "applications": APPLICATION_LICENSE_TEMPLATES["license_issue"],
            "compliance": LICENSE_COMPLIANCE_TEMPLATES["license_issue"],
        },
        "parent_dependency": {
            "applications": APPLICATION_LICENSE_TEMPLATES.get("parent_dependency", []),
        },
    }


def get_phase5_activity_by_id(activity_id: str) -> Dict:
    """Look up a Phase 5 activity by its ID."""
    all_templates = get_phase5_templates()

    for category, workstreams in all_templates.items():
        for workstream, activities in workstreams.items():
            for activity in activities:
                if activity.get("id") == activity_id:
                    return activity

    return None


def calculate_phase5_activity_cost(
    activity: Dict,
    user_count: int = 1000,
    server_count: int = 50,
    database_count: int = 20,
    cpu_count: int = 30,
    core_count: int = 100,
    vm_count: int = 100,
    endpoint_count: int = None,
    device_count: int = 50,
    developer_count: int = 20,
    app_count: int = 30,
    complexity: str = "moderate",
    industry: str = "standard",
) -> tuple:
    """
    Calculate cost range for a Phase 5 activity based on quantities and modifiers.

    Returns: (low, high, formula)
    """
    endpoint_count = endpoint_count or int(user_count * 1.5)

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

    # Per-unit costs
    if "per_user_cost" in activity:
        per_low, per_high = activity["per_user_cost"]
        low += per_low * user_count
        high += per_high * user_count
        formula_parts.append(f"{user_count:,} users × ${per_low}-${per_high}")

    if "per_server_cost" in activity:
        per_low, per_high = activity["per_server_cost"]
        low += per_low * server_count
        high += per_high * server_count
        formula_parts.append(f"{server_count} servers × ${per_low:,}-${per_high:,}")

    if "per_database_cost" in activity:
        per_low, per_high = activity["per_database_cost"]
        low += per_low * database_count
        high += per_high * database_count
        formula_parts.append(f"{database_count} databases × ${per_low:,}-${per_high:,}")

    if "per_cpu_cost" in activity:
        per_low, per_high = activity["per_cpu_cost"]
        low += per_low * cpu_count
        high += per_high * cpu_count
        formula_parts.append(f"{cpu_count} CPUs × ${per_low:,}-${per_high:,}")

    if "per_core_cost" in activity:
        per_low, per_high = activity["per_core_cost"]
        low += per_low * core_count
        high += per_high * core_count
        formula_parts.append(f"{core_count} cores × ${per_low:,}-${per_high:,}")

    if "per_vm_cost" in activity:
        per_low, per_high = activity["per_vm_cost"]
        low += per_low * vm_count
        high += per_high * vm_count
        formula_parts.append(f"{vm_count} VMs × ${per_low:,}-${per_high:,}")

    if "per_endpoint_cost" in activity:
        per_low, per_high = activity["per_endpoint_cost"]
        low += per_low * endpoint_count
        high += per_high * endpoint_count
        formula_parts.append(f"{endpoint_count:,} endpoints × ${per_low}-${per_high}")

    if "per_device_cost" in activity:
        per_low, per_high = activity["per_device_cost"]
        low += per_low * device_count
        high += per_high * device_count
        formula_parts.append(f"{device_count} devices × ${per_low:,}-${per_high:,}")

    if "per_developer_cost" in activity:
        per_low, per_high = activity["per_developer_cost"]
        low += per_low * developer_count
        high += per_high * developer_count
        formula_parts.append(f"{developer_count} developers × ${per_low:,}-${per_high:,}")

    if "per_app_cost" in activity:
        per_low, per_high = activity["per_app_cost"]
        low += per_low * app_count
        high += per_high * app_count
        formula_parts.append(f"{app_count} apps × ${per_low:,}-${per_high:,}")

    formula = " + ".join(formula_parts) if formula_parts else "Unknown cost model"

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
    'MICROSOFT_LICENSE_TEMPLATES',
    'DATABASE_LICENSE_TEMPLATES',
    'INFRASTRUCTURE_LICENSE_TEMPLATES',
    'APPLICATION_LICENSE_TEMPLATES',
    'LICENSE_COMPLIANCE_TEMPLATES',
    'get_phase5_templates',
    'get_phase5_activity_by_id',
    'calculate_phase5_activity_cost',
]
