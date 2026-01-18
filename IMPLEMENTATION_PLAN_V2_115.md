# IT Due Diligence Agent v2 - Two-Phase Architecture
# 115-Point Implementation Plan

## Mission
Transform the single-pass analysis system into a two-phase architecture that separates **Discovery** (fact extraction) from **Reasoning** (analysis and inference), enabling more accurate, traceable, and iterative due diligence.

---

## Why Two Phases?

### Current Architecture (v1)
```
Documents → [Domain Agents] → Findings (all mixed together)
```
- Agents simultaneously extract facts AND make judgments
- Hard to trace why a risk was identified
- Re-analysis requires re-reading documents
- Reasoning quality limited by context window pressure

### Target Architecture (v2)
```
Documents → [Discovery Phase] → Structured Facts → [Reasoning Phase] → Findings
```
- Discovery focuses purely on "what does this say?"
- Reasoning focuses purely on "what does this mean?"
- Facts persist independently of conclusions
- Can re-reason with different deal contexts
- Human review possible between phases
- Better audit trail from conclusion → evidence

---

## Phase 1: Architecture Design (Points 1-23)
**Goal:** Define the complete two-phase system design before building

### Core Architecture Decisions
1. Define the boundary between Discovery and Reasoning
2. Document what Discovery produces (output schema)
3. Document what Reasoning consumes (input requirements)
4. Document what Reasoning produces (output schema)
5. Define how source citations flow through both phases
6. Design the "Fact" data model (core unit of Discovery output)
7. Design the "Evidence Chain" linking conclusions to facts

### Fact Taxonomy Design
8. Define fact categories for Infrastructure domain
9. Define fact categories for Network domain
10. Define fact categories for Cybersecurity domain
11. Define fact categories for Applications domain
12. Define fact categories for Identity & Access domain
13. Define fact categories for Organization domain
14. Define cross-domain fact categories (contracts, costs, dates)
15. Define confidence levels for extracted facts

### Discovery Agent Design
16. Design Discovery agent prompt structure
17. Define Discovery-only tools (no judgment tools)
18. Design fact extraction patterns (what to look for)
19. Design entity recognition approach (systems, people, vendors)
20. Design relationship extraction (system A connects to system B)
21. Design temporal extraction (dates, timelines, durations)
22. Design quantitative extraction (counts, costs, percentages)

### Reasoning Agent Design
23. Design Reasoning agent prompt structure that works from facts

---

## Phase 2: Discovery Engine (Points 24-46)
**Goal:** Build the fact extraction system

### Database Schema Updates
24. Create `facts` table with columns: id, run_id, domain, category, fact_text, confidence, source_document_id, source_page, source_quote, extraction_timestamp
25. Create `entities` table: id, run_id, entity_type, entity_name, attributes (JSON), first_seen_document_id
26. Create `relationships` table: id, run_id, source_entity_id, relationship_type, target_entity_id, evidence_fact_id
27. Create `discovery_runs` table to track discovery sessions separately from reasoning
28. Add foreign keys linking facts → entities where applicable
29. Create indexes for efficient fact querying by domain, category, entity

### Discovery Tools Implementation
30. Create `extract_fact` tool - records a single factual observation
31. Create `register_entity` tool - registers a system, person, vendor, or other entity
32. Create `record_relationship` tool - links two entities with a relationship type
33. Create `extract_quantity` tool - records numerical facts with units
34. Create `extract_date` tool - records temporal facts (dates, periods, deadlines)
35. Create `flag_ambiguity` tool - marks unclear or contradictory statements
36. Create `mark_quote` tool - captures exact quotes for later citation

### Discovery Prompts
37. Write Infrastructure Discovery prompt (fact extraction focus)
38. Write Network Discovery prompt
39. Write Cybersecurity Discovery prompt
40. Write Applications Discovery prompt
41. Write Identity & Access Discovery prompt
42. Write Organization Discovery prompt
43. Write General Discovery prompt for cross-cutting facts

### Discovery Agents
44. Create DiscoveryAgent base class (extends BaseAgent with discovery tools only)
45. Create domain-specific Discovery agents (6 total)
46. Create DiscoveryOrchestrator to run all discovery agents on a document

---

## Phase 3: Reasoning Engine (Points 47-69)
**Goal:** Build the analysis system that works from extracted facts

### Reasoning Tools Implementation
47. Modify `identify_risk` to require linked fact IDs as evidence
48. Modify `flag_gap` to reference what facts revealed the gap
49. Modify `create_work_item` to link to triggering risks/gaps
50. Modify `create_recommendation` to cite supporting facts
51. Modify `create_strategic_consideration` to reference evidence
52. Create `infer_dependency` tool - identifies dependencies between entities
53. Create `assess_complexity` tool - evaluates complexity from fact patterns
54. Create `estimate_effort` tool - derives effort from fact-based scope

### Evidence Chain Implementation
55. Create `evidence_chains` table linking conclusions to supporting facts
56. Implement evidence strength scoring (single fact vs. corroborated)
57. Create function to retrieve full evidence chain for any finding
58. Create function to identify findings with weak evidence
59. Implement "confidence inheritance" - conclusion confidence based on fact confidence

