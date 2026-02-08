# Audit B3: Risks vs Gaps Classification

## Status: PARTIALLY IMPLEMENTED ✓
## Priority: MEDIUM (Tier 2 - Data Integrity)
## Complexity: Medium
## Review Score: 8.7/10 (GPT review, Feb 8 2026)
## Implementation Date: Feb 8, 2026

---

## 1. Problem Statement

**Symptom:** Many items classified as "risks" should be "gaps" (missing information that needs to be requested).

**User Impact:**
- Inflated risk count creates false alarm
- Confuses what needs investigation vs what's a known problem
- Harder to prioritize true risks
- Misleads stakeholders about risk posture

**Expected Behavior:** Clear semantic distinction:
- **Gap** = Information we don't have yet → request from seller
- **Risk** = Confirmed problem we found → needs mitigation plan

---

## 2. Three-Category Model (GPT FEEDBACK)

### Add: Observation / Watch Item

Edge cases need a third bucket. Forcing uncertain items into Risk or Gap causes misclassification.

| Category | Definition | Action | Example |
|----------|------------|--------|---------|
| **Gap** | Missing data | Ask seller | "Contract end date not provided" |
| **Observation** | Plausible issue, needs verification | Investigate | "DR testing appears informal; frequency not evidenced" |
| **Risk** | Confirmed issue with evidence | Mitigate | "Application running on unsupported OS" |

### Decision Tree:
```
Is information missing/unknown?
  YES → GAP (request from seller)
  NO → Is there confirmed evidence of a problem?
         YES → RISK (needs mitigation)
         NO → Is there a plausible concern but lacking proof?
               YES → OBSERVATION (needs verification)
               NO → Just a fact (no flag needed)
```

### Rule of Thumb:
- **Gap** = missing data
- **Observation** = missing certainty (needs verification to confirm risk)
- **Risk** = missing mitigation (confirmed issue)

---

## 3. Risk Evidence Requirement (GPT FEEDBACK - CRITICAL)

### Hard Constraint: Risks MUST have evidence

Add to Risk model:
```python
@dataclass
class Risk:
    id: str
    deal_id: str
    domain: str
    title: str
    description: str
    severity: str  # High, Medium, Low

    # REQUIRED (GPT FEEDBACK)
    evidence_facts: List[str]  # [fact_id, ...] - CANNOT BE EMPTY
    evidence_quote: str        # Short quote from source
    confidence: float          # 0.0 - 1.0
    impact: str               # High, Medium, Low
    likelihood: str           # High, Medium, Low

    # Metadata
    created_at: datetime
    source_agent: str
```

### Validation Rule:
```python
def validate_risk(risk: Risk) -> ValidationResult:
    """Risk is invalid if no evidence."""
    if not risk.evidence_facts or len(risk.evidence_facts) == 0:
        return ValidationResult(
            valid=False,
            reason="Risk has no supporting evidence",
            action="Downgrade to Observation or delete"
        )
    return ValidationResult(valid=True)
```

**This single change does more than prompt tuning to keep the system honest.**

---

## 4. Gap as Seller Request Backlog (GPT FEEDBACK)

### Gaps should be actionable, not just FYIs

Each Gap should include:
```python
@dataclass
class Gap:
    id: str
    deal_id: str
    domain: str

    # Request-ready fields (GPT FEEDBACK)
    question_to_seller: str    # One sentence question
    why_it_matters: str        # One sentence importance
    system_or_app: str         # Related system (if applicable)
    blocking: bool             # Does this block diligence conclusion?

    # Context
    source_document: str
    source_section: str
    created_at: datetime
```

### Example Gap Output:
```json
{
  "question_to_seller": "What is the contract renewal date for ServiceNow?",
  "why_it_matters": "Contract cliff risk cannot be assessed without renewal timeline",
  "system_or_app": "ServiceNow ITSM",
  "blocking": true
}
```

This turns gaps into an actual **diligence request list**.

---

## 5. Definitions (Refined)

### Gap (Information Gap)
- Missing documentation
- Unclear or incomplete data
- Questions that need answers
- "We need to find out X"

**Examples:**
- "Contract end date not provided"
- "User count unknown"
- "DR testing frequency not documented"
- "Security audit results not included"

### Observation (Watch Item) - NEW
- Plausible issue but lacking proof
- Early warning / potential concern
- Needs verification to confirm as risk

**Examples:**
- "DR testing appears informal; frequency not evidenced"
- "Vendor concentration seems high; contracts not provided"
- "May have compliance gaps in access controls"

### Risk (Confirmed Risk)
- Known problem with evidence
- Architectural concern
- Compliance violation
- Technical debt

**Examples:**
- "Application running on unsupported OS (Windows Server 2012)"
- "Single point of failure in payment processing"
- "No MFA enabled for privileged accounts"
- "Contract expires in 30 days with no renewal plan"

---

## 6. Current Evidence

Need to sample current gaps and risks to categorize:
```sql
SELECT item, description, 'gap' as type FROM gaps WHERE deal_id = '...' LIMIT 10;
SELECT item, description, 'risk' as type FROM risks WHERE deal_id = '...' LIMIT 10;
```

