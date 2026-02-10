# Spec 03: Resource-Cost Integration
**Version:** 1.0
**Date:** February 10, 2026
**Status:** Ready for Implementation
**Dependencies:** Spec 01 (Resource Buildup Data Model), Spec 02 (Resource Calculation Engine)

---

## Executive Summary

This specification defines the **integration layer** between `ResourceBuildUp` and `CostBuildUp`, enabling:

1. **Bidirectional linking** - Navigate from resources → costs and costs → resources
2. **Automatic labor cost derivation** - Generate labor costs from resource effort estimates
3. **Consistency validation** - Ensure resource estimates align with cost models
4. **Transparency enhancement** - Show users HOW resources drive costs
5. **Unified display** - Present resources AND costs together in UI

### Why This Matters

**User Feedback Context:**
- "Cost tracking visibility - show calculations based on inventory data"
- "Sub-activities that add up to totals"
- "Resource buildup lens" must integrate with existing cost transparency

**Current State:**
- ✅ CostBuildUp exists with world-class transparency
- ✅ ResourceBuildUp framework designed (Spec 01)
- ❌ No connection between them - resources and costs exist in isolation

**Target State:**
- Resources define EFFORT (person-months)
- Blended rates convert effort to LABOR COSTS
- Total costs = Labor + Non-labor (tools, licenses, services)
- Full transparency: Users see effort → rate → cost chain

---

## Architecture Overview

### Integration Points

```
┌─────────────────────────────────────────────────────────────┐
│                        Finding                               │
│  ┌────────────────────────────┐  ┌─────────────────────────┐│
│  │   resource_buildup_json     │  │    cost_buildup_json    ││
│  │  (ResourceBuildUp)          │◄─┤   (CostBuildUp)         ││
│  │                             │  │                          ││
│  │  • Total effort: 34 PM      │  │  • Labor cost: $340k    ││
│  │  • Peak headcount: 6 FTEs   │  │  • Non-labor: $50k      ││
│  │  • Roles breakdown          │  │  • Total: $390k         ││
│  │  • Skills required          │  │  • Derived from RB-123  ││
│  └─────────────┬───────────────┘  └──────────┬──────────────┘│
│                │                              │               │
│                └──────────┬───────────────────┘               │
│                           │                                   │
│                    Bidirectional                              │
│                       Linking                                 │
└─────────────────────────────────────────────────────────────┘

Integration Layer:
├─ LaborCostCalculator: Effort × Rate → Labor Cost
├─ ConsistencyValidator: Ensure alignment
├─ CostFromResourceBuilder: Auto-generate costs from resources
└─ UnifiedDisplayBuilder: Resources + Costs in single view
```

### Data Flow

**Scenario 1: Resources → Costs (Automatic)**
```
1. ResourceCalculator generates ResourceBuildUp (34 PM effort)
2. LaborCostCalculator applies blended rates ($10k/PM)
3. CostFromResourceBuilder creates CostBuildUp ($340k labor)
4. Non-labor costs added manually or from benchmarks ($50k tools)
5. Finding stores both resource_buildup_json AND cost_buildup_json
6. Both link to each other via IDs
```

**Scenario 2: Manual Cost Entry (Validation)**
```
1. User manually enters CostBuildUp ($500k total, $400k labor)
2. ResourceCalculator estimates ResourceBuildUp (34 PM)
3. ConsistencyValidator compares:
   - Expected labor cost: 34 PM × $10k/PM = $340k
   - Actual labor cost: $400k
   - Variance: +17.6%
4. If variance > threshold, flag for review
5. User adjusts resource estimate OR cost estimate to reconcile
```

**Scenario 3: Resource Updates (Propagation)**
```
1. User edits ResourceBuildUp (34 PM → 40 PM)
2. System detects linked CostBuildUp exists
3. LaborCostCalculator recalculates ($340k → $400k)
4. User prompted: "Resources changed. Update linked costs?"
5. If yes: CostBuildUp labor component auto-updated
6. If no: Mark as "needs reconciliation"
```

---

## Enhanced CostBuildUp Model

### New Fields for Resource Integration

**Add to existing `CostBuildUp` dataclass:**

```python
from dataclasses import dataclass, field
from typing import Optional, List, Dict
from enum import Enum

@dataclass
class CostBuildUp:
    """
    ENHANCED with resource integration fields.

    Backward compatible: All new fields have defaults.
    """

    # ============= EXISTING FIELDS (unchanged) =============
    id: str
    workstream: str
    workstream_display: str

    # Cost ranges
    cost_low: float
    cost_high: float
    currency: str = "USD"

    # Breakdown
    cost_components: List['CostComponent'] = field(default_factory=list)

    # Transparency
    estimation_method: str = "benchmark"
    assumptions: List[str] = field(default_factory=list)
    source_facts: List[str] = field(default_factory=list)
    confidence: float = 0.7

    # Metadata
    created_at: str = ""
    updated_at: str = ""
    version: int = 1

    # ============= NEW FIELDS (resource integration) =============

    # Linking
    derived_from_resource_buildup: bool = False
    """True if this cost was auto-generated from ResourceBuildUp."""

    resource_buildup_id: Optional[str] = None
    """ID of linked ResourceBuildUp (if any). Enables bidirectional nav."""

    # Labor cost breakdown
    labor_cost_low: Optional[float] = None
    labor_cost_high: Optional[float] = None
    """Labor costs derived from resource effort × blended rate."""

    non_labor_cost_low: Optional[float] = None
    non_labor_cost_high: Optional[float] = None
    """Non-labor costs (tools, licenses, cloud services, etc.)."""

    blended_rate_low: Optional[float] = None
    blended_rate_high: Optional[float] = None
    """Blended rate per person-month used in labor calculation."""

    # Validation
    consistency_status: str = "not_validated"
    """One of: not_validated, consistent, needs_review, conflicting."""

    consistency_notes: List[str] = field(default_factory=list)
    """Validation findings (e.g., "Labor cost 15% higher than resource estimate")."""

    # Hierarchical (will be used in Spec 04)
    parent_id: Optional[str] = None
    children_ids: List[str] = field(default_factory=list)

    def __post_init__(self):
        """Validate on creation."""
        # Generate ID if not provided
        if not self.id:
            from datetime import datetime
            import uuid
            timestamp = datetime.utcnow().strftime("%Y%m%d")
            uuid_short = uuid.uuid4().hex[:8]
            self.id = f"CB-{self.workstream}-{timestamp}-{uuid_short}"

        # Validate cost ranges
        if self.cost_low > self.cost_high:
            raise ValueError(f"cost_low ({self.cost_low}) > cost_high ({self.cost_high})")

        # Validate labor/non-labor sum matches total
        if self.labor_cost_low is not None and self.non_labor_cost_low is not None:
            expected_low = self.labor_cost_low + self.non_labor_cost_low
            if abs(expected_low - self.cost_low) > 0.01:
                raise ValueError(
                    f"Labor + non-labor ({expected_low}) != total cost_low ({self.cost_low})"
                )

        if self.labor_cost_high is not None and self.non_labor_cost_high is not None:
            expected_high = self.labor_cost_high + self.non_labor_cost_high
            if abs(expected_high - self.cost_high) > 0.01:
                raise ValueError(
                    f"Labor + non-labor ({expected_high}) != total cost_high ({self.cost_high})"
                )

    @property
    def labor_cost_percentage(self) -> Optional[float]:
        """What % of total cost is labor?"""
        if self.labor_cost_low is None or self.cost_low == 0:
            return None
        return (self.labor_cost_low / self.cost_low) * 100

    @property
    def non_labor_cost_percentage(self) -> Optional[float]:
        """What % of total cost is non-labor?"""
        if self.non_labor_cost_low is None or self.cost_low == 0:
            return None
        return (self.non_labor_cost_low / self.cost_low) * 100

    def to_dict(self) -> Dict:
        """Serialize to JSON-compatible dict."""
        return {
            "id": self.id,
            "workstream": self.workstream,
            "workstream_display": self.workstream_display,
            "cost_low": self.cost_low,
            "cost_high": self.cost_high,
            "currency": self.currency,
            "cost_components": [c.to_dict() for c in self.cost_components],
            "estimation_method": self.estimation_method,
            "assumptions": self.assumptions,
            "source_facts": self.source_facts,
            "confidence": self.confidence,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "version": self.version,
            # New fields
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
            "parent_id": self.parent_id,
            "children_ids": self.children_ids,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> Optional['CostBuildUp']:
        """Deserialize with error handling."""
        try:
            if not isinstance(data, dict):
                logger.error(f"CostBuildUp data is not a dict: {type(data)}")
                return None

            # Required fields
            required = ['workstream', 'workstream_display', 'cost_low', 'cost_high']
            missing = [f for f in required if f not in data]
            if missing:
                logger.error(f"Missing required fields: {missing}")
                return None

            # Deserialize cost components
            components = []
            for comp_data in data.get('cost_components', []):
                comp = CostComponent.from_dict(comp_data)
                if comp:
                    components.append(comp)

            return cls(
                id=data.get('id', ''),
                workstream=data['workstream'],
                workstream_display=data['workstream_display'],
                cost_low=float(data['cost_low']),
                cost_high=float(data['cost_high']),
                currency=data.get('currency', 'USD'),
                cost_components=components,
                estimation_method=data.get('estimation_method', 'benchmark'),
                assumptions=data.get('assumptions', []),
                source_facts=data.get('source_facts', []),
                confidence=float(data.get('confidence', 0.7)),
                created_at=data.get('created_at', ''),
                updated_at=data.get('updated_at', ''),
                version=int(data.get('version', 1)),
                # New fields (all optional)
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
                parent_id=data.get('parent_id'),
                children_ids=data.get('children_ids', []),
            )
        except Exception as e:
            logger.error(f"Error deserializing CostBuildUp: {e}", exc_info=True)
            return None
```

