# MCP Integration Roadmap
## Connecting IT DD Agent to Firm Infrastructure

---

## Executive Summary

The IT Due Diligence Agent can integrate with firm systems via **Model Context Protocol (MCP)** in two directions:

1. **Expose** — Make our capabilities available to other firm tools
2. **Consume** — Connect to firm data sources for richer analysis

This document outlines how, when, and why to pursue each integration.

---

## Current State

```
┌─────────────────────────────────────────────────────────────┐
│                 IT DD AGENT (Standalone)                     │
│                                                             │
│   ┌──────────┐  ┌──────────┐  ┌──────────┐                │
│   │ Inventory │  │  Facts   │  │  Costs   │                │
│   │   Store   │  │  Store   │  │  Center  │                │
│   └──────────┘  └──────────┘  └──────────┘                │
│                                                             │
│   User uploads docs → AI processes → Web UI shows results   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                          │
                          │ (No external connections)
                          ▼
                       [Island]
```

**Limitation:** Tool operates in isolation. No access to firm deal data, benchmarks, or other systems.

---

## Future State with MCP

```
┌─────────────────────────────────────────────────────────────┐
│                      FIRM MCP ECOSYSTEM                      │
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │ Deal Flow   │  │  Portfolio  │  │  Benchmark  │        │
│  │   (Deals)   │  │   (PortCos) │  │   (Comps)   │        │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘        │
│         │                │                │                │
│         └────────────────┼────────────────┘                │
│                          │                                  │
│                          ▼                                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              IT DD AGENT (Connected)                 │   │
│  │                                                      │   │
│  │   CONSUMES:              EXPOSES:                   │   │
│  │   • Deal context         • Inventory queries        │   │
│  │   • Portfolio IT data    • Risk summaries           │   │
│  │   • Industry benchmarks  • Cost calculations        │   │
│  │   • Historical deals     • Evidence chains          │   │
│  │                                                      │   │
│  └─────────────────────────────────────────────────────┘   │
│                          │                                  │
│                          ▼                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │ Claude Code │  │  Deal Model │  │  IC Memo    │        │
│  │   (Users)   │  │  (Finance)  │  │  (Reports)  │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Integration Opportunities

### A. What We EXPOSE (IT DD → Firm)

| MCP Server | Tools Exposed | Who Uses It |
|------------|---------------|-------------|
| `itdd-inventory` | `query_applications`, `query_infrastructure`, `get_app_details` | Deal teams via Claude Code |
| `itdd-facts` | `search_facts`, `get_evidence_chain`, `list_gaps` | Analysts doing research |
| `itdd-risks` | `get_risks_by_severity`, `get_risk_details`, `list_mitigations` | Partners reviewing deals |
| `itdd-costs` | `get_run_rate`, `get_one_time_costs`, `get_synergies` | Finance for deal models |
| `itdd-workitems` | `get_integration_roadmap`, `get_items_by_phase` | Operating partners |

**Example Usage (from Claude Code):**
```
User: "What are the high-severity IT risks for Project Atlas?"

Claude: [Calls itdd-risks.get_risks_by_severity(deal="atlas", severity="high")]

Response: "Project Atlas has 4 high-severity IT risks:
1. R-APP-001: ERP concentration (SAP handles 80% of transactions)
2. R-SEC-003: No MFA for admin accounts
..."
```

### B. What We CONSUME (Firm → IT DD)

| Firm MCP Server | What We Get | How It Helps |
|-----------------|-------------|--------------|
| `dealflow` | Deal metadata, timeline, structure | Auto-populate deal context (carve-out vs acquisition) |
| `portfolio` | Existing portfolio company IT stacks | Compare target to buyer's systems, find overlaps |
| `benchmarks` | Industry IT spend ratios, cost benchmarks | Contextualize costs ("4.2% IT spend vs 3.5% industry avg") |
| `historical-deals` | Past IT DD findings, actual integration costs | Improve estimates based on real outcomes |
| `vdr-connector` | Direct VDR access | Auto-pull documents instead of manual upload |
| `hr-systems` | Compensation data by role/geography | More accurate headcount cost calculations |

**Example Enhancement:**
```
BEFORE (Standalone):
  Headcount cost = FTE count × assumed $150K avg