Hypothesis: Many "gaps" are actually flags for missing info (correct), but some "risks" are really just gaps (incorrect).

---

## 7. Hypotheses

| # | Hypothesis | Likelihood | How to Verify |
|---|------------|------------|---------------|
| H1 | Discovery prompts don't define gap vs risk clearly | HIGH | Read prompts |
| H2 | Reasoning agent treats all issues as risks | HIGH | Read reasoning prompts |
| H3 | Gap/Risk distinction not enforced in data model | MEDIUM | Check dataclass constraints |
| H4 | LLM conflates "problem" with "missing info" | HIGH | Sample outputs |
| H5 | No validation layer between generation and storage | MEDIUM | Check pipeline |
| **H6** | **Risks created without evidence (no constraint)** | **HIGH** | Check Risk model |

---

## 8. Files to Investigate

### Discovery Prompts:
| File | What to Look For |
|------|------------------|
| `prompts/v2_applications_discovery_prompt.py` | Gap definition |
| `prompts/v2_infrastructure_discovery_prompt.py` | Gap definition |
| `prompts/v2_organization_discovery_prompt.py` | Gap definition |
| `prompts/v2_security_discovery_prompt.py` | Gap definition |

### Reasoning Prompts:
| File | What to Look For |
|------|------------------|
| `prompts/v2_applications_reasoning_prompt.py` | Risk definition |
| `prompts/v2_infrastructure_reasoning_prompt.py` | Risk definition |
| `prompts/v2_organization_reasoning_prompt.py` | Risk definition |
| `prompts/v2_security_reasoning_prompt.py` | Risk definition |

### Data Models:
| File | What to Look For |
|------|------------------|
| `stores/fact_store.py` | Gap dataclass, Risk dataclass |
| `web/database.py` | Gap model, Risk model |

---

## 9. Audit Steps

### Phase 1: Sample Current Classification
- [ ] 1.1 Query gaps and risks for test deal
- [ ] 1.2 Manually classify each as true-gap, observation, or true-risk
- [ ] 1.3 Calculate misclassification rate
- [ ] 1.4 Identify patterns in misclassification

### Phase 2: Review Prompts
- [ ] 2.1 Read discovery prompts - how are gaps defined?
- [ ] 2.2 Read reasoning prompts - how are risks defined?
- [ ] 2.3 Identify missing/unclear criteria
- [ ] 2.4 Draft improved definitions

### Phase 3: Update Data Models
- [ ] 3.1 Add Observation category to model
- [ ] 3.2 Add evidence_facts requirement to Risk
- [ ] 3.3 Add question_to_seller fields to Gap
- [ ] 3.4 Add validation constraints

### Phase 4: Update Prompts
- [ ] 4.1 Add three-category definitions to discovery prompts
- [ ] 4.2 Add evidence requirement to reasoning prompts
- [ ] 4.3 Add examples for each category
- [ ] 4.4 Add explicit "do not" instructions

### Phase 5: Add Validation Layer
- [ ] 5.1 Create post-processing validator
- [ ] 5.2 Auto-downgrade risks without evidence → Observation
- [ ] 5.3 Log all downgrades for audit
- [ ] 5.4 Test validation rules

### Phase 6: Test & Iterate
- [ ] 6.1 Re-run analysis with updated prompts
- [ ] 6.2 Sample new outputs
- [ ] 6.3 Measure improvement in classification
- [ ] 6.4 Refine prompts as needed

---

## 10. Validation Layer (GPT FEEDBACK)

### Post-Processing Validator:

```python
GAP_INDICATORS = [
    'unknown', 'not provided', 'not documented',
    'not specified', 'unclear', 'need to confirm',
    'should verify', 'requires clarification',
    'missing', 'not included', 'unavailable'
]

OBSERVATION_INDICATORS = [
    'may', 'might', 'appears', 'possibly', 'seems',
    'could be', 'potential', 'likely', 'suggests'
]


def validate_and_classify(item, current_type: str) -> ClassificationResult:
    """
    Validate classification and auto-correct if needed.
    Returns suggested classification with reason.
    """
    description = item.description.lower()

    # Check 1: Evidence (for risks)
    if current_type == 'risk':
        if not item.evidence_facts or len(item.evidence_facts) == 0:
            return ClassificationResult(
                suggested_type='observation',
                reason='Risk has no supporting evidence',
                confidence=0.9
            )

    # Check 2: Gap indicators in risk
    if current_type == 'risk':
        for indicator in GAP_INDICATORS:
            if indicator in description:
                return ClassificationResult(
                    suggested_type='gap',
                    reason=f'Contains gap indicator: "{indicator}"',
                    confidence=0.8
                )

    # Check 3: Observation indicators in risk
    if current_type == 'risk':
        for indicator in OBSERVATION_INDICATORS:
            if indicator in description:
                return ClassificationResult(
                    suggested_type='observation',
                    reason=f'Contains uncertainty indicator: "{indicator}"',
                    confidence=0.7
                )

    return ClassificationResult(
        suggested_type=current_type,
        reason='Classification appears correct',
        confidence=1.0
    )
```

