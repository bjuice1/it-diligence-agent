# Industry Context Integration Plan
## 115-Point Implementation Across 10 Phases

**Objective:** Make industry selection (and sub-industry) flow throughout the entire analysis pipeline, fundamentally changing how facts are interpreted, risks are framed, questions are raised, and recommendations are made.

**Core Principle:** A single industry selection at the start flows everywhere - discovery, reasoning, narrative, reports, and open questions for the deal team.

---

## PHASE 1: Data Model & Foundation (12 points)
*Establish the data structures and configuration to support industry hierarchy*

### DealContext Enhancement
1. Add `sub_industry` field to `DealContext` dataclass in `tools_v2/session.py`
2. Add `secondary_industries` list field for ambiguous companies (e.g., fintech + software)
3. Add `industry_confirmed` boolean to track if user confirmed vs. auto-detected
4. Create `IndustryContext` dataclass to hold industry + sub-industry + metadata
5. Add method `DealContext.get_industry_context()` to return full industry configuration

### Sub-Industry Configuration
6. Create `INDUSTRY_HIERARCHY` dict mapping industry → list of sub-industries
7. Define sub-industries for Financial Services: `commercial_banking`, `mortgage_lending`, `wealth_management`, `broker_dealer`, `credit_union`, `fintech`
8. Define sub-industries for Healthcare: `hospital_system`, `physician_practice`, `specialty_clinic`, `payer`, `healthcare_it`
9. Define sub-industries for Manufacturing: `discrete`, `process`, `job_shop`, `oem`, `contract_manufacturing`
10. Add sub-industry specific overrides to `industry_application_considerations.py`

### Validation & Defaults
11. Create `validate_industry_selection()` function to ensure valid industry/sub-industry combo
12. Add fallback behavior for when industry is not specified (use "general" with no industry-specific framing)

---

## PHASE 2: UI - Industry Selection (14 points)
*Add industry selection to Flask and Streamlit interfaces*

### Flask Upload Form
13. Add industry dropdown to `/upload` page in `web/templates/upload.html`
14. Populate dropdown from `get_all_industries()` function
15. Add conditional sub-industry dropdown that updates based on industry selection
16. Add JavaScript to dynamically load sub-industries when industry changes
17. Add "Other/Ambiguous" option with free-text field for edge cases
18. Store industry selection in Flask session alongside deal_type
19. Pass industry to `start_analysis()` endpoint

### Flask Settings/Context Page
20. Create `/deal-context` page to view/edit deal context mid-session
21. Allow industry change with warning about re-analysis implications
22. Show current industry context and what it means for analysis

### Streamlit UI
23. Add industry selectbox to Streamlit sidebar in `app.py`
24. Add conditional sub-industry selectbox
25. Store in `st.session_state["industry"]` and `st.session_state["sub_industry"]`
26. Pass to `run_analysis()` function

---

## PHASE 3: Industry Configuration Enhancement (15 points)
*Enrich the industry considerations with sub-industry specifics and better structure*

### Sub-Industry Considerations
27. Add `sub_industries` dict to each industry in `industry_application_considerations.py`
28. For `financial_services.commercial_banking`: emphasize core banking, treasury, commercial lending
29. For `financial_services.mortgage_lending`: emphasize LOS, servicing, TRID/RESPA, warehouse lending
30. For `financial_services.wealth_management`: emphasize portfolio management, trading, fiduciary, custody
31. For `financial_services.broker_dealer`: emphasize trading systems, FINRA compliance, clearing, settlement

### Industry-Specific Question Banks
32. Create `get_industry_open_questions(industry, sub_industry)` function
33. Define 10-15 key diligence questions per industry that should always be asked
34. Define 5-10 sub-industry specific questions
35. Create question priority levels: `must_ask`, `should_ask`, `if_relevant`

### Industry Risk Weights
36. Create `INDUSTRY_RISK_WEIGHTS` dict mapping industry to risk category weights
37. For financial_services: elevate `regulatory_compliance`, `data_security`, `audit_controls`
38. For healthcare: elevate `hipaa_compliance`, `clinical_systems`, `patient_safety`
39. For manufacturing: elevate `ot_security`, `quality_systems`, `supply_chain`
40. Create `get_risk_weight_adjustment(industry, risk_category)` function

