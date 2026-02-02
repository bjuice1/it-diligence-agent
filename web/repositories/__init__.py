"""
Repository Layer for Database Operations

Implements the repository pattern for clean separation between
business logic and data access. All database operations go through
repositories.
"""

from .base import BaseRepository
from .deal_repository import DealRepository
from .document_repository import DocumentRepository
from .fact_repository import FactRepository
from .finding_repository import FindingRepository
from .analysis_run_repository import AnalysisRunRepository
from .gap_repository import GapRepository

__all__ = [
    'BaseRepository',
    'DealRepository',
    'DocumentRepository',
    'FactRepository',
    'FindingRepository',
    'AnalysisRunRepository',
    'GapRepository',
]