### Reasoning Prompts
60. Write Infrastructure Reasoning prompt (works from facts, not documents)
61. Write Network Reasoning prompt
62. Write Cybersecurity Reasoning prompt
63. Write Applications Reasoning prompt
64. Write Identity & Access Reasoning prompt
65. Write Organization Reasoning prompt
66. Write Cross-Domain Reasoning prompt for synthesis

### Reasoning Agents
67. Create ReasoningAgent base class (receives facts, produces findings)
68. Create domain-specific Reasoning agents (6 total)
69. Create ReasoningOrchestrator to run reasoning across all domains

---

## Phase 4: Pipeline & Orchestration (Points 70-92)
**Goal:** Connect the phases into a complete workflow

### Pipeline Architecture
70. Create `AnalysisPipeline` class to orchestrate full workflow
71. Implement pipeline stages: Ingest → Discover → Review → Reason → Synthestic
72. Add stage status tracking (pending, running, complete, failed)
73. Implement checkpoint/resume capability between stages
74. Create pipeline configuration (skip stages, re-run stages)

### Discovery-to-Reasoning Handoff
75. Create function to package discovery output for reasoning input
76. Implement fact summarization for large fact sets (prevent context overflow)
77. Create fact prioritization (surface most relevant facts per domain)
78. Implement fact deduplication across multiple documents
79. Create fact conflict detection (contradictory facts from different sources)

### Human Review Integration
80. Create review checkpoint after Discovery phase
81. Implement fact approval/rejection workflow
82. Allow human fact additions (manually noted facts)
83. Create fact correction capability (fix extraction errors)
84. Implement review status tracking (unreviewed, approved, rejected, corrected)

### Deal Context Integration
85. Design deal context schema (buyer info, deal thesis, integration plans)
86. Create function to inject deal context into Reasoning phase
87. Implement context-aware reasoning (same facts, different conclusions based on context)
88. Create comparison capability (reason same facts with different contexts)

### Re-Reasoning Capability
89. Implement "re-reason" function that re-runs Reasoning on existing facts
90. Track reasoning versions (v1, v2, etc. on same fact base)
91. Create diff capability (what changed between reasoning runs)
92. Implement selective re-reasoning (re-reason single domain only)

---

## Phase 5: Testing & Validation (Points 93-115)
**Goal:** Validate the two-phase system produces better results

### Discovery Quality Testing
93. Create test document with known facts (ground truth)
94. Run Discovery and measure fact extraction recall (% of facts found)
95. Measure fact extraction precision (% of extracted facts that are correct)
96. Test entity recognition accuracy
97. Test relationship extraction accuracy
98. Test source citation accuracy (correct page/section references)
99. Benchmark Discovery speed vs. v1 full analysis speed

### Reasoning Quality Testing
100. Create test fact set with known correct conclusions
101. Run Reasoning and measure conclusion accuracy
102. Test evidence chain completeness (all conclusions have evidence)
103. Test evidence chain validity (evidence actually supports conclusion)
104. Compare Reasoning output quality vs. v1 output quality
105. Test re-reasoning consistency (same facts → same conclusions)

### End-to-End Testing
106. Run full pipeline on synthetic document v1
107. Verify Discovery extracts expected facts
108. Verify Reasoning produces expected findings
109. Run full pipeline on synthetic document v2 (incremental)
110. Verify incremental facts merge correctly
111. Verify incremental reasoning builds on previous

### Comparison & Validation
112. Run v1 and v2 on same document, compare outputs
113. Measure improvement in evidence traceability
114. Measure improvement in finding accuracy (manual review)
115. Create validation checklist for v2 output quality

---

## Success Criteria

### Phase 1 Complete When:
- [ ] Architecture document reviewed and approved
- [ ] Fact taxonomy defined for all 6 domains
- [ ] Data models designed and documented
- [ ] Tool specifications complete

### Phase 2 Complete When:
- [ ] Facts table created and tested
- [ ] All Discovery tools implemented
- [ ] All Discovery prompts written
- [ ] Discovery agents extract facts from test document

### Phase 3 Complete When:
- [ ] Evidence chain schema implemented
- [ ] All Reasoning tools require evidence links
- [ ] All Reasoning prompts work from facts (not documents)
- [ ] Reasoning agents produce findings from test facts

### Phase 4 Complete When:
- [ ] Full pipeline runs end-to-end
- [ ] Human review checkpoint functional
- [ ] Re-reasoning produces consistent results
- [ ] Deal context injection working

### Phase 5 Complete When:
- [ ] Discovery recall > 80% on test document
- [ ] Discovery precision > 90% on test document
- [ ] All findings have valid evidence chains
- [ ] v2 output quality >= v1 output quality

---

## Key Data Structures

