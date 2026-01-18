# IT Due Diligence Agent Expansion Plan (120 Points)

**Objective**: Expand the DD tool from 3 domain agents to 6 domain agents while implementing robust anti-hallucination measures.

**New Agents to Build**:
1. Applications Agent - Application portfolio analysis, overlap detection, rationalization
2. Organization Agent - IT org structure, key person risk, outsourcing, team analysis
3. Identity & Access Agent - IAM, SSO, MFA, PAM, JML processes, access governance

**Guiding Principles**:
- Every finding must be grounded in document evidence
- Gaps are preferable to guesses
- Consistent methodology (four lenses) across all domains
- Structured tools enforce discipline

---

## PHASE 1: FRAMEWORK ENHANCEMENTS (Points 1-25)

### Anti-Hallucination Infrastructure (1-10)

1. Add `source_evidence` field to all finding tool schemas (risks, current_state, strategic_considerations)
2. Add `exact_quote` field requiring verbatim text from source document
3. Add `confidence_level` enum (high/medium/low) to all finding tools
4. Add `evidence_type` field (direct_statement/logical_inference/pattern_based) to tools
5. Create validation function to verify `exact_quote` exists in source document
6. Add prompt section "Evidence Requirements" to all domain agent prompts
7. Create "hallucination likelihood" scoring based on confidence distribution
8. Add Coordinator validation step to cross-check source attributions
9. Implement post-processing filter to flag low-confidence findings for review
10. Create "evidence density" metric (findings per 1000 chars of source) to detect over-inference

### Tool Schema Enhancements (11-18)

11. Update `create_current_state_entry()` to require source_evidence
12. Update `identify_risk()` to require exact_quote and confidence_level
13. Update `flag_gap()` to categorize gap type (missing_document/incomplete_detail/unclear_statement)
14. Update `log_assumption()` to require supporting_evidence and inference_chain
15. Update `create_strategic_consideration()` to require deal_evidence
16. Update `create_work_item()` to link to triggering risks/gaps
17. Add `create_application_entry()` tool for Applications Agent
18. Add `create_org_finding()` tool for Organization Agent

### Shared Prompt Components (19-25)

19. Create `prompts/shared/evidence_requirements.py` - standard evidence gathering instructions
20. Create `prompts/shared/hallucination_guardrails.py` - explicit anti-hallucination instructions
21. Create `prompts/shared/gap_over_guess.py` - instructions preferring gaps to speculation
22. Create `prompts/shared/four_lens_framework.py` - standard methodology reference
23. Create `prompts/shared/confidence_calibration.py` - guidance on confidence assignment
24. Update `dd_reasoning_framework.py` to import and use shared components
25. Create base prompt template that all domain agents extend

---

## PHASE 2: APPLICATIONS AGENT (Points 26-55)

### Agent Foundation (26-35)

26. Create `agents/applications_agent.py` extending BaseAgent
27. Define Applications domain scope: portfolio inventory, licensing, technical debt, overlap
28. Create `prompts/applications_prompt.py` with four-lens structure
29. Define application categories for insurance vertical (policy admin, claims, billing, etc.)
30. Create application criticality assessment criteria
31. Define application-specific risk types (licensing, EOL, integration complexity, vendor lock-in)
32. Create application overlap detection logic (target vs buyer comparison)
33. Define rationalization decision framework (consolidate/migrate/retire/maintain)
34. Create application cost analysis structure (licensing, support, hosting, integration)
35. Define application integration complexity scoring

### Applications-Specific Tools (36-42)

36. Create `create_application_inventory_entry()` tool with full schema
37. Create `identify_application_overlap()` tool for target-buyer comparison
38. Create `assess_application_risk()` tool with app-specific risk types
39. Create `create_rationalization_recommendation()` tool
40. Create `estimate_application_migration_effort()` tool
41. Create `flag_application_gap()` tool for missing app documentation
42. Create `identify_licensing_risk()` tool for contract/compliance issues

### Applications Prompt Development (43-50)

