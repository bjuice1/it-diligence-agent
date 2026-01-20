"""
Activity Templates V2 - Phase 3: Applications

Phase 3: Application Workstream (Deep Dive)
- ERP (SAP, Oracle, NetSuite, Dynamics)
- CRM (Salesforce, Dynamics CRM, HubSpot)
- HR/HCM (Workday, ADP, UKG, SAP SuccessFactors)
- Custom/Legacy Applications
- SaaS Portfolio

This is often the largest cost driver in carveouts.

Each activity template includes:
- name: Activity name
- description: What this activity involves
- activity_type: "implementation", "operational", "license"
- cost_model: How cost is calculated
- timeline_months: Duration range
- requires_tsa: Whether TSA is typically needed
- tsa_duration: TSA duration if applicable
- prerequisites: What must happen first
- outputs: Deliverables
- notes: Implementation considerations

Cost Anchor Sources:
- ERP implementation partner rates
- SaaS vendor migration services
- System integrator pricing
- Historical deal data
"""

from typing import Dict, List, Any

# Import shared modifiers from Phase 1
from tools_v2.activity_templates_v2 import COMPLEXITY_MULTIPLIERS, INDUSTRY_MODIFIERS

# =============================================================================
# PHASE 3: ERP WORKSTREAM
# =============================================================================

