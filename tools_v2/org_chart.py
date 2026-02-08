"""
Org Chart Builder and Renderer (C3 Fix)

Single source of truth for org chart tree building and HTML rendering.
Replaces fragile Mermaid-based org charts with pure CSS tree layout.

Key features:
- Special character safe (HTML escaping)
- Multi-root handling (synthetic parent)
- Cycle detection (cut edge, mark, continue)
- Fuzzy matching for reports_to
- Depth limiting for large trees
- Graceful flat list fallback

Usage:
    from tools_v2.org_chart import build_org_tree, render_org_tree_html

    tree_data = build_org_tree(fact_store, entity='target')
    html = render_org_tree_html(tree_data)
"""

import html
import logging
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Set

logger = logging.getLogger(__name__)


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class OrgNode:
    """Standard org chart node."""
    name: str
    role: str = ''
    reports_to: str = ''
    node_type: str = 'staff'  # leadership, team, staff, vendor, synthetic
    team: str = ''
    headcount: int = 0
    children: List['OrgNode'] = field(default_factory=list)
    cycle_detected: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'role': self.role,
            'reports_to': self.reports_to,
            'node_type': self.node_type,
            'team': self.team,
            'headcount': self.headcount,
            'children': [c.to_dict() for c in self.children],
            'cycle_detected': self.cycle_detected,
        }


@dataclass
class OrgTreeData:
    """Org chart tree data structure."""
    root: Optional[OrgNode] = None
    has_hierarchy: bool = False
    flat_list: List[OrgNode] = field(default_factory=list)
    total_nodes: int = 0
    warning: str = ''

    def to_dict(self) -> Dict[str, Any]:
        return {
            'root': self.root.to_dict() if self.root else None,
            'has_hierarchy': self.has_hierarchy,
            'flat_list': [n.to_dict() for n in self.flat_list],
            'total_nodes': self.total_nodes,
            'warning': self.warning,
        }


# =============================================================================
# TREE BUILDING
# =============================================================================

def build_org_tree(fact_store, entity: str = 'target') -> OrgTreeData:
    """
    Build org chart tree from fact store.

    Args:
        fact_store: FactStore with organization facts
        entity: Entity filter ('target' or 'buyer')

    Returns:
        OrgTreeData with tree or flat list fallback
    """
    # Extract org nodes from facts
    nodes = _extract_org_nodes(fact_store, entity)

    if not nodes:
        logger.info("C3: No org nodes found, returning empty tree")
        return OrgTreeData(warning="No organization data available")

    total = len(nodes)
    logger.info(f"C3: Building org tree from {total} nodes")

    # Try to build hierarchy
    root = _build_tree_from_reports_to(nodes)

    if root:
        return OrgTreeData(
            root=root,
            has_hierarchy=True,
            flat_list=[],
            total_nodes=total,
        )
    else:
        # Fallback to flat list
        logger.info("C3: No hierarchy detected, using flat list")
        return OrgTreeData(
            root=None,
            has_hierarchy=False,
            flat_list=nodes,
            total_nodes=total,
            warning="Hierarchy data not available - showing flat list"
        )


def _extract_org_nodes(fact_store, entity: str) -> List[OrgNode]:
    """Extract org nodes from fact store."""
    nodes = []

    # Get organization domain facts
    org_facts = [f for f in fact_store.facts
                 if f.domain == 'organization'
                 and getattr(f, 'entity', 'target') == entity]

    for fact in org_facts:
        details = fact.details or {}
        category = (getattr(fact, 'category', '') or '').lower()

        # Determine node type
        if 'leadership' in category or 'executive' in category:
            node_type = 'leadership'
        elif 'team' in category or 'department' in category:
            node_type = 'team'
        elif 'vendor' in category or 'contractor' in category:
            node_type = 'vendor'
        else:
            node_type = 'staff'

        # Get name and role
        name = details.get('name') or details.get('title') or fact.item or ''
        role = details.get('role') or details.get('title') or ''
        reports_to = details.get('reports_to', '') or ''

        if name:
            nodes.append(OrgNode(
                name=str(name).strip(),
                role=str(role).strip(),
                reports_to=str(reports_to).strip(),
                node_type=node_type,
                team=str(details.get('team', '')).strip(),
                headcount=int(details.get('headcount', 0) or 0),
            ))

    return nodes


