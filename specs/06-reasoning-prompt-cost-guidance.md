# Spec 06: Reasoning Prompt Cost Guidance — Anchor Keys, Examples & Per-Domain Instructions

**Status:** Implemented
**Depends on:** Spec 05 (tool schema supports `cost_buildup`)
**Enables:** Spec 07 (validation that agents produce cost_buildup in practice)

---

## Problem Statement

The `create_work_item` tool now supports `cost_buildup` (Spec 05), but reasoning agents won't use it unless their prompts tell them how. Currently:

- Each domain prompt has a "PE Concerns" section with informal cost ranges (e.g., "$500K-$5M for DC exit")
- No prompt references `anchor_key` values from `COST_ANCHORS`
- No prompt explains the `cost_buildup` object structure
- No worked examples showing how to derive `quantity` from cited facts
- Agents have no guidance on WHEN to use `cost_buildup` vs. just `cost_estimate`

---

## Approach

1. Create a **shared cost estimation guidance component** (`prompts/shared/cost_estimation_guidance.py`) that all 6 domain prompts import
2. Add **domain-specific anchor tables** to each prompt, listing which anchors are most relevant
3. Add **worked examples** showing the complete flow: cited fact → quantity extraction → anchor selection → cost_buildup object
4. Define **when to use vs. skip** cost_buildup

---

## New File: `prompts/shared/cost_estimation_guidance.py`

