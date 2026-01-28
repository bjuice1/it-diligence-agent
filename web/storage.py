"""
Cloud Storage Module for IT Due Diligence Agent

Phase 5: Unified storage interface supporting local filesystem and S3-compatible storage.
Supports AWS S3, Cloudflare R2, MinIO, and other S3-compatible services.
"""

import os
import hashlib
import logging
import mimetypes
from abc import ABC, abstractmethod
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, BinaryIO, Dict, Any, List, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Storage configuration from environment
STORAGE_TYPE = os.environ.get('STORAGE_TYPE', 'local')  # 'local' or 's3'
S3_BUCKET = os.environ.get('S3_BUCKET', 'diligence-documents')
S3_REGION = os.environ.get('S3_REGION', 'us-east-1')
S3_ENDPOINT = os.environ.get('S3_ENDPOINT', '')  # For R2, MinIO, etc.
S3_ACCESS_KEY = os.environ.get('S3_ACCESS_KEY', '')
S3_SECRET_KEY = os.environ.get('S3_SECRET_KEY', '')
S3_PUBLIC_URL = os.environ.get('S3_PUBLIC_URL', '')  # Optional CDN URL


@dataclass
class StoredFile:
    """Represents a file in storage."""
    key: str  # Storage key/path
    filename: str  # Original filename
    size: int  # File size in bytes
    content_type: str  # MIME type
    hash: str  # SHA-256 hash
    storage_type: str  # 'local' or 's3'
    created_at: datetime
    metadata: Dict[str, str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            'key': self.key,
            'filename': self.filename,
            'size': self.size,
            'content_type': self.content_type,
            'hash': self.hash,
            'storage_type': self.storage_type,
            'created_at': self.created_at.isoformat(),
            'metadata': self.metadata,
        }


