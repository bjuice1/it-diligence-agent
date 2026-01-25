"""
File Manager - Document Upload and Storage

Handles file uploads, validation, persistence, and document loading.

Steps 11-18 of the alignment plan.
"""

import os
import tempfile
import shutil
import hashlib
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, Tuple, BinaryIO
from datetime import datetime
import json


# =============================================================================
# CONFIGURATION
# =============================================================================

# File size limits
MAX_FILE_SIZE_MB = 50
MAX_TOTAL_SIZE_MB = 200

# Allowed file types
ALLOWED_EXTENSIONS = {
    ".pdf": "application/pdf",
    ".txt": "text/plain",
    ".md": "text/markdown",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}

# Entity types for document organization
ENTITY_TARGET = "target"
ENTITY_BUYER = "buyer"


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class UploadedFile:
    """Represents an uploaded file."""
    filename: str
    original_name: str
    path: Path
    size_bytes: int
    content_hash: str
    entity: str
    mime_type: str
    uploaded_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "filename": self.filename,
            "original_name": self.original_name,
            "path": str(self.path),
            "size_bytes": self.size_bytes,
            "content_hash": self.content_hash,
            "entity": self.entity,
            "mime_type": self.mime_type,
            "uploaded_at": self.uploaded_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UploadedFile":
        """Deserialize from dictionary."""
        return cls(
            filename=data["filename"],
            original_name=data["original_name"],
            path=Path(data["path"]),
            size_bytes=data["size_bytes"],
            content_hash=data["content_hash"],
            entity=data["entity"],
            mime_type=data["mime_type"],
            uploaded_at=data.get("uploaded_at", datetime.now().isoformat()),
        )


@dataclass
class FileValidationResult:
    """Result of file validation."""
    valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


# =============================================================================
# FILE MANAGER
# =============================================================================