### Industry "What Good Looks Like" Benchmarks
41. Expand `what_good_looks_like` section for each industry with specific benchmarks

---

## PHASE 4: Discovery Integration (10 points)
*Pass industry context to discovery agents to ask industry-relevant questions*

### Discovery Agent Enhancement
42. Add `industry` and `sub_industry` parameters to `BaseDiscoveryAgent.__init__()`
43. Modify `system_prompt` property to inject industry context when available
44. Create `get_industry_discovery_supplement(industry, sub_industry)` function
45. Inject industry-specific "also look for" instructions into discovery prompts

### Pipeline Wiring
46. Update `run_parallel_discovery()` in `main_v2.py` to accept industry parameter
47. Pass industry from Flask `start_analysis()` to discovery pipeline
48. Pass industry from Streamlit `run_analysis()` to discovery pipeline
49. Log industry context at discovery start for debugging

### Industry-Aware Gap Flagging
50. Modify gap flagging to be industry-aware (missing EMR in healthcare = critical gap)
51. Use `expected_applications` from industry config to flag industry-specific gaps

---

## PHASE 5: Reasoning Integration (15 points)
*Inject industry context into reasoning to change how facts are interpreted*

### Prompt Context Enhancement
52. Update `DealContext.to_prompt_context()` to include industry section
53. Create `get_industry_reasoning_context(industry, sub_industry)` function
54. Include industry-specific risk lens in reasoning context
55. Include industry-specific "what to watch for" in reasoning context
56. Include regulatory framework relevant to industry

### Reasoning Prompt Modification
57. Add `{industry_context}` placeholder to all reasoning prompts
58. Update `base_reasoning_agent._build_system_prompt()` to inject industry context
59. Create industry-specific reasoning supplements for each domain
60. For infrastructure + financial_services: add regulatory exam, SOX control framing
61. For cybersecurity + financial_services: add FFIEC, GLBA framing
62. For applications + financial_services: add core banking, regulatory reporting framing

### Industry-Specific Inference Patterns
63. Create `INDUSTRY_INFERENCE_PATTERNS` - common patterns by industry
64. For financial_services: "manual process" → "potential SOX control gap"
65. For healthcare: "unencrypted data" → "potential HIPAA violation"
66. Inject patterns into reasoning prompts

---

## PHASE 6: Open Questions & Gaps (12 points)
*Generate industry-specific questions for the deal team*

### Question Generation
67. Create `OpenQuestionGenerator` class in new file `tools_v2/open_questions.py`
68. Method `generate_industry_questions(industry, sub_industry, facts)`
69. Method `generate_gap_questions(gaps, industry)` - turn gaps into deal team questions
70. Method `generate_regulatory_questions(industry)` - always-ask regulatory questions

### Question Prioritization
71. Implement question scoring based on industry relevance
72. Flag questions as `critical`, `important`, `nice_to_have`
73. Link questions to supporting facts/gaps

### Question Output
74. Add `open_questions` section to reasoning output
75. Create `OpenQuestion` dataclass with: question, priority, category, based_on_facts, industry_relevant
76. Store open questions in ReasoningStore
77. Display open questions in Flask dashboard
78. Include open questions in reports

---

## PHASE 7: Risk Framing & Elevation (12 points)
*Change how risks are assessed and framed based on industry*

### Risk Severity Adjustment
79. Create `adjust_risk_severity_for_industry(risk, industry)` function
80. Elevate regulatory/compliance risks for regulated industries
81. Elevate OT/safety risks for manufacturing/utilities
82. Elevate data privacy risks for healthcare/financial

### Risk Description Enhancement
83. Modify risk generation to include industry-specific implications
84. Add `industry_implication` field to Risk dataclass
85. For financial_services risks, add regulatory exam impact framing
86. For healthcare risks, add HIPAA/patient safety framing

