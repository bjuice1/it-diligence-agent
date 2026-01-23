# Applications Landscape Review Playlist

## Pre-Flight Considerations

**What makes Applications different from other IT domains:**

1. **Business-centric, not technical** - Applications map to business processes. You're assessing "can Finance close the books?" not "is the server running?" This requires understanding what the business DOES.

2. **Vendor dependency is everything** - Unlike infrastructure you control, applications come with vendor roadmaps, EOL dates, licensing models, and support contracts. A SaaS app is fundamentally different from an on-prem ERP.

3. **Customization is hidden risk** - Two companies can both have "SAP" but one is vanilla and one has 500 custom ABAP programs. The name tells you nothing; the customization level tells you everything about migration complexity.

4. **The "shadow IT" problem** - Official inventories miss things. Marketing bought their own tools. Sales has three CRMs. The documents won't tell you everything - that's why follow-up questions matter.

5. **Capability gaps matter more than app counts** - Having 200 applications means nothing. Having ZERO applications for payroll is a crisis. Always assess against business capability needs, not just what's documented.

**What we learned building the bespoke tool:**

- The Business Capability Checklist (Finance, HR, Sales, Ops, IT, Security, Collaboration, Analytics, Legal, Customer Service, E-commerce, Industry-specific) is essential. Without it, you only find what's documented.
- EOL dates are frequently wrong when LLMs guess. A maintained reference database adds real value.
- "Unknown" is a valid and important answer. Forcing a guess creates false confidence.
- Buyer comparison needs to be explicit - "same product," "same category different vendor," "target only," "buyer only" - these drive different integration decisions.

---

## Phase 1: Application Discovery

### Prompt 1.1 - Core Application Inventory
```
Review all documents and create a comprehensive application inventory table with these columns:
- Application Name
- Vendor
- Category (ERP, CRM, HCM, Finance, Supply Chain, BI/Analytics, Collaboration, Security, Infrastructure, Other)
- Hosting Model (On-Premise, SaaS, IaaS/Cloud-Hosted, Hybrid, Unknown)
- Business Criticality (Critical, High, Medium, Low, Unknown)
- Version (if mentioned)
- User Count (if mentioned)
- Source Document and Page

Include ALL applications mentioned, even if only referenced in passing. If information is not stated, mark as "Not documented."
```

### Prompt 1.2 - Application Details Deep Dive
```
For each application in the inventory, extract additional details where documented:
- Contract expiration date
- License type (Perpetual, Subscription, Open Source)
- License count
- Support status (Active support, Extended support, End of life)
- Customization level (Out of box, Lightly customized, Heavily customized)
- Key integrations mentioned
- Known issues or concerns mentioned
- Data residency/hosting location

Format as a table. Mark "Not documented" where information is not found.
```

---

## Phase 2: Business Capability Coverage

### Prompt 2.1 - Capability Gap Analysis
```
Assess application coverage for each business capability area. For each area below, identify:
1. Which applications cover this area (from the inventory)
2. Coverage status: Fully Documented / Partially Documented / Mentioned Not Detailed / Not Found
3. Gaps or missing information
4. Follow-up questions needed

Business Capability Areas:
- Finance & Accounting (GL, AP, AR, Expense, Treasury, Tax, Consolidation)
- Human Resources & Payroll (HRIS, Payroll, Benefits, Recruiting, Time & Attendance)
- Sales & CRM (CRM, CPQ, Sales Enablement, Contract Management)
- Marketing (Marketing Automation, CMS, Email, Analytics)
- Operations & Supply Chain (SCM, Procurement, Inventory, WMS, MES, PLM)
- IT Service Management (ITSM, Monitoring, Asset Management, Backup)
- Identity & Security (IAM, SSO, PAM, SIEM, Endpoint Protection)
- Collaboration (Email, Chat, Video, Document Management)
- Data & Analytics (BI, Data Warehouse, Reporting)
- Legal & Compliance (Contract Management, eDiscovery, GRC)

Format as a table with columns: Capability Area | Applications Found | Coverage Status | Key Gaps | Follow-up Questions
```

### Prompt 2.2 - Expected but Missing Applications
```
Based on typical IT environments for a company of this size and industry, identify applications or capabilities that would be EXPECTED but are NOT documented:

Consider:
- Is there an ERP or core financial system clearly identified?
- Is there a payroll system? (Required for any company with employees)
- Is there identity management / SSO?
- Is there backup and disaster recovery?
- Is there endpoint protection / antivirus?
- Is there a collaboration platform (email, chat)?

For each gap, note:
- What's missing
- Why it's expected (regulatory requirement, operational necessity, industry standard)
- Risk if truly absent vs. just not documented
- Recommended follow-up question
```

---

## Phase 3: Technical Health Assessment

