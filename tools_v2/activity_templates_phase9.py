"""
Activity Templates V2 - Phase 9: Vendor & Contract

Phase 9: Vendor and Contract Transition
- Contract Analysis (review, transfer rights, assignment)
- Vendor Transition (relationship transfer, notifications)
- Contract Negotiation (new agreements, amendments, terminations)
- Third-Party Risk (vendor due diligence, assessments)
- Procurement (new vendor selection, RFP, sourcing)

Key considerations for carveouts:
- Many contracts don't allow assignment without consent
- Parent volume discounts typically don't transfer
- New entity may not have credit/payment history
- Critical vendors need early engagement
- Some contracts may require TSA coverage during transition

Each activity template includes:
- name: Activity name
- description: What this activity involves
- activity_type: "assessment", "negotiation", "implementation"
- cost_model: How cost is calculated
- timeline_months: Duration range
- requires_tsa: Whether TSA is typically needed
- notes: Implementation considerations
"""

from typing import Dict, List, Any

# Import shared modifiers from Phase 1
from tools_v2.activity_templates_v2 import COMPLEXITY_MULTIPLIERS, INDUSTRY_MODIFIERS

# =============================================================================
# PHASE 9: CONTRACT ANALYSIS
# =============================================================================

CONTRACT_ANALYSIS_TEMPLATES = {
    "vendor_contract": [
        # -----------------------------------------------------------------
        # CONTRACT INVENTORY
        # -----------------------------------------------------------------
        {
            "id": "VND-CON-001",
            "name": "IT contract inventory",
            "description": "Comprehensive inventory of all IT-related contracts",
            "activity_type": "assessment",
            "phase": "assessment",
            "base_cost": (25000, 60000),
            "per_contract_cost": (200, 600),
            "timeline_months": (0.5, 1.5),
            "requires_tsa": False,
            "prerequisites": [],
            "outputs": ["Contract inventory", "Vendor list", "Spend analysis", "Expiration schedule"],
        },
        {
            "id": "VND-CON-002",
            "name": "Contract categorization and prioritization",
            "description": "Categorize contracts by criticality and transition complexity",
            "activity_type": "assessment",
            "phase": "assessment",
            "base_cost": (15000, 40000),
            "timeline_months": (0.25, 0.75),
            "requires_tsa": False,
            "prerequisites": ["VND-CON-001"],
            "outputs": ["Priority matrix", "Critical vendor list", "Transition complexity", "Risk assessment"],
        },
        {
            "id": "VND-CON-003",
            "name": "Contract spend analysis",
            "description": "Analyze IT spend by vendor, category, and cost center",
            "activity_type": "assessment",
            "phase": "assessment",
            "base_cost": (20000, 50000),
            "timeline_months": (0.5, 1),
            "requires_tsa": False,
            "prerequisites": ["VND-CON-001"],
            "outputs": ["Spend analysis", "Cost allocation", "Budget baseline", "Savings opportunities"],
        },
        # -----------------------------------------------------------------
        # TRANSFER RIGHTS ANALYSIS
        # -----------------------------------------------------------------
        {
            "id": "VND-CON-010",
            "name": "Assignment clause analysis",
            "description": "Review contracts for assignment and transfer provisions",
            "activity_type": "assessment",
            "phase": "assessment",
            "base_cost": (30000, 80000),
            "per_contract_cost": (300, 1000),
            "timeline_months": (0.5, 1.5),
            "requires_tsa": False,
            "prerequisites": ["VND-CON-001"],
            "outputs": ["Assignment analysis", "Consent requirements", "Transfer restrictions", "Risk summary"],
            "notes": "Legal review typically required",
        },
        {
            "id": "VND-CON-011",
            "name": "License transfer rights analysis",
            "description": "Analyze software license transfer and portability rights",
            "activity_type": "assessment",
            "phase": "assessment",
            "base_cost": (25000, 70000),
            "per_contract_cost": (500, 1500),
            "timeline_months": (0.5, 1.5),
            "requires_tsa": False,
            "prerequisites": ["VND-CON-001"],
            "outputs": ["Transfer rights summary", "Portability analysis", "Re-procurement needs"],
        },
        {
            "id": "VND-CON-012",
            "name": "Change of control analysis",
            "description": "Assess change of control provisions and impacts",
            "activity_type": "assessment",
            "phase": "assessment",
            "base_cost": (20000, 50000),
            "timeline_months": (0.25, 0.75),
            "requires_tsa": False,
            "prerequisites": ["VND-CON-010"],
            "outputs": ["CoC provisions", "Notification requirements", "Consent needs", "Risk mitigation"],
        },
        # -----------------------------------------------------------------
        # TERMINATION ANALYSIS
        # -----------------------------------------------------------------
        {
            "id": "VND-CON-020",
            "name": "Termination rights and costs analysis",
            "description": "Analyze termination provisions, fees, and notice periods",
            "activity_type": "assessment",
            "phase": "assessment",
            "base_cost": (20000, 50000),
            "per_contract_cost": (200, 600),
            "timeline_months": (0.5, 1),
            "requires_tsa": False,
            "prerequisites": ["VND-CON-001"],
            "outputs": ["Termination provisions", "ETF analysis", "Notice requirements", "Exit costs"],
        },
        {
            "id": "VND-CON-021",
            "name": "Minimum commitment analysis",
            "description": "Analyze minimum purchase commitments and true-up obligations",
            "activity_type": "assessment",
            "phase": "assessment",
            "base_cost": (15000, 40000),
            "timeline_months": (0.25, 0.75),
            "requires_tsa": False,
            "prerequisites": ["VND-CON-001"],
            "outputs": ["Commitment analysis", "True-up exposure", "Shortfall risks"],
        },
        {
            "id": "VND-CON-022",
            "name": "Data return and deletion provisions",
            "description": "Analyze data portability and deletion requirements",
            "activity_type": "assessment",
            "phase": "assessment",
            "base_cost": (15000, 40000),
            "per_contract_cost": (200, 500),
            "timeline_months": (0.25, 0.75),
            "requires_tsa": False,
            "prerequisites": ["VND-CON-001"],
            "outputs": ["Data return provisions", "Deletion requirements", "Format specifications"],
        },
    ],
}

