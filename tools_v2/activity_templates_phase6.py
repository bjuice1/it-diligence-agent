"""
Activity Templates V2 - Phase 6: Acquisition & Integration

Phase 6: Buyer-Side Integration Activities
- Integration Planning & Assessment
- Technology Integration (identity, email, infrastructure, applications)
- Synergy Realization (cost synergies, consolidation)
- Day 1 Readiness

This phase covers the BUYER/ACQUIRER perspective - integrating a target
company into existing operations. Different from carveout (separation).

Deal Types Covered:
- Bolt-on acquisition (integrate into buyer platform)
- Platform acquisition (target becomes new platform)
- Merger of equals (best-of-breed integration)

Each activity template includes standard fields plus:
- integration_approach: absorb, best-of-breed, parallel-run
- synergy_type: cost, revenue, capability
- day1_critical: Whether required for Day 1 operations
"""

from typing import Dict, List, Any

# Import shared modifiers from Phase 1
from tools_v2.activity_templates_v2 import COMPLEXITY_MULTIPLIERS, INDUSTRY_MODIFIERS

# =============================================================================
# PHASE 6: INTEGRATION PLANNING
# =============================================================================

INTEGRATION_PLANNING_TEMPLATES = {
    "integration_planning": [
        # -----------------------------------------------------------------
        # ASSESSMENT & STRATEGY
        # -----------------------------------------------------------------
        {
            "id": "INT-001",
            "name": "IT integration assessment",
            "description": "Comprehensive assessment of target IT environment for integration planning",
            "activity_type": "implementation",
            "phase": "assessment",
            "base_cost": (50000, 125000),
            "timeline_months": (1, 2),
            "requires_tsa": False,
            "prerequisites": [],
            "outputs": ["IT inventory", "Architecture comparison", "Integration complexity", "Risk assessment"],
            "notes": "Foundation for integration planning - typically during DD or immediately post-sign",
        },
        {
            "id": "INT-002",
            "name": "Technology stack comparison",
            "description": "Compare buyer and target technology stacks for integration approach",
            "activity_type": "implementation",
            "phase": "assessment",
            "base_cost": (30000, 75000),
            "timeline_months": (0.5, 1.5),
            "requires_tsa": False,
            "prerequisites": ["INT-001"],
            "outputs": ["Stack comparison matrix", "Overlap analysis", "Gap identification", "Standardization opportunities"],
        },
        {
            "id": "INT-003",
            "name": "Integration complexity scoring",
            "description": "Score integration complexity across workstreams",
            "activity_type": "implementation",
            "phase": "assessment",
            "base_cost": (20000, 50000),
            "timeline_months": (0.25, 0.75),
            "requires_tsa": False,
            "prerequisites": ["INT-001", "INT-002"],
            "outputs": ["Complexity scores", "Risk ratings", "Effort estimates", "Timeline impacts"],
        },
        {
            "id": "INT-004",
            "name": "Synergy identification and validation",
            "description": "Identify and validate IT synergy opportunities",
            "activity_type": "implementation",
            "phase": "assessment",
            "base_cost": (35000, 85000),
            "timeline_months": (0.5, 1.5),
            "requires_tsa": False,
            "prerequisites": ["INT-001", "INT-002"],
            "outputs": ["Synergy inventory", "Cost/benefit analysis", "Timeline to realize", "Dependencies"],
            "notes": "Critical for deal model validation",
        },
        {
            "id": "INT-005",
            "name": "Integration strategy design",
            "description": "Design overall IT integration strategy and approach",
            "activity_type": "implementation",
            "phase": "design",
            "base_cost": (50000, 125000),
            "timeline_months": (1, 2),
            "requires_tsa": False,
            "prerequisites": ["INT-001", "INT-002", "INT-003", "INT-004"],
            "outputs": ["Integration strategy", "Approach by workstream", "Phasing plan", "Resource requirements"],
        },
        {
            "id": "INT-006",
            "name": "Integration roadmap development",
            "description": "Develop detailed integration roadmap with milestones",
            "activity_type": "implementation",
            "phase": "design",
            "base_cost": (30000, 75000),
            "timeline_months": (0.5, 1),
            "requires_tsa": False,
            "prerequisites": ["INT-005"],
            "outputs": ["Integration roadmap", "Milestone plan", "Dependency map", "Critical path"],
        },
        {
            "id": "INT-007",
            "name": "Integration governance setup",
            "description": "Establish integration governance and PMO",
            "activity_type": "implementation",
            "phase": "design",
            "base_cost": (25000, 60000),
            "timeline_months": (0.5, 1),
            "requires_tsa": False,
            "prerequisites": ["INT-005"],
            "outputs": ["Governance structure", "Decision rights", "Reporting cadence", "Escalation procedures"],
        },
    ],
}