ERP_TEMPLATES = {
    "parent_dependency": [
        # -----------------------------------------------------------------
        # ASSESSMENT
        # -----------------------------------------------------------------
        {
            "id": "ERP-001",
            "name": "ERP landscape assessment",
            "description": "Assess current ERP landscape, instances, and dependencies",
            "activity_type": "implementation",
            "phase": "assessment",
            "base_cost": (50000, 125000),
            "timeline_months": (1, 2),
            "requires_tsa": False,
            "prerequisites": [],
            "outputs": ["ERP inventory", "Instance topology", "Module inventory", "Integration map"],
            "notes": "Critical for understanding separation complexity",
        },
        {
            "id": "ERP-002",
            "name": "ERP data segmentation analysis",
            "description": "Analyze data ownership and segmentation requirements",
            "activity_type": "implementation",
            "phase": "assessment",
            "base_cost": (40000, 100000),
            "timeline_months": (1, 2),
            "requires_tsa": False,
            "prerequisites": ["ERP-001"],
            "outputs": ["Data ownership matrix", "Segmentation approach", "Master data strategy"],
        },
        {
            "id": "ERP-003",
            "name": "ERP integration mapping",
            "description": "Map all integrations to/from ERP systems",
            "activity_type": "implementation",
            "phase": "assessment",
            "per_integration_cost": (1000, 3000),
            "base_cost": (25000, 60000),
            "timeline_months": (0.5, 1.5),
            "requires_tsa": False,
            "prerequisites": ["ERP-001"],
            "outputs": ["Integration inventory", "Data flow diagrams", "API documentation"],
        },
        {
            "id": "ERP-004",
            "name": "ERP customization inventory",
            "description": "Inventory custom code, reports, and configurations",
            "activity_type": "implementation",
            "phase": "assessment",
            "base_cost": (30000, 80000),
            "timeline_months": (0.5, 1.5),
            "requires_tsa": False,
            "prerequisites": ["ERP-001"],
            "outputs": ["Custom code inventory", "Report inventory", "Configuration documentation"],
        },
        {
            "id": "ERP-005",
            "name": "ERP license entitlement analysis",
            "description": "Analyze license entitlements and transfer/procurement requirements",
            "activity_type": "implementation",
            "phase": "assessment",
            "base_cost": (20000, 50000),
            "timeline_months": (0.5, 1),
            "requires_tsa": False,
            "prerequisites": ["ERP-001"],
            "outputs": ["License inventory", "Entitlement analysis", "Procurement requirements"],
        },
        {
            "id": "ERP-006",
            "name": "ERP separation strategy design",
            "description": "Design ERP separation approach and target architecture",
            "activity_type": "implementation",
            "phase": "design",
            "base_cost": (75000, 200000),
            "timeline_months": (1, 3),
            "requires_tsa": False,
            "prerequisites": ["ERP-001", "ERP-002", "ERP-003", "ERP-004"],
            "outputs": ["Separation strategy", "Target architecture", "Implementation roadmap"],
            "notes": "Key decision point - clone vs new instance vs TSA extension",
        },
        # -----------------------------------------------------------------
        # SAP SPECIFIC
        # -----------------------------------------------------------------
        {
            "id": "ERP-010",
            "name": "SAP system copy and carve",
            "description": "Clone SAP system and carve out target company data",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (200000, 500000),
            "timeline_months": (3, 6),
            "requires_tsa": True,
            "tsa_duration": (6, 12),
            "prerequisites": ["ERP-006"],
            "outputs": ["Cloned SAP system", "Carved data set", "Validation reports"],
            "notes": "Complex activity - requires SAP Basis expertise",
        },
        {
            "id": "ERP-011",
            "name": "SAP new instance implementation",
            "description": "Implement new SAP instance for standalone operations",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (500000, 2000000),
            "timeline_months": (6, 18),
            "requires_tsa": True,
            "tsa_duration": (12, 24),
            "prerequisites": ["ERP-006"],
            "outputs": ["New SAP instance", "Configuration", "Master data", "Testing"],
            "notes": "Major undertaking - typically requires TSA extension",
        },
        {
            "id": "ERP-012",
            "name": "SAP data migration",
            "description": "Migrate data from parent to new SAP environment",
            "activity_type": "implementation",
            "phase": "migration",
            "base_cost": (100000, 300000),
            "timeline_months": (2, 6),
            "requires_tsa": True,
            "tsa_duration": (6, 12),
            "prerequisites": ["ERP-010"],
            "outputs": ["Migrated master data", "Migrated transactional data", "Data validation"],
        },
        {
            "id": "ERP-013",
            "name": "SAP integration rebuild",
            "description": "Rebuild integrations for standalone SAP environment",
            "activity_type": "implementation",
            "phase": "build",
            "per_integration_cost": (5000, 20000),
            "base_cost": (50000, 150000),
            "timeline_months": (2, 6),
            "requires_tsa": True,
            "tsa_duration": (6, 12),
            "prerequisites": ["ERP-010"],
            "outputs": ["Rebuilt integrations", "API configurations", "Testing validation"],
        },
        {
            "id": "ERP-014",
            "name": "SAP custom development migration",
            "description": "Migrate custom ABAP code and enhancements",
            "activity_type": "implementation",
            "phase": "migration",
            "base_cost": (75000, 250000),
            "timeline_months": (2, 6),
            "requires_tsa": True,
            "tsa_duration": (6, 12),
            "prerequisites": ["ERP-010", "ERP-004"],
            "outputs": ["Migrated custom code", "Testing validation", "Documentation"],
        },
        # -----------------------------------------------------------------
        # ORACLE SPECIFIC
        # -----------------------------------------------------------------
        {
            "id": "ERP-020",
            "name": "Oracle EBS/Cloud instance separation",
            "description": "Separate Oracle ERP instance for standalone operations",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (200000, 600000),
            "timeline_months": (4, 10),
            "requires_tsa": True,
            "tsa_duration": (6, 12),
            "prerequisites": ["ERP-006"],
            "outputs": ["Separated Oracle instance", "Data carve", "Configuration"],
        },
        {
            "id": "ERP-021",
            "name": "Oracle data extraction and migration",
            "description": "Extract and migrate Oracle ERP data",
            "activity_type": "implementation",
            "phase": "migration",
            "base_cost": (100000, 300000),
            "timeline_months": (2, 6),
            "requires_tsa": True,
            "tsa_duration": (6, 12),
            "prerequisites": ["ERP-020"],
            "outputs": ["Extracted data", "Migrated data", "Validation reports"],
        },
        # -----------------------------------------------------------------
        # MID-MARKET ERP (NetSuite, Dynamics)
        # -----------------------------------------------------------------
        {
            "id": "ERP-030",
            "name": "NetSuite account separation",
            "description": "Separate or provision new NetSuite account",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (75000, 200000),
            "timeline_months": (2, 5),
            "requires_tsa": True,
            "tsa_duration": (3, 6),
            "prerequisites": ["ERP-006"],
            "outputs": ["New NetSuite account", "Configuration", "Data migration"],
        },
        {
            "id": "ERP-031",
            "name": "Dynamics 365 F&O tenant separation",
            "description": "Separate or provision Dynamics 365 Finance & Operations",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (100000, 300000),
            "timeline_months": (3, 8),
            "requires_tsa": True,
            "tsa_duration": (6, 12),
            "prerequisites": ["ERP-006"],
            "outputs": ["New D365 environment", "Configuration", "Data migration"],
        },
        {
            "id": "ERP-032",
            "name": "Dynamics GP/NAV migration",
            "description": "Migrate Dynamics GP or NAV to standalone environment",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (50000, 150000),
            "timeline_months": (2, 6),
            "requires_tsa": True,
            "tsa_duration": (3, 6),
            "prerequisites": ["ERP-006"],
            "outputs": ["Migrated system", "Data migration", "Configuration"],
        },
        # -----------------------------------------------------------------
        # TESTING & CUTOVER
        # -----------------------------------------------------------------
        {
            "id": "ERP-040",
            "name": "ERP functional testing",
            "description": "Execute functional testing of separated ERP",
            "activity_type": "implementation",
            "phase": "testing",
            "base_cost": (50000, 150000),
            "timeline_months": (1, 3),
            "requires_tsa": False,
            "prerequisites": ["ERP-010", "ERP-012"],
            "outputs": ["Test scripts", "Test execution", "Defect resolution"],
        },
        {
            "id": "ERP-041",
            "name": "ERP integration testing",
            "description": "Execute end-to-end integration testing",
            "activity_type": "implementation",
            "phase": "testing",
            "base_cost": (40000, 100000),
            "timeline_months": (1, 2),
            "requires_tsa": False,
            "prerequisites": ["ERP-040", "ERP-013"],
            "outputs": ["Integration test scripts", "Test execution", "Defect resolution"],
        },
        {
            "id": "ERP-042",
            "name": "ERP performance testing",
            "description": "Execute performance and load testing",
            "activity_type": "implementation",
            "phase": "testing",
            "base_cost": (30000, 80000),
            "timeline_months": (0.5, 1.5),
            "requires_tsa": False,
            "prerequisites": ["ERP-040"],
            "outputs": ["Performance baselines", "Load test results", "Optimization recommendations"],
        },
        {
            "id": "ERP-043",
            "name": "ERP user acceptance testing",
            "description": "Facilitate user acceptance testing",
            "activity_type": "implementation",
            "phase": "testing",
            "base_cost": (25000, 75000),
            "timeline_months": (1, 2),
            "requires_tsa": False,
            "prerequisites": ["ERP-040"],
            "outputs": ["UAT scripts", "UAT execution", "Sign-off"],
        },
        {
            "id": "ERP-044",
            "name": "ERP cutover planning and execution",
            "description": "Plan and execute ERP cutover",
            "activity_type": "implementation",
            "phase": "cutover",
            "base_cost": (50000, 150000),
            "timeline_months": (0.5, 1),
            "requires_tsa": False,
            "prerequisites": ["ERP-043"],
            "outputs": ["Cutover plan", "Execution", "Validation"],
            "notes": "High-risk activity - typically weekend execution",
        },
        {
            "id": "ERP-045",
            "name": "ERP hypercare support",
            "description": "Post-go-live hypercare support period",
            "activity_type": "implementation",
            "phase": "cutover",
            "base_cost": (40000, 120000),
            "timeline_months": (1, 3),
            "requires_tsa": False,
            "prerequisites": ["ERP-044"],
            "outputs": ["Hypercare support", "Issue resolution", "Stabilization"],
        },
    ],
}

# =============================================================================
# PHASE 3: CRM WORKSTREAM
# =============================================================================

