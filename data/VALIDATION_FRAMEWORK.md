# IT Due Diligence Agent - Validation Framework

## Purpose

This framework provides a systematic approach to validating the IT DD Agent's output quality. Use this when testing against synthetic scenarios or real deals.

---

## Test Scenarios Overview

| Scenario | File | Purpose | Expected Behavior |
|----------|------|---------|-------------------|
| **1. Clean Modern** | `scenario_1_clean_modern.txt` | Test for FALSE POSITIVES | Few risks, high maturity |
| **2. Legacy Nightmare** | `scenario_2_legacy_nightmare.txt` | Test MAXIMUM DETECTION | Many critical risks, all complexity signals |
| **3. Carveout** | `scenario_3_carveout.txt` | Test TSA/SEPARATION | Entanglement, Day 1 risks |
| **4. Healthcare** | `scenario_4_healthcare.txt` | Test INDUSTRY PATTERNS | HIPAA, PHI, medical devices |
| **5. Financial Services** | `scenario_5_financial_services.txt` | Test REGULATORY | SOX, PCI, core banking |
| **6. Acme Manufacturing** | `synthetic_it_discovery_v1.txt` | BASELINE scenario | Mixed complexity |

---

## Scoring Rubric

### 1. Detection Accuracy (40 points)

#### A. True Positives (20 points)
Did the system correctly identify known risks?

| Scenario | Must Detect | Points |
|----------|-------------|--------|
| **Clean Modern** | Few/no risks | 4 pts if <5 risks flagged |
| **Legacy Nightmare** | EOL systems, DR gap, key person, dual ERP | 4 pts if >30 risks |
| **Carveout** | TSA dependency, parent entanglement, Day 1 | 4 pts if TSA mentioned |
| **Healthcare** | HIPAA gaps, medical devices, PHI | 4 pts if industry detected |
| **Financial** | SOX, PCI, regulatory findings, core banking | 4 pts if regulatory flags |

#### B. False Positives (10 points)
Did the system flag things that shouldn't be flagged?

| Test | Scoring |
|------|---------|
| Clean Modern scenario has <5 risks | 5 pts |
| Risks are evidence-linked (not hallucinated) | 5 pts |

#### C. Severity Calibration (10 points)
Are severity ratings appropriate?

| Test | Scoring |
|------|---------|
| Critical risks are truly critical | 5 pts |
| Low risks are truly low | 5 pts |

### 2. Complexity Signal Detection (20 points)

#### A. Infrastructure Signals (4 points)
| Signal | Pattern | Expected In |
|--------|---------|-------------|
| Legacy Systems | AS/400, Windows 2003/2008, COBOL | Scenarios 2, 5, 6 |
| Single Point of Failure | No DR, single DC, no backup | Scenarios 2, 6 |
| High Customization | Custom code, proprietary | Scenarios 2, 4, 5 |
| Technical Debt | Deferred maintenance | Scenarios 2, 6 |

Score: Count signals detected / Total expected × 4

#### B. Application Signals (4 points)
| Signal | Pattern | Expected In |
|--------|---------|-------------|
| Dual ERP | SAP + Oracle, multiple ERPs | Scenario 2 |
| Shadow IT | Undocumented apps | Scenarios 2, 6 |
| Legacy Applications | COBOL, AS/400, VB6 | Scenarios 2, 5 |

#### C. Security Signals (4 points)
| Signal | Pattern | Expected In |
|--------|---------|-------------|
| No MFA | MFA gaps | Scenarios 2, 6 |
| No EDR | Missing endpoint protection | Scenario 2 |
| Compliance Gaps | Failed audits, open findings | Scenarios 2, 4, 5 |

#### D. Organization Signals (4 points)
| Signal | Pattern | Expected In |
|--------|---------|-------------|
| Key Person | Bob, Harold, single expert | Scenarios 2, 5, 6 |
| Documentation Gaps | No runbooks, tribal knowledge | Scenarios 2, 6 |

#### E. M&A Signals (4 points)
| Signal | Pattern | Expected In |
|--------|---------|-------------|
| Carveout Entanglement | Shared services, parent | Scenario 3 |
| TSA Dependency | Transition services needed | Scenario 3 |
| Prior M&A | Never integrated | Scenario 2 |

### 3. Industry Multiplier Application (10 points)

| Industry | Expected Multiplier | Test Scenario |
|----------|---------------------|---------------|
| Manufacturing | 1.1x | Scenario 2, 6 |
| Healthcare | 1.4x | Scenario 4 |
| Financial Services | 1.5x | Scenario 5 |

Score: Correct multiplier applied × 3.33 pts

### 4. Output Quality (20 points)