43. Write Lens 1 prompt: Application portfolio current state assessment
44. Write Lens 2 prompt: Application risks (EOL, licensing, vendor, technical debt)
45. Write Lens 3 prompt: Strategic implications (overlap, rationalization opportunities)
46. Write Lens 4 prompt: Application integration/migration roadmap
47. Add insurance-specific application guidance (Duck Creek, Guidewire, Majesco patterns)
48. Add ERP-specific analysis guidance (SAP, Oracle, NetSuite migration complexity)
49. Add SaaS vs on-prem analysis framework
50. Add application dependency mapping guidance

### Applications Integration (51-55)

51. Register Applications Agent in main.py orchestration
52. Add applications domain to Coordinator synthesis
53. Create applications-specific output files (application_inventory.json, app_overlap.json)
54. Add applications section to HTML viewer
55. Test Applications Agent with Great Insurance scenario

---

## PHASE 3: ORGANIZATION AGENT (Points 56-85)

### Agent Foundation (56-65)

56. Create `agents/organization_agent.py` extending BaseAgent
57. Define Organization domain scope: structure, headcount, skills, key person risk, outsourcing
58. Create `prompts/organization_prompt.py` with four-lens structure
59. Define IT organization assessment framework (team structure, reporting, capabilities)
60. Create key person risk identification criteria
61. Define outsourcing dependency assessment framework
62. Create skill gap analysis structure
63. Define organizational integration complexity scoring
64. Create retention risk assessment criteria
65. Define cultural/operational alignment assessment

### Organization-Specific Tools (66-72)

66. Create `create_org_structure_entry()` tool for team/role documentation
67. Create `identify_key_person_risk()` tool with specific risk factors
68. Create `assess_outsourcing_dependency()` tool for vendor relationships
69. Create `identify_skill_gap()` tool for capability assessment
70. Create `assess_retention_risk()` tool for critical personnel
71. Create `create_org_integration_consideration()` tool
72. Create `estimate_org_transition_effort()` tool

### Organization Prompt Development (73-80)

73. Write Lens 1 prompt: Current IT organization state assessment
74. Write Lens 2 prompt: Organizational risks (key person, skill gaps, outsourcing dependency)
75. Write Lens 3 prompt: Strategic implications (integration complexity, cultural fit, TSA needs)
76. Write Lens 4 prompt: Organizational integration/transition roadmap
77. Add team-by-team analysis guidance (Infrastructure, Apps, Security, Service Desk, etc.)
78. Add outsourcing assessment framework (scope, contract terms, transition complexity)
79. Add retention program guidance for critical personnel
80. Add TSA staffing requirement guidance

### Organization Integration (81-85)

81. Register Organization Agent in main.py orchestration
82. Add organization domain to Coordinator synthesis
83. Create organization-specific output files (org_structure.json, key_person_risks.json)
84. Add organization section to HTML viewer
85. Test Organization Agent with Great Insurance scenario

---

## PHASE 4: IDENTITY & ACCESS AGENT (Points 86-115)

### Agent Foundation (86-95)

86. Create `agents/identity_access_agent.py` extending BaseAgent
87. Define Identity domain scope: IAM, SSO, MFA, PAM, JML, access governance, directories
88. Create `prompts/identity_access_prompt.py` with four-lens structure
89. Define identity maturity assessment framework
90. Create authentication coverage assessment criteria (MFA %, SSO integration %)
91. Define privileged access management scope assessment
92. Create JML (Joiner/Mover/Leaver) process maturity framework
93. Define access governance assessment criteria (certifications, reviews, segregation)
94. Create directory services assessment framework (AD, Azure AD, LDAP, federation)
95. Define identity integration complexity scoring

### Identity-Specific Tools (96-105)

96. Create `create_identity_inventory_entry()` tool for identity systems documentation
97. Create `assess_authentication_coverage()` tool for MFA/SSO analysis
98. Create `assess_pam_maturity()` tool for privileged access evaluation
99. Create `assess_jml_process()` tool for lifecycle management evaluation
100. Create `identify_access_governance_gap()` tool
101. Create `assess_directory_integration_complexity()` tool
102. Create `identify_identity_risk()` tool with identity-specific risk types
103. Create `create_identity_integration_work_item()` tool
104. Create `assess_federation_requirements()` tool for cross-domain trust
105. Create `identify_compliance_identity_gap()` tool (SOX, PCI identity controls)

