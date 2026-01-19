# Vendor & License Management Playbook

## Overview

Software licensing and vendor contracts are one of the most underestimated areas in M&A. Change of control clauses, license non-transferability, compliance gaps, and true-up audits can create millions in unexpected costs. This playbook addresses the upstream and downstream dependencies for vendor/license management in M&A.

**Typical Duration:** 6-18 months (full rationalization)
**Cost Range:** $500K-$10M+ in license exposure (varies wildly)
**Risk Level:** High (compliance, financial exposure)

---

## M&A Licensing Challenges

```
                    COMMON M&A LICENSE NIGHTMARES

    ┌─────────────────────────────────────────────────────────────────┐
    │  CHANGE OF CONTROL                                               │
    │                                                                  │
    │  Contract says: "Change of control requires consent and         │
    │                  may trigger renegotiation or termination"      │
    │                                                                  │
    │  Result: Vendor uses M&A as opportunity to reset pricing        │
    │          Can delay close if consent not obtained                │
    └─────────────────────────────────────────────────────────────────┘

    ┌─────────────────────────────────────────────────────────────────┐
    │  LICENSE NON-TRANSFERABILITY                                     │
    │                                                                  │
    │  Contract says: "Licenses are non-transferable to affiliates"   │
    │                                                                  │
    │  Result: Target's licenses cannot be used by buyer's users      │
    │          Must purchase new licenses or renegotiate              │
    └─────────────────────────────────────────────────────────────────┘

    ┌─────────────────────────────────────────────────────────────────┐
    │  TRUE-UP AUDIT TRIGGERED                                         │
    │                                                                  │
    │  M&A activity often triggers vendor audit clauses               │
    │                                                                  │
    │  Result: Discover license shortfall mid-integration             │
    │          Compliance gap becomes buyer's problem                  │
    └─────────────────────────────────────────────────────────────────┘

    ┌─────────────────────────────────────────────────────────────────┐
    │  VIRTUALIZATION / CLOUD LICENSING                                │
    │                                                                  │
    │  Target licensed for physical servers                           │
    │  Buyer runs in cloud/virtual                                    │
    │                                                                  │
    │  Result: Licenses don't transfer to new environment             │
    │          Must re-license for cloud deployment                   │
    └─────────────────────────────────────────────────────────────────┘
```

---

## Dependency Map

```
                    ┌─────────────────────────────────────────────────────────┐
                    │              UPSTREAM DEPENDENCIES                       │
                    │  (Must be complete BEFORE license remediation)           │
                    └─────────────────────────────────────────────────────────┘
                                              │
        ┌─────────────────┬──────────────────┼──────────────────┬─────────────────┐
        ▼                 ▼                  ▼                  ▼                 ▼
┌───────────────┐ ┌───────────────┐ ┌───────────────┐ ┌───────────────┐ ┌───────────────┐
│ Contract      │ │  Software     │ │  Usage        │ │  Target       │ │  Legal        │
│ Inventory     │ │  Inventory    │ │  Measurement  │ │  Architecture │ │  Review       │
│               │ │               │ │               │ │               │ │               │
│ - All vendor  │ │ - What's      │ │ - Actual      │ │ - Where will  │ │ - Change of   │
│   contracts   │ │   installed   │ │   users       │ │   software    │ │   control     │
│ - Terms       │ │ - Versions    │ │ - Deployments │ │   run         │ │ - Transfer    │
│ - Expiry      │ │ - Locations   │ │ - Compliance  │ │ - Cloud/VM    │ │   rights      │
└───────────────┘ └───────────────┘ └───────────────┘ └───────────────┘ └───────────────┘
                                              │
                    ┌─────────────────────────────────────────────────────────┐
                    │            VENDOR/LICENSE REMEDIATION                    │
                    │                                                          │
                    │  Assess → Negotiate → Remediate → Consolidate           │
                    └─────────────────────────────────────────────────────────┘
                                              │
        ┌─────────────────┬──────────────────┼──────────────────┬─────────────────┐
        ▼                 ▼                  ▼                  ▼                 ▼
┌───────────────┐ ┌───────────────┐ ┌───────────────┐ ┌───────────────┐ ┌───────────────┐
│ Compliance    │ │  Contract     │ │  Vendor       │ │  Cost         │ │  Technical    │
│ Achievement   │ │  Consolidation│ │  Leverage     │ │  Optimization │ │  Enablement   │
│               │ │               │ │               │ │               │ │               │
│ - True-up     │ │ - Single      │ │ - Volume      │ │ - License     │ │ - Use target  │
│   resolved    │ │   agreement   │ │   discounts   │ │   retirement  │ │   software    │
│ - Audit-ready │ │ - Aligned     │ │ - Better      │ │ - Duplicate   │ │ - Migrate to  │
│               │ │   terms       │ │   terms       │ │   removal     │ │   standard    │
└───────────────┘ └───────────────┘ └───────────────┘ └───────────────┘ └───────────────┘
                    │              DOWNSTREAM DEPENDENCIES                     │
                    │  (Enabled after license management resolved)             │
                    └─────────────────────────────────────────────────────────┘
```

