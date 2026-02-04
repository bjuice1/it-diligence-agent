# Plan: Buyer-Aware Reasoning with Entity Separation

## Objective
Enable reasoning agents to see BUYER facts for comparative/overlap analysis while maintaining strict separation between target and buyer entities.

## Core Principle
**We are doing due diligence on the TARGET, not the buyer.**
- TARGET findings = what's wrong/notable about the target
- BUYER context = reference material for understanding integration implications
- OVERLAP findings = integration work driven by differences between target and buyer

---

## Implementation Plan

### Step 1: Enhance `format_for_reasoning()` in `stores/fact_store.py`

Add a new method that formats BOTH entities with clear separation:

```python
def format_for_reasoning_with_buyer_context(self, domain: str) -> str:
    """
    Format facts for reasoning with both TARGET and BUYER context.

    Structure:
    1. TARGET INVENTORY (primary analysis focus)
    2. BUYER REFERENCE (read-only context for overlap analysis)
    3. ANALYSIS GUARDRAILS (rules for using buyer context)
    """
```

**Output Format:**
```
## TARGET COMPANY INVENTORY
Entity: TARGET
Total Facts: 15
Gaps Identified: 3

### ERP Systems
- [F-TGT-APP-001] SAP ECC 6.0 EHP 6 - Status: active
  Details: 247 custom ABAP programs, single developer
  Evidence: "IT Assessment Report, p.12"

### CRM
- [F-TGT-APP-002] HubSpot Professional - Status: active
  Details: 500 contacts, basic automation
  Evidence: "Application Inventory, p.5"

[... more target facts ...]

---

## BUYER COMPANY REFERENCE (Read-Only Context)
⚠️ PURPOSE: Understand integration implications and overlaps ONLY.
⚠️ DO NOT: Create risks, work items, or recommendations FOR the buyer.

Entity: BUYER
Total Facts: 8

### ERP Systems
- [F-BYR-APP-001] Oracle Cloud ERP - Status: active
  Details: Enterprise license, 500 users

### CRM
- [F-BYR-APP-002] Salesforce Enterprise - Status: active
  Details: 10,000 contacts, full automation suite

[... more buyer facts ...]

---

## OVERLAP ANALYSIS GUIDANCE

When you see differences between TARGET and BUYER systems, consider:

| Target Has | Buyer Has | Implication | Finding Type |
|------------|-----------|-------------|--------------|
| SAP ECC | Oracle Cloud | ERP platform mismatch | Integration Work Item |
| HubSpot | Salesforce | CRM consolidation opportunity | Strategic Consideration |
| On-prem DC | AWS | Infrastructure migration needed | Integration Work Item |
| No SSO | Okta | Identity integration opportunity | Work Item (Day 100) |

### Rules for Overlap-Driven Findings:

1. **Work Items**: Create for TARGET migration/integration work
   - ✅ "Migrate target SAP data to buyer Oracle Cloud"
   - ❌ "Upgrade buyer's Oracle Cloud" (out of scope)

2. **Risks**: Only for TARGET exposure, but can note buyer context
   - ✅ "Target's SAP customizations (F-TGT-APP-001) create migration barriers to buyer's Oracle (F-BYR-APP-001)"
   - ❌ "Buyer's Oracle licensing may be insufficient" (out of scope)

3. **Strategic Considerations**: CAN discuss synergies and overlaps
   - ✅ "CRM consolidation opportunity: Target HubSpot → Buyer Salesforce"
   - ✅ "Platform alignment: Both use AWS, reducing migration complexity"

4. **Recommendations**: Focus on TARGET actions
   - ✅ "Recommend early engagement with SAP on migration licensing"
   - ❌ "Recommend buyer upgrade their systems" (out of scope)
```

---

### Step 2: Update `base_reasoning_agent.py`

Modify the `reason()` method to use the enhanced formatter:

```python
def reason(self, deal_context: Optional[Dict] = None) -> Dict[str, Any]:
    # ...existing code...

    # Check if buyer facts exist for this domain
    buyer_facts = self.fact_store.get_entity_facts("buyer")
    buyer_facts_for_domain = [f for f in buyer_facts if f.domain == self.domain]

    if buyer_facts_for_domain:
        # Use enhanced formatter with buyer context
        inventory_text = self.fact_store.format_for_reasoning_with_buyer_context(self.domain)
        self.logger.info(f"Including {len(buyer_facts_for_domain)} BUYER facts as reference context")
    else:
        # Fall back to target-only (no buyer docs uploaded)
        inventory_text = self.fact_store.format_for_reasoning(self.domain)
```

---

### Step 3: Update Reasoning Prompts

Add a new section to each domain's reasoning prompt. Example for Applications:

**Add to `prompts/v2_applications_reasoning_prompt.py`:**

```python
BUYER_CONTEXT_RULES = """
## BUYER CONTEXT USAGE RULES

You have been provided with BUYER company facts as reference context. Use these rules:

### MUST DO:
- Compare target applications to buyer equivalents for overlap analysis
- Identify consolidation opportunities (target → buyer platform)
- Note platform alignment or misalignment
- Factor buyer environment into integration work item scoping
- Tag findings as `integration_related: true` when they depend on buyer comparison

### MUST NOT DO:
- Create risks FOR the buyer (buyer's issues are out of scope)
- Recommend buyer system changes (we're advising on target acquisition)
- Assume buyer systems are "correct" - they're just the integration target
- Ignore buyer context when it's relevant to integration planning

### CITATION RULES FOR OVERLAP FINDINGS:
When a finding involves both entities, cite BOTH fact IDs:
- based_on_facts: ["F-TGT-APP-001", "F-BYR-APP-001"]
- reasoning: "Target's SAP ECC (F-TGT-APP-001) requires migration to buyer's Oracle Cloud (F-BYR-APP-001)..."

### FINDING CLASSIFICATION:

| Finding Type | Can Reference Buyer? | Example |
|--------------|---------------------|---------|
| Standalone Risk | No (target issue exists regardless) | "SAP ECC 6.0 reaches EOL 2027" |
| Integration Risk | Yes (risk depends on buyer context) | "SAP-to-Oracle migration complexity" |
| Strategic Consideration | Yes (synergies, overlaps) | "CRM consolidation opportunity" |
| Work Item | Yes (integration work) | "Migrate SAP master data to Oracle" |
| Recommendation | Target-focused, can note buyer | "Engage SAP licensing early for migration" |
"""
```

---

### Step 4: Add `integration_related` Field to Findings

Update the dataclasses in `tools_v2/reasoning_tools.py`:

```python
@dataclass
class Risk:
    # ...existing fields...
    integration_related: bool = False  # True if this risk depends on buyer context
    buyer_facts_cited: List[str] = field(default_factory=list)  # F-BYR-xxx IDs

@dataclass
class WorkItem:
    # ...existing fields...
    integration_related: bool = False
    buyer_facts_cited: List[str] = field(default_factory=list)

@dataclass
class StrategicConsideration:
    # ...existing fields...
    integration_related: bool = False
    buyer_facts_cited: List[str] = field(default_factory=list)
```

Update tools to accept these fields:

```python
REASONING_TOOLS = [
    {
        "name": "identify_risk",
        "input_schema": {
            "properties": {
                # ...existing...
                "integration_related": {
                    "type": "boolean",
                    "description": "True if this risk depends on buyer/integration context"
                },
                "buyer_facts_cited": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "F-BYR-xxx fact IDs referenced (if integration_related)"
                }
            }
        }
    },
    # ... update other tools similarly
]
```

---

### Step 5: Fact ID Naming Convention

Ensure fact IDs clearly indicate entity. Update `fact_store.py` ID generation:

