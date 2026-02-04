# Plan: Reasoning Prompts Update (PE-Grade)

## Why This Matters

The reasoning prompts are where we translate raw facts into PE-actionable insights. Bad prompts → generic findings that don't help deal teams. Good prompts → specific, costed, phased work that ICs can act on.

This plan defines **exactly what each domain prompt needs** to produce PE-grade outputs.

---

## The 6 Domain Prompts to Update

| File | Domain | Key PE Concerns |
|------|--------|-----------------|
| `v2_infrastructure_reasoning_prompt.py` | Infrastructure | DC exit, cloud alignment, compute refresh |
| `v2_network_reasoning_prompt.py` | Network | WAN consolidation, connectivity, firewall policy |
| `v2_cybersecurity_reasoning_prompt.py` | Cybersecurity | Security tool consolidation, compliance gaps |
| `v2_applications_reasoning_prompt.py` | Applications | ERP/CRM consolidation, licensing, custom apps |
| `v2_identity_access_reasoning_prompt.py` | Identity | AD consolidation, SSO, PAM, JML processes |
| `v2_organization_reasoning_prompt.py` | Organization | Team structure, key person risk, TSA staffing |

---

## Standard Sections for ALL Prompts

Every reasoning prompt will get these standard sections:

### Section 1: Overlap Map Instruction (New)

```markdown
## STEP 1: GENERATE OVERLAP MAP (Required)

Before creating ANY findings, you MUST call `generate_overlap_map` to compare TARGET vs BUYER systems.

For each category where both entities have facts, create an overlap candidate:
- What does TARGET have? (cite F-TGT-xxx)
- What does BUYER have? (cite F-BYR-xxx)
- What type of overlap? (platform_mismatch, capability_gap, etc.)
- Why does this matter for integration?
- What questions would increase confidence?

This forces you to "show your work" before making conclusions.

If NO buyer facts exist for this domain, skip this step and focus on target-standalone analysis.
```

### Section 2: 3-Layer Output Structure (New)

```markdown
## OUTPUT STRUCTURE (Required)

Organize your findings into three distinct layers:

### LAYER 1: TARGET STANDALONE
Findings about the target that exist REGARDLESS of buyer identity.
- These risks/issues would matter even if target stayed independent
- Do NOT reference buyer facts (F-BYR-xxx)
- Set `risk_scope: "target_standalone"` or `integration_related: false`

Examples:
- "VMware 6.7 reaches EOL April 2025" (technical debt)
- "Single IT admin manages all infrastructure" (key person risk)
- "No documented DR plan exists" (operational risk)

### LAYER 2: OVERLAP FINDINGS
Findings that DEPEND ON buyer context for meaning.
- Must reference BOTH target AND buyer facts
- Must link to an overlap_id from your overlap map
- Set `risk_scope: "integration_dependent"` or `integration_related: true`

Examples:
- "Target uses AWS, Buyer uses Azure → cloud migration required"
- "Both have Salesforce → consolidation opportunity"
- "Target AD forest incompatible with Buyer's Okta → identity rearchitecture"

### LAYER 3: INTEGRATION WORKPLAN
Work items with separated target vs integration actions.

For EACH work item, provide:
- `target_action`: What TARGET must do (always required)
- `integration_option`: Buyer-dependent path (optional)

Example:
```json
{
  "title": "Cloud Platform Migration Assessment",
  "target_action": "Inventory AWS workloads; document dependencies; assess lift-and-shift readiness",
  "integration_option": "If buyer confirms Azure as target state, add landing zone design (+8 weeks)"
}
```
```

### Section 3: Tone Control (New)

```markdown
## BUYER CONTEXT RULES

Buyer facts describe ONE POSSIBLE destination state, not a standard.

**USE buyer context to:**
- Explain integration complexity (what makes migration hard/easy)
- Identify sequencing dependencies (what must happen first)
- Surface optional paths (scenarios, not mandates)

**ALL actions must be framed as TARGET-SIDE outputs:**
- What to VERIFY (gaps, unknowns)
- What to SIZE (effort, cost, timeline)
- What to REMEDIATE (technical debt, risks)
- What to MIGRATE (data, systems, processes)
- What to INTERFACE (integration points)
- What to TSA (transition services needed)

❌ WRONG: "Buyer should upgrade their Oracle instance"
✅ RIGHT: "Target SAP migration blocked until buyer Oracle version confirmed (GAP)"

❌ WRONG: "Recommend buyer implement MFA"
✅ RIGHT: "Target MFA rollout required; integration with buyer IdP TBD pending buyer SSO details"
```

---

## Domain-Specific Overlap Considerations

### INFRASTRUCTURE

**Realistic PE Concerns:**
| Concern | Why It Matters | Typical Cost Impact |
|---------|----------------|---------------------|
| Data Center Exit | Lease obligations, migration timeline | $500K-$5M |
| Cloud Platform Mismatch | AWS vs Azure vs GCP migration | $200K-$2M |
| Virtualization Consolidation | VMware licensing, version gaps | $100K-$500K |
| Storage Platform | SAN/NAS consolidation or interfaces | $150K-$800K |
| Compute Refresh | EOL hardware, capacity planning | $200K-$1M |

