# Test Document Set for Leadership Demo

## Overview

This directory contains a complete, realistic test dataset for demonstrating the IT due diligence tool to leadership. The documents showcase a fictional M&A transaction with comprehensive IT details across all 6 domains.

**Deal Scenario:**
- **Target:** CloudServe Technologies (B2B SaaS platform, $87M revenue)
- **Buyer:** Enterprise Solutions Group (ESG) (Enterprise software giant, $12.4B revenue)
- **Deal Type:** Platform acquisition + customer base expansion
- **Industry:** Enterprise SaaS (different from existing Great Insurance dataset)

---

## Document Inventory

### TARGET COMPANY (CloudServe Technologies) - 6 Documents

| Document | Filename | Purpose |
|---|---|---|
| **Doc 1** | `Target_CloudServe_Document_1_Executive_IT_Profile.md` | Executive summary, budget, metrics, deal context |
| **Doc 2** | `Target_CloudServe_Document_2_Application_Inventory.md` | 38 applications (8 platform components + 30 business apps) |
| **Doc 3** | `Target_CloudServe_Document_3_Infrastructure_Hosting_Inventory.md` | AWS infrastructure (9 accounts, EKS, databases, networking) |
| **Doc 4** | `Target_CloudServe_Document_4_Network_Cybersecurity_Inventory.md` | Network architecture, security tools, compliance status |
| **Doc 5** | `Target_CloudServe_Document_5_Identity_Access_Management.md` | Okta (workforce), Auth0 (customer), MFA, PAM, access governance |
| **Doc 6** | `Target_CloudServe_Document_6_Organization_Vendor_Inventory.md` | 67 IT staff (role-level detail), vendor contracts, org structure |

### BUYER COMPANY (ESG) - 6 Documents

| Document | Filename | Purpose |
|---|---|---|
| **Doc 1** | `Buyer_ESG_Document_1_IT_Profile_Integration_Standards.md` | Buyer IT landscape, M&A philosophy, integration standards |
| **Doc 2** | `Buyer_ESG_Document_2_Application_Portfolio_Standards.md` | ESG standard apps, overlap analysis, migration priorities |
| **Doc 3** | `Buyer_ESG_Document_3_Infrastructure_Cloud_Standards.md` | Azure-first strategy, cloud standards, integration requirements |
| **Doc 4** | `Buyer_ESG_Document_4_Security_Compliance_Requirements.md` | Security baseline (SIEM, PAM, CSPM), compliance mandates |
| **Doc 5** | `Buyer_ESG_Document_5_IAM_Standards_Requirements.md` | Azure AD standards, Okta→Azure AD migration, PAM requirements |
| **Doc 6** | `Buyer_ESG_Document_6_Org_Model_Approved_Vendors.md` | ESG org structure, approved vendor list, integration approach |

---

## What This Dataset Demonstrates

### 1. **Documentation Gaps** (System will identify these)

| Gap Type | Example | Where |
|---|---|---|
| **Missing info** | Network diagrams not provided | Doc 4 |
| **Incomplete coverage** | DR runbooks only 40% complete | Doc 1, Doc 3 |
| **Unaudited compliance** | GDPR/CCPA self-assessed (no formal audit) | Doc 4 |
| **Undocumented integrations** | API integrations with customer systems | Doc 2 |
| **Missing contracts** | Vendor contract details not provided | Doc 6 |

**Expected Output:** System should generate VDR (Virtual Data Room) requests for missing information.

---

### 2. **Risks for Management Attention**

