# Spec 04: Hierarchical Breakdown Architecture
**Version:** 1.0
**Date:** February 10, 2026
**Status:** Ready for Implementation
**Dependencies:** Spec 01 (Resource Buildup), Spec 02 (Calculation Engine), Spec 03 (Resource-Cost Integration)

---

## Executive Summary

This specification implements **hierarchical drill-down** for both ResourceBuildUp and CostBuildUp, enabling users to:

1. **View top-level summaries** - Total cost, effort, timeline at workstream level
2. **Drill down to sub-activities** - See task-level breakdown (e.g., "Identity Migration" → "Account Mapping", "MFA Setup", etc.)
3. **Navigate parent-child relationships** - Tree view with expand/collapse
4. **Aggregate from bottom-up** - Child costs/efforts sum to parent totals
5. **Maintain transparency** - All calculations visible at every level

### User Feedback Context

**Original Feedback:**
- "Cost tracking visibility... potentially the sub activities we have in the one time cost inventory that add up"
- User wants to see HOW top-level estimates break down into component tasks
- Need drill-down capability to understand where costs/effort come from

**Current State:**
- ✅ Flat structure exists (workstream-level only)
- ❌ No sub-activity breakdown
- ❌ No hierarchical navigation
- ❌ Cannot see task-level detail

**Target State:**
```
Total Separation Cost: $2.1M - $2.8M
├─ Applications: $650k - $900k
│  ├─ ERP Migration: $200k - $300k
│  │  ├─ Discovery & Planning: $40k - $50k
│  │  ├─ Data Mapping: $60k - $90k
│  │  ├─ Development & Config: $80k - $120k
│  │  └─ Testing & Validation: $20k - $40k
│  ├─ CRM Reconfiguration: $150k - $200k
│  └─ ... (other apps)
└─ ... (other workstreams)
```

---

## Architecture Overview

### Hierarchical Model Design

Both `ResourceBuildUp` and `CostBuildUp` support **multi-level hierarchies**:

```
Level 0: Finding-level aggregate (all workstreams)
Level 1: Workstream-level (application_migration, identity_management, etc.)
Level 2: Sub-workstream (ERP migration, CRM reconfiguration, etc.)
Level 3: Task-level (discovery, data mapping, development, testing, etc.)
Level 4+: Subtasks (optional, for very complex workstreams)
```

### Parent-Child Relationships

```
┌─────────────────────────────────────────────────────────┐
│                  ResourceBuildUp/CostBuildUp             │
├─────────────────────────────────────────────────────────┤
│  id: "RB-APP-001"                                        │
│  parent_id: None                     (ROOT NODE)         │
│  children_ids: ["RB-APP-ERP", "RB-APP-CRM"]             │
│  level: 1                                                │
│  path: "application_migration"                           │
│  display_name: "Application Migration"                   │
│                                                          │
│  ┌─────────────────────────────────────────────────┐   │
│  │  Child: RB-APP-ERP                               │   │
│  │  parent_id: "RB-APP-001"                        │   │
│  │  children_ids: ["RB-APP-ERP-DISC", ...]        │   │
│  │  level: 2                                        │   │
│  │  path: "application_migration.erp_migration"    │   │
│  │  display_name: "ERP Migration"                  │   │
│  │                                                  │   │
│  │  ┌──────────────────────────────────────────┐  │   │
│  │  │  Child: RB-APP-ERP-DISC                  │  │   │
│  │  │  parent_id: "RB-APP-ERP"                 │  │   │
│  │  │  children_ids: []          (LEAF NODE)   │  │   │
│  │  │  level: 3                                │  │   │
│  │  │  path: "...erp_migration.discovery"     │  │   │
│  │  │  display_name: "Discovery & Planning"   │  │   │
│  │  └──────────────────────────────────────────┘  │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

### Aggregation Rules

**Bottom-Up Aggregation:**

1. **Leaf nodes** (tasks with no children):
   - Have explicit effort/cost values
   - Calculated from inventory data or benchmarks

2. **Parent nodes** (sub-workstreams, workstreams):
   - Effort/cost = SUM of all children
   - Automatically recalculated when children change
   - Display rollup values

3. **Root node** (finding-level):
   - Total across all workstreams
   - Highest-level summary

**Example:**
```
ERP Migration (Parent):
  total_effort_pm = CALCULATED PROPERTY = sum(child.total_effort_pm for child in children)

  Children:
    - Discovery: 2 PM (explicit)
    - Data Mapping: 5 PM (explicit)
    - Development: 12 PM (explicit)
    - Testing: 3 PM (explicit)

  Parent total: 2 + 5 + 12 + 3 = 22 PM
```

---

## Enhanced Data Models

### ResourceBuildUp with Hierarchy

```python
from dataclasses import dataclass, field
from typing import Optional, List, Dict
import uuid
import logging

logger = logging.getLogger(__name__)