**Domain-Specific Overlap Types:**
```
| Target Has | Buyer Has | Overlap Type | Integration Path |
|------------|-----------|--------------|------------------|
| On-prem DC | Cloud-first | platform_mismatch | Migrate to buyer cloud |
| AWS | Azure | platform_mismatch | Cross-cloud migration |
| AWS | AWS | platform_alignment | Account consolidation |
| VMware 6.7 | VMware 8.0 | version_gap | Upgrade before migration |
| No DR | Multi-region DR | capability_gap | Build DR capability |
```

**Infrastructure-Specific Questions to Surface:**
- What are the DC lease terms? Exit penalties?
- Is there a cloud strategy alignment or mismatch?
- What hardware is approaching EOL in next 24 months?
- What's the bandwidth between target and buyer networks?

---

### NETWORK

**Realistic PE Concerns:**
| Concern | Why It Matters | Typical Cost Impact |
|---------|----------------|---------------------|
| WAN Consolidation | Circuit costs, MPLS vs SD-WAN | $50K-$300K/year |
| Site Connectivity | Getting target sites on buyer network | $100K-$500K |
| Firewall Policy Alignment | Security posture, rule migration | $50K-$200K |
| DNS/DHCP Integration | Namespace conflicts, IP overlap | $25K-$100K |
| Internet Egress | Proxy, filtering, breakout strategy | $50K-$150K |

**Domain-Specific Overlap Types:**
```
| Target Has | Buyer Has | Overlap Type | Integration Path |
|------------|-----------|--------------|------------------|
| MPLS | SD-WAN | platform_mismatch | Migrate circuits |
| Cisco firewalls | Palo Alto | platform_mismatch | Policy migration |
| Flat network | Segmented | security_posture_gap | Redesign required |
| 10.x.x.x | 10.x.x.x | data_model_mismatch | IP re-addressing |
| Regional ISPs | Global MPLS | capability_gap | Circuit procurement |
```

**Network-Specific Questions to Surface:**
- What's the IP address scheme? Any overlaps with buyer?
- What's the WAN contract status? Early termination fees?
- How many sites need connectivity to buyer?
- What's the current internet bandwidth per site?

---

### CYBERSECURITY

**Realistic PE Concerns:**
| Concern | Why It Matters | Typical Cost Impact |
|---------|----------------|---------------------|
| Security Tool Consolidation | EDR, SIEM, vulnerability scanning | $100K-$400K |
| Compliance Gaps | SOC2, PCI, HIPAA remediation | $150K-$800K |
| Security Posture Alignment | Policy gaps, control differences | $75K-$250K |
| Incident Response | IR plan, retainer, integration | $50K-$150K |
| Penetration Testing | Pre-close assessment, remediation | $30K-$100K |

**Domain-Specific Overlap Types:**
```
| Target Has | Buyer Has | Overlap Type | Integration Path |
|------------|-----------|--------------|------------------|
| CrowdStrike | SentinelOne | platform_mismatch | Agent swap |
| No SIEM | Splunk | capability_gap | Onboard to buyer SIEM |
| Splunk | Splunk | platform_alignment | Consolidate instances |
| SOC2 Type 1 | SOC2 Type 2 | security_posture_gap | Upgrade certification |
| No IR plan | Mature IR | capability_gap | Extend buyer IR coverage |
```

**Cybersecurity-Specific Questions to Surface:**
- What's the current security tooling stack?
- When was the last penetration test? Results?
- What compliance certifications does target hold?
- Is there a documented incident response plan?

---

### APPLICATIONS

**Realistic PE Concerns:**
| Concern | Why It Matters | Typical Cost Impact |
|---------|----------------|---------------------|
| ERP Consolidation | SAP vs Oracle, data migration | $1M-$10M |
| CRM Consolidation | Salesforce vs HubSpot vs custom | $200K-$1M |
| Custom App Migration | Business-critical custom apps | $100K-$2M |
| Licensing Change of Control | Contract triggers, true-ups | $100K-$500K |
| Integration Middleware | ESB, iPaaS, API management | $100K-$400K |

**Domain-Specific Overlap Types:**
```
| Target Has | Buyer Has | Overlap Type | Integration Path |
|------------|-----------|--------------|------------------|
| SAP ECC | Oracle Cloud | platform_mismatch | Full ERP migration |
| SAP ECC | SAP S/4 | version_gap | Upgrade + consolidate |
| Salesforce | Salesforce | platform_alignment | Instance merge |
| HubSpot | Salesforce | platform_mismatch | CRM migration |
| Custom ERP | SAP | platform_mismatch | Replace or interface |
| Point-to-point | MuleSoft | integration_complexity | Middleware adoption |
```

