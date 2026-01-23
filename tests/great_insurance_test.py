"""
Great Insurance Test Case - Full Pipeline Test

Tests the complete analysis pipeline against the Great Insurance
carveout scenario with 7 DD documents and 6 test hooks.
"""

import sys
from pathlib import Path
from typing import Dict, List, Any

# Add project root
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools_v2.evidence_query import EvidenceStore, Evidence, EvidenceType, QueryBuilder
from prompts.shared.function_deep_dive import (
    get_function_criteria,
    get_all_criteria,
)


# =============================================================================
# GREAT INSURANCE - BASELINE FACTS FROM DOCUMENTS
# =============================================================================

DEAL_CONTEXT = {
    "deal_type": "carveout",
    "target_name": "Great Insurance",
    "target_revenue": 500_000_000,
    "target_employees": 2296,
    "it_budget": 22_100_000,
    "it_headcount": 141,
}

# Key facts extracted from Documents 1-7
BASELINE_FACTS = {
    # Organization
    "org": {
        "it_headcount": 141,
        "outsourced_pct": 13,
        "personnel_cost": 19_632_626,
        "teams": [
            {"name": "IT Leadership", "headcount": 8, "cost": 2_075_736, "outsourced_pct": 0},
            {"name": "Applications", "headcount": 46, "cost": 6_634_032, "outsourced_pct": 0},
            {"name": "Data & Analytics", "headcount": 17, "cost": 2_715_440, "outsourced_pct": 0},
            {"name": "Cybersecurity", "headcount": 11, "cost": 1_867_863, "outsourced_pct": 0},
            {"name": "Infrastructure", "headcount": 24, "cost": 3_148_235, "outsourced_pct": 38},
            {"name": "Service Desk", "headcount": 21, "cost": 1_555_949, "outsourced_pct": 43},
            {"name": "Enterprise PMO", "headcount": 14, "cost": 1_635_371, "outsourced_pct": 0},
        ],
        "vendors": [
            {"name": "CGI", "scope": "Infrastructure + Service Desk", "cost": 623_830},
            {"name": "Ensono", "scope": "Infrastructure", "headcount": 9, "cost": 1_180_588},
            {"name": "Unisys", "scope": "Service Desk", "headcount": 9, "cost": 666_835},
        ]
    },

    # Applications
    "applications": {
        "total_apps": 33,
        "total_cost": 7_183_701,
        "saas_cloud": 25,
        "on_prem_hybrid": 8,
        "critical_apps": [
            {"name": "Duck Creek Policy", "category": "Policy", "hosting": "On Prem", "cost": 546_257, "criticality": "CRITICAL"},
            {"name": "Majesco Policy", "category": "Policy", "hosting": "On Prem", "cost": 440_225, "criticality": "CRITICAL"},
            {"name": "Duck Creek Claims", "category": "Claims", "hosting": "On Prem", "cost": 435_426, "criticality": "CRITICAL"},
            {"name": "Guidewire ClaimCenter", "category": "Claims", "hosting": "Cloud", "cost": 421_687, "criticality": "CRITICAL"},
            {"name": "NetSuite", "category": "ERP", "hosting": "SaaS", "cost": 309_562, "criticality": "CRITICAL"},
            {"name": "SAP S/4HANA", "category": "ERP", "hosting": "Hybrid", "cost": 276_449, "criticality": "CRITICAL"},
        ],
        "erp_systems": ["NetSuite", "SAP S/4HANA"],  # Dual ERP!
        "billing_systems": ["CSG Ascendon", "Netcracker Revenue Mgmt", "Amdocs Revenue Mgmt"],
    },

    # Infrastructure
    "infrastructure": {
        "data_centers": 4,
        "total_spend": 2_575_899,
        "dc_inventory": [
            {"name": "Primary DC - Dallas", "type": "Colocation", "tier": 3, "racks": 24, "cost": 992_625, "constraint": "Non-cancellable 12 months"},
            {"name": "Secondary DC - Seattle", "type": "Colocation", "tier": 3, "racks": 3, "cost": 103_267},
            {"name": "Secondary DC - Phoenix", "type": "Owned", "tier": 2, "racks": 11, "cost": 0},
            {"name": "Secondary DC - Atlanta", "type": "Owned", "tier": 2, "racks": 4, "cost": 0},
        ],
        "cloud": {
            "provider": "AWS",
            "region": "us-east-1",
            "accounts": 25,
            "services": ["DynamoDB", "CloudFront", "SQS"],
            "monthly_spend": 123_334,
            "annual_spend": 1_480_007,
        },
        "dr": {
            "strategy": "Hot",
            "tier": 2,
            "rpo": "0 hours",
            "rto": "1 hour",
            "retention": "180 days",
            "tools": ["Zerto", "Druva"],
        }
    },

    # Security
    "security": {
        "tools_overlap": {
            "endpoint": ["SentinelOne", "CrowdStrike"],  # H4 - Dual tool
            "siem": ["Elastic SIEM", "Splunk ES"],  # H4 - Dual tool
            "email_security": ["Mimecast", "Proofpoint"],  # H4 - Dual tool
            "identity": ["Okta", "Microsoft Entra ID"],  # H4 - Dual tool
        },
        "pam": "CyberArk",
        "firewall": "Juniper",
        "backup": "Druva",
    },

    # Test Hooks (intentional complications)
    "test_hooks": {
        "H1": {
            "name": "Carveout perimeter",
            "description": "Shared corporate services (Identity + Email)",
            "impact": "TSA dependency",
            "affected": ["Microsoft Entra ID", "Okta", "Microsoft 365", "Exchange Online"],
        },
        "H2": {
            "name": "Parent-hosted app",
            "description": "Netcracker Revenue Mgmt is parent-hosted",
            "impact": "TSA until Day-180",
            "affected": ["Netcracker Revenue Management"],
        },
        "H3": {
            "name": "Contract cliff",
            "description": "Renewals due <90 days",
            "impact": "Immediate action required",
            "affected": ["ServiceNow ITSM", "Workday HCM"],
        },
        "H4": {
            "name": "Dual-tool reality",
            "description": "Overlapping tools across domains",
            "impact": "Rationalization needed",
            "affected": ["Endpoint", "SIEM", "Email Security", "Identity"],
        },
        "H5": {
            "name": "DC constraint",
            "description": "Dallas DC lease non-cancellable",
            "impact": "12 months stranded cost risk",
            "affected": ["Primary DC - Dallas"],
        },
        "H6": {
            "name": "Data residency",
            "description": "PII must remain in AWS us-east-1",
            "impact": "Migration constraint until Day-120",
            "affected": ["Snowflake", "Data workloads"],
        },
    }
}