def _build_tree_from_reports_to(nodes: List[OrgNode]) -> Optional[OrgNode]:
    """
    Build tree from reports_to relationships.

    Handles:
    - Multiple roots (creates synthetic parent)
    - Cycles (cuts edge, marks node)
    - Fuzzy matching for reports_to
    """
    if not nodes:
        return None

    # Build lookup by name
    by_name: Dict[str, OrgNode] = {}
    for node in nodes:
        by_name[node.name] = node
        # Also add normalized version for fuzzy matching
        by_name[_normalize_name(node.name)] = node

    # Find roots (no reports_to or reports_to not found)
    roots: List[OrgNode] = []
    for node in nodes:
        if not node.reports_to:
            roots.append(node)
        else:
            # Check if parent exists
            parent = _find_parent(node.reports_to, by_name, nodes)
            if not parent:
                roots.append(node)

    if not roots:
        # No roots found - might be all circular, fallback
        logger.warning("C3: No root nodes found (possible cycle?)")
        return None

    # Handle multiple roots with synthetic parent
    if len(roots) == 1:
        root = roots[0]
    else:
        # Create synthetic root (GPT FEEDBACK)
        logger.info(f"C3: Multiple roots ({len(roots)}), creating synthetic parent")
        root = OrgNode(
            name='IT Organization',
            role='',
            node_type='synthetic',
            reports_to='',
        )
        for r in roots:
            r.reports_to = 'IT Organization'
        root.children = roots

    # Build children recursively with cycle detection
    _build_children_recursive(root, nodes, by_name, visited=set())

    return root


def _build_children_recursive(
    parent: OrgNode,
    all_nodes: List[OrgNode],
    by_name: Dict[str, OrgNode],
    visited: Set[str]
) -> None:
    """Build children with cycle detection."""
    parent_name = parent.name

    # Cycle detection (GPT FEEDBACK)
    if parent_name in visited:
        logger.warning(f"C3: Cycle detected at: {parent_name}")
        parent.cycle_detected = True
        return

    visited.add(parent_name)

    # Find children (nodes that report to this parent)
    # Skip if parent already has children (synthetic root case)
    if not parent.children:
        children = []
        for node in all_nodes:
            if node.name != parent_name and node.reports_to:
                # Check if this node reports to parent
                if _matches_name(node.reports_to, parent_name):
                    children.append(node)
        parent.children = children

    # Recurse for children
    for child in parent.children:
        _build_children_recursive(child, all_nodes, by_name, visited.copy())


def _normalize_name(name: str) -> str:
    """Normalize name for matching."""
    return name.lower().strip().replace('.', '').replace(',', '').replace("'", '')


def _matches_name(reports_to: str, target_name: str) -> bool:
    """Check if reports_to matches target_name (fuzzy)."""
    if not reports_to or not target_name:
        return False

    # Exact match
    if reports_to == target_name:
        return True

    # Normalized match
    if _normalize_name(reports_to) == _normalize_name(target_name):
        return True

    # Partial match (for "John Smith" matching "John A. Smith")
    norm_reports = _normalize_name(reports_to)
    norm_target = _normalize_name(target_name)
    if norm_reports in norm_target or norm_target in norm_reports:
        return True

    return False


def _find_parent(
    reports_to: str,
    by_name: Dict[str, OrgNode],
    all_nodes: List[OrgNode]
) -> Optional[OrgNode]:
    """Find parent with fuzzy matching."""
    if not reports_to:
        return None

    # Exact match first
    if reports_to in by_name:
        return by_name[reports_to]

    # Normalized match
    normalized = _normalize_name(reports_to)
    if normalized in by_name:
        return by_name[normalized]

    # Partial match as last resort
    for node in all_nodes:
        if _matches_name(reports_to, node.name):
            return node

    return None


# =============================================================================
# HTML RENDERING
# =============================================================================

