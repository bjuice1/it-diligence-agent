# Reasoning Prompt Conditioning by Deal Type

**Document:** 03-reasoning-prompt-conditioning.md
**Purpose:** Add deal-type-specific instructions to all 6 domain reasoning prompts to guide LLM toward correct M&A lens emphasis
**Status:** Core implementation - Critical P0 fix
**Date:** 2026-02-11
**Depends On:** Doc 01 (deal type taxonomy, M&A lens applicability matrix)

---

## Overview

**Current State (CRITICAL BUG):**
```python
# prompts/v2_applications_reasoning_prompt.py
APPLICATIONS_REASONING_PROMPT = """
...
### The 5 M&A Lenses
| **Separation Complexity** | How entangled? | ...
| **Synergy Opportunity** | Consolidation value? | ...

# ❌ Lists ALL lenses with equal weight
# ❌ No conditional guidance based on deal type
# ❌ LLM applies whichever lens it thinks fits
```

**Target State:**
```python
def get_applications_reasoning_prompt(inventory, deal_context):
    prompt = APPLICATIONS_REASONING_PROMPT

    # NEW: Inject deal-type-specific conditioning
    deal_type = deal_context.get('deal_type', 'acquisition')

    if deal_type in ['carveout', 'divestiture']:
        conditioning = """
        🚨 CRITICAL DEAL TYPE OVERRIDE 🚨
        This is a CARVE-OUT/DIVESTITURE. DO NOT recommend consolidation synergies.

        Focus ONLY on:
        - Separation Complexity (how to stand up standalone systems)
        - TSA Exposure (what services needed from parent)
        - Day-1 Continuity (what must work independently)

        IGNORE: Synergy Opportunity lens (not applicable for separations)
        """
    elif deal_type == 'acquisition':
        conditioning = """
        This is an ACQUISITION. Focus on integration and consolidation.

        Primary lenses:
        - Synergy Opportunity (consolidation value)
        - Day-1 Continuity (operational readiness)
        - Cost Driver (integration costs)

        DE-EMPHASIZE: Separation Complexity, TSA Exposure
        """

    prompt = conditioning + "\n\n" + prompt
    return prompt
```

---

## Architecture

### System-Wide Prompt Injection

```
┌─────────────────────────────────────────────────────────────┐
│ Analysis Runner (web/analysis_runner.py)                    │
│                                                              │
│ deal_context = {                                             │
│     "deal_type": "carveout",  ← From database                │
│     ...                                                      │
│ }                                                            │
└─────────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│ For Each Domain (Applications, Infrastructure, etc.)         │
│                                                              │
│ ┌─────────────────────────────────────────────────────┐    │
│ │ get_*_reasoning_prompt(inventory, deal_context)     │    │
│ │                                                      │    │
│ │ 1. Build base prompt (existing logic)               │    │
│ │ 2. Extract deal_type from deal_context              │    │
│ │ 3. Generate deal-type-specific conditioning         │    │
│ │ 4. Inject conditioning at top of prompt             │    │
│ │ 5. Return modified prompt                           │    │
│ └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│ LLM Reasoning (Claude Sonnet)                                │
│                                                              │
│ Sees conditioning FIRST before base prompt:                  │
│   "🚨 This is a CARVE-OUT. DO NOT recommend consolidation"   │
│                                                              │
│ Then sees normal M&A lens table and instructions            │
│                                                              │
│ Result: Emphasizes correct lenses, ignores irrelevant ones  │
└─────────────────────────────────────────────────────────────┘
```

### Affected Files

**6 Domain Reasoning Prompts (all must be updated):**
1. `prompts/v2_applications_reasoning_prompt.py`
2. `prompts/v2_infrastructure_reasoning_prompt.py`
3. `prompts/v2_network_reasoning_prompt.py`
4. `prompts/v2_cybersecurity_reasoning_prompt.py`
5. `prompts/v2_identity_access_reasoning_prompt.py`
6. `prompts/v2_organization_reasoning_prompt.py`

**Narrative Synthesis (template routing):**
7. `agents_v2/narrative_synthesis_agent.py`

---

## Specification

### Deal-Type-Specific Conditioning Templates

#### Acquisition Conditioning