# =============================================================================
# PHASE 6: TECHNOLOGY INTEGRATION
# =============================================================================

TECHNOLOGY_INTEGRATION_TEMPLATES = {
    "integration_planning": [
        # -----------------------------------------------------------------
        # IDENTITY INTEGRATION
        # -----------------------------------------------------------------
        {
            "id": "INT-010",
            "name": "Identity integration assessment",
            "description": "Assess identity integration approach (federation, migration, hybrid)",
            "activity_type": "implementation",
            "phase": "assessment",
            "base_cost": (25000, 60000),
            "timeline_months": (0.5, 1),
            "requires_tsa": False,
            "prerequisites": ["INT-001"],
            "outputs": ["Identity comparison", "Integration approach", "Coexistence requirements"],
        },
        {
            "id": "INT-011",
            "name": "Directory trust/federation setup",
            "description": "Establish trust or federation between buyer and target directories",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (30000, 75000),
            "timeline_months": (0.5, 1.5),
            "requires_tsa": False,
            "prerequisites": ["INT-010"],
            "outputs": ["Directory trust", "Federation configuration", "Cross-tenant access"],
            "day1_critical": True,
        },
        {
            "id": "INT-012",
            "name": "User migration to buyer identity",
            "description": "Migrate target users to buyer identity platform",
            "activity_type": "implementation",
            "phase": "migration",
            "per_user_cost": (20, 50),
            "base_cost": (25000, 60000),
            "timeline_months": (2, 6),
            "requires_tsa": False,
            "prerequisites": ["INT-011"],
            "outputs": ["Migrated users", "Profile consolidation", "Access provisioning"],
        },
        {
            "id": "INT-013",
            "name": "SSO integration for target applications",
            "description": "Integrate target applications with buyer SSO",
            "activity_type": "implementation",
            "phase": "build",
            "per_app_cost": (2000, 6000),
            "base_cost": (20000, 50000),
            "timeline_months": (1, 3),
            "requires_tsa": False,
            "prerequisites": ["INT-011"],
            "outputs": ["SSO integration", "App reconfiguration", "User access"],
        },
        {
            "id": "INT-014",
            "name": "Legacy identity decommission",
            "description": "Decommission target legacy identity systems",
            "activity_type": "implementation",
            "phase": "decommission",
            "base_cost": (20000, 50000),
            "timeline_months": (1, 2),
            "requires_tsa": False,
            "prerequisites": ["INT-012"],
            "outputs": ["Decommissioned systems", "Access removal", "Documentation"],
        },
        # -----------------------------------------------------------------
        # EMAIL INTEGRATION
        # -----------------------------------------------------------------
        {
            "id": "INT-020",
            "name": "Email integration assessment",
            "description": "Assess email integration approach (migration, coexistence)",
            "activity_type": "implementation",
            "phase": "assessment",
            "base_cost": (20000, 50000),
            "timeline_months": (0.5, 1),
            "requires_tsa": False,
            "prerequisites": ["INT-001"],
            "outputs": ["Email comparison", "Integration approach", "Domain strategy"],
        },
        {
            "id": "INT-021",
            "name": "Cross-tenant mail flow configuration",
            "description": "Configure mail flow between buyer and target tenants",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (15000, 40000),
            "timeline_months": (0.5, 1),
            "requires_tsa": False,
            "prerequisites": ["INT-020"],
            "outputs": ["Mail routing", "Free/busy sharing", "GAL sync"],
            "day1_critical": True,
        },
        {
            "id": "INT-022",
            "name": "Mailbox migration to buyer tenant",
            "description": "Migrate target mailboxes to buyer M365 tenant",
            "activity_type": "implementation",
            "phase": "migration",
            "per_user_cost": (25, 60),
            "base_cost": (25000, 60000),
            "timeline_months": (2, 6),
            "requires_tsa": False,
            "prerequisites": ["INT-021"],
            "outputs": ["Migrated mailboxes", "Archive migration", "Unified address book"],
        },
        {
            "id": "INT-023",
            "name": "Email domain consolidation",
            "description": "Consolidate email domains (optional rebranding)",
            "activity_type": "implementation",
            "phase": "migration",
            "per_domain_cost": (3000, 8000),
            "base_cost": (15000, 40000),
            "timeline_months": (1, 3),
            "requires_tsa": False,
            "prerequisites": ["INT-022"],
            "outputs": ["Domain consolidation", "Address rewriting", "External communication"],
        },
        # -----------------------------------------------------------------
        # INFRASTRUCTURE INTEGRATION
        # -----------------------------------------------------------------
        {
            "id": "INT-030",
            "name": "Network interconnection",
            "description": "Establish network connectivity between buyer and target",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (40000, 100000),
            "per_site_cost": (3000, 10000),
            "timeline_months": (1, 3),
            "requires_tsa": False,
            "prerequisites": ["INT-001"],
            "outputs": ["Network connectivity", "Routing configuration", "Firewall rules"],
            "day1_critical": True,
        },
        {
            "id": "INT-031",
            "name": "Workload migration to buyer platform",
            "description": "Migrate target workloads to buyer infrastructure",
            "activity_type": "implementation",
            "phase": "migration",
            "per_vm_cost": (800, 2500),
            "base_cost": (50000, 125000),
            "timeline_months": (3, 9),
            "requires_tsa": False,
            "prerequisites": ["INT-030"],
            "outputs": ["Migrated workloads", "Platform standardization", "Performance validation"],
        },
        {
            "id": "INT-032",
            "name": "Infrastructure tool consolidation",
            "description": "Consolidate monitoring, backup, and management tools",
            "activity_type": "implementation",
            "phase": "migration",
            "base_cost": (30000, 80000),
            "timeline_months": (1, 3),
            "requires_tsa": False,
            "prerequisites": ["INT-030"],
            "outputs": ["Tool consolidation", "Unified monitoring", "Standardized backup"],
            "synergy_type": "cost",
        },
        {
            "id": "INT-033",
            "name": "Target datacenter exit",
            "description": "Exit target datacenter after workload migration",
            "activity_type": "implementation",
            "phase": "decommission",
            "base_cost": (25000, 75000),
            "timeline_months": (1, 3),
            "requires_tsa": False,
            "prerequisites": ["INT-031"],
            "outputs": ["Datacenter exit", "Contract termination", "Asset disposition"],
            "synergy_type": "cost",
        },
        # -----------------------------------------------------------------
        # APPLICATION INTEGRATION
        # -----------------------------------------------------------------
        {
            "id": "INT-040",
            "name": "Application portfolio rationalization",
            "description": "Rationalize combined application portfolio",
            "activity_type": "implementation",
            "phase": "assessment",
            "per_app_cost": (500, 1500),
            "base_cost": (30000, 75000),
            "timeline_months": (1, 2),
            "requires_tsa": False,
            "prerequisites": ["INT-001"],
            "outputs": ["Rationalization analysis", "Keep/retire decisions", "Consolidation plan"],
            "synergy_type": "cost",
        },
        {
            "id": "INT-041",
            "name": "ERP integration/consolidation",
            "description": "Integrate or consolidate ERP systems",
            "activity_type": "implementation",
            "phase": "migration",
            "base_cost": (200000, 750000),
            "timeline_months": (6, 18),
            "requires_tsa": False,
            "prerequisites": ["INT-040"],
            "outputs": ["ERP integration", "Data consolidation", "Process harmonization"],
            "notes": "Major undertaking - often multi-year initiative",
        },
        {
            "id": "INT-042",
            "name": "CRM integration/consolidation",
            "description": "Integrate or consolidate CRM systems",
            "activity_type": "implementation",
            "phase": "migration",
            "base_cost": (75000, 250000),
            "timeline_months": (3, 9),
            "requires_tsa": False,
            "prerequisites": ["INT-040"],
            "outputs": ["CRM integration", "Customer data merge", "Sales process alignment"],
        },
        {
            "id": "INT-043",
            "name": "Application retirement execution",
            "description": "Retire redundant applications post-rationalization",
            "activity_type": "implementation",
            "phase": "decommission",
            "per_app_cost": (5000, 15000),
            "base_cost": (20000, 50000),
            "timeline_months": (2, 6),
            "requires_tsa": False,
            "prerequisites": ["INT-040"],
            "outputs": ["Retired applications", "Data archival", "License recovery"],
            "synergy_type": "cost",
        },
        {
            "id": "INT-044",
            "name": "SaaS account consolidation",
            "description": "Consolidate SaaS accounts and subscriptions",
            "activity_type": "implementation",
            "phase": "migration",
            "per_app_cost": (2000, 8000),
            "base_cost": (20000, 50000),
            "timeline_months": (2, 6),
            "requires_tsa": False,
            "prerequisites": ["INT-040"],
            "outputs": ["Consolidated accounts", "User migration", "Contract optimization"],
            "synergy_type": "cost",
        },
    ],
}

