# IT Due Diligence Agent - Enhancement Checklist
## From B- to A: Prioritized Improvements

*Generated: January 14, 2026*
*Based on: Technical review and workflow analysis*

---

## Priority 1: Critical Bug Fixes
*Must fix before adding features*

- [x] **Fix string data import errors** ✅ Fixed Jan 14
  - Root cause: `SourceEvidence.from_dict()` called `.items()` on strings
  - Fix: Added `isinstance(data, dict)` checks in storage/models.py and tools/analysis_tools.py

- [x] **HTML viewer toggle display** ✅ Working (removed from list)
  - Was working in last test run

- [x] **Fix double logging** ✅ Fixed Jan 14
  - Issue: "Database schema initialized" printed twice
  - Root cause: Repository.__init__ called initialize_schema() redundantly
  - Fix: Removed redundant call in storage/repository.py:142

---

## Priority 2: Performance Improvements
*Quick wins for efficiency*

- [ ] **Parallelize domain agent execution**
  - Current: Sequential (Infra → Network → Cyber → Apps → IAM → Org)
  - Target: All 6 agents run simultaneously
  - Benefit: ~5x faster analysis (20 min → 4 min)
  - Implementation: `asyncio` or `concurrent.futures` in `main.py`

- [ ] **Add cost tracking**
  - Track tokens per agent, per run
  - Log estimated cost ($X.XX) at end of each analysis
  - Store in database: `analysis_runs.total_tokens`, `analysis_runs.estimated_cost`
  - Benefit: Visibility into spend, identify expensive agents

- [ ] **Consider tiered model usage**
  - Use Haiku for Discovery/extraction (cheaper, faster)
  - Use Opus for Reasoning/synthesis (smarter, more expensive)
  - Potential savings: 50-70% cost reduction

---

## Priority 3: Question Tracking Workflow
*Critical for iterative DD process*

- [x] **Parse questions from input documents** ✅ NEW
  - Documents can contain "Questions - Answered" and "Questions - Unanswered" sections
  - Parser extracts questions with answers, context, priority
  - Stored in questions table at start of analysis
  - `tools/question_workflow.py` - DocumentQuestionParser

- [x] **Add flag_question tool for domain agents** ✅ NEW
  - Agents can identify questions during analysis
  - Tool: `flag_question` with question, context, priority, related_gap_id
  - Questions stored to database after analysis
  - `tools/analysis_tools.py` - added flag_question tool

- [x] **Build question export to Excel** ✅
  - `python main.py --export-questions [run_id]`
  - Exports Open Questions and Answered Questions sheets
  - Answer column for client input
  - `tools/question_workflow.py` - export_questions_to_excel()

- [x] **Build answer import from Excel** ✅
  - `python main.py --import-answers [file.xlsx] --import-run-id [run_id]`
  - Parses answers from Excel
  - Updates questions in database
  - `tools/question_workflow.py` - import_answers_from_excel()

- [x] **Question status tracking** ✅
  - `python main.py --questions [run_id]` shows status summary
  - Counts by status: draft, ready, sent, answered, closed
  - Already implemented in repository

- [x] **Re-analysis trigger on answers** ✅ Jan 14
  - `python main.py --import-answers file.xlsx --reanalyze`
  - Answers become input "document" for incremental analysis
  - Builds context from answered questions by domain

---

## Priority 4: Excel Export Capability ✅
*Required for deliverables*

- [x] **Export findings to Excel** ✅ Jan 14
  - Risks worksheet with all risk fields
  - Gaps worksheet with all gap fields
  - Work Items worksheet
  - Recommendations worksheet
  - Summary worksheet with metrics
  - Current State and Assumptions worksheets
  - `python main.py --export-findings [run_id]`

- [x] **Export with evidence/citations** ✅ Jan 14
  - Include source document references
  - Evidence columns in each worksheet
  - Source references included

- [x] **Formatted for client delivery** ✅ Jan 14
  - Professional formatting with headers
  - Sortable/filterable columns (auto-filter)
  - Conditional formatting for severity/priority/phase
  - Frozen header rows
  - Auto-sized columns
  - `tools/excel_export.py`

---

## Priority 5: Foundation Hardening ✅
*Before building v2*

- [x] **Add unit tests for core functions** ✅ Jan 14
  - Repository CRUD operations (24 tests)
  - Tool processing / AnalysisStore (22 tests)
  - `tests/test_repository.py`
  - `tests/test_analysis_tools.py`

- [x] **Add integration tests** ✅ Jan 14
  - run_single_agent tests (11 tests)
  - `tests/test_run_single_agent.py`
  - 57 total tests passing

- [ ] **Validate v2 hypothesis manually**
  - Manually do two-phase analysis on test doc
  - Grade quality vs. v1 output
  - Document findings before building v2

---

## Priority 6: v2 Architecture Prep
*Only after Priorities 1-5*

- [x] **Reduce 115-point plan to 30-point MVP** ✅ Jan 14
  - Focus on core Discovery → Reasoning flow
  - Infrastructure domain only for MVP
  - Defer human review gates to v2.1

- [ ] **Define success metrics**
  - What quality score makes v2 "better" than v1?
  - How to measure evidence chain value?
  - Cost/benefit threshold for 2x API calls

- [x] **Build Discovery prototype (single domain)** ✅ Jan 14
  - `tools_v2/fact_store.py` - FactStore with unique fact IDs
  - `tools_v2/discovery_tools.py` - create_inventory_entry, flag_gap tools
  - `agents_v2/discovery/infrastructure_discovery.py` - Haiku-based extraction
  - Uses existing `prompts/v2_infrastructure_discovery_prompt.py`

