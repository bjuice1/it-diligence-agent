# Database Schema: IT Due Diligence Platform

## Overview - MVP Focus

Core functionality for persisting deals and analysis. Auth/teams/audit trail deferred.

```
┌─────────────┐
│    Deals    │
└──────┬──────┘
       │
       ├──────────────┬──────────────┬──────────────┐
       │              │              │              │
       ▼              ▼              ▼              ▼
┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐
│ Documents │  │   Facts   │  │   Gaps    │  │ Findings  │
└───────────┘  └───────────┘  └───────────┘  └───────────┘
                                                   │
                                    ┌──────────────┼──────────────┐
                                    │              │              │
                                    ▼              ▼              ▼
                              ┌──────────┐  ┌───────────┐  ┌────────────┐
                              │  Risks   │  │Work Items │  │VDR Requests│
                              └──────────┘  └───────────┘  └────────────┘
```

---

## Tables

### 1. Deals

```sql
CREATE TABLE deals (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Deal Info
    name            VARCHAR(255) NOT NULL,          -- "Great Insurance Acquisition"
    target_name     VARCHAR(255) NOT NULL,          -- "Great Insurance"
    buyer_name      VARCHAR(255),                   -- "Guardian International"
    deal_type       VARCHAR(50) NOT NULL,           -- 'bolt_on', 'carve_out', 'platform'
    industry        VARCHAR(100),                   -- 'insurance', 'healthcare', etc.

    -- Status
    status          VARCHAR(50) DEFAULT 'active',   -- active, in_review, closed, archived
    phase           VARCHAR(50) DEFAULT 'discovery', -- discovery, reasoning, review, complete

    -- Summary Stats (denormalized for fast display)
    fact_count      INTEGER DEFAULT 0,
    gap_count       INTEGER DEFAULT 0,
    risk_count      INTEGER DEFAULT 0,
    work_item_count INTEGER DEFAULT 0,
    total_cost_low  INTEGER DEFAULT 0,
    total_cost_high INTEGER DEFAULT 0,

    -- Metadata
    settings        JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),
    closed_at       TIMESTAMPTZ
);

CREATE INDEX idx_deals_status ON deals(status);
CREATE INDEX idx_deals_created ON deals(created_at DESC);
```

### 2. Documents

```sql
CREATE TABLE documents (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    deal_id         UUID NOT NULL REFERENCES deals(id) ON DELETE CASCADE,

    -- File Info
    filename        VARCHAR(500) NOT NULL,
    file_type       VARCHAR(50),                    -- 'pdf', 'txt', 'md'
    file_size       BIGINT,                         -- bytes
    storage_path    VARCHAR(1000),                  -- file path or S3 path

    -- Classification
    entity          VARCHAR(50) NOT NULL DEFAULT 'target',  -- 'target', 'buyer'
    doc_type        VARCHAR(100),                   -- 'it_profile', 'meeting_notes', etc.

    -- Processing
    status          VARCHAR(50) DEFAULT 'pending',  -- pending, processed, error
    processed_at    TIMESTAMPTZ,
    page_count      INTEGER,

    -- For search (optional - can populate later)
    extracted_text  TEXT,

    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_documents_deal ON documents(deal_id);
CREATE INDEX idx_documents_entity ON documents(deal_id, entity);
```

### 3. Facts

```sql
CREATE TABLE facts (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    deal_id         UUID NOT NULL REFERENCES deals(id) ON DELETE CASCADE,

    -- Identity (matches current FactStore)
    fact_id         VARCHAR(50) NOT NULL,           -- 'F-INFRA-001'
    domain          VARCHAR(50) NOT NULL,           -- 'infrastructure', 'network', etc.
    category        VARCHAR(100) NOT NULL,          -- 'compute', 'hosting', etc.
    entity          VARCHAR(50) DEFAULT 'target',   -- 'target', 'buyer'

    -- Content
    item            VARCHAR(500) NOT NULL,          -- 'VMware Environment'
    details         JSONB DEFAULT '{}',             -- Structured details
    status          VARCHAR(50) DEFAULT 'documented', -- documented, partial

    -- Evidence
    evidence_quote  TEXT,
    evidence_section VARCHAR(255),
    source_document_id UUID REFERENCES documents(id),

    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(deal_id, fact_id)
);

CREATE INDEX idx_facts_deal ON facts(deal_id);
CREATE INDEX idx_facts_domain ON facts(deal_id, domain);
CREATE INDEX idx_facts_entity ON facts(deal_id, entity);
```

