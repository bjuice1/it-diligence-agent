"""
Function Deep Dive - Comprehensive Review Criteria

This module defines the specific questions, evidence requirements, and maturity
criteria for each IT function. Use this for quality review to ensure
function-by-function analysis meets IC standards.

The goal: For every function, we should be able to answer these questions
with evidence, or explicitly flag gaps.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum


class MaturityLevel(Enum):
    """Function maturity levels."""
    UNKNOWN = 0  # Not enough information
    IMMATURE = 1  # Ad-hoc, undocumented, high risk
    DEVELOPING = 2  # Some process, gaps exist
    DEFINED = 3  # Documented, repeatable
    MANAGED = 4  # Measured, controlled
    OPTIMIZED = 5  # Continuous improvement


@dataclass
class FunctionReviewCriteria:
    """Defines what we MUST know about each function for IC-ready output."""
    function_name: str
    domain: str

    # Core questions - must answer all or flag as GAP
    must_answer_questions: List[str]

    # Required evidence types
    required_evidence: List[str]

    # Key risk indicators to check
    risk_indicators: List[str]

    # M&A-specific questions
    mna_questions: Dict[str, List[str]]  # By deal type

    # Maturity assessment criteria
    maturity_criteria: Dict[int, str]  # Level -> description

    # Cross-domain dependencies
    cross_domain_links: List[str]

    # Typical cost drivers
    cost_drivers: List[str]


# =============================================================================
# INFRASTRUCTURE DOMAIN - DEEP DIVE CRITERIA
# =============================================================================

INFRASTRUCTURE_FUNCTIONS = {
    "Data Center": FunctionReviewCriteria(
        function_name="Data Center",
        domain="infrastructure",
        must_answer_questions=[
            "Where are the data centers located (owned, colo, parent)?",
            "What is the lease/contract status and expiry dates?",
            "What is the physical capacity (power, cooling, space)?",
            "Who has physical access and how is it controlled?",
            "What is the DR posture - is there a secondary site?",
            "What is the network connectivity (carriers, bandwidth)?",
            "Are there any compliance certifications (SOC 2, ISO)?",
        ],
        required_evidence=[
            "DC location(s)",
            "Ownership model (owned/colo/cloud)",
            "Lease or contract terms",
            "Power capacity (kW)",
            "DR site existence",
        ],
        risk_indicators=[
            "Single DC with no DR",
            "Lease expiring within 18 months",
            "Parent-owned facility (TSA complexity)",
            "No physical security documentation",
            "Capacity constraints approaching",
            "Aging facility infrastructure",
        ],
        mna_questions={
            "acquisition": [
                "Does buyer have DC in same region for consolidation?",
                "What is the network path to connect to buyer?",
            ],
            "carveout": [
                "Is DC shared with parent (TSA required)?",
                "What equipment is dedicated vs shared?",
                "Who owns the facility lease?",
            ],
            "divestiture": [
                "What equipment stays vs goes?",
                "Impact on RemainCo capacity?",
            ],
        },
        maturity_criteria={
            1: "No DR, single facility, no monitoring",
            2: "Basic DR exists but untested, some monitoring",
            3: "DR tested annually, 24x7 monitoring, documented procedures",
            4: "DR tested quarterly, capacity planning, predictive maintenance",
            5: "Multi-region active-active, automated failover, continuous optimization",
        },
        cross_domain_links=[
            "Network (WAN connectivity)",
            "Security Operations (physical security)",
            "Backup/DR (recovery capability)",
            "Applications (hosting requirements)",
        ],
        cost_drivers=[
            "Power costs ($/kWh)",
            "Colo fees ($/rack/month)",
            "Network bandwidth",
            "Maintenance contracts",
            "Refresh cycles (UPS, HVAC)",
        ],
    ),

    "Compute/Virtualization": FunctionReviewCriteria(
        function_name="Compute/Virtualization",
        domain="infrastructure",
        must_answer_questions=[
            "What hypervisor platform (VMware, Hyper-V, KVM)?",
            "What version and support status?",
            "How many hosts and VMs?",
            "What is the average utilization?",
            "Who manages the platform (internal/MSP)?",
            "What licensing model (per-CPU, per-VM)?",
            "Is there a refresh cycle planned?",
        ],
        required_evidence=[
            "Hypervisor platform and version",
            "Host count and VM count",
            "Licensing model",
            "Support contract status",
        ],
        risk_indicators=[
            "VMware 6.x (EOL)",
            "Single vCenter (no HA)",
            "Overprovisioned (>80% utilization)",
            "No capacity planning",
            "Mixed hypervisors without strategy",
            "Broadcom acquisition impact (VMware)",
        ],
        mna_questions={
            "acquisition": [
                "Same hypervisor as buyer (consolidation)?",
                "Can VMs be migrated to buyer environment?",
            ],
            "carveout": [
                "Shared cluster with parent?",
                "Can we get dedicated capacity?",
            ],
            "divestiture": [
                "What VMs move with the business?",
                "License transfer possible?",
            ],
        },
        maturity_criteria={
            1: "Manual VM management, no templates, no monitoring",
            2: "Basic templates, some automation, reactive monitoring",
            3: "Standardized builds, proactive monitoring, capacity planning",
            4: "Infrastructure as Code, automated scaling, performance optimization",
            5: "Fully automated, self-healing, cost-optimized",
        },
        cross_domain_links=[
            "Storage (datastore dependencies)",
            "Network (virtual networking)",
            "Backup/DR (VM protection)",
            "Security (endpoint protection)",
        ],
        cost_drivers=[
            "VMware licensing (per-CPU very expensive)",
            "Hardware refresh (3-5 year cycle)",
            "Support contracts",
            "Power/cooling",
        ],
    ),

    "Cloud Infrastructure": FunctionReviewCriteria(
        function_name="Cloud Infrastructure",
        domain="infrastructure",
        must_answer_questions=[
            "Which cloud provider(s) (AWS, Azure, GCP)?",
            "What is the monthly spend?",
            "What workloads are in cloud vs on-prem?",
            "Who manages cloud (internal/MSP)?",
            "What governance exists (tagging, budgets)?",
            "What security controls are in place?",
            "Is there a cloud-first or hybrid strategy?",
        ],
        required_evidence=[
            "Cloud provider(s)",
            "Monthly spend range",
            "Account/subscription structure",
            "Primary workload types",
        ],
        risk_indicators=[
            "No cloud governance/tagging",
            "Spend growing uncontrolled",
            "Lift-and-shift only (no optimization)",
            "Multi-cloud without strategy",
            "Parent account dependency (carveout)",
            "No security baseline",
        ],
        mna_questions={
            "acquisition": [
                "Same cloud provider as buyer?",
                "Account consolidation possible?",
                "Enterprise agreement leverage?",
            ],
            "carveout": [
                "Is this a parent cloud account?",
                "Can we create dedicated subscription?",
                "What data separation needed?",
            ],
            "divestiture": [
                "What accounts/subscriptions transfer?",
                "Impact on enterprise agreements?",
            ],
        },
        maturity_criteria={
            1: "Ad-hoc usage, no governance, no cost controls",
            2: "Basic structure, some monitoring, limited governance",
            3: "Landing zone, cost controls, security baseline",
            4: "FinOps practice, Infrastructure as Code, automated security",
            5: "Cloud-native, optimized costs, continuous compliance",
        },
        cross_domain_links=[
            "Network (ExpressRoute/Direct Connect)",
            "Identity (Cloud IAM)",
            "Security (Cloud security posture)",
            "Applications (SaaS/PaaS usage)",
        ],
        cost_drivers=[
            "Compute instances",
            "Storage (egress fees!)",
            "Reserved vs on-demand",
            "Data transfer",
            "Managed services",
        ],
    ),

    "Storage": FunctionReviewCriteria(
        function_name="Storage",
        domain="infrastructure",
        must_answer_questions=[
            "What storage platforms (SAN, NAS, object)?",
            "What is the total capacity and utilization?",
            "What is the data growth rate?",
            "Who manages storage (internal/vendor)?",
            "What is the refresh cycle and contract status?",
            "What replication/tiering exists?",
            "What performance tier is available?",
        ],
        required_evidence=[
            "Storage platform(s)",
            "Total capacity (TB/PB)",
            "Utilization percentage",
            "Support contract status",
        ],
        risk_indicators=[
            "Storage at >80% capacity",
            "EOL storage arrays",
            "No replication (data loss risk)",
            "Single storage admin",
            "Rapid growth without plan",
            "Performance bottlenecks",
        ],
        mna_questions={
            "acquisition": [
                "Compatible with buyer storage?",
                "Data migration path?",
            ],
            "carveout": [
                "Storage shared with parent?",
                "Data separation complexity?",
            ],
            "divestiture": [
                "What data goes with divested entity?",
            ],
        },
        maturity_criteria={
            1: "Direct-attached, no redundancy, manual management",
            2: "Basic SAN/NAS, some RAID, reactive management",
            3: "Enterprise storage, replication, capacity planning",
            4: "Tiered storage, automation, predictive analytics",
            5: "Software-defined, fully automated, optimized",
        },
        cross_domain_links=[
            "Compute (datastores)",
            "Backup/DR (backup targets)",
            "Applications (database storage)",
        ],
        cost_drivers=[
            "Capacity ($/TB)",
            "Performance tier",
            "Maintenance contracts",
            "Refresh cycles",
        ],
    ),

    "Backup/DR": FunctionReviewCriteria(
        function_name="Backup/DR",
        domain="infrastructure",
        must_answer_questions=[
            "What backup solution (Veeam, Commvault, etc.)?",
            "What is the backup architecture (on-prem, cloud, tape)?",
            "What are the defined RPO/RTO targets?",
            "When was DR last tested?",
            "What is covered vs not covered?",
            "Who manages backups (internal/MSP)?",
            "What is the retention policy?",
        ],
        required_evidence=[
            "Backup solution name",
            "RPO/RTO targets (or GAP)",
            "DR test date (or GAP)",
            "Backup scope (what's covered)",
        ],
        risk_indicators=[
            "No defined RPO/RTO",
            "DR never tested",
            "Tape-only backup (slow recovery)",
            "Gaps in coverage (some systems not backed up)",
            "No offsite copy (ransomware vulnerability)",
            "Backup team is single person",
        ],
        mna_questions={
            "acquisition": [
                "Compatible with buyer backup solution?",
                "Can backup infrastructure consolidate?",
            ],
            "carveout": [
                "DR leverages parent infrastructure?",
                "Backup data commingled with parent?",
            ],
            "divestiture": [
                "Backup history needed by divested entity?",
                "Impact on parent DR posture?",
            ],
        },
        maturity_criteria={
            1: "Manual backups, no testing, no offsite",
            2: "Automated backups, occasional tests, basic offsite",
            3: "Defined RPO/RTO, annual DR test, documented procedures",
            4: "Regular DR tests, automated recovery, immutable backups",
            5: "Continuous DR capability, automated failover, verified recovery",
        },
        cross_domain_links=[
            "Storage (backup targets)",
            "Network (replication bandwidth)",
            "Applications (application-consistent backups)",
            "Security (ransomware resilience)",
        ],
        cost_drivers=[
            "Storage capacity (TB backed up)",
            "Backup software licensing",
            "DR site costs",
            "Network bandwidth for replication",
            "Tape handling (if used)",
        ],
    ),
}


# =============================================================================
# APPLICATIONS DOMAIN - DEEP DIVE CRITERIA
# =============================================================================

APPLICATIONS_FUNCTIONS = {
    "ERP": FunctionReviewCriteria(
        function_name="ERP",
        domain="applications",
        must_answer_questions=[
            "What ERP system (SAP, Oracle, NetSuite, etc.)?",
            "What version and support status?",
            "How many users (named, concurrent)?",
            "What modules are in use?",
            "How heavily customized (custom objects count)?",
            "How many integrations to/from ERP?",
            "Who supports the ERP (internal/vendor/SI)?",
            "What is the upgrade path/roadmap?",
        ],
        required_evidence=[
            "ERP system name and version",
            "User count",
            "Modules in use",
            "Customization level (custom objects if SAP)",
            "Integration count",
        ],
        risk_indicators=[
            "Dual ERP (prior M&A not integrated)",
            "SAP ECC (end of support 2027)",
            "Heavily customized (200+ custom objects)",
            "Single person supports ERP",
            "No upgrade path documented",
            "Intercompany transactions (separation complexity)",
        ],
        mna_questions={
            "acquisition": [
                "Same ERP as buyer (consolidation possible)?",
                "Chart of accounts alignment?",
                "What's the rationalization path?",
            ],
            "carveout": [
                "Shared ERP instance with parent?",
                "Intercompany transactions to separate?",
                "Data extraction complexity?",
            ],
            "divestiture": [
                "Is ERP instance dedicated or shared?",
                "Master data ownership?",
            ],
        },
        maturity_criteria={
            1: "Basic financials only, heavy manual workarounds",
            2: "Multiple modules, some customization, limited reporting",
            3: "Integrated modules, documented customizations, standard reports",
            4: "Process automation, advanced analytics, regular upgrades",
            5: "Best-in-class utilization, continuous improvement, cloud-native",
        },
        cross_domain_links=[
            "Integration/Middleware (all integrations)",
            "BI/Analytics (reporting source)",
            "HCM (payroll integration)",
            "Infrastructure (hosting)",
            "Identity (user provisioning)",
        ],
        cost_drivers=[
            "Licensing (perpetual vs subscription)",
            "Maintenance fees (typically 20-22% of license)",
            "Customization support",
            "Integration maintenance",
            "Upgrade projects",
        ],
    ),

    "HCM/Payroll": FunctionReviewCriteria(
        function_name="HCM/Payroll",
        domain="applications",
        must_answer_questions=[
            "What HCM system (Workday, ADP, UKG, etc.)?",
            "What payroll system (same or different)?",
            "How many employees processed?",
            "What countries/jurisdictions?",
            "What modules (core HR, benefits, time)?",
            "Who runs payroll (internal/outsourced)?",
            "What integrations exist (ERP, time, benefits)?",
        ],
        required_evidence=[
            "HCM/Payroll system name",
            "Employee count",
            "Jurisdictions served",
            "Payroll frequency and method",
        ],
        risk_indicators=[
            "Payroll is Day-1 critical - cannot fail",
            "Multiple payroll systems across regions",
            "Parent shared HCM instance",
            "Manual payroll processes",
            "Tax/regulatory compliance gaps",
            "Single payroll admin",
        ],
        mna_questions={
            "acquisition": [
                "Same HCM as buyer (consolidation)?",
                "Payroll cutover timing (Day 1 or later)?",
            ],
            "carveout": [
                "Shared HCM instance with parent?",
                "Employee data separation needed?",
                "TSA for payroll services?",
            ],
            "divestiture": [
                "Payroll service continuity?",
                "Benefits administration transfer?",
            ],
        },
        maturity_criteria={
            1: "Manual payroll, spreadsheet-based HR",
            2: "Basic HRIS, some automation",
            3: "Integrated HCM, automated payroll, self-service",
            4: "Workforce analytics, automated compliance",
            5: "AI-enabled HR, predictive workforce planning",
        },
        cross_domain_links=[
            "ERP (finance integration)",
            "Identity (JML process)",
            "Security (data privacy)",
        ],
        cost_drivers=[
            "Per-employee licensing",
            "Payroll processing fees",
            "Benefits administration",
            "Compliance/tax services",
        ],
    ),

    "CRM": FunctionReviewCriteria(
        function_name="CRM",
        domain="applications",
        must_answer_questions=[
            "What CRM system (Salesforce, Dynamics, HubSpot)?",
            "How many users and what roles?",
            "What modules/features are used?",
            "How customized is the implementation?",
            "What integrations exist (ERP, marketing, support)?",
            "What data is in the CRM (customers, pipeline)?",
            "Who manages the CRM?",
        ],
        required_evidence=[
            "CRM system name",
            "User count",
            "Modules in use",
            "Integration count",
        ],
        risk_indicators=[
            "Heavily customized (hard to migrate)",
            "Critical sales data only in CRM",
            "Poor data quality",
            "No integration with ERP",
            "Contract renewal approaching",
            "Shadow CRM usage",
        ],
        mna_questions={
            "acquisition": [
                "Same CRM as buyer (consolidation)?",
                "Customer data merge strategy?",
                "Sales process alignment?",
            ],
            "carveout": [
                "Shared CRM instance?",
                "Customer data ownership?",
                "Pipeline data separation?",
            ],
            "divestiture": [
                "What customer data goes?",
                "Ongoing data sharing needs?",
            ],
        },
        maturity_criteria={
            1: "Spreadsheets, no central CRM",
            2: "Basic CRM, limited adoption",
            3: "Full CRM usage, integrated processes",
            4: "Advanced analytics, automation, AI features",
            5: "Customer 360, predictive, fully integrated",
        },
        cross_domain_links=[
            "ERP (order/invoice integration)",
            "Integration/Middleware (data sync)",
            "BI/Analytics (sales reporting)",
        ],
        cost_drivers=[
            "Per-user licensing",
            "Premium features",
            "Integration costs",
            "Customization maintenance",
        ],
    ),

    "BI/Analytics": FunctionReviewCriteria(
        function_name="BI/Analytics",
        domain="applications",
        must_answer_questions=[
            "What BI platform (Tableau, Power BI, Looker)?",
            "Is there a data warehouse?",
            "What are the key reports/dashboards?",
            "How many users consume analytics?",
            "What data sources feed the platform?",
            "Who manages BI (IT vs business)?",
            "What is the refresh frequency?",
        ],
        required_evidence=[
            "BI platform name",
            "Data warehouse (Y/N and platform)",
            "User count",
            "Key data sources",
        ],
        risk_indicators=[
            "No single source of truth",
            "Spreadsheet-based reporting",
            "Multiple BI tools (consolidation needed)",
            "Stale data (infrequent refresh)",
            "No data governance",
            "Critical reports undocumented",
        ],
        mna_questions={
            "acquisition": [
                "Same BI platform as buyer?",
                "KPI/metric alignment needed?",
                "Data warehouse consolidation?",
            ],
            "carveout": [
                "Reports depend on parent data?",
                "Data warehouse shared?",
                "Historical data needs?",
            ],
            "divestiture": [
                "What reports go with business?",
                "Data access post-separation?",
            ],
        },
        maturity_criteria={
            1: "Ad-hoc spreadsheets, no central BI",
            2: "Basic reporting tool, departmental",
            3: "Enterprise BI, data warehouse, self-service",
            4: "Advanced analytics, governed, automated",
            5: "AI/ML, predictive, real-time, embedded",
        },
        cross_domain_links=[
            "ERP (primary data source)",
            "CRM (sales data)",
            "Data & Analytics team (ownership)",
        ],
        cost_drivers=[
            "BI licensing (viewer vs creator)",
            "Data warehouse compute/storage",
            "ETL/data pipeline tools",
            "Development/maintenance",
        ],
    ),

    "Integration/Middleware": FunctionReviewCriteria(
        function_name="Integration/Middleware",
        domain="applications",
        must_answer_questions=[
            "What integration platform (MuleSoft, Boomi, Informatica)?",
            "How many integrations are managed?",
            "What are the critical integrations?",
            "Is it point-to-point or hub-based?",
            "Who maintains integrations?",
            "What is the documentation level?",
            "What monitoring exists?",
        ],
        required_evidence=[
            "Integration platform (or point-to-point)",
            "Total integration count",
            "Critical integration list",
            "Management model",
        ],
        risk_indicators=[
            "Point-to-point spaghetti",
            "Undocumented integrations",
            "Single person maintains all",
            "No monitoring/alerting",
            "Legacy protocols (FTP, flat files)",
            "Direct database connections",
        ],
        mna_questions={
            "acquisition": [
                "Integration platform alignment?",
                "Which integrations change post-close?",
                "API strategy alignment?",
            ],
            "carveout": [
                "Integrations to parent systems?",
                "Data flows that must change?",
                "TSA for integration support?",
            ],
            "divestiture": [
                "Integrations to sever?",
                "New integrations needed?",
            ],
        },
        maturity_criteria={
            1: "Point-to-point, undocumented, fragile",
            2: "Some middleware, basic monitoring",
            3: "Integration platform, documented APIs",
            4: "API-first, automated, self-service",
            5: "Event-driven, real-time, fully governed",
        },
        cross_domain_links=[
            "All applications (data flows)",
            "Security (API security)",
            "Network (connectivity)",
        ],
        cost_drivers=[
            "Platform licensing",
            "Connection/API counts",
            "Development effort",
            "Monitoring tools",
        ],
    ),

    "Custom Applications": FunctionReviewCriteria(
        function_name="Custom Applications",
        domain="applications",
        must_answer_questions=[
            "What custom applications exist?",
            "What business function does each serve?",
            "What technology stack (languages, frameworks)?",
            "Who developed and who maintains?",
            "Is there documentation?",
            "What is the criticality to business?",
            "What integrations exist?",
        ],
        required_evidence=[
            "Application inventory list",
            "Technology stack per app",
            "Criticality rating",
            "Support model (internal/vendor)",
        ],
        risk_indicators=[
            "Legacy languages (COBOL, VB6, Classic ASP)",
            "Original developer no longer available",
            "No documentation",
            "Single maintainer",
            "Core business logic in custom app",
            "Shadow IT (business-owned, not managed)",
        ],
        mna_questions={
            "acquisition": [
                "Does buyer have equivalent capability?",
                "Migrate, retire, or maintain?",
            ],
            "carveout": [
                "Are custom apps shared with parent?",
                "Can we get source code and docs?",
            ],
            "divestiture": [
                "Intellectual property ownership?",
                "Support continuity?",
            ],
        },
        maturity_criteria={
            1: "Undocumented, single maintainer, legacy tech",
            2: "Some documentation, basic maintenance",
            3: "Documented, supported, modern-ish stack",
            4: "CI/CD, automated testing, monitored",
            5: "Cloud-native, microservices, DevOps",
        },
        cross_domain_links=[
            "Infrastructure (hosting)",
            "Integration/Middleware (data flows)",
            "Security (code security)",
            "Organization (developer skills)",
        ],
        cost_drivers=[
            "Internal developer time",
            "Hosting/infrastructure",
            "Technical debt remediation",
            "Modernization projects",
        ],
    ),
}


# =============================================================================
# ORGANIZATION DOMAIN - DEEP DIVE CRITERIA
# =============================================================================

ORGANIZATION_FUNCTIONS = {
    "IT Leadership": FunctionReviewCriteria(
        function_name="IT Leadership",
        domain="organization",
        must_answer_questions=[
            "Who leads IT (CIO, CTO, VP, Director)?",
            "What is the reporting structure?",
            "What is the tenure and background?",
            "What is the leadership's strategic vision?",
            "What is the governance model?",
            "What major initiatives are in progress?",
        ],
        required_evidence=[
            "IT leader name and title",
            "Reporting line",
            "Tenure",
            "Team size (direct + indirect)",
        ],
        risk_indicators=[
            "IT reports to CFO (cost-center view)",
            "IT leader is departing/retiring",
            "No clear succession plan",
            "Strategic initiatives stalled",
            "Governance gaps",
        ],
        mna_questions={
            "acquisition": [
                "Will IT leader stay or go?",
                "What is the integration org model?",
            ],
            "carveout": [
                "Is IT leadership dedicated or shared?",
                "Who will lead standalone IT?",
            ],
            "divestiture": [
                "Impact on remaining IT leadership?",
            ],
        },
        maturity_criteria={
            1: "Reactive, tactical focus, no strategy",
            2: "Some planning, limited business alignment",
            3: "IT strategy exists, business partnership emerging",
            4: "Strategic partner to business, governance in place",
            5: "Digital leadership, innovation driver, board-level engagement",
        },
        cross_domain_links=[
            "All IT functions (governance)",
            "Business (alignment)",
        ],
        cost_drivers=[
            "Leadership compensation",
            "Strategy/consulting spend",
            "Governance overhead",
        ],
    ),

    "Applications Team": FunctionReviewCriteria(
        function_name="Applications Team",
        domain="organization",
        must_answer_questions=[
            "How many FTEs on the applications team?",
            "What skills are represented (ERP, web, mobile)?",
            "What is the split between support vs development?",
            "What delivery methodology (Agile, Waterfall)?",
            "What is the contractor/FTE mix?",
            "Who are the key people and their tenure?",
            "What is the backlog size?",
        ],
        required_evidence=[
            "Team headcount",
            "Skill breakdown",
            "Key person names and roles",
            "Delivery model",
        ],
        risk_indicators=[
            "Single person for critical systems",
            "Heavy contractor reliance",
            "Scarce skills (legacy platforms)",
            "Large backlog (capacity issue)",
            "No succession planning",
            "Key person retirement approaching",
        ],
        mna_questions={
            "acquisition": [
                "Team consolidation with buyer?",
                "Skill gaps buyer needs?",
                "Unique capabilities to retain?",
            ],
            "carveout": [
                "Team shared with parent?",
                "Who comes with the business?",
                "TSA for application support?",
            ],
            "divestiture": [
                "Impact on remaining team?",
                "Knowledge transfer needs?",
            ],
        },
        maturity_criteria={
            1: "Reactive, break-fix only, no process",
            2: "Some process, basic support model",
            3: "Defined roles, documented processes, SLAs",
            4: "DevOps practices, automation, metrics-driven",
            5: "Product teams, continuous delivery, innovation",
        },
        cross_domain_links=[
            "All applications (support ownership)",
            "Infrastructure (hosting needs)",
            "PMO (project delivery)",
        ],
        cost_drivers=[
            "FTE salaries",
            "Contractor rates",
            "Training",
            "Tools/licenses",
        ],
    ),

    "Infrastructure Team": FunctionReviewCriteria(
        function_name="Infrastructure Team",
        domain="organization",
        must_answer_questions=[
            "How many FTEs on infrastructure?",
            "What areas do they cover (servers, storage, network)?",
            "What is outsourced vs internal?",
            "Who are the key people?",
            "What is the on-call model?",
            "What certifications exist?",
        ],
        required_evidence=[
            "Team headcount",
            "Coverage areas",
            "Outsourcing percentage",
            "Key person names",
        ],
        risk_indicators=[
            "Lean team for infrastructure size",
            "Single person for critical area",
            "Heavy MSP reliance",
            "No after-hours coverage",
            "Legacy skills concentration",
            "Turnover issues",
        ],
        mna_questions={
            "acquisition": [
                "Consolidation with buyer team?",
                "Skill gaps to address?",
            ],
            "carveout": [
                "Infrastructure support from parent?",
                "TSA for infrastructure ops?",
                "Standalone team needed?",
            ],
            "divestiture": [
                "Team split impact?",
            ],
        },
        maturity_criteria={
            1: "Reactive, firefighting, no documentation",
            2: "Basic operations, some process",
            3: "Proactive monitoring, documented runbooks",
            4: "Automation, IaC, SRE practices",
            5: "Self-healing, fully automated, optimized",
        },
        cross_domain_links=[
            "All infrastructure functions",
            "Security (ops collaboration)",
            "Applications (hosting support)",
        ],
        cost_drivers=[
            "FTE salaries",
            "MSP fees",
            "On-call compensation",
            "Training/certifications",
        ],
    ),

    "Security Team": FunctionReviewCriteria(
        function_name="Security Team",
        domain="organization",
        must_answer_questions=[
            "Is there dedicated security staff?",
            "Who leads security (CISO, Director)?",
            "What is the team size and structure?",
            "What areas do they cover?",
            "What is outsourced (SOC, pen testing)?",
            "What certifications do they hold?",
        ],
        required_evidence=[
            "Security headcount",
            "Security leader name/title",
            "Coverage model",
            "Outsourcing details",
        ],
        risk_indicators=[
            "No dedicated security staff",
            "Security is part-time role",
            "No CISO or equivalent",
            "Fully outsourced security",
            "Compliance-only focus",
            "High turnover",
        ],
        mna_questions={
            "acquisition": [
                "Security team integration?",
                "Unique capabilities to retain?",
            ],
            "carveout": [
                "Security from parent shared services?",
                "TSA for security operations?",
                "Standalone security capability?",
            ],
            "divestiture": [
                "Security team impact?",
            ],
        },
        maturity_criteria={
            1: "No security function, IT handles ad-hoc",
            2: "Part-time security, reactive",
            3: "Dedicated team, defined program",
            4: "Proactive security, threat hunting, metrics",
            5: "Security-first culture, embedded, automated",
        },
        cross_domain_links=[
            "All cybersecurity functions",
            "Infrastructure (security ops)",
            "Applications (AppSec)",
        ],
        cost_drivers=[
            "Security FTE salaries (premium)",
            "MSSP/MDR fees",
            "Tools and platforms",
            "Training and certifications",
        ],
    ),

    "PMO/Project Management": FunctionReviewCriteria(
        function_name="PMO/Project Management",
        domain="organization",
        must_answer_questions=[
            "Is there a formal PMO?",
            "How many project managers?",
            "What methodology (Agile, Waterfall, hybrid)?",
            "What is the project portfolio size?",
            "What tools are used?",
            "What is the project success rate?",
        ],
        required_evidence=[
            "PMO existence (Y/N)",
            "PM headcount",
            "Methodology",
            "Active project count",
        ],
        risk_indicators=[
            "No PMO (ad-hoc project management)",
            "Overloaded PMs",
            "Poor project success rate",
            "No portfolio visibility",
            "Integration project capacity concern",
        ],
        mna_questions={
            "acquisition": [
                "Integration PMO structure?",
                "Who leads integration projects?",
            ],
            "carveout": [
                "PMO support from parent?",
                "TSA for project management?",
            ],
            "divestiture": [
                "PMO capacity post-divestiture?",
            ],
        },
        maturity_criteria={
            1: "No PMO, informal project management",
            2: "Basic PM, some methodology",
            3: "Formal PMO, portfolio management, reporting",
            4: "Mature PMO, resource optimization, metrics",
            5: "Strategic PMO, business alignment, continuous improvement",
        },
        cross_domain_links=[
            "All IT teams (project delivery)",
            "Business (stakeholder management)",
        ],
        cost_drivers=[
            "PM salaries",
            "PPM tools",
            "Contractor PMs for surge",
        ],
    ),

    "Data & Analytics Team": FunctionReviewCriteria(
        function_name="Data & Analytics Team",
        domain="organization",
        must_answer_questions=[
            "Is there a dedicated data team?",
            "What skills exist (BI, data engineering, data science)?",
            "Who owns data governance?",
            "What is the team size?",
            "What tools/platforms do they use?",
            "What is the relationship with business?",
        ],
        required_evidence=[
            "Team existence and size",
            "Skill breakdown",
            "Tools/platforms",
            "Governance model",
        ],
        risk_indicators=[
            "No data team (shadow analytics)",
            "BI only, no data engineering",
            "No data governance",
            "Single BI developer",
            "Critical reports undocumented",
        ],
        mna_questions={
            "acquisition": [
                "Data team integration?",
                "Analytics capabilities to leverage?",
            ],
            "carveout": [
                "Data team shared with parent?",
                "Analytics capability standalone?",
            ],
            "divestiture": [
                "Data team split?",
            ],
        },
        maturity_criteria={
            1: "No data team, business does own",
            2: "Basic BI support, reactive",
            3: "Data team, defined processes, governance",
            4: "Data platform, self-service, data engineering",
            5: "Data-driven culture, AI/ML, advanced analytics",
        },
        cross_domain_links=[
            "BI/Analytics (platform)",
            "Applications (data sources)",
            "Security (data privacy)",
        ],
        cost_drivers=[
            "Data team salaries",
            "Platform licensing",
            "Cloud compute for analytics",
        ],
    ),

    "Service Desk": FunctionReviewCriteria(
        function_name="Service Desk",
        domain="organization",
        must_answer_questions=[
            "How is service desk delivered (internal/MSP)?",
            "What is the headcount or FTE equivalent?",
            "What are the hours of coverage?",
            "What is the ticket volume and resolution time?",
            "What tools are used (ITSM platform)?",
            "What is the user satisfaction?",
        ],
        required_evidence=[
            "Delivery model (internal/MSP)",
            "Headcount or FTE",
            "Coverage hours",
            "ITSM tool name",
        ],
        risk_indicators=[
            "Fully outsourced (vendor dependency)",
            "Single point of contact",
            "No after-hours coverage",
            "Poor user satisfaction",
            "No ITSM tool (email-based)",
            "Contract ending soon",
        ],
        mna_questions={
            "acquisition": [
                "Can consolidate with buyer service desk?",
                "Tool alignment?",
            ],
            "carveout": [
                "Service desk part of parent shared services?",
                "TSA for service desk?",
                "Build or buy for standalone?",
            ],
            "divestiture": [
                "Impact on remaining service desk capacity?",
            ],
        },
        maturity_criteria={
            1: "Email-based, no ticketing, reactive",
            2: "Basic ITSM tool, ticket tracking",
            3: "ITIL-aligned, SLAs defined, self-service portal",
            4: "Automation, knowledge base, proactive support",
            5: "AI-assisted, predictive, excellent satisfaction",
        },
        cross_domain_links=[
            "Identity (user provisioning)",
            "Applications (app support)",
            "Infrastructure (hardware support)",
        ],
        cost_drivers=[
            "Headcount (internal)",
            "MSP fees (outsourced)",
            "ITSM tool licensing",
            "Training",
        ],
    ),
}


# =============================================================================
# CYBERSECURITY DOMAIN - DEEP DIVE CRITERIA
# =============================================================================

CYBERSECURITY_FUNCTIONS = {
    "Security Operations": FunctionReviewCriteria(
        function_name="Security Operations",
        domain="cybersecurity",
        must_answer_questions=[
            "Is there a SOC (internal, MSSP, none)?",
            "What SIEM is in use?",
            "What is the coverage (24x7, business hours)?",
            "What is the incident response capability?",
            "Who leads security?",
            "What is the security staffing level?",
        ],
        required_evidence=[
            "SOC model (internal/MSSP/none)",
            "SIEM name (or GAP)",
            "Coverage hours",
            "Security headcount",
        ],
        risk_indicators=[
            "No SIEM",
            "No SOC/monitoring",
            "Security is part-time role",
            "No incident response plan",
            "No 24x7 coverage for critical systems",
            "Parent-provided security (TSA exposure)",
        ],
        mna_questions={
            "acquisition": [
                "Can integrate with buyer SOC?",
                "SIEM consolidation?",
            ],
            "carveout": [
                "Security operations from parent?",
                "TSA for security services?",
                "Standalone security capability?",
            ],
            "divestiture": [
                "Impact on remaining security posture?",
            ],
        },
        maturity_criteria={
            1: "No monitoring, reactive only",
            2: "Basic logging, ad-hoc monitoring",
            3: "SIEM deployed, defined processes, some automation",
            4: "SOC with 24x7, threat hunting, SOAR",
            5: "Advanced analytics, AI/ML, integrated threat intel",
        },
        cross_domain_links=[
            "Infrastructure (log sources)",
            "Network (traffic analysis)",
            "Identity (privileged access)",
            "Applications (app security)",
        ],
        cost_drivers=[
            "Security staffing",
            "SIEM licensing (data volume)",
            "MSSP fees",
            "Incident response retainer",
        ],
    ),

    "Vulnerability Management": FunctionReviewCriteria(
        function_name="Vulnerability Management",
        domain="cybersecurity",
        must_answer_questions=[
            "What scanning tool (Qualys, Tenable, Rapid7)?",
            "What is the scanning coverage?",
            "What is the scan frequency?",
            "What is the patch cadence?",
            "What is the remediation SLA?",
            "Who owns vulnerability management?",
        ],
        required_evidence=[
            "Scanning tool name",
            "Coverage percentage",
            "Scan frequency",
            "Patch cadence",
        ],
        risk_indicators=[
            "No vulnerability scanning",
            "Low coverage (<80%)",
            "Infrequent scans (monthly or less)",
            "No remediation tracking",
            "Large backlog of critical vulns",
            "No patch management process",
        ],
        mna_questions={
            "acquisition": [
                "Same scanning platform?",
                "Current vulnerability posture?",
            ],
            "carveout": [
                "Scanning from parent?",
                "Standalone capability needed?",
            ],
            "divestiture": [
                "Scanning coverage impact?",
            ],
        },
        maturity_criteria={
            1: "No scanning, reactive patching",
            2: "Basic scanning, ad-hoc patching",
            3: "Regular scanning, defined SLAs, tracking",
            4: "Continuous scanning, automated patching, metrics",
            5: "Risk-based prioritization, predictive, integrated",
        },
        cross_domain_links=[
            "Infrastructure (patch deployment)",
            "Endpoint Security (remediation)",
            "Security Operations (risk tracking)",
        ],
        cost_drivers=[
            "Scanner licensing (per-IP)",
            "Patch management tools",
            "Remediation effort",
        ],
    ),

    "Security Compliance": FunctionReviewCriteria(
        function_name="Security Compliance",
        domain="cybersecurity",
        must_answer_questions=[
            "What compliance frameworks apply (SOC 2, ISO, PCI)?",
            "What certifications are current?",
            "Who owns compliance?",
            "What GRC tool is used?",
            "What is the audit schedule?",
            "Are there any compliance gaps?",
        ],
        required_evidence=[
            "Applicable frameworks",
            "Current certifications",
            "Compliance owner",
            "Last audit date",
        ],
        risk_indicators=[
            "Required certifications missing",
            "Audit findings unresolved",
            "No GRC tool or process",
            "Compliance gaps known",
            "Certification expiring",
            "No compliance staff",
        ],
        mna_questions={
            "acquisition": [
                "Buyer compliance requirements?",
                "Certification timeline post-close?",
            ],
            "carveout": [
                "Parent certifications cover target?",
                "Standalone certification needed?",
                "TSA for compliance?",
            ],
            "divestiture": [
                "Compliance certification impact?",
            ],
        },
        maturity_criteria={
            1: "No formal compliance program",
            2: "Basic compliance, reactive",
            3: "Formal program, regular audits, tracking",
            4: "Continuous compliance, automation, GRC platform",
            5: "Compliance-as-code, integrated, proactive",
        },
        cross_domain_links=[
            "All security functions",
            "IT Leadership (governance)",
            "Applications (data privacy)",
        ],
        cost_drivers=[
            "Audit fees",
            "GRC platform",
            "Compliance staff",
            "Remediation costs",
        ],
    ),

    "Endpoint Security": FunctionReviewCriteria(
        function_name="Endpoint Security",
        domain="cybersecurity",
        must_answer_questions=[
            "What endpoint protection (EDR/AV)?",
            "What is the coverage percentage?",
            "Is it managed (MDR) or self-managed?",
            "What OS types are covered?",
            "What is the response capability?",
        ],
        required_evidence=[
            "Endpoint protection name",
            "Coverage percentage",
            "Managed vs self-managed",
        ],
        risk_indicators=[
            "Legacy AV (not EDR)",
            "Coverage gaps (<95%)",
            "No Mac/Linux coverage",
            "No automated response",
            "Multiple tools (consolidation needed)",
        ],
        mna_questions={
            "acquisition": [
                "Same tool as buyer (consolidation)?",
                "License transfer possible?",
            ],
            "carveout": [
                "Part of parent enterprise license?",
                "Standalone license needed?",
            ],
            "divestiture": [
                "License structure impact?",
            ],
        },
        maturity_criteria={
            1: "Basic AV, limited coverage",
            2: "AV everywhere, manual response",
            3: "EDR deployed, automated response",
            4: "MDR service, threat hunting",
            5: "XDR, integrated response, continuous validation",
        },
        cross_domain_links=[
            "Identity (device trust)",
            "Network (network detection)",
            "Infrastructure (deployment)",
        ],
        cost_drivers=[
            "Per-endpoint licensing",
            "MDR services",
            "IR retainer",
        ],
    ),
}


# =============================================================================
# IDENTITY DOMAIN - DEEP DIVE CRITERIA
# =============================================================================

IDENTITY_FUNCTIONS = {
    "Directory Services": FunctionReviewCriteria(
        function_name="Directory Services",
        domain="identity_access",
        must_answer_questions=[
            "What directory service (AD, Azure AD, Okta)?",
            "How many forests/tenants?",
            "Is there federation or trust relationships?",
            "What is the user population?",
            "Who manages identity?",
            "What is the authentication method?",
        ],
        required_evidence=[
            "Directory platform",
            "Forest/tenant count",
            "User count",
            "Trust relationships",
        ],
        risk_indicators=[
            "Multiple AD forests (prior M&A)",
            "Parent AD forest (separation complexity)",
            "No Azure AD/cloud identity",
            "No MFA",
            "Single identity admin",
        ],
        mna_questions={
            "acquisition": [
                "Forest/tenant consolidation path?",
                "Trust or migration?",
            ],
            "carveout": [
                "Part of parent AD forest?",
                "New tenant/forest needed?",
                "TSA for identity services?",
            ],
            "divestiture": [
                "Identity separation plan?",
            ],
        },
        maturity_criteria={
            1: "Local accounts, no centralized directory",
            2: "AD deployed, basic group management",
            3: "Azure AD hybrid, SSO, MFA",
            4: "Identity governance, automated provisioning",
            5: "Zero trust, passwordless, continuous verification",
        },
        cross_domain_links=[
            "All applications (authentication)",
            "Security (access controls)",
            "HCM (JML integration)",
        ],
        cost_drivers=[
            "Directory licensing (Azure AD P1/P2)",
            "MFA licensing",
            "Identity governance tools",
        ],
    ),

    "Access Management": FunctionReviewCriteria(
        function_name="Access Management",
        domain="identity_access",
        must_answer_questions=[
            "What SSO solution (Okta, Azure AD, Ping)?",
            "How many applications in SSO?",
            "What MFA is deployed?",
            "What is MFA coverage percentage?",
            "What federation exists (SAML, OIDC)?",
            "Who manages access?",
        ],
        required_evidence=[
            "SSO platform",
            "Applications in SSO",
            "MFA solution",
            "MFA coverage %",
        ],
        risk_indicators=[
            "No SSO (password sprawl)",
            "Low MFA coverage (<80%)",
            "No MFA for admins",
            "Manual access provisioning",
            "No access reviews",
            "Orphaned accounts",
        ],
        mna_questions={
            "acquisition": [
                "SSO platform alignment?",
                "Federation or migration?",
            ],
            "carveout": [
                "SSO from parent?",
                "Standalone IdP needed?",
                "MFA licensing transfer?",
            ],
            "divestiture": [
                "Access separation plan?",
            ],
        },
        maturity_criteria={
            1: "No SSO, password-only, manual",
            2: "Some SSO, basic MFA",
            3: "Enterprise SSO, MFA everywhere, automated",
            4: "Adaptive MFA, RBAC, access certification",
            5: "Passwordless, continuous verification, zero trust",
        },
        cross_domain_links=[
            "Directory Services (identity source)",
            "All applications (access)",
            "Security (access controls)",
        ],
        cost_drivers=[
            "IdP licensing (per user)",
            "MFA licensing",
            "IGA platform",
        ],
    ),

    "JML Process": FunctionReviewCriteria(
        function_name="JML Process",
        domain="identity_access",
        must_answer_questions=[
            "What is the onboarding process?",
            "What is the offboarding process?",
            "How are movers handled?",
            "What systems are provisioned automatically?",
            "What is the typical provisioning time?",
            "Who owns JML process?",
            "What audit/compliance exists?",
        ],
        required_evidence=[
            "Onboarding process (documented Y/N)",
            "Offboarding process (documented Y/N)",
            "Automation level",
            "Average provisioning time",
        ],
        risk_indicators=[
            "Manual onboarding (slow, error-prone)",
            "Incomplete offboarding (orphaned access)",
            "No mover process (access creep)",
            "No access reviews",
            "Long provisioning time (>1 day)",
            "No audit trail",
        ],
        mna_questions={
            "acquisition": [
                "JML process integration?",
                "HR system alignment?",
            ],
            "carveout": [
                "JML handled by parent HR/IT?",
                "Standalone process needed?",
                "TSA for identity services?",
            ],
            "divestiture": [
                "JML separation?",
            ],
        },
        maturity_criteria={
            1: "Manual, email-based, inconsistent",
            2: "Some process, basic ticketing",
            3: "Defined process, automated triggers, SLAs",
            4: "Automated provisioning, access reviews, audit",
            5: "Full IGA, birthright access, continuous compliance",
        },
        cross_domain_links=[
            "HCM (employee lifecycle)",
            "Directory Services (account creation)",
            "All applications (access provisioning)",
        ],
        cost_drivers=[
            "IGA platform",
            "Manual effort (without automation)",
            "Compliance/audit costs",
        ],
    ),

    "Privileged Access": FunctionReviewCriteria(
        function_name="Privileged Access",
        domain="identity_access",
        must_answer_questions=[
            "Is there a PAM solution?",
            "What accounts are managed?",
            "What systems are covered?",
            "Is there session recording?",
            "How are credentials rotated?",
            "Who has admin access?",
        ],
        required_evidence=[
            "PAM solution (or GAP)",
            "Coverage scope",
            "Session recording (Y/N)",
        ],
        risk_indicators=[
            "No PAM solution",
            "Shared admin accounts",
            "No password rotation",
            "No session recording",
            "Privileged access not audited",
            "Too many admins",
        ],
        mna_questions={
            "acquisition": [
                "Can integrate with buyer PAM?",
                "Admin account consolidation?",
            ],
            "carveout": [
                "PAM from parent?",
                "Standalone PAM needed?",
            ],
            "divestiture": [
                "Privileged access separation?",
            ],
        },
        maturity_criteria={
            1: "Shared accounts, no controls",
            2: "Named accounts, manual rotation",
            3: "PAM deployed, automated rotation",
            4: "Session recording, just-in-time access",
            5: "Zero standing privilege, full audit, analytics",
        },
        cross_domain_links=[
            "Security Operations (monitoring)",
            "Infrastructure (system access)",
            "Applications (app admin access)",
        ],
        cost_drivers=[
            "PAM licensing",
            "Implementation services",
            "Ongoing administration",
        ],
    ),
}


# =============================================================================
# NETWORK DOMAIN - DEEP DIVE CRITERIA
# =============================================================================

NETWORK_FUNCTIONS = {
    "WAN": FunctionReviewCriteria(
        function_name="WAN",
        domain="network",
        must_answer_questions=[
            "What WAN technology (MPLS, SD-WAN, Internet)?",
            "Who is the carrier(s)?",
            "What is the bandwidth per site?",
            "What is the contract status and term?",
            "How many sites connected?",
            "What is the redundancy model?",
            "Who manages the WAN?",
        ],
        required_evidence=[
            "WAN technology type",
            "Carrier name(s)",
            "Site count",
            "Contract term/expiry",
        ],
        risk_indicators=[
            "Single carrier (no redundancy)",
            "Contract expiring within 12 months",
            "Parent WAN (separation complexity)",
            "No SD-WAN (limited agility)",
            "Bandwidth constraints",
            "Long-term contract (lock-in)",
        ],
        mna_questions={
            "acquisition": [
                "Can sites connect to buyer network?",
                "WAN consolidation opportunity?",
                "Contract transfer possible?",
            ],
            "carveout": [
                "Part of parent WAN?",
                "Dedicated circuits needed?",
                "TSA for network services?",
            ],
            "divestiture": [
                "Circuit ownership?",
                "Impact on remaining sites?",
            ],
        },
        maturity_criteria={
            1: "Basic internet, no redundancy",
            2: "MPLS, single carrier, limited monitoring",
            3: "Multi-carrier or SD-WAN, good monitoring",
            4: "Full SD-WAN, automated failover, SLA management",
            5: "Software-defined, fully automated, optimized",
        },
        cross_domain_links=[
            "Cloud (ExpressRoute/Direct Connect)",
            "Security (WAN security)",
            "Applications (bandwidth requirements)",
            "DR (replication traffic)",
        ],
        cost_drivers=[
            "Circuit costs (bandwidth)",
            "SD-WAN licensing",
            "Managed service fees",
            "Installation/change fees",
        ],
    ),

    "VPN/Remote Access": FunctionReviewCriteria(
        function_name="VPN/Remote Access",
        domain="network",
        must_answer_questions=[
            "What VPN solution (Cisco, Palo Alto, etc.)?",
            "How many concurrent users?",
            "What authentication method (MFA)?",
            "Is there split-tunnel or full-tunnel?",
            "What resources are accessible?",
            "Who manages VPN?",
        ],
        required_evidence=[
            "VPN solution name",
            "Concurrent user capacity",
            "MFA enabled (Y/N)",
            "Tunnel type",
        ],
        risk_indicators=[
            "No MFA on VPN",
            "Capacity constraints (COVID surge)",
            "Legacy VPN (client issues)",
            "No logging/monitoring",
            "Split-tunnel without security",
        ],
        mna_questions={
            "acquisition": [
                "Consolidate with buyer VPN?",
                "Timeline to integrate?",
            ],
            "carveout": [
                "VPN infrastructure shared?",
                "Standalone VPN needed?",
            ],
            "divestiture": [
                "VPN separation plan?",
            ],
        },
        maturity_criteria={
            1: "Basic VPN, no MFA, limited capacity",
            2: "VPN with MFA, adequate capacity",
            3: "Modern VPN, integrated MFA, monitored",
            4: "Always-on VPN, ZTNA elements",
            5: "Full ZTNA, no traditional VPN",
        },
        cross_domain_links=[
            "Identity (authentication)",
            "Security (access controls)",
            "Endpoint (device compliance)",
        ],
        cost_drivers=[
            "VPN licensing (concurrent users)",
            "Hardware refresh",
            "Support contracts",
        ],
    ),

    "LAN": FunctionReviewCriteria(
        function_name="LAN",
        domain="network",
        must_answer_questions=[
            "What LAN switching platform (Cisco, Aruba, etc.)?",
            "How many sites and switches?",
            "What is the network topology?",
            "What segmentation exists (VLANs)?",
            "What is the equipment age?",
            "Who manages LAN?",
        ],
        required_evidence=[
            "Switch platform",
            "Site count",
            "Switch count",
            "Management model",
        ],
        risk_indicators=[
            "Aging equipment (EOL)",
            "No network segmentation",
            "Single switch (no redundancy)",
            "Flat network (security risk)",
            "No monitoring",
            "Undocumented topology",
        ],
        mna_questions={
            "acquisition": [
                "Same platform as buyer?",
                "Network integration path?",
            ],
            "carveout": [
                "LAN shared with parent?",
                "Network separation needed?",
            ],
            "divestiture": [
                "Equipment ownership?",
            ],
        },
        maturity_criteria={
            1: "Basic switches, no segmentation, unmanaged",
            2: "Managed switches, basic VLANs",
            3: "Enterprise network, segmented, monitored",
            4: "Software-defined elements, automation",
            5: "Full SDN, microsegmentation, self-healing",
        },
        cross_domain_links=[
            "Security (segmentation)",
            "Wireless (campus network)",
            "Infrastructure (server connectivity)",
        ],
        cost_drivers=[
            "Hardware refresh",
            "Maintenance contracts",
            "Management tools",
        ],
    ),

    "Wireless": FunctionReviewCriteria(
        function_name="Wireless",
        domain="network",
        must_answer_questions=[
            "What WiFi platform (Cisco, Aruba, Meraki)?",
            "How many access points?",
            "What is the coverage?",
            "What security (WPA3, 802.1X)?",
            "Is there guest WiFi separation?",
            "Who manages wireless?",
        ],
        required_evidence=[
            "WiFi platform",
            "Access point count",
            "Coverage areas",
            "Security method",
        ],
        risk_indicators=[
            "Legacy WiFi (WPA2-PSK)",
            "No guest network separation",
            "Coverage gaps",
            "Rogue AP concerns",
            "No WIPS/WIDS",
            "Aging equipment",
        ],
        mna_questions={
            "acquisition": [
                "WiFi platform alignment?",
                "Site-by-site integration?",
            ],
            "carveout": [
                "WiFi part of parent network?",
                "Standalone SSID needed?",
            ],
            "divestiture": [
                "WiFi equipment ownership?",
            ],
        },
        maturity_criteria={
            1: "Basic WiFi, no security, no management",
            2: "Managed WiFi, basic security",
            3: "Enterprise WiFi, 802.1X, guest separation",
            4: "Cloud-managed, analytics, optimization",
            5: "AI-driven, self-optimizing, integrated",
        },
        cross_domain_links=[
            "LAN (wired backbone)",
            "Security (wireless security)",
            "Identity (802.1X auth)",
        ],
        cost_drivers=[
            "Access point hardware",
            "Controller/cloud licensing",
            "Management platform",
        ],
    ),

    "Firewalls/Security": FunctionReviewCriteria(
        function_name="Firewalls/Security",
        domain="network",
        must_answer_questions=[
            "What firewall platform (Palo Alto, Fortinet, Cisco)?",
            "How many firewalls and where?",
            "What features enabled (IPS, AV, URL filtering)?",
            "Who manages firewalls?",
            "What is the rule review process?",
            "Are firewalls HA configured?",
        ],
        required_evidence=[
            "Firewall platform",
            "Firewall count and locations",
            "Management model",
            "HA status",
        ],
        risk_indicators=[
            "EOL firewall versions",
            "No IPS/threat prevention",
            "Single firewall (no HA)",
            "Rules never reviewed",
            "Mixed vendors (complexity)",
            "Parent-managed firewalls",
        ],
        mna_questions={
            "acquisition": [
                "Same platform as buyer?",
                "Policy consolidation?",
            ],
            "carveout": [
                "Firewalls part of parent infrastructure?",
                "Standalone firewalls needed?",
            ],
            "divestiture": [
                "Firewall ownership?",
                "Policy separation?",
            ],
        },
        maturity_criteria={
            1: "Basic packet filtering, no HA",
            2: "Stateful with IPS, some HA",
            3: "NGFW with full features, HA, monitored",
            4: "Automated policy management, threat intel",
            5: "Software-defined, zero trust microsegmentation",
        },
        cross_domain_links=[
            "Security Operations (monitoring)",
            "WAN (perimeter protection)",
            "Cloud (cloud firewalls)",
        ],
        cost_drivers=[
            "Hardware/licensing",
            "Support/subscription",
            "Management (internal or MSSP)",
        ],
    ),
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_function_criteria(domain: str, function_name: str) -> Optional[FunctionReviewCriteria]:
    """Get review criteria for a specific function."""
    domain_map = {
        "infrastructure": INFRASTRUCTURE_FUNCTIONS,
        "applications": APPLICATIONS_FUNCTIONS,
        "organization": ORGANIZATION_FUNCTIONS,
        "cybersecurity": CYBERSECURITY_FUNCTIONS,
        "identity_access": IDENTITY_FUNCTIONS,
        "network": NETWORK_FUNCTIONS,
    }

    domain_functions = domain_map.get(domain, {})
    return domain_functions.get(function_name)


def get_all_criteria() -> Dict[str, Dict[str, FunctionReviewCriteria]]:
    """Get all function review criteria."""
    return {
        "infrastructure": INFRASTRUCTURE_FUNCTIONS,
        "applications": APPLICATIONS_FUNCTIONS,
        "organization": ORGANIZATION_FUNCTIONS,
        "cybersecurity": CYBERSECURITY_FUNCTIONS,
        "identity_access": IDENTITY_FUNCTIONS,
        "network": NETWORK_FUNCTIONS,
    }


def assess_function_completeness(
    function_name: str,
    domain: str,
    evidence: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Assess completeness of evidence for a function.

    Returns:
        Dict with completeness score and gaps identified
    """
    criteria = get_function_criteria(domain, function_name)
    if not criteria:
        return {"error": f"No criteria defined for {domain}/{function_name}"}

    # Check required evidence
    evidence_found = []
    evidence_missing = []

    for req in criteria.required_evidence:
        # Simple check - look for key terms in evidence dict
        found = False
        for key, value in evidence.items():
            if req.lower() in key.lower() or (value and req.lower() in str(value).lower()):
                found = True
                break

        if found:
            evidence_found.append(req)
        else:
            evidence_missing.append(req)

    completeness = len(evidence_found) / len(criteria.required_evidence) * 100 if criteria.required_evidence else 0

    return {
        "function": function_name,
        "domain": domain,
        "completeness_pct": round(completeness, 1),
        "evidence_found": evidence_found,
        "evidence_missing": evidence_missing,
        "risk_indicators_to_check": criteria.risk_indicators,
        "questions_to_answer": criteria.must_answer_questions,
    }


def get_cross_domain_dependencies(function_name: str, domain: str) -> List[str]:
    """Get cross-domain dependencies for a function."""
    criteria = get_function_criteria(domain, function_name)
    if criteria:
        return criteria.cross_domain_links
    return []


def get_mna_questions(function_name: str, domain: str, deal_type: str) -> List[str]:
    """Get M&A-specific questions for a function and deal type."""
    criteria = get_function_criteria(domain, function_name)
    if criteria and deal_type in criteria.mna_questions:
        return criteria.mna_questions[deal_type]
    return []


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    'MaturityLevel',
    'FunctionReviewCriteria',
    'INFRASTRUCTURE_FUNCTIONS',
    'APPLICATIONS_FUNCTIONS',
    'ORGANIZATION_FUNCTIONS',
    'CYBERSECURITY_FUNCTIONS',
    'IDENTITY_FUNCTIONS',
    'NETWORK_FUNCTIONS',
    'get_function_criteria',
    'get_all_criteria',
    'assess_function_completeness',
    'get_cross_domain_dependencies',
    'get_mna_questions',
]
