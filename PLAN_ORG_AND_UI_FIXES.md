# 15-Point Plan: Organization, Work Items, and UI Fixes

## Issue Summary
1. Work Item IDs look random (e.g., "WI-a3f2" instead of "WI-001")
2. Some areas missing Fact ID linkage (questions, work items, etc.)
3. Org Mermaid diagram too big and centered weirdly
4. Organization data still not pulling from analysis

---

## PART A: Work Item & ID Display Issues (Points 1-4)

### Point 1: Add Sequential Display IDs for Work Items
**File:** `tools_v2/reasoning_tools.py`
- The hash-based IDs (WI-a3f2) are for deduplication but confusing to users
- Add a `display_id` field that shows sequential numbering (WI-001, WI-002)
- Keep the hash-based `finding_id` for internal deduplication
- Update `ReasoningStore` to track display order

### Point 2: Show Fact ID Links in Work Items Table
**Files:** `web/templates/work_items.html`, `web/app.py`
- Work items have `triggered_by` and `based_on_facts` fields but they may not display
- Ensure the template shows linked fact IDs (e.g., "Based on: F-INF-001, F-APP-002")
- Add click-to-navigate to the source fact

### Point 3: Show Fact ID Links in Risks Table
**Files:** `web/templates/risks.html`, `web/app.py`
- Risks have `based_on_facts` field
- Ensure the template displays these fact IDs
- Add tooltip or expandable row to show supporting facts

### Point 4: Show Fact ID Links in Gaps/Questions
**Files:** `web/templates/gaps.html`, `tools_v2/open_questions.py`
- Questions have `based_on_facts` field (line 42 in open_questions.py)
- Ensure the template displays which facts triggered the question
- Link back to source facts for context

---

## PART B: Org Chart Mermaid Fixes (Points 5-9)

### Point 5: Fix Mermaid Container Layout
**File:** `web/templates/organization/staffing_tree.html`
- Remove the 1.3x scale transform (causing sizing issues)
- Change container to use flexbox with left alignment
- Set explicit width/height instead of transforms

### Point 6: Make Chart Horizontally Scrollable
**File:** `web/templates/organization/staffing_tree.html`
- Add `overflow-x: auto` to container
- Set max-width to viewport width
- Allow horizontal scroll for large org charts

### Point 7: Adjust Mermaid Spacing Configuration
**File:** `web/templates/organization/staffing_tree.html`
- Reduce nodeSpacing from 100 to 60
- Reduce rankSpacing from 120 to 80
- Make the chart more compact

### Point 8: Add Zoom Controls to Org Chart
**File:** `web/templates/organization/staffing_tree.html`
- Add zoom in/out buttons
- Add "fit to screen" button
- Use CSS transform scale controlled by JS

### Point 9: Fix Chart Centering/Alignment
**File:** `web/templates/organization/staffing_tree.html`
- Remove `text-align: center` from mermaid div
- Use `justify-content: flex-start` in container
- Ensure chart starts from left edge

---

## PART C: Organization Data Pull Issues (Points 10-14)

### Point 10: Debug Session Data Loading
**File:** `web/app.py` - `get_session()` function
- Add detailed logging showing what session data exists
- Log which file path is being loaded (task.facts_file vs fallback)
- Trace why org facts aren't being found

### Point 11: Fix Facts File Path Resolution
**File:** `web/app.py` - `get_session()` function
- Check if `OUTPUT_DIR.glob("facts_*.json")` returns correct files
- Ensure newest file is being loaded (not empty old ones)
- Add file size check to skip empty facts files

### Point 12: Clear Demo Data Cache Properly
**File:** `web/app.py` - `get_organization_analysis()`
- Current logic may return cached demo data even when real data exists
- Force rebuild if session has ANY facts (not just org facts)
- Add cache invalidation timestamp

### Point 13: Add Data Source Indicator in Org UI
**File:** `web/templates/organization/overview.html`
- Show banner: "Data Source: Analysis" or "Data Source: Demo Data"
- Display timestamp of last data refresh
- Help user know if they're seeing real vs demo data

### Point 14: Fix org_bridge to Handle Empty Facts Gracefully
**File:** `services/organization_bridge.py`
- If no org facts but other facts exist, show appropriate message
- Don't fall back to demo data if analysis ran but found no org info
- Distinguish "no analysis" from "analysis found nothing"

---

## PART D: Verification & Testing (Point 15)

### Point 15: Create Test Script for Data Flow
**File:** `test_org_data_flow.py` (new)
- Script to verify facts → session → organization → UI flow
- Load facts from latest file
- Call `build_organization_result()` directly
- Print diagnostic info about what data exists

---

## Implementation Order (Recommended)

**Phase 1 - Critical Data Fixes (Points 10-14):**
Fix org data not pulling - this is the core issue

**Phase 2 - Org Chart UI (Points 5-9):**
Fix the Mermaid display issues

**Phase 3 - ID & Linkage (Points 1-4):**
Improve work item IDs and fact linkage

**Phase 4 - Verification (Point 15):**
Create test script to prevent regression

---

## Quick Wins (Can Fix Now)

1. Remove the `transform: scale(1.3)` from mermaid CSS
2. Add horizontal scroll to chart container
3. Add data source indicator to org overview
4. Add logging to `get_session()` and `get_organization_analysis()`