### 4. Gaps

```sql
CREATE TABLE gaps (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    deal_id         UUID NOT NULL REFERENCES deals(id) ON DELETE CASCADE,

    -- Identity
    gap_id          VARCHAR(50) NOT NULL,           -- 'G-INFRA-001'
    domain          VARCHAR(50) NOT NULL,
    category        VARCHAR(100) NOT NULL,

    -- Content
    item            VARCHAR(500) NOT NULL,          -- What's missing
    expected_info   TEXT,
    impact          VARCHAR(50) DEFAULT 'medium',   -- critical, high, medium, low

    -- Resolution
    status          VARCHAR(50) DEFAULT 'open',     -- open, resolved, wont_fix
    resolved_by_fact_id VARCHAR(50),

    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(deal_id, gap_id)
);

CREATE INDEX idx_gaps_deal ON gaps(deal_id);
CREATE INDEX idx_gaps_status ON gaps(deal_id, status);
```

### 5. Risks

```sql
CREATE TABLE risks (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    deal_id         UUID NOT NULL REFERENCES deals(id) ON DELETE CASCADE,

    -- Identity
    risk_id         VARCHAR(50) NOT NULL,           -- 'R-INFRA-001'
    domain          VARCHAR(50) NOT NULL,
    category        VARCHAR(100),

    -- Content
    title           VARCHAR(500) NOT NULL,
    description     TEXT NOT NULL,
    severity        VARCHAR(50) NOT NULL,           -- critical, high, medium, low
    mitigation      TEXT,
    reasoning       TEXT,

    -- Flags
    integration_dependent BOOLEAN DEFAULT FALSE,
    confidence      VARCHAR(50) DEFAULT 'medium',

    -- Status (for manual review)
    status          VARCHAR(50) DEFAULT 'identified', -- identified, confirmed, accepted, mitigated

    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(deal_id, risk_id)
);

CREATE INDEX idx_risks_deal ON risks(deal_id);
CREATE INDEX idx_risks_severity ON risks(deal_id, severity);
```

### 6. Work Items

```sql
CREATE TABLE work_items (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    deal_id         UUID NOT NULL REFERENCES deals(id) ON DELETE CASCADE,

    -- Identity
    work_item_id    VARCHAR(50) NOT NULL,           -- 'W-INFRA-001'
    domain          VARCHAR(50) NOT NULL,

    -- Content
    title           VARCHAR(500) NOT NULL,
    description     TEXT NOT NULL,

    -- Classification
    phase           VARCHAR(50) NOT NULL,           -- 'Day_1', 'Day_100', 'Post_100'
    priority        VARCHAR(50) DEFAULT 'medium',
    owner_type      VARCHAR(100),                   -- 'target_it', 'buyer_it', 'shared'

    -- Cost
    cost_estimate   VARCHAR(50),                    -- 'under_25k', '25k_to_100k', etc.
    cost_low        INTEGER,                        -- $ amount
    cost_high       INTEGER,

    -- Status
    status          VARCHAR(50) DEFAULT 'identified',

    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(deal_id, work_item_id)
);

CREATE INDEX idx_work_items_deal ON work_items(deal_id);
CREATE INDEX idx_work_items_phase ON work_items(deal_id, phase);
```

### 7. Strategic Considerations

```sql
CREATE TABLE strategic_considerations (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    deal_id         UUID NOT NULL REFERENCES deals(id) ON DELETE CASCADE,

    consideration_id VARCHAR(50) NOT NULL,
    domain          VARCHAR(50) NOT NULL,

    title           VARCHAR(500) NOT NULL,
    description     TEXT NOT NULL,
    lens            VARCHAR(100),                   -- 'synergy', 'risk', 'value_creation'
    implication     TEXT,
    confidence      VARCHAR(50) DEFAULT 'medium',

    created_at      TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(deal_id, consideration_id)
);

CREATE INDEX idx_strategic_deal ON strategic_considerations(deal_id);
```

### 8. Recommendations