CRM_TEMPLATES = {
    "parent_dependency": [
        # -----------------------------------------------------------------
        # ASSESSMENT
        # -----------------------------------------------------------------
        {
            "id": "CRM-001",
            "name": "CRM landscape assessment",
            "description": "Assess current CRM systems and dependencies",
            "activity_type": "implementation",
            "phase": "assessment",
            "base_cost": (25000, 60000),
            "timeline_months": (0.5, 1.5),
            "requires_tsa": False,
            "prerequisites": [],
            "outputs": ["CRM inventory", "User analysis", "Customization inventory", "Integration map"],
        },
        {
            "id": "CRM-002",
            "name": "CRM data ownership analysis",
            "description": "Analyze customer data ownership and segmentation",
            "activity_type": "implementation",
            "phase": "assessment",
            "base_cost": (20000, 50000),
            "timeline_months": (0.5, 1),
            "requires_tsa": False,
            "prerequisites": ["CRM-001"],
            "outputs": ["Data ownership matrix", "Customer segmentation", "Data quality assessment"],
        },
        {
            "id": "CRM-003",
            "name": "CRM separation strategy design",
            "description": "Design CRM separation approach",
            "activity_type": "implementation",
            "phase": "design",
            "base_cost": (30000, 75000),
            "timeline_months": (0.5, 1.5),
            "requires_tsa": False,
            "prerequisites": ["CRM-001", "CRM-002"],
            "outputs": ["Separation strategy", "Target architecture", "Implementation approach"],
        },
        # -----------------------------------------------------------------
        # SALESFORCE
        # -----------------------------------------------------------------
        {
            "id": "CRM-010",
            "name": "Salesforce org provisioning",
            "description": "Provision new Salesforce org for standalone operations",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (40000, 100000),
            "timeline_months": (1, 2),
            "requires_tsa": False,
            "prerequisites": ["CRM-003"],
            "outputs": ["New Salesforce org", "Admin setup", "Base configuration"],
        },
        {
            "id": "CRM-011",
            "name": "Salesforce configuration migration",
            "description": "Migrate Salesforce configuration and customizations",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (50000, 150000),
            "timeline_months": (1, 3),
            "requires_tsa": True,
            "tsa_duration": (3, 6),
            "prerequisites": ["CRM-010"],
            "outputs": ["Migrated objects", "Workflows", "Validation rules", "Page layouts"],
        },
        {
            "id": "CRM-012",
            "name": "Salesforce data migration",
            "description": "Migrate customer and sales data to new org",
            "activity_type": "implementation",
            "phase": "migration",
            "per_record_cost": (0.05, 0.20),
            "base_cost": (30000, 80000),
            "timeline_months": (1, 3),
            "requires_tsa": True,
            "tsa_duration": (3, 6),
            "prerequisites": ["CRM-011"],
            "outputs": ["Migrated accounts", "Migrated contacts", "Migrated opportunities", "Historical data"],
            "notes": "Cost depends on data volume and complexity",
        },
        {
            "id": "CRM-013",
            "name": "Salesforce integration rebuild",
            "description": "Rebuild integrations for new Salesforce org",
            "activity_type": "implementation",
            "phase": "build",
            "per_integration_cost": (3000, 12000),
            "base_cost": (20000, 50000),
            "timeline_months": (1, 3),
            "requires_tsa": True,
            "tsa_duration": (3, 6),
            "prerequisites": ["CRM-010"],
            "outputs": ["Rebuilt integrations", "API configurations", "Testing"],
        },
        {
            "id": "CRM-014",
            "name": "Salesforce AppExchange app migration",
            "description": "Migrate or replace AppExchange applications",
            "activity_type": "implementation",
            "phase": "build",
            "per_app_cost": (2000, 8000),
            "timeline_months": (0.5, 2),
            "requires_tsa": False,
            "prerequisites": ["CRM-010"],
            "outputs": ["Installed apps", "Configuration", "License procurement"],
        },
        # -----------------------------------------------------------------
        # DYNAMICS CRM
        # -----------------------------------------------------------------
        {
            "id": "CRM-020",
            "name": "Dynamics 365 CE environment provisioning",
            "description": "Provision new Dynamics 365 Customer Engagement environment",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (35000, 90000),
            "timeline_months": (1, 2),
            "requires_tsa": False,
            "prerequisites": ["CRM-003"],
            "outputs": ["New D365 CE environment", "Admin setup", "Base configuration"],
        },
        {
            "id": "CRM-021",
            "name": "Dynamics CRM solution migration",
            "description": "Migrate Dynamics solutions and customizations",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (40000, 120000),
            "timeline_months": (1, 3),
            "requires_tsa": True,
            "tsa_duration": (3, 6),
            "prerequisites": ["CRM-020"],
            "outputs": ["Migrated solutions", "Workflows", "Business rules", "Forms"],
        },
        {
            "id": "CRM-022",
            "name": "Dynamics CRM data migration",
            "description": "Migrate CRM data to new environment",
            "activity_type": "implementation",
            "phase": "migration",
            "base_cost": (30000, 80000),
            "timeline_months": (1, 2),
            "requires_tsa": True,
            "tsa_duration": (3, 6),
            "prerequisites": ["CRM-021"],
            "outputs": ["Migrated data", "Data validation", "Relationship mapping"],
        },
        # -----------------------------------------------------------------
        # OTHER CRM
        # -----------------------------------------------------------------
        {
            "id": "CRM-030",
            "name": "HubSpot account separation",
            "description": "Separate or provision new HubSpot account",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (20000, 50000),
            "timeline_months": (0.5, 1.5),
            "requires_tsa": True,
            "tsa_duration": (2, 4),
            "prerequisites": ["CRM-003"],
            "outputs": ["New HubSpot account", "Configuration", "Data migration"],
        },
        {
            "id": "CRM-031",
            "name": "Zoho CRM separation",
            "description": "Separate or provision Zoho CRM environment",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (15000, 40000),
            "timeline_months": (0.5, 1.5),
            "requires_tsa": True,
            "tsa_duration": (2, 4),
            "prerequisites": ["CRM-003"],
            "outputs": ["New Zoho environment", "Configuration", "Data migration"],
        },
        # -----------------------------------------------------------------
        # TESTING & CUTOVER
        # -----------------------------------------------------------------
        {
            "id": "CRM-040",
            "name": "CRM testing and validation",
            "description": "Execute CRM functional and integration testing",
            "activity_type": "implementation",
            "phase": "testing",
            "base_cost": (25000, 60000),
            "timeline_months": (0.5, 1.5),
            "requires_tsa": False,
            "prerequisites": ["CRM-012", "CRM-013"],
            "outputs": ["Test execution", "Defect resolution", "Sign-off"],
        },
        {
            "id": "CRM-041",
            "name": "CRM user training",
            "description": "Train users on new CRM environment",
            "activity_type": "implementation",
            "phase": "cutover",
            "per_user_cost": (50, 150),
            "base_cost": (10000, 25000),
            "timeline_months": (0.5, 1),
            "requires_tsa": False,
            "prerequisites": ["CRM-040"],
            "outputs": ["Training materials", "Training delivery", "User adoption support"],
        },
        {
            "id": "CRM-042",
            "name": "CRM cutover and hypercare",
            "description": "Execute CRM cutover with hypercare support",
            "activity_type": "implementation",
            "phase": "cutover",
            "base_cost": (20000, 50000),
            "timeline_months": (0.5, 1.5),
            "requires_tsa": False,
            "prerequisites": ["CRM-040"],
            "outputs": ["Cutover execution", "Hypercare support", "Stabilization"],
        },
    ],
}

