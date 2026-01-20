# Activity Inventory Buildout Plan

## Objective

Build a comprehensive, market-anchored activity template inventory that:
1. Covers all common IT DD scenarios (carveout, acquisition, standalone)
2. Provides defensible cost ranges based on market data
3. Can be reviewed and refined by the team
4. Serves as the "rule base" for Stage 2 matching

---

## 10-Phase Plan

### Phase 1: Carveout Core Infrastructure
**Focus:** The foundational separation activities for carveouts

**Workstreams:**
- Identity (Azure AD, Okta, on-prem AD)
- Email (M365, Google Workspace, Exchange)
- Core Infrastructure (compute, storage, backup)

**Deliverables:**
- 15-20 activity templates per workstream
- Cost formulas with market anchors
- TSA duration guidance
- Complexity modifiers (simple/moderate/complex)

**Activities to Define:**
```
IDENTITY:
├── Assessment & Design
│   ├── Identity architecture assessment
│   ├── Directory services inventory
│   ├── SSO application mapping
│   └── MFA requirements analysis
├── Platform Standup
│   ├── Azure AD tenant provisioning
│   ├── Okta org provisioning
│   ├── On-prem AD forest design
│   └── Hybrid identity configuration
├── Migration
│   ├── User account migration
│   ├── Group/distribution list migration
│   ├── Service account remediation
│   └── Password sync/reset coordination
├── Application Integration
│   ├── SAML/OIDC SSO reconfiguration
│   ├── Legacy app authentication
│   ├── MFA enrollment
│   └── Conditional access policies
└── Cutover & Validation
    ├── Parallel running period
    ├── Authentication cutover
    └── Post-migration support

EMAIL:
├── Assessment & Design
│   ├── Mailbox inventory & sizing
│   ├── Shared mailbox mapping
│   ├── Distribution list analysis
│   └── Mail flow requirements
├── Platform Standup
│   ├── M365 tenant provisioning
│   ├── Domain configuration
│   ├── Mail routing setup
│   └── Security policy configuration
├── Migration
│   ├── Mailbox migration (staged)
│   ├── Archive migration
│   ├── Public folder migration
│   └── Calendar/contact migration
├── Coexistence
│   ├── Cross-tenant free/busy
│   ├── Mail forwarding period
│   └── Address book sync
└── Cutover
    ├── MX record cutover
    ├── Client reconfiguration
    └── Post-migration support

INFRASTRUCTURE:
├── Assessment & Design
│   ├── Server/VM inventory
│   ├── Storage assessment
│   ├── Backup requirements
│   └── DR requirements
├── Environment Build
│   ├── Cloud landing zone
│   ├── Network connectivity
│   ├── Security baseline
│   └── Monitoring setup
├── Migration
│   ├── VM migration (lift & shift)
│   ├── Database migration
│   ├── Storage migration
│   └── Application migration
└── Operations Handoff
    ├── Runbook creation
    ├── Operations training
    └── Support transition
```

---

### Phase 2: Carveout Network & Security
**Focus:** Network separation and security stack standup

**Workstreams:**
- Network (WAN, LAN, firewall, DNS)
- Security (endpoint, SIEM, vulnerability mgmt)
- Perimeter (VPN, proxy, web filtering)

**Activities to Define:**
```
NETWORK:
├── Assessment & Design
│   ├── Network topology mapping
│   ├── IP addressing scheme
│   ├── DNS/DHCP requirements
│   └── WAN circuit requirements
├── WAN Implementation
│   ├── MPLS circuit provisioning
│   ├── SD-WAN deployment
│   ├── Internet circuit provisioning
│   └── Circuit migration/cutover
├── LAN Implementation
│   ├── Switch configuration
│   ├── VLAN segmentation
│   ├── Wireless infrastructure
│   └── Network access control
├── Security Controls
│   ├── Firewall deployment
│   ├── Firewall rule migration
│   ├── IDS/IPS implementation
│   └── Network segmentation
└── DNS & Services
    ├── DNS zone separation
    ├── DHCP scope configuration
    ├── NTP infrastructure
    └── Certificate services

SECURITY:
├── Assessment & Design
│   ├── Security architecture design
│   ├── Control gap analysis
│   ├── Compliance mapping
│   └── Tooling requirements
├── Endpoint Security
│   ├── EDR deployment
│   ├── Antivirus migration
│   ├── Device encryption
│   └── Mobile device management
├── Security Operations
│   ├── SIEM deployment
│   ├── Log aggregation
│   ├── Alert tuning
│   └── SOC procedures
├── Vulnerability Management
│   ├── Scanner deployment
│   ├── Baseline scanning
│   ├── Remediation tracking
│   └── Patch management
└── Identity Security
    ├── PAM implementation
    ├── Service account vault
    ├── Access reviews
    └── Identity governance
```

