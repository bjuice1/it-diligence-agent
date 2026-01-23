"""
Benchmark Generator

Generates relative/directional benchmark statements from inventory data.
CRITICAL: Never fabricates external statistics or industry benchmarks.

All statements use:
- Relative language ("suggests", "indicates", "appears")
- Internal data only (from inventory)
- Labeled inferences
- M&A implications

Output: 4-6 benchmark statements per narrative
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


# =============================================================================
# BENCHMARK PATTERN DEFINITIONS
# =============================================================================

class BenchmarkType(Enum):
    """Types of benchmark statements."""
    CONCENTRATION = "concentration"
    OUTSOURCING = "outsourcing"
    RATIO = "ratio"
    POSTURE = "posture"
    MATURITY = "maturity"
    COST = "cost"


@dataclass
class BenchmarkPattern:
    """A pattern for generating benchmark statements."""
    pattern_type: BenchmarkType
    template: str
    example: str
    required_data: List[str]
    mna_relevance: str


BENCHMARK_PATTERNS = {
    BenchmarkType.CONCENTRATION: BenchmarkPattern(
        pattern_type=BenchmarkType.CONCENTRATION,
        template="Relative concentration in {area} ({pct:.0f}% of {base}) suggests {implication}",
        example="Relative concentration in Applications (35% of IT headcount) suggests a project-heavy operating model",
        required_data=["area", "pct", "base"],
        mna_relevance="Concentration signals where integration/separation complexity lies"
    ),

    BenchmarkType.OUTSOURCING: BenchmarkPattern(
        pattern_type=BenchmarkType.OUTSOURCING,
        template="Outsourcing is {level} in {areas} ({pct:.0f}%), which implies {implication}",
        example="Outsourcing is concentrated in Infrastructure and Service Desk (38-43%), implying potential TSA complexity",
        required_data=["level", "areas", "pct"],
        mna_relevance="Outsourcing concentration affects TSA scope and separation complexity"
    ),

    BenchmarkType.RATIO: BenchmarkPattern(
        pattern_type=BenchmarkType.RATIO,
        template="The {role_a}-to-{role_b} ratio of {ratio} indicates {implication}",
        example="The IT-to-employee ratio of 1:85 indicates a lean IT organization",
        required_data=["role_a", "role_b", "ratio"],
        mna_relevance="Ratios signal operating model and potential capacity constraints"
    ),

    BenchmarkType.POSTURE: BenchmarkPattern(
        pattern_type=BenchmarkType.POSTURE,
        template="The organization appears {posture} based on {evidence}",
        example="The organization appears run-heavy (70% ops, 30% projects) based on team composition",
        required_data=["posture", "evidence"],
        mna_relevance="Operating posture affects integration approach and synergy realization"
    ),

    BenchmarkType.MATURITY: BenchmarkPattern(
        pattern_type=BenchmarkType.MATURITY,
        template="Inference: {area} maturity appears {level} given {evidence}",
        example="Inference: Security maturity appears moderate given MFA at 62% and no PAM solution",
        required_data=["area", "level", "evidence"],
        mna_relevance="Maturity gaps signal investment needs post-close"
    ),

    BenchmarkType.COST: BenchmarkPattern(
        pattern_type=BenchmarkType.COST,
        template="{cost_area} represents {pct:.0f}% of IT spend, suggesting {implication}",
        example="External labor represents 45% of IT spend, suggesting potential cost optimization opportunity",
        required_data=["cost_area", "pct"],
        mna_relevance="Cost distribution signals synergy opportunities and TSA pricing"
    )
}


# =============================================================================
# SAFE LANGUAGE DEFINITIONS
# =============================================================================

# Safe relative language (use these)
SAFE_LANGUAGE = {
    "suggests": "Use when drawing reasonable conclusions from data",
    "indicates": "Use when data points toward a conclusion",
    "appears": "Use when making observations with some uncertainty",
    "implies": "Use when logical inference is being made",
    "signals": "Use when data serves as an indicator",
    "is consistent with": "Use when data aligns with a pattern",
    "is notable": "Use when highlighting something worth attention",
    "is concentrated": "Use when describing distribution skew"
}

# Unsafe absolute language (never use these)
UNSAFE_LANGUAGE = [
    "industry average",
    "best practice",
    "benchmark",
    "standard",
    "typical",
    "normal",
    "should be",
    "compared to peers",
    "market rate",
    "industry standard"
]

# Posture descriptions (relative, not absolute)
POSTURE_DESCRIPTORS = {
    "run_heavy": {
        "threshold": 0.65,  # >65% run-focused
        "description": "run/operate-heavy",
        "implication": "steady-state focus, may lack change capacity"
    },
    "change_heavy": {
        "threshold": 0.45,  # >45% change-focused
        "description": "change/project-heavy",
        "implication": "transformation mode, project-oriented"
    },
    "balanced": {
        "range": (0.35, 0.65),
        "description": "balanced run/change",
        "implication": "moderate project capacity alongside operations"
    },
    "lean": {
        "ratio_threshold": 100,  # IT:employee ratio > 1:100
        "description": "lean",
        "implication": "efficiency-focused, may have capacity constraints"
    },
    "well_resourced": {
        "ratio_threshold": 50,  # IT:employee ratio < 1:50
        "description": "well-resourced",
        "implication": "capacity for change, potentially over-resourced"
    }
}

# Concentration thresholds (relative to total)
CONCENTRATION_THRESHOLDS = {
    "low": (0, 0.15),
    "moderate": (0.15, 0.30),
    "notable": (0.30, 0.45),
    "high": (0.45, 0.60),
    "very_high": (0.60, 1.0)
}

# Outsourcing level descriptions
OUTSOURCING_LEVELS = {
    "minimal": (0, 0.15),
    "moderate": (0.15, 0.30),
    "substantial": (0.30, 0.50),
    "heavy": (0.50, 0.75),
    "extensive": (0.75, 1.0)
}


# =============================================================================
# INVENTORY ANALYSIS FUNCTIONS
# =============================================================================

def analyze_team_concentration(inventory: Dict) -> List[Dict]:
    """
    Analyze headcount/cost concentration by team.

    Returns list of concentration findings with percentages and implications.
    """
    concentrations = []

    # Extract team data
    teams = inventory.get("teams", {})
    total_headcount = sum(t.get("headcount", 0) for t in teams.values())
    total_cost = sum(t.get("cost", 0) for t in teams.values())

    if total_headcount == 0:
        return concentrations

    for team_name, team_data in teams.items():
        headcount = team_data.get("headcount", 0)
        cost = team_data.get("cost", 0)

        if headcount > 0:
            hc_pct = headcount / total_headcount
            level = _get_concentration_level(hc_pct)

            if level in ["notable", "high", "very_high"]:
                concentrations.append({
                    "area": team_name,
                    "pct": hc_pct * 100,
                    "base": "IT headcount",
                    "level": level,
                    "implication": _get_concentration_implication(team_name, hc_pct)
                })

        if cost > 0 and total_cost > 0:
            cost_pct = cost / total_cost
            level = _get_concentration_level(cost_pct)

            if level in ["notable", "high", "very_high"]:
                concentrations.append({
                    "area": team_name,
                    "pct": cost_pct * 100,
                    "base": "IT cost",
                    "level": level,
                    "implication": _get_concentration_implication(team_name, cost_pct, is_cost=True)
                })

    return concentrations


def analyze_outsourcing(inventory: Dict) -> Optional[Dict]:
    """
    Analyze outsourcing levels across functions.

    Returns outsourcing finding if notable.
    """
    teams = inventory.get("teams", {})
    total_headcount = sum(t.get("headcount", 0) for t in teams.values())

    if total_headcount == 0:
        return None

    # Calculate outsourced headcount
    outsourced_count = 0
    outsourced_areas = []

    for team_name, team_data in teams.items():
        contractors = team_data.get("contractors", 0)
        outsourced = team_data.get("outsourced", 0)
        team_total = team_data.get("headcount", 0)

        external = contractors + outsourced
        if external > 0 and team_total > 0:
            team_outsource_pct = external / team_total
            if team_outsource_pct > 0.3:  # >30% outsourced
                outsourced_areas.append(team_name)
            outsourced_count += external

    overall_pct = outsourced_count / total_headcount if total_headcount > 0 else 0
    level = _get_outsourcing_level(overall_pct)

    if level in ["substantial", "heavy", "extensive"] or outsourced_areas:
        return {
            "level": level,
            "pct": overall_pct * 100,
            "areas": outsourced_areas if outsourced_areas else ["various functions"],
            "implication": _get_outsourcing_implication(overall_pct, outsourced_areas)
        }

    return None


def analyze_ratios(inventory: Dict) -> List[Dict]:
    """
    Analyze key ratios (IT:employee, manager:IC, etc.).

    Returns list of ratio findings.
    """
    ratios = []

    it_headcount = inventory.get("total_it_headcount", 0)
    total_employees = inventory.get("total_company_employees", 0)

    # IT to employee ratio
    if it_headcount > 0 and total_employees > 0:
        ratio = total_employees / it_headcount
        ratios.append({
            "role_a": "IT",
            "role_b": "employee",
            "ratio": f"1:{ratio:.0f}",
            "ratio_value": ratio,
            "implication": _get_ratio_implication("it_employee", ratio)
        })

    # Manager to IC ratio (if available)
    teams = inventory.get("teams", {})
    total_managers = sum(t.get("managers", 0) for t in teams.values())
    total_ics = it_headcount - total_managers

    if total_managers > 0 and total_ics > 0:
        mgr_ratio = total_ics / total_managers
        ratios.append({
            "role_a": "IC",
            "role_b": "manager",
            "ratio": f"{mgr_ratio:.1f}:1",
            "ratio_value": mgr_ratio,
            "implication": _get_ratio_implication("manager_ic", mgr_ratio)
        })

    return ratios


def analyze_posture(inventory: Dict) -> Optional[Dict]:
    """
    Analyze operating posture (run vs change, lean vs resourced).

    Returns posture finding.
    """
    teams = inventory.get("teams", {})

    # Categorize teams as run vs change
    run_teams = ["infrastructure", "operations", "service_desk", "support", "network"]
    change_teams = ["applications", "development", "pmo", "projects", "architecture"]

    run_headcount = 0
    change_headcount = 0
    total_headcount = 0

    for team_name, team_data in teams.items():
        hc = team_data.get("headcount", 0)
        total_headcount += hc

        team_lower = team_name.lower()
        if any(r in team_lower for r in run_teams):
            run_headcount += hc
        elif any(c in team_lower for c in change_teams):
            change_headcount += hc

    if total_headcount == 0:
        return None

    run_pct = run_headcount / total_headcount
    change_pct = change_headcount / total_headcount

    # Determine posture
    if run_pct > POSTURE_DESCRIPTORS["run_heavy"]["threshold"]:
        posture = "run/operate-heavy"
        evidence = f"{run_pct*100:.0f}% in run/ops teams, {change_pct*100:.0f}% in change/project teams"
        implication = "steady-state operations focus with limited project/change capacity"
    elif change_pct > POSTURE_DESCRIPTORS["change_heavy"]["threshold"]:
        posture = "change/project-heavy"
        evidence = f"{change_pct*100:.0f}% in change/project teams, {run_pct*100:.0f}% in run/ops teams"
        implication = "significant project activity, potentially in transformation mode"
    else:
        posture = "balanced"
        evidence = f"roughly {run_pct*100:.0f}% run / {change_pct*100:.0f}% change split"
        implication = "moderate capacity for both operations and projects"

    return {
        "posture": posture,
        "evidence": evidence,
        "implication": implication,
        "run_pct": run_pct * 100,
        "change_pct": change_pct * 100
    }


def analyze_maturity_signals(inventory: Dict, findings: Dict) -> List[Dict]:
    """
    Analyze maturity signals from inventory and findings.

    Returns list of maturity observations.
    """
    maturity_signals = []

    # Security maturity signals
    security_data = inventory.get("security", {})
    mfa_coverage = security_data.get("mfa_coverage_pct", 0)
    has_pam = security_data.get("has_pam", False)
    has_siem = security_data.get("has_siem", False)

    if mfa_coverage > 0 or has_pam is not None:
        evidence_parts = []
        if mfa_coverage > 0:
            evidence_parts.append(f"MFA at {mfa_coverage:.0f}%")
        if has_pam is False:
            evidence_parts.append("no PAM solution")
        elif has_pam is True:
            evidence_parts.append("PAM in place")
        if has_siem is False:
            evidence_parts.append("no centralized SIEM")
        elif has_siem is True:
            evidence_parts.append("SIEM deployed")

        if evidence_parts:
            level = "moderate" if mfa_coverage > 50 else "developing"
            if has_pam and has_siem and mfa_coverage > 80:
                level = "mature"

            maturity_signals.append({
                "area": "Security",
                "level": level,
                "evidence": ", ".join(evidence_parts)
            })

    # DR/BC maturity signals
    dr_data = inventory.get("disaster_recovery", {})
    has_dr_plan = dr_data.get("has_plan", None)
    dr_tested = dr_data.get("tested_annually", None)

    if has_dr_plan is not None:
        evidence_parts = []
        if has_dr_plan:
            evidence_parts.append("DR plan documented")
        else:
            evidence_parts.append("no formal DR plan")
        if dr_tested is True:
            evidence_parts.append("tested annually")
        elif dr_tested is False:
            evidence_parts.append("not regularly tested")

        if evidence_parts:
            level = "developing"
            if has_dr_plan and dr_tested:
                level = "mature"
            elif not has_dr_plan:
                level = "limited"

            maturity_signals.append({
                "area": "Disaster Recovery",
                "level": level,
                "evidence": ", ".join(evidence_parts)
            })

    return maturity_signals


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _get_concentration_level(pct: float) -> str:
    """Get concentration level descriptor."""
    for level, (low, high) in CONCENTRATION_THRESHOLDS.items():
        if low <= pct < high:
            return level
    return "moderate"


def _get_outsourcing_level(pct: float) -> str:
    """Get outsourcing level descriptor."""
    for level, (low, high) in OUTSOURCING_LEVELS.items():
        if low <= pct < high:
            return level
    return "moderate"


def _get_concentration_implication(area: str, pct: float, is_cost: bool = False) -> str:
    """Get implication for concentration finding."""
    area_lower = area.lower()

    if "application" in area_lower:
        if is_cost:
            return "significant investment in application portfolio"
        return "project-heavy operating model with application focus"

    elif "infrastructure" in area_lower:
        if is_cost:
            return "infrastructure-driven cost structure, potential consolidation opportunity"
        return "infrastructure-heavy model, may indicate technical debt or complex environment"

    elif "security" in area_lower or "cyber" in area_lower:
        return "security-focused investment, may reflect regulatory requirements or prior incidents"

    elif "service" in area_lower or "support" in area_lower:
        return "support-heavy model, may indicate user base complexity or legacy applications"

    else:
        base = "cost" if is_cost else "headcount"
        return f"notable {base} concentration warranting further analysis"


def _get_outsourcing_implication(pct: float, areas: List[str]) -> str:
    """Get implication for outsourcing finding."""
    if pct > 0.5:
        return "significant external dependency, potential TSA complexity and knowledge risk"
    elif pct > 0.3:
        return "moderate external reliance, TSA planning will be important"
    else:
        return "external resources in specific areas may require TSA consideration"


def _get_ratio_implication(ratio_type: str, value: float) -> str:
    """Get implication for ratio finding."""
    if ratio_type == "it_employee":
        if value > 100:
            return "a lean IT organization, may have capacity constraints"
        elif value > 75:
            return "moderate IT staffing levels"
        elif value > 50:
            return "well-resourced IT relative to company size"
        else:
            return "heavily invested IT organization relative to company size"

    elif ratio_type == "manager_ic":
        if value > 8:
            return "flat management structure with wide spans of control"
        elif value > 5:
            return "moderate management layering"
        else:
            return "management-heavy structure, potential efficiency opportunity"

    return "notable ratio warranting consideration"


# =============================================================================
# MAIN GENERATOR FUNCTION
# =============================================================================

def generate_benchmarks(
    inventory: Dict,
    findings: Optional[Dict] = None,
    deal_type: str = "acquisition",
    max_benchmarks: int = 6
) -> List[str]:
    """
    Generate 4-6 benchmark statements from inventory data.

    Args:
        inventory: Inventory data dict with teams, costs, etc.
        findings: Optional findings from reasoning agents
        deal_type: Deal type for M&A-relevant implications
        max_benchmarks: Maximum number of benchmarks to generate

    Returns:
        List of 4-6 benchmark statement strings
    """
    benchmarks = []
    findings = findings or {}

    # 1. Analyze concentration
    concentrations = analyze_team_concentration(inventory)
    for conc in concentrations[:2]:  # Max 2 concentration statements
        pattern = BENCHMARK_PATTERNS[BenchmarkType.CONCENTRATION]
        statement = pattern.template.format(
            area=conc["area"],
            pct=conc["pct"],
            base=conc["base"],
            implication=conc["implication"]
        )
        benchmarks.append(statement)

    # 2. Analyze outsourcing
    outsourcing = analyze_outsourcing(inventory)
    if outsourcing:
        pattern = BENCHMARK_PATTERNS[BenchmarkType.OUTSOURCING]
        statement = pattern.template.format(
            level=outsourcing["level"],
            areas=", ".join(outsourcing["areas"]),
            pct=outsourcing["pct"],
            implication=outsourcing["implication"]
        )
        benchmarks.append(statement)

    # 3. Analyze ratios
    ratios = analyze_ratios(inventory)
    for ratio in ratios[:1]:  # Max 1 ratio statement
        pattern = BENCHMARK_PATTERNS[BenchmarkType.RATIO]
        statement = pattern.template.format(
            role_a=ratio["role_a"],
            role_b=ratio["role_b"],
            ratio=ratio["ratio"],
            implication=ratio["implication"]
        )
        benchmarks.append(statement)

    # 4. Analyze posture
    posture = analyze_posture(inventory)
    if posture:
        pattern = BENCHMARK_PATTERNS[BenchmarkType.POSTURE]
        statement = pattern.template.format(
            posture=posture["posture"],
            evidence=posture["evidence"]
        )
        benchmarks.append(statement)

    # 5. Analyze maturity (if we need more statements)
    if len(benchmarks) < 4:
        maturity_signals = analyze_maturity_signals(inventory, findings)
        for signal in maturity_signals[:2]:
            pattern = BENCHMARK_PATTERNS[BenchmarkType.MATURITY]
            statement = pattern.template.format(
                area=signal["area"],
                level=signal["level"],
                evidence=signal["evidence"]
            )
            benchmarks.append(statement)

    # Ensure we have 4-6 statements
    if len(benchmarks) < 4:
        # Add a generic observation if we're short
        total_hc = inventory.get("total_it_headcount", 0)
        if total_hc > 0:
            benchmarks.append(
                f"Inference: The IT organization of {total_hc} staff warrants detailed "
                f"assessment of Day-1 continuity and separation complexity"
            )

    # Trim to max
    return benchmarks[:max_benchmarks]


def validate_benchmark_safety(statement: str) -> Tuple[bool, Optional[str]]:
    """
    Validate that a benchmark statement is safe (no fabricated external data).

    Returns (is_safe, issue_description).
    """
    statement_lower = statement.lower()

    for unsafe_phrase in UNSAFE_LANGUAGE:
        if unsafe_phrase in statement_lower:
            return False, f"Contains unsafe language: '{unsafe_phrase}'"

    # Check for specific numbers that look like external benchmarks
    import re
    external_benchmark_pattern = r'industry|market|typical|average|benchmark|standard'
    if re.search(external_benchmark_pattern, statement_lower):
        return False, "May reference external benchmarks"

    return True, None


def get_benchmark_mna_context(benchmark_type: BenchmarkType, deal_type: str) -> str:
    """Get M&A-relevant context for a benchmark type and deal."""
    contexts = {
        "acquisition": {
            BenchmarkType.CONCENTRATION: "Concentration areas signal integration complexity and synergy potential",
            BenchmarkType.OUTSOURCING: "Outsourcing levels affect integration timeline and knowledge transfer",
            BenchmarkType.RATIO: "Ratios indicate operating model and headcount synergy potential",
            BenchmarkType.POSTURE: "Posture affects integration approach and change capacity",
            BenchmarkType.MATURITY: "Maturity gaps signal post-close investment requirements"
        },
        "carveout": {
            BenchmarkType.CONCENTRATION: "Concentration areas signal TSA scope and separation complexity",
            BenchmarkType.OUTSOURCING: "Outsourcing levels directly impact TSA requirements",
            BenchmarkType.RATIO: "Ratios indicate standalone viability and staffing needs",
            BenchmarkType.POSTURE: "Posture affects standalone capability and transition complexity",
            BenchmarkType.MATURITY: "Maturity gaps signal standalone investment requirements"
        },
        "divestiture": {
            BenchmarkType.CONCENTRATION: "Concentration areas signal separation complexity and stranded costs",
            BenchmarkType.OUTSOURCING: "Outsourcing levels affect TSA provision burden on RemainCo",
            BenchmarkType.RATIO: "Ratios indicate potential stranded overhead",
            BenchmarkType.POSTURE: "Posture affects clean separation feasibility",
            BenchmarkType.MATURITY: "Maturity gaps may affect sale positioning"
        }
    }

    deal_contexts = contexts.get(deal_type.lower(), contexts["acquisition"])
    return deal_contexts.get(benchmark_type, "Relevant for M&A assessment")


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Types and patterns
    'BenchmarkType',
    'BenchmarkPattern',
    'BENCHMARK_PATTERNS',
    # Language guides
    'SAFE_LANGUAGE',
    'UNSAFE_LANGUAGE',
    'POSTURE_DESCRIPTORS',
    'CONCENTRATION_THRESHOLDS',
    'OUTSOURCING_LEVELS',
    # Analysis functions
    'analyze_team_concentration',
    'analyze_outsourcing',
    'analyze_ratios',
    'analyze_posture',
    'analyze_maturity_signals',
    # Generator
    'generate_benchmarks',
    'validate_benchmark_safety',
    'get_benchmark_mna_context'
]