# =============================================================================
# PHASE 9: VENDOR TRANSITION
# =============================================================================

VENDOR_TRANSITION_TEMPLATES = {
    "vendor_contract": [
        # -----------------------------------------------------------------
        # VENDOR NOTIFICATION
        # -----------------------------------------------------------------
        {
            "id": "VND-TRN-001",
            "name": "Vendor notification planning",
            "description": "Plan vendor notification strategy and timing",
            "activity_type": "implementation",
            "phase": "planning",
            "base_cost": (15000, 40000),
            "timeline_months": (0.25, 0.5),
            "requires_tsa": False,
            "prerequisites": ["VND-CON-002"],
            "outputs": ["Notification plan", "Communication templates", "Timeline", "Escalation paths"],
        },
        {
            "id": "VND-TRN-002",
            "name": "Critical vendor engagement",
            "description": "Early engagement with critical/strategic vendors",
            "activity_type": "implementation",
            "phase": "planning",
            "base_cost": (25000, 60000),
            "per_vendor_cost": (2000, 6000),
            "timeline_months": (0.5, 1.5),
            "requires_tsa": False,
            "prerequisites": ["VND-TRN-001"],
            "outputs": ["Vendor meetings", "Transition discussions", "Preliminary agreements"],
            "notes": "Top 10-20 vendors typically need dedicated engagement",
        },
        {
            "id": "VND-TRN-003",
            "name": "Vendor notification execution",
            "description": "Execute formal vendor notifications",
            "activity_type": "implementation",
            "phase": "execution",
            "base_cost": (15000, 40000),
            "per_vendor_cost": (200, 500),
            "timeline_months": (0.25, 0.75),
            "requires_tsa": False,
            "prerequisites": ["VND-TRN-001"],
            "outputs": ["Notification letters", "Acknowledgments", "Response tracking"],
        },
        # -----------------------------------------------------------------
        # ACCOUNT TRANSITION
        # -----------------------------------------------------------------
        {
            "id": "VND-TRN-010",
            "name": "Vendor account setup",
            "description": "Establish new vendor accounts for standalone entity",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (20000, 50000),
            "per_vendor_cost": (300, 1000),
            "timeline_months": (1, 2),
            "requires_tsa": False,
            "prerequisites": ["VND-TRN-003"],
            "outputs": ["New accounts", "Credit applications", "Payment setup", "Portal access"],
        },
        {
            "id": "VND-TRN-011",
            "name": "Vendor portal and access migration",
            "description": "Migrate vendor portal access and credentials",
            "activity_type": "implementation",
            "phase": "migration",
            "base_cost": (10000, 30000),
            "per_vendor_cost": (100, 400),
            "timeline_months": (0.5, 1),
            "requires_tsa": False,
            "prerequisites": ["VND-TRN-010"],
            "outputs": ["Portal access", "Credentials", "User assignments"],
        },
        {
            "id": "VND-TRN-012",
            "name": "Support contract transition",
            "description": "Transfer or establish new support contracts",
            "activity_type": "implementation",
            "phase": "migration",
            "base_cost": (20000, 50000),
            "per_contract_cost": (500, 2000),
            "timeline_months": (1, 2),
            "requires_tsa": True,
            "tsa_duration": (3, 6),
            "prerequisites": ["VND-TRN-010"],
            "outputs": ["Support contracts", "SLA definitions", "Escalation paths", "Contact lists"],
        },
        # -----------------------------------------------------------------
        # RELATIONSHIP MANAGEMENT
        # -----------------------------------------------------------------
        {
            "id": "VND-TRN-020",
            "name": "Vendor relationship manager assignment",
            "description": "Assign relationship owners for key vendors",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (10000, 30000),
            "timeline_months": (0.25, 0.5),
            "requires_tsa": False,
            "prerequisites": ["VND-CON-002"],
            "outputs": ["Relationship owners", "RACI matrix", "Meeting cadence"],
        },
        {
            "id": "VND-TRN-021",
            "name": "Vendor governance establishment",
            "description": "Establish vendor governance and review processes",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (20000, 50000),
            "timeline_months": (0.5, 1.5),
            "requires_tsa": False,
            "prerequisites": ["VND-TRN-020"],
            "outputs": ["Governance framework", "Review cadence", "Scorecard", "Issue management"],
        },
        {
            "id": "VND-TRN-022",
            "name": "Strategic vendor QBR establishment",
            "description": "Establish quarterly business reviews with strategic vendors",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (15000, 40000),
            "per_vendor_cost": (1000, 3000),
            "timeline_months": (0.5, 1),
            "requires_tsa": False,
            "prerequisites": ["VND-TRN-021"],
            "outputs": ["QBR schedule", "Agenda templates", "Reporting framework"],
        },
    ],
}