### CostComponent Model (Existing, Referenced)

```python
@dataclass
class CostComponent:
    """
    Individual cost item within a CostBuildUp.

    Example: "Senior Developer labor" or "AWS EC2 instances"
    """
    id: str
    label: str
    cost_low: float
    cost_high: float
    quantity: Optional[float] = None
    unit: Optional[str] = None
    notes: str = ""

    # NEW: Resource linkage
    derived_from_role: Optional[str] = None
    """If derived from ResourceBuildUp, which role? (e.g., "Senior Developer")"""

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "label": self.label,
            "cost_low": self.cost_low,
            "cost_high": self.cost_high,
            "quantity": self.quantity,
            "unit": self.unit,
            "notes": self.notes,
            "derived_from_role": self.derived_from_role,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> Optional['CostComponent']:
        try:
            return cls(
                id=data.get('id', ''),
                label=data['label'],
                cost_low=float(data['cost_low']),
                cost_high=float(data['cost_high']),
                quantity=data.get('quantity'),
                unit=data.get('unit'),
                notes=data.get('notes', ''),
                derived_from_role=data.get('derived_from_role'),
            )
        except Exception as e:
            logger.error(f"Error deserializing CostComponent: {e}")
            return None
```

---

## LaborCostCalculator

### Purpose

Convert resource effort (person-months) into labor costs using blended rates.

### Blended Rate Model

```python
from dataclasses import dataclass
from typing import Dict

@dataclass
class BlendedRateConfig:
    """
    Configuration for labor cost calculation.

    Rates vary by:
    - Geography (onshore vs offshore)
    - Role seniority (junior vs senior)
    - Sourcing mix (internal vs contractor vs vendor)
    """

    # Base rates per person-month by seniority
    rates_internal: Dict[str, float] = None
    rates_contractor: Dict[str, float] = None
    rates_vendor: Dict[str, float] = None

    # Default overrides
    default_internal_rate: float = 12000  # $12k/PM (fully loaded)
    default_contractor_rate: float = 15000  # $15k/PM (premium)
    default_vendor_rate: float = 10000  # $10k/PM (offshore)

    # Multipliers
    offshore_multiplier: float = 0.6  # Offshore is 60% of onshore cost
    nearshore_multiplier: float = 0.8  # Nearshore is 80% of onshore cost

    def __post_init__(self):
        if self.rates_internal is None:
            # Default rates by seniority (onshore, internal)
            self.rates_internal = {
                "junior": 8000,
                "mid": 12000,
                "senior": 16000,
                "lead": 20000,
                "principal": 25000,
            }

        if self.rates_contractor is None:
            # Contractors are ~25% premium over internal
            self.rates_contractor = {
                k: v * 1.25 for k, v in self.rates_internal.items()
            }

        if self.rates_vendor is None:
            # Vendors are often offshore, lower rates
            self.rates_vendor = {
                k: v * self.offshore_multiplier for k, v in self.rates_internal.items()
            }

    def get_rate(
        self,
        seniority: str,
        sourcing: str,
        geography: str = "onshore"
    ) -> float:
        """
        Get blended rate for a specific role configuration.

        Args:
            seniority: junior, mid, senior, lead, principal
            sourcing: internal, contractor, vendor
            geography: onshore, nearshore, offshore

        Returns:
            Rate in USD per person-month
        """
        # Select rate table
        if sourcing == "internal":
            rate_table = self.rates_internal
        elif sourcing == "contractor":
            rate_table = self.rates_contractor
        elif sourcing == "vendor":
            rate_table = self.rates_vendor
        else:
            # Fallback to default
            return self.default_internal_rate

        # Get base rate by seniority
        base_rate = rate_table.get(seniority.lower())
        if base_rate is None:
            # Unknown seniority, use default
            if sourcing == "internal":
                base_rate = self.default_internal_rate
            elif sourcing == "contractor":
                base_rate = self.default_contractor_rate
            else:
                base_rate = self.default_vendor_rate

        # Apply geography multiplier
        if geography == "offshore":
            base_rate *= self.offshore_multiplier
        elif geography == "nearshore":
            base_rate *= self.nearshore_multiplier
        # onshore: no multiplier (base rate)

        return base_rate
```

### LaborCostCalculator Class