| Risk Category | Specific Risk | Severity | Where |
|---|---|---|---|
| **Security** | SOC 2 renewal due in 4 months | 🔴 HIGH | Doc 1, Doc 4 |
| **Security** | Wiz (CSPM) contract expiring in 2 months | 🔴 HIGH | Doc 2, Doc 4 |
| **Compliance** | No ISO 27001 certification | 🟠 MEDIUM | Doc 4 |
| **DR capability** | Last DR test failed 14 months ago | 🔴 HIGH | Doc 1, Doc 3 |
| **Data sovereignty** | All data in US (GDPR risk - no EU region) | 🔴 HIGH | Doc 1, Doc 3 |
| **Key person** | CTO is co-founder with deep knowledge | 🟠 MEDIUM | Doc 1, Doc 6 |
| **Identity** | 15% of users (62 people) without MFA | 🟠 MEDIUM | Doc 5 |
| **Vendor lock-in** | Auth0 embedded in platform architecture | 🟠 MEDIUM | Doc 2, Doc 5 |

**Expected Output:** System should flag these risks with severity ratings and mitigation recommendations.

---

### 3. **One-Time Cost Items**

| Cost Category | Description | Estimated Cost | Where |
|---|---|---:|---|
| **Security remediation** | ISO 27001, GDPR/CCPA audits, gap closure | $250K-500K | Doc 1 |
| **Compliance certification** | SOC 2 renewal acceleration | $100K-150K | Doc 1, Doc 4 |
| **DR capability build** | Runbook completion, testing, validation | $75K-125K | Doc 1, Doc 3 |
| **Infrastructure standardization** | AWS account restructure, governance | $50K-100K | Doc 3 |
| **Identity integration** | Okta → Azure AD migration | $100K-200K | Doc 5, Buyer Doc 5 |
| **Customer IdP migration** | Auth0 → Azure AD B2C | $200K-400K | Doc 5, Buyer Doc 5 |
| **EU data residency** | Deploy EU region for GDPR | $250K-500K | Doc 3, Buyer Doc 3 |
| **Application migrations** | ERP, CRM, collaboration tools | $1.5M-3M | Buyer Doc 2 |
| **Retention bonuses** | Key technical leaders | $500K-1M | Doc 6, Buyer Doc 6 |
| **TOTAL** | | **$3M-6.5M** | Various |

**Expected Output:** System should aggregate costs by category and provide range estimates.

---

### 4. **Report Language Quality**

The system should generate professional, board-ready language like:

**Example - Executive Summary:**
> "CloudServe Technologies operates a cloud-native SaaS platform with 67 IT staff supporting $87M in annual revenue. The IT environment is 100% AWS-based with modern infrastructure (Kubernetes, serverless). Key risks include upcoming compliance renewals (SOC 2 in 4 months, Wiz CSPM in 2 months), unproven disaster recovery capability (last test failed), and GDPR data residency gaps (no EU region). Estimated one-time integration costs range from $3M-6.5M, primarily driven by security remediation ($250K-500K), compliance certifications ($100K-150K), identity migrations ($300K-600K), and EU data residency deployment ($250K-500K). Talent retention is critical, particularly for the co-founder CTO who holds deep architectural knowledge."

**Example - Risk Summary:**
> "Five high-severity risks require immediate attention: (1) SOC 2 renewal in 4 months poses customer retention risk; (2) Wiz contract expiration in 2 months creates cloud security visibility gap; (3) unproven DR capability (last test failed 14 months ago); (4) GDPR data residency non-compliance (all customer data in US region); (5) CTO retention risk (co-founder with concentrated knowledge). Recommended mitigation: accelerate SOC 2 audit ($100K-150K), renew Wiz urgently ($125K/year), execute DR validation test ($75K-125K), deploy EU region ($250K-500K), and secure CTO retention agreement ($500K-1M)."

---

## Key Features Demonstrated

### ✅ Entity Separation (Target vs. Buyer)

- **Target documents** have `# Entity: TARGET` in headers
- **Buyer documents** have `# Entity: BUYER` in headers
- Filenames use `Target_CloudServe_*` and `Buyer_ESG_*` prefixes
- System should correctly separate target inventory from buyer standards

**Test:** UI should show separate counts for "Target" and "Buyer" entities.