# =============================================================================
# POPULATE EVIDENCE STORE
# =============================================================================

def populate_evidence_store() -> EvidenceStore:
    """Create and populate evidence store from Great Insurance documents."""
    store = EvidenceStore()

    # Organization facts
    store.add_evidence(Evidence(
        evidence_id="F-ORG-001",
        evidence_type=EvidenceType.FACT,
        domain="organization",
        function="IT Leadership",
        content=f"IT headcount: {BASELINE_FACTS['org']['it_headcount']} (13% outsourced)",
        details={"headcount": 141, "outsourced_pct": 13},
        tags=["headcount", "org-structure"],
    ))

    for team in BASELINE_FACTS["org"]["teams"]:
        store.add_evidence(Evidence(
            evidence_id="",
            evidence_type=EvidenceType.FACT,
            domain="organization",
            function=team["name"] if team["name"] != "IT Leadership" else "IT Leadership",
            content=f"{team['name']}: {team['headcount']} FTEs, ${team['cost']:,} annual cost, {team['outsourced_pct']}% outsourced",
            details=team,
            tags=["team", "headcount", "cost"],
        ))

    for vendor in BASELINE_FACTS["org"]["vendors"]:
        store.add_evidence(Evidence(
            evidence_id="",
            evidence_type=EvidenceType.FACT,
            domain="organization",
            function="Service Desk" if "Desk" in vendor["scope"] else "Infrastructure Team",
            content=f"Vendor: {vendor['name']} - {vendor['scope']} (${vendor['cost']:,}/yr)",
            details=vendor,
            tags=["vendor", "outsourcing", "msp"],
            mna_lens="tsa_exposure",
        ))

    # Applications facts
    store.add_evidence(Evidence(
        evidence_id="F-APP-001",
        evidence_type=EvidenceType.FACT,
        domain="applications",
        function="ERP",
        content=f"Total applications: {BASELINE_FACTS['applications']['total_apps']} (${BASELINE_FACTS['applications']['total_cost']:,}/yr)",
        details={"total": 33, "cost": 7_183_701},
        tags=["apps", "portfolio"],
    ))

    store.add_evidence(Evidence(
        evidence_id="F-APP-002",
        evidence_type=EvidenceType.FACT,
        domain="applications",
        function="ERP",
        content="Dual ERP environment: NetSuite (SaaS) + SAP S/4HANA (Hybrid)",
        details={"erp_systems": ["NetSuite", "SAP S/4HANA"]},
        tags=["erp", "dual-erp", "complexity"],
        mna_lens="synergy_opportunity",
    ))

    for app in BASELINE_FACTS["applications"]["critical_apps"]:
        store.add_evidence(Evidence(
            evidence_id="",
            evidence_type=EvidenceType.FACT,
            domain="applications",
            function="ERP" if app["category"] == "ERP" else "Custom Applications",
            content=f"{app['name']} ({app['category']}): {app['hosting']}, ${app['cost']:,}/yr, {app['criticality']}",
            details=app,
            tags=["critical-app", app["category"].lower()],
            mna_lens="day_1_continuity" if app["criticality"] == "CRITICAL" else None,
        ))

    # Infrastructure facts
    store.add_evidence(Evidence(
        evidence_id="F-INFRA-001",
        evidence_type=EvidenceType.FACT,
        domain="infrastructure",
        function="Data Center",
        content="4 data centers: 2 colocation (Dallas, Seattle), 2 owned (Phoenix, Atlanta)",
        details={"dc_count": 4, "colo": 2, "owned": 2},
        tags=["dc", "hosting"],
    ))

    for dc in BASELINE_FACTS["infrastructure"]["dc_inventory"]:
        constraint = dc.get("constraint")
        store.add_evidence(Evidence(
            evidence_id="",
            evidence_type=EvidenceType.FACT,
            domain="infrastructure",
            function="Data Center",
            content=f"{dc['name']}: {dc['type']}, Tier {dc['tier']}, {dc['racks']} racks" + (f" - {constraint}" if constraint else ""),
            details=dc,
            tags=["dc", dc["type"].lower()],
            mna_lens="separation_complexity" if constraint else None,
        ))

    cloud = BASELINE_FACTS["infrastructure"]["cloud"]
    store.add_evidence(Evidence(
        evidence_id="F-INFRA-010",
        evidence_type=EvidenceType.FACT,
        domain="infrastructure",
        function="Cloud Infrastructure",
        content=f"AWS ({cloud['region']}): {cloud['accounts']} accounts, ${cloud['annual_spend']:,}/yr",
        details=cloud,
        tags=["cloud", "aws"],
    ))

    dr = BASELINE_FACTS["infrastructure"]["dr"]
    store.add_evidence(Evidence(
        evidence_id="F-INFRA-020",
        evidence_type=EvidenceType.FACT,
        domain="infrastructure",
        function="Backup/DR",
        content=f"DR Strategy: {dr['strategy']}, Tier {dr['tier']}, RPO {dr['rpo']}, RTO {dr['rto']}",
        details=dr,
        tags=["dr", "bcdr", "resilience"],
        mna_lens="day_1_continuity",
    ))

    # Security facts - with dual tool overlap (H4)
    for domain, tools in BASELINE_FACTS["security"]["tools_overlap"].items():
        store.add_evidence(Evidence(
            evidence_id="",
            evidence_type=EvidenceType.FACT,
            domain="cybersecurity",
            function="Security Operations" if domain in ["siem", "endpoint"] else "Access Management",
            content=f"{domain.replace('_', ' ').title()}: Dual tools observed - {', '.join(tools)}",
            details={"domain": domain, "tools": tools, "overlap": True},
            tags=["security", "tool-overlap", "h4"],
            mna_lens="synergy_opportunity",
        ))

    # Test Hook evidence
    for hook_id, hook in BASELINE_FACTS["test_hooks"].items():
        store.add_evidence(Evidence(
            evidence_id="",
            evidence_type=EvidenceType.RISK if "risk" in hook["impact"].lower() else EvidenceType.INFERENCE,
            domain="applications" if "app" in hook["name"].lower() else "infrastructure",
            function=None,
            content=f"{hook_id}: {hook['name']} - {hook['description']}. Impact: {hook['impact']}",
            details=hook,
            tags=["test-hook", hook_id.lower()],
            mna_lens="tsa_exposure" if "TSA" in hook["impact"] else "day_1_continuity",
        ))

    # Key risks
    store.add_evidence(Evidence(
        evidence_id="R-APP-001",
        evidence_type=EvidenceType.RISK,
        domain="applications",
        function="ERP",
        content="Contract cliff: ServiceNow ITSM and Workday HCM renewals due in <90 days",
        details={"apps": ["ServiceNow", "Workday"], "window": "<90 days"},
        source_facts=["F-APP-001"],
        tags=["contract", "renewal", "h3"],
        mna_lens="day_1_continuity",
        confidence="high",
    ))

    store.add_evidence(Evidence(
        evidence_id="R-INFRA-001",
        evidence_type=EvidenceType.RISK,
        domain="infrastructure",
        function="Data Center",
        content="Dallas DC lease non-cancellable for 12 months - stranded cost risk",
        details={"dc": "Dallas", "duration": "12 months"},
        source_facts=["F-INFRA-001"],
        tags=["dc", "lease", "stranded-cost", "h5"],
        mna_lens="cost_driver",
        confidence="high",
    ))

    store.add_evidence(Evidence(
        evidence_id="R-APP-002",
        evidence_type=EvidenceType.RISK,
        domain="applications",
        function="Custom Applications",
        content="Netcracker Revenue Mgmt parent-hosted until Day-180 - TSA required",
        details={"app": "Netcracker", "tsa_duration": "Day-180"},
        source_facts=["F-APP-001"],
        tags=["tsa", "billing", "h2"],
        mna_lens="tsa_exposure",
        confidence="high",
    ))

    # Gaps
    store.add_evidence(Evidence(
        evidence_id="G-INFRA-001",
        evidence_type=EvidenceType.GAP,
        domain="infrastructure",
        function="Backup/DR",
        content="GAP: DR test date and evidence not provided",
        details={"missing": "DR test documentation"},
        tags=["dr", "testing", "evidence-gap"],
        mna_lens="day_1_continuity",
    ))

    store.add_evidence(Evidence(
        evidence_id="G-SEC-001",
        evidence_type=EvidenceType.GAP,
        domain="cybersecurity",
        function="Security Operations",
        content="GAP: SOC coverage model (24x7 vs business hours) not specified",
        details={"missing": "SOC coverage hours"},
        tags=["soc", "coverage", "evidence-gap"],
    ))

    # Inferences
    store.add_evidence(Evidence(
        evidence_id="I-ORG-001",
        evidence_type=EvidenceType.INFERENCE,
        domain="organization",
        function="Infrastructure Team",
        content="Inference: 38% outsourcing in Infrastructure + 43% in Service Desk indicates TSA complexity for carveout",
        source_facts=["F-ORG-001"],
        tags=["outsourcing", "tsa"],
        mna_lens="tsa_exposure",
    ))

    store.add_evidence(Evidence(
        evidence_id="I-APP-001",
        evidence_type=EvidenceType.INFERENCE,
        domain="applications",
        function="ERP",
        content="Inference: Dual ERP (NetSuite + SAP S/4HANA) suggests prior M&A not fully integrated - rationalization opportunity",
        source_facts=["F-APP-002"],
        tags=["erp", "rationalization"],
        mna_lens="synergy_opportunity",
    ))

    return store


