# Infrastructure Review Playlist

## Pre-Flight Considerations

**What makes Infrastructure different from other IT domains:**

1. **Physical and financial reality** - Unlike applications (which are logic), infrastructure is capital assets: servers, storage, network gear, data centers. There are depreciation schedules, refresh cycles, and lease obligations. Ask about CapEx.

2. **Cloud vs. On-Prem is THE question** - A company that's 90% cloud has a completely different risk profile than one with two owned data centers. This single factor changes everything about integration planning.

3. **Capacity and runway matter** - "Do they have enough compute?" is a real question. Approaching capacity limits mean forced spend. This is less common in applications.

4. **Dependency chains are deep** - Applications depend on infrastructure. If you miss that the SAP server is on hardware approaching EOL, you've missed a critical risk.

5. **DR/BC is often the hidden gap** - Companies claim they have disaster recovery. Probe hard. Untested DR is not DR. No DR for critical systems is a material risk.

6. **Contracts and commitments** - Data center leases, colocation agreements, cloud committed spend (AWS/Azure reservations), telecom circuits - these have financial and operational lock-in.

**What we learned building the bespoke tool:**

- Standalone viability (can they operate without buyer infrastructure?) is the key lens for infrastructure.
- The cloud maturity spectrum matters: Lift-and-shift (IaaS) vs. Cloud-native (PaaS/Serverless) vs. Hybrid have different integration implications.
- Backup and DR are frequently mentioned but rarely validated. "We back up everything" often means "we think we do."
- Hardware refresh cycles and EOL dates are capital planning concerns that affect deal economics.

---

## Phase 1: Infrastructure Inventory

### Prompt 1.1 - Data Center & Hosting Inventory
```
Create an inventory of all data centers, hosting locations, and cloud environments:

For each location/environment:
- Location type (Owned DC, Leased DC, Colocation, Cloud Region, Office Server Room)
- Physical address or cloud region
- Provider (if colo or cloud - e.g., Equinix, AWS us-east-1)
- Purpose (Production, DR, Dev/Test, Archive)
- Tier/redundancy level (if mentioned)
- Contract end date (if mentioned)
- Key systems hosted there

Format as a table: Location | Type | Provider | Purpose | Tier | Contract End | Key Systems | Source
```

### Prompt 1.2 - Compute Environment Inventory
```
Document all compute environments mentioned:

- Compute type (Physical servers, VMware/Hyper-V virtual, AWS EC2, Azure VMs, Containers/Kubernetes, Serverless)
- Count or scale (number of hosts, VMs, pods)
- Operating systems in use (Windows Server versions, Linux distributions)
- Age of physical hardware (if mentioned)
- Virtualization platform and version (VMware vSphere X.X, Hyper-V, etc.)
- Cloud accounts/subscriptions (AWS account IDs, Azure subscriptions)

For physical servers, note:
- Manufacturer/model if mentioned
- Warranty/support status
- Refresh timeline

Format as a table with source citations.
```

### Prompt 1.3 - Storage Environment
```
Document all storage systems mentioned:

- Storage type (SAN, NAS, Object storage, Cloud storage)
- Vendor and model (NetApp, Pure, Dell EMC, AWS S3, Azure Blob)
- Capacity total and utilized (if mentioned)
- Protocol (iSCSI, FC, NFS, SMB)
- Performance tier (Flash, Hybrid, HDD)
- Replication/backup integration
- Age and support status

Include cloud storage:
- S3 buckets, Azure Blob containers
- Cloud file shares (EFS, Azure Files)
- Backup storage (Veeam Cloud, AWS Backup)

Format as a table.
```

---

## Phase 2: Cloud Maturity Assessment

### Prompt 2.1 - Cloud Footprint Analysis
```
Assess the organization's cloud maturity:

1. What percentage of workloads are cloud vs. on-premise?
2. Which cloud providers are in use (AWS, Azure, GCP, other)?
3. What cloud services are consumed?
   - IaaS (VMs, storage)
   - PaaS (databases, app services)
   - SaaS (covered in Applications)
   - Serverless/Functions
   - Containers/Kubernetes

4. Cloud governance:
   - Is there a landing zone / account structure?
   - Are there tagging standards?
   - Is there a Cloud Center of Excellence?
   - Cost management and FinOps practices?

5. Cloud spend:
   - Monthly/annual cloud spend (if mentioned)
   - Reserved instances or savings plans?
   - Commitment agreements with providers?

Assess overall cloud maturity: Early/Ad-hoc | Developing | Defined | Optimized
```