```python
"""Shared cost estimation guidance for all reasoning domain prompts.

Provides anchor key reference, estimation methods, and worked examples
for the cost_buildup object on create_work_item.
"""

COST_ESTIMATION_GUIDANCE = """
## COST ESTIMATION GUIDANCE

When creating work items, you SHOULD provide a `cost_buildup` object for transparent,
auditable cost estimates. This is in ADDITION to the required `cost_estimate` range.

### When to Provide cost_buildup
- ALWAYS provide it when you have concrete quantities from cited facts (user counts, app counts, site counts)
- ALWAYS provide it for work items with cost_estimate of "100k_to_250k" or higher
- SKIP it only for small, straightforward items where the range is self-evident (e.g., "Buy 5 licenses")

### cost_buildup Structure
```json
{
    "anchor_key": "app_migration_moderate",     // From COST ANCHORS table below
    "quantity": 12,                              // From cited facts
    "unit_label": "applications",                // What the quantity represents
    "source_facts": ["F-TGT-APP-001"],          // Fact IDs that provide the quantity
    "assumptions": [                             // List your assumptions
        "12 applications from F-TGT-APP-001 application inventory",
        "Moderate complexity due to custom integrations"
    ],
    "size_tier": "medium",                       // Only for fixed_by_size anchors
    "notes": "Excludes SAP which requires separate complex migration"
}
```

### Estimation Methods
| Method | When to Use | How to Calculate |
|--------|-------------|------------------|
| `per_user` | License transitions, change management | quantity = user count from facts |
| `per_app` | App migrations, cloud migrations | quantity = app count from facts |
| `per_site` | WAN setup, network work | quantity = site/office count from facts |
| `fixed_by_size` | Identity separation, data segregation | Use size_tier: small (<1000 users), medium (1000-5000), large (>5000) |
| `fixed_by_complexity` | Network separation | Use size_tier: small (simple), medium (moderate), large (complex) |
| `percentage` | PMO overhead | quantity = 1, applied as percentage of total |

### CRITICAL RULES
1. **quantity MUST come from cited facts** — do NOT guess user counts or app counts
2. **source_facts MUST reference real fact IDs** that contain the quantity you're using
3. **If you don't have a concrete quantity, use cost_estimate only** (no cost_buildup)
4. **cost_estimate and cost_buildup should be CONSISTENT** — the buildup total should fall within the estimate range
5. **One anchor per work item** — if a work item spans multiple anchors, split into separate work items

### COST ANCHORS REFERENCE TABLE
| Anchor Key | Name | Unit | Typical Range |
|------------|------|------|---------------|
| `app_migration_simple` | Simple App Migration | per_app | $5K-$25K/app |
| `app_migration_moderate` | Moderate App Migration | per_app | $25K-$100K/app |
| `app_migration_complex` | Complex App Migration | per_app | $100K-$500K/app |
| `license_microsoft` | Microsoft License Transition | per_user | $150-$400/user |
| `license_erp` | ERP License Transition | per_user | $500-$2,000/user |
| `dc_migration` | Data Center Migration | per_dc | $500K-$2M/DC |
| `cloud_migration` | Cloud Migration | per_app | $10K-$100K/app |
| `storage_migration` | Storage Migration | per_tb | $5K-$20K/TB |
| `identity_separation` | Identity Separation | fixed_by_size | $100K-$2M |
| `network_separation` | Network Separation | fixed_by_complexity | $50K-$500K |
| `wan_setup` | WAN Setup | per_site | $10K-$50K/site |
| `security_remediation` | Security Remediation | fixed_by_gaps | $50K-$500K |
| `security_tool_deployment` | Security Tool Deployment | per_endpoint | $30-$80/endpoint |
| `data_segregation` | Data Segregation | fixed_by_size | $100K-$1M |
| `vendor_contract_transition` | Vendor Contract Transition | per_vendor | $5K-$50K/vendor |
| `pmo_overhead` | PMO Overhead | percentage | 10-15% of total |
| `change_management` | Change Management | per_user | $50-$200/user |
| `tsa_exit_identity` | TSA Exit: Identity | fixed_plus_per_user | $100K-$500K |
| `tsa_exit_email` | TSA Exit: Email | per_user | $20-$50/user |
| `tsa_exit_service_desk` | TSA Exit: Service Desk | fixed_plus_per_user | $200K-$800K |
| `tsa_exit_infrastructure` | TSA Exit: Infrastructure | fixed_by_size | $300K-$2M |
| `tsa_exit_network` | TSA Exit: Network | per_site | $20K-$80K/site |
| `tsa_exit_security` | TSA Exit: Security | fixed_by_size | $150K-$600K |
| `tsa_exit_erp_support` | TSA Exit: ERP Support | fixed_by_size | $200K-$1M |
"""

COST_BUILDUP_EXAMPLE_PER_USER = """
### Worked Example: per_user (Microsoft License Transition)
**Fact cited:** F-TGT-APP-023 — "Microsoft 365 E3 licenses for 2,500 users"

```json
{
    "cost_estimate": "500k_to_1m",
    "cost_buildup": {
        "anchor_key": "license_microsoft",
        "quantity": 2500,
        "unit_label": "users",
        "source_facts": ["F-TGT-APP-023"],
        "assumptions": [
            "2,500 users from F-TGT-APP-023",
            "E3 to E3 license transition (no upgrade)",
            "Includes migration tooling and project management"
        ],
        "notes": "Assumes no license tier upgrade; if moving to E5, use license_erp anchor"
    }
}
```
Estimated range: 2,500 × $150-$400 = $375,000 - $1,000,000 → matches cost_estimate "500k_to_1m"
"""

COST_BUILDUP_EXAMPLE_PER_APP = """
### Worked Example: per_app (Application Migration)
**Facts cited:** F-TGT-APP-001 — "47 applications in inventory, 12 rated moderate complexity"

```json
{
    "cost_estimate": "250k_to_500k",
    "cost_buildup": {
        "anchor_key": "app_migration_moderate",
        "quantity": 12,
        "unit_label": "applications",
        "source_facts": ["F-TGT-APP-001"],
        "assumptions": [
            "12 moderate-complexity applications from F-TGT-APP-001",
            "Excludes simple apps (handled separately) and ERP (separate complex migration)",
            "Standard integration testing included"
        ],
        "notes": "12 of 47 total apps; 30 simple apps and 5 complex apps tracked in separate work items"
    }
}
```
Estimated range: 12 × $25,000-$100,000 = $300,000 - $1,200,000 → cost_estimate "250k_to_500k" (conservative)
"""

COST_BUILDUP_EXAMPLE_FIXED_BY_SIZE = """
### Worked Example: fixed_by_size (Identity Separation)
**Facts cited:** F-TGT-IAM-005 — "Single AD forest, 3,200 user accounts"

```json
{
    "cost_estimate": "250k_to_500k",
    "cost_buildup": {
        "anchor_key": "identity_separation",
        "quantity": 1,
        "unit_label": "organization",
        "size_tier": "medium",
        "source_facts": ["F-TGT-IAM-005"],
        "assumptions": [
            "3,200 users = medium tier (1,000-5,000)",
            "Single AD forest simplifies separation",
            "Includes new directory build, user migration, service account remediation"
        ]
    }
}
```
Medium tier range: $300,000 - $800,000 → cost_estimate "250k_to_500k" (lower half of range)
"""

COST_BUILDUP_EXAMPLE_FIXED_BY_COMPLEXITY = """
### Worked Example: fixed_by_complexity (Network Separation)
**Facts cited:** F-TGT-NET-003 — "Flat network, shared VLANs with parent, no documented topology"

```json
{
    "cost_estimate": "250k_to_500k",
    "cost_buildup": {
        "anchor_key": "network_separation",
        "quantity": 1,
        "unit_label": "organization",
        "size_tier": "large",
        "source_facts": ["F-TGT-NET-003"],
        "assumptions": [
            "Complex separation: flat network + shared VLANs + no documentation",
            "Requires full topology discovery before separation can begin",
            "Includes firewall rule migration and testing"
        ]
    }
}
```
"""


def get_cost_estimation_guidance() -> str:
    """Return the full cost estimation guidance block for inclusion in reasoning prompts."""
    return (
        COST_ESTIMATION_GUIDANCE
        + "\n"
        + COST_BUILDUP_EXAMPLE_PER_USER
        + "\n"
        + COST_BUILDUP_EXAMPLE_PER_APP
        + "\n"
        + COST_BUILDUP_EXAMPLE_FIXED_BY_SIZE
        + "\n"
        + COST_BUILDUP_EXAMPLE_FIXED_BY_COMPLEXITY
    )
```

