# CloudServe Test Scenario - Validation Guide

## Purpose

This guide explains how to use the `expected_facts_cloudserve_validation.json` file to proof-check automated IT due diligence analysis runs against known "right answers."

---

## Test Scenario Overview

**Deal:** CloudServe Technologies (Target) acquired by Enterprise Solutions Group (ESG, Buyer)

**Documents:**
- **6 Target documents** (CloudServe Technologies): Executive profile, applications, infrastructure, network/security, IAM, organization/vendors
- **6 Buyer documents** (ESG): IT profile, application standards, infrastructure standards, security requirements, IAM requirements, org model

**Total:** 12 documents across all 6 IT DD domains

---

## What's in the Validation File

The `expected_facts_cloudserve_validation.json` contains ground-truth data structured as:

### 1. **Expected Inventory Counts**
```json
{
  "target": {
    "applications": { "total": 38 },
    "infrastructure": { "aws_accounts": 9 },
    "organization": { "total_it_headcount": 67 },
    "vendors": { "total_vendors": 32 }
  }
}
```

**Test:** Automated extraction should match these exact counts.

---

### 2. **Expected Key Metrics**
```json
{
  "target_company": {
    "annual_revenue": 87000000,
    "it_budget": { "total_annual": 14200000 },
    "cloud_spend": { "aws_annual": 4800000 }
  }
}
```

**Test:** Discovery agents should extract these financial metrics accurately.

---

### 3. **Expected Critical Risks** (8 risks)
```json
{
  "risk_id": "RISK-001",
  "title": "SOC 2 Renewal Due in 4 Months",
  "severity": "HIGH",
  "estimated_cost": { "min": 100000, "max": 150000 }
}
```

**Risks that MUST be detected:**
- SOC 2 renewal urgency (4 months)
- Wiz CSPM contract expiring (2 months)
- DR test failure
- GDPR data residency gap
- CTO key person risk
- MFA coverage gap
- No ISO 27001
- Vulnerability remediation backlog

**Test:** Reasoning agents should flag all 8 high/medium severity risks.

---

### 4. **Expected Compliance Status**
```json
{
  "soc2_type2": { "status": "CERTIFIED", "months_until_renewal": 4 },
  "iso27001": { "status": "NOT_CERTIFIED", "gap": true },
  "gdpr": { "status": "SELF_ASSESSED", "formal_audit": false }
}
```

**Test:** Compliance analysis should correctly identify certifications and gaps.

---

### 5. **Expected Contract Expirations** (3 urgent)
```json
{
  "vendor": "Wiz",
  "contract_end": "2025-02",
  "months_until_expiration": 0,
  "alert": "URGENT - Expires in 2 months"
}
```

**Contracts expiring soon:**
- Wiz (2 months) - $125K/year
- Datadog (3 months) - $312K/year
- Fastly (3 months) - $85K/year

**Test:** Contract risk detection should flag these expirations.

---

### 6. **Expected Integration Gaps** (8 gaps)
```json
{
  "gap_id": "GAP-001",
  "title": "Okta to Azure AD Migration",
  "complexity": "HIGH",
  "estimated_cost": { "min": 100000, "max": 200000 }
}
```

**Integration gaps (Target vs Buyer standards):**
- Okta → Azure AD (workforce IdP)
- Auth0 → Azure AD B2C (customer IdP, CRITICAL complexity)
- AWS → Azure migration strategy
- Datadog → Splunk
- NetSuite → SAP S/4HANA (ERP)
- Salesforce → Dynamics 365 (CRM)
- Google Workspace → Microsoft 365
- ISO 27001 certification needed

**Test:** Gap analysis should identify all 8 misalignments.

---

### 7. **Expected Cost Estimates**
```json
{
  "one_time_integration_costs": {
    "total": { "min": 3025000, "max": 6475000 }
  },
  "annual_cost_savings_opportunities": {
    "total_potential_savings": { "min": 2195000, "max": 2735000 }
  }
}
```

**One-time costs breakdown:**
- Security remediation: $250K-500K
- Compliance certification: $100K-150K
- DR capability: $75K-125K
- Identity integration: $300K-600K
- EU data residency: $250K-500K
- Application migrations: $1.5M-3M
- Retention bonuses: $500K-1M

**Annual savings opportunities:**
- AWS Reserved Instances/Savings Plans: $1M-1.65M
- Vendor consolidation: $965K

**Test:** Cost synthesis should aggregate to these totals.

---

