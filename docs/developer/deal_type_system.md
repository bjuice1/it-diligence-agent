# Deal Type System - Developer Guide

**Version**: 1.0
**Last Updated**: 2025-02-11
**Target Audience**: Developers contributing to the IT DD Agent codebase

---

## Overview

The **deal type system** enables the IT Due Diligence Agent to branch analysis logic based on deal structure:

- **Acquisition (Integration)**: Focus on consolidation synergies, integration planning, cost savings
- **Carve-Out (Separation)**: Focus on separation costs, TSA exposure, standalone build-out
- **Divestiture (Clean Separation)**: Focus on extraction costs, untangling from parent

This guide explains when and how to use `deal_type` in your code.

---

## Core Concept

**The fundamental principle**: Different deal types require fundamentally different recommendations.

### Example: Infrastructure Analysis

```python
# ❌ WRONG: Always recommending consolidation
def analyze_infrastructure(facts):
    return "Recommend consolidating target datacenter to buyer AWS"

# ✅ RIGHT: Conditional on deal_type
def analyze_infrastructure(facts, deal_type: str = "acquisition"):
    if deal_type == 'acquisition':
        return "Recommend consolidating target datacenter to buyer AWS"
    elif deal_type == 'carveout':
        return "Build standalone AWS environment for target (no consolidation)"
    elif deal_type == 'divestiture':
        return "Extract target from parent datacenter to standalone environment"
    else:
        raise ValueError(f"Unknown deal_type: {deal_type}")
```

---

## When to Check deal_type

### Decision Points Where deal_type Matters

| Component | Check deal_type? | Reason |
|-----------|------------------|--------|
| **Discovery agents** | ❌ No | Fact extraction is deal-agnostic |
| **Reasoning agents** | ✅ Yes | Recommendations differ by deal structure |
| **Synergy engine** | ✅ Yes | Consolidation vs. separation logic |
| **Cost engine** | ✅ Yes | Multipliers and TSA costs differ |
| **Work item generation** | ✅ Yes | Integration vs. separation tasks |
| **Narrative generation** | ✅ Yes | Storyline differs by deal type |
| **VDR requests** | ✅ Yes | Different questions for carveouts |

### Quick Reference

**Check `deal_type` if your code:**
- Generates recommendations
- Calculates costs
- Identifies synergies or risks
- Creates work items
- Generates narratives

**Don't check `deal_type` if your code:**
- Extracts facts from documents
- Parses tables or PDFs
- Stores inventory items
- Validates data

---

## How to Use deal_type

### 1. Function Signatures

**Always use `deal_type` as an optional parameter with default `"acquisition"`:**

```python
def calculate_costs(
    work_items: List[WorkItem],
    inv_store: InventoryStore,
    deal_type: str = "acquisition"  # ✅ Optional with default
) -> dict:
    """Calculate total costs based on work items and deal type."""
    pass
```

**Why?** Backward compatibility. Existing code that doesn't pass `deal_type` will default to acquisition behavior.

### 2. Validation

**Always validate deal_type values:**

```python
VALID_DEAL_TYPES = ['acquisition', 'carveout', 'divestiture']

def validate_deal_type(deal_type: str) -> str:
    """Validate and normalize deal_type."""
    if deal_type not in VALID_DEAL_TYPES:
        raise ValueError(
            f"Invalid deal_type: {deal_type}. "
            f"Must be one of: {', '.join(VALID_DEAL_TYPES)}"
        )
    return deal_type
```

### 3. Branching Logic

**Use clear if/elif/else blocks:**

```python
def identify_synergies(inv_store: InventoryStore, deal_type: str = "acquisition"):
    """Identify synergies or separation costs based on deal type."""

    if deal_type == 'acquisition':
        # Integration scenario: consolidation synergies
        return _calculate_consolidation_synergies(inv_store)

    elif deal_type in ['carveout', 'divestiture']:
        # Separation scenario: separation costs
        return _calculate_separation_costs(inv_store, deal_type)

    else:
        raise ValueError(f"Unknown deal_type: {deal_type}")
```

**Prefer explicit over implicit:**
- ✅ `if deal_type == 'acquisition':`
- ❌ `if not deal_type or deal_type == 'acquisition':`

### 4. Logging

**Always log deal_type for debugging:**

```python
import logging
logger = logging.getLogger(__name__)

def calculate_costs(work_items, inv_store, deal_type='acquisition'):
    logger.info(
        f"Cost calculation started: deal_type={deal_type}, "
        f"work_items={len(work_items)}"
    )

    # ... calculation logic ...

    logger.info(
        f"Cost calculation complete: total=${total_cost}, "
        f"multiplier={multiplier}"
    )
```

