# Playbook Integration Architecture

## Overview

This document explains how the IT Due Diligence playbook library connects to the reasoning agents, why this architecture matters, and the current state of integration.

---

## The Problem We're Solving

Traditional IT due diligence suffers from three critical gaps:

1. **Isolated Findings** - Analysts identify risks but don't connect them to upstream/downstream impacts
2. **Generic Recommendations** - Work items lack sequencing context ("do network before identity")
3. **Missing Cost Drivers** - Complexity signals that multiply costs aren't systematically detected

**Example of the problem:**
> "Target has no DR capability"

This finding is useless without context:
- What does it block? (Compliance certification, insurance, ransomware resilience)
- What must happen first? (BIA, asset inventory, network to DR site)
- What does it cost? (Level 0 to Level 2 DR = $500K-2M)

---

## The Solution: Playbook-Wired Reasoning

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           PLAYBOOK LIBRARY                                   │
│                                                                              │
│  12 Expert Playbooks containing:                                            │
│  • Upstream/downstream dependencies                                          │
│  • DD document signal detection                                              │
│  • Cost estimation references                                                │
│  • Common failure modes                                                      │
│  • Integration scenarios                                                     │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ Knowledge extracted and embedded
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         REASONING AGENT PROMPTS                              │
│                                                                              │
│  Each domain agent has playbook knowledge injected into its prompt:         │
│                                                                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │Infrastructure│  │Applications │  │  Identity   │  │   Network   │        │
│  │   Agent     │  │    Agent    │  │   Agent     │  │    Agent    │        │
│  │             │  │             │  │             │  │             │        │
│  │ • Cloud     │  │ • SAP/ERP   │  │ • AD Consol │  │ • SD-WAN    │        │
│  │ • DR/BCP    │  │ • BI/Analytics│ │ • M365     │  │ • Lead times│        │
│  │ • DC exit   │  │ • Licensing │  │ • SSO deps  │  │ • Patterns  │        │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘        │
│                                                                              │
│  ┌─────────────┐  ┌─────────────┐                                           │
│  │  Security   │  │Organization │                                           │
│  │   Agent     │  │   Agent     │                                           │
│  │             │  │             │                                           │
│  │ • Remediation│ │ • Carveout  │                                           │
│  │ • Priority  │  │ • TSA       │                                           │
│  │ • Insurance │  │ • Op Model  │                                           │
│  └─────────────┘  └─────────────┘                                           │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ Agent reasons with playbook context
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           INTELLIGENT OUTPUT                                 │
│                                                                              │
│  Findings now include:                                                       │
│  • Dependency-aware work items (sequenced correctly)                        │
│  • Signal-detected risks (specific phrases trigger findings)                │
│  • Cost-informed estimates (complexity multipliers applied)                 │
│  • Failure mode awareness (common pitfalls flagged)                         │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Why This Matters

### 1. Dependency Awareness

Without playbook knowledge, an agent might recommend:
> "Migrate applications to cloud"

With playbook knowledge, the agent knows:
> "Cloud migration requires: (1) Network connectivity first, (2) Identity foundation, (3) Security controls. Blocking: DC decommission, app modernization, cost optimization."

### 2. Signal Detection

Playbooks teach agents what phrases to look for in DD documents:

| Signal in Document | What Agent Now Knows |
|--------------------|---------------------|
| "SAP ECC 6.0" | End of mainstream maintenance 2027 = forced migration |
| "No MFA" | Security remediation priority, insurance implications |
| "Single data center" | DR investment needed, business continuity gap |
| "Change of control clause" | License may terminate at close, legal review needed |
| "MPLS only" | 45-90 day lead times, SD-WAN opportunity |

### 3. Cost Intelligence

Agents can now flag complexity signals that affect cost estimates:

| Complexity Signal | Cost Multiplier |
|-------------------|-----------------|
| Dual ERP environment | +1.3x application integration |
| Legacy systems (COBOL, mainframe) | +1.3x infrastructure |
| No documentation | +1.15x-1.5x discovery effort |
| Key person dependency | +1.2x organizational risk |
| Heavy customization | +1.3x-2.5x remediation |

