"""
Analysis Tools for IT Diligence Agents

These tools are used by Claude to record structured findings during analysis.
Each tool creates a specific type of output that feeds into the final report.

Updated for Four-Lens DD Framework:
- create_current_state_entry (Lens 1)
- identify_risk with integration_dependent flag (Lens 2)
- create_strategic_consideration (Lens 3)
- create_work_item with phase tagging (Lens 4)

Anti-Hallucination Features (v2.0):
- source_evidence required on key findings
- exact_quote validation
- confidence_level on all findings
- evidence_type classification
- Evidence density metrics
"""
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import json
from difflib import SequenceMatcher


# =============================================================================
# STANDARDIZED ENUMS
# =============================================================================

# All domains supported by the system
ALL_DOMAINS = [
    "infrastructure",
    "network",
    "cybersecurity",
    "applications",
    "organization",
    "identity_access",
    "cross-domain"
]

# Evidence types for anti-hallucination
EVIDENCE_TYPES = ["direct_statement", "logical_inference", "pattern_based"]

# Confidence levels
CONFIDENCE_LEVELS = ["high", "medium", "low"]

# Gap types for categorization
GAP_TYPES = ["missing_document", "incomplete_detail", "unclear_statement", "unstated_critical"]


# =============================================================================
# BUSINESS CAPABILITY FRAMEWORK (Phase 1: Steps 1-12)
# =============================================================================
# This framework ensures complete application coverage analysis by checking
# that all business capability areas are assessed, not just what's in documents.

# Step 2: Capability Areas Enum
CAPABILITY_AREAS = [
    "finance_accounting",
    "human_resources",
    "sales_crm",
    "marketing",
    "operations_supply_chain",
    "it_infrastructure",
    "identity_security",
    "collaboration",
    "data_analytics",
    "legal_compliance",
    "customer_service",
    "ecommerce_digital",
    "industry_specific"
]

# Steps 3-12: Complete Business Capability Checklist
# Each capability defines typical apps, criticality, and default follow-up questions
BUSINESS_CAPABILITY_CHECKLIST = {
    # Step 3: Finance & Accounting
    "finance_accounting": {
        "name": "Finance & Accounting",
        "description": "Core financial operations including general ledger, accounts payable/receivable, and financial reporting",
        "typical_apps": [
            "ERP / General Ledger",
            "Accounts Payable (AP) Automation",
            "Accounts Receivable (AR) / Billing",
            "Expense Management",
            "Fixed Assets Management",
            "Treasury / Cash Management",
            "Budgeting / FP&A",
            "Tax Management",
            "Consolidation / Close Management"
        ],
        "criticality": "Critical",
        "question_if_missing": "What system handles general ledger and financial reporting?",
        "common_vendors": ["SAP", "Oracle", "NetSuite", "Microsoft Dynamics", "Workday", "Sage", "QuickBooks"],
        "risk_if_absent": "Cannot operate as standalone entity without core financial systems"
    },

    # Step 4: Human Resources
    "human_resources": {
        "name": "Human Resources & Payroll",
        "description": "Employee lifecycle management from hire to retire, including payroll processing",
        "typical_apps": [
            "Core HRIS",
            "Payroll Processing",
            "Benefits Administration",
            "Recruiting / ATS",
            "Performance Management",
            "Learning Management (LMS)",
            "Time & Attendance",
            "Compensation Management",
            "Workforce Planning"
        ],
        "criticality": "Critical",
        "question_if_missing": "What system handles payroll and HR management?",
        "common_vendors": ["Workday", "ADP", "UKG", "SAP SuccessFactors", "Oracle HCM", "BambooHR", "Paylocity"],
        "risk_if_absent": "Payroll disruption is immediate Day 1 risk; compliance exposure"
    },

    # Step 5: Sales & CRM
    "sales_crm": {
        "name": "Sales & Customer Management",
        "description": "Customer relationship management, sales pipeline, and revenue operations",
        "typical_apps": [
            "CRM",
            "Sales Force Automation",
            "CPQ (Configure-Price-Quote)",
            "Sales Enablement",
            "Customer Portal",
            "Contract Management",
            "Revenue Intelligence",
            "Partner Relationship Management"
        ],
        "criticality": "High",
        "question_if_missing": "What system manages customer relationships and sales pipeline?",
        "common_vendors": ["Salesforce", "Microsoft Dynamics 365", "HubSpot", "Zoho", "Pipedrive", "SAP CRM"],
        "risk_if_absent": "Revenue visibility and customer data management at risk"
    },

    # Step 6: Marketing
    "marketing": {
        "name": "Marketing",
        "description": "Marketing operations, campaign management, and demand generation",
        "typical_apps": [
            "Marketing Automation",
            "Email Marketing",
            "CMS / Website Platform",
            "Marketing Analytics",
            "Social Media Management",
            "ABM Platform",
            "Content Management",
            "SEO / SEM Tools",
            "Event Management"
        ],
        "criticality": "Medium",
        "question_if_missing": "What systems support marketing operations and demand generation?",
        "common_vendors": ["HubSpot", "Marketo", "Pardot", "Mailchimp", "Adobe Experience Cloud", "WordPress"],
        "risk_if_absent": "Lead generation and brand continuity may be impacted"
    },

    # Step 7: Operations & Supply Chain
    "operations_supply_chain": {
        "name": "Operations & Supply Chain",
        "description": "Supply chain management, inventory, manufacturing, and logistics",
        "typical_apps": [
            "Supply Chain Management (SCM)",
            "Procurement / Sourcing",
            "Inventory Management",
            "Warehouse Management (WMS)",
            "Manufacturing Execution (MES)",
            "Quality Management (QMS)",
            "Product Lifecycle Management (PLM)",
            "Transportation Management (TMS)",
            "Demand Planning"
        ],
        "criticality": "High",
        "criticality_note": "Critical for manufacturing/distribution; may be N/A for services",
        "question_if_missing": "What systems manage supply chain, inventory, and operations?",
        "common_vendors": ["SAP", "Oracle SCM", "Blue Yonder", "Manhattan Associates", "Kinaxis", "Coupa"],
        "risk_if_absent": "Supply chain visibility and operational continuity at risk",
        "industry_relevance": ["Manufacturing", "Distribution", "Retail", "CPG"]
    },

    # Step 8: IT Infrastructure Management
    "it_infrastructure": {
        "name": "IT Service & Infrastructure Management",
        "description": "IT service delivery, infrastructure monitoring, and operational management",
        "typical_apps": [
            "ITSM / Service Desk",
            "Infrastructure Monitoring / APM",
            "CMDB / Asset Management",
            "Endpoint Management / MDM",
            "Patch Management",
            "Backup & Recovery",
            "Cloud Management Platform",
            "Network Management",
            "Log Management"
        ],
        "criticality": "High",
        "question_if_missing": "What system handles IT service requests and incident management?",
        "common_vendors": ["ServiceNow", "Jira Service Management", "BMC", "Freshservice", "SolarWinds", "Datadog"],
        "risk_if_absent": "IT operational visibility and service delivery at risk"
    },

    # Step 9: Identity & Security
    "identity_security": {
        "name": "Identity & Security",
        "description": "Identity management, access control, and security operations",
        "typical_apps": [
            "Identity Provider (IdP) / SSO",
            "Multi-Factor Authentication (MFA)",
            "Privileged Access Management (PAM)",
            "Identity Governance (IGA)",
            "SIEM / Security Monitoring",
            "Endpoint Detection & Response (EDR)",
            "Email Security Gateway",
            "Data Loss Prevention (DLP)",
            "Vulnerability Management",
            "Security Awareness Training"
        ],
        "criticality": "Critical",
        "question_if_missing": "What systems manage identity, access control, and security monitoring?",
        "common_vendors": ["Okta", "Microsoft Entra ID", "CyberArk", "SailPoint", "Splunk", "CrowdStrike", "Palo Alto"],
        "risk_if_absent": "Security posture and access control gaps create immediate risk"
    },

    # Step 10: Collaboration & Productivity
    "collaboration": {
        "name": "Collaboration & Productivity",
        "description": "Communication, document management, and team collaboration",
        "typical_apps": [
            "Email & Calendar",
            "Document Management / File Sharing",
            "Intranet / Employee Portal",
            "Video Conferencing",
            "Team Chat / Messaging",
            "Project Management",
            "Knowledge Management",
            "Digital Workplace Platform"
        ],
        "criticality": "High",
        "question_if_missing": "What collaboration suite is used (Microsoft 365, Google Workspace, etc.)?",
        "common_vendors": ["Microsoft 365", "Google Workspace", "Slack", "Zoom", "Atlassian", "Dropbox", "Box"],
        "risk_if_absent": "Day 1 communication and productivity disruption"
    },

    # Step 11a: Data & Analytics
    "data_analytics": {
        "name": "Data & Analytics",
        "description": "Business intelligence, data warehousing, and analytics platforms",
        "typical_apps": [
            "Business Intelligence / Reporting",
            "Data Warehouse / Data Lake",
            "ETL / Data Integration",
            "Master Data Management (MDM)",
            "Data Catalog / Governance",
            "Advanced Analytics / ML Platform",
            "Dashboard / Visualization"
        ],
        "criticality": "Medium-High",
        "question_if_missing": "What systems support business intelligence and reporting?",
        "common_vendors": ["Tableau", "Power BI", "Looker", "Snowflake", "Databricks", "Informatica", "Qlik"],
        "risk_if_absent": "Management reporting and data-driven decision making impacted"
    },

    # Step 11b: Legal & Compliance
    "legal_compliance": {
        "name": "Legal & Compliance",
        "description": "Contract management, compliance tracking, and legal operations",
        "typical_apps": [
            "Contract Lifecycle Management (CLM)",
            "GRC Platform",
            "Policy Management",
            "eDiscovery",
            "Audit Management",
            "Compliance Training",
            "Legal Matter Management",
            "IP Management"
        ],
        "criticality": "Medium",
        "question_if_missing": "What systems support contract management and compliance tracking?",
        "common_vendors": ["DocuSign CLM", "Ironclad", "ServiceNow GRC", "OneTrust", "Relativity", "Diligent"],
        "risk_if_absent": "Contract visibility and compliance tracking gaps"
    },

    # Step 11c: Customer Service
    "customer_service": {
        "name": "Customer Service & Support",
        "description": "Customer support, help desk, and service operations",
        "typical_apps": [
            "Help Desk / Ticketing",
            "Knowledge Base",
            "Live Chat / Chatbot",
            "Call Center / CCaaS",
            "Customer Success Platform",
            "Customer Feedback / NPS",
            "Field Service Management",
            "Self-Service Portal"
        ],
        "criticality": "High",
        "criticality_note": "Critical for B2C and B2B service businesses",
        "question_if_missing": "What systems handle customer support and service operations?",
        "common_vendors": ["Zendesk", "Salesforce Service Cloud", "Freshdesk", "ServiceNow CSM", "Intercom", "Genesys"],
        "risk_if_absent": "Customer service continuity and satisfaction at risk",
        "industry_relevance": ["B2C", "B2B Services", "SaaS", "Retail"]
    },

    # Step 11d: E-Commerce & Digital
    "ecommerce_digital": {
        "name": "E-Commerce & Digital",
        "description": "Online sales, digital commerce, and payment processing",
        "typical_apps": [
            "E-Commerce Platform",
            "Product Information Management (PIM)",
            "Order Management System (OMS)",
            "Payment Processing",
            "Fraud Detection",
            "Personalization Engine",
            "Digital Experience Platform (DXP)",
            "Subscription Management"
        ],
        "criticality": "Critical",
        "criticality_note": "Critical if e-commerce is primary revenue channel",
        "question_if_missing": "What platform handles e-commerce and online sales?",
        "common_vendors": ["Shopify", "Magento", "Salesforce Commerce", "SAP Commerce", "BigCommerce", "Stripe"],
        "risk_if_absent": "Revenue disruption if e-commerce is core channel",
        "industry_relevance": ["Retail", "D2C", "B2B E-commerce", "SaaS"]
    },

    # Step 11e: Industry-Specific
    "industry_specific": {
        "name": "Industry-Specific Applications",
        "description": "Vertical-specific applications unique to the target's industry",
        "typical_apps": [
            "Industry-specific ERP modules",
            "Vertical SaaS solutions",
            "Regulatory compliance systems",
            "Specialized operational systems",
            "Industry data/benchmarking platforms"
        ],
        "criticality": "Varies",
        "question_if_missing": "Are there industry-specific systems critical to operations?",
        "examples_by_industry": {
            "Healthcare": ["EHR/EMR", "Practice Management", "Medical Billing", "PACS"],
            "Financial Services": ["Core Banking", "Trading Platform", "Risk Management", "Regulatory Reporting"],
            "Manufacturing": ["MES", "SCADA", "PLM", "Quality Management"],
            "Real Estate": ["Property Management", "Lease Administration", "Construction Management"],
            "Legal": ["Legal Practice Management", "Document Management", "eDiscovery", "Billing"],
            "Education": ["Student Information System", "LMS", "Enrollment Management"]
        },
        "risk_if_absent": "Core business operations may depend on vertical solutions"
    }
}

# Convenience function to get capability by area
def get_capability_info(capability_area: str) -> Optional[Dict]:
    """Get capability checklist info for a specific area."""
    return BUSINESS_CAPABILITY_CHECKLIST.get(capability_area)

# Get all critical capabilities (must be assessed)
def get_critical_capabilities() -> List[str]:
    """Return list of capability areas marked as Critical."""
    return [
        area for area, info in BUSINESS_CAPABILITY_CHECKLIST.items()
        if info.get("criticality") == "Critical"
    ]

# Get default follow-up question for a capability
def get_default_question(capability_area: str) -> Optional[str]:
    """Get the default follow-up question for a capability area."""
    info = BUSINESS_CAPABILITY_CHECKLIST.get(capability_area)
    return info.get("question_if_missing") if info else None


# =============================================================================
# APPLICATION INVENTORY ENUMS (Phase 2: Steps 13-18)
# =============================================================================
# These enums support the record_application tool for structured app capture.

# Step 13: Application Categories
APPLICATION_CATEGORIES = [
    "ERP",
    "CRM",
    "HCM",
    "Finance",
    "BI_Analytics",
    "Collaboration",
    "Security",
    "IT_Operations",
    "Custom_Internal",
    "Industry_Vertical",
    "Integration_Middleware",
    "Infrastructure",
    "Development_DevOps",
    "Marketing",
    "Customer_Service",
    "Supply_Chain",
    "E_Commerce",
    "Other"
]

# Step 14: Hosting Models
HOSTING_MODELS = [
    "SaaS",
    "On_Premise",
    "IaaS_Cloud",
    "PaaS",
    "Hybrid",
    "Managed_Hosting",
    "Unknown"
]

# Step 15: Support Status
SUPPORT_STATUS = [
    "Fully_Supported",
    "Mainstream_Support",
    "Extended_Support",
    "End_of_Life",
    "End_of_Support",
    "Community_Only",
    "Unknown"
]

# Step 16: License Types
LICENSE_TYPES = [
    "Subscription_SaaS",
    "Subscription_Term",
    "Perpetual",
    "Open_Source",
    "Freemium",
    "Custom_Agreement",
    "Bundled",
    "Unknown"
]

# Step 17: Customization Levels
CUSTOMIZATION_LEVELS = [
    "Out_of_Box",
    "Configured",
    "Lightly_Customized",
    "Moderately_Customized",
    "Heavily_Customized",
    "Fully_Custom",
    "Unknown"
]

# Step 18: Discovery Sources (how the app was found)
DISCOVERY_SOURCES = [
    "App_Inventory_Document",
    "Architecture_Diagram",
    "Integration_Documentation",
    "Mentioned_In_Passing",
    "Inferred_From_Context",
    "Vendor_Contract",
    "Interview_Notes",
    "Other"
]

# Business Criticality (reused across tools)
BUSINESS_CRITICALITY = [
    "Critical",
    "High",
    "Medium",
    "Low",
    "Unknown"
]


# =============================================================================
# DATA CLASSIFICATION ENUMS (Phase 11: Data Classification Enhancement)
# =============================================================================
# These enums support structured data classification for compliance and risk assessment.

# PII Types - Personally Identifiable Information categories
PII_TYPES = [
    "Names",
    "Email_Addresses",
    "Phone_Numbers",
    "Physical_Addresses",
    "SSN_Tax_ID",
    "Date_of_Birth",
    "Driver_License",
    "Passport",
    "Financial_Account_Numbers",
    "Biometric_Data",
    "IP_Addresses",
    "Device_Identifiers",
    "Geolocation",
    "Employment_Records",
    "Education_Records",
    "Photos_Videos"
]

# PHI Types - Protected Health Information (HIPAA)
PHI_TYPES = [
    "Medical_Records",
    "Diagnosis_Codes",
    "Treatment_Information",
    "Prescription_Data",
    "Lab_Results",
    "Insurance_Information",
    "Provider_Information",
    "Mental_Health_Records",
    "Substance_Abuse_Records",
    "Genetic_Information"
]

# PCI Types - Payment Card Industry data
PCI_TYPES = [
    "Credit_Card_Numbers",
    "Debit_Card_Numbers",
    "CVV_CVC",
    "Cardholder_Name",
    "Expiration_Date",
    "PIN_Data",
    "Track_Data",
    "Service_Codes"
]

# Data Residency Locations
DATA_RESIDENCY_LOCATIONS = [
    "US",
    "EU",
    "UK",
    "Canada",
    "Australia",
    "Japan",
    "Singapore",
    "China",
    "India",
    "Brazil",
    "Multi_Region",
    "Unknown"
]


# =============================================================================
# BUYER COMPARISON ENUMS (Phase 12: Integration Analysis - Simplified)
# =============================================================================
# These enums support identifying overlaps between target and buyer environments.
# Focus is on WHAT overlaps exist and WHAT QUESTIONS this raises - not prescriptive decisions.
# Each deal is unique; the value is surfacing considerations, not dictating outcomes.

# Overlap Types - how does target app relate to buyer's landscape?
OVERLAP_TYPES = [
    "Same_Product",                    # Both have same vendor/product (e.g., both have Salesforce)
    "Same_Category_Different_Vendor",  # Same function, different vendors (e.g., Salesforce vs Dynamics)
    "Target_Only",                     # Target has app, buyer doesn't have equivalent
    "Complementary",                   # Different apps that serve different purposes
    "Unknown"                          # Need more info to determine
]

# Buyer Application Source - how do we know about buyer's apps?
BUYER_APP_SOURCE = [
    "Buyer_Questionnaire",       # From buyer-provided information
    "Prior_DD",                  # From previous due diligence
    "Known_Environment",         # Common knowledge about buyer
    "Assumption",                # Assumed based on buyer profile
    "Interview",                 # From discussions with buyer team
    "Public_Information",        # From public sources
    "Unknown"                    # Source not specified
]


# =============================================================================
# BUSINESS CONTEXT ENUMS (Phase 7-8: Business Context Profile)
# =============================================================================
# These enums support capturing the target company's business profile
# to inform capability relevance assessments.

# Industry Types
INDUSTRY_TYPES = [
    "Manufacturing",
    "Technology_Software",
    "Technology_Hardware",
    "Healthcare",
    "Financial_Services",
    "Insurance",
    "Retail",
    "E_Commerce",
    "Professional_Services",
    "Energy_Utilities",
    "Telecommunications",
    "Media_Entertainment",
    "Transportation_Logistics",
    "Real_Estate",
    "Construction",
    "Hospitality",
    "Education",
    "Government",
    "Nonprofit",
    "Agriculture",
    "Pharmaceuticals",
    "Other",
    "Unknown"
]

# Business Models
BUSINESS_MODELS = [
    "B2B",                      # Business to Business
    "B2C",                      # Business to Consumer
    "B2B2C",                    # Business to Business to Consumer
    "D2C",                      # Direct to Consumer
    "Marketplace",              # Platform connecting buyers/sellers
    "Subscription_SaaS",        # Recurring revenue SaaS
    "Subscription_Other",       # Non-SaaS recurring
    "Product_Sales",            # Physical or digital product sales
    "Professional_Services",    # Consulting, services
    "Licensing_Royalties",      # IP licensing
    "Franchise",                # Franchise model
    "Hybrid",                   # Multiple models
    "Unknown"
]

# Company Size Ranges (by employee count)
COMPANY_SIZE_RANGES = [
    "Small_Under_100",          # <100 employees
    "Medium_100_500",           # 100-500 employees
    "Large_500_2000",           # 500-2000 employees
    "Enterprise_2000_10000",    # 2000-10000 employees
    "Enterprise_Over_10000",    # >10000 employees
    "Unknown"
]

# Revenue Ranges
REVENUE_RANGES = [
    "Under_10M",
    "10M_50M",
    "50M_100M",
    "100M_500M",
    "500M_1B",
    "Over_1B",
    "Unknown"
]

# Geographic Presence
GEOGRAPHIC_PRESENCE = [
    "Single_Country",
    "Multi_Country_Single_Region",   # e.g., US + Canada
    "Multi_Region",                  # e.g., Americas + Europe
    "Global",
    "Unknown"
]

# Business Context Information Source
BUSINESS_CONTEXT_SOURCE = [
    "Public_Filings_SEC",       # SEC filings (10-K, 10-Q)
    "Company_Website",          # Public company info
    "Seller_Provided",          # From management/CIM
    "Prior_DD",                 # Previous due diligence
    "News_Research",            # Public news/research
    "Assumption",               # Assumed based on limited info
    "Unknown"
]


