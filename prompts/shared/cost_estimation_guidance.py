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
Estimated range: 2,500 x $150-$400 = $375,000 - $1,000,000 -> matches cost_estimate "500k_to_1m"
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
Estimated range: 12 x $25,000-$100,000 = $300,000 - $1,200,000 -> cost_estimate "250k_to_500k" (conservative)
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
Medium tier range: $300,000 - $800,000 -> cost_estimate "250k_to_500k" (lower half of range)
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
