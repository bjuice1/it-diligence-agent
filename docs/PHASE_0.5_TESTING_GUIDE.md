# Phase 0.5: System Validation Testing Guide

## What We've Created

### 1. Synthetic Test Scenarios (5 new + 1 existing)

| # | Scenario | File | Purpose |
|---|----------|------|---------|
| 1 | **Clean Modern Stack** | `data/input_test/scenario_1_clean_modern.txt` | Tests for FALSE POSITIVES - Cloud-native company with no legacy. Should produce <5 risks. |
| 2 | **Legacy Nightmare** | `data/input_test/scenario_2_legacy_nightmare.txt` | Tests MAXIMUM DETECTION - Everything is broken. Should produce 30+ risks. |
| 3 | **Carveout from Parent** | `data/input_test/scenario_3_carveout.txt` | Tests TSA/SEPARATION detection - Heavy parent dependencies, entanglement. |
| 4 | **Healthcare** | `data/input_test/scenario_4_healthcare.txt` | Tests INDUSTRY PATTERNS - HIPAA, PHI, medical devices, compliance gaps. |
| 5 | **Financial Services** | `data/input_test/scenario_5_financial_services.txt` | Tests REGULATORY - SOX, PCI, core banking, examiner findings. |
| 6 | **Acme Manufacturing** | `data/input/synthetic_it_discovery_v1.txt` | BASELINE scenario (already existed) - Mid-complexity manufacturing. |

### 2. Validation Framework

- **Location**: `data/VALIDATION_FRAMEWORK.md`
- **Purpose**: Scoring rubric (100 points total) covering:
  - Detection Accuracy (40 pts)
  - Complexity Signal Detection (20 pts)
  - Industry Multiplier Application (10 pts)
  - Output Quality (20 pts)
  - Cost Estimation (10 pts)

### 3. Supporting Documentation

- `data/TEST_VALIDATION_GUIDE.md` - Expected findings for Acme scenario
- `data/ASSOCIATE_REVIEW_CHECKLIST.md` - Human review checklist

---

## How to Run Tests

### Quick Test (Single Scenario)
```bash
# Navigate to project
cd "/Users/JB/Documents/IT/IT DD Test 2/9.5/it-diligence-agent 2"

# Run Clean Modern (fastest, fewest findings)
python main.py data/input_test/scenario_1_clean_modern.txt

# Run Legacy Nightmare (comprehensive test)
python main.py data/input_test/scenario_2_legacy_nightmare.txt

# Run Healthcare (industry test)
python main.py data/input_test/scenario_4_healthcare.txt
```

### Full Test Suite
```bash
# Run each scenario and note results
for scenario in scenario_1_clean_modern scenario_2_legacy_nightmare scenario_3_carveout scenario_4_healthcare scenario_5_financial_services; do
    echo "Running $scenario..."
    python main.py "data/input_test/${scenario}.txt"
    echo "Done. Check data/output/ for results."
done
```

### Compare Results
```bash
# List all runs
python main.py --list-runs

# Compare two runs
python main.py --compare RUN-xxx RUN-yyy

# Export findings for review
python main.py --export-findings RUN-xxx
```

---

## Expected Results by Scenario

### Scenario 1: Clean Modern (False Positive Test)
**Expected:**
- Total Risks: 0-5 (ideally 0-3)
- Critical Risks: 0
- Complexity Signals: NONE detected
- Industry Multiplier: Standard (1.0x)

**Pass Criteria:** If >5 risks flagged, investigate false positives.

### Scenario 2: Legacy Nightmare (Detection Test)
**Expected:**
- Total Risks: 30-50
- Critical Risks: 15+
- Must Detect:
  - [ ] AS/400 key person risk
  - [ ] Dual ERP (SAP + Oracle)
  - [ ] No DR capability
  - [ ] Windows 2003/2008 EOL
  - [ ] Ransomware history (non-disclosed)
  - [ ] PCI non-compliance
  - [ ] Bob key person dependency
  - [ ] Harold (SAP) retirement risk

