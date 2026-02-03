# 115-Point Plan of Action: Data Isolation & Dashboard Fix

**Date:** 2026-02-03
**Priority:** CRITICAL
**Scope:** Fix cost_summary 500 error, DocumentStore deal isolation, Organization data isolation

---

## PHASE 1: COST_SUMMARY 500 ERROR FIX (Points 1-20)

### Analysis & Preparation
1. Read `web/app.py` dashboard route (lines 1100-1300) to understand current summary structure
2. Read `dashboard.html` template to map all `cost_summary` usage points
3. Identify expected `cost_summary` structure: `{phase: {count, low, high}}`
4. Read `interactive/session.py` `_get_cost_summary()` method for reference implementation
5. Read `web/repositories/finding_repository.py` for `get_cost_estimate_total()` method

### Implementation
6. Create `get_cost_summary_by_phase()` method in `web/deal_data.py`
7. Method should query work items grouped by phase (Day_1, Day_100, Post_100)
8. Calculate `count`, `low`, `high` for each phase from `cost_estimate` field
9. Return dict matching template expected format
10. Add error handling for missing/null cost estimates

### Integration
11. Import new method in `web/app.py` dashboard route
12. Call `get_cost_summary_by_phase()` after `get_dashboard_summary()`
13. Add `cost_summary` key to summary dict at line ~1164
14. Default to empty structure if no work items: `{Day_1: {count:0, low:0, high:0}, ...}`
15. Test dashboard loads without 500 error

### Template Safety
16. Update `dashboard.html` line 122 to use `|default({})` filter
17. Update `dashboard.html` line 367 to check `if summary.cost_summary`
18. Update footer calculations (lines 383-385) with safe defaults
19. Add null checks for `.values()` and `.items()` calls
20. Verify all cost_summary template references have fallbacks

---

## PHASE 2: DOCUMENTSTORE DEAL_ID ISOLATION (Points 21-50)

### Audit Current State
21. Read `stores/document_store.py` fully to understand singleton pattern
22. Map all methods that return document lists/counts
23. Identify methods missing deal_id filtering
24. List all callers of `get_statistics()` across codebase
25. List all callers of `get_documents_for_entity()` across codebase

### Fix get_statistics()
26. Add `deal_id` parameter to `get_statistics()` method signature
27. Make parameter optional with default `None`
28. If `deal_id` provided, filter `self._documents` by deal_id first
29. If `self.deal_id` set on instance, use as fallback filter
30. Update docstring to document deal_id filtering behavior

### Fix get_documents_for_entity()
31. Add `deal_id` parameter to `get_documents_for_entity()` method
32. Filter by both entity AND deal_id when provided
33. Use instance `self.deal_id` as fallback
34. Maintain backwards compatibility with optional parameter
35. Update docstring

### Fix Other Methods
36. Audit `get_document()` method for deal_id awareness
37. Audit `search_documents()` for deal_id filtering
38. Audit `get_documents_by_authority()` for deal_id filtering
39. Add deal_id filtering to any method returning document subsets
40. Ensure `clear()` method respects deal_id (only clears current deal)

### Update Callers in web/app.py
41. Update `web/app.py:1217` - pass `deal_id=current_deal_id` to `get_statistics()`
42. Update `web/app.py:3974` - pass `deal_id=current_deal_id` to `get_statistics()`
43. Update `web/app.py:4008` - pass `deal_id=current_deal_id` to `get_statistics()`
44. Update any `get_documents_for_entity()` calls with deal_id
45. Verify flask_session import available in all locations

### Update Other Callers
46. Search for `get_statistics()` in `run_test_analysis.py` - add deal_id
47. Search for `get_statistics()` in `scripts/healthcheck.py` - add deal_id
48. Update `docs/storage.md` documentation example
49. Search for any other callers via grep
50. Update all remaining callers with deal_id parameter

---

## PHASE 3: ORGANIZATION MODELS DEAL_ID (Points 51-75)

### Model Updates
51. Read `models/organization_models.py` fully
52. Add `deal_id: Optional[str] = None` field to `StaffMember` dataclass
53. Add `deal_id: Optional[str] = None` field to `MSPRelationship` dataclass
54. Add `deal_id: Optional[str] = None` field to `MSPService` dataclass
55. Add `deal_id: Optional[str] = None` field to `SharedServiceDependency` dataclass
56. Add `deal_id: Optional[str] = None` field to `CategorySummary` dataclass
57. Add `deal_id: Optional[str] = None` field to `RoleSummary` dataclass
58. Update any `to_dict()` methods to include deal_id
59. Update any `from_dict()` methods to parse deal_id
60. Ensure dataclass field order maintains backwards compatibility

