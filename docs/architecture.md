# IT Due Diligence Agent - Architecture Overview

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Web Interface                                │
│                    (Flask + Templates)                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │   Upload &   │  │   Analysis   │  │   Export &   │              │
│  │   Documents  │  │   Dashboard  │  │   Reports    │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
│                                                                      │
├─────────────────────────────────────────────────────────────────────┤
│                         API Layer                                    │
│                    (85+ REST Endpoints)                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                    Analysis Engine                            │  │
│  │  ┌────────────┐    ┌────────────┐    ┌────────────┐         │  │
│  │  │ Discovery  │───▶│  Reasoning │───▶│  Synthesis │         │  │
│  │  │  (Haiku)   │    │  (Sonnet)  │    │  (Sonnet)  │         │  │
│  │  └────────────┘    └────────────┘    └────────────┘         │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                      │
├─────────────────────────────────────────────────────────────────────┤
│                         Stores Layer                                 │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐   │
│  │ FactStore  │  │ DocStore   │  │ Session    │  │ Validation │   │
│  │            │  │            │  │ Store      │  │ Store      │   │
│  └────────────┘  └────────────┘  └────────────┘  └────────────┘   │
├─────────────────────────────────────────────────────────────────────┤
│                      Storage Layer                                   │
│  ┌────────────────────┐  ┌────────────────────┐                    │
│  │  uploads/          │  │  output/           │                    │
│  │  (documents)       │  │  (runs, exports)   │                    │
│  └────────────────────┘  └────────────────────┘                    │
└─────────────────────────────────────────────────────────────────────┘
```

## Key Components

### 1. Web Interface (`web/`)
- **app.py**: Flask application with 85+ API endpoints
- **templates/**: 19 Jinja2 templates with design tokens
- **session_store.py**: Thread-safe session management (redirect to stores/)
- **storage.py**: Unified local/S3 storage interface

### 2. Analysis Engine
- **Discovery Phase**: Uses Claude Haiku for fast, parallel fact extraction
- **Reasoning Phase**: Uses Claude Sonnet for risk analysis and synthesis
- **Two-Phase Analysis**: Separates Target and Buyer document processing

### 3. Stores Package (`stores/`)
- **FactStore**: Central repository for extracted facts with evidence chains
- **DocumentStore**: Document registry with SHA-256 hash verification
- **SessionStore**: Web session management with TTL
- **ValidationStore**: Fact validation state tracking
- **CorrectionStore**: Human correction audit trail
- **AuditStore**: Complete audit trail for all actions

### 4. Agents (`agents_v2/`)
- **Discovery Agents**: One per domain (infrastructure, network, security, etc.)
- **Reasoning Agents**: Analyze facts to identify risks and work items
- **Narrative Agent**: Generates executive summaries

### 5. Services (`services/`)
- **RunManager**: Organizes analysis outputs by timestamped runs
- **ExportService**: Excel, Markdown, CSV, HTML exports
- **InventoryDossier**: Per-item evidence dossiers

## Directory Structure

```
it-diligence-agent/
├── web/                 # Flask web application
├── agents_v2/           # Discovery and reasoning agents
├── stores/              # Data persistence layer
├── services/            # Business logic services
├── tools_v2/            # Agent tools and utilities
├── uploads/             # User document uploads
├── output/              # Analysis outputs
│   └── runs/            # Timestamped run directories
├── docs/                # Documentation
├── tests/               # Test suite
└── docker/              # Docker configuration
```

## Technology Stack

| Component | Technology |
|-----------|------------|
| Backend | Python 3.11, Flask |
| AI Models | Claude Haiku (discovery), Claude Sonnet (reasoning) |
| Database | JSON files (local), PostgreSQL (production) |
| Sessions | In-memory (local), Redis (production) |
| Tasks | Threading (local), Celery (production) |
| Storage | Local filesystem, S3-compatible (production) |

## Configuration

Key configuration in `config_v2.py`:
- `DISCOVERY_MODEL`: Model for fact extraction
- `REASONING_MODEL`: Model for analysis
- `UPLOADS_DIR`: Document storage location
- `OUTPUT_DIR`: Analysis output location
- `MAX_PARALLEL_AGENTS`: Concurrency limit

See also:
- [Data Flow](data-flow.md)
- [Storage Architecture](storage.md)
- [API Reference](api.md)
- [Deployment Guide](deployment.md)
