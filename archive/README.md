# Archive Directory

This directory contains archived code, data, and outputs that are no longer needed for active development but are preserved for reference.

## Directory Structure

```
archive/
├── old_runs/           # Historical analysis outputs by date
│   ├── 2026-01-18/    # Facts, findings, reports from this date
│   ├── 2026-01-19/
│   └── ...
│
├── legacy_code/        # Old implementations and database backups
│   ├── *.backup       # Database backups
│   └── *.old_schema_* # Old database schemas
│
├── test_outputs/       # Test data and fixtures
│   ├── input_test/    # Test input documents
│   ├── data_output/   # Test output data
│   └── test/          # Other test files
│
├── old_outputs/        # Legacy output files
│
├── old_ui/            # Previous UI implementations
│
└── unused_prompts/    # Prompt templates no longer in use
```

## What's Archived

### old_runs/
Each dated folder contains:
- `facts_*.json` - Extracted facts from that analysis run
- `findings_*.json` - Generated findings (risks, work items)
- `deal_context_*.json` - Deal metadata
- `open_questions_*.json` - VDR gaps identified
- `vdr_requests_*.json` - VDR document requests
- `it_dd_report_*.html` - Generated HTML reports
- `investment_thesis_*.html` - Executive summaries

### legacy_code/
- Database backup files
- Old schema migrations
- Deprecated code modules

### test_outputs/
- Test fixtures and sample data
- Integration test outputs
- Not needed for production

## Retention Policy

- **old_runs/**: Keep for 90 days, then delete
- **legacy_code/**: Keep indefinitely for reference
- **test_outputs/**: Can be deleted anytime

## Note

This directory is gitignored (old_runs/ and test_outputs/). Only the README and directory structure are committed.