- [x] **Build Reasoning prototype (single domain)** ✅ Jan 14
  - `tools_v2/reasoning_tools.py` - ReasoningStore with fact citations
  - `agents_v2/reasoning/infrastructure_reasoning.py` - Sonnet-based analysis
  - Evidence chain linking via `based_on_facts` in all findings
  - Uses existing `prompts/v2_infrastructure_reasoning_prompt.py`

- [x] **V2 Entry Point** ✅ Jan 14
  - `main_v2.py` - CLI with discovery-only and from-facts options
  - `config_v2.py` - Model tiering (Haiku for discovery, Sonnet for reasoning)
  - Cost estimation built-in

---

## Already Completed ✅

- [x] **Fix coordinator agent assumption key error**
  - Changed `a['assumption']` to handle both key variants
  - Location: `coordinator_agent.py:132`

- [x] **Fix duplicate handling in database imports**
  - Added `replace_on_conflict` parameter
  - Uses `INSERT OR REPLACE` for incremental analysis

- [x] **Add type checking for string data**
  - Added validation in `_execute_insert`
  - Added skip logic in `import_from_analysis_store`

- [x] **Parallelize domain agent execution** ✅ Jan 14
  - All 6 agents run in batches of 3 (rate limit aware)
  - ~5x faster: 20 min → 4 min typical

- [x] **Build 4-stage cost refinement** ✅ Jan 14
  - Research → Review → Refine → Summary for each work item
  - ON by default, use `--skip-costs` to disable
  - `agents/cost_refinement_agent.py`

- [x] **Question tracking workflow** ✅ Jan 14
  - Parse questions from input documents
  - flag_question tool for domain agents
  - Excel export/import for client workflow
  - `tools/question_workflow.py`

- [x] **System architecture documentation** ✅ Jan 14
  - "What's Actually Agentic" presentation
  - Clear explanation: NOT LangChain/LangGraph
  - `docs/SYSTEM_ARCHITECTURE.md`, `docs/AGENTIC_ARCHITECTURE_PRESENTATION.md`

- [x] **Excel export for all findings** ✅ Jan 14
  - Multiple worksheets: Summary, Risks, Gaps, Work Items, Recommendations, etc.
  - Professional formatting with conditional formatting
  - Auto-filter, frozen headers, evidence citations
  - `python main.py --export-findings [run_id]`
  - `tools/excel_export.py`

- [x] **Re-analysis on imported answers** ✅ Jan 14
  - `--reanalyze` flag triggers incremental analysis
  - Answered questions converted to input document
  - `_build_answer_document()` in main.py

- [x] **Unit and integration tests** ✅ Jan 14
  - 81 tests across 4 test files
  - Repository CRUD, AnalysisStore, run_single_agent, parallelization
  - `pytest tests/` all passing

- [x] **Quality Review Agent (Phase 1.5)** ✅ Jan 14
  - Reviews domain agent findings BEFORE coordinator synthesis
  - Validates evidence quality (strong/moderate/weak/missing)
  - Checks severity ratings are justified
  - Flags weak or unsupported findings
  - Outputs: validated, needs_evidence, overstated, understated, flagged
  - ON by default, use `--skip-review` to disable
  - `agents/review_agent.py`
  - Results saved to `review_results.json` in output directory

- [x] **Full Question Workflow Integration** ✅ Jan 14
  - Review Agent now manages the full question lifecycle
  - Checks if open questions have been answered by new findings/documents
  - Auto-closes questions when answers are found (high confidence required)
  - Auto-creates questions from high/critical priority gaps
  - Links gaps to questions via `related_gap_id`
  - Uses LLM to match questions against findings
  - Outputs question actions to console and `review_results.json`
  - When new docs come in: questions automatically updated

---

## Effort Estimates

| Item | Effort | Impact |
|------|--------|--------|
| Fix string data errors | 2-3 hours | High - data integrity |
| Fix HTML viewer | 1-2 hours | High - usability |
| Fix double logging | 30 min | Low - quality of life |
| Parallelize agents | 2-3 hours | High - 5x faster |
| Add cost tracking | 1 hour | Medium - visibility |
| Question export/import | 3-4 hours | High - workflow critical |
| Excel export | 4-6 hours | High - deliverables |
| Unit tests | 4-6 hours | Medium - maintainability |
| v2 prototype | 8-12 hours | High - future capability |

---

## Suggested Order of Attack

### Session 1: Stability
1. Fix double logging (quick win)
2. Investigate string data root cause
3. Fix HTML viewer toggle

### Session 2: Performance
4. Parallelize agent execution
5. Add cost tracking

### Session 3: Workflow
6. Build question export
7. Build answer import
8. Test question workflow end-to-end

### Session 4: Deliverables
9. Build Excel export
10. Format for client delivery

### Session 5: Validation
11. Add core unit tests
12. Manual v2 hypothesis test

### Session 6+: v2
13. Build v2 MVP based on learnings

---

## Notes

- Priorities 1-3 should be done before any v2 work
- Question workflow is critical path for iterative DD
- Excel export needed for actual client work
- v2 should be validated conceptually before full build
- Keep v1 functional throughout - it's the fallback

---

*This checklist supersedes IMPLEMENTATION_PLAN_V2_115.md until Priorities 1-5 are complete.*
