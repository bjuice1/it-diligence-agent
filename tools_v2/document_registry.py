"""
Document Registry for Incremental Updates

Tracks which documents have been processed to enable:
- Detection of new vs. updated documents (via content hash)
- Incremental analysis without reprocessing unchanged docs
- Linking facts back to source documents
- Document version history
"""

import hashlib
import logging
import json
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum

logger = logging.getLogger(__name__)


class DocumentStatus(Enum):
    """Document processing status."""
    PENDING = "pending"          # Detected but not yet processed
    PROCESSING = "processing"    # Currently being analyzed
    PROCESSED = "processed"      # Successfully analyzed
    FAILED = "failed"            # Analysis failed
    SUPERSEDED = "superseded"    # Replaced by newer version
    REMOVED = "removed"          # No longer in document set


class ChangeType(Enum):
    """Type of change detected in a document."""
    NEW = "new"                  # First time seeing this document
    UPDATED = "updated"          # Content has changed (different hash)
    UNCHANGED = "unchanged"      # Same content as before
    RENAMED = "renamed"          # Same content, different filename


@dataclass
class DocumentRecord:
    """
    Record of a processed document.

    Tracks document identity, processing history, and linked facts.
    """
    doc_id: str                          # Unique document ID (DOC-001, etc.)
    filename: str                        # Original filename
    file_path: str = ""                  # Full path if available
    content_hash: str = ""               # SHA-256 of content
    file_size: int = 0                   # Size in bytes

    # Processing info
    status: DocumentStatus = DocumentStatus.PENDING
    first_seen_at: str = ""              # When first detected
    last_processed_at: str = ""          # When last analyzed
    processing_duration_ms: int = 0      # How long analysis took

    # Linked facts
    fact_ids: List[str] = field(default_factory=list)
    fact_count: int = 0

    # Version tracking
    version: int = 1                     # Increments on content change
    previous_hash: str = ""              # Hash before last update
    superseded_by: str = ""              # If replaced, the new doc_id

    # Metadata
    document_type: str = ""              # pdf, docx, xlsx, md, etc.
    title: str = ""                      # Extracted title if available
    notes: str = ""                      # User notes about this doc

    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result['status'] = self.status.value
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DocumentRecord':
        if 'status' in data and isinstance(data['status'], str):
            data['status'] = DocumentStatus(data['status'])
        return cls(**data)


@dataclass
class DocumentChange:
    """Represents a detected change in a document."""
    doc_id: str
    filename: str
    change_type: ChangeType
    old_hash: str = ""
    new_hash: str = ""
    old_fact_count: int = 0
    new_fact_count: int = 0
    facts_added: List[str] = field(default_factory=list)
    facts_removed: List[str] = field(default_factory=list)
    facts_updated: List[str] = field(default_factory=list)


