# 115-Point Cleanup Plan

*Created: 2026-01-28*
*Status: In Progress*

## Overview

Comprehensive plan to polish the IT Due Diligence Agent codebase, organizing outputs, adding human-readable exports, and consolidating code.

---

## Phase A: Archive & Cleanup (Points 1-20)
**Status: COMPLETE**

- [x] 1. Create `archive/` directory structure
- [x] 2. Move old timestamped facts files to archive
- [x] 3. Move old timestamped findings files to archive
- [x] 4. Move old timestamped deal_context files to archive
- [x] 5. Move old timestamped open_questions files to archive
- [x] 6. Move old timestamped vdr_requests files to archive
- [x] 7. Move old timestamped HTML reports to archive
- [x] 8. Move old investment_thesis files to archive
- [x] 9. Move `data/input_test/` to archive
- [x] 10. Move `data/output/` to archive
- [x] 11. Move root-level test_*.py files to tests/
- [x] 12. Move database backups to archive
- [x] 13. Archive `archive/unused_prompts/` properly
- [x] 14. Archive old UI code
- [x] 15. Remove empty directories
- [x] 16. Clean up `.DS_Store` files
- [x] 17. Update `.gitignore` for archive folder
- [x] 18. Create `archive/README.md` explaining contents
- [x] 19. Verify app still runs after cleanup
- [x] 20. Commit cleanup changes

**Completed:** 2026-01-28

---

## Phase B: Output Directory Reorganization (Points 21-40)
**Status: NOT STARTED**

- [ ] 21. Create `output/runs/` directory
- [ ] 22. Create `RunOutputManager` class
- [ ] 23. Implement `create_run_directory()`
- [ ] 24. Implement `get_run_paths()`
- [ ] 25. Implement `save_latest_pointer()`
- [ ] 26. Implement `get_latest_run()`
- [ ] 27. Update `FactStore.save()` to use run folder
- [ ] 28. Update findings save to use run folder
- [ ] 29. Update deal_context save to use run folder
- [ ] 30. Update open_questions save to use run folder
- [ ] 31. Update logs to use run folder
- [ ] 32. Update HTML report generation path
- [ ] 33. Update `get_session()` to load from latest run
- [ ] 34. Update web app to read from new paths
- [ ] 35. Add run selector to web UI
- [ ] 36. Add run metadata file
- [ ] 37. Implement `list_runs()`
- [ ] 38. Implement `archive_run()`
- [ ] 39. Test full analysis with new output structure
- [ ] 40. Commit output reorganization

---

## Phase C: Human-Readable Exports (Points 41-70)
**Status: IN PROGRESS**

### Core Export Service (41-50)
- [x] 41. Create `services/export_service.py`
- [x] 42. Add `openpyxl` to requirements.txt (already installed)
- [x] 43. Create `ExcelExporter` class
- [x] 44. Create `MarkdownExporter` class
- [x] 45. Create `CSVExporter` class
- [x] 46. Implement `export_applications_excel()`
- [x] 47. Implement `export_applications_markdown()`
- [x] 48. Implement `export_infrastructure_excel()`
- [x] 49. Implement `export_infrastructure_markdown()`
- [x] 50. Implement `export_network_markdown()`

### Domain Exports (51-60)
- [x] 51. Implement `export_cybersecurity_markdown()`
- [x] 52. Implement `export_identity_markdown()` (combined with cybersecurity)
- [x] 53. Implement `export_organization_csv()`
- [x] 54. Implement `export_organization_excel()`
- [x] 55. Implement `export_msp_summary()` (part of organization)
- [x] 56. Implement `export_risks_markdown()` (in findings)
- [ ] 57. Implement `export_work_items_markdown()`
- [ ] 58. Implement `export_vdr_requests_markdown()`
- [ ] 59. Implement `export_executive_summary()`
- [x] 60. Create Excel template with formatting

### Polish & Integration (61-70)
- [x] 61. Add auto-column-width to Excel exports
- [x] 62. Add Excel table formatting (filters)
- [x] 63. Add hyperlinks in MD exports (via anchor links in dossiers)
- [x] 64. Add table of contents to MD exports (quick reference tables)
- [ ] 65. Call exports automatically after analysis
- [x] 66. Add "Export" button to web UI
- [x] 67. Add export format selector
- [x] 68. Add download endpoint for exports
- [x] 69. Test all export formats
- [ ] 70. Commit export feature