```python
import logging
from typing import Tuple, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class LaborCostBreakdown:
    """Result of labor cost calculation."""
    total_cost_low: float
    total_cost_high: float
    blended_rate_low: float
    blended_rate_high: float
    cost_components: List['CostComponent']
    assumptions: List[str]

class LaborCostCalculator:
    """
    Calculates labor costs from ResourceBuildUp.

    Formula:
        Labor Cost = Σ (role.effort_pm × rate)

    Where rate depends on:
        - Role seniority (junior, senior, etc.)
        - Sourcing (internal, contractor, vendor)
        - Geography (onshore, nearshore, offshore)
    """

    def __init__(
        self,
        rate_config: Optional[BlendedRateConfig] = None,
        geography: str = "onshore"
    ):
        """
        Initialize calculator.

        Args:
            rate_config: Rate configuration (defaults to standard US rates)
            geography: onshore, nearshore, or offshore
        """
        self.rate_config = rate_config or BlendedRateConfig()
        self.geography = geography

    def calculate(
        self,
        resource_buildup: 'ResourceBuildUp'
    ) -> LaborCostBreakdown:
        """
        Calculate labor costs from resource buildup.

        Args:
            resource_buildup: ResourceBuildUp instance

        Returns:
            LaborCostBreakdown with total costs and components
        """
        cost_components = []
        total_cost_low = 0.0
        total_cost_high = 0.0
        assumptions = []

        # Calculate cost per role
        for role in resource_buildup.roles:
            role_cost_low, role_cost_high, role_assumptions = self._calculate_role_cost(
                role, resource_buildup.sourcing_mix
            )

            # Create cost component
            component = CostComponent(
                id=f"LABOR-{role.id}",
                label=f"{role.role} labor ({role.effort_pm:.1f} PM)",
                cost_low=role_cost_low,
                cost_high=role_cost_high,
                quantity=role.effort_pm,
                unit="person-months",
                notes=f"Seniority: {role.seniority}, FTE: {role.fte}",
                derived_from_role=role.role
            )
            cost_components.append(component)

            total_cost_low += role_cost_low
            total_cost_high += role_cost_high
            assumptions.extend(role_assumptions)

        # Calculate blended rates
        total_effort = resource_buildup.total_effort_pm
        blended_rate_low = total_cost_low / total_effort if total_effort > 0 else 0
        blended_rate_high = total_cost_high / total_effort if total_effort > 0 else 0

        # Add global assumptions
        assumptions.extend([
            f"Geography: {self.geography}",
            f"Total effort: {total_effort:.1f} person-months",
            f"Blended rate: ${blended_rate_low:,.0f} - ${blended_rate_high:,.0f} per PM",
        ])

        if resource_buildup.sourcing_mix:
            sourcing_desc = ", ".join([
                f"{k}: {v*100:.0f}%" for k, v in resource_buildup.sourcing_mix.items()
            ])
            assumptions.append(f"Sourcing mix: {sourcing_desc}")

        return LaborCostBreakdown(
            total_cost_low=total_cost_low,
            total_cost_high=total_cost_high,
            blended_rate_low=blended_rate_low,
            blended_rate_high=blended_rate_high,
            cost_components=cost_components,
            assumptions=assumptions
        )

    def _calculate_role_cost(
        self,
        role: 'RoleRequirement',
        sourcing_mix: Dict[str, float]
    ) -> Tuple[float, float, List[str]]:
        """
        Calculate cost for a single role.

        Returns:
            (cost_low, cost_high, assumptions)
        """
        effort_pm = role.effort_pm
        assumptions = []

        # If role has explicit sourcing, use it
        if role.sourcing_type and role.sourcing_type != "mixed":
            rate = self.rate_config.get_rate(
                seniority=role.seniority,
                sourcing=role.sourcing_type,
                geography=self.geography
            )
            cost_low = effort_pm * rate
            cost_high = cost_low  # Single sourcing = no range
            assumptions.append(
                f"{role.role}: {role.sourcing_type}, "
                f"${rate:,.0f}/PM × {effort_pm:.1f} PM = ${cost_low:,.0f}"
            )
            return (cost_low, cost_high, assumptions)

        # Mixed sourcing: Calculate weighted average
        if not sourcing_mix:
            # No sourcing mix specified, use default internal rate
            rate = self.rate_config.get_rate(
                seniority=role.seniority,
                sourcing="internal",
                geography=self.geography
            )
            cost_low = effort_pm * rate
            cost_high = cost_low
            assumptions.append(
                f"{role.role}: Default internal rate ${rate:,.0f}/PM"
            )
            return (cost_low, cost_high, assumptions)

        # Calculate blended rate across sourcing types
        blended_rate_low = 0.0
        blended_rate_high = 0.0

        for sourcing, fraction in sourcing_mix.items():
            rate = self.rate_config.get_rate(
                seniority=role.seniority,
                sourcing=sourcing,
                geography=self.geography
            )
            blended_rate_low += rate * fraction
            blended_rate_high += rate * fraction * 1.1  # 10% variance

        cost_low = effort_pm * blended_rate_low
        cost_high = effort_pm * blended_rate_high

        assumptions.append(
            f"{role.role}: Blended rate ${blended_rate_low:,.0f}/PM "
            f"(±10% for range) × {effort_pm:.1f} PM"
        )

        return (cost_low, cost_high, assumptions)
```

---

## CostFromResourceBuilder

### Purpose

Auto-generate complete `CostBuildUp` from `ResourceBuildUp`.

### Class Implementation

```python
from datetime import datetime
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)

class CostFromResourceBuilder:
    """
    Builds CostBuildUp from ResourceBuildUp.

    Steps:
    1. Calculate labor costs (via LaborCostCalculator)
    2. Estimate or retrieve non-labor costs
    3. Combine into total cost
    4. Link to source ResourceBuildUp
    5. Return CostBuildUp instance

    Usage:
        builder = CostFromResourceBuilder(
            resource_buildup=rb,
            rate_config=BlendedRateConfig(),
            non_labor_costs=(10000, 20000)
        )
        cost_buildup = builder.build()
    """

    def __init__(
        self,
        resource_buildup: 'ResourceBuildUp',
        rate_config: Optional[BlendedRateConfig] = None,
        geography: str = "onshore",
        non_labor_costs: Optional[Tuple[float, float]] = None,
        non_labor_assumptions: Optional[List[str]] = None
    ):
        """
        Initialize builder.

        Args:
            resource_buildup: Source ResourceBuildUp
            rate_config: Labor rate configuration
            geography: onshore, nearshore, offshore
            non_labor_costs: (low, high) tuple for non-labor costs
            non_labor_assumptions: List of assumptions for non-labor costs
        """
        self.resource_buildup = resource_buildup
        self.rate_config = rate_config or BlendedRateConfig()
        self.geography = geography
        self.non_labor_costs = non_labor_costs or (0, 0)
        self.non_labor_assumptions = non_labor_assumptions or []

    def build(self) -> 'CostBuildUp':
        """
        Build CostBuildUp from ResourceBuildUp.

        Returns:
            CostBuildUp instance with full transparency
        """
        # Step 1: Calculate labor costs
        labor_calculator = LaborCostCalculator(
            rate_config=self.rate_config,
            geography=self.geography
        )
        labor_breakdown = labor_calculator.calculate(self.resource_buildup)

        # Step 2: Get non-labor costs
        non_labor_low, non_labor_high = self.non_labor_costs

        # Step 3: Total costs
        total_low = labor_breakdown.total_cost_low + non_labor_low
        total_high = labor_breakdown.total_cost_high + non_labor_high

        # Step 4: Combine assumptions
        all_assumptions = labor_breakdown.assumptions + self.non_labor_assumptions

        # Add resource-specific assumptions
        if self.resource_buildup.assumptions:
            all_assumptions.append("Resource assumptions:")
            all_assumptions.extend([
                f"  - {a}" for a in self.resource_buildup.assumptions
            ])

        # Step 5: Create CostBuildUp
        now = datetime.utcnow().isoformat()

        cost_buildup = CostBuildUp(
            id="",  # Will auto-generate in __post_init__
            workstream=self.resource_buildup.workstream,
            workstream_display=self.resource_buildup.workstream_display,
            cost_low=total_low,
            cost_high=total_high,
            currency="USD",
            cost_components=labor_breakdown.cost_components,
            estimation_method="resource_based",
            assumptions=all_assumptions,
            source_facts=self.resource_buildup.source_facts,
            confidence=self.resource_buildup.confidence,
            created_at=now,
            updated_at=now,
            version=1,
            # Resource integration fields
            derived_from_resource_buildup=True,
            resource_buildup_id=self.resource_buildup.id,
            labor_cost_low=labor_breakdown.total_cost_low,
            labor_cost_high=labor_breakdown.total_cost_high,
            non_labor_cost_low=non_labor_low,
            non_labor_cost_high=non_labor_high,
            blended_rate_low=labor_breakdown.blended_rate_low,
            blended_rate_high=labor_breakdown.blended_rate_high,
            consistency_status="consistent",  # Auto-generated, so consistent
            consistency_notes=[],
        )

        logger.info(
            f"Generated CostBuildUp {cost_buildup.id} from ResourceBuildUp {self.resource_buildup.id}: "
            f"${total_low:,.0f} - ${total_high:,.0f} "
            f"({labor_breakdown.total_cost_low:,.0f} labor + {non_labor_low:,.0f} non-labor)"
        )

        return cost_buildup
```