---

### Phase 3: Application Workstream (Deep Dive)
**Focus:** The often-largest cost driver - applications

**Categories:**
- ERP (SAP, Oracle, NetSuite, Dynamics)
- CRM (Salesforce, Dynamics, HubSpot)
- HR/HCM (Workday, ADP, UKG)
- Custom/Legacy Applications
- SaaS Portfolio

**Activities to Define:**
```
ERP SEPARATION:
├── Assessment
│   ├── Instance topology analysis
│   ├── Integration mapping
│   ├── Data segmentation analysis
│   ├── Customization inventory
│   └── License entitlement review
├── Separation Options
│   ├── Instance clone & carve
│   ├── New instance standup
│   ├── Data extraction & load
│   └── Shared instance (TSA)
├── Implementation
│   ├── Environment provisioning
│   ├── Configuration migration
│   ├── Data migration
│   ├── Integration rebuild
│   └── Custom development port
├── Testing
│   ├── Functional testing
│   ├── Integration testing
│   ├── Performance testing
│   └── User acceptance testing
└── Cutover
    ├── Go-live planning
    ├── Data cutover
    ├── Hypercare support
    └── Stabilization

SAAS PORTFOLIO:
├── Inventory & Analysis
│   ├── SaaS discovery
│   ├── Contract review
│   ├── Data classification
│   └── Integration mapping
├── Account Separation
│   ├── New tenant/org creation
│   ├── User provisioning
│   ├── Data migration
│   └── SSO reconfiguration
├── Contract Transition
│   ├── License negotiation
│   ├── Contract assignment
│   ├── New procurement
│   └── Termination management
└── Data Handling
    ├── Data export
    ├── Data import
    ├── Historical data archival
    └── Data deletion verification
```

---

### Phase 4: Data & Migration Workstream
**Focus:** Data separation, archival, and migration tooling

**Categories:**
- Structured data (databases)
- Unstructured data (file shares, SharePoint)
- Data archival & retention
- Migration tooling & automation

**Activities to Define:**
```
DATABASE SEPARATION:
├── Assessment
│   ├── Database inventory
│   ├── Schema analysis
│   ├── Data classification
│   └── Dependency mapping
├── Separation Strategy
│   ├── Full database clone
│   ├── Schema-level separation
│   ├── Row-level filtering
│   └── Reference data handling
├── Implementation
│   ├── Target environment setup
│   ├── Schema migration
│   ├── Data migration
│   ├── Stored procedure migration
│   └── ETL job migration
└── Validation
    ├── Data integrity validation
    ├── Application testing
    └── Performance validation

FILE DATA:
├── Assessment
│   ├── File share inventory
│   ├── SharePoint site inventory
│   ├── Permission mapping
│   └── Data ownership analysis
├── Migration Planning
│   ├── Migration wave planning
│   ├── Tool selection
│   ├── Permission mapping strategy
│   └── Communication planning
├── Execution
│   ├── Pilot migration
│   ├── Wave migrations
│   ├── Permission remediation
│   └── Shortcut/link updates
└── Archival
    ├── Archive policy definition
    ├── Archive migration
    ├── Retention configuration
    └── Legal hold management
```

---

### Phase 5: Licensing Deep Dive
**Focus:** Software licensing across all categories

**Categories:**
- Microsoft licensing (M365, Azure, Windows Server)
- Database licensing (Oracle, SQL Server)
- Infrastructure licensing (VMware, backup)
- Application licensing (ERP, CRM, specialty)