# =============================================================================
# EOL & TECHNICAL DEBT ENUMS (Phase 9-10: EOL Assessment)
# =============================================================================
# These enums support the EOL assessment and technical debt analysis tools.

# EOL Status - where is the product in its lifecycle?
EOL_STATUS = [
    "Current",                  # Latest or recent version, fully supported
    "Supported",                # Older but still in mainstream support
    "Extended_Support",         # Past mainstream, vendor offers extended support
    "Approaching_EOL",          # EOL within 24 months
    "Past_EOL",                 # Past end of life, no vendor support
    "Community_Only",           # No vendor support, community maintained
    "Unknown"
]

# Technical Debt Severity
TECHNICAL_DEBT_SEVERITY = [
    "Critical",                 # Must address immediately (security/compliance risk)
    "High",                     # Should address within 12 months
    "Medium",                   # Plan to address within 24 months
    "Low",                      # Nice to have, no immediate risk
    "Unknown"
]

# Technical Debt Categories
TECHNICAL_DEBT_CATEGORIES = [
    "Version_Debt",             # Outdated version, needs upgrade
    "Architecture_Debt",        # Poor architecture decisions
    "Code_Debt",                # Custom code quality issues
    "Documentation_Debt",       # Missing or outdated documentation
    "Skills_Debt",              # Scarce skills to maintain
    "Integration_Debt",         # Brittle or outdated integrations
    "Security_Debt",            # Security vulnerabilities/gaps
    "Compliance_Debt",          # Compliance gaps
    "Performance_Debt",         # Performance issues
    "Other"
]

# Modernization Urgency
MODERNIZATION_URGENCY = [
    "Immediate",                # Security/compliance requires immediate action
    "Near_Term_12_Months",      # Should modernize within 12 months
    "Medium_Term_24_Months",    # Can wait 12-24 months
    "Long_Term",                # No urgency, plan for future
    "Not_Required",             # No modernization needed
    "Unknown"
]

# EOL Reference Data - Known EOL dates for major enterprise software
# Format: "Vendor_Product_Version": {"eol_date": "YYYY-MM", "status": EOL_STATUS}
EOL_REFERENCE_DATA = {
    # SAP
    "SAP_ECC_6.0": {"eol_date": "2027-12", "status": "Approaching_EOL", "notes": "End of mainstream maintenance 2027"},
    "SAP_ECC_6.0_EHP7": {"eol_date": "2027-12", "status": "Approaching_EOL", "notes": "Enhancement pack 7"},
    "SAP_ECC_6.0_EHP8": {"eol_date": "2027-12", "status": "Approaching_EOL", "notes": "Enhancement pack 8"},
    "SAP_S4HANA_1909": {"eol_date": "2024-12", "status": "Past_EOL", "notes": "Past mainstream support"},
    "SAP_S4HANA_2020": {"eol_date": "2025-12", "status": "Approaching_EOL", "notes": "Mainstream ends 2025"},
    "SAP_S4HANA_2021": {"eol_date": "2026-12", "status": "Supported", "notes": "Current LTS"},
    "SAP_S4HANA_2023": {"eol_date": "2028-12", "status": "Current", "notes": "Latest release"},

    # Oracle
    "Oracle_EBS_12.1": {"eol_date": "2021-12", "status": "Past_EOL", "notes": "Extended support ended"},
    "Oracle_EBS_12.2": {"eol_date": "2031-12", "status": "Supported", "notes": "Premier support until 2031"},
    "Oracle_Database_11g": {"eol_date": "2020-12", "status": "Past_EOL", "notes": "Extended support ended"},
    "Oracle_Database_12c": {"eol_date": "2022-03", "status": "Past_EOL", "notes": "Extended support ended"},
    "Oracle_Database_19c": {"eol_date": "2027-04", "status": "Supported", "notes": "Long term support"},
    "Oracle_Database_21c": {"eol_date": "2024-04", "status": "Past_EOL", "notes": "Innovation release"},
    "Oracle_Database_23c": {"eol_date": "2028-04", "status": "Current", "notes": "Latest release"},

    # Microsoft Dynamics
    "Microsoft_Dynamics_AX_2012": {"eol_date": "2023-10", "status": "Past_EOL", "notes": "Extended support ended"},
    "Microsoft_Dynamics_GP": {"eol_date": "2028-04", "status": "Approaching_EOL", "notes": "Mainstream ended, extended until 2028"},
    "Microsoft_Dynamics_365_FO": {"eol_date": "N/A", "status": "Current", "notes": "Cloud, continuous updates"},
    "Microsoft_Dynamics_NAV_2018": {"eol_date": "2023-01", "status": "Past_EOL", "notes": "Migrated to Business Central"},

    # Microsoft Windows Server
    "Windows_Server_2012": {"eol_date": "2023-10", "status": "Past_EOL", "notes": "Extended support ended"},
    "Windows_Server_2012_R2": {"eol_date": "2023-10", "status": "Past_EOL", "notes": "Extended support ended"},
    "Windows_Server_2016": {"eol_date": "2027-01", "status": "Extended_Support", "notes": "Mainstream ended 2022"},
    "Windows_Server_2019": {"eol_date": "2029-01", "status": "Supported", "notes": "Mainstream until 2024"},
    "Windows_Server_2022": {"eol_date": "2031-10", "status": "Current", "notes": "Current LTS"},

    # Java
    "Java_8": {"eol_date": "2030-12", "status": "Extended_Support", "notes": "Oracle extended support, OpenJDK community"},
    "Java_11": {"eol_date": "2032-01", "status": "Supported", "notes": "LTS release"},
    "Java_17": {"eol_date": "2029-09", "status": "Current", "notes": "Current LTS"},
    "Java_21": {"eol_date": "2031-09", "status": "Current", "notes": "Latest LTS"},

    # .NET
    "DotNet_Framework_4.5": {"eol_date": "2022-04", "status": "Past_EOL", "notes": "Superseded"},
    "DotNet_Framework_4.6": {"eol_date": "2022-04", "status": "Past_EOL", "notes": "Superseded"},
    "DotNet_Framework_4.7": {"eol_date": "N/A", "status": "Supported", "notes": "Part of Windows support"},
    "DotNet_Framework_4.8": {"eol_date": "N/A", "status": "Current", "notes": "Final Framework version"},
    "DotNet_Core_3.1": {"eol_date": "2022-12", "status": "Past_EOL", "notes": "LTS ended"},
    "DotNet_6": {"eol_date": "2024-11", "status": "Approaching_EOL", "notes": "LTS ending soon"},
    "DotNet_7": {"eol_date": "2024-05", "status": "Past_EOL", "notes": "STS release"},
    "DotNet_8": {"eol_date": "2026-11", "status": "Current", "notes": "Current LTS"},

    # Python
    "Python_2.7": {"eol_date": "2020-01", "status": "Past_EOL", "notes": "Critical - security risk"},
    "Python_3.6": {"eol_date": "2021-12", "status": "Past_EOL", "notes": "No longer supported"},
    "Python_3.7": {"eol_date": "2023-06", "status": "Past_EOL", "notes": "No longer supported"},
    "Python_3.8": {"eol_date": "2024-10", "status": "Approaching_EOL", "notes": "Security fixes only"},
    "Python_3.9": {"eol_date": "2025-10", "status": "Supported", "notes": "Security fixes only"},
    "Python_3.10": {"eol_date": "2026-10", "status": "Supported", "notes": "Bug fixes"},
    "Python_3.11": {"eol_date": "2027-10", "status": "Current", "notes": "Active development"},
    "Python_3.12": {"eol_date": "2028-10", "status": "Current", "notes": "Latest stable"},

    # SQL Server
    "SQL_Server_2012": {"eol_date": "2022-07", "status": "Past_EOL", "notes": "Extended support ended"},
    "SQL_Server_2014": {"eol_date": "2024-07", "status": "Past_EOL", "notes": "Extended support ended"},
    "SQL_Server_2016": {"eol_date": "2026-07", "status": "Extended_Support", "notes": "Mainstream ended 2021"},
    "SQL_Server_2017": {"eol_date": "2027-10", "status": "Extended_Support", "notes": "Mainstream ended 2022"},
    "SQL_Server_2019": {"eol_date": "2030-01", "status": "Supported", "notes": "Current"},
    "SQL_Server_2022": {"eol_date": "2033-01", "status": "Current", "notes": "Latest release"},

    # VMware
    "VMware_vSphere_6.5": {"eol_date": "2022-10", "status": "Past_EOL", "notes": "General support ended"},
    "VMware_vSphere_6.7": {"eol_date": "2023-10", "status": "Past_EOL", "notes": "General support ended"},
    "VMware_vSphere_7.0": {"eol_date": "2025-04", "status": "Approaching_EOL", "notes": "General support ending"},
    "VMware_vSphere_8.0": {"eol_date": "2028-04", "status": "Current", "notes": "Latest release"},
}


def get_eol_info(product_key: str) -> Optional[Dict]:
    """
    Look up EOL information for a product.

    Args:
        product_key: Key in format "Vendor_Product_Version" (e.g., "SAP_ECC_6.0")

    Returns:
        Dict with eol_date, status, notes or None if not found
    """
    return EOL_REFERENCE_DATA.get(product_key)


def find_eol_matches(vendor: str, product: str, version: str = None) -> List[Dict]:
    """
    Find potential EOL matches for a vendor/product/version combination.

    Returns list of potential matches with their EOL info.
    """
    matches = []
    search_prefix = f"{vendor}_{product}".lower()

    for key, info in EOL_REFERENCE_DATA.items():
        if search_prefix in key.lower():
            match = {
                "key": key,
                "eol_date": info["eol_date"],
                "status": info["status"],
                "notes": info.get("notes", "")
            }
            # Boost exact version match
            if version and version.lower() in key.lower():
                match["confidence"] = "high"
            else:
                match["confidence"] = "medium"
            matches.append(match)

    return matches


# =============================================================================
# CAPABILITY COVERAGE ENUMS (Phase 3: Steps 26-28)
# =============================================================================
# These enums support the record_capability_coverage tool for business capability analysis.

# Step 26: Coverage Status - how well is this capability documented?
COVERAGE_STATUS = [
    "Fully_Documented",
    "Partially_Documented",
    "Mentioned_Not_Detailed",
    "Not_Found",
    "Not_Applicable",
    "Unknown"                    # Cannot determine from available docs
]

# Step 27: Business Relevance - how relevant is this capability to this business?
BUSINESS_RELEVANCE = [
    "Critical",
    "High",
    "Medium",
    "Low",
    "Not_Applicable",
    "Unknown"                    # Relevance cannot be determined
]

# Step 28: Question Targets - who should answer follow-up questions?
QUESTION_TARGETS = [
    "Target_Management",
    "Target_IT_Leadership",
    "Target_Finance",
    "Target_HR",
    "Target_Operations",
    "Buyer_IT",
    "Buyer_Integration_Team",
    "Deal_Team",
    "Legal",
    "External_Expert",
    "Vendor",
    "Unknown"                    # Target not specified
]

# Capability Maturity Levels
CAPABILITY_MATURITY = [
    "Nascent",       # Just starting, minimal capability
    "Developing",    # Building capability, significant gaps
    "Established",   # Functional capability, some optimization needed
    "Optimized",     # Mature, well-optimized capability
    "Unknown"        # Cannot assess from available information
]

# Integration Complexity
INTEGRATION_COMPLEXITY = [
    "Low",           # Few integrations, standard APIs
    "Medium",        # Moderate integrations, some custom work
    "High",          # Many integrations, significant custom work
    "Very_High",     # Complex web of integrations, major effort
    "Unknown"
]


# =============================================================================
# SOURCE EVIDENCE SCHEMA (reusable)
# =============================================================================

SOURCE_EVIDENCE_SCHEMA = {
    "type": "object",
    "description": "Evidence from the source document supporting this finding. REQUIRED for all findings.",
    "properties": {
        "exact_quote": {
            "type": "string",
            "description": "Verbatim text from the document (copy-paste, 10-500 chars). REQUIRED."
        },
        "source_section": {
            "type": "string",
            "description": "Section of document where evidence was found (e.g., 'Application Inventory', 'IT Organization')"
        },
        "evidence_type": {
            "type": "string",
            "enum": EVIDENCE_TYPES,
            "description": "direct_statement=explicitly stated, logical_inference=deduced from facts, pattern_based=recognized pattern (use sparingly)"
        },
        "confidence_level": {
            "type": "string",
            "enum": CONFIDENCE_LEVELS,
            "description": "high=certain/direct quote, medium=logical inference, low=pattern-based (consider flagging as gap)"
        }
    },
    "required": ["exact_quote", "evidence_type", "confidence_level"]
}


# =============================================================================
# VALIDATION FUNCTIONS
# =============================================================================