```python
ACQUISITION_CONDITIONING = """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 DEAL TYPE: ACQUISITION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Strategic Direction: INTEGRATION - Absorb target into buyer's environment
Key Question: "How do we integrate?"

PRIMARY M&A LENSES (Focus here):
✅ Synergy Opportunity - Where can we consolidate and eliminate redundancy?
✅ Day-1 Continuity - What must work immediately for business continuity?
✅ Cost Driver - What are the integration costs?

SECONDARY LENSES (Consider if relevant):
⚠️  Integration Complexity - How difficult will this be?

DE-EMPHASIZE (Usually not relevant for acquisitions):
❌ TSA Exposure - Low priority unless target is itself carved out
❌ Separation Complexity - Not applicable (we're integrating, not separating)

RECOMMENDATIONS SHOULD FOCUS ON:
- Which target systems can be retired (consolidate to buyer's platform)
- What buyer systems target will adopt
- Timeline to migrate target onto buyer infrastructure
- Synergies from eliminating duplicate licenses/systems/teams

DO NOT RECOMMEND:
- Standing up standalone target systems (opposite of integration)
- TSA services from buyer to target (target is being absorbed)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
```

#### Carveout Conditioning

```python
CARVEOUT_CONDITIONING = """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚨 DEAL TYPE: CARVE-OUT (Separation from Parent)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Strategic Direction: SEPARATION - Extract target from parent to operate standalone
Key Question: "How do we stand alone?"

⚠️  CRITICAL: This is NOT an acquisition. Target is LEAVING the parent company.
Entity "buyer" = new owner (may not exist yet), NOT the parent being separated from.

PRIMARY M&A LENSES (Focus here):
✅ TSA Exposure - What services must parent provide during transition?
✅ Separation Complexity - How entangled with parent systems/data?
✅ Day-1 Continuity - What must work independently from Day 1?

SECONDARY LENSES (Consider if relevant):
⚠️  Cost Driver - What are the standup costs?

IGNORE (Not applicable for carveouts):
❌ Synergy Opportunity - There are NO consolidation synergies in a separation
❌ DO NOT recommend consolidating target systems with buyer

RECOMMENDATIONS SHOULD FOCUS ON:
- What standalone systems target needs to build/buy
- Which parent services require TSA (and for how long)
- How to separate commingled data/processes from parent
- Timeline to achieve standalone operations
- Stranded costs that will remain with parent

EXAMPLES OF CORRECT RECOMMENDATIONS:
✅ "Stand up standalone Salesforce instance for target"
✅ "Negotiate 18-month TSA for ERP access from parent"
✅ "Separate target customer data from parent's shared database"

EXAMPLES OF WRONG RECOMMENDATIONS (DO NOT DO THIS):
❌ "Consolidate target's Salesforce onto buyer's instance" (wrong direction)
❌ "Eliminate redundant systems between buyer and target" (no synergies in carveouts)
❌ "Migrate target to buyer's infrastructure" (target needs standalone, not integration)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
```

#### Divestiture Conditioning

```python
DIVESTITURE_CONDITIONING = """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔄 DEAL TYPE: DIVESTITURE (Asset Sale / Clean Separation)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Strategic Direction: CLEAN SEPARATION - Remove target from seller with minimal RemainCo disruption
Key Question: "How do we cleanly separate?"

Note: Focus is on SELLER's perspective (protecting RemainCo operations).

PRIMARY M&A LENSES (Focus here):
✅ Separation Complexity - How to extract target without damaging RemainCo?
✅ Cost Driver - What are the separation/cleanup costs?
✅ RemainCo Impact - How does removing target affect remaining business?

SECONDARY LENSES (Consider if relevant):
⚠️  Day-1 Continuity - Ensure RemainCo operations unaffected
⚠️  TSA Exposure - May provide services to buyer during transition

IGNORE (Usually not known or relevant):
❌ Synergy Opportunity - Buyer may not be known during diligence
❌ Do NOT recommend consolidation (buyer may be unknown)

RECOMMENDATIONS SHOULD FOCUS ON:
- How to separate target data from RemainCo systems
- Which contracts/licenses need to be assigned or split
- Protecting RemainCo operations during separation
- Transition service agreements (TSAs) seller will provide to buyer
- Stranded costs remaining with seller after divestiture

EXAMPLES OF CORRECT RECOMMENDATIONS:
✅ "Separate target's customer data from shared CRM database"
✅ "Split ERP instance to isolate target transactions from RemainCo"
✅ "Renegotiate software licenses to remove target user count"
✅ "Offer 12-month TSA for data center services to buyer"

EXAMPLES OF WRONG RECOMMENDATIONS:
❌ "Consolidate target with buyer's systems" (buyer may be unknown)
❌ "Synergies from combining target and buyer apps" (not applicable)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
```

### Conditioning Injection Function

