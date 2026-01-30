# System Data Audit

> **Date:** January 2026
> **Purpose:** Document data disconnects and UI/UX issues identified during inventory system integration

---

## Executive Summary

The system currently has **two separate data systems** that are not connected, causing inconsistent data to appear across different pages. This creates confusion and undermines trust in the tool's outputs.

---

## Two Separate Data Systems (The Core Problem)

| Data Source | What It Contains | Storage Location | Where Used |
|------------|------------------|------------------|------------|
| **FactStore** | 38 facts extracted by discovery agents | `facts_*.json` | `/applications`, `/organization`, `/infrastructure`, `/risks`, `/dashboard` |
| **InventoryStore** | 33 apps from structured table import | `inventory_store.json` | `/inventory`, `/inventory/diagram`, `/inventory/insights` |

### FactStore Details
- **Source:** Discovery agents reading prose documents
- **Applications domain:** 13 facts (F-APP-001 through F-APP-013)
- **Organization domain:** 6 facts (141 staff referenced)
- **Infrastructure domain:** 8 facts
- **Cybersecurity domain:** 5 facts
- **Network domain:** 2 facts
- **Identity/Access domain:** 4 facts

### InventoryStore Details
- **Source:** Parsed markdown tables (Application Inventory document)
- **Applications:** 33 items with full metadata
- **Infrastructure:** 2 items
- **Total annual cost:** $7,183,698
- **Has:** Vendor, cost, criticality, category, users for each item

---

## The Disconnects

| Page | Currently Shows | Data Source | Expected | Status |
|------|-----------------|-------------|----------|--------|
| `/applications` | **33 applications** | InventoryStore | 33 | ✅ FIXED |
| `/organization` | **141 staff** | FactStore | ? | ⚠️ Works but different data model |
| `/infrastructure` | **2 items** | InventoryStore | 2 | ✅ FIXED |
| `/inventory` | **33 applications** | InventoryStore | 33 | ✅ Consistent |
| `/dashboard` | **Single count** | InventoryStore | Consistent | ✅ FIXED - removed domain chip |
| `/risks` | **17 risks** | ReasoningStore | 17 | ⚠️ Not linked to inventory items |
| `/inventory/insights` | **Risks loaded** | ReasoningStore | 17 | ✅ FIXED - loads from findings file |

---

## Visual/UI Issues Identified

### Fixed Issues
1. **Mermaid Diagram** - Was showing raw code instead of rendering
   - Cause: Jinja HTML escaping
   - Fix: Added `| safe` filter

2. **Inventory pages standalone styling** - Didn't match main app UI
   - Cause: Templates didn't extend `base.html`
   - Fix: Updated templates to use `{% extends "base.html" %}`

3. **Node ID syntax errors in Mermaid** - Parentheses in IDs breaking parser
   - Cause: `make_id()` not stripping special characters
   - Fix: Updated to use regex to keep only alphanumeric

### Outstanding Issues
1. **Dashboard confusion** - Shows "applications: 13" chip AND "33 Applications" card
2. **Navigation disconnect** - `/applications` and `/inventory` show different data for same concept
3. **No evidence linking** - Risks don't link to inventory items they reference

---

## Current Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        CURRENT STATE                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   Documents ──→ Discovery Agents ──→ FactStore (38 facts)       │
│                                            │                    │
│                                            ▼                    │
│                                      ReasoningStore             │
│                                      (17 risks, 21 work items)  │
│                                            │                    │
│                                            ▼                    │
│                                    /applications (13)           │
│                                    /organization (141)          │
│                                    /risks (17)                  │
│                                                                 │
│   ─────────────────── NO CONNECTION ───────────────────         │
│                                                                 │
│   Documents ──→ File Router ──→ InventoryStore (33 apps)        │
│                                            │                    │
│                                            ▼                    │
│                                    /inventory (33)              │
│                                    /inventory/diagram           │
│                                    /inventory/insights (0)      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Desired Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        DESIRED STATE                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   Structured Docs ──→ InventoryStore (Single Source of Truth)   │
│   (Excel, Tables)           │                                   │
│                             │ 33 apps with metadata             │
│                             ▼                                   │
│   ┌─────────────────────────────────────────────────────┐       │
│   │  I-APP-001: Duck Creek Policy ($546K, Critical)     │       │
│   │  I-APP-002: Majesco Policy ($440K, Critical)        │       │
│   │  ...                                                │       │
│   └─────────────────────────────────────────────────────┘       │
│                             │                                   │
│                             │ Linked by item ID                 │
│                             ▼                                   │
│   Prose Docs ──→ Discovery ──→ Facts (Annotations ON items)     │
│                                    │                            │
│                                    │ F-APP-001 references       │
│                                    │ I-APP-001                  │
│                                    ▼                            │
│                             ReasoningStore                      │
│                             (Risks linked to items)             │
│                                    │                            │
│                                    ▼                            │
│                             ALL PAGES show consistent data      │
│                             /applications = /inventory = 33     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Priority Fixes Needed

