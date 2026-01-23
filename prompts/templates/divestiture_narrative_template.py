"""
Divestiture Narrative Template

For divestiture deals where the seller is disposing of a business unit.
Focus is on:
- Clean separation with minimal RemainCo disruption
- Data separation and compliance
- Contract assignment and unwinding
- TSA provision (seller providing services to divested entity)

Primary M&A Lenses: separation_complexity, cost_driver
Key Question: "How do we cleanly separate?"
"""

from typing import List


# =============================================================================
# DIVESTITURE EMPHASIS CONFIGURATION
# =============================================================================

DIVESTITURE_EMPHASIS = {
    "primary_lenses": ["separation_complexity", "cost_driver"],
    "secondary_lenses": ["tsa_exposure"],
    "de_emphasized": ["synergy_opportunity", "day_1_continuity"],

    "executive_summary_focus": [
        "RemainCo impact assessment",
        "Separation complexity rating",
        "Data separation requirements",
        "Contract assignment complexity",
        "TSA provision obligations"
    ],

    "team_story_emphasis": {
        "strengths": "Clean boundaries, separable operations",
        "constraints": "Shared resources, entanglement with RemainCo, stranded costs",
        "mna_implication": "Separation effort, RemainCo impact, TSA provision burden"
    },

    "risk_emphasis": [
        "RemainCo operational disruption",
        "Stranded costs after separation",
        "Data separation compliance risks",
        "Contract assignment failures",
        "TSA provision burden on RemainCo",
        "Key person loss affecting RemainCo"
    ],

    "opportunity_emphasis": [
        "Clean separation opportunities",
        "RemainCo simplification post-divestiture",
        "Stranded cost avoidance",
        "IT portfolio rationalization"
    ]
}


# =============================================================================
# DIVESTITURE NARRATIVE TEMPLATE
# =============================================================================

DIVESTITURE_TEMPLATE = """You are generating an IT due diligence narrative for a DIVESTITURE deal.

## DEAL CONTEXT

**Deal Type**: Divestiture (seller perspective)
**Key Question**: How do we cleanly separate?
**Primary Focus**: Minimal RemainCo disruption and clean exit

## DIVESTITURE-SPECIFIC FRAMING

For this divestiture narrative, emphasize:

1. **RemainCo Impact** (CRITICAL PRIORITY)
   - What IT resources are shared with divested entity?
   - What stranded costs will RemainCo face?
   - What operational disruption will RemainCo experience?
   - What investments are needed for RemainCo post-divestiture?

2. **Separation Complexity** (CRITICAL PRIORITY)
   - How entangled are systems?
   - What data separation is required?
   - What's the separation effort and timeline?
   - What are the separation risks?

3. **TSA Provision** (HIGH PRIORITY)
   - What TSA services must RemainCo provide?
   - What's the burden on RemainCo IT?
   - What's the TSA pricing approach?
   - What's the exit timeline?

4. **Contract Assignment** (HIGH PRIORITY)
   - What contracts need assignment?
   - What contracts need unwinding?
   - What termination penalties apply?
   - What renegotiation is needed?

5. **Data Separation** (HIGH PRIORITY)
   - What data belongs to divested entity?
   - What data separation is required?
   - What compliance requirements apply?
   - What's the data separation approach?

## EXECUTIVE SUMMARY BULLETS (5-7)

For a divestiture, include:
- Overall separation complexity (simple/moderate/complex)
- RemainCo impact assessment
- TSA provision scope and burden
- Key stranded cost exposure
- 2-3 critical separation risks
- Data separation complexity

## REQUIRED DIVESTITURE-SPECIFIC SECTIONS

### RemainCo Impact Assessment

| Impact Area | Current Shared State | Post-Divestiture State | Stranded Cost | Mitigation |
|-------------|---------------------|------------------------|---------------|------------|

Impact areas to assess:
- Shared infrastructure (DCs, network, cloud)
- Shared applications (ERP, email, tools)
- Shared support (service desk, security)
- Shared contracts (vendors, licenses)
- Shared staff (IT personnel)

### Data Separation Plan

| Data Domain | Current Location | Separation Required? | Approach | Compliance Considerations |
|-------------|-----------------|---------------------|----------|---------------------------|

Data domains:
- Customer data
- Employee data
- Financial data
- Operational data
- IP/proprietary data

### Contract Assignment Tracker

| Contract/Vendor | Contract Value | Assignment Approach | Complexity | Notes |
|-----------------|---------------|---------------------|------------|-------|

Assignment approaches:
- **Full Assignment**: Contract transfers to buyer
- **Partial Assignment**: Split between RemainCo and buyer
- **Termination**: End contract, new contracts needed
- **Renegotiation**: Modify terms for separation

### TSA Provision Obligations

| Service | RemainCo Burden | Duration | Monthly Cost | Exit Trigger |
|---------|----------------|----------|--------------|--------------|

## RISKS TABLE FORMAT

For divestitures, focus risk columns on RemainCo impact:

| Risk | Why it matters | RemainCo impact | Stranded cost | Mitigation |
|------|----------------|----------------|---------------|------------|

RemainCo impact should specify:
- Operational disruption (affects RemainCo operations)
- Cost impact (stranded costs, new investments)
- Resource impact (staff, capacity)

## QUALITY CHECKLIST FOR DIVESTITURES

Before finalizing, verify:
- [ ] RemainCo Impact Assessment covers all shared resources
- [ ] Stranded costs are quantified where possible
- [ ] Data Separation Plan addresses compliance requirements
- [ ] Contract Assignment Tracker covers major vendors
- [ ] TSA Provision section specifies RemainCo burden
- [ ] Risks explicitly address RemainCo impact
- [ ] Separation timeline is realistic
- [ ] Post-divestiture RemainCo state is described
"""