```python
def _generate_fact_id(self, domain: str, entity: str) -> str:
    """Generate fact ID with entity prefix for clarity."""
    prefix = "TGT" if entity == "target" else "BYR"
    domain_abbrev = {
        "applications": "APP",
        "infrastructure": "INF",
        "network": "NET",
        "cybersecurity": "SEC",
        "identity_access": "IAM",
        "organization": "ORG"
    }.get(domain, domain[:3].upper())

    count = len([f for f in self.facts if f.entity == entity and f.domain == domain]) + 1
    return f"F-{prefix}-{domain_abbrev}-{count:03d}"
```

**Result:**
- Target facts: `F-TGT-APP-001`, `F-TGT-INF-002`
- Buyer facts: `F-BYR-APP-001`, `F-BYR-INF-002`

This makes it visually obvious which entity a fact belongs to.

---

### Step 6: Output Validation (Optional Enhancement)

Add validation to catch improper buyer fact usage:

```python
def validate_finding_citations(finding, fact_store) -> List[str]:
    """Validate that findings properly cite facts and follow entity rules."""
    warnings = []

    buyer_facts_cited = [f for f in finding.based_on_facts if f.startswith("F-BYR-")]
    target_facts_cited = [f for f in finding.based_on_facts if f.startswith("F-TGT-")]

    # Rule: If citing buyer facts, must also cite target facts (it's a comparison)
    if buyer_facts_cited and not target_facts_cited:
        warnings.append(f"Finding {finding.id} cites buyer facts but no target facts - may be out of scope")

    # Rule: If citing buyer facts, should be marked integration_related
    if buyer_facts_cited and not finding.integration_related:
        warnings.append(f"Finding {finding.id} cites buyer facts but integration_related=False")

    return warnings
```

---

## Files to Modify

| File | Changes |
|------|---------|
| `stores/fact_store.py` | Add `format_for_reasoning_with_buyer_context()`, update ID generation |
| `agents_v2/base_reasoning_agent.py` | Use enhanced formatter when buyer facts exist |
| `tools_v2/reasoning_tools.py` | Add `integration_related`, `buyer_facts_cited` fields |
| `prompts/v2_applications_reasoning_prompt.py` | Add BUYER_CONTEXT_RULES section |
| `prompts/v2_infrastructure_reasoning_prompt.py` | Add BUYER_CONTEXT_RULES section |
| `prompts/v2_network_reasoning_prompt.py` | Add BUYER_CONTEXT_RULES section |
| `prompts/v2_cybersecurity_reasoning_prompt.py` | Add BUYER_CONTEXT_RULES section |
| `prompts/v2_identity_access_reasoning_prompt.py` | Add BUYER_CONTEXT_RULES section |
| `prompts/v2_organization_reasoning_prompt.py` | Add BUYER_CONTEXT_RULES section |

---

## Testing Checklist

- [ ] Upload target-only docs → reasoning works as before (no buyer section)
- [ ] Upload target + buyer docs → reasoning includes buyer context section
- [ ] Verify fact IDs show entity prefix (F-TGT-xxx, F-BYR-xxx)
- [ ] Verify findings that compare systems cite both entity facts
- [ ] Verify no "buyer-only" risks are created (validation catches these)
- [ ] Verify `integration_related` flag is set correctly on overlap findings
- [ ] UI can filter/display integration vs standalone findings

---

## Rollout Strategy

1. **Phase 1**: Implement fact ID naming convention (low risk, immediate clarity)
2. **Phase 2**: Add `format_for_reasoning_with_buyer_context()` method
3. **Phase 3**: Update base_reasoning_agent to use it
4. **Phase 4**: Update all domain reasoning prompts with BUYER_CONTEXT_RULES
5. **Phase 5**: Add `integration_related` field to findings
6. **Phase 6**: Add validation (optional, for quality assurance)

---

## Expected Outcomes

**Before:**
- Reasoning sees only target facts
- Cannot make specific buyer comparisons
- Generic statements like "will need to integrate with buyer environment"

**After:**
- Reasoning sees both entities, clearly separated
- Can make specific comparisons: "Target SAP (F-TGT-APP-001) → Buyer Oracle (F-BYR-APP-001)"
- Findings tagged as integration-related vs standalone
- No accidental buyer-focused findings (out of scope)
