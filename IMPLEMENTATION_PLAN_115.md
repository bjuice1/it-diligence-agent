# IT Due Diligence Agent - 115-Point Implementation Plan

## Mission
Get the legacy system running, add persistent storage, and establish foundation for iterative analysis capability.

---

## Phase 1: Verify Legacy System (Points 1-23)
**Goal:** Confirm the existing system runs end-to-end on a PDF

### Environment Setup
1. Verify Python 3.11+ is installed and active in venv
2. Verify all dependencies in requirements.txt are installed
3. Verify Anthropic API key is configured in .env
4. Verify config.py loads environment variables correctly
5. Verify data/input and data/output directories exist

### Code Integrity Check
6. Review main.py for any syntax errors or import issues
7. Review base_agent.py for completeness
8. Review all 6 domain agent files exist and import correctly
9. Review all 6 domain prompt files exist and export correctly
10. Review coordinator_agent.py exists and functions
11. Review tools/analysis_tools.py for all required tools
12. Verify AnalysisStore class has all required methods

### PDF Ingestion Verification
13. Review ingestion/pdf_parser.py exists
14. Test PDF parser on a simple PDF file
15. Verify text extraction works correctly
16. Verify parser handles multi-page documents
17. Verify parser returns clean text (no corruption)

### Single Agent Test
18. Create minimal test script to run one agent (Infrastructure)
19. Run Infrastructure agent on sample text
20. Verify agent completes without errors
21. Verify agent produces output via tools
22. Verify output is captured in AnalysisStore

### Full Pipeline Test
23. Run full main.py on sample document and capture all errors

---

## Phase 2: Storage Layer Foundation (Points 24-46)
**Goal:** Design and build persistent storage for all findings

### Storage Architecture Design
24. Define storage requirements (what needs to persist)
25. Choose storage format: SQLite for structure + JSON for flexibility
26. Design database schema for core entities
27. Design schema for: inventory_items table
28. Design schema for: risks table
29. Design schema for: gaps table
30. Design schema for: assumptions table
31. Design schema for: work_items table
32. Design schema for: recommendations table
33. Design schema for: strategic_considerations table
34. Design schema for: documents table (source tracking)
35. Design schema for: analysis_runs table (session tracking)

### Document Tracking Schema
36. Add fields for document_id, document_name, document_path
37. Add fields for page_number, section reference
38. Add fields for ingestion_date, last_updated
39. Add fields for document_type (VDR, meeting_transcript, etc.)

### Attribution Schema
40. Add fields for source_type (document, meeting, assumption)
41. Add fields for speaker_name (for meeting transcripts)
42. Add fields for statement_date
43. Add fields for confidence_level (confirmed, assumed, gap)

### Storage Implementation
44. Create storage/database.py with SQLite connection management
45. Create storage/models.py with data classes for each entity
46. Create storage/repository.py with CRUD operations

---

## Phase 3: Integrate Storage with Legacy System (Points 47-69)
**Goal:** Wire storage layer into existing analysis flow

### AnalysisStore Enhancement
47. Modify AnalysisStore to accept database connection
48. Add method: save_to_database() for each finding type
49. Add method: load_from_database() for resuming analysis
50. Add method: get_analysis_history() for viewing past runs
51. Add analysis_run_id to track which run produced which findings
52. Add document_id linking to track source documents

### Tool Integration
53. Modify identify_risk tool to include document_source field
54. Modify flag_gap tool to include document_source field
55. Modify log_assumption tool to include document_source field
56. Modify create_work_item tool to include document_source field
57. Modify create_recommendation tool to include document_source field
58. Modify create_strategic_consideration tool to include document_source field
59. Modify create_current_state_entry tool to include document_source field

### Document Registration
60. Create function to register new document in database
61. Create function to link findings to source document
62. Create function to query findings by document
63. Create function to query findings by domain
64. Create function to query findings by analysis_run

### Main.py Updates
65. Add database initialization at startup
66. Add document registration before analysis
67. Add analysis_run creation with timestamp
68. Add database save after each agent completes
69. Add summary of persisted findings at end

---

## Phase 4: Iterative Capability Foundation (Points 70-92)
**Goal:** Enable building on previous analysis, not just one-shot

### State Management
70. Create function to load previous analysis state
71. Create function to identify what's new vs. existing
72. Create function to merge new findings with existing
73. Create function to flag conflicts/contradictions
74. Create function to track finding status changes over time