# =============================================================================
# PHASE 3: HR/HCM WORKSTREAM
# =============================================================================

HRHCM_TEMPLATES = {
    "parent_dependency": [
        # -----------------------------------------------------------------
        # ASSESSMENT
        # -----------------------------------------------------------------
        {
            "id": "HCM-001",
            "name": "HR/HCM landscape assessment",
            "description": "Assess current HR systems, processes, and data",
            "activity_type": "implementation",
            "phase": "assessment",
            "base_cost": (30000, 75000),
            "timeline_months": (0.5, 1.5),
            "requires_tsa": False,
            "prerequisites": [],
            "outputs": ["HCM inventory", "Process documentation", "Data inventory", "Integration map"],
        },
        {
            "id": "HCM-002",
            "name": "HR data separation analysis",
            "description": "Analyze employee data ownership and separation requirements",
            "activity_type": "implementation",
            "phase": "assessment",
            "base_cost": (20000, 50000),
            "timeline_months": (0.5, 1),
            "requires_tsa": False,
            "prerequisites": ["HCM-001"],
            "outputs": ["Employee data inventory", "Data ownership", "Privacy requirements", "Historical data needs"],
        },
        {
            "id": "HCM-003",
            "name": "Payroll and benefits analysis",
            "description": "Analyze payroll processing and benefits administration",
            "activity_type": "implementation",
            "phase": "assessment",
            "base_cost": (25000, 60000),
            "timeline_months": (0.5, 1),
            "requires_tsa": False,
            "prerequisites": ["HCM-001"],
            "outputs": ["Payroll requirements", "Benefits inventory", "Vendor analysis", "Compliance requirements"],
        },
        {
            "id": "HCM-004",
            "name": "HR/HCM separation strategy design",
            "description": "Design HR systems separation approach",
            "activity_type": "implementation",
            "phase": "design",
            "base_cost": (35000, 85000),
            "timeline_months": (0.5, 1.5),
            "requires_tsa": False,
            "prerequisites": ["HCM-001", "HCM-002", "HCM-003"],
            "outputs": ["Separation strategy", "Platform selection", "Implementation roadmap"],
        },
        # -----------------------------------------------------------------
        # WORKDAY
        # -----------------------------------------------------------------
        {
            "id": "HCM-010",
            "name": "Workday tenant provisioning",
            "description": "Provision new Workday tenant for standalone operations",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (100000, 300000),
            "timeline_months": (3, 6),
            "requires_tsa": True,
            "tsa_duration": (6, 12),
            "prerequisites": ["HCM-004"],
            "outputs": ["New Workday tenant", "Base configuration", "Security setup"],
            "notes": "Workday implementation typically 6-12 months",
        },
        {
            "id": "HCM-011",
            "name": "Workday configuration and customization",
            "description": "Configure Workday for business requirements",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (150000, 400000),
            "timeline_months": (3, 8),
            "requires_tsa": True,
            "tsa_duration": (6, 12),
            "prerequisites": ["HCM-010"],
            "outputs": ["Business process configuration", "Calculated fields", "Reports", "Integrations"],
        },
        {
            "id": "HCM-012",
            "name": "Workday data migration",
            "description": "Migrate employee data to new Workday tenant",
            "activity_type": "implementation",
            "phase": "migration",
            "per_employee_cost": (100, 300),
            "base_cost": (50000, 150000),
            "timeline_months": (2, 4),
            "requires_tsa": True,
            "tsa_duration": (6, 12),
            "prerequisites": ["HCM-011"],
            "outputs": ["Migrated employee records", "Historical data", "Data validation"],
        },
        # -----------------------------------------------------------------
        # ADP
        # -----------------------------------------------------------------
        {
            "id": "HCM-020",
            "name": "ADP implementation",
            "description": "Implement ADP Workforce Now or similar for standalone payroll/HR",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (50000, 150000),
            "per_employee_cost": (30, 100),
            "timeline_months": (2, 4),
            "requires_tsa": True,
            "tsa_duration": (3, 6),
            "prerequisites": ["HCM-004"],
            "outputs": ["ADP implementation", "Payroll setup", "Benefits configuration"],
        },
        {
            "id": "HCM-021",
            "name": "ADP data migration",
            "description": "Migrate payroll and HR data to ADP",
            "activity_type": "implementation",
            "phase": "migration",
            "per_employee_cost": (50, 150),
            "base_cost": (25000, 75000),
            "timeline_months": (1, 3),
            "requires_tsa": True,
            "tsa_duration": (3, 6),
            "prerequisites": ["HCM-020"],
            "outputs": ["Migrated employee data", "Payroll history", "Tax setup"],
        },
        # -----------------------------------------------------------------
        # UKG (Ultimate Kronos Group)
        # -----------------------------------------------------------------
        {
            "id": "HCM-030",
            "name": "UKG Pro implementation",
            "description": "Implement UKG Pro for HR and payroll",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (75000, 200000),
            "per_employee_cost": (40, 120),
            "timeline_months": (3, 6),
            "requires_tsa": True,
            "tsa_duration": (6, 9),
            "prerequisites": ["HCM-004"],
            "outputs": ["UKG implementation", "Configuration", "Integrations"],
        },
        {
            "id": "HCM-031",
            "name": "UKG time and attendance setup",
            "description": "Configure time and attendance in UKG",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (30000, 80000),
            "timeline_months": (1, 3),
            "requires_tsa": True,
            "tsa_duration": (3, 6),
            "prerequisites": ["HCM-030"],
            "outputs": ["Time tracking configuration", "Scheduling", "Compliance rules"],
        },
        # -----------------------------------------------------------------
        # SAP SUCCESSFACTORS
        # -----------------------------------------------------------------
        {
            "id": "HCM-040",
            "name": "SAP SuccessFactors tenant provisioning",
            "description": "Provision SuccessFactors tenant for standalone HR",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (100000, 250000),
            "timeline_months": (3, 6),
            "requires_tsa": True,
            "tsa_duration": (6, 12),
            "prerequisites": ["HCM-004"],
            "outputs": ["SuccessFactors tenant", "Module configuration", "Integration setup"],
        },
        {
            "id": "HCM-041",
            "name": "SuccessFactors Employee Central migration",
            "description": "Migrate to SuccessFactors Employee Central",
            "activity_type": "implementation",
            "phase": "migration",
            "per_employee_cost": (75, 200),
            "base_cost": (75000, 200000),
            "timeline_months": (3, 6),
            "requires_tsa": True,
            "tsa_duration": (6, 12),
            "prerequisites": ["HCM-040"],
            "outputs": ["Migrated employee data", "Org structure", "Position management"],
        },
        # -----------------------------------------------------------------
        # PAYROLL SPECIFIC
        # -----------------------------------------------------------------
        {
            "id": "HCM-050",
            "name": "Payroll provider setup",
            "description": "Establish standalone payroll processing",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (30000, 80000),
            "per_employee_cost": (20, 60),
            "timeline_months": (1, 3),
            "requires_tsa": True,
            "tsa_duration": (3, 6),
            "prerequisites": ["HCM-004"],
            "outputs": ["Payroll provider setup", "Tax registration", "Bank setup", "Compliance configuration"],
        },
        {
            "id": "HCM-051",
            "name": "Benefits administration setup",
            "description": "Establish standalone benefits administration",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (25000, 75000),
            "per_employee_cost": (15, 50),
            "timeline_months": (1, 3),
            "requires_tsa": True,
            "tsa_duration": (3, 6),
            "prerequisites": ["HCM-004"],
            "outputs": ["Benefits broker selection", "Plan setup", "Carrier feeds", "Open enrollment config"],
        },
        {
            "id": "HCM-052",
            "name": "401(k)/retirement plan setup",
            "description": "Establish standalone retirement plan",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (20000, 50000),
            "timeline_months": (1, 3),
            "requires_tsa": True,
            "tsa_duration": (3, 6),
            "prerequisites": ["HCM-004"],
            "outputs": ["Retirement plan setup", "Recordkeeper selection", "Payroll integration"],
        },
        # -----------------------------------------------------------------
        # TESTING & CUTOVER
        # -----------------------------------------------------------------
        {
            "id": "HCM-060",
            "name": "HR/HCM parallel payroll testing",
            "description": "Execute parallel payroll runs for validation",
            "activity_type": "implementation",
            "phase": "testing",
            "base_cost": (20000, 50000),
            "timeline_months": (1, 2),
            "requires_tsa": True,
            "tsa_duration": (2, 3),
            "prerequisites": ["HCM-050"],
            "outputs": ["Parallel payroll results", "Variance analysis", "Issue resolution"],
            "notes": "Critical for payroll accuracy validation",
        },
        {
            "id": "HCM-061",
            "name": "HR/HCM cutover and go-live",
            "description": "Execute HR systems cutover",
            "activity_type": "implementation",
            "phase": "cutover",
            "base_cost": (25000, 60000),
            "timeline_months": (0.5, 1),
            "requires_tsa": False,
            "prerequisites": ["HCM-060"],
            "outputs": ["Cutover execution", "Go-live validation", "Employee communication"],
        },
        {
            "id": "HCM-062",
            "name": "HR/HCM hypercare support",
            "description": "Post-go-live hypercare for HR systems",
            "activity_type": "implementation",
            "phase": "cutover",
            "base_cost": (20000, 50000),
            "timeline_months": (1, 2),
            "requires_tsa": False,
            "prerequisites": ["HCM-061"],
            "outputs": ["Hypercare support", "Issue resolution", "Process stabilization"],
        },
    ],
}

