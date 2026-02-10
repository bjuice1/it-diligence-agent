"""
Storage Layer for IT Due Diligence Agent

Provides persistent storage for all findings with:
- Document tracking and attribution
- Analysis run management
- Iterative analysis support
"""

from storage.database import Database, get_db
from storage.models import (
    Document,
    AnalysisRun,
    InventoryItem,
    Risk,
    Gap,
    Assumption,
    WorkItem,
    Recommendation,
    StrategicConsideration,
    Question,
    SourceEvidence
)
from storage.repository import (
    Repository,
    RepositoryError,
    EntityNotFoundError,
    DuplicateEntityError,
    ValidationError
)

__all__ = [
    'Database',
    'get_db',
    'Repository',
    'RepositoryError',
    'EntityNotFoundError',
    'DuplicateEntityError',
    'ValidationError',
    'Document',
    'AnalysisRun',
    'InventoryItem',
    'Risk',
    'Gap',
    'Assumption',
    'WorkItem',
    'Recommendation',
    'StrategicConsideration',
    'Question',
    'SourceEvidence'
]
