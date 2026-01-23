"""
IT Integration Cost Database - Research-Backed Estimates

This module provides realistic cost estimates for ~100 IT integration activities
based on industry research, vendor pricing, and consulting benchmarks.

METHODOLOGY:
- Base costs are researched from vendor pricing, industry reports, and consulting data
- Each activity has tiers: Small, Medium, Large, Enterprise
- Multipliers (size, industry, geography, maturity) adjust the base costs

SOURCES:
- NetSuite/SAP/Oracle ERP vendor pricing guides
- Salesforce implementation partner data
- Microsoft 365 migration service providers
- Okta/Azure AD pricing documentation
- Penetration testing industry reports
- ServiceNow partner pricing guides
- Gartner/Forrester research
- M&A integration consulting benchmarks

LAST UPDATED: January 2026
ACTIVITY COUNT: 100 activities across 12 categories
NOTE: These are estimates. Actual costs vary by vendor, scope, and complexity.
      Teams should validate against their specific deal context.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional, Any
from enum import Enum


class ProjectTier(Enum):
    """Project complexity/size tiers."""
    SMALL = "small"        # <100 users, simple scope
    MEDIUM = "medium"      # 100-500 users, standard scope
    LARGE = "large"        # 500-2000 users, complex scope
    ENTERPRISE = "enterprise"  # 2000+ users, highly complex


@dataclass
class CostEstimate:
    """A single cost estimate with range and metadata."""
    low: int
    high: int
    unit: str  # "project", "per_user", "per_month", "per_endpoint"
    notes: str = ""
    source: str = ""


@dataclass
class ActivityCost:
    """Cost data for a specific IT integration activity."""
    activity_id: str
    name: str
    category: str
    description: str

    # Costs by tier
    small: CostEstimate
    medium: CostEstimate
    large: CostEstimate
    enterprise: CostEstimate

    # Metadata
    typical_duration_weeks: Tuple[int, int]  # (min, max) weeks
    keywords: List[str] = field(default_factory=list)
    sources: List[str] = field(default_factory=list)
    notes: str = ""


# =============================================================================
# COMPREHENSIVE COST DATABASE
# =============================================================================

COST_DATABASE: Dict[str, ActivityCost] = {

    # =========================================================================
    # ERP SYSTEMS (10 activities)
    # =========================================================================

    "erp_netsuite_implementation": ActivityCost(
        activity_id="ERP-001",
        name="NetSuite ERP Implementation",
        category="erp",
        description="Full NetSuite ERP implementation including configuration, data migration, and training",
        small=CostEstimate(50_000, 100_000, "project", "Starter edition, basic modules", "NetSuite partner data"),
        medium=CostEstimate(100_000, 250_000, "project", "Mid-market edition, multiple modules", "Kimberlite Partners"),
        large=CostEstimate(250_000, 500_000, "project", "Enterprise edition, complex integrations", "Industry benchmarks"),
        enterprise=CostEstimate(500_000, 1_500_000, "project", "Multi-subsidiary, global rollout", "Top10ERP.org"),
        typical_duration_weeks=(12, 40),
        keywords=["netsuite", "erp", "oracle"],
        sources=["NetSuite pricing guides", "Kimberlite Partners", "SCS Cloud"],
    ),

    "erp_sap_s4hana_implementation": ActivityCost(
        activity_id="ERP-002",
        name="SAP S/4HANA Implementation",
        category="erp",
        description="SAP S/4HANA implementation including migration from legacy SAP or greenfield",
        small=CostEstimate(200_000, 500_000, "project", "SAP Business One, limited scope"),
        medium=CostEstimate(500_000, 1_500_000, "project", "S/4HANA Cloud, standard modules"),
        large=CostEstimate(1_500_000, 5_000_000, "project", "S/4HANA on-prem, full suite"),
        enterprise=CostEstimate(5_000_000, 20_000_000, "project", "Global rollout, complex landscape"),
        typical_duration_weeks=(24, 104),
        keywords=["sap", "s4hana", "erp", "hana"],
        sources=["SAP partner network", "Gartner research"],
    ),

    "erp_oracle_cloud_implementation": ActivityCost(
        activity_id="ERP-003",
        name="Oracle Cloud ERP Implementation",
        category="erp",
        description="Oracle Fusion Cloud ERP implementation",
        small=CostEstimate(150_000, 350_000, "project", "Core financials only"),
        medium=CostEstimate(350_000, 800_000, "project", "Financials + procurement"),
        large=CostEstimate(800_000, 2_000_000, "project", "Full suite implementation"),
        enterprise=CostEstimate(2_000_000, 8_000_000, "project", "Multi-pillar, global"),
        typical_duration_weeks=(20, 78),
        keywords=["oracle", "fusion", "erp", "cloud"],
        sources=["Oracle partner data"],
    ),

    "erp_integration_middleware": ActivityCost(
        activity_id="ERP-004",
        name="ERP Integration (Middleware/API)",
        category="erp",
        description="Integrate ERP with other systems via middleware or API development",
        small=CostEstimate(25_000, 75_000, "project", "Single integration, standard APIs"),
        medium=CostEstimate(75_000, 200_000, "project", "3-5 integrations, custom mapping"),
        large=CostEstimate(200_000, 500_000, "project", "10+ integrations, complex orchestration"),
        enterprise=CostEstimate(500_000, 1_500_000, "project", "Enterprise integration platform"),
        typical_duration_weeks=(4, 24),
        keywords=["erp", "integration", "api", "middleware", "mulesoft", "boomi"],
        sources=["Integration partner rates"],
    ),

    "erp_data_migration": ActivityCost(
        activity_id="ERP-005",
        name="ERP Data Migration",
        category="erp",
        description="Extract, transform, and load data from legacy ERP to new system",
        small=CostEstimate(20_000, 50_000, "project", "Basic master data"),
        medium=CostEstimate(50_000, 150_000, "project", "Master + transactional data"),
        large=CostEstimate(150_000, 400_000, "project", "Full historical migration"),
        enterprise=CostEstimate(400_000, 1_000_000, "project", "Multi-system consolidation"),
        typical_duration_weeks=(4, 20),
        keywords=["erp", "data", "migration", "etl"],
        sources=["Data migration consultants"],
    ),

    # =========================================================================
    # CRM SYSTEMS (8 activities)
    # =========================================================================

    "crm_salesforce_implementation": ActivityCost(
        activity_id="CRM-001",
        name="Salesforce CRM Implementation",
        category="crm",
        description="Salesforce Sales Cloud or Service Cloud implementation",
        small=CostEstimate(15_000, 50_000, "project", "Basic Sales Cloud", "Ascendix research"),
        medium=CostEstimate(50_000, 150_000, "project", "Sales + Service Cloud", "CloudArc"),
        large=CostEstimate(150_000, 400_000, "project", "Multi-cloud with integrations"),
        enterprise=CostEstimate(400_000, 1_500_000, "project", "Full platform + CPQ + custom"),
        typical_duration_weeks=(6, 26),
        keywords=["salesforce", "crm", "sales cloud", "service cloud"],
        sources=["Ascendix", "CloudArc", "Salesforce partners"],
    ),

    "crm_hubspot_implementation": ActivityCost(
        activity_id="CRM-002",
        name="HubSpot CRM Implementation",
        category="crm",
        description="HubSpot CRM Hub implementation and configuration",
        small=CostEstimate(5_000, 20_000, "project", "Starter tier, basic setup"),
        medium=CostEstimate(20_000, 75_000, "project", "Professional tier, integrations"),
        large=CostEstimate(75_000, 200_000, "project", "Enterprise tier, complex workflows"),
        enterprise=CostEstimate(200_000, 500_000, "project", "Multi-hub, global rollout"),
        typical_duration_weeks=(4, 16),
        keywords=["hubspot", "crm", "marketing"],
        sources=["HubSpot partner data"],
    ),

    "crm_dynamics_implementation": ActivityCost(
        activity_id="CRM-003",
        name="Microsoft Dynamics 365 CRM Implementation",
        category="crm",
        description="Dynamics 365 Sales/Customer Service implementation",
        small=CostEstimate(30_000, 80_000, "project", "Sales module only"),
        medium=CostEstimate(80_000, 200_000, "project", "Sales + Service"),
        large=CostEstimate(200_000, 500_000, "project", "Full CRM suite"),
        enterprise=CostEstimate(500_000, 1_500_000, "project", "Integrated with D365 ERP"),
        typical_duration_weeks=(8, 30),
        keywords=["dynamics", "d365", "crm", "microsoft"],
        sources=["Microsoft partner network"],
    ),

    "crm_migration": ActivityCost(
        activity_id="CRM-004",
        name="CRM to CRM Migration",
        category="crm",
        description="Migrate from one CRM platform to another (e.g., legacy to Salesforce)",
        small=CostEstimate(15_000, 40_000, "project", "<10K records"),
        medium=CostEstimate(40_000, 100_000, "project", "10K-100K records"),
        large=CostEstimate(100_000, 300_000, "project", "100K-1M records, complex mapping"),
        enterprise=CostEstimate(300_000, 800_000, "project", "Multi-system consolidation"),
        typical_duration_weeks=(4, 16),
        keywords=["crm", "migration", "data"],
        sources=["CRM migration specialists"],
    ),

    # =========================================================================
    # IDENTITY & ACCESS MANAGEMENT (10 activities)
    # =========================================================================

    "iam_okta_implementation": ActivityCost(
        activity_id="IAM-001",
        name="Okta SSO/IAM Implementation",
        category="identity",
        description="Okta Workforce Identity implementation including SSO and MFA",
        small=CostEstimate(15_000, 40_000, "project", "<200 users, basic SSO"),
        medium=CostEstimate(40_000, 100_000, "project", "200-1000 users, SSO + MFA"),
        large=CostEstimate(100_000, 250_000, "project", "1000-5000 users, lifecycle mgmt"),
        enterprise=CostEstimate(250_000, 600_000, "project", "5000+ users, full IGA"),
        typical_duration_weeks=(4, 16),
        keywords=["okta", "sso", "identity", "iam", "mfa"],
        sources=["Okta pricing", "SuperTokens guide"],
        notes="Plus $2-6/user/month ongoing license",
    ),

    "iam_azure_ad_implementation": ActivityCost(
        activity_id="IAM-002",
        name="Azure AD / Entra ID Implementation",
        category="identity",
        description="Microsoft Entra ID (Azure AD) setup and configuration",
        small=CostEstimate(10_000, 30_000, "project", "Basic SSO, cloud-only"),
        medium=CostEstimate(30_000, 80_000, "project", "Hybrid with AD Connect"),
        large=CostEstimate(80_000, 200_000, "project", "P1/P2 features, conditional access"),
        enterprise=CostEstimate(200_000, 500_000, "project", "PIM, identity governance"),
        typical_duration_weeks=(2, 12),
        keywords=["azure", "entra", "ad", "active directory", "sso", "microsoft"],
        sources=["Microsoft partner data"],
    ),

    "iam_ad_migration": ActivityCost(
        activity_id="IAM-003",
        name="Active Directory Migration/Consolidation",
        category="identity",
        description="Migrate or consolidate Active Directory forests/domains",
        small=CostEstimate(25_000, 75_000, "project", "Single domain, <500 users"),
        medium=CostEstimate(75_000, 200_000, "project", "Multi-domain, 500-2000 users"),
        large=CostEstimate(200_000, 500_000, "project", "Forest consolidation, 2000-10000 users"),
        enterprise=CostEstimate(500_000, 1_500_000, "project", "Multi-forest, global"),
        typical_duration_weeks=(8, 30),
        keywords=["active directory", "ad", "migration", "consolidation", "forest"],
        sources=["Quest Migration Manager", "Semperis"],
    ),

    "iam_pam_implementation": ActivityCost(
        activity_id="IAM-004",
        name="Privileged Access Management (PAM) Implementation",
        category="identity",
        description="Implement PAM solution (CyberArk, BeyondTrust, etc.)",
        small=CostEstimate(50_000, 150_000, "project", "<100 privileged accounts"),
        medium=CostEstimate(150_000, 400_000, "project", "100-500 accounts"),
        large=CostEstimate(400_000, 1_000_000, "project", "500-2000 accounts"),
        enterprise=CostEstimate(1_000_000, 3_000_000, "project", "2000+ accounts, full enterprise"),
        typical_duration_weeks=(12, 40),
        keywords=["pam", "cyberark", "beyondtrust", "privileged"],
        sources=["PAM vendor pricing"],
    ),

    # =========================================================================
    # CLOUD & INFRASTRUCTURE (15 activities)
    # =========================================================================

    "cloud_aws_migration": ActivityCost(
        activity_id="CLOUD-001",
        name="AWS Cloud Migration",
        category="cloud",
        description="Migrate workloads from on-premises to AWS",
        small=CostEstimate(40_000, 100_000, "project", "<20 VMs, lift-and-shift"),
        medium=CostEstimate(100_000, 300_000, "project", "20-100 VMs, some re-platforming"),
        large=CostEstimate(300_000, 800_000, "project", "100-500 VMs, hybrid approach"),
        enterprise=CostEstimate(800_000, 3_000_000, "project", "500+ VMs, re-architecture"),
        typical_duration_weeks=(8, 52),
        keywords=["aws", "cloud", "migration", "ec2"],
        sources=["AWS migration partners", "Appinventiv"],
    ),

    "cloud_azure_migration": ActivityCost(
        activity_id="CLOUD-002",
        name="Azure Cloud Migration",
        category="cloud",
        description="Migrate workloads from on-premises to Microsoft Azure",
        small=CostEstimate(40_000, 100_000, "project", "<20 VMs"),
        medium=CostEstimate(100_000, 300_000, "project", "20-100 VMs"),
        large=CostEstimate(300_000, 800_000, "project", "100-500 VMs"),
        enterprise=CostEstimate(800_000, 3_000_000, "project", "500+ VMs, Azure Landing Zone"),
        typical_duration_weeks=(8, 52),
        keywords=["azure", "cloud", "migration", "microsoft"],
        sources=["Microsoft Azure Migrate", "DuploCloud"],
    ),

    "cloud_m365_migration": ActivityCost(
        activity_id="CLOUD-003",
        name="Microsoft 365 Migration",
        category="cloud",
        description="Migrate email and collaboration to Microsoft 365",
        small=CostEstimate(5_000, 20_000, "project", "<100 mailboxes", "eSudo, Intuitive IT"),
        medium=CostEstimate(20_000, 75_000, "project", "100-500 mailboxes"),
        large=CostEstimate(75_000, 200_000, "project", "500-2000 mailboxes"),
        enterprise=CostEstimate(200_000, 600_000, "project", "2000+ mailboxes, hybrid"),
        typical_duration_weeks=(2, 16),
        keywords=["m365", "office 365", "microsoft", "email", "exchange", "migration"],
        sources=["eSudo", "Intuitive IT", "Agile IT"],
        notes="$50-225 per user typical range",
    ),

    "cloud_google_workspace_migration": ActivityCost(
        activity_id="CLOUD-004",
        name="Google Workspace Migration",
        category="cloud",
        description="Migrate to Google Workspace from other platforms",
        small=CostEstimate(5_000, 15_000, "project", "<100 users"),
        medium=CostEstimate(15_000, 50_000, "project", "100-500 users"),
        large=CostEstimate(50_000, 150_000, "project", "500-2000 users"),
        enterprise=CostEstimate(150_000, 400_000, "project", "2000+ users"),
        typical_duration_weeks=(2, 12),
        keywords=["google", "workspace", "gsuite", "gmail", "migration"],
        sources=["Google Cloud partners"],
    ),

    "infra_datacenter_consolidation": ActivityCost(
        activity_id="INFRA-001",
        name="Data Center Consolidation",
        category="infrastructure",
        description="Consolidate multiple data centers into fewer facilities",
        small=CostEstimate(100_000, 300_000, "project", "2 to 1 consolidation, <50 servers"),
        medium=CostEstimate(300_000, 800_000, "project", "3-4 to 1, 50-200 servers"),
        large=CostEstimate(800_000, 2_000_000, "project", "5+ to 1-2, 200-1000 servers"),
        enterprise=CostEstimate(2_000_000, 10_000_000, "project", "Global consolidation"),
        typical_duration_weeks=(20, 78),
        keywords=["datacenter", "consolidation", "colocation"],
        sources=["Data center consultants", "TierPoint"],
    ),

    "infra_network_refresh": ActivityCost(
        activity_id="INFRA-002",
        name="Network Infrastructure Refresh",
        category="infrastructure",
        description="Upgrade/replace network switches, routers, firewalls",
        small=CostEstimate(15_000, 50_000, "project", "Single site, <50 ports"),
        medium=CostEstimate(50_000, 150_000, "project", "2-5 sites, 50-200 ports"),
        large=CostEstimate(150_000, 400_000, "project", "5-20 sites, 200-1000 ports"),
        enterprise=CostEstimate(400_000, 1_500_000, "project", "20+ sites, full refresh"),
        typical_duration_weeks=(4, 20),
        keywords=["network", "switch", "router", "firewall", "refresh", "upgrade"],
        sources=["Optimal Networks", "Fortinet pricing"],
    ),

    "infra_server_refresh": ActivityCost(
        activity_id="INFRA-003",
        name="Server Infrastructure Refresh",
        category="infrastructure",
        description="Replace end-of-life servers with new hardware or virtualization",
        small=CostEstimate(20_000, 75_000, "project", "<10 servers"),
        medium=CostEstimate(75_000, 250_000, "project", "10-50 servers"),
        large=CostEstimate(250_000, 750_000, "project", "50-200 servers"),
        enterprise=CostEstimate(750_000, 3_000_000, "project", "200+ servers"),
        typical_duration_weeks=(8, 30),
        keywords=["server", "hardware", "refresh", "vmware", "hyperv"],
        sources=["Server vendor pricing"],
    ),

    # =========================================================================
    # CYBERSECURITY (15 activities)
    # =========================================================================

    "security_siem_implementation": ActivityCost(
        activity_id="SEC-001",
        name="SIEM Implementation (Splunk/Sentinel)",
        category="cybersecurity",
        description="Deploy and configure SIEM platform",
        small=CostEstimate(50_000, 150_000, "project", "<500GB/day, basic use cases"),
        medium=CostEstimate(150_000, 400_000, "project", "500GB-2TB/day, standard SOC"),
        large=CostEstimate(400_000, 1_000_000, "project", "2-10TB/day, advanced analytics"),
        enterprise=CostEstimate(1_000_000, 3_000_000, "project", "10+TB/day, 24/7 SOC"),
        typical_duration_weeks=(8, 26),
        keywords=["siem", "splunk", "sentinel", "security", "soc"],
        sources=["Splunk partner data", "Microsoft Sentinel pricing"],
    ),

    "security_edr_deployment": ActivityCost(
        activity_id="SEC-002",
        name="EDR Deployment (CrowdStrike/SentinelOne)",
        category="cybersecurity",
        description="Deploy endpoint detection and response solution",
        small=CostEstimate(10_000, 30_000, "project", "<500 endpoints"),
        medium=CostEstimate(30_000, 80_000, "project", "500-2000 endpoints"),
        large=CostEstimate(80_000, 200_000, "project", "2000-10000 endpoints"),
        enterprise=CostEstimate(200_000, 500_000, "project", "10000+ endpoints"),
        typical_duration_weeks=(2, 8),
        keywords=["edr", "crowdstrike", "sentinelone", "endpoint", "security"],
        sources=["CrowdStrike pricing", "SentinelOne pricing"],
        notes="Plus $60-185/endpoint/year ongoing",
    ),

    "security_pentest": ActivityCost(
        activity_id="SEC-003",
        name="Penetration Testing",
        category="cybersecurity",
        description="External and internal penetration testing engagement",
        small=CostEstimate(5_000, 15_000, "project", "Single web app or network"),
        medium=CostEstimate(15_000, 40_000, "project", "Web + network + social engineering"),
        large=CostEstimate(40_000, 100_000, "project", "Comprehensive assessment"),
        enterprise=CostEstimate(100_000, 300_000, "project", "Red team engagement, multiple sites"),
        typical_duration_weeks=(1, 6),
        keywords=["pentest", "penetration", "security", "assessment", "red team"],
        sources=["TCM Security", "Blaze InfoSec", "Invicti"],
    ),

    "security_vulnerability_program": ActivityCost(
        activity_id="SEC-004",
        name="Vulnerability Management Program",
        category="cybersecurity",
        description="Implement continuous vulnerability scanning and remediation program",
        small=CostEstimate(20_000, 50_000, "project", "Basic scanning, <500 assets"),
        medium=CostEstimate(50_000, 150_000, "project", "Managed scanning, 500-2000 assets"),
        large=CostEstimate(150_000, 400_000, "project", "Full program, 2000-10000 assets"),
        enterprise=CostEstimate(400_000, 1_000_000, "project", "Enterprise program, 10000+ assets"),
        typical_duration_weeks=(4, 16),
        keywords=["vulnerability", "scanning", "qualys", "tenable", "rapid7"],
        sources=["Vulnerability management vendors"],
    ),

    "security_compliance_remediation": ActivityCost(
        activity_id="SEC-005",
        name="Security Compliance Remediation (SOC2/ISO27001)",
        category="cybersecurity",
        description="Remediate gaps to achieve security compliance certification",
        small=CostEstimate(30_000, 80_000, "project", "SOC2 Type 1, minimal gaps"),
        medium=CostEstimate(80_000, 200_000, "project", "SOC2 Type 2, moderate gaps"),
        large=CostEstimate(200_000, 500_000, "project", "ISO27001 + SOC2, significant gaps"),
        enterprise=CostEstimate(500_000, 1_500_000, "project", "Multi-framework, major remediation"),
        typical_duration_weeks=(12, 40),
        keywords=["soc2", "iso27001", "compliance", "security", "audit"],
        sources=["Compliance consultants"],
    ),

    # =========================================================================
    # BACKUP & DISASTER RECOVERY (5 activities)
    # =========================================================================

    "dr_backup_implementation": ActivityCost(
        activity_id="DR-001",
        name="Enterprise Backup Solution Implementation",
        category="disaster_recovery",
        description="Implement enterprise backup solution (Veeam, Commvault)",
        small=CostEstimate(20_000, 60_000, "project", "<50 VMs"),
        medium=CostEstimate(60_000, 150_000, "project", "50-200 VMs"),
        large=CostEstimate(150_000, 400_000, "project", "200-1000 VMs"),
        enterprise=CostEstimate(400_000, 1_000_000, "project", "1000+ VMs, global"),
        typical_duration_weeks=(4, 16),
        keywords=["backup", "veeam", "commvault", "recovery"],
        sources=["Veeam pricing", "Commvault partners"],
    ),

    "dr_plan_development": ActivityCost(
        activity_id="DR-002",
        name="Disaster Recovery Plan Development",
        category="disaster_recovery",
        description="Develop comprehensive DR plan with testing procedures",
        small=CostEstimate(15_000, 40_000, "project", "Single site, basic plan"),
        medium=CostEstimate(40_000, 100_000, "project", "Multi-site, detailed runbooks"),
        large=CostEstimate(100_000, 250_000, "project", "Enterprise-wide, automated testing"),
        enterprise=CostEstimate(250_000, 600_000, "project", "Global DR program"),
        typical_duration_weeks=(4, 16),
        keywords=["disaster recovery", "dr", "bcdr", "plan", "rto", "rpo"],
        sources=["DR consultants"],
    ),

    # =========================================================================
    # ITSM & SERVICE MANAGEMENT (5 activities)
    # =========================================================================

    "itsm_servicenow_implementation": ActivityCost(
        activity_id="ITSM-001",
        name="ServiceNow ITSM Implementation",
        category="itsm",
        description="Implement ServiceNow IT Service Management platform",
        small=CostEstimate(75_000, 200_000, "project", "Core ITSM only"),
        medium=CostEstimate(200_000, 500_000, "project", "ITSM + ITOM"),
        large=CostEstimate(500_000, 1_200_000, "project", "Multi-module, integrations"),
        enterprise=CostEstimate(1_200_000, 4_500_000, "project", "Full platform, global"),
        typical_duration_weeks=(12, 52),
        keywords=["servicenow", "itsm", "itil"],
        sources=["ServiceNow pricing guide", "Aelum Consulting"],
        notes="Plus $50-100/user/month licensing",
    ),

    "itsm_jira_implementation": ActivityCost(
        activity_id="ITSM-002",
        name="Jira Service Management Implementation",
        category="itsm",
        description="Implement Atlassian Jira Service Management",
        small=CostEstimate(10_000, 30_000, "project", "Basic setup, <100 agents"),
        medium=CostEstimate(30_000, 80_000, "project", "Standard, 100-500 agents"),
        large=CostEstimate(80_000, 200_000, "project", "Enterprise, 500-2000 agents"),
        enterprise=CostEstimate(200_000, 500_000, "project", "Data Center, 2000+ agents"),
        typical_duration_weeks=(4, 16),
        keywords=["jira", "jsm", "itsm", "atlassian"],
        sources=["Atlassian partners"],
    ),

    # =========================================================================
    # HR & HCM SYSTEMS (5 activities)
    # =========================================================================

    "hcm_workday_implementation": ActivityCost(
        activity_id="HCM-001",
        name="Workday HCM Implementation",
        category="hcm",
        description="Implement Workday Human Capital Management",
        small=CostEstimate(200_000, 500_000, "project", "Core HCM, <1000 employees"),
        medium=CostEstimate(500_000, 1_500_000, "project", "HCM + Payroll, 1000-5000 employees"),
        large=CostEstimate(1_500_000, 4_000_000, "project", "Full suite, 5000-15000 employees"),
        enterprise=CostEstimate(4_000_000, 10_000_000, "project", "Global, 15000+ employees"),
        typical_duration_weeks=(24, 78),
        keywords=["workday", "hcm", "hr", "payroll"],
        sources=["Workday implementation partners", "OutSail"],
        notes="Implementation typically 100-200% of annual subscription",
    ),

    "hcm_adp_implementation": ActivityCost(
        activity_id="HCM-002",
        name="ADP Workforce Now Implementation",
        category="hcm",
        description="Implement ADP payroll and HR solution",
        small=CostEstimate(15_000, 40_000, "project", "<100 employees"),
        medium=CostEstimate(40_000, 100_000, "project", "100-500 employees"),
        large=CostEstimate(100_000, 250_000, "project", "500-2000 employees"),
        enterprise=CostEstimate(250_000, 600_000, "project", "2000+ employees"),
        typical_duration_weeks=(6, 20),
        keywords=["adp", "payroll", "hr", "workforce"],
        sources=["ADP partner data"],
    ),

    # =========================================================================
    # APPLICATION RATIONALIZATION (5 activities)
    # =========================================================================

    "app_portfolio_assessment": ActivityCost(
        activity_id="APP-001",
        name="Application Portfolio Assessment",
        category="applications",
        description="Assess application portfolio for rationalization opportunities",
        small=CostEstimate(20_000, 50_000, "project", "<50 applications"),
        medium=CostEstimate(50_000, 120_000, "project", "50-200 applications"),
        large=CostEstimate(120_000, 300_000, "project", "200-500 applications"),
        enterprise=CostEstimate(300_000, 800_000, "project", "500+ applications"),
        typical_duration_weeks=(4, 12),
        keywords=["application", "portfolio", "rationalization", "assessment"],
        sources=["IT consulting firms"],
    ),

    "app_decommission": ActivityCost(
        activity_id="APP-002",
        name="Application Decommissioning",
        category="applications",
        description="Safely decommission legacy applications including data archival",
        small=CostEstimate(10_000, 30_000, "project", "Simple app, minimal dependencies"),
        medium=CostEstimate(30_000, 80_000, "project", "Medium complexity, integrations"),
        large=CostEstimate(80_000, 200_000, "project", "Complex app, data retention needs"),
        enterprise=CostEstimate(200_000, 500_000, "project", "Business-critical legacy system"),
        typical_duration_weeks=(4, 16),
        keywords=["decommission", "legacy", "application", "sunset"],
        sources=["IT decommissioning specialists"],
    ),

    # =========================================================================
    # M&A SPECIFIC ACTIVITIES (10 activities)
    # =========================================================================

    "ma_it_due_diligence": ActivityCost(
        activity_id="MA-001",
        name="IT Due Diligence Assessment",
        category="ma_integration",
        description="Comprehensive IT due diligence for M&A transaction",
        small=CostEstimate(25_000, 75_000, "project", "Small target, <$50M revenue"),
        medium=CostEstimate(75_000, 200_000, "project", "Mid-market, $50-250M revenue"),
        large=CostEstimate(200_000, 500_000, "project", "Large target, $250M-1B revenue"),
        enterprise=CostEstimate(500_000, 1_500_000, "project", "Enterprise, >$1B revenue"),
        typical_duration_weeks=(2, 8),
        keywords=["due diligence", "m&a", "assessment", "acquisition"],
        sources=["IMAA Institute", "Synoptek"],
        notes="Typically 0.5-2% of deal value",
    ),

    "ma_day1_readiness": ActivityCost(
        activity_id="MA-002",
        name="Day 1 Readiness Program",
        category="ma_integration",
        description="Ensure IT systems operational on Day 1 of acquisition close",
        small=CostEstimate(50_000, 150_000, "project", "Basic connectivity, email"),
        medium=CostEstimate(150_000, 400_000, "project", "Standard Day 1 requirements"),
        large=CostEstimate(400_000, 1_000_000, "project", "Complex carve-out"),
        enterprise=CostEstimate(1_000_000, 3_000_000, "project", "Full standalone capability"),
        typical_duration_weeks=(4, 16),
        keywords=["day 1", "m&a", "readiness", "acquisition", "close"],
        sources=["M&A integration consultants"],
    ),

    "ma_tsa_management": ActivityCost(
        activity_id="MA-003",
        name="Transition Services Agreement (TSA) Management",
        category="ma_integration",
        description="Manage IT services during TSA period post-close",
        small=CostEstimate(25_000, 75_000, "per_month", "Limited services"),
        medium=CostEstimate(75_000, 200_000, "per_month", "Standard IT services"),
        large=CostEstimate(200_000, 500_000, "per_month", "Comprehensive services"),
        enterprise=CostEstimate(500_000, 1_500_000, "per_month", "Full outsourced IT"),
        typical_duration_weeks=(26, 104),
        keywords=["tsa", "transition services", "m&a"],
        sources=["EY", "Deloitte M&A practice"],
    ),

    "ma_integration_planning": ActivityCost(
        activity_id="MA-004",
        name="IT Integration Planning",
        category="ma_integration",
        description="Develop detailed IT integration roadmap and plan",
        small=CostEstimate(30_000, 80_000, "project", "Simple integration"),
        medium=CostEstimate(80_000, 200_000, "project", "Standard integration"),
        large=CostEstimate(200_000, 500_000, "project", "Complex integration"),
        enterprise=CostEstimate(500_000, 1_500_000, "project", "Transformational integration"),
        typical_duration_weeks=(4, 12),
        keywords=["integration", "planning", "m&a", "roadmap"],
        sources=["M&A consulting firms", "Fifth Chrome"],
    ),

    "ma_synergy_capture": ActivityCost(
        activity_id="MA-005",
        name="IT Cost Synergy Capture",
        category="ma_integration",
        description="Execute IT cost synergy initiatives identified in deal model",
        small=CostEstimate(50_000, 150_000, "project", "<$1M synergies targeted"),
        medium=CostEstimate(150_000, 400_000, "project", "$1-5M synergies targeted"),
        large=CostEstimate(400_000, 1_000_000, "project", "$5-20M synergies targeted"),
        enterprise=CostEstimate(1_000_000, 3_000_000, "project", "$20M+ synergies targeted"),
        typical_duration_weeks=(12, 52),
        keywords=["synergy", "cost", "m&a", "integration"],
        sources=["DealRoom", "EY M&A integration"],
    ),

    # =========================================================================
    # ADDITIONAL CRM (4 activities)
    # =========================================================================

    "crm_zendesk_implementation": ActivityCost(
        activity_id="CRM-005",
        name="Zendesk Implementation",
        category="crm",
        description="Implement Zendesk support/service platform",
        small=CostEstimate(8_000, 25_000, "project", "Suite Team, <100 agents"),
        medium=CostEstimate(25_000, 75_000, "project", "Suite Growth, 100-500 agents"),
        large=CostEstimate(75_000, 200_000, "project", "Suite Professional, custom workflows"),
        enterprise=CostEstimate(200_000, 500_000, "project", "Suite Enterprise, full customization"),
        typical_duration_weeks=(3, 12),
        keywords=["zendesk", "support", "ticketing", "helpdesk"],
        sources=["Zendesk pricing", "Partner implementations"],
    ),

    "crm_freshworks_implementation": ActivityCost(
        activity_id="CRM-006",
        name="Freshworks CRM/Freshsales Implementation",
        category="crm",
        description="Implement Freshworks CRM suite",
        small=CostEstimate(5_000, 15_000, "project", "Growth tier"),
        medium=CostEstimate(15_000, 50_000, "project", "Pro tier, integrations"),
        large=CostEstimate(50_000, 150_000, "project", "Enterprise tier"),
        enterprise=CostEstimate(150_000, 350_000, "project", "Multi-product, global"),
        typical_duration_weeks=(2, 10),
        keywords=["freshworks", "freshsales", "freshdesk", "crm"],
        sources=["Freshworks pricing"],
    ),

    "crm_zoho_implementation": ActivityCost(
        activity_id="CRM-007",
        name="Zoho CRM Implementation",
        category="crm",
        description="Implement Zoho CRM and related modules",
        small=CostEstimate(3_000, 12_000, "project", "Standard edition"),
        medium=CostEstimate(12_000, 40_000, "project", "Professional edition"),
        large=CostEstimate(40_000, 120_000, "project", "Enterprise with Zoho One"),
        enterprise=CostEstimate(120_000, 300_000, "project", "Full Zoho One suite"),
        typical_duration_weeks=(2, 12),
        keywords=["zoho", "crm"],
        sources=["Zoho pricing", "Implementation partners"],
    ),

    "crm_cpq_implementation": ActivityCost(
        activity_id="CRM-008",
        name="CPQ (Configure Price Quote) Implementation",
        category="crm",
        description="Implement CPQ solution (Salesforce CPQ, Conga, DealHub)",
        small=CostEstimate(30_000, 80_000, "project", "Basic product catalog"),
        medium=CostEstimate(80_000, 200_000, "project", "Complex pricing rules"),
        large=CostEstimate(200_000, 500_000, "project", "Multi-channel, approvals"),
        enterprise=CostEstimate(500_000, 1_200_000, "project", "Global, ERP integrated"),
        typical_duration_weeks=(8, 24),
        keywords=["cpq", "configure", "price", "quote", "salesforce"],
        sources=["Salesforce CPQ pricing", "Conga"],
    ),

    # =========================================================================
    # ADDITIONAL IDENTITY/IAM (6 activities)
    # =========================================================================

    "iam_ping_identity_implementation": ActivityCost(
        activity_id="IAM-005",
        name="Ping Identity Implementation",
        category="identity",
        description="Implement Ping Identity platform for SSO and federation",
        small=CostEstimate(20_000, 50_000, "project", "<500 users"),
        medium=CostEstimate(50_000, 150_000, "project", "500-2000 users"),
        large=CostEstimate(150_000, 400_000, "project", "2000-10000 users"),
        enterprise=CostEstimate(400_000, 1_000_000, "project", "10000+ users, complex federation"),
        typical_duration_weeks=(6, 20),
        keywords=["ping", "identity", "sso", "federation"],
        sources=["Ping Identity pricing"],
    ),

    "iam_sailpoint_implementation": ActivityCost(
        activity_id="IAM-006",
        name="SailPoint IGA Implementation",
        category="identity",
        description="Implement SailPoint Identity Governance and Administration",
        small=CostEstimate(100_000, 250_000, "project", "Core IGA, <1000 identities"),
        medium=CostEstimate(250_000, 600_000, "project", "Full IGA, 1000-5000 identities"),
        large=CostEstimate(600_000, 1_500_000, "project", "Enterprise IGA, access certification"),
        enterprise=CostEstimate(1_500_000, 4_000_000, "project", "Global IGA program"),
        typical_duration_weeks=(16, 52),
        keywords=["sailpoint", "iga", "identity", "governance", "access"],
        sources=["SailPoint partners"],
    ),

    "iam_mfa_rollout": ActivityCost(
        activity_id="IAM-007",
        name="MFA Rollout (Standalone)",
        category="identity",
        description="Deploy multi-factor authentication across organization",
        small=CostEstimate(10_000, 30_000, "project", "<500 users, basic MFA"),
        medium=CostEstimate(30_000, 80_000, "project", "500-2000 users, hardware tokens"),
        large=CostEstimate(80_000, 200_000, "project", "2000-10000 users, multiple methods"),
        enterprise=CostEstimate(200_000, 500_000, "project", "10000+ users, adaptive MFA"),
        typical_duration_weeks=(4, 12),
        keywords=["mfa", "multi-factor", "authentication", "2fa"],
        sources=["Duo, Microsoft, Okta pricing"],
    ),

    "iam_directory_federation": ActivityCost(
        activity_id="IAM-008",
        name="Directory Sync/Federation Setup",
        category="identity",
        description="Set up directory synchronization and SAML/OIDC federation",
        small=CostEstimate(8_000, 25_000, "project", "Single directory, few apps"),
        medium=CostEstimate(25_000, 75_000, "project", "Multiple directories, 10-20 apps"),
        large=CostEstimate(75_000, 200_000, "project", "Complex hybrid, 50+ apps"),
        enterprise=CostEstimate(200_000, 500_000, "project", "Multi-forest, global federation"),
        typical_duration_weeks=(2, 12),
        keywords=["directory", "sync", "federation", "saml", "oidc", "ldap"],
        sources=["Identity consultants"],
    ),

    "iam_ztna_implementation": ActivityCost(
        activity_id="IAM-009",
        name="Zero Trust Network Access (ZTNA)",
        category="identity",
        description="Implement ZTNA solution (Zscaler, Cloudflare Access, etc.)",
        small=CostEstimate(25_000, 75_000, "project", "<500 users"),
        medium=CostEstimate(75_000, 200_000, "project", "500-2000 users"),
        large=CostEstimate(200_000, 500_000, "project", "2000-10000 users"),
        enterprise=CostEstimate(500_000, 1_500_000, "project", "Global deployment"),
        typical_duration_weeks=(6, 20),
        keywords=["ztna", "zero trust", "zscaler", "cloudflare", "network access"],
        sources=["Zscaler pricing", "Cloudflare"],
    ),

    "iam_onelogin_implementation": ActivityCost(
        activity_id="IAM-010",
        name="OneLogin Implementation",
        category="identity",
        description="Implement OneLogin SSO and identity management",
        small=CostEstimate(12_000, 35_000, "project", "<200 users"),
        medium=CostEstimate(35_000, 90_000, "project", "200-1000 users"),
        large=CostEstimate(90_000, 220_000, "project", "1000-5000 users"),
        enterprise=CostEstimate(220_000, 550_000, "project", "5000+ users"),
        typical_duration_weeks=(3, 14),
        keywords=["onelogin", "sso", "identity"],
        sources=["OneLogin pricing"],
    ),

    # =========================================================================
    # ADDITIONAL CLOUD (8 activities)
    # =========================================================================

    "cloud_gcp_migration": ActivityCost(
        activity_id="CLOUD-005",
        name="Google Cloud Platform Migration",
        category="cloud",
        description="Migrate workloads to Google Cloud Platform",
        small=CostEstimate(40_000, 100_000, "project", "<20 VMs"),
        medium=CostEstimate(100_000, 300_000, "project", "20-100 VMs"),
        large=CostEstimate(300_000, 800_000, "project", "100-500 VMs"),
        enterprise=CostEstimate(800_000, 3_000_000, "project", "500+ VMs, Anthos"),
        typical_duration_weeks=(8, 52),
        keywords=["gcp", "google cloud", "migration"],
        sources=["Google Cloud partners"],
    ),

    "cloud_multi_cloud_strategy": ActivityCost(
        activity_id="CLOUD-006",
        name="Multi-Cloud Strategy Implementation",
        category="cloud",
        description="Design and implement multi-cloud architecture",
        small=CostEstimate(50_000, 150_000, "project", "2 clouds, basic workloads"),
        medium=CostEstimate(150_000, 400_000, "project", "2-3 clouds, governance"),
        large=CostEstimate(400_000, 1_000_000, "project", "Full multi-cloud platform"),
        enterprise=CostEstimate(1_000_000, 3_000_000, "project", "Enterprise multi-cloud"),
        typical_duration_weeks=(12, 40),
        keywords=["multi-cloud", "hybrid", "cloud strategy"],
        sources=["Cloud consultants"],
    ),

    "cloud_kubernetes_platform": ActivityCost(
        activity_id="CLOUD-007",
        name="Kubernetes/Container Platform",
        category="cloud",
        description="Implement Kubernetes platform (EKS, AKS, GKE, OpenShift)",
        small=CostEstimate(30_000, 80_000, "project", "Dev/test, <10 apps"),
        medium=CostEstimate(80_000, 250_000, "project", "Production, 10-50 apps"),
        large=CostEstimate(250_000, 700_000, "project", "Multi-cluster, service mesh"),
        enterprise=CostEstimate(700_000, 2_000_000, "project", "Global platform, GitOps"),
        typical_duration_weeks=(8, 30),
        keywords=["kubernetes", "k8s", "container", "docker", "openshift", "eks", "aks", "gke"],
        sources=["Container platform vendors"],
    ),

    "cloud_vdi_migration": ActivityCost(
        activity_id="CLOUD-008",
        name="VDI Migration (Citrix/VMware Horizon)",
        category="cloud",
        description="Migrate virtual desktop infrastructure to cloud",
        small=CostEstimate(40_000, 100_000, "project", "<100 desktops"),
        medium=CostEstimate(100_000, 300_000, "project", "100-500 desktops"),
        large=CostEstimate(300_000, 800_000, "project", "500-2000 desktops"),
        enterprise=CostEstimate(800_000, 2_500_000, "project", "2000+ desktops, global"),
        typical_duration_weeks=(8, 30),
        keywords=["vdi", "citrix", "vmware horizon", "desktop", "avd", "azure virtual desktop"],
        sources=["VDI vendors", "Microsoft AVD"],
    ),

    "cloud_finops_program": ActivityCost(
        activity_id="CLOUD-009",
        name="Cloud FinOps/Cost Optimization",
        category="cloud",
        description="Implement FinOps program for cloud cost management",
        small=CostEstimate(15_000, 40_000, "project", "<$100K/mo cloud spend"),
        medium=CostEstimate(40_000, 120_000, "project", "$100K-500K/mo spend"),
        large=CostEstimate(120_000, 300_000, "project", "$500K-2M/mo spend"),
        enterprise=CostEstimate(300_000, 800_000, "project", "$2M+/mo spend"),
        typical_duration_weeks=(4, 16),
        keywords=["finops", "cloud cost", "optimization", "reserved instances"],
        sources=["FinOps Foundation", "Cloud consultants"],
    ),

    "cloud_saas_consolidation": ActivityCost(
        activity_id="CLOUD-010",
        name="SaaS Consolidation/Rationalization",
        category="cloud",
        description="Consolidate and rationalize SaaS application portfolio",
        small=CostEstimate(20_000, 60_000, "project", "<50 SaaS apps"),
        medium=CostEstimate(60_000, 150_000, "project", "50-200 SaaS apps"),
        large=CostEstimate(150_000, 400_000, "project", "200-500 SaaS apps"),
        enterprise=CostEstimate(400_000, 1_000_000, "project", "500+ SaaS apps"),
        typical_duration_weeks=(6, 20),
        keywords=["saas", "consolidation", "rationalization", "shadow it"],
        sources=["SaaS management platforms", "Zylo, Productiv"],
    ),

    "cloud_serverless_migration": ActivityCost(
        activity_id="CLOUD-011",
        name="Serverless/Function Migration",
        category="cloud",
        description="Migrate applications to serverless architecture",
        small=CostEstimate(20_000, 60_000, "project", "1-5 applications"),
        medium=CostEstimate(60_000, 180_000, "project", "5-20 applications"),
        large=CostEstimate(180_000, 500_000, "project", "20-50 applications"),
        enterprise=CostEstimate(500_000, 1_500_000, "project", "Enterprise serverless platform"),
        typical_duration_weeks=(6, 26),
        keywords=["serverless", "lambda", "azure functions", "cloud functions"],
        sources=["Cloud vendors"],
    ),

    "cloud_governance_implementation": ActivityCost(
        activity_id="CLOUD-012",
        name="Cloud Governance Framework",
        category="cloud",
        description="Implement cloud governance, policies, and guardrails",
        small=CostEstimate(25_000, 70_000, "project", "Single cloud, basic policies"),
        medium=CostEstimate(70_000, 200_000, "project", "Multi-cloud, landing zones"),
        large=CostEstimate(200_000, 500_000, "project", "Enterprise framework"),
        enterprise=CostEstimate(500_000, 1_200_000, "project", "Global governance program"),
        typical_duration_weeks=(6, 24),
        keywords=["cloud governance", "policy", "landing zone", "guardrails"],
        sources=["Cloud consultants", "Azure CAF, AWS Well-Architected"],
    ),

    # =========================================================================
    # ADDITIONAL INFRASTRUCTURE (8 activities)
    # =========================================================================

    "infra_sdwan_implementation": ActivityCost(
        activity_id="INFRA-004",
        name="SD-WAN Implementation",
        category="infrastructure",
        description="Implement Software-Defined WAN solution",
        small=CostEstimate(30_000, 80_000, "project", "5-10 sites"),
        medium=CostEstimate(80_000, 250_000, "project", "10-50 sites"),
        large=CostEstimate(250_000, 700_000, "project", "50-200 sites"),
        enterprise=CostEstimate(700_000, 2_000_000, "project", "200+ sites, global"),
        typical_duration_weeks=(8, 30),
        keywords=["sd-wan", "wan", "network", "cisco", "vmware velocloud", "silver peak"],
        sources=["SD-WAN vendors", "Gartner"],
    ),

    "infra_voip_implementation": ActivityCost(
        activity_id="INFRA-005",
        name="VoIP/Unified Communications",
        category="infrastructure",
        description="Implement VoIP and unified communications platform",
        small=CostEstimate(15_000, 50_000, "project", "<100 users"),
        medium=CostEstimate(50_000, 150_000, "project", "100-500 users"),
        large=CostEstimate(150_000, 400_000, "project", "500-2000 users"),
        enterprise=CostEstimate(400_000, 1_200_000, "project", "2000+ users, contact center"),
        typical_duration_weeks=(4, 20),
        keywords=["voip", "unified communications", "teams", "zoom", "ringcentral", "cisco webex"],
        sources=["UCaaS vendors"],
    ),

    "infra_wireless_refresh": ActivityCost(
        activity_id="INFRA-006",
        name="Wireless Network Refresh",
        category="infrastructure",
        description="Upgrade wireless infrastructure (WiFi 6/6E)",
        small=CostEstimate(10_000, 35_000, "project", "Single site, <50 APs"),
        medium=CostEstimate(35_000, 100_000, "project", "2-5 sites, 50-200 APs"),
        large=CostEstimate(100_000, 300_000, "project", "5-20 sites, 200-500 APs"),
        enterprise=CostEstimate(300_000, 1_000_000, "project", "20+ sites, 500+ APs"),
        typical_duration_weeks=(4, 16),
        keywords=["wireless", "wifi", "wifi6", "access point", "aruba", "cisco meraki"],
        sources=["Wireless vendors"],
    ),

    "infra_storage_refresh": ActivityCost(
        activity_id="INFRA-007",
        name="Storage Infrastructure Refresh",
        category="infrastructure",
        description="Upgrade SAN/NAS storage infrastructure",
        small=CostEstimate(30_000, 100_000, "project", "<100TB"),
        medium=CostEstimate(100_000, 350_000, "project", "100TB-1PB"),
        large=CostEstimate(350_000, 1_000_000, "project", "1-5PB"),
        enterprise=CostEstimate(1_000_000, 4_000_000, "project", "5PB+, multi-site replication"),
        typical_duration_weeks=(8, 24),
        keywords=["storage", "san", "nas", "netapp", "dell emc", "pure storage"],
        sources=["Storage vendors"],
    ),

    "infra_print_consolidation": ActivityCost(
        activity_id="INFRA-008",
        name="Print Infrastructure Consolidation",
        category="infrastructure",
        description="Consolidate and modernize print infrastructure",
        small=CostEstimate(10_000, 30_000, "project", "<50 devices"),
        medium=CostEstimate(30_000, 80_000, "project", "50-200 devices"),
        large=CostEstimate(80_000, 200_000, "project", "200-500 devices"),
        enterprise=CostEstimate(200_000, 500_000, "project", "500+ devices, managed print"),
        typical_duration_weeks=(4, 16),
        keywords=["print", "printer", "mfp", "managed print"],
        sources=["Print vendors", "MPS providers"],
    ),

    "infra_physical_security": ActivityCost(
        activity_id="INFRA-009",
        name="Physical Security Systems Integration",
        category="infrastructure",
        description="Integrate/upgrade physical security (access control, cameras)",
        small=CostEstimate(20_000, 60_000, "project", "Single site, basic system"),
        medium=CostEstimate(60_000, 180_000, "project", "2-5 sites"),
        large=CostEstimate(180_000, 500_000, "project", "5-20 sites"),
        enterprise=CostEstimate(500_000, 1_500_000, "project", "20+ sites, SOC integration"),
        typical_duration_weeks=(6, 20),
        keywords=["physical security", "access control", "cameras", "cctv", "badge"],
        sources=["Security integrators"],
    ),

    "infra_cabling_infrastructure": ActivityCost(
        activity_id="INFRA-010",
        name="Structured Cabling/Infrastructure",
        category="infrastructure",
        description="Install or upgrade structured cabling infrastructure",
        small=CostEstimate(15_000, 50_000, "project", "Single floor, <100 drops"),
        medium=CostEstimate(50_000, 150_000, "project", "Single building, 100-500 drops"),
        large=CostEstimate(150_000, 400_000, "project", "Campus, 500-2000 drops"),
        enterprise=CostEstimate(400_000, 1_200_000, "project", "Multi-campus, data center"),
        typical_duration_weeks=(4, 16),
        keywords=["cabling", "structured cabling", "cat6", "fiber"],
        sources=["Cabling contractors"],
    ),

    "infra_building_automation": ActivityCost(
        activity_id="INFRA-011",
        name="Building Automation/IoT Integration",
        category="infrastructure",
        description="Integrate building automation and IoT systems",
        small=CostEstimate(25_000, 75_000, "project", "Single building, basic BMS"),
        medium=CostEstimate(75_000, 200_000, "project", "2-5 buildings"),
        large=CostEstimate(200_000, 500_000, "project", "Campus, smart building"),
        enterprise=CostEstimate(500_000, 1_500_000, "project", "Portfolio-wide IoT platform"),
        typical_duration_weeks=(8, 26),
        keywords=["building automation", "bms", "iot", "smart building", "hvac"],
        sources=["BMS vendors"],
    ),

    # =========================================================================
    # ADDITIONAL CYBERSECURITY (10 activities)
    # =========================================================================

    "security_zero_trust_architecture": ActivityCost(
        activity_id="SEC-006",
        name="Zero Trust Architecture Implementation",
        category="cybersecurity",
        description="Design and implement zero trust security architecture",
        small=CostEstimate(50_000, 150_000, "project", "Core components"),
        medium=CostEstimate(150_000, 400_000, "project", "Full ZTA framework"),
        large=CostEstimate(400_000, 1_000_000, "project", "Enterprise-wide ZTA"),
        enterprise=CostEstimate(1_000_000, 3_000_000, "project", "Global ZTA transformation"),
        typical_duration_weeks=(16, 52),
        keywords=["zero trust", "zta", "security architecture"],
        sources=["NIST ZTA, Forrester"],
    ),

    "security_dlp_implementation": ActivityCost(
        activity_id="SEC-007",
        name="DLP Implementation",
        category="cybersecurity",
        description="Implement Data Loss Prevention solution",
        small=CostEstimate(30_000, 80_000, "project", "Email DLP only"),
        medium=CostEstimate(80_000, 200_000, "project", "Email + endpoint DLP"),
        large=CostEstimate(200_000, 500_000, "project", "Full DLP suite"),
        enterprise=CostEstimate(500_000, 1_500_000, "project", "Enterprise DLP program"),
        typical_duration_weeks=(8, 26),
        keywords=["dlp", "data loss prevention", "symantec", "microsoft purview"],
        sources=["DLP vendors"],
    ),

    "security_email_gateway": ActivityCost(
        activity_id="SEC-008",
        name="Email Security Gateway",
        category="cybersecurity",
        description="Implement email security gateway (Proofpoint, Mimecast)",
        small=CostEstimate(10_000, 30_000, "project", "<500 mailboxes"),
        medium=CostEstimate(30_000, 80_000, "project", "500-2000 mailboxes"),
        large=CostEstimate(80_000, 200_000, "project", "2000-10000 mailboxes"),
        enterprise=CostEstimate(200_000, 500_000, "project", "10000+ mailboxes"),
        typical_duration_weeks=(2, 8),
        keywords=["email security", "proofpoint", "mimecast", "email gateway"],
        sources=["Email security vendors"],
    ),

    "security_web_proxy": ActivityCost(
        activity_id="SEC-009",
        name="Secure Web Gateway",
        category="cybersecurity",
        description="Implement secure web gateway/proxy (Zscaler, Netskope)",
        small=CostEstimate(20_000, 60_000, "project", "<500 users"),
        medium=CostEstimate(60_000, 180_000, "project", "500-2000 users"),
        large=CostEstimate(180_000, 450_000, "project", "2000-10000 users"),
        enterprise=CostEstimate(450_000, 1_200_000, "project", "10000+ users"),
        typical_duration_weeks=(4, 16),
        keywords=["swg", "web proxy", "zscaler", "netskope", "web gateway"],
        sources=["SWG vendors"],
    ),

    "security_awareness_training": ActivityCost(
        activity_id="SEC-010",
        name="Security Awareness Training Program",
        category="cybersecurity",
        description="Implement security awareness training and phishing simulation",
        small=CostEstimate(5_000, 15_000, "project", "<500 users"),
        medium=CostEstimate(15_000, 40_000, "project", "500-2000 users"),
        large=CostEstimate(40_000, 100_000, "project", "2000-10000 users"),
        enterprise=CostEstimate(100_000, 300_000, "project", "10000+ users, custom content"),
        typical_duration_weeks=(2, 8),
        keywords=["security awareness", "training", "phishing", "knowbe4", "proofpoint"],
        sources=["KnowBe4, Proofpoint pricing"],
        notes="Plus $15-50/user/year ongoing",
    ),

    "security_incident_response": ActivityCost(
        activity_id="SEC-011",
        name="Incident Response Planning",
        category="cybersecurity",
        description="Develop incident response plan and playbooks",
        small=CostEstimate(15_000, 40_000, "project", "Basic IR plan"),
        medium=CostEstimate(40_000, 100_000, "project", "Detailed playbooks, tabletop"),
        large=CostEstimate(100_000, 250_000, "project", "Full IR program"),
        enterprise=CostEstimate(250_000, 600_000, "project", "Global IR capability"),
        typical_duration_weeks=(4, 16),
        keywords=["incident response", "ir", "playbook", "tabletop"],
        sources=["IR consultants"],
    ),

    "security_threat_intel": ActivityCost(
        activity_id="SEC-012",
        name="Threat Intelligence Platform",
        category="cybersecurity",
        description="Implement threat intelligence platform and feeds",
        small=CostEstimate(20_000, 60_000, "project", "Basic TIP, standard feeds"),
        medium=CostEstimate(60_000, 180_000, "project", "Full TIP, multiple feeds"),
        large=CostEstimate(180_000, 450_000, "project", "Advanced TIP, custom intel"),
        enterprise=CostEstimate(450_000, 1_200_000, "project", "Enterprise intel program"),
        typical_duration_weeks=(6, 20),
        keywords=["threat intelligence", "tip", "threat", "intel"],
        sources=["TIP vendors"],
    ),

    "security_soc_setup": ActivityCost(
        activity_id="SEC-013",
        name="Security Operations Center Setup",
        category="cybersecurity",
        description="Establish internal SOC capability",
        small=CostEstimate(100_000, 300_000, "project", "Basic SOC, 8x5"),
        medium=CostEstimate(300_000, 800_000, "project", "Standard SOC, extended hours"),
        large=CostEstimate(800_000, 2_000_000, "project", "Full SOC, 24x7"),
        enterprise=CostEstimate(2_000_000, 6_000_000, "project", "Global SOC, follow-the-sun"),
        typical_duration_weeks=(16, 52),
        keywords=["soc", "security operations", "security operations center"],
        sources=["SOC consultants"],
        notes="Excludes ongoing staffing costs",
    ),

    "security_cspm_implementation": ActivityCost(
        activity_id="SEC-014",
        name="Cloud Security Posture Management (CSPM)",
        category="cybersecurity",
        description="Implement CSPM solution (Wiz, Prisma Cloud, etc.)",
        small=CostEstimate(25_000, 70_000, "project", "Single cloud, <1000 assets"),
        medium=CostEstimate(70_000, 200_000, "project", "Multi-cloud, 1000-5000 assets"),
        large=CostEstimate(200_000, 500_000, "project", "Enterprise, 5000-20000 assets"),
        enterprise=CostEstimate(500_000, 1_500_000, "project", "Global CSPM program"),
        typical_duration_weeks=(4, 16),
        keywords=["cspm", "cloud security", "wiz", "prisma cloud", "orca"],
        sources=["CSPM vendors"],
    ),

    "security_appsec_program": ActivityCost(
        activity_id="SEC-015",
        name="Application Security Testing Program",
        category="cybersecurity",
        description="Implement SAST/DAST/SCA tools and DevSecOps",
        small=CostEstimate(30_000, 80_000, "project", "Basic SAST/SCA"),
        medium=CostEstimate(80_000, 220_000, "project", "Full toolchain, CI/CD integration"),
        large=CostEstimate(220_000, 550_000, "project", "Enterprise AppSec program"),
        enterprise=CostEstimate(550_000, 1_500_000, "project", "Global DevSecOps"),
        typical_duration_weeks=(8, 26),
        keywords=["appsec", "sast", "dast", "sca", "devsecops", "snyk", "veracode", "checkmarx"],
        sources=["AppSec vendors"],
    ),

    # =========================================================================
    # ADDITIONAL DISASTER RECOVERY (3 activities)
    # =========================================================================

    "dr_cloud_backup": ActivityCost(
        activity_id="DR-003",
        name="Cloud Backup Implementation",
        category="disaster_recovery",
        description="Implement cloud-based backup solution",
        small=CostEstimate(10_000, 30_000, "project", "<10TB data"),
        medium=CostEstimate(30_000, 80_000, "project", "10-100TB data"),
        large=CostEstimate(80_000, 200_000, "project", "100TB-1PB data"),
        enterprise=CostEstimate(200_000, 600_000, "project", "1PB+ data, multi-region"),
        typical_duration_weeks=(2, 12),
        keywords=["cloud backup", "backup", "druva", "rubrik", "cohesity"],
        sources=["Cloud backup vendors"],
    ),

    "dr_site_setup": ActivityCost(
        activity_id="DR-004",
        name="DR Site Setup",
        category="disaster_recovery",
        description="Establish disaster recovery site (colo or cloud)",
        small=CostEstimate(50_000, 150_000, "project", "Cold site, basic systems"),
        medium=CostEstimate(150_000, 400_000, "project", "Warm site, key applications"),
        large=CostEstimate(400_000, 1_000_000, "project", "Hot site, near-real-time"),
        enterprise=CostEstimate(1_000_000, 3_500_000, "project", "Active-active, global"),
        typical_duration_weeks=(12, 40),
        keywords=["dr site", "disaster recovery", "colo", "colocation"],
        sources=["DR providers"],
    ),

    "dr_bcp_development": ActivityCost(
        activity_id="DR-005",
        name="Business Continuity Planning",
        category="disaster_recovery",
        description="Develop comprehensive business continuity program",
        small=CostEstimate(20_000, 60_000, "project", "Basic BCP"),
        medium=CostEstimate(60_000, 150_000, "project", "Full BCP with BIA"),
        large=CostEstimate(150_000, 350_000, "project", "Enterprise BCP program"),
        enterprise=CostEstimate(350_000, 900_000, "project", "Global BCP/BCM"),
        typical_duration_weeks=(6, 20),
        keywords=["bcp", "business continuity", "bia", "bcm"],
        sources=["BCP consultants"],
    ),

    # =========================================================================
    # ADDITIONAL ITSM (3 activities)
    # =========================================================================

    "itsm_bmc_implementation": ActivityCost(
        activity_id="ITSM-003",
        name="BMC Helix/Remedy Implementation",
        category="itsm",
        description="Implement BMC Helix ITSM platform",
        small=CostEstimate(80_000, 200_000, "project", "Core ITSM"),
        medium=CostEstimate(200_000, 500_000, "project", "ITSM + ITOM"),
        large=CostEstimate(500_000, 1_200_000, "project", "Full platform"),
        enterprise=CostEstimate(1_200_000, 4_000_000, "project", "Global deployment"),
        typical_duration_weeks=(12, 52),
        keywords=["bmc", "helix", "remedy", "itsm"],
        sources=["BMC partners"],
    ),

    "itsm_freshservice_implementation": ActivityCost(
        activity_id="ITSM-004",
        name="Freshservice Implementation",
        category="itsm",
        description="Implement Freshworks Freshservice ITSM",
        small=CostEstimate(8_000, 25_000, "project", "Starter tier"),
        medium=CostEstimate(25_000, 70_000, "project", "Growth tier"),
        large=CostEstimate(70_000, 180_000, "project", "Pro/Enterprise tier"),
        enterprise=CostEstimate(180_000, 450_000, "project", "Enterprise, multi-workspace"),
        typical_duration_weeks=(3, 14),
        keywords=["freshservice", "itsm", "freshworks"],
        sources=["Freshworks partners"],
    ),

    "itsm_cmdb_implementation": ActivityCost(
        activity_id="ITSM-005",
        name="CMDB Implementation",
        category="itsm",
        description="Implement Configuration Management Database",
        small=CostEstimate(25_000, 70_000, "project", "<1000 CIs"),
        medium=CostEstimate(70_000, 180_000, "project", "1000-10000 CIs"),
        large=CostEstimate(180_000, 450_000, "project", "10000-50000 CIs"),
        enterprise=CostEstimate(450_000, 1_200_000, "project", "50000+ CIs, federation"),
        typical_duration_weeks=(8, 26),
        keywords=["cmdb", "configuration management", "asset management"],
        sources=["ITSM vendors"],
    ),

    # =========================================================================
    # ADDITIONAL HCM (4 activities)
    # =========================================================================

    "hcm_successfactors_implementation": ActivityCost(
        activity_id="HCM-003",
        name="SAP SuccessFactors Implementation",
        category="hcm",
        description="Implement SAP SuccessFactors HCM suite",
        small=CostEstimate(150_000, 400_000, "project", "Core HR, <1000 employees"),
        medium=CostEstimate(400_000, 1_000_000, "project", "Full HCM, 1000-5000 employees"),
        large=CostEstimate(1_000_000, 2_500_000, "project", "Global, 5000-15000 employees"),
        enterprise=CostEstimate(2_500_000, 7_000_000, "project", "15000+ employees"),
        typical_duration_weeks=(20, 65),
        keywords=["successfactors", "sap", "hcm", "hr"],
        sources=["SAP partners"],
    ),

    "hcm_ukg_implementation": ActivityCost(
        activity_id="HCM-004",
        name="UKG (Ultimate Kronos) Implementation",
        category="hcm",
        description="Implement UKG Pro/Ready HCM solution",
        small=CostEstimate(40_000, 120_000, "project", "<500 employees"),
        medium=CostEstimate(120_000, 350_000, "project", "500-2000 employees"),
        large=CostEstimate(350_000, 900_000, "project", "2000-10000 employees"),
        enterprise=CostEstimate(900_000, 2_500_000, "project", "10000+ employees"),
        typical_duration_weeks=(12, 40),
        keywords=["ukg", "ultimate", "kronos", "hcm", "workforce"],
        sources=["UKG partners"],
    ),

    "hcm_bamboohr_implementation": ActivityCost(
        activity_id="HCM-005",
        name="BambooHR Implementation",
        category="hcm",
        description="Implement BambooHR for SMB HR management",
        small=CostEstimate(5_000, 15_000, "project", "<100 employees"),
        medium=CostEstimate(15_000, 40_000, "project", "100-500 employees"),
        large=CostEstimate(40_000, 100_000, "project", "500-1000 employees"),
        enterprise=CostEstimate(100_000, 250_000, "project", "1000+ employees, complex"),
        typical_duration_weeks=(2, 10),
        keywords=["bamboohr", "hr", "hris"],
        sources=["BambooHR"],
    ),

    "hcm_payroll_migration": ActivityCost(
        activity_id="HCM-006",
        name="Payroll System Migration",
        category="hcm",
        description="Migrate payroll from one system to another",
        small=CostEstimate(20_000, 60_000, "project", "<500 employees, single country"),
        medium=CostEstimate(60_000, 180_000, "project", "500-2000 employees"),
        large=CostEstimate(180_000, 450_000, "project", "2000-10000 employees, multi-state"),
        enterprise=CostEstimate(450_000, 1_200_000, "project", "10000+ employees, global"),
        typical_duration_weeks=(8, 26),
        keywords=["payroll", "migration"],
        sources=["Payroll consultants"],
    ),

    # =========================================================================
    # ADDITIONAL APPLICATIONS (6 activities)
    # =========================================================================

    "app_modernization": ActivityCost(
        activity_id="APP-003",
        name="Custom Application Modernization",
        category="applications",
        description="Modernize legacy custom application",
        small=CostEstimate(50_000, 150_000, "project", "Simple app, containerization"),
        medium=CostEstimate(150_000, 400_000, "project", "Medium complexity, re-platform"),
        large=CostEstimate(400_000, 1_000_000, "project", "Complex app, refactor"),
        enterprise=CostEstimate(1_000_000, 3_500_000, "project", "Mission-critical rebuild"),
        typical_duration_weeks=(12, 52),
        keywords=["modernization", "legacy", "refactor", "replatform"],
        sources=["App modernization consultants"],
    ),

    "app_mobile_development": ActivityCost(
        activity_id="APP-004",
        name="Mobile Application Development",
        category="applications",
        description="Develop or migrate mobile application",
        small=CostEstimate(30_000, 80_000, "project", "Simple app, single platform"),
        medium=CostEstimate(80_000, 250_000, "project", "Medium complexity, cross-platform"),
        large=CostEstimate(250_000, 600_000, "project", "Complex app, integrations"),
        enterprise=CostEstimate(600_000, 1_800_000, "project", "Enterprise mobile platform"),
        typical_duration_weeks=(8, 30),
        keywords=["mobile", "ios", "android", "react native", "flutter"],
        sources=["Mobile dev agencies"],
    ),

    "app_bi_platform": ActivityCost(
        activity_id="APP-005",
        name="BI Platform Implementation (Tableau/PowerBI)",
        category="applications",
        description="Implement business intelligence platform",
        small=CostEstimate(25_000, 70_000, "project", "<50 users, standard reports"),
        medium=CostEstimate(70_000, 200_000, "project", "50-200 users, custom dashboards"),
        large=CostEstimate(200_000, 500_000, "project", "200-1000 users, advanced analytics"),
        enterprise=CostEstimate(500_000, 1_500_000, "project", "1000+ users, embedded BI"),
        typical_duration_weeks=(6, 24),
        keywords=["bi", "tableau", "power bi", "analytics", "reporting"],
        sources=["BI vendors"],
    ),

    "app_sharepoint_implementation": ActivityCost(
        activity_id="APP-006",
        name="SharePoint/Document Management",
        category="applications",
        description="Implement SharePoint or document management system",
        small=CostEstimate(15_000, 50_000, "project", "Basic team sites"),
        medium=CostEstimate(50_000, 150_000, "project", "Intranet, custom workflows"),
        large=CostEstimate(150_000, 400_000, "project", "Enterprise content management"),
        enterprise=CostEstimate(400_000, 1_000_000, "project", "Global DMS, compliance"),
        typical_duration_weeks=(6, 24),
        keywords=["sharepoint", "document management", "dms", "content management"],
        sources=["SharePoint partners"],
    ),

    "app_clm_implementation": ActivityCost(
        activity_id="APP-007",
        name="Contract Lifecycle Management",
        category="applications",
        description="Implement CLM solution (DocuSign CLM, Ironclad)",
        small=CostEstimate(30_000, 80_000, "project", "Basic CLM"),
        medium=CostEstimate(80_000, 200_000, "project", "Full CLM, integrations"),
        large=CostEstimate(200_000, 500_000, "project", "Enterprise CLM"),
        enterprise=CostEstimate(500_000, 1_300_000, "project", "Global CLM program"),
        typical_duration_weeks=(8, 24),
        keywords=["clm", "contract management", "docusign", "ironclad"],
        sources=["CLM vendors"],
    ),

    "app_ecommerce_platform": ActivityCost(
        activity_id="APP-008",
        name="E-Commerce Platform Implementation",
        category="applications",
        description="Implement e-commerce platform (Shopify, Magento, Salesforce Commerce)",
        small=CostEstimate(20_000, 60_000, "project", "Basic Shopify store"),
        medium=CostEstimate(60_000, 200_000, "project", "Custom theme, integrations"),
        large=CostEstimate(200_000, 600_000, "project", "Enterprise platform"),
        enterprise=CostEstimate(600_000, 2_000_000, "project", "Headless commerce, global"),
        typical_duration_weeks=(8, 30),
        keywords=["ecommerce", "shopify", "magento", "salesforce commerce"],
        sources=["E-commerce agencies"],
    ),

    # =========================================================================
    # ADDITIONAL M&A ACTIVITIES (5 activities)
    # =========================================================================

    "ma_carveout_separation": ActivityCost(
        activity_id="MA-006",
        name="Carve-Out IT Separation",
        category="ma_integration",
        description="Separate IT systems for divestiture/carve-out",
        small=CostEstimate(150_000, 400_000, "project", "Simple carve-out"),
        medium=CostEstimate(400_000, 1_000_000, "project", "Moderate entanglement"),
        large=CostEstimate(1_000_000, 3_000_000, "project", "Significant entanglement"),
        enterprise=CostEstimate(3_000_000, 10_000_000, "project", "Highly complex carve-out"),
        typical_duration_weeks=(16, 78),
        keywords=["carve-out", "separation", "divestiture"],
        sources=["M&A consultants"],
    ),

    "ma_operating_model": ActivityCost(
        activity_id="MA-007",
        name="IT Operating Model Harmonization",
        category="ma_integration",
        description="Harmonize IT operating models post-merger",
        small=CostEstimate(40_000, 120_000, "project", "Similar models"),
        medium=CostEstimate(120_000, 350_000, "project", "Moderate differences"),
        large=CostEstimate(350_000, 800_000, "project", "Significant differences"),
        enterprise=CostEstimate(800_000, 2_000_000, "project", "Full transformation"),
        typical_duration_weeks=(8, 30),
        keywords=["operating model", "governance", "organizational design"],
        sources=["IT consultants"],
    ),

    "ma_vendor_rationalization": ActivityCost(
        activity_id="MA-008",
        name="Vendor Contract Rationalization",
        category="ma_integration",
        description="Rationalize and consolidate vendor contracts post-merger",
        small=CostEstimate(25_000, 75_000, "project", "<50 vendors"),
        medium=CostEstimate(75_000, 200_000, "project", "50-200 vendors"),
        large=CostEstimate(200_000, 500_000, "project", "200-500 vendors"),
        enterprise=CostEstimate(500_000, 1_200_000, "project", "500+ vendors"),
        typical_duration_weeks=(8, 26),
        keywords=["vendor", "contract", "rationalization", "procurement"],
        sources=["Procurement consultants"],
    ),

    "ma_license_trueup": ActivityCost(
        activity_id="MA-009",
        name="License True-Up and Optimization",
        category="ma_integration",
        description="Software license true-up and optimization post-merger",
        small=CostEstimate(20_000, 60_000, "project", "Limited software"),
        medium=CostEstimate(60_000, 180_000, "project", "Standard enterprise"),
        large=CostEstimate(180_000, 450_000, "project", "Complex licensing"),
        enterprise=CostEstimate(450_000, 1_000_000, "project", "Global license mgmt"),
        typical_duration_weeks=(6, 20),
        keywords=["license", "true-up", "software asset management", "sam"],
        sources=["SAM consultants"],
    ),

    "ma_it_governance": ActivityCost(
        activity_id="MA-010",
        name="Post-Merger IT Governance",
        category="ma_integration",
        description="Establish IT governance for merged organization",
        small=CostEstimate(30_000, 90_000, "project", "Basic governance"),
        medium=CostEstimate(90_000, 250_000, "project", "Standard governance"),
        large=CostEstimate(250_000, 600_000, "project", "Enterprise governance"),
        enterprise=CostEstimate(600_000, 1_500_000, "project", "Global governance framework"),
        typical_duration_weeks=(6, 24),
        keywords=["governance", "pmo", "steering committee"],
        sources=["IT governance consultants"],
    ),

    # =========================================================================
    # DATA & ANALYTICS (5 activities)
    # =========================================================================

    "data_warehouse_implementation": ActivityCost(
        activity_id="DATA-001",
        name="Data Warehouse Implementation",
        category="data_analytics",
        description="Implement cloud data warehouse (Snowflake, BigQuery, Redshift)",
        small=CostEstimate(40_000, 120_000, "project", "Basic warehouse, <1TB"),
        medium=CostEstimate(120_000, 350_000, "project", "Standard, 1-10TB"),
        large=CostEstimate(350_000, 900_000, "project", "Enterprise, 10-100TB"),
        enterprise=CostEstimate(900_000, 3_000_000, "project", "Massive scale, 100TB+"),
        typical_duration_weeks=(8, 30),
        keywords=["data warehouse", "snowflake", "bigquery", "redshift", "databricks"],
        sources=["Data platform vendors"],
    ),

    "data_etl_pipeline": ActivityCost(
        activity_id="DATA-002",
        name="ETL/Data Pipeline Implementation",
        category="data_analytics",
        description="Implement data integration and ETL pipelines",
        small=CostEstimate(25_000, 75_000, "project", "5-10 sources"),
        medium=CostEstimate(75_000, 220_000, "project", "10-30 sources"),
        large=CostEstimate(220_000, 550_000, "project", "30-100 sources"),
        enterprise=CostEstimate(550_000, 1_500_000, "project", "100+ sources, real-time"),
        typical_duration_weeks=(6, 24),
        keywords=["etl", "data pipeline", "fivetran", "airbyte", "informatica"],
        sources=["Data integration vendors"],
    ),

    "data_mdm_implementation": ActivityCost(
        activity_id="DATA-003",
        name="Master Data Management",
        category="data_analytics",
        description="Implement MDM solution for data quality and governance",
        small=CostEstimate(75_000, 200_000, "project", "Single domain"),
        medium=CostEstimate(200_000, 500_000, "project", "Multi-domain"),
        large=CostEstimate(500_000, 1_200_000, "project", "Enterprise MDM"),
        enterprise=CostEstimate(1_200_000, 3_500_000, "project", "Global MDM program"),
        typical_duration_weeks=(16, 52),
        keywords=["mdm", "master data", "data quality", "informatica", "reltio"],
        sources=["MDM vendors"],
    ),

    "data_governance_program": ActivityCost(
        activity_id="DATA-004",
        name="Data Governance Program",
        category="data_analytics",
        description="Establish enterprise data governance program",
        small=CostEstimate(30_000, 90_000, "project", "Basic governance"),
        medium=CostEstimate(90_000, 250_000, "project", "Standard program"),
        large=CostEstimate(250_000, 600_000, "project", "Enterprise program"),
        enterprise=CostEstimate(600_000, 1_500_000, "project", "Global data governance"),
        typical_duration_weeks=(12, 40),
        keywords=["data governance", "data catalog", "collibra", "alation"],
        sources=["Data governance consultants"],
    ),

    "data_analytics_platform": ActivityCost(
        activity_id="DATA-005",
        name="Analytics/ML Platform Implementation",
        category="data_analytics",
        description="Implement analytics and machine learning platform",
        small=CostEstimate(50_000, 150_000, "project", "Basic analytics"),
        medium=CostEstimate(150_000, 400_000, "project", "Standard ML platform"),
        large=CostEstimate(400_000, 1_000_000, "project", "Enterprise MLOps"),
        enterprise=CostEstimate(1_000_000, 3_000_000, "project", "Global AI/ML platform"),
        typical_duration_weeks=(12, 40),
        keywords=["analytics", "ml", "machine learning", "ai", "mlops", "databricks"],
        sources=["ML platform vendors"],
    ),
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_activity_cost(activity_id: str, tier: ProjectTier = ProjectTier.MEDIUM) -> Optional[CostEstimate]:
    """Get cost estimate for an activity at a specific tier."""
    activity = COST_DATABASE.get(activity_id)
    if not activity:
        return None

    tier_map = {
        ProjectTier.SMALL: activity.small,
        ProjectTier.MEDIUM: activity.medium,
        ProjectTier.LARGE: activity.large,
        ProjectTier.ENTERPRISE: activity.enterprise,
    }
    return tier_map.get(tier)


def search_activities(keywords: List[str], category: str = None) -> List[ActivityCost]:
    """Search for activities matching keywords and optional category."""
    results = []
    keywords_lower = [k.lower() for k in keywords]

    for activity in COST_DATABASE.values():
        if category and activity.category != category:
            continue

        # Check if any keyword matches
        activity_text = f"{activity.name} {activity.description} {' '.join(activity.keywords)}".lower()
        if any(kw in activity_text for kw in keywords_lower):
            results.append(activity)

    return results


def get_activities_by_category(category: str) -> List[ActivityCost]:
    """Get all activities in a category."""
    return [a for a in COST_DATABASE.values() if a.category == category]


def get_all_categories() -> List[str]:
    """Get list of all categories."""
    return sorted(set(a.category for a in COST_DATABASE.values()))


def estimate_total_integration_cost(
    activities: List[Tuple[str, ProjectTier]],
    company_multiplier: float = 1.0
) -> Dict[str, Any]:
    """
    Estimate total integration cost for a list of activities.

    Args:
        activities: List of (activity_id, tier) tuples
        company_multiplier: Overall company profile multiplier

    Returns:
        {
            "total_low": int,
            "total_high": int,
            "breakdown": [...],
            "methodology": str
        }
    """
    total_low = 0
    total_high = 0
    breakdown = []

    for activity_id, tier in activities:
        cost = get_activity_cost(activity_id, tier)
        if cost:
            adjusted_low = int(cost.low * company_multiplier)
            adjusted_high = int(cost.high * company_multiplier)
            total_low += adjusted_low
            total_high += adjusted_high

            activity = COST_DATABASE[activity_id]
            breakdown.append({
                "activity_id": activity_id,
                "name": activity.name,
                "tier": tier.value,
                "base_low": cost.low,
                "base_high": cost.high,
                "adjusted_low": adjusted_low,
                "adjusted_high": adjusted_high,
                "unit": cost.unit
            })

    return {
        "total_low": total_low,
        "total_high": total_high,
        "formatted": f"${total_low:,} - ${total_high:,}",
        "breakdown": breakdown,
        "company_multiplier": company_multiplier,
        "methodology": "Research-backed estimates from vendor pricing and industry benchmarks, adjusted by company profile multiplier"
    }


# =============================================================================
# SUMMARY STATISTICS
# =============================================================================

def get_database_stats() -> Dict[str, Any]:
    """Get summary statistics about the cost database."""
    categories = get_all_categories()
    return {
        "total_activities": len(COST_DATABASE),
        "categories": categories,
        "activities_by_category": {cat: len(get_activities_by_category(cat)) for cat in categories},
        "last_updated": "January 2026",
        "sources_count": sum(len(a.sources) for a in COST_DATABASE.values())
    }


def export_to_csv(filepath: str = "cost_database_export.csv") -> str:
    """Export the entire database to CSV format."""
    import csv

    rows = []
    for key, activity in COST_DATABASE.items():
        for tier_name, tier_data in [
            ("small", activity.small),
            ("medium", activity.medium),
            ("large", activity.large),
            ("enterprise", activity.enterprise)
        ]:
            rows.append({
                "activity_key": key,
                "activity_id": activity.activity_id,
                "name": activity.name,
                "category": activity.category,
                "description": activity.description,
                "tier": tier_name,
                "cost_low": tier_data.low,
                "cost_high": tier_data.high,
                "unit": tier_data.unit,
                "tier_notes": tier_data.notes,
                "source": tier_data.source,
                "duration_min_weeks": activity.typical_duration_weeks[0],
                "duration_max_weeks": activity.typical_duration_weeks[1],
                "keywords": "|".join(activity.keywords),
                "sources": "|".join(activity.sources),
                "notes": activity.notes
            })

    fieldnames = [
        "activity_key", "activity_id", "name", "category", "description",
        "tier", "cost_low", "cost_high", "unit", "tier_notes", "source",
        "duration_min_weeks", "duration_max_weeks", "keywords", "sources", "notes"
    ]

    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return filepath


def export_summary_csv(filepath: str = "cost_database_summary.csv") -> str:
    """Export a summary view (one row per activity, medium tier as default)."""
    import csv

    rows = []
    for key, activity in COST_DATABASE.items():
        rows.append({
            "activity_id": activity.activity_id,
            "name": activity.name,
            "category": activity.category,
            "description": activity.description,
            "small_low": activity.small.low,
            "small_high": activity.small.high,
            "medium_low": activity.medium.low,
            "medium_high": activity.medium.high,
            "large_low": activity.large.low,
            "large_high": activity.large.high,
            "enterprise_low": activity.enterprise.low,
            "enterprise_high": activity.enterprise.high,
            "unit": activity.medium.unit,
            "duration_weeks": f"{activity.typical_duration_weeks[0]}-{activity.typical_duration_weeks[1]}",
            "keywords": "|".join(activity.keywords),
            "sources": "|".join(activity.sources)
        })

    fieldnames = [
        "activity_id", "name", "category", "description",
        "small_low", "small_high", "medium_low", "medium_high",
        "large_low", "large_high", "enterprise_low", "enterprise_high",
        "unit", "duration_weeks", "keywords", "sources"
    ]

    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return filepath


if __name__ == "__main__":
    import sys

    # Print database summary
    stats = get_database_stats()
    print("IT Integration Cost Database")
    print("=" * 50)
    print(f"Total Activities: {stats['total_activities']}")
    print(f"Last Updated: {stats['last_updated']}")
    print("\nActivities by Category:")
    for cat, count in sorted(stats['activities_by_category'].items()):
        print(f"  {cat}: {count}")

    # Export to CSV if requested
    if len(sys.argv) > 1 and sys.argv[1] == "--export":
        print("\nExporting to CSV...")
        export_to_csv("docs/cost_database_detailed.csv")
        export_summary_csv("docs/cost_database_summary.csv")
        print("  Created: docs/cost_database_detailed.csv")
        print("  Created: docs/cost_database_summary.csv")