### Identity Prompt Development (106-112)

106. Write Lens 1 prompt: Current identity landscape assessment
107. Write Lens 2 prompt: Identity risks (coverage gaps, weak authentication, PAM gaps, orphan accounts)
108. Write Lens 3 prompt: Strategic implications (integration complexity, Day 1 requirements, federation needs)
109. Write Lens 4 prompt: Identity integration roadmap (directory merge, SSO consolidation, PAM integration)
110. Add MFA coverage analysis guidance (what % of users, what % of apps, what methods)
111. Add PAM scope analysis guidance (coverage of privileged accounts, session recording, etc.)
112. Add JML process assessment guidance (automation level, time to provision/deprovision, audit trail)

### Identity Integration (113-115)

113. Register Identity & Access Agent in main.py orchestration
114. Add identity domain to Coordinator synthesis
115. Create identity-specific output files (identity_inventory.json, access_governance.json)

---

## PHASE 5: INTEGRATION, TESTING & REFINEMENT (Points 116-120)

### Full Integration (116-118)

116. Update Coordinator to synthesize all 6 domains (infra, network, cyber, apps, org, identity)
117. Update HTML viewer to display all 6 domains with proper navigation
118. Update ANALYSIS_SUMMARY.md generation to include all domains

### Testing & Validation (119-120)

119. Run full 6-agent analysis on Great Insurance scenario, document findings
120. Review outputs with team, identify prompt improvements needed for each domain

---

## IMPLEMENTATION SEQUENCE

**Recommended Order**:
1. Phase 1 (Framework) - Must do first, creates foundation
2. Phase 4 (Identity) - Highest user priority, most missing from current tool
3. Phase 2 (Applications) - High value, enables overlap analysis
4. Phase 3 (Organization) - Important but simpler domain
5. Phase 5 (Integration) - Brings it all together

**Review Checkpoints**:
- After Point 25: Review anti-hallucination measures before building new agents
- After Point 55: Review Applications Agent outputs, refine prompts
- After Point 85: Review Organization Agent outputs, refine prompts
- After Point 115: Review Identity Agent outputs, refine prompts
- After Point 120: Full system review with team

---

## SUCCESS CRITERIA

### Anti-Hallucination Metrics
- [ ] 100% of findings have source_evidence populated
- [ ] exact_quote validation passes for 95%+ of findings
- [ ] Confidence distribution is realistic (not all "high")
- [ ] Gap count is reasonable for input completeness level

### Coverage Metrics
- [ ] All 6 domains produce findings on test scenarios
- [ ] Cross-domain dependencies are identified
- [ ] Work items cover all domains appropriately

### Quality Metrics
- [ ] IC review rates outputs as "useful" for 80%+ of findings
- [ ] False positive rate < 15% (findings that are wrong or unsupported)
- [ ] Gap coverage rate > 70% (known missing info is flagged)

---

## FILES TO CREATE/MODIFY

### New Files
- `agents/applications_agent.py`
- `agents/organization_agent.py`
- `agents/identity_access_agent.py`
- `prompts/applications_prompt.py`
- `prompts/organization_prompt.py`
- `prompts/identity_access_prompt.py`
- `prompts/shared/evidence_requirements.py`
- `prompts/shared/hallucination_guardrails.py`
- `prompts/shared/gap_over_guess.py`
- `prompts/shared/four_lens_framework.py`
- `prompts/shared/confidence_calibration.py`
- `tools/applications_tools.py`
- `tools/organization_tools.py`
- `tools/identity_tools.py`

### Modified Files
- `tools/analysis_tools.py` - Add source_evidence, exact_quote, confidence fields
- `agents/base_agent.py` - Add evidence validation
- `agents/coordinator_agent.py` - Expand to 6 domains
- `main.py` - Register new agents
- `generate_viewer.py` - Add new domain sections
- `prompts/dd_reasoning_framework.py` - Import shared components

---

*Plan Version: 1.0*
*Created: 2026-01-10*
*Status: Ready for Review*