def validate_quote_exists(quote: str, document_text: str, threshold: float = 0.85) -> Tuple[bool, float]:
    """
    Validate that a quote exists in the source document.
    Uses fuzzy matching to handle minor OCR errors or formatting differences.

    Args:
        quote: The exact_quote from a finding
        document_text: The full source document text
        threshold: Minimum similarity ratio to consider a match (0.0-1.0)

    Returns:
        Tuple of (is_valid, best_match_score)
    """
    if not quote or not document_text:
        return False, 0.0

    quote_clean = quote.lower().strip()
    doc_clean = document_text.lower()

    # Quick check for exact substring match
    if quote_clean in doc_clean:
        return True, 1.0

    # Sliding window fuzzy match for longer quotes
    quote_len = len(quote_clean)
    if quote_len < 10:
        return False, 0.0

    best_score = 0.0
    window_size = min(quote_len + 50, len(doc_clean))  # Allow some flexibility

    # Sample positions to avoid O(n*m) complexity
    step = max(1, len(doc_clean) // 1000)
    for i in range(0, len(doc_clean) - quote_len, step):
        window = doc_clean[i:i + window_size]
        score = SequenceMatcher(None, quote_clean, window[:quote_len]).ratio()
        best_score = max(best_score, score)

        if best_score >= threshold:
            return True, best_score

    return best_score >= threshold, best_score


def calculate_evidence_density(findings_count: int, document_length: int) -> float:
    """
    Calculate findings per 1000 characters of source document.
    High density may indicate over-inference.

    Typical ranges:
    - < 0.5: Under-analyzed
    - 0.5 - 2.0: Normal range
    - > 2.0: May be over-inferring / hallucinating
    """
    if document_length == 0:
        return 0.0
    return (findings_count / document_length) * 1000


def assess_confidence_distribution(findings: List[Dict]) -> Dict[str, Any]:
    """
    Assess the distribution of confidence levels across findings.
    Flags suspicious patterns that may indicate hallucination.
    """
    if not findings:
        return {"status": "no_findings", "distribution": {}}

    distribution = {"high": 0, "medium": 0, "low": 0, "missing": 0}

    for finding in findings:
        # Check source_evidence.confidence_level or top-level confidence
        source_evidence = finding.get("source_evidence", {})
        confidence = source_evidence.get("confidence_level") or finding.get("confidence", "missing")

        if confidence in distribution:
            distribution[confidence] += 1
        else:
            distribution["missing"] += 1

    total = len(findings)
    percentages = {k: (v / total * 100) for k, v in distribution.items()}

    # Flag suspicious patterns
    warnings = []
    if percentages.get("high", 0) > 80:
        warnings.append("Over 80% high confidence - likely over-confident")
    if percentages.get("low", 0) > 30:
        warnings.append("Over 30% low confidence - consider converting to gaps")
    if percentages.get("missing", 0) > 10:
        warnings.append("Missing confidence levels on some findings")

    return {
        "status": "analyzed",
        "distribution": distribution,
        "percentages": percentages,
        "total_findings": total,
        "warnings": warnings
    }


# =============================================================================
# TOOL DEFINITIONS (for Anthropic API)
# =============================================================================

ANALYSIS_TOOLS = [
    # =========================================================================
    # APPLICATION INVENTORY TOOLS (Phase 2: Steps 19-25)
    # These tools capture individual applications in a structured format
    # =========================================================================
    {
        "name": "record_application",
        "description": """Record a SINGLE application in the structured inventory.

        CRITICAL USAGE RULES:
        1. Call this tool ONCE PER APPLICATION - enumerate ALL apps, never summarize
        2. If a document mentions "50 applications", you should have ~50 record_application calls
        3. Include apps mentioned in passing (e.g., "data from Workday" = record Workday)
        4. Record apps from ALL documents, not just app inventories

        HANDLING MISSING INFORMATION:
        - Use "Unknown" for enum fields when information is not available
        - For optional string fields, omit them or use null if not documented
        - Use fields_not_documented array to track which fields couldn't be populated
        - Example: fields_not_documented: ["version", "user_count", "license_type"]

        This tool creates a structured inventory with all fields needed for DD analysis:
        name, vendor, version, hosting, criticality, licensing, integrations, etc.

        IMPORTANT: Every recorded application MUST have source_evidence with exact_quote.""",
        "input_schema": {
            "type": "object",
            "properties": {
                # Step 19: Basic identification fields
                "application_name": {
                    "type": "string",
                    "description": "Official name of the application (e.g., 'SAP ECC', 'Salesforce Sales Cloud', 'Custom Inventory System')"
                },
                "application_category": {
                    "type": "string",
                    "enum": APPLICATION_CATEGORIES,
                    "description": "Primary category of the application"
                },
                "vendor": {
                    "type": "string",
                    "description": "Vendor/publisher (e.g., 'SAP', 'Salesforce', 'Microsoft', 'Internal/Custom')"
                },
                "description": {
                    "type": "string",
                    "description": "Brief description of what this application does and its business purpose"
                },

                # Step 20: Technical fields
                "version": {
                    "type": "string",
                    "description": "Version if known (e.g., '6.0 EHP7', 'Enterprise Edition', '2023.1', 'Unknown')"
                },
                "hosting_model": {
                    "type": "string",
                    "enum": HOSTING_MODELS,
                    "description": "Where/how is this application hosted?"
                },
                "support_status": {
                    "type": "string",
                    "enum": SUPPORT_STATUS,
                    "description": "Current vendor support status"
                },
                "deployment_date": {
                    "type": "string",
                    "description": "When deployed/implemented if known (e.g., '2018', 'Q3 2020', 'Unknown')"
                },
                "technology_stack": {
                    "type": "string",
                    "description": "Underlying technology if known (e.g., '.NET/SQL Server', 'Java/Oracle', 'Python/PostgreSQL')"
                },

                # Step 21: Business fields
                "user_count": {
                    "type": "string",
                    "description": "Number of users if known (e.g., '450', '50-100', 'All employees', 'Unknown')"
                },
                "business_criticality": {
                    "type": "string",
                    "enum": BUSINESS_CRITICALITY,
                    "description": "How critical is this to business operations?"
                },
                "business_owner": {
                    "type": "string",
                    "description": "Business owner/department if known (e.g., 'Finance', 'IT', 'Operations')"
                },
                "business_processes_supported": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Key business processes this app supports (e.g., ['Order to Cash', 'Financial Close', 'Payroll'])"
                },
                "capability_areas_covered": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": CAPABILITY_AREAS
                    },
                    "description": "Which business capability areas does this app cover?"
                },

                # Step 22: Contract/licensing fields
                "license_type": {
                    "type": "string",
                    "enum": LICENSE_TYPES,
                    "description": "Type of licensing model"
                },
                "contract_expiry": {
                    "type": "string",
                    "description": "Contract/subscription end date if known (e.g., '12/2025', 'Perpetual', 'Auto-renews annually', 'Unknown')"
                },
                "license_count": {
                    "type": "string",
                    "description": "Number of licenses if known (e.g., '500 named users', 'Unlimited', 'Unknown')"
                },
                "annual_cost_known": {
                    "type": "boolean",
                    "description": "Is the annual cost/spend known? (Note: actual cost handled by Costing Agent)"
                },

                # Step 23: Integration fields
                "integration_count": {
                    "type": "string",
                    "description": "Number of integrations if known (e.g., '15', '5-10', 'Heavy', 'Standalone', 'Unknown')"
                },
                "key_integrations": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Key systems this app integrates with (e.g., ['SAP ECC', 'Salesforce', 'Data Warehouse'])"
                },
                "customization_level": {
                    "type": "string",
                    "enum": CUSTOMIZATION_LEVELS,
                    "description": "Level of customization from out-of-box"
                },
                "custom_development_notes": {
                    "type": "string",
                    "description": "Notes on custom development if heavily customized (e.g., '143 custom ABAP programs')"
                },
                "api_availability": {
                    "type": "string",
                    "enum": ["Full_API", "Limited_API", "No_API", "Unknown"],
                    "description": "API availability for integration"
                },

                # Step 24: Provenance/evidence fields
                "discovery_source": {
                    "type": "string",
                    "enum": DISCOVERY_SOURCES,
                    "description": "How was this application discovered in the documents?"
                },
                "source_evidence": SOURCE_EVIDENCE_SCHEMA,
                "source_document_id": {
                    "type": "string",
                    "description": "ID of the source document where this app was found"
                },
                "source_page": {
                    "type": "integer",
                    "description": "Page number in source document"
                },

                # Step 25: Risk/notes fields
                "known_issues": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Known issues or risks specific to this application"
                },
                "notes": {
                    "type": "string",
                    "description": "Additional notes or observations about this application"
                },

                # Step 26: Data Classification fields (Phase 11 Enhancement - Simplified)
                "data_classification": {
                    "type": "object",
                    "description": "Data classification for compliance and risk assessment. Focus on: Does it have PII/PHI/PCI? Where does the data live?",
                    "properties": {
                        "contains_pii": {
                            "type": "boolean",
                            "description": "Does this application process Personally Identifiable Information?"
                        },
                        "pii_types": {
                            "type": "array",
                            "items": {
                                "type": "string",
                                "enum": PII_TYPES
                            },
                            "description": "Types of PII processed (e.g., Names, Email, SSN)"
                        },
                        "contains_phi": {
                            "type": "boolean",
                            "description": "Does this application process Protected Health Information (HIPAA)?"
                        },
                        "phi_types": {
                            "type": "array",
                            "items": {
                                "type": "string",
                                "enum": PHI_TYPES
                            },
                            "description": "Types of PHI processed (e.g., Medical_Records, Diagnosis_Codes)"
                        },
                        "contains_pci": {
                            "type": "boolean",
                            "description": "Does this application process Payment Card Industry data?"
                        },
                        "pci_types": {
                            "type": "array",
                            "items": {
                                "type": "string",
                                "enum": PCI_TYPES
                            },
                            "description": "Types of PCI data processed (e.g., Credit_Card_Numbers)"
                        },
                        "contains_financial": {
                            "type": "boolean",
                            "description": "Does this application process sensitive financial data (bank accounts, salary, etc.)?"
                        },
                        "data_residency": {
                            "type": "array",
                            "items": {
                                "type": "string",
                                "enum": DATA_RESIDENCY_LOCATIONS
                            },
                            "description": "Where is the data stored? (e.g., US, EU, Multi_Region)"
                        }
                    }
                },

                # Phase 2-3 Enhancement: Track fields not documented
                "fields_not_documented": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of field names that could not be populated from available documentation. Use this to track completeness. Example: ['version', 'user_count', 'license_type'] when these details are not in the docs."
                }
            },
            "required": [
                "application_name",
                "application_category",
                "vendor",
                "hosting_model",
                "business_criticality",
                "discovery_source",
                "source_evidence"
            ]
        }
    },

    # =========================================================================
    # CAPABILITY COVERAGE TOOL (Phase 3: Steps 29-38)
    # Maps applications to business capabilities and identifies gaps
    # =========================================================================
    {
        "name": "record_capability_coverage",
        "description": """Record the application coverage analysis for a SINGLE business capability area.

        CRITICAL USAGE RULES:
        1. Call this tool for EACH of the 12+ capability areas to ensure complete coverage analysis
        2. This is a CHECKLIST-DRIVEN approach - assess every area, even if "Not_Applicable"
        3. For areas where no apps were found, generate follow-up questions for the seller
        4. This ensures we identify EXPECTED apps that may be missing from documentation

        Capability Areas to Assess:
        - finance_accounting: ERP, GL, AP, AR, Expense, Treasury, FP&A
        - human_resources: HRIS, Payroll, Benefits, Recruiting, LMS
        - sales_crm: CRM, CPQ, Sales Enablement, Customer Portal
        - marketing: Marketing Automation, CMS, Analytics
        - operations_supply_chain: SCM, Inventory, WMS, MES (if applicable)
        - it_infrastructure: ITSM, Monitoring, CMDB, Endpoint Management
        - identity_security: IdP/SSO, PAM, SIEM, EDR
        - collaboration: Email, Chat, Video, Document Management
        - data_analytics: BI, Data Warehouse, ETL
        - legal_compliance: CLM, GRC, Policy Management
        - customer_service: Help Desk, Knowledge Base (if applicable)
        - ecommerce_digital: E-commerce Platform (if applicable)
        - industry_specific: Vertical-specific apps

        IMPORTANT: Every capability area needs a record, even if coverage_status is "Not_Applicable".""",
        "input_schema": {
            "type": "object",
            "properties": {
                # Step 29: Identification
                "capability_area": {
                    "type": "string",
                    "enum": CAPABILITY_AREAS,
                    "description": "Which business capability area is being assessed"
                },
                "coverage_status": {
                    "type": "string",
                    "enum": COVERAGE_STATUS,
                    "description": "How well is this capability covered in the documentation?"
                },
                "business_relevance": {
                    "type": "string",
                    "enum": BUSINESS_RELEVANCE,
                    "description": "How relevant/important is this capability to THIS specific business?"
                },
                "relevance_reasoning": {
                    "type": "string",
                    "description": "REQUIRED: Why is this capability relevant or not relevant? (e.g., 'Manufacturing company - SCM is critical', 'Services company - SCM not applicable')"
                },

                # Step 30: Applications found
                "applications_found": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "app_name": {
                                "type": "string",
                                "description": "Name of the application"
                            },
                            "app_id": {
                                "type": "string",
                                "description": "ID from record_application (e.g., 'APP-001') if recorded"
                            },
                            "discovery_source": {
                                "type": "string",
                                "enum": DISCOVERY_SOURCES,
                                "description": "How was this app discovered?"
                            },
                            "coverage_quality": {
                                "type": "string",
                                "enum": ["high", "medium", "low"],
                                "description": "How well does documentation cover this app?"
                            },
                            "function_within_capability": {
                                "type": "string",
                                "description": "What specific function does this app serve? (e.g., 'Core ERP/GL', 'Expense Management')"
                            }
                        },
                        "required": ["app_name", "coverage_quality"]
                    },
                    "description": "Applications found that cover this capability area"
                },

                # Step 31: Gaps - expected but missing
                "expected_but_missing": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Typical apps for this capability that were NOT found (e.g., 'Treasury Management', 'SIEM', 'LMS')"
                },
                "gap_severity": {
                    "type": "string",
                    "enum": ["critical", "high", "medium", "low", "none"],
                    "description": "How severe is the gap in coverage for this capability?"
                },
                "gap_reasoning": {
                    "type": "string",
                    "description": "Why are the missing apps a concern? What's the business impact?"
                },

                # Step 32: Follow-up questions
                "follow_up_questions": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "question": {
                                "type": "string",
                                "description": "The specific question to ask"
                            },
                            "priority": {
                                "type": "string",
                                "enum": ["critical", "high", "medium", "low"],
                                "description": "How urgent is this question?"
                            },
                            "target": {
                                "type": "string",
                                "enum": QUESTION_TARGETS,
                                "description": "Who should answer this question?"
                            },
                            "context": {
                                "type": "string",
                                "description": "Why does this question matter for the deal?"
                            }
                        },
                        "required": ["question", "priority", "target"]
                    },
                    "description": "REQUIRED if gaps exist: Follow-up questions for the seller/target"
                },

                # Step 33: Assessment
                "capability_maturity": {
                    "type": "string",
                    "enum": CAPABILITY_MATURITY,
                    "description": "Overall maturity of this capability area"
                },
                "standalone_viability": {
                    "type": "string",
                    "enum": ["viable", "constrained", "high_risk", "not_applicable"],
                    "description": "Could this capability operate independently post-transaction?"
                },
                "integration_complexity": {
                    "type": "string",
                    "enum": INTEGRATION_COMPLEXITY,
                    "description": "How complex would it be to integrate this capability with buyer?"
                },

                # Step 34: Evidence
                "assessment_basis": {
                    "type": "string",
                    "description": "What is this assessment based on? Summarize the evidence."
                },
                "documents_reviewed": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of document types/names reviewed for this capability"
                },
                "confidence_level": {
                    "type": "string",
                    "enum": CONFIDENCE_LEVELS,
                    "description": "How confident are you in this assessment?"
                },

                # Step 35-36: Additional context
                "buyer_overlap_notes": {
                    "type": "string",
                    "description": "If buyer info available: notes on overlap/synergy with buyer capabilities"
                },
                "rationalization_opportunity": {
                    "type": "string",
                    "enum": ["high", "medium", "low", "none", "unknown"],
                    "description": "Potential for application rationalization in this capability area"
                },
                "notes": {
                    "type": "string",
                    "description": "Additional observations about this capability area"
                }
            },
            "required": [
                "capability_area",
                "coverage_status",
                "business_relevance",
                "relevance_reasoning",
                "confidence_level"
            ]
        }
    },

    # =========================================================================
    # BUYER COMPARISON TOOLS (Phase 12: Integration Analysis - Simplified)
    # Focus: Identify overlaps and surface questions/considerations
    # NOT prescriptive decisions - each deal is unique
    # =========================================================================
    {
        "name": "record_buyer_application",
        "description": """Record a SINGLE application from the BUYER's environment.

        Use this to capture buyer's known application landscape for overlap comparison.
        Keep it simple - we just need to know what they have, not detailed specs.

        Sources for buyer apps:
        - Buyer questionnaire / profile
        - Prior due diligence on buyer
        - Known buyer environment
        - Assumptions based on buyer's industry/size

        IMPORTANT: Record each buyer app separately.""",
        "input_schema": {
            "type": "object",
            "properties": {
                "application_name": {
                    "type": "string",
                    "description": "Name of the buyer's application (e.g., 'Salesforce', 'SAP S/4HANA', 'Workday')"
                },
                "vendor": {
                    "type": "string",
                    "description": "Vendor/publisher (e.g., 'Salesforce', 'SAP', 'Microsoft')"
                },
                "application_category": {
                    "type": "string",
                    "enum": APPLICATION_CATEGORIES,
                    "description": "Primary category of the application"
                },
                "capability_areas_covered": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": CAPABILITY_AREAS
                    },
                    "description": "Which business capability areas does this app cover?"
                },
                "information_source": {
                    "type": "string",
                    "enum": BUYER_APP_SOURCE,
                    "description": "How do we know about this buyer application?"
                },
                "notes": {
                    "type": "string",
                    "description": "Any additional context about buyer's use of this app"
                }
            },
            "required": [
                "application_name",
                "vendor",
                "application_category",
                "capability_areas_covered",
                "information_source"
            ]
        }
    },
    {
        "name": "record_application_overlap",
        "description": """Record an overlap between a TARGET application and BUYER's environment.

        PURPOSE: Identify what overlaps exist and what questions/considerations this raises.
        NOT for prescribing specific integration decisions - each deal is unique.

        Focus on:
        1. WHAT overlap exists (same product, same category different vendor, unique to target)
        2. WHAT CONSIDERATIONS this raises for the deal team
        3. WHAT QUESTIONS need to be answered to understand integration implications

        Call this for significant target applications where overlap (or lack thereof) matters.""",
        "input_schema": {
            "type": "object",
            "properties": {
                # Target application reference
                "target_app_name": {
                    "type": "string",
                    "description": "Name of the target application"
                },
                "target_app_id": {
                    "type": "string",
                    "description": "ID from record_application (e.g., 'APP-001') if recorded"
                },
                "target_app_category": {
                    "type": "string",
                    "enum": APPLICATION_CATEGORIES,
                    "description": "Category of the target application"
                },

                # Buyer application reference (if overlap exists)
                "buyer_app_name": {
                    "type": "string",
                    "description": "Name of the buyer's comparable application (leave empty if Target_Only)"
                },
                "buyer_app_id": {
                    "type": "string",
                    "description": "ID from record_buyer_application (e.g., 'BAPP-001') if recorded"
                },

                # Overlap identification
                "overlap_type": {
                    "type": "string",
                    "enum": OVERLAP_TYPES,
                    "description": "Type of overlap: Same_Product, Same_Category_Different_Vendor, Target_Only, Complementary, Unknown"
                },

                # Considerations - free text, deal-specific
                "considerations": {
                    "type": "string",
                    "description": "REQUIRED: What does this overlap (or lack thereof) mean for the deal? What should the deal team be thinking about? Be specific to this situation."
                },

                # Questions to surface
                "follow_up_questions": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "question": {
                                "type": "string",
                                "description": "Specific question that needs answering"
                            },
                            "target": {
                                "type": "string",
                                "enum": QUESTION_TARGETS,
                                "description": "Who should answer this question?"
                            },
                            "why_it_matters": {
                                "type": "string",
                                "description": "Why is this question important for the deal?"
                            }
                        },
                        "required": ["question", "target"]
                    },
                    "description": "REQUIRED: Questions that need to be answered to understand integration implications"
                },

                "notes": {
                    "type": "string",
                    "description": "Additional observations"
                }
            },
            "required": [
                "target_app_name",
                "target_app_category",
                "overlap_type",
                "considerations",
                "follow_up_questions"
            ]
        }
    },

    # =========================================================================
    # BUSINESS CONTEXT TOOL (Phase 7-8: Business Context Profile)
    # Captures target company business profile to inform capability relevance
    # =========================================================================
    {
        "name": "record_business_context",
        "description": """Record the target company's business context and profile.

        PURPOSE: Capture key business characteristics that inform:
        - Which capabilities are critical vs optional for THIS business
        - What systems are expected given the industry and size
        - How to interpret gaps and relevance

        WHEN TO USE: Call this EARLY in the analysis, before capability coverage.
        Business context helps determine what's "expected_but_missing".

        SOURCES: Public filings (10-K), company website, seller-provided info (CIM),
        or informed assumptions based on deal context.

        NOTE: Only ONE business_context record per analysis. Update if needed.""",
        "input_schema": {
            "type": "object",
            "properties": {
                "company_name": {
                    "type": "string",
                    "description": "Target company name"
                },
                "industry": {
                    "type": "string",
                    "enum": INDUSTRY_TYPES,
                    "description": "Primary industry classification"
                },
                "industry_details": {
                    "type": "string",
                    "description": "Specific industry details (e.g., 'Medical device manufacturing', 'Enterprise SaaS for HR')"
                },
                "business_model": {
                    "type": "string",
                    "enum": BUSINESS_MODELS,
                    "description": "Primary business model"
                },
                "business_model_details": {
                    "type": "string",
                    "description": "Details on how they make money (e.g., 'Subscription revenue from SMB customers')"
                },
                "employee_count_range": {
                    "type": "string",
                    "enum": COMPANY_SIZE_RANGES,
                    "description": "Employee count range"
                },
                "employee_count_actual": {
                    "type": "string",
                    "description": "Actual employee count if known (e.g., '450', '~2000')"
                },
                "revenue_range": {
                    "type": "string",
                    "enum": REVENUE_RANGES,
                    "description": "Revenue range"
                },
                "geographic_presence": {
                    "type": "string",
                    "enum": GEOGRAPHIC_PRESENCE,
                    "description": "Geographic footprint"
                },
                "geographic_details": {
                    "type": "string",
                    "description": "Countries/regions of operation (e.g., 'US, Canada, UK, Germany')"
                },
                "key_business_processes": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Key business processes critical to operations (e.g., ['Manufacturing', 'Order fulfillment', 'Customer support'])"
                },
                "regulatory_requirements": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Key regulatory/compliance requirements (e.g., ['SOX', 'HIPAA', 'GDPR', 'PCI-DSS'])"
                },
                "is_public_company": {
                    "type": "boolean",
                    "description": "Is this a publicly traded company?"
                },
                "ticker_symbol": {
                    "type": "string",
                    "description": "Stock ticker if public (e.g., 'ACME')"
                },
                "information_source": {
                    "type": "string",
                    "enum": BUSINESS_CONTEXT_SOURCE,
                    "description": "Primary source of this information"
                },
                "source_evidence": SOURCE_EVIDENCE_SCHEMA,
                "notes": {
                    "type": "string",
                    "description": "Additional context about the business"
                }
            },
            "required": [
                "company_name",
                "industry",
                "business_model",
                "employee_count_range",
                "information_source"
            ]
        }
    },

    # =========================================================================
    # EOL & TECHNICAL DEBT TOOLS (Phase 9-10: Technical Maturity Assessment)
    # =========================================================================
    {
        "name": "assess_application_eol",
        "description": """Assess the end-of-life status for an application or technology component.

        PURPOSE: Record EOL assessment for version currency analysis. This helps identify:
        - Applications past end-of-life (security/support risk)
        - Applications approaching EOL (planning required)
        - Technology stack currency (Java, .NET, databases)

        WHEN TO USE: After recording applications, assess critical applications for EOL status.
        Reference EOL_REFERENCE_DATA for known dates, or record vendor-provided EOL info.

        NOTE: One assessment per application/version combination. Link to application_id if known.""",
        "input_schema": {
            "type": "object",
            "properties": {
                "application_name": {
                    "type": "string",
                    "description": "Name of the application or technology (e.g., 'SAP ECC', 'Oracle Database', 'Java')"
                },
                "application_id": {
                    "type": "string",
                    "description": "Link to recorded application ID (e.g., 'APP-001') if applicable"
                },
                "vendor": {
                    "type": "string",
                    "description": "Vendor name (e.g., 'SAP', 'Oracle', 'Microsoft')"
                },
                "current_version": {
                    "type": "string",
                    "description": "Current version in use (e.g., 'ECC 6.0 EHP8', '19c', '11')"
                },
                "eol_status": {
                    "type": "string",
                    "enum": EOL_STATUS,
                    "description": "Current EOL status"
                },
                "eol_date": {
                    "type": "string",
                    "description": "End-of-life date in YYYY-MM format (e.g., '2027-12') or 'N/A' for evergreen"
                },
                "eol_source": {
                    "type": "string",
                    "enum": ["EOL_Reference_Data", "Vendor_Documentation", "Seller_Provided", "Public_Source", "Assumption"],
                    "description": "Source of EOL information"
                },
                "latest_available_version": {
                    "type": "string",
                    "description": "Latest version available from vendor (e.g., 'S/4HANA 2023', '23c')"
                },
                "version_gap": {
                    "type": "string",
                    "enum": ["None", "Minor", "Major", "Critical"],
                    "description": "Gap between current and latest: None=current, Minor=1-2 versions, Major=3+ versions, Critical=past EOL"
                },
                "upgrade_path_available": {
                    "type": "boolean",
                    "description": "Is there a clear upgrade path from current version?"
                },
                "upgrade_path_notes": {
                    "type": "string",
                    "description": "Notes on upgrade path (e.g., 'Direct upgrade available', 'Migration to cloud required')"
                },
                "risk_if_not_upgraded": {
                    "type": "string",
                    "description": "Risk statement if not upgraded (e.g., 'No security patches after 2027', 'Compliance gap')"
                },
                "source_evidence": SOURCE_EVIDENCE_SCHEMA,
                "notes": {
                    "type": "string",
                    "description": "Additional notes on EOL assessment"
                }
            },
            "required": [
                "application_name",
                "vendor",
                "current_version",
                "eol_status",
                "eol_source"
            ]
        }
    },

    {
        "name": "assess_technical_debt",
        "description": """Record a technical debt assessment for an application or system.

        PURPOSE: Capture technical debt that requires remediation. Categories include:
        - Version Debt: Outdated versions needing upgrade
        - Architecture Debt: Poor design decisions
        - Integration Debt: Brittle integrations
        - Security/Compliance Debt: Gaps requiring attention

        WHEN TO USE: After reviewing applications for:
        - Heavy customizations making upgrades difficult
        - Outdated technology stacks
        - Missing documentation
        - Scarce support skills
        - Known technical issues

        NOTE: Can record multiple debt items per application.""",
        "input_schema": {
            "type": "object",
            "properties": {
                "application_name": {
                    "type": "string",
                    "description": "Name of the application or system"
                },
                "application_id": {
                    "type": "string",
                    "description": "Link to recorded application ID (e.g., 'APP-001') if applicable"
                },
                "debt_category": {
                    "type": "string",
                    "enum": TECHNICAL_DEBT_CATEGORIES,
                    "description": "Type of technical debt"
                },
                "debt_description": {
                    "type": "string",
                    "description": "Clear description of the technical debt (e.g., 'Heavy ABAP customizations to MM module')"
                },
                "severity": {
                    "type": "string",
                    "enum": TECHNICAL_DEBT_SEVERITY,
                    "description": "Severity of the debt"
                },
                "severity_reasoning": {
                    "type": "string",
                    "description": "Why this severity level? (e.g., 'Security risk due to past EOL', 'Blocking other upgrades')"
                },
                "business_impact": {
                    "type": "string",
                    "description": "Impact on business operations (e.g., 'Prevents ERP upgrade', 'Compliance gap')"
                },
                "modernization_urgency": {
                    "type": "string",
                    "enum": MODERNIZATION_URGENCY,
                    "description": "How urgently should this be addressed?"
                },
                "estimated_effort": {
                    "type": "string",
                    "enum": ["Low", "Medium", "High", "Very_High", "Unknown"],
                    "description": "Rough effort estimate for remediation"
                },
                "remediation_options": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Potential remediation approaches (e.g., ['Upgrade to S/4HANA', 'Migrate to cloud ERP', 'Retire and replace'])"
                },
                "dependencies": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Other systems/projects this debt depends on or blocks"
                },
                "eol_assessment_id": {
                    "type": "string",
                    "description": "Link to related EOL assessment (e.g., 'EOL-001') if applicable"
                },
                "source_evidence": SOURCE_EVIDENCE_SCHEMA,
                "notes": {
                    "type": "string",
                    "description": "Additional notes"
                }
            },
            "required": [
                "application_name",
                "debt_category",
                "debt_description",
                "severity",
                "modernization_urgency"
            ]
        }
    },

    # =========================================================================
    # LENS 1: CURRENT STATE ASSESSMENT
    # =========================================================================
    {
        "name": "create_current_state_entry",
        "description": """Record a current state observation about the IT environment.
        Use this in LENS 1 to document what exists TODAY, independent of any integration plans.
        Focus on MATURITY assessment, not just existence of tools/systems.

        IMPORTANT: You MUST provide source_evidence with an exact_quote from the document.""",
        "input_schema": {
            "type": "object",
            "properties": {
                "domain": {
                    "type": "string",
                    "enum": ALL_DOMAINS,
                    "description": "Which domain this observation relates to"
                },
                "category": {
                    "type": "string",
                    "description": "Specific area within domain (e.g., 'cloud_presence', 'wan_connectivity', 'iam_posture', 'compliance_certifications')"
                },
                "summary": {
                    "type": "string",
                    "description": "Plain-English description of what exists. Be specific - include numbers, versions, coverage percentages."
                },
                "maturity": {
                    "type": "string",
                    "enum": ["low", "medium", "high"],
                    "description": "Maturity level: low=basic/gaps, medium=functional/some gaps, high=robust/optimized"
                },
                "key_characteristics": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Notable attributes (e.g., ['Single cloud provider', 'No IaC adoption', '60% MFA coverage'])"
                },
                "standalone_viability": {
                    "type": "string",
                    "enum": ["viable", "constrained", "high_risk"],
                    "description": "Could this operate independently? viable=yes, constrained=challenges, high_risk=significant issues"
                },
                "source_document_id": {
                    "type": "string",
                    "description": "ID of the source document (for tracking provenance)"
                },
                "source_page": {
                    "type": "integer",
                    "description": "Page number in source document"
                },
                "source_evidence": SOURCE_EVIDENCE_SCHEMA
            },
            "required": ["domain", "category", "summary", "maturity", "standalone_viability", "source_evidence"]
        }
    },

    # =========================================================================
    # SUPPORTING TOOLS (used across lenses)
    # =========================================================================
    {
        "name": "log_assumption",
        "description": """Record an assumption made during analysis. Use this when you're making
        a judgment call based on available information. Every assumption should have clear reasoning
        about WHY you're making this assumption and what evidence supports it.

        IMPORTANT: Assumptions require supporting evidence. If you have no evidence, flag as gap instead.""",
        "input_schema": {
            "type": "object",
            "properties": {
                "assumption": {
                    "type": "string",
                    "description": "The assumption being made (e.g., 'SAP ECC migration to S/4HANA will be required')"
                },
                "basis": {
                    "type": "string",
                    "description": "Evidence or reasoning supporting this assumption"
                },
                "domain": {
                    "type": "string",
                    "enum": ALL_DOMAINS,
                    "description": "Which domain this assumption relates to"
                },
                "confidence": {
                    "type": "string",
                    "enum": CONFIDENCE_LEVELS,
                    "description": "Confidence level in this assumption"
                },
                "impact": {
                    "type": "string",
                    "enum": ["high", "medium", "low"],
                    "description": "Impact if this assumption is wrong"
                },
                "validation_needed": {
                    "type": "string",
                    "description": "What would need to be verified to confirm this assumption"
                },
                "supporting_quote": {
                    "type": "string",
                    "description": "Direct quote from document that supports this assumption (if available)"
                },
                "source_document_id": {
                    "type": "string",
                    "description": "ID of the source document"
                },
                "source_section": {
                    "type": "string",
                    "description": "Section of document where assumption is based"
                }
            },
            "required": ["assumption", "basis", "domain", "confidence", "impact", "validation_needed"]
        }
    },
    {
        "name": "flag_gap",
        "description": """Flag a knowledge gap - information that is missing or unclear and needs
        to be obtained. Gaps should be specific and actionable - what exactly do we need to know?

        IMPORTANT: Prefer flagging gaps over making low-confidence findings. Gaps are valuable.""",
        "input_schema": {
            "type": "object",
            "properties": {
                "gap": {
                    "type": "string",
                    "description": "What information is missing (e.g., 'Number of customizations in SAP ECC')"
                },
                "why_needed": {
                    "type": "string",
                    "description": "Why this information matters for the deal"
                },
                "domain": {
                    "type": "string",
                    "enum": ALL_DOMAINS,
                    "description": "Which domain this gap relates to"
                },
                "priority": {
                    "type": "string",
                    "enum": ["critical", "high", "medium", "low"],
                    "description": "How urgently this gap needs to be filled"
                },
                "gap_type": {
                    "type": "string",
                    "enum": GAP_TYPES,
                    "description": "missing_document=doc should exist, incomplete_detail=topic mentioned but sparse, unclear_statement=ambiguous info, unstated_critical=critical info completely absent"
                },
                "suggested_source": {
                    "type": "string",
                    "description": "Suggested way to obtain this information (document request, interview, technical assessment)"
                },
                # Step 63: cost_impact REMOVED - cost estimation handled by Costing Agent
                "source_document_id": {
                    "type": "string",
                    "description": "ID of the source document where this gap was identified"
                },
                "source_section": {
                    "type": "string",
                    "description": "Section of document where gap was identified"
                }
            },
            "required": ["gap", "why_needed", "domain", "priority", "gap_type", "suggested_source"]
        }
    },
    {
        "name": "flag_question",
        "description": """Flag a question that needs to be asked to management/seller during follow-up.
        Use when you identify specific questions that need answers to complete the assessment.

        IMPORTANT: Questions should be specific and actionable. Include context about why the question matters.""",
        "input_schema": {
            "type": "object",
            "properties": {
                "question": {
                    "type": "string",
                    "description": "The specific question to ask (e.g., 'What is the current cyber insurance coverage limit?')"
                },
                "context": {
                    "type": "string",
                    "description": "Why this question is important / what decision it impacts"
                },
                "domain": {
                    "type": "string",
                    "enum": ALL_DOMAINS,
                    "description": "Which domain this question relates to"
                },
                "priority": {
                    "type": "string",
                    "enum": ["critical", "high", "medium", "low"],
                    "description": "How urgently this needs to be answered"
                },
                "related_gap_id": {
                    "type": "string",
                    "description": "If this question relates to a specific gap, provide the gap ID (e.g., 'G-001')"
                },
                "suggested_source": {
                    "type": "string",
                    "description": "Suggested person/role to ask (e.g., 'CTO', 'IT Director', 'CFO')"
                }
            },
            "required": ["question", "context", "domain", "priority"]
        }
    },

    # =========================================================================
    # LENS 2: RISK IDENTIFICATION (Enhanced with Anti-Hallucination)
    # =========================================================================
    {
        "name": "identify_risk",
        "description": """Identify a risk that could impact the deal, integration, or operations.

        CRITICAL REQUIREMENTS:
        1. You MUST provide source_evidence with an exact_quote from the document
        2. Flag whether this risk exists independent of integration (integration_dependent: false)
           or only because of integration plans (integration_dependent: true)
        3. If you cannot provide evidence, flag as gap instead of creating a risk

        DO NOT create risks based on pattern recognition alone. Every risk must be grounded in the document.""",
        "input_schema": {
            "type": "object",
            "properties": {
                "risk": {
                    "type": "string",
                    "description": "Description of the risk"
                },
                "trigger": {
                    "type": "string",
                    "description": "What would cause this risk to materialize"
                },
                "domain": {
                    "type": "string",
                    "enum": ALL_DOMAINS,
                    "description": "Which domain this risk relates to"
                },
                "severity": {
                    "type": "string",
                    "enum": ["critical", "high", "medium", "low"],
                    "description": "Severity if the risk materializes"
                },
                "likelihood": {
                    "type": "string",
                    "enum": ["high", "medium", "low"],
                    "description": "Probability of this risk occurring"
                },
                "risk_type": {
                    "type": "string",
                    "enum": ["technical_debt", "security", "vendor", "organization", "scalability", "compliance", "integration"],
                    "description": "Category of risk"
                },
                "integration_dependent": {
                    "type": "boolean",
                    "description": "Does this risk ONLY exist because of integration? false=standalone risk, true=integration-specific"
                },
                "standalone_exposure": {
                    "type": "string",
                    "description": "If integration_dependent is false, describe the exposure if target operates independently"
                },
                "deal_impact": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": ["value_leakage", "execution_risk", "dependency", "timeline_risk", "cost_exposure", "tsa_dependency"]
                    },
                    "description": "How this risk affects the deal"
                },
                "impact_description": {
                    "type": "string",
                    "description": "What happens if this risk materializes (cost, timeline, operations)"
                },
                "mitigation": {
                    "type": "string",
                    "description": "Recommended actions to reduce or eliminate this risk"
                },
                # Step 62: cost_impact_estimate REMOVED - cost estimation handled by Costing Agent
                "source_document_id": {
                    "type": "string",
                    "description": "ID of the source document"
                },
                "source_page": {
                    "type": "integer",
                    "description": "Page number in source document"
                },
                "source_evidence": SOURCE_EVIDENCE_SCHEMA
            },
            "required": ["risk", "trigger", "domain", "severity", "likelihood", "risk_type", "integration_dependent", "mitigation", "source_evidence"]
        }
    },

    # =========================================================================
    # LENS 3: STRATEGIC CONSIDERATIONS
    # =========================================================================
    {
        "name": "create_strategic_consideration",
        "description": """Record a strategic consideration - a deal-relevant insight that informs
        negotiation, structure, or planning. This is deal LOGIC, not deal MATH.

        IMPORTANT (Phase 5 Enhancement):
        1. The observation must be grounded in document evidence - provide source_evidence
        2. Every strategic consideration MUST include a follow_up_question
        3. The question should be specific, actionable, and assigned to a target

        Strategic considerations without follow-up questions are not actionable for the deal team.""",
        "input_schema": {
            "type": "object",
            "properties": {
                "theme": {
                    "type": "string",
                    "description": "Short theme name (e.g., 'Cloud Platform Mismatch', 'Key Person Dependency')"
                },
                "observation": {
                    "type": "string",
                    "description": "Neutral statement of fact (what IS, not what should be)"
                },
                "implication": {
                    "type": "string",
                    "description": "What this means for the deal - the 'so what'"
                },
                "deal_relevance": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": ["integration_risk", "value_leakage", "tsa_dependency", "execution_risk", "synergy_barrier"]
                    },
                    "description": "How this affects the deal"
                },
                "buyer_alignment": {
                    "type": "string",
                    "enum": ["aligned", "partial", "misaligned", "unknown"],
                    "description": "How well target approach aligns with buyer standards"
                },
                "domain": {
                    "type": "string",
                    "enum": ALL_DOMAINS,
                    "description": "Which domain this relates to"
                },

                # ============================================================
                # FOLLOW-UP QUESTION FIELDS (Phase 5: Steps 52-56)
                # ============================================================
                "follow_up_question": {
                    "type": "string",
                    "description": "REQUIRED: What specific question does this consideration raise for the deal team? (e.g., 'What is buyer's position on S/4HANA migration?', 'Can seller confirm the CTO transition timeline?')"
                },
                "question_priority": {
                    "type": "string",
                    "enum": ["critical", "high", "medium", "low"],
                    "description": "How urgent is this follow-up question?"
                },
                "question_target": {
                    "type": "string",
                    "enum": QUESTION_TARGETS,
                    "description": "REQUIRED: Who should answer this question?"
                },
                "question_context": {
                    "type": "string",
                    "description": "Additional context for why this question matters and what decision it informs"
                },

                "source_document_id": {
                    "type": "string",
                    "description": "ID of the source document"
                },
                "source_evidence": SOURCE_EVIDENCE_SCHEMA
            },
            "required": [
                "theme", "observation", "implication", "deal_relevance", "buyer_alignment",
                "domain", "source_evidence",
                "follow_up_question", "question_target"  # Phase 5: New required fields
            ]
        }
    },

    # =========================================================================
    # LENS 4: INTEGRATION ACTIONS (Enhanced with phases)
    # =========================================================================
    {
        "name": "create_work_item",
        "description": """Create a work item - a specific task or work package needed for integration.
        Work items should be concrete, estimable, and MUST be tagged with a phase.

        IMPORTANT: Work items should be linked to identified risks or gaps that drive them.""",
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Short title for the work item"
                },
                "description": {
                    "type": "string",
                    "description": "Detailed description of the work required"
                },
                "domain": {
                    "type": "string",
                    "enum": ALL_DOMAINS,
                    "description": "Which domain this work item belongs to"
                },
                "category": {
                    "type": "string",
                    "enum": ["migration", "integration", "remediation", "assessment", "decommission", "security", "compliance"],
                    "description": "Type of work"
                },
                "phase": {
                    "type": "string",
                    "enum": ["Day_1", "Day_100", "Post_100", "Optional"],
                    "description": "When this work should occur: Day_1=business continuity must-haves, Day_100=stabilization/quick wins, Post_100=full integration, Optional=nice-to-have"
                },
                "phase_rationale": {
                    "type": "string",
                    "description": "Why this timing - what drives the phase assignment"
                },
                "effort_estimate": {
                    "type": "string",
                    "description": "Estimated effort (e.g., '2-4 weeks', '200-400 hours')"
                },
                "cost_estimate_range": {
                    "type": "string",
                    "description": "Estimated cost range (e.g., '$50K-$100K')"
                },
                "depends_on": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Work item IDs this depends on (e.g., ['WI-001', 'WI-003'])"
                },
                "skills_required": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Skills/roles needed (e.g., ['cloud_engineer', 'dba'])"
                },
                "triggered_by": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Risk or gap IDs that drive this work item (e.g., ['R-001', 'G-003'])"
                },
                "source_document_id": {
                    "type": "string",
                    "description": "ID of the source document that informed this work item"
                }
            },
            "required": ["title", "description", "domain", "category", "phase", "phase_rationale", "effort_estimate"]
        }
    },
    {
        "name": "create_recommendation",
        "description": """Create a strategic recommendation for the deal team. Recommendations
        should be actionable and clearly tied to findings.

        IMPORTANT: Link recommendations to specific risks, gaps, or findings that drive them.""",
        "input_schema": {
            "type": "object",
            "properties": {
                "recommendation": {
                    "type": "string",
                    "description": "The recommendation"
                },
                "rationale": {
                    "type": "string",
                    "description": "Why this is recommended based on findings"
                },
                "domain": {
                    "type": "string",
                    "enum": ALL_DOMAINS + ["deal"],
                    "description": "Which domain this recommendation relates to"
                },
                "priority": {
                    "type": "string",
                    "enum": ["critical", "high", "medium", "low"],
                    "description": "Priority level"
                },
                "timing": {
                    "type": "string",
                    "enum": ["pre_close", "day_1", "first_90_days", "ongoing"],
                    "description": "When to act on this recommendation"
                },
                "investment_required": {
                    "type": "string",
                    "description": "Resources or investment needed"
                },
                "driven_by": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Finding IDs that drive this recommendation (e.g., ['R-001', 'R-005', 'G-003'])"
                },
                "source_document_id": {
                    "type": "string",
                    "description": "ID of the source document that informed this recommendation"
                }
            },
            "required": ["recommendation", "rationale", "domain", "priority", "timing"]
        }
    },
    {
        "name": "complete_analysis",
        "description": """Signal that domain analysis is complete and provide a summary.
        Use this as the final tool call for a domain.

        IMPORTANT: Include evidence quality metrics in your summary.""",
        "input_schema": {
            "type": "object",
            "properties": {
                "domain": {
                    "type": "string",
                    "enum": ALL_DOMAINS,
                    "description": "Which domain analysis is complete"
                },
                "summary": {
                    "type": "string",
                    "description": "Brief summary of key findings (2-3 sentences)"
                },
                "complexity_assessment": {
                    "type": "string",
                    "enum": ["low", "medium", "high", "very_high"],
                    "description": "Overall complexity for this domain"
                },
                "estimated_cost_range": {
                    "type": "string",
                    "description": "Total estimated cost range for this domain (e.g., '$500K-$1.5M')"
                },
                "estimated_timeline": {
                    "type": "string",
                    "description": "Estimated timeline for this domain's work (e.g., '12-18 months')"
                },
                "top_risks": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Top 3 risks for this domain (by risk ID)"
                },
                "critical_gaps": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Most critical information gaps (by gap ID)"
                },
                "evidence_quality": {
                    "type": "object",
                    "description": "Self-assessment of evidence quality",
                    "properties": {
                        "high_confidence_findings": {"type": "integer"},
                        "medium_confidence_findings": {"type": "integer"},
                        "low_confidence_findings": {"type": "integer"},
                        "gaps_flagged": {"type": "integer"}
                    }
                }
            },
            "required": ["domain", "summary", "complexity_assessment", "top_risks", "critical_gaps"]
        }
    }
]


