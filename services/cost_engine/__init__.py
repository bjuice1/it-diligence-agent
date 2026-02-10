"""
Cost Engine Module

Driver-based cost estimation with deterministic calculations.

Components:
- drivers.py: Extract quantitative drivers from facts
- models.py: Cost model definitions (8 core models)
- calculator.py: Driver-based cost calculations with scenarios
- exports.py: CSV export for deal models
"""

from .drivers import (
    DealDrivers,
    DriverSource,
    DriverExtractionResult,
    DriverConfidence,
    OwnershipType,
    extract_drivers_from_facts,
    get_effective_drivers,
)

from .models import (
    CostModel,
    CostEstimate,
    CostScenario,
    Complexity,
    WorkItemType,
    LicenseComponent,
    COST_MODELS,
    get_model,
    get_all_models,
    get_models_by_tower,
)

from .calculator import (
    calculate_cost,
    calculate_work_item_cost,
    calculate_deal_costs,
    DealCostSummary,
    assess_complexity,
    get_volume_discount,
)

from .exports import (
    generate_deal_costs_csv,
    generate_drivers_csv,
    generate_assumptions_csv,
    generate_all_exports,
    export_to_files,
)

__all__ = [
    # Drivers
    'DealDrivers',
    'DriverSource',
    'DriverExtractionResult',
    'DriverConfidence',
    'OwnershipType',
    'extract_drivers_from_facts',
    'get_effective_drivers',

    # Models
    'CostModel',
    'CostEstimate',
    'CostScenario',
    'Complexity',
    'WorkItemType',
    'LicenseComponent',
    'COST_MODELS',
    'get_model',
    'get_all_models',
    'get_models_by_tower',

    # Calculator
    'calculate_cost',
    'calculate_work_item_cost',
    'calculate_deal_costs',
    'DealCostSummary',
    'assess_complexity',
    'get_volume_discount',

    # Exports
    'generate_deal_costs_csv',
    'generate_drivers_csv',
    'generate_assumptions_csv',
    'generate_all_exports',
    'export_to_files',
]
