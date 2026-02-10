"""
Tests for DocumentStore

Tests cover:
- Document addition and retrieval
- Hash-based duplicate detection
- Entity separation
- Authority level filtering
- Text extraction hooks
- Manifest persistence
"""

import pytest
import tempfile
import shutil
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.file_hasher import compute_sha256, compute_sha256_from_bytes, verify_file_hash
from stores.document_store import (
    DocumentStore,
    Document,
    DocumentStatus,
    AuthorityLevel,
    Entity
)


@pytest.fixture
def temp_dir():
    """Create temporary directory for test files."""
    temp = tempfile.mkdtemp()
    yield Path(temp)
    shutil.rmtree(temp)


@pytest.fixture
def document_store(temp_dir):
    """Create a fresh DocumentStore for testing."""
    DocumentStore.reset_instance()
    store = DocumentStore(base_dir=temp_dir / "documents")
    yield store
    DocumentStore.reset_instance()


@pytest.fixture
def sample_file(temp_dir):
    """Create a sample text file for testing."""
    file_path = temp_dir / "sample_document.txt"
    content = "This is a sample document for testing.\nIt has multiple lines.\nPage 2 content here."
    file_path.write_text(content)
    return file_path


@pytest.fixture
def sample_pdf_content():
    """Sample content that would be in a PDF."""
    return b"%PDF-1.4 sample pdf content for testing hash computation"


class TestFileHasher:
    """Tests for file hashing utilities."""

    def test_compute_sha256_creates_hash(self, sample_file):
        """Test that SHA-256 hash is computed correctly."""
        hash_value = compute_sha256(sample_file)

        assert hash_value is not None
        assert len(hash_value) == 64  # SHA-256 produces 64 hex characters
        assert all(c in '0123456789abcdef' for c in hash_value)

    def test_same_file_same_hash(self, sample_file):
        """Test that same file produces same hash."""
        hash1 = compute_sha256(sample_file)
        hash2 = compute_sha256(sample_file)

        assert hash1 == hash2

    def test_different_content_different_hash(self, temp_dir):
        """Test that different content produces different hash."""
        file1 = temp_dir / "file1.txt"
        file2 = temp_dir / "file2.txt"

        file1.write_text("Content A")
        file2.write_text("Content B")

        hash1 = compute_sha256(file1)
        hash2 = compute_sha256(file2)

        assert hash1 != hash2

    def test_compute_sha256_from_bytes(self):
        """Test hashing from bytes."""
        content = b"Test content for hashing"
        hash_value = compute_sha256_from_bytes(content)

        assert len(hash_value) == 64
        # Same content should produce same hash
        assert compute_sha256_from_bytes(content) == hash_value

    def test_verify_file_hash(self, sample_file):
        """Test hash verification."""
        correct_hash = compute_sha256(sample_file)

        assert verify_file_hash(sample_file, correct_hash) is True
        assert verify_file_hash(sample_file, "wrong_hash") is False

    def test_hash_file_not_found(self):
        """Test error handling for missing file."""
        with pytest.raises(FileNotFoundError):
            compute_sha256("/nonexistent/file.txt")

    def test_bytes_hash_type_error(self):
        """Test that non-bytes input raises error."""
        with pytest.raises(TypeError):
            compute_sha256_from_bytes("not bytes")