### 8. **Expected VDR Requests** (10 requests)
```json
{
  "vdr_id": "VDR-001",
  "domain": "infrastructure",
  "title": "Network Architecture Diagrams",
  "priority": "HIGH",
  "reason": "Gap identified in Document 3"
}
```

**VDR requests that should be generated:**
1. Network architecture diagrams
2. DR runbooks
3. AWS IAM policies export
4. 12-month AWS cost reports
5. Penetration test report
6. Vulnerability scan reports
7. Vendor contracts (top 15)
8. Compensation benchmarking
9. Access review reports
10. Infrastructure incident log

**Test:** VDR generation should produce at least these 10 requests.

---

### 9. **Expected Cross-Document Consistency** (10 validations)
```json
{
  "fact": "Total applications",
  "expected_value": 38,
  "appears_in": ["Document 1", "Document 2"],
  "should_match": true
}
```

**Facts that appear in multiple documents (should be consistent):**
- Total applications: 38 (Doc 1, Doc 2)
- AWS accounts: 9 (Doc 1, Doc 3)
- AWS annual spend: $4.8M (Doc 1, Doc 3)
- IT headcount: 67 (Doc 1, Doc 6)
- SOC 2 renewal: 4 months (Doc 1, Doc 4)
- DR strategy: Warm standby (Doc 1, Doc 3)
- RPO/RTO: 4h/8h (Doc 1, Doc 3)
- MFA coverage: 85% (Doc 4, Doc 5)

**Test:** System should NOT flag inconsistencies (all facts are intentionally aligned).

---

### 10. **Expected Work Items** (by phase)
```json
{
  "day_1": [
    { "title": "Renew Wiz CSPM contract", "priority": "CRITICAL" },
    { "title": "Accelerate SOC 2 renewal audit", "priority": "HIGH" }
  ],
  "day_100": [...],
  "post_100": [...]
}
```

**Work items by integration phase:**
- **Day 1** (3 items): Wiz renewal, SOC 2 acceleration, CTO retention
- **Day 100** (4 items): DR testing, EU region, ISO 27001, MFA enforcement
- **Post-100** (5 items): Identity migrations, application migrations, AWS cost optimization

**Test:** Work item generation should create items across all 3 phases.

---

## How to Run Validation

### Step 1: Run Full Analysis
```bash
cd "9.5/it-diligence-agent 2"

# Run full pipeline on CloudServe documents
python main_v2.py data/input/ --all --narrative --target-name "CloudServe Technologies"
```

This will generate:
- `output/facts/facts_TIMESTAMP.json`
- `output/findings/findings_TIMESTAMP.json`
- `output/reports/report_TIMESTAMP.html`

---

### Step 2: Compare Against Expected Facts

**(Option A) Manual Comparison:**
```bash
# Open expected facts
cat data/input/expected_facts_cloudserve_validation.json

# Open actual output
cat output/facts/facts_TIMESTAMP.json

# Compare key metrics
```

**(Option B) Automated Validation (if /itddcheck exists):**
```bash
/itddcheck \
  --expected data/input/expected_facts_cloudserve_validation.json \
  --actual output/facts/facts_TIMESTAMP.json \
  --findings output/findings/findings_TIMESTAMP.json
```

Expected output:
```
✅ Inventory counts: PASS (38/38 applications)
✅ Key metrics: PASS (AWS spend $4.8M)
⚠️ Risk detection: PARTIAL (7/8 risks detected)
❌ VDR requests: FAIL (8/10 generated)

Overall Score: 87% accuracy
```

---

### Step 3: Validate Specific Areas

#### **A. Inventory Counts**
```json
"test_assertions": {
  "inventory_counts": {
    "assertions": [
      { "test": "Target applications count", "expected": 38, "tolerance": 0 },
      { "test": "Target AWS accounts", "expected": 9, "tolerance": 0 },
      { "test": "Target IT headcount", "expected": 67, "tolerance": 0 }
    ]
  }
}
```

**Check:**
- Target applications = 38 (EXACT)
- Target AWS accounts = 9 (EXACT)
- Target IT headcount = 67 (EXACT)
- Target vendors ≈ 32 (±2 tolerance)

---

#### **B. Risk Detection**
```json
"risk_detection": {
  "assertions": [
    { "test": "SOC 2 renewal flagged", "expected": true, "severity": "HIGH" },
    { "test": "Wiz expiration flagged", "expected": true, "severity": "HIGH" },
    { "test": "DR test failure flagged", "expected": true, "severity": "HIGH" }
  ]
}
```