---

## 11. Prompt Improvements

### Discovery Prompt Addition:
```
## Gap Flagging

Flag a GAP when information is MISSING or UNKNOWN. A gap means:
- The document does not provide this information
- We need to request this from the seller
- This is NOT a problem, just missing data

For each gap, provide:
- question_to_seller: A one-sentence question to ask
- why_it_matters: Why this information is needed

DO NOT flag a gap as a risk. Gaps are informational needs, not problems.

Examples of GAPS:
- "Contract renewal date not specified" → Question: "What is the renewal date for X?"
- "User count for this application unknown" → Question: "How many users access X?"
- "DR testing frequency not documented" → Question: "How often is DR tested?"

Examples that are NOT gaps (these are facts or potential risks):
- "Application uses outdated technology" (this is a risk, not a gap)
- "System has 500 users" (this is a fact, not a gap)
```

### Reasoning Prompt Addition:
```
## Risk Identification

Identify a RISK only when you have CONFIRMED EVIDENCE of a problem.

A risk MUST have:
- evidence_facts: List of fact IDs that support this risk
- evidence_quote: A short quote from the source showing the problem
- Clear statement of what IS wrong (not what MIGHT be wrong)

If you are uncertain, create an OBSERVATION instead:
- Observation = plausible concern, needs verification
- Risk = confirmed problem with evidence

DO NOT flag missing information as a risk. Those are GAPS.
DO NOT flag uncertain concerns as risks. Those are OBSERVATIONS.

Examples of RISKS (with evidence):
- "3 applications running on Windows Server 2012 (end of life)"
  Evidence: Fact F-INF-0023 states "OS: Windows Server 2012"
- "No MFA configured for admin accounts per security inventory"
  Evidence: Fact F-SEC-0012 states "MFA: Not enabled"

Examples that are NOT risks:
- "DR testing frequency unknown" → GAP
- "May have compliance gaps" → OBSERVATION
- "User satisfaction not measured" → GAP
```

---

## 12. Risk Assessment

| Risk | Mitigation |
|------|------------|
| Prompt changes break extraction | Test incrementally |
| Over-correction (miss real risks) | Keep criteria balanced |
| LLM ignores instructions | Reinforce in system prompt |
| Existing data needs reclassification | Migration script with audit log |
| Adding Observation increases complexity | Start simple, expand later |

---

## 13. Definition of Done (GPT FEEDBACK)

### Must have:
- [ ] Three categories defined: Gap, Observation, Risk
- [ ] Risk model requires evidence_facts (non-empty)
- [ ] Gap model includes question_to_seller
- [ ] Validation layer auto-downgrades invalid risks
- [ ] Sample of 20 items shows <10% misclassification
- [ ] **False positive risk rate = 0%** (risks with zero evidence)

### Tests:
- [ ] Unit test: Risk without evidence fails validation
- [ ] Unit test: Gap indicator in risk → downgraded
- [ ] Unit test: Observation indicator in risk → downgraded
- [ ] Integration test: Full pipeline produces valid classifications

---

## 14. Success Criteria

- [ ] Clear criteria documented for Gap vs Observation vs Risk
- [ ] Discovery prompts explicitly define gaps with question format
- [ ] Reasoning prompts explicitly require evidence for risks
- [ ] Validation prevents evidence-free risks
- [ ] Sample of 20 items shows <10% misclassification
- [ ] Gaps and risks feel semantically correct to user
- [ ] Gaps form actionable seller request list

---

## 15. Questions Resolved

| Question | Decision |
|----------|----------|
| Third category (Observation)? | **Yes - add it** |
| Edge cases ("may have issue")? | **Observation, not Risk** |
| User reclassify in UI? | Future (admin-only) |
| Migrate existing data? | Validation script with audit log |
| Validation at generation or display? | **Both** - generation + post-process |

---

## 16. Implementation Order (GPT FEEDBACK)

1. **Prompt updates** (sections 11) — immediate lift
2. **Add Observation category** + UI support (even basic)
3. **Add Risk evidence requirements** (schema + code)
4. **Add post-processing validator** that auto-downgrades with audit log
5. Optional: UI reclassify (admin-only) + feedback loop

---

## 17. Dependencies

- None

## 18. Blocks

- Accurate risk reporting
- Proper gap request list generation
- Stakeholder trust in analysis

---

## 19. GPT Review Notes (Feb 8, 2026)

**Score: 8.7/10**

**Strengths:**
- Definitions are correct and client-aligned
- Impact section is dead on (inflated risks = distrust)
- Decision tree is exactly right
- Prompt additions are practical

**Improvements made based on feedback:**
1. Added third category: **Observation / Watch Item**
2. Added **Risk evidence requirement** (evidence_facts non-empty)
3. Added **Gap as seller request** (question_to_seller, why_it_matters)
4. Added validation layer with auto-downgrade
5. Added language checks (gap indicators, observation indicators)
6. Added success metric: **False positive risk rate = 0%**
7. Added implementation order (prompts → observation → evidence → validator)