**Pass Criteria:** If <30 risks flagged, detection is too weak.

### Scenario 3: Carveout (TSA/Separation Test)
**Expected:**
- TSA Findings: 10+
- Must Detect:
  - [ ] Parent IT dependency
  - [ ] Shared SAP instance
  - [ ] No standalone infrastructure
  - [ ] Day 1 continuity risks
  - [ ] 12-month TSA may be insufficient

**Pass Criteria:** TSA term must be prominently featured.

### Scenario 4: Healthcare (Industry Test)
**Expected:**
- Industry Multiplier: 1.4x applied
- Must Detect:
  - [ ] HIPAA gaps (DLP, segmentation)
  - [ ] Medical device risks (Windows 7)
  - [ ] BAA inventory incomplete
  - [ ] PHI in email/Box without controls
  - [ ] PACS DR gap
  - [ ] Breach notification history

**Pass Criteria:** Healthcare-specific patterns identified.

### Scenario 5: Financial Services (Regulatory Test)
**Expected:**
- Industry Multiplier: 1.5x applied
- Must Detect:
  - [ ] OCC MRA (third-party risk)
  - [ ] SEC deficiency
  - [ ] FINRA records gap
  - [ ] Core banking aging
  - [ ] SOX control deficiencies
  - [ ] AS/400 check processing risk

**Pass Criteria:** Regulatory findings prominently featured.

---

## Validation Process

### Step 1: Run Analysis
```bash
python main.py data/input_test/scenario_X.txt
```

### Step 2: Review Output
- Check `data/output/analysis_YYYYMMDD_HHMMSS/`
- Open `analysis_report.html` in browser
- Review `ANALYSIS_SUMMARY.md`

### Step 3: Score Against Framework
Use `data/VALIDATION_FRAMEWORK.md` scoring rubric:
1. Count true positives vs expected
2. Count false positives
3. Check complexity signals detected
4. Verify industry multiplier
5. Review evidence linkage

### Step 4: Document Issues
For each issue found:
```markdown
| ID | Category | Description | Severity |
|----|----------|-------------|----------|
| 1 | FALSE_POSITIVE | Flagged X when shouldn't | HIGH |
| 2 | MISSED_RISK | Didn't detect Y | CRITICAL |
```

### Step 5: Calculate Score
- Detection: X/40
- Signals: X/20
- Industry: X/10
- Quality: X/20
- Costs: X/10
- **Total: X/100**

---

## What Success Looks Like

| Scenario | Pass Score | Key Success Indicator |
|----------|------------|----------------------|
| Clean Modern | >80/100 | <5 risks, no false positives |
| Legacy Nightmare | >80/100 | >30 risks, all critical detected |
| Carveout | >75/100 | TSA prominently featured |
| Healthcare | >75/100 | HIPAA/PHI patterns detected |
| Financial | >75/100 | Regulatory findings highlighted |

---

## Next Steps After Testing

### If Tests Pass (>75/100):
1. Move to Phase 1: Real Document Validation
2. Run against actual DD documents
3. Compare AI output to expert analysis

### If Tests Fail (<75/100):
1. Document specific failure modes
2. Tune prompts for weak areas
3. Re-test until passing
4. Then proceed to Phase 1

---

## Files Created This Session

```
data/input_test/
├── scenario_1_clean_modern.txt         # False positive test
├── scenario_2_legacy_nightmare.txt     # Maximum detection test
├── scenario_3_carveout.txt             # TSA/separation test
├── scenario_4_healthcare.txt           # Industry pattern test
└── scenario_5_financial_services.txt   # Regulatory test

data/
├── VALIDATION_FRAMEWORK.md             # Scoring rubric
└── TEST_VALIDATION_GUIDE.md            # Expected findings (existing)

docs/
└── PHASE_0.5_TESTING_GUIDE.md         # This document
```

---

*Created: January 2026*
*Phase: 0.5 - System Validation*