# =============================================================================
# PHASE 6: SYNERGY REALIZATION
# =============================================================================

SYNERGY_TEMPLATES = {
    "integration_planning": [
        # -----------------------------------------------------------------
        # COST SYNERGIES
        # -----------------------------------------------------------------
        {
            "id": "SYN-001",
            "name": "IT cost synergy tracking setup",
            "description": "Establish synergy tracking and reporting",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (20000, 50000),
            "timeline_months": (0.5, 1),
            "requires_tsa": False,
            "prerequisites": ["INT-004"],
            "outputs": ["Synergy tracking", "Baseline costs", "Reporting dashboard"],
        },
        {
            "id": "SYN-002",
            "name": "License consolidation execution",
            "description": "Execute license consolidation for cost savings",
            "activity_type": "implementation",
            "phase": "migration",
            "base_cost": (30000, 80000),
            "timeline_months": (2, 6),
            "requires_tsa": False,
            "prerequisites": ["INT-004"],
            "outputs": ["Consolidated licenses", "Volume discounts", "Cost savings"],
            "synergy_type": "cost",
            "notes": "Typical savings 15-30% through volume consolidation",
        },
        {
            "id": "SYN-003",
            "name": "Vendor consolidation execution",
            "description": "Consolidate vendors for improved pricing and efficiency",
            "activity_type": "implementation",
            "phase": "migration",
            "base_cost": (25000, 60000),
            "timeline_months": (2, 6),
            "requires_tsa": False,
            "prerequisites": ["INT-004"],
            "outputs": ["Vendor consolidation", "Contract renegotiation", "Reduced management overhead"],
            "synergy_type": "cost",
        },
        {
            "id": "SYN-004",
            "name": "Infrastructure consolidation",
            "description": "Consolidate infrastructure for cost reduction",
            "activity_type": "implementation",
            "phase": "migration",
            "base_cost": (50000, 150000),
            "timeline_months": (3, 9),
            "requires_tsa": False,
            "prerequisites": ["INT-031"],
            "outputs": ["Consolidated infrastructure", "Reduced footprint", "Optimized capacity"],
            "synergy_type": "cost",
        },
        {
            "id": "SYN-005",
            "name": "IT organization optimization",
            "description": "Optimize combined IT organization structure",
            "activity_type": "implementation",
            "phase": "design",
            "base_cost": (40000, 100000),
            "timeline_months": (1, 3),
            "requires_tsa": False,
            "prerequisites": ["INT-005"],
            "outputs": ["Org design", "Role mapping", "Transition plan"],
            "synergy_type": "cost",
            "notes": "Sensitive activity - requires HR partnership",
        },
        # -----------------------------------------------------------------
        # REVENUE/CAPABILITY SYNERGIES
        # -----------------------------------------------------------------
        {
            "id": "SYN-010",
            "name": "Cross-sell technology enablement",
            "description": "Enable technology for cross-sell opportunities",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (30000, 80000),
            "timeline_months": (1, 3),
            "requires_tsa": False,
            "prerequisites": ["INT-042"],
            "outputs": ["Integrated CRM", "Product catalog merge", "Sales enablement"],
            "synergy_type": "revenue",
        },
        {
            "id": "SYN-011",
            "name": "Data platform integration",
            "description": "Integrate data platforms for unified analytics",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (75000, 200000),
            "timeline_months": (3, 6),
            "requires_tsa": False,
            "prerequisites": ["INT-001"],
            "outputs": ["Unified data platform", "Combined analytics", "Enhanced insights"],
            "synergy_type": "capability",
        },
        {
            "id": "SYN-012",
            "name": "Technology capability transfer",
            "description": "Transfer unique technology capabilities between entities",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (40000, 120000),
            "timeline_months": (2, 6),
            "requires_tsa": False,
            "prerequisites": ["INT-001"],
            "outputs": ["Capability transfer", "Knowledge transfer", "Team integration"],
            "synergy_type": "capability",
        },
    ],
}

