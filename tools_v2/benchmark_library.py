"""
Benchmark Library for PE Reporting

Sourced benchmark data with citations - NO fake authority.
Every benchmark includes:
- Metric definition
- Industry context
- Company size context
- Low/typical/high ranges
- Source citation
- Year of data

Usage:
    benchmark = get_benchmark("it_pct_revenue", "software", "50-100M")
    if benchmark:
        print(f"Typical: {benchmark.typical}% ({benchmark.source})")
"""

import json
import logging
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


@dataclass
class BenchmarkData:
    """
    Sourced benchmark with citation.

    Every benchmark MUST have a source - no fake authority.
    If source is internal estimation, mark it as "Internal rule of thumb".
    """
    metric: str  # it_pct_revenue, cost_per_employee, app_count_per_100_employees, etc.
    industry: str  # software, manufacturing, healthcare, financial_services, retail, general
    company_size: str  # 0-50M, 50-100M, 100-500M, 500M+
    low: float
    typical: float
    high: float
    source: str  # "Gartner IT Key Metrics 2025" or "Internal rule of thumb"
    year: int
    unit: str = ""  # "%", "$", "count", "ratio"
    notes: str = ""  # Additional context

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> "BenchmarkData":
        return cls(**data)

    def format_range(self) -> str:
        """Format benchmark as readable range string."""
        if self.unit == "%":
            return f"{self.low:.1f}% - {self.high:.1f}% (typical: {self.typical:.1f}%)"
        elif self.unit == "$":
            return f"${self.low:,.0f} - ${self.high:,.0f} (typical: ${self.typical:,.0f})"
        else:
            return f"{self.low:.1f} - {self.high:.1f} (typical: {self.typical:.1f})"

    def format_citation(self) -> str:
        """Format benchmark with source citation."""
        return f"{self.format_range()} - {self.source} ({self.year})"

    def assess_value(self, value: float) -> str:
        """
        Assess a value against this benchmark.

        Returns: 'below_typical', 'typical', 'above_typical'
        """
        # Use 20% tolerance around typical for "typical" classification
        low_threshold = self.typical * 0.8
        high_threshold = self.typical * 1.2

        if value < low_threshold:
            return "below_typical"
        elif value > high_threshold:
            return "above_typical"
        else:
            return "typical"


# =============================================================================
# BENCHMARK LIBRARY DATA
# =============================================================================

# Organized by metric -> industry_size key
# Industry codes: software, manufacturing, healthcare, financial_services, retail, general
# Size codes: 0-50M, 50-100M, 100-500M, 500M+