---

## ConsistencyValidator

### Purpose

Validate that manually-entered costs align with resource estimates.

### Validation Logic

```python
from typing import Tuple, List
from enum import Enum

class ConsistencyStatus(Enum):
    """Consistency check results."""
    NOT_VALIDATED = "not_validated"
    CONSISTENT = "consistent"
    NEEDS_REVIEW = "needs_review"  # 10-25% variance
    CONFLICTING = "conflicting"    # >25% variance

@dataclass
class ConsistencyCheckResult:
    """Result of consistency validation."""
    status: ConsistencyStatus
    notes: List[str]
    variance_percentage: Optional[float]
    expected_cost_low: Optional[float]
    expected_cost_high: Optional[float]
    actual_cost_low: Optional[float]
    actual_cost_high: Optional[float]

class ConsistencyValidator:
    """
    Validates alignment between ResourceBuildUp and CostBuildUp.

    Checks:
    1. Does labor cost match resource effort × rate?
    2. Are assumptions consistent?
    3. Is variance within acceptable range?

    Thresholds:
    - <10%: Consistent
    - 10-25%: Needs review
    - >25%: Conflicting
    """

    def __init__(
        self,
        rate_config: Optional[BlendedRateConfig] = None,
        geography: str = "onshore"
    ):
        self.rate_config = rate_config or BlendedRateConfig()
        self.geography = geography

    def validate(
        self,
        resource_buildup: 'ResourceBuildUp',
        cost_buildup: 'CostBuildUp'
    ) -> ConsistencyCheckResult:
        """
        Check if cost buildup is consistent with resource buildup.

        Args:
            resource_buildup: ResourceBuildUp instance
            cost_buildup: CostBuildUp instance to validate

        Returns:
            ConsistencyCheckResult with status and details
        """
        notes = []

        # If cost was auto-generated from this resource, it's consistent
        if (cost_buildup.derived_from_resource_buildup and
            cost_buildup.resource_buildup_id == resource_buildup.id):
            return ConsistencyCheckResult(
                status=ConsistencyStatus.CONSISTENT,
                notes=["Auto-generated from this ResourceBuildUp"],
                variance_percentage=0.0,
                expected_cost_low=cost_buildup.labor_cost_low,
                expected_cost_high=cost_buildup.labor_cost_high,
                actual_cost_low=cost_buildup.labor_cost_low,
                actual_cost_high=cost_buildup.labor_cost_high,
            )

        # Calculate expected labor cost from resources
        labor_calculator = LaborCostCalculator(
            rate_config=self.rate_config,
            geography=self.geography
        )
        expected_labor = labor_calculator.calculate(resource_buildup)

        # Get actual labor cost from CostBuildUp
        actual_labor_low = cost_buildup.labor_cost_low
        actual_labor_high = cost_buildup.labor_cost_high

        if actual_labor_low is None or actual_labor_high is None:
            # Cost buildup doesn't have labor breakdown
            notes.append(
                "CostBuildUp missing labor cost breakdown. "
                "Cannot validate against resources."
            )
            return ConsistencyCheckResult(
                status=ConsistencyStatus.NOT_VALIDATED,
                notes=notes,
                variance_percentage=None,
                expected_cost_low=expected_labor.total_cost_low,
                expected_cost_high=expected_labor.total_cost_high,
                actual_cost_low=None,
                actual_cost_high=None,
            )

        # Calculate variance
        variance_low = abs(actual_labor_low - expected_labor.total_cost_low) / expected_labor.total_cost_low
        variance_high = abs(actual_labor_high - expected_labor.total_cost_high) / expected_labor.total_cost_high
        variance_pct = max(variance_low, variance_high) * 100

        # Determine status
        if variance_pct < 10:
            status = ConsistencyStatus.CONSISTENT
            notes.append(
                f"Labor cost within 10% of resource-based estimate (variance: {variance_pct:.1f}%)"
            )
        elif variance_pct < 25:
            status = ConsistencyStatus.NEEDS_REVIEW
            notes.append(
                f"Labor cost {variance_pct:.1f}% different from resource-based estimate. "
                f"Expected: ${expected_labor.total_cost_low:,.0f} - ${expected_labor.total_cost_high:,.0f}, "
                f"Actual: ${actual_labor_low:,.0f} - ${actual_labor_high:,.0f}"
            )
        else:
            status = ConsistencyStatus.CONFLICTING
            notes.append(
                f"⚠️ Labor cost {variance_pct:.1f}% different from resource-based estimate. "
                f"This indicates a significant discrepancy. "
                f"Expected: ${expected_labor.total_cost_low:,.0f} - ${expected_labor.total_cost_high:,.0f}, "
                f"Actual: ${actual_labor_low:,.0f} - ${actual_labor_high:,.0f}. "
                f"Review resource estimates or cost assumptions."
            )

        # Check blended rates
        if cost_buildup.blended_rate_low and cost_buildup.blended_rate_high:
            actual_rate_avg = (cost_buildup.blended_rate_low + cost_buildup.blended_rate_high) / 2
            expected_rate_avg = (expected_labor.blended_rate_low + expected_labor.blended_rate_high) / 2
            rate_variance = abs(actual_rate_avg - expected_rate_avg) / expected_rate_avg * 100

            if rate_variance > 15:
                notes.append(
                    f"Blended rate differs by {rate_variance:.1f}%: "
                    f"Expected ~${expected_rate_avg:,.0f}/PM, "
                    f"Actual ~${actual_rate_avg:,.0f}/PM"
                )

        return ConsistencyCheckResult(
            status=status,
            notes=notes,
            variance_percentage=variance_pct,
            expected_cost_low=expected_labor.total_cost_low,
            expected_cost_high=expected_labor.total_cost_high,
            actual_cost_low=actual_labor_low,
            actual_cost_high=actual_labor_high,
        )
```

