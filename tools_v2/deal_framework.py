"""
Deal Framework - Comprehensive M&A IT Considerations

This module defines the complete framework for understanding:
1. What each deal type means for IT
2. What's required at each milestone (Day 1, Day 30, Day 100, Year 1)
3. Why certain activities are critical vs deferrable
4. How to reason through any M&A scenario

This is the "knowledge base" that powers intelligent recommendations.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum


# =============================================================================
# DEAL TYPE DEFINITIONS
# =============================================================================

class DealType(Enum):
    CARVEOUT = "carveout"
    ACQUISITION = "acquisition"
    DIVESTITURE = "divestiture"
    MERGER = "merger"
    PLATFORM_ADDON = "platform_addon"  # PE platform acquiring add-on


DEAL_TYPE_DEFINITIONS = {
    DealType.CARVEOUT: {
        "name": "Carveout / Spin-off",
        "description": "Target is being separated from a parent company to operate independently or be sold",
        "key_characteristic": "Must BUILD standalone capabilities that parent currently provides",
        "typical_buyer": "PE firm, strategic buyer, or IPO",
        "seller_role": "Parent company divesting a business unit",
        "primary_challenge": "Disentangling shared services and systems",
        "tsa_typical": True,
        "tsa_purpose": "Bridge until standalone capabilities are established",
        "cost_driver": "Building what doesn't exist today",
        "timeline_driver": "Complexity of parent dependencies",
        "key_questions": [
            "What services does parent currently provide?",
            "What shared systems need to be separated?",
            "What standalone capabilities need to be built?",
            "How long until target can operate independently?",
        ],
    },
    DealType.ACQUISITION: {
        "name": "Acquisition",
        "description": "Buyer is acquiring target and will integrate into buyer's environment",
        "key_characteristic": "Target moves INTO buyer's existing systems and processes",
        "typical_buyer": "Strategic corporate, PE portfolio company",
        "seller_role": "Standalone company being acquired",
        "primary_challenge": "Integrating target into buyer's environment",
        "tsa_typical": False,  # Less common - buyer provides destination
        "tsa_purpose": "Bridge if buyer needs time to absorb",
        "cost_driver": "Integration and migration to buyer systems",
        "timeline_driver": "Buyer readiness to absorb target",
        "key_questions": [
            "What systems does buyer have that target will move to?",
            "What's the gap between target and buyer technology?",
            "How quickly can buyer absorb target users/systems?",
            "What synergies are expected from consolidation?",
        ],
    },
    DealType.DIVESTITURE: {
        "name": "Divestiture",
        "description": "Seller is divesting a business unit (seller's perspective on carveout)",
        "key_characteristic": "Seller must prepare target for separation",
        "typical_buyer": "PE firm, strategic buyer",
        "seller_role": "Parent company preparing unit for sale",
        "primary_challenge": "Preparing clean separation while maintaining operations",
        "tsa_typical": True,
        "tsa_purpose": "Seller provides services during buyer's transition",
        "cost_driver": "Separation preparation and TSA delivery",
        "timeline_driver": "Deal timeline and buyer readiness",
        "key_questions": [
            "What services will seller provide via TSA?",
            "How will seller deliver TSA services?",
            "What's the cost to seller of providing TSA?",
            "What stranded costs remain with seller?",
        ],
    },
    DealType.MERGER: {
        "name": "Merger",
        "description": "Two companies combining where neither is clearly dominant",
        "key_characteristic": "Must choose target state from EITHER or build NEW",
        "typical_buyer": "N/A - combination of equals",
        "seller_role": "N/A - both parties are combining",
        "primary_challenge": "Deciding whose systems to keep, managing politics",
        "tsa_typical": False,
        "tsa_purpose": "N/A - internal transition",
        "cost_driver": "Integration complexity and change management",
        "timeline_driver": "Decision-making and organizational alignment",
        "key_questions": [
            "Whose systems will be the go-forward platform?",
            "How will decisions be made between the two orgs?",
            "What's the integration timeline expectation?",
            "How will duplicate roles be handled?",
        ],
    },
    DealType.PLATFORM_ADDON: {
        "name": "Platform Add-on",
        "description": "PE portfolio company acquiring a smaller add-on company",
        "key_characteristic": "Platform has established systems; add-on integrates in",
        "typical_buyer": "PE-backed platform company",
        "seller_role": "Smaller company being acquired",
        "primary_challenge": "Rapid integration while maintaining add-on operations",
        "tsa_typical": False,
        "tsa_purpose": "Rare - platform usually absorbs quickly",
        "cost_driver": "Speed of integration vs. complexity of add-on",
        "timeline_driver": "Platform capacity and add-on complexity",
        "key_questions": [
            "How mature is the platform's integration playbook?",
            "What's the size differential (platform vs add-on)?",
            "Are there immediate synergies to capture?",
            "Can platform absorb add-on without disruption?",
        ],
    },
}


# =============================================================================
# MILESTONE DEFINITIONS
# =============================================================================

class Milestone(Enum):
    PRE_CLOSE = "pre_close"
    DAY_1 = "day_1"
    DAY_30 = "day_30"
    DAY_100 = "day_100"
    YEAR_1 = "year_1"
    STEADY_STATE = "steady_state"


MILESTONE_DEFINITIONS = {
    Milestone.PRE_CLOSE: {
        "name": "Pre-Close",
        "description": "Activities that must complete before deal closes",
        "typical_duration": "Deal signing to close (30-90 days typically)",
        "focus": "Planning, preparation, regulatory requirements",
        "constraints": [
            "Limited access to counterparty systems",
            "Gun-jumping restrictions",
            "Regulatory approval requirements",
        ],
        "typical_activities": [
            "Due diligence completion",
            "Integration/separation planning",
            "TSA negotiation",
            "Day-1 readiness preparation",
            "Regulatory filings and approvals",
        ],
    },
    Milestone.DAY_1: {
        "name": "Day 1 (Close)",
        "description": "The moment the deal closes - business must continue operating",
        "typical_duration": "The day of close",
        "focus": "Business continuity - nothing breaks",
        "constraints": [
            "Zero downtime tolerance",
            "All users must be able to work",
            "All critical systems must function",
            "Legal entity changes take effect",
        ],
        "typical_activities": [
            "Legal entity cutover",
            "Email domain changes (if immediate)",
            "Access provisioning to new systems",
            "TSA activation (for carveouts)",
            "Day-1 communications to employees",
        ],
        "critical_success_factors": [
            "Users can log in",
            "Email works",
            "Critical applications accessible",
            "Network connectivity maintained",
            "Security monitoring active",
        ],
    },
    Milestone.DAY_30: {
        "name": "Day 30",
        "description": "First month - stabilization and quick wins",
        "typical_duration": "Close + 30 days",
        "focus": "Stabilize operations, capture quick wins, build momentum",
        "constraints": [
            "Still learning target environment",
            "Change fatigue risk",
            "TSA costs accruing (if applicable)",
        ],
        "typical_activities": [
            "Quick win synergies (tool consolidation)",
            "Communication platform alignment",
            "Initial user training",
            "Identify blockers and risks",
            "Refine integration/separation plan",
        ],
    },
    Milestone.DAY_100: {
        "name": "Day 100",
        "description": "First major milestone - significant progress expected",
        "typical_duration": "Close + 100 days (~3 months)",
        "focus": "Demonstrate meaningful progress, exit critical TSAs",
        "constraints": [
            "Board/investor expectations",
            "TSA cost pressure",
            "Employee retention concerns",
        ],
        "typical_activities": [
            "Exit Day-1 critical TSAs",
            "Complete identity separation/integration",
            "Complete email migration",
            "Establish security baseline",
            "Network separation/integration complete",
        ],
    },
    Milestone.YEAR_1: {
        "name": "Year 1",
        "description": "Full separation/integration substantially complete",
        "typical_duration": "Close + 12 months",
        "focus": "Complete major transitions, realize synergies",
        "constraints": [
            "TSA expiration deadlines",
            "Budget constraints",
            "Synergy realization targets",
        ],
        "typical_activities": [
            "Exit all TSAs",
            "Complete ERP separation/consolidation",
            "Application rationalization",
            "Full security program in place",
            "Optimized run-rate achieved",
        ],
    },
    Milestone.STEADY_STATE: {
        "name": "Steady State",
        "description": "Ongoing operations - fully separated or integrated",
        "typical_duration": "Year 2+",
        "focus": "Optimize, continuous improvement",
        "constraints": [
            "BAU budget constraints",
            "Ongoing optimization pressure",
        ],
        "typical_activities": [
            "Continuous improvement",
            "Technical debt remediation",
            "Further consolidation/optimization",
            "Strategic initiatives",
        ],
    },
}


# =============================================================================
# WORKSTREAM REQUIREMENTS BY DEAL TYPE AND MILESTONE
# =============================================================================

@dataclass
class WorkstreamRequirement:
    """What's required for a workstream at a specific milestone."""
    criticality: str  # "critical", "important", "optional", "not_applicable"
    description: str
    activities: List[str]
    success_criteria: List[str]
    risks_if_missed: List[str]
    typical_cost_range: Optional[Tuple[str, str]] = None  # ("$X", "$Y")
    typical_duration: Optional[str] = None


