# Validation System Architecture

## Overview

The IT Due Diligence Validation System provides a comprehensive three-layer architecture for validating extracted facts, ensuring data quality, and maintaining audit trails.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          VALIDATION SYSTEM                                   │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
        ┌───────────────────────────┼───────────────────────────┐
        ▼                           ▼                           ▼
┌───────────────┐         ┌───────────────┐         ┌───────────────┐
│   LAYER 1     │         │   LAYER 2     │         │   LAYER 3     │
│   Category    │    →    │    Domain     │    →    │ Cross-Domain  │
│  Validators   │         │  Validators   │         │  Consistency  │
└───────────────┘         └───────────────┘         └───────────────┘
        │                         │                         │
        ▼                         ▼                         ▼
┌───────────────┐         ┌───────────────┐         ┌───────────────┐
│  Checkpoints  │         │  Completeness │         │  Headcount vs │
│  Required     │         │  Scoring      │         │  Endpoints    │
│  Fields       │         │  Consistency  │         │  Cost Ratios  │
│  Min/Max      │         │  Checks       │         │  Vendor Match │
└───────────────┘         └───────────────┘         └───────────────┘
```

## Components

### 1. Evidence Verifier (`tools_v2/evidence_verifier.py`)

Verifies that extracted quotes actually exist in source documents.

**Key Features:**
- Fuzzy string matching with configurable thresholds
- Whitespace and case normalization
- Batch verification support

**Thresholds:**
- `>= 0.85`: Verified
- `0.50 - 0.85`: Partial match
- `< 0.50`: Not found

### 2. Category Validator (`tools_v2/category_validator.py`)

Layer 1 validation checking category-level completeness.

**Checkpoints:**
- Minimum/maximum expected items per category
- Required fields validation
- LLM-based completeness check

**Example Checkpoint:**
```python
CategoryCheckpoint(
    category="central_it",
    min_expected_items=5,
    max_expected_items=10,
    required_fields=["headcount", "item"],
    importance="high"
)
```

### 3. Domain Validator (`tools_v2/domain_validator.py`)

Layer 2 validation checking domain-level consistency.

**Checks:**
- Required categories present
- Headcount consistency
- Team extraction completeness
- LLM deep validation

### 4. Cross-Domain Validator (`tools_v2/cross_domain_validator.py`)

Layer 3 validation checking consistency across all domains.

**Consistency Checks:**
| Check | Expected Range |
|-------|----------------|
| Endpoints per IT person | 20-200 |
| Applications per IT person | 0.5-30 |
| Cost per head | $50K-$300K |

### 5. Adversarial Reviewer (`tools_v2/adversarial_reviewer.py`)

Red-team review that actively seeks problems.

**Focus Areas:**
- Missing information
- Numbers that don't make sense
- Suspicious patterns
- Coverage gaps
- Evidence quality

## Data Flow

```
Document → Extract → Validate → Review → Confirm/Correct
                         │
                         ▼
              ┌──────────────────┐
              │  Need Rerun?     │──Yes──→ Re-extract (max 3x)
              └──────────────────┘                │
                         │                        ▼
                        No              ┌──────────────────┐
                         │              │  Still failing?  │──Yes──→ Escalate
                         ▼              └──────────────────┘
              ┌──────────────────┐
              │  Human Review    │
              │  Queue           │
              └──────────────────┘
                         │
            ┌────────────┼────────────┐
            ▼            ▼            ▼
         Confirm      Correct      Reject
            │            │            │
            └────────────┼────────────┘
                         ▼
              ┌──────────────────┐
              │  Update Store    │
              │  Log Audit       │
              └──────────────────┘
```

## Storage Layer

### ValidationStore (`stores/validation_store.py`)

Stores validation state for each fact:
- Status (extracted → validated → reviewed)
- Confidence scores
- Flags
- Human review history

### CorrectionStore (`stores/correction_store.py`)

Records all corrections:
- Original and corrected values
- Who made the correction
- Reason for correction

### AuditStore (`stores/audit_store.py`)

Complete audit trail:
- All extraction events
- Validation events
- Human review events
- System events (re-extraction, escalation)

## Validation States

```
EXTRACTED
    │
    ▼
AI_VALIDATED ───────────────────┐
    │                           │
    ▼                           ▼
HUMAN_PENDING             (passes)
    │
    ├──────┬──────┬──────┐
    ▼      ▼      ▼      ▼
CONFIRMED CORRECTED REJECTED (skip)
```

## Flag Severities

| Severity | Impact | Example |
|----------|--------|---------|
| CRITICAL | Likely wrong | Evidence not found |
| ERROR | Probably wrong | Major inconsistency |
| WARNING | Might be wrong | Unusual value |
| INFO | FYI | Note for reviewer |

## Configuration

Key settings in `config_v2.py`:

```python
# Master switch
VALIDATION_ENABLED = True

# Thresholds
EVIDENCE_MATCH_THRESHOLD = 0.85
CONFIDENCE_THRESHOLD_FOR_REVIEW = 0.70

# Re-extraction
MAX_REEXTRACTION_ATTEMPTS = 3

# Model selection
VALIDATION_MODEL = "claude-sonnet-4-20250514"
CATEGORY_VALIDATION_MODEL = "claude-3-5-haiku-20241022"
```

## Performance Optimization

### Parallel Execution
- Evidence verification runs in parallel
- Category validators run in parallel per domain
- Domain validation after categories complete
- Cross-domain after all domains complete

### Caching
- Document text parsing cached
- LLM responses cached for identical prompts
- Validation results cached with TTL

### Cost Optimization
- Haiku for category checkpoints (cheaper)
- Sonnet for domain/adversarial (more thorough)
- Skip adversarial if major issues found

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/review/queue` | GET | Get review queue |
| `/api/review/{fact_id}` | GET | Get review item |
| `/api/review/{fact_id}/confirm` | POST | Confirm fact |
| `/api/review/{fact_id}/correct` | POST | Correct fact |
| `/api/review/{fact_id}/reject` | POST | Reject fact |
| `/api/validation/status` | GET | Get validation status |

## Metrics

Tracked metrics:
- `validation_runs_total`
- `reextraction_triggers_total`
- `human_reviews_total`
- `corrections_total`
- `flags_generated_total`

## Best Practices

1. **Bias Toward Flagging**: When in doubt, flag it. Missing something is worse than a false positive.

2. **Latency Acceptable**: 10 extra minutes of validation is worth it for accuracy.

3. **Validation is Visible**: Show users what validation found. Transparency builds trust.

4. **No Hard Blocks**: Don't prevent data from flowing. Flag issues, don't reject entries.

5. **Evidence-Based**: Every finding should cite specific facts. No unsupported claims.