# =============================================================================
# PHASE 9: CONTRACT NEGOTIATION
# =============================================================================

CONTRACT_NEGOTIATION_TEMPLATES = {
    "vendor_contract": [
        # -----------------------------------------------------------------
        # NEW CONTRACTS
        # -----------------------------------------------------------------
        {
            "id": "VND-NEG-001",
            "name": "Contract negotiation strategy",
            "description": "Develop negotiation strategy for key contracts",
            "activity_type": "negotiation",
            "phase": "planning",
            "base_cost": (25000, 60000),
            "timeline_months": (0.5, 1),
            "requires_tsa": False,
            "prerequisites": ["VND-CON-001", "VND-CON-010"],
            "outputs": ["Negotiation playbook", "Position papers", "BATNA analysis", "Target terms"],
        },
        {
            "id": "VND-NEG-002",
            "name": "New master agreement negotiation",
            "description": "Negotiate new master service agreements",
            "activity_type": "negotiation",
            "phase": "negotiation",
            "base_cost": (30000, 100000),
            "per_contract_cost": (5000, 20000),
            "timeline_months": (2, 6),
            "requires_tsa": True,
            "tsa_duration": (3, 9),
            "prerequisites": ["VND-NEG-001"],
            "outputs": ["Executed MSAs", "Negotiated terms", "Rate cards"],
            "notes": "Major vendors (Microsoft, Oracle, SAP) require significant effort",
        },
        {
            "id": "VND-NEG-003",
            "name": "Contract assignment negotiation",
            "description": "Negotiate contract assignments with vendor consent",
            "activity_type": "negotiation",
            "phase": "negotiation",
            "base_cost": (20000, 50000),
            "per_contract_cost": (2000, 8000),
            "timeline_months": (1, 3),
            "requires_tsa": True,
            "tsa_duration": (2, 6),
            "prerequisites": ["VND-CON-010"],
            "outputs": ["Assignment agreements", "Consent letters", "Amended terms"],
        },
        {
            "id": "VND-NEG-004",
            "name": "Statement of work negotiation",
            "description": "Negotiate new or transferred SOWs",
            "activity_type": "negotiation",
            "phase": "negotiation",
            "base_cost": (15000, 40000),
            "per_contract_cost": (1000, 4000),
            "timeline_months": (0.5, 2),
            "requires_tsa": False,
            "prerequisites": ["VND-NEG-002"],
            "outputs": ["Executed SOWs", "Scope definitions", "Pricing"],
        },
        # -----------------------------------------------------------------
        # AMENDMENTS AND RENEWALS
        # -----------------------------------------------------------------
        {
            "id": "VND-NEG-010",
            "name": "Contract amendment negotiation",
            "description": "Negotiate amendments to existing contracts",
            "activity_type": "negotiation",
            "phase": "negotiation",
            "base_cost": (15000, 40000),
            "per_contract_cost": (1500, 5000),
            "timeline_months": (0.5, 2),
            "requires_tsa": False,
            "prerequisites": ["VND-CON-010"],
            "outputs": ["Amendments", "Updated terms", "New pricing"],
        },
        {
            "id": "VND-NEG-011",
            "name": "Contract renewal negotiation",
            "description": "Negotiate contract renewals at favorable terms",
            "activity_type": "negotiation",
            "phase": "negotiation",
            "base_cost": (20000, 50000),
            "per_contract_cost": (2000, 8000),
            "timeline_months": (1, 3),
            "requires_tsa": False,
            "prerequisites": [],
            "outputs": ["Renewed contracts", "Improved terms", "Rate reductions"],
        },
        {
            "id": "VND-NEG-012",
            "name": "Volume/pricing renegotiation",
            "description": "Renegotiate pricing after loss of parent volume discounts",
            "activity_type": "negotiation",
            "phase": "negotiation",
            "base_cost": (25000, 70000),
            "per_contract_cost": (2000, 6000),
            "timeline_months": (1, 3),
            "requires_tsa": False,
            "prerequisites": ["VND-CON-003"],
            "outputs": ["Revised pricing", "New discount structure", "Commitment levels"],
            "notes": "Standalone entity typically gets worse pricing; mitigate through negotiation",
        },
        # -----------------------------------------------------------------
        # TERMINATIONS
        # -----------------------------------------------------------------
        {
            "id": "VND-NEG-020",
            "name": "Contract termination execution",
            "description": "Execute contract terminations and wind-down",
            "activity_type": "negotiation",
            "phase": "execution",
            "base_cost": (15000, 40000),
            "per_contract_cost": (1000, 3000),
            "timeline_months": (1, 3),
            "requires_tsa": False,
            "prerequisites": ["VND-CON-020"],
            "outputs": ["Termination notices", "Wind-down plans", "Final settlements"],
        },
        {
            "id": "VND-NEG-021",
            "name": "Early termination fee negotiation",
            "description": "Negotiate reduction or waiver of early termination fees",
            "activity_type": "negotiation",
            "phase": "negotiation",
            "base_cost": (20000, 50000),
            "per_contract_cost": (2000, 8000),
            "timeline_months": (0.5, 2),
            "requires_tsa": False,
            "prerequisites": ["VND-CON-020"],
            "outputs": ["ETF reductions", "Waiver agreements", "Settlement terms"],
        },
        {
            "id": "VND-NEG-022",
            "name": "Vendor exit and data extraction",
            "description": "Manage vendor exit including data extraction",
            "activity_type": "implementation",
            "phase": "execution",
            "base_cost": (15000, 40000),
            "per_vendor_cost": (2000, 8000),
            "timeline_months": (0.5, 2),
            "requires_tsa": False,
            "prerequisites": ["VND-CON-022"],
            "outputs": ["Data extraction", "Service cutoff", "Deletion confirmation"],
        },
    ],
}