AFTER (Connected to hr-systems MCP):
  Headcount cost = FTE count × actual comp by role/level/geography
  → $28.9M calculated vs $24.2M with real data = $4.7M difference
```

---

## Phased Roadmap

### Phase 1: Expose Core Data (Foundation)
**Goal:** Make IT DD queryable from Claude Code

| Task | Description | Dependencies |
|------|-------------|--------------|
| Build `itdd-inventory` MCP server | Wrap InventoryStore with MCP protocol | MCP SDK |
| Build `itdd-costs` MCP server | Expose Cost Center calculations | None |
| Build `itdd-risks` MCP server | Expose risk register queries | None |
| Deploy to firm MCP registry | Register servers for firm-wide use | Firm infra team |
| Documentation | How to query IT DD from Claude Code | None |

**Deliverable:** Deal teams can query IT DD data without opening the web UI

**Value Unlocked:**
- Associates can ask "What apps does Target X use?" from anywhere
- Partners can get risk summaries in their workflow
- Finance can pull costs directly into models

---

### Phase 2: Connect to Deal Context
**Goal:** IT DD automatically knows deal structure

| Task | Description | Dependencies |
|------|-------------|--------------|
| Integrate `dealflow` MCP | Pull deal metadata (name, type, timeline) | Firm dealflow MCP exists |
| Auto-detect deal type | Carve-out vs acquisition vs merger | dealflow integration |
| TSA implications | Flag TSA-relevant systems based on deal type | Deal type detection |
| Deal-aware prompts | Reasoning agents get deal context | dealflow integration |

**Deliverable:** Upload docs → system knows it's a carve-out → flags TSA risks automatically

**Value Unlocked:**
- No manual deal setup
- Risks contextualized to deal structure
- TSA exposure calculated automatically

---

### Phase 3: Portfolio Intelligence
**Goal:** Compare target to buyer's existing IT

| Task | Description | Dependencies |
|------|-------------|--------------|
| Integrate `portfolio` MCP | Pull buyer's application inventory | Firm portfolio MCP exists |
| Overlap detection | Find duplicate systems (both have Salesforce) | Portfolio integration |
| Synergy enhancement | Calculate consolidation savings with real data | Overlap detection |
| Integration complexity | Score based on system compatibility | Portfolio integration |

**Deliverable:** "Target uses NetSuite, Buyer uses SAP → High integration complexity, recommend extended TSA"

**Value Unlocked:**
- Synergy estimates based on actual overlap
- Integration recommendations informed by buyer stack
- Realistic complexity assessments

---

### Phase 4: Benchmark Integration
**Goal:** Contextualize every number

| Task | Description | Dependencies |
|------|-------------|--------------|
| Integrate `benchmarks` MCP | Pull industry IT spend ratios | Firm benchmarks MCP exists |
| Auto-benchmark costs | Compare target IT spend to industry | Benchmarks integration |
| Historical accuracy | Compare estimates to actual outcomes | Historical deals data |
| Confidence calibration | Adjust estimates based on past accuracy | Historical integration |

**Deliverable:** Every cost shows "vs industry benchmark" and "vs similar past deals"

**Value Unlocked:**
- IC gets context, not just numbers
- Estimates improve over time
- "This looks high/low" backed by data

---

### Phase 5: Full Automation
**Goal:** Zero-touch document ingestion

| Task | Description | Dependencies |
|------|-------------|--------------|
| Integrate `vdr-connector` MCP | Direct VDR access | Firm VDR MCP exists |
| Auto-detect IT docs | Identify IT-relevant docs in VDR | VDR integration |
| Scheduled processing | Process new docs as they appear | VDR integration |
| Alert on findings | Notify team of high-severity discoveries | Processing pipeline |

**Deliverable:** VDR populated → IT DD runs automatically → team notified of key findings

**Value Unlocked:**
- No manual upload step
- Continuous monitoring as VDR grows
- Faster time-to-insight

---

## Technical Architecture

### MCP Server Structure (What We Build)

```
itdd-mcp-servers/
├── servers/
│   ├── inventory/
│   │   ├── server.py          # MCP server implementation
│   │   ├── tools.py           # Tool definitions
│   │   └── handlers.py        # Request handlers
│   ├── costs/
│   │   ├── server.py
│   │   ├── tools.py
│   │   └── handlers.py
│   ├── risks/
│   │   └── ...
│   └── workitems/
│       └── ...
├── shared/
│   ├── auth.py                # Firm SSO integration
│   ├── data_access.py         # Connect to IT DD stores
│   └── schemas.py             # Shared data models
├── config/
│   └── mcp_config.json        # Server configurations
└── deploy/
    ├── Dockerfile
    └── k8s/                   # Kubernetes manifests
