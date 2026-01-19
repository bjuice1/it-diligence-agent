# IT Due Diligence Playbook Library

## Overview

This playbook library provides expert knowledge for IT due diligence analysis, with a focus on **upstream and downstream dependencies**. Each playbook maps:

- **Upstream Dependencies** - What must be complete before this work can start
- **Downstream Dependencies** - What depends on this work completing
- **Complexity Signals** - What to look for in DD documents
- **Cost Estimation Factors** - How to assess scope/cost
- **Common Failure Modes** - What typically goes wrong

---

## Playbook Index

### Core Integration Playbooks
| # | Playbook | Primary Use Case | Typical Timeline |
|---|----------|------------------|------------------|
| 01 | [SAP S/4HANA Migration](01_sap_s4hana_migration.md) | SAP modernization, ERP consolidation | 18-36 months |
| 02 | [Microsoft 365 Migration](02_microsoft_365_migration.md) | Email, collaboration modernization | 3-12 months |
| 03 | [Active Directory Consolidation](03_active_directory_consolidation.md) | Identity integration, M&A | 6-18 months |
| 04 | [Carveout & TSA Separation](04_carveout_tsa_separation.md) | Divestitures, spin-offs | 12-24 months |
| 05 | [Cloud Migration](05_cloud_migration.md) | Data center exit, modernization | 12-36 months |
| 06 | [Security Remediation](06_security_remediation.md) | Post-acquisition security | 6-18 months |
| 07 | [ERP Rationalization](07_erp_rationalization.md) | Dual/multiple ERP consolidation | 18-48 months |

### Operational & Enablement Playbooks
| # | Playbook | Primary Use Case | Typical Timeline |
|---|----------|------------------|------------------|
| 08 | [DR/BCP Implementation](08_dr_bcp_implementation.md) | Disaster recovery, business continuity | 6-18 months |
| 09 | [Data Analytics/BI Consolidation](09_data_analytics_bi_consolidation.md) | Reporting, analytics unification | 6-18 months |
| 10 | [SD-WAN & Network Modernization](10_sdwan_network_modernization.md) | WAN transformation, site connectivity | 6-12 months |
| 11 | [IT Operating Model](11_it_operating_model.md) | Org structure, process alignment | 12-24 months |
| 12 | [Vendor & License Management](12_vendor_license_management.md) | Contract consolidation, compliance | 6-18 months |

---

## How Playbooks Interconnect

```
                        M&A IT INTEGRATION DEPENDENCIES

                    ┌─────────────────────────────────────────┐
                    │           FOUNDATION LAYER               │
                    │                                          │
                    │  ┌─────────────┐    ┌─────────────┐     │
                    │  │   Active    │    │   Network   │     │
                    │  │  Directory  │    │ Connectivity│     │
                    │  │ Consolidation│   │             │     │
                    │  └──────┬──────┘    └──────┬──────┘     │
                    └─────────┼──────────────────┼────────────┘
                              │                  │
                              ▼                  ▼
                    ┌─────────────────────────────────────────┐
                    │           APPLICATION LAYER              │
                    │                                          │
                    │  ┌─────────────┐    ┌─────────────┐     │
                    │  │ Microsoft   │    │   Cloud     │     │
                    │  │    365      │    │ Migration   │     │
                    │  │ Migration   │    │             │     │
                    │  └──────┬──────┘    └──────┬──────┘     │
                    │         │                  │             │
                    │         │    ┌─────────────┐             │
                    │         └───►│   Security  │◄────────────┘
                    │              │ Remediation │             │
                    │              └──────┬──────┘             │
                    └─────────────────────┼───────────────────┘
                                          │
                                          ▼
                    ┌─────────────────────────────────────────┐
                    │           BUSINESS LAYER                 │
                    │                                          │
                    │  ┌─────────────┐    ┌─────────────┐     │
                    │  │    SAP      │    │    ERP      │     │
                    │  │  S/4HANA    │◄───│ Rationali-  │     │
                    │  │ Migration   │    │   zation    │     │
                    │  └─────────────┘    └─────────────┘     │
                    │                                          │
                    │         ┌─────────────┐                  │
                    │         │  Carveout/  │                  │
                    │         │    TSA      │                  │
                    │         │ Separation  │                  │
                    │         └─────────────┘                  │
                    └─────────────────────────────────────────┘

LEGEND:
─────────
→ Depends on (downstream depends on upstream)
```

---

## Dependency Sequencing Matrix

### Which playbooks depend on which?

| Playbook | Depends On (Upstream) | Enables (Downstream) |
|----------|----------------------|---------------------|
| AD Consolidation | Network connectivity | M365, Cloud, Security, ERP |
| M365 Migration | AD Consolidation, Network | Security, Collaboration |
| Cloud Migration | Network, Identity | App modernization, DR |
| Security Remediation | Asset inventory, AD | Integration, Compliance |
| SAP S/4HANA | AD, Network, Data, Process | Shared services, Analytics |
| ERP Rationalization | All foundational | Shared services, Analytics |
| Carveout/TSA | Entanglement assessment | Standalone operations |
| DR/BCP | BIA, Asset inventory, Network | Ransomware resilience, Compliance |
| Data Analytics/BI | Source systems stable, KPIs defined | Executive reporting, Financial close |
| SD-WAN | Internet circuits, Security architecture | Cloud connectivity, Site integration |
| IT Operating Model | Business strategy, Current state assessment | Technical integration, Vendor consolidation |
| Vendor/License | Contract inventory, Software inventory | Technical integration, Cost optimization |