---

## License Risk Categories

### 1. Change of Control Clauses
**Risk:** Contract may terminate or require renegotiation at close

| Vendor Category | Typical Terms | M&A Impact |
|-----------------|---------------|------------|
| Enterprise software (SAP, Oracle) | Notification required | May leverage for price increase |
| Cloud/SaaS | Assignment clause | Usually transferable |
| Data providers (Bloomberg, Reuters) | Strict non-transfer | May require new contract |
| Specialized software | Varies widely | Review each contract |
| Government/regulated | Often restrictive | May block transfer |

**Due Diligence Questions:**
- Does the contract contain change of control provisions?
- Is consent required for assignment?
- What happens on "deemed assignment"?
- Is there a termination right for the vendor?

### 2. License Compliance Gaps
**Risk:** Existing non-compliance becomes buyer's liability

| Gap Type | How It Happens | Discovery Risk |
|----------|----------------|----------------|
| Over-deployment | More installs than licenses | Vendor audit |
| Unauthorized use | Users not covered by license | Compliance review |
| Wrong edition | Using features not licensed | Self-assessment |
| Virtualization | Exceeds physical license rights | Cloud migration |
| Geographic | Licenses restricted by region | Global integration |

**High-Risk Vendors for Compliance:**
```
┌─────────────────────────────────────────────────────────────────┐
│  AUDIT-PRONE VENDORS (actively audit customers)                  │
│                                                                  │
│  • Microsoft - Most active auditor; complex licensing            │
│  • Oracle - Aggressive; virtualization traps                     │
│  • SAP - Indirect access; expensive                              │
│  • IBM - Complex; mainframe and distributed                      │
│  • Adobe - Named user vs device licensing                        │
│  • Autodesk - Serial number enforcement                          │
│  • VMware - Per-CPU licensing changes                            │
└─────────────────────────────────────────────────────────────────┘
```

### 3. License Non-Transferability
**Risk:** Target licenses cannot be used by buyer's environment

| Scenario | Problem | Solution |
|----------|---------|----------|
| Target has perpetual licenses | May not transfer to buyer entity | Contract amendment |
| Target has volume agreement | Buyer's users not covered | Add to buyer's agreement |
| Named user licenses | Specific to target employees | Reassignment process |
| Site licenses | Specific to target locations | Location change |
| OEM licenses | Tied to specific hardware | New licenses if hardware changes |

### 4. Virtualization/Cloud Licensing
**Risk:** Licenses don't work in new deployment model

| License Type | Risk in Cloud/Virtual | Remediation |
|--------------|----------------------|-------------|
| Per-server | May count virtual CPUs | Switch to core-based |
| Per-physical CPU | Doesn't translate to VM | Cloud licensing |
| Named user | Usually OK | Verify cloud rights |
| Device-based | OK if same devices | Re-evaluate for mobility |
| Subscription | Usually OK | Verify multi-tenant rights |