```

### Example MCP Server Implementation

```python
# servers/inventory/server.py
from mcp import Server, Tool
from shared.data_access import get_inventory_store

server = Server("itdd-inventory")

@server.tool()
def query_applications(
    deal_id: str,
    status: str = "active",
    min_cost: int = 0
) -> list:
    """Query applications from IT DD inventory.

    Args:
        deal_id: The deal identifier
        status: Filter by status (active, planned, retired)
        min_cost: Minimum annual cost filter

    Returns:
        List of applications matching criteria
    """
    store = get_inventory_store(deal_id)
    apps = store.get_items(
        inventory_type="application",
        status=status
    )
    return [a for a in apps if a.data.get("cost", 0) >= min_cost]

@server.tool()
def get_app_details(deal_id: str, app_id: str) -> dict:
    """Get detailed information about a specific application."""
    store = get_inventory_store(deal_id)
    return store.get_item(app_id)

if __name__ == "__main__":
    server.run()
```

### Firm MCP Client Integration

```python
# In IT DD Agent - consuming firm MCPs
from mcp import Client

class FirmMCPIntegration:
    def __init__(self):
        self.dealflow = Client("firm://dealflow")
        self.portfolio = Client("firm://portfolio")
        self.benchmarks = Client("firm://benchmarks")

    def get_deal_context(self, deal_id: str) -> dict:
        """Pull deal metadata from firm systems."""
        return self.dealflow.call("get_deal", deal_id=deal_id)

    def get_buyer_stack(self, deal_id: str) -> list:
        """Get buyer's application inventory for comparison."""
        deal = self.get_deal_context(deal_id)
        buyer_id = deal.get("buyer_entity_id")
        return self.portfolio.call("get_applications", entity_id=buyer_id)

    def get_industry_benchmarks(self, industry: str) -> dict:
        """Get IT spend benchmarks for industry."""
        return self.benchmarks.call("get_it_benchmarks", industry=industry)
```

---

## Value Summary by Phase

| Phase | Investment | Value Unlocked |
|-------|------------|----------------|
| **Phase 1** | Build 4 MCP servers | Query IT DD from anywhere in firm |
| **Phase 2** | Integrate dealflow | Auto deal context, smarter analysis |
| **Phase 3** | Integrate portfolio | Buyer comparison, real synergies |
| **Phase 4** | Integrate benchmarks | Contextual insights, better estimates |
| **Phase 5** | Integrate VDR | Zero-touch automation |

---

## Dependencies & Prerequisites

### From Firm Infrastructure Team
- [ ] MCP registry available for server registration
- [ ] Authentication/SSO integration for MCP servers
- [ ] Network access between IT DD and firm MCP servers

### Existing Firm MCPs Needed
- [ ] `dealflow` — Deal metadata and structure
- [ ] `portfolio` — Portfolio company data
- [ ] `benchmarks` — Industry comparison data
- [ ] `vdr-connector` — VDR access (for Phase 5)

### IT DD Readiness
- [x] Data stores support external queries
- [x] Cost calculations are modular
- [ ] Deal isolation (multi-deal support)
- [ ] API authentication layer

---

## Next Steps

1. **Discovery:** Inventory existing firm MCP servers
2. **Prioritize:** Which integrations unlock most value?
3. **Phase 1 Build:** Start with exposing our data
4. **Pilot:** Test with one deal team
5. **Iterate:** Expand based on feedback

---

## Appendix: MCP Protocol Basics

**What is MCP?**
Model Context Protocol — a standard for AI tools to communicate with external systems.

**Key Concepts:**
- **Server:** Exposes tools (functions) that AI can call
- **Client:** Consumes tools from servers
- **Tool:** A function with defined inputs/outputs
- **Transport:** How messages move (stdio, HTTP, WebSocket)

**Why MCP vs Custom API?**
- Standard protocol = interoperability
- Built-in tool discovery
- Type-safe schemas
- Works natively with Claude Code

---

*Document Version: 1.0*
*Last Updated: January 2026*