### Prompt 3.1 - Version Currency & EOL Risk
```
For each application with a version number documented, assess:
- Current version in use
- Is this version current, approaching end-of-life, or past end-of-life?
- Latest available version from vendor
- Version gap (None, Minor, Major, Critical)
- Risk if not upgraded
- Upgrade path complexity (if known)

Flag any applications where:
- Version is more than 2 major versions behind
- Vendor has announced end-of-life
- Extended support is required
- Security patches are no longer available

Common EOL concerns to check:
- SAP ECC 6.0 (EOL 2027)
- Oracle Database 11g/12c (past EOL)
- Windows Server 2012/2012 R2 (past EOL)
- Java 8 (extended support only)
- Python 2.x (past EOL)
- .NET Framework < 4.7

Format as a table: Application | Current Version | EOL Status | Latest Version | Risk Level | Notes
```

### Prompt 3.2 - Technical Debt Indicators
```
Identify indicators of technical debt from the documents:

1. Version Debt: Outdated versions requiring upgrade
2. Customization Debt: Heavy customizations mentioned (especially for ERP/HCM)
3. Integration Debt: Point-to-point integrations, manual data transfers, batch processes
4. Architecture Debt: Monolithic systems, on-premise systems that should be cloud
5. Skills Debt: Specialized skills mentioned as scarce or single points of failure
6. Documentation Debt: Systems mentioned with no documentation provided
7. Security Debt: Missing security controls, compliance gaps

For each item found:
- Application affected
- Type of debt
- Severity (Critical, High, Medium, Low)
- Business impact
- Remediation approach (if mentioned)

Format as a table.
```

---

## Phase 4: Integration Landscape

### Prompt 4.1 - Integration Inventory
```
Document all integrations mentioned between applications:
- Source system
- Target system
- Integration type (API, File/Batch, Direct DB, Manual, iPaaS/Middleware)
- Data exchanged (if mentioned)
- Frequency (Real-time, Daily, Weekly, Manual)
- Integration platform used (if any - e.g., MuleSoft, Boomi, Informatica)

Also identify:
- Is there a central integration platform or middleware?
- Are integrations documented or tribal knowledge?
- Any integration concerns or failures mentioned?

Format as a table.
```

### Prompt 4.2 - Data Flow Analysis
```
Based on the applications and integrations identified, describe:
1. Where does master data live? (Customer, Employee, Product, Vendor, Chart of Accounts)
2. What is the system of record for key data domains?
3. Are there data quality concerns mentioned?
4. Is there a data warehouse or central reporting repository?
5. What reporting/BI tools consume data from which sources?

Identify any risks:
- Duplicate data entry across systems
- No clear system of record
- Manual data transfers
- Data reconciliation issues mentioned
```

---

## Phase 5: Risk & Considerations Summary

### Prompt 5.1 - Application Risks for Due Diligence
```
Synthesize all findings into a risk summary. For each risk:
- Risk title (concise)
- Risk description
- Severity (Critical, High, Medium, Low)
- Category: Standalone Viability / Integration Complexity / Cost / Timeline / Compliance
- Evidence (quote from documents)
- Mitigation or follow-up needed

Prioritize risks that affect:
1. Day 1 readiness (can the company operate independently?)
2. Integration complexity (what makes integration harder?)
3. Cost exposure (unbudgeted spend required)
4. Timeline risk (what could delay integration?)
5. Compliance/regulatory gaps
```

### Prompt 5.2 - Follow-up Questions
```
Based on all gaps and unknowns identified, create a prioritized list of follow-up questions:

For each question:
- Question text
- Why it matters (what risk or decision does it inform?)
- Priority (Must have before close / Important for planning / Nice to have)
- Who should answer (Target IT, Target Finance, Target HR, Management)

Group questions by:
1. Critical gaps (blocking issues)
2. Application-specific questions
3. Infrastructure questions
4. Security/compliance questions
5. Integration planning questions
```

---

## Phase 6: Buyer Comparison (if applicable)

### Prompt 6.1 - Application Overlap Analysis
```
Compare the target's application inventory to the buyer's known applications:

[INSERT BUYER'S APPLICATION LIST HERE]

For each application pair, categorize as:
- Same Product: Both use identical application (consolidation opportunity)
- Same Category, Different Vendor: Both have capability but different tools (migration decision needed)
- Target Only: Target has, buyer doesn't (absorb or retire?)
- Buyer Only: Buyer has, target doesn't (extend to target?)

For overlaps, note:
- Integration complexity
- Data migration considerations
- License implications
- Recommended approach (Consolidate to Buyer / Consolidate to Target / Run Parallel / Retire)
```

---

## Output Checklist

After running this playlist, you should have:
- [ ] Complete application inventory with all columns populated (or marked Unknown)
- [ ] Capability coverage matrix showing gaps
- [ ] EOL assessment for all versioned applications
- [ ] Technical debt inventory
- [ ] Integration map
- [ ] Prioritized risk list
- [ ] Follow-up questions for management sessions
- [ ] Buyer overlap analysis (if applicable)
