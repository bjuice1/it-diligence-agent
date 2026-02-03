# IT Due Diligence Agent - Storage Architecture

## Directory Structure

```
it-diligence-agent/
├── uploads/                    # User document uploads
│   ├── target/                 # Target company documents
│   │   ├── data_room/          # Authority level 1 (highest)
│   │   ├── correspondence/     # Authority level 2
│   │   ├── notes/              # Authority level 3 (lowest)
│   │   └── extracted/          # Extracted text files
│   ├── buyer/                  # Buyer company documents
│   │   ├── data_room/
│   │   ├── correspondence/
│   │   ├── notes/
│   │   └── extracted/
│   ├── deals/                  # StorageService deals (web uploads)
│   ├── tenants/                # Multi-tenant storage (if enabled)
│   └── manifest.json           # Document registry
│
└── output/                     # Analysis outputs
    ├── runs/                   # Timestamped run directories
    │   ├── 2026-01-28_143052_target-name/
    │   │   ├── metadata.json
    │   │   ├── facts/
    │   │   ├── findings/
    │   │   ├── reports/
    │   │   ├── exports/
    │   │   ├── documents/
    │   │   └── logs/
    │   ├── .latest             # Pointer to latest run
    │   └── latest -> ...       # Symlink (Unix only)
    ├── archive/                # Archived runs
    ├── validation/             # Validation state
    └── audit/                  # Audit logs
```

## Stores Package

All persistence is handled through the `stores/` package:

### FactStore (`stores/fact_store.py`)
Central repository for extracted facts. **Requires deal_id for data isolation (V2.3).**

```python
from stores import FactStore

# Initialize with deal_id for proper isolation
store = FactStore(deal_id="deal_abc123")

# Add a fact (deal_id inherited from store)
fact_id = store.add_fact(
    domain="infrastructure",
    category="hosting",
    item="AWS EC2 Instances",
    details={"count": 50, "region": "us-east-1"},
    status="documented",
    evidence={"exact_quote": "50 EC2 instances...", "page": 5},
    entity="target"
)

# Or provide deal_id per-fact
fact_id = store.add_fact(
    domain="infrastructure",
    category="hosting",
    item="Azure VMs",
    deal_id="deal_xyz789"  # Override store's deal_id
)

# Retrieve facts
facts = store.get_domain_facts("infrastructure")
fact = store.get_fact("F-INFRA-001")
```

### DocumentStore (`stores/document_store.py`)
Document registry with integrity verification.

```python
from stores import DocumentStore

store = DocumentStore.get_instance()

# Add document
doc = store.add_document(
    file_path="/path/to/doc.pdf",
    entity="target",
    authority_level=1,
    uploaded_by="user@example.com"
)

# Duplicate detection
existing = store.get_by_hash(sha256_hash)

# Get documents
docs = store.list_documents(entity="target", status="processed")
```

### SessionStore (`stores/session_store.py`)
Web session management.

```python
from stores import session_store, get_or_create_session_id

# Get/create session
session_id = get_or_create_session_id(flask_session)

# Store analysis session
session_store.set_analysis_session(session_id, analysis_session)

# Retrieve
session = session_store.get_analysis_session(session_id)
```

## Storage Service (Cloud-Ready)

The `web/storage.py` module provides a unified interface for local and S3 storage:

```python
from web.storage import get_storage, StorageService

storage = get_storage()

# Upload document
stored = storage.upload_document(
    file=file_obj,
    deal_id="deal-123",
    entity="target",
    filename="contract.pdf"
)

# Get document
file_obj, metadata = storage.get_document(key)

# List documents
docs = storage.list_deal_documents(deal_id="deal-123")
```

### Storage Backends

**Local Storage** (default):
```
uploads/deals/{deal_id}/documents/{entity}/{filename}
```

**S3 Storage** (production):
```
s3://bucket/deals/{deal_id}/documents/{entity}/{filename}
```

**Multi-Tenant Storage**:
```
s3://bucket/tenants/{tenant_id}/deals/{deal_id}/documents/{entity}/{filename}
```

## Run Management

The `services/run_manager.py` organizes analysis outputs:

```python
from services.run_manager import get_run_manager, create_new_run

# Create new run
run_paths = create_new_run(target_name="Acme Corp", deal_type="acquisition")
# Returns: RunPaths with root, facts, findings, reports, exports, logs paths

# Get current run
manager = get_run_manager()
paths = manager.get_run_paths()  # Latest run
paths = manager.get_run_paths("2026-01-28_143052_acme-corp")  # Specific run

# List runs
runs = manager.list_runs()

# Archive old run
manager.archive_run("2026-01-27_091523_old-deal")
```

## Configuration

Key storage settings in `config_v2.py`:

```python
# Document storage
UPLOADS_DIR = BASE_DIR / "uploads"
DOCUMENTS_DIR = UPLOADS_DIR  # Alias

# Output storage
OUTPUT_DIR = BASE_DIR / "output"

# Entity directories
TARGET_DOCS_DIR = UPLOADS_DIR / "target"
BUYER_DOCS_DIR = UPLOADS_DIR / "buyer"

# Authority levels
AUTHORITY_FOLDERS = {
    1: "data_room",
    2: "correspondence",
    3: "notes"
}
```

## Environment Variables (Production)

```bash
# Storage type
STORAGE_TYPE=s3  # 'local' or 's3'

# S3 configuration
S3_BUCKET=diligence-documents
S3_REGION=us-east-1
S3_ENDPOINT=https://s3.amazonaws.com  # Or R2/MinIO endpoint
S3_ACCESS_KEY=...
S3_SECRET_KEY=...
S3_PUBLIC_URL=https://cdn.example.com  # Optional CDN

# Multi-tenancy
USE_MULTI_TENANCY=true
```

## Data Integrity

### Document Hashing
All documents are SHA-256 hashed on upload:
- Duplicate detection
- Integrity verification
- Audit trail anchoring

### Evidence Chain
Facts maintain evidence chains back to source documents:
```
Finding → Fact → Document (hash-verified)
```

### Atomic Writes
All store operations use atomic writes (write to temp, then rename) to prevent corruption.

---

## Document Processing Utilities (V2.3)

The `tools_v2/` package includes preprocessing utilities for reliable document handling:

### Document Preprocessor
Cleans text before parsing or storage:

```python
from tools_v2 import preprocess_document

# Remove PUA chars, filecite artifacts, normalize whitespace
clean_text = preprocess_document(dirty_text)
```

### Numeric Normalizer
Consistent parsing of numbers, currencies, and null values:

```python
from tools_v2 import normalize_numeric, normalize_cost, is_null_value

normalize_numeric("$1,234.56")  # → 1234.56
normalize_numeric("N/A")        # → None
normalize_numeric("~500")       # → 500
is_null_value("TBD")            # → True
```

### Table-Aware Chunker
Chunks documents while preserving table integrity:

```python
from tools_v2 import chunk_document

chunks = chunk_document(text, max_chunk_size=4000)
# Tables never split mid-row; large tables repeat headers
```

### Table Parser
Deterministic Markdown table parsing:

```python
from tools_v2 import parse_table

table = parse_table(markdown_table)
# Returns ParsedTable with headers, rows (normalized), raw_rows
```

---

See also:
- [Architecture Overview](architecture.md)
- [Data Flow](data-flow.md)
- [API Reference](api.md)