```sql
CREATE TABLE recommendations (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    deal_id         UUID NOT NULL REFERENCES deals(id) ON DELETE CASCADE,

    recommendation_id VARCHAR(50) NOT NULL,
    domain          VARCHAR(50) NOT NULL,

    title           VARCHAR(500) NOT NULL,
    description     TEXT NOT NULL,
    action_type     VARCHAR(100),
    urgency         VARCHAR(50) DEFAULT 'medium',
    rationale       TEXT,

    created_at      TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(deal_id, recommendation_id)
);

CREATE INDEX idx_recommendations_deal ON recommendations(deal_id);
```

### 9. VDR Requests

```sql
CREATE TABLE vdr_requests (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    deal_id         UUID NOT NULL REFERENCES deals(id) ON DELETE CASCADE,

    request_id      VARCHAR(50) NOT NULL,           -- 'VDR-001'

    title           VARCHAR(500) NOT NULL,
    description     TEXT,
    priority        VARCHAR(50) NOT NULL,
    category        VARCHAR(100),                   -- domain

    -- Source
    triggered_by_gap_id VARCHAR(50),
    triggered_by_risk_id VARCHAR(50),

    -- Status
    status          VARCHAR(50) DEFAULT 'pending',  -- pending, sent, received
    received_document_id UUID REFERENCES documents(id),

    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(deal_id, request_id)
);

CREATE INDEX idx_vdr_deal ON vdr_requests(deal_id);
CREATE INDEX idx_vdr_status ON vdr_requests(deal_id, status);
```

### 10. Fact Citations (Junction Table)

```sql
-- Links findings to the facts they're based on
CREATE TABLE fact_citations (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    deal_id         UUID NOT NULL REFERENCES deals(id) ON DELETE CASCADE,

    -- The finding citing the fact
    citing_type     VARCHAR(50) NOT NULL,           -- 'risk', 'work_item', 'recommendation', etc.
    citing_id       VARCHAR(50) NOT NULL,           -- 'R-INFRA-001', 'W-NET-002', etc.

    -- The fact being cited
    fact_id         VARCHAR(50) NOT NULL,           -- 'F-INFRA-001'

    UNIQUE(deal_id, citing_type, citing_id, fact_id)
);

CREATE INDEX idx_citations_fact ON fact_citations(deal_id, fact_id);
CREATE INDEX idx_citations_citing ON fact_citations(deal_id, citing_type, citing_id);
```

### 11. Analysis Runs

```sql
CREATE TABLE analysis_runs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    deal_id         UUID NOT NULL REFERENCES deals(id) ON DELETE CASCADE,

    run_type        VARCHAR(50) NOT NULL,           -- 'full', 'discovery', 'reasoning'
    domains         VARCHAR(50)[] NOT NULL,

    status          VARCHAR(50) DEFAULT 'running',  -- running, completed, failed
    started_at      TIMESTAMPTZ DEFAULT NOW(),
    completed_at    TIMESTAMPTZ,

    -- Results
    facts_extracted INTEGER DEFAULT 0,
    gaps_identified INTEGER DEFAULT 0,
    risks_found     INTEGER DEFAULT 0,
    work_items_found INTEGER DEFAULT 0,

    -- Cost
    tokens_used     INTEGER DEFAULT 0,
    estimated_cost  DECIMAL(10,4) DEFAULT 0,

    error_message   TEXT
);

CREATE INDEX idx_runs_deal ON analysis_runs(deal_id, started_at DESC);
```

---

## Helper: Update Timestamp Trigger

```sql
-- Auto-update updated_at on any table
CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply to tables with updated_at
CREATE TRIGGER update_deals_timestamp BEFORE UPDATE ON deals
    FOR EACH ROW EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER update_facts_timestamp BEFORE UPDATE ON facts
    FOR EACH ROW EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER update_gaps_timestamp BEFORE UPDATE ON gaps
    FOR EACH ROW EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER update_risks_timestamp BEFORE UPDATE ON risks
    FOR EACH ROW EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER update_work_items_timestamp BEFORE UPDATE ON work_items
    FOR EACH ROW EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER update_vdr_timestamp BEFORE UPDATE ON vdr_requests
    FOR EACH ROW EXECUTE FUNCTION update_timestamp();
```