WORKSTREAM_REQUIREMENTS = {
    # =========================================================================
    # IDENTITY & ACCESS MANAGEMENT
    # =========================================================================
    "identity": {
        "name": "Identity & Access Management",
        "why_it_matters": """
Identity is the foundation of all IT access. Without identity services:
- Users cannot log in to any system
- Applications cannot authenticate users
- Security controls cannot be enforced
- Business operations STOP

This makes identity Day-1 CRITICAL for any deal involving separation from parent.
""",
        DealType.CARVEOUT: {
            Milestone.PRE_CLOSE: WorkstreamRequirement(
                criticality="critical",
                description="Plan identity separation architecture",
                activities=[
                    "Document current identity dependencies on parent",
                    "Design standalone identity architecture",
                    "Plan user migration approach",
                    "Inventory all SSO-integrated applications",
                    "Negotiate identity TSA terms",
                ],
                success_criteria=[
                    "Identity architecture design approved",
                    "Migration plan documented",
                    "TSA terms agreed for identity services",
                ],
                risks_if_missed=[
                    "Day-1 identity crisis - users cannot log in",
                    "Unplanned TSA extensions",
                    "Security gaps during transition",
                ],
            ),
            Milestone.DAY_1: WorkstreamRequirement(
                criticality="critical",
                description="Ensure users can authenticate - TSA or temporary solution",
                activities=[
                    "Activate identity TSA with parent",
                    "Verify all users can log in",
                    "Ensure critical applications accessible",
                    "Establish emergency access procedures",
                ],
                success_criteria=[
                    "100% of users can authenticate",
                    "All critical applications accessible",
                    "Security monitoring active",
                ],
                risks_if_missed=[
                    "BUSINESS STOPS - users cannot work",
                    "Security incidents without monitoring",
                    "Regulatory compliance failures",
                ],
            ),
            Milestone.DAY_100: WorkstreamRequirement(
                criticality="critical",
                description="Complete identity separation - exit TSA",
                activities=[
                    "Provision standalone identity platform",
                    "Migrate all user accounts",
                    "Reconfigure all application SSO",
                    "Re-enroll MFA for all users",
                    "Execute identity cutover",
                    "Decommission TSA dependency",
                ],
                success_criteria=[
                    "Standalone identity platform operational",
                    "All users migrated",
                    "All applications using new SSO",
                    "Identity TSA exited",
                ],
                risks_if_missed=[
                    "Extended TSA costs ($50-150K/month)",
                    "Security vulnerabilities during extended transition",
                    "Dependency on parent continues",
                ],
                typical_cost_range=("$200K", "$800K"),
                typical_duration="3-6 months",
            ),
        },
        DealType.ACQUISITION: {
            Milestone.PRE_CLOSE: WorkstreamRequirement(
                criticality="important",
                description="Plan integration into buyer's identity platform",
                activities=[
                    "Assess target's current identity setup",
                    "Plan integration into buyer's directory",
                    "Identify application SSO requirements",
                ],
                success_criteria=[
                    "Integration approach agreed",
                    "Timeline established",
                ],
                risks_if_missed=[
                    "Delayed integration",
                    "User experience issues",
                ],
            ),
            Milestone.DAY_1: WorkstreamRequirement(
                criticality="important",
                description="Establish basic connectivity - users can access critical systems",
                activities=[
                    "Provision target users in buyer directory (basic)",
                    "Establish trust/federation between directories",
                    "Enable access to critical buyer systems",
                ],
                success_criteria=[
                    "Target users can access required buyer systems",
                    "Target systems still accessible",
                ],
                risks_if_missed=[
                    "Collaboration barriers",
                    "Productivity loss",
                ],
            ),
            Milestone.DAY_100: WorkstreamRequirement(
                criticality="important",
                description="Complete identity integration",
                activities=[
                    "Full migration to buyer's identity platform",
                    "Reconfigure target applications for buyer SSO",
                    "Decommission target's standalone identity (if any)",
                ],
                success_criteria=[
                    "All users on single identity platform",
                    "All applications using unified SSO",
                ],
                risks_if_missed=[
                    "Ongoing dual-platform costs",
                    "Security complexity",
                    "User experience fragmentation",
                ],
                typical_cost_range=("$100K", "$400K"),
                typical_duration="2-4 months",
            ),
        },
    },

    # =========================================================================
    # EMAIL & COLLABORATION
    # =========================================================================
    "email": {
        "name": "Email & Collaboration",
        "why_it_matters": """
Email is how business communicates - internally and externally.
- Customer communications must continue
- Internal collaboration must work
- Legal/compliance requirements for email retention
- Brand identity tied to email domain

Email is Day-1 CRITICAL because communication cannot stop.
""",
        DealType.CARVEOUT: {
            Milestone.PRE_CLOSE: WorkstreamRequirement(
                criticality="critical",
                description="Plan email separation and domain strategy",
                activities=[
                    "Inventory email domains and routing",
                    "Plan email platform (new tenant vs. migration)",
                    "Determine domain strategy (keep vs. new)",
                    "Negotiate email TSA terms",
                    "Plan mailbox migration approach",
                ],
                success_criteria=[
                    "Email separation plan approved",
                    "Domain strategy decided",
                    "TSA terms agreed",
                ],
                risks_if_missed=[
                    "Email disruption at close",
                    "Lost communications",
                    "Customer confusion",
                ],
            ),
            Milestone.DAY_1: WorkstreamRequirement(
                criticality="critical",
                description="Email works - TSA or forwarding in place",
                activities=[
                    "Activate email TSA",
                    "Verify email send/receive working",
                    "Confirm external email delivery",
                    "Test critical email workflows",
                ],
                success_criteria=[
                    "All users can send/receive email",
                    "External email delivery working",
                    "No email bounces or delays",
                ],
                risks_if_missed=[
                    "BUSINESS STOPS - cannot communicate",
                    "Lost customer communications",
                    "Reputational damage",
                ],
            ),
            Milestone.DAY_100: WorkstreamRequirement(
                criticality="critical",
                description="Complete email migration to standalone platform",
                activities=[
                    "Provision standalone email tenant",
                    "Migrate all mailboxes",
                    "Migrate shared resources (calendars, rooms)",
                    "Transfer email domains",
                    "Migrate file storage (Drive/OneDrive)",
                    "User training on new platform",
                ],
                success_criteria=[
                    "All mailboxes on standalone platform",
                    "Domains transferred",
                    "Email TSA exited",
                ],
                risks_if_missed=[
                    "Extended TSA costs",
                    "Data migration complexity increases",
                    "User productivity impact",
                ],
                typical_cost_range=("$50K", "$200K"),
                typical_duration="2-4 months",
            ),
        },
        DealType.ACQUISITION: {
            Milestone.DAY_1: WorkstreamRequirement(
                criticality="important",
                description="Establish email interoperability",
                activities=[
                    "Enable email flow between buyer and target",
                    "Set up shared calendar visibility",
                    "Establish basic collaboration",
                ],
                success_criteria=[
                    "Buyer and target can email each other seamlessly",
                    "Calendar sharing works",
                ],
                risks_if_missed=[
                    "Collaboration barriers",
                    "Productivity loss",
                ],
            ),
            Milestone.DAY_30: WorkstreamRequirement(
                criticality="important",
                description="Quick win - consolidate to single platform",
                activities=[
                    "Migrate target to buyer's email platform",
                    "Migrate files to buyer's storage",
                    "Training on buyer's tools",
                ],
                success_criteria=[
                    "Single email platform",
                    "Single collaboration suite",
                ],
                risks_if_missed=[
                    "Dual platform costs",
                    "Collaboration friction",
                ],
                typical_cost_range=("$20K", "$80K"),
                typical_duration="2-4 weeks",
            ),
        },
    },

    # =========================================================================
    # INFRASTRUCTURE
    # =========================================================================
    "infrastructure": {
        "name": "Infrastructure & Hosting",
        "why_it_matters": """
Infrastructure is where applications run.
- Servers, storage, databases
- Cloud platforms (AWS, Azure, GCP)
- Data centers and colocation

Infrastructure is Day-1 CRITICAL if applications are parent-hosted.
Can be Day-100 if applications are already standalone or SaaS.
""",
        DealType.CARVEOUT: {
            Milestone.PRE_CLOSE: WorkstreamRequirement(
                criticality="critical",
                description="Inventory and plan infrastructure separation",
                activities=[
                    "Complete infrastructure inventory",
                    "Identify parent-hosted vs. standalone systems",
                    "Design target state architecture",
                    "Plan migration waves",
                    "Negotiate infrastructure TSA",
                ],
                success_criteria=[
                    "Full inventory documented",
                    "Target architecture approved",
                    "Migration plan in place",
                    "TSA terms agreed",
                ],
                risks_if_missed=[
                    "Unknown dependencies surface post-close",
                    "Unplanned costs",
                    "Migration delays",
                ],
            ),
            Milestone.DAY_1: WorkstreamRequirement(
                criticality="critical",
                description="All systems operational - TSA active",
                activities=[
                    "Activate infrastructure TSA",
                    "Verify all systems accessible",
                    "Confirm connectivity",
                    "Establish monitoring",
                ],
                success_criteria=[
                    "All critical systems operational",
                    "Users can access applications",
                    "Monitoring in place",
                ],
                risks_if_missed=[
                    "Application outages",
                    "Business disruption",
                    "Data access issues",
                ],
            ),
            Milestone.YEAR_1: WorkstreamRequirement(
                criticality="critical",
                description="Complete infrastructure migration",
                activities=[
                    "Build standalone infrastructure (cloud/colo)",
                    "Migrate all workloads",
                    "Migrate all data",
                    "Establish DR/backup",
                    "Exit infrastructure TSA",
                ],
                success_criteria=[
                    "All workloads on standalone infrastructure",
                    "TSA exited",
                    "DR capability in place",
                ],
                risks_if_missed=[
                    "Significant ongoing TSA costs",
                    "Operational dependency on parent",
                    "Limited flexibility",
                ],
                typical_cost_range=("$500K", "$3M"),
                typical_duration="6-12 months",
            ),
        },
    },

    # =========================================================================
    # NETWORK
    # =========================================================================
    "network": {
        "name": "Network & Connectivity",
        "why_it_matters": """
Network connects everything.
- WAN links between offices
- Internet connectivity
- VPN for remote access
- Firewalls for security

Network is Day-1 CRITICAL - without connectivity, nothing works.
""",
        DealType.CARVEOUT: {
            Milestone.DAY_1: WorkstreamRequirement(
                criticality="critical",
                description="Network connectivity maintained",
                activities=[
                    "Activate network TSA",
                    "Verify site connectivity",
                    "Confirm VPN/remote access",
                    "Test internet access",
                ],
                success_criteria=[
                    "All sites connected",
                    "Remote access working",
                    "Internet access confirmed",
                ],
                risks_if_missed=[
                    "Sites isolated - cannot work",
                    "Remote workers disconnected",
                    "Business disruption",
                ],
            ),
            Milestone.DAY_100: WorkstreamRequirement(
                criticality="critical",
                description="Establish standalone network",
                activities=[
                    "Design standalone network architecture",
                    "Procure network services (ISP, SDWAN)",
                    "Deploy edge devices at sites",
                    "Implement firewalls",
                    "Cutover from parent network",
                ],
                success_criteria=[
                    "Standalone WAN operational",
                    "All sites connected independently",
                    "Network TSA exited",
                ],
                risks_if_missed=[
                    "Ongoing network TSA costs",
                    "Limited network control",
                    "Security concerns",
                ],
                typical_cost_range=("$150K", "$500K"),
                typical_duration="3-6 months",
            ),
        },
    },

    # =========================================================================
    # SECURITY
    # =========================================================================
    "security": {
        "name": "Security & Compliance",
        "why_it_matters": """
Security protects the business.
- Endpoint protection (EDR)
- Security monitoring (SIEM)
- Threat detection and response
- Compliance requirements

Security is Day-1 CRITICAL - you cannot operate without security controls.
A security incident during transition could derail the entire deal.
""",
        DealType.CARVEOUT: {
            Milestone.DAY_1: WorkstreamRequirement(
                criticality="critical",
                description="Security monitoring active - no gap in coverage",
                activities=[
                    "Activate security TSA (if parent provides SOC)",
                    "Verify endpoint protection active",
                    "Confirm security monitoring working",
                    "Establish incident response procedures",
                ],
                success_criteria=[
                    "Security monitoring active",
                    "Endpoint protection on all devices",
                    "Incident response plan in place",
                ],
                risks_if_missed=[
                    "Security blind spot during transition",
                    "Potential breach undetected",
                    "Compliance violations",
                    "Deal reputation damage",
                ],
            ),
            Milestone.DAY_100: WorkstreamRequirement(
                criticality="critical",
                description="Establish standalone security capabilities",
                activities=[
                    "Deploy standalone SIEM/logging",
                    "Implement MDR or build SOC",
                    "Deploy security tools (EDR, email security)",
                    "Establish vulnerability management",
                    "Document security policies",
                ],
                success_criteria=[
                    "Standalone security monitoring",
                    "All security tools deployed",
                    "Security TSA exited",
                ],
                risks_if_missed=[
                    "Ongoing security TSA costs",
                    "Increased risk exposure",
                    "Compliance gaps",
                ],
                typical_cost_range=("$200K", "$600K"),
                typical_duration="3-6 months",
            ),
        },
    },

    # =========================================================================
    # APPLICATIONS (ERP)
    # =========================================================================
    "applications": {
        "name": "Business Applications (ERP/Core)",
        "why_it_matters": """
ERP and core applications run the business.
- Finance and accounting
- Supply chain and operations
- HR and payroll
- Customer-facing systems

ERP is typically NOT Day-1 critical (can run on TSA) but is YEAR-1 critical.
ERP separation is often the longest and most expensive workstream.
""",
        DealType.CARVEOUT: {
            Milestone.DAY_1: WorkstreamRequirement(
                criticality="important",
                description="ERP operational via TSA - business continues",
                activities=[
                    "Activate ERP TSA",
                    "Verify all ERP functions working",
                    "Confirm reporting operational",
                    "Establish support escalation",
                ],
                success_criteria=[
                    "ERP fully operational",
                    "All business processes working",
                    "Reporting functional",
                ],
                risks_if_missed=[
                    "Business operations disrupted",
                    "Financial close impacted",
                    "Supply chain issues",
                ],
            ),
            Milestone.YEAR_1: WorkstreamRequirement(
                criticality="critical",
                description="Complete ERP separation",
                activities=[
                    "Deploy standalone ERP instance",
                    "Extract and migrate data",
                    "Rebuild customizations",
                    "Rebuild integrations",
                    "User acceptance testing",
                    "Training and change management",
                    "Go-live and hypercare",
                ],
                success_criteria=[
                    "Standalone ERP operational",
                    "All data migrated",
                    "All integrations working",
                    "ERP TSA exited",
                ],
                risks_if_missed=[
                    "Very high ongoing TSA costs",
                    "Operational dependency",
                    "Data separation challenges",
                ],
                typical_cost_range=("$1M", "$5M"),
                typical_duration="9-18 months",
            ),
        },
    },

    # =========================================================================
    # SERVICE DESK
    # =========================================================================
    "service_desk": {
        "name": "IT Support / Service Desk",
        "why_it_matters": """
Service desk keeps IT running day-to-day.
- User support and troubleshooting
- Password resets and access issues
- Hardware/software problems
- Incident management

Service desk is Day-1 IMPORTANT - users need support from day one.
""",
        DealType.CARVEOUT: {
            Milestone.DAY_1: WorkstreamRequirement(
                criticality="important",
                description="User support available - TSA or interim solution",
                activities=[
                    "Activate service desk TSA",
                    "Establish support contact info",
                    "Communicate support process to users",
                    "Set up escalation paths",
                ],
                success_criteria=[
                    "Users know how to get help",
                    "Support channels operational",
                    "Escalation path to parent (TSA) working",
                ],
                risks_if_missed=[
                    "User frustration",
                    "Productivity loss",
                    "IT issues unresolved",
                ],
            ),
            Milestone.DAY_100: WorkstreamRequirement(
                criticality="important",
                description="Establish standalone support capability",
                activities=[
                    "Contract MSP or hire IT staff",
                    "Implement ITSM tool",
                    "Knowledge transfer from parent",
                    "Document environment runbooks",
                    "Transition support to standalone",
                ],
                success_criteria=[
                    "Standalone support operational",
                    "Service desk TSA exited",
                    "Knowledge documented",
                ],
                risks_if_missed=[
                    "Ongoing TSA costs",
                    "Knowledge loss",
                    "Support quality issues",
                ],
                typical_cost_range=("$100K", "$300K"),
                typical_duration="3-6 months",
            ),
        },
    },
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_deal_type_summary(deal_type: DealType) -> Dict:
    """Get comprehensive summary for a deal type."""
    return DEAL_TYPE_DEFINITIONS.get(deal_type, {})


def get_milestone_summary(milestone: Milestone) -> Dict:
    """Get comprehensive summary for a milestone."""
    return MILESTONE_DEFINITIONS.get(milestone, {})


def get_workstream_requirement(
    workstream: str,
    deal_type: DealType,
    milestone: Milestone
) -> Optional[WorkstreamRequirement]:
    """Get specific requirement for workstream/deal/milestone combination."""
    ws_reqs = WORKSTREAM_REQUIREMENTS.get(workstream, {})
    deal_reqs = ws_reqs.get(deal_type, {})
    return deal_reqs.get(milestone)


def get_day1_critical_workstreams(deal_type: DealType) -> List[str]:
    """Get list of Day-1 critical workstreams for a deal type."""
    critical = []
    for ws_key, ws_data in WORKSTREAM_REQUIREMENTS.items():
        deal_data = ws_data.get(deal_type, {})
        day1_req = deal_data.get(Milestone.DAY_1)
        if day1_req and day1_req.criticality == "critical":
            critical.append(ws_key)
    return critical


def get_day100_requirements(deal_type: DealType) -> List[Dict]:
    """Get all Day-100 requirements for a deal type."""
    requirements = []
    for ws_key, ws_data in WORKSTREAM_REQUIREMENTS.items():
        deal_data = ws_data.get(deal_type, {})
        day100_req = deal_data.get(Milestone.DAY_100)
        if day100_req:
            requirements.append({
                "workstream": ws_key,
                "name": ws_data.get("name", ws_key),
                "requirement": day100_req
            })
    return requirements


def generate_deal_summary(deal_type: DealType) -> str:
    """Generate a narrative summary for a deal type."""
    deal_info = DEAL_TYPE_DEFINITIONS.get(deal_type, {})
    day1_critical = get_day1_critical_workstreams(deal_type)
    day100_reqs = get_day100_requirements(deal_type)

    lines = [
        f"# {deal_info.get('name', deal_type.value)} - IT Considerations",
        "",
        f"## Overview",
        deal_info.get('description', ''),
        "",
        f"**Key Characteristic**: {deal_info.get('key_characteristic', '')}",
        f"**Primary Challenge**: {deal_info.get('primary_challenge', '')}",
        f"**TSA Typically Required**: {'Yes' if deal_info.get('tsa_typical') else 'No'}",
        "",
        "## Key Questions to Answer",
    ]

    for q in deal_info.get('key_questions', []):
        lines.append(f"- {q}")

    lines.extend([
        "",
        "## Day-1 Critical Workstreams",
        "These MUST be operational at close or business stops:",
    ])

    for ws in day1_critical:
        ws_data = WORKSTREAM_REQUIREMENTS.get(ws, {})
        lines.append(f"- **{ws_data.get('name', ws)}**")

    lines.extend([
        "",
        "## Day-100 Requirements",
        "These should be substantially complete by Day 100:",
    ])

    for req in day100_reqs:
        lines.append(f"- **{req['name']}**: {req['requirement'].description}")
        if req['requirement'].typical_cost_range:
            lines.append(f"  - Typical Cost: {req['requirement'].typical_cost_range[0]} - {req['requirement'].typical_cost_range[1]}")

    return "\n".join(lines)


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    'DealType',
    'Milestone',
    'WorkstreamRequirement',
    'DEAL_TYPE_DEFINITIONS',
    'MILESTONE_DEFINITIONS',
    'WORKSTREAM_REQUIREMENTS',
    'get_deal_type_summary',
    'get_milestone_summary',
    'get_workstream_requirement',
    'get_day1_critical_workstreams',
    'get_day100_requirements',
    'generate_deal_summary',
]
