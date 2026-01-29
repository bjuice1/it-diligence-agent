"""
Document Repository

Database operations for Document model with version tracking.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
import hashlib

from web.database import db, Document
from .base import BaseRepository


class DocumentRepository(BaseRepository[Document]):
    """Repository for Document CRUD and queries."""

    model = Document

    # =========================================================================
    # DOCUMENT-SPECIFIC QUERIES
    # =========================================================================

    def get_by_deal(
        self,
        deal_id: str,
        entity: str = None,
        current_only: bool = True,
        status: str = None
    ) -> List[Document]:
        """Get documents for a deal with optional filters."""
        query = self.query().filter(Document.deal_id == deal_id)

        if entity:
            query = query.filter(Document.entity == entity)

        if current_only:
            query = query.filter(Document.is_current == True)

        if status:
            query = query.filter(Document.status == status)

        return query.order_by(Document.uploaded_at.desc()).all()

    def get_by_entity(self, deal_id: str, entity: str) -> List[Document]:
        """Get all current documents for an entity."""
        return self.get_by_deal(deal_id, entity=entity, current_only=True)

    def get_by_hash(self, deal_id: str, file_hash: str) -> Optional[Document]:
        """Find a document by its file hash."""
        return self.query().filter(
            Document.deal_id == deal_id,
            Document.file_hash == file_hash
        ).first()

    def get_versions(self, document_id: str) -> List[Document]:
        """Get all versions of a document."""
        # Get the original document
        doc = self.get_by_id(document_id, include_deleted=True)
        if not doc:
            return []

        # Find all versions with the same filename
        return self.query(include_deleted=True).filter(
            Document.deal_id == doc.deal_id,
            Document.filename == doc.filename
        ).order_by(Document.version.desc()).all()

    def get_pending(self, deal_id: str = None) -> List[Document]:
        """Get documents pending processing."""
        query = self.query().filter(Document.status == 'pending')

        if deal_id:
            query = query.filter(Document.deal_id == deal_id)

        return query.all()

    def get_failed(self, deal_id: str = None) -> List[Document]:
        """Get documents that failed processing."""
        query = self.query().filter(Document.status == 'failed')

        if deal_id:
            query = query.filter(Document.deal_id == deal_id)

        return query.all()

    # =========================================================================
    # DOCUMENT LIFECYCLE
    # =========================================================================

    def create_document(
        self,
        deal_id: str,
        filename: str,
        file_hash: str,
        storage_path: str,
        entity: str = 'target',
        file_size: int = 0,
        mime_type: str = '',
        authority_level: int = 1,
        document_type: str = '',
        storage_type: str = 'local',
        uploaded_by: str = None,
        original_filename: str = None
    ) -> Document:
        """Create a new document record."""
        return self.create(
            deal_id=deal_id,
            filename=filename,
            original_filename=original_filename or filename,
            file_hash=file_hash,
            storage_path=storage_path,
            entity=entity,
            file_size=file_size,
            mime_type=mime_type,
            authority_level=authority_level,
            document_type=document_type,
            storage_type=storage_type,
            uploaded_by=uploaded_by,
            status='pending',
            version=1,
            is_current=True
        )

    def create_new_version(
        self,
        previous_doc: Document,
        file_hash: str,
        storage_path: str,
        file_size: int = 0,
        uploaded_by: str = None
    ) -> Document:
        """
        Create a new version of an existing document.

        Marks the previous version as not current.
        """
        # Mark previous version as not current
        self.update(previous_doc, is_current=False)

        # Create new version
        new_doc = self.create(
            deal_id=previous_doc.deal_id,
            filename=previous_doc.filename,
            original_filename=previous_doc.original_filename,
            file_hash=file_hash,
            storage_path=storage_path,
            entity=previous_doc.entity,
            file_size=file_size,
            mime_type=previous_doc.mime_type,
            authority_level=previous_doc.authority_level,
            document_type=previous_doc.document_type,
            document_category=previous_doc.document_category,
            storage_type=previous_doc.storage_type,
            uploaded_by=uploaded_by,
            status='pending',
            version=previous_doc.version + 1,
            is_current=True,
            previous_version_id=previous_doc.id
        )

        return new_doc

    def check_duplicate(self, deal_id: str, file_hash: str) -> Optional[Document]:
        """Check if a document with this hash already exists."""
        return self.get_by_hash(deal_id, file_hash)

    # =========================================================================
    # PROCESSING STATUS
    # =========================================================================

    def mark_processing(self, document: Document) -> Document:
        """Mark document as being processed."""
        return self.update(document, status='processing')

    def mark_completed(
        self,
        document: Document,
        extracted_text: str,
        page_count: int = 0,
        word_count: int = 0,
        content_checksum: str = None
    ) -> Document:
        """Mark document processing as complete."""
        # Calculate content checksum if not provided
        if not content_checksum and extracted_text:
            content_checksum = hashlib.sha256(
                extracted_text.encode('utf-8')
            ).hexdigest()

        return self.update(
            document,
            status='completed',
            extracted_text=extracted_text,
            page_count=page_count,
            word_count=word_count,
            content_checksum=content_checksum,
            processed_at=datetime.utcnow()
        )

    def mark_failed(
        self,
        document: Document,
        error_message: str
    ) -> Document:
        """Mark document processing as failed."""
        return self.update(
            document,
            status='failed',
            processing_error=error_message,
            processed_at=datetime.utcnow()
        )

    def reset_for_reprocessing(self, document: Document) -> Document:
        """Reset a document to be processed again."""
        return self.update(
            document,
            status='pending',
            extracted_text='',
            processing_error='',
            processed_at=None
        )

    # =========================================================================
    # SUMMARY & STATISTICS
    # =========================================================================

    def get_summary(self, deal_id: str) -> Dict[str, Any]:
        """Get document summary statistics for a deal."""
        documents = self.get_by_deal(deal_id, current_only=True)

        by_entity = {'target': 0, 'buyer': 0}
        by_status = {'pending': 0, 'processing': 0, 'completed': 0, 'failed': 0}
        total_size = 0
        total_pages = 0

        for doc in documents:
            by_entity[doc.entity] = by_entity.get(doc.entity, 0) + 1
            by_status[doc.status] = by_status.get(doc.status, 0) + 1
            total_size += doc.file_size or 0
            total_pages += doc.page_count or 0

        return {
            'total': len(documents),
            'by_entity': by_entity,
            'by_status': by_status,
            'total_size_bytes': total_size,
            'total_pages': total_pages
        }

    def get_processing_queue(self, limit: int = 10) -> List[Document]:
        """Get documents ready for processing, ordered by priority."""
        return self.query().filter(
            Document.status == 'pending'
        ).order_by(
            Document.authority_level.desc(),  # Higher authority first
            Document.uploaded_at.asc()  # FIFO within priority
        ).limit(limit).all()

    # =========================================================================
    # CONTENT ANALYSIS
    # =========================================================================

    def has_content_changed(
        self,
        new_checksum: str,
        previous_doc: Document
    ) -> bool:
        """Check if document content has changed from previous version."""
        if not previous_doc or not previous_doc.content_checksum:
            return True

        return new_checksum != previous_doc.content_checksum

    def find_documents_needing_analysis(
        self,
        deal_id: str,
        since: datetime = None
    ) -> List[Document]:
        """Find documents that haven't been analyzed or have changed."""
        query = self.query().filter(
            Document.deal_id == deal_id,
            Document.is_current == True,
            Document.status == 'completed'
        )

        if since:
            query = query.filter(Document.processed_at > since)

        return query.all()
