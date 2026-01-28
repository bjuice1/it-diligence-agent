# Two-Phase Contextual Analysis Implementation Plan

## Overview
Implement a two-phase analysis system where TARGET documents are analyzed first (clean extraction), then BUYER documents are analyzed with TARGET facts as read-only context for integration insights.

---

## PHASE 1: DATA MODEL & STORAGE (Points 1-15)

### Entity Separation in Fact Store
1. Add `analysis_phase` field to Fact dataclass ("target_extraction" or "buyer_extraction")
2. Add `is_integration_insight` boolean field to Fact for cross-entity observations
3. Create `get_facts_by_entity()` method that guarantees no cross-contamination
4. Add `lock_entity_facts()` method to make TARGET facts immutable after Phase 1
5. Create `FactStoreSnapshot` class to create read-only view of TARGET facts for Phase 2

### Session State Management
6. Add `analysis_state` enum to Session: NOT_STARTED, TARGET_COMPLETE, BUYER_COMPLETE, FULLY_COMPLETE
7. Add `target_analysis_timestamp` field to Session
8. Add `buyer_analysis_timestamp` field to Session
9. Add `target_facts_locked` boolean to Session
10. Create `SessionStateManager` class to track analysis progression

### Database/Storage Schema
11. Update facts JSON schema to include `analysis_phase` field
12. Update facts JSON schema to include `is_integration_insight` field
13. Create separate output files: `facts_target_{timestamp}.json` and `facts_buyer_{timestamp}.json`
14. Add migration logic for existing facts without entity field (default to "target")
15. Add validation that rejects facts without explicit entity assignment

---

## PHASE 2: UPLOAD UI CHANGES (Points 16-35)

### Separate Upload Sections
16. Redesign upload.html with clear visual separation between TARGET and BUYER sections
17. Add colored borders: green for TARGET section, blue for BUYER section
18. Add section headers: "Step 1: Target Company Documents" and "Step 2: Buyer Company Documents (Optional)"
19. Add helper text explaining why documents are separated
20. Add document count badges for each section

### Independent Analysis Buttons
21. Add "Analyze Target" button in TARGET section
22. Add "Analyze Buyer" button in BUYER section (disabled until TARGET complete)
23. Add "Analyze Both (Sequential)" button for convenience
24. Add visual state indicators: "Not Started", "In Progress", "Complete"
25. Add progress spinners for each section independently

### Upload State Persistence
26. Store uploaded TARGET file paths in Flask session
27. Store uploaded BUYER file paths in Flask session
28. Add "Clear Target Documents" button
29. Add "Clear Buyer Documents" button
30. Persist upload state across page refreshes

### Validation & Guards
31. Require at least 1 TARGET document before any analysis
32. Prevent BUYER analysis until TARGET analysis is complete
33. Show warning if user tries to analyze BUYER first
34. Add confirmation dialog if re-analyzing TARGET (will reset BUYER results)
35. Validate file types separately for each section

---

## PHASE 3: ANALYSIS RUNNER REFACTOR (Points 36-55)

### Two-Phase Analysis Architecture
36. Create `run_target_analysis()` function - Phase 1 only
37. Create `run_buyer_analysis()` function - Phase 2 only
38. Refactor `run_analysis()` to orchestrate both phases sequentially
39. Add `phase` parameter to `run_discovery_for_domain()`: "target" or "buyer"
40. Create `TargetAnalysisResult` dataclass to pass to Phase 2

### Phase 1: Target Extraction (Clean)
41. Phase 1 receives ONLY target document content
42. Phase 1 discovery agents instructed: "All content is from TARGET company"
43. Phase 1 facts automatically tagged with `entity="target"`
44. Phase 1 completes and locks TARGET facts
45. Phase 1 saves intermediate results before Phase 2 begins

### Phase 2: Buyer Extraction with Context
46. Phase 2 receives ONLY buyer document content
47. Phase 2 receives TARGET facts as READ-ONLY context (not as documents to extract from)
48. Phase 2 discovery agents instructed: "Document content is BUYER, reference facts are TARGET"
49. Phase 2 facts automatically tagged with `entity="buyer"`
50. Phase 2 can create `is_integration_insight=True` facts for cross-entity observations

### Context Injection for Phase 2
51. Create `format_target_facts_as_context()` function
52. Format TARGET facts as structured summary, not raw documents
53. Add clear markers: "=== TARGET COMPANY FACTS (READ-ONLY REFERENCE) ==="
54. Include instruction: "Do NOT extract facts from this section, only reference it"
55. Limit context size to prevent token overflow (summarize if needed)

---

## PHASE 4: DISCOVERY AGENT UPDATES (Points 56-75)

### Base Discovery Agent Changes
56. Add `phase` parameter to `__init__`: "target" or "buyer"
57. Add `target_context` parameter for Phase 2 agents
58. Update `_build_system_prompt()` to include phase-specific instructions
59. Add strict entity enforcement in tool validation
60. Reject any fact creation with wrong entity for current phase