# =============================================================================
# ANALYSIS FUNCTIONS
# =============================================================================

def analyze_coverage(store: EvidenceStore) -> Dict[str, Any]:
    """Analyze evidence coverage against function criteria."""
    all_criteria = get_all_criteria()
    coverage_report = {}

    for domain, functions in all_criteria.items():
        domain_evidence = store.query_by_domain(domain)
        coverage_report[domain] = {
            "evidence_count": len(domain_evidence),
            "functions": {}
        }

        for func_name, criteria in functions.items():
            func_evidence = store.query_by_function(func_name)
            coverage_report[domain]["functions"][func_name] = {
                "evidence_count": len(func_evidence),
                "questions_count": len(criteria.must_answer_questions),
                "required_evidence": len(criteria.required_evidence),
            }

    return coverage_report


def generate_executive_summary(store: EvidenceStore) -> List[str]:
    """Generate executive summary bullets from evidence."""
    bullets = []

    # Org shape
    _ = store.query_by_domain("organization")
    bullets.append("Great Insurance operates with 141 IT staff (13% outsourced) across 7 teams, supporting 2,296 employees (F-ORG-001)")

    # Key risks
    risks = store.query_by_type(EvidenceType.RISK)
    bullets.append(f"Identified {len(risks)} key risks including contract cliffs (<90 days on ServiceNow/Workday) and DC lease constraints")

    # TSA exposure
    tsa_evidence = store.query_by_mna_lens("tsa_exposure")
    bullets.append(f"High TSA exposure: {len(tsa_evidence)} items tied to shared services (Identity, Email) and parent-hosted billing")

    # Tool rationalization
    bullets.append("Inference: Dual-tool overlap across EDR (SentinelOne/CrowdStrike), SIEM (Elastic/Splunk), and Identity (Okta/Entra) - rationalization required post-Day-1")

    # Day-1 critical
    day1 = store.query_by_mna_lens("day_1_continuity")
    bullets.append(f"Day-1 continuity: {len(day1)} items flagged including DR posture (Hot, RPO 0h, RTO 1h) and critical billing systems")

    # Gaps
    gaps = store.get_gaps()
    bullets.append(f"Identified {len(gaps)} evidence gaps requiring follow-up: DR test documentation, SOC coverage model")

    return bullets