# =============================================================================
# PHASE 3: CUSTOM/LEGACY APPLICATIONS
# =============================================================================

CUSTOM_APP_TEMPLATES = {
    "parent_dependency": [
        # -----------------------------------------------------------------
        # ASSESSMENT
        # -----------------------------------------------------------------
        {
            "id": "APP-001",
            "name": "Custom application portfolio assessment",
            "description": "Assess custom and legacy application portfolio",
            "activity_type": "implementation",
            "phase": "assessment",
            "base_cost": (30000, 75000),
            "timeline_months": (0.5, 1.5),
            "requires_tsa": False,
            "prerequisites": [],
            "outputs": ["Application inventory", "Technology stack analysis", "Dependency map", "Business criticality"],
        },
        {
            "id": "APP-002",
            "name": "Application disposition analysis",
            "description": "Determine disposition for each application (migrate, retire, replace)",
            "activity_type": "implementation",
            "phase": "assessment",
            "per_app_cost": (500, 2000),
            "base_cost": (20000, 50000),
            "timeline_months": (0.5, 1.5),
            "requires_tsa": False,
            "prerequisites": ["APP-001"],
            "outputs": ["Disposition decisions", "Migration approach", "Retirement plan", "Replacement candidates"],
        },
        {
            "id": "APP-003",
            "name": "Application separation strategy",
            "description": "Design application separation and migration strategy",
            "activity_type": "implementation",
            "phase": "design",
            "base_cost": (40000, 100000),
            "timeline_months": (1, 2),
            "requires_tsa": False,
            "prerequisites": ["APP-001", "APP-002"],
            "outputs": ["Migration strategy", "Wave planning", "Risk assessment", "Timeline"],
        },
        # -----------------------------------------------------------------
        # MIGRATION - BY COMPLEXITY
        # -----------------------------------------------------------------
        {
            "id": "APP-010",
            "name": "Simple application migration",
            "description": "Migrate simple applications (standalone, minimal integration)",
            "activity_type": "implementation",
            "phase": "migration",
            "per_app_cost": (5000, 15000),
            "timeline_months": (1, 2),
            "requires_tsa": True,
            "tsa_duration": (2, 4),
            "prerequisites": ["APP-003"],
            "outputs": ["Migrated application", "Testing validation", "Documentation"],
            "notes": "Simple = standalone, <3 integrations, well-documented",
        },
        {
            "id": "APP-011",
            "name": "Moderate application migration",
            "description": "Migrate moderate complexity applications",
            "activity_type": "implementation",
            "phase": "migration",
            "per_app_cost": (15000, 50000),
            "timeline_months": (2, 4),
            "requires_tsa": True,
            "tsa_duration": (3, 6),
            "prerequisites": ["APP-003"],
            "outputs": ["Migrated application", "Integration rebuild", "Testing validation"],
            "notes": "Moderate = 3-10 integrations, some customization",
        },
        {
            "id": "APP-012",
            "name": "Complex application migration",
            "description": "Migrate complex applications with extensive dependencies",
            "activity_type": "implementation",
            "phase": "migration",
            "per_app_cost": (50000, 150000),
            "timeline_months": (3, 8),
            "requires_tsa": True,
            "tsa_duration": (6, 12),
            "prerequisites": ["APP-003"],
            "outputs": ["Migrated application", "Integration rebuild", "Custom development", "Extensive testing"],
            "notes": "Complex = >10 integrations, heavy customization, poor documentation",
        },
        {
            "id": "APP-013",
            "name": "Legacy application modernization",
            "description": "Modernize legacy applications during migration",
            "activity_type": "implementation",
            "phase": "migration",
            "per_app_cost": (75000, 300000),
            "timeline_months": (4, 12),
            "requires_tsa": True,
            "tsa_duration": (6, 18),
            "prerequisites": ["APP-003"],
            "outputs": ["Modernized application", "New platform", "Data migration", "User training"],
            "notes": "Modernization adds significant cost but reduces technical debt",
        },
        # -----------------------------------------------------------------
        # APPLICATION RETIREMENT
        # -----------------------------------------------------------------
        {
            "id": "APP-020",
            "name": "Application retirement - Simple",
            "description": "Retire simple applications with data archival",
            "activity_type": "implementation",
            "phase": "migration",
            "per_app_cost": (3000, 10000),
            "timeline_months": (0.5, 1),
            "requires_tsa": False,
            "prerequisites": ["APP-003"],
            "outputs": ["Retired application", "Data archive", "Documentation"],
        },
        {
            "id": "APP-021",
            "name": "Application retirement - Complex",
            "description": "Retire complex applications with data migration/archival",
            "activity_type": "implementation",
            "phase": "migration",
            "per_app_cost": (10000, 35000),
            "timeline_months": (1, 3),
            "requires_tsa": True,
            "tsa_duration": (2, 4),
            "prerequisites": ["APP-003"],
            "outputs": ["Retired application", "Data migration", "Compliance archive", "Audit trail"],
        },
        # -----------------------------------------------------------------
        # INTEGRATION WORK
        # -----------------------------------------------------------------
        {
            "id": "APP-030",
            "name": "Integration platform standup",
            "description": "Deploy integration platform (MuleSoft, Boomi, etc.)",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (50000, 150000),
            "timeline_months": (1, 3),
            "requires_tsa": False,
            "prerequisites": ["APP-003"],
            "outputs": ["Integration platform", "Base configuration", "Development standards"],
        },
        {
            "id": "APP-031",
            "name": "API gateway deployment",
            "description": "Deploy API gateway for application integration",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (30000, 80000),
            "timeline_months": (0.5, 1.5),
            "requires_tsa": False,
            "prerequisites": ["APP-003"],
            "outputs": ["API gateway", "Security policies", "Rate limiting", "Monitoring"],
        },
        {
            "id": "APP-032",
            "name": "Integration rebuild - Per integration",
            "description": "Rebuild individual integrations for standalone environment",
            "activity_type": "implementation",
            "phase": "build",
            "per_integration_cost": (3000, 15000),
            "timeline_months": (1, 4),
            "requires_tsa": True,
            "tsa_duration": (3, 6),
            "prerequisites": ["APP-030"],
            "outputs": ["Rebuilt integrations", "Testing validation", "Documentation"],
        },
        # -----------------------------------------------------------------
        # TESTING
        # -----------------------------------------------------------------
        {
            "id": "APP-040",
            "name": "Application testing coordination",
            "description": "Coordinate testing across application portfolio",
            "activity_type": "implementation",
            "phase": "testing",
            "base_cost": (25000, 75000),
            "timeline_months": (1, 3),
            "requires_tsa": False,
            "prerequisites": ["APP-010", "APP-011", "APP-012"],
            "outputs": ["Test coordination", "Defect management", "Sign-off tracking"],
        },
        {
            "id": "APP-041",
            "name": "End-to-end process testing",
            "description": "Execute end-to-end business process testing",
            "activity_type": "implementation",
            "phase": "testing",
            "base_cost": (30000, 80000),
            "timeline_months": (1, 2),
            "requires_tsa": False,
            "prerequisites": ["APP-040"],
            "outputs": ["E2E test execution", "Process validation", "Issue resolution"],
        },
    ],
    "technology_mismatch": [
        {
            "id": "APP-050",
            "name": "Application technology assessment",
            "description": "Assess application technology stack for compatibility",
            "activity_type": "implementation",
            "phase": "assessment",
            "per_app_cost": (2000, 6000),
            "base_cost": (15000, 40000),
            "timeline_months": (0.5, 1),
            "requires_tsa": False,
            "prerequisites": [],
            "outputs": ["Technology assessment", "Compatibility matrix", "Remediation requirements"],
        },
        {
            "id": "APP-051",
            "name": "Application refactoring",
            "description": "Refactor applications for new technology standards",
            "activity_type": "implementation",
            "phase": "build",
            "per_app_cost": (25000, 100000),
            "timeline_months": (2, 6),
            "requires_tsa": True,
            "tsa_duration": (3, 6),
            "prerequisites": ["APP-050"],
            "outputs": ["Refactored application", "Updated technology stack", "Testing"],
        },
    ],
}