### Prompt 2.2 - Cloud vs. On-Prem Decision Drivers
```
Based on the documents, identify:

1. What is driving cloud adoption (or resistance)?
   - Cost optimization
   - Scalability needs
   - Compliance requirements
   - Skills availability
   - Application requirements

2. What workloads are explicitly cloud vs. on-prem?
   - What's in cloud and why?
   - What's on-prem and why? (compliance, latency, legacy)
   - What's planned to migrate?

3. Cloud blockers or concerns mentioned:
   - Data sovereignty / compliance
   - Egress costs
   - Application compatibility
   - Skills gaps
   - Security concerns

Summarize the cloud strategy posture and any tension points.
```

---

## Phase 3: Disaster Recovery & Business Continuity

### Prompt 3.1 - DR/BC Capabilities Assessment
```
Assess disaster recovery and business continuity posture:

1. Is there a documented DR plan? (Yes/No/Unknown)
2. When was it last tested? (Date or "Unknown")
3. DR site details:
   - Location (secondary DC, cloud DR, hot/warm/cold)
   - Provider
   - Replication type (synchronous, asynchronous, backup-based)

4. Recovery objectives:
   - RTO (Recovery Time Objective) stated?
   - RPO (Recovery Point Objective) stated?
   - Which systems are covered by DR?

5. Backup infrastructure:
   - Backup solution (Veeam, Commvault, Rubrik, native cloud)
   - Backup frequency
   - Retention periods
   - Off-site/air-gapped copies?
   - Tested restores documented?

6. Gaps or concerns:
   - Systems without DR coverage
   - Untested plans
   - Single points of failure

Rate DR maturity: None | Basic Backups Only | Documented Untested | Tested Annually | Continuous Validation
```

### Prompt 3.2 - Critical System Dependencies
```
For business-critical systems (ERP, core databases, customer-facing apps):

Map each critical system to:
- Primary hosting location
- DR/failover capability (Yes/No/Partial)
- Backup method and frequency
- RTO/RPO if stated
- Single points of failure identified
- Dependencies (storage, network, other systems)

Identify any critical systems that:
- Have no documented DR
- Depend on infrastructure with no redundancy
- Have backup but no tested restore process
- Would cause business stoppage if unavailable >4 hours

Format as a table.
```

---

## Phase 4: Infrastructure Lifecycle & Technical Debt

### Prompt 4.1 - Hardware & Software Currency
```
Assess the age and support status of infrastructure components:

For each category, identify items that are:
- Past vendor support (EOL)
- In extended/paid support only
- Approaching EOL (<24 months)

Categories to assess:
1. Physical servers (>5 years old, out of warranty)
2. Storage arrays (EOL models, unsupported firmware)
3. Network equipment (covered in Network playlist)
4. Operating systems:
   - Windows Server 2012/2012 R2 (past EOL)
   - Windows Server 2016 (extended support)
   - RHEL 6/7, CentOS 7 (check support dates)
   - Ubuntu LTS versions
5. Virtualization platforms:
   - VMware vSphere 6.5/6.7 (past general support)
   - Hyper-V on older Windows Server
6. Backup software versions

For each EOL/aging item:
- Component
- Current version/age
- EOL date
- Risk if not upgraded
- Estimated refresh cost (if mentioned)

Format as a table.
```

### Prompt 4.2 - Infrastructure Technical Debt
```
Identify infrastructure technical debt indicators:

1. Capacity Debt:
   - Storage utilization >80%
   - Compute at capacity limits
   - Network bandwidth constraints

2. Architecture Debt:
   - No virtualization (bare metal everything)
   - No infrastructure-as-code
   - Manual provisioning processes
   - Lack of standardization (every server different)

3. Operational Debt:
   - No monitoring or alerting
   - Manual patching processes
   - No configuration management
   - Undocumented infrastructure

4. Security Debt:
   - Unpatched systems
   - End-of-life operating systems
   - Unsegmented networks
   - No encryption at rest

5. Skills Debt:
   - Single person knows the infrastructure
   - Outdated skills (mainframe, legacy platforms)
   - No documentation

For each debt item:
- Component affected
- Debt type
- Severity (Critical/High/Medium/Low)
- Business impact
- Remediation approach
```