---

### ✅ Complete Inventory Tables

All documents have properly formatted markdown tables that the deterministic parser can extract:

**Applications (Doc 2):**
```markdown
| Application | Vendor | Category | Version | Hosting | Users | Annual Cost | Criticality | Contract End | Notes |
```

**Infrastructure (Doc 3):**
```markdown
| Account Name | Account ID | Purpose | Environment | Monthly Cost |
```

**Organization (Doc 6):**
```markdown
| Role | Team | Reports To | Headcount | FTE | Location | Avg Salary | Total Cost |
```

**Vendors (Doc 6):**
```markdown
| Vendor | Category | Services Provided | Annual Spend | Contract Start | Contract End | Auto-Renew | Termination Notice |
```

---

### ✅ Cross-Document Consistency

Key facts are consistent across documents to validate reconciliation:

| Fact | Value | Appears In |
|---|---:|---|
| Total applications | 38 | Doc 1, Doc 2 |
| AWS accounts | 9 | Doc 1, Doc 3 |
| AWS annual spend | $4.8M | Doc 1, Doc 3 |
| IT headcount | 67 | Doc 1, Doc 6 |
| SOC 2 renewal | 4 months | Doc 1, Doc 4 |
| DR strategy | Warm standby | Doc 1, Doc 3 |
| RPO / RTO | 4h / 8h | Doc 1, Doc 3 |

**Test:** System should NOT flag inconsistencies between these documents.

---

### ✅ Intentional Gaps & Edge Cases

| Gap Type | Example | Purpose |
|---|---|---|
| **Contract expiring soon** | Wiz (2 months), Datadog (3 months) | Test contract risk flagging |
| **Compliance gaps** | No ISO 27001, GDPR unaudited | Test compliance requirement detection |
| **MFA coverage gap** | 85% (62 users without MFA) | Test security control gaps |
| **Privileged access gap** | 26 users not in PAM | Test privileged access analysis |
| **Failed DR test** | Last test failed 14 months ago | Test BCDR capability assessment |
| **Data residency** | No EU region (GDPR risk) | Test regulatory compliance analysis |
| **Vendor lock-in** | Auth0 embedded in platform | Test migration complexity assessment |

---

## How to Run the Demo

### 1. Run Full Pipeline (Command Line)

```bash
cd "9.5/it-diligence-agent 2"

# Full analysis with narratives (best quality output)
python main_v2.py data/input/ --all --narrative --target-name "CloudServe Technologies"

# Quick analysis (no narratives)
python main_v2.py data/input/ --all --target-name "CloudServe Technologies"
```

### 2. Run via Web UI

```bash
cd "9.5/it-diligence-agent 2"
python -m web.app
# Navigate to http://localhost:5001
# Create new deal "CloudServe Technologies"
# Upload documents (or point to data/input/)
# Run analysis
```

### 3. Expected Outputs

| Output | Location | What to Show Leadership |
|---|---|---|
| **Facts extracted** | `output/facts/facts_TIMESTAMP.json` | Raw data extraction (6 domains) |
| **Findings generated** | `output/findings/findings_TIMESTAMP.json` | Risks, work items, costs |
| **HTML report** | `output/reports/report_TIMESTAMP.html` | Professional formatted report |
| **Excel workbook** | `output/reports/workbook_TIMESTAMP.xlsx` | Detailed analysis tables |
| **VDR requests** | `output/vdr/vdr_requests_TIMESTAMP.json` | Follow-up data requests |
| **Web UI** | `http://localhost:5001/deals/{deal_id}` | Interactive dashboard |

---

## UI Screens to Show

### 1. **Dashboard Overview**
- Total applications: **38**
- Total infrastructure: **9 AWS accounts**
- Total IT headcount: **67**
- Entity breakdown: **Target vs. Buyer**