### 4. Failure Mode Prevention

Playbooks encode common M&A IT failures:

- **ERP**: Data quality underestimated (40% of projects delayed)
- **Network**: IP overlap discovered late (NAT mid-project)
- **Identity**: Nested groups cause sync failures
- **Security**: Controls not replicated in cloud
- **Carveout**: TSA pricing doesn't cover actual effort

---

## Current Playbook-to-Prompt Mappings

### Infrastructure Reasoning Agent
**File:** `prompts/v2_infrastructure_reasoning_prompt.py`

| Playbook | Knowledge Injected |
|----------|-------------------|
| 05 - Cloud Migration | Migration dependencies, wave sequencing, 7 R's framework |
| 08 - DR/BCP Implementation | DR maturity levels (0-3), BIA dependencies, RTO/RPO cost curves |

**Key Capabilities Added:**
- Detects cloud readiness signals
- Understands DC exit sequencing
- Knows DR investment requirements by maturity level
- Can identify what blocks cloud migration (network, identity, security)

---

### Applications Reasoning Agent
**File:** `prompts/v2_applications_reasoning_prompt.py`

| Playbook | Knowledge Injected |
|----------|-------------------|
| 01 - SAP S/4HANA Migration | SAP-specific signals, upgrade paths, Z-program complexity |
| 07 - ERP Rationalization | Dual ERP scenarios, consolidation paths, timeline ranges |
| 09 - Data Analytics/BI | BI maturity levels, consolidation dependencies |
| 12 - Vendor/License Management | Change of control risks, compliance gaps, high-risk vendors |

**Key Capabilities Added:**
- Detects ERP complexity signals (ECC 6.0, custom ABAP, dual ERP)
- Understands ERP migration dependencies (data quality, master data, integrations)
- Identifies licensing risks (Oracle, SAP, Microsoft audit exposure)
- Knows BI platform consolidation sequencing

---

### Identity & Access Reasoning Agent
**File:** `prompts/v2_identity_access_reasoning_prompt.py`

| Playbook | Knowledge Injected |
|----------|-------------------|
| 03 - Active Directory Consolidation | Forest trust patterns, consolidation strategies, sync dependencies |
| 02 - Microsoft 365 Migration | Tenant migration complexity, coexistence scenarios |

**Key Capabilities Added:**
- Detects AD complexity (multiple forests, trust relationships)
- Understands identity as foundation for everything else
- Knows M365 migration sequencing (identity before mailbox)
- Can identify SSO/federation dependencies

---

### Cybersecurity Reasoning Agent
**File:** `prompts/v2_cybersecurity_reasoning_prompt.py`

| Playbook | Knowledge Injected |
|----------|-------------------|
| 06 - Security Remediation | Priority sequencing, workstream dependencies, insurance signals |

**Key Capabilities Added:**
- Detects security maturity signals (no MFA, flat network, no EDR)
- Understands security remediation sequencing (Day 1 → Week 1 → Month 1)
- Knows what blocks security work (asset inventory, identity)
- Identifies cyber insurance implications

---

### Network Reasoning Agent
**File:** `prompts/v2_network_reasoning_prompt.py`

| Playbook | Knowledge Injected |
|----------|-------------------|
| 10 - SD-WAN & Network Modernization | MPLS vs SD-WAN comparison, deployment waves, M&A acceleration |

**Key Capabilities Added:**
- Understands network as foundation layer (everything depends on it)
- Knows lead times (MPLS 45-90 days vs SD-WAN 14-30 days)
- Detects modernization opportunities (high WAN costs, single carrier)
- Understands M&A benefit of SD-WAN (faster site integration)

---

### Organization Reasoning Agent
**File:** `prompts/v2_organization_reasoning_prompt.py`

| Playbook | Knowledge Injected |
|----------|-------------------|
| 04 - Carveout & TSA Separation | TSA service categories, exit sequencing, entanglement signals |
| 11 - IT Operating Model | Operating model archetypes, integration scenarios, staffing signals |