def render_org_tree_html(
    tree_data: OrgTreeData,
    max_depth: int = 4,
    include_css: bool = True
) -> str:
    """
    Render org tree as HTML.

    Args:
        tree_data: OrgTreeData from build_org_tree()
        max_depth: Maximum depth to render (for large trees)
        include_css: Include inline CSS (True for standalone)

    Returns:
        HTML string
    """
    parts = []

    if include_css:
        parts.append(_get_inline_css())

    if tree_data.warning:
        parts.append(f'<div class="org-warning">{_escape(tree_data.warning)}</div>')

    if tree_data.has_hierarchy and tree_data.root:
        parts.append('<div class="org-tree">')
        parts.append('<ul>')
        parts.append(_render_tree_node(tree_data.root, depth=0, max_depth=max_depth))
        parts.append('</ul>')
        parts.append('</div>')
    elif tree_data.flat_list:
        parts.append(_render_flat_list(tree_data.flat_list))
    else:
        parts.append('<div class="org-empty">No organization data available</div>')

    return '\n'.join(parts)


def _render_tree_node(node: OrgNode, depth: int, max_depth: int) -> str:
    """Render a single tree node recursively."""
    parts = []

    # Node content
    node_class = f"node {node.node_type}"
    if node.cycle_detected:
        node_class += " cycle"

    name = _escape(node.name)
    role = _escape(node.role) if node.role else ''
    headcount = f"({node.headcount})" if node.headcount > 0 else ''

    parts.append('<li>')
    parts.append(f'<div class="{node_class}">')
    parts.append(f'<span class="node-name">{name}</span>')
    if role:
        parts.append(f'<span class="node-role">{role}</span>')
    if headcount:
        parts.append(f'<span class="node-headcount">{headcount}</span>')
    if node.cycle_detected:
        parts.append('<span class="cycle-marker" title="Circular reference detected">!</span>')
    parts.append('</div>')

    # Children
    children = node.children or []
    if children:
        if depth >= max_depth:
            # Collapse deep levels
            parts.append(f'<div class="collapsed-indicator">+{len(children)} more</div>')
        else:
            parts.append('<ul>')
            for child in children:
                parts.append(_render_tree_node(child, depth + 1, max_depth))
            parts.append('</ul>')

    parts.append('</li>')

    return '\n'.join(parts)


def _render_flat_list(nodes: List[OrgNode]) -> str:
    """Render nodes as flat list (fallback)."""
    parts = ['<div class="org-flat-list">']

    # Group by type
    by_type: Dict[str, List[OrgNode]] = {}
    for node in nodes:
        if node.node_type not in by_type:
            by_type[node.node_type] = []
        by_type[node.node_type].append(node)

    # Render by type
    type_order = ['leadership', 'team', 'staff', 'vendor']
    type_labels = {
        'leadership': 'Leadership',
        'team': 'Teams',
        'staff': 'Staff',
        'vendor': 'Vendors/Contractors'
    }

    for node_type in type_order:
        type_nodes = by_type.get(node_type, [])
        if not type_nodes:
            continue

        parts.append(f'<div class="flat-section">')
        parts.append(f'<h4>{type_labels.get(node_type, node_type.title())}</h4>')
        parts.append('<div class="flat-nodes">')

        for node in type_nodes:
            name = _escape(node.name)
            role = _escape(node.role) if node.role else ''
            headcount = f"({node.headcount})" if node.headcount > 0 else ''

            parts.append(f'<div class="node {node.node_type}">')
            parts.append(f'<span class="node-name">{name}</span>')
            if role:
                parts.append(f'<span class="role-tag">{role}</span>')
            if headcount:
                parts.append(f'<span class="headcount-tag">{headcount}</span>')
            parts.append('</div>')

        parts.append('</div>')
        parts.append('</div>')

    parts.append('</div>')
    return '\n'.join(parts)


def _escape(text: str) -> str:
    """HTML-escape special characters."""
    return html.escape(str(text)) if text else ''