# =============================================================================
# PHASE 9: THIRD-PARTY RISK
# =============================================================================

THIRD_PARTY_RISK_TEMPLATES = {
    "vendor_contract": [
        # -----------------------------------------------------------------
        # RISK ASSESSMENT
        # -----------------------------------------------------------------
        {
            "id": "VND-RSK-001",
            "name": "Third-party risk program establishment",
            "description": "Establish vendor risk management program",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (40000, 100000),
            "timeline_months": (1, 3),
            "requires_tsa": False,
            "prerequisites": [],
            "outputs": ["TPRM framework", "Risk methodology", "Assessment criteria", "Governance"],
        },
        {
            "id": "VND-RSK-002",
            "name": "Vendor risk tiering",
            "description": "Tier vendors by risk level and criticality",
            "activity_type": "assessment",
            "phase": "assessment",
            "base_cost": (20000, 50000),
            "per_vendor_cost": (100, 400),
            "timeline_months": (0.5, 1),
            "requires_tsa": False,
            "prerequisites": ["VND-CON-001"],
            "outputs": ["Vendor tiers", "Criticality ratings", "Assessment requirements"],
        },
        {
            "id": "VND-RSK-003",
            "name": "Critical vendor due diligence",
            "description": "Conduct due diligence on critical vendors",
            "activity_type": "assessment",
            "phase": "assessment",
            "base_cost": (25000, 60000),
            "per_vendor_cost": (2000, 8000),
            "timeline_months": (1, 3),
            "requires_tsa": False,
            "prerequisites": ["VND-RSK-002"],
            "outputs": ["Due diligence reports", "Risk assessments", "Findings", "Remediation plans"],
        },
        {
            "id": "VND-RSK-004",
            "name": "Vendor security assessment",
            "description": "Assess vendor security posture and controls",
            "activity_type": "assessment",
            "phase": "assessment",
            "base_cost": (20000, 50000),
            "per_vendor_cost": (1500, 5000),
            "timeline_months": (1, 2),
            "requires_tsa": False,
            "prerequisites": ["VND-RSK-002"],
            "outputs": ["Security questionnaires", "SOC reports review", "Penetration test results"],
        },
        # -----------------------------------------------------------------
        # COMPLIANCE AND CONTRACTS
        # -----------------------------------------------------------------
        {
            "id": "VND-RSK-010",
            "name": "Vendor compliance verification",
            "description": "Verify vendor compliance with regulatory requirements",
            "activity_type": "assessment",
            "phase": "assessment",
            "base_cost": (20000, 50000),
            "per_vendor_cost": (500, 2000),
            "timeline_months": (0.5, 1.5),
            "requires_tsa": False,
            "prerequisites": ["VND-RSK-002"],
            "outputs": ["Compliance verification", "Certification review", "Gap identification"],
        },
        {
            "id": "VND-RSK-011",
            "name": "Contract security requirements",
            "description": "Define and negotiate security requirements in contracts",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (20000, 50000),
            "timeline_months": (0.5, 1.5),
            "requires_tsa": False,
            "prerequisites": ["VND-RSK-001"],
            "outputs": ["Security addenda", "SLA requirements", "Audit rights", "Breach notification"],
        },
        {
            "id": "VND-RSK-012",
            "name": "Business associate agreement management",
            "description": "Manage BAAs and data processing agreements",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (20000, 50000),
            "per_contract_cost": (500, 1500),
            "timeline_months": (1, 2),
            "requires_tsa": False,
            "prerequisites": [],
            "outputs": ["BAAs", "DPAs", "Executed agreements", "Compliance tracking"],
        },
        # -----------------------------------------------------------------
        # ONGOING MONITORING
        # -----------------------------------------------------------------
        {
            "id": "VND-RSK-020",
            "name": "Vendor monitoring program",
            "description": "Establish ongoing vendor monitoring capabilities",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (30000, 80000),
            "timeline_months": (1, 2),
            "requires_tsa": False,
            "prerequisites": ["VND-RSK-001"],
            "outputs": ["Monitoring program", "Alert thresholds", "Review cadence", "Reporting"],
        },
        {
            "id": "VND-RSK-021",
            "name": "TPRM platform implementation",
            "description": "Implement third-party risk management platform",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (50000, 150000),
            "timeline_months": (2, 4),
            "requires_tsa": False,
            "prerequisites": ["VND-RSK-001"],
            "outputs": ["TPRM platform", "Assessment workflows", "Risk scoring", "Reporting"],
            "notes": "Prevalent, OneTrust, ProcessUnity, etc.",
        },
        {
            "id": "VND-RSK-022",
            "name": "Vendor incident response planning",
            "description": "Plan for vendor-related security incidents",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (15000, 40000),
            "timeline_months": (0.5, 1),
            "requires_tsa": False,
            "prerequisites": ["VND-RSK-001"],
            "outputs": ["Vendor IR playbook", "Communication templates", "Escalation paths"],
        },
    ],
}