**Check:**
- SOC 2 renewal flagged as HIGH risk? ✅
- Wiz expiration flagged as HIGH risk? ✅
- DR test failure flagged as HIGH risk? ✅
- GDPR gap flagged as HIGH risk? ✅

---

#### **C. Entity Separation**
```json
"entity_separation": {
  "assertions": [
    { "test": "Target inventory items have entity=target", "expected": true },
    { "test": "Buyer standards not counted as Target inventory", "expected": true },
    { "test": "UI shows separate Target/Buyer counts", "expected": true }
  ]
}
```

**Check:**
- All Target inventory items have `entity: "target"` field? ✅
- Buyer documents don't inflate Target counts? ✅
- UI shows separate dropdowns/filters for Target vs Buyer? ✅

---

#### **D. Cost Accuracy**
```json
"cost_accuracy": {
  "assertions": [
    { "test": "AWS annual spend", "expected": 4800000, "tolerance_percent": 0 },
    { "test": "Total application cost", "expected": 2331500, "tolerance_percent": 1 },
    { "test": "One-time integration cost range", "expected_min": 3025000, "expected_max": 6475000 }
  ]
}
```

**Check:**
- AWS spend = $4,800,000? (exact)
- App costs = $2,331,500? (±1% tolerance)
- One-time costs in range $3M-6.5M? (±5% tolerance)

---

## Common Validation Failures

### ❌ **Inventory Count Mismatch**
**Symptom:** Target apps = 76 (expected 38)

**Likely cause:**
- Counting facts instead of inventory items
- Not filtering by entity (mixing Target + Buyer)
- Deterministic parser creating duplicates

**Fix:** Query InventoryStore filtered by `entity="target"`, not FactStore.

---

### ❌ **Risk Not Detected**
**Symptom:** SOC 2 renewal risk missing from findings

**Likely cause:**
- Reasoning agent didn't parse "4 months" timeframe
- Risk severity threshold too high
- Prompt doesn't include contract expiration guidance

**Fix:** Check reasoning prompts for contract risk detection logic.

---

### ❌ **Entity Separation Broken**
**Symptom:** Target count = 38 apps, Buyer count = 0

**Likely cause:**
- Entity field missing/null in database
- Default entity = "target" silently applied
- Fingerprint not including entity (cross-entity merging)

**Fix:** Enforce entity as NOT NULL, include in inventory fingerprints.

---

### ❌ **Cost Aggregation Wrong**
**Symptom:** Total costs = $0 or wildly off

**Likely cause:**
- Cost fields not parsed from tables
- Cost synthesis agent didn't run
- Currency parsing issues ("$4.8M" vs. 4800000)

**Fix:** Check cost field extraction in deterministic parser, verify synthesis agent ran.

---

## Expected Report Quality

The generated HTML report should include:

### **Executive Summary**
```
CloudServe Technologies operates a cloud-native SaaS platform with 67 IT staff
supporting $87M in annual revenue. The IT environment is 100% AWS-based with modern
infrastructure (Kubernetes, serverless). Key risks include upcoming compliance renewals
(SOC 2 in 4 months, Wiz CSPM in 2 months), unproven disaster recovery capability
(last test failed), and GDPR data residency gaps (no EU region). Estimated one-time
integration costs range from $3M-6.5M, primarily driven by security remediation,
identity migrations, and EU data residency deployment.
```

### **Top 5 Risks**
1. SOC 2 renewal in 4 months (customer retention risk)
2. Wiz contract expiration in 2 months (security visibility gap)
3. DR capability unproven (last test failed 14 months ago)
4. GDPR data residency non-compliance (no EU region)
5. CTO retention risk (co-founder with concentrated knowledge)

### **Cost Summary**
- **One-time costs:** $3M-6.5M
- **Annual savings:** $2.2M-2.7M
- **Net investment:** $0.3M-4.3M (year 1)

---

## Validation Checklist

Use this checklist to validate automation output:

### **Inventory Extraction**
- [ ] Target applications = 38
- [ ] Target AWS accounts = 9
- [ ] Target IT headcount = 67
- [ ] Target vendors ≈ 32 (±2)
- [ ] Buyer documents don't inflate Target counts

### **Risk Detection**
- [ ] SOC 2 renewal (4 months) flagged as HIGH
- [ ] Wiz expiration (2 months) flagged as HIGH
- [ ] DR test failure flagged as HIGH
- [ ] GDPR gap flagged as HIGH
- [ ] CTO retention flagged as HIGH
- [ ] MFA gap flagged as MEDIUM
- [ ] ISO 27001 gap flagged as MEDIUM
- [ ] Vulnerability backlog flagged as MEDIUM

