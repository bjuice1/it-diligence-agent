# Running the IT Due Diligence Tool
## All the Ways to Use It

---

## Overview Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         IT DUE DILIGENCE TOOL                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                     PRODUCTION (Recommended)                         │   │
│   │                                                                     │   │
│   │   ┌─────────────────┐                                               │   │
│   │   │     DOCKER      │  Full stack with all services                 │   │
│   │   │   (Port 5001)   │  Web UI + API + Workers + DB + Redis         │   │
│   │   └─────────────────┘                                               │   │
│   │                                                                     │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                     DEVELOPMENT / TESTING                            │   │
│   │                                                                     │   │
│   │   ┌───────────────┐  ┌───────────────┐  ┌───────────────┐          │   │
│   │   │  FLASK LOCAL  │  │   STREAMLIT   │  │     CLI       │          │   │
│   │   │  (Port 5001)  │  │  (Port 8501)  │  │   Terminal    │          │   │
│   │   └───────────────┘  └───────────────┘  └───────────────┘          │   │
│   │                                                                     │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                     BATCH / SCRIPTING                                │   │
│   │                                                                     │   │
│   │   ┌───────────────┐  ┌───────────────┐  ┌───────────────┐          │   │
│   │   │  main_v2.py   │  │   app.py      │  │ session_cli   │          │   │
│   │   │   (CLI)       │  │  (Streamlit)  │  │  (Sessions)   │          │   │
│   │   └───────────────┘  └───────────────┘  └───────────────┘          │   │
│   │                                                                     │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 1. Docker (Recommended for Production)

**What it is:** Full production stack with web UI, background workers, database, and Redis.

**Best for:** Day-to-day deal work, team collaboration, persistent data.

### Quick Start
```bash
cd docker/
docker-compose up -d
# Open http://localhost:5001
```

### What's Included
| Service | Port | Purpose |
|---------|------|---------|
| **app** | 5001 | Flask web UI + API |
| **celery-worker** | — | Background document processing |
| **celery-beat** | — | Scheduled tasks |
| **postgres** | 5432 | Database for deals, findings |
| **redis** | 6379 | Sessions, task queue |
| **minio** | 9000/9001 | Document storage (S3-compatible) |

### Architecture
```
┌─────────────────────────────────────────────────────────────────┐
│                         BROWSER                                  │
│                    http://localhost:5001                         │
└─────────────────────────────┬───────────────────────────────────┘
                              │
┌─────────────────────────────▼───────────────────────────────────┐
│                      FLASK APP (app)                             │
│   • Web UI (upload, dashboard, costs, risks)                    │
│   • REST API                                                    │
│   • Authentication                                              │
└───────────┬─────────────────────────────────────┬───────────────┘
            │                                     │
            ▼                                     ▼
┌───────────────────────┐             ┌───────────────────────────┐
│     CELERY WORKER     │             │      POSTGRES + REDIS     │
│  • Document parsing   │             │  • Deals, findings        │
│  • AI analysis        │             │  • Sessions               │
│  • Background tasks   │             │  • Task queue             │
└───────────────────────┘             └───────────────────────────┘
```

### Commands
```bash
# Start everything
docker-compose up -d

# View logs
docker-compose logs -f app
docker-compose logs -f celery-worker

# Stop everything
docker-compose down

# Rebuild after code changes
docker-compose build app && docker-compose up -d

# Reset database (fresh start)
docker-compose down -v
docker-compose up -d
```

### Environment Variables (docker/.env)
```bash
ANTHROPIC_API_KEY=sk-ant-...     # Required
AUTH_REQUIRED=true                # Enable login
DEFAULT_ADMIN_EMAIL=admin@example.com
DEFAULT_ADMIN_PASSWORD=changeme123
```

---

## 2. Local Flask (Development)

**What it is:** Run the Flask web app directly on your machine without Docker.

**Best for:** Development, debugging, quick testing.

### Quick Start
```bash
# Set up environment
export ANTHROPIC_API_KEY=sk-ant-...
export FLASK_ENV=development
export AUTH_REQUIRED=false  # Skip login for dev

# Run Flask directly
python -m flask --app web.app run --port 5001

# Or with the app.py entrypoint
python app.py
```