---

## Per-Domain Prompt Updates

### 1. `prompts/v2_infrastructure_reasoning_prompt.py`

**Add after the existing PE Concerns section (line ~530), before Examples:**

```python
# Import at top of file:
from prompts.shared.cost_estimation_guidance import get_cost_estimation_guidance

# In the prompt string, add domain-specific anchor guidance:
INFRASTRUCTURE_COST_ANCHORS = """
### Infrastructure-Specific Cost Anchors
Use these anchor_keys for infrastructure work items:

| Scenario | anchor_key | When to Use |
|----------|------------|-------------|
| Data center exit/migration | `dc_migration` | Moving workloads out of a physical DC |
| Cloud lift-and-shift | `cloud_migration` | Moving apps to IaaS/PaaS |
| Storage migration | `storage_migration` | SAN/NAS data migration (use TB from facts) |
| TSA exit: infrastructure | `tsa_exit_infrastructure` | Standing up independent infra post-carveout |

**Quantity sources for infrastructure:**
- Server count → from F-TGT-INFRA-xxx facts
- Storage TB → from F-TGT-INFRA-xxx details.storage
- Data center count → from F-TGT-INFRA-xxx details.location (unique count)
"""
```

**Inject into `get_infrastructure_reasoning_prompt()`:**

```python
def get_infrastructure_reasoning_prompt(inventory="", deal_context=""):
    cost_guidance = get_cost_estimation_guidance()
    prompt = INFRASTRUCTURE_REASONING_PROMPT.replace(
        "## PE CONCERNS",  # Or wherever appropriate
        cost_guidance + "\n" + INFRASTRUCTURE_COST_ANCHORS + "\n\n## PE CONCERNS"
    )
    # ... existing template injection ...
    return prompt
```

### 2. `prompts/v2_network_reasoning_prompt.py`

**Domain-specific anchors:**

```python
NETWORK_COST_ANCHORS = """
### Network-Specific Cost Anchors
| Scenario | anchor_key | When to Use |
|----------|------------|-------------|
| Network separation from parent | `network_separation` | Carveout: disentangling shared network |
| WAN/SD-WAN per site | `wan_setup` | New connectivity per office/site |
| TSA exit: network | `tsa_exit_network` | Standing up independent network services |

**Quantity sources for network:**
- Site/office count → from F-TGT-NET-xxx or F-TGT-INFRA-xxx location facts
- Complexity → from topology description (flat=complex, segmented=moderate, documented=simple)

**Complexity mapping for network_separation:**
- simple: Segmented network, documented topology, clear boundaries
- moderate: Some shared VLANs, partial documentation
- large/complex: Flat network, no documentation, shared with parent
"""
```

### 3. `prompts/v2_cybersecurity_reasoning_prompt.py`

**Domain-specific anchors:**