---

## Common Patterns

### Pattern 1: Conditional Prompts

```python
def get_reasoning_prompt(domain: str, deal_type: str = "acquisition") -> str:
    """Get reasoning prompt template for domain and deal type."""

    base_prompt = REASONING_PROMPTS[domain]

    if deal_type == 'acquisition':
        context = "Focus on integration planning and consolidation synergies."
    elif deal_type == 'carveout':
        context = "Focus on separation costs and standalone capability build-out."
    elif deal_type == 'divestiture':
        context = "Focus on extraction costs and untangling from parent."
    else:
        raise ValueError(f"Unknown deal_type: {deal_type}")

    return f"{base_prompt}\n\n{context}"
```

### Pattern 2: Conditional Cost Multipliers

```python
def get_cost_multiplier(deal_type: str = "acquisition") -> float:
    """Get cost multiplier based on deal type."""

    multipliers = {
        'acquisition': 1.0,      # Baseline
        'carveout': 2.5,         # Higher due to separation complexity
        'divestiture': 1.8       # Moderate due to extraction effort
    }

    return multipliers.get(deal_type, 1.0)
```

### Pattern 3: Conditional Work Items

```python
def generate_work_items(facts: List[Fact], deal_type: str = "acquisition") -> List[WorkItem]:
    """Generate work items based on facts and deal type."""

    work_items = []

    if deal_type == 'acquisition':
        # Integration work items
        work_items.append(WorkItem(
            title="Consolidate target systems to buyer platform",
            phase="Day_100",
            cost_range="100k_to_500k"
        ))

    elif deal_type == 'carveout':
        # Separation work items
        work_items.append(WorkItem(
            title="Build standalone systems for target",
            phase="Day_1",
            cost_range="500k_to_1m"
        ))
        work_items.append(WorkItem(
            title="Negotiate TSA with parent for shared services",
            phase="Day_1",
            cost_range="25k_to_100k"
        ))

    return work_items
```

---

## Testing Checklist

When modifying any analysis component, test with ALL three deal types:

### Unit Test Template

```python
import pytest

class TestYourFunction:
    """Test your function with all deal types."""

    def test_acquisition(self):
        """Test acquisition scenario."""
        result = your_function(data, deal_type='acquisition')
        assert 'consolidation' in result.lower()
        assert 'separation' not in result.lower()

    def test_carveout(self):
        """Test carveout scenario."""
        result = your_function(data, deal_type='carveout')
        assert 'separation' in result.lower()
        assert 'TSA' in result or 'standalone' in result.lower()

    def test_divestiture(self):
        """Test divestiture scenario."""
        result = your_function(data, deal_type='divestiture')
        assert 'extraction' in result.lower() or 'untangle' in result.lower()

    def test_default_to_acquisition(self):
        """Test default behavior (backward compatibility)."""
        result = your_function(data)  # No deal_type parameter
        # Should behave like acquisition
        assert 'consolidation' in result.lower()

    def test_invalid_deal_type(self):
        """Test error handling for invalid deal_type."""
        with pytest.raises(ValueError):
            your_function(data, deal_type='invalid')
```

### Integration Test Template

```python
def test_end_to_end_carveout():
    """Test full pipeline for carveout deal."""

    # Create carveout deal
    deal = Deal(name="Test Carveout", deal_type="carveout")
    db.session.add(deal)
    db.session.commit()

    # Run full analysis
    result = run_analysis(deal_id=deal.id)

    # Verify carveout-specific outputs
    assert any('separation' in s['description'].lower() for s in result['synergies'])
    assert any('TSA' in wi['title'] for wi in result['work_items'])
    assert result['total_cost'] > result_for_equivalent_acquisition['total_cost']
```

---

## Common Pitfalls

### Pitfall 1: Forgetting to Pass deal_type

```python
# ❌ BAD: Calling function without passing deal_type
def reasoning_agent(facts, deal_id):
    work_items = generate_work_items(facts)  # Missing deal_type!
    costs = calculate_costs(work_items)      # Missing deal_type!

# ✅ GOOD: Always pass deal_type
def reasoning_agent(facts, deal_id, deal_type='acquisition'):
    work_items = generate_work_items(facts, deal_type=deal_type)
    costs = calculate_costs(work_items, deal_type=deal_type)
```

### Pitfall 2: Hard-Coding Consolidation Logic

