"""
Calibration Testing Module

Provides test cases, quality rubric scoring, and calibration runner
for validating executive narrative generation quality.
"""

from .test_cases import (
    TestCase,
    DealType,
    Complexity,
    TEST_CASES,
    get_test_case,
    get_all_test_cases,
    get_test_cases_by_deal_type,
    get_test_cases_by_complexity,
)

from .quality_rubric import (
    ScoreLevel,
    DimensionScore,
    RubricResult,
    DIMENSION_WEIGHTS,
    score_narrative,
    format_rubric_result,
)

from .calibration_runner import (
    run_calibration,
    run_all_calibrations,
    score_existing_narrative,
    generate_mock_narrative,
)


__all__ = [
    # Test Cases
    'TestCase',
    'DealType',
    'Complexity',
    'TEST_CASES',
    'get_test_case',
    'get_all_test_cases',
    'get_test_cases_by_deal_type',
    'get_test_cases_by_complexity',
    # Quality Rubric
    'ScoreLevel',
    'DimensionScore',
    'RubricResult',
    'DIMENSION_WEIGHTS',
    'score_narrative',
    'format_rubric_result',
    # Calibration Runner
    'run_calibration',
    'run_all_calibrations',
    'score_existing_narrative',
    'generate_mock_narrative',
]