```python
CYBERSECURITY_COST_ANCHORS = """
### Cybersecurity-Specific Cost Anchors
| Scenario | anchor_key | When to Use |
|----------|------------|-------------|
| Remediate security gaps | `security_remediation` | Fixing identified vulnerabilities/gaps |
| Deploy security tools (EDR, SIEM) | `security_tool_deployment` | New security tooling rollout |
| TSA exit: security | `tsa_exit_security` | Standing up independent security operations |

**Quantity sources for cybersecurity:**
- Endpoint count → from F-TGT-SEC-xxx or user count (approximate: users × 1.5 devices)
- Gap severity → from gap analysis (minimal=few gaps, moderate=several, significant=many critical)

**Gap severity mapping for security_remediation:**
- small (minimal gaps): MFA exists but coverage <100%, EDR deployed but not tuned
- medium (moderate gaps): No SIEM, partial MFA, vulnerability management immature
- large (significant gaps): No EDR, no MFA on privileged, no vulnerability scanning, no IR plan
"""
```

### 4. `prompts/v2_applications_reasoning_prompt.py`

**Domain-specific anchors:**

```python
APPLICATIONS_COST_ANCHORS = """
### Application-Specific Cost Anchors
| Scenario | anchor_key | When to Use |
|----------|------------|-------------|
| Simple app migration (SaaS reconfig) | `app_migration_simple` | Re-pointing SaaS, SSO updates |
| Moderate app migration (data + config) | `app_migration_moderate` | Data migration, integration rework |
| Complex app migration (ERP, custom) | `app_migration_complex` | ERP migration, heavily customized apps |
| Microsoft license transition | `license_microsoft` | M365 license reassignment/migration |
| ERP license transition | `license_erp` | SAP/Oracle license transfer or repurchase |
| Cloud migration (lift-and-shift) | `cloud_migration` | Moving on-prem apps to cloud |
| Vendor contract transition | `vendor_contract_transition` | Renegotiating/transferring vendor contracts |

**Quantity sources for applications:**
- App count by complexity tier → from application inventory (F-TGT-APP-xxx)
- User count for licenses → from F-TGT-APP-xxx details.users
- Vendor count → count of unique vendors in application inventory

**How to split app migration work items:**
1. Count apps by complexity: simple (SaaS, no custom), moderate (data migration needed), complex (ERP, >50 customizations)
2. Create SEPARATE work items for each tier with appropriate anchor_key
3. Reference the specific apps in each tier via assumptions
"""
```

### 5. `prompts/v2_identity_access_reasoning_prompt.py`

**Domain-specific anchors:**

```python
IDENTITY_COST_ANCHORS = """
### Identity & Access-Specific Cost Anchors
| Scenario | anchor_key | When to Use |
|----------|------------|-------------|
| AD/Azure AD separation | `identity_separation` | New directory + user migration |
| Change management for identity | `change_management` | User communication, training for new identity |
| TSA exit: identity | `tsa_exit_identity` | Standing up independent identity services |
| TSA exit: email | `tsa_exit_email` | Migrating to independent email platform |

**Quantity sources for identity:**
- User count → from F-TGT-IAM-xxx details.users or AD user count
- Size tier → small (<1,000 users), medium (1,000-5,000), large (>5,000)

**Identity separation sizing:**
- small: Single domain, <1,000 users, few service accounts, no multi-forest
- medium: Single forest, 1,000-5,000 users, moderate service accounts, some app integrations
- large: Multi-forest, >5,000 users, many service accounts, complex app/SAML integrations
"""
```

### 6. `prompts/v2_organization_reasoning_prompt.py`

**Domain-specific anchors:**

```python
ORGANIZATION_COST_ANCHORS = """
### Organization-Specific Cost Anchors
| Scenario | anchor_key | When to Use |
|----------|------------|-------------|
| PMO overhead | `pmo_overhead` | Program management for integration (% of total) |
| Change management | `change_management` | User communication, training, adoption |
| TSA exit: service desk | `tsa_exit_service_desk` | Standing up independent helpdesk |
| TSA exit: ERP support | `tsa_exit_erp_support` | Building ERP support team |

**Quantity sources for organization:**
- User count → from organizational facts (headcount, FTE count)
- PMO → quantity=1, percentage method (10-15% of total project cost)

**TSA exit sizing:**
- Service desk size tier based on user count:
  - small: <500 users
  - medium: 500-2,000 users
  - large: >2,000 users
"""
```

---

## Integration Pattern

Each domain prompt file follows the same integration pattern:

```python
# At top of file:
from prompts.shared.cost_estimation_guidance import get_cost_estimation_guidance

# Domain-specific anchor table defined as constant:
DOMAIN_COST_ANCHORS = """..."""

# In the get_<domain>_reasoning_prompt() function:
def get_<domain>_reasoning_prompt(inventory="", deal_context=""):
    cost_guidance = get_cost_estimation_guidance()

    prompt = DOMAIN_REASONING_PROMPT
    # Insert cost guidance before PE Concerns section
    prompt = prompt.replace(
        "## PE CONCERNS",
        cost_guidance + "\n" + DOMAIN_COST_ANCHORS + "\n\n## PE CONCERNS"
    )
    # ... existing template variable injection ...
    return prompt
```

---

## Update `prompts/shared/__init__.py`

**Add the new module to the shared prompt exports:**

```python
from prompts.shared.cost_estimation_guidance import (
    get_cost_estimation_guidance,
    COST_ESTIMATION_GUIDANCE,
    COST_BUILDUP_EXAMPLE_PER_USER,
    COST_BUILDUP_EXAMPLE_PER_APP,
    COST_BUILDUP_EXAMPLE_FIXED_BY_SIZE,
    COST_BUILDUP_EXAMPLE_FIXED_BY_COMPLEXITY,
)
```

---

## Test Cases

### Test 1: Prompt Contains Anchor Reference
```python
def test_infrastructure_prompt_includes_cost_guidance():
    from prompts.v2_infrastructure_reasoning_prompt import get_infrastructure_reasoning_prompt
    prompt = get_infrastructure_reasoning_prompt()
    assert "COST ANCHORS REFERENCE TABLE" in prompt
    assert "dc_migration" in prompt
    assert "cloud_migration" in prompt
    assert "cost_buildup" in prompt
```

### Test 2: All Domains Have Cost Guidance
```python
@pytest.mark.parametrize("module_name,func_name", [
    ("v2_infrastructure_reasoning_prompt", "get_infrastructure_reasoning_prompt"),
    ("v2_network_reasoning_prompt", "get_network_reasoning_prompt"),
    ("v2_cybersecurity_reasoning_prompt", "get_cybersecurity_reasoning_prompt"),
    ("v2_applications_reasoning_prompt", "get_applications_reasoning_prompt"),
    ("v2_identity_access_reasoning_prompt", "get_identity_access_reasoning_prompt"),
    ("v2_organization_reasoning_prompt", "get_organization_reasoning_prompt"),
])
def test_all_prompts_include_cost_guidance(module_name, func_name):
    module = importlib.import_module(f"prompts.{module_name}")
    func = getattr(module, func_name)
    prompt = func()
    assert "COST ANCHORS REFERENCE TABLE" in prompt
    assert "anchor_key" in prompt
    assert "cost_buildup" in prompt
    assert "source_facts" in prompt
```

### Test 3: Domain-Specific Anchors Present
```python
def test_applications_prompt_has_app_anchors():
    from prompts.v2_applications_reasoning_prompt import get_applications_reasoning_prompt
    prompt = get_applications_reasoning_prompt()
    assert "app_migration_simple" in prompt
    assert "app_migration_moderate" in prompt
    assert "app_migration_complex" in prompt
    assert "license_microsoft" in prompt

def test_identity_prompt_has_identity_anchors():
    from prompts.v2_identity_access_reasoning_prompt import get_identity_access_reasoning_prompt
    prompt = get_identity_access_reasoning_prompt()
    assert "identity_separation" in prompt
    assert "tsa_exit_identity" in prompt
    assert "tsa_exit_email" in prompt
```

### Test 4: Worked Examples Present
```python
def test_cost_guidance_includes_examples():
    from prompts.shared.cost_estimation_guidance import get_cost_estimation_guidance
    guidance = get_cost_estimation_guidance()
    assert "Worked Example: per_user" in guidance
    assert "Worked Example: per_app" in guidance
    assert "Worked Example: fixed_by_size" in guidance
    assert "Worked Example: fixed_by_complexity" in guidance
    assert "F-TGT-APP-023" in guidance  # Example fact reference
```

---

## Acceptance Criteria

1. All 6 domain reasoning prompts include the shared cost estimation guidance
2. Each domain prompt includes domain-specific anchor tables with relevant `anchor_key` values
3. Shared guidance includes 4 worked examples (per_user, per_app, fixed_by_size, fixed_by_complexity)
4. Run single-domain analysis → verify >50% of work items include `cost_buildup` with valid `anchor_key`
5. `source_facts` in cost_buildup reference real fact IDs with quantities (not hallucinated)
6. `cost_estimate` and `cost_buildup` totals are consistent (buildup falls within estimate range)
7. New shared module properly exported from `prompts/shared/__init__.py`