```python
def get_deal_type_conditioning(deal_type: str) -> str:
    """
    Get deal-type-specific conditioning to inject into reasoning prompts.

    Args:
        deal_type: "acquisition", "carveout", or "divestiture"

    Returns:
        Conditioning text to prepend to reasoning prompt
    """
    # Normalize deal_type
    deal_type = deal_type.lower()

    if deal_type in ['bolt_on', 'platform']:
        deal_type = 'acquisition'
    elif deal_type in ['carve_out', 'carve-out', 'spinoff', 'spin-off']:
        deal_type = 'carveout'
    elif deal_type in ['sale', 'disposal']:
        deal_type = 'divestiture'

    conditioning_map = {
        'acquisition': ACQUISITION_CONDITIONING,
        'carveout': CARVEOUT_CONDITIONING,
        'divestiture': DIVESTITURE_CONDITIONING
    }

    return conditioning_map.get(deal_type, ACQUISITION_CONDITIONING)
```

---

## Implementation Steps

### Step 1: Define Conditioning Templates

**File:** `prompts/shared/deal_type_conditioning.py` (NEW)

```python
"""
Deal-type-specific conditioning for reasoning prompts.

Provides explicit M&A lens guidance based on deal structure.
See specs/deal-type-awareness/03-reasoning-prompt-conditioning.md
"""

ACQUISITION_CONDITIONING = """[Full template from above]"""

CARVEOUT_CONDITIONING = """[Full template from above]"""

DIVESTITURE_CONDITIONING = """[Full template from above]"""

def get_deal_type_conditioning(deal_type: str) -> str:
    """[Full function from above]"""
    ...
```

### Step 2: Update Applications Reasoning Prompt

**File:** `prompts/v2_applications_reasoning_prompt.py`

**Function to modify:** `get_applications_reasoning_prompt(inventory, deal_context)`

```python
def get_applications_reasoning_prompt(inventory, deal_context):
    """Generate applications reasoning prompt with deal-type conditioning."""
    import json
    from prompts.shared.deal_type_conditioning import get_deal_type_conditioning

    # Build base prompt (existing logic)
    inventory_str = json.dumps(inventory, indent=2)
    context_str = json.dumps(deal_context, indent=2)

    prompt = APPLICATIONS_REASONING_PROMPT
    prompt = prompt.replace("{inventory}", inventory_str)
    prompt = prompt.replace("{deal_context}", context_str)

    # NEW: Inject deal-type conditioning
    deal_type = deal_context.get('deal_type', 'acquisition')
    conditioning = get_deal_type_conditioning(deal_type)

    prompt = conditioning + "\n\n" + prompt

    # Inject cost estimation guidance (existing logic)
    cost_guidance = get_cost_estimation_guidance()
    prompt = prompt.replace(
        "## APPLICATIONS PE CONCERNS",
        cost_guidance + "\n" + APPLICATIONS_COST_ANCHORS + "\n\n## APPLICATIONS PE CONCERNS"
    )

    return prompt
```

### Step 3: Update Infrastructure Reasoning Prompt

**File:** `prompts/v2_infrastructure_reasoning_prompt.py`

**Same pattern as Step 2:**

```python
def get_infrastructure_reasoning_prompt(inventory, deal_context):
    """Generate infrastructure reasoning prompt with deal-type conditioning."""
    import json
    from prompts.shared.deal_type_conditioning import get_deal_type_conditioning

    # Build base prompt
    inventory_str = json.dumps(inventory, indent=2)
    context_str = json.dumps(deal_context, indent=2)

    prompt = INFRASTRUCTURE_REASONING_PROMPT
    prompt = prompt.replace("{inventory}", inventory_str)
    prompt = prompt.replace("{deal_context}", context_str)

    # NEW: Inject deal-type conditioning
    deal_type = deal_context.get('deal_type', 'acquisition')
    conditioning = get_deal_type_conditioning(deal_type)

    prompt = conditioning + "\n\n" + prompt

    return prompt
```

### Step 4: Update Network Reasoning Prompt

**File:** `prompts/v2_network_reasoning_prompt.py`

**Same pattern - add conditioning injection to `get_network_reasoning_prompt()`**

### Step 5: Update Cybersecurity Reasoning Prompt

**File:** `prompts/v2_cybersecurity_reasoning_prompt.py`

**Same pattern - add conditioning injection to `get_cybersecurity_reasoning_prompt()`**

### Step 6: Update Identity & Access Reasoning Prompt

**File:** `prompts/v2_identity_access_reasoning_prompt.py`

**Same pattern - add conditioning injection to `get_identity_access_reasoning_prompt()`**

### Step 7: Update Organization Reasoning Prompt

**File:** `prompts/v2_organization_reasoning_prompt.py`

**Same pattern - add conditioning injection to `get_organization_reasoning_prompt()`**

