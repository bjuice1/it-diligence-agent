# Known Issues and Future Considerations

## Critical Issues Found in Testing (Feb 6, 2026)

### 1. Applications Not Extracting Completely
- **Status**: ✅ FIXED (Feb 7, 2026)
- **Root Cause**: `deterministic_parser.py` was passing `extraction_method` parameter to `FactStore.add_fact()` but that parameter doesn't exist
- **Fix**: Removed `extraction_method` from all three `add_fact()` calls in the parser
- All 33 apps now extract correctly

### 2. Documents Showing "No Documents"
- Dashboard and home page show no documents
- Documents were uploaded but not displaying
- Need to check document storage/retrieval path

### 3. Risks vs Gaps Classification
- Many "risks" should be "gaps in information"
- Gap = we don't have the info yet (request it from seller)
- Risk = we know there's a confirmed problem
- Need semantic distinction in classification

### 4. Risk Consolidation/Deduplication
- Multiple related risks should be grouped
- Example: Two separate risks about "multiple ERP environment" should be one
- Suggestion: Add "Risk PE Agent" to review/consolidate before UI display

### 5. Questions Pulling Old Data
- Questions feature may be using stale database data
- Need to verify query is scoped to current deal

---

## Future Enhancements

### Document Processing
- [ ] Document inventory showing facts pulled from each doc
- [ ] Multi-contract handling (currently weak)
- [ ] Track which facts came from which document section

### Diagram Generation
- [ ] Generate Mermaid diagrams from system data
- [ ] Parse Visio files for system architecture
- [ ] Interactive system connection diagrams
- [ ] Smart dropdowns: "This system connects to X with Y data"
- [ ] Auto-generate infrastructure diagrams from facts
- [ ] Application data flow visualization

### IT Organization
- [ ] Org design assumptions (who reports to whom)
- [ ] L1-L5 layering inference from census data
- [ ] Management structure assumptions for validation
- [ ] Interactive org chart manipulation

### Risk Analysis
- [ ] Risk consolidation agent (group related risks)
- [ ] Risk validation before UI display
- [ ] Distinguish confirmed risks from information gaps
- [ ] Risk interdependency mapping

---

## Investigation Queue

1. **Why aren't all apps extracting?** - Check deterministic parser output, check DB storage
2. **Why no documents showing?** - Check Document table, check deal_id scoping
3. **Questions data source** - Verify query uses current deal_id
