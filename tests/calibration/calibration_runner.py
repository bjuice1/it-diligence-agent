"""
Calibration Runner for Executive Narrative Testing

Runs test cases through the narrative generation pipeline and scores
the outputs against the quality rubric.

Usage:
    python -m tests.calibration.calibration_runner --test-case TC-01
    python -m tests.calibration.calibration_runner --all
    python -m tests.calibration.calibration_runner --quick  # Score existing narratives
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import asdict

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tests.calibration.test_cases import (
    TestCase, get_test_case, get_all_test_cases, DealType
)
from tests.calibration.quality_rubric import (
    score_narrative, format_rubric_result, RubricResult
)


# =============================================================================
# MOCK NARRATIVE GENERATOR (for testing without LLM)
# =============================================================================

def generate_mock_narrative(test_case: TestCase) -> Dict[str, Any]:
    """
    Generate a mock narrative from test case inventory.
    This allows testing the scoring system without LLM calls.
    """
    inventory = test_case.inventory
    org = inventory.get("organization", {})
    apps = inventory.get("applications", {})
    infra = inventory.get("infrastructure", {})
    security = inventory.get("cybersecurity", {})

    # Extract team info
    structure = org.get("structure", {})
    teams = structure.get("teams", [])

    # Build executive summary
    exec_summary = []
    exec_summary.append(f"Target employs {org.get('it_headcount', 'unknown')} IT staff across {len(teams)} functional teams")

    if test_case.deal_type == DealType.CARVEOUT:
        exec_summary.append("Inference: High TSA dependency due to shared services reliance")
        exec_summary.append("Day-1 risk: Multiple critical functions require parent support")
    elif test_case.deal_type == DealType.ACQUISITION:
        exec_summary.append("Synergy opportunity: License consolidation and tool rationalization")
        exec_summary.append("Integration complexity appears manageable given cloud-first architecture")

    exec_summary.append(f"Primary ERP: {apps.get('erp', {}).get('name', 'Unknown')} (F-APPS-001)")
    exec_summary.append("Key person risk identified in IT leadership (F-ORG-001)")
    exec_summary.append("Security posture requires attention - MFA coverage below target")

    # Build org structure narrative
    org_narrative = f"""
The IT organization at {test_case.target_name} is structured as a {'lean' if org.get('it_headcount', 0) < 20 else 'layered'} team
with {org.get('it_headcount', 'unknown')} total headcount. The organization appears {'run-heavy' if len(teams) < 5 else 'balanced'}
based on team composition, with {'significant' if any(t.get('outsourced_pct', 0) > 50 for t in teams) else 'limited'}
outsourcing in service delivery functions.