### P0 - Critical (Data Consistency)
1. ✅ **Make `/applications` use InventoryStore** - DONE
   - Updated `applications_overview()` to pull from InventoryStore first
   - Now shows 33 applications with costs

2. ⏳ **Link facts to inventory items** - FUTURE ENHANCEMENT
   - Add `inventory_item_id` field to facts
   - F-APP-001 about "Duck Creek Policy" → links to I-APP-xxx
   - Note: Risk detail now shows affected items via name matching (interim solution)

3. ✅ **Connect risks to inventory items** - DONE
   - Risk detail page now shows "Affected Inventory Items" section
   - Matches fact items to inventory items by name
   - Shows criticality, cost, vendor, users for each affected item

### P1 - High (User Experience)
4. ✅ **Populate `/inventory/insights` from ReasoningStore** - DONE
   - Now loads risks from findings files
   - Shows 2 Critical, 6 High findings

5. ✅ **Consolidate dashboard** - DONE
   - Removed "applications: 13" domain chip
   - Shows consistent inventory counts

6. ✅ **Add evidence chain UI** - DONE
   - Risk → click → see "Why This Conclusion?" with reasoning chain
   - Risk detail page shows supporting facts with exact quotes
   - Facts drawer shows source document names and confidence score
   - Facts page enhanced with evidence chain styling

### P2 - Medium (Polish)
7. ✅ **Merge diagram approaches** - DONE
   - Nodes now show cost (e.g., "$546K")
   - Nodes show criticality indicator (🔴 Critical, 🟠 High, 🟡 Medium)
   - Border colors: Critical=red, High=orange, Medium=yellow
   - Data flow connections with labels (Claims Data, GL Data, SSO, etc.)

8. ✅ **Organization data alignment** - ARCHITECTURAL DECISION
   - Organization uses FactStore (appropriate - complex data model)
   - Org data includes roles, compensation, tenure, MSP relationships
   - This doesn't fit simple inventory model - FactStore is correct approach
   - Future: Could add org-specific inventory type if structured imports needed

### Also Fixed
- ✅ **Make `/infrastructure` use InventoryStore** - DONE
  - Updated `infrastructure_overview()` to pull from InventoryStore first
  - Updated `infrastructure_category()` route as well

---

## Files Involved

### Data Stores
- `stores/inventory_store.py` - InventoryStore class
- `pipeline/schemas.py` - FactStore, ReasoningStore classes
- `data/inventory_store.json` - Persisted inventory
- `output/facts_*.json` - Persisted facts

### Routes Using FactStore
- `web/app.py` lines 2258-2305 - `/applications` routes
- `web/app.py` lines 2312+ - `/infrastructure` routes
- `web/app.py` - `/organization` routes

### Routes Using InventoryStore
- `web/blueprints/inventory.py` - All `/inventory/*` routes

### Templates
- `web/templates/applications/` - Uses FactStore data
- `web/templates/inventory/` - Uses InventoryStore data

---

## Questions to Resolve

1. Should FactStore be deprecated in favor of InventoryStore for structured data?
2. Should facts become "annotations" on inventory items rather than standalone entities?
3. How to handle the 13 apps in FactStore that may overlap with the 33 in InventoryStore?
4. Should organization data (141 staff) move to InventoryStore as well?

---

## Next Steps

1. Review this audit with stakeholders
2. Decide on target architecture (merge vs. link vs. replace)
3. Prioritize fixes based on demo/user needs
4. Implement P0 fixes first for data consistency
5. Add evidence chain UI for trust/transparency

---

*Audit performed: January 2026*