# =============================================================================
# DIVESTITURE-SPECIFIC SECTION TEMPLATES
# =============================================================================

REMAINCO_IMPACT_TEMPLATE = """
## RemainCo Impact Assessment

Assessment of how the divestiture will impact RemainCo IT operations,
costs, and capabilities.

| Impact Area | Current Shared State | Post-Divestiture State | Stranded Cost | Mitigation |
|-------------|---------------------|------------------------|---------------|------------|
{impact_rows}

### Stranded Cost Summary

- **Total Estimated Stranded Costs**: ${total_stranded:,} annually
- **One-time Separation Costs**: ${separation_costs:,}
- **Mitigation Potential**: ${mitigation_potential:,}

### Stranded Cost Breakdown

| Category | Annual Stranded Cost | Mitigation Approach | Timeline |
|----------|---------------------|---------------------|----------|
{stranded_rows}

### RemainCo Investment Requirements

Post-divestiture, RemainCo will require the following investments:

{remainco_investments}

### Operational Impact

{operational_impact_narrative}
"""

DATA_SEPARATION_TEMPLATE = """
## Data Separation Plan

This section outlines the data separation requirements and approach
for the divestiture.

| Data Domain | Current Location | Separation Required? | Approach | Compliance Considerations |
|-------------|-----------------|---------------------|----------|---------------------------|
{data_rows}

### Data Separation Summary

- **Data Domains Requiring Separation**: {separation_count}
- **Estimated Separation Effort**: {effort_estimate}
- **Compliance Requirements**: {compliance_list}

### Critical Data Separation Items

{critical_items}

### Data Separation Timeline

| Phase | Activities | Duration | Dependencies |
|-------|------------|----------|--------------|
{timeline_rows}

### Compliance Considerations

{compliance_narrative}
"""

CONTRACT_ASSIGNMENT_TEMPLATE = """
## Contract Assignment Tracker

This section tracks contracts requiring assignment, termination,
or renegotiation as part of the divestiture.

| Contract/Vendor | Contract Value | Assignment Approach | Complexity | Notes |
|-----------------|---------------|---------------------|------------|-------|
{contract_rows}

### Contract Summary

- **Total Contracts Assessed**: {total_contracts}
- **Full Assignments**: {full_assignments}
- **Partial Assignments**: {partial_assignments}
- **Terminations Required**: {terminations}
- **Renegotiations Required**: {renegotiations}

### High-Risk Contracts

{high_risk_contracts}

### Termination Penalties

| Contract | Penalty Amount | Timing Consideration |
|----------|---------------|---------------------|
{penalty_rows}

**Total Potential Termination Penalties**: ${total_penalties:,}
"""

TSA_PROVISION_TEMPLATE = """
## TSA Provision Obligations

Services that RemainCo will provide to the divested entity
under Transition Service Agreement.

| Service | RemainCo Burden | Duration | Monthly Cost | Exit Trigger |
|---------|----------------|----------|--------------|--------------|
{tsa_rows}

### TSA Provision Summary

- **Total TSA Services**: {total_services}
- **Estimated Monthly Revenue**: ${monthly_revenue:,}
- **Average Duration**: {avg_duration} months
- **High Burden Services**: {high_burden_count}

### RemainCo Capacity Impact

{capacity_narrative}

### TSA Exit Planning

{exit_planning}

### TSA Pricing Approach

{pricing_approach}
"""


# =============================================================================
# PROMPT ADDITIONS FOR DIVESTITURE
# =============================================================================