# =============================================================================
# ANALYSIS STORE (collects tool outputs)
# =============================================================================

@dataclass
class AnalysisStore:
    """
    Stores all findings from analysis agents.

    Updated for Four-Lens DD Framework with:
    - current_state entries (Lens 1)
    - strategic_considerations (Lens 3)
    - Enhanced risk schema with integration_dependent flag
    - Enhanced work items with phase tagging
    - DD completeness validation

    Phase 3 Updates (Points 47-52 of 115PP):
    - Database connection support
    - save_to_database() for persisting findings
    - load_from_database() for resuming analysis
    - get_analysis_history() for viewing past runs
    - run_id and document_id tracking
    """

    # ==========================================================================
    # APPLICATION INVENTORY (Phase 4: Steps 39-40)
    # ==========================================================================
    # Step 39: Application inventory from record_application tool
    applications: List[Dict] = field(default_factory=list)

    # Step 40: Capability coverage from record_capability_coverage tool
    capability_coverage: List[Dict] = field(default_factory=list)

    # ==========================================================================
    # BUYER COMPARISON (Phase 12: Integration Analysis)
    # ==========================================================================
    # Buyer's application landscape for overlap analysis
    buyer_applications: List[Dict] = field(default_factory=list)

    # Target vs Buyer overlap analysis
    application_overlaps: List[Dict] = field(default_factory=list)

    # ==========================================================================
    # BUSINESS CONTEXT (Phase 7-8: Business Context Profile)
    # ==========================================================================
    # Target company business profile - informs capability relevance
    business_context: Optional[Dict] = None

    # ==========================================================================
    # EOL & TECHNICAL DEBT (Phase 9-10: Technical Maturity Assessment)
    # ==========================================================================
    # EOL assessments for applications and technology components
    eol_assessments: List[Dict] = field(default_factory=list)

    # Technical debt assessments
    technical_debt_assessments: List[Dict] = field(default_factory=list)

    # ==========================================================================
    # FOUR-LENS FRAMEWORK
    # ==========================================================================
    # Lens 1: Current State
    current_state: List[Dict] = field(default_factory=list)

    # Lens 2: Risks (enhanced)
    risks: List[Dict] = field(default_factory=list)

    # Lens 3: Strategic Considerations
    strategic_considerations: List[Dict] = field(default_factory=list)

    # Lens 4: Integration Actions
    work_items: List[Dict] = field(default_factory=list)
    recommendations: List[Dict] = field(default_factory=list)

    # Supporting
    assumptions: List[Dict] = field(default_factory=list)
    gaps: List[Dict] = field(default_factory=list)
    questions: List[Dict] = field(default_factory=list)  # Questions for follow-up
    domain_summaries: Dict[str, Dict] = field(default_factory=dict)

    # Reasoning chain - stores the logic flow from observation to finding
    reasoning_chains: Dict[str, List[Dict]] = field(default_factory=dict)

    # Executive summary (generated by coordinator)
    executive_summary: Optional[Dict] = None

    # Point 51-52: Analysis run and document tracking
    run_id: Optional[str] = None
    document_ids: List[str] = field(default_factory=list)

    # Point 47: Database connection (injected) - use field() for proper dataclass handling
    _db: Any = field(default=None, init=False, repr=False)
    _repository: Any = field(default=None, init=False, repr=False)

    # Step 41: Updated ID counters with application and capability types
    _id_counters: Dict[str, int] = field(default_factory=lambda: {
        "assumption": 0, "gap": 0, "question": 0, "risk": 0, "work_item": 0,
        "recommendation": 0, "current_state": 0, "strategic_consideration": 0,
        "application": 0, "capability": 0,  # Phase 4 additions
        "buyer_application": 0, "overlap": 0,  # Phase 12: Buyer comparison
        "eol_assessment": 0, "technical_debt": 0  # Phase 9-10: EOL & Technical Debt
    })

    def _next_id(self, type_: str) -> str:
        """Generate sequential ID for a finding type"""
        prefix = {
            "assumption": "A",
            "gap": "G",
            "question": "Q",
            "risk": "R",
            "work_item": "WI",
            "recommendation": "REC",
            "current_state": "CS",
            "strategic_consideration": "SC",
            # Phase 4: New prefixes for application inventory
            "application": "APP",
            "capability": "CAP",
            # Phase 12: Buyer comparison prefixes
            "buyer_application": "BAPP",
            "overlap": "OVL",
            # Phase 9-10: EOL & Technical Debt prefixes
            "eol_assessment": "EOL",
            "technical_debt": "TD"
        }
        self._id_counters[type_] += 1
        return f"{prefix[type_]}-{self._id_counters[type_]:03d}"

    def _check_duplicate(self, tool_name: str, tool_input: Dict, threshold: float = 0.85) -> Optional[Dict]:
        """Check if finding is duplicate of existing one"""
        finding_map = {
            "log_assumption": ("assumptions", "assumption"),
            "identify_risk": ("risks", "risk"),
            "flag_gap": ("gaps", "gap"),
            "flag_question": ("questions", "question"),
            "create_current_state_entry": ("current_state", "summary"),
            "create_strategic_consideration": ("strategic_considerations", "theme")
        }

        if tool_name not in finding_map:
            return None

        collection_name, key_field = finding_map[tool_name]
        existing = getattr(self, collection_name)

        # Check same domain first
        domain = tool_input.get("domain")
        domain_findings = [f for f in existing if f.get("domain") == domain]

        new_text = tool_input.get(key_field, "").lower().strip()
        if not new_text:
            return None

        # Check similarity
        for existing_item in domain_findings:
            existing_text = existing_item.get(key_field, "").lower().strip()
            if not existing_text:
                continue

            similarity = SequenceMatcher(None, new_text, existing_text).ratio()
            if similarity > threshold:
                return existing_item

        return None

    def execute_tool(self, tool_name: str, tool_input: Dict) -> Dict:
        """
        Execute a tool and store the result.
        Includes duplicate detection and default value handling.
        """
        # Validate tool_input is a dict (Claude may sometimes send malformed input)
        if not isinstance(tool_input, dict):
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Invalid tool_input type for {tool_name}: expected dict, got {type(tool_input).__name__}. Value: {str(tool_input)[:200]}")
            return {
                "status": "error",
                "message": f"Invalid tool input: expected dict, got {type(tool_input).__name__}",
                "tool_name": tool_name
            }

        timestamp = datetime.now().isoformat()

        # Check for duplicates before adding
        duplicate = self._check_duplicate(tool_name, tool_input)
        if duplicate:
            return {
                "status": "duplicate",
                "id": duplicate["id"],
                "message": f"Similar finding already exists: {duplicate['id']}",
                "type": tool_name.replace("create_", "").replace("log_", "").replace("identify_", "").replace("flag_", "")
            }

        # =====================================================================
        # APPLICATION INVENTORY TOOLS (Phase 4: Steps 42-46)
        # =====================================================================

        # Step 42-43: Record Application
        if tool_name == "record_application":
            # Check for duplicate application by name + vendor
            app_name = tool_input.get("application_name", "").lower().strip()
            vendor = tool_input.get("vendor", "").lower().strip()

            for existing in self.applications:
                existing_name = existing.get("application_name", "").lower().strip()
                existing_vendor = existing.get("vendor", "").lower().strip()
                # Check exact match or high similarity
                if existing_name == app_name and existing_vendor == vendor:
                    return {
                        "status": "duplicate",
                        "id": existing["id"],
                        "message": f"Application already recorded: {existing['application_name']} ({existing['vendor']})",
                        "type": "application"
                    }

            finding = {
                "id": self._next_id("application"),
                "timestamp": timestamp,
                **tool_input
            }
            # Add defaults
            if "capability_areas_covered" not in finding:
                finding["capability_areas_covered"] = []
            if "key_integrations" not in finding:
                finding["key_integrations"] = []
            if "business_processes_supported" not in finding:
                finding["business_processes_supported"] = []
            if "known_issues" not in finding:
                finding["known_issues"] = []
            # Phase 2-3: Track fields that weren't documented
            if "fields_not_documented" not in finding:
                finding["fields_not_documented"] = []

            self.applications.append(finding)
            return {
                "status": "recorded",
                "id": finding["id"],
                "type": "application",
                "message": f"Application recorded: {finding['application_name']}"
            }

        # Step 44-45: Record Capability Coverage
        elif tool_name == "record_capability_coverage":
            capability_area = tool_input.get("capability_area", "")

            # Check if this capability area already recorded (only one per area)
            for existing in self.capability_coverage:
                if existing.get("capability_area") == capability_area:
                    return {
                        "status": "duplicate",
                        "id": existing["id"],
                        "message": f"Capability area already assessed: {capability_area}. Update the existing entry instead.",
                        "type": "capability"
                    }

            finding = {
                "id": self._next_id("capability"),
                "timestamp": timestamp,
                **tool_input
            }
            # Add defaults
            if "applications_found" not in finding:
                finding["applications_found"] = []
            if "expected_but_missing" not in finding:
                finding["expected_but_missing"] = []
            if "follow_up_questions" not in finding:
                finding["follow_up_questions"] = []
            if "documents_reviewed" not in finding:
                finding["documents_reviewed"] = []

            # Step 45: Validate - if Not_Found and Critical, must have follow_up_questions
            if (finding.get("coverage_status") == "Not_Found" and
                finding.get("business_relevance") in ["Critical", "High"] and
                not finding.get("follow_up_questions")):
                # Auto-generate a default question
                default_q = get_default_question(capability_area)
                if default_q:
                    finding["follow_up_questions"] = [{
                        "question": default_q,
                        "priority": "high",
                        "target": "Target_Management",
                        "context": f"No applications found for {capability_area} capability"
                    }]

            self.capability_coverage.append(finding)
            return {
                "status": "recorded",
                "id": finding["id"],
                "type": "capability",
                "message": f"Capability coverage recorded: {capability_area}"
            }

        # =====================================================================
        # BUYER COMPARISON TOOLS (Phase 12: Integration Analysis)
        # =====================================================================

        # Record Buyer Application
        elif tool_name == "record_buyer_application":
            # Check for duplicate by name + vendor
            app_name = tool_input.get("application_name", "").lower().strip()
            vendor = tool_input.get("vendor", "").lower().strip()

            for existing in self.buyer_applications:
                existing_name = existing.get("application_name", "").lower().strip()
                existing_vendor = existing.get("vendor", "").lower().strip()
                if existing_name == app_name and existing_vendor == vendor:
                    return {
                        "status": "duplicate",
                        "id": existing["id"],
                        "message": f"Buyer application already recorded: {existing['application_name']} ({existing['vendor']})",
                        "type": "buyer_application"
                    }

            finding = {
                "id": self._next_id("buyer_application"),
                "timestamp": timestamp,
                **tool_input
            }
            # Add defaults
            if "capability_areas_covered" not in finding:
                finding["capability_areas_covered"] = []

            self.buyer_applications.append(finding)
            return {
                "status": "recorded",
                "id": finding["id"],
                "type": "buyer_application",
                "message": f"Buyer application recorded: {finding['application_name']}"
            }

        # Record Application Overlap
        elif tool_name == "record_application_overlap":
            target_app = tool_input.get("target_app_name", "")
            buyer_app = tool_input.get("buyer_app_name", "")

            # Check for duplicate overlap analysis
            for existing in self.application_overlaps:
                if (existing.get("target_app_name") == target_app and
                    existing.get("buyer_app_name") == buyer_app):
                    return {
                        "status": "duplicate",
                        "id": existing["id"],
                        "message": f"Overlap already analyzed: {target_app} vs {buyer_app}",
                        "type": "overlap"
                    }

            finding = {
                "id": self._next_id("overlap"),
                "timestamp": timestamp,
                **tool_input
            }
            # Add defaults
            if "follow_up_questions" not in finding:
                finding["follow_up_questions"] = []

            self.application_overlaps.append(finding)
            return {
                "status": "recorded",
                "id": finding["id"],
                "type": "overlap",
                "message": f"Overlap recorded: {target_app} vs {buyer_app or 'Target only'}"
            }

        # =====================================================================
        # BUSINESS CONTEXT (Phase 7-8)
        # =====================================================================

        elif tool_name == "record_business_context":
            company_name = tool_input.get("company_name", "")

            # Check if business context already exists (singleton - only one per analysis)
            if self.business_context is not None:
                return {
                    "status": "already_exists",
                    "message": f"Business context already recorded for {self.business_context.get('company_name', 'Unknown')}. Use update_business_context to modify.",
                    "type": "business_context"
                }

            context = {
                "id": "BC-001",  # Singleton, always BC-001
                "timestamp": timestamp,
                **tool_input
            }
            # Add defaults
            if "key_business_processes" not in context:
                context["key_business_processes"] = []
            if "regulatory_requirements" not in context:
                context["regulatory_requirements"] = []

            self.business_context = context
            return {
                "status": "recorded",
                "id": "BC-001",
                "type": "business_context",
                "message": f"Business context recorded for: {company_name}"
            }

        # =====================================================================
        # EOL & TECHNICAL DEBT (Phase 9-10)
        # =====================================================================

        elif tool_name == "assess_application_eol":
            app_name = tool_input.get("application_name", "Unknown")
            vendor = tool_input.get("vendor", "Unknown")
            version = tool_input.get("current_version", "Unknown")
            eol_status = tool_input.get("eol_status", "Unknown")

            assessment = {
                "id": self._next_id("eol_assessment"),
                "timestamp": timestamp,
                **tool_input
            }
            # Add defaults
            if "upgrade_path_available" not in assessment:
                assessment["upgrade_path_available"] = None

            self.eol_assessments.append(assessment)
            return {
                "status": "recorded",
                "id": assessment["id"],
                "type": "eol_assessment",
                "message": f"EOL assessed: {vendor} {app_name} {version} - {eol_status}"
            }

        elif tool_name == "assess_technical_debt":
            app_name = tool_input.get("application_name", "Unknown")
            category = tool_input.get("debt_category", "Unknown")
            severity = tool_input.get("severity", "Unknown")

            assessment = {
                "id": self._next_id("technical_debt"),
                "timestamp": timestamp,
                **tool_input
            }
            # Add defaults
            if "remediation_options" not in assessment:
                assessment["remediation_options"] = []
            if "dependencies" not in assessment:
                assessment["dependencies"] = []

            self.technical_debt_assessments.append(assessment)
            return {
                "status": "recorded",
                "id": assessment["id"],
                "type": "technical_debt",
                "message": f"Technical debt recorded: {app_name} - {category} ({severity})"
            }

        # =====================================================================
        # FOUR-LENS FRAMEWORK TOOLS
        # =====================================================================

        # Lens 1: Current State
        elif tool_name == "create_current_state_entry":
            finding = {
                "id": self._next_id("current_state"),
                "timestamp": timestamp,
                **tool_input
            }
            # Add defaults
            if "key_characteristics" not in finding:
                finding["key_characteristics"] = []
            self.current_state.append(finding)
            return {"status": "recorded", "id": finding["id"], "type": "current_state"}

        # Supporting: Assumptions
        elif tool_name == "log_assumption":
            finding = {
                "id": self._next_id("assumption"),
                "timestamp": timestamp,
                **tool_input
            }
            self.assumptions.append(finding)
            return {"status": "recorded", "id": finding["id"], "type": "assumption"}

        # Supporting: Gaps
        elif tool_name == "flag_gap":
            finding = {
                "id": self._next_id("gap"),
                "timestamp": timestamp,
                **tool_input
            }
            self.gaps.append(finding)
            return {"status": "recorded", "id": finding["id"], "type": "gap"}

        # Supporting: Questions for follow-up
        elif tool_name == "flag_question":
            finding = {
                "id": self._next_id("question"),
                "timestamp": timestamp,
                **tool_input
            }
            self.questions.append(finding)
            return {"status": "recorded", "id": finding["id"], "type": "question"}

        # Lens 2: Risks (enhanced)
        elif tool_name == "identify_risk":
            finding = {
                "id": self._next_id("risk"),
                "timestamp": timestamp,
                **tool_input
            }
            # Add defaults for new fields (backward compatibility)
            if "risk_type" not in finding:
                finding["risk_type"] = "integration"
            if "integration_dependent" not in finding:
                finding["integration_dependent"] = True  # Default to integration risk
            if "deal_impact" not in finding:
                finding["deal_impact"] = []
            if "standalone_exposure" not in finding and not finding.get("integration_dependent", True):
                finding["standalone_exposure"] = "See risk description"
            self.risks.append(finding)
            return {"status": "recorded", "id": finding["id"], "type": "risk"}

        # Lens 3: Strategic Considerations
        # Lens 3: Strategic Considerations (Phase 5: Steps 58-60 - Enhanced with follow-up questions)
        elif tool_name == "create_strategic_consideration":
            finding = {
                "id": self._next_id("strategic_consideration"),
                "timestamp": timestamp,
                **tool_input
            }

            # Step 58-59: Add defaults for new follow-up question fields
            if "question_priority" not in finding:
                finding["question_priority"] = "medium"
            if "question_context" not in finding and finding.get("implication"):
                finding["question_context"] = finding["implication"]

            # Step 60: Validate follow-up question exists (warn if missing but don't block)
            if not finding.get("follow_up_question"):
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Strategic consideration {finding['id']} missing follow_up_question - consider adding one")

            self.strategic_considerations.append(finding)
            return {
                "status": "recorded",
                "id": finding["id"],
                "type": "strategic_consideration",
                "has_follow_up": bool(finding.get("follow_up_question"))
            }

        # Lens 4: Work Items (enhanced)
        elif tool_name == "create_work_item":
            finding = {
                "id": self._next_id("work_item"),
                "timestamp": timestamp,
                **tool_input
            }
            # Add defaults for new fields
            if "phase" not in finding:
                finding["phase"] = "Day_100"  # Default phase
            if "phase_rationale" not in finding:
                finding["phase_rationale"] = "Default assignment"
            if "depends_on" not in finding:
                finding["depends_on"] = []
            self.work_items.append(finding)
            return {"status": "recorded", "id": finding["id"], "type": "work_item"}

        # Lens 4: Recommendations
        elif tool_name == "create_recommendation":
            finding = {
                "id": self._next_id("recommendation"),
                "timestamp": timestamp,
                **tool_input
            }
            self.recommendations.append(finding)
            return {"status": "recorded", "id": finding["id"], "type": "recommendation"}

        # Domain completion
        elif tool_name == "complete_analysis":
            domain = tool_input.get("domain")
            self.domain_summaries[domain] = {
                "timestamp": timestamp,
                **tool_input
            }
            return {"status": "domain_complete", "domain": domain}

        # Coordinator tools
        elif tool_name == "create_executive_summary":
            self.executive_summary = {
                "timestamp": timestamp,
                **tool_input
            }
            return {"status": "recorded", "type": "executive_summary"}

        elif tool_name == "identify_cross_domain_dependency":
            # Store as a cross-domain risk
            finding = {
                "id": self._next_id("risk"),
                "timestamp": timestamp,
                "risk": f"Cross-domain dependency: {tool_input.get('dependency', '')}",
                "trigger": tool_input.get("impact", ""),
                "domain": "cross-domain",
                "severity": "high",
                "likelihood": "high",
                "risk_type": "integration",
                "integration_dependent": True,
                "mitigation": tool_input.get("sequencing_requirement", ""),
                **tool_input
            }
            self.risks.append(finding)
            return {"status": "recorded", "id": finding["id"], "type": "cross_domain_dependency"}

        else:
            return {"status": "error", "message": f"Unknown tool: {tool_name}"}

    def get_by_domain(self, domain: str) -> Dict:
        """Get all findings for a specific domain (Step 47: Updated for app inventory)"""
        # For applications domain, include application inventory and capability coverage
        result = {
            "current_state": [c for c in self.current_state if c.get("domain") == domain],
            "assumptions": [a for a in self.assumptions if a.get("domain") == domain],
            "gaps": [g for g in self.gaps if g.get("domain") == domain],
            "risks": [r for r in self.risks if r.get("domain") == domain],
            "strategic_considerations": [s for s in self.strategic_considerations if s.get("domain") == domain],
            "work_items": [w for w in self.work_items if w.get("domain") == domain],
            "recommendations": [r for r in self.recommendations if r.get("domain") == domain],
            "summary": self.domain_summaries.get(domain),
            "reasoning_chain": self.reasoning_chains.get(domain, [])
        }

        # Add application inventory for applications domain
        if domain == "applications":
            result["applications"] = self.applications
            result["capability_coverage"] = self.capability_coverage
            result["application_count"] = len(self.applications)
            result["capabilities_assessed"] = len(self.capability_coverage)
            result["capabilities_total"] = len(CAPABILITY_AREAS)

        return result

    def add_reasoning_chain(self, domain: str, reasoning_entries: List[Dict]):
        """Add reasoning chain entries from an agent's analysis."""
        if domain not in self.reasoning_chains:
            self.reasoning_chains[domain] = []
        self.reasoning_chains[domain].extend(reasoning_entries)

    def get_reasoning_for_finding(self, finding_id: str) -> Optional[Dict]:
        """Get the reasoning chain entry for a specific finding"""
        for domain, entries in self.reasoning_chains.items():
            for entry in entries:
                if entry.get("finding_id") == finding_id:
                    return entry
        return None

    def get_all_reasoning(self) -> Dict[str, List[Dict]]:
        """Get all reasoning chains organized by domain"""
        return self.reasoning_chains

    def get_risks_by_type(self) -> Dict[str, List[Dict]]:
        """Get risks grouped by risk_type"""
        by_type = {}
        for risk in self.risks:
            risk_type = risk.get("risk_type", "other")
            if risk_type not in by_type:
                by_type[risk_type] = []
            by_type[risk_type].append(risk)
        return by_type

    def get_standalone_risks(self) -> List[Dict]:
        """Get risks that exist independent of integration"""
        return [r for r in self.risks if not r.get("integration_dependent", True)]

    def get_integration_risks(self) -> List[Dict]:
        """Get risks that only exist because of integration"""
        return [r for r in self.risks if r.get("integration_dependent", True)]

    # =========================================================================
    # APPLICATION INVENTORY METHODS (Phase 4: Steps 48-50)
    # =========================================================================

    def get_application_inventory(
        self,
        category: Optional[str] = None,
        hosting_model: Optional[str] = None,
        criticality: Optional[str] = None,
        sort_by: str = "application_name"
    ) -> List[Dict]:
        """
        Step 48: Get application inventory with optional filtering and sorting.

        Args:
            category: Filter by APPLICATION_CATEGORIES (e.g., 'ERP', 'CRM')
            hosting_model: Filter by HOSTING_MODELS (e.g., 'SaaS', 'On_Premise')
            criticality: Filter by BUSINESS_CRITICALITY (e.g., 'Critical', 'High')
            sort_by: Field to sort by (default: application_name)

        Returns:
            Filtered and sorted list of applications
        """
        result = self.applications.copy()

        # Apply filters
        if category:
            result = [a for a in result if a.get("application_category") == category]
        if hosting_model:
            result = [a for a in result if a.get("hosting_model") == hosting_model]
        if criticality:
            result = [a for a in result if a.get("business_criticality") == criticality]

        # Sort
        if sort_by and result:
            result.sort(key=lambda x: x.get(sort_by, "").lower() if isinstance(x.get(sort_by), str) else str(x.get(sort_by, "")))

        return result

    def get_applications_by_category(self) -> Dict[str, List[Dict]]:
        """Get applications grouped by category"""
        by_category = {}
        for app in self.applications:
            cat = app.get("application_category", "Other")
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(app)
        return by_category

    def get_applications_by_criticality(self) -> Dict[str, List[Dict]]:
        """Get applications grouped by business criticality"""
        by_crit = {"Critical": [], "High": [], "Medium": [], "Low": [], "Unknown": []}
        for app in self.applications:
            crit = app.get("business_criticality", "Unknown")
            if crit in by_crit:
                by_crit[crit].append(app)
            else:
                by_crit["Unknown"].append(app)
        return by_crit

    # =========================================================================
    # BUSINESS CONTEXT METHODS (Phase 7-8)
    # =========================================================================

    def get_business_context(self) -> Optional[Dict]:
        """Get the recorded business context for the target company."""
        return self.business_context

    def get_expected_capability_relevance(self) -> Dict[str, str]:
        """
        Get expected capability relevance based on business context.

        Returns a dict mapping capability areas to expected relevance:
        - "Critical", "High", "Medium", "Low", "Not_Applicable"

        If no business context is recorded, returns default relevance.
        """
        # Default relevance (applies to most businesses)
        default_relevance = {
            "finance_accounting": "Critical",
            "human_resources": "Critical",
            "sales_crm": "High",
            "marketing": "Medium",
            "operations_supply_chain": "Medium",
            "it_infrastructure": "High",
            "identity_security": "Critical",
            "collaboration": "High",
            "data_analytics": "Medium",
            "legal_compliance": "Medium",
            "customer_service": "Medium",
            "ecommerce_digital": "Low",
            "industry_specific": "Medium"
        }

        if not self.business_context:
            return default_relevance

        relevance = default_relevance.copy()
        industry = self.business_context.get("industry", "Unknown")
        business_model = self.business_context.get("business_model", "Unknown")

        # Adjust based on industry
        if industry in ["Manufacturing", "Distribution"]:
            relevance["operations_supply_chain"] = "Critical"
            relevance["ecommerce_digital"] = "Low"
        elif industry in ["E_Commerce", "Retail"]:
            relevance["operations_supply_chain"] = "High"
            relevance["ecommerce_digital"] = "Critical"
            relevance["customer_service"] = "High"
        elif industry == "Healthcare":
            relevance["legal_compliance"] = "Critical"
            relevance["industry_specific"] = "Critical"
        elif industry == "Financial_Services":
            relevance["legal_compliance"] = "Critical"
            relevance["data_analytics"] = "High"
        elif industry in ["Technology_Software", "Technology_Hardware"]:
            relevance["operations_supply_chain"] = "Low"
            relevance["data_analytics"] = "High"
        elif industry == "Professional_Services":
            relevance["operations_supply_chain"] = "Not_Applicable"
            relevance["ecommerce_digital"] = "Low"

        # Adjust based on business model
        if business_model in ["B2C", "D2C"]:
            relevance["customer_service"] = "High"
            relevance["marketing"] = "High"
        elif business_model == "Subscription_SaaS":
            relevance["customer_service"] = "High"
            relevance["data_analytics"] = "High"
        elif business_model == "Marketplace":
            relevance["ecommerce_digital"] = "Critical"

        return relevance

    def get_business_context_summary(self) -> str:
        """Generate a human-readable summary of the business context."""
        if not self.business_context:
            return "No business context recorded. Use record_business_context to capture target company profile."

        ctx = self.business_context
        lines = [
            f"Company: {ctx.get('company_name', 'Unknown')}",
            f"Industry: {ctx.get('industry', 'Unknown')} - {ctx.get('industry_details', 'No details')}",
            f"Business Model: {ctx.get('business_model', 'Unknown')} - {ctx.get('business_model_details', 'No details')}",
            f"Size: {ctx.get('employee_count_range', 'Unknown')} employees",
            f"Revenue: {ctx.get('revenue_range', 'Unknown')}",
            f"Geographic: {ctx.get('geographic_presence', 'Unknown')} - {ctx.get('geographic_details', 'No details')}"
        ]

        if ctx.get("key_business_processes"):
            lines.append(f"Key Processes: {', '.join(ctx['key_business_processes'])}")

        if ctx.get("regulatory_requirements"):
            lines.append(f"Regulatory: {', '.join(ctx['regulatory_requirements'])}")

        if ctx.get("is_public_company"):
            lines.append(f"Public Company: Yes ({ctx.get('ticker_symbol', 'N/A')})")

        return "\n".join(lines)

    # =========================================================================
    # EOL & TECHNICAL DEBT METHODS (Phase 9-10)
    # =========================================================================

    def get_eol_assessments(self) -> List[Dict]:
        """Get all recorded EOL assessments."""
        return self.eol_assessments

    def get_eol_assessments_by_status(self, status: str) -> List[Dict]:
        """Get EOL assessments filtered by status (e.g., 'Past_EOL', 'Approaching_EOL')."""
        return [a for a in self.eol_assessments if a.get("eol_status") == status]

    def get_eol_risks(self) -> List[Dict]:
        """Get EOL assessments that represent risks (Past_EOL or Approaching_EOL)."""
        risk_statuses = ["Past_EOL", "Approaching_EOL", "Extended_Support"]
        return [a for a in self.eol_assessments if a.get("eol_status") in risk_statuses]

    def get_technical_debt_assessments(self) -> List[Dict]:
        """Get all recorded technical debt assessments."""
        return self.technical_debt_assessments

    def get_technical_debt_by_severity(self, severity: str) -> List[Dict]:
        """Get technical debt filtered by severity (e.g., 'Critical', 'High')."""
        return [t for t in self.technical_debt_assessments if t.get("severity") == severity]

    def get_critical_technical_debt(self) -> List[Dict]:
        """Get all Critical and High severity technical debt."""
        return [t for t in self.technical_debt_assessments if t.get("severity") in ["Critical", "High"]]

    def get_eol_summary(self) -> Dict[str, Any]:
        """
        Generate a summary of EOL status across all assessed applications.

        Returns:
            Dict with EOL summary metrics and risk breakdown
        """
        if not self.eol_assessments:
            return {
                "status": "no_assessments",
                "total_assessed": 0,
                "by_status": {},
                "risks": []
            }

        # Count by status
        status_counts = {}
        for assessment in self.eol_assessments:
            status = assessment.get("eol_status", "Unknown")
            status_counts[status] = status_counts.get(status, 0) + 1

        # Identify risks
        risks = []
        for assessment in self.eol_assessments:
            status = assessment.get("eol_status")
            if status in ["Past_EOL", "Approaching_EOL"]:
                risks.append({
                    "id": assessment.get("id"),
                    "application": assessment.get("application_name"),
                    "vendor": assessment.get("vendor"),
                    "version": assessment.get("current_version"),
                    "status": status,
                    "eol_date": assessment.get("eol_date"),
                    "risk_if_not_upgraded": assessment.get("risk_if_not_upgraded")
                })

        return {
            "status": "analyzed",
            "total_assessed": len(self.eol_assessments),
            "by_status": status_counts,
            "past_eol_count": status_counts.get("Past_EOL", 0),
            "approaching_eol_count": status_counts.get("Approaching_EOL", 0),
            "current_count": status_counts.get("Current", 0) + status_counts.get("Supported", 0),
            "risks": risks
        }

    def get_technical_debt_summary(self) -> Dict[str, Any]:
        """
        Generate a summary of technical debt across all assessments.

        Returns:
            Dict with technical debt summary metrics and severity breakdown
        """
        if not self.technical_debt_assessments:
            return {
                "status": "no_assessments",
                "total_debt_items": 0,
                "by_severity": {},
                "by_category": {},
                "critical_items": []
            }

        # Count by severity
        severity_counts = {}
        for debt in self.technical_debt_assessments:
            severity = debt.get("severity", "Unknown")
            severity_counts[severity] = severity_counts.get(severity, 0) + 1

        # Count by category
        category_counts = {}
        for debt in self.technical_debt_assessments:
            category = debt.get("debt_category", "Unknown")
            category_counts[category] = category_counts.get(category, 0) + 1

        # Identify critical items
        critical_items = []
        for debt in self.technical_debt_assessments:
            if debt.get("severity") in ["Critical", "High"]:
                critical_items.append({
                    "id": debt.get("id"),
                    "application": debt.get("application_name"),
                    "category": debt.get("debt_category"),
                    "severity": debt.get("severity"),
                    "description": debt.get("debt_description"),
                    "urgency": debt.get("modernization_urgency")
                })

        return {
            "status": "analyzed",
            "total_debt_items": len(self.technical_debt_assessments),
            "by_severity": severity_counts,
            "by_category": category_counts,
            "critical_count": severity_counts.get("Critical", 0),
            "high_count": severity_counts.get("High", 0),
            "critical_items": critical_items
        }

    def get_application_completeness_metrics(self) -> Dict[str, Any]:
        """
        Phase 2-3 Enhancement: Calculate completeness metrics for application inventory.

        Tracks:
        - Total applications recorded
        - Fields documented vs not documented
        - Applications with Unknown values
        - Overall documentation completeness score

        Returns:
            Dict with completeness metrics
        """
        if not self.applications:
            return {
                "status": "no_applications",
                "total_applications": 0,
                "completeness_score": 0.0,
                "fields_analysis": {},
                "unknown_value_counts": {}
            }

        # Key fields to track (optional fields that indicate documentation quality)
        trackable_fields = [
            "version", "user_count", "license_type", "contract_expiry",
            "license_count", "integration_count", "technology_stack",
            "deployment_date", "customization_level"
        ]

        # Enum fields that might be Unknown
        enum_fields = [
            "hosting_model", "support_status", "business_criticality",
            "customization_level"
        ]

        # Count field documentation
        field_documented = {f: 0 for f in trackable_fields}
        field_not_documented = {f: 0 for f in trackable_fields}
        unknown_counts = {f: 0 for f in enum_fields}

        apps_with_fields_not_documented = []

        for app in self.applications:
            # Check trackable fields
            fields_missing = app.get("fields_not_documented", [])
            if fields_missing:
                apps_with_fields_not_documented.append({
                    "app_id": app.get("id"),
                    "app_name": app.get("application_name"),
                    "missing_fields": fields_missing
                })

            for field in trackable_fields:
                if field in fields_missing:
                    field_not_documented[field] += 1
                elif app.get(field) and app.get(field) != "Unknown":
                    field_documented[field] += 1

            # Check for Unknown enum values
            for field in enum_fields:
                if app.get(field) == "Unknown":
                    unknown_counts[field] += 1

        # Calculate completeness score
        total_apps = len(self.applications)
        total_trackable_fields = total_apps * len(trackable_fields)
        total_documented = sum(field_documented.values())
        completeness_score = (total_documented / total_trackable_fields * 100) if total_trackable_fields > 0 else 0

        return {
            "status": "analyzed",
            "total_applications": total_apps,
            "completeness_score": round(completeness_score, 1),
            "fields_analysis": {
                "documented": field_documented,
                "not_documented": field_not_documented,
                "trackable_fields": trackable_fields
            },
            "unknown_value_counts": unknown_counts,
            "apps_with_missing_fields": len(apps_with_fields_not_documented),
            "apps_missing_field_details": apps_with_fields_not_documented[:10]  # Limit to first 10
        }

    def get_capability_summary(self) -> Dict[str, Any]:
        """
        Step 49: Get summary of capability coverage analysis.

        Returns:
            Summary with coverage status, gaps, and follow-up questions
        """
        total_areas = len(CAPABILITY_AREAS)
        assessed = len(self.capability_coverage)
        not_assessed = [area for area in CAPABILITY_AREAS
                        if area not in [c.get("capability_area") for c in self.capability_coverage]]

        # Aggregate by coverage status
        by_status = {}
        for cap in self.capability_coverage:
            status = cap.get("coverage_status", "Unknown")
            if status not in by_status:
                by_status[status] = []
            by_status[status].append(cap.get("capability_area"))

        # Collect all follow-up questions
        all_questions = []
        for cap in self.capability_coverage:
            for q in cap.get("follow_up_questions", []):
                all_questions.append({
                    "capability_area": cap.get("capability_area"),
                    **q
                })

        # Sort questions by priority
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        all_questions.sort(key=lambda x: priority_order.get(x.get("priority", "low"), 4))

        # Identify critical gaps
        critical_gaps = [
            cap for cap in self.capability_coverage
            if cap.get("coverage_status") == "Not_Found"
            and cap.get("business_relevance") in ["Critical", "High"]
        ]

        return {
            "total_capability_areas": total_areas,
            "areas_assessed": assessed,
            "areas_not_assessed": not_assessed,
            "coverage_by_status": by_status,
            "critical_gaps": [g.get("capability_area") for g in critical_gaps],
            "all_follow_up_questions": all_questions,
            "question_count": len(all_questions),
            "completeness_percentage": round((assessed / total_areas) * 100, 1) if total_areas > 0 else 0
        }

    def get_all_follow_up_questions(self) -> List[Dict]:
        """
        Aggregate all follow-up questions from multiple sources:
        - capability_coverage
        - strategic_considerations (if they have follow_up_question)
        - questions (from flag_question tool)
        """
        all_questions = []

        # From capability coverage
        for cap in self.capability_coverage:
            for q in cap.get("follow_up_questions", []):
                all_questions.append({
                    "source": "capability_coverage",
                    "capability_area": cap.get("capability_area"),
                    **q
                })

        # From strategic considerations (if enhanced with follow_up_question)
        for sc in self.strategic_considerations:
            if sc.get("follow_up_question"):
                all_questions.append({
                    "source": "strategic_consideration",
                    "consideration_id": sc.get("id"),
                    "question": sc.get("follow_up_question"),
                    "priority": sc.get("question_priority", "medium"),
                    "target": sc.get("question_target", "Target_Management"),
                    "context": sc.get("question_context", sc.get("consideration", ""))
                })

        # From direct questions (flag_question tool)
        for q in self.questions:
            all_questions.append({
                "source": "direct_question",
                "question_id": q.get("id"),
                "question": q.get("question"),
                "priority": q.get("priority", "medium"),
                "target": q.get("suggested_source", "Target_Management"),
                "context": q.get("context", ""),
                "domain": q.get("domain")
            })

        # Sort by priority
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        all_questions.sort(key=lambda x: priority_order.get(x.get("priority", "low"), 4))

        return all_questions

    # =========================================================================
    # APPLICATION COMPLETENESS VERIFICATION (Phase 8: Steps 89-98)
    # =========================================================================

    def validate_application_completeness(self) -> Dict[str, Any]:
        """
        Step 89-95: Comprehensive validation of application analysis completeness.

        Checks:
        - Application count vs document mentions
        - Capability area coverage
        - Critical capabilities assessed
        - Follow-up questions for gaps
        - Evidence coverage

        Returns:
            Dict with completeness status, issues, and recommendations
        """
        issues = []
        warnings = []
        recommendations = []

        # Step 90: Check application count
        app_count = len(self.applications)
        if app_count == 0:
            issues.append("No applications recorded - run record_application for each app found")

        # Step 91: Check capability coverage completeness
        capability_areas_assessed = [c.get("capability_area") for c in self.capability_coverage]
        missing_areas = [area for area in CAPABILITY_AREAS if area not in capability_areas_assessed]

        if missing_areas:
            issues.append(f"Capability areas not assessed: {', '.join(missing_areas)}")
            recommendations.append(f"Use record_capability_coverage for: {', '.join(missing_areas)}")

        # Step 92: Check critical capabilities specifically
        critical_capabilities = get_critical_capabilities()
        missing_critical = [area for area in critical_capabilities if area not in capability_areas_assessed]

        if missing_critical:
            issues.append(f"CRITICAL capability areas missing: {', '.join(missing_critical)}")

        # Step 93: Check follow-up questions exist for gaps
        gaps_without_questions = []
        for cap in self.capability_coverage:
            if cap.get("coverage_status") in ["Not_Found", "Partially_Documented"]:
                if cap.get("business_relevance") in ["Critical", "High"]:
                    if not cap.get("follow_up_questions"):
                        gaps_without_questions.append(cap.get("capability_area"))

        if gaps_without_questions:
            warnings.append(f"Gaps without follow-up questions: {', '.join(gaps_without_questions)}")

        # Step 94: Validate evidence coverage
        apps_without_evidence = [
            app.get("application_name")
            for app in self.applications
            if not app.get("source_evidence") or not app.get("source_evidence", {}).get("exact_quote")
        ]

        if apps_without_evidence:
            warnings.append(f"Applications without evidence: {', '.join(apps_without_evidence[:5])}{'...' if len(apps_without_evidence) > 5 else ''}")

        # Step 95: Generate completeness report
        total_areas = len(CAPABILITY_AREAS)
        assessed_areas = len(capability_areas_assessed)
        completeness_pct = round((assessed_areas / total_areas) * 100, 1) if total_areas > 0 else 0

        # Calculate overall status
        if issues:
            status = "incomplete"
        elif warnings:
            status = "complete_with_warnings"
        else:
            status = "complete"

        return {
            "status": status,
            "application_count": app_count,
            "capability_areas_total": total_areas,
            "capability_areas_assessed": assessed_areas,
            "capability_completeness_pct": completeness_pct,
            "missing_capability_areas": missing_areas,
            "missing_critical_areas": missing_critical,
            "issues": issues,
            "warnings": warnings,
            "recommendations": recommendations,
            "follow_up_questions_count": len(self.get_all_follow_up_questions()),
            "apps_without_evidence_count": len(apps_without_evidence)
        }

    def get_completeness_report(self) -> str:
        """
        Step 98: Generate human-readable completeness report.

        Returns:
            Formatted string report
        """
        validation = self.validate_application_completeness()
        cap_summary = self.get_capability_summary()

        lines = [
            "=" * 70,
            "APPLICATION ANALYSIS COMPLETENESS REPORT",
            "=" * 70,
            "",
            f"Overall Status: {validation['status'].upper()}",
            "",
            "APPLICATION INVENTORY:",
            f"  Applications Recorded: {validation['application_count']}",
            f"  Applications Without Evidence: {validation['apps_without_evidence_count']}",
            "",
            "CAPABILITY COVERAGE:",
            f"  Total Capability Areas: {validation['capability_areas_total']}",
            f"  Areas Assessed: {validation['capability_areas_assessed']}",
            f"  Completeness: {validation['capability_completeness_pct']}%",
            "",
        ]

        if validation['missing_capability_areas']:
            lines.append("MISSING CAPABILITY ASSESSMENTS:")
            for area in validation['missing_capability_areas']:
                lines.append(f"  - {area}")
            lines.append("")

        if validation['issues']:
            lines.append("ISSUES (must resolve):")
            for issue in validation['issues']:
                lines.append(f"  [!] {issue}")
            lines.append("")

        if validation['warnings']:
            lines.append("WARNINGS:")
            for warning in validation['warnings']:
                lines.append(f"  [?] {warning}")
            lines.append("")

        if validation['recommendations']:
            lines.append("RECOMMENDATIONS:")
            for rec in validation['recommendations']:
                lines.append(f"  -> {rec}")
            lines.append("")

        # Follow-up questions summary
        lines.append(f"FOLLOW-UP QUESTIONS GENERATED: {validation['follow_up_questions_count']}")
        if cap_summary.get('critical_gaps'):
            lines.append(f"CRITICAL GAPS: {', '.join(cap_summary['critical_gaps'])}")

        lines.append("")
        lines.append("=" * 70)

        return "\n".join(lines)

    # =========================================================================
    # BUYER COMPARISON METHODS (Phase 12: Integration Analysis)
    # =========================================================================

    def get_buyer_applications(
        self,
        category: Optional[str] = None,
        capability_area: Optional[str] = None
    ) -> List[Dict]:
        """
        Get buyer applications with optional filtering.

        Args:
            category: Filter by APPLICATION_CATEGORIES
            capability_area: Filter by CAPABILITY_AREAS

        Returns:
            Filtered list of buyer applications
        """
        result = self.buyer_applications.copy()

        if category:
            result = [a for a in result if a.get("application_category") == category]
        if capability_area:
            result = [a for a in result
                      if capability_area in a.get("capability_areas_covered", [])]

        return result

    def get_application_overlaps(
        self,
        overlap_type: Optional[str] = None,
        decision: Optional[str] = None,
        complexity: Optional[str] = None
    ) -> List[Dict]:
        """
        Get application overlap analyses with optional filtering.

        Args:
            overlap_type: Filter by OVERLAP_TYPES
            decision: Filter by INTEGRATION_DECISIONS
            complexity: Filter by INTEGRATION_COMPLEXITY

        Returns:
            Filtered list of overlap analyses
        """
        result = self.application_overlaps.copy()

        if overlap_type:
            result = [o for o in result if o.get("overlap_type") == overlap_type]
        if decision:
            result = [o for o in result if o.get("integration_decision") == decision]
        if complexity:
            result = [o for o in result if o.get("integration_complexity") == complexity]

        return result

    def get_overlap_matrix(self) -> Dict[str, Any]:
        """
        Generate an overlap matrix showing target apps vs buyer apps.

        Returns:
            Dict with matrix structure:
            - target_apps: list of target app names
            - buyer_apps: list of buyer app names
            - overlaps: matrix of overlap types
            - decisions: matrix of integration decisions
        """
        # Get unique apps
        target_apps = [a.get("application_name") for a in self.applications]
        buyer_apps = [a.get("application_name") for a in self.buyer_applications]

        # Build lookup for overlaps
        overlap_lookup = {}
        for ovl in self.application_overlaps:
            key = (ovl.get("target_app_name"), ovl.get("buyer_app_name"))
            overlap_lookup[key] = ovl

        # Build matrix
        matrix = []
        for target in target_apps:
            row = {
                "target_app": target,
                "overlaps": []
            }
            for buyer in buyer_apps:
                ovl = overlap_lookup.get((target, buyer))
                if ovl:
                    row["overlaps"].append({
                        "buyer_app": buyer,
                        "overlap_type": ovl.get("overlap_type"),
                        "decision": ovl.get("integration_decision"),
                        "complexity": ovl.get("integration_complexity")
                    })
            # Also check for "Target_Only" overlaps (no buyer equivalent)
            for ovl in self.application_overlaps:
                if ovl.get("target_app_name") == target and ovl.get("overlap_type") == "Target_Only":
                    row["overlaps"].append({
                        "buyer_app": None,
                        "overlap_type": "Target_Only",
                        "decision": ovl.get("integration_decision"),
                        "complexity": ovl.get("integration_complexity")
                    })
            matrix.append(row)

        return {
            "target_app_count": len(target_apps),
            "buyer_app_count": len(buyer_apps),
            "overlap_count": len(self.application_overlaps),
            "matrix": matrix
        }

    def get_integration_summary(self) -> Dict[str, Any]:
        """
        Generate a summary of overlap analysis.

        Focus on:
        - What overlaps exist (by type)
        - What considerations have been raised
        - What questions need answering

        Returns:
            Dict with overlap counts, considerations, and questions
        """
        if not self.application_overlaps:
            return {
                "status": "no_overlaps_analyzed",
                "message": "No application overlaps have been recorded. Use record_application_overlap to analyze target vs buyer apps.",
                "overlap_by_type": {},
                "follow_up_questions": []
            }

        # Count by overlap type
        overlap_by_type = {}
        for ovl in self.application_overlaps:
            otype = ovl.get("overlap_type", "Unknown")
            overlap_by_type[otype] = overlap_by_type.get(otype, 0) + 1

        # Collect all considerations
        considerations = [
            {
                "target_app": ovl.get("target_app_name"),
                "buyer_app": ovl.get("buyer_app_name"),
                "overlap_type": ovl.get("overlap_type"),
                "considerations": ovl.get("considerations", "")
            }
            for ovl in self.application_overlaps
            if ovl.get("considerations")
        ]

        # Aggregate follow-up questions from overlaps
        overlap_questions = []
        for ovl in self.application_overlaps:
            for q in ovl.get("follow_up_questions", []):
                overlap_questions.append({
                    "source": "application_overlap",
                    "target_app": ovl.get("target_app_name"),
                    "buyer_app": ovl.get("buyer_app_name"),
                    "overlap_type": ovl.get("overlap_type"),
                    **q
                })

        return {
            "status": "analyzed",
            "total_overlaps_analyzed": len(self.application_overlaps),
            "overlap_by_type": overlap_by_type,
            "considerations": considerations,
            "follow_up_questions": overlap_questions,
            "question_count": len(overlap_questions)
        }

    def get_integration_report(self) -> str:
        """
        Generate human-readable overlap analysis report.

        Returns:
            Formatted string report
        """
        summary = self.get_integration_summary()

        if summary.get("status") == "no_overlaps_analyzed":
            return "No application overlaps have been analyzed yet.\nUse record_application_overlap to compare target apps against buyer environment."

        lines = [
            "=" * 70,
            "TARGET vs BUYER APPLICATION OVERLAP REPORT",
            "=" * 70,
            "",
            f"Total Overlaps Analyzed: {summary['total_overlaps_analyzed']}",
            "",
            "OVERLAP BY TYPE:",
        ]

        for otype, count in sorted(summary['overlap_by_type'].items(), key=lambda x: -x[1]):
            lines.append(f"  {otype}: {count}")

        if summary['considerations']:
            lines.extend(["", "KEY CONSIDERATIONS:"])
            for cons in summary['considerations'][:10]:  # Show top 10
                buyer_str = f" vs {cons['buyer_app']}" if cons['buyer_app'] else ""
                lines.append(f"  [{cons['overlap_type']}] {cons['target_app']}{buyer_str}")
                # Truncate long considerations
                cons_text = cons['considerations'][:150] + "..." if len(cons['considerations']) > 150 else cons['considerations']
                lines.append(f"      {cons_text}")

        if summary['follow_up_questions']:
            lines.extend(["", f"FOLLOW-UP QUESTIONS ({summary['question_count']}):"])
            for q in summary['follow_up_questions'][:10]:  # Show top 10
                lines.append(f"  - [{q.get('target', 'TBD')}] {q.get('question', '')}")

        lines.extend(["", "=" * 70])

        return "\n".join(lines)

    def get_work_items_by_phase(self) -> Dict[str, List[Dict]]:
        """Get work items grouped by phase"""
        by_phase = {"Day_1": [], "Day_100": [], "Post_100": [], "Optional": []}
        for item in self.work_items:
            phase = item.get("phase", "Day_100")
            if phase in by_phase:
                by_phase[phase].append(item)
            else:
                by_phase["Day_100"].append(item)  # Default
        return by_phase

    def validate_work_item_dependencies(self) -> List[str]:
        """Check for dependency issues in work items"""
        issues = []
        work_item_ids = {w["id"] for w in self.work_items}
        work_item_phases = {w["id"]: w.get("phase", "Day_100") for w in self.work_items}
        phase_order = {"Day_1": 1, "Day_100": 2, "Post_100": 3, "Optional": 4}

        for item in self.work_items:
            item_phase = item.get("phase", "Day_100")
            for dep_id in item.get("depends_on", []):
                # Check if dependency exists
                if dep_id not in work_item_ids:
                    issues.append(f"{item['id']} depends on non-existent {dep_id}")
                else:
                    # Check phase ordering
                    dep_phase = work_item_phases.get(dep_id, "Day_100")
                    if phase_order.get(dep_phase, 2) > phase_order.get(item_phase, 2):
                        issues.append(f"{item['id']} ({item_phase}) depends on {dep_id} ({dep_phase}) - invalid sequence")

        return issues

    def validate_dd_completeness(self) -> Dict[str, Any]:
        """Validate that all four lenses produced output for each domain"""
        domains = ["infrastructure", "network", "cybersecurity"]
        missing_lenses = []
        missing_domains = []

        for domain in domains:
            domain_findings = self.get_by_domain(domain)

            # Check Lens 1: Current State
            if not domain_findings.get("current_state"):
                missing_lenses.append(f"{domain}: current_state")

            # Check Lens 2: Risks
            if not domain_findings.get("risks"):
                missing_lenses.append(f"{domain}: risks")

            # Check Lens 3: Strategic Considerations
            if not domain_findings.get("strategic_considerations"):
                missing_lenses.append(f"{domain}: strategic_considerations")

            # Check Lens 4: Work Items
            if not domain_findings.get("work_items"):
                missing_lenses.append(f"{domain}: work_items")

            # Check domain summary
            if domain not in self.domain_summaries:
                missing_domains.append(domain)

        # Check for non-integration risks
        standalone_risks = self.get_standalone_risks()
        non_integration_risks_evaluated = len(standalone_risks) > 0

        return {
            "dd_completeness_check": "pass" if not missing_lenses and not missing_domains else "fail",
            "missing_lenses": missing_lenses,
            "missing_domains": missing_domains,
            "non_integration_risks_evaluated": non_integration_risks_evaluated,
            "standalone_risk_count": len(standalone_risks)
        }

    def validate_outputs(self) -> Dict[str, Any]:
        """Validate analysis outputs for completeness and quality"""
        issues = []
        warnings = []

        # Check each domain has a summary
        for domain in ["infrastructure", "network", "cybersecurity"]:
            if domain not in self.domain_summaries:
                issues.append(f"Missing summary for {domain}")

        # Check critical risks have mitigations
        for risk in self.risks:
            if risk.get("severity") in ["critical", "high"]:
                mitigation = risk.get("mitigation", "")
                if not mitigation or len(mitigation) < 20:
                    warnings.append(f"Risk {risk['id']} lacks detailed mitigation")

        # Check work items have estimates
        for item in self.work_items:
            if not item.get("effort_estimate"):
                warnings.append(f"Work item {item['id']} missing effort estimate")
            if not item.get("phase"):
                warnings.append(f"Work item {item['id']} missing phase tag")

        # Check assumptions have validation plans
        for assumption in self.assumptions:
            if assumption.get("confidence") == "low":
                if not assumption.get("validation_needed"):
                    warnings.append(f"Low-confidence assumption {assumption['id']} needs validation plan")

        # Check work item dependencies
        dep_issues = self.validate_work_item_dependencies()
        warnings.extend(dep_issues)

        # DD completeness check
        dd_check = self.validate_dd_completeness()

        # Step 96-97: Application completeness check (Phase 8)
        app_completeness = self.validate_application_completeness()

        # Add application-specific issues/warnings
        if app_completeness.get("issues"):
            for issue in app_completeness["issues"]:
                issues.append(f"[Applications] {issue}")

        if app_completeness.get("warnings"):
            for warning in app_completeness["warnings"]:
                warnings.append(f"[Applications] {warning}")

        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "quality_score": self._calculate_quality_score(),
            "dd_completeness": dd_check,
            "application_completeness": app_completeness  # Phase 8 addition
        }

    def _calculate_quality_score(self) -> float:
        """Calculate overall quality score (0-100)"""
        score = 100.0

        # Deduct for missing summaries
        expected_domains = 3
        score -= (expected_domains - len(self.domain_summaries)) * 10

        # Deduct for missing current state entries
        domains_with_current_state = len(set(c.get("domain") for c in self.current_state))
        score -= (expected_domains - domains_with_current_state) * 5

        # Deduct for incomplete findings
        incomplete_risks = sum(1 for r in self.risks
                              if r.get("severity") in ["critical", "high"]
                              and (not r.get("mitigation") or len(r.get("mitigation", "")) < 20))
        score -= incomplete_risks * 2

        incomplete_work_items = sum(1 for w in self.work_items
                                   if not w.get("effort_estimate") or not w.get("phase"))
        score -= incomplete_work_items * 1

        incomplete_assumptions = sum(1 for a in self.assumptions
                                    if a.get("confidence") == "low"
                                    and not a.get("validation_needed"))
        score -= incomplete_assumptions * 1

        # Bonus for non-integration risk coverage
        if self.get_standalone_risks():
            score += 5

        return max(0, min(100, score))

    def enrich_outputs(self):
        """Enrich outputs with additional context and calculations"""
        # Add risk scores
        for risk in self.risks:
            risk["risk_score"] = self._calculate_risk_score(risk)

        # Add priority rankings
        self._rank_findings()

    def _calculate_risk_score(self, risk: Dict) -> float:
        """Calculate numeric risk score"""
        severity_map = {"critical": 4, "high": 3, "medium": 2, "low": 1}
        likelihood_map = {"high": 3, "medium": 2, "low": 1}

        severity = severity_map.get(risk.get("severity", "low"), 1)
        likelihood = likelihood_map.get(risk.get("likelihood", "low"), 1)

        return severity * likelihood

    def _rank_findings(self):
        """Add priority rankings to findings"""
        # Rank risks by score
        for risk in self.risks:
            risk["risk_score"] = self._calculate_risk_score(risk)

        risks_with_scores = [(r, r.get("risk_score", 0)) for r in self.risks]
        risks_with_scores.sort(key=lambda x: x[1], reverse=True)

        for rank, (risk, _) in enumerate(risks_with_scores, 1):
            risk["priority_rank"] = rank

        # Rank work items by priority
        for item in self.work_items:
            priority_map = {"critical": 4, "high": 3, "medium": 2, "low": 1}
            item["priority_score"] = priority_map.get(item.get("priority", "low"), 1)

    # =========================================================================
    # DATABASE INTEGRATION (Points 47-52 of 115PP)
    # =========================================================================

    def set_database(self, db=None, repository=None):
        """
        Point 47: Accept database connection for persistence.

        Args:
            db: Database instance (optional if repository provided)
            repository: Repository instance (optional, will be created from db)
        """
        self._db = db
        self._repository = repository

    @property
    def has_database(self) -> bool:
        """Check if database is configured for persistence"""
        return self._repository is not None

    def ensure_database(self):
        """
        Ensure database is configured, auto-configuring if not.

        This is useful for CLI tools that need database access.
        """
        if self._repository is not None:
            return

        # Auto-configure with default database
        try:
            from storage import Database, Repository
            db = Database()
            db.initialize_schema()
            self._db = db
            self._repository = Repository(db)
            print("💾 Auto-configured database connection")
        except ImportError as e:
            raise ValueError(
                "Database repository not set and auto-configuration failed. "
                "Call set_database() first or ensure storage module is available."
            ) from e

    def _require_database(self, operation: str):
        """Helper to check database is available before operations"""
        if self._repository is None:
            raise ValueError(
                f"Database required for {operation}. "
                "Call set_database(db, repository) first, or use ensure_database() for auto-configuration."
            )

    def set_run_id(self, run_id: str):
        """
        Point 51: Set the analysis run ID for tracking which run produced findings.
        """
        self.run_id = run_id

    def add_document_id(self, document_id: str):
        """
        Point 52: Link a source document to this analysis.
        """
        if document_id not in self.document_ids:
            self.document_ids.append(document_id)

    def save_to_database(self) -> Dict[str, int]:
        """
        Point 48: Save all findings to database.

        Returns:
            Dict with counts of saved items per type
        """
        self._require_database("save_to_database")

        if self.run_id is None:
            raise ValueError("Run ID not set. Call set_run_id() first.")

        return self._repository.import_from_analysis_store(self, self.run_id)

    def load_from_database(self, run_id: str) -> bool:
        """
        Point 49: Load findings from a previous run for resuming analysis.

        Args:
            run_id: The run ID to load findings from

        Returns:
            True if loaded successfully
        """
        self._require_database("load_from_database")

        self.run_id = run_id

        # Load all findings from the run
        findings = self._repository.get_all_findings_for_run(run_id)

        # Helper to safely convert list of model objects to dicts
        def convert_list(items: list) -> list:
            if not items:
                return []
            # Check first item to determine conversion method
            if hasattr(items[0], 'to_dict'):
                return [self._model_to_dict(item) for item in items]
            return items

        # Convert model objects back to dicts and populate lists
        self.current_state = convert_list(findings.get('inventory_items', []))
        self.risks = convert_list(findings.get('risks', []))
        self.gaps = convert_list(findings.get('gaps', []))
        self.assumptions = convert_list(findings.get('assumptions', []))
        self.work_items = convert_list(findings.get('work_items', []))
        self.recommendations = convert_list(findings.get('recommendations', []))
        self.strategic_considerations = convert_list(findings.get('strategic_considerations', []))

        # Update ID counters to continue from loaded data
        self._update_id_counters()

        return True

    def _model_to_dict(self, obj) -> Dict:
        """Convert a model object to dict with standardized 'id' field"""
        if hasattr(obj, 'to_dict'):
            d = obj.to_dict()
        elif hasattr(obj, '__dict__'):
            d = obj.__dict__.copy()
        else:
            return obj

        # Standardize ID field names to 'id' for AnalysisStore compatibility
        id_fields = ['risk_id', 'gap_id', 'assumption_id', 'item_id', 'work_item_id',
                     'recommendation_id', 'consideration_id', 'question_id']
        for id_field in id_fields:
            if id_field in d and 'id' not in d:
                d['id'] = d[id_field]
                break

        return d

    def _update_id_counters(self):
        """Update ID counters based on loaded findings to avoid ID collisions"""
        def extract_number(id_str: str) -> int:
            """Extract number from ID like 'R-005' -> 5"""
            if not id_str:
                return 0
            parts = id_str.split('-')
            if len(parts) >= 2:
                try:
                    return int(parts[-1])
                except ValueError:
                    return 0
            return 0

        def get_max_id(items: list, counter_key: str):
            """Safely get max ID from a list of items"""
            if not items:
                return
            max_val = max((extract_number(item.get('id', '')) for item in items), default=0)
            self._id_counters[counter_key] = max(self._id_counters[counter_key], max_val)

        # Update each counter based on max ID found
        get_max_id(self.current_state, 'current_state')
        get_max_id(self.risks, 'risk')
        get_max_id(self.gaps, 'gap')
        get_max_id(self.assumptions, 'assumption')
        get_max_id(self.work_items, 'work_item')
        get_max_id(self.recommendations, 'recommendation')
        get_max_id(self.strategic_considerations, 'strategic_consideration')

    @staticmethod
    def get_analysis_history(repository) -> List[Dict]:
        """
        Point 50: Get history of past analysis runs.

        Args:
            repository: Repository instance to query

        Returns:
            List of analysis run summaries
        """
        runs = repository.get_all_runs()
        history = []
        for run in runs:
            run_dict = run.to_dict() if hasattr(run, 'to_dict') else run
            # Add summary statistics
            try:
                summary = repository.get_run_summary(run_dict.get('run_id'))
                run_dict['statistics'] = summary.get('counts', {})
            except Exception:
                run_dict['statistics'] = {}
            history.append(run_dict)
        return history

    # =========================================================================
    # PHASE 4: ITERATIVE CAPABILITY (Points 70-74 of 115PP)
    # =========================================================================

    def load_previous_state(self, run_id: str = None) -> Dict[str, Any]:
        """
        Point 70: Load previous analysis state for iterative analysis.

        If run_id is None, loads the most recent completed run.

        Args:
            run_id: Specific run to load, or None for latest

        Returns:
            Dict with load status and statistics
        """
        self._require_database("load_previous_state")

        # Get the run to load
        if run_id is None:
            latest_run = self._repository.get_latest_run()
            if latest_run is None:
                return {"status": "no_previous_runs", "loaded": False}
            run_id = latest_run.run_id

        # Load the findings
        success = self.load_from_database(run_id)

        if success:
            return {
                "status": "loaded",
                "loaded": True,
                "run_id": run_id,
                "statistics": {
                    "current_state": len(self.current_state),
                    "risks": len(self.risks),
                    "gaps": len(self.gaps),
                    "assumptions": len(self.assumptions),
                    "work_items": len(self.work_items),
                    "recommendations": len(self.recommendations),
                    "strategic_considerations": len(self.strategic_considerations)
                }
            }
        return {"status": "load_failed", "loaded": False, "run_id": run_id}

    def identify_new_vs_existing(self, new_findings: List[Dict], finding_type: str,
                                   similarity_threshold: float = 0.85) -> Dict[str, List[Dict]]:
        """
        Point 71: Identify what's new vs. existing in a set of findings.

        Args:
            new_findings: List of new findings to compare
            finding_type: Type of finding ('risk', 'gap', 'assumption', 'current_state', etc.)
            similarity_threshold: Threshold for considering findings similar (0.0-1.0)

        Returns:
            Dict with 'new', 'existing', and 'updated' lists
        """
        # Map finding type to collection and key field
        type_map = {
            'risk': (self.risks, 'risk'),
            'gap': (self.gaps, 'gap'),
            'assumption': (self.assumptions, 'assumption'),
            'current_state': (self.current_state, 'summary'),
            'strategic_consideration': (self.strategic_considerations, 'theme'),
            'work_item': (self.work_items, 'title'),
            'recommendation': (self.recommendations, 'recommendation')
        }

        if finding_type not in type_map:
            raise ValueError(f"Unknown finding type: {finding_type}")

        existing_collection, key_field = type_map[finding_type]

        result = {
            'new': [],
            'existing': [],
            'updated': []  # Similar but with changes
        }

        for new_item in new_findings:
            new_text = new_item.get(key_field, '').lower().strip()
            new_domain = new_item.get('domain', '')

            best_match = None
            best_score = 0.0

            # Compare against existing items in same domain
            for existing_item in existing_collection:
                if existing_item.get('domain') != new_domain:
                    continue

                existing_text = existing_item.get(key_field, '').lower().strip()
                score = SequenceMatcher(None, new_text, existing_text).ratio()

                if score > best_score:
                    best_score = score
                    best_match = existing_item

            if best_score >= similarity_threshold:
                # Check if there are meaningful differences
                if self._has_meaningful_changes(new_item, best_match):
                    result['updated'].append({
                        'new': new_item,
                        'existing': best_match,
                        'similarity': best_score
                    })
                else:
                    result['existing'].append({
                        'finding': new_item,
                        'matched_to': best_match['id'],
                        'similarity': best_score
                    })
            else:
                result['new'].append(new_item)

        return result

    def _has_meaningful_changes(self, new_item: Dict, existing_item: Dict) -> bool:
        """Check if two similar findings have meaningful differences"""
        # Fields that indicate meaningful changes
        change_fields = ['severity', 'likelihood', 'priority', 'maturity',
                        'cost_estimate_range', 'effort_estimate', 'phase']

        for field in change_fields:
            if field in new_item and field in existing_item:
                if new_item[field] != existing_item[field]:
                    return True
        return False

    def merge_findings(self, new_findings: List[Dict], finding_type: str,
                       strategy: str = 'update') -> Dict[str, Any]:
        """
        Point 72: Merge new findings with existing ones.

        Args:
            new_findings: List of new findings to merge
            finding_type: Type of finding
            strategy: 'update' (replace existing), 'append' (keep both), 'newest' (keep newer)

        Returns:
            Dict with merge results and any conflicts
        """
        comparison = self.identify_new_vs_existing(new_findings, finding_type)

        merge_result = {
            'added': 0,
            'updated': 0,
            'skipped': 0,
            'conflicts': []
        }

        # Map finding type to collection
        type_to_collection = {
            'risk': 'risks',
            'gap': 'gaps',
            'assumption': 'assumptions',
            'current_state': 'current_state',
            'strategic_consideration': 'strategic_considerations',
            'work_item': 'work_items',
            'recommendation': 'recommendations'
        }

        collection_name = type_to_collection.get(finding_type)
        if not collection_name:
            raise ValueError(f"Unknown finding type: {finding_type}")

        collection = getattr(self, collection_name)

        # Add genuinely new findings
        for new_item in comparison['new']:
            # Generate ID if needed
            if 'id' not in new_item:
                new_item['id'] = self._next_id(finding_type)
            new_item['_merged_at'] = datetime.now().isoformat()
            new_item['_merge_status'] = 'new'
            collection.append(new_item)
            merge_result['added'] += 1

        # Handle updates based on strategy
        for update_info in comparison['updated']:
            new_item = update_info['new']
            existing_item = update_info['existing']

            if strategy == 'update':
                # Update existing item with new data
                existing_idx = next(i for i, x in enumerate(collection) if x.get('id') == existing_item['id'])
                new_item['id'] = existing_item['id']  # Keep same ID
                new_item['_previous_version'] = existing_item.copy()
                new_item['_updated_at'] = datetime.now().isoformat()
                new_item['_merge_status'] = 'updated'
                collection[existing_idx] = new_item
                merge_result['updated'] += 1

            elif strategy == 'append':
                # Keep both versions
                if 'id' not in new_item:
                    new_item['id'] = self._next_id(finding_type)
                new_item['_related_to'] = existing_item['id']
                new_item['_merge_status'] = 'appended'
                collection.append(new_item)
                merge_result['added'] += 1

            elif strategy == 'newest':
                # Keep only if newer (based on timestamp or higher severity)
                if self._is_newer_or_more_severe(new_item, existing_item):
                    existing_idx = next(i for i, x in enumerate(collection) if x.get('id') == existing_item['id'])
                    new_item['id'] = existing_item['id']
                    new_item['_previous_version'] = existing_item.copy()
                    new_item['_merge_status'] = 'superseded'
                    collection[existing_idx] = new_item
                    merge_result['updated'] += 1
                else:
                    merge_result['skipped'] += 1

        # Skip exact duplicates
        merge_result['skipped'] += len(comparison['existing'])

        return merge_result

    def _is_newer_or_more_severe(self, new_item: Dict, existing_item: Dict) -> bool:
        """Determine if new item should supersede existing"""
        severity_order = {'critical': 4, 'high': 3, 'medium': 2, 'low': 1}

        new_severity = severity_order.get(new_item.get('severity', 'low'), 1)
        existing_severity = severity_order.get(existing_item.get('severity', 'low'), 1)

        if new_severity > existing_severity:
            return True

        # Check timestamps if available
        new_time = new_item.get('timestamp', '')
        existing_time = existing_item.get('timestamp', '')
        if new_time and existing_time:
            return new_time > existing_time

        return False

    def flag_conflicts(self) -> List[Dict]:
        """
        Point 73: Flag conflicts/contradictions between findings.

        Detects:
        - Risks with conflicting severity assessments
        - Assumptions that contradict each other
        - Gaps that have been filled but not removed
        - Work items with conflicting phase assignments

        Returns:
            List of conflict descriptions
        """
        conflicts = []

        # Check for severity conflicts in similar risks
        for i, risk1 in enumerate(self.risks):
            for risk2 in self.risks[i+1:]:
                if risk1.get('domain') != risk2.get('domain'):
                    continue

                # Check if risks are about the same thing
                text1 = risk1.get('risk', '').lower()
                text2 = risk2.get('risk', '').lower()
                similarity = SequenceMatcher(None, text1, text2).ratio()

                if similarity > 0.7 and risk1.get('severity') != risk2.get('severity'):
                    conflicts.append({
                        'type': 'severity_conflict',
                        'finding_type': 'risk',
                        'items': [risk1['id'], risk2['id']],
                        'description': f"Similar risks with different severities: {risk1['id']} ({risk1.get('severity')}) vs {risk2['id']} ({risk2.get('severity')})",
                        'recommendation': 'Review and reconcile severity assessments'
                    })

        # Check for contradicting assumptions
        for i, a1 in enumerate(self.assumptions):
            for a2 in self.assumptions[i+1:]:
                if a1.get('domain') != a2.get('domain'):
                    continue

                # Look for opposing language
                text1 = a1.get('assumption', '').lower()
                text2 = a2.get('assumption', '').lower()

                # Simple contradiction detection
                opposing_pairs = [
                    ('will', 'will not'), ('can', 'cannot'), ('has', 'lacks'),
                    ('adequate', 'inadequate'), ('sufficient', 'insufficient')
                ]

                for pos, neg in opposing_pairs:
                    if (pos in text1 and neg in text2) or (neg in text1 and pos in text2):
                        similarity = SequenceMatcher(None, text1.replace(pos, '').replace(neg, ''),
                                                    text2.replace(pos, '').replace(neg, '')).ratio()
                        if similarity > 0.5:
                            conflicts.append({
                                'type': 'contradicting_assumptions',
                                'finding_type': 'assumption',
                                'items': [a1['id'], a2['id']],
                                'description': f"Potentially contradicting assumptions: {a1['id']} vs {a2['id']}",
                                'recommendation': 'Validate which assumption is correct'
                            })

        # Check for work items with conflicting dependencies
        work_item_phases = {w['id']: w.get('phase', 'Day_100') for w in self.work_items}
        phase_order = {'Day_1': 1, 'Day_100': 2, 'Post_100': 3, 'Optional': 4}

        for item in self.work_items:
            item_phase = item.get('phase', 'Day_100')
            for dep_id in item.get('depends_on', []):
                if dep_id in work_item_phases:
                    dep_phase = work_item_phases[dep_id]
                    if phase_order.get(dep_phase, 2) > phase_order.get(item_phase, 2):
                        conflicts.append({
                            'type': 'dependency_conflict',
                            'finding_type': 'work_item',
                            'items': [item['id'], dep_id],
                            'description': f"{item['id']} ({item_phase}) depends on {dep_id} ({dep_phase}) - invalid sequence",
                            'recommendation': f"Move {item['id']} to {dep_phase} or later, or move {dep_id} earlier"
                        })

        return conflicts

    def track_status_changes(self, previous_run_id: str = None) -> Dict[str, Any]:
        """
        Point 74: Track finding status changes over time.

        Compares current state against a previous run to identify:
        - New findings
        - Removed findings
        - Changed findings (severity, priority, etc.)
        - Resolved gaps

        Args:
            previous_run_id: Run to compare against (default: latest completed)

        Returns:
            Dict with change summary
        """
        self._require_database("track_status_changes")

        # Get previous run's findings
        if previous_run_id is None:
            latest_run = self._repository.get_latest_run()
            if latest_run is None:
                return {"status": "no_previous_runs", "changes": {}}
            previous_run_id = latest_run.run_id

        previous_findings = self._repository.get_all_findings_for_run(previous_run_id)

        changes = {
            'compared_to_run': previous_run_id,
            'risks': {'added': [], 'removed': [], 'severity_changed': []},
            'gaps': {'added': [], 'removed': [], 'resolved': []},
            'assumptions': {'added': [], 'removed': [], 'validated': [], 'invalidated': []},
            'work_items': {'added': [], 'removed': [], 'phase_changed': []},
            'summary': {}
        }

        # Helper to compare lists
        def compare_findings(current: List, previous: List, key_field: str, finding_type: str):
            current_ids = {f.get('id') for f in current}
            previous_ids = {self._get_id(f) for f in previous}

            added = [f for f in current if f.get('id') not in previous_ids]
            removed_ids = previous_ids - current_ids

            return added, list(removed_ids)

        # Compare each finding type
        for ftype, (current_list, prev_key, key_field) in {
            'risks': (self.risks, 'risks', 'risk'),
            'gaps': (self.gaps, 'gaps', 'gap'),
            'assumptions': (self.assumptions, 'assumptions', 'assumption'),
            'work_items': (self.work_items, 'work_items', 'title')
        }.items():
            prev_list = previous_findings.get(prev_key, [])
            added, removed = compare_findings(current_list, prev_list, key_field, ftype)
            changes[ftype]['added'] = [f.get('id') for f in added]
            changes[ftype]['removed'] = removed

        # Track specific changes for risks (severity)
        prev_risks = {self._get_id(r): r for r in previous_findings.get('risks', [])}
        for risk in self.risks:
            rid = risk.get('id')
            if rid in prev_risks:
                prev_severity = self._get_field(prev_risks[rid], 'severity')
                if risk.get('severity') != prev_severity:
                    changes['risks']['severity_changed'].append({
                        'id': rid,
                        'from': prev_severity,
                        'to': risk.get('severity')
                    })

        # Track resolved gaps (gaps that were removed or answered)
        prev_gaps = {self._get_id(g): g for g in previous_findings.get('gaps', [])}
        current_gap_ids = {g.get('id') for g in self.gaps}
        for gap_id in prev_gaps:
            if gap_id not in current_gap_ids:
                changes['gaps']['resolved'].append(gap_id)

        # Summary
        changes['summary'] = {
            'total_risks_added': len(changes['risks']['added']),
            'total_risks_removed': len(changes['risks']['removed']),
            'total_gaps_added': len(changes['gaps']['added']),
            'total_gaps_resolved': len(changes['gaps']['resolved']),
            'severity_escalations': sum(1 for c in changes['risks']['severity_changed']
                                       if self._severity_increased(c['from'], c['to']))
        }

        return changes

    def _get_id(self, finding) -> str:
        """Get ID from finding (handles both dict and model objects)"""
        if hasattr(finding, 'risk_id'):
            return finding.risk_id
        if hasattr(finding, 'gap_id'):
            return finding.gap_id
        if hasattr(finding, 'assumption_id'):
            return finding.assumption_id
        if hasattr(finding, 'work_item_id'):
            return finding.work_item_id
        if hasattr(finding, 'item_id'):
            return finding.item_id
        if isinstance(finding, dict):
            return finding.get('id', '')
        return ''

    def _get_field(self, finding, field: str):
        """Get field from finding (handles both dict and model objects)"""
        if hasattr(finding, field):
            return getattr(finding, field)
        if isinstance(finding, dict):
            return finding.get(field)
        return None

    def _severity_increased(self, old: str, new: str) -> bool:
        """Check if severity increased"""
        order = {'low': 1, 'medium': 2, 'high': 3, 'critical': 4}
        return order.get(new, 0) > order.get(old, 0)

    def merge_from(self, other: 'AnalysisStore') -> Dict[str, int]:
        """
        Merge findings from another AnalysisStore into this one.
        Used for parallel agent execution - each agent has its own store,
        then results are merged into a master store.

        Args:
            other: Another AnalysisStore instance to merge from

        Returns:
            Dict with counts of merged items per category
        """
        import logging
        logger = logging.getLogger(__name__)

        counts = {
            'current_state': 0,
            'risks': 0,
            'gaps': 0,
            'questions': 0,
            'assumptions': 0,
            'work_items': 0,
            'recommendations': 0,
            'strategic_considerations': 0,
            'domain_summaries': 0,
            'reasoning_chains': 0,
            'skipped_invalid': 0
        }

        def validate_and_append(source_list, target_list, list_name):
            """Helper to validate items before appending"""
            valid_count = 0
            for item in source_list:
                if isinstance(item, dict):
                    target_list.append(item)
                    valid_count += 1
                else:
                    logger.warning(f"Skipping invalid {list_name} item (type={type(item).__name__}): {str(item)[:100]}")
                    counts['skipped_invalid'] += 1
            return valid_count

        # Merge current state entries
        counts['current_state'] = validate_and_append(other.current_state, self.current_state, 'current_state')

        # Merge risks
        counts['risks'] = validate_and_append(other.risks, self.risks, 'risk')

        # Merge gaps
        counts['gaps'] = validate_and_append(other.gaps, self.gaps, 'gap')

        # Merge questions
        counts['questions'] = validate_and_append(other.questions, self.questions, 'question')

        # Merge assumptions
        counts['assumptions'] = validate_and_append(other.assumptions, self.assumptions, 'assumption')

        # Merge work items
        counts['work_items'] = validate_and_append(other.work_items, self.work_items, 'work_item')

        # Merge recommendations
        counts['recommendations'] = validate_and_append(other.recommendations, self.recommendations, 'recommendation')

        # Merge strategic considerations
        counts['strategic_considerations'] = validate_and_append(other.strategic_considerations, self.strategic_considerations, 'strategic_consideration')

        # Merge domain summaries
        for domain, summary in other.domain_summaries.items():
            self.domain_summaries[domain] = summary
            counts['domain_summaries'] += 1

        # Merge reasoning chains
        for domain, entries in other.reasoning_chains.items():
            if domain not in self.reasoning_chains:
                self.reasoning_chains[domain] = []
            self.reasoning_chains[domain].extend(entries)
            counts['reasoning_chains'] += len(entries)

        return counts

    def get_all(self) -> Dict:
        """Get all findings with validation"""
        # Enrich before returning
        self.enrich_outputs()

        # Validate
        validation = self.validate_outputs()

        # Group risks by type
        risks_by_type = self.get_risks_by_type()
        standalone_risks = self.get_standalone_risks()

        # Group work items by phase
        work_items_by_phase = self.get_work_items_by_phase()

        # Step 50: Get capability summary for applications
        capability_summary = self.get_capability_summary()

        return {
            # =================================================================
            # APPLICATION INVENTORY (Phase 4: Step 50)
            # =================================================================
            "applications": self.applications,
            "applications_by_category": self.get_applications_by_category(),
            "applications_by_criticality": self.get_applications_by_criticality(),
            "capability_coverage": self.capability_coverage,
            "capability_summary": capability_summary,
            "all_follow_up_questions": self.get_all_follow_up_questions(),

            # =================================================================
            # FOUR-LENS FRAMEWORK
            # =================================================================
            # Lens 1
            "current_state": self.current_state,
            # Lens 2
            "risks": self.risks,
            "risks_by_type": risks_by_type,
            "standalone_risks": standalone_risks,
            # Lens 3
            "strategic_considerations": self.strategic_considerations,
            # Lens 4
            "work_items": self.work_items,
            "work_items_by_phase": work_items_by_phase,
            "recommendations": self.recommendations,
            # Supporting
            "assumptions": self.assumptions,
            "gaps": self.gaps,
            "questions": self.questions,
            "domain_summaries": self.domain_summaries,
            "executive_summary": self.executive_summary,
            # Meta
            "statistics": {
                # Application inventory stats
                "total_applications": len(self.applications),
                "capabilities_assessed": len(self.capability_coverage),
                "capabilities_total": len(CAPABILITY_AREAS),
                "capability_completeness_pct": capability_summary.get("completeness_percentage", 0),
                "total_follow_up_questions": len(self.get_all_follow_up_questions()),
                # Four-lens stats
                "total_current_state": len(self.current_state),
                "total_assumptions": len(self.assumptions),
                "total_gaps": len(self.gaps),
                "total_questions": len(self.questions),
                "total_risks": len(self.risks),
                "standalone_risks": len(standalone_risks),
                "integration_risks": len(self.risks) - len(standalone_risks),
                "total_strategic_considerations": len(self.strategic_considerations),
                "total_work_items": len(self.work_items),
                "total_recommendations": len(self.recommendations),
                "domains_analyzed": list(self.domain_summaries.keys())
            },
            "validation": validation
        }

    def save(self, output_dir: str):
        """Save all findings to JSON files with validation report"""
        from pathlib import Path
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Validate before saving
        validation = self.validate_outputs()

        # Individual files (organized by lens)
        files = {
            # Lens 1
            "current_state.json": self.current_state,
            # Lens 2
            "risks.json": self.risks,
            # Lens 3
            "strategic_considerations.json": self.strategic_considerations,
            # Lens 4
            "work_items.json": self.work_items,
            "recommendations.json": self.recommendations,
            # Supporting
            "assumptions.json": self.assumptions,
            "gaps.json": self.gaps,
            "questions.json": self.questions,
            "domain_summaries.json": self.domain_summaries,
            "validation_report.json": validation
        }

        for filename, data in files.items():
            with open(output_dir / filename, 'w') as f:
                json.dump(data, f, indent=2)

        # Save executive summary if present
        if self.executive_summary:
            with open(output_dir / "executive_summary.json", 'w') as f:
                json.dump(self.executive_summary, f, indent=2)
            self._save_executive_summary_markdown(output_dir)

        # Save reasoning chains
        if self.reasoning_chains:
            with open(output_dir / "reasoning_chains.json", 'w') as f:
                json.dump(self.reasoning_chains, f, indent=2)
            self._save_reasoning_narrative(output_dir)

        # Combined output
        with open(output_dir / "analysis_output.json", 'w') as f:
            json.dump(self.get_all(), f, indent=2)

        # Count totals
        total_reasoning = sum(len(entries) for entries in self.reasoning_chains.values())
        standalone_count = len(self.get_standalone_risks())

        print(f"\n✓ Analysis saved to {output_dir}/")
        print(f"  - {len(self.current_state)} current state entries")
        print(f"  - {len(self.assumptions)} assumptions")
        print(f"  - {len(self.gaps)} gaps")
        print(f"  - {len(self.risks)} risks ({standalone_count} standalone)")
        print(f"  - {len(self.strategic_considerations)} strategic considerations")
        print(f"  - {len(self.work_items)} work items")
        print(f"  - {len(self.recommendations)} recommendations")
        print(f"  - {total_reasoning} reasoning chain entries")
        print(f"  - Quality Score: {validation['quality_score']:.1f}/100")
        if validation['issues']:
            print(f"  - ⚠️  {len(validation['issues'])} validation issues")
        if validation['warnings']:
            print(f"  - ⚠️  {len(validation['warnings'])} warnings")

    def _save_executive_summary_markdown(self, output_dir):
        """Save IC-ready executive summary as markdown"""
        from pathlib import Path
        output_dir = Path(output_dir)

        if not self.executive_summary:
            return

        es = self.executive_summary
        lines = []
        lines.append("# Executive Summary")
        lines.append("")
        lines.append("*Investment Committee Ready*")
        lines.append("")

        # Overall assessment
        complexity = es.get("overall_complexity", "unknown")
        cost = es.get("total_estimated_cost_range", "TBD")
        timeline = es.get("estimated_timeline", "TBD")
        recommendation = es.get("deal_recommendation", "TBD")

        lines.append(f"**Overall Complexity:** {complexity.upper()}")
        lines.append(f"**Estimated Investment:** {cost}")
        lines.append(f"**Timeline:** {timeline}")
        lines.append(f"**Recommendation:** {recommendation.replace('_', ' ').title()}")
        lines.append("")

        # Key findings
        if es.get("key_findings"):
            lines.append("## Key Findings")
            for finding in es["key_findings"]:
                lines.append(f"- {finding}")
            lines.append("")

        # Critical risks
        if es.get("critical_risks"):
            lines.append("## Critical Risks")
            for risk in es["critical_risks"]:
                lines.append(f"- {risk}")
            lines.append("")

        # Immediate actions
        if es.get("immediate_actions"):
            lines.append("## Immediate Actions (Pre-Close)")
            for action in es["immediate_actions"]:
                lines.append(f"- {action}")
            lines.append("")

        # Day 1 requirements
        if es.get("day_1_requirements"):
            lines.append("## Day 1 Requirements")
            for req in es["day_1_requirements"]:
                lines.append(f"- {req}")
            lines.append("")

        # Key unknowns
        if es.get("key_unknowns"):
            lines.append("## Key Unknowns")
            for unknown in es["key_unknowns"]:
                lines.append(f"- {unknown}")
            lines.append("")

        with open(output_dir / "EXECUTIVE_SUMMARY.md", 'w') as f:
            f.write("\n".join(lines))

    def _save_reasoning_narrative(self, output_dir):
        """Save a human-readable narrative of the reasoning chains"""
        from pathlib import Path
        output_dir = Path(output_dir)

        lines = []
        lines.append("# Analysis Reasoning Chain")
        lines.append("")
        lines.append("This document shows the logic flow from document observations to findings.")
        lines.append("Each entry shows: what Claude observed → what it concluded → the finding created.")
        lines.append("")

        for domain in ["infrastructure", "network", "cybersecurity"]:
            entries = self.reasoning_chains.get(domain, [])
            if not entries:
                continue

            lines.append(f"## {domain.title()} Domain")
            lines.append("")

            for entry in entries:
                finding_id = entry.get("finding_id", "Unknown")
                finding_type = entry.get("finding_type", "unknown")
                finding_summary = entry.get("finding_summary", "")
                reasoning = entry.get("reasoning_text", "")
                evidence = entry.get("evidence_from_finding", "")
                iteration = entry.get("iteration", 0)

                lines.append(f"### {finding_id} ({finding_type})")
                lines.append("")
                lines.append(f"**Finding:** {finding_summary}")
                lines.append("")
                lines.append(f"**Reasoning (Iteration {iteration}):**")
                lines.append("```")
                lines.append(reasoning[:2000] + "..." if len(reasoning) > 2000 else reasoning)
                lines.append("```")
                lines.append("")
                if evidence:
                    lines.append(f"**Evidence/Basis:** {evidence}")
                    lines.append("")
                lines.append("---")
                lines.append("")

        with open(output_dir / "REASONING_NARRATIVE.md", 'w') as f:
            f.write("\n".join(lines))