---

## Upstream Dependencies (Prerequisites)

### 1. Contract Inventory
**Must complete before:** Compliance assessment

| Dependency | Why Required | If Missing |
|------------|--------------|------------|
| All vendor contracts | Know what exists | Hidden obligations |
| Contract terms | Understand rights | Compliance guessing |
| Expiration dates | Renewal timeline | Missed renewals |
| Change of control clauses | M&A impact | Deal surprises |
| Spend by vendor | Materiality | Wrong priorities |

### 2. Software Inventory
**Must complete before:** License reconciliation

| Dependency | Why Required | If Missing |
|------------|--------------|------------|
| Installed software list | What's deployed | Unknown installs |
| Version information | License type needed | Wrong licenses |
| Location/devices | Geographic rights | Compliance gaps |
| User counts | Named user licenses | Under/over licensed |

### 3. Usage Measurement
**Must complete before:** True-up negotiation

| Dependency | Why Required | If Missing |
|------------|--------------|------------|
| Actual user counts | License consumption | Over-declare |
| Deployment counts | Server/device licenses | Compliance gap |
| Feature usage | Edition requirements | Over-licensed |
| Access patterns | Concurrent vs named | Wrong license type |

### 4. Target Architecture Decisions
**Must complete before:** License procurement

| Dependency | Why Required | If Missing |
|------------|--------------|------------|
| Where software will run | Physical/virtual/cloud | Wrong license type |
| Who will use software | User scope | Under-licensed |
| How long (sunset plans) | Duration | Over-investment |
| Integration approach | Keep/replace | Wasted procurement |

### 5. Legal Review of Key Contracts
**Must complete before:** Vendor negotiations

| Dependency | Why Required | If Missing |
|------------|--------------|------------|
| Change of control review | Assignment rights | Deal delay |
| Transfer provisions | License portability | Legal exposure |
| Termination rights | Vendor options | Contract loss |
| Audit rights | Compliance exposure | Surprise audit |

---

## Downstream Dependencies (Enabled After License Management)

### 1. Technical Integration
**Blocked until:** License rights confirmed

| Dependency | Why Blocked | Impact of Delay |
|------------|-------------|-----------------|
| Software deployment | License required | Can't deploy |
| User provisioning | License available | Users blocked |
| Migration projects | Target license rights | Migration blocked |
| Cloud migration | Cloud license rights | Architecture constraint |

### 2. Vendor Consolidation
**Blocked until:** Contract inventory complete

| Dependency | Why Blocked | Impact of Delay |
|------------|-------------|-----------------|
| Contract negotiation | Know starting point | No leverage |
| Volume discounts | Combined volumes | Missed savings |
| Single agreement | Multiple contracts | Admin overhead |
| Aligned renewals | Different dates | Ongoing effort |

### 3. Cost Optimization
**Blocked until:** Compliance resolved

| Dependency | Why Blocked | Impact of Delay |
|------------|-------------|-----------------|
| License retirement | Unknown compliance | Can't reduce |
| Renegotiation | Compliance liability | Weak position |
| True-up credits | Must settle first | No credits |
| Software rationalization | Need full picture | Parallel licenses |

---

## DD Document Signals to Detect

### Contract Signals
| Signal | Implication | Risk Level |
|--------|-------------|------------|
| "Change of control clause" | May require consent | High |
| "Non-transferable" | Licenses may not move | High |
| "Audit rights" | Vendor can audit | Medium |
| "Per-CPU licensing" | Virtualization risk | High |
| "Named user" | User-specific | Medium |

### Compliance Signals
| Signal | Implication | Action |
|--------|-------------|--------|
| "True-up pending" | Known compliance gap | Negotiate pre-close |
| "Audit in progress" | Active investigation | Resolve before close |
| "License shortfall" | Under-licensed | Budget for remediation |
| "Compliance not verified" | Unknown state | Discovery required |

