"""
V2 Tools Module

Discovery-Reasoning split architecture tools:
- FactStore: Central fact storage with unique IDs
- ReasoningStore: Findings storage with fact citations
- Discovery Tools: Fact extraction (create_inventory_entry, flag_gap)
- Reasoning Tools: Analysis with fact citations
- Coverage: Coverage checklists and quality scoring
"""

from tools_v2.fact_store import FactStore, Fact, Gap
from tools_v2.discovery_tools import DISCOVERY_TOOLS, execute_discovery_tool
from tools_v2.reasoning_tools import (
    REASONING_TOOLS,
    execute_reasoning_tool,
    ReasoningStore,
    Risk,
    StrategicConsideration,
    WorkItem,
    Recommendation,
    get_reasoning_tools,
    COST_RANGES,
    COST_RANGE_VALUES
)
from tools_v2.coverage import (
    COVERAGE_CHECKLISTS,
    CoverageAnalyzer,
    DomainCoverage,
    CategoryCoverage,
    ChecklistItem
)
from tools_v2.vdr_generator import (
    VDRGenerator,
    VDRRequest,
    VDRRequestPack,
    SUGGESTED_DOCUMENTS
)
from tools_v2.synthesis import (
    SynthesisAnalyzer,
    ConsistencyIssue,
    RelatedFinding
)

__all__ = [
    # Fact Store
    'FactStore',
    'Fact',
    'Gap',
    # Reasoning Store
    'ReasoningStore',
    'Risk',
    'StrategicConsideration',
    'WorkItem',
    'Recommendation',
    # Cost estimation
    'COST_RANGES',
    'COST_RANGE_VALUES',
    # Coverage
    'COVERAGE_CHECKLISTS',
    'CoverageAnalyzer',
    'DomainCoverage',
    'CategoryCoverage',
    'ChecklistItem',
    # VDR Generator
    'VDRGenerator',
    'VDRRequest',
    'VDRRequestPack',
    'SUGGESTED_DOCUMENTS',
    # Synthesis
    'SynthesisAnalyzer',
    'ConsistencyIssue',
    'RelatedFinding',
    # Tools
    'DISCOVERY_TOOLS',
    'REASONING_TOOLS',
    'execute_discovery_tool',
    'execute_reasoning_tool'
]
