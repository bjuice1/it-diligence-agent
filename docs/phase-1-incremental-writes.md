# Phase 1: Incremental Database Writes

**Status:** IMPLEMENTED

## Prerequisites

```bash
# Required environment variable
export USE_DATABASE=true
```

Without this, the database is not initialized and incremental writes fall back to batch mode.

## Goal

Write facts, gaps, and findings to the database **immediately after extraction**, providing crash durability. If the process dies, data up to the last commit is preserved.

---

## What Was Built

### 1. `stores/db_writer.py` - Incremental Write Service

Core class: `IncrementalDBWriter`

**Key methods:**
```python
# Create analysis run at START
run_id = writer.create_analysis_run(session, deal_id, task_id)

# Write data immediately (each commits by default)
writer.write_fact(session, fact_data, deal_id, run_id)
writer.write_gap(session, gap_data, deal_id, run_id)
writer.write_finding(session, finding_data, deal_id, run_id)

# Throttled progress updates (max 1 per 2 seconds)
writer.update_analysis_progress(session, run_id, progress=50.0)

# Mark complete with final counts
writer.complete_analysis_run(session, run_id, status='completed')
```

**Design decisions:**
- Per-write commits for crash durability (optional batching via `commit=False`)
- UPSERT semantics for idempotent retries
- Session scope handles Flask request context and background threads
- Throttled progress updates to avoid DB spam

### 2. `web/analysis_runner.py` - Integration

Added `IncrementalPersistence` helper class that:
- Tracks which facts/gaps/findings have already been written
- Persists only NEW items after each domain discovery/reasoning
- Batches writes within a domain for efficiency

**Integration points:**
```
run_analysis()
  ├── Create AnalysisRun record (START)
  ├── For each TARGET domain:
  │     ├── run_discovery_for_domain()
  │     └── incremental.persist_new_facts()  ← WRITE
  │     └── incremental.persist_new_gaps()   ← WRITE
  ├── For each BUYER domain:
  │     ├── run_discovery_for_domain()
  │     └── incremental.persist_new_facts()  ← WRITE
  ├── For each reasoning domain:
  │     ├── run_reasoning_for_domain()
  │     └── incremental.persist_new_findings() ← WRITE
  └── incremental.complete()  ← MARK DONE
```

---

## Crash Guarantee

> All committed writes are durable. If the process crashes, data is preserved up to and including the last successful commit.

---

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `PROGRESS_THROTTLE_SECONDS` | 2.0 | Min seconds between progress DB updates |
| `commit` parameter | `True` | Set to `False` to batch writes manually |

---

## Testing

To verify incremental writes:

1. Start analysis on a deal
2. Kill the process mid-analysis (Ctrl+C)
3. Check database - facts written before crash should be present
4. Restart analysis - UPSERT ensures no duplicates

---

## Limitations

- Requires Flask `app` instance passed to `run_analysis()`
- Falls back to batch persistence if incremental setup fails
- Does not yet handle document writes (documents uploaded separately)

---

## Next Steps

Phase 2: Make all UI routes read from database consistently.