### **Compliance Analysis**
- [ ] SOC 2 Type II = CERTIFIED
- [ ] ISO 27001 = NOT CERTIFIED (gap)
- [ ] GDPR = SELF-ASSESSED (gap)
- [ ] PCI-DSS = NOT APPLICABLE

### **Contract Risk Detection**
- [ ] Wiz expiring in 2 months detected
- [ ] Datadog expiring in 3 months detected
- [ ] Fastly expiring in 3 months detected

### **Integration Gap Analysis**
- [ ] Okta → Azure AD gap detected
- [ ] Auth0 → Azure AD B2C gap detected (CRITICAL complexity)
- [ ] AWS → Azure strategy documented
- [ ] Datadog → Splunk consolidation opportunity
- [ ] NetSuite → SAP S/4HANA migration needed
- [ ] Salesforce → Dynamics 365 migration needed
- [ ] Google Workspace → M365 migration needed
- [ ] ISO 27001 certification gap detected

### **Cost Estimates**
- [ ] AWS spend = $4,800,000
- [ ] App costs = $2,331,500
- [ ] IT personnel costs = $6,900,000
- [ ] One-time integration costs = $3M-6.5M
- [ ] Annual savings opportunities = $2.2M-2.7M

### **VDR Requests**
- [ ] Network diagrams requested
- [ ] DR runbooks requested
- [ ] AWS IAM policies export requested
- [ ] AWS cost reports requested
- [ ] Pentest report requested
- [ ] Vulnerability scans requested
- [ ] Vendor contracts requested
- [ ] Compensation data requested
- [ ] Access review reports requested
- [ ] Incident log requested

### **Cross-Document Consistency**
- [ ] No inconsistencies flagged (all facts aligned)
- [ ] Applications count matches across Doc 1 & Doc 2
- [ ] AWS accounts match across Doc 1 & Doc 3
- [ ] IT headcount matches across Doc 1 & Doc 6

### **Entity Separation**
- [ ] UI shows separate Target/Buyer filters
- [ ] Target inventory has entity="target"
- [ ] Buyer documents don't create inventory items
- [ ] Database entity field is NOT NULL

---

## Success Criteria

**Passing grades:**
- **Inventory extraction:** 95%+ accuracy (exact counts)
- **Risk detection:** 100% (all 8 risks flagged)
- **Compliance analysis:** 100% (all statuses correct)
- **Contract risks:** 100% (all 3 expirations detected)
- **Integration gaps:** 87.5%+ (7/8 gaps detected)
- **Cost estimates:** 90%+ accuracy (±10% tolerance)
- **VDR requests:** 80%+ (8/10 requests generated)
- **Entity separation:** 100% (no cross-entity contamination)

**Overall score:** **90%+ = PASS**

---

## Troubleshooting

### Issue: "Inventory counts are double"
**Root cause:** Counting facts instead of inventory items

**Fix:**
```python
# WRONG - counts facts (duplicates)
count = len([f for f in fact_store.facts if f.domain == "applications"])

# CORRECT - counts inventory items
count = len(inventory_store.get_items(entity="target", item_type="application"))
```

---

### Issue: "Buyer documents creating Target inventory"
**Root cause:** Entity field missing or defaulting to "target"

**Fix:**
```python
# Enforce entity as required field
class InventoryItem:
    entity: str  # "target" or "buyer" - REQUIRED

# Check fingerprint includes entity
def fingerprint(item):
    return hash(f"{item.entity}:{item.name}:{item.category}")
```

---

### Issue: "Risks not being detected"
**Root cause:** Reasoning prompt doesn't include contract expiration guidance

**Fix:** Update reasoning prompts to include:
```
RISK DETECTION GUIDANCE:
- Contracts expiring within 3 months = HIGH risk
- Compliance certifications expiring within 6 months = HIGH risk
- Failed DR tests within 12 months = HIGH risk
- Key person dependencies = HIGH risk
```

---

## Next Steps

1. **Run full analysis** on CloudServe test scenario
2. **Compare output** against this validation file
3. **Document discrepancies** in an issue tracker
4. **Fix root causes** (parser, prompts, entity handling)
5. **Re-run and validate** until 90%+ pass rate
6. **Automate validation** via `/itddcheck` command

---

**Questions?** See `CLAUDE.md` for architecture details or `audits/` for known issues and fixes.