Inference: The ratio of {org.get('it_headcount', 0)} IT staff to support the business suggests a lean operating model
that may face capacity constraints during integration or separation activities.
""".strip()

    # Build team stories
    team_stories = []
    for team in teams:
        story = {
            "function_name": team.get("name", "Unknown Team"),
            "day_to_day": f"The {team.get('name')} team handles day-to-day operations with {team.get('headcount', 0)} staff",
            "strengths": [
                "Established processes for core responsibilities",
                "Team tenure suggests institutional knowledge"
            ],
            "constraints": [],
            "upstream_dependencies": ["Corporate IT", "Vendors"],
            "downstream_dependents": ["Business units", "End users"],
            "mna_implication": ""
        }

        # Add constraints based on outsourcing
        outsourced = team.get("outsourced_pct", 0)
        if outsourced > 50:
            story["constraints"].append(f"High outsourcing ({outsourced}%) creates vendor dependency (F-ORG-002)")
            story["mna_implication"] = "TSA exposure: Outsourced services may require transition agreement"
        elif outsourced > 0:
            story["constraints"].append("Mixed staffing model may complicate transition")

        # Add shared service constraint for carveouts
        if team.get("shared_with_parent") or team.get("dedicated") == False:
            story["constraints"].append("Shared with parent - separation required")
            story["mna_implication"] = "Day-1 risk: Function depends on parent shared services"

        if not story["mna_implication"]:
            story["mna_implication"] = "Synergy opportunity: Consolidation with buyer team possible"

        team_stories.append(story)

    # Build M&A lens section
    mna_section = {
        "tsa_exposed_functions": [],
        "day_1_requirements": [],
        "separation_considerations": []
    }

    # TSA exposure
    parent_services = org.get("parent_shared_services", [])
    if parent_services:
        mna_section["tsa_exposed_functions"] = parent_services
    else:
        for team in teams:
            if team.get("outsourced_pct", 0) > 50:
                mna_section["tsa_exposed_functions"].append(f"{team['name']} ({team['outsourced_pct']}% outsourced)")

    # Day-1 requirements
    mna_section["day_1_requirements"] = [
        f"Ensure {apps.get('erp', {}).get('name', 'ERP')} access continues without interruption",
        "Maintain network connectivity to all locations",
        "Preserve authentication and access management",
        "Continue security monitoring and incident response capability"
    ]

    # Separation considerations
    mna_section["separation_considerations"] = [
        "Establish standalone identity management (migrate from parent AD)",
        "Deploy dedicated security tooling (endpoint, SIEM)",
        "Negotiate TSA for infrastructure services (6-12 month term)",
        "Build or contract Service Desk capability",
        "Migrate to dedicated cloud tenant/subscription",
        "Implement standalone network egress and security"
    ]

    # Build benchmark statements
    benchmarks = []
    it_headcount = org.get("it_headcount", 0)
    if it_headcount > 0:
        benchmarks.append(f"Inference: IT headcount of {it_headcount} suggests a {'lean' if it_headcount < 20 else 'standard'} operating model")

    outsource_teams = [t for t in teams if t.get("outsourced_pct", 0) > 30]
    if outsource_teams:
        benchmarks.append(f"Outsourcing concentration in {len(outsource_teams)} functions indicates reliance on external delivery")

    mfa = security.get("mfa_coverage")
    if mfa and isinstance(mfa, (int, float)):
        benchmarks.append(f"MFA coverage at {mfa}% {'meets' if mfa >= 90 else 'falls below'} enterprise security expectations")
    elif mfa:
        benchmarks.append(f"MFA coverage: {mfa}")

    cloud_primary = infra.get("cloud_primary")
    cloud_posture = "modern" if cloud_primary else "traditional"
    benchmarks.append(f"Inference: Cloud adoption level suggests {cloud_posture} infrastructure posture")

    # Build risks table
    risks = [
        {
            "risk": "Key person dependency on CIO/IT leadership",
            "why_it_matters": "Single point of failure for IT strategy and operations",
            "likely_impact": "Day-1 continuity risk if key staff depart",
            "mitigation": "Implement knowledge transfer program and document critical processes",
            "severity": "high"
        },
        {
            "risk": "Security tooling gaps",
            "why_it_matters": "Incomplete security controls increase breach risk",
            "likely_impact": "Potential compliance issues and security incidents",
            "mitigation": "Deploy PAM solution and consolidate endpoint protection within 90 days",
            "severity": "medium"
        },
        {
            "risk": "Vendor/outsourcing concentration",
            "why_it_matters": "Heavy reliance on third parties for critical functions",
            "likely_impact": "TSA complexity and potential service gaps during transition",
            "mitigation": "Map all vendor dependencies and negotiate assignment/continuation terms",
            "severity": "medium"
        },
        {
            "risk": "Technical debt in applications",
            "why_it_matters": "Aging systems require investment and pose integration challenges",
            "likely_impact": "Higher integration costs and timeline risk",
            "mitigation": "Prioritize modernization roadmap aligned with deal thesis",
            "severity": "medium"
        },
        {
            "risk": "Data separation complexity",
            "why_it_matters": "Shared systems contain commingled data requiring extraction",
            "likely_impact": "Extended timeline and cost for clean separation",
            "mitigation": "Engage data migration specialist and establish extraction plan",
            "severity": "high"
        }
    ]

    # Build synergies table
    synergies = [
        {
            "opportunity": "License consolidation",
            "why_it_matters": "Duplicate software licenses across buyer and target",
            "value_mechanism": "cost_elimination",
            "first_step": "Inventory all software licenses and identify overlaps within 30 days",
            "estimated_value": "$200K-500K annually"
        },
        {
            "opportunity": "Service desk consolidation",
            "why_it_matters": "Redundant support organizations can be combined",
            "value_mechanism": "efficiency_gain",
            "first_step": "Map service desk volumes and SLAs to plan consolidation",
            "estimated_value": "$150K-300K annually"
        },
        {
            "opportunity": "Cloud optimization",
            "why_it_matters": "Combined cloud footprint enables better pricing and architecture",
            "value_mechanism": "cost_avoidance",
            "first_step": "Consolidate cloud accounts and negotiate enterprise agreement",
            "estimated_value": "$100K-250K annually"
        },
        {
            "opportunity": "Security tool rationalization",
            "why_it_matters": "Multiple overlapping security tools can be standardized",
            "value_mechanism": "cost_elimination",
            "first_step": "Assess security stack overlap and select go-forward toolset",
            "estimated_value": "$75K-150K annually"
        }
    ]

    return {
        "company_name": test_case.target_name,
        "deal_type": test_case.deal_type.value,
        "created_at": datetime.now().isoformat(),
        "executive_summary": exec_summary,
        "org_structure_narrative": org_narrative,
        "team_stories": team_stories,
        "mna_lens_section": mna_section,
        "benchmark_statements": benchmarks,
        "risks_table": risks,
        "synergies_table": synergies
    }


# =============================================================================
# NARRATIVE GENERATOR (with LLM)
# =============================================================================

def generate_narrative_with_llm(test_case: TestCase) -> Dict[str, Any]:
    """
    Generate narrative using the actual NarrativeSynthesisAgent.
    Requires API key and may take time.
    """
    try:
        from agents_v2 import NarrativeSynthesisAgent
    except ImportError:
        print("Warning: NarrativeSynthesisAgent not available, using mock generator")
        return generate_mock_narrative(test_case)

    # Convert test case inventory to domain findings format
    domain_findings = _inventory_to_findings(test_case.inventory)

    deal_context = {
        "deal_type": test_case.deal_type.value,
        "target_name": test_case.target_name,
        "buyer_name": test_case.buyer_name
    }

    agent = NarrativeSynthesisAgent()
    narrative = agent.synthesize(
        domain_findings=domain_findings,
        deal_context=deal_context
    )

    return narrative.to_dict() if hasattr(narrative, 'to_dict') else narrative


def _inventory_to_findings(inventory: Dict) -> Dict[str, Any]:
    """Convert test case inventory to domain findings format."""
    # This is a simplified conversion - real implementation would be more detailed
    findings = {
        "organization": {
            "risks": [],
            "work_items": [],
            "strategic_considerations": [],
            "recommendations": []
        },
        "applications": {
            "risks": [],
            "work_items": [],
            "strategic_considerations": [],
            "recommendations": []
        },
        "infrastructure": {
            "risks": [],
            "work_items": [],
            "strategic_considerations": [],
            "recommendations": []
        },
        "cybersecurity": {
            "risks": [],
            "work_items": [],
            "strategic_considerations": [],
            "recommendations": []
        },
        "network": {
            "risks": [],
            "work_items": [],
            "strategic_considerations": [],
            "recommendations": []
        },
        "identity_access": {
            "risks": [],
            "work_items": [],
            "strategic_considerations": [],
            "recommendations": []
        }
    }

    return findings


# =============================================================================
# CALIBRATION RUNNER
# =============================================================================

def run_calibration(
    test_case: TestCase,
    use_llm: bool = False,
    save_output: bool = True
) -> RubricResult:
    """
    Run calibration for a single test case.

    Args:
        test_case: The test case to run
        use_llm: Whether to use LLM for narrative generation
        save_output: Whether to save narrative and results to files

    Returns:
        RubricResult with scoring details
    """
    print(f"\n{'='*60}")
    print(f"Running calibration: {test_case.id} - {test_case.name}")
    print(f"Deal Type: {test_case.deal_type.value}, Complexity: {test_case.complexity.value}")
    print(f"{'='*60}")

    # Generate narrative
    print("\nGenerating narrative...")
    if use_llm:
        narrative = generate_narrative_with_llm(test_case)
    else:
        narrative = generate_mock_narrative(test_case)

    print(f"Generated narrative with {len(narrative.get('executive_summary', []))} exec summary bullets")

    # Score narrative
    print("\nScoring narrative...")
    deal_context = {
        "deal_type": test_case.deal_type.value,
        "target_name": test_case.target_name
    }

    result = score_narrative(narrative, test_case, deal_context)

    # Print results
    print(format_rubric_result(result))

    # Check against minimum scores
    print("\nMinimum Score Check:")
    all_pass = True
    for dim, min_score in test_case.minimum_scores.items():
        actual = result.dimension_scores.get(dim)
        if actual:
            passed = actual.score >= min_score
            status = "✅" if passed else "❌"
            print(f"  {status} {dim}: {actual.score:.1f} >= {min_score} required")
            if not passed:
                all_pass = False

    # Save outputs
    if save_output:
        output_dir = Path(__file__).parent / "outputs"
        output_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Save narrative
        narrative_file = output_dir / f"{test_case.id}_narrative_{timestamp}.json"
        with open(narrative_file, 'w') as f:
            json.dump(narrative, f, indent=2)
        print(f"\nNarrative saved to: {narrative_file}")

        # Save result
        result_file = output_dir / f"{test_case.id}_result_{timestamp}.json"
        result_dict = {
            "test_case_id": result.test_case_id,
            "overall_score": result.overall_score,
            "passing": result.passing,
            "dimension_scores": {
                k: {
                    "score": v.score,
                    "weight": v.weight,
                    "weighted_score": v.weighted_score,
                    "issues": v.issues,
                    "suggestions": v.suggestions
                }
                for k, v in result.dimension_scores.items()
            },
            "critical_issues": result.critical_issues,
            "improvement_areas": result.improvement_areas,
            "strengths": result.strengths
        }
        with open(result_file, 'w') as f:
            json.dump(result_dict, f, indent=2)
        print(f"Results saved to: {result_file}")

    return result


def run_all_calibrations(use_llm: bool = False) -> Dict[str, RubricResult]:
    """Run calibration for all test cases."""
    results = {}

    for test_case in get_all_test_cases():
        result = run_calibration(test_case, use_llm=use_llm)
        results[test_case.id] = result

    # Print summary
    print("\n" + "="*60)
    print("CALIBRATION SUMMARY")
    print("="*60)

    passing = sum(1 for r in results.values() if r.passing)
    total = len(results)

    print(f"\nOverall: {passing}/{total} test cases passing")
    print("\nBy test case:")
    for case_id, result in results.items():
        status = "✅ PASS" if result.passing else "❌ FAIL"
        print(f"  {case_id}: {result.overall_score:.1f}/100 {status}")

    return results


def score_existing_narrative(narrative_path: Path, deal_type: str = "acquisition") -> RubricResult:
    """Score an existing narrative JSON file."""
    with open(narrative_path, 'r') as f:
        narrative = json.load(f)

    deal_context = {
        "deal_type": deal_type,
        "target_name": narrative.get("company_name", "Target")
    }

    result = score_narrative(narrative, deal_context=deal_context)
    print(format_rubric_result(result))

    return result


# =============================================================================
# CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description="Run narrative calibration tests")
    parser.add_argument("--test-case", "-t", help="Specific test case ID (e.g., TC-01)")
    parser.add_argument("--all", "-a", action="store_true", help="Run all test cases")
    parser.add_argument("--use-llm", action="store_true", help="Use LLM for narrative generation")
    parser.add_argument("--score-file", "-f", help="Score an existing narrative JSON file")
    parser.add_argument("--deal-type", "-d", default="acquisition", help="Deal type for scoring existing file")

    args = parser.parse_args()

    if args.score_file:
        score_existing_narrative(Path(args.score_file), args.deal_type)
    elif args.all:
        run_all_calibrations(use_llm=args.use_llm)
    elif args.test_case:
        test_case = get_test_case(args.test_case)
        if test_case:
            run_calibration(test_case, use_llm=args.use_llm)
        else:
            print(f"Unknown test case: {args.test_case}")
            print(f"Available: {', '.join(tc.id for tc in get_all_test_cases())}")
    else:
        # Default: run TC-01 as quick test
        print("No arguments provided. Running TC-01 as quick test.")
        print("Use --all to run all test cases, or --help for options.")
        test_case = get_test_case("TC-01")
        if test_case:
            run_calibration(test_case, use_llm=args.use_llm)


if __name__ == "__main__":
    main()
