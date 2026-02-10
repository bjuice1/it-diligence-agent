"""
Cost Engine Exports

Generate model-ready CSV exports:
- deal_costs.csv: Work item costs by tower
- drivers.csv: Driver values with sources
- assumptions.csv: Key assumptions driving the model
"""

import csv
import io
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from .drivers import DealDrivers, DriverExtractionResult, DriverConfidence
from .calculator import DealCostSummary, CostEstimate
from .models import get_all_models

logger = logging.getLogger(__name__)


# =============================================================================
# CSV GENERATORS
# =============================================================================

def generate_deal_costs_csv(summary: DealCostSummary) -> str:
    """
    Generate deal_costs.csv for deal model import.

    Format:
    tower,work_item,one_time_upside,one_time_base,one_time_stress,annual_licenses,run_rate_delta,source
    """
    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow([
        'tower',
        'work_item',
        'one_time_upside',
        'one_time_base',
        'one_time_stress',
        'annual_licenses',
        'run_rate_delta',
        'complexity',
        'months',
        'source',
    ])

    # Data rows
    for estimate in summary.estimates:
        writer.writerow([
            estimate.tower,
            estimate.display_name,
            estimate.one_time_upside,
            estimate.one_time_base,
            estimate.one_time_stress,
            estimate.annual_licenses,
            estimate.run_rate_delta,
            estimate.complexity,
            estimate.estimated_months,
            'calculated',
        ])

    # Tower subtotals
    writer.writerow([])  # Blank row
    writer.writerow(['--- TOWER SUBTOTALS ---'])
    for tower, costs in summary.tower_costs.items():
        writer.writerow([
            tower,
            f"SUBTOTAL ({len(costs['items'])} items)",
            costs['one_time_upside'],
            costs['one_time_base'],
            costs['one_time_stress'],
            costs['annual_licenses'],
            '',
            '',
            '',
            'subtotal',
        ])

    # Grand totals
    writer.writerow([])
    writer.writerow([
        'TOTAL',
        f'ALL ({len(summary.estimates)} items)',
        summary.total_one_time_upside,
        summary.total_one_time_base,
        summary.total_one_time_stress,
        summary.total_annual_licenses,
        summary.total_run_rate_delta,
        '',
        '',
        'total',
    ])

    output.seek(0)
    return output.getvalue()


def generate_drivers_csv(result: DriverExtractionResult, deal_id: str = '') -> str:
    """
    Generate drivers.csv with all driver values and sources.

    Format:
    driver,value,source_type,source_id,confidence,overridden,notes
    """
    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow([
        'driver',
        'value',
        'source_type',
        'source_fact_id',
        'confidence',
        'overridden',
        'notes',
    ])

    drivers = result.drivers

    # Iterate through all driver fields
    for field_name in drivers.__dataclass_fields__:
        if field_name in ('sources', 'shared_with_parent'):
            continue

        value = getattr(drivers, field_name)
        source = drivers.sources.get(field_name)

        if value is not None:
            # Handle enum values
            if hasattr(value, 'value'):
                value = value.value

            writer.writerow([
                field_name,
                value,
                source.extraction_method if source else 'not_extracted',
                source.fact_id if source else '',
                source.confidence.value if source else 'unknown',
                'true' if source and source.confidence == DriverConfidence.OVERRIDE else 'false',
                source.notes if source else '',
            ])

    # Add shared_with_parent as special row
    if drivers.shared_with_parent:
        writer.writerow([
            'shared_with_parent',
            ','.join(drivers.shared_with_parent),
            'derived',
            '',
            'high',
            'false',
            'Services shared with parent company',
        ])

    # Add metadata
    writer.writerow([])
    writer.writerow(['--- EXTRACTION SUMMARY ---'])
    writer.writerow(['facts_scanned', result.facts_scanned])
    writer.writerow(['drivers_extracted', result.drivers_extracted])
    writer.writerow(['drivers_assumed', result.drivers_assumed])
    writer.writerow(['deal_id', deal_id])
    writer.writerow(['generated_at', datetime.utcnow().isoformat()])

    output.seek(0)
    return output.getvalue()