### 2. **Application Inventory**
- Sortable table with 38 applications
- Category breakdown (8 categories)
- Cost rollup ($2.85M total)
- Criticality distribution

### 3. **Infrastructure Inventory**
- AWS accounts (9)
- Cloud spend ($4.8M/year)
- Region distribution (us-east-1 primary, eu-west-1 DR)

### 4. **Risk Dashboard**
- High-severity risks highlighted (SOC 2, Wiz, DR, GDPR)
- Risk categorization (security, compliance, operational)
- Mitigation recommendations

### 5. **Cost Estimates**
- One-time costs: $3M-6.5M
- Annual savings opportunities: $800K-1.3M (vendor consolidation)
- Cost breakdown by category

### 6. **Organization Chart**
- 67 IT staff across 7 teams
- Role-level detail with reporting structure
- Key person dependencies (CTO)

### 7. **Vendor Inventory**
- Complete vendor list with contracts
- Contract expiration tracking
- Vendor consolidation opportunities

---

## Questions Leadership Will Ask

### Q1: "How accurate is this?"

**Answer:**
- "The system uses deterministic table parsing for structured data (100% accuracy on clean tables)"
- "AI agents cross-validate facts across documents and flag inconsistencies"
- "We've intentionally included edge cases (expiring contracts, compliance gaps) to test the system's detection capabilities"

### Q2: "How long does it take to run?"

**Answer:**
- "Full analysis (6 domains, 12 documents): 8-12 minutes"
- "Quick analysis (no narratives): 4-6 minutes"
- "Discovery phase uses Haiku (cheap/fast), reasoning uses Sonnet (capable)"

### Q3: "What's the business case?"

**Answer:**
- "Traditional IT DD: 2-4 weeks, $50K-150K (consultants)"
- "This tool: <15 minutes, $5-10 in API costs"
- "Use case: Pre-LOI screening (multiple targets in parallel), post-LOI deep dive acceleration"

### Q4: "What if documents are missing?"

**Answer:**
- "System generates VDR (Virtual Data Room) requests for gaps"
- "Example: Missing network diagrams, incomplete BCDR runbooks, vendor contract details"
- "Partial analysis still valuable for go/no-go decisions"

### Q5: "Can it compare target to buyer standards?"

**Answer:**
- "Yes - buyer documents define integration standards (Azure, Dynamics 365, ISO 27001, etc.)"
- "System flags gaps (Okta→Azure AD migration, no ISO, GDPR non-compliance)"
- "Provides migration timelines and cost estimates"

### Q6: "How does it handle different industries?"

**Answer:**
- "We have 2 complete test datasets: Insurance (Great Insurance) and SaaS (CloudServe)"
- "Category mappings handle industry-specific apps (Duck Creek for insurance, Salesforce for SaaS)"
- "Works across any industry with IT infrastructure"

---

## Troubleshooting

### If counts are wrong (e.g., 0 applications)

**Check:**
1. Entity field populated correctly (`target` or `buyer`)
2. Tables parsed successfully (check logs for "deterministic_parser")
3. InventoryStore queries filtering by `deal_id` and `entity`

### If risks are missing

**Check:**
1. Reasoning phase completed (check `findings_*.json`)
2. Narrative agents ran (if using `--narrative`)
3. Gap detection logic triggered (contract expirations, compliance gaps)

### If costs are zero

**Check:**
1. Cost fields populated in application tables (`Annual Cost` column)
2. Cost aggregation in findings (check `cost_estimate` fields)
3. Cost synthesis agent ran (if using `--narrative`)

---

## Next Steps After Demo

If leadership approves:

1. **Production testing:** Run against real deal documents (anonymized)
2. **UI refinement:** Based on leadership feedback
3. **Integration:** Connect to deal management system
4. **Scaling:** Multi-deal parallel processing
5. **Customization:** Industry-specific templates and risk frameworks

---

**Questions?** Check `CLAUDE.md` for full system architecture and testing guidance.
