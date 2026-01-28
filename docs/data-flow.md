# IT Due Diligence Agent - Data Flow

## Analysis Pipeline

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Document   │────▶│  Discovery  │────▶│  Reasoning  │────▶│   Export    │
│   Upload    │     │   Phase     │     │   Phase     │     │   Phase     │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
      │                   │                   │                   │
      ▼                   ▼                   ▼                   ▼
  DocumentStore       FactStore          Findings            Reports
```

## Phase 1: Document Upload

```
User Upload ──▶ DocumentStore.add_document()
                      │
                      ├── Compute SHA-256 hash
                      ├── Check for duplicates
                      ├── Copy to uploads/{entity}/{authority}/
                      ├── Create manifest entry
                      └── Extract text (PDF, DOCX, XLSX)
```

**Entity Separation:**
- `uploads/target/` - Target company documents
- `uploads/buyer/` - Buyer company documents

**Authority Levels:**
1. `data_room/` - Official documents (highest weight)
2. `correspondence/` - Formal correspondence
3. `notes/` - Discussion notes (lowest weight)

## Phase 2: Discovery (Fact Extraction)

```
For each domain (infrastructure, network, security, apps, identity, org):
    │
    ├── Load domain-specific prompt
    ├── Send documents to Claude Haiku
    ├── Extract structured facts
    │       │
    │       ├── fact_id: F-INFRA-001
    │       ├── domain: infrastructure
    │       ├── category: hosting
    │       ├── item: "AWS EC2 instances"
    │       ├── details: {count: 50, region: "us-east-1"}
    │       ├── evidence: {exact_quote: "...", page: 5}
    │       └── confidence_score: 0.85
    │
    └── Store in FactStore
```

**Parallel Execution:**
- Up to 3 domains processed simultaneously
- Rate limiting: 40 requests/minute to Anthropic API
- Circuit breaker for fault tolerance

## Phase 3: Reasoning (Analysis)

```
FactStore facts ──▶ Reasoning Agents ──▶ Findings
                          │
                          ├── Identify risks (R-xxxx)
                          ├── Generate work items (WI-xxxx)
                          ├── Create recommendations
                          └── Score severity (critical/high/medium/low)
```

**Finding Types:**
- **Risks**: Technology debt, security gaps, compliance issues
- **Work Items**: Integration tasks, migration activities
- **Recommendations**: Improvement suggestions

**Evidence Chain:**
```
Finding.based_on_facts ──▶ [F-INFRA-001, F-NET-003]
                                  │
                                  ▼
                          Fact.evidence.exact_quote
                                  │
                                  ▼
                          Document (SHA-256 verified)
```

## Phase 4: Export & Reporting

```
FactStore + Findings ──▶ ExportService
                              │
                              ├── Excel: applications.xlsx, infrastructure.xlsx
                              ├── Markdown: executive_summary.md
                              ├── HTML: it_dd_report.html
                              ├── JSON: facts.json, findings.json
                              └── Dossiers: per-item evidence files
```

## Run Organization

Each analysis creates a timestamped run directory:

```
output/runs/
└── 2026-01-28_143052_target-name/
    ├── metadata.json      # Run metadata
    ├── facts/
    │   └── facts.json     # All extracted facts
    ├── findings/
    │   └── findings.json  # Risks, work items
    ├── reports/
    │   ├── it_dd_report.html
    │   └── executive_summary.md
    ├── exports/
    │   ├── applications.xlsx
    │   └── dossiers/
    └── logs/
        └── analysis.log
```

## Data Models

### Fact
```python
@dataclass
class Fact:
    fact_id: str           # F-DOMAIN-NNN
    domain: str            # infrastructure, network, etc.
    category: str          # hosting, compute, etc.
    item: str              # What this fact describes
    status: str            # documented, partial, gap
    details: Dict          # Structured attributes
    evidence: Dict         # exact_quote, source_document, page
    confidence_score: float
    entity: str            # target or buyer
```

### Finding
```python
@dataclass
class Finding:
    finding_id: str        # R-xxxx or WI-xxxx
    finding_type: str      # risk, work_item, recommendation
    domain: str
    title: str
    description: str
    severity: str          # critical, high, medium, low
    based_on_facts: List[str]  # Evidence chain
```

### Document
```python
@dataclass
class Document:
    doc_id: str            # UUID
    filename: str
    hash_sha256: str       # Integrity verification
    entity: str            # target or buyer
    authority_level: int   # 1=high, 3=low
    status: str            # pending, processed, error
```

## Session Management

```
Web Request ──▶ get_or_create_session_id()
                      │
                      ▼
              SessionStore._sessions[session_id]
                      │
                      ├── analysis_session: Session object
                      ├── analysis_task_id: Background task
                      └── last_accessed: TTL tracking
```

Sessions expire after 24 hours of inactivity.

See also:
- [Architecture Overview](architecture.md)
- [Storage Architecture](storage.md)
- [API Reference](api.md)
