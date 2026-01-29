# Database Entity Relationship Diagram

## Overview

The IT Diligence Agent uses PostgreSQL for persistent data storage. The schema supports multi-tenancy, soft deletes, and full audit trails.

## Entity Relationship Diagram (Mermaid)

```mermaid
erDiagram
    TENANTS ||--o{ USERS : has
    TENANTS ||--o{ DEALS : has
    USERS ||--o{ DEALS : owns
    USERS ||--o{ NOTIFICATIONS : receives

    DEALS ||--o{ DOCUMENTS : contains
    DEALS ||--o{ FACTS : has
    DEALS ||--o{ FINDINGS : has
    DEALS ||--o{ ANALYSIS_RUNS : tracks
    DEALS ||--o{ PENDING_CHANGES : queues
    DEALS ||--o{ DEAL_SNAPSHOTS : archives

    FACTS ||--o{ FACT_FINDING_LINKS : links_to
    FINDINGS ||--o{ FACT_FINDING_LINKS : links_from

    DOCUMENTS ||--o{ FACTS : sources

    TENANTS {
        uuid id PK
        string name
        string slug UK
        string plan
        jsonb settings
        timestamp created_at
        timestamp updated_at
    }

    USERS {
        uuid id PK
        uuid tenant_id FK
        string email UK
        string password_hash
        string name
        text[] roles
        boolean active
        timestamp created_at
        timestamp updated_at
        timestamp last_login_at
    }

    DEALS {
        uuid id PK
        uuid tenant_id FK
        uuid owner_id FK
        string name
        string target_name
        string buyer_name
        string deal_type
        string industry
        string status
        boolean target_locked
        boolean buyer_locked
        jsonb context
        jsonb settings
        timestamp created_at
        timestamp updated_at
        timestamp deleted_at
    }

    DOCUMENTS {
        uuid id PK
        uuid deal_id FK
        string filename
        string file_hash
        string entity
        integer authority_level
        string storage_path
        integer version
        uuid previous_version_id FK
        string content_checksum
        text extracted_text
        string status
        timestamp uploaded_at
        timestamp deleted_at
    }

    FACTS {
        string id PK
        uuid deal_id FK
        string domain
        string category
        string entity
        string item
        string status
        jsonb details
        jsonb evidence
        string source_document
        uuid source_document_id FK
        float confidence_score
        boolean verified
        string verification_status
        text source_quote
        int[] source_page_numbers
        string content_checksum
        uuid previous_version_id FK
        timestamp created_at
        timestamp updated_at
        timestamp deleted_at
    }

    FINDINGS {
        string id PK
        uuid deal_id FK
        string finding_type
        string domain
        string title
        text description
        string severity
        string phase
        integer cost_estimate_low
        integer cost_estimate_high
        string currency
        text[] based_on_facts
        jsonb extra_data
        timestamp created_at
        timestamp updated_at
        timestamp deleted_at
    }

    FACT_FINDING_LINKS {
        string fact_id PK,FK
        string finding_id PK,FK
        string link_type
        timestamp created_at
    }

    ANALYSIS_RUNS {
        uuid id PK
        uuid deal_id FK
        string run_type
        string status
        text[] domains_analyzed
        integer facts_count
        integer findings_count
        float duration_seconds
        jsonb metadata
        jsonb errors
        timestamp started_at
        timestamp completed_at
    }

    PENDING_CHANGES {
        uuid id PK
        uuid deal_id FK
        string change_type
        string entity_type
        string entity_id
        jsonb old_value
        jsonb new_value
        string confidence_tier
        string status
        string reviewed_by
        timestamp created_at
        timestamp reviewed_at
    }

    DEAL_SNAPSHOTS {
        uuid id PK
        uuid deal_id FK
        jsonb snapshot_data
        string trigger_type
        uuid analysis_run_id FK
        timestamp created_at
    }

    NOTIFICATIONS {
        uuid id PK
        uuid user_id FK
        uuid deal_id FK
        string notification_type
        text message
        jsonb data
        boolean read
        timestamp created_at
    }
```

## Table Summary

| Table | Description | Key Relationships |
|-------|-------------|-------------------|
| `tenants` | Organizations/customers | Parent of users and deals |
| `users` | System users | Belongs to tenant, owns deals |
| `deals` | Due diligence deals | Central entity, owns all analysis data |
| `documents` | Uploaded documents | Belongs to deal, sources facts |
| `facts` | Extracted facts | Belongs to deal, linked to findings |
| `findings` | Risks, work items, recommendations | Belongs to deal, linked to facts |
| `fact_finding_links` | Many-to-many junction | Links facts to findings |
| `analysis_runs` | Analysis execution records | Tracks deal analysis history |
| `pending_changes` | Merge queue for changes | Queues incremental updates |
| `deal_snapshots` | Point-in-time snapshots | Archives deal state |
| `notifications` | User notifications | User alerts and updates |

## Key Design Decisions

### 1. Soft Deletes
All core entities use soft deletes (`deleted_at` timestamp) to preserve data integrity and enable recovery.

### 2. Audit Columns
`created_by` and `updated_by` columns track who made changes.

### 3. Version Tracking
Documents and facts have `previous_version_id` for change history.

### 4. JSONB for Flexible Data
`details`, `evidence`, `metadata`, and `settings` use JSONB for schema flexibility.

### 5. Full-Text Search
Facts table has a GIN index on `item` and `source_quote` for efficient search.

### 6. Normalized Fact-Finding Links
Junction table allows many-to-many relationships with link type metadata.

## Indexes

```sql
-- Full-text search on facts
CREATE INDEX idx_facts_fulltext ON facts USING gin(
    to_tsvector('english', item || ' ' || COALESCE(source_quote, ''))
);

-- Common query patterns
CREATE INDEX idx_facts_deal_domain ON facts(deal_id, domain);
CREATE INDEX idx_findings_deal_type ON findings(deal_id, finding_type);
CREATE INDEX idx_documents_deal_hash ON documents(deal_id, file_hash);
CREATE INDEX idx_pending_changes_status ON pending_changes(deal_id, status);
```

## Data Flow

```
1. User creates Deal
   └── Deal assigned to Tenant and User

2. Documents uploaded to Deal
   └── Stored with hash for deduplication
   └── Version tracked if replaced

3. Analysis run executed
   └── AnalysisRun record created
   └── Facts extracted from documents
   └── Findings generated from facts
   └── FactFindingLinks created

4. Incremental updates
   └── PendingChanges queued
   └── Human review and approval
   └── Facts/Findings updated

5. Snapshot created
   └── DealSnapshot preserves state
   └── Can restore or compare
```