### Step 8: Wire Narrative Synthesis to Deal-Type Templates

**File:** `agents_v2/narrative_synthesis_agent.py`

**Finding from Doc 01:** Templates exist but not wired up.

**Current Status:** Need to locate narrative generation function and add:

```python
from prompts.templates import get_template_for_deal_type

def generate_narrative(deal_context, findings, ...):
    """Generate narrative using deal-type-specific template."""

    deal_type = deal_context.get('deal_type', 'acquisition')

    # NEW: Get correct template
    template_config = get_template_for_deal_type(deal_type)
    template = template_config['template']
    emphasis = template_config['emphasis']

    # Build narrative using selected template
    # ... (rest of logic)
```

**Action Required:** Locate exact function and integration point in `agents_v2/narrative_synthesis_agent.py`

---

## Verification Strategy

### Unit Tests

**Test File:** `tests/unit/test_reasoning_prompt_conditioning.py`

```python
class TestDealTypeConditioning:
    """Test deal-type conditioning injection."""

    def test_get_conditioning_acquisition(self):
        """Acquisition returns acquisition conditioning."""
        conditioning = get_deal_type_conditioning('acquisition')

        assert 'DEAL TYPE: ACQUISITION' in conditioning
        assert 'Synergy Opportunity' in conditioning
        assert 'DO NOT recommend' not in conditioning  # No prohibitions

    def test_get_conditioning_carveout(self):
        """Carveout returns carveout conditioning."""
        conditioning = get_deal_type_conditioning('carveout')

        assert 'CARVE-OUT' in conditioning
        assert 'TSA Exposure' in conditioning
        assert 'DO NOT recommend consolidating' in conditioning
        assert 'CRITICAL' in conditioning  # Emphasizes importance

    def test_get_conditioning_divestiture(self):
        """Divestiture returns divestiture conditioning."""
        conditioning = get_deal_type_conditioning('divestiture')

        assert 'DIVESTITURE' in conditioning
        assert 'RemainCo Impact' in conditioning
        assert 'Separation Complexity' in conditioning

    def test_alias_normalization(self):
        """Deal type aliases map to correct conditioning."""
        assert 'ACQUISITION' in get_deal_type_conditioning('bolt_on')
        assert 'CARVE-OUT' in get_deal_type_conditioning('spinoff')
        assert 'DIVESTITURE' in get_deal_type_conditioning('sale')

    def test_applications_prompt_includes_conditioning(self):
        """Applications reasoning prompt includes conditioning."""
        deal_context = {'deal_type': 'carveout', 'target_name': 'TestCo'}
        inventory = [{'name': 'Salesforce', 'category': 'crm'}]

        prompt = get_applications_reasoning_prompt(inventory, deal_context)

        assert 'CARVE-OUT' in prompt
        assert 'DO NOT recommend consolidating' in prompt
        assert 'TSA Exposure' in prompt

    def test_all_six_prompts_accept_deal_context(self):
        """All 6 domain prompts accept deal_context parameter."""
        deal_context = {'deal_type': 'acquisition'}
        inventory = []

        # Should not raise
        get_applications_reasoning_prompt(inventory, deal_context)
        get_infrastructure_reasoning_prompt(inventory, deal_context)
        get_network_reasoning_prompt(inventory, deal_context)
        get_cybersecurity_reasoning_prompt(inventory, deal_context)
        get_identity_access_reasoning_prompt(inventory, deal_context)
        get_organization_reasoning_prompt(inventory, deal_context)
```

### Integration Tests (LLM Behavior)

**Test File:** `tests/integration/test_llm_deal_type_conditioning.py`

