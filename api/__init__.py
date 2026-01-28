"""
API package for IT Due Diligence System.

Contains REST API endpoints for:
- Human review workflow
- Validation status queries
- Correction operations
"""

from api.review_routes import (
    review_bp,
    register_review_routes
)

__all__ = [
    'review_bp',
    'register_review_routes'
]