BENCHMARK_LIBRARY: Dict[str, Dict[str, BenchmarkData]] = {
    # =========================================================================
    # IT Spending as % of Revenue
    # =========================================================================
    "it_pct_revenue": {
        "software_0-50M": BenchmarkData(
            metric="it_pct_revenue",
            industry="software",
            company_size="0-50M",
            low=5.0, typical=7.0, high=10.0,
            source="Gartner IT Key Metrics Data 2024",
            year=2024,
            unit="%",
            notes="Software companies typically invest more in IT as a core capability"
        ),
        "software_50-100M": BenchmarkData(
            metric="it_pct_revenue",
            industry="software",
            company_size="50-100M",
            low=4.5, typical=6.5, high=9.0,
            source="Gartner IT Key Metrics Data 2024",
            year=2024,
            unit="%"
        ),
        "software_100-500M": BenchmarkData(
            metric="it_pct_revenue",
            industry="software",
            company_size="100-500M",
            low=4.0, typical=5.5, high=8.0,
            source="Gartner IT Key Metrics Data 2024",
            year=2024,
            unit="%"
        ),
        "software_500M+": BenchmarkData(
            metric="it_pct_revenue",
            industry="software",
            company_size="500M+",
            low=3.5, typical=5.0, high=7.0,
            source="Gartner IT Key Metrics Data 2024",
            year=2024,
            unit="%"
        ),
        "manufacturing_0-50M": BenchmarkData(
            metric="it_pct_revenue",
            industry="manufacturing",
            company_size="0-50M",
            low=1.5, typical=2.5, high=4.0,
            source="Gartner IT Key Metrics Data 2024",
            year=2024,
            unit="%",
            notes="Manufacturing typically lower IT spend as % of revenue"
        ),
        "manufacturing_50-100M": BenchmarkData(
            metric="it_pct_revenue",
            industry="manufacturing",
            company_size="50-100M",
            low=1.5, typical=2.5, high=3.5,
            source="Gartner IT Key Metrics Data 2024",
            year=2024,
            unit="%"
        ),
        "manufacturing_100-500M": BenchmarkData(
            metric="it_pct_revenue",
            industry="manufacturing",
            company_size="100-500M",
            low=1.2, typical=2.0, high=3.0,
            source="Gartner IT Key Metrics Data 2024",
            year=2024,
            unit="%"
        ),
        "healthcare_50-100M": BenchmarkData(
            metric="it_pct_revenue",
            industry="healthcare",
            company_size="50-100M",
            low=3.0, typical=4.5, high=6.0,
            source="HIMSS Healthcare IT Survey 2024",
            year=2024,
            unit="%",
            notes="Healthcare IT spending driven by compliance and EHR requirements"
        ),
        "healthcare_100-500M": BenchmarkData(
            metric="it_pct_revenue",
            industry="healthcare",
            company_size="100-500M",
            low=2.5, typical=4.0, high=5.5,
            source="HIMSS Healthcare IT Survey 2024",
            year=2024,
            unit="%"
        ),
        "financial_services_50-100M": BenchmarkData(
            metric="it_pct_revenue",
            industry="financial_services",
            company_size="50-100M",
            low=5.0, typical=7.5, high=10.0,
            source="Deloitte Financial Services IT Survey 2024",
            year=2024,
            unit="%",
            notes="Financial services among highest IT spenders due to compliance and digital"
        ),
        "financial_services_100-500M": BenchmarkData(
            metric="it_pct_revenue",
            industry="financial_services",
            company_size="100-500M",
            low=4.5, typical=6.5, high=9.0,
            source="Deloitte Financial Services IT Survey 2024",
            year=2024,
            unit="%"
        ),
        "retail_50-100M": BenchmarkData(
            metric="it_pct_revenue",
            industry="retail",
            company_size="50-100M",
            low=1.5, typical=2.5, high=4.0,
            source="NRF Retail IT Spending Report 2024",
            year=2024,
            unit="%"
        ),
        "general_0-50M": BenchmarkData(
            metric="it_pct_revenue",
            industry="general",
            company_size="0-50M",
            low=2.5, typical=4.0, high=6.0,
            source="Internal rule of thumb (cross-industry average)",
            year=2024,
            unit="%",
            notes="General benchmark when industry-specific data unavailable"
        ),
        "general_50-100M": BenchmarkData(
            metric="it_pct_revenue",
            industry="general",
            company_size="50-100M",
            low=2.5, typical=3.5, high=5.5,
            source="Internal rule of thumb (cross-industry average)",
            year=2024,
            unit="%"
        ),
        "general_100-500M": BenchmarkData(
            metric="it_pct_revenue",
            industry="general",
            company_size="100-500M",
            low=2.0, typical=3.0, high=4.5,
            source="Internal rule of thumb (cross-industry average)",
            year=2024,
            unit="%"
        ),
        "general_500M+": BenchmarkData(
            metric="it_pct_revenue",
            industry="general",
            company_size="500M+",
            low=1.5, typical=2.5, high=4.0,
            source="Internal rule of thumb (cross-industry average)",
            year=2024,
            unit="%"
        ),
    },

    # =========================================================================
    # IT Cost per Employee
    # =========================================================================
    "cost_per_employee": {
        "software_50-100M": BenchmarkData(
            metric="cost_per_employee",
            industry="software",
            company_size="50-100M",
            low=12000, typical=18000, high=25000,
            source="Computer Economics IT Spending Report 2024",
            year=2024,
            unit="$",
            notes="Software companies have higher per-employee IT costs"
        ),
        "software_100-500M": BenchmarkData(
            metric="cost_per_employee",
            industry="software",
            company_size="100-500M",
            low=10000, typical=15000, high=22000,
            source="Computer Economics IT Spending Report 2024",
            year=2024,
            unit="$"
        ),
        "manufacturing_50-100M": BenchmarkData(
            metric="cost_per_employee",
            industry="manufacturing",
            company_size="50-100M",
            low=5000, typical=8000, high=12000,
            source="Computer Economics IT Spending Report 2024",
            year=2024,
            unit="$"
        ),
        "manufacturing_100-500M": BenchmarkData(
            metric="cost_per_employee",
            industry="manufacturing",
            company_size="100-500M",
            low=4500, typical=7000, high=10000,
            source="Computer Economics IT Spending Report 2024",
            year=2024,
            unit="$"
        ),
        "healthcare_50-100M": BenchmarkData(
            metric="cost_per_employee",
            industry="healthcare",
            company_size="50-100M",
            low=8000, typical=12000, high=18000,
            source="HIMSS Healthcare IT Survey 2024",
            year=2024,
            unit="$"
        ),
        "financial_services_50-100M": BenchmarkData(
            metric="cost_per_employee",
            industry="financial_services",
            company_size="50-100M",
            low=15000, typical=22000, high=30000,
            source="Deloitte Financial Services IT Survey 2024",
            year=2024,
            unit="$"
        ),
        "general_50-100M": BenchmarkData(
            metric="cost_per_employee",
            industry="general",
            company_size="50-100M",
            low=8000, typical=12000, high=18000,
            source="Internal rule of thumb (cross-industry average)",
            year=2024,
            unit="$"
        ),
        "general_100-500M": BenchmarkData(
            metric="cost_per_employee",
            industry="general",
            company_size="100-500M",
            low=7000, typical=10000, high=15000,
            source="Internal rule of thumb (cross-industry average)",
            year=2024,
            unit="$"
        ),
    },

    # =========================================================================
    # IT Staff per 100 Employees
    # =========================================================================
    "it_staff_ratio": {
        "software_50-100M": BenchmarkData(
            metric="it_staff_ratio",
            industry="software",
            company_size="50-100M",
            low=8, typical=12, high=18,
            source="AITE Group IT Staffing Benchmarks 2024",
            year=2024,
            unit="ratio",
            notes="IT staff per 100 employees; software companies staff heavier"
        ),
        "software_100-500M": BenchmarkData(
            metric="it_staff_ratio",
            industry="software",
            company_size="100-500M",
            low=6, typical=10, high=15,
            source="AITE Group IT Staffing Benchmarks 2024",
            year=2024,
            unit="ratio"
        ),
        "manufacturing_50-100M": BenchmarkData(
            metric="it_staff_ratio",
            industry="manufacturing",
            company_size="50-100M",
            low=2, typical=4, high=6,
            source="AITE Group IT Staffing Benchmarks 2024",
            year=2024,
            unit="ratio"
        ),
        "manufacturing_100-500M": BenchmarkData(
            metric="it_staff_ratio",
            industry="manufacturing",
            company_size="100-500M",
            low=2, typical=3, high=5,
            source="AITE Group IT Staffing Benchmarks 2024",
            year=2024,
            unit="ratio"
        ),
        "general_50-100M": BenchmarkData(
            metric="it_staff_ratio",
            industry="general",
            company_size="50-100M",
            low=3, typical=5, high=8,
            source="Internal rule of thumb (cross-industry average)",
            year=2024,
            unit="ratio"
        ),
        "general_100-500M": BenchmarkData(
            metric="it_staff_ratio",
            industry="general",
            company_size="100-500M",
            low=2, typical=4, high=6,
            source="Internal rule of thumb (cross-industry average)",
            year=2024,
            unit="ratio"
        ),
    },

    # =========================================================================
    # Application Count per 100 Employees
    # =========================================================================
    "app_count_ratio": {
        "software_50-100M": BenchmarkData(
            metric="app_count_ratio",
            industry="software",
            company_size="50-100M",
            low=15, typical=25, high=40,
            source="Zylo SaaS Management Report 2024",
            year=2024,
            unit="count",
            notes="Applications per 100 employees; includes SaaS"
        ),
        "software_100-500M": BenchmarkData(
            metric="app_count_ratio",
            industry="software",
            company_size="100-500M",
            low=12, typical=20, high=35,
            source="Zylo SaaS Management Report 2024",
            year=2024,
            unit="count"
        ),
        "general_50-100M": BenchmarkData(
            metric="app_count_ratio",
            industry="general",
            company_size="50-100M",
            low=10, typical=18, high=30,
            source="Zylo SaaS Management Report 2024",
            year=2024,
            unit="count"
        ),
        "general_100-500M": BenchmarkData(
            metric="app_count_ratio",
            industry="general",
            company_size="100-500M",
            low=8, typical=15, high=25,
            source="Zylo SaaS Management Report 2024",
            year=2024,
            unit="count"
        ),
    },

    # =========================================================================
    # Outsourcing Percentage
    # =========================================================================
    "outsourcing_pct": {
        "general_0-50M": BenchmarkData(
            metric="outsourcing_pct",
            industry="general",
            company_size="0-50M",
            low=20, typical=40, high=60,
            source="ISG Outsourcing Index 2024",
            year=2024,
            unit="%",
            notes="Smaller companies tend to outsource more IT functions"
        ),
        "general_50-100M": BenchmarkData(
            metric="outsourcing_pct",
            industry="general",
            company_size="50-100M",
            low=15, typical=30, high=50,
            source="ISG Outsourcing Index 2024",
            year=2024,
            unit="%"
        ),
        "general_100-500M": BenchmarkData(
            metric="outsourcing_pct",
            industry="general",
            company_size="100-500M",
            low=10, typical=25, high=40,
            source="ISG Outsourcing Index 2024",
            year=2024,
            unit="%"
        ),
    },

    # =========================================================================
    # Cloud Adoption Percentage
    # =========================================================================
    "cloud_adoption_pct": {
        "software_50-100M": BenchmarkData(
            metric="cloud_adoption_pct",
            industry="software",
            company_size="50-100M",
            low=60, typical=80, high=95,
            source="Flexera State of the Cloud Report 2024",
            year=2024,
            unit="%",
            notes="Percentage of workloads in public/private cloud"
        ),
        "manufacturing_50-100M": BenchmarkData(
            metric="cloud_adoption_pct",
            industry="manufacturing",
            company_size="50-100M",
            low=25, typical=40, high=60,
            source="Flexera State of the Cloud Report 2024",
            year=2024,
            unit="%"
        ),
        "general_50-100M": BenchmarkData(
            metric="cloud_adoption_pct",
            industry="general",
            company_size="50-100M",
            low=35, typical=55, high=75,
            source="Flexera State of the Cloud Report 2024",
            year=2024,
            unit="%"
        ),
    },

    # =========================================================================
    # Cybersecurity Spending as % of IT Budget
    # =========================================================================
    "security_pct_it": {
        "general_50-100M": BenchmarkData(
            metric="security_pct_it",
            industry="general",
            company_size="50-100M",
            low=5, typical=10, high=15,
            source="Gartner Security & Risk Management Survey 2024",
            year=2024,
            unit="%",
            notes="Cybersecurity spending as percentage of total IT budget"
        ),
        "financial_services_50-100M": BenchmarkData(
            metric="security_pct_it",
            industry="financial_services",
            company_size="50-100M",
            low=10, typical=15, high=20,
            source="Deloitte Financial Services IT Survey 2024",
            year=2024,
            unit="%"
        ),
        "healthcare_50-100M": BenchmarkData(
            metric="security_pct_it",
            industry="healthcare",
            company_size="50-100M",
            low=8, typical=12, high=18,
            source="HIMSS Healthcare IT Survey 2024",
            year=2024,
            unit="%"
        ),
    },

    # =========================================================================
    # Technology Refresh Cycle (Years)
    # =========================================================================
    "tech_refresh_cycle": {
        "general_50-100M": BenchmarkData(
            metric="tech_refresh_cycle",
            industry="general",
            company_size="50-100M",
            low=3, typical=5, high=7,
            source="Gartner Infrastructure & Operations Survey 2024",
            year=2024,
            unit="years",
            notes="Typical hardware/infrastructure refresh cycle"
        ),
        "software_50-100M": BenchmarkData(
            metric="tech_refresh_cycle",
            industry="software",
            company_size="50-100M",
            low=2, typical=4, high=5,
            source="Gartner Infrastructure & Operations Survey 2024",
            year=2024,
            unit="years"
        ),
    },
}


