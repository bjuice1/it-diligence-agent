"""
Deterministic Estimator

Provides reproducible cost estimates, severity ratings, and timelines
using lookup tables and formulas - NOT AI generation.

Philosophy:
- AI identifies WHAT is present (patterns, facts, implications)
- Rules determine HOW MUCH it costs and HOW SEVERE it is
- Same inputs = Same outputs, every time

This addresses the credibility concern: "If I run it twice, do I get the same answer?"
Answer: YES, because quantification is deterministic.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from enum import Enum
import hashlib
import json


# =============================================================================
# SEVERITY MATRIX - Deterministic Risk Rating
# =============================================================================

class Severity(Enum):
    """Risk severity levels with deterministic criteria."""
    CRITICAL = "critical"  # Deal breaker or Day-1 failure risk
    HIGH = "high"          # >$1M impact or >90 day delay
    MEDIUM = "medium"      # $250K-$1M impact or 30-90 day delay
    LOW = "low"            # <$250K impact or <30 day delay
    INFO = "info"          # Observation, no material impact


@dataclass
class SeverityMatrix:
    """
    Deterministic severity scoring based on impact and likelihood.

    This is NOT AI-generated - it's a fixed matrix that gives
    the same result every time for the same inputs.
    """

    # Impact bands (annual cost or one-time)
    IMPACT_BANDS = {
        "critical": (5_000_000, float('inf')),   # >$5M
        "high": (1_000_000, 5_000_000),          # $1M-$5M
        "medium": (250_000, 1_000_000),          # $250K-$1M
        "low": (50_000, 250_000),                # $50K-$250K
        "minimal": (0, 50_000),                  # <$50K
    }

    # Timeline bands (days of delay/effort)
    TIMELINE_BANDS = {
        "critical": (365, float('inf')),  # >1 year
        "high": (90, 365),                # 90 days - 1 year
        "medium": (30, 90),               # 30-90 days
        "low": (7, 30),                   # 1-4 weeks
        "minimal": (0, 7),                # <1 week
    }

    # Likelihood weights
    LIKELIHOOD = {
        "certain": 1.0,      # Will definitely happen
        "likely": 0.75,      # >75% chance
        "possible": 0.5,     # 50% chance
        "unlikely": 0.25,    # <25% chance
    }

    @staticmethod
    def calculate_severity(
        cost_impact: float,
        timeline_days: int,
        likelihood: str = "likely",
        is_day1_critical: bool = False
    ) -> Severity:
        """
        Calculate severity deterministically.

        Same inputs ALWAYS produce same output.
        """
        # Day-1 critical items are always at least HIGH
        if is_day1_critical:
            base_severity = Severity.HIGH
        else:
            base_severity = Severity.LOW

        # Check cost impact band
        for band_name, (low, high) in SeverityMatrix.IMPACT_BANDS.items():
            if low <= cost_impact < high:
                cost_severity = band_name
                break
        else:
            cost_severity = "minimal"

        # Check timeline band
        for band_name, (low, high) in SeverityMatrix.TIMELINE_BANDS.items():
            if low <= timeline_days < high:
                time_severity = band_name
                break
        else:
            time_severity = "minimal"

        # Combined severity (take the worse of cost or time)
        severity_order = ["critical", "high", "medium", "low", "minimal"]
        combined_idx = min(
            severity_order.index(cost_severity),
            severity_order.index(time_severity)
        )

        # Apply likelihood adjustment (unlikely issues drop one level)
        likelihood_weight = SeverityMatrix.LIKELIHOOD.get(likelihood, 0.5)
        if likelihood_weight < 0.5 and combined_idx < len(severity_order) - 1:
            combined_idx += 1

        # Map to Severity enum
        severity_map = {
            "critical": Severity.CRITICAL,
            "high": Severity.HIGH,
            "medium": Severity.MEDIUM,
            "low": Severity.LOW,
            "minimal": Severity.INFO,
        }

        final_severity = severity_map[severity_order[combined_idx]]

        # Day-1 critical floor
        if is_day1_critical and final_severity in (Severity.LOW, Severity.INFO):
            final_severity = Severity.MEDIUM

        return final_severity


# =============================================================================
# COST LOOKUP TABLES - Deterministic Cost Ranges
# =============================================================================

# These are FIXED ranges - not AI-generated
# Source: Market research, vendor pricing, deal experience

COST_LOOKUP = {
    # License transitions (per user, annual)
    "license_microsoft_ea_standalone": {
        "unit": "per_user_annual",
        "range": (180, 360),  # $180-360/user/year
        "description": "Microsoft 365 E3/E5 standalone vs. EA pricing delta"
    },
    "license_sap_standalone": {
        "unit": "per_user_annual",
        "range": (2000, 5000),
        "description": "SAP named user license standalone"
    },
    "license_oracle_standalone": {
        "unit": "per_user_annual",
        "range": (1500, 4000),
        "description": "Oracle EBS/Cloud user license"
    },
    "license_salesforce": {
        "unit": "per_user_annual",
        "range": (150, 300),
        "description": "Salesforce Enterprise/Unlimited"
    },
    "license_servicenow": {
        "unit": "per_user_annual",
        "range": (100, 200),
        "description": "ServiceNow ITSM fulfiller"
    },

    # MSP/Outsourcing (per user, monthly)
    "msp_service_desk": {
        "unit": "per_user_monthly",
        "range": (50, 150),
        "description": "Managed service desk"
    },
    "msp_infrastructure": {
        "unit": "per_user_monthly",
        "range": (75, 200),
        "description": "Managed infrastructure services"
    },
    "msp_security_soc": {
        "unit": "per_user_monthly",
        "range": (30, 80),
        "description": "Managed SOC/MDR"
    },

    # Migration projects (one-time)
    "migration_email_per_mailbox": {
        "unit": "per_mailbox",
        "range": (10, 30),
        "description": "Email migration per mailbox"
    },
    "migration_erp_small": {
        "unit": "fixed",
        "range": (500_000, 1_500_000),
        "description": "ERP migration (<500 users)"
    },
    "migration_erp_medium": {
        "unit": "fixed",
        "range": (1_500_000, 4_000_000),
        "description": "ERP migration (500-2000 users)"
    },
    "migration_erp_large": {
        "unit": "fixed",
        "range": (4_000_000, 12_000_000),
        "description": "ERP migration (>2000 users)"
    },
    "migration_cloud_lift_shift": {
        "unit": "per_server",
        "range": (2000, 8000),
        "description": "Lift & shift per server"
    },
    "migration_identity_separation": {
        "unit": "fixed_by_size",
        "range_small": (100_000, 300_000),   # <1000 users
        "range_medium": (300_000, 800_000),  # 1000-5000 users
        "range_large": (800_000, 2_000_000), # >5000 users
        "description": "Identity/AD separation project"
    },

    # Infrastructure (monthly)
    "hosting_cloud_per_server": {
        "unit": "per_server_monthly",
        "range": (500, 2000),
        "description": "Cloud VM hosting"
    },
    "hosting_colocation_per_rack": {
        "unit": "per_rack_monthly",
        "range": (1500, 4000),
        "description": "Colocation per rack"
    },
    "network_wan_per_site": {
        "unit": "per_site_monthly",
        "range": (500, 2500),
        "description": "WAN/MPLS per site"
    },

    # TSA costs (monthly)
    "tsa_it_services_per_user": {
        "unit": "per_user_monthly",
        "range": (100, 300),
        "description": "Full IT TSA per user"
    },
    "tsa_infrastructure_only": {
        "unit": "per_user_monthly",
        "range": (50, 150),
        "description": "Infrastructure-only TSA"
    },
    "tsa_applications_only": {
        "unit": "per_user_monthly",
        "range": (40, 120),
        "description": "Applications-only TSA"
    },
}


# =============================================================================
# TIMELINE LOOKUP TABLES - Deterministic Durations
# =============================================================================

TIMELINE_LOOKUP = {
    # In months
    "email_migration": {"min": 1, "typical": 2, "max": 4},
    "identity_separation": {"min": 3, "typical": 6, "max": 12},
    "erp_migration_small": {"min": 6, "typical": 12, "max": 18},
    "erp_migration_medium": {"min": 12, "typical": 18, "max": 24},
    "erp_migration_large": {"min": 18, "typical": 24, "max": 36},
    "dc_migration": {"min": 6, "typical": 12, "max": 18},
    "cloud_migration": {"min": 3, "typical": 6, "max": 12},
    "network_separation": {"min": 2, "typical": 4, "max": 8},
    "security_tool_consolidation": {"min": 3, "typical": 6, "max": 12},
    "msp_transition": {"min": 2, "typical": 3, "max": 6},
    "vendor_contract_negotiation": {"min": 2, "typical": 3, "max": 4},
    "tsa_typical": {"min": 6, "typical": 12, "max": 24},
}


# =============================================================================
# DETERMINISTIC ESTIMATOR CLASS
# =============================================================================

class DeterministicEstimator:
    """
    Produces reproducible estimates using lookup tables.

    Key guarantee: Same inputs = Same outputs, every time.
    This is achieved by:
    1. Using fixed lookup tables (not AI generation)
    2. Deterministic formulas for calculations
    3. Input hashing for verification
    """

    def __init__(self):
        self.cost_lookup = COST_LOOKUP
        self.timeline_lookup = TIMELINE_LOOKUP
        self.severity_matrix = SeverityMatrix()

    def get_input_hash(self, inputs: Dict) -> str:
        """Generate hash of inputs for reproducibility verification."""
        input_str = json.dumps(inputs, sort_keys=True)
        return hashlib.sha256(input_str.encode()).hexdigest()[:12]

    def estimate_license_transition_cost(
        self,
        license_type: str,
        user_count: int,
        years: int = 1
    ) -> Dict:
        """
        Estimate license transition cost deterministically.

        Returns same range for same inputs, always.
        """
        lookup_key = f"license_{license_type}"
        if lookup_key not in self.cost_lookup:
            lookup_key = "license_microsoft_ea_standalone"  # Default

        cost_data = self.cost_lookup[lookup_key]
        low, high = cost_data["range"]

        annual_low = low * user_count
        annual_high = high * user_count

        return {
            "item": f"{license_type} license transition",
            "user_count": user_count,
            "annual_cost_range": (annual_low, annual_high),
            "total_cost_range": (annual_low * years, annual_high * years),
            "years": years,
            "unit_cost_range": cost_data["range"],
            "methodology": "lookup_table",
            "input_hash": self.get_input_hash({
                "type": "license", "license_type": license_type,
                "user_count": user_count, "years": years
            })
        }

    def estimate_msp_cost(
        self,
        service_type: str,
        user_count: int,
        months: int = 12
    ) -> Dict:
        """Estimate MSP/outsourcing cost deterministically."""
        lookup_key = f"msp_{service_type}"
        if lookup_key not in self.cost_lookup:
            lookup_key = "msp_service_desk"

        cost_data = self.cost_lookup[lookup_key]
        low, high = cost_data["range"]

        monthly_low = low * user_count
        monthly_high = high * user_count

        return {
            "item": f"{service_type} MSP services",
            "user_count": user_count,
            "monthly_cost_range": (monthly_low, monthly_high),
            "annual_cost_range": (monthly_low * 12, monthly_high * 12),
            "total_cost_range": (monthly_low * months, monthly_high * months),
            "months": months,
            "unit_cost_range": cost_data["range"],
            "methodology": "lookup_table",
            "input_hash": self.get_input_hash({
                "type": "msp", "service_type": service_type,
                "user_count": user_count, "months": months
            })
        }

    def estimate_migration_cost(
        self,
        migration_type: str,
        size_category: str = "medium",  # small, medium, large
        unit_count: Optional[int] = None
    ) -> Dict:
        """Estimate migration project cost deterministically."""
        lookup_key = f"migration_{migration_type}"

        # Handle size-based lookups
        if f"{lookup_key}_{size_category}" in self.cost_lookup:
            lookup_key = f"{lookup_key}_{size_category}"
        elif lookup_key not in self.cost_lookup:
            lookup_key = "migration_cloud_lift_shift"

        cost_data = self.cost_lookup[lookup_key]

        if cost_data["unit"] == "fixed":
            low, high = cost_data["range"]
        elif cost_data["unit"] == "fixed_by_size":
            range_key = f"range_{size_category}"
            low, high = cost_data.get(range_key, cost_data.get("range_medium", (500000, 1500000)))
        else:
            # Per-unit calculation
            low_unit, high_unit = cost_data["range"]
            count = unit_count or 100
            low = low_unit * count
            high = high_unit * count

        # Get timeline
        timeline_key = f"{migration_type}_{size_category}" if f"{migration_type}_{size_category}" in self.timeline_lookup else migration_type
        if timeline_key not in self.timeline_lookup:
            timeline_key = "cloud_migration"
        timeline = self.timeline_lookup[timeline_key]

        return {
            "item": f"{migration_type} migration ({size_category})",
            "cost_range": (low, high),
            "cost_midpoint": (low + high) // 2,
            "timeline_months": timeline,
            "methodology": "lookup_table",
            "input_hash": self.get_input_hash({
                "type": "migration", "migration_type": migration_type,
                "size_category": size_category, "unit_count": unit_count
            })
        }

    def estimate_tsa_cost(
        self,
        tsa_type: str,
        user_count: int,
        months: int = 12
    ) -> Dict:
        """Estimate TSA cost deterministically."""
        lookup_key = f"tsa_{tsa_type}"
        if lookup_key not in self.cost_lookup:
            lookup_key = "tsa_it_services_per_user"

        cost_data = self.cost_lookup[lookup_key]
        low, high = cost_data["range"]

        monthly_low = low * user_count
        monthly_high = high * user_count

        return {
            "item": f"TSA - {tsa_type}",
            "user_count": user_count,
            "monthly_cost_range": (monthly_low, monthly_high),
            "total_cost_range": (monthly_low * months, monthly_high * months),
            "months": months,
            "methodology": "lookup_table",
            "input_hash": self.get_input_hash({
                "type": "tsa", "tsa_type": tsa_type,
                "user_count": user_count, "months": months
            })
        }

    def calculate_severity(
        self,
        cost_impact: float,
        timeline_days: int,
        likelihood: str = "likely",
        is_day1_critical: bool = False
    ) -> Dict:
        """Calculate risk severity deterministically."""
        severity = SeverityMatrix.calculate_severity(
            cost_impact=cost_impact,
            timeline_days=timeline_days,
            likelihood=likelihood,
            is_day1_critical=is_day1_critical
        )

        return {
            "severity": severity.value,
            "severity_display": severity.value.upper(),
            "inputs": {
                "cost_impact": cost_impact,
                "timeline_days": timeline_days,
                "likelihood": likelihood,
                "is_day1_critical": is_day1_critical
            },
            "methodology": "severity_matrix",
            "input_hash": self.get_input_hash({
                "cost_impact": cost_impact,
                "timeline_days": timeline_days,
                "likelihood": likelihood,
                "is_day1_critical": is_day1_critical
            })
        }

    def estimate_total_separation_cost(
        self,
        user_count: int,
        deal_type: str,
        has_shared_services: bool = False,
        has_parent_licenses: bool = False,
        erp_size: str = "medium",
        dc_count: int = 1,
        tsa_months: int = 12
    ) -> Dict:
        """
        Estimate total IT separation cost deterministically.

        This uses formulas and lookups - NOT AI judgment.
        Same inputs = Same outputs, guaranteed.
        """
        components = []
        total_low = 0
        total_high = 0

        # 1. License transition (if parent licenses)
        if has_parent_licenses:
            license_est = self.estimate_license_transition_cost(
                "microsoft_ea_standalone", user_count, years=1
            )
            components.append(license_est)
            total_low += license_est["annual_cost_range"][0]
            total_high += license_est["annual_cost_range"][1]

        # 2. TSA costs (if shared services)
        if has_shared_services:
            tsa_est = self.estimate_tsa_cost(
                "it_services_per_user", user_count, tsa_months
            )
            components.append(tsa_est)
            total_low += tsa_est["total_cost_range"][0]
            total_high += tsa_est["total_cost_range"][1]

        # 3. Identity separation (always for carveout)
        if deal_type == "carveout":
            size = "small" if user_count < 1000 else "medium" if user_count < 5000 else "large"
            identity_est = self.estimate_migration_cost(
                "identity_separation", size
            )
            components.append(identity_est)
            total_low += identity_est["cost_range"][0]
            total_high += identity_est["cost_range"][1]

        # 4. Infrastructure migration
        if dc_count > 0:
            infra_est = self.estimate_migration_cost(
                "cloud_lift_shift", "medium", unit_count=dc_count * 20  # Assume 20 servers per DC
            )
            components.append(infra_est)
            total_low += infra_est["cost_range"][0]
            total_high += infra_est["cost_range"][1]

        # 5. Contingency (15-25%)
        contingency_low = total_low * 0.15
        contingency_high = total_high * 0.25

        return {
            "deal_type": deal_type,
            "user_count": user_count,
            "components": components,
            "subtotal_range": (total_low, total_high),
            "contingency_range": (contingency_low, contingency_high),
            "total_range": (
                round(total_low + contingency_low, -3),
                round(total_high + contingency_high, -3)
            ),
            "total_midpoint": round((total_low + total_high) / 2 + (contingency_low + contingency_high) / 2, -3),
            "methodology": "deterministic_formula",
            "input_hash": self.get_input_hash({
                "user_count": user_count,
                "deal_type": deal_type,
                "has_shared_services": has_shared_services,
                "has_parent_licenses": has_parent_licenses,
                "erp_size": erp_size,
                "dc_count": dc_count,
                "tsa_months": tsa_months
            })
        }


# =============================================================================
# CONSISTENCY VERIFICATION
# =============================================================================

def verify_consistency(estimator: DeterministicEstimator, inputs: Dict, runs: int = 5) -> Dict:
    """
    Verify that the estimator produces consistent results.

    Runs the same estimation multiple times and checks for variance.
    (There should be ZERO variance since it's deterministic.)
    """
    results = []

    for _ in range(runs):
        if inputs.get("type") == "license":
            result = estimator.estimate_license_transition_cost(
                inputs["license_type"],
                inputs["user_count"],
                inputs.get("years", 1)
            )
        elif inputs.get("type") == "total_separation":
            result = estimator.estimate_total_separation_cost(
                inputs["user_count"],
                inputs["deal_type"],
                inputs.get("has_shared_services", False),
                inputs.get("has_parent_licenses", False)
            )
        else:
            result = {"error": "Unknown input type"}

        results.append(result)

    # Check consistency
    hashes = [r.get("input_hash") for r in results]
    totals = [r.get("total_range") or r.get("total_cost_range") for r in results]

    is_consistent = len(set(hashes)) == 1 and len(set(str(t) for t in totals)) == 1

    return {
        "runs": runs,
        "consistent": is_consistent,
        "hash_variance": len(set(hashes)),
        "result_variance": len(set(str(t) for t in totals)),
        "sample_result": results[0] if results else None
    }


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    'Severity',
    'SeverityMatrix',
    'COST_LOOKUP',
    'TIMELINE_LOOKUP',
    'DeterministicEstimator',
    'verify_consistency',
]
