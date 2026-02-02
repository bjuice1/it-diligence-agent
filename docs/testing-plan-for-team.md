# IT Due Diligence Tool - Team Testing Plan

**Version:** 1.0
**Date:** February 2026
**Purpose:** Structured testing before leadership review

---

## 1. Testing Objectives

Validate that the tool:
1. Extracts facts accurately from VDR-style documents
2. Identifies risks and gaps appropriately
3. Generates reasonable cost estimates with transparent build-up
4. Produces professional, leadership-ready outputs (Excel, narratives)
5. Handles different deal types and industries correctly

---

## 2. Deal Type Matrix

The tool behaves differently based on deal type. **Each tester should test BOTH types.**

| Deal Type | System Setting | Key Focus Areas | What to Validate |
|-----------|---------------|-----------------|------------------|
| **Carve-out (Standalone)** | `carveout` | TSA services, standalone readiness, separation costs | TSA inventory populated, Day-1 requirements clear, separation work items generated |
| **Acquisition (Integration)** | `acquisition` | Synergies, integration planning, buyer fit | Synergy opportunities identified, integration work items generated, buyer context considered |

### What Changes by Deal Type
- Executive summary emphasis (TSA vs. synergies)
- Work item categorization (separation vs. integration)
- Cost framing (standalone build vs. integration effort)
- Narrative tone and recommendations

---

## 3. Industry Coverage Matrix

**Assign each tester a primary industry to ensure coverage:**

| Industry | Tester | Key IT Characteristics to Include |
|----------|--------|-----------------------------------|
| Healthcare | TBD | HIPAA compliance, EHR systems, medical devices, clinical apps |
| Manufacturing | TBD | OT/SCADA systems, ERP (SAP/Oracle), plant-level IT, MES |
| Financial Services | TBD | Trading platforms, regulatory systems, data security, SOX |
| Retail/Consumer | TBD | POS systems, e-commerce, supply chain, seasonal scaling |
| Technology/SaaS | TBD | Cloud-native, DevOps, SaaS sprawl, engineering headcount |
| Professional Services | TBD | Time/billing systems, document management, client data |

---

## 4. Test Scenario Templates

### 4.1 Document Set Requirements

Each test scenario should include synthetic documents covering:

**REQUIRED Documents (minimum):**
1. IT Organization Chart / Staffing Summary
2. Application Inventory (with vendor, users, criticality)
3. Infrastructure Summary (servers, cloud, network)
4. IT Budget or Cost Summary
5. Cybersecurity Overview

**OPTIONAL (for richer testing):**
- Vendor contracts / MSP agreements
- Network diagrams
- DR/BCP documentation
- Recent audit findings
- IT roadmap / strategic plan

### 4.2 Synthetic Data Guidelines

When using AI to generate test documents:

**DO:**
- Include specific numbers (headcount: 23, servers: 47, apps: 89)
- Include realistic vendor names (ServiceNow, Salesforce, Oracle, Cisco)
- Include some gaps/unknowns ("cost data not available", "pending vendor confirmation")
- Include minor inconsistencies (app count differs between docs)
- Vary document quality (some well-formatted, some raw tables)

**DON'T:**
- Create perfectly clean data with no missing information
- Use generic placeholders ("Company A", "System X")
- Make every document follow the same format
- Include only positive information (no technical debt, no risks)

### 4.3 AI Prompt Template for Test Data Generation

```
Create a realistic IT Due Diligence document set for a fictional company:

COMPANY PROFILE:
- Name: [Generate realistic name]
- Industry: [ASSIGNED INDUSTRY]
- Revenue: $[50M-500M range]
- Employees: [200-2000 range]
- IT Headcount: [15-80 range]
- Deal Type: [carveout OR acquisition]

DOCUMENT 1: IT Organization Summary
Include: Org chart, role titles, headcounts by function, reporting structure,
key person dependencies, mix of FTE vs contractors, any outsourced functions.
Include some roles with unclear reporting or missing headcount.

DOCUMENT 2: Application Inventory
Include: 30-100 applications with name, vendor, function, users, criticality,
support status. Include some legacy apps, some with expired contracts,
some with unknown ownership. Format as a table.

DOCUMENT 3: Infrastructure Overview
Include: Data center/cloud mix, server counts, network topology summary,
disaster recovery status, backup systems. Include some end-of-life hardware.

DOCUMENT 4: IT Budget Summary
Include: Annual spend by category (personnel, software, hardware, services),
vendor concentration, YoY trends. Include some items with estimated vs actual.

DOCUMENT 5: Security Posture Summary
Include: Security tools in use, compliance certifications, recent audit findings,
known vulnerabilities or gaps. Be realistic about maturity level.

FORMAT: Make documents look like real VDR extracts - some as prose, some as tables,
varying levels of detail. Include a few inconsistencies between documents.
```

---

## 5. Evaluation Criteria

### 5.1 Fact Extraction (Score 1-5)

| Rating | Description |
|--------|-------------|
| 5 | All key facts captured, accurate, properly categorized |
| 4 | Most facts captured, minor categorization issues |
| 3 | Core facts captured but significant gaps or errors |
| 2 | Many facts missed or miscategorized |
| 1 | Major extraction failures |

**What to check:**
- [ ] Headcount numbers match source documents
- [ ] Application counts are accurate
- [ ] Vendor names captured correctly
- [ ] Cost figures extracted properly
- [ ] Domain categorization makes sense

### 5.2 Risk Identification (Score 1-5)

