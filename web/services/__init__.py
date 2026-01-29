"""
Services Package

Business logic layer for IT Due Diligence Agent.
Services coordinate between repositories, handle complex operations,
and implement business rules.
"""

from web.services.deal_service import DealService

__all__ = ['DealService']