### What You Get
- Web UI at http://localhost:5001
- Hot reload on code changes
- No background workers (processing is synchronous)
- File-based storage (no database needed)

### Architecture
```
┌─────────────────────────────────────────────────────────────────┐
│                         BROWSER                                  │
│                    http://localhost:5001                         │
└─────────────────────────────┬───────────────────────────────────┘
                              │
┌─────────────────────────────▼───────────────────────────────────┐
│                      FLASK APP                                   │
│   • Web UI                                                      │
│   • Synchronous processing (no workers)                         │
│   • File-based stores (data/*.json)                             │
└─────────────────────────────────────────────────────────────────┘
```

### When to Use
- Writing/testing UI changes
- Debugging API endpoints
- Quick experiments

---

## 3. Streamlit App

**What it is:** Alternative UI using Streamlit framework.

**Best for:** Data exploration, visualization, prototyping.

### Quick Start
```bash
export ANTHROPIC_API_KEY=sk-ant-...
streamlit run streamlit_app/main.py
# Opens http://localhost:8501
```

### What You Get
- Dashboard with metrics
- Interactive fact/risk exploration
- Coverage analysis views
- Chart visualizations

### Architecture
```
┌─────────────────────────────────────────────────────────────────┐
│                         BROWSER                                  │
│                    http://localhost:8501                         │
└─────────────────────────────┬───────────────────────────────────┘
                              │
┌─────────────────────────────▼───────────────────────────────────┐
│                     STREAMLIT APP                                │
│   • React-like components                                       │
│   • Session state management                                    │
│   • Direct store access                                         │
└─────────────────────────────────────────────────────────────────┘
```

### Views Available
- Dashboard
- Risks, Work Items, Facts, Gaps
- Applications, Infrastructure
- Costs, Staffing
- Org Chart, Vendors

---

## 4. CLI - Batch Processing (main_v2.py)

**What it is:** Command-line tool for running analysis pipelines.

**Best for:** Batch processing, scripting, CI/CD.

### Quick Start
```bash
export ANTHROPIC_API_KEY=sk-ant-...

# Full pipeline on a folder of documents
python main_v2.py data/input/

# Discovery only (extract facts)
python main_v2.py data/input/ --discovery-only

# Reasoning only (from existing facts)
python main_v2.py --from-facts output/facts/facts_latest.json

# Single domain for testing
python main_v2.py data/input/ --domain applications

# Interactive shell after analysis
python main_v2.py data/input/ --interactive
```

### Pipeline Stages
```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  DISCOVERY  │ ──► │  REASONING  │ ──► │  SYNTHESIS  │
│   (Haiku)   │     │  (Sonnet)   │     │  (Reports)  │
└─────────────┘     └─────────────┘     └─────────────┘
     │                    │                   │
     ▼                    ▼                   ▼
 facts.json          risks.json          report.html
                     work_items.json
```

### Options
| Flag | Description |
|------|-------------|
| `--discovery-only` | Stop after extracting facts |
| `--from-facts FILE` | Skip discovery, use existing facts |
| `--domain NAME` | Run single domain (applications, infrastructure, etc.) |
| `--no-vdr` | Skip VDR request generation |
| `--interactive` | Enter shell after analysis |
| `--interactive-only` | Just load existing outputs into shell |

---

## 5. CLI - Session-Based (session_cli.py)

**What it is:** Incremental analysis with named sessions.

**Best for:** Multi-round VDR analysis, tracking changes over time.

### Quick Start
```bash
export ANTHROPIC_API_KEY=sk-ant-...

# Create a session for a deal
python session_cli.py create acme_2024 --target "Acme Corp" --deal-type carve_out

# Add documents and run discovery
python session_cli.py add acme_2024 data/vdr_round1/
python session_cli.py discover acme_2024

# Run reasoning
python session_cli.py reason acme_2024

# Later: Add more docs (only processes new/changed)
python session_cli.py add acme_2024 data/vdr_round2/
python session_cli.py discover acme_2024

# Export deliverables
python session_cli.py export acme_2024 --output ./deliverables/

# List all sessions
python session_cli.py list

# Check status
python session_cli.py status acme_2024
```

