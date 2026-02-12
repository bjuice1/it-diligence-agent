"""
Application Category Mappings

Maps known applications to IT Due Diligence categories.
Used for auto-categorization during inventory ingestion.

Categories follow IT DD taxonomy:
- erp: Enterprise Resource Planning
- crm: Customer Relationship Management
- hcm: Human Capital Management / HR
- finance: Financial Management
- collaboration: Communication & Collaboration
- productivity: Office & Productivity
- security: Security & Identity
- infrastructure: Infrastructure & Platform
- database: Database Systems
- devops: Development & Operations
- bi_analytics: Business Intelligence & Analytics
- industry_vertical: Industry-Specific Software
- custom: Custom/In-house Built

Phase 3: App Ingestion & Category Mapping
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import re


@dataclass
class AppMapping:
    """Mapping for a known application."""
    category: str
    vendor: str
    description: str
    aliases: List[str]  # Alternative names
    is_saas: bool = True
    is_industry_standard: bool = True


# =============================================================================
# STANDARD APPLICATION MAPPINGS
# =============================================================================

# Maps normalized app name (lowercase) to AppMapping
APP_MAPPINGS: Dict[str, AppMapping] = {
    # -------------------------------------------------------------------------
    # ERP - Enterprise Resource Planning
    # -------------------------------------------------------------------------
    "sap": AppMapping(
        category="erp",
        vendor="SAP",
        description="Enterprise resource planning and business suite",
        aliases=["sap erp", "sap s/4hana", "sap hana", "sap ecc", "sap r/3"],
        is_saas=False,
    ),
    "oracle e-business suite": AppMapping(
        category="erp",
        vendor="Oracle",
        description="Oracle's integrated business applications suite",
        aliases=["oracle ebs", "oracle ebusiness", "e-business suite"],
        is_saas=False,
    ),
    "oracle cloud erp": AppMapping(
        category="erp",
        vendor="Oracle",
        description="Oracle's cloud-based ERP solution",
        aliases=["oracle fusion", "oracle cloud"],
    ),
    "netsuite": AppMapping(
        category="erp",
        vendor="Oracle",
        description="Cloud-based ERP for mid-market companies",
        aliases=["oracle netsuite", "netsuite erp"],
    ),
    "microsoft dynamics 365": AppMapping(
        category="erp",
        vendor="Microsoft",
        description="Cloud-based ERP and CRM suite",
        aliases=["dynamics 365", "d365", "dynamics365"],
    ),
    "microsoft dynamics ax": AppMapping(
        category="erp",
        vendor="Microsoft",
        description="Enterprise ERP (legacy, now Dynamics 365)",
        aliases=["dynamics ax", "axapta"],
        is_saas=False,
    ),
    "microsoft dynamics nav": AppMapping(
        category="erp",
        vendor="Microsoft",
        description="SMB ERP (now Business Central)",
        aliases=["dynamics nav", "navision", "business central"],
    ),
    "infor": AppMapping(
        category="erp",
        vendor="Infor",
        description="Industry-specific ERP solutions",
        aliases=["infor erp", "infor m3", "infor ln", "infor cloudsuite"],
    ),
    "epicor": AppMapping(
        category="erp",
        vendor="Epicor",
        description="ERP for manufacturing and distribution",
        aliases=["epicor erp", "epicor prophet 21", "epicor eclipse"],
        is_saas=False,
    ),
    "sage": AppMapping(
        category="erp",
        vendor="Sage",
        description="Business management software",
        aliases=["sage 100", "sage 300", "sage x3", "sage intacct"],
    ),

    # -------------------------------------------------------------------------
    # CRM - Customer Relationship Management
    # -------------------------------------------------------------------------
    "salesforce": AppMapping(
        category="crm",
        vendor="Salesforce",
        description="Cloud-based CRM platform",
        aliases=["sfdc", "salesforce crm", "sales cloud", "service cloud"],
    ),
    "hubspot": AppMapping(
        category="crm",
        vendor="HubSpot",
        description="Inbound marketing and CRM platform",
        aliases=["hubspot crm", "hubspot sales"],
    ),
    "microsoft dynamics crm": AppMapping(
        category="crm",
        vendor="Microsoft",
        description="Customer relationship management",
        aliases=["dynamics crm", "d365 sales"],
    ),
    "zoho crm": AppMapping(
        category="crm",
        vendor="Zoho",
        description="Cloud CRM for businesses",
        aliases=["zoho"],
    ),
    "pipedrive": AppMapping(
        category="crm",
        vendor="Pipedrive",
        description="Sales CRM for small teams",
        aliases=[],
    ),
    "sugar crm": AppMapping(
        category="crm",
        vendor="SugarCRM",
        description="CRM platform",
        aliases=["sugarcrm"],
    ),

    # -------------------------------------------------------------------------
    # HCM - Human Capital Management / HR
    # -------------------------------------------------------------------------
    "workday": AppMapping(
        category="hcm",
        vendor="Workday",
        description="Cloud HCM and financial management",
        aliases=["workday hcm", "workday hr"],
    ),
    "adp": AppMapping(
        category="hcm",
        vendor="ADP",
        description="Payroll and HR services",
        aliases=["adp workforce now", "adp vantage", "adp totalconnect"],
    ),
    "ultipro": AppMapping(
        category="hcm",
        vendor="UKG",
        description="HCM suite (now UKG Pro)",
        aliases=["ukg pro", "ultimate software"],
    ),
    "bamboohr": AppMapping(
        category="hcm",
        vendor="BambooHR",
        description="HR software for SMBs",
        aliases=["bamboo hr"],
    ),
    "paycom": AppMapping(
        category="hcm",
        vendor="Paycom",
        description="Payroll and HR technology",
        aliases=[],
    ),
    "paylocity": AppMapping(
        category="hcm",
        vendor="Paylocity",
        description="Payroll and HR software",
        aliases=[],
    ),
    "ceridian dayforce": AppMapping(
        category="hcm",
        vendor="Ceridian",
        description="HCM platform",
        aliases=["dayforce", "ceridian"],
    ),
    "successfactors": AppMapping(
        category="hcm",
        vendor="SAP",
        description="Cloud-based HCM suite",
        aliases=["sap successfactors", "sf"],
    ),

    # -------------------------------------------------------------------------
    # Finance
    # -------------------------------------------------------------------------
    "quickbooks": AppMapping(
        category="finance",
        vendor="Intuit",
        description="Accounting software for small businesses",
        aliases=["qb", "quickbooks online", "qbo"],
    ),
    "xero": AppMapping(
        category="finance",
        vendor="Xero",
        description="Cloud accounting software",
        aliases=[],
    ),
    "bill.com": AppMapping(
        category="finance",
        vendor="Bill.com",
        description="AP/AR automation",
        aliases=["billcom", "bill com"],
    ),
    "coupa": AppMapping(
        category="finance",
        vendor="Coupa",
        description="Business spend management",
        aliases=[],
    ),
    "concur": AppMapping(
        category="finance",
        vendor="SAP",
        description="Travel and expense management",
        aliases=["sap concur"],
    ),
    "blackline": AppMapping(
        category="finance",
        vendor="BlackLine",
        description="Financial close automation",
        aliases=[],
    ),

    # -------------------------------------------------------------------------
    # Collaboration
    # -------------------------------------------------------------------------
    "microsoft teams": AppMapping(
        category="collaboration",
        vendor="Microsoft",
        description="Team collaboration and chat",
        aliases=["teams", "ms teams"],
    ),
    "slack": AppMapping(
        category="collaboration",
        vendor="Salesforce",
        description="Business messaging platform",
        aliases=[],
    ),
    "zoom": AppMapping(
        category="collaboration",
        vendor="Zoom",
        description="Video communications",
        aliases=["zoom meetings", "zoom video"],
    ),
    "webex": AppMapping(
        category="collaboration",
        vendor="Cisco",
        description="Video conferencing and collaboration",
        aliases=["cisco webex", "webex meetings"],
    ),
    "google meet": AppMapping(
        category="collaboration",
        vendor="Google",
        description="Video conferencing",
        aliases=["meet", "hangouts meet"],
    ),
    "asana": AppMapping(
        category="collaboration",
        vendor="Asana",
        description="Work management platform",
        aliases=[],
    ),
    "monday.com": AppMapping(
        category="collaboration",
        vendor="monday.com",
        description="Work operating system",
        aliases=["monday", "mondaycom"],
    ),
    "trello": AppMapping(
        category="collaboration",
        vendor="Atlassian",
        description="Project management boards",
        aliases=[],
    ),

    # -------------------------------------------------------------------------
    # Productivity
    # -------------------------------------------------------------------------
    "microsoft 365": AppMapping(
        category="productivity",
        vendor="Microsoft",
        description="Cloud productivity suite",
        aliases=["office 365", "o365", "m365", "microsoft office"],
    ),
    "google workspace": AppMapping(
        category="productivity",
        vendor="Google",
        description="Cloud productivity and collaboration",
        aliases=["g suite", "gsuite", "google apps"],
    ),
    "dropbox": AppMapping(
        category="productivity",
        vendor="Dropbox",
        description="Cloud file storage and sharing",
        aliases=["dropbox business"],
    ),
    "box": AppMapping(
        category="productivity",
        vendor="Box",
        description="Cloud content management",
        aliases=["box.com"],
    ),
    "sharepoint": AppMapping(
        category="productivity",
        vendor="Microsoft",
        description="Document management and collaboration",
        aliases=["sharepoint online", "spo"],
    ),
    "confluence": AppMapping(
        category="productivity",
        vendor="Atlassian",
        description="Team wiki and knowledge base",
        aliases=[],
    ),
    "notion": AppMapping(
        category="productivity",
        vendor="Notion",
        description="All-in-one workspace",
        aliases=[],
    ),
    "docusign": AppMapping(
        category="productivity",
        vendor="DocuSign",
        description="Electronic signature platform",
        aliases=["docusign esignature"],
    ),
    "adobe sign": AppMapping(
        category="productivity",
        vendor="Adobe",
        description="Electronic signatures",
        aliases=["adobe esign", "echosign"],
    ),

    # -------------------------------------------------------------------------
    # Security & Identity
    # -------------------------------------------------------------------------
    "okta": AppMapping(
        category="security",
        vendor="Okta",
        description="Identity and access management",
        aliases=["okta sso", "okta iam"],
    ),
    "azure ad": AppMapping(
        category="security",
        vendor="Microsoft",
        description="Cloud identity service",
        aliases=["azure active directory", "aad", "entra id", "microsoft entra"],
    ),
    "duo": AppMapping(
        category="security",
        vendor="Cisco",
        description="Multi-factor authentication",
        aliases=["duo security", "duo mfa"],
    ),
    "ping identity": AppMapping(
        category="security",
        vendor="Ping Identity",
        description="Identity security platform",
        aliases=["pingone", "pingfederate"],
    ),
    "crowdstrike": AppMapping(
        category="security",
        vendor="CrowdStrike",
        description="Endpoint security platform",
        aliases=["crowdstrike falcon"],
    ),
    "sentinelone": AppMapping(
        category="security",
        vendor="SentinelOne",
        description="Autonomous endpoint protection",
        aliases=["sentinel one", "s1"],
    ),
    "carbon black": AppMapping(
        category="security",
        vendor="VMware",
        description="Endpoint security",
        aliases=["vmware carbon black", "cb defense"],
    ),
    "zscaler": AppMapping(
        category="security",
        vendor="Zscaler",
        description="Cloud security platform",
        aliases=["zscaler zia", "zscaler zpa"],
    ),
    "palo alto": AppMapping(
        category="security",
        vendor="Palo Alto Networks",
        description="Network security",
        aliases=["palo alto networks", "pan", "prisma"],
    ),
    "splunk": AppMapping(
        category="security",
        vendor="Splunk",
        description="SIEM and observability",
        aliases=["splunk enterprise", "splunk cloud"],
    ),
    "cyberark": AppMapping(
        category="security",
        vendor="CyberArk",
        description="Privileged access management",
        aliases=["cyberark pam"],
    ),
    "sailpoint": AppMapping(
        category="security",
        vendor="SailPoint",
        description="Identity governance",
        aliases=["sailpoint identitynow", "sailpoint iiq"],
    ),
    "proofpoint": AppMapping(
        category="security",
        vendor="Proofpoint",
        description="Email security",
        aliases=[],
    ),
    "mimecast": AppMapping(
        category="security",
        vendor="Mimecast",
        description="Email security and archiving",
        aliases=[],
    ),
    "knowbe4": AppMapping(
        category="security",
        vendor="KnowBe4",
        description="Security awareness training",
        aliases=["know be 4"],
    ),

    # -------------------------------------------------------------------------
    # Infrastructure & Platform
    # -------------------------------------------------------------------------
    "vmware": AppMapping(
        category="infrastructure",
        vendor="VMware",
        description="Virtualization platform",
        aliases=["vmware vsphere", "esxi", "vcenter"],
        is_saas=False,
    ),
    "aws": AppMapping(
        category="infrastructure",
        vendor="Amazon",
        description="Amazon Web Services cloud platform",
        aliases=["amazon web services", "amazon aws"],
    ),
    "azure": AppMapping(
        category="infrastructure",
        vendor="Microsoft",
        description="Microsoft cloud platform",
        aliases=["microsoft azure"],
    ),
    "google cloud": AppMapping(
        category="infrastructure",
        vendor="Google",
        description="Google Cloud Platform",
        aliases=["gcp", "google cloud platform"],
    ),
    "kubernetes": AppMapping(
        category="infrastructure",
        vendor="CNCF",
        description="Container orchestration",
        aliases=["k8s"],
        is_saas=False,
    ),
    "docker": AppMapping(
        category="infrastructure",
        vendor="Docker",
        description="Container platform",
        aliases=["docker enterprise"],
        is_saas=False,
    ),
    "terraform": AppMapping(
        category="infrastructure",
        vendor="HashiCorp",
        description="Infrastructure as code",
        aliases=["terraform cloud"],
    ),
    "ansible": AppMapping(
        category="infrastructure",
        vendor="Red Hat",
        description="Automation platform",
        aliases=["ansible tower", "ansible automation"],
        is_saas=False,
    ),
    "citrix": AppMapping(
        category="infrastructure",
        vendor="Citrix",
        description="Desktop and app virtualization",
        aliases=["citrix virtual apps", "xenapp", "xendesktop"],
    ),

    # -------------------------------------------------------------------------
    # Database
    # -------------------------------------------------------------------------
    "oracle database": AppMapping(
        category="database",
        vendor="Oracle",
        description="Enterprise database",
        aliases=["oracle db", "oracle rdbms"],
        is_saas=False,
    ),
    "sql server": AppMapping(
        category="database",
        vendor="Microsoft",
        description="Microsoft database server",
        aliases=["microsoft sql server", "mssql", "ms sql"],
        is_saas=False,
    ),
    "postgresql": AppMapping(
        category="database",
        vendor="PostgreSQL",
        description="Open source database",
        aliases=["postgres"],
        is_saas=False,
        is_industry_standard=False,
    ),
    "mysql": AppMapping(
        category="database",
        vendor="Oracle",
        description="Open source database",
        aliases=[],
        is_saas=False,
        is_industry_standard=False,
    ),
    "mongodb": AppMapping(
        category="database",
        vendor="MongoDB",
        description="NoSQL document database",
        aliases=["mongo"],
    ),
    "snowflake": AppMapping(
        category="database",
        vendor="Snowflake",
        description="Cloud data platform",
        aliases=[],
    ),
    "databricks": AppMapping(
        category="database",
        vendor="Databricks",
        description="Data lakehouse platform",
        aliases=[],
    ),

    # -------------------------------------------------------------------------
    # DevOps & Development
    # -------------------------------------------------------------------------
    "github": AppMapping(
        category="devops",
        vendor="Microsoft",
        description="Code hosting and collaboration",
        aliases=["github enterprise"],
    ),
    "gitlab": AppMapping(
        category="devops",
        vendor="GitLab",
        description="DevOps platform",
        aliases=["gitlab enterprise"],
    ),
    "bitbucket": AppMapping(
        category="devops",
        vendor="Atlassian",
        description="Git repository management",
        aliases=[],
    ),
    "jira": AppMapping(
        category="devops",
        vendor="Atlassian",
        description="Issue and project tracking",
        aliases=["jira software", "jira service management"],
    ),
    "jenkins": AppMapping(
        category="devops",
        vendor="Jenkins",
        description="CI/CD automation server",
        aliases=[],
        is_saas=False,
        is_industry_standard=False,
    ),
    "azure devops": AppMapping(
        category="devops",
        vendor="Microsoft",
        description="DevOps services",
        aliases=["azure devops services", "vsts", "tfs"],
    ),
    "servicenow": AppMapping(
        category="devops",
        vendor="ServiceNow",
        description="IT service management",
        aliases=["snow", "service now"],
    ),
    "pagerduty": AppMapping(
        category="devops",
        vendor="PagerDuty",
        description="Incident management",
        aliases=["pager duty"],
    ),
    "datadog": AppMapping(
        category="devops",
        vendor="Datadog",
        description="Monitoring and analytics",
        aliases=[],
    ),
    "new relic": AppMapping(
        category="devops",
        vendor="New Relic",
        description="Application performance monitoring",
        aliases=["newrelic"],
    ),

    # -------------------------------------------------------------------------
    # Business Intelligence & Analytics
    # -------------------------------------------------------------------------
    "tableau": AppMapping(
        category="bi_analytics",
        vendor="Salesforce",
        description="Business intelligence and visualization",
        aliases=["tableau server", "tableau online"],
    ),
    "power bi": AppMapping(
        category="bi_analytics",
        vendor="Microsoft",
        description="Business analytics service",
        aliases=["powerbi", "power bi pro"],
    ),
    "looker": AppMapping(
        category="bi_analytics",
        vendor="Google",
        description="Business intelligence platform",
        aliases=["google looker"],
    ),
    "qlik": AppMapping(
        category="bi_analytics",
        vendor="Qlik",
        description="Data analytics platform",
        aliases=["qlikview", "qlik sense"],
    ),
    "domo": AppMapping(
        category="bi_analytics",
        vendor="Domo",
        description="Business intelligence platform",
        aliases=[],
    ),
    "alteryx": AppMapping(
        category="bi_analytics",
        vendor="Alteryx",
        description="Data analytics automation",
        aliases=[],
    ),

    # -------------------------------------------------------------------------
    # Industry Vertical - Healthcare
    # -------------------------------------------------------------------------
    "epic": AppMapping(
        category="industry_vertical",
        vendor="Epic Systems",
        description="Healthcare EHR system",
        aliases=["epic ehr", "epic systems"],
        is_saas=False,
    ),
    "cerner": AppMapping(
        category="industry_vertical",
        vendor="Oracle",
        description="Healthcare IT solutions",
        aliases=["oracle cerner", "oracle health"],
    ),
    "meditech": AppMapping(
        category="industry_vertical",
        vendor="MEDITECH",
        description="Healthcare information system",
        aliases=[],
        is_saas=False,
    ),
    "allscripts": AppMapping(
        category="industry_vertical",
        vendor="Allscripts",
        description="Healthcare IT solutions",
        aliases=[],
    ),
    "athenahealth": AppMapping(
        category="industry_vertical",
        vendor="athenahealth",
        description="Cloud-based healthcare services",
        aliases=["athena health"],
    ),
    # Healthcare additions
    "veradigm": AppMapping(
        category="industry_vertical",
        vendor="Veradigm (Allscripts)",
        description="EHR, practice management, and health data analytics",
        aliases=["veradigm ehr", "allscripts veradigm", "veradigm practice fusion"],
        is_saas=True,
        is_industry_standard=True,
    ),
    "nextgen healthcare": AppMapping(
        category="industry_vertical",
        vendor="NextGen Healthcare",
        description="Ambulatory EHR and practice management",
        aliases=["nextgen ehr", "nextgen pm", "nextgen healthcare ehr"],
        is_saas=True,
        is_industry_standard=True,
    ),
    "eclinicalworks": AppMapping(
        category="industry_vertical",
        vendor="eClinicalWorks",
        description="Cloud-based EHR, practice management, and RCM",
        aliases=["ecw", "eclinicalworks ehr", "eclinical"],
        is_saas=True,
        is_industry_standard=True,
    ),
    "netsmart": AppMapping(
        category="industry_vertical",
        vendor="Netsmart Technologies",
        description="Behavioral health and human services EHR",
        aliases=["netsmart ehr", "netsmart myavatar", "myavatar"],
        is_saas=True,
        is_industry_standard=True,
    ),
    "inovalon": AppMapping(
        category="industry_vertical",
        vendor="Inovalon",
        description="Healthcare data analytics and quality measures",
        aliases=["inovalon one", "inovalon analytics"],
        is_saas=True,
        is_industry_standard=False,
    ),
    "healthstream": AppMapping(
        category="industry_vertical",
        vendor="HealthStream",
        description="Healthcare workforce management and credentialing",
        aliases=["healthstream learning", "healthstream credentialing"],
        is_saas=True,
        is_industry_standard=True,
    ),

    # -------------------------------------------------------------------------
    # Industry Vertical - Insurance
    # -------------------------------------------------------------------------
    "duck creek": AppMapping(
        category="industry_vertical",
        vendor="Duck Creek",
        description="Insurance software suite",
        aliases=["duckcreek", "duck creek technologies"],
    ),
    "guidewire": AppMapping(
        category="industry_vertical",
        vendor="Guidewire",
        description="P&C insurance platform",
        aliases=["guidewire insurancesuite"],
    ),
    # Policy Administration
    "majesco": AppMapping(
        category="industry_vertical",
        vendor="Majesco",
        description="Cloud-native P&C and L&A policy administration",
        aliases=["majesco policy", "majesco l&a", "majesco p&c"],
        is_saas=True,
        is_industry_standard=True,
    ),
    "insurity": AppMapping(
        category="industry_vertical",
        vendor="Insurity",
        description="P&C policy, billing, and claims platform",
        aliases=["insurity policy", "insurity billing", "insurity claims"],
        is_saas=True,
        is_industry_standard=True,
    ),
    "socotra": AppMapping(
        category="industry_vertical",
        vendor="Socotra",
        description="Cloud-native insurance core platform",
        aliases=["socotra insurance", "socotra core"],
        is_saas=True,
        is_industry_standard=False,
    ),
    "earnix": AppMapping(
        category="industry_vertical",
        vendor="Earnix",
        description="Insurance pricing and rating engine",
        aliases=["earnix pricing", "earnix rating"],
        is_saas=True,
        is_industry_standard=True,
    ),
    "sapiens": AppMapping(
        category="industry_vertical",
        vendor="Sapiens International",
        description="Insurance software for P&C, L&A, and reinsurance",
        aliases=["sapiens insurance", "sapiens alis", "sapiens idit"],
        is_saas=True,
        is_industry_standard=True,
    ),
    "vertafore": AppMapping(
        category="industry_vertical",
        vendor="Vertafore",
        description="Insurance distribution management (AMS360, Sircon)",
        aliases=["vertafore ams360", "ams360", "vertafore sircon", "sircon", "vertafore agency platform"],
        is_saas=True,
        is_industry_standard=True,
    ),
    "applied systems": AppMapping(
        category="industry_vertical",
        vendor="Applied Systems",
        description="Insurance agency management (Applied Epic, TAM)",
        aliases=["applied epic", "applied tam", "applied systems epic", "applied rater"],
        is_saas=True,
        is_industry_standard=True,
    ),
    "britecore": AppMapping(
        category="industry_vertical",
        vendor="BriteCore",
        description="Cloud-native P&C core platform for insurers",
        aliases=["britecore insurance", "brite core"],
        is_saas=True,
        is_industry_standard=False,
    ),
    "snapsheet": AppMapping(
        category="industry_vertical",
        vendor="Snapsheet",
        description="Virtual claims appraisal and management",
        aliases=["snapsheet claims"],
        is_saas=True,
        is_industry_standard=False,
    ),

    # -------------------------------------------------------------------------
    # Industry Vertical - Manufacturing
    # -------------------------------------------------------------------------
    "siemens plm": AppMapping(
        category="industry_vertical",
        vendor="Siemens",
        description="Product lifecycle management",
        aliases=["teamcenter", "siemens teamcenter"],
        is_saas=False,
    ),
    "ptc windchill": AppMapping(
        category="industry_vertical",
        vendor="PTC",
        description="PLM software",
        aliases=["windchill"],
        is_saas=False,
    ),
    "autodesk": AppMapping(
        category="industry_vertical",
        vendor="Autodesk",
        description="Design and engineering software",
        aliases=["autocad", "revit", "fusion 360"],
    ),
    # Manufacturing additions
    "rockwell automation": AppMapping(
        category="industry_vertical",
        vendor="Rockwell Automation",
        description="Industrial automation and MES (FactoryTalk)",
        aliases=["factorytalk", "rockwell factorytalk", "rockwell mes", "allen-bradley"],
        is_saas=False,
        is_industry_standard=True,
    ),
    "aveva": AppMapping(
        category="industry_vertical",
        vendor="AVEVA (Schneider Electric)",
        description="Industrial software for engineering and operations",
        aliases=["aveva engineering", "aveva operations", "wonderware", "schneider electric aveva"],
        is_saas=False,
        is_industry_standard=True,
    ),
    "dassault systemes": AppMapping(
        category="industry_vertical",
        vendor="Dassault Systemes",
        description="PLM, CAD/CAM (CATIA, ENOVIA, SOLIDWORKS)",
        aliases=["catia", "enovia", "solidworks", "3dexperience", "delmia"],
        is_saas=False,
        is_industry_standard=True,
    ),
    "sap plant maintenance": AppMapping(
        category="industry_vertical",
        vendor="SAP",
        description="Plant maintenance and asset management module",
        aliases=["sap pm", "sap plant maintenance", "sap eam"],
        is_saas=False,
        is_industry_standard=True,
    ),
    "infor cloudsuite industrial": AppMapping(
        category="industry_vertical",
        vendor="Infor",
        description="Manufacturing ERP for discrete and process manufacturing",
        aliases=["infor csi", "cloudsuite industrial", "syteline", "infor syteline"],
        is_saas=True,
        is_industry_standard=True,
    ),
    "plex": AppMapping(
        category="industry_vertical",
        vendor="Rockwell Automation (Plex Systems)",
        description="Cloud-native smart manufacturing platform",
        aliases=["plex manufacturing", "plex systems", "plex erp"],
        is_saas=True,
        is_industry_standard=False,
    ),

    # -------------------------------------------------------------------------
    # Industry Vertical - Retail
    # -------------------------------------------------------------------------
    "shopify": AppMapping(
        category="industry_vertical",
        vendor="Shopify",
        description="E-commerce platform",
        aliases=["shopify plus"],
    ),
    "magento": AppMapping(
        category="industry_vertical",
        vendor="Adobe",
        description="E-commerce platform",
        aliases=["adobe commerce"],
    ),
    # Retail additions
    "oracle retail": AppMapping(
        category="industry_vertical",
        vendor="Oracle",
        description="Retail merchandising, planning, and POS",
        aliases=["oracle retail merchandising", "oracle retail pos", "oracle xstore"],
        is_saas=False,
        is_industry_standard=True,
    ),
    "manhattan associates": AppMapping(
        category="industry_vertical",
        vendor="Manhattan Associates",
        description="Supply chain and warehouse management for retail",
        aliases=["manhattan wms", "manhattan active", "manhattan warehouse"],
        is_saas=True,
        is_industry_standard=True,
    ),
    "blue yonder": AppMapping(
        category="industry_vertical",
        vendor="Blue Yonder (Panasonic)",
        description="Supply chain planning and fulfillment",
        aliases=["jda software", "blue yonder wms", "blue yonder planning", "jda"],
        is_saas=True,
        is_industry_standard=True,
    ),
    "lightspeed": AppMapping(
        category="industry_vertical",
        vendor="Lightspeed Commerce",
        description="Cloud POS and ecommerce platform for retail/restaurant",
        aliases=["lightspeed pos", "lightspeed retail", "lightspeed restaurant"],
        is_saas=True,
        is_industry_standard=False,
    ),

    # -------------------------------------------------------------------------
    # Custom/Internal Applications
    # -------------------------------------------------------------------------
    "internal": AppMapping(
        category="custom",
        vendor="Internal",
        description="Internally developed application",
        aliases=["in-house", "custom", "proprietary"],
        is_saas=False,
        is_industry_standard=False,
    ),
}


# =============================================================================
# CATEGORY DEFINITIONS
# =============================================================================

CATEGORY_DEFINITIONS: Dict[str, str] = {
    "erp": "Enterprise Resource Planning - Core business systems for finance, operations, supply chain",
    "crm": "Customer Relationship Management - Sales, marketing, and customer service",
    "hcm": "Human Capital Management - HR, payroll, talent management",
    "finance": "Financial Management - Accounting, AP/AR, expense management",
    "collaboration": "Communication & Collaboration - Messaging, video, project management",
    "productivity": "Office & Productivity - Documents, storage, workflow",
    "security": "Security & Identity - IAM, endpoint protection, SIEM",
    "infrastructure": "Infrastructure & Platform - Cloud, virtualization, containers",
    "database": "Database Systems - RDBMS, NoSQL, data platforms",
    "devops": "Development & Operations - CI/CD, ITSM, monitoring",
    "bi_analytics": "Business Intelligence & Analytics - Reporting, visualization, analytics",
    "industry_vertical": "Industry-Specific Software - Healthcare, insurance, manufacturing, etc.",
    "custom": "Custom/In-house Built - Proprietary applications",
    "unknown": "Unknown - Requires investigation",
}


# =============================================================================
# LOOKUP FUNCTIONS
# =============================================================================

def normalize_app_name(name: str) -> str:
    """
    Normalize application name for matching.

    - Lowercase
    - Remove common suffixes (Inc, LLC, Corp)
    - Remove version numbers
    - Trim whitespace
    """
    if not name:
        return ""

    normalized = name.lower().strip()

    # Remove common company suffixes
    suffixes = [" inc", " llc", " corp", " ltd", " limited", " gmbh"]
    for suffix in suffixes:
        if normalized.endswith(suffix):
            normalized = normalized[:-len(suffix)]

    # Remove version numbers (e.g., "SAP 7.5" -> "SAP")
    normalized = re.sub(r'\s+v?\d+(\.\d+)*$', '', normalized)
    normalized = re.sub(r'\s+\d{4}$', '', normalized)  # Year like "Office 2019"

    return normalized.strip()


def lookup_app(name: str) -> Optional[AppMapping]:
    """
    Look up an application by name.

    Tries:
    1. Exact match (normalized)
    2. Alias match
    3. Partial match (starts with)

    Args:
        name: Application name to look up

    Returns:
        AppMapping if found, None otherwise
    """
    if not name:
        return None

    normalized = normalize_app_name(name)

    # Exact match
    if normalized in APP_MAPPINGS:
        return APP_MAPPINGS[normalized]

    # Alias match
    for key, mapping in APP_MAPPINGS.items():
        if normalized in [normalize_app_name(a) for a in mapping.aliases]:
            return mapping

    # Partial match (app name starts with known name)
    for key, mapping in APP_MAPPINGS.items():
        if normalized.startswith(key) or key.startswith(normalized):
            return mapping
        for alias in mapping.aliases:
            norm_alias = normalize_app_name(alias)
            if normalized.startswith(norm_alias) or norm_alias.startswith(normalized):
                return mapping

    return None


def categorize_app(name: str) -> Tuple[str, Optional[AppMapping], str, str]:
    """Categorize an app and return (category, mapping, confidence, inferred_from).

    Returns:
        category: The category string
        mapping: The AppMapping if found, None otherwise
        confidence: "high", "medium", "low", or "none"
        inferred_from: "mapping_exact", "mapping_alias", "mapping_partial", "keyword_inference", "default"
    """
    normalized = normalize_app_name(name)

    # Tier 1: Exact match (high confidence)
    if normalized in APP_MAPPINGS:
        m = APP_MAPPINGS[normalized]
        return m.category, m, "high", "mapping_exact"

    # Tier 2: Alias match (high confidence)
    for app_key, m in APP_MAPPINGS.items():
        for alias in m.aliases:
            if normalize_app_name(alias) == normalized:
                return m.category, m, "high", "mapping_alias"

    # Tier 3: Partial match (medium confidence)
    for app_key, m in APP_MAPPINGS.items():
        if app_key in normalized or normalized in app_key:
            return m.category, m, "medium", "mapping_partial"
        for alias in m.aliases:
            norm_alias = normalize_app_name(alias)
            if norm_alias in normalized or normalized in norm_alias:
                return m.category, m, "medium", "mapping_partial"

    # Tier 4: No match (unknown)
    return "unknown", None, "none", "default"


def categorize_app_simple(name: str) -> Tuple[str, Optional[AppMapping]]:
    """Backwards-compatible wrapper returning just (category, mapping)."""
    category, mapping, _, _ = categorize_app(name)
    return category, mapping


def get_category_description(category: str) -> str:
    """Get description for a category."""
    return CATEGORY_DEFINITIONS.get(category, "Unknown category")


def list_categories() -> List[str]:
    """List all valid categories."""
    return list(CATEGORY_DEFINITIONS.keys())


def list_apps_by_category(category: str) -> List[str]:
    """List all known apps in a category."""
    return [
        key for key, mapping in APP_MAPPINGS.items()
        if mapping.category == category
    ]


def get_all_known_apps() -> List[str]:
    """Get list of all known application names."""
    apps = list(APP_MAPPINGS.keys())
    # Also include aliases
    for mapping in APP_MAPPINGS.values():
        apps.extend(mapping.aliases)
    return sorted(set(apps))