### Bridge Updates
61. Read `services/organization_bridge.py` fully
62. Update `build_organization_from_facts()` to accept deal_id parameter
63. Pass deal_id to all `StaffMember` creations in `_create_staff_from_leadership_fact()`
64. Pass deal_id to all `StaffMember` creations in `_create_staff_from_team_fact()`
65. Pass deal_id to all `StaffMember` creations in `_create_staff_from_role_fact()`
66. Pass deal_id to all `StaffMember` creations in `_create_staff_from_key_individual_fact()`
67. Pass deal_id to all `MSPRelationship` creations in `_create_msp_from_fact()`
68. Update `build_organization_result()` to accept and propagate deal_id
69. Add validation: warn if any fact has different deal_id than expected
70. Log deal_id for debugging in bridge operations

### OrganizationDataStore Updates
71. Read `models/organization_stores.py` fully
72. Add `deal_id` field to `OrganizationDataStore` class
73. Update constructor to accept deal_id
74. Add method `filter_by_deal()` to return subset for specific deal
75. Update serialization methods for deal_id

---

## PHASE 4: WEB LAYER ORGANIZATION ISOLATION (Points 76-95)

### Cache Updates
76. Read `web/app.py` organization route (lines 2274-2453)
77. Verify `_org_cache_by_deal` uses deal_id as key (already implemented)
78. Update cache fingerprint calculation to include deal_id in hash
79. Add deal_id validation when retrieving from cache
80. Clear cache entry if deal_id mismatch detected

### Database Path
81. Verify `DealData.get_organization()` filters by deal_id
82. Verify `FactRepository.get_organization()` includes deal_id in WHERE clause
83. Add logging to confirm deal_id filtering active
84. Test with multiple deals to verify isolation
85. Add assertion that returned facts all have matching deal_id

### Fallback Session Path
86. Update `web/app.py:2376-2383` fallback path
87. Add deal_id filtering to `s.fact_store.facts` iteration
88. Filter: `[f for f in facts if f.deal_id == current_deal_id]`
89. Log warning if session contains facts from multiple deals
90. Consider removing fallback path if database is primary

### Organization API Endpoints
91. Audit `/api/organization` endpoint for deal_id filtering
92. Audit `/api/org_chart` endpoint for deal_id filtering
93. Audit any organization export endpoints
94. Ensure all org APIs use `current_deal_id` from session
95. Add deal_id to API response metadata for debugging

---

## PHASE 5: TESTING & VALIDATION (Points 96-110)

### Unit Tests
96. Create test: `test_cost_summary_in_dashboard_summary()`
97. Create test: `test_document_store_statistics_filters_by_deal()`
98. Create test: `test_document_store_entity_filters_by_deal()`
99. Create test: `test_staff_member_has_deal_id()`
100. Create test: `test_organization_bridge_propagates_deal_id()`

### Integration Tests
101. Create test: Upload docs to Deal A, verify not visible in Deal B
102. Create test: Create org facts in Deal A, verify not in Deal B org view
103. Create test: Cost summary shows only current deal work items
104. Create test: Dashboard loads without 500 error after fix
105. Create test: Switch between deals, verify data isolation

### Manual Testing
106. Create two test deals with different data
107. Verify dashboard cost_summary shows correct per-deal data
108. Verify document counts accurate per deal
109. Verify organization headcount/costs correct per deal
110. Verify no data leakage when switching deals

---

## PHASE 6: DEPLOYMENT & MONITORING (Points 111-115)

### Code Review
111. Review all changes for backwards compatibility
112. Ensure no breaking changes to API contracts
113. Verify database migrations not needed (deal_id already in schema)

### Deployment
114. Commit changes with detailed message
115. Push to GitHub and monitor for errors

---

## IMPLEMENTATION ORDER

**Critical Path (blocks dashboard):**
- Points 1-20: Fix cost_summary 500 error FIRST

**High Priority (data integrity):**
- Points 21-50: DocumentStore deal_id isolation
- Points 51-75: Organization models deal_id

**Medium Priority (complete isolation):**
- Points 76-95: Web layer organization isolation

**Validation:**
- Points 96-115: Testing and deployment

---

## ESTIMATED CHANGES BY FILE

| File | Points | Changes |
|------|--------|---------|
| `web/app.py` | 12 | Add cost_summary, update callers |
| `web/deal_data.py` | 4 | Add get_cost_summary_by_phase() |
| `web/templates/dashboard.html` | 5 | Add safe defaults |
| `stores/document_store.py` | 10 | Add deal_id filtering to methods |
| `models/organization_models.py` | 10 | Add deal_id to dataclasses |
| `models/organization_stores.py` | 5 | Add deal_id to store |
| `services/organization_bridge.py` | 10 | Propagate deal_id |
| `web/repositories/finding_repository.py` | 3 | Cost summary method |
| Test files | 15 | New tests |
| Other callers | 6 | Update deal_id params |

---

## SUCCESS CRITERIA

1. Dashboard loads without 500 error
2. Cost summary shows correct phase breakdown
3. Document counts accurate per deal
4. Organization data shows only current deal staff
5. No data leakage between deals
6. All existing functionality preserved
