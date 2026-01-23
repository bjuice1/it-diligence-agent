# IT Due Diligence Agent - Handoff Document

## Project Overview
AI-powered IT Due Diligence tool for M&A technology assessments. Analyzes VDR documents to extract facts, identify risks, generate work items, and provide organization/staffing analysis.

## Current State

### Working Features
- **Welcome Page** (`/`) - Landing page with hero, feature cards, stats
- **Upload Page** (`/upload`) - Drag-drop file upload with domain selection and deal context
- **Dashboard** (`/dashboard`) - Main analysis results view
- **Risks** (`/risks`) - Risk listing and detail views
- **Work Items** (`/work-items`) - Work item listing by phase (Day 1, Day 100, Post 100)
- **Facts** (`/facts`) - Extracted facts listing
- **Gaps** (`/gaps`) - Information gaps listing
- **Organization Module** (`/organization`) - Staffing tree, benchmark comparison, MSP analysis, shared services

### Known Issues

#### 1. Processing Page Shows Blank - FIXED
**Status:** Fixed in Phase 1

**Solution Implemented:**
- Created `AnalysisTaskManager` for background task execution
- `/analysis/status` now returns real progress from task manager
- Processing page polls and displays actual progress
- Proper redirect only when analysis completes or fails

#### 2. Analysis Pipeline Not Connected - FIXED
**Status:** Fixed in Phase 1

**Solution Implemented:**
- Created `analysis_runner.py` that calls discovery and reasoning agents
- `process_upload()` now creates a task and starts background analysis
- Results are saved and loaded into session when complete

#### 3. Remaining Issues
- Agent imports may fail if prompts or dependencies are missing (falls back to simple runner)
- Organization module still uses demo data (connect to main pipeline in Phase 4)
- No WebSocket for live updates (polling every 2 seconds works but not ideal)

## Key Files

### Web Application
- `web/app.py` - Flask routes and session management
- `web/templates/base.html` - Base template with navigation
- `web/templates/welcome.html` - Landing page (standalone)
- `web/templates/upload.html` - Document upload form
- `web/templates/processing.html` - Loading animation page (standalone, needs fix)
- `web/templates/dashboard.html` - Main dashboard
- `web/templates/organization/` - Organization module templates

### Models
- `models/organization_models.py` - StaffMember, MSPRelationship, SharedServiceDependency, etc.
- `models/organization_stores.py` - OrganizationDataStore, StaffingComparisonResult, etc.
- `models/facts.py` - Fact, Gap models
- `models/reasoning.py` - Risk, WorkItem models

### Services
- `services/organization_pipeline.py` - Organization analysis pipeline
- `interactive/session.py` - Session class for managing analysis state

### Configuration
- `config_v2.py` - Paths and settings

## Running the App

```bash
cd "/Users/JB/Documents/IT/IT DD Test 2/9.5/it-diligence-agent 2"
python -m web.app
```

Server runs at http://127.0.0.1:5000

## Next Steps

1. ~~**Fix Processing Page**~~ - DONE
2. ~~**Connect Analysis Pipeline**~~ - DONE
3. ~~**Background Processing**~~ - DONE
4. **Real-time Updates** - Eventually add WebSocket or SSE for live progress updates
5. **Organization Module Integration** - Connect org module to main analysis pipeline
6. **Testing** - Add comprehensive test suite

## Recent Changes Made

### Phase 2 & 3 UI and Document Processing (Latest)

1. Updated `web/templates/dashboard.html`:
   - Added empty state when no analysis results
   - Added analysis metadata display (file count, timestamp)
   - Added "New Analysis" button
   - Added domain coverage indicators
   - Improved severity color coding

2. Updated `web/templates/risks.html`:
   - Added pagination (50 items per page)
   - Improved summary stats

3. Updated `web/templates/facts.html`:
   - Added pagination support

4. Updated `web/app.py`:
   - Added pagination to risks, facts, work_items routes
   - Added error handlers (404, 500, exceptions)
   - Added API endpoints (/api/health, /api/session/info, /api/cleanup)

5. Updated `web/templates/upload.html`:
   - Added file type validation (client-side)
   - Added file size limits (50MB/file, 200MB total)
   - Added duplicate file detection
   - Added upload progress spinner
   - Improved file list display with icons

6. Created `web/templates/error.html`:
   - User-friendly error pages for 404, 500, and other errors

7. Updated `web/templates/base.html`:
   - Added pagination styles
   - Added additional utility classes

### Phase 1 Backend Fixes
1. Created `web/task_manager.py` - Thread-safe background analysis task management
   - `AnalysisTaskManager` singleton for managing concurrent analyses
   - Progress tracking with phases (Discovery, Reasoning, Synthesis)
   - Task cancellation and timeout support
   - Result persistence

2. Created `web/analysis_runner.py` - Connects web app to analysis pipeline
   - `run_analysis()` function that orchestrates full pipeline
   - Calls discovery agents per domain
   - Calls reasoning agents
   - Supports progress callbacks for real-time updates

3. Created `web/session_store.py` - Thread-safe session management
   - Replaces global session with per-user isolation
   - `SessionStore` singleton with automatic cleanup
   - Links user sessions to analysis tasks

4. Updated `web/app.py`:
   - Replaced global session with SessionStore
   - Added TaskManager integration
   - Fixed `/analysis/status` to return real progress
   - Added `/analysis/cancel` endpoint
   - Improved `process_upload()` to start background analysis

5. Updated `web/templates/processing.html`:
   - Real-time progress polling
   - Live stats display (facts, risks, work items)
   - Proper step-by-step progress indication
   - Cancel button with confirmation
   - Error display support

6. Updated `ingestion/pdf_parser.py`:
   - Added `parse_documents()` function for multi-file parsing
   - Support for PDF, TXT, MD, DOCX, XLSX file types

7. Updated `requirements.txt`:
   - Added `tenacity` for retry logic
   - Added `pytest`, `pytest-asyncio` for testing
   - Added `python-docx` for Word document support

### Earlier Changes
1. Added `welcome.html` - Landing page with gradient hero
2. Added `upload.html` - Drag-drop upload with domain selection
3. Added `processing.html` - Animated loading page (rings, particles, progress steps)
4. Updated `app.py`:
   - Added `/processing` route
   - Added `/analysis/status` endpoint
   - Modified `/upload/process` to redirect to processing page
   - Added `flask_session` for tracking analysis state
5. Added `.md,.markdown` to accepted upload file types

## File Locations

```
/Users/JB/Documents/IT/IT DD Test 2/9.5/it-diligence-agent 2/
├── web/
│   ├── app.py                    # Flask application
│   ├── static/css/               # Stylesheets
│   └── templates/
│       ├── base.html
│       ├── welcome.html
│       ├── upload.html
│       ├── processing.html       # NEEDS FIX - redirects too fast
│       ├── dashboard.html
│       └── organization/
│           ├── overview.html
│           ├── staffing_tree.html
│           ├── benchmark.html
│           ├── msp_analysis.html
│           └── shared_services.html
├── models/
│   ├── organization_models.py
│   ├── organization_stores.py
│   ├── facts.py
│   └── reasoning.py
├── services/
│   └── organization_pipeline.py
├── interactive/
│   └── session.py
└── config_v2.py
```

## Demo Data

The organization module uses demo data created in `_create_demo_organization_data()` function in `app.py` (around line 503). This creates:
- 7 demo staff members
- 2 MSP relationships
- 3 shared service dependencies
- Benchmark comparison results
- TSA recommendations
- Staffing needs

To use real data, upload a census file through `/organization/run-analysis` or connect the main analysis pipeline.