| Rating | Description |
|--------|-------------|
| 5 | Risks are specific, actionable, tied to facts, appropriately severe |
| 4 | Good risks identified, minor severity calibration issues |
| 3 | Obvious risks found, but missed nuanced issues |
| 2 | Generic risks, poor fact linkage |
| 1 | Risks don't match the data or are completely generic |

**What to check:**
- [ ] Risks reference specific facts from documents
- [ ] Severity levels are calibrated appropriately
- [ ] M&A lens is applied (Day-1, TSA, integration)
- [ ] No hallucinated risks (invented problems not in docs)

### 5.3 Gap Identification (Score 1-5)

**What to check:**
- [ ] Gaps reflect actual missing information in docs
- [ ] Importance levels are appropriate
- [ ] VDR request suggestions are actionable
- [ ] No false gaps (claiming missing info that exists)

### 5.4 Cost Estimation (Score 1-5)

**What to check:**
- [ ] Cost ranges are plausible for company size/industry
- [ ] Build-up worksheet shows method and assumptions
- [ ] Anchor selections make sense
- [ ] No wildly unrealistic estimates

### 5.5 Output Quality (Score 1-5)

**What to check:**
- [ ] Excel export opens without errors
- [ ] All sheets are populated
- [ ] Formatting is professional
- [ ] Executive narrative is coherent
- [ ] Facts are traceable to sources

---

## 6. Test Execution Checklist

### Per Test Scenario:

**Setup:**
- [ ] Create/obtain synthetic document set
- [ ] Note company profile (industry, size, deal type)
- [ ] Start fresh deal in the tool

**Execution:**
- [ ] Upload all documents
- [ ] Run full analysis
- [ ] Note any errors or warnings during processing
- [ ] Record processing time

**Validation:**
- [ ] Review Facts page - score extraction accuracy
- [ ] Review Risks page - score risk quality
- [ ] Review Gaps page - score gap identification
- [ ] Review Cost Center - score estimate reasonableness
- [ ] Review Organization page - verify org chart renders
- [ ] Export to Excel - verify all sheets populated
- [ ] Generate narrative - verify coherence

**Documentation:**
- [ ] Complete evaluation scorecard
- [ ] Note specific bugs or issues
- [ ] Screenshot any problems
- [ ] Record suggestions for improvement

---

## 7. Bug Reporting Template

When you find an issue:

```
**Issue Title:** [Brief description]

**Severity:** Critical / High / Medium / Low

**Steps to Reproduce:**
1. [Step 1]
2. [Step 2]
3. [Step 3]

**Expected Result:** [What should happen]

**Actual Result:** [What actually happened]

**Test Scenario:** [Industry, deal type, company size]

**Screenshots:** [Attach if applicable]

**Document that triggered issue:** [Filename if specific]
```

---

## 8. Testing Schedule

| Phase | Duration | Focus | Deliverable |
|-------|----------|-------|-------------|
| **Setup** | Day 1-2 | Create synthetic data sets | 6 test scenarios ready |
| **Round 1** | Day 3-5 | Individual testing | Initial scorecards |
| **Triage** | Day 6 | Team sync, prioritize issues | Bug priority list |
| **Round 2** | Day 7-8 | Retest after fixes | Updated scorecards |
| **Final Report** | Day 9-10 | Compile findings | Leadership-ready summary |

---

## 9. Success Criteria for Leadership Review

**Minimum bar to proceed:**
- [ ] Average extraction score >= 4.0 across all scenarios
- [ ] Average risk score >= 3.5 across all scenarios
- [ ] No critical bugs remaining
- [ ] Excel export works for all scenarios
- [ ] Org chart renders for scenarios with org data
- [ ] Cost estimates within reasonable range for all scenarios

**Nice to have:**
- [ ] Average scores >= 4.0 across all categories
- [ ] Consistent performance across industries
- [ ] Carveout vs. acquisition outputs are clearly differentiated

---

## 10. Tester Assignment Template

| Tester Name | Primary Industry | Deal Type 1 | Deal Type 2 | Notes |
|-------------|-----------------|-------------|-------------|-------|
| [Name 1] | Healthcare | Carveout | Acquisition | |
| [Name 2] | Manufacturing | Acquisition | Carveout | |
| [Name 3] | Financial Services | Carveout | Acquisition | |
| [Name 4] | Retail | Acquisition | Carveout | |
| [Name 5] | Technology/SaaS | Carveout | Acquisition | |
| [Name 6] | Prof Services | Acquisition | Carveout | |

---

## Appendix A: Sample Evaluation Scorecard

**Test Scenario ID:** _______________
**Tester:** _______________
**Date:** _______________

**Company Profile:**
- Name: _______________
- Industry: _______________
- Revenue: _______________
- IT Headcount: _______________
- Deal Type: _______________

**Scores (1-5):**

| Category | Score | Notes |
|----------|-------|-------|
| Fact Extraction | | |
| Risk Identification | | |
| Gap Identification | | |
| Cost Estimation | | |
| Output Quality | | |
| **AVERAGE** | | |

**Bugs Found:** (list issue IDs)

**Top 3 Observations:**
1.
2.
3.

**Recommendation:** Ready for leadership / Needs fixes first

---

## Appendix B: Quick Reference - Tool Features to Test

1. **Document Upload** - Multiple file formats
2. **Facts View** - Filtering, verification, drill-down
3. **Risks View** - Severity, domain filtering
4. **Gaps View** - VDR request generation
5. **Organization** - Census view, Org chart view
6. **Cost Center** - Build-up worksheet, summary
7. **Excel Export** - All sheets, formatting
8. **Narrative Generation** - Executive summary coherence
9. **Deal Context** - Industry/deal type effects