**Key Capabilities Added:**
- Detects carveout complexity (shared services, parent dependencies)
- Understands TSA duration by service type
- Knows operating model patterns (centralized, federated, hybrid)
- Identifies key person risks with retention urgency levels

---

## How It Works Technically

### 1. Playbook Creation
Expert knowledge is encoded in markdown playbooks (`playbooks/*.md`) with structured sections:
- Dependency maps (upstream/downstream)
- Signal detection tables
- Cost estimation references
- Common failure modes

### 2. Knowledge Extraction
Key tables and frameworks are extracted from playbooks and formatted for prompt injection.

### 3. Prompt Enhancement
The `DEPENDENCY & INTEGRATION KNOWLEDGE` section is added to each reasoning prompt, containing:
```python
## DEPENDENCY & INTEGRATION KNOWLEDGE (from Expert Playbooks)

Understanding dependencies is critical for sequencing and cost estimation.

### [Domain] Dependencies

**Upstream (must complete BEFORE [domain] work):**
| Dependency | Why Required | If Missing |
|------------|--------------|------------|
| ... | ... | ... |

**Downstream (blocked UNTIL [domain] completes):**
| What's Blocked | Why | Impact of Delay |
|----------------|-----|-----------------|
| ... | ... | ... |

### DD Document Signals to Detect
| Signal | Implication | Action |
|--------|-------------|--------|
| ... | ... | ... |
```

### 4. Runtime Reasoning
When the agent analyzes inventory, it has playbook context available:
- It knows what signals to look for
- It understands dependencies when creating work items
- It can flag complexity multipliers for costing
- It avoids common failure modes

---

## Playbook Library Summary

| # | Playbook | Primary Domain | Timeline | Cost Range |
|---|----------|----------------|----------|------------|
| 01 | SAP S/4HANA Migration | Applications | 18-36 mo | $5-50M |
| 02 | Microsoft 365 Migration | Identity | 3-12 mo | $500K-5M |
| 03 | Active Directory Consolidation | Identity | 6-18 mo | $500K-3M |
| 04 | Carveout & TSA Separation | Organization | 12-24 mo | $5-30M |
| 05 | Cloud Migration | Infrastructure | 12-36 mo | $2-20M |
| 06 | Security Remediation | Security | 6-18 mo | $1-10M |
| 07 | ERP Rationalization | Applications | 18-48 mo | $10-100M |
| 08 | DR/BCP Implementation | Infrastructure | 6-18 mo | $500K-5M |
| 09 | Data Analytics/BI Consolidation | Applications | 6-18 mo | $500K-5M |
| 10 | SD-WAN & Network Modernization | Network | 6-12 mo | $500K-3M |
| 11 | IT Operating Model | Organization | 12-24 mo | $1-10M |
| 12 | Vendor & License Management | Applications | 6-18 mo | $500K-10M+ |

**Total Library Size:** ~280KB of structured expert knowledge

---

## Future Enhancements

### Planned Additions
1. **Industry-Specific Playbooks** - Healthcare (HIPAA, EMR), Financial Services (SOX, core banking), Manufacturing (OT/IT)
2. **Failure Case Studies** - Real examples with lessons learned
3. **Quantified Signals** - More precise cost multipliers from actual deal data

### Architecture Evolution
1. **Dynamic Playbook Selection** - Choose relevant playbooks based on deal context
2. **Playbook Versioning** - Track changes as knowledge evolves
3. **Feedback Loop** - Learn from actual integration outcomes

---

## Conclusion

The playbook integration transforms the IT due diligence agent from a "finding generator" into a "strategic advisor." By embedding expert knowledge about dependencies, signals, and failure modes directly into reasoning prompts, the agent produces:

- **Sequenced work items** that respect dependencies
- **Specific findings** triggered by signal detection
- **Cost-aware recommendations** with complexity multipliers
- **Failure-resistant plans** informed by common pitfalls

This architecture captures the knowledge of senior M&A IT specialists and makes it available for every analysis.