def generate_mna_lens_view(store: EvidenceStore) -> Dict[str, Any]:
    """Generate M&A lens breakdown."""
    return {
        "day_1_continuity": {
            "count": len(store.get_day1_evidence()),
            "items": [e.content[:80] + "..." for e in store.get_day1_evidence()[:5]]
        },
        "tsa_exposure": {
            "count": len(store.get_tsa_evidence()),
            "items": [e.content[:80] + "..." for e in store.get_tsa_evidence()[:5]]
        },
        "separation_complexity": {
            "count": len(store.get_separation_evidence()),
            "items": [e.content[:80] + "..." for e in store.get_separation_evidence()[:5]]
        },
        "synergy_opportunity": {
            "count": len(store.get_synergy_evidence()),
            "items": [e.content[:80] + "..." for e in store.get_synergy_evidence()[:5]]
        },
    }


# =============================================================================
# MAIN TEST
# =============================================================================

def run_test():
    """Run the Great Insurance test case."""
    print("=" * 70)
    print("GREAT INSURANCE CARVEOUT - IT DUE DILIGENCE TEST")
    print("=" * 70)

    # Populate evidence store
    print("\n1. POPULATING EVIDENCE STORE...")
    store = populate_evidence_store()
    print(f"   Total evidence items: {len(store.evidence)}")

    # Coverage analysis
    print("\n2. EVIDENCE COVERAGE BY DOMAIN:")
    coverage = store.get_coverage_by_domain()
    for domain, stats in coverage.items():
        print(f"   {domain}: {stats['total']} items (Facts: {stats['facts']}, Risks: {stats['risks']}, Gaps: {stats['gaps']})")

    # M&A Lens view
    print("\n3. M&A LENS BREAKDOWN:")
    mna = store.get_mna_summary()
    for lens, count in mna.items():
        print(f"   {lens}: {count} items")

    # Executive Summary
    print("\n4. EXECUTIVE SUMMARY (Generated):")
    print("-" * 50)
    bullets = generate_executive_summary(store)
    for i, bullet in enumerate(bullets, 1):
        print(f"   {i}. {bullet}")

    # Query demonstrations
    print("\n5. QUERY DEMONSTRATIONS:")
    print("-" * 50)

    # Query: All TSA-related evidence
    print("\n   a) TSA Exposure Evidence:")
    tsa = store.get_tsa_evidence()
    for e in tsa[:3]:
        print(f"      - [{e.evidence_id}] {e.content[:70]}...")

    # Query: Contract risks
    print("\n   b) Contract/Renewal Risks (tag: 'contract'):")
    contract_risks = store.query(tags=["contract"])
    for e in contract_risks:
        print(f"      - [{e.evidence_id}] {e.content[:70]}...")

    # Query: Test hooks
    print("\n   c) Test Hooks Detected:")
    hooks = store.query(tags=["test-hook"])
    for e in hooks:
        print(f"      - {e.content[:80]}...")

    # Query Builder demo
    print("\n   d) QueryBuilder: Infrastructure + Gaps:")
    infra_gaps = QueryBuilder(store).domain("infrastructure").type(EvidenceType.GAP).execute()
    for e in infra_gaps:
        print(f"      - [{e.evidence_id}] {e.content}")

    # Traceability demo
    print("\n6. TRACEABILITY DEMONSTRATION:")
    print("-" * 50)
    chain = store.get_evidence_chain("I-ORG-001")
    if "error" not in chain:
        print(f"   Evidence: {chain['evidence']['content'][:70]}...")
        print(f"   Source facts: {chain['evidence']['source_facts']}")

    # Gaps summary
    print("\n7. GAPS REQUIRING FOLLOW-UP:")
    print("-" * 50)
    gaps = store.get_gaps()
    for gap in gaps:
        print(f"   - [{gap.evidence_id}] {gap.content}")
        print(f"     Function: {gap.function}, Lens: {gap.mna_lens}")

    # Function coverage check
    print("\n8. FUNCTION DEEP DIVE COVERAGE CHECK:")
    print("-" * 50)

    # Check ERP function
    erp_criteria = get_function_criteria("applications", "ERP")
    if erp_criteria:
        print(f"\n   ERP Function ({len(erp_criteria.must_answer_questions)} must-answer questions):")
        erp_evidence = store.query_by_function("ERP")
        print(f"   Evidence collected: {len(erp_evidence)} items")
        print(f"   Risk indicators to check: {erp_criteria.risk_indicators[:3]}...")

    # Check Data Center function
    dc_criteria = get_function_criteria("infrastructure", "Data Center")
    if dc_criteria:
        print(f"\n   Data Center Function ({len(dc_criteria.must_answer_questions)} must-answer questions):")
        dc_evidence = store.query_by_function("Data Center")
        print(f"   Evidence collected: {len(dc_evidence)} items")

    print("\n" + "=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)

    return store


if __name__ == "__main__":
    store = run_test()