### Vendor Signals
| Signal | Implication | Concern Level |
|--------|-------------|---------------|
| "Oracle" | Complex licensing, audit risk | High |
| "SAP" | Indirect access, expensive | High |
| "Microsoft EA" | Large agreement, transferable | Medium |
| "SaaS/subscription" | Usually easier | Lower |
| "Perpetual licenses" | Transfer questions | Medium |

### Spend Signals
| Signal | Implication | Opportunity |
|--------|-------------|-------------|
| "High software spend" | Material cost | Optimization target |
| "Multiple agreements same vendor" | Consolidation | Volume leverage |
| "Upcoming renewal" | Negotiation timing | Leverage opportunity |
| "Recently renewed" | Locked in | Limited flexibility |

---

## Cost Estimation

### License Exposure Categories
| Category | Typical Exposure | Discovery Method |
|----------|------------------|------------------|
| Over-deployment | $50K-$5M | Software inventory |
| Wrong edition | $50K-$1M | Feature usage analysis |
| Virtualization gaps | $100K-$5M | Infrastructure review |
| Indirect access (SAP) | $500K-$10M+ | Usage analysis |
| Change of control fees | $0-$2M | Contract review |

### Remediation Costs
| Activity | Typical Cost | Notes |
|----------|--------------|-------|
| License compliance assessment | $50-200K | Third-party typically |
| True-up settlement | Varies widely | 2-5x list price typical |
| Contract renegotiation | $0-500K | Leverage dependent |
| License management tooling | $50-200K | SAM tools |
| Ongoing management | $100-300K/year | FTE + tools |

---

## Common Failure Modes

1. **Ignored Until Audit** - No proactive assessment, vendor audits post-close
2. **Change of Control Surprise** - Key contract has blocking provision
3. **True-Up Shock** - Compliance gap discovered, large settlement
4. **Transfer Blocked** - Licenses can't move to buyer entity
5. **Virtualization Trap** - Physical licenses don't work in cloud
6. **Indirect Access (SAP)** - Third-party system access costs millions
7. **Renewals Missed** - Contracts auto-renewed at bad terms
8. **Volume Not Combined** - Separate contracts, no leverage
9. **Shadow IT Licenses** - Unknown software deployed
10. **Sunset Not Executed** - Keep paying for software to be retired

---

## M&A Due Diligence Checklist

| Question | Red Flag Answer | Cost Impact |
|----------|-----------------|-------------|
| Change of control clauses? | "Yes" / "Unknown" | Deal delay risk |
| Last license compliance review? | "Never" / ">2 years" | Unknown exposure |
| Major vendor contracts | SAP, Oracle, IBM | Complex licensing |
| Pending audits? | "Yes" | Active exposure |
| License types | "Per-CPU perpetual" | Virtualization risk |
| Software inventory exists? | "No" / "Outdated" | Discovery needed |
| Upcoming renewals? | <12 months | Timing pressure |
| Material spend by vendor? | >$500K/year | Negotiation opportunity |

---

## High-Risk Vendor Negotiation Tips

### Microsoft
- Enterprise Agreement (EA) usually transferable with assignment
- Verify Cloud Solution Provider (CSP) vs EA status
- Check Microsoft 365 license types (E3 vs E5)
- Azure consumption may not require change

### Oracle
- One of the most complex and risky
- Verify licensing model (Named User Plus vs Processor)
- Virtualization on VMware requires licensing all hosts in cluster
- Change of control often triggers renegotiation
- Consider Oracle LMS audit risk

### SAP
- Indirect/digital access is major trap
- Third-party systems accessing SAP data may trigger fees
- Named user types (Professional, Limited, etc.)
- Change of control typically requires notification
- Consider SAP audit risk

### IBM
- Multiple license metrics (PVU, VPC, RVU)
- Passport Advantage transferability varies
- Mainframe licensing is complex
- Sub-capacity licensing has strict rules

---

*Playbook Version: 1.0*
*Last Updated: January 2026*