# =============================================================================
# PHASE 9: PROCUREMENT
# =============================================================================

PROCUREMENT_TEMPLATES = {
    "vendor_contract": [
        # -----------------------------------------------------------------
        # PROCUREMENT FUNCTION
        # -----------------------------------------------------------------
        {
            "id": "VND-PRO-001",
            "name": "IT procurement function establishment",
            "description": "Establish IT procurement capabilities",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (30000, 80000),
            "timeline_months": (1, 2),
            "requires_tsa": False,
            "prerequisites": [],
            "outputs": ["Procurement process", "Policies", "Approval workflows", "Templates"],
        },
        {
            "id": "VND-PRO-002",
            "name": "Procurement system setup",
            "description": "Configure procurement system for standalone operations",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (25000, 75000),
            "timeline_months": (1, 2),
            "requires_tsa": False,
            "prerequisites": ["VND-PRO-001"],
            "outputs": ["Procurement system", "Catalog setup", "Approval routing", "Reporting"],
        },
        {
            "id": "VND-PRO-003",
            "name": "Vendor master data setup",
            "description": "Establish vendor master data in financial systems",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (15000, 40000),
            "per_vendor_cost": (50, 200),
            "timeline_months": (0.5, 1.5),
            "requires_tsa": False,
            "prerequisites": ["VND-CON-001"],
            "outputs": ["Vendor master records", "Payment terms", "Banking details"],
        },
        # -----------------------------------------------------------------
        # SOURCING
        # -----------------------------------------------------------------
        {
            "id": "VND-PRO-010",
            "name": "Strategic sourcing initiative",
            "description": "Conduct strategic sourcing for key IT categories",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (40000, 120000),
            "per_category_cost": (10000, 30000),
            "timeline_months": (2, 4),
            "requires_tsa": False,
            "prerequisites": ["VND-CON-003"],
            "outputs": ["Category strategy", "Market analysis", "Vendor shortlist", "Recommendations"],
        },
        {
            "id": "VND-PRO-011",
            "name": "RFP development and execution",
            "description": "Develop and execute RFPs for major procurements",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (20000, 60000),
            "per_rfp_cost": (5000, 20000),
            "timeline_months": (1, 3),
            "requires_tsa": False,
            "prerequisites": ["VND-PRO-010"],
            "outputs": ["RFP documents", "Vendor responses", "Evaluation", "Selection"],
        },
        {
            "id": "VND-PRO-012",
            "name": "Vendor selection and onboarding",
            "description": "Select and onboard new vendors",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (15000, 40000),
            "per_vendor_cost": (1000, 4000),
            "timeline_months": (1, 2),
            "requires_tsa": False,
            "prerequisites": ["VND-PRO-011", "VND-RSK-003"],
            "outputs": ["Vendor selection", "Onboarding", "Kickoff meetings", "Implementation plans"],
        },
        # -----------------------------------------------------------------
        # COST OPTIMIZATION
        # -----------------------------------------------------------------
        {
            "id": "VND-PRO-020",
            "name": "IT spend optimization assessment",
            "description": "Identify IT spend optimization opportunities",
            "activity_type": "assessment",
            "phase": "assessment",
            "base_cost": (30000, 80000),
            "timeline_months": (1, 2),
            "requires_tsa": False,
            "prerequisites": ["VND-CON-003"],
            "outputs": ["Optimization opportunities", "Quick wins", "Savings roadmap"],
        },
        {
            "id": "VND-PRO-021",
            "name": "Vendor consolidation analysis",
            "description": "Analyze vendor consolidation opportunities",
            "activity_type": "assessment",
            "phase": "assessment",
            "base_cost": (20000, 50000),
            "timeline_months": (0.5, 1.5),
            "requires_tsa": False,
            "prerequisites": ["VND-CON-001"],
            "outputs": ["Consolidation opportunities", "Vendor rationalization", "Savings estimate"],
        },
        {
            "id": "VND-PRO-022",
            "name": "Cost optimization execution",
            "description": "Execute cost optimization initiatives",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (25000, 75000),
            "timeline_months": (2, 4),
            "requires_tsa": False,
            "prerequisites": ["VND-PRO-020"],
            "outputs": ["Executed optimizations", "Realized savings", "Performance tracking"],
        },
        # -----------------------------------------------------------------
        # CONTRACT MANAGEMENT
        # -----------------------------------------------------------------
        {
            "id": "VND-PRO-030",
            "name": "Contract lifecycle management setup",
            "description": "Establish CLM processes and tools",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (30000, 80000),
            "timeline_months": (1, 3),
            "requires_tsa": False,
            "prerequisites": [],
            "outputs": ["CLM process", "Templates", "Approval workflows", "Repository"],
        },
        {
            "id": "VND-PRO-031",
            "name": "CLM platform implementation",
            "description": "Implement contract lifecycle management platform",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (50000, 150000),
            "timeline_months": (2, 4),
            "requires_tsa": False,
            "prerequisites": ["VND-PRO-030"],
            "outputs": ["CLM platform", "Contract repository", "Alerts", "Reporting"],
            "notes": "Icertis, Agiloft, DocuSign CLM, etc.",
        },
        {
            "id": "VND-PRO-032",
            "name": "Contract migration to CLM",
            "description": "Migrate existing contracts to CLM system",
            "activity_type": "implementation",
            "phase": "migration",
            "base_cost": (20000, 50000),
            "per_contract_cost": (100, 400),
            "timeline_months": (1, 3),
            "requires_tsa": False,
            "prerequisites": ["VND-PRO-031"],
            "outputs": ["Migrated contracts", "Metadata extraction", "Obligation tracking"],
        },
    ],
}