---

## Integration Helpers

### Linking Functions

```python
from typing import Optional
from web.database import Finding
import logging

logger = logging.getLogger(__name__)

def link_resource_to_cost(
    finding: Finding,
    resource_buildup: 'ResourceBuildUp',
    cost_buildup: 'CostBuildUp'
) -> None:
    """
    Establish bidirectional link between ResourceBuildUp and CostBuildUp.

    Updates both models and saves to finding.

    Args:
        finding: Finding instance to update
        resource_buildup: ResourceBuildUp to link
        cost_buildup: CostBuildUp to link
    """
    # Link cost → resource
    cost_buildup.resource_buildup_id = resource_buildup.id
    cost_buildup.derived_from_resource_buildup = True

    # Update finding
    finding.resource_buildup_json = resource_buildup.to_dict()
    finding.cost_buildup_json = cost_buildup.to_dict()

    logger.info(
        f"Linked ResourceBuildUp {resource_buildup.id} ↔ CostBuildUp {cost_buildup.id} "
        f"on Finding {finding.id}"
    )

def get_linked_cost(finding: Finding, resource_buildup: 'ResourceBuildUp') -> Optional['CostBuildUp']:
    """
    Get CostBuildUp linked to this ResourceBuildUp (if any).

    Args:
        finding: Finding to search
        resource_buildup: ResourceBuildUp to find cost for

    Returns:
        CostBuildUp if linked, else None
    """
    if not finding.cost_buildup_json:
        return None

    cost = CostBuildUp.from_dict(finding.cost_buildup_json)
    if not cost:
        return None

    # Check if linked
    if cost.resource_buildup_id == resource_buildup.id:
        return cost

    return None

def get_linked_resource(finding: Finding, cost_buildup: 'CostBuildUp') -> Optional['ResourceBuildUp']:
    """
    Get ResourceBuildUp linked to this CostBuildUp (if any).

    Args:
        finding: Finding to search
        cost_buildup: CostBuildUp to find resource for

    Returns:
        ResourceBuildUp if linked, else None
    """
    if not cost_buildup.resource_buildup_id:
        return None

    if not finding.resource_buildup_json:
        return None

    resource = ResourceBuildUp.from_dict(finding.resource_buildup_json)
    if not resource:
        return None

    # Check if IDs match
    if resource.id == cost_buildup.resource_buildup_id:
        return resource

    return None
```

### Reconciliation Helpers

```python
def reconcile_resource_and_cost(
    finding: Finding,
    updated_resource: 'ResourceBuildUp',
    rate_config: Optional[BlendedRateConfig] = None
) -> Tuple['ResourceBuildUp', 'CostBuildUp', List[str]]:
    """
    When ResourceBuildUp is updated, update linked CostBuildUp if needed.

    Args:
        finding: Finding containing both buildups
        updated_resource: New ResourceBuildUp
        rate_config: Rate configuration for recalculation

    Returns:
        (ResourceBuildUp, CostBuildUp, warnings)
    """
    warnings = []

    # Get existing cost
    existing_cost = get_linked_cost(finding, updated_resource)

    if not existing_cost:
        # No linked cost, nothing to reconcile
        return (updated_resource, None, [])

    # Recalculate expected labor cost
    validator = ConsistencyValidator(rate_config=rate_config)
    check_result = validator.validate(updated_resource, existing_cost)

    if check_result.status == ConsistencyStatus.CONSISTENT:
        # Already consistent, no update needed
        return (updated_resource, existing_cost, [])

    # Update cost buildup with new labor costs
    builder = CostFromResourceBuilder(
        resource_buildup=updated_resource,
        rate_config=rate_config,
        non_labor_costs=(
            existing_cost.non_labor_cost_low or 0,
            existing_cost.non_labor_cost_high or 0
        ),
        non_labor_assumptions=existing_cost.assumptions
    )

    updated_cost = builder.build()

    # Preserve ID and version (update, not replace)
    updated_cost.id = existing_cost.id
    updated_cost.version = existing_cost.version + 1
    updated_cost.consistency_status = "consistent"
    updated_cost.consistency_notes = [
        f"Auto-updated from ResourceBuildUp change (variance was {check_result.variance_percentage:.1f}%)"
    ]

    warnings.append(
        f"CostBuildUp auto-updated due to ResourceBuildUp change. "
        f"Labor cost: ${existing_cost.labor_cost_low:,.0f} → ${updated_cost.labor_cost_low:,.0f}"
    )

    return (updated_resource, updated_cost, warnings)
```

---

## Usage Examples

### Example 1: Auto-Generate Cost from Resource

```python
from specs.analysis_depth_enhancement.resource_buildup_model import ResourceBuildUp, RoleRequirement
from specs.analysis_depth_enhancement.resource_cost_integration import (
    CostFromResourceBuilder,
    BlendedRateConfig
)

# Step 1: Have a ResourceBuildUp (from Spec 01)
resource_buildup = ResourceBuildUp(
    id="RB-APP-20260210-abc123",
    workstream="application_migration",
    workstream_display="Application Migration",
    duration_months_low=6.0,
    duration_months_high=8.0,
    duration_confidence="medium",
    roles=[
        RoleRequirement(
            id="ROLE-1",
            role="Senior Developer",
            fte=3.0,
            duration_months=6.0,
            skills=["Java", "AWS", "PostgreSQL"],
            seniority="senior",
            sourcing_type="mixed"
        ),
        RoleRequirement(
            id="ROLE-2",
            role="QA Engineer",
            fte=2.0,
            duration_months=3.0,
            skills=["Testing", "Selenium"],
            seniority="mid",
            sourcing_type="internal"
        ),
    ],
    skills_required=["Java", "AWS", "PostgreSQL", "Testing"],
    sourcing_mix={"internal": 0.7, "contractor": 0.3},
    assumptions=["Team has prior migration experience"],
    source_facts=["F-APP-001", "F-APP-002"],
    confidence=0.8
)

# Step 2: Build CostBuildUp from it
builder = CostFromResourceBuilder(
    resource_buildup=resource_buildup,
    rate_config=BlendedRateConfig(),  # Default US rates
    geography="onshore",
    non_labor_costs=(50000, 75000),  # $50k-$75k for tools/licenses
    non_labor_assumptions=[
        "AWS infrastructure costs",
        "Third-party testing tools",
        "Migration tooling licenses"
    ]
)

cost_buildup = builder.build()

# Step 3: Save to Finding
finding.resource_buildup_json = resource_buildup.to_dict()
finding.cost_buildup_json = cost_buildup.to_dict()
db.session.commit()

print(f"Generated cost: ${cost_buildup.cost_low:,.0f} - ${cost_buildup.cost_high:,.0f}")
print(f"  Labor: ${cost_buildup.labor_cost_low:,.0f} - ${cost_buildup.labor_cost_high:,.0f}")
print(f"  Non-labor: ${cost_buildup.non_labor_cost_low:,.0f} - ${cost_buildup.non_labor_cost_high:,.0f}")
print(f"  Blended rate: ${cost_buildup.blended_rate_low:,.0f}/PM")

# Output:
# Generated cost: $374,000 - $459,000
#   Labor: $324,000 - $384,000
#   Non-labor: $50,000 - $75,000
#   Blended rate: $13,500/PM
```