---

## Phase 5: Capacity & Scalability

### Prompt 5.1 - Current Capacity Utilization
```
Where mentioned, document current capacity utilization:

- Compute: CPU and memory utilization across hosts
- Storage: Capacity used vs. available
- Network: Bandwidth utilization on key links
- Cloud: Current spend vs. limits/budgets

Identify:
- Any resources above 80% utilization (capacity risk)
- Upcoming capacity constraints mentioned
- Growth projections and runway
- Recent capacity additions or planned expansions

Format as a table: Resource | Current Utilization | Capacity | Runway | Notes
```

### Prompt 5.2 - Scalability Assessment
```
Assess the ability to scale infrastructure:

1. Can compute scale easily?
   - Virtualized (easy to add VMs)
   - Cloud (elastic)
   - Physical only (requires procurement)

2. Can storage scale easily?
   - Expandable arrays
   - Cloud storage (unlimited)
   - Fixed capacity at limits

3. Are there architectural bottlenecks?
   - Single points of failure
   - Non-scalable components
   - Licensing limits

4. What would happen if the business grew 50%?
   - Could infrastructure support it?
   - What would need to change?
   - Approximate cost to scale?

Summarize scalability posture: Constrained | Moderate | Highly Scalable
```

---

## Phase 6: Contracts & Financial Obligations

### Prompt 6.1 - Infrastructure Contracts Inventory
```
Document all infrastructure-related contracts and commitments:

1. Data center / colocation:
   - Provider
   - Contract end date
   - Monthly/annual cost
   - Termination terms
   - Expansion rights

2. Cloud commitments:
   - AWS Reserved Instances / Savings Plans
   - Azure Reserved Instances
   - Committed spend agreements
   - Term and amount

3. Hardware maintenance:
   - Servers, storage, network under contract
   - Provider (vendor, third-party)
   - Expiration dates
   - Annual cost

4. Software licenses (infrastructure):
   - VMware licensing
   - Windows Server licensing
   - Backup software
   - Monitoring tools

For each contract:
- Vendor | Description | Term End | Annual Cost | Termination Clause | Notes

Flag contracts that:
- Expire within 12 months
- Have auto-renewal without notice period
- Have change of control provisions
```

---

## Phase 7: Risk & Considerations Summary

### Prompt 7.1 - Infrastructure Risks
```
Synthesize findings into infrastructure-specific risks:

For each risk:
- Risk title
- Description
- Severity (Critical/High/Medium/Low)
- Category:
  - Standalone Viability (can they operate independently?)
  - Integration Complexity (how hard to integrate/migrate?)
  - Cost Exposure (unplanned spend required?)
  - Compliance Gap
  - Operational Risk
- Evidence (source quote)
- Recommended mitigation

Priority order:
1. Day 1 risks (what could stop the business?)
2. Near-term risks (action needed within 6 months)
3. Planning risks (affects integration timeline/cost)
```

### Prompt 7.2 - Infrastructure Follow-up Questions
```
Generate follow-up questions for infrastructure gaps:

For each question:
- Question text
- Why it matters
- Priority (Must have / Important / Nice to have)
- Who should answer (IT Ops, CIO, Vendor)

Key areas to probe:
- DR test results (when, what was tested, results)
- Hardware refresh plans and budget
- Cloud migration roadmap
- Capacity planning
- Contract renewal intentions
- Staffing and skills for current infrastructure
```

---

## Output Checklist

After running this playlist, you should have:
- [ ] Complete data center / hosting inventory
- [ ] Compute, storage, and virtualization inventory
- [ ] Cloud maturity assessment
- [ ] DR/BC assessment with gaps identified
- [ ] Infrastructure EOL and technical debt inventory
- [ ] Capacity utilization and scalability assessment
- [ ] Infrastructure contracts with key dates
- [ ] Prioritized risk list
- [ ] Follow-up questions