# =============================================================================
# PHASE 6: DAY 1 READINESS
# =============================================================================

DAY1_TEMPLATES = {
    "integration_planning": [
        # -----------------------------------------------------------------
        # DAY 1 PLANNING
        # -----------------------------------------------------------------
        {
            "id": "D1-001",
            "name": "Day 1 requirements gathering",
            "description": "Gather Day 1 IT requirements across business functions",
            "activity_type": "implementation",
            "phase": "assessment",
            "base_cost": (20000, 50000),
            "timeline_months": (0.5, 1),
            "requires_tsa": False,
            "prerequisites": [],
            "outputs": ["Day 1 requirements", "Critical systems", "Communication needs", "Access requirements"],
            "day1_critical": True,
        },
        {
            "id": "D1-002",
            "name": "Day 1 checklist development",
            "description": "Develop comprehensive Day 1 IT checklist",
            "activity_type": "implementation",
            "phase": "design",
            "base_cost": (15000, 35000),
            "timeline_months": (0.25, 0.75),
            "requires_tsa": False,
            "prerequisites": ["D1-001"],
            "outputs": ["Day 1 checklist", "Responsibility matrix", "Contingency plans"],
            "day1_critical": True,
        },
        {
            "id": "D1-003",
            "name": "Day 1 dress rehearsal",
            "description": "Execute Day 1 dress rehearsal/dry run",
            "activity_type": "implementation",
            "phase": "testing",
            "base_cost": (20000, 50000),
            "timeline_months": (0.25, 0.5),
            "requires_tsa": False,
            "prerequisites": ["D1-002"],
            "outputs": ["Rehearsal execution", "Issue identification", "Plan refinement"],
            "day1_critical": True,
        },
        # -----------------------------------------------------------------
        # DAY 1 CONNECTIVITY
        # -----------------------------------------------------------------
        {
            "id": "D1-010",
            "name": "Day 1 network connectivity",
            "description": "Establish minimum viable network connectivity for Day 1",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (30000, 80000),
            "timeline_months": (0.5, 1.5),
            "requires_tsa": False,
            "prerequisites": ["D1-001"],
            "outputs": ["Basic connectivity", "VPN access", "Critical system access"],
            "day1_critical": True,
        },
        {
            "id": "D1-011",
            "name": "Day 1 communication systems",
            "description": "Ensure communication systems ready for Day 1",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (15000, 40000),
            "timeline_months": (0.5, 1),
            "requires_tsa": False,
            "prerequisites": ["D1-001"],
            "outputs": ["Email readiness", "Phone/Teams", "Collaboration tools"],
            "day1_critical": True,
        },
        # -----------------------------------------------------------------
        # DAY 1 ACCESS
        # -----------------------------------------------------------------
        {
            "id": "D1-020",
            "name": "Day 1 access provisioning",
            "description": "Provision critical system access for Day 1",
            "activity_type": "implementation",
            "phase": "build",
            "per_user_cost": (10, 30),
            "base_cost": (15000, 40000),
            "timeline_months": (0.5, 1),
            "requires_tsa": False,
            "prerequisites": ["D1-001", "INT-011"],
            "outputs": ["Provisioned access", "Credentials", "Access verification"],
            "day1_critical": True,
        },
        {
            "id": "D1-021",
            "name": "Day 1 shared services access",
            "description": "Configure access to shared services (HR, finance, etc.)",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (20000, 50000),
            "timeline_months": (0.5, 1),
            "requires_tsa": False,
            "prerequisites": ["D1-001"],
            "outputs": ["Shared service access", "SSO configuration", "Role provisioning"],
            "day1_critical": True,
        },
        # -----------------------------------------------------------------
        # DAY 1 SUPPORT
        # -----------------------------------------------------------------
        {
            "id": "D1-030",
            "name": "Day 1 support model",
            "description": "Establish IT support model for Day 1 and transition",
            "activity_type": "implementation",
            "phase": "design",
            "base_cost": (15000, 40000),
            "timeline_months": (0.5, 1),
            "requires_tsa": False,
            "prerequisites": ["D1-001"],
            "outputs": ["Support model", "Escalation paths", "Contact information"],
            "day1_critical": True,
        },
        {
            "id": "D1-031",
            "name": "Day 1 war room setup",
            "description": "Establish Day 1 command center/war room",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (10000, 30000),
            "timeline_months": (0.25, 0.5),
            "requires_tsa": False,
            "prerequisites": ["D1-002"],
            "outputs": ["War room setup", "Communication channels", "Issue tracking"],
            "day1_critical": True,
        },
        {
            "id": "D1-032",
            "name": "Day 1 execution and support",
            "description": "Execute Day 1 plan with dedicated support",
            "activity_type": "implementation",
            "phase": "cutover",
            "base_cost": (25000, 75000),
            "timeline_months": (0.1, 0.25),
            "requires_tsa": False,
            "prerequisites": ["D1-003"],
            "outputs": ["Day 1 execution", "Issue resolution", "Status communication"],
            "day1_critical": True,
        },
        # -----------------------------------------------------------------
        # POST-DAY 1
        # -----------------------------------------------------------------
        {
            "id": "D1-040",
            "name": "Post-Day 1 stabilization",
            "description": "Stabilization support after Day 1",
            "activity_type": "implementation",
            "phase": "cutover",
            "base_cost": (30000, 80000),
            "timeline_months": (1, 2),
            "requires_tsa": False,
            "prerequisites": ["D1-032"],
            "outputs": ["Stabilization support", "Issue resolution", "Lessons learned"],
        },
        {
            "id": "D1-041",
            "name": "Integration transition to BAU",
            "description": "Transition from integration project to business as usual",
            "activity_type": "implementation",
            "phase": "cutover",
            "base_cost": (20000, 50000),
            "timeline_months": (1, 2),
            "requires_tsa": False,
            "prerequisites": ["D1-040"],
            "outputs": ["BAU transition", "Support handoff", "Documentation"],
        },
    ],
}