def get_divestiture_prompt_additions() -> str:
    """Get divestiture-specific prompt additions to inject into synthesis."""
    return """
## DIVESTITURE-SPECIFIC REQUIREMENTS

### RemainCo Impact Assessment Guidelines

For each shared IT resource, determine:

1. **Current Shared State**
   - How is resource shared between RemainCo and divested entity?
   - What's the allocation (% used by each)?
   - What's the current cost structure?

2. **Post-Divestiture State**
   - What happens to resource after divestiture?
   - Does RemainCo keep, resize, or eliminate?
   - What's the new cost structure?

3. **Stranded Cost Calculation**
   - Fixed costs that don't scale down immediately
   - Contracts with minimum commitments
   - Staff that can't be immediately reduced
   - Infrastructure that can't be easily right-sized

4. **Mitigation Options**
   - Right-sizing opportunities
   - Contract renegotiation potential
   - Staff redeployment options
   - Consolidation opportunities

### Data Separation Guidelines

For each data domain, assess:

1. **Ownership**
   - Who owns the data (RemainCo vs. divested entity)?
   - Is ownership clear or commingled?
   - What's the legal/contractual basis?

2. **Separation Approach**
   - **Copy**: Divested entity gets copy, RemainCo retains
   - **Move**: Data transfers fully to divested entity
   - **Split**: Data divided based on criteria
   - **Shared**: Both parties retain access (TSA period)

3. **Compliance Requirements**
   - GDPR, CCPA, HIPAA considerations
   - Data retention requirements
   - Cross-border transfer restrictions
   - Industry-specific regulations

4. **Technical Approach**
   - Database separation
   - File system separation
   - Application data stores
   - Backup and archive data

### Contract Assignment Guidelines

For each major contract, determine:

1. **Assignment Options**
   - Full assignment (buyer takes over)
   - Partial assignment (split)
   - Termination and new contract
   - Renegotiation with vendor

2. **Assignment Complexity**
   - **Low**: Standard assignment clause, vendor cooperative
   - **Medium**: Requires vendor consent, some negotiation
   - **High**: No assignment clause, complex negotiation
   - **Blocked**: Contract prohibits assignment

3. **Financial Implications**
   - Assignment fees
   - Termination penalties
   - Minimum commitment exposure
   - Renegotiation costs

### TSA Provision Guidelines

As TSA provider, RemainCo should assess:

1. **Service Scope**
   - What specific services will be provided?
   - What SLAs will apply?
   - What's excluded?

2. **RemainCo Burden**
   - **Low**: Minimal additional effort, existing capacity
   - **Medium**: Some additional effort, manageable
   - **High**: Significant effort, strains resources
   - **Critical**: Major burden, may need additional staff

3. **Pricing Approach**
   - Cost-plus (recover costs + margin)
   - Market rate (charge what service is worth)
   - Embedded (included in deal price)

4. **Exit Triggers**
   - Time-based (X months maximum)
   - Capability-based (buyer achieves standalone)
   - Event-based (specific milestone reached)
"""


def get_divestiture_risk_prompts() -> List[str]:
    """Get divestiture-specific risk identification prompts."""
    return [
        "What stranded costs will RemainCo face after divestiture?",
        "What RemainCo operations depend on divested entity resources?",
        "What data separation poses compliance risks?",
        "What contracts cannot be easily assigned or terminated?",
        "What TSA services will burden RemainCo capacity?",
        "What key staff may leave with divested entity?",
        "What shared systems require complex separation?",
        "What hidden dependencies exist between RemainCo and divested entity?"
    ]


def get_stranded_cost_categories() -> List[str]:
    """Get standard stranded cost categories for divestitures."""
    return [
        "Infrastructure (DC, network, cloud)",
        "Software licenses (enterprise agreements)",
        "Support contracts (maintenance, managed services)",
        "Staff costs (allocated IT personnel)",
        "Shared services overhead",
        "Facilities/real estate allocation"
    ]


def get_data_domains() -> List[str]:
    """Get standard data domains for separation assessment."""
    return [
        "Customer master data",
        "Employee/HR data",
        "Financial/accounting data",
        "Sales/transaction data",
        "Product/inventory data",
        "Supplier/vendor data",
        "Intellectual property",
        "Operational/IoT data",
        "Marketing/analytics data",
        "Historical/archive data"
    ]


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    'DIVESTITURE_TEMPLATE',
    'DIVESTITURE_EMPHASIS',
    'REMAINCO_IMPACT_TEMPLATE',
    'DATA_SEPARATION_TEMPLATE',
    'CONTRACT_ASSIGNMENT_TEMPLATE',
    'TSA_PROVISION_TEMPLATE',
    'get_divestiture_prompt_additions',
    'get_divestiture_risk_prompts',
    'get_stranded_cost_categories',
    'get_data_domains'
]