# =============================================================================
# COMBINED TEMPLATES FOR PHASE 9
# =============================================================================

def get_phase9_templates() -> Dict[str, Dict[str, List[Dict]]]:
    """Get all Phase 9 templates organized by category and workstream."""
    return {
        "vendor_contract": {
            "contract_analysis": CONTRACT_ANALYSIS_TEMPLATES["vendor_contract"],
            "vendor_transition": VENDOR_TRANSITION_TEMPLATES["vendor_contract"],
            "contract_negotiation": CONTRACT_NEGOTIATION_TEMPLATES["vendor_contract"],
            "third_party_risk": THIRD_PARTY_RISK_TEMPLATES["vendor_contract"],
            "procurement": PROCUREMENT_TEMPLATES["vendor_contract"],
        },
    }


def get_phase9_activity_by_id(activity_id: str) -> Dict:
    """Look up a Phase 9 activity by its ID."""
    all_templates = get_phase9_templates()

    for category, workstreams in all_templates.items():
        for workstream, activities in workstreams.items():
            for activity in activities:
                if activity.get("id") == activity_id:
                    return activity

    return None


def calculate_phase9_activity_cost(
    activity: Dict,
    contract_count: int = 100,
    vendor_count: int = 75,
    category_count: int = 10,
    rfp_count: int = 5,
    complexity: str = "moderate",
    industry: str = "standard",
) -> tuple:
    """
    Calculate cost range for a Phase 9 activity based on quantities and modifiers.

    Returns: (low, high, formula)
    """
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
    if "per_contract_cost" in activity:
        per_low, per_high = activity["per_contract_cost"]
        low += per_low * contract_count
        high += per_high * contract_count
        formula_parts.append(f"{contract_count} contracts × ${per_low:,}-${per_high:,}")

    if "per_vendor_cost" in activity:
        per_low, per_high = activity["per_vendor_cost"]
        low += per_low * vendor_count
        high += per_high * vendor_count
        formula_parts.append(f"{vendor_count} vendors × ${per_low:,}-${per_high:,}")

    if "per_category_cost" in activity:
        per_low, per_high = activity["per_category_cost"]
        low += per_low * category_count
        high += per_high * category_count
        formula_parts.append(f"{category_count} categories × ${per_low:,}-${per_high:,}")

    if "per_rfp_cost" in activity:
        per_low, per_high = activity["per_rfp_cost"]
        low += per_low * rfp_count
        high += per_high * rfp_count
        formula_parts.append(f"{rfp_count} RFPs × ${per_low:,}-${per_high:,}")

    formula = " + ".join(formula_parts) if formula_parts else "Unknown cost model"

    # Apply modifiers
    if combined_mult != 1.0:
        low = int(low * combined_mult)
        high = int(high * combined_mult)
        formula += f" × {combined_mult:.2f} ({complexity}/{industry})"

    return (int(low), int(high), formula)