class FileManager:
    """
    Manages file uploads and document storage.

    Provides:
    - Secure file upload handling
    - File validation (type, size, duplicates)
    - Temporary storage with cleanup
    - Document text extraction
    - File hash-based deduplication
    """

    def __init__(self, base_dir: Optional[Path] = None):
        """
        Initialize file manager.

        Args:
            base_dir: Base directory for file storage. If None, uses temp dir.
        """
        if base_dir is None:
            self.base_dir = Path(tempfile.mkdtemp(prefix="itdd_"))
            self._is_temp = True
        else:
            self.base_dir = Path(base_dir)
            self.base_dir.mkdir(parents=True, exist_ok=True)
            self._is_temp = False

        self.files: Dict[str, UploadedFile] = {}
        self._registry_path = self.base_dir / ".file_registry.json"

    # -------------------------------------------------------------------------
    # File Operations
    # -------------------------------------------------------------------------

    def save_file(
        self,
        file_obj: BinaryIO,
        filename: str,
        entity: str = ENTITY_TARGET
    ) -> Tuple[UploadedFile, FileValidationResult]:
        """
        Save an uploaded file.

        Args:
            file_obj: File-like object with read() method
            filename: Original filename
            entity: Entity type (target or buyer)

        Returns:
            Tuple of (UploadedFile, FileValidationResult)
        """
        # Read content
        content = file_obj.read()

        # Validate
        validation = self._validate_file(filename, content)
        if not validation.valid:
            return None, validation

        # Compute hash
        content_hash = self._compute_hash(content)

        # Check for duplicates
        if self._is_duplicate(content_hash):
            validation.warnings.append(f"Duplicate file detected: {filename}")
            # Return existing file
            for f in self.files.values():
                if f.content_hash == content_hash:
                    return f, validation

        # Create entity directory
        entity_dir = self.base_dir / entity
        entity_dir.mkdir(parents=True, exist_ok=True)

        # Generate safe filename
        safe_name = self._sanitize_filename(filename)
        file_path = entity_dir / safe_name

        # Handle filename collisions
        counter = 1
        while file_path.exists():
            stem = Path(safe_name).stem
            suffix = Path(safe_name).suffix
            file_path = entity_dir / f"{stem}_{counter}{suffix}"
            counter += 1

        # Write file
        with open(file_path, "wb") as f:
            f.write(content)

        # Create file record
        uploaded_file = UploadedFile(
            filename=file_path.name,
            original_name=filename,
            path=file_path,
            size_bytes=len(content),
            content_hash=content_hash,
            entity=entity,
            mime_type=ALLOWED_EXTENSIONS.get(Path(filename).suffix.lower(), "application/octet-stream"),
        )

        # Register file
        self.files[content_hash] = uploaded_file
        self._save_registry()

        return uploaded_file, validation

    def save_notes(
        self,
        notes_text: str,
        entity: str = ENTITY_TARGET
    ) -> Optional[UploadedFile]:
        """
        Save notes text as a file.

        Args:
            notes_text: Notes content
            entity: Entity type

        Returns:
            UploadedFile if notes were saved, None if empty
        """
        if not notes_text or not notes_text.strip():
            return None

        # Create entity directory
        entity_dir = self.base_dir / entity
        entity_dir.mkdir(parents=True, exist_ok=True)

        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"meeting_notes_{timestamp}.txt"
        file_path = entity_dir / filename

        # Prepare content
        content = f"# Meeting Notes / Discussion Points\n\n{notes_text}"
        content_bytes = content.encode("utf-8")

        # Write file
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        # Create file record
        uploaded_file = UploadedFile(
            filename=filename,
            original_name=filename,
            path=file_path,
            size_bytes=len(content_bytes),
            content_hash=self._compute_hash(content_bytes),
            entity=entity,
            mime_type="text/plain",
        )

        self.files[uploaded_file.content_hash] = uploaded_file
        self._save_registry()

        return uploaded_file

    def get_files(self, entity: Optional[str] = None) -> List[UploadedFile]:
        """
        Get all uploaded files.

        Args:
            entity: Filter by entity type (optional)

        Returns:
            List of UploadedFile objects
        """
        files = list(self.files.values())
        if entity:
            files = [f for f in files if f.entity == entity]
        return files

    def get_file_by_hash(self, content_hash: str) -> Optional[UploadedFile]:
        """Get a file by its content hash."""
        return self.files.get(content_hash)

    def remove_file(self, content_hash: str) -> bool:
        """
        Remove a file by its content hash.

        Returns:
            True if file was removed, False if not found
        """
        if content_hash not in self.files:
            return False

        file_info = self.files[content_hash]

        # Delete physical file
        if file_info.path.exists():
            file_info.path.unlink()

        # Remove from registry
        del self.files[content_hash]
        self._save_registry()

        return True

    def clear_all(self):
        """Remove all uploaded files."""
        for file_info in list(self.files.values()):
            if file_info.path.exists():
                file_info.path.unlink()

        self.files = {}
        self._save_registry()

    # -------------------------------------------------------------------------
    # Document Loading
    # -------------------------------------------------------------------------

    def load_document_text(self) -> str:
        """
        Load and combine all documents with entity markers.

        Returns:
            Combined document text with entity markers
        """
        try:
            # Import parser - handle import errors gracefully
            from ingestion.pdf_parser import PDFParser
            parser = PDFParser()
        except ImportError:
            parser = None

        combined_text = []

        # Process TARGET documents
        target_files = self.get_files(ENTITY_TARGET)
        if target_files:
            combined_text.append("=" * 80)
            combined_text.append("# ENTITY: TARGET")
            combined_text.append("# All documents below describe the TARGET company (being evaluated)")
            combined_text.append("=" * 80 + "\n")

            for file_info in target_files:
                doc_text = self._extract_text(file_info, parser)
                if doc_text:
                    combined_text.append(f"\n# Document: {file_info.original_name}")
                    combined_text.append("# Entity: TARGET")
                    combined_text.append(doc_text)
                    combined_text.append("\n" + "-" * 40 + "\n")

        # Process BUYER documents
        buyer_files = self.get_files(ENTITY_BUYER)
        if buyer_files:
            combined_text.append("\n" + "=" * 80)
            combined_text.append("# ENTITY: BUYER")
            combined_text.append("# All documents below describe the BUYER company (for integration context)")
            combined_text.append("=" * 80 + "\n")

            for file_info in buyer_files:
                doc_text = self._extract_text(file_info, parser)
                if doc_text:
                    combined_text.append(f"\n# Document: {file_info.original_name}")
                    combined_text.append("# Entity: BUYER")
                    combined_text.append(doc_text)
                    combined_text.append("\n" + "-" * 40 + "\n")

        return "\n".join(combined_text)

    def _extract_text(self, file_info: UploadedFile, parser) -> Optional[str]:
        """Extract text from a file."""
        try:
            suffix = file_info.path.suffix.lower()

            if suffix == ".pdf" and parser:
                parsed = parser.parse_file(file_info.path)
                return parsed.raw_text

            elif suffix in [".txt", ".md"]:
                with open(file_info.path, "r", encoding="utf-8") as f:
                    return f.read()

            elif suffix == ".docx":
                # Use pdf_parser's docx handling if available
                if parser and hasattr(parser, "parse_file"):
                    parsed = parser.parse_file(file_info.path)
                    return parsed.raw_text
                return None

            else:
                return None

        except Exception as e:
            print(f"Error extracting text from {file_info.filename}: {e}")
            return None

    # -------------------------------------------------------------------------
    # Validation
    # -------------------------------------------------------------------------

    def _validate_file(self, filename: str, content: bytes) -> FileValidationResult:
        """Validate a file before saving."""
        errors = []
        warnings = []

        # Check extension
        suffix = Path(filename).suffix.lower()
        if suffix not in ALLOWED_EXTENSIONS:
            errors.append(f"File type not allowed: {suffix}. Allowed: {', '.join(ALLOWED_EXTENSIONS.keys())}")

        # Check file size
        size_mb = len(content) / (1024 * 1024)
        if size_mb > MAX_FILE_SIZE_MB:
            errors.append(f"File too large: {size_mb:.1f}MB. Maximum: {MAX_FILE_SIZE_MB}MB")

        # Check total size
        total_size = sum(f.size_bytes for f in self.files.values()) + len(content)
        total_mb = total_size / (1024 * 1024)
        if total_mb > MAX_TOTAL_SIZE_MB:
            errors.append(f"Total upload size exceeded: {total_mb:.1f}MB. Maximum: {MAX_TOTAL_SIZE_MB}MB")

        # Check for empty file
        if len(content) == 0:
            errors.append("Empty file")

        # Warn about small files
        if len(content) < 1000:
            warnings.append(f"File is very small ({len(content)} bytes)")

        return FileValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )

    def _is_duplicate(self, content_hash: str) -> bool:
        """Check if a file with this hash already exists."""
        return content_hash in self.files

    # -------------------------------------------------------------------------
    # Utilities
    # -------------------------------------------------------------------------

    def _compute_hash(self, content: bytes) -> str:
        """Compute SHA256 hash of content."""
        return hashlib.sha256(content).hexdigest()[:16]

    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for safe storage."""
        # Replace problematic characters
        safe = filename.replace(" ", "_")
        safe = "".join(c for c in safe if c.isalnum() or c in "._-")
        return safe or "unnamed_file"

    def _save_registry(self):
        """Save file registry to disk."""
        registry = {
            hash_: file.to_dict()
            for hash_, file in self.files.items()
        }
        with open(self._registry_path, "w") as f:
            json.dump(registry, f, indent=2)

    def _load_registry(self):
        """Load file registry from disk."""
        if self._registry_path.exists():
            try:
                with open(self._registry_path, "r") as f:
                    registry = json.load(f)
                self.files = {
                    hash_: UploadedFile.from_dict(data)
                    for hash_, data in registry.items()
                }
            except Exception as e:
                print(f"Error loading file registry: {e}")
                self.files = {}

    # -------------------------------------------------------------------------
    # Cleanup
    # -------------------------------------------------------------------------

    def cleanup(self):
        """Clean up temporary storage."""
        if self._is_temp and self.base_dir.exists():
            shutil.rmtree(self.base_dir)

    def __del__(self):
        """Cleanup on destruction."""
        # Only cleanup temp directories
        if self._is_temp:
            self.cleanup()


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def save_uploaded_files(
    files: List[Any],  # Streamlit UploadedFile objects
    base_dir: Path,
    entity: str = ENTITY_TARGET
) -> Tuple[List[UploadedFile], List[str]]:
    """
    Save multiple uploaded files.

    Args:
        files: List of Streamlit UploadedFile objects
        base_dir: Base directory for storage
        entity: Entity type (target or buyer)

    Returns:
        Tuple of (saved files, error messages)
    """
    manager = FileManager(base_dir)
    saved = []
    errors = []

    for file in files:
        uploaded, validation = manager.save_file(file, file.name, entity)
        if uploaded:
            saved.append(uploaded)
        errors.extend(validation.errors)

    return saved, errors


def load_document_text(base_dir: Path) -> str:
    """Load combined document text from a directory."""
    manager = FileManager(base_dir)
    manager._load_registry()
    return manager.load_document_text()


def cleanup_temp_files(base_dir: Path):
    """Clean up temporary files in a directory."""
    if base_dir.exists():
        shutil.rmtree(base_dir)


def get_file_info(file_obj: Any) -> Dict[str, Any]:
    """
    Get info about an uploaded file.

    Args:
        file_obj: Streamlit UploadedFile object

    Returns:
        Dictionary with file info
    """
    content = file_obj.read()
    file_obj.seek(0)  # Reset file pointer

    return {
        "name": file_obj.name,
        "size_bytes": len(content),
        "size_mb": len(content) / (1024 * 1024),
        "extension": Path(file_obj.name).suffix.lower(),
        "hash": hashlib.sha256(content).hexdigest()[:16],
        "valid_type": Path(file_obj.name).suffix.lower() in ALLOWED_EXTENSIONS,
    }