### Risk Categorization
87. Add industry-specific risk categories (e.g., "regulatory_compliance" for financial)
88. Create `get_industry_risk_categories(industry)` function
89. Ensure risks are tagged with industry-relevant categories
90. Update risk filtering in UI to show industry-relevant categories

---

## PHASE 8: Recommendations & Work Items (10 points)
*Make recommendations and work items industry-aware*

### Recommendation Framing
91. Add industry context to recommendation generation
92. For financial_services: frame recommendations in regulatory compliance terms
93. For healthcare: frame recommendations in patient safety/HIPAA terms
94. Add `regulatory_driver` field to Recommendation dataclass when applicable

### Work Item Prioritization
95. Adjust work item priority based on industry context
96. Regulatory remediation = Day_1 for regulated industries
97. Add industry-specific work item templates

### Cost Estimation
98. Use industry-specific cost ranges from `cost_implications` in industry config
99. Adjust cost estimates based on industry (healthcare IT typically costs more)
100. Include industry benchmark costs in work item descriptions

---

## PHASE 9: Narrative & Reports (10 points)
*Include industry context in narrative synthesis and report output*

### Narrative Enhancement
101. Add industry section to executive narrative
102. Include industry-specific regulatory landscape summary
103. Frame findings in industry context ("For a financial institution, this means...")
104. Add industry-specific "what good looks like" comparison

### HTML Report
105. Add industry context header to HTML report
106. Include industry-specific risk summary section
107. Add regulatory considerations section for regulated industries
108. Include industry-specific open questions section

### Export Formats
109. Include industry context in JSON export
110. Include industry context in Excel export
111. Add industry-specific sheets to Excel (regulatory checklist, etc.)

---

## PHASE 10: Testing & Validation (5 points)
*Ensure industry context flows correctly end-to-end*

### Test Cases
112. Create test case: Financial Services + Carve-out (full flow)
113. Create test case: Healthcare + Bolt-on (full flow)
114. Create test case: Ambiguous company with multiple industries
115. Validate industry context appears in all outputs (facts, risks, questions, narrative, report)

---

## Implementation Priority

**Must Have (MVP):**
- Phase 1: Points 1-5 (basic DealContext)
- Phase 2: Points 13-19 (Flask UI)
- Phase 5: Points 52-59 (reasoning integration)
- Phase 6: Points 67-70, 74-78 (open questions)

**Should Have (v1.1):**
- Phase 3: Points 27-31 (sub-industries)
- Phase 4: Points 42-51 (discovery integration)
- Phase 7: Points 79-86 (risk framing)

**Nice to Have (v1.2):**
- Phase 2: Points 20-22 (deal context page)
- Phase 3: Points 36-40 (risk weights)
- Phase 8-9: Full implementation
- Phase 10: Comprehensive testing

---

## Success Metrics

1. **Industry flows everywhere:** Single selection at upload appears in discovery, reasoning, narrative, and reports
2. **Questions change:** Open questions for deal team include industry-specific regulatory/compliance questions
3. **Risk framing changes:** Same fact produces different risk framing for financial_services vs. manufacturing
4. **"So what" is clear:** Every finding explicitly connects to industry context when relevant
5. **Deal team value:** Questions and recommendations are immediately actionable for the specific industry

---

## Files to Modify/Create

**Modify:**
- `tools_v2/session.py` - DealContext enhancement
- `prompts/shared/industry_application_considerations.py` - Sub-industries, question banks
- `web/templates/upload.html` - Industry dropdown
- `web/app.py` - Industry parameter flow
- `app.py` (Streamlit) - Industry selection
- `main_v2.py` - Pipeline wiring
- `agents_v2/base_reasoning_agent.py` - Industry context injection
- All reasoning prompts - Add {industry_context} placeholder
- `tools_v2/html_report.py` - Industry section in reports

**Create:**
- `tools_v2/open_questions.py` - Question generation
- `tools_v2/industry_context.py` - Industry context utilities
- `prompts/shared/industry_reasoning_supplements.py` - Industry-specific reasoning guidance