---

## Deal Summary View

```sql
CREATE VIEW deal_summary AS
SELECT
    d.id,
    d.name,
    d.target_name,
    d.buyer_name,
    d.deal_type,
    d.status,
    d.phase,
    d.created_at,
    COUNT(DISTINCT doc.id) as document_count,
    COUNT(DISTINCT f.id) as fact_count,
    COUNT(DISTINCT g.id) FILTER (WHERE g.status = 'open') as open_gap_count,
    COUNT(DISTINCT r.id) as risk_count,
    COUNT(DISTINCT r.id) FILTER (WHERE r.severity IN ('critical', 'high')) as high_risk_count,
    COUNT(DISTINCT w.id) as work_item_count,
    COALESCE(SUM(w.cost_low), 0) as total_cost_low,
    COALESCE(SUM(w.cost_high), 0) as total_cost_high
FROM deals d
LEFT JOIN documents doc ON doc.deal_id = d.id
LEFT JOIN facts f ON f.deal_id = d.id AND f.entity = 'target'
LEFT JOIN gaps g ON g.deal_id = d.id
LEFT JOIN risks r ON r.deal_id = d.id
LEFT JOIN work_items w ON w.deal_id = d.id
GROUP BY d.id;
```

---

## Quick Reference: Table Count

| Table | Purpose | Rows per Deal (typical) |
|-------|---------|-------------------------|
| deals | 1 per transaction | 1 |
| documents | Uploaded files | 5-20 |
| facts | Extracted facts | 50-200 |
| gaps | Missing info | 10-50 |
| risks | Identified risks | 10-30 |
| work_items | Tasks/costs | 20-50 |
| strategic_considerations | Strategic insights | 5-15 |
| recommendations | Action items | 5-20 |
| vdr_requests | Follow-up requests | 10-40 |
| fact_citations | Fact → Finding links | 100-500 |
| analysis_runs | Run history | 1-10 |

---

## Migration from JSON Files

```python
def migrate_to_db(deal_name: str, fact_store: FactStore, reasoning_store: ReasoningStore, db):
    """Migrate existing JSON outputs to database."""

    # 1. Create deal
    deal = db.deals.insert({
        'name': deal_name,
        'target_name': deal_name,
        'status': 'active',
        'phase': 'complete'
    })
    deal_id = deal.id

    # 2. Migrate facts
    for fact in fact_store.facts:
        db.facts.insert({
            'deal_id': deal_id,
            'fact_id': fact.fact_id,
            'domain': fact.domain,
            'category': fact.category,
            'entity': getattr(fact, 'entity', 'target'),
            'item': fact.item,
            'details': fact.details,
            'status': fact.status,
            'evidence_quote': fact.evidence.get('exact_quote'),
            'evidence_section': fact.evidence.get('source_section')
        })

    # 3. Migrate gaps
    for gap in fact_store.gaps:
        db.gaps.insert({
            'deal_id': deal_id,
            'gap_id': gap.gap_id,
            'domain': gap.domain,
            'category': gap.category,
            'item': gap.item,
            'expected_info': gap.expected_info,
            'impact': gap.impact
        })

    # 4. Migrate risks
    for risk in reasoning_store.risks:
        db.risks.insert({
            'deal_id': deal_id,
            'risk_id': risk.risk_id,
            'domain': risk.domain,
            'category': risk.category,
            'title': risk.title,
            'description': risk.description,
            'severity': risk.severity,
            'mitigation': risk.mitigation,
            'reasoning': getattr(risk, 'reasoning', ''),
            'integration_dependent': risk.integration_dependent
        })

        # Add citations
        for fact_id in risk.based_on_facts:
            db.fact_citations.insert({
                'deal_id': deal_id,
                'citing_type': 'risk',
                'citing_id': risk.risk_id,
                'fact_id': fact_id
            })

    # 5. Migrate work items (similar pattern)
    # 6. Update deal summary stats

    return deal_id
```

---

## Next Steps

1. **SQLite first** - Works for single-user local, easy to start
2. **Add to Streamlit** - Save/load deals from DB instead of JSON
3. **Deal list page** - Show all deals with summary stats
4. **Later: Postgres** - When ready for web deployment