@dataclass
class ResourceBuildUp:
    """
    ENHANCED with hierarchical support.

    New fields for parent-child relationships and aggregation.
    """

    # ============= EXISTING FIELDS (from Spec 01 FIXED) =============
    id: str = field(default_factory=lambda: f"RB-{uuid.uuid4().hex[:12]}")
    workstream: str = ""
    workstream_display: str = ""

    duration_months_low: float = 0.0
    duration_months_high: float = 0.0
    duration_confidence: str = "medium"

    roles: List['RoleRequirement'] = field(default_factory=list)

    skills_required: List[str] = field(default_factory=list)
    sourcing_mix: Dict[str, float] = field(default_factory=dict)

    assumptions: List[str] = field(default_factory=list)
    source_facts: List[str] = field(default_factory=list)
    confidence: float = 0.7

    created_at: str = ""
    updated_at: str = ""
    version: int = 1

    # ============= NEW FIELDS (hierarchical support) =============

    parent_id: Optional[str] = None
    """ID of parent ResourceBuildUp. None for root nodes."""

    children_ids: List[str] = field(default_factory=list)
    """IDs of child ResourceBuildUp nodes."""

    level: int = 1
    """
    Hierarchy level:
    - 1: Workstream (root)
    - 2: Sub-workstream
    - 3: Task
    - 4+: Subtask
    """

    path: str = ""
    """
    Hierarchical path for navigation.
    Example: "application_migration.erp_migration.discovery"
    """

    display_order: int = 0
    """Display order among siblings (for consistent sorting)."""

    is_aggregate: bool = False
    """
    True if this is a parent node (effort/cost calculated from children).
    False if this is a leaf node (explicit values).
    """

    # Aggregation metadata
    aggregated_effort_pm: Optional[float] = None
    """If is_aggregate=True, this is sum of children efforts. Otherwise None."""

    aggregated_peak_headcount: Optional[int] = None
    """If is_aggregate=True, this is max of children peak headcounts."""

    def __post_init__(self):
        """Validate on creation."""
        # Generate ID if not provided
        if not self.id or self.id.startswith("RB-"):
            pass  # Already valid
        else:
            self.id = f"RB-{uuid.uuid4().hex[:12]}"

        # Generate path if not provided
        if not self.path:
            self.path = self.workstream

        # Normalize skills
        from specs.analysis_depth_enhancement.resource_buildup_model import normalize_skills
        self.skills_required = normalize_skills(self.skills_required)

        # Validate
        is_valid, errors = validate_resource_buildup(self)
        if not is_valid:
            raise ValueError(f"Invalid ResourceBuildUp: {'; '.join(errors)}")

    @property
    def total_effort_pm(self) -> float:
        """
        COMPUTED PROPERTY - always in sync with roles or children.

        If is_aggregate:
            Returns aggregated_effort_pm (sum of children)
        Else:
            Returns sum of role efforts
        """
        if self.is_aggregate:
            return self.aggregated_effort_pm or 0.0
        else:
            return sum(role.effort_pm for role in self.roles)

    @property
    def peak_headcount(self) -> int:
        """
        COMPUTED PROPERTY - peak concurrent FTEs.

        If is_aggregate:
            Returns aggregated_peak_headcount (max of children)
        Else:
            Calculates from roles
        """
        if self.is_aggregate:
            return self.aggregated_peak_headcount or 0

        # Calculate from roles (same logic as Spec 01 FIXED)
        if any(role.phase_allocation for role in self.roles):
            phases = {}
            for role in self.roles:
                if role.phase_allocation:
                    for phase, fraction in role.phase_allocation.items():
                        phases[phase] = phases.get(phase, 0) + (role.fte * fraction)
            return int(max(phases.values())) if phases else 0
        else:
            return sum(int(role.fte) + (1 if role.fte % 1 >= 0.5 else 0) for role in self.roles)

    def is_root(self) -> bool:
        """Is this a root node (no parent)?"""
        return self.parent_id is None

    def is_leaf(self) -> bool:
        """Is this a leaf node (no children)?"""
        return len(self.children_ids) == 0

    def get_depth(self) -> int:
        """
        Get depth of this node in tree.
        Root = 1, children = 2, etc.
        """
        return self.level

    def to_dict(self) -> Dict:
        """Serialize to JSON-compatible dict."""
        return {
            "id": self.id,
            "workstream": self.workstream,
            "workstream_display": self.workstream_display,
            "duration_months_low": self.duration_months_low,
            "duration_months_high": self.duration_months_high,
            "duration_confidence": self.duration_confidence,
            "roles": [r.to_dict() for r in self.roles],
            "total_effort_pm": self.total_effort_pm,  # COMPUTED
            "peak_headcount": self.peak_headcount,    # COMPUTED
            "skills_required": self.skills_required,
            "sourcing_mix": self.sourcing_mix,
            "assumptions": self.assumptions,
            "source_facts": self.source_facts,
            "confidence": self.confidence,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "version": self.version,
            # Hierarchical fields
            "parent_id": self.parent_id,
            "children_ids": self.children_ids,
            "level": self.level,
            "path": self.path,
            "display_order": self.display_order,
            "is_aggregate": self.is_aggregate,
            "aggregated_effort_pm": self.aggregated_effort_pm,
            "aggregated_peak_headcount": self.aggregated_peak_headcount,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> Optional['ResourceBuildUp']:
        """Deserialize with error handling."""
        try:
            if not isinstance(data, dict):
                logger.error(f"ResourceBuildUp data is not a dict: {type(data)}")
                return None

            # Deserialize roles
            roles = []
            for role_data in data.get('roles', []):
                from specs.analysis_depth_enhancement.resource_buildup_model import RoleRequirement
                role = RoleRequirement.from_dict(role_data)
                if role:
                    roles.append(role)

            return cls(
                id=data.get('id', ''),
                workstream=data.get('workstream', ''),
                workstream_display=data.get('workstream_display', ''),
                duration_months_low=float(data.get('duration_months_low', 0)),
                duration_months_high=float(data.get('duration_months_high', 0)),
                duration_confidence=data.get('duration_confidence', 'medium'),
                roles=roles,
                skills_required=data.get('skills_required', []),
                sourcing_mix=data.get('sourcing_mix', {}),
                assumptions=data.get('assumptions', []),
                source_facts=data.get('source_facts', []),
                confidence=float(data.get('confidence', 0.7)),
                created_at=data.get('created_at', ''),
                updated_at=data.get('updated_at', ''),
                version=int(data.get('version', 1)),
                # Hierarchical fields
                parent_id=data.get('parent_id'),
                children_ids=data.get('children_ids', []),
                level=int(data.get('level', 1)),
                path=data.get('path', ''),
                display_order=int(data.get('display_order', 0)),
                is_aggregate=data.get('is_aggregate', False),
                aggregated_effort_pm=data.get('aggregated_effort_pm'),
                aggregated_peak_headcount=data.get('aggregated_peak_headcount'),
            )
        except Exception as e:
            logger.error(f"Error deserializing ResourceBuildUp: {e}", exc_info=True)
            return None
```

### CostBuildUp with Hierarchy

```python
@dataclass
class CostBuildUp:
    """
    ENHANCED with hierarchical support.

    Parent-child relationships identical to ResourceBuildUp structure.
    """

    # ============= EXISTING FIELDS (from Spec 03) =============
    id: str = field(default_factory=lambda: f"CB-{uuid.uuid4().hex[:12]}")
    workstream: str = ""
    workstream_display: str = ""

    cost_low: float = 0.0
    cost_high: float = 0.0
    currency: str = "USD"

    cost_components: List['CostComponent'] = field(default_factory=list)

    estimation_method: str = "benchmark"
    assumptions: List[str] = field(default_factory=list)
    source_facts: List[str] = field(default_factory=list)
    confidence: float = 0.7

    created_at: str = ""
    updated_at: str = ""
    version: int = 1

    # Resource integration (from Spec 03)
    derived_from_resource_buildup: bool = False
    resource_buildup_id: Optional[str] = None
    labor_cost_low: Optional[float] = None
    labor_cost_high: Optional[float] = None
    non_labor_cost_low: Optional[float] = None
    non_labor_cost_high: Optional[float] = None
    blended_rate_low: Optional[float] = None
    blended_rate_high: Optional[float] = None
    consistency_status: str = "not_validated"
    consistency_notes: List[str] = field(default_factory=list)

    # ============= NEW FIELDS (hierarchical support) =============

    parent_id: Optional[str] = None
    """ID of parent CostBuildUp. None for root nodes."""

    children_ids: List[str] = field(default_factory=list)
    """IDs of child CostBuildUp nodes."""

    level: int = 1
    """Hierarchy level (1=workstream, 2=sub-workstream, 3=task, etc.)"""

    path: str = ""
    """Hierarchical path. Example: "application_migration.erp_migration.discovery" """

    display_order: int = 0
    """Display order among siblings."""

    is_aggregate: bool = False
    """
    True if cost calculated from children.
    False if explicit cost (leaf node).
    """

    # Aggregation metadata
    aggregated_cost_low: Optional[float] = None
    """If is_aggregate=True, sum of children costs (low). Otherwise None."""

    aggregated_cost_high: Optional[float] = None
    """If is_aggregate=True, sum of children costs (high). Otherwise None."""

    def __post_init__(self):
        """Validate on creation."""
        if not self.id or self.id.startswith("CB-"):
            pass
        else:
            self.id = f"CB-{uuid.uuid4().hex[:12]}"

        if not self.path:
            self.path = self.workstream

        # Validate cost ranges
        if self.cost_low > self.cost_high:
            raise ValueError(f"cost_low ({self.cost_low}) > cost_high ({self.cost_high})")

        # If aggregate, ensure aggregated values are set
        if self.is_aggregate and self.aggregated_cost_low is None:
            logger.warning(f"Aggregate CostBuildUp {self.id} has no aggregated_cost_low")

    @property
    def total_cost_low(self) -> float:
        """
        COMPUTED PROPERTY.

        If is_aggregate: Returns aggregated_cost_low (sum of children)
        Else: Returns cost_low (explicit value)
        """
        if self.is_aggregate:
            return self.aggregated_cost_low or 0.0
        else:
            return self.cost_low

    @property
    def total_cost_high(self) -> float:
        """COMPUTED PROPERTY."""
        if self.is_aggregate:
            return self.aggregated_cost_high or 0.0
        else:
            return self.cost_high

    def is_root(self) -> bool:
        return self.parent_id is None

    def is_leaf(self) -> bool:
        return len(self.children_ids) == 0

    def to_dict(self) -> Dict:
        """Serialize to JSON-compatible dict."""
        return {
            "id": self.id,
            "workstream": self.workstream,
            "workstream_display": self.workstream_display,
            "cost_low": self.cost_low,
            "cost_high": self.cost_high,
            "total_cost_low": self.total_cost_low,  # COMPUTED
            "total_cost_high": self.total_cost_high,  # COMPUTED
            "currency": self.currency,
            "cost_components": [c.to_dict() for c in self.cost_components],
            "estimation_method": self.estimation_method,
            "assumptions": self.assumptions,
            "source_facts": self.source_facts,
            "confidence": self.confidence,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "version": self.version,
            # Resource integration
            "derived_from_resource_buildup": self.derived_from_resource_buildup,
            "resource_buildup_id": self.resource_buildup_id,
            "labor_cost_low": self.labor_cost_low,
            "labor_cost_high": self.labor_cost_high,
            "non_labor_cost_low": self.non_labor_cost_low,
            "non_labor_cost_high": self.non_labor_cost_high,
            "blended_rate_low": self.blended_rate_low,
            "blended_rate_high": self.blended_rate_high,
            "consistency_status": self.consistency_status,
            "consistency_notes": self.consistency_notes,
            # Hierarchical
            "parent_id": self.parent_id,
            "children_ids": self.children_ids,
            "level": self.level,
            "path": self.path,
            "display_order": self.display_order,
            "is_aggregate": self.is_aggregate,
            "aggregated_cost_low": self.aggregated_cost_low,
            "aggregated_cost_high": self.aggregated_cost_high,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> Optional['CostBuildUp']:
        """Deserialize with error handling."""
        try:
            if not isinstance(data, dict):
                logger.error(f"CostBuildUp data is not a dict: {type(data)}")
                return None

            # Deserialize cost components
            components = []
            for comp_data in data.get('cost_components', []):
                from specs.analysis_depth_enhancement.resource_cost_integration import CostComponent
                comp = CostComponent.from_dict(comp_data)
                if comp:
                    components.append(comp)

            return cls(
                id=data.get('id', ''),
                workstream=data.get('workstream', ''),
                workstream_display=data.get('workstream_display', ''),
                cost_low=float(data.get('cost_low', 0)),
                cost_high=float(data.get('cost_high', 0)),
                currency=data.get('currency', 'USD'),
                cost_components=components,
                estimation_method=data.get('estimation_method', 'benchmark'),
                assumptions=data.get('assumptions', []),
                source_facts=data.get('source_facts', []),
                confidence=float(data.get('confidence', 0.7)),
                created_at=data.get('created_at', ''),
                updated_at=data.get('updated_at', ''),
                version=int(data.get('version', 1)),
                # Resource integration
                derived_from_resource_buildup=data.get('derived_from_resource_buildup', False),
                resource_buildup_id=data.get('resource_buildup_id'),
                labor_cost_low=data.get('labor_cost_low'),
                labor_cost_high=data.get('labor_cost_high'),
                non_labor_cost_low=data.get('non_labor_cost_low'),
                non_labor_cost_high=data.get('non_labor_cost_high'),
                blended_rate_low=data.get('blended_rate_low'),
                blended_rate_high=data.get('blended_rate_high'),
                consistency_status=data.get('consistency_status', 'not_validated'),
                consistency_notes=data.get('consistency_notes', []),
                # Hierarchical
                parent_id=data.get('parent_id'),
                children_ids=data.get('children_ids', []),
                level=int(data.get('level', 1)),
                path=data.get('path', ''),
                display_order=int(data.get('display_order', 0)),
                is_aggregate=data.get('is_aggregate', False),
                aggregated_cost_low=data.get('aggregated_cost_low'),
                aggregated_cost_high=data.get('aggregated_cost_high'),
            )
        except Exception as e:
            logger.error(f"Error deserializing CostBuildUp: {e}", exc_info=True)
            return None
```

---

## Hierarchy Builder

### Purpose

Build hierarchical structures from flat lists of ResourceBuildUp/CostBuildUp.

### HierarchyBuilder Class

```python
from typing import List, Dict, Optional
from dataclasses import dataclass

@dataclass
class HierarchyNode:
    """
    Tree node representation for UI display.

    Contains ResourceBuildUp/CostBuildUp data plus children.
    """
    data: any  # ResourceBuildUp or CostBuildUp
    children: List['HierarchyNode'] = field(default_factory=list)

    @property
    def id(self) -> str:
        return self.data.id

    @property
    def parent_id(self) -> Optional[str]:
        return self.data.parent_id

    @property
    def level(self) -> int:
        return self.data.level

    @property
    def display_name(self) -> str:
        return self.data.workstream_display

    def to_dict(self) -> Dict:
        """Serialize to JSON for API responses."""
        return {
            "data": self.data.to_dict(),
            "children": [child.to_dict() for child in self.children]
        }

class HierarchyBuilder:
    """
    Builds tree structure from flat list of ResourceBuildUp or CostBuildUp.

    Usage:
        builder = HierarchyBuilder(buildups)
        root_nodes = builder.build_tree()
    """

    def __init__(self, buildups: List[any]):
        """
        Initialize builder.

        Args:
            buildups: List of ResourceBuildUp or CostBuildUp instances
        """
        self.buildups = buildups
        self.node_map = {}  # id -> HierarchyNode

    def build_tree(self) -> List[HierarchyNode]:
        """
        Build tree from flat list.

        Returns:
            List of root nodes (nodes with parent_id=None)
        """
        # Step 1: Create nodes
        for buildup in self.buildups:
            node = HierarchyNode(data=buildup)
            self.node_map[buildup.id] = node

        # Step 2: Link children to parents
        root_nodes = []
        for buildup in self.buildups:
            node = self.node_map[buildup.id]

            if buildup.parent_id is None:
                # Root node
                root_nodes.append(node)
            else:
                # Child node - attach to parent
                parent = self.node_map.get(buildup.parent_id)
                if parent:
                    parent.children.append(node)
                else:
                    logger.warning(
                        f"Parent {buildup.parent_id} not found for {buildup.id}. "
                        f"Treating as root."
                    )
                    root_nodes.append(node)

        # Step 3: Sort children by display_order
        self._sort_children_recursive(root_nodes)

        return root_nodes

    def _sort_children_recursive(self, nodes: List[HierarchyNode]):
        """Sort children by display_order, recursively."""
        for node in nodes:
            if node.children:
                node.children.sort(key=lambda n: n.data.display_order)
                self._sort_children_recursive(node.children)

    def get_node_by_id(self, node_id: str) -> Optional[HierarchyNode]:
        """Get node by ID."""
        return self.node_map.get(node_id)

    def get_path_to_root(self, node_id: str) -> List[HierarchyNode]:
        """
        Get path from node to root.

        Returns:
            List of nodes [root, ..., target_node]
        """
        path = []
        current = self.node_map.get(node_id)

        while current:
            path.insert(0, current)
            if current.parent_id:
                current = self.node_map.get(current.parent_id)
            else:
                break

        return path

    def get_all_descendants(self, node_id: str) -> List[HierarchyNode]:
        """
        Get all descendants of a node (recursive).

        Returns:
            List of all child/grandchild/... nodes
        """
        node = self.node_map.get(node_id)
        if not node:
            return []

        descendants = []
        self._collect_descendants(node, descendants)
        return descendants

    def _collect_descendants(self, node: HierarchyNode, accumulator: List):
        """Recursively collect all descendants."""
        for child in node.children:
            accumulator.append(child)
            self._collect_descendants(child, accumulator)
```

---

## Aggregator

### Purpose

Calculate parent node values from children (bottom-up aggregation).

### ResourceAggregator Class

```python
class ResourceAggregator:
    """
    Aggregates ResourceBuildUp values from children to parents.

    Calculates:
    - Total effort (sum of children)
    - Peak headcount (max across children)
    - Duration (max of children durations)
    - Skills (union of children skills)
    """

    def aggregate(self, root_nodes: List[HierarchyNode]) -> None:
        """
        Perform bottom-up aggregation.

        Modifies nodes in-place.

        Args:
            root_nodes: List of root HierarchyNodes (with ResourceBuildUp data)
        """
        for root in root_nodes:
            self._aggregate_node(root)

    def _aggregate_node(self, node: HierarchyNode) -> None:
        """Recursively aggregate a node."""
        resource: ResourceBuildUp = node.data

        if resource.is_leaf():
            # Leaf node - no aggregation needed
            return

        # Aggregate children first (depth-first)
        for child in node.children:
            self._aggregate_node(child)

        # Now aggregate from children
        total_effort = 0.0
        max_headcount = 0
        max_duration_low = 0.0
        max_duration_high = 0.0
        all_skills = set()

        for child in node.children:
            child_resource: ResourceBuildUp = child.data

            total_effort += child_resource.total_effort_pm
            max_headcount = max(max_headcount, child_resource.peak_headcount)
            max_duration_low = max(max_duration_low, child_resource.duration_months_low)
            max_duration_high = max(max_duration_high, child_resource.duration_months_high)
            all_skills.update(child_resource.skills_required)

        # Update parent node
        resource.aggregated_effort_pm = total_effort
        resource.aggregated_peak_headcount = max_headcount
        resource.duration_months_low = max_duration_low
        resource.duration_months_high = max_duration_high
        resource.skills_required = sorted(list(all_skills))
        resource.is_aggregate = True

        logger.debug(
            f"Aggregated ResourceBuildUp {resource.id}: "
            f"{total_effort:.1f} PM, {max_headcount} FTEs peak"
        )

class CostAggregator:
    """
    Aggregates CostBuildUp values from children to parents.

    Calculates:
    - Total cost (sum of children)
    - Labor vs non-labor (sum of children components)
    """

    def aggregate(self, root_nodes: List[HierarchyNode]) -> None:
        """
        Perform bottom-up aggregation.

        Args:
            root_nodes: List of root HierarchyNodes (with CostBuildUp data)
        """
        for root in root_nodes:
            self._aggregate_node(root)

    def _aggregate_node(self, node: HierarchyNode) -> None:
        """Recursively aggregate a node."""
        cost: CostBuildUp = node.data

        if cost.is_leaf():
            # Leaf node
            return

        # Aggregate children first
        for child in node.children:
            self._aggregate_node(child)

        # Aggregate from children
        total_cost_low = 0.0
        total_cost_high = 0.0
        total_labor_low = 0.0
        total_labor_high = 0.0
        total_non_labor_low = 0.0
        total_non_labor_high = 0.0

        for child in node.children:
            child_cost: CostBuildUp = child.data

            total_cost_low += child_cost.total_cost_low
            total_cost_high += child_cost.total_cost_high

            if child_cost.labor_cost_low is not None:
                total_labor_low += child_cost.labor_cost_low
            if child_cost.labor_cost_high is not None:
                total_labor_high += child_cost.labor_cost_high
            if child_cost.non_labor_cost_low is not None:
                total_non_labor_low += child_cost.non_labor_cost_low
            if child_cost.non_labor_cost_high is not None:
                total_non_labor_high += child_cost.non_labor_cost_high

        # Update parent
        cost.aggregated_cost_low = total_cost_low
        cost.aggregated_cost_high = total_cost_high
        cost.cost_low = total_cost_low  # Also set explicit fields for compatibility
        cost.cost_high = total_cost_high
        cost.labor_cost_low = total_labor_low if total_labor_low > 0 else None
        cost.labor_cost_high = total_labor_high if total_labor_high > 0 else None
        cost.non_labor_cost_low = total_non_labor_low if total_non_labor_low > 0 else None
        cost.non_labor_cost_high = total_non_labor_high if total_non_labor_high > 0 else None
        cost.is_aggregate = True

        logger.debug(
            f"Aggregated CostBuildUp {cost.id}: "
            f"${total_cost_low:,.0f} - ${total_cost_high:,.0f}"
        )
```

---

## Hierarchy Generator

### Purpose

Auto-generate hierarchical breakdowns from flat workstream-level estimates.

### Task Decomposition Templates

```python
from typing import Dict, List, Tuple

# Task breakdown templates by workstream
# Each workstream has standard sub-tasks with effort % allocations

TASK_TEMPLATES: Dict[str, List[Tuple[str, str, float, float]]] = {
    # Workstream: [(task_name, task_display, effort_min_pct, effort_max_pct)]

    "application_migration": [
        ("discovery", "Discovery & Planning", 0.10, 0.15),
        ("data_mapping", "Data Mapping & Transformation", 0.20, 0.30),
        ("development", "Development & Configuration", 0.35, 0.40),
        ("testing", "Testing & Validation", 0.15, 0.20),
        ("deployment", "Deployment & Cutover", 0.10, 0.15),
    ],

    "infrastructure_migration": [
        ("assessment", "Infrastructure Assessment", 0.15, 0.20),
        ("design", "Architecture Design", 0.15, 0.20),
        ("provisioning", "Provisioning & Setup", 0.30, 0.35),
        ("migration", "Data & Workload Migration", 0.25, 0.30),
        ("optimization", "Optimization & Tuning", 0.10, 0.15),
    ],

    "identity_management": [
        ("account_mapping", "Account Mapping", 0.20, 0.25),
        ("mfa_setup", "MFA Setup", 0.25, 0.30),
        ("sso_integration", "SSO Integration", 0.25, 0.30),
        ("testing_validation", "Testing & Validation", 0.20, 0.25),
    ],

    "data_migration": [
        ("data_profiling", "Data Profiling & Analysis", 0.15, 0.20),
        ("schema_mapping", "Schema Mapping", 0.15, 0.20),
        ("etl_development", "ETL Development", 0.35, 0.40),
        ("data_validation", "Data Validation", 0.20, 0.25),
        ("reconciliation", "Reconciliation", 0.10, 0.15),
    ],

    "network_segmentation": [
        ("network_design", "Network Design", 0.20, 0.25),
        ("firewall_config", "Firewall Configuration", 0.30, 0.35),
        ("routing_setup", "Routing Setup", 0.20, 0.25),
        ("testing", "Testing & Verification", 0.20, 0.25),
    ],

    "security_hardening": [
        ("security_assessment", "Security Assessment", 0.20, 0.25),
        ("policy_definition", "Policy Definition", 0.15, 0.20),
        ("implementation", "Implementation", 0.40, 0.45),
        ("validation", "Validation & Audit", 0.15, 0.20),
    ],
}

class HierarchyGenerator:
    """
    Auto-generates hierarchical ResourceBuildUp/CostBuildUp from flat estimates.

    Takes workstream-level estimate and breaks down into tasks using templates.
    """

    def __init__(self, use_templates: bool = True):
        """
        Initialize generator.

        Args:
            use_templates: If True, use TASK_TEMPLATES. If False, generate generic tasks.
        """
        self.use_templates = use_templates

    def generate_resource_hierarchy(
        self,
        parent_resource: ResourceBuildUp
    ) -> List[ResourceBuildUp]:
        """
        Generate child ResourceBuildUp nodes from parent.

        Args:
            parent_resource: Workstream-level ResourceBuildUp (flat, no children)

        Returns:
            List of child ResourceBuildUp nodes (tasks)
        """
        workstream = parent_resource.workstream

        # Get task template
        if self.use_templates and workstream in TASK_TEMPLATES:
            tasks_template = TASK_TEMPLATES[workstream]
        else:
            # Generic fallback
            tasks_template = [
                ("planning", "Planning", 0.15, 0.20),
                ("execution", "Execution", 0.60, 0.65),
                ("validation", "Validation", 0.15, 0.20),
            ]

        total_effort = parent_resource.total_effort_pm
        children = []

        for idx, (task_name, task_display, effort_min_pct, effort_max_pct) in enumerate(tasks_template):
            # Calculate task effort
            task_effort_low = total_effort * effort_min_pct
            task_effort_high = total_effort * effort_max_pct

            # Distribute effort to roles proportionally
            task_roles = []
            for parent_role in parent_resource.roles:
                role_fraction = parent_role.effort_pm / total_effort
                task_role_effort = task_effort_low * role_fraction

                # Calculate duration for task role
                task_role_duration = task_role_effort / parent_role.fte if parent_role.fte > 0 else 0

                task_role = RoleRequirement(
                    id=f"{parent_role.id}-{task_name}",
                    role=parent_role.role,
                    fte=parent_role.fte,
                    duration_months=task_role_duration,
                    skills=parent_role.skills[:],  # Copy
                    seniority=parent_role.seniority,
                    sourcing_type=parent_role.sourcing_type,
                    phase_allocation=parent_role.phase_allocation.copy() if parent_role.phase_allocation else None
                )
                task_roles.append(task_role)

            # Create child ResourceBuildUp
            child_resource = ResourceBuildUp(
                id=f"{parent_resource.id}-{task_name}",
                workstream=f"{workstream}.{task_name}",
                workstream_display=task_display,
                duration_months_low=parent_resource.duration_months_low * effort_min_pct,
                duration_months_high=parent_resource.duration_months_high * effort_max_pct,
                duration_confidence=parent_resource.duration_confidence,
                roles=task_roles,
                skills_required=parent_resource.skills_required[:],  # Copy
                sourcing_mix=parent_resource.sourcing_mix.copy(),
                assumptions=[f"Derived from {parent_resource.workstream_display} ({effort_min_pct*100:.0f}-{effort_max_pct*100:.0f}% of effort)"],
                source_facts=parent_resource.source_facts[:],
                confidence=parent_resource.confidence,
                # Hierarchical fields
                parent_id=parent_resource.id,
                children_ids=[],
                level=parent_resource.level + 1,
                path=f"{parent_resource.path}.{task_name}",
                display_order=idx,
                is_aggregate=False,  # Leaf node
            )

            children.append(child_resource)

        # Update parent to be aggregate
        parent_resource.children_ids = [child.id for child in children]
        parent_resource.is_aggregate = True

        # Aggregate parent values
        aggregator = ResourceAggregator()
        builder = HierarchyBuilder([parent_resource] + children)
        tree = builder.build_tree()
        aggregator.aggregate(tree)

        return children

    def generate_cost_hierarchy(
        self,
        parent_cost: CostBuildUp,
        parent_resource: Optional[ResourceBuildUp] = None
    ) -> List[CostBuildUp]:
        """
        Generate child CostBuildUp nodes from parent.

        If parent_resource provided, aligns cost breakdown with resource tasks.

        Args:
            parent_cost: Workstream-level CostBuildUp
            parent_resource: Optional ResourceBuildUp for alignment

        Returns:
            List of child CostBuildUp nodes
        """
        workstream = parent_cost.workstream

        # If resource provided, use its task breakdown
        if parent_resource and parent_resource.children_ids:
            # Align with resource tasks
            return self._generate_cost_from_resource_children(parent_cost, parent_resource)

        # Otherwise, use task templates
        if self.use_templates and workstream in TASK_TEMPLATES:
            tasks_template = TASK_TEMPLATES[workstream]
        else:
            tasks_template = [
                ("planning", "Planning", 0.15, 0.20),
                ("execution", "Execution", 0.60, 0.65),
                ("validation", "Validation", 0.15, 0.20),
            ]

        total_cost_low = parent_cost.cost_low
        total_cost_high = parent_cost.cost_high
        children = []

        for idx, (task_name, task_display, cost_min_pct, cost_max_pct) in enumerate(tasks_template):
            task_cost_low = total_cost_low * cost_min_pct
            task_cost_high = total_cost_high * cost_max_pct

            # Distribute labor/non-labor proportionally
            task_labor_low = (parent_cost.labor_cost_low or 0) * cost_min_pct
            task_labor_high = (parent_cost.labor_cost_high or 0) * cost_max_pct
            task_non_labor_low = (parent_cost.non_labor_cost_low or 0) * cost_min_pct
            task_non_labor_high = (parent_cost.non_labor_cost_high or 0) * cost_max_pct

            child_cost = CostBuildUp(
                id=f"{parent_cost.id}-{task_name}",
                workstream=f"{workstream}.{task_name}",
                workstream_display=task_display,
                cost_low=task_cost_low,
                cost_high=task_cost_high,
                currency=parent_cost.currency,
                cost_components=[],  # Could be populated from parent components
                estimation_method="derived",
                assumptions=[f"Derived from {parent_cost.workstream_display} ({cost_min_pct*100:.0f}-{cost_max_pct*100:.0f}% of cost)"],
                source_facts=parent_cost.source_facts[:],
                confidence=parent_cost.confidence,
                # Resource integration
                derived_from_resource_buildup=False,
                labor_cost_low=task_labor_low if task_labor_low > 0 else None,
                labor_cost_high=task_labor_high if task_labor_high > 0 else None,
                non_labor_cost_low=task_non_labor_low if task_non_labor_low > 0 else None,
                non_labor_cost_high=task_non_labor_high if task_non_labor_high > 0 else None,
                # Hierarchical
                parent_id=parent_cost.id,
                children_ids=[],
                level=parent_cost.level + 1,
                path=f"{parent_cost.path}.{task_name}",
                display_order=idx,
                is_aggregate=False,
            )

            children.append(child_cost)

        # Update parent
        parent_cost.children_ids = [child.id for child in children]
        parent_cost.is_aggregate = True

        # Aggregate
        aggregator = CostAggregator()
        builder = HierarchyBuilder([parent_cost] + children)
        tree = builder.build_tree()
        aggregator.aggregate(tree)

        return children

    def _generate_cost_from_resource_children(
        self,
        parent_cost: CostBuildUp,
        parent_resource: ResourceBuildUp
    ) -> List[CostBuildUp]:
        """
        Generate cost children aligned with resource children.

        Requires resource children to exist.
        """
        # This would retrieve resource children from Finding storage
        # For now, placeholder logic

        # TODO: Implement resource → cost alignment
        # Would use CostFromResourceBuilder for each resource child

        return []
```

---

## Usage Examples

### Example 1: Auto-Generate Task Hierarchy

```python
from specs.analysis_depth_enhancement.hierarchical_breakdown import HierarchyGenerator

# Step 1: Have a workstream-level ResourceBuildUp (flat)
parent_resource = ResourceBuildUp(
    id="RB-APP-001",
    workstream="application_migration",
    workstream_display="Application Migration",
    duration_months_low=6.0,
    duration_months_high=8.0,
    duration_confidence="high",
    roles=[
        RoleRequirement(
            id="ROLE-1",
            role="Senior Developer",
            fte=3.0,
            duration_months=6.0,
            skills=["Java", "AWS"],
            seniority="senior",
            sourcing_type="internal"
        ),
        RoleRequirement(
            id="ROLE-2",
            role="QA Engineer",
            fte=2.0,
            duration_months=3.0,
            skills=["Testing"],
            seniority="mid",
            sourcing_type="internal"
        ),
    ],
    skills_required=["Java", "AWS", "Testing"],
    sourcing_mix={},
    assumptions=["Team available"],
    source_facts=["F-APP-001"],
    confidence=0.85
)

# Step 2: Generate child tasks
generator = HierarchyGenerator(use_templates=True)
child_resources = generator.generate_resource_hierarchy(parent_resource)

print(f"Generated {len(child_resources)} tasks:")
for child in child_resources:
    print(f"  - {child.workstream_display}: {child.total_effort_pm:.1f} PM")

# Output:
# Generated 5 tasks:
#   - Discovery & Planning: 2.7 PM
#   - Data Mapping & Transformation: 6.0 PM
#   - Development & Configuration: 8.5 PM
#   - Testing & Validation: 4.0 PM
#   - Deployment & Cutover: 2.8 PM

# Parent is now aggregate
print(f"\nParent aggregated effort: {parent_resource.total_effort_pm:.1f} PM")
# Output: Parent aggregated effort: 24.0 PM
```

### Example 2: Build Tree and Display

```python
from specs.analysis_depth_enhancement.hierarchical_breakdown import HierarchyBuilder

# Step 1: Have parent + children
all_resources = [parent_resource] + child_resources

# Step 2: Build tree
builder = HierarchyBuilder(all_resources)
tree = builder.build_tree()

# Step 3: Display tree (recursive)
def print_tree(node, indent=0):
    effort = node.data.total_effort_pm
    print("  " * indent + f"├─ {node.display_name}: {effort:.1f} PM")
    for child in node.children:
        print_tree(child, indent + 1)

for root in tree:
    print_tree(root)

# Output:
# ├─ Application Migration: 24.0 PM
#   ├─ Discovery & Planning: 2.7 PM
#   ├─ Data Mapping & Transformation: 6.0 PM
#   ├─ Development & Configuration: 8.5 PM
#   ├─ Testing & Validation: 4.0 PM
#   ├─ Deployment & Cutover: 2.8 PM
```

### Example 3: Navigate Hierarchy

```python
# Get a specific node
builder = HierarchyBuilder(all_resources)
tree = builder.build_tree()

# Find node by ID
dev_node = builder.get_node_by_id("RB-APP-001-development")
print(f"Found: {dev_node.display_name}, Effort: {dev_node.data.total_effort_pm:.1f} PM")

# Get path to root
path = builder.get_path_to_root("RB-APP-001-development")
breadcrumb = " > ".join([node.display_name for node in path])
print(f"Breadcrumb: {breadcrumb}")

# Output:
# Found: Development & Configuration, Effort: 8.5 PM
# Breadcrumb: Application Migration > Development & Configuration
```

---

## API Endpoints

### GET /api/findings/<finding_id>/hierarchy/resources

**Purpose:** Retrieve complete ResourceBuildUp hierarchy as tree structure

**Response:**
```json
{
  "success": true,
  "finding_id": "FND-12345",
  "tree": [
    {
      "data": {
        "id": "RB-APP-001",
        "workstream_display": "Application Migration",
        "total_effort_pm": 24.0,
        "peak_headcount": 5,
        "level": 1,
        "is_aggregate": true
      },
      "children": [
        {
          "data": {
            "id": "RB-APP-001-discovery",
            "workstream_display": "Discovery & Planning",
            "total_effort_pm": 2.7,
            "level": 2,
            "is_aggregate": false
          },
          "children": []
        },
        ...
      ]
    }
  ]
}
```

### POST /api/findings/<finding_id>/hierarchy/generate

**Purpose:** Auto-generate hierarchical breakdown from flat estimate

**Request Body:**
```json
{
  "resource_buildup_id": "RB-APP-001",
  "use_templates": true
}
```

**Response:**
```json
{
  "success": true,
  "message": "Generated 5 child tasks",
  "parent_id": "RB-APP-001",
  "children_count": 5,
  "children": [...]
}
```

### GET /api/findings/<finding_id>/hierarchy/breadcrumb/<node_id>

**Purpose:** Get breadcrumb trail for a node

**Response:**
```json
{
  "success": true,
  "breadcrumb": [
    {
      "id": "RB-APP-001",
      "display_name": "Application Migration",
      "level": 1
    },
    {
      "id": "RB-APP-ERP",
      "display_name": "ERP Migration",
      "level": 2
    },
    {
      "id": "RB-APP-ERP-DEV",
      "display_name": "Development",
      "level": 3
    }
  ]
}
```

---

## UI Components

### TreeView Component

**File:** `web/static/js/components/TreeView.jsx`

```jsx
import React, { useState } from 'react';

/**
 * Recursive tree view component for hierarchical data.
 *
 * Props:
 * - node: HierarchyNode data
 * - onNodeClick: Callback when node clicked
 * - expandedIds: Set of expanded node IDs
 * - onToggleExpand: Callback when expand/collapse clicked
 */
const TreeNode = ({ node, onNodeClick, expandedIds, onToggleExpand, level = 0 }) => {
  const hasChildren = node.children && node.children.length > 0;
  const isExpanded = expandedIds.has(node.data.id);
  const indent = level * 20;

  return (
    <div className="tree-node">
      <div
        className="tree-node-content"
        style={{ paddingLeft: `${indent}px` }}
      >
        {hasChildren && (
          <button
            className="tree-node-toggle"
            onClick={() => onToggleExpand(node.data.id)}
          >
            {isExpanded ? '▼' : '▶'}
          </button>
        )}

        <div
          className="tree-node-label"
          onClick={() => onNodeClick(node.data)}
        >
          <span className="tree-node-icon">
            {hasChildren ? '📁' : '📄'}
          </span>
          <span className="tree-node-name">{node.data.workstream_display}</span>
          <span className="tree-node-stats">
            {node.data.total_effort_pm?.toFixed(1)} PM
            {node.data.total_cost_low && (
              <> • ${(node.data.total_cost_low / 1000).toFixed(0)}k</>
            )}
          </span>
        </div>
      </div>

      {isExpanded && hasChildren && (
        <div className="tree-node-children">
          {node.children.map(child => (
            <TreeNode
              key={child.data.id}
              node={child}
              onNodeClick={onNodeClick}
              expandedIds={expandedIds}
              onToggleExpand={onToggleExpand}
              level={level + 1}
            />
          ))}
        </div>
      )}
    </div>
  );
};

const TreeView = ({ tree, onNodeClick }) => {
  const [expandedIds, setExpandedIds] = useState(new Set());

  const handleToggleExpand = (nodeId) => {
    setExpandedIds(prev => {
      const newSet = new Set(prev);
      if (newSet.has(nodeId)) {
        newSet.delete(nodeId);
      } else {
        newSet.add(nodeId);
      }
      return newSet;
    });
  };

  const handleExpandAll = () => {
    const allIds = new Set();
    const collectIds = (nodes) => {
      nodes.forEach(node => {
        allIds.add(node.data.id);
        if (node.children) {
          collectIds(node.children);
        }
      });
    };
    collectIds(tree);
    setExpandedIds(allIds);
  };

  const handleCollapseAll = () => {
    setExpandedIds(new Set());
  };

  return (
    <div className="tree-view">
      <div className="tree-view-controls">
        <button onClick={handleExpandAll}>Expand All</button>
        <button onClick={handleCollapseAll}>Collapse All</button>
      </div>

      <div className="tree-view-content">
        {tree.map(root => (
          <TreeNode
            key={root.data.id}
            node={root}
            onNodeClick={onNodeClick}
            expandedIds={expandedIds}
            onToggleExpand={handleToggleExpand}
          />
        ))}
      </div>
    </div>
  );
};

export default TreeView;
```

### CSS Styling

```css
.tree-view {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  font-size: 14px;
}

.tree-view-controls {
  margin-bottom: 12px;
  display: flex;
  gap: 8px;
}

.tree-view-controls button {
  padding: 6px 12px;
  border: 1px solid #d0d7de;
  background: white;
  border-radius: 4px;
  cursor: pointer;
}

.tree-view-controls button:hover {
  background: #f6f8fa;
}

.tree-node {
  margin: 2px 0;
}

.tree-node-content {
  display: flex;
  align-items: center;
  padding: 6px 8px;
  border-radius: 4px;
  transition: background 0.15s;
}

.tree-node-content:hover {
  background: #f6f8fa;
}

.tree-node-toggle {
  background: none;
  border: none;
  cursor: pointer;
  padding: 4px;
  margin-right: 8px;
  font-size: 12px;
  color: #57606a;
}

.tree-node-label {
  display: flex;
  align-items: center;
  cursor: pointer;
  flex: 1;
}

.tree-node-icon {
  margin-right: 8px;
  font-size: 16px;
}

.tree-node-name {
  font-weight: 500;
  color: #24292f;
  margin-right: 12px;
}

.tree-node-stats {
  color: #57606a;
  font-size: 13px;
  margin-left: auto;
}

.tree-node-children {
  margin-left: 0;
}
```

---

## Testing Strategy

### Unit Tests

**File:** `tests/test_hierarchical_breakdown.py`

```python
import pytest
from specs.analysis_depth_enhancement.hierarchical_breakdown import (
    HierarchyBuilder,
    HierarchyGenerator,
    ResourceAggregator,
    CostAggregator,
)

class TestHierarchyBuilder:
    def test_build_tree_from_flat_list(self):
        # Create parent + children
        parent = ResourceBuildUp(
            id="RB-PARENT",
            workstream="parent",
            workstream_display="Parent",
            ...
        )

        child1 = ResourceBuildUp(
            id="RB-CHILD1",
            workstream="parent.child1",
            workstream_display="Child 1",
            parent_id="RB-PARENT",
            level=2,
            ...
        )

        child2 = ResourceBuildUp(
            id="RB-CHILD2",
            workstream="parent.child2",
            workstream_display="Child 2",
            parent_id="RB-PARENT",
            level=2,
            ...
        )

        # Build tree
        builder = HierarchyBuilder([parent, child1, child2])
        tree = builder.build_tree()

        # Assertions
        assert len(tree) == 1  # One root
        root = tree[0]
        assert root.id == "RB-PARENT"
        assert len(root.children) == 2
        assert root.children[0].id == "RB-CHILD1"

    def test_get_path_to_root(self):
        # ... (similar setup)
        builder = HierarchyBuilder([parent, child1, grandchild])
        tree = builder.build_tree()

        path = builder.get_path_to_root("RB-GRANDCHILD")
        assert len(path) == 3
        assert [node.id for node in path] == ["RB-PARENT", "RB-CHILD1", "RB-GRANDCHILD"]

class TestResourceAggregator:
    def test_aggregate_effort_from_children(self):
        parent = ResourceBuildUp(
            id="RB-PARENT",
            workstream="parent",
            workstream_display="Parent",
            children_ids=["RB-CHILD1", "RB-CHILD2"],
            is_aggregate=True,
            roles=[],
        )

        child1 = ResourceBuildUp(
            id="RB-CHILD1",
            parent_id="RB-PARENT",
            roles=[RoleRequirement(id="R1", fte=1, duration_months=10)],  # 10 PM
        )

        child2 = ResourceBuildUp(
            id="RB-CHILD2",
            parent_id="RB-PARENT",
            roles=[RoleRequirement(id="R2", fte=2, duration_months=5)],  # 10 PM
        )

        builder = HierarchyBuilder([parent, child1, child2])
        tree = builder.build_tree()

        aggregator = ResourceAggregator()
        aggregator.aggregate(tree)

        # Parent effort = 10 + 10 = 20 PM
        assert parent.aggregated_effort_pm == 20.0

class TestHierarchyGenerator:
    def test_generate_resource_hierarchy(self):
        parent = ResourceBuildUp(
            id="RB-APP",
            workstream="application_migration",
            workstream_display="Application Migration",
            roles=[RoleRequirement(id="R1", fte=3, duration_months=6)],  # 18 PM
        )

        generator = HierarchyGenerator(use_templates=True)
        children = generator.generate_resource_hierarchy(parent)

        # Application migration has 5 tasks
        assert len(children) == 5

        # Total child effort should equal parent effort (approx)
        total_child_effort = sum(c.total_effort_pm for c in children)
        assert abs(total_child_effort - 18.0) < 1.0  # Allow rounding

        # Parent should now be aggregate
        assert parent.is_aggregate is True
        assert len(parent.children_ids) == 5
```

---

## Migration Strategy

### Phase 1: Add Hierarchical Fields

**Migration Script:** `scripts/migrate_add_hierarchical_fields.py`

```python
"""Add hierarchical fields to existing ResourceBuildUp/CostBuildUp."""

from web.app import create_app
from web.database import db, Finding

def migrate():
    app = create_app()
    with app.app_context():
        findings = Finding.query.all()

        for finding in findings:
            # Migrate ResourceBuildUp
            if finding.resource_buildup_json:
                rb_data = finding.resource_buildup_json
                rb_data.setdefault('parent_id', None)
                rb_data.setdefault('children_ids', [])
                rb_data.setdefault('level', 1)
                rb_data.setdefault('path', rb_data.get('workstream', ''))
                rb_data.setdefault('display_order', 0)
                rb_data.setdefault('is_aggregate', False)
                rb_data.setdefault('aggregated_effort_pm', None)
                rb_data.setdefault('aggregated_peak_headcount', None)

            # Migrate CostBuildUp
            if finding.cost_buildup_json:
                cb_data = finding.cost_buildup_json
                cb_data.setdefault('parent_id', None)
                cb_data.setdefault('children_ids', [])
                cb_data.setdefault('level', 1)
                cb_data.setdefault('path', cb_data.get('workstream', ''))
                cb_data.setdefault('display_order', 0)
                cb_data.setdefault('is_aggregate', False)
                cb_data.setdefault('aggregated_cost_low', None)
                cb_data.setdefault('aggregated_cost_high', None)

        db.session.commit()

if __name__ == '__main__':
    migrate()
```

---

## Success Criteria

✅ **Hierarchy successful when:**

1. **Tree building works:** Flat list → correct parent-child structure
2. **Aggregation accurate:** Parent totals match sum of children (±1% rounding)
3. **Navigation functional:** Can traverse parent → child and child → parent
4. **UI renders correctly:** TreeView displays expandable/collapsible hierarchy
5. **Auto-generation quality:** Generated tasks match templates, reasonable effort splits
6. **Performance acceptable:** Build tree for 100 nodes in <100ms
7. **Data integrity:** No orphaned nodes, all parent_id references valid

---

## Document Status

**Status:** ✅ Ready for Implementation
**Dependencies:** Specs 01-03
**Next Steps:** Proceed to Spec 05 (Explanatory UI Enhancement)

**Author:** Claude Sonnet 4.5
**Date:** February 10, 2026
**Version:** 1.0