class DocumentRegistry:
    """
    Central registry for tracking processed documents.

    Features:
    - Hash-based duplicate/update detection
    - Document version history
    - Fact-to-document linking
    - Incremental processing support
    """

    def __init__(self):
        self.documents: Dict[str, DocumentRecord] = {}  # doc_id -> record
        self._hash_index: Dict[str, str] = {}           # content_hash -> doc_id
        self._filename_index: Dict[str, str] = {}       # filename -> doc_id
        self._next_id = 1
        self._analysis_runs: List[Dict[str, Any]] = []  # History of analysis runs

    def _generate_doc_id(self) -> str:
        """Generate unique document ID."""
        doc_id = f"DOC-{self._next_id:04d}"
        self._next_id += 1
        return doc_id

    def compute_hash(self, content: str) -> str:
        """Compute SHA-256 hash of document content."""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

    def compute_file_hash(self, file_path: str) -> str:
        """Compute SHA-256 hash of file content."""
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                sha256.update(chunk)
        return sha256.hexdigest()

    def detect_change(self, filename: str, content_hash: str) -> Tuple[ChangeType, Optional[str]]:
        """
        Detect what kind of change this document represents.

        Returns:
            Tuple of (ChangeType, existing_doc_id or None)
        """
        # Check if we've seen this exact content before
        if content_hash in self._hash_index:
            existing_id = self._hash_index[content_hash]
            existing_doc = self.documents[existing_id]

            if existing_doc.filename == filename:
                return ChangeType.UNCHANGED, existing_id
            else:
                return ChangeType.RENAMED, existing_id

        # Check if we've seen this filename before
        if filename in self._filename_index:
            existing_id = self._filename_index[filename]
            return ChangeType.UPDATED, existing_id

        # Completely new document
        return ChangeType.NEW, None

    def register_document(
        self,
        filename: str,
        content: str = "",
        content_hash: str = "",
        file_path: str = "",
        file_size: int = 0,
        document_type: str = ""
    ) -> Tuple[DocumentRecord, ChangeType]:
        """
        Register a document for processing.

        Returns:
            Tuple of (DocumentRecord, ChangeType indicating if new/updated/unchanged)
        """
        # Compute hash if not provided
        if not content_hash and content:
            content_hash = self.compute_hash(content)

        # Detect change type
        change_type, existing_id = self.detect_change(filename, content_hash)

        timestamp = datetime.now().isoformat()

        if change_type == ChangeType.NEW:
            # Create new document record
            doc_id = self._generate_doc_id()
            record = DocumentRecord(
                doc_id=doc_id,
                filename=filename,
                file_path=file_path,
                content_hash=content_hash,
                file_size=file_size,
                first_seen_at=timestamp,
                document_type=document_type or self._detect_type(filename)
            )
            self.documents[doc_id] = record
            self._hash_index[content_hash] = doc_id
            self._filename_index[filename] = doc_id

            logger.info(f"Registered new document: {filename} -> {doc_id}")
            return record, change_type

        elif change_type == ChangeType.UPDATED:
            # Update existing document record
            record = self.documents[existing_id]
            record.previous_hash = record.content_hash
            record.content_hash = content_hash
            record.version += 1
            record.file_size = file_size
            record.status = DocumentStatus.PENDING

            # Update hash index
            if record.previous_hash in self._hash_index:
                del self._hash_index[record.previous_hash]
            self._hash_index[content_hash] = existing_id

            logger.info(f"Document updated: {filename} (v{record.version})")
            return record, change_type

        elif change_type == ChangeType.RENAMED:
            # Same content, different filename - just update filename
            record = self.documents[existing_id]
            old_filename = record.filename
            record.filename = filename

            # Update filename index
            if old_filename in self._filename_index:
                del self._filename_index[old_filename]
            self._filename_index[filename] = existing_id

            logger.info(f"Document renamed: {old_filename} -> {filename}")
            return record, change_type

        else:  # UNCHANGED
            record = self.documents[existing_id]
            logger.debug(f"Document unchanged: {filename}")
            return record, change_type

    def _detect_type(self, filename: str) -> str:
        """Detect document type from filename extension."""
        ext = os.path.splitext(filename)[1].lower()
        type_map = {
            '.pdf': 'pdf',
            '.docx': 'docx',
            '.doc': 'doc',
            '.xlsx': 'xlsx',
            '.xls': 'xls',
            '.pptx': 'pptx',
            '.ppt': 'ppt',
            '.md': 'markdown',
            '.txt': 'text',
            '.csv': 'csv',
            '.json': 'json'
        }
        return type_map.get(ext, 'unknown')

    def mark_processing(self, doc_id: str) -> bool:
        """Mark document as currently processing."""
        if doc_id not in self.documents:
            return False
        self.documents[doc_id].status = DocumentStatus.PROCESSING
        return True

    def mark_processed(
        self,
        doc_id: str,
        fact_ids: List[str],
        duration_ms: int = 0
    ) -> bool:
        """Mark document as successfully processed with linked facts."""
        if doc_id not in self.documents:
            return False

        record = self.documents[doc_id]
        record.status = DocumentStatus.PROCESSED
        record.last_processed_at = datetime.now().isoformat()
        record.processing_duration_ms = duration_ms
        record.fact_ids = fact_ids
        record.fact_count = len(fact_ids)

        logger.info(f"Document processed: {record.filename} -> {len(fact_ids)} facts")
        return True

    def mark_failed(self, doc_id: str, error: str = "") -> bool:
        """Mark document as failed processing."""
        if doc_id not in self.documents:
            return False

        record = self.documents[doc_id]
        record.status = DocumentStatus.FAILED
        record.notes = f"Processing failed: {error}"

        logger.warning(f"Document processing failed: {record.filename}")
        return True

    def get_document(self, doc_id: str) -> Optional[DocumentRecord]:
        """Get document by ID."""
        return self.documents.get(doc_id)

    def get_by_filename(self, filename: str) -> Optional[DocumentRecord]:
        """Get document by filename."""
        doc_id = self._filename_index.get(filename)
        return self.documents.get(doc_id) if doc_id else None

    def get_by_hash(self, content_hash: str) -> Optional[DocumentRecord]:
        """Get document by content hash."""
        doc_id = self._hash_index.get(content_hash)
        return self.documents.get(doc_id) if doc_id else None

    def get_documents_for_processing(self) -> List[DocumentRecord]:
        """Get all documents that need processing (pending or updated)."""
        return [
            doc for doc in self.documents.values()
            if doc.status in [DocumentStatus.PENDING, DocumentStatus.PROCESSING]
        ]

    def get_all_documents(self) -> List[DocumentRecord]:
        """Get all registered documents."""
        return list(self.documents.values())

    def get_facts_for_document(self, doc_id: str) -> List[str]:
        """Get all fact IDs linked to a document."""
        record = self.documents.get(doc_id)
        return record.fact_ids if record else []

    def get_document_for_fact(self, fact_id: str) -> Optional[str]:
        """Find which document a fact came from."""
        for doc_id, record in self.documents.items():
            if fact_id in record.fact_ids:
                return doc_id
        return None

    def start_analysis_run(self, run_id: str = None) -> str:
        """Start a new analysis run and return its ID."""
        if not run_id:
            run_id = f"RUN-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

        run_record = {
            "run_id": run_id,
            "started_at": datetime.now().isoformat(),
            "completed_at": None,
            "documents_processed": 0,
            "documents_new": 0,
            "documents_updated": 0,
            "documents_unchanged": 0,
            "facts_added": 0,
            "facts_updated": 0,
            "facts_removed": 0,
            "conflicts_detected": 0
        }
        self._analysis_runs.append(run_record)
        return run_id

    def complete_analysis_run(
        self,
        run_id: str,
        stats: Dict[str, int] = None
    ) -> bool:
        """Complete an analysis run with final stats."""
        for run in self._analysis_runs:
            if run["run_id"] == run_id:
                run["completed_at"] = datetime.now().isoformat()
                if stats:
                    run.update(stats)
                return True
        return False

    def get_analysis_runs(self) -> List[Dict[str, Any]]:
        """Get history of analysis runs."""
        return self._analysis_runs

    def get_latest_run(self) -> Optional[Dict[str, Any]]:
        """Get the most recent analysis run."""
        return self._analysis_runs[-1] if self._analysis_runs else None

    def get_stats(self) -> Dict[str, Any]:
        """Get registry statistics."""
        docs = list(self.documents.values())

        by_status = {}
        for status in DocumentStatus:
            by_status[status.value] = sum(1 for d in docs if d.status == status)

        by_type = {}
        for doc in docs:
            doc_type = doc.document_type or 'unknown'
            by_type[doc_type] = by_type.get(doc_type, 0) + 1

        total_facts = sum(d.fact_count for d in docs)

        return {
            "total_documents": len(docs),
            "by_status": by_status,
            "by_type": by_type,
            "total_facts_linked": total_facts,
            "analysis_runs": len(self._analysis_runs)
        }

    def export_to_dict(self) -> Dict[str, Any]:
        """Export registry to dictionary for serialization."""
        return {
            "documents": {
                doc_id: record.to_dict()
                for doc_id, record in self.documents.items()
            },
            "next_id": self._next_id,
            "analysis_runs": self._analysis_runs
        }

    def import_from_dict(self, data: Dict[str, Any]) -> None:
        """Import registry from dictionary."""
        self.documents = {}
        self._hash_index = {}
        self._filename_index = {}

        for doc_id, doc_data in data.get("documents", {}).items():
            record = DocumentRecord.from_dict(doc_data)
            self.documents[doc_id] = record
            if record.content_hash:
                self._hash_index[record.content_hash] = doc_id
            if record.filename:
                self._filename_index[record.filename] = doc_id

        self._next_id = data.get("next_id", len(self.documents) + 1)
        self._analysis_runs = data.get("analysis_runs", [])

    def save_to_file(self, file_path: str) -> None:
        """Save registry to JSON file."""
        with open(file_path, 'w') as f:
            json.dump(self.export_to_dict(), f, indent=2)
        logger.info(f"Registry saved to {file_path}")

    def load_from_file(self, file_path: str) -> None:
        """Load registry from JSON file."""
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                self.import_from_dict(json.load(f))
            logger.info(f"Registry loaded from {file_path} ({len(self.documents)} documents)")