### Incremental Analysis Support
75. Add "analysis_mode" parameter: fresh vs. incremental
76. In incremental mode, load existing findings first
77. Pass existing findings context to agents
78. Add duplicate detection across runs
79. Add finding update capability (refine existing, not just add)

### Question/Gap Tracking
80. Create questions table for tracking open questions
81. Link questions to gaps that generated them
82. Track question status: open, sent, answered, closed
83. Link answers back to questions when received
84. Update related gaps when questions are answered

### Assumption Management
85. Create assumption_evidence table
86. Track evidence for/against each assumption
87. Calculate assumption confidence based on evidence
88. Flag assumptions that need validation
89. Link assumptions to questions that would prove/disprove

### Session Management
90. Create ability to name/tag analysis sessions
91. Create ability to compare sessions
92. Create ability to branch from previous session

---

## Phase 5: Testing & Validation (Points 93-115)
**Goal:** Validate system works end-to-end with synthetic data

### Synthetic Data Creation
93. Create synthetic IT overview document (3-5 pages)
94. Create synthetic infrastructure details (2-3 pages)
95. Create synthetic application inventory (2-3 pages)
96. Create synthetic org chart / team info (1-2 pages)
97. Create synthetic security overview (1-2 pages)
98. Combine into single 10-15 page synthetic IT package

### Synthetic Document Characteristics
99. Include clear facts that should become inventory items
100. Include ambiguous statements that should become assumptions
101. Include obvious gaps (topics not covered)
102. Include some risks that should be identified
103. Include enough detail for meaningful analysis

### End-to-End Test: Fresh Analysis
104. Run full analysis on synthetic document
105. Verify all 6 domains produce output
106. Verify findings are persisted to database
107. Verify HTML viewer displays results
108. Verify JSON exports are complete
109. Manual review: Are findings reasonable?

### End-to-End Test: Incremental Analysis
110. Create second synthetic document with "additional info"
111. Run incremental analysis
112. Verify new findings merge with existing
113. Verify duplicates are handled correctly
114. Verify updated findings show change history

### Validation Checklist
115. Create associate review checklist for validating output quality

---

## Success Criteria

### Phase 1 Complete When: ✅ DONE
- [x] Legacy system runs without errors
- [x] PDF ingestion works
- [x] All 6 agents produce output
- [x] HTML viewer displays results

### Phase 2 Complete When: ✅ DONE
- [x] SQLite database created with all tables
- [x] All entity types can be stored/retrieved
- [x] Document tracking works
- [x] Attribution fields present

### Phase 3 Complete When: ✅ DONE
- [x] Findings persist to database after analysis
- [x] Findings link to source documents
- [x] Analysis runs are tracked
- [x] Can query findings by document/domain/run

### Phase 4 Complete When: ✅ DONE (Jan 13, 2026)
- [x] Can load previous analysis state (Point 70: load_previous_state)
- [x] Can run incremental analysis (Points 75-79: --incremental flag)
- [x] Questions/gaps tracked with status (Points 80-84: question workflow)
- [x] Assumptions tracked with evidence (Points 85-89: assumption_evidence table)
- [x] Session naming/tagging/branching (Points 90-92: session management)

### Phase 5 Complete When: ✅ DONE (Jan 13, 2026)
- [x] Synthetic documents created (Points 93-98: v1 + v2 followup documents)
- [x] Test characteristics included (Points 99-103: facts, assumptions, gaps, risks)
- [x] Fresh analysis produces reasonable output (Points 104-109)
      - 15/16 expected items found, 7/7 risk types found
      - All 6 domains covered, Quality Score: 100.0
- [x] Incremental analysis merges correctly (Points 110-114)
      - Previous findings loaded, new findings merged
      - Duplicate detection working
- [x] Associate review checklist created (Point 115: ASSOCIATE_REVIEW_CHECKLIST.md)

---

## Estimated Complexity

| Phase | Points | Complexity | Dependencies |
|-------|--------|------------|--------------|
| Phase 1 | 23 | Low | Existing code |
| Phase 2 | 23 | Medium | None |
| Phase 3 | 23 | Medium | Phase 1, 2 |
| Phase 4 | 23 | High | Phase 3 |
| Phase 5 | 23 | Low | Phase 1-4 |

---

## Notes

- This plan focuses on **Option A**: Run legacy system + add storage layer
- v2 two-phase architecture (Discovery → Reasoning) is separate future work
- Excel export capability can be added after Phase 3
- Real document testing happens after validation on synthetic data
- Each phase can be validated independently before moving to next

---

*Created: January 2026*
*Version: 1.0*
