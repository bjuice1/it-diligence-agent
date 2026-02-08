# Audit C3: Replace Mermaid Org Chart with CSS Tree

## Status: PARTIALLY IMPLEMENTED
## Priority: MEDIUM (Tier 3 - Feature Improvement) → **Tier 2 if partner-facing**
## Complexity: Medium
## Review Score: 8.6/10 (GPT review, Feb 8 2026)
## Implementation Date: Feb 8, 2026

---

## 1. Problem Statement

**Symptom:** Mermaid-based org chart crashes on special characters, doesn't scale, and has hardcoded assumptions.

**User Impact:**
- Org chart unusable for real names (O'Brien, R&D, etc.)
- Crashes or renders incorrectly
- Cannot display large organizations (>20 nodes)
- Looks unprofessional when broken

**Expected Behavior:** Org chart renders cleanly for any names, scales to 50+ nodes, gracefully handles missing hierarchy data.

**Tier Note:** If showing to partners soon → Tier 2 (org chart breakage is reputation damage)

---

## 2. Current Problems

### 2.1 Special Character Crashes
Mermaid syntax breaks on:
- Apostrophes: `O'Brien` → syntax error
- Ampersands: `R&D` → breaks
- Parentheses: `Manager (Interim)` → breaks
- Quotes: `John "Jack" Smith` → breaks

### 2.2 Hardcoded Root
```javascript
// Current code assumes:
root = "CIO / IT Leader"  // What if different?
```

### 2.3 Fragile Parent Matching
```javascript
// Current matching logic:
if (role.includes(parent_text)) { ... }
// Fails when:
// - "VP of Technology" doesn't match "VP Technology"
// - Name variants don't match exactly
```

### 2.4 Scaling Issues
- Horizontal layout overflows
- No scrolling or zoom
- >20 nodes become unreadable

### 2.5 Multiple Implementations
Three different org chart codepaths:
1. Streamlit version
2. Flask web version
3. presentation.py version

All slightly different, all broken in different ways.

---

## 3. Data Contract (GPT FEEDBACK)

### Expected Org Fact Shape:

```python
@dataclass
class OrgNode:
    """Standard org chart node."""
    name: str                    # Person/team name
    role: str                    # Job title or team role
    reports_to: str              # Parent name (or empty string, not None)
    type: str                    # 'leadership', 'team', 'staff', 'vendor'

    # Optional
    team: str = ''
    headcount: int = 0
    person_id: str = ''          # For stable matching (future)
```

### Defaults:
- Empty string for missing fields (not None)
- `type` defaults to 'staff' if unspecified
- `reports_to` empty means potential root

---

## 4. Multi-Root Handling (GPT FEEDBACK)

### Problem: Current code requires exactly one root

```python
# Current (too strict):
if len(roots) != 1:
    return None  # Falls back to flat list
```

### Solution: Synthetic root for multiple roots

```python
def _build_tree_from_reports_to(people: List[dict]) -> Optional[dict]:
    """Build tree, handling multiple roots gracefully."""

    # Find roots (no reports_to)
    roots = [p for p in people if not p.get('reports_to')]

    if len(roots) == 0:
        # No root found - might be circular, fall back
        return None

    if len(roots) == 1:
        # Perfect - single root
        root = roots[0]
    else:
        # Multiple roots - create synthetic parent (GPT FEEDBACK)
        root = {
            'name': 'IT Organization',
            'role': '',
            'type': 'synthetic',
            'reports_to': '',
            'children': roots  # Attach all roots as children
        }
        # Update roots to report to synthetic
        for r in roots:
            r['reports_to'] = 'IT Organization'

    # Build children recursively
    return _build_children_recursive(root, people, visited=set())
```

This dramatically reduces "flat list" outcomes.

---

## 5. Cycle Detection (GPT FEEDBACK)

### Problem: Circular reports_to will infinite-loop

### Solution: Track visited nodes

```python
def _build_children_recursive(
    parent: dict,
    all_people: List[dict],
    visited: set
) -> dict:
    """Build children with cycle detection."""

    parent_name = parent['name']

    # Cycle detection (GPT FEEDBACK)
    if parent_name in visited:
        logger.warning(f"Cycle detected at: {parent_name}")
        parent['cycle_detected'] = True
        return parent

    visited.add(parent_name)

    # Find children
    children = [
        p for p in all_people
        if p.get('reports_to') == parent_name and p['name'] != parent_name
    ]

    parent['children'] = [
        _build_children_recursive(child, all_people, visited.copy())
        for child in children
    ]

    return parent
```

**Behavior:** Cut the edge, mark the node, keep rendering (more resilient than full fallback).

---

## 6. Fuzzy Matching for reports_to (GPT FEEDBACK)

### Problem: Exact match fails on name variants

`"John Smith"` vs `"John A. Smith"` vs `"J. Smith"`

### Solution: Normalized matching

```python
def _normalize_name(name: str) -> str:
    """Normalize for matching."""
    return name.lower().strip().replace('.', '').replace(',', '')


def _find_parent(child: dict, all_people: List[dict]) -> Optional[dict]:
    """Find parent with fuzzy matching."""
    reports_to = child.get('reports_to', '')
    if not reports_to:
        return None

    normalized_target = _normalize_name(reports_to)

    # Exact match first
    for p in all_people:
        if p['name'] == reports_to:
            return p

    # Normalized match
    candidates = []
    for p in all_people:
        if _normalize_name(p['name']) == normalized_target:
            candidates.append(p)

    # Only use if exactly one candidate (GPT FEEDBACK)
    if len(candidates) == 1:
        return candidates[0]

    # Partial match as last resort
    for p in all_people:
        if normalized_target in _normalize_name(p['name']):
            candidates.append(p)

    if len(candidates) == 1:
        return candidates[0]

    return None  # Ambiguous or not found
```

---

## 7. Large Tree UI Affordances (GPT FEEDBACK)

### Problem: 50-100 nodes gets ugly

### Solutions:

**Option A: Depth limiting (server-side, no JS)**
```python
def _render_tree_node(node: dict, depth: int, max_depth: int = 3) -> str:
    """Render with depth limiting."""
    # ... render current node ...

    children = node.get('children', [])
    if depth >= max_depth and children:
        # Collapse deep levels
        html += f'<div class="collapsed-indicator">+ {len(children)} more</div>'
        return html

    for child in children:
        html += _render_tree_node(child, depth + 1, max_depth)

    return html
```

**Option B: CSS collapsible (minimal JS)**
```css
.org-tree .node-children.collapsed {
    display: none;
}

.org-tree .toggle-btn::before {
    content: '▶';
}

.org-tree .toggle-btn.expanded::before {
    content: '▼';
}
```

**Recommended:** Start with Option A (no JS), add Option B later if needed.

---

## 8. One Renderer Rule (GPT FEEDBACK - Critical)

### Rule: Single source for tree generation and rendering

```python
# This is the ONLY place org trees are generated:
# tools_v2/org_chart.py (NEW)

def build_org_tree(fact_store, entity='target') -> OrgTreeData:
    """Single source of truth for org tree data."""
    ...

def render_org_tree_html(tree_data: OrgTreeData) -> str:
    """Single source of truth for org HTML."""
    ...

# ALL consumers use this:
# - Streamlit
# - Flask web view
# - presentation.py
# - domain_generators/organization.py
```

**Why:** Fix once, works everywhere. No divergence.

---

## 9. CSS Tree Stylesheet

```css
/* org_tree.css */

.org-tree {
    overflow-x: auto;
    padding: 20px;
}

.org-tree ul {
    display: flex;
    justify-content: center;
    padding-top: 20px;
    position: relative;
    list-style: none;
    margin: 0;
}

.org-tree ul::before {
    content: '';
    position: absolute;
    top: 0;
    left: 50%;
    width: 0;
    height: 20px;
    border-left: 2px solid #ccc;
}

.org-tree li {
    display: flex;
    flex-direction: column;
    align-items: center;
    position: relative;
    padding: 20px 10px 0;
}

/* Horizontal connector lines */
.org-tree li::before,
.org-tree li::after {
    content: '';
    position: absolute;
    top: 0;
    width: 50%;
    height: 20px;
    border-top: 2px solid #ccc;
}

.org-tree li::before { right: 50%; }
.org-tree li::after { left: 50%; }

.org-tree li:first-child::before,
.org-tree li:last-child::after {
    border: none;
}

.org-tree li:only-child::before,
.org-tree li:only-child::after {
    border: none;
}

/* Node styling */
.org-tree .node {
    padding: 10px 15px;
    border: 2px solid #333;
    border-radius: 8px;
    background: white;
    font-size: 14px;
    white-space: nowrap;
    position: relative;
}

.org-tree .node.leadership {
    background: #fef3c7;
    border-color: #f59e0b;
    font-weight: bold;
}

.org-tree .node.team {
    background: #dbeafe;
    border-color: #3b82f6;
}

.org-tree .node.vendor {
    background: #f3e8ff;
    border-color: #8b5cf6;
    font-style: italic;
}

.org-tree .node.synthetic {
    background: #f3f4f6;
    border-color: #9ca3af;
    font-style: italic;
}

/* Flat list fallback */
.org-flat-list {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    padding: 20px;
}

.org-flat-list .node {
    padding: 8px 12px;
    border: 1px solid #ccc;
    border-radius: 4px;
    background: #f9fafb;
}

.org-flat-list .role-tag {
    font-size: 10px;
    color: #6b7280;
    display: block;
}

/* Collapsed indicator */
.collapsed-indicator {
    font-size: 12px;
    color: #6b7280;
    padding: 4px 8px;
    cursor: pointer;
}
```

---

## 10. Files to Create/Modify

### New Files:
| File | Purpose |
|------|---------|
| `tools_v2/org_chart.py` | **Single source** for tree building + rendering |
| `web/static/css/org_tree.css` | Tree layout styles |
| `web/templates/organization/_org_tree.html` | Jinja partial |

### Modified Files:
| File | Changes |
|------|---------|
| `web/templates/organization/staffing_tree.html` | Remove mermaid, use CSS tree |
| `tools_v2/presentation.py` | Import from org_chart.py |
| `tools_v2/domain_generators/organization.py` | Import from org_chart.py |
| `web/app.py` | Pass tree_data to template |

---

## 11. Audit Steps

### Phase 1: Analyze Current Implementation
- [ ] 1.1 Read `staffing_tree.html` - understand mermaid usage
- [ ] 1.2 Read mermaid generation in `presentation.py`
- [ ] 1.3 Identify all org chart codepaths
- [ ] 1.4 Document current failure modes

### Phase 2: Create Shared Module
- [ ] 2.1 Create `tools_v2/org_chart.py`
- [ ] 2.2 Implement `build_org_tree()` with:
  - Cycle detection
  - Multi-root synthetic root
  - Fuzzy matching
- [ ] 2.3 Implement `render_org_tree_html()`
- [ ] 2.4 Add depth limiting

### Phase 3: Create CSS Tree
- [ ] 3.1 Create `org_tree.css`
- [ ] 3.2 Test CSS layout with static sample tree
- [ ] 3.3 Verify responsive/scroll behavior
- [ ] 3.4 Test with special characters

### Phase 4: Integrate with Web View
- [ ] 4.1 Update `staffing_tree.html` - remove mermaid
- [ ] 4.2 Add CSS tree include
- [ ] 4.3 Update org route in `app.py`
- [ ] 4.4 Test end-to-end

### Phase 5: Consolidate All Codepaths
- [ ] 5.1 Update `presentation.py` to use shared module
- [ ] 5.2 Update `organization.py` to use shared module
- [ ] 5.3 Remove duplicate implementations
- [ ] 5.4 Verify all surfaces render same tree

### Phase 6: Test
- [ ] 6.1 Special chars test (O'Brien, R&D, etc.)
- [ ] 6.2 Multi-root test
- [ ] 6.3 Cycle test
- [ ] 6.4 50-node synthetic tree test
- [ ] 6.5 Add snapshot tests

---

## 12. Implementation Order (GPT FEEDBACK)

1. **Build CSS + HTML templates with static sample tree** (prove layout works)
2. **Implement `build_org_tree()` with:**
   - Cycle detection
   - Multi-root synthetic root
   - Normalized matching
3. **Integrate into web view first** (fastest feedback)
4. **Reuse same renderer** in presentation.py + domain_generators
5. **Add snapshot tests** for special chars, multi-root, cycle, large tree

---

## 13. Test Cases

### Special Characters:
| Input | Expected |
|-------|----------|
| `O'Brien` | Renders correctly |
| `R&D` | Renders correctly |
| `Manager (Interim)` | Renders correctly |
| `John "Jack" Smith` | Renders correctly |
| `<script>` | Escaped, not executed |

### Scaling:
| Nodes | Expected |
|-------|----------|
| 5 | Clean centered tree |
| 20 | Readable, may need scroll |
| 50 | Horizontal scroll, depth-limited |
| 100 | Scroll works, collapsed beyond depth 3 |

### Hierarchy Edge Cases:
| Scenario | Expected |
|----------|----------|
| Single root | Full tree |
| Multiple roots | Synthetic "IT Organization" parent |
| No reports_to data | Flat list fallback |
| Circular reference | Cut edge, mark node, keep rendering |
| Name variants | Fuzzy match finds parent |

---

## 14. Risk Assessment

| Risk | Mitigation |
|------|------------|
| CSS not loading | Fallback styles inline |
| Very deep trees | Depth limit (max 3-4) |
| Missing data | Graceful fallback to flat list |
| Print/PDF issues | Print stylesheet |
| Multiple codepaths diverging | Single shared module (rule) |

---

## 15. Definition of Done

### Must have:
- [ ] Names with special chars render correctly
- [ ] 50+ node trees scroll horizontally with depth limiting
- [ ] Missing hierarchy shows flat list
- [ ] Node colors differentiate types
- [ ] Works without JavaScript
- [ ] No mermaid errors in console
- [ ] PE report includes org chart
- [ ] **All codepaths use single shared module**

### Tests:
- [ ] Snapshot test: special chars
- [ ] Snapshot test: multi-root
- [ ] Snapshot test: cycle detected
- [ ] Snapshot test: 50-node tree

---

## 16. Questions Resolved

| Question | Decision |
|----------|----------|
| Collapsible nodes? | Depth limit server-side (v1), JS collapse (v2) |
| Zoom controls? | Horizontal scroll (v1), zoom later |
| Multiple org structures? | Separate sections if needed |
| Vendors in separate section? | Include in tree with `.vendor` styling |
| Visualize headcount? | Show in node if available |

---

## 17. Dependencies

- None (can be built independently)

## 18. Blocks

- Org chart visualization in all views
- Professional organization section in reports

---

## 19. GPT Review Notes (Feb 8, 2026)

**Score: 8.6/10**

**Strengths:**
- Root cause is correct (Mermaid fragile with real text)
- Solution choice is right (HTML + escaping + CSS)
- Explicitly tackles hardcoded root, fragile matching, scaling
- Complete plan with CSS, data builder, renderer, tests

**Improvements made based on feedback:**
1. Added "Data Contract" - expected org fact shape
2. **Multi-root handling** - synthetic root instead of flat fallback
3. **Cycle detection** - cut edge, mark node, keep rendering
4. **Fuzzy matching** for reports_to (normalized, partial)
5. **Large tree UI** - depth limiting, collapsed indicator
6. **One Renderer Rule** - single shared module for all codepaths
7. Added implementation order (CSS first, then data, then integrate)
8. Added snapshot tests for edge cases

---

## 20. Implementation Notes (Feb 8, 2026)

### Files Created:

**`tools_v2/org_chart.py`** - Single source for tree building + rendering:
- `OrgNode` dataclass for tree nodes
- `OrgTreeData` dataclass for tree data structure
- `build_org_tree(fact_store, entity)` - Main tree builder with:
  - Multi-root handling (synthetic "IT Organization" parent)
  - Cycle detection (cuts edge, marks node, continues)
  - Fuzzy name matching for reports_to
- `render_org_tree_html(tree_data, max_depth)` - HTML renderer with:
  - Depth limiting (default 4)
  - Flat list fallback when no hierarchy
  - Inline CSS option
  - HTML escaping for special characters
- `get_org_chart_html()` - One-liner convenience function

**`web/static/css/org_tree.css`** - Updated with new UL/LI-based CSS:
- Flexbox tree layout with connector lines
- Node type colors (leadership=orange, team=blue, vendor=purple, synthetic=gray)
- Collapsed indicator styling
- Warning/empty state styling
- Print styles

### Key Implementation Details:

1. **Special Character Safe**: Uses `html.escape()` for all text
2. **Multi-Root**: Creates synthetic "IT Organization" parent for multiple roots
3. **Cycle Detection**: Tracks visited set, marks cycle nodes with `.cycle` class
4. **Fuzzy Matching**: Normalized comparison, partial matching
5. **Depth Limiting**: Default max_depth=4, shows "+N more" indicator

### Usage:
```python
from tools_v2.org_chart import build_org_tree, render_org_tree_html

tree_data = build_org_tree(fact_store, entity='target')
html = render_org_tree_html(tree_data, max_depth=4)
```

### Remaining Work:
- [ ] Integrate into web views (replace mermaid in staffing_tree.html)
- [ ] Update domain_generators/organization.py to use new module
- [ ] Update presentation.py to use new module
- [ ] Remove old mermaid JavaScript