def generate_assumptions_csv(
    summary: DealCostSummary,
    driver_result: DriverExtractionResult,
) -> str:
    """
    Generate assumptions.csv listing all assumptions and their impact.

    Format:
    category,assumption,value,impact,source,confidence
    """
    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow([
        'category',
        'assumption',
        'value',
        'impact',
        'source',
        'confidence',
    ])

    drivers = driver_result.drivers

    # Driver-based assumptions (high impact)
    if drivers.total_users:
        writer.writerow([
            'scale',
            'Total user count',
            f'{drivers.total_users:,}',
            'high',
            _get_source_label(drivers.sources.get('total_users')),
            _get_confidence_label(drivers.sources.get('total_users')),
        ])

    if drivers.sites:
        writer.writerow([
            'scale',
            'Number of sites',
            drivers.sites,
            'high' if drivers.sites > 5 else 'medium',
            _get_source_label(drivers.sources.get('sites')),
            _get_confidence_label(drivers.sources.get('sites')),
        ])

    if drivers.erp_system:
        writer.writerow([
            'applications',
            'ERP system',
            drivers.erp_system,
            'high',
            _get_source_label(drivers.sources.get('erp_system')),
            _get_confidence_label(drivers.sources.get('erp_system')),
        ])

    # Parent ownership assumptions
    if drivers.shared_with_parent:
        writer.writerow([
            'ownership',
            'Parent-owned services',
            ', '.join(drivers.shared_with_parent),
            'high',
            'derived from facts',
            'medium',
        ])

    # Model assumptions from estimates
    seen_assumptions = set()
    for estimate in summary.estimates:
        for assumption in estimate.assumptions:
            if assumption not in seen_assumptions:
                seen_assumptions.add(assumption)

                # Determine category and impact
                category = _categorize_assumption(assumption)
                impact = _assess_assumption_impact(assumption, estimate)

                writer.writerow([
                    category,
                    assumption,
                    '',
                    impact,
                    f'cost model: {estimate.display_name}',
                    'medium',
                ])

    # Default assumptions (low confidence)
    if driver_result.drivers_assumed > 0:
        writer.writerow([])
        writer.writerow(['--- ASSUMED VALUES (verify these) ---'])
        for driver_name in drivers.get_assumed_drivers():
            value = getattr(drivers, driver_name, None)
            if value is not None:
                writer.writerow([
                    'assumed',
                    driver_name,
                    value,
                    'medium',
                    'default assumption',
                    'low',
                ])

    output.seek(0)
    return output.getvalue()


def _get_source_label(source) -> str:
    """Get human-readable source label."""
    if not source:
        return 'not extracted'
    if source.fact_id:
        return source.fact_id
    if source.extraction_method == 'override':
        return 'user override'
    if source.extraction_method == 'default':
        return 'default assumption'
    return source.extraction_method


def _get_confidence_label(source) -> str:
    """Get confidence label."""
    if not source:
        return 'unknown'
    return source.confidence.value


def _categorize_assumption(assumption: str) -> str:
    """Categorize an assumption string."""
    lower = assumption.lower()

    if any(x in lower for x in ['user', 'count', 'headcount']):
        return 'scale'
    if any(x in lower for x in ['license', 'pricing', 'cost']):
        return 'pricing'
    if any(x in lower for x in ['cloud', 'azure', 'aws', 'deployment']):
        return 'infrastructure'
    if any(x in lower for x in ['sap', 'oracle', 'erp', 'netsuite']):
        return 'applications'
    if any(x in lower for x in ['complexity', 'standard', 'typical']):
        return 'complexity'
    if any(x in lower for x in ['migration', 'duration', 'month', 'week']):
        return 'timeline'

    return 'general'


def _assess_assumption_impact(assumption: str, estimate: CostEstimate) -> str:
    """Assess impact of an assumption."""
    lower = assumption.lower()

    # High impact assumptions
    if any(x in lower for x in ['user count', 'site count', 'complexity: high', 'sap']):
        return 'high'

    # Medium impact
    if any(x in lower for x in ['volume discount', 'pricing', 'standard']):
        return 'medium'

    return 'low'


# =============================================================================
# COMBINED EXPORT
# =============================================================================

def generate_all_exports(
    deal_id: str,
    summary: DealCostSummary,
    driver_result: DriverExtractionResult,
) -> Dict[str, str]:
    """
    Generate all three CSV exports.

    Returns dict with keys: 'deal_costs', 'drivers', 'assumptions'
    """
    return {
        'deal_costs': generate_deal_costs_csv(summary),
        'drivers': generate_drivers_csv(driver_result, deal_id),
        'assumptions': generate_assumptions_csv(summary, driver_result),
    }


def export_to_files(
    deal_id: str,
    summary: DealCostSummary,
    driver_result: DriverExtractionResult,
    output_dir: str,
) -> List[str]:
    """
    Export all CSVs to files.

    Returns list of created file paths.
    """
    import os
    from pathlib import Path

    exports = generate_all_exports(deal_id, summary, driver_result)
    created_files = []

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    for name, content in exports.items():
        filename = f"{name}_{deal_id}.csv"
        filepath = output_path / filename

        with open(filepath, 'w', newline='') as f:
            f.write(content)

        created_files.append(str(filepath))
        logger.info(f"Exported {name} to {filepath}")

    return created_files