def _get_inline_css() -> str:
    """Return inline CSS for org tree."""
    return '''<style>
.org-tree {
    overflow-x: auto;
    padding: 20px;
    background: #f9fafb;
    border-radius: 8px;
}

.org-tree ul {
    display: flex;
    justify-content: center;
    padding-top: 20px;
    position: relative;
    list-style: none;
    margin: 0;
    padding-left: 0;
}

.org-tree ul::before {
    content: '';
    position: absolute;
    top: 0;
    left: 50%;
    width: 0;
    height: 20px;
    border-left: 2px solid #d1d5db;
}

.org-tree > ul::before {
    display: none;
}

.org-tree li {
    display: flex;
    flex-direction: column;
    align-items: center;
    position: relative;
    padding: 20px 10px 0;
}

.org-tree li::before,
.org-tree li::after {
    content: '';
    position: absolute;
    top: 0;
    width: 50%;
    height: 20px;
    border-top: 2px solid #d1d5db;
}

.org-tree li::before { right: 50%; border-right: 2px solid #d1d5db; }
.org-tree li::after { left: 50%; }

.org-tree li:first-child::before { border: none; border-right: 2px solid #d1d5db; }
.org-tree li:last-child::after { border: none; }
.org-tree li:first-child::after { border-radius: 5px 0 0 0; }
.org-tree li:last-child::before { border-radius: 0 5px 0 0; }

.org-tree li:only-child::before,
.org-tree li:only-child::after { border: none; }

.org-tree .node {
    padding: 10px 15px;
    border: 2px solid #374151;
    border-radius: 8px;
    background: white;
    font-size: 14px;
    white-space: nowrap;
    text-align: center;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.org-tree .node-name { display: block; font-weight: 600; }
.org-tree .node-role { display: block; font-size: 12px; color: #6b7280; }
.org-tree .node-headcount { display: block; font-size: 11px; color: #9ca3af; }

.org-tree .node.leadership {
    background: #fef3c7;
    border-color: #f59e0b;
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

.org-tree .node.cycle {
    border-color: #ef4444;
    border-style: dashed;
}

.org-tree .cycle-marker {
    color: #ef4444;
    font-weight: bold;
    margin-left: 4px;
}

.collapsed-indicator {
    font-size: 12px;
    color: #6b7280;
    padding: 4px 8px;
    background: #f3f4f6;
    border-radius: 4px;
    margin-top: 8px;
}

.org-flat-list {
    padding: 20px;
    background: #f9fafb;
    border-radius: 8px;
}

.org-flat-list h4 {
    color: #374151;
    margin: 16px 0 8px 0;
    font-size: 14px;
    border-bottom: 1px solid #e5e7eb;
    padding-bottom: 4px;
}

.org-flat-list h4:first-child { margin-top: 0; }

.org-flat-list .flat-nodes {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
}

.org-flat-list .node {
    padding: 8px 12px;
    border: 1px solid #d1d5db;
    border-radius: 4px;
    background: white;
    font-size: 13px;
}

.org-flat-list .node.leadership { border-left: 3px solid #f59e0b; }
.org-flat-list .node.team { border-left: 3px solid #3b82f6; }
.org-flat-list .node.vendor { border-left: 3px solid #8b5cf6; }

.org-flat-list .role-tag,
.org-flat-list .headcount-tag {
    font-size: 10px;
    color: #6b7280;
    display: block;
}

.org-warning {
    padding: 10px 15px;
    background: #fef3c7;
    border-left: 3px solid #f59e0b;
    color: #92400e;
    font-size: 13px;
    margin-bottom: 15px;
    border-radius: 4px;
}

.org-empty {
    padding: 40px;
    text-align: center;
    color: #6b7280;
    font-style: italic;
}
</style>'''


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def get_org_chart_html(fact_store, entity: str = 'target', max_depth: int = 4) -> str:
    """
    One-liner to get org chart HTML.

    Args:
        fact_store: FactStore with organization facts
        entity: Entity filter
        max_depth: Maximum tree depth

    Returns:
        Complete HTML string with CSS
    """
    tree_data = build_org_tree(fact_store, entity)
    return render_org_tree_html(tree_data, max_depth=max_depth, include_css=True)


def get_org_tree_data(fact_store, entity: str = 'target') -> Dict[str, Any]:
    """
    Get org tree data as dict (for JSON API).

    Args:
        fact_store: FactStore with organization facts
        entity: Entity filter

    Returns:
        Dict representation of tree data
    """
    tree_data = build_org_tree(fact_store, entity)
    return tree_data.to_dict()
