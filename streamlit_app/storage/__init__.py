"""
Storage Module

Handles file uploads, temporary storage, and document persistence.
"""

from .file_manager import (
    FileManager,
    UploadedFile,
    save_uploaded_files,
    load_document_text,
    cleanup_temp_files,
    get_file_info,
)

__all__ = [
    "FileManager",
    "UploadedFile",
    "save_uploaded_files",
    "load_document_text",
    "cleanup_temp_files",
    "get_file_info",
]