# =============================================================================
# PHASE 3: SAAS PORTFOLIO
# =============================================================================

SAAS_TEMPLATES = {
    "parent_dependency": [
        # -----------------------------------------------------------------
        # ASSESSMENT
        # -----------------------------------------------------------------
        {
            "id": "SAS-001",
            "name": "SaaS discovery and inventory",
            "description": "Discover and inventory all SaaS applications in use",
            "activity_type": "implementation",
            "phase": "assessment",
            "base_cost": (20000, 50000),
            "timeline_months": (0.5, 1),
            "requires_tsa": False,
            "prerequisites": [],
            "outputs": ["SaaS inventory", "Shadow IT discovery", "User mapping", "Spend analysis"],
            "notes": "Use SaaS management tools for discovery",
        },
        {
            "id": "SAS-002",
            "name": "SaaS contract analysis",
            "description": "Analyze SaaS contracts for assignment and transfer",
            "activity_type": "implementation",
            "phase": "assessment",
            "per_contract_cost": (500, 1500),
            "base_cost": (15000, 40000),
            "timeline_months": (0.5, 1),
            "requires_tsa": False,
            "prerequisites": ["SAS-001"],
            "outputs": ["Contract inventory", "Assignment analysis", "Termination provisions", "Cost allocation"],
        },
        {
            "id": "SAS-003",
            "name": "SaaS data classification",
            "description": "Classify data stored in SaaS applications",
            "activity_type": "implementation",
            "phase": "assessment",
            "per_app_cost": (500, 2000),
            "base_cost": (10000, 30000),
            "timeline_months": (0.5, 1),
            "requires_tsa": False,
            "prerequisites": ["SAS-001"],
            "outputs": ["Data classification", "Sensitivity mapping", "Retention requirements"],
        },
        {
            "id": "SAS-004",
            "name": "SaaS separation strategy",
            "description": "Design SaaS portfolio separation approach",
            "activity_type": "implementation",
            "phase": "design",
            "base_cost": (20000, 50000),
            "timeline_months": (0.5, 1),
            "requires_tsa": False,
            "prerequisites": ["SAS-001", "SAS-002", "SAS-003"],
            "outputs": ["Separation strategy", "Migration waves", "Contract approach"],
        },
        # -----------------------------------------------------------------
        # ACCOUNT SEPARATION
        # -----------------------------------------------------------------
        {
            "id": "SAS-010",
            "name": "SaaS account provisioning - Simple",
            "description": "Provision new accounts for simple SaaS applications",
            "activity_type": "implementation",
            "phase": "build",
            "per_app_cost": (1000, 3000),
            "timeline_months": (0.5, 1),
            "requires_tsa": True,
            "tsa_duration": (1, 3),
            "prerequisites": ["SAS-004"],
            "outputs": ["New SaaS accounts", "Admin setup", "Basic configuration"],
            "notes": "Simple = minimal configuration, standard features",
        },
        {
            "id": "SAS-011",
            "name": "SaaS account provisioning - Complex",
            "description": "Provision and configure complex SaaS applications",
            "activity_type": "implementation",
            "phase": "build",
            "per_app_cost": (5000, 20000),
            "timeline_months": (1, 3),
            "requires_tsa": True,
            "tsa_duration": (2, 4),
            "prerequisites": ["SAS-004"],
            "outputs": ["New SaaS accounts", "Custom configuration", "Integration setup"],
            "notes": "Complex = extensive configuration, integrations, customization",
        },
        {
            "id": "SAS-012",
            "name": "SaaS user provisioning",
            "description": "Provision users in new SaaS accounts",
            "activity_type": "implementation",
            "phase": "migration",
            "per_user_cost": (5, 20),
            "per_app_cost": (500, 2000),
            "timeline_months": (0.5, 1.5),
            "requires_tsa": True,
            "tsa_duration": (2, 4),
            "prerequisites": ["SAS-010", "SAS-011"],
            "outputs": ["Provisioned users", "Role assignments", "SSO configuration"],
        },
        {
            "id": "SAS-013",
            "name": "SaaS data migration",
            "description": "Migrate data between SaaS accounts",
            "activity_type": "implementation",
            "phase": "migration",
            "per_app_cost": (3000, 15000),
            "timeline_months": (0.5, 2),
            "requires_tsa": True,
            "tsa_duration": (2, 4),
            "prerequisites": ["SAS-011"],
            "outputs": ["Migrated data", "Data validation", "Historical data handling"],
        },
        {
            "id": "SAS-014",
            "name": "SaaS SSO reconfiguration",
            "description": "Reconfigure SSO for SaaS applications",
            "activity_type": "implementation",
            "phase": "migration",
            "per_app_cost": (1000, 4000),
            "timeline_months": (0.5, 1.5),
            "requires_tsa": True,
            "tsa_duration": (2, 4),
            "prerequisites": ["SAS-010", "SAS-011"],
            "outputs": ["SSO configuration", "SAML/OIDC setup", "Testing validation"],
        },
        # -----------------------------------------------------------------
        # CONTRACT TRANSITION
        # -----------------------------------------------------------------
        {
            "id": "SAS-020",
            "name": "SaaS contract assignment",
            "description": "Execute contract assignment to new entity",
            "activity_type": "implementation",
            "phase": "migration",
            "per_contract_cost": (1000, 4000),
            "timeline_months": (0.5, 2),
            "requires_tsa": False,
            "prerequisites": ["SAS-002"],
            "outputs": ["Assigned contracts", "Vendor acknowledgment", "Updated billing"],
        },
        {
            "id": "SAS-021",
            "name": "SaaS new contract negotiation",
            "description": "Negotiate new contracts for non-transferable SaaS",
            "activity_type": "implementation",
            "phase": "build",
            "per_contract_cost": (2000, 8000),
            "timeline_months": (1, 3),
            "requires_tsa": False,
            "prerequisites": ["SAS-002"],
            "outputs": ["New contracts", "Negotiated terms", "Volume pricing"],
        },
        {
            "id": "SAS-022",
            "name": "SaaS contract termination",
            "description": "Terminate SaaS contracts no longer needed",
            "activity_type": "implementation",
            "phase": "migration",
            "per_contract_cost": (500, 2000),
            "timeline_months": (0.5, 1.5),
            "requires_tsa": False,
            "prerequisites": ["SAS-002"],
            "outputs": ["Terminated contracts", "Data export", "Deletion verification"],
        },
        # -----------------------------------------------------------------
        # DATA HANDLING
        # -----------------------------------------------------------------
        {
            "id": "SAS-030",
            "name": "SaaS data export",
            "description": "Export data from SaaS applications",
            "activity_type": "implementation",
            "phase": "migration",
            "per_app_cost": (1000, 5000),
            "timeline_months": (0.25, 1),
            "requires_tsa": True,
            "tsa_duration": (1, 3),
            "prerequisites": ["SAS-003"],
            "outputs": ["Exported data", "Export validation", "Archive storage"],
        },
        {
            "id": "SAS-031",
            "name": "SaaS historical data archival",
            "description": "Archive historical data from SaaS applications",
            "activity_type": "implementation",
            "phase": "migration",
            "per_app_cost": (2000, 8000),
            "timeline_months": (0.5, 1.5),
            "requires_tsa": False,
            "prerequisites": ["SAS-030"],
            "outputs": ["Archived data", "Retention compliance", "Access procedures"],
        },
        {
            "id": "SAS-032",
            "name": "SaaS data deletion verification",
            "description": "Verify data deletion from parent SaaS accounts",
            "activity_type": "implementation",
            "phase": "migration",
            "per_app_cost": (500, 2000),
            "timeline_months": (0.25, 0.5),
            "requires_tsa": False,
            "prerequisites": ["SAS-013"],
            "outputs": ["Deletion confirmation", "Audit evidence", "Compliance documentation"],
        },
        # -----------------------------------------------------------------
        # SPECIFIC SAAS CATEGORIES
        # -----------------------------------------------------------------
        {
            "id": "SAS-040",
            "name": "Collaboration tools migration (Slack/Teams)",
            "description": "Migrate collaboration platform (Slack, Teams, etc.)",
            "activity_type": "implementation",
            "phase": "migration",
            "per_user_cost": (10, 30),
            "base_cost": (20000, 60000),
            "timeline_months": (1, 3),
            "requires_tsa": True,
            "tsa_duration": (3, 6),
            "prerequisites": ["SAS-004"],
            "outputs": ["New workspace", "Channel migration", "Historical data handling"],
        },
        {
            "id": "SAS-041",
            "name": "Project management tools migration",
            "description": "Migrate project management tools (Jira, Asana, Monday)",
            "activity_type": "implementation",
            "phase": "migration",
            "per_user_cost": (15, 40),
            "base_cost": (15000, 45000),
            "timeline_months": (1, 2),
            "requires_tsa": True,
            "tsa_duration": (2, 4),
            "prerequisites": ["SAS-004"],
            "outputs": ["New instance", "Project migration", "Workflow configuration"],
        },
        {
            "id": "SAS-042",
            "name": "Document management migration",
            "description": "Migrate document management (Box, Dropbox, Google Drive)",
            "activity_type": "implementation",
            "phase": "migration",
            "per_user_cost": (10, 25),
            "base_cost": (15000, 40000),
            "timeline_months": (1, 3),
            "requires_tsa": True,
            "tsa_duration": (3, 6),
            "prerequisites": ["SAS-004"],
            "outputs": ["New account", "File migration", "Permission mapping"],
        },
        {
            "id": "SAS-043",
            "name": "Business intelligence tools migration",
            "description": "Migrate BI tools (Tableau, Power BI, Looker)",
            "activity_type": "implementation",
            "phase": "migration",
            "base_cost": (30000, 100000),
            "timeline_months": (1, 4),
            "requires_tsa": True,
            "tsa_duration": (3, 6),
            "prerequisites": ["SAS-004"],
            "outputs": ["New BI environment", "Dashboard migration", "Data source reconfiguration"],
        },
    ],
    "license_issue": [
        {
            "id": "SAS-050",
            "name": "SaaS license true-up",
            "description": "True-up SaaS licenses for carveout population",
            "activity_type": "license",
            "phase": "assessment",
            "per_app_cost": (1000, 4000),
            "base_cost": (10000, 30000),
            "timeline_months": (0.5, 1),
            "requires_tsa": False,
            "prerequisites": ["SAS-001"],
            "outputs": ["License true-up", "Cost allocation", "Optimization opportunities"],
        },
        {
            "id": "SAS-051",
            "name": "SaaS license optimization",
            "description": "Optimize SaaS licenses for standalone environment",
            "activity_type": "license",
            "phase": "build",
            "base_cost": (15000, 40000),
            "timeline_months": (0.5, 1.5),
            "requires_tsa": False,
            "prerequisites": ["SAS-050"],
            "outputs": ["Optimized licensing", "Cost savings", "Right-sized subscriptions"],
        },
    ],
}