def estimate_contract_transition_costs(
    contract_count: int = 100,
    critical_vendors: int = 20,
    new_contracts_needed: int = 30,
    terminations_needed: int = 15,
) -> Dict[str, tuple]:
    """
    Estimate total contract transition costs.

    Returns dict of category: (low, high)
    """
    estimates = {
        "contract_analysis": (
            45000 + (contract_count * 700),
            135000 + (contract_count * 2100),
        ),
        "vendor_transition": (
            85000 + (critical_vendors * 3500),
            240000 + (critical_vendors * 10500),
        ),
        "new_negotiations": (
            50000 + (new_contracts_needed * 4000),
            150000 + (new_contracts_needed * 14000),
        ),
        "terminations": (
            35000 + (terminations_needed * 2500),
            90000 + (terminations_needed * 9500),
        ),
    }

    return estimates


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    'CONTRACT_ANALYSIS_TEMPLATES',
    'VENDOR_TRANSITION_TEMPLATES',
    'CONTRACT_NEGOTIATION_TEMPLATES',
    'THIRD_PARTY_RISK_TEMPLATES',
    'PROCUREMENT_TEMPLATES',
    'get_phase9_templates',
    'get_phase9_activity_by_id',
    'calculate_phase9_activity_cost',
    'estimate_contract_transition_costs',
]