# =============================================================================
# PHASE 6: TSA MANAGEMENT (Buyer Side)
# =============================================================================

TSA_MANAGEMENT_TEMPLATES = {
    "integration_planning": [
        {
            "id": "TSA-001",
            "name": "TSA requirements definition",
            "description": "Define TSA requirements for services from seller",
            "activity_type": "implementation",
            "phase": "assessment",
            "base_cost": (25000, 60000),
            "timeline_months": (0.5, 1),
            "requires_tsa": False,
            "prerequisites": ["INT-001"],
            "outputs": ["TSA requirements", "Service definitions", "Duration needs", "Exit criteria"],
        },
        {
            "id": "TSA-002",
            "name": "TSA negotiation support",
            "description": "Support TSA negotiation with seller",
            "activity_type": "implementation",
            "phase": "design",
            "base_cost": (30000, 80000),
            "timeline_months": (0.5, 1.5),
            "requires_tsa": False,
            "prerequisites": ["TSA-001"],
            "outputs": ["TSA terms", "SLA definitions", "Pricing agreement", "Exit provisions"],
        },
        {
            "id": "TSA-003",
            "name": "TSA governance setup",
            "description": "Establish TSA governance and management",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (20000, 50000),
            "timeline_months": (0.5, 1),
            "requires_tsa": False,
            "prerequisites": ["TSA-002"],
            "outputs": ["TSA governance", "Service tracking", "Issue management", "Exit planning"],
        },
        {
            "id": "TSA-004",
            "name": "TSA exit planning",
            "description": "Plan exit from TSA services",
            "activity_type": "implementation",
            "phase": "design",
            "base_cost": (25000, 60000),
            "timeline_months": (0.5, 1),
            "requires_tsa": False,
            "prerequisites": ["TSA-003"],
            "outputs": ["Exit plan", "Capability readiness", "Cutover approach", "Risk mitigation"],
        },
        {
            "id": "TSA-005",
            "name": "TSA exit execution",
            "description": "Execute TSA exit for IT services",
            "activity_type": "implementation",
            "phase": "migration",
            "base_cost": (40000, 100000),
            "timeline_months": (1, 3),
            "requires_tsa": False,
            "prerequisites": ["TSA-004"],
            "outputs": ["TSA exit", "Service transition", "Validation"],
        },
    ],
}