# =============================================================================
# BENCHMARK RETRIEVAL FUNCTIONS
# =============================================================================

def get_benchmark(
    metric: str,
    industry: str,
    company_size: str,
    fallback_to_general: bool = True
) -> Optional[BenchmarkData]:
    """
    Retrieve benchmark data for a specific metric, industry, and company size.

    Args:
        metric: Metric key (e.g., "it_pct_revenue", "cost_per_employee")
        industry: Industry code (e.g., "software", "manufacturing", "general")
        company_size: Size tier (e.g., "50-100M", "100-500M")
        fallback_to_general: If True, fall back to "general" industry if specific not found

    Returns:
        BenchmarkData if found, None otherwise
    """
    if metric not in BENCHMARK_LIBRARY:
        logger.warning(f"Unknown benchmark metric: {metric}")
        return None

    metric_data = BENCHMARK_LIBRARY[metric]

    # Try exact match first
    key = f"{industry}_{company_size}"
    if key in metric_data:
        return metric_data[key]

    # Fall back to general industry
    if fallback_to_general and industry != "general":
        general_key = f"general_{company_size}"
        if general_key in metric_data:
            logger.info(f"Using general benchmark for {metric} (no {industry} data)")
            return metric_data[general_key]

    logger.warning(f"No benchmark found for {metric}/{industry}/{company_size}")
    return None