# =============================================================================
# COORDINATOR TOOLS (additional tools for roll-up agent)
# =============================================================================

COORDINATOR_TOOLS = ANALYSIS_TOOLS + [
    {
        "name": "create_executive_summary",
        "description": """Create the final executive summary that synthesizes all domain findings.
        This is the primary output for deal team leadership and Investment Committee.""",
        "input_schema": {
            "type": "object",
            "properties": {
                "overall_complexity": {
                    "type": "string",
                    "enum": ["low", "medium", "high", "very_high"],
                    "description": "Overall integration complexity"
                },
                "total_estimated_cost_range": {
                    "type": "string",
                    "description": "Total one-time cost estimate (e.g., '$2M-$4M')"
                },
                "estimated_timeline": {
                    "type": "string",
                    "description": "Overall timeline estimate (e.g., '18-24 months')"
                },
                "deal_recommendation": {
                    "type": "string",
                    "enum": ["proceed", "proceed_with_caution", "significant_concerns", "reconsider"],
                    "description": "Overall deal recommendation from IT perspective"
                },
                "key_findings": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Top 5-7 key findings for leadership (no jargon)"
                },
                "critical_risks": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Risks that could materially impact the deal"
                },
                "immediate_actions": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Actions to take before close"
                },
                "day_1_requirements": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "What must be ready for Day 1"
                },
                "synergy_opportunities": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Cost savings or value creation opportunities"
                },
                "confidence_level": {
                    "type": "string",
                    "enum": ["high", "medium", "low"],
                    "description": "Confidence in estimates given available information"
                },
                "key_unknowns": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Critical unknowns that could change the assessment"
                }
            },
            "required": ["overall_complexity", "total_estimated_cost_range", "deal_recommendation",
                        "key_findings", "critical_risks", "confidence_level"]
        }
    },
    {
        "name": "identify_cross_domain_dependency",
        "description": """Identify a dependency or interaction between domains that affects sequencing or risk.""",
        "input_schema": {
            "type": "object",
            "properties": {
                "dependency": {
                    "type": "string",
                    "description": "Description of the cross-domain dependency"
                },
                "source_domain": {
                    "type": "string",
                    "description": "Domain that must happen first or provides input"
                },
                "target_domain": {
                    "type": "string",
                    "description": "Domain that depends on the source"
                },
                "impact": {
                    "type": "string",
                    "description": "What happens if this dependency isn't managed"
                },
                "sequencing_requirement": {
                    "type": "string",
                    "description": "How this affects project sequencing"
                }
            },
            "required": ["dependency", "source_domain", "target_domain", "impact"]
        }
    }
]
