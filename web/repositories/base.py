"""
Base Repository Pattern Implementation

Provides common CRUD operations and query helpers for all repositories.
Supports soft delete pattern and audit columns.
"""

from typing import TypeVar, Generic, Optional, List, Dict, Any, Type
from datetime import datetime
from sqlalchemy import and_, or_
from sqlalchemy.orm import Query

from web.database import db, SoftDeleteMixin

T = TypeVar('T')


class BaseRepository(Generic[T]):
    """
    Base repository with common database operations.

    All repositories inherit from this class for consistent
    CRUD operations and query patterns.
    """

    model: Type[T] = None

    def __init__(self):
        if self.model is None:
            raise NotImplementedError("Repository must define a model class")

    # =========================================================================
    # CORE CRUD OPERATIONS
    # =========================================================================

    def get_by_id(self, id: str, include_deleted: bool = False) -> Optional[T]:
        """Get a single record by ID."""
        query = self.model.query.filter_by(id=id)

        if not include_deleted and hasattr(self.model, 'deleted_at'):
            query = query.filter(self.model.deleted_at.is_(None))

        return query.first()

    def get_all(self, include_deleted: bool = False) -> List[T]:
        """Get all records."""
        query = self.model.query

        if not include_deleted and hasattr(self.model, 'deleted_at'):
            query = query.filter(self.model.deleted_at.is_(None))

        return query.all()

    def create(self, **kwargs) -> T:
        """Create a new record."""
        instance = self.model(**kwargs)
        db.session.add(instance)
        db.session.commit()
        return instance

    def update(self, instance: T, **kwargs) -> T:
        """Update an existing record."""
        for key, value in kwargs.items():
            if hasattr(instance, key):
                setattr(instance, key, value)

        if hasattr(instance, 'updated_at'):
            instance.updated_at = datetime.utcnow()

        db.session.commit()
        return instance

    def delete(self, instance: T, soft: bool = True) -> bool:
        """
        Delete a record.

        Args:
            instance: The record to delete
            soft: If True, use soft delete (set deleted_at). If False, hard delete.

        Returns:
            True if deleted successfully
        """
        if soft and hasattr(instance, 'soft_delete'):
            instance.soft_delete()
            db.session.commit()
        else:
            db.session.delete(instance)
            db.session.commit()

        return True

    def restore(self, instance: T) -> T:
        """Restore a soft-deleted record."""
        if hasattr(instance, 'restore'):
            instance.restore()
            db.session.commit()
        return instance

    # =========================================================================
    # QUERY HELPERS
    # =========================================================================

    def query(self, include_deleted: bool = False) -> Query:
        """Get a base query with soft delete filter applied."""
        q = self.model.query

        if not include_deleted and hasattr(self.model, 'deleted_at'):
            q = q.filter(self.model.deleted_at.is_(None))

        return q

    def find_by(self, include_deleted: bool = False, **kwargs) -> List[T]:
        """Find records by attribute values."""
        query = self.query(include_deleted)
        return query.filter_by(**kwargs).all()

    def find_one_by(self, include_deleted: bool = False, **kwargs) -> Optional[T]:
        """Find a single record by attribute values."""
        query = self.query(include_deleted)
        return query.filter_by(**kwargs).first()

    def exists(self, id: str) -> bool:
        """Check if a record exists."""
        return self.get_by_id(id) is not None

    def count(self, include_deleted: bool = False, **kwargs) -> int:
        """Count records matching criteria."""
        query = self.query(include_deleted)
        if kwargs:
            query = query.filter_by(**kwargs)
        return query.count()

    # =========================================================================
    # PAGINATION
    # =========================================================================

    def paginate(
        self,
        page: int = 1,
        per_page: int = 50,
        include_deleted: bool = False,
        order_by: str = None,
        descending: bool = True,
        **filters
    ) -> Dict[str, Any]:
        """
        Paginate query results.

        Returns:
            Dict with 'items', 'total', 'page', 'per_page', 'pages'
        """
        query = self.query(include_deleted)

        # Apply filters
        if filters:
            query = query.filter_by(**filters)

        # Apply ordering
        if order_by and hasattr(self.model, order_by):
            order_col = getattr(self.model, order_by)
            if descending:
                order_col = order_col.desc()
            query = query.order_by(order_col)

        # Get total count
        total = query.count()

        # Calculate pages
        pages = (total + per_page - 1) // per_page

        # Get items for current page
        items = query.offset((page - 1) * per_page).limit(per_page).all()

        return {
            'items': items,
            'total': total,
            'page': page,
            'per_page': per_page,
            'pages': pages,
            'has_next': page < pages,
            'has_prev': page > 1,
        }

    # =========================================================================
    # BULK OPERATIONS
    # =========================================================================

    def bulk_create(self, items: List[Dict[str, Any]]) -> List[T]:
        """Create multiple records at once."""
        instances = [self.model(**item) for item in items]
        db.session.bulk_save_objects(instances)
        db.session.commit()
        return instances

    def bulk_update(self, updates: List[Dict[str, Any]]) -> int:
        """
        Bulk update records.

        Args:
            updates: List of dicts with 'id' and fields to update

        Returns:
            Number of records updated
        """
        count = 0
        for update in updates:
            id = update.pop('id', None)
            if id:
                instance = self.get_by_id(id)
                if instance:
                    self.update(instance, **update)
                    count += 1
        return count

    def bulk_delete(self, ids: List[str], soft: bool = True) -> int:
        """Delete multiple records by ID."""
        count = 0
        for id in ids:
            instance = self.get_by_id(id)
            if instance:
                self.delete(instance, soft=soft)
                count += 1
        return count

    # =========================================================================
    # TRANSACTION HELPERS
    # =========================================================================

    @staticmethod
    def commit():
        """Commit the current transaction."""
        db.session.commit()

    @staticmethod
    def rollback():
        """Rollback the current transaction."""
        db.session.rollback()

    @staticmethod
    def flush():
        """Flush pending changes without committing."""
        db.session.flush()