class StorageBackend(ABC):
    """Abstract base class for storage backends."""

    @abstractmethod
    def upload(
        self,
        file: BinaryIO,
        key: str,
        filename: str,
        content_type: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> StoredFile:
        """Upload a file to storage."""
        pass

    @abstractmethod
    def download(self, key: str) -> Tuple[BinaryIO, StoredFile]:
        """Download a file from storage."""
        pass

    @abstractmethod
    def delete(self, key: str) -> bool:
        """Delete a file from storage."""
        pass

    @abstractmethod
    def exists(self, key: str) -> bool:
        """Check if a file exists."""
        pass

    @abstractmethod
    def get_url(self, key: str, expires_in: int = 3600) -> str:
        """Get a URL for accessing the file."""
        pass

    @abstractmethod
    def list_files(self, prefix: str = '') -> List[StoredFile]:
        """List files with optional prefix filter."""
        pass

    def compute_hash(self, file: BinaryIO) -> str:
        """Compute SHA-256 hash of file contents."""
        sha256 = hashlib.sha256()
        file.seek(0)
        for chunk in iter(lambda: file.read(8192), b''):
            sha256.update(chunk)
        file.seek(0)
        return sha256.hexdigest()


class LocalStorage(StorageBackend):
    """Local filesystem storage backend."""

    def __init__(self, base_path: Optional[Path] = None):
        if base_path is None:
            from config_v2 import OUTPUT_DIR
            base_path = OUTPUT_DIR / 'documents'
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _get_full_path(self, key: str) -> Path:
        """Get full filesystem path for a key."""
        # Sanitize key to prevent path traversal
        safe_key = key.replace('..', '').lstrip('/')
        return self.base_path / safe_key

    def upload(
        self,
        file: BinaryIO,
        key: str,
        filename: str,
        content_type: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> StoredFile:
        """Upload a file to local storage."""
        full_path = self._get_full_path(key)
        full_path.parent.mkdir(parents=True, exist_ok=True)

        # Compute hash before saving
        file_hash = self.compute_hash(file)

        # Determine content type
        if content_type is None:
            content_type, _ = mimetypes.guess_type(filename)
            content_type = content_type or 'application/octet-stream'

        # Write file
        file.seek(0)
        with open(full_path, 'wb') as f:
            while True:
                chunk = file.read(8192)
                if not chunk:
                    break
                f.write(chunk)

        # Get file size
        size = full_path.stat().st_size

        # Save metadata to sidecar file
        meta = metadata or {}
        meta['filename'] = filename
        meta['content_type'] = content_type
        meta['hash'] = file_hash
        meta['created_at'] = datetime.utcnow().isoformat()

        meta_path = full_path.with_suffix(full_path.suffix + '.meta')
        import json
        with open(meta_path, 'w') as f:
            json.dump(meta, f)

        return StoredFile(
            key=key,
            filename=filename,
            size=size,
            content_type=content_type,
            hash=file_hash,
            storage_type='local',
            created_at=datetime.utcnow(),
            metadata=metadata or {}
        )

    def download(self, key: str) -> Tuple[BinaryIO, StoredFile]:
        """Download a file from local storage."""
        full_path = self._get_full_path(key)

        if not full_path.exists():
            raise FileNotFoundError(f"File not found: {key}")

        # Load metadata
        meta_path = full_path.with_suffix(full_path.suffix + '.meta')
        metadata = {}
        if meta_path.exists():
            import json
            with open(meta_path, 'r') as f:
                metadata = json.load(f)

        file = open(full_path, 'rb')
        stored_file = StoredFile(
            key=key,
            filename=metadata.get('filename', full_path.name),
            size=full_path.stat().st_size,
            content_type=metadata.get('content_type', 'application/octet-stream'),
            hash=metadata.get('hash', ''),
            storage_type='local',
            created_at=datetime.fromisoformat(metadata['created_at']) if metadata.get('created_at') else datetime.utcnow(),
            metadata={k: v for k, v in metadata.items() if k not in ['filename', 'content_type', 'hash', 'created_at']}
        )

        return file, stored_file

    def delete(self, key: str) -> bool:
        """Delete a file from local storage."""
        full_path = self._get_full_path(key)
        meta_path = full_path.with_suffix(full_path.suffix + '.meta')

        try:
            if full_path.exists():
                full_path.unlink()
            if meta_path.exists():
                meta_path.unlink()
            return True
        except Exception as e:
            logger.error(f"Error deleting file {key}: {e}")
            return False

    def exists(self, key: str) -> bool:
        """Check if a file exists."""
        return self._get_full_path(key).exists()

    def get_url(self, key: str, expires_in: int = 3600) -> str:
        """Get URL for local file (returns relative path for local serving)."""
        # For local storage, return a path that can be served by Flask
        return f"/documents/{key}"

    def list_files(self, prefix: str = '') -> List[StoredFile]:
        """List files with optional prefix filter."""
        files = []
        search_path = self.base_path / prefix if prefix else self.base_path

        if not search_path.exists():
            return files

        for path in search_path.rglob('*'):
            if path.is_file() and not path.suffix == '.meta':
                key = str(path.relative_to(self.base_path))

                # Load metadata
                meta_path = path.with_suffix(path.suffix + '.meta')
                metadata = {}
                if meta_path.exists():
                    import json
                    with open(meta_path, 'r') as f:
                        metadata = json.load(f)

                files.append(StoredFile(
                    key=key,
                    filename=metadata.get('filename', path.name),
                    size=path.stat().st_size,
                    content_type=metadata.get('content_type', 'application/octet-stream'),
                    hash=metadata.get('hash', ''),
                    storage_type='local',
                    created_at=datetime.fromisoformat(metadata['created_at']) if metadata.get('created_at') else datetime.fromtimestamp(path.stat().st_mtime),
                    metadata={}
                ))

        return files


class S3Storage(StorageBackend):
    """S3-compatible cloud storage backend."""

    def __init__(
        self,
        bucket: Optional[str] = None,
        region: Optional[str] = None,
        endpoint_url: Optional[str] = None,
        access_key: Optional[str] = None,
        secret_key: Optional[str] = None
    ):
        import boto3
        from botocore.config import Config

        self.bucket = bucket or S3_BUCKET
        self.region = region or S3_REGION
        self.endpoint_url = endpoint_url or S3_ENDPOINT or None

        # Configure boto3 client
        config = Config(
            signature_version='s3v4',
            retries={'max_attempts': 3, 'mode': 'adaptive'}
        )

        client_kwargs = {
            'service_name': 's3',
            'region_name': self.region,
            'config': config,
        }

        # Use custom credentials if provided
        if access_key or S3_ACCESS_KEY:
            client_kwargs['aws_access_key_id'] = access_key or S3_ACCESS_KEY
            client_kwargs['aws_secret_access_key'] = secret_key or S3_SECRET_KEY

        # Use custom endpoint for R2, MinIO, etc.
        if self.endpoint_url:
            client_kwargs['endpoint_url'] = self.endpoint_url

        self.client = boto3.client(**client_kwargs)
        self.resource = boto3.resource(**client_kwargs)

    def upload(
        self,
        file: BinaryIO,
        key: str,
        filename: str,
        content_type: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> StoredFile:
        """Upload a file to S3."""
        # Compute hash
        file_hash = self.compute_hash(file)

        # Determine content type
        if content_type is None:
            content_type, _ = mimetypes.guess_type(filename)
            content_type = content_type or 'application/octet-stream'

        # Prepare metadata
        s3_metadata = metadata or {}
        s3_metadata['original-filename'] = filename
        s3_metadata['sha256'] = file_hash

        # Upload to S3
        file.seek(0)
        self.client.upload_fileobj(
            file,
            self.bucket,
            key,
            ExtraArgs={
                'ContentType': content_type,
                'Metadata': s3_metadata
            }
        )

        # Get file size
        file.seek(0, 2)  # Seek to end
        size = file.tell()
        file.seek(0)

        return StoredFile(
            key=key,
            filename=filename,
            size=size,
            content_type=content_type,
            hash=file_hash,
            storage_type='s3',
            created_at=datetime.utcnow(),
            metadata=metadata or {}
        )

    def download(self, key: str) -> Tuple[BinaryIO, StoredFile]:
        """Download a file from S3."""
        import io

        # Get object metadata first
        head = self.client.head_object(Bucket=self.bucket, Key=key)

        # Download to memory
        buffer = io.BytesIO()
        self.client.download_fileobj(self.bucket, key, buffer)
        buffer.seek(0)

        metadata = head.get('Metadata', {})
        stored_file = StoredFile(
            key=key,
            filename=metadata.get('original-filename', key.split('/')[-1]),
            size=head['ContentLength'],
            content_type=head.get('ContentType', 'application/octet-stream'),
            hash=metadata.get('sha256', ''),
            storage_type='s3',
            created_at=head.get('LastModified', datetime.utcnow()),
            metadata=metadata
        )

        return buffer, stored_file

    def delete(self, key: str) -> bool:
        """Delete a file from S3."""
        try:
            self.client.delete_object(Bucket=self.bucket, Key=key)
            return True
        except Exception as e:
            logger.error(f"Error deleting S3 object {key}: {e}")
            return False

    def exists(self, key: str) -> bool:
        """Check if a file exists in S3."""
        try:
            self.client.head_object(Bucket=self.bucket, Key=key)
            return True
        except self.client.exceptions.ClientError:
            return False

    def get_url(self, key: str, expires_in: int = 3600) -> str:
        """Get a presigned URL for accessing the file."""
        # If public URL is configured (CDN), use that
        if S3_PUBLIC_URL:
            return f"{S3_PUBLIC_URL.rstrip('/')}/{key}"

        # Generate presigned URL
        url = self.client.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': self.bucket,
                'Key': key
            },
            ExpiresIn=expires_in
        )
        return url

    def list_files(self, prefix: str = '') -> List[StoredFile]:
        """List files in S3 with optional prefix filter."""
        files = []

        paginator = self.client.get_paginator('list_objects_v2')
        pages = paginator.paginate(Bucket=self.bucket, Prefix=prefix)

        for page in pages:
            for obj in page.get('Contents', []):
                # Get metadata for each object
                try:
                    head = self.client.head_object(Bucket=self.bucket, Key=obj['Key'])
                    metadata = head.get('Metadata', {})

                    files.append(StoredFile(
                        key=obj['Key'],
                        filename=metadata.get('original-filename', obj['Key'].split('/')[-1]),
                        size=obj['Size'],
                        content_type=head.get('ContentType', 'application/octet-stream'),
                        hash=metadata.get('sha256', ''),
                        storage_type='s3',
                        created_at=obj['LastModified'],
                        metadata=metadata
                    ))
                except Exception as e:
                    logger.warning(f"Error getting metadata for {obj['Key']}: {e}")

        return files

    def create_bucket_if_not_exists(self):
        """Create the bucket if it doesn't exist."""
        try:
            self.client.head_bucket(Bucket=self.bucket)
        except self.client.exceptions.ClientError:
            # Bucket doesn't exist, create it
            if self.region == 'us-east-1':
                self.client.create_bucket(Bucket=self.bucket)
            else:
                self.client.create_bucket(
                    Bucket=self.bucket,
                    CreateBucketConfiguration={'LocationConstraint': self.region}
                )
            logger.info(f"Created S3 bucket: {self.bucket}")


class StorageService:
    """
    Unified storage service that abstracts the storage backend.

    Provides a consistent interface for file operations regardless of
    whether files are stored locally or in S3.

    Phase 6 Update: Supports multi-tenancy with tenant-namespaced storage.
    Storage layout:
    - Without tenancy: deals/{deal_id}/documents/{entity}/{filename}
    - With tenancy: tenants/{tenant_id}/deals/{deal_id}/documents/{entity}/{filename}
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._backend: Optional[StorageBackend] = None
        self._multi_tenancy_enabled = False
        self._initialized = True

    def initialize(self, storage_type: Optional[str] = None, multi_tenancy: bool = False):
        """Initialize the storage backend."""
        storage_type = storage_type or STORAGE_TYPE
        self._multi_tenancy_enabled = multi_tenancy or os.environ.get('USE_MULTI_TENANCY', 'false').lower() == 'true'

        if storage_type == 's3':
            if not S3_ACCESS_KEY or not S3_SECRET_KEY:
                logger.warning("S3 credentials not configured, falling back to local storage")
                self._backend = LocalStorage()
            else:
                try:
                    self._backend = S3Storage()
                    logger.info(f"S3 storage initialized: bucket={S3_BUCKET}")
                except Exception as e:
                    logger.error(f"Failed to initialize S3 storage: {e}")
                    self._backend = LocalStorage()
        else:
            self._backend = LocalStorage()
            logger.info("Local storage initialized")

        if self._multi_tenancy_enabled:
            logger.info("Multi-tenancy storage namespacing enabled")

    @property
    def backend(self) -> StorageBackend:
        """Get the storage backend, initializing if needed."""
        if self._backend is None:
            self.initialize()
        return self._backend

    def _get_current_tenant_id(self) -> Optional[str]:
        """Get current tenant ID from Flask context."""
        try:
            from flask import g
            return getattr(g, 'tenant_id', None)
        except RuntimeError:
            # Not in Flask request context
            return None

    def _build_key(self, deal_id: str, entity: str, filename: str, tenant_id: Optional[str] = None) -> str:
        """
        Build storage key with optional tenant namespace.

        Args:
            deal_id: The deal ID
            entity: Entity type ('target' or 'buyer')
            filename: Original filename
            tenant_id: Optional tenant ID (uses current tenant if not provided)

        Returns:
            Storage key path
        """
        # Get tenant ID from argument or context
        effective_tenant_id = tenant_id
        if effective_tenant_id is None and self._multi_tenancy_enabled:
            effective_tenant_id = self._get_current_tenant_id()

        # Build key with or without tenant namespace
        if effective_tenant_id and self._multi_tenancy_enabled:
            return f"tenants/{effective_tenant_id}/deals/{deal_id}/documents/{entity}/{filename}"
        else:
            return f"deals/{deal_id}/documents/{entity}/{filename}"

    def _build_prefix(self, deal_id: str, entity: Optional[str] = None, tenant_id: Optional[str] = None) -> str:
        """
        Build storage prefix for listing files.

        Args:
            deal_id: The deal ID
            entity: Optional entity type filter
            tenant_id: Optional tenant ID (uses current tenant if not provided)

        Returns:
            Storage prefix path
        """
        effective_tenant_id = tenant_id
        if effective_tenant_id is None and self._multi_tenancy_enabled:
            effective_tenant_id = self._get_current_tenant_id()

        if effective_tenant_id and self._multi_tenancy_enabled:
            prefix = f"tenants/{effective_tenant_id}/deals/{deal_id}/documents/"
        else:
            prefix = f"deals/{deal_id}/documents/"

        if entity:
            prefix += f"{entity}/"

        return prefix

    def upload_document(
        self,
        file: BinaryIO,
        deal_id: str,
        entity: str,
        filename: str,
        content_type: Optional[str] = None,
        tenant_id: Optional[str] = None
    ) -> StoredFile:
        """
        Upload a document for a deal.

        Storage layout depends on multi-tenancy setting:
        - Without: deals/{deal_id}/documents/{entity}/{filename}
        - With: tenants/{tenant_id}/deals/{deal_id}/documents/{entity}/{filename}
        """
        # Build storage key with tenant namespace if enabled
        key = self._build_key(deal_id, entity, filename, tenant_id)

        # Get effective tenant ID for metadata
        effective_tenant_id = tenant_id
        if effective_tenant_id is None and self._multi_tenancy_enabled:
            effective_tenant_id = self._get_current_tenant_id()

        metadata = {
            'deal_id': deal_id,
            'entity': entity,
        }
        if effective_tenant_id:
            metadata['tenant_id'] = effective_tenant_id

        return self.backend.upload(
            file=file,
            key=key,
            filename=filename,
            content_type=content_type,
            metadata=metadata
        )

    def get_document(self, key: str, validate_tenant: bool = True) -> Tuple[BinaryIO, StoredFile]:
        """
        Get a document by its storage key.

        Args:
            key: Storage key
            validate_tenant: If True, validates the key belongs to current tenant
        """
        if validate_tenant and self._multi_tenancy_enabled:
            current_tenant = self._get_current_tenant_id()
            if current_tenant:
                # Check if key starts with expected tenant prefix
                expected_prefix = f"tenants/{current_tenant}/"
                if not key.startswith(expected_prefix) and not key.startswith('deals/'):
                    # Key belongs to a different tenant
                    raise PermissionError(f"Access denied: document belongs to a different organization")

        return self.backend.download(key)

    def delete_document(self, key: str, validate_tenant: bool = True) -> bool:
        """Delete a document."""
        if validate_tenant and self._multi_tenancy_enabled:
            current_tenant = self._get_current_tenant_id()
            if current_tenant:
                expected_prefix = f"tenants/{current_tenant}/"
                if not key.startswith(expected_prefix) and not key.startswith('deals/'):
                    raise PermissionError(f"Access denied: cannot delete document from different organization")

        return self.backend.delete(key)

    def get_document_url(self, key: str, expires_in: int = 3600) -> str:
        """Get a URL for accessing a document."""
        return self.backend.get_url(key, expires_in)

    def list_deal_documents(
        self,
        deal_id: str,
        entity: Optional[str] = None,
        tenant_id: Optional[str] = None
    ) -> List[StoredFile]:
        """List all documents for a deal."""
        prefix = self._build_prefix(deal_id, entity, tenant_id)
        return self.backend.list_files(prefix)

    def list_tenant_documents(self, tenant_id: Optional[str] = None) -> List[StoredFile]:
        """List all documents for a tenant."""
        effective_tenant_id = tenant_id or self._get_current_tenant_id()

        if effective_tenant_id and self._multi_tenancy_enabled:
            prefix = f"tenants/{effective_tenant_id}/"
        else:
            prefix = "deals/"

        return self.backend.list_files(prefix)

    def document_exists(self, key: str) -> bool:
        """Check if a document exists."""
        return self.backend.exists(key)

    @property
    def storage_type(self) -> str:
        """Get the current storage type."""
        if isinstance(self.backend, S3Storage):
            return 's3'
        return 'local'

    @property
    def multi_tenancy_enabled(self) -> bool:
        """Check if multi-tenancy storage is enabled."""
        return self._multi_tenancy_enabled


# Global storage service instance
storage_service = StorageService()


def get_storage() -> StorageService:
    """Get the storage service instance."""
    return storage_service


# Export
__all__ = [
    'StorageService',
    'StorageBackend',
    'LocalStorage',
    'S3Storage',
    'StoredFile',
    'get_storage',
    'storage_service',
]