**Activities to Define:**
```
LICENSE ASSESSMENT:
├── Inventory
│   ├── Deployed software discovery
│   ├── License entitlement mapping
│   ├── Usage analysis
│   └── Compliance assessment
├── Separation Analysis
│   ├── Transferability review
│   ├── True-up requirements
│   ├── Gap analysis
│   └── Cost modeling

LICENSE ACTIONS:
├── Transfer Scenarios
│   ├── Assignment agreement
│   ├── Novation
│   ├── Partial transfer
│   └── New procurement
├── Microsoft Specific
│   ├── EA transfer/termination
│   ├── CSP migration
│   ├── Azure subscription transfer
│   └── M365 tenant licensing
├── Oracle/Database
│   ├── License audit prep
│   ├── Processor licensing calc
│   ├── NUP true-up
│   └── Cloud migration licensing
└── Vendor Negotiations
    ├── Contract negotiation
    ├── Volume discount analysis
    ├── Term optimization
    └── Audit defense
```

---

### Phase 6: Acquisition & Integration
**Focus:** Buyer-side integration activities (vs. separation)

**Categories:**
- Technology integration
- Organization integration
- Synergy realization
- Day 1 readiness

**Activities to Define:**
```
INTEGRATION PLANNING:
├── Assessment
│   ├── Technology stack comparison
│   ├── Integration complexity scoring
│   ├── Synergy identification
│   └── Risk assessment
├── Strategy
│   ├── Integration approach (absorb/best-of-breed/parallel)
│   ├── Phasing & prioritization
│   ├── Resource planning
│   └── Governance model

TECHNOLOGY INTEGRATION:
├── Identity
│   ├── Directory trust/federation
│   ├── User migration to buyer
│   ├── Access provisioning
│   └── Decommission legacy
├── Email
│   ├── Domain integration
│   ├── GAL synchronization
│   ├── Mailbox migration to buyer
│   └── Unified address space
├── Infrastructure
│   ├── Network interconnection
│   ├── Workload migration
│   ├── Tool consolidation
│   └── Datacenter exit
├── Applications
│   ├── ERP consolidation
│   ├── CRM integration
│   ├── Tool rationalization
│   └── Custom app retirement

SYNERGY ACTIVITIES:
├── Cost Synergies
│   ├── License consolidation
│   ├── Vendor consolidation
│   ├── Headcount optimization
│   └── Contract renegotiation
├── Revenue Synergies
│   ├── Cross-sell enablement
│   ├── Platform integration
│   └── Data consolidation
```

---

### Phase 7: Operational Run-Rate
**Focus:** Ongoing costs post-transaction

**Categories:**
- Platform costs (cloud, SaaS)
- People costs (FTEs, contractors)
- Managed services
- License renewals

**Cost Models:**
```
PLATFORM RUN-RATE:
├── Cloud Infrastructure
│   ├── Compute ($/vCPU/month)
│   ├── Storage ($/GB/month)
│   ├── Network egress ($/GB)
│   └── Managed services ($/instance)
├── SaaS Platforms
│   ├── M365 ($/user/month by SKU)
│   ├── Salesforce ($/user/month by edition)
│   ├── Other SaaS ($/user/month typical)
│   └── Usage-based services
├── Security Tools
│   ├── EDR ($/endpoint/month)
│   ├── SIEM ($/GB ingested)
│   ├── Identity ($/user/month)
│   └── Vulnerability mgmt ($/asset/year)

PEOPLE RUN-RATE:
├── IT Leadership
│   ├── CIO/VP IT
│   ├── IT Directors
│   └── IT Managers
├── Operations
│   ├── System administrators
│   ├── Network engineers
│   ├── Security analysts
│   ├── Help desk (L1/L2/L3)
│   └── Database administrators
├── Development
│   ├── Application developers
│   ├── DevOps engineers
│   └── QA engineers
├── Ratios (typical)
│   ├── IT:Employee (1:50-100 typical)
│   ├── Help desk:Employee (1:100-200)
│   └── Security:Employee (1:500-1000)

MANAGED SERVICES:
├── Service Models
│   ├── Full IT outsource
│   ├── Co-managed IT
│   ├── Help desk only
│   └── NOC/SOC only
├── Pricing Models
│   ├── Per user/month
│   ├── Per device/month
│   ├── Fixed fee + variable
│   └── Consumption-based
```

---

### Phase 8: Compliance & Regulatory
**Focus:** Industry and regulatory requirements

**Categories:**
- SOC 2 / SOC 1
- HIPAA
- PCI-DSS
- GDPR / Privacy
- Industry-specific (FINRA, FDA, etc.)