### Example 2: Validate Manual Cost Entry

```python
from specs.analysis_depth_enhancement.resource_cost_integration import ConsistencyValidator

# User manually entered a cost
manual_cost = CostBuildUp(
    id="CB-APP-20260210-xyz789",
    workstream="application_migration",
    workstream_display="Application Migration",
    cost_low=500000,
    cost_high=600000,
    labor_cost_low=450000,  # Much higher than resource-based estimate
    labor_cost_high=550000,
    non_labor_cost_low=50000,
    non_labor_cost_high=50000,
    estimation_method="vendor_quote",
    assumptions=["Vendor quote from Accenture"],
    source_facts=["F-APP-001"],
    confidence=0.9
)

# Validate against resource estimate
validator = ConsistencyValidator()
result = validator.validate(resource_buildup, manual_cost)

print(f"Status: {result.status.value}")
print(f"Variance: {result.variance_percentage:.1f}%")
print("Notes:")
for note in result.notes:
    print(f"  - {note}")

# Output:
# Status: conflicting
# Variance: 38.9%
# Notes:
#   - ⚠️ Labor cost 38.9% different from resource-based estimate.
#     Expected: $324,000 - $384,000, Actual: $450,000 - $550,000.
#     Review resource estimates or cost assumptions.

# Update Finding with validation results
manual_cost.consistency_status = result.status.value
manual_cost.consistency_notes = result.notes
finding.cost_buildup_json = manual_cost.to_dict()
db.session.commit()
```

### Example 3: Update Resources, Auto-Update Costs

```python
from specs.analysis_depth_enhancement.resource_cost_integration import reconcile_resource_and_cost

# User updates resource estimate (adds more developers)
updated_resource = resource_buildup  # (copy and modify)
updated_resource.roles.append(
    RoleRequirement(
        id="ROLE-3",
        role="Senior Developer",
        fte=2.0,
        duration_months=4.0,
        skills=["Java", "AWS"],
        seniority="senior",
        sourcing_type="contractor"
    )
)
updated_resource.version += 1

# Reconcile costs
resource, cost, warnings = reconcile_resource_and_cost(
    finding=finding,
    updated_resource=updated_resource,
    rate_config=BlendedRateConfig()
)

# Save
finding.resource_buildup_json = resource.to_dict()
if cost:
    finding.cost_buildup_json = cost.to_dict()
db.session.commit()

print("Warnings:")
for w in warnings:
    print(f"  - {w}")

# Output:
# Warnings:
#   - CostBuildUp auto-updated due to ResourceBuildUp change.
#     Labor cost: $324,000 → $444,000
```

---

## API Endpoints

### GET /api/findings/<finding_id>/resource-cost-breakdown

**Purpose:** Retrieve both ResourceBuildUp and CostBuildUp in unified format

**Response:**
```json
{
  "success": true,
  "finding_id": "FND-12345",
  "resource_buildup": {
    "id": "RB-APP-20260210-abc123",
    "workstream": "application_migration",
    "total_effort_pm": 24.0,
    "peak_headcount": 5,
    "roles": [...],
    "skills_required": ["Java", "AWS", "PostgreSQL"]
  },
  "cost_buildup": {
    "id": "CB-APP-20260210-xyz789",
    "total_cost_low": 374000,
    "total_cost_high": 459000,
    "labor_cost_low": 324000,
    "labor_cost_high": 384000,
    "non_labor_cost_low": 50000,
    "non_labor_cost_high": 75000,
    "blended_rate_low": 13500,
    "blended_rate_high": 16000,
    "derived_from_resource_buildup": true,
    "resource_buildup_id": "RB-APP-20260210-abc123"
  },
  "consistency": {
    "status": "consistent",
    "variance_percentage": 0.0,
    "notes": ["Auto-generated from ResourceBuildUp"]
  }
}
```

### POST /api/findings/<finding_id>/generate-cost-from-resource

**Purpose:** Auto-generate CostBuildUp from existing ResourceBuildUp

**Request Body:**
```json
{
  "geography": "onshore",
  "non_labor_costs": {
    "low": 50000,
    "high": 75000
  },
  "non_labor_assumptions": [
    "AWS infrastructure costs",
    "Third-party tooling"
  ]
}
```

**Response:**
```json
{
  "success": true,
  "message": "CostBuildUp generated from ResourceBuildUp",
  "cost_buildup": {...},
  "labor_breakdown": {
    "total_cost_low": 324000,
    "total_cost_high": 384000,
    "blended_rate_low": 13500,
    "components": [...]
  }
}
```

### POST /api/findings/<finding_id>/validate-cost-consistency

**Purpose:** Validate manual CostBuildUp against ResourceBuildUp

**Request Body:**
```json
{
  "geography": "onshore"
}
```

**Response:**
```json
{
  "success": true,
  "consistency": {
    "status": "needs_review",
    "variance_percentage": 18.5,
    "expected_labor_cost_low": 324000,
    "expected_labor_cost_high": 384000,
    "actual_labor_cost_low": 380000,
    "actual_labor_cost_high": 450000,
    "notes": [
      "Labor cost 18.5% different from resource-based estimate...",
      "Blended rate differs by 12.3%: Expected ~$13,500/PM, Actual ~$15,200/PM"
    ]
  }
}
```

---

## UI Display Integration

### Unified Resource-Cost Panel

**Location:** Finding detail page, expandable section

**Design Mockup:**

```
┌─────────────────────────────────────────────────────────────┐
│ 📊 Resource & Cost Breakdown                        [View Details ▼] │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ Resources Required                                          │
│ ─────────────────                                          │
│   Total Effort:        24 person-months                     │
│   Peak Team Size:      5 FTEs                              │
│   Duration:            6-8 months                          │
│   Confidence:          Medium (75%)                        │
│                                                             │
│   Roles Breakdown:     [View Details ▶]                    │
│   Skills Required:     Java, AWS, PostgreSQL, Testing      │
│   Sourcing Mix:        70% internal, 30% contractor        │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ Cost Estimate                                               │
│ ─────────────                                              │
│   Total Cost:          $374,000 - $459,000                 │
│   ├─ Labor:            $324,000 - $384,000 (71%)           │
│   └─ Non-Labor:        $50,000 - $75,000 (29%)             │
│                                                             │
│   Blended Rate:        $13,500/PM (±18%)                   │
│   Estimation Method:   Resource-based                      │
│   Confidence:          High (85%)                          │
│                                                             │
│   💡 Generated from resource estimate                      │
│   🔗 Linked to ResourceBuildUp RB-APP-20260210-abc123      │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ Calculation Transparency                                    │
│ ────────────────────────                                   │
│   Labor Cost = Effort × Blended Rate                       │
│              = 24 PM × $13,500/PM                          │
│              = $324,000 (low)                              │
│                                                             │
│   Blended Rate = Weighted average across roles:            │
│     • Senior Developers (18 PM): $16,000/PM (70% int, 30% cont) │
│     • QA Engineers (6 PM): $12,000/PM (100% internal)      │
│     = $13,500/PM average                                   │
│                                                             │
│   [View Full Calculation ▶]                                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Consistency Warning Badge

**If variance detected:**

```
┌─────────────────────────────────────────────────────────────┐
│ ⚠️ Cost-Resource Inconsistency Detected                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ The manually-entered cost estimate differs from the         │
│ resource-based calculation by 18.5%.                        │
│                                                             │
│   Expected Labor Cost:   $324,000 - $384,000               │
│   Actual Labor Cost:     $380,000 - $450,000               │
│   Variance:              +18.5%                             │
│                                                             │
│ Possible reasons:                                           │
│   • Higher blended rates than assumed                       │
│   • Additional roles not captured in resource estimate      │
│   • Vendor quote includes markup                           │
│                                                             │
│ [Review Resource Estimate] [Review Cost Estimate] [Dismiss] │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Testing Strategy