def get_all_benchmarks_for_metric(metric: str) -> Dict[str, BenchmarkData]:
    """Get all available benchmarks for a specific metric."""
    return BENCHMARK_LIBRARY.get(metric, {})


def list_available_metrics() -> List[str]:
    """List all available benchmark metrics."""
    return list(BENCHMARK_LIBRARY.keys())


def get_benchmark_context_string(
    metric: str,
    industry: str,
    company_size: str,
    actual_value: Optional[float] = None
) -> str:
    """
    Get a formatted benchmark context string for LLM prompts.

    Args:
        metric: Metric key
        industry: Industry code
        company_size: Size tier
        actual_value: Optional actual value to compare

    Returns:
        Formatted string with benchmark context and source
    """
    benchmark = get_benchmark(metric, industry, company_size)
    if not benchmark:
        return f"No benchmark data available for {metric}"

    context = f"Benchmark for {metric} ({industry}, {company_size}):\n"
    context += f"  Range: {benchmark.format_range()}\n"
    context += f"  Source: {benchmark.source} ({benchmark.year})\n"

    if actual_value is not None:
        assessment = benchmark.assess_value(actual_value)
        context += f"  Actual value: {actual_value}\n"
        context += f"  Assessment: {assessment}\n"

    if benchmark.notes:
        context += f"  Notes: {benchmark.notes}\n"

    return context