# =============================================================================
# COMBINED TEMPLATES FOR PHASE 6
# =============================================================================

def get_phase6_templates() -> Dict[str, Dict[str, List[Dict]]]:
    """Get all Phase 6 templates organized by category and workstream."""
    return {
        "integration_planning": {
            "planning": INTEGRATION_PLANNING_TEMPLATES["integration_planning"],
            "technology": TECHNOLOGY_INTEGRATION_TEMPLATES["integration_planning"],
            "synergy": SYNERGY_TEMPLATES["integration_planning"],
            "day1": DAY1_TEMPLATES["integration_planning"],
            "tsa_management": TSA_MANAGEMENT_TEMPLATES["integration_planning"],
        },
    }


def get_phase6_activity_by_id(activity_id: str) -> Dict:
    """Look up a Phase 6 activity by its ID."""
    all_templates = get_phase6_templates()

    for category, workstreams in all_templates.items():
        for workstream, activities in workstreams.items():
            for activity in activities:
                if activity.get("id") == activity_id:
                    return activity

    return None


def calculate_phase6_activity_cost(
    activity: Dict,
    user_count: int = 1000,
    site_count: int = 5,
    vm_count: int = 100,
    app_count: int = 30,
    domain_count: int = 3,
    complexity: str = "moderate",
    industry: str = "standard",
) -> tuple:
    """
    Calculate cost range for a Phase 6 activity based on quantities and modifiers.

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
    if "per_user_cost" in activity:
        per_low, per_high = activity["per_user_cost"]
        low += per_low * user_count
        high += per_high * user_count
        formula_parts.append(f"{user_count:,} users × ${per_low}-${per_high}")

    if "per_site_cost" in activity:
        per_low, per_high = activity["per_site_cost"]
        low += per_low * site_count
        high += per_high * site_count
        formula_parts.append(f"{site_count} sites × ${per_low:,}-${per_high:,}")

    if "per_vm_cost" in activity:
        per_low, per_high = activity["per_vm_cost"]
        low += per_low * vm_count
        high += per_high * vm_count
        formula_parts.append(f"{vm_count} VMs × ${per_low:,}-${per_high:,}")

    if "per_app_cost" in activity:
        per_low, per_high = activity["per_app_cost"]
        low += per_low * app_count
        high += per_high * app_count
        formula_parts.append(f"{app_count} apps × ${per_low:,}-${per_high:,}")

    if "per_domain_cost" in activity:
        per_low, per_high = activity["per_domain_cost"]
        low += per_low * domain_count
        high += per_high * domain_count
        formula_parts.append(f"{domain_count} domains × ${per_low:,}-${per_high:,}")

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
    'INTEGRATION_PLANNING_TEMPLATES',
    'TECHNOLOGY_INTEGRATION_TEMPLATES',
    'SYNERGY_TEMPLATES',
    'DAY1_TEMPLATES',
    'TSA_MANAGEMENT_TEMPLATES',
    'get_phase6_templates',
    'get_phase6_activity_by_id',
    'calculate_phase6_activity_cost',
]