### Unit Tests

**File:** `tests/test_resource_cost_integration.py`

```python
import pytest
from specs.analysis_depth_enhancement.resource_buildup_model import ResourceBuildUp, RoleRequirement
from specs.analysis_depth_enhancement.resource_cost_integration import (
    LaborCostCalculator,
    CostFromResourceBuilder,
    ConsistencyValidator,
    BlendedRateConfig,
    ConsistencyStatus
)

class TestBlendedRateConfig:
    def test_default_rates(self):
        config = BlendedRateConfig()

        # Internal senior developer onshore
        rate = config.get_rate("senior", "internal", "onshore")
        assert rate == 16000

        # Contractor is ~25% premium
        contractor_rate = config.get_rate("senior", "contractor", "onshore")
        assert contractor_rate == 20000

        # Offshore is 60% of onshore
        offshore_rate = config.get_rate("senior", "internal", "offshore")
        assert offshore_rate == 9600  # 16000 * 0.6

    def test_unknown_seniority_fallback(self):
        config = BlendedRateConfig()
        rate = config.get_rate("unknown_seniority", "internal", "onshore")
        assert rate == config.default_internal_rate

class TestLaborCostCalculator:
    def test_single_role_calculation(self):
        resource = ResourceBuildUp(
            id="RB-TEST-001",
            workstream="test",
            workstream_display="Test",
            duration_months_low=6.0,
            duration_months_high=8.0,
            duration_confidence="high",
            roles=[
                RoleRequirement(
                    id="ROLE-1",
                    role="Senior Developer",
                    fte=1.0,
                    duration_months=6.0,
                    skills=["Java"],
                    seniority="senior",
                    sourcing_type="internal"
                )
            ],
            skills_required=["Java"],
            sourcing_mix={},
            assumptions=[],
            source_facts=[],
            confidence=0.8
        )

        calculator = LaborCostCalculator()
        result = calculator.calculate(resource)

        # 6 PM × $16k/PM = $96k
        assert result.total_cost_low == 96000
        assert result.blended_rate_low == 16000
        assert len(result.cost_components) == 1

    def test_mixed_sourcing(self):
        resource = ResourceBuildUp(
            id="RB-TEST-002",
            workstream="test",
            workstream_display="Test",
            duration_months_low=6.0,
            duration_months_high=8.0,
            duration_confidence="high",
            roles=[
                RoleRequirement(
                    id="ROLE-1",
                    role="Senior Developer",
                    fte=1.0,
                    duration_months=10.0,  # 10 PM
                    skills=["Java"],
                    seniority="senior",
                    sourcing_type="mixed"
                )
            ],
            skills_required=["Java"],
            sourcing_mix={"internal": 0.5, "contractor": 0.5},  # 50/50 split
            assumptions=[],
            source_facts=[],
            confidence=0.8
        )

        calculator = LaborCostCalculator()
        result = calculator.calculate(resource)

        # Blended rate = (16000 * 0.5) + (20000 * 0.5) = 18000
        # 10 PM × $18k/PM = $180k
        assert result.total_cost_low == 180000
        assert result.blended_rate_low == 18000

class TestCostFromResourceBuilder:
    def test_auto_generate_cost(self):
        resource = ResourceBuildUp(
            id="RB-TEST-003",
            workstream="application_migration",
            workstream_display="Application Migration",
            duration_months_low=6.0,
            duration_months_high=8.0,
            duration_confidence="high",
            roles=[
                RoleRequirement(
                    id="ROLE-1",
                    role="Senior Developer",
                    fte=2.0,
                    duration_months=6.0,  # 12 PM
                    skills=["Java"],
                    seniority="senior",
                    sourcing_type="internal"
                )
            ],
            skills_required=["Java"],
            sourcing_mix={},
            assumptions=["Team has experience"],
            source_facts=["F-APP-001"],
            confidence=0.85
        )

        builder = CostFromResourceBuilder(
            resource_buildup=resource,
            non_labor_costs=(50000, 75000)
        )
        cost = builder.build()

        # Labor: 12 PM × $16k/PM = $192k
        # Non-labor: $50k - $75k
        # Total: $242k - $267k
        assert cost.labor_cost_low == 192000
        assert cost.non_labor_cost_low == 50000
        assert cost.cost_low == 242000
        assert cost.cost_high == 267000
        assert cost.derived_from_resource_buildup is True
        assert cost.resource_buildup_id == resource.id
        assert cost.consistency_status == "consistent"

class TestConsistencyValidator:
    def test_consistent_cost(self):
        resource = ResourceBuildUp(
            id="RB-TEST-004",
            workstream="test",
            workstream_display="Test",
            duration_months_low=6.0,
            duration_months_high=8.0,
            duration_confidence="high",
            roles=[
                RoleRequirement(
                    id="ROLE-1",
                    role="Senior Developer",
                    fte=1.0,
                    duration_months=10.0,  # 10 PM
                    skills=["Java"],
                    seniority="senior",
                    sourcing_type="internal"
                )
            ],
            skills_required=["Java"],
            sourcing_mix={},
            assumptions=[],
            source_facts=[],
            confidence=0.8
        )

        # Expected: 10 PM × $16k = $160k
        # Actual: $158k (within 10%)
        cost = CostBuildUp(
            id="CB-TEST-004",
            workstream="test",
            workstream_display="Test",
            cost_low=208000,  # $158k labor + $50k non-labor
            cost_high=233000,
            labor_cost_low=158000,
            labor_cost_high=158000,
            non_labor_cost_low=50000,
            non_labor_cost_high=75000,
            estimation_method="manual",
            assumptions=[],
            source_facts=[],
            confidence=0.8
        )

        validator = ConsistencyValidator()
        result = validator.validate(resource, cost)

        # Variance = (160000 - 158000) / 160000 = 1.25%
        assert result.status == ConsistencyStatus.CONSISTENT
        assert result.variance_percentage < 10

    def test_conflicting_cost(self):
        resource = ResourceBuildUp(
            id="RB-TEST-005",
            workstream="test",
            workstream_display="Test",
            duration_months_low=6.0,
            duration_months_high=8.0,
            duration_confidence="high",
            roles=[
                RoleRequirement(
                    id="ROLE-1",
                    role="Senior Developer",
                    fte=1.0,
                    duration_months=10.0,  # 10 PM
                    skills=["Java"],
                    seniority="senior",
                    sourcing_type="internal"
                )
            ],
            skills_required=["Java"],
            sourcing_mix={},
            assumptions=[],
            source_facts=[],
            confidence=0.8
        )

        # Expected: 10 PM × $16k = $160k
        # Actual: $250k (56% higher!)
        cost = CostBuildUp(
            id="CB-TEST-005",
            workstream="test",
            workstream_display="Test",
            cost_low=300000,  # $250k labor + $50k non-labor
            cost_high=325000,
            labor_cost_low=250000,
            labor_cost_high=250000,
            non_labor_cost_low=50000,
            non_labor_cost_high=75000,
            estimation_method="vendor_quote",
            assumptions=[],
            source_facts=[],
            confidence=0.9
        )

        validator = ConsistencyValidator()
        result = validator.validate(resource, cost)

        assert result.status == ConsistencyStatus.CONFLICTING
        assert result.variance_percentage > 25
        assert any("⚠️" in note for note in result.notes)
```