### Phase 1 System Prompt
61. Add instruction: "You are analyzing TARGET company documents ONLY"
62. Add instruction: "Every fact you extract is about the TARGET company"
63. Add instruction: "Always use entity='target' - no exceptions"
64. Remove any mention of BUYER to avoid confusion
65. Add target company name prominently in prompt

### Phase 2 System Prompt
66. Add instruction: "You are analyzing BUYER company documents"
67. Add instruction: "Every fact you extract is about the BUYER company"
68. Add instruction: "Always use entity='buyer' - no exceptions"
69. Add instruction: "Reference TARGET facts below for integration context"
70. Add instruction: "You may note integration implications between systems"

### Integration Insight Extraction
71. Add `flag_integration_insight` tool for Phase 2 agents
72. Integration insights reference both TARGET and BUYER facts
73. Integration insights stored with `is_integration_insight=True`
74. Examples: "TARGET Oracle ERP will need integration with BUYER SAP"
75. Integration insights appear in separate "Integration Considerations" section

---

## PHASE 5: API ENDPOINTS (Points 76-90)

### New Analysis Endpoints
76. `POST /api/analysis/target/start` - Start Phase 1 only
77. `POST /api/analysis/buyer/start` - Start Phase 2 only (requires Phase 1 complete)
78. `POST /api/analysis/full/start` - Start both phases sequentially
79. `GET /api/analysis/status` - Get current analysis state
80. `GET /api/analysis/target/status` - Get Phase 1 status specifically

### Fact Retrieval Endpoints
81. `GET /api/facts?entity=target` - Get only TARGET facts
82. `GET /api/facts?entity=buyer` - Get only BUYER facts
83. `GET /api/facts?type=integration` - Get only integration insights
84. `GET /api/facts/summary` - Get counts by entity
85. Update existing `/api/facts` to include entity filter parameter

### State Management Endpoints
86. `POST /api/analysis/target/reset` - Clear TARGET results and unlock
87. `POST /api/analysis/buyer/reset` - Clear BUYER results only
88. `GET /api/analysis/can-start-buyer` - Check if Phase 2 can begin
89. `POST /api/analysis/lock-target` - Manually lock TARGET facts
90. `GET /api/session/state` - Get full session state including analysis phase

---

## PHASE 6: PROCESSING UI UPDATES (Points 91-100)

### Two-Phase Progress Display
91. Update processing.html to show two-phase progress
92. Add Phase 1 progress section: "Analyzing Target Company..."
93. Add Phase 2 progress section: "Analyzing Buyer Company..." (shows after Phase 1)
94. Add visual transition between phases
95. Show "Phase 1 Complete - Starting Phase 2" message

### Phase-Specific Metrics
96. Display TARGET facts count separately
97. Display BUYER facts count separately
98. Display integration insights count
99. Show time elapsed for each phase
100. Add "Skip Buyer Analysis" button if user wants TARGET only

---

## PHASE 7: RESULTS UI UPDATES (Points 101-110)

### Entity-Separated Display
101. Add entity filter toggle on Facts page: "All | Target | Buyer | Integration"
102. Color-code facts by entity: green=target, blue=buyer, purple=integration
103. Add entity badge to each fact row
104. Update fact detail drawer to show entity prominently
105. Add "Entity" column to facts table

### Dashboard Updates
106. Update dashboard to show entity breakdown in summary stats
107. Add "Target vs Buyer" comparison widget
108. Show integration insights as separate card
109. Add visual indicator of analysis completeness by entity
110. Update domain cards to show entity breakdown

---

## PHASE 8: TESTING & VALIDATION (Points 111-115)

### Contamination Prevention Tests
111. Unit test: Phase 1 cannot create buyer facts
112. Unit test: Phase 2 cannot create target facts
113. Unit test: TARGET facts are immutable after Phase 1
114. Integration test: Full two-phase flow with sample documents
115. Manual test checklist: Upload target docs, analyze, upload buyer docs, analyze, verify separation

---

## Implementation Order

**Week 1: Foundation**
- Points 1-15 (Data Model)
- Points 36-55 (Analysis Runner)

**Week 2: Agent Updates**
- Points 56-75 (Discovery Agents)

**Week 3: UI & API**
- Points 16-35 (Upload UI)
- Points 76-90 (API Endpoints)
- Points 91-100 (Processing UI)

**Week 4: Polish & Test**
- Points 101-110 (Results UI)
- Points 111-115 (Testing)

---

## Success Criteria

1. Zero cross-contamination: TARGET facts never attributed to BUYER and vice versa
2. Clear visual separation in all UI screens
3. BUYER analysis has access to TARGET facts for integration insights
4. User can analyze TARGET only, or both sequentially
5. Re-analyzing TARGET warns about resetting BUYER results