---

## Rollback Plan

- Remove `get_cost_estimation_guidance()` call from prompt functions → prompts revert to original text
- Delete `prompts/shared/cost_estimation_guidance.py` → no side effects
- Domain-specific anchor constants are self-contained — deleting them doesn't affect other code

---

## Implementation Notes

*Documented: 2026-02-09*

### 1. Files Modified

**NEW: `prompts/shared/cost_estimation_guidance.py` (189 lines)**
- Lines 1-5: Module docstring
- Lines 7-78: `COST_ESTIMATION_GUIDANCE` constant — anchor reference table (24 anchors), estimation methods table (6 methods), 5 critical rules, `cost_buildup` JSON structure example
- Lines 80-102: `COST_BUILDUP_EXAMPLE_PER_USER` — Microsoft License Transition worked example
- Lines 104-126: `COST_BUILDUP_EXAMPLE_PER_APP` — Application Migration worked example
- Lines 128-150: `COST_BUILDUP_EXAMPLE_FIXED_BY_SIZE` — Identity Separation worked example
- Lines 152-173: `COST_BUILDUP_EXAMPLE_FIXED_BY_COMPLEXITY` — Network Separation worked example
- Lines 176-188: `get_cost_estimation_guidance()` function — concatenates all 5 constants with newline separators

**MODIFIED: `prompts/shared/__init__.py`**
- Lines 109-116: Added import block for `cost_estimation_guidance` (imports `get_cost_estimation_guidance`, `COST_ESTIMATION_GUIDANCE`, and all 4 `COST_BUILDUP_EXAMPLE_*` constants)
- Lines 235-241: Added `__all__` entries under comment `# Cost Estimation Guidance (Spec 06)`

**MODIFIED: `prompts/v2_infrastructure_reasoning_prompt.py`**
- Line 10: Added `from prompts.shared.cost_estimation_guidance import get_cost_estimation_guidance`
- Lines 12-27: Added `INFRASTRUCTURE_COST_ANCHORS` constant with 4 anchor keys (`dc_migration`, `cloud_migration`, `storage_migration`, `tsa_exit_infrastructure`) and quantity source guidance
- Lines 638-665: `get_infrastructure_reasoning_prompt(inventory: dict, deal_context: dict)` — uses `json.dumps` for inventory/deal_context, then `.replace("{inventory}", ...)` and `.replace("{deal_context}", ...)`, then injects cost guidance before `"## INFRASTRUCTURE PE CONCERNS"` via `.replace()`

**MODIFIED: `prompts/v2_network_reasoning_prompt.py`**
- Line 10: Added import
- Lines 12-28: Added `NETWORK_COST_ANCHORS` constant with 3 anchor keys (`network_separation`, `wan_setup`, `tsa_exit_network`) and complexity mapping guidance
- Lines 614-630: `get_network_reasoning_prompt(inventory: dict, deal_context: dict)` — same `.replace()` pattern, injects before `"## NETWORK PE CONCERNS"`

**MODIFIED: `prompts/v2_cybersecurity_reasoning_prompt.py`**
- Line 10: Added import
- Lines 12-28: Added `CYBERSECURITY_COST_ANCHORS` constant with 3 anchor keys (`security_remediation`, `security_tool_deployment`, `tsa_exit_security`) and gap severity mapping
- Lines 603-619: `get_cybersecurity_reasoning_prompt(inventory: dict, deal_context: dict)` — same `.replace()` pattern, injects before `"## CYBERSECURITY PE CONCERNS"`

**MODIFIED: `prompts/v2_applications_reasoning_prompt.py`**
- Line 10: Added import
- Lines 12-33: Added `APPLICATIONS_COST_ANCHORS` constant with 7 anchor keys (`app_migration_simple`, `app_migration_moderate`, `app_migration_complex`, `license_microsoft`, `license_erp`, `cloud_migration`, `vendor_contract_transition`) and app tier splitting guidance
- Lines 616-636: `get_applications_reasoning_prompt(inventory: dict, deal_context: dict)` — same `.replace()` pattern, injects before `"## APPLICATIONS PE CONCERNS"`