### Fact (Discovery Output)
```python
{
    "fact_id": "F-001",
    "run_id": "DISC-xxx",
    "domain": "infrastructure",
    "category": "server_inventory",
    "fact_text": "Production environment runs on 12 Dell PowerEdge servers",
    "confidence": "high",  # high, medium, low
    "source_document_id": "DOC-xxx",
    "source_page": 3,
    "source_quote": "Our production environment consists of 12 Dell PowerEdge R740 servers",
    "entities_referenced": ["ENT-001"],  # Dell PowerEdge servers entity
    "extracted_at": "2026-01-14T10:00:00Z"
}
```

### Entity (Discovery Output)
```python
{
    "entity_id": "ENT-001",
    "run_id": "DISC-xxx",
    "entity_type": "hardware",  # hardware, software, person, vendor, location, system
    "entity_name": "Dell PowerEdge R740 Servers",
    "attributes": {
        "count": 12,
        "environment": "production",
        "vendor": "Dell"
    },
    "first_seen_fact_id": "F-001"
}
```

### Evidence Chain (Reasoning Output)
```python
{
    "finding_id": "R-001",
    "finding_type": "risk",
    "evidence": [
        {
            "fact_id": "F-001",
            "relevance": "Shows server count for capacity planning",
            "strength": "direct"  # direct, supporting, circumstantial
        },
        {
            "fact_id": "F-015",
            "relevance": "Shows no documented DR for these servers",
            "strength": "direct"
        }
    ],
    "inference_notes": "Combined lack of DR documentation with production server count indicates significant business continuity risk"
}
```

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         PHASE 1: DISCOVERY                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   ┌──────────┐    ┌─────────────────────────────────────────────┐  │
│   │          │    │           Discovery Agents                   │  │
│   │ Document │───▶│  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐   │  │
│   │  (PDF/   │    │  │Infra│ │ Net │ │Cyber│ │ App │ │ IAM │   │  │
│   │   TXT)   │    │  └──┬──┘ └──┬──┘ └──┬──┘ └──┬──┘ └──┬──┘   │  │
│   └──────────┘    │     │       │       │       │       │       │  │
│                   │     └───────┴───────┴───────┴───────┘       │  │
│                   │                     │                        │  │
│                   └─────────────────────┼────────────────────────┘  │
│                                         ▼                           │
│                              ┌─────────────────────┐                │
│                              │    Facts Store      │                │
│                              │  ┌─────┐ ┌─────┐   │                │
│                              │  │Facts│ │Ents │   │                │
│                              │  └─────┘ └─────┘   │                │
│                              └─────────────────────┘                │
│                                         │                           │
└─────────────────────────────────────────┼───────────────────────────┘
                                          │
                              ┌───────────▼───────────┐
                              │   HUMAN REVIEW GATE   │
                              │  (Optional Checkpoint) │
                              └───────────┬───────────┘
                                          │
┌─────────────────────────────────────────┼───────────────────────────┐
│                         PHASE 2: REASONING                          │
├─────────────────────────────────────────┼───────────────────────────┤
│                                         ▼                           │
│                   ┌─────────────────────────────────────────────┐   │
│   ┌──────────┐    │           Reasoning Agents                  │   │
│   │  Facts   │───▶│  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐   │   │
│   │    +     │    │  │Infra│ │ Net │ │Cyber│ │ App │ │ IAM │   │   │
│   │  Deal    │    │  └──┬──┘ └──┬──┘ └──┬──┘ └──┬──┘ └──┬──┘   │   │
│   │ Context  │    │     │       │       │       │       │       │   │
│   └──────────┘    │     └───────┴───────┴───────┴───────┘       │   │
│                   │                     │                        │   │
│                   └─────────────────────┼────────────────────────┘   │
│                                         ▼                           │
│                              ┌─────────────────────┐                │
│                              │   Findings Store    │                │
│                              │  (with Evidence     │                │
│                              │      Chains)        │                │
│                              └─────────────────────┘                │
│                                         │                           │
│                                         ▼                           │
│                              ┌─────────────────────┐                │
│                              │    Coordinator      │                │
│                              │    (Synthesis)      │                │
│                              └─────────────────────┘                │
│                                         │                           │
└─────────────────────────────────────────┼───────────────────────────┘
                                          │
                                          ▼
                              ┌─────────────────────┐
                              │   Final Outputs     │
                              │  - Risks            │
                              │  - Gaps             │
                              │  - Work Items       │
                              │  - Recommendations  │
                              │  (all with evidence)│
                              └─────────────────────┘
```

---

## Estimated Complexity

| Phase | Points | Complexity | Dependencies |
|-------|--------|------------|--------------|
| Phase 1 | 23 | Medium | None (design only) |
| Phase 2 | 23 | High | Phase 1 |
| Phase 3 | 23 | High | Phase 1, 2 |
| Phase 4 | 23 | Very High | Phase 2, 3 |
| Phase 5 | 23 | Medium | Phase 1-4 |

---

## Notes

- v1 system remains functional during v2 development
- Can run v1 and v2 in parallel for comparison
- Phase 1 (Design) should be reviewed before implementation begins
- Human review gate is optional but recommended for high-stakes deals
- Re-reasoning capability enables "what-if" analysis with different deal contexts

---

*Created: January 2026*
*Version: 1.0*
*Predecessor: IMPLEMENTATION_PLAN_115.md (v1 system)*