### Dossier System (NEW - Beyond Original Plan)
- [x] Create `services/inventory_dossier.py` with comprehensive dossier builder
- [x] Implement fact_id chain tracing to link findings to inventory items
- [x] Create DossierMarkdownExporter with full evidence + risks + work items
- [x] Create DossierJSONExporter for programmatic access
- [x] Create DossierHTMLExporter with interactive filters
- [x] Test dossier generation for all domains

---

## Phase D: Upload Directory Rename (Points 71-85)
**Status: NOT STARTED**

- [ ] 71. Create `uploads/` directory
- [ ] 72. Update `config_v2.py` DOCUMENTS_DIR
- [ ] 73. Update `config_v2.py` TARGET_DOCS_DIR
- [ ] 74. Update `config_v2.py` BUYER_DOCS_DIR
- [ ] 75. Update `document_store.py` paths
- [ ] 76. Update `web/storage.py` paths
- [ ] 77. Update manifest.json path references
- [ ] 78. Migrate existing documents
- [ ] 79. Update all hardcoded paths in web/app.py
- [ ] 80. Update Docker volume mounts
- [ ] 81. Update `.gitignore`
- [ ] 82. Test document upload flow
- [ ] 83. Test document reading in analysis
- [ ] 84. Remove old `output/documents/`
- [ ] 85. Commit upload directory change

---

## Phase E: Store Consolidation (Points 86-100)
**Status: NOT STARTED**

- [ ] 86. Create `stores/` directory (if not exists)
- [ ] 87. Move `tools_v2/fact_store.py` to `stores/`
- [ ] 88. Move `tools_v2/document_store.py` to `stores/`
- [ ] 89. Move `tools_v2/granular_facts_store.py` to `stores/`
- [ ] 90. Move `web/session_store.py` to `stores/`
- [ ] 91. Create redirect imports in old locations
- [ ] 92. Update all imports in agents/
- [ ] 93. Update all imports in services/
- [ ] 94. Update all imports in web/
- [ ] 95. Create `stores/__init__.py`
- [ ] 96. Add type hints to all stores
- [ ] 97. Add docstrings to all store methods
- [ ] 98. Verify all tests pass
- [ ] 99. Remove redirect files after verification
- [ ] 100. Commit store consolidation

---

## Phase F: Documentation & Final Polish (Points 101-115)
**Status: NOT STARTED**

- [x] 101. Create `docs/` directory
- [ ] 102. Write `docs/architecture.md`
- [ ] 103. Write `docs/data-flow.md`
- [ ] 104. Write `docs/storage.md`
- [ ] 105. Write `docs/api.md`
- [ ] 106. Write `docs/deployment.md`
- [ ] 107. Update root `README.md`
- [ ] 108. Add inline code comments
- [ ] 109. Create `scripts/cleanup.py`
- [ ] 110. Create `scripts/healthcheck.py`
- [ ] 111. Move Dockerfile to `docker/`
- [ ] 112. Move docker-compose.yml to `docker/`
- [ ] 113. Update Railway config for new paths
- [ ] 114. Final end-to-end test
- [ ] 115. Tag release v2.0

---

## Progress Summary

| Phase | Points | Complete | Status |
|-------|--------|----------|--------|
| A: Archive & Cleanup | 1-20 | 20/20 | COMPLETE |
| B: Output Reorganization | 21-40 | 0/20 | NOT STARTED |
| C: Human Exports | 41-70 | 27/30 | IN PROGRESS |
| C+: Dossier System | BONUS | 6/6 | COMPLETE |
| D: Upload Rename | 71-85 | 0/15 | NOT STARTED |
| E: Store Consolidation | 86-100 | 0/15 | NOT STARTED |
| F: Documentation | 101-115 | 1/15 | NOT STARTED |

**Overall: 54/121 points complete (45%)**

---

## Notes

- Phase A completed 2026-01-28
- Phase C export service created with enhanced AI fields
- **Phase C+ (Dossier System)** - Major enhancement creating comprehensive per-item dossiers with:
  - Fact_id chain tracing to link findings to inventory items
  - Full evidence, risks, work items, and recommendations per item
  - Three export formats: Markdown, JSON, HTML (interactive with filters)
  - Status classification (red/yellow/green) based on linked findings
- Future enhancements documented in `export_enhancements_backlog.md`