**MODIFIED: `prompts/v2_identity_access_reasoning_prompt.py`**
- Line 10: Added import
- Lines 12-29: Added `IDENTITY_COST_ANCHORS` constant with 4 anchor keys (`identity_separation`, `change_management`, `tsa_exit_identity`, `tsa_exit_email`) and identity separation sizing
- Lines 590-606: `get_identity_access_reasoning_prompt(inventory: dict, deal_context: dict)` — same `.replace()` pattern, injects before `"## IDENTITY & ACCESS PE CONCERNS"`

**MODIFIED: `prompts/v2_organization_reasoning_prompt.py`**
- Line 10: Added import
- Lines 12-30: Added `ORGANIZATION_COST_ANCHORS` constant with 4 anchor keys (`pmo_overhead`, `change_management`, `tsa_exit_service_desk`, `tsa_exit_erp_support`) and TSA exit sizing
- Lines 579-595: `get_organization_reasoning_prompt(inventory: dict, deal_context: dict)` — same `.replace()` pattern, injects before `"### Organization PE Concerns"` (note: h3 heading, not h2)

**NEW: `tests/test_cost_prompts.py` (160 lines)**
- See Test Coverage section below

### 2. Deviations from Spec

| Area | Spec Said | Implementation Did | Rationale |
|------|-----------|-------------------|-----------|
| **Function signatures** | `get_<domain>_reasoning_prompt(inventory="", deal_context="")` with string defaults | `get_<domain>_reasoning_prompt(inventory: dict, deal_context: dict)` with dict type hints and no defaults | Functions use `json.dumps()` on the arguments, so dict type is correct; callers always pass both arguments |
| **Template injection** | Spec showed `.format()` for `{inventory}` and `{deal_context}` placeholders | All 6 prompts use `.replace("{inventory}", ...)` and `.replace("{deal_context}", ...)` | Avoids conflicts with JSON curly braces in the prompt template (e.g., worked examples contain `{` and `}` that would break `.format()`) |
| **PE Concerns section header** | Spec used generic `"## PE CONCERNS"` as the `.replace()` target | Each domain uses its own domain-prefixed header: `"## INFRASTRUCTURE PE CONCERNS"`, `"## NETWORK PE CONCERNS"`, `"## CYBERSECURITY PE CONCERNS"`, `"## APPLICATIONS PE CONCERNS"`, `"## IDENTITY & ACCESS PE CONCERNS"` | Matches the actual section headers in each prompt template |
| **Organization injection point** | Spec implied h2-level `## PE CONCERNS` | Organization prompt injects before `"### Organization PE Concerns"` (h3 heading) | The organization prompt uses h3 for this section (nested under buyer-aware reasoning), so the injection target matches the actual heading |
| **Worked example arrows** | Spec used Unicode arrows `→` and multiplication `×` | Implementation uses ASCII `->` and `x` | Avoids potential encoding issues in prompt strings |
| **Test function signatures** | Spec tests called `func()` with no arguments | Test file calls `func(inventory={}, deal_context={})` with empty dicts | Matches actual function signatures that require dict arguments |

### 3. Test Coverage

**File: `tests/test_cost_prompts.py`**

| Class | Methods | Parametrized Cases | What They Verify |
|-------|---------|-------------------|------------------|
| `TestSharedGuidance` | 6 | 0 | Shared guidance content: anchor table present, 4 worked examples present, critical rules present, `cost_buildup` structure explained, estimation methods table present, 9 key anchor keys listed |
| `TestAllDomainsHaveGuidance` | 2 | 12 (6+6) | All 6 domain prompts: (a) generated prompt contains `COST ANCHORS REFERENCE TABLE` and `cost_buildup`, (b) module source code contains `cost_estimation_guidance` import |
| `TestDomainSpecificAnchors` | 7 | 0 | Domain-specific anchors appear in correct prompts: infrastructure has `dc_migration` and `cloud_migration`; applications has `app_migration_simple` and `app_migration_complex`; identity has `identity_separation`; network has `network_separation`; cybersecurity has `security_remediation` and `security_tool_deployment`; organization has `pmo_overhead` |

**Total: 15 test methods producing 25 distinct test cases** (the 2 parametrized methods in `TestAllDomainsHaveGuidance` each expand to 6 cases across the 6 domains).

All tests invoke the actual prompt generation functions with empty dict arguments and verify string containment in the output, confirming end-to-end injection of cost guidance into every domain prompt.