class TestDocumentStore:
    """Tests for DocumentStore functionality."""

    def test_add_document(self, document_store, sample_file):
        """Test adding a document to the store."""
        doc = document_store.add_document(
            file_path=sample_file,
            entity="target",
            authority_level=1,
            uploaded_by="test_user"
        )

        assert doc is not None
        assert doc.doc_id is not None
        assert doc.filename == sample_file.name
        assert doc.entity == "target"
        assert doc.authority_level == 1
        assert doc.uploaded_by == "test_user"
        assert doc.status == DocumentStatus.PENDING.value
        assert len(doc.hash_sha256) == 64

    def test_add_document_requires_valid_entity(self, document_store, sample_file):
        """Test that invalid entity raises error."""
        with pytest.raises(ValueError) as exc_info:
            document_store.add_document(
                file_path=sample_file,
                entity="invalid_entity"
            )

        assert "invalid entity" in str(exc_info.value).lower()

    def test_duplicate_detection_by_hash(self, document_store, sample_file):
        """Test that uploading same file returns existing document."""
        doc1 = document_store.add_document(
            file_path=sample_file,
            entity="target"
        )

        doc2 = document_store.add_document(
            file_path=sample_file,
            entity="target"
        )

        assert doc1.doc_id == doc2.doc_id
        assert doc1.hash_sha256 == doc2.hash_sha256

    def test_get_document(self, document_store, sample_file):
        """Test retrieving document by ID."""
        doc = document_store.add_document(
            file_path=sample_file,
            entity="target"
        )

        retrieved = document_store.get_document(doc.doc_id)

        assert retrieved is not None
        assert retrieved.doc_id == doc.doc_id
        assert retrieved.filename == doc.filename

    def test_get_document_not_found(self, document_store):
        """Test retrieving non-existent document."""
        result = document_store.get_document("nonexistent-id")
        assert result is None

    def test_get_by_hash(self, document_store, sample_file):
        """Test retrieving document by hash."""
        doc = document_store.add_document(
            file_path=sample_file,
            entity="target"
        )

        retrieved = document_store.get_by_hash(doc.hash_sha256)

        assert retrieved is not None
        assert retrieved.doc_id == doc.doc_id

    def test_get_by_hash_not_found(self, document_store):
        """Test hash lookup for non-existent document."""
        result = document_store.get_by_hash("a" * 64)
        assert result is None

    def test_entity_separation(self, document_store, temp_dir):
        """Test that documents are correctly separated by entity."""
        # Create two different files
        target_file = temp_dir / "target_doc.txt"
        buyer_file = temp_dir / "buyer_doc.txt"
        target_file.write_text("Target company information")
        buyer_file.write_text("Buyer company information")

        # Add to different entities
        target_doc = document_store.add_document(
            file_path=target_file,
            entity="target"
        )
        buyer_doc = document_store.add_document(
            file_path=buyer_file,
            entity="buyer"
        )

        # Verify separation
        target_docs = document_store.get_documents_for_entity("target")
        buyer_docs = document_store.get_documents_for_entity("buyer")

        assert len(target_docs) == 1
        assert len(buyer_docs) == 1
        assert target_docs[0].doc_id == target_doc.doc_id
        assert buyer_docs[0].doc_id == buyer_doc.doc_id

    def test_authority_level_filtering(self, document_store, temp_dir):
        """Test filtering by authority level."""
        # Create files with different authority levels
        files = []
        for i, level in enumerate([1, 2, 3, 1]):
            f = temp_dir / f"doc_{i}.txt"
            f.write_text(f"Document {i} content")
            document_store.add_document(
                file_path=f,
                entity="target",
                authority_level=level
            )
            files.append(f)

        high_authority = document_store.get_high_authority_docs()
        discussion_notes = document_store.get_discussion_notes()

        assert len(high_authority) == 2  # Two level 1 docs
        assert len(discussion_notes) == 1  # One level 3 doc

    def test_list_documents_with_filters(self, document_store, temp_dir):
        """Test listing documents with various filters."""
        # Add multiple documents
        for i in range(3):
            f = temp_dir / f"target_doc_{i}.txt"
            f.write_text(f"Target content {i}")
            document_store.add_document(file_path=f, entity="target")

        for i in range(2):
            f = temp_dir / f"buyer_doc_{i}.txt"
            f.write_text(f"Buyer content {i}")
            document_store.add_document(file_path=f, entity="buyer")

        # Test filters
        all_docs = document_store.list_documents()
        target_only = document_store.list_documents(entity="target")
        buyer_only = document_store.list_documents(entity="buyer")

        assert len(all_docs) == 5
        assert len(target_only) == 3
        assert len(buyer_only) == 2

    def test_update_status(self, document_store, sample_file):
        """Test updating document status."""
        doc = document_store.add_document(
            file_path=sample_file,
            entity="target"
        )

        document_store.update_status(doc.doc_id, DocumentStatus.PROCESSED)

        updated = document_store.get_document(doc.doc_id)
        assert updated.status == DocumentStatus.PROCESSED.value

    def test_update_status_with_error(self, document_store, sample_file):
        """Test updating status with error message."""
        doc = document_store.add_document(
            file_path=sample_file,
            entity="target"
        )

        document_store.update_status(
            doc.doc_id,
            DocumentStatus.ERROR,
            "Extraction failed: file corrupted"
        )

        updated = document_store.get_document(doc.doc_id)
        assert updated.status == DocumentStatus.ERROR.value
        assert "corrupted" in updated.extraction_error