**Activities to Define:**
```
COMPLIANCE ASSESSMENT:
├── Gap Analysis
│   ├── Control mapping
│   ├── Evidence collection
│   ├── Risk assessment
│   └── Remediation planning
├── Certification
│   ├── Audit preparation
│   ├── Auditor engagement
│   ├── Evidence provision
│   └── Finding remediation

COMPLIANCE IMPLEMENTATION:
├── SOC 2
│   ├── Policy development
│   ├── Control implementation
│   ├── Monitoring setup
│   └── Type 1 → Type 2 bridge
├── HIPAA
│   ├── Risk assessment
│   ├── BAA management
│   ├── Technical safeguards
│   └── Training program
├── PCI-DSS
│   ├── Scope reduction
│   ├── Control implementation
│   ├── Penetration testing
│   └── SAQ/ROC preparation
├── Privacy
│   ├── Data mapping
│   ├── Consent management
│   ├── DSR process
│   └── Cross-border transfer
```

---

### Phase 9: Vendor & Contract Transition
**Focus:** Third-party relationships

**Categories:**
- Contract assignment/novation
- Vendor transitions
- Procurement setup
- Ongoing vendor management

**Activities to Define:**
```
CONTRACT TRANSITION:
├── Assessment
│   ├── Contract inventory
│   ├── Assignment clause review
│   ├── Change of control analysis
│   └── Termination clause review
├── Execution
│   ├── Assignment agreements
│   ├── Novation execution
│   ├── New contract negotiation
│   └── Termination processing
├── Specific Vendors
│   ├── Telecom circuits
│   ├── Cloud providers
│   ├── SaaS vendors
│   └── Hardware maintenance

PROCUREMENT SETUP:
├── Process
│   ├── Procurement policy
│   ├── Approval workflows
│   ├── Vendor onboarding
│   └── P2P system setup
├── Vendor Management
│   ├── Vendor database
│   ├── Performance tracking
│   ├── Contract repository
│   └── Renewal tracking
```

---

### Phase 10: Validation & Team Refinement
**Focus:** Quality assurance and team convergence

**Activities:**
```
VALIDATION:
├── Cross-Reference Check
│   ├── All workstreams have activities
│   ├── No duplicate activities
│   ├── Consistent cost methodology
│   └── TSA durations align
├── Market Anchor Validation
│   ├── Compare to past deals
│   ├── Vendor quote comparison
│   ├── Industry benchmark review
│   └── Team experience check
├── Gap Analysis
│   ├── Missing scenarios
│   ├── Edge cases
│   └── Industry variations

TEAM REFINEMENT PROCESS:
├── Review Sessions
│   ├── Workstream-by-workstream review
│   ├── Cost range calibration
│   ├── Complexity modifier tuning
│   └── TSA duration validation
├── Documentation
│   ├── Assumptions documented
│   ├── Sources cited
│   ├── Limitations noted
│   └── Update process defined
├── Testing
│   ├── Sample deal analysis
│   ├── Historical deal comparison
│   ├── Edge case testing
│   └── Team feedback incorporation
```

---

## Implementation Approach

### For Each Phase:

1. **Draft templates** (Claude builds initial structure)
2. **Team review** (SMEs validate activities and ranges)
3. **Calibrate costs** (Adjust based on team input and market data)
4. **Test with examples** (Run through sample scenarios)
5. **Commit to codebase** (Add to ACTIVITY_TEMPLATES)

### Artifacts Per Phase:

- Activity template code (Python dict)
- Cost anchor documentation (markdown)
- Review checklist (for team sign-off)
- Test scenarios (sample considerations → expected activities)

---

## Timeline Suggestion

| Phase | Focus | Complexity |
|-------|-------|------------|
| 1 | Carveout Core | High - foundational |
| 2 | Network & Security | Medium |
| 3 | Applications | High - complex |
| 4 | Data & Migration | Medium |
| 5 | Licensing | Medium |
| 6 | Acquisition | Medium |
| 7 | Run-Rate | Low - formulas |
| 8 | Compliance | Medium |
| 9 | Vendor/Contract | Low |
| 10 | Validation | High - convergence |

---

## Ready to Start?

Begin with **Phase 1: Carveout Core Infrastructure** and build out the detailed activity templates for Identity, Email, and Core Infrastructure workstreams.