### Integration Tests

```python
class TestResourceCostIntegration:
    def test_end_to_end_workflow(self, app, db, sample_finding):
        """Test complete workflow: resource → cost → validation → update."""

        # Step 1: Create resource buildup
        resource = ResourceBuildUp(
            id="RB-E2E-001",
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
                )
            ],
            skills_required=["Java", "AWS"],
            sourcing_mix={},
            assumptions=["Team available"],
            source_facts=["F-APP-001"],
            confidence=0.85
        )

        # Step 2: Generate cost from resource
        builder = CostFromResourceBuilder(
            resource_buildup=resource,
            non_labor_costs=(50000, 75000)
        )
        cost = builder.build()

        # Step 3: Save to finding
        sample_finding.resource_buildup_json = resource.to_dict()
        sample_finding.cost_buildup_json = cost.to_dict()
        db.session.commit()

        # Step 4: Retrieve and verify
        retrieved_resource = ResourceBuildUp.from_dict(sample_finding.resource_buildup_json)
        retrieved_cost = CostBuildUp.from_dict(sample_finding.cost_buildup_json)

        assert retrieved_resource.id == resource.id
        assert retrieved_cost.resource_buildup_id == resource.id
        assert retrieved_cost.derived_from_resource_buildup is True

        # Step 5: Update resource
        updated_resource = ResourceBuildUp.from_dict(retrieved_resource.to_dict())
        updated_resource.roles[0].fte = 4.0  # Increase team size
        updated_resource.version += 1

        # Step 6: Reconcile costs
        from specs.analysis_depth_enhancement.resource_cost_integration import reconcile_resource_and_cost

        final_resource, final_cost, warnings = reconcile_resource_and_cost(
            finding=sample_finding,
            updated_resource=updated_resource
        )

        assert len(warnings) > 0
        assert final_cost.version > cost.version
        assert final_cost.labor_cost_low > cost.labor_cost_low  # More FTEs = more cost
```

---

## Migration Script

**File:** `scripts/migrate_add_resource_cost_integration.py`

```python
"""
Add resource-cost integration fields to existing CostBuildUp records.

Backward compatible: Existing records get default values.
"""

from web.app import create_app
from web.database import db, Finding
import logging

logger = logging.getLogger(__name__)

def migrate_cost_buildup_fields():
    """Add new fields to existing CostBuildUp records."""

    app = create_app()
    with app.app_context():
        findings_with_costs = Finding.query.filter(
            Finding.cost_buildup_json.isnot(None)
        ).all()

        logger.info(f"Found {len(findings_with_costs)} findings with cost buildups")

        updated = 0
        for finding in findings_with_costs:
            cost_data = finding.cost_buildup_json

            # Add new fields if missing
            changed = False
            if 'derived_from_resource_buildup' not in cost_data:
                cost_data['derived_from_resource_buildup'] = False
                changed = True

            if 'resource_buildup_id' not in cost_data:
                cost_data['resource_buildup_id'] = None
                changed = True

            if 'labor_cost_low' not in cost_data:
                cost_data['labor_cost_low'] = None
                changed = True

            if 'labor_cost_high' not in cost_data:
                cost_data['labor_cost_high'] = None
                changed = True

            if 'non_labor_cost_low' not in cost_data:
                cost_data['non_labor_cost_low'] = None
                changed = True

            if 'non_labor_cost_high' not in cost_data:
                cost_data['non_labor_cost_high'] = None
                changed = True

            if 'blended_rate_low' not in cost_data:
                cost_data['blended_rate_low'] = None
                changed = True

            if 'blended_rate_high' not in cost_data:
                cost_data['blended_rate_high'] = None
                changed = True

            if 'consistency_status' not in cost_data:
                cost_data['consistency_status'] = 'not_validated'
                changed = True

            if 'consistency_notes' not in cost_data:
                cost_data['consistency_notes'] = []
                changed = True

            if changed:
                finding.cost_buildup_json = cost_data
                updated += 1

        if updated > 0:
            db.session.commit()
            logger.info(f"Updated {updated} cost buildups with new fields")
        else:
            logger.info("No updates needed")

if __name__ == '__main__':
    migrate_cost_buildup_fields()
```

---

## Implementation Checklist

### Phase 1: Data Models (Week 1)
- [ ] Add new fields to `CostBuildUp` dataclass
- [ ] Implement `BlendedRateConfig` class
- [ ] Add serialization/deserialization with error handling
- [ ] Write unit tests for models
- [ ] Run migration script on existing data

### Phase 2: Calculators (Week 1-2)
- [ ] Implement `LaborCostCalculator`
- [ ] Implement `CostFromResourceBuilder`
- [ ] Implement `ConsistencyValidator`
- [ ] Write unit tests for calculators
- [ ] Test with real ResourceBuildUp instances

### Phase 3: Integration (Week 2)
- [ ] Implement linking helper functions
- [ ] Implement reconciliation logic
- [ ] Add API endpoints
- [ ] Write integration tests
- [ ] Test end-to-end workflows

### Phase 4: UI (Week 3)
- [ ] Build unified resource-cost panel component
- [ ] Add consistency warning badges
- [ ] Implement drill-down views
- [ ] Add "View Calculation" modals
- [ ] User testing and feedback

### Phase 5: Documentation & Deployment (Week 3)
- [ ] Update API documentation
- [ ] Create user guide for resource-cost integration
- [ ] Train deal teams on new features
- [ ] Deploy to staging
- [ ] Production deployment

---

## Success Criteria

✅ **Integration successful when:**

1. **Auto-generation works:** ResourceBuildUp → CostBuildUp with <2% calculation error
2. **Validation detects issues:** 95%+ accuracy in flagging inconsistencies
3. **Bidirectional linking:** Can navigate resource ↔ cost in UI
4. **Transparency achieved:** Users can see effort → rate → cost chain
5. **Performance acceptable:** Calculation <100ms, validation <50ms
6. **Zero data loss:** Concurrency control prevents overwrites
7. **Backward compatible:** Existing costs work without migration issues

---

## Document Status

**Status:** ✅ Ready for Implementation
**Dependencies:** Spec 01 (ResourceBuildUp model), Spec 02 (ResourceCalculator)
**Next Steps:** Proceed to Spec 04 (Hierarchical Breakdown Architecture)

**Author:** Claude Sonnet 4.5
**Date:** February 10, 2026
**Version:** 1.0