```python
class TestLLMDealTypeConditioning:
    """Test that LLM actually follows deal-type conditioning."""

    @pytest.mark.slow
    @pytest.mark.llm
    def test_carveout_llm_does_not_recommend_consolidation(self, anthropic_api):
        """LLM with carveout conditioning does NOT recommend consolidation."""

        # Setup: Carveout deal with overlapping apps
        deal_context = {
            'deal_type': 'carveout',
            'target_name': 'DivisionX',
            'buyer_name': 'NewOwner'
        }
        inventory = [
            {'name': 'Salesforce (Parent Shared)', 'category': 'crm', 'notes': 'Shared with parent'},
            {'name': 'NetSuite (Parent Shared)', 'category': 'erp', 'notes': 'Shared with parent'}
        ]

        # Generate prompt with conditioning
        prompt = get_applications_reasoning_prompt(inventory, deal_context)

        # Call LLM
        response = anthropic_api.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )

        response_text = response.content[0].text

        # Verify: Should NOT recommend consolidation
        assert 'consolidate' not in response_text.lower() or \
               ('do not consolidate' in response_text.lower())  # Only if prohibiting it

        # Verify: Should recommend standalone
        assert any(term in response_text.lower() for term in ['standalone', 'separate', 'tsa'])

        # Verify: Should mention separation lens
        assert 'separation' in response_text.lower() or 'tsa' in response_text.lower()

    @pytest.mark.slow
    @pytest.mark.llm
    def test_acquisition_llm_recommends_consolidation(self, anthropic_api):
        """LLM with acquisition conditioning recommends consolidation."""

        deal_context = {
            'deal_type': 'acquisition',
            'target_name': 'StartupCo',
            'buyer_name': 'BigCorp'
        }
        inventory = [
            {'name': 'Salesforce (Target)', 'category': 'crm'},
            {'name': 'Salesforce (Buyer)', 'category': 'crm'}  # Overlap
        ]

        prompt = get_applications_reasoning_prompt(inventory, deal_context)

        response = anthropic_api.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )

        response_text = response.content[0].text

        # Verify: Should recommend consolidation
        assert 'consolidate' in response_text.lower() or 'eliminate' in response_text.lower()

        # Verify: Should mention synergy lens
        assert 'synergy' in response_text.lower()
```

### Manual Verification

1. **Create test deal with deal_type="carveout"**

2. **Run discovery + reasoning** on test documents

3. **Read reasoning output** for Applications domain

4. **Verify:**
   - Reasoning output mentions "TSA" or "standalone"
   - Does NOT recommend "consolidate target apps with buyer"
   - Flags systems that need standup

4. **Check logs:**
   - Confirm conditioning was injected into prompt
   - Look for "DEAL TYPE: CARVE-OUT" in logged prompts (if enabled)

---

## Benefits

**Why This Approach:**
1. **Explicit > Implicit:** LLM sees clear instructions, doesn't have to infer
2. **Visual prominence:** Box formatting makes conditioning hard to miss
3. **Examples provided:** Shows LLM both correct and wrong recommendation patterns
4. **Backward compatible:** Defaults to acquisition if deal_type missing
5. **Centralized:** All conditioning templates in single shared module

**Alternatives Considered:**
- ❌ Rely on LLM to infer from deal_context JSON → Too subtle, unreliable
- ❌ Put conditioning at end of prompt → LLM may not weight it as highly
- ✅ Put conditioning at TOP with visual emphasis → LLM sees it first, hard to miss

---

## Expectations

### Success Criteria
- [ ] Conditioning templates created for all 3 deal types
- [ ] All 6 domain reasoning prompts inject conditioning
- [ ] Narrative synthesis wired to template factory
- [ ] Unit tests verify correct conditioning selected
- [ ] LLM integration tests confirm behavior change
- [ ] Manual test shows carveout no longer recommends consolidation

### Measurable Outcomes
- 0% of carveout analyses recommend consolidation (currently ~80%)
- 100% of carveout analyses mention TSA or separation
- LLM follows lens emphasis (tested via 10+ sample prompts)

---

## Risks & Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| LLM ignores conditioning despite prominence | Wrong recommendations persist | Low | Use 🚨 emoji, box formatting, explicit examples to maximize salience |
| Conditioning too restrictive, limits valid recommendations | Miss edge cases | Low | Use "PRIMARY" and "DE-EMPHASIZE" instead of absolute prohibitions |
| Prompt length increases significantly | Token cost increases | Low | Conditioning adds ~200 tokens, acceptable trade-off for correctness |
| Template wiring point not found in narrative agent | Templates still not used | Medium | Doc 01 investigation found status, this doc adds specific integration points |

---

## Results Criteria

### Acceptance Criteria
1. ✅ 3 conditioning templates created with visual formatting
2. ✅ `get_deal_type_conditioning()` function routes to correct template
3. ✅ All 6 domain reasoning prompts inject conditioning
4. ✅ Narrative synthesis calls `get_template_for_deal_type()`
5. ✅ Unit tests pass for all deal types
6. ✅ LLM integration tests show behavior change
7. ✅ Manual verification confirms no consolidation recommendations for carveouts

### Success Metrics
- Carveout test case produces 0 consolidation recommendations
- Acquisition test case produces 3+ consolidation synergies
- All 6 domains use consistent conditioning approach

---

**Document Status:** ✅ COMPLETE

**Version:** 1.0
**Last Updated:** 2026-02-11
**Depends On:** Doc 01 (M&A lens applicability matrix)
**Enables:** Doc 06 (testing), Reasoning agents