```python
# ❌ BAD: Hard-coded consolidation assumption
def analyze_applications(apps):
    return f"Migrate {len(apps)} applications to buyer platform"

# ✅ GOOD: Conditional logic
def analyze_applications(apps, deal_type='acquisition'):
    if deal_type == 'acquisition':
        return f"Migrate {len(apps)} applications to buyer platform"
    elif deal_type == 'carveout':
        return f"Establish standalone environment for {len(apps)} applications"
```

### Pitfall 3: Inconsistent Validation

```python
# ❌ BAD: Inconsistent validation
def function_a(deal_type):
    if deal_type not in ['acquisition', 'carveout', 'divestiture']:
        raise ValueError("Invalid deal_type")

def function_b(deal_type):
    if deal_type not in ['Acquisition', 'Carveout', 'Divestiture']:  # Different case!
        raise ValueError("Invalid deal_type")

# ✅ GOOD: Use shared validation
from config_v2 import VALID_DEAL_TYPES

def validate_deal_type(deal_type: str) -> str:
    if deal_type not in VALID_DEAL_TYPES:
        raise ValueError(f"Invalid deal_type: {deal_type}")
    return deal_type
```

### Pitfall 4: Missing Logging

```python
# ❌ BAD: No logging (hard to debug)
def calculate_costs(work_items, deal_type='acquisition'):
    multiplier = get_multiplier(deal_type)
    total = sum(wi.cost * multiplier for wi in work_items)
    return total

# ✅ GOOD: Log deal_type and key decisions
def calculate_costs(work_items, deal_type='acquisition'):
    logger.info(f"Calculating costs: deal_type={deal_type}, items={len(work_items)}")
    multiplier = get_multiplier(deal_type)
    logger.debug(f"Using multiplier: {multiplier}")
    total = sum(wi.cost * multiplier for wi in work_items)
    logger.info(f"Total cost: ${total:,.0f}")
    return total
```

---

## Database Considerations

### deal_type Field Constraints

The `deals.deal_type` column has the following constraints:

- **NOT NULL**: Every deal MUST have a deal_type
- **CHECK constraint**: Only 'acquisition', 'carveout', or 'divestiture' allowed
- **Default**: 'acquisition' (for backward compatibility)

### Querying by deal_type

```python
# Get all carveout deals
carveout_deals = Deal.query.filter_by(deal_type='carveout').all()

# Count deals by type
from sqlalchemy import func
deal_counts = db.session.query(
    Deal.deal_type,
    func.count(Deal.id)
).group_by(Deal.deal_type).all()
```

### Migrations

When modifying deal_type logic, always check if a database migration is needed:

```python
# If adding new deal type (e.g., 'merger'):
# 1. Add to VALID_DEAL_TYPES constant
# 2. Update CHECK constraint in migration
# 3. Update all branching logic
# 4. Update tests
```

---

## Code Review Checklist

When reviewing code that touches deal_type:

- [ ] Function accepts `deal_type` parameter (with default 'acquisition')
- [ ] Validation is consistent with `VALID_DEAL_TYPES`
- [ ] Branching logic covers all three deal types
- [ ] Default behavior matches acquisition (backward compatibility)
- [ ] Logging includes `deal_type` for debugging
- [ ] Tests cover all three deal types
- [ ] Tests verify default behavior (no `deal_type` passed)
- [ ] Error handling for invalid `deal_type` values
- [ ] Documentation updated (docstrings, type hints)

---

## Examples from Codebase

### Example 1: Synergy Engine

**File**: `services/synergy_engine.py`

```python
def identify_synergies(inv_store: InventoryStore, deal_type: str = "acquisition") -> List[dict]:
    """
    Identify synergies or separation costs based on deal type.

    Args:
        inv_store: Inventory store with applications, infrastructure, etc.
        deal_type: Type of deal ('acquisition', 'carveout', 'divestiture')

    Returns:
        List of synergy opportunities or separation cost items
    """
    logger.info(f"Identifying synergies for deal_type={deal_type}")

    if deal_type == 'acquisition':
        return _calculate_consolidation_synergies(inv_store)
    elif deal_type in ['carveout', 'divestiture']:
        return _calculate_separation_costs(inv_store, deal_type)
    else:
        raise ValueError(f"Invalid deal_type: {deal_type}")
```

### Example 2: Cost Service

**File**: `services/cost_service.py`