---

## Quick Reference: DD Document Signals

### When analyzing IT DD documents, look for these signals:

#### Critical Risk Indicators
| Signal | Implication | Playbook Reference |
|--------|-------------|-------------------|
| "Multiple ERPs" | ERP rationalization required | 07_erp_rationalization |
| "Legacy ERP" (AS/400, JDE, COBOL) | Modernization urgency | 01_sap_s4hana, 07_erp_rationalization |
| "No MFA" | Security remediation priority | 06_security_remediation |
| "Flat network" | Segmentation required | 06_security_remediation |
| "Shared infrastructure" (carveout) | TSA complexity | 04_carveout_tsa |
| "Multiple AD forests" | Identity consolidation | 03_active_directory |
| "On-premises data center" | Cloud migration candidate | 05_cloud_migration |
| "Key person dependency" | Knowledge transfer risk | All playbooks |
| "No DR" / "DR untested" | Business continuity gap | 08_dr_bcp |
| "Multiple BI tools" | Reporting consolidation | 09_data_analytics_bi |
| "MPLS only" / "High WAN costs" | Network modernization | 10_sdwan |
| "Heavy outsourcing" | Operating model review | 11_it_operating_model |
| "Change of control clause" | License risk | 12_vendor_license |
| "Oracle/SAP audit" | Compliance exposure | 12_vendor_license |

#### Complexity Multipliers
| Signal | Multiplier | Notes |
|--------|------------|-------|
| "Custom development" / "Z-programs" | 1.3x-2.0x | SAP/ERP complexity |
| "500+ interfaces" | 1.5x-2.0x | Integration work |
| "No documentation" | 1.2x-1.5x | Discovery effort |
| "Multiple countries" | 1.2x-1.5x | Coordination |
| "Regulatory requirements" | 1.2x-1.5x | Compliance work |
| "EOL systems" | 1.3x-1.5x | Forced timeline |

---

## Common M&A IT Integration Sequences

### Acquisition (Full Integration)

```
Phase 1: Foundation (0-6 months)
├── Network connectivity
├── AD trust establishment
├── Security assessment
└── Asset inventory

Phase 2: Identity & Collaboration (3-12 months)
├── AD consolidation
├── M365 migration
├── Security remediation
└── SSO integration

Phase 3: Applications (6-24 months)
├── Cloud migration
├── Application rationalization
└── ERP consolidation planning

Phase 4: Business Systems (12-36 months)
├── ERP migration/consolidation
├── Shared services enablement
└── Legacy decommissioning
```

### Carveout (Divestiture)

```
Phase 1: Pre-Close (0-6 months)
├── Entanglement assessment
├── TSA negotiation
├── Day 1 planning
└── Standalone architecture

Phase 2: Day 1 Readiness (Close)
├── Legal entity setup
├── Basic connectivity
├── TSA services active
└── Minimal viable IT

Phase 3: TSA Operations (0-18 months)
├── Standalone infrastructure build
├── Application separation
├── User migration
└── Data extraction

Phase 4: TSA Exit (12-24 months)
├── Service-by-service exit
├── Final data migration
├── Legacy access removal
└── TSA close-out
```

---

## Using Playbooks for DD Analysis

### Step 1: Identify Relevant Playbooks
Based on deal type and DD findings, identify which playbooks apply:

| Deal Type | Primary Playbooks | Secondary Playbooks |
|-----------|-------------------|---------------------|
| Acquisition | 03, 02, 06, 05 | 01, 07 |
| Carveout | 04, 03, 02 | 06, 05 |
| Merger of equals | 07, 03, 02, 06 | 01, 05 |
| Platform add-on | 03, 02, 06 | 05 |
| Technology acquisition | 05, 06, 03 | 02 |

### Step 2: Map Dependencies
For each identified playbook:
1. Note upstream dependencies (what must happen first)
2. Note downstream dependencies (what this enables)
3. Identify critical path items
4. Flag blockers or risks

### Step 3: Estimate Effort
Use complexity signals from each playbook to:
1. Identify base scope (users, systems, data volume)
2. Apply multipliers (customization, geography, compliance)
3. Account for dependencies (can't do X until Y complete)
4. Build timeline with dependencies

### Step 4: Flag Risks
Each playbook includes common failure modes. Use these to:
1. Identify risks in DD findings
2. Create mitigation recommendations
3. Inform deal pricing/negotiation
4. Plan post-close priorities

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | January 2026 | Initial playbook library (7 playbooks) |
| 1.1 | January 2026 | Added 5 operational playbooks (08-12) |

---

*This playbook library is designed to provide context for AI-assisted IT due diligence analysis. It encodes expert knowledge about common IT integration scenarios and their dependencies.*