# =============================================================================
# COMBINED TEMPLATES FOR PHASE 3
# =============================================================================

def get_phase3_templates() -> Dict[str, Dict[str, List[Dict]]]:
    """Get all Phase 3 templates organized by category and workstream."""
    return {
        "parent_dependency": {
            "erp": ERP_TEMPLATES["parent_dependency"],
            "crm": CRM_TEMPLATES["parent_dependency"],
            "hrhcm": HRHCM_TEMPLATES["parent_dependency"],
            "custom_apps": CUSTOM_APP_TEMPLATES["parent_dependency"],
            "saas": SAAS_TEMPLATES["parent_dependency"],
        },
        "technology_mismatch": {
            "custom_apps": CUSTOM_APP_TEMPLATES.get("technology_mismatch", []),
        },
        "license_issue": {
            "saas": SAAS_TEMPLATES.get("license_issue", []),
        },
    }


def get_phase3_activity_by_id(activity_id: str) -> Dict:
    """Look up a Phase 3 activity by its ID."""
    all_templates = get_phase3_templates()

    for category, workstreams in all_templates.items():
        for workstream, activities in workstreams.items():
            for activity in activities:
                if activity.get("id") == activity_id:
                    return activity

    return None


def calculate_phase3_activity_cost(
    activity: Dict,
    user_count: int = 1000,
    employee_count: int = None,
    app_count: int = 30,
    integration_count: int = 20,
    contract_count: int = 50,
    record_count: int = 100000,
    complexity: str = "moderate",
    industry: str = "standard",
) -> tuple:
    """
    Calculate cost range for a Phase 3 activity based on quantities and modifiers.

    Returns: (low, high, formula)
    """
    employee_count = employee_count or user_count  # Default employees = users

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

    if "per_employee_cost" in activity:
        per_low, per_high = activity["per_employee_cost"]
        low += per_low * employee_count
        high += per_high * employee_count
        formula_parts.append(f"{employee_count:,} employees × ${per_low}-${per_high}")

    if "per_app_cost" in activity:
        per_low, per_high = activity["per_app_cost"]
        low += per_low * app_count
        high += per_high * app_count
        formula_parts.append(f"{app_count} apps × ${per_low:,}-${per_high:,}")

    if "per_integration_cost" in activity:
        per_low, per_high = activity["per_integration_cost"]
        low += per_low * integration_count
        high += per_high * integration_count
        formula_parts.append(f"{integration_count} integrations × ${per_low:,}-${per_high:,}")

    if "per_contract_cost" in activity:
        per_low, per_high = activity["per_contract_cost"]
        low += per_low * contract_count
        high += per_high * contract_count
        formula_parts.append(f"{contract_count} contracts × ${per_low:,}-${per_high:,}")

    if "per_record_cost" in activity:
        per_low, per_high = activity["per_record_cost"]
        low += per_low * record_count
        high += per_high * record_count
        formula_parts.append(f"{record_count:,} records × ${per_low}-${per_high}")

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
    'ERP_TEMPLATES',
    'CRM_TEMPLATES',
    'HRHCM_TEMPLATES',
    'CUSTOM_APP_TEMPLATES',
    'SAAS_TEMPLATES',
    'get_phase3_templates',
    'get_phase3_activity_by_id',
    'calculate_phase3_activity_cost',
]