### Session Lifecycle
```
┌─────────────────────────────────────────────────────────────────┐
│                    SESSION: acme_2024                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   Round 1                     Round 2                           │
│   ┌─────────────────┐        ┌─────────────────┐               │
│   │ add docs        │        │ add more docs   │               │
│   │ discover        │   ──►  │ discover (delta)│   ──►  ...    │
│   │ reason          │        │ reason          │               │
│   └─────────────────┘        └─────────────────┘               │
│                                                                 │
│   Documents: 5                Documents: 12                     │
│   Facts: 45                   Facts: 89 (+44)                   │
│   Risks: 8                    Risks: 14 (+6)                    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Benefits
- Track changes across VDR rounds
- Only re-process new/changed documents
- Named sessions for organization
- Export deliverables anytime

---

## 6. Interactive Shell

**What it is:** REPL for reviewing and adjusting findings.

**Best for:** Manual review, adjustments, exploration.

### Quick Start
```bash
# Enter interactive mode after analysis
python main_v2.py data/input/ --interactive

# Or load existing outputs
python main_v2.py --interactive-only
```

### Commands
```
IT DD Agent > help

Navigation:
  status, s         Show current status
  dashboard, d      Show dashboard summary

Listing:
  list facts        List all facts (or: lf)
  list risks        List all risks (or: lr)
  list work-items   List work items (or: lw)
  list gaps         List gaps (or: lg)

Viewing:
  show <id>         Show details for item
  explain <id>      Explain reasoning for item

Adjusting:
  adjust <id>       Modify item (severity, phase, cost)
  delete <id>       Remove item
  note <id> <text>  Add note to item

Exporting:
  export            Export all to files

Other:
  history           Show command history
  undo              Undo last change
  exit, q           Exit shell
```

---

## Comparison Matrix

| Aspect | Docker | Local Flask | Streamlit | CLI Batch | CLI Session |
|--------|--------|-------------|-----------|-----------|-------------|
| **UI** | Web | Web | Web | Terminal | Terminal |
| **Port** | 5001 | 5001 | 8501 | — | — |
| **Background Workers** | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Database** | PostgreSQL | File JSON | File JSON | File JSON | File JSON |
| **Multi-user** | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Authentication** | ✅ | Optional | ❌ | ❌ | ❌ |
| **Best For** | Production | Dev/Debug | Exploration | Batch/Script | VDR Rounds |

---

## Which Should I Use?

```
┌─────────────────────────────────────────────────────────────────┐
│                    DECISION TREE                                 │
└─────────────────────────────────────────────────────────────────┘

Are you working on a real deal?
├── YES → Use DOCKER
│         - Full production stack
│         - Persistent data
│         - Authentication
│         - Background processing
│
└── NO → What are you doing?
         │
         ├── Developing/debugging UI?
         │   └── Use LOCAL FLASK
         │       - Hot reload
         │       - Direct code changes
         │
         ├── Exploring data visually?
         │   └── Use STREAMLIT
         │       - Charts and visualizations
         │       - Interactive widgets
         │
         ├── Batch processing many docs?
         │   └── Use CLI (main_v2.py)
         │       - Scriptable
         │       - Pipeline options
         │
         └── Tracking multi-round VDR?
             └── Use CLI (session_cli.py)
                 - Named sessions
                 - Incremental processing
```

---

## Quick Reference

```bash
# DOCKER (Production)
cd docker && docker-compose up -d
# → http://localhost:5001

# LOCAL FLASK (Development)
python -m flask --app web.app run --port 5001
# → http://localhost:5001

# STREAMLIT (Exploration)
streamlit run streamlit_app/main.py
# → http://localhost:8501

# CLI BATCH (Scripting)
python main_v2.py data/input/

# CLI SESSION (VDR Rounds)
python session_cli.py create deal_name
python session_cli.py add deal_name data/docs/
python session_cli.py discover deal_name
python session_cli.py reason deal_name
```

---

*Last Updated: January 2026*