```python
def calculate_all_costs(
    inv_store: InventoryStore,
    fact_store: FactStore,
    deal_type: str = "acquisition"
) -> dict:
    """Calculate total costs with deal-type-aware multipliers."""

    base_costs = _calculate_base_costs(inv_store, fact_store)

    # Apply deal-type-specific multiplier
    multiplier = COST_MULTIPLIERS.get(deal_type, 1.0)

    # Add TSA costs for carveouts
    tsa_costs = 0
    if deal_type == 'carveout':
        tsa_costs = _calculate_tsa_costs(inv_store)

    return {
        'base_costs': base_costs,
        'multiplier': multiplier,
        'tsa_costs': tsa_costs,
        'total_cost': base_costs * multiplier + tsa_costs
    }
```

### Example 3: Reasoning Agent

**File**: `agents_v2/reasoning/infrastructure_reasoning.py`

```python
def run_infrastructure_reasoning(
    facts: List[Fact],
    deal_type: str = "acquisition"
) -> dict:
    """Run infrastructure reasoning with deal-type-specific prompts."""

    prompt = get_reasoning_prompt('infrastructure', deal_type)

    # Call LLM
    response = client.messages.create(
        model=REASONING_MODEL,
        messages=[{"role": "user", "content": prompt}],
        # ... other params ...
    )

    # Parse response
    findings = parse_findings(response.content)

    logger.info(
        f"Infrastructure reasoning complete: deal_type={deal_type}, "
        f"findings={len(findings)}"
    )

    return findings
```

---

## Performance Considerations

### No Performance Impact on Discovery

Discovery agents do NOT check `deal_type`, so fact extraction performance is unchanged.

### Minimal Impact on Reasoning

Reasoning agents check `deal_type` once at the start, so performance impact is negligible (<1ms per check).

### Caching Considerations

If caching analysis results, include `deal_type` in cache key:

```python
cache_key = f"analysis:{deal_id}:{deal_type}:{timestamp}"
```

---

## Future Enhancements

### Potential Future Deal Types

If adding new deal types (e.g., 'merger', 'joint_venture'):

1. Add to `VALID_DEAL_TYPES` constant
2. Update database CHECK constraint (requires migration)
3. Update all branching logic in:
   - Synergy engine
   - Cost engine
   - Reasoning agents
   - Narrative agents
4. Add tests for new deal type
5. Update user documentation

### Type Safety

Consider using Enum for type safety:

```python
from enum import Enum

class DealType(str, Enum):
    ACQUISITION = "acquisition"
    CARVEOUT = "carveout"
    DIVESTITURE = "divestiture"

def calculate_costs(deal_type: DealType = DealType.ACQUISITION) -> dict:
    # Type checker ensures only valid values
    pass
```

---

## Getting Help

**Questions about deal_type system?**

- Check this guide first
- Review existing code examples (grep for `deal_type` in codebase)
- Ask in team Slack: #it-dd-dev
- Contact: engineering-lead@example.com

**Found a bug?**

- Create GitHub issue with `deal_type` label
- Include: deal type, expected behavior, actual behavior, reproduction steps

**Want to extend the system?**

- Review this guide
- Write RFC (Request for Comments) for major changes
- Submit PR with tests covering all deal types

---

## Quick Reference Card

```
┌─────────────────────────────────────────────────────────────┐
│ DEAL TYPE SYSTEM - QUICK REFERENCE                          │
├─────────────────────────────────────────────────────────────┤
│ Valid Values:    acquisition | carveout | divestiture       │
│ Default:         acquisition (for backward compatibility)    │
│ Constraint:      NOT NULL + CHECK in database               │
├─────────────────────────────────────────────────────────────┤
│ WHEN TO CHECK:                                              │
│   ✅ Reasoning agents                                       │
│   ✅ Synergy engine                                         │
│   ✅ Cost engine                                            │
│   ✅ Work item generation                                   │
│   ✅ Narratives                                             │
│   ❌ Discovery agents (deal-agnostic)                       │
├─────────────────────────────────────────────────────────────┤
│ FUNCTION SIGNATURE:                                         │
│   def your_function(data, deal_type: str = "acquisition"):  │
│       # Always validate                                     │
│       if deal_type not in VALID_DEAL_TYPES:                 │
│           raise ValueError(...)                             │
│       # Always log                                          │
│       logger.info(f"deal_type={deal_type}")                 │
│       # Branch logic                                        │
│       if deal_type == 'acquisition': ...                    │
├─────────────────────────────────────────────────────────────┤
│ TESTING:                                                    │
│   • Test with all 3 deal types                             │
│   • Test default (no parameter)                            │
│   • Test invalid value raises error                        │
└─────────────────────────────────────────────────────────────┘
```

---

**End of Developer Guide**