def assess_against_benchmark(
    metric: str,
    industry: str,
    company_size: str,
    actual_value: float
) -> Dict[str, Any]:
    """
    Assess a value against benchmark and return structured result.

    Returns dict with:
        - found: bool - whether benchmark was found
        - benchmark: BenchmarkData or None
        - assessment: "below_typical", "typical", "above_typical", or "unknown"
        - context: formatted string for display
    """
    benchmark = get_benchmark(metric, industry, company_size)

    if not benchmark:
        return {
            "found": False,
            "benchmark": None,
            "assessment": "unknown",
            "context": f"No benchmark available for {metric}"
        }

    assessment = benchmark.assess_value(actual_value)

    return {
        "found": True,
        "benchmark": benchmark,
        "assessment": assessment,
        "context": benchmark.format_citation()
    }


# =============================================================================
# METRIC DESCRIPTIONS
# =============================================================================

METRIC_DESCRIPTIONS = {
    "it_pct_revenue": "IT spending as a percentage of company revenue",
    "cost_per_employee": "Total IT cost divided by total employees (annual)",
    "it_staff_ratio": "Number of IT staff per 100 total employees",
    "app_count_ratio": "Number of applications per 100 employees",
    "outsourcing_pct": "Percentage of IT functions outsourced",
    "cloud_adoption_pct": "Percentage of workloads in cloud (public/private)",
    "security_pct_it": "Cybersecurity spending as percentage of IT budget",
    "tech_refresh_cycle": "Typical hardware/infrastructure refresh cycle in years",
}


def get_metric_description(metric: str) -> str:
    """Get human-readable description of a metric."""
    return METRIC_DESCRIPTIONS.get(metric, metric)