**Applications-Specific Questions to Surface:**
- What's the ERP customization level? # of custom objects?
- What are the licensing terms? Change of control clauses?
- How many integrations touch the ERP?
- What custom applications are business-critical?

---

### IDENTITY & ACCESS

**Realistic PE Concerns:**
| Concern | Why It Matters | Typical Cost Impact |
|---------|----------------|---------------------|
| AD Consolidation | Forest trust vs migration | $200K-$800K |
| SSO Integration | Identity federation, Okta/Azure AD | $100K-$300K |
| PAM Consolidation | Privileged access, shared accounts | $75K-$200K |
| JML Processes | Joiner/Mover/Leaver automation | $50K-$150K |
| MFA Rollout | Gap remediation, user enrollment | $50K-$150K |

**Domain-Specific Overlap Types:**
```
| Target Has | Buyer Has | Overlap Type | Integration Path |
|------------|-----------|--------------|------------------|
| Single AD | Multi-forest AD | integration_complexity | Trust or migration |
| No SSO | Okta | capability_gap | SSO rollout |
| Okta | Azure AD | platform_mismatch | Federation or migration |
| Local accounts | Centralized IAM | security_posture_gap | Identity cleanup |
| Manual JML | Automated JML | process_divergence | Process adoption |
```

**Identity-Specific Questions to Surface:**
- How many AD forests/domains? Trust relationships?
- What's the SSO coverage? % of apps federated?
- How are privileged accounts managed?
- What's the JML process? Manual or automated?

---

### ORGANIZATION

**Realistic PE Concerns:**
| Concern | Why It Matters | Typical Cost Impact |
|---------|----------------|---------------------|
| Key Person Risk | Critical knowledge holders | Risk exposure |
| TSA Staffing | IT staff needed during transition | $200K-$500K/year |
| Skill Gaps | Missing capabilities post-close | $100K-$300K (hiring) |
| Reporting Structure | Integration into buyer org | Operational |
| Vendor Management | Contract transitions, relationships | $50K-$200K |

**Domain-Specific Overlap Types:**
```
| Target Has | Buyer Has | Overlap Type | Integration Path |
|------------|-----------|--------------|------------------|
| 2-person IT | 50-person IT | capability_gap | Absorb or augment |
| Generalist IT | Specialized IT | process_divergence | Role alignment |
| No ITSM | ServiceNow | capability_gap | ITSM adoption |
| External MSP | Internal IT | platform_mismatch | MSP exit or retain |
| CIO reports to CFO | CIO reports to CEO | process_divergence | Reporting change |
```

**Organization-Specific Questions to Surface:**
- Who are the key IT personnel? Flight risk?
- What's the current IT budget? Run vs change?
- What vendor relationships need to transfer?
- What's the IT operating model? Centralized vs federated?

---

## Implementation Approach

### For Each Prompt:

1. **Add Standard Sections** (same for all):
   - Overlap Map Instruction
   - 3-Layer Output Structure
   - Tone Control Rules

2. **Add Domain-Specific Content**:
   - PE Concerns table (from above)
   - Overlap Types table (from above)
   - Domain-Specific Questions (from above)

3. **Update Example Outputs**:
   - Show target_action + integration_option format
   - Show proper fact citation (F-TGT-xxx, F-BYR-xxx)
   - Show overlap_id linkage

4. **Test Each Prompt**:
   - Run with target-only docs (should produce Layer 1 findings)
   - Run with target+buyer docs (should produce all 3 layers)
   - Verify entity separation is maintained

---

## Questions Before Implementation

1. **Should overlap map be REQUIRED or RECOMMENDED?**
   - Required = model must call generate_overlap_map before any findings
   - Recommended = model should call it but can skip if no buyer facts

2. **Should we add scenario support now or later?**
   - The plan includes MigrationHypothesis but we haven't implemented it
   - Could add scenario tags to work items (MS-ABSORB, MS-STANDALONE, etc.)

3. **How verbose should the prompts be?**
   - More detail = better guidance but more tokens
   - Less detail = faster but may miss edge cases

4. **Should we update all 6 prompts at once or incrementally?**
   - All at once = consistency but bigger blast radius
   - Incrementally = safer but may have inconsistencies

---

## Recommended Order

1. **Applications** (most complex, highest PE value)
2. **Infrastructure** (common DD focus)
3. **Identity & Access** (Day-1 critical)
4. **Cybersecurity** (compliance-driven)
5. **Network** (supporting domain)
6. **Organization** (softer findings)

---

## Success Criteria

A good reasoning prompt produces findings that:

- [ ] Clearly separate target-standalone vs integration-dependent
- [ ] Use correct fact ID format (F-TGT-xxx, F-BYR-xxx)
- [ ] Include target_action on all work items
- [ ] Only use integration_option for buyer-dependent paths
- [ ] Link to overlap_id when referencing both entities
- [ ] Avoid "Buyer should..." language in wrong places
- [ ] Include realistic cost estimates (not generic ranges)
- [ ] Surface the questions a PE deal team would actually ask