class TestDocumentStoreFromBytes:
    """Tests for adding documents from bytes (web upload scenario)."""

    def test_add_document_from_bytes(self, document_store):
        """Test adding document from raw bytes."""
        content = b"Document content from web upload"

        doc = document_store.add_document_from_bytes(
            file_bytes=content,
            filename="uploaded_file.txt",
            entity="target",
            authority_level=2,
            uploaded_by="web_user"
        )

        assert doc is not None
        assert doc.filename == "uploaded_file.txt"
        assert doc.entity == "target"
        assert doc.authority_level == 2
        assert doc.file_size_bytes == len(content)

    def test_duplicate_from_bytes(self, document_store):
        """Test duplicate detection from bytes."""
        content = b"Same content for duplicate test"

        doc1 = document_store.add_document_from_bytes(
            file_bytes=content,
            filename="first.txt",
            entity="target"
        )

        doc2 = document_store.add_document_from_bytes(
            file_bytes=content,
            filename="second.txt",  # Different name, same content
            entity="target"
        )

        # Should return same document
        assert doc1.doc_id == doc2.doc_id


class TestDocumentStorePersistence:
    """Tests for manifest save/load."""

    def test_manifest_persists(self, temp_dir, sample_file):
        """Test that documents persist across store instances."""
        store_dir = temp_dir / "documents"

        # Create store and add document
        DocumentStore.reset_instance()
        store1 = DocumentStore(base_dir=store_dir)
        doc = store1.add_document(
            file_path=sample_file,
            entity="target"
        )
        doc_id = doc.doc_id

        # Create new store instance (simulating restart)
        DocumentStore.reset_instance()
        store2 = DocumentStore(base_dir=store_dir)

        # Document should still exist
        retrieved = store2.get_document(doc_id)
        assert retrieved is not None
        assert retrieved.filename == sample_file.name

        DocumentStore.reset_instance()

    def test_manifest_file_created(self, document_store, sample_file):
        """Test that manifest.json is created."""
        document_store.add_document(
            file_path=sample_file,
            entity="target"
        )

        manifest_path = document_store.base_dir / "manifest.json"
        assert manifest_path.exists()


class TestDocumentStoreStatistics:
    """Tests for statistics and reporting."""

    def test_get_statistics(self, document_store, temp_dir):
        """Test statistics calculation."""
        # Add various documents
        for i in range(3):
            f = temp_dir / f"target_{i}.txt"
            f.write_text(f"Content {i}")
            document_store.add_document(file_path=f, entity="target", authority_level=1)

        for i in range(2):
            f = temp_dir / f"buyer_{i}.txt"
            f.write_text(f"Buyer content {i}")
            document_store.add_document(file_path=f, entity="buyer", authority_level=3)

        stats = document_store.get_statistics()

        assert stats["total_documents"] == 5
        assert stats["by_entity"]["target"] == 3
        assert stats["by_entity"]["buyer"] == 2
        assert stats["by_authority"]["data_room"] == 3
        assert stats["by_authority"]["discussion_notes"] == 2


class TestTextExtraction:
    """Tests for text extraction functionality."""

    def test_extract_text_file(self, document_store, sample_file):
        """Test extracting text from plain text file."""
        doc = document_store.add_document(
            file_path=sample_file,
            entity="target"
        )

        text = document_store.extract_text(doc.doc_id)

        assert text is not None
        assert "sample document" in text
        assert "[PAGE 1]" in text

        # Status should be updated
        updated = document_store.get_document(doc.doc_id)
        assert updated.status == DocumentStatus.PROCESSED.value

    def test_get_extracted_text(self, document_store, sample_file):
        """Test retrieving extracted text."""
        doc = document_store.add_document(
            file_path=sample_file,
            entity="target"
        )

        # First call extracts
        text1 = document_store.get_extracted_text(doc.doc_id)

        # Second call retrieves from file
        text2 = document_store.get_extracted_text(doc.doc_id)

        assert text1 == text2
        assert "sample document" in text1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