#### A. Evidence Linkage (5 points)
- Every finding references source document
- Quotes are accurate
- Page/section references correct

#### B. Recommendation Quality (5 points)
- Recommendations are actionable
- Linked to underlying risks
- Appropriately prioritized

#### C. Work Item Quality (5 points)
- Work items are specific
- Phasing (Day 1/100/Post) appropriate
- Owner type reasonable

#### D. Gap Identification (5 points)
- Gaps reflect missing information (not guesses)
- Follow-up questions are specific
- Priority appropriate

### 5. Cost Estimation (10 points)

#### A. Range Reasonableness (5 points)
- Cost ranges fall within expected bounds
- Profile multipliers applied correctly
- Not wildly over/under estimated

#### B. Consistency (5 points)
- Similar work items have similar costs
- Costs scale appropriately with complexity
- Total adds up correctly

---

## Validation Checklist

### Pre-Run Checklist
- [ ] Test scenario file exists and is readable
- [ ] Database is fresh (or note if incremental)
- [ ] API key is configured
- [ ] Output directory is writable

### Post-Run Checklist
- [ ] Analysis completed without errors
- [ ] JSON output files created
- [ ] HTML report generated
- [ ] All 6 domains produced findings

### Finding Validation
For each risk/finding, verify:
- [ ] Evidence quote matches source
- [ ] Severity seems appropriate
- [ ] Mitigation is reasonable
- [ ] Domain categorization correct

---

## Expected Finding Counts

| Scenario | Risks | Gaps | Work Items | Score Threshold |
|----------|-------|------|------------|-----------------|
| **1. Clean Modern** | 0-5 | 0-3 | 5-10 | >80 pts (no false positives) |
| **2. Legacy Nightmare** | 30-50 | 15-25 | 40-60 | >80 pts (detection) |
| **3. Carveout** | 15-25 | 10-15 | 25-40 | >75 pts (TSA focus) |
| **4. Healthcare** | 15-25 | 8-15 | 20-35 | >75 pts (industry) |
| **5. Financial** | 15-25 | 10-15 | 25-40 | >75 pts (regulatory) |
| **6. Acme Baseline** | 20-35 | 12-20 | 30-45 | >75 pts (baseline) |

---

## Pass/Fail Criteria

### PASS (Green)
- Total score: >75/100
- No critical false positives
- All expected complexity signals detected
- Evidence linkage accurate

### MARGINAL (Yellow)
- Total score: 60-75/100
- Minor false positives
- Most complexity signals detected
- Some evidence gaps

### FAIL (Red)
- Total score: <60/100
- Significant false positives
- Missing critical risks
- Hallucinated findings

---

## Issue Categorization

When documenting issues, categorize as:

| Category | Description | Example |
|----------|-------------|---------|
| **FALSE_POSITIVE** | Flagged something that isn't a risk | Flagged "legacy" for 2-year-old system |
| **MISSED_RISK** | Failed to identify known risk | Didn't flag AS/400 key person |
| **SEVERITY_ERROR** | Wrong severity level | Critical as Medium |
| **EVIDENCE_ERROR** | Wrong/missing source citation | Quote doesn't match doc |
| **HALLUCINATION** | Made up information | Invented server count |
| **DOMAIN_ERROR** | Wrong domain classification | Network issue in Apps |
| **COST_ERROR** | Cost estimate unreasonable | $10M for MFA deployment |

---

## Reporting Template

```markdown
# Validation Report: [Scenario Name]

## Summary
- Date: [Date]
- Run ID: [RUN-xxx]
- Total Score: [X]/100
- Status: [PASS/MARGINAL/FAIL]

## Detection Results
- Risks Found: [X]
- Expected: [Y]
- True Positives: [A]
- False Positives: [B]
- Missed: [C]

## Complexity Signals
- Detected: [List]
- Missed: [List]

## Issues Found
| ID | Category | Description | Severity |
|----|----------|-------------|----------|
| 1 | TYPE | Details | HIGH/MED/LOW |

## Recommendations
- [Fix recommendations]

## Raw Scores
- Detection Accuracy: X/40
- Complexity Signals: X/20
- Industry Multiplier: X/10
- Output Quality: X/20
- Cost Estimation: X/10
```

---

## Running Validation Tests

```bash
# Run single scenario
python main.py data/input_test/scenario_1_clean_modern.txt

# Run with specific output
python main.py data/input_test/scenario_2_legacy_nightmare.txt

# Compare runs
python main.py --compare RUN-xxx RUN-yyy

# Export for review
python main.py --export-findings RUN-xxx
```

---

*Version: 1.0*
*Created: January 2026*
