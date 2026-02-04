# Buyer-Aware Reasoning: Implementation Context & Issues

**Purpose:** Standalone document for external review (GPT/Claude)
**Created:** 2026-02-04
**Status:** Seeking feedback on approach and fixes

---

## BACKGROUND: What We're Trying to Achieve

### The Problem
Our IT due diligence system currently analyzes only the **target company** in isolation. It produces findings like:
- "Target uses SAP S/4HANA as ERP platform"
- "Target should consolidate applications"
- "Integration will be needed"

This is **too generic** for M&A deals. Investment committees need specific answers:
- "Target's SAP vs Buyer's Oracle - which platform wins?"
- "Target has 2-person IT team, Buyer has 568 - can buyer absorb target?"
- "Target uses CrowdStrike, Buyer uses Carbon Black - consolidation cost?"

### The Solution: Buyer-Aware Reasoning
Enable the system to:
1. Extract facts from **both** target and buyer companies
2. Compare them side-by-side (overlap analysis)
3. Generate integration-specific findings with concrete options
4. Maintain strict entity separation (never mix target/buyer perspectives)

---

## ARCHITECTURE: Two-Phase Analysis

### Phase 1: TARGET Analysis
```
INPUT: Target company documents
PROCESS: Discovery agents extract facts
OUTPUT: Facts tagged with entity="target", IDs like F-TGT-APP-001
```

### Phase 2: BUYER Analysis
```
INPUT: Buyer company documents
PROCESS: Discovery agents extract facts (WITH target context visible)
OUTPUT: Facts tagged with entity="buyer", IDs like F-BYR-APP-001
```

### Phase 3: Reasoning (Buyer-Aware)
```
INPUT: Facts from BOTH entities
PROCESS: Reasoning agents with special instructions:
  1. Generate Overlap Map (compare target vs buyer)
  2. Create findings in 3 layers:
     - Layer 1: Target standalone analysis
     - Layer 2: Overlap analysis (specific comparisons)
     - Layer 3: Integration workplan (buyer-dependent options)
OUTPUT: Findings with buyer-aware fields populated
```

---

## KEY FEATURES IMPLEMENTED

### 1. Fact ID Convention (WORKING ✅)
Every fact gets an entity-aware ID:
- Target facts: `F-TGT-APP-001`, `F-TGT-INFRA-002`, etc.
- Buyer facts: `F-BYR-APP-001`, `F-BYR-INFRA-002`, etc.

**Code:** `stores/fact_store.py:593, 697`

```python
def _generate_fact_id(self, domain: str, entity: str = "target") -> str:
    entity_prefix = "TGT" if entity == "target" else "BYR"
    domain_prefix = DOMAIN_PREFIXES.get(domain, "GEN")
    counter_key = f"{entity_prefix}_{domain_prefix}"
    # ...
    return f"F-{entity_prefix}-{domain_prefix}-{counter:03d}"
```

---

### 2. OverlapCandidate Dataclass (WORKING ✅)
Structured object for overlap analysis:

```python
@dataclass
class OverlapCandidate:
    overlap_id: str                    # OVL-APP-001
    domain: str                        # applications
    overlap_type: str                  # "platform_mismatch"
    target_fact_ids: List[str]         # ["F-TGT-APP-001"]
    buyer_fact_ids: List[str]          # ["F-BYR-APP-001"]
    target_summary: str                # "Target uses SAP"
    buyer_summary: str                 # "Buyer uses Oracle"
    why_it_matters: str                # Integration implication
    confidence: float                  # 0.0-1.0
    missing_info_questions: List[str]  # Gaps to explore
```

**Code:** `tools_v2/reasoning_tools.py`

---

### 3. Runtime Validation Rules (WORKING ✅)
Enforces 5 rules to prevent mixing target/buyer perspectives:

**RULE 1 (ANCHOR):** Buyer facts require target facts
- ❌ Rejected: Finding cites only F-BYR facts
- ✅ Allowed: Finding cites F-TGT-001 + F-BYR-002

**RULE 2 (AUTO-TAG):** Auto-tag integration_related
- If finding cites any F-BYR facts → `integration_related = true`

**RULE 3 (SCOPE):** Check for "Buyer should..." language
- Warn if finding says "Buyer should fix X" (wrong - we're assessing target!)

**RULE 4 (WORK ITEM):** Should have target action focus
- Work items must specify what TARGET does, not buyer

**RULE 5 (LEGACY):** Warn about old fact IDs without entity prefix

**Code:** `tools_v2/reasoning_tools.py:validate_finding_entity_rules()`

---

### 4. Enhanced WorkItem Dataclass (WORKING ✅)
Added fields to separate target vs buyer actions:

```python
@dataclass
class WorkItem:
    # ... existing fields ...

    # NEW BUYER-AWARE FIELDS:
    target_action: str = ""              # What TARGET must do (always required)
    integration_option: Optional[str]    # Buyer-dependent path
    integration_related: bool = False    # Auto-tagged if buyer facts cited
    overlap_id: Optional[str] = None     # References OverlapCandidate
    target_facts_cited: List[str] = []   # F-TGT-xxx IDs
    buyer_facts_cited: List[str] = []    # F-BYR-xxx IDs
```

**Example Usage:**
```json
{
  "title": "ERP Platform Consolidation",
  "overlap_id": "OVL-APP-001",
  "integration_related": true,
  "target_action": "Maintain SAP through TSA period, prepare migration plan",
  "integration_option": "If buyer absorbs target: migrate to Oracle ($2-4M, 18mo); if separate: continue SAP with extended TSA ($400K/yr)",
  "target_facts_cited": ["F-TGT-APP-001", "F-TGT-APP-003"],
  "buyer_facts_cited": ["F-BYR-APP-001"]
}
```

**Code:** `tools_v2/reasoning_tools.py`

---

### 5. Updated Reasoning Prompts (WORKING ✅)
All 6 domain prompts updated with:

**STEP 1: Generate Overlap Map**
```
Before creating any findings, use generate_overlap_map to identify
meaningful overlaps between target and buyer.

Example overlaps for Applications domain:
- platform_mismatch: Target SAP vs Buyer Oracle
- version_gap: Target uses v10, Buyer uses v11
- capability_overlap: Both have CRM systems
```

**3-Layer Output Structure**
```
Layer 1: TARGET STANDALONE
- Findings about target that apply regardless of buyer
- Example: "Target's 2-person IT team creates knowledge concentration risk"

Layer 2: OVERLAP ANALYSIS
- Specific target ↔ buyer comparisons
- Example: "Target 2-person IT vs Buyer 568-person IT creates absorption opportunity"

Layer 3: INTEGRATION WORKPLAN
- Buyer-dependent integration options
- Example: "If buyer absorbs: extend Buyer's service desk ($50K); if separate: hire 2-3 FTEs ($200K)"
```

**Buyer Context Rules**
```
When citing buyer facts:
- ALWAYS pair with target facts (ANCHOR rule)
- Use integration language: "If buyer absorbs...", "Consolidation of..."
- Frame as OPTIONS, not directives
- Avoid "Buyer must fix target's X"
```

**PE-Grade Cost Tables**
```
Applications PE Concerns:
| Concern | Cost Range |
| ERP Consolidation | $1M - $10M |
| CRM Consolidation | $200K - $1M |
| Custom Apps | $100K - $2M per app |
```

**Code:** `prompts/v2_*_reasoning_prompt.py` (all 6 domains)

---

## WHAT WE TESTED

### Test Setup
- **Target Document:** National Mutual (Insurance, $500M revenue, 121 IT staff)
- **Buyer Document:** Atlantic International (Insurance, $2B revenue, 568 IT staff)

### Known Overlaps in Test Data
1. **AWS Region Mismatch:**
   - Target: AWS us-east-1
   - Buyer: AWS us-east-2
   - *Should trigger infrastructure overlap finding*

2. **Security Tool Differences:**
   - Target: CrowdStrike + IBM QRadar + RSA SecurID
   - Buyer: Carbon Black + Microsoft Sentinel + Microsoft Authenticator
   - *Should trigger 3 cybersecurity overlap findings*

3. **Team Size Disparity:**
   - Target: 121 IT staff (centralized)
   - Buyer: 568 IT staff (hybrid model)
   - *Should trigger organization overlap finding*

4. **ERP Platform Mismatch:**
   - Target: Oracle ERP Cloud + NetSuite
   - Buyer: Oracle ERP Cloud + NetSuite
   - *Should trigger platform_alignment finding (they match!)*

---

## WHAT ACTUALLY HAPPENED (TEST RESULTS)

### Phase 1 & 2: Fact Extraction ✅ WORKING

**Document Separation:**
```
Document separation: 1 TARGET, 1 BUYER ✅
```

**Facts Extracted:**
```
Total Facts: 108
TARGET Facts: 62 (F-TGT-xxx) ✅
BUYER Facts: 46 (F-BYR-xxx) ✅

Facts by Domain:
                    TARGET    BUYER
applications           34       15
infrastructure          5        8
organization           12       11
cybersecurity           5        5
network                 3        3
identity_access         3        4
```

**Conclusion:** Fact extraction working perfectly. Both entities separated correctly.

---

### Phase 3: Reasoning ❌ NOT WORKING

**Buyer-Aware Features:**
```
Work Items with integration_related:     0/12  ❌
Work Items with overlap_id:              0/12  ❌
Work Items with target_action:           0/12  ❌
Work Items with integration_option:      0/12  ❌
Work Items citing buyer facts:           0/12  ❌

Risks citing buyer facts:                0/22  ❌
```

**Conclusion:** Reasoning agents produced findings, but NO buyer-aware features used!

---

## ROOT CAUSE ANALYSIS

### The Problem: Reasoning Agents Never See Buyer Facts

**Data Flow (Current - BROKEN):**
```
┌─────────────────────────────────────────────────────────────┐
│ FACT EXTRACTION (Working)                                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ Phase 1: Documents → Discovery → FactStore                  │
│          ├─ Target docs → F-TGT-001, F-TGT-002, ... ✅      │
│                                                             │
│ Phase 2: Documents → Discovery → FactStore                  │
│          ├─ Buyer docs → F-BYR-001, F-BYR-002, ... ✅       │
│                                                             │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ REASONING (Broken - Missing Link)                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ Phase 3: Reasoning                                          │
│          ├─ format_for_reasoning(domain, entity="target")   │
│          │  └─ Returns ONLY F-TGT facts                     │
│          │                                                  │
│          ├─ Agent receives inventory with ONLY target facts │
│          │                                                  │
│          ├─ Prompt says: "Generate overlap map..."          │
│          │  BUT agent has NO buyer facts to compare! ❌     │
│          │                                                  │
│          └─ Result: No overlap analysis possible            │
│                     No buyer facts cited                    │
│                     New fields stay empty                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Specific Code Issues

#### ISSUE #1: format_for_reasoning() Only Returns One Entity

**Location:** `stores/fact_store.py:1793`

**Current Implementation:**
```python
def format_for_reasoning(self, domain: str, entity: str = "target") -> str:
    """Format facts for injection into reasoning prompt."""
    with self._lock:
        # Filter by entity - ONLY ONE ENTITY AT A TIME!
        entity_facts = [f for f in self.facts if f.domain == domain and f.entity == entity]

        # Format and return
        return formatted_inventory  # Contains ONLY target OR buyer, not both
```

**What's Missing:**
No function that combines BOTH target and buyer facts in a single inventory format.

**Planned (but not implemented):**
```python
def format_for_reasoning_with_buyer_context(self, domain: str) -> str:
    """
    Format facts with BOTH target and buyer context.

    Returns:
        ## TARGET COMPANY INVENTORY
        [All F-TGT facts for this domain]

        ## BUYER COMPANY REFERENCE
        [All F-BYR facts for this domain]

        ## ANALYSIS GUARDRAILS
        [Rules for using buyer context]
    """
    # NOT IMPLEMENTED YET
```

---

#### ISSUE #2: Reasoning Agents Don't Request Buyer Context

**Location:** `agents_v2/base_reasoning_agent.py:188`

**Current Implementation:**
```python
def reason(self, deal_context: dict) -> dict:
    """Run reasoning for this domain."""

    # Get inventory - USES DEFAULT entity="target"!
    inventory_str = self.fact_store.format_for_reasoning(self.domain)

    # Construct prompt with inventory
    prompt = self.prompt_template.format(
        inventory=inventory_str,  # ONLY contains target facts!
        deal_context=deal_context_str
    )

    # Agent receives prompt with no buyer facts
    # Even though prompt SAYS "generate overlap map", there's no buyer data!
```

**The Problem:**
Even if we create `format_for_reasoning_with_buyer_context()`, this line won't use it unless we change it.

---

## WHY THIS MATTERS (IMPACT)

### Current System Output (Generic)
```
RISK: ERP Consolidation Complexity
The target uses Oracle ERP Cloud for financial management.

MITIGATION: Plan for ERP integration during post-close period.

COST: TBD (requires further analysis)
```

### Desired System Output (Buyer-Aware)
```
RISK: ERP Platform Alignment Opportunity
OVERLAP: OVL-APP-001 (platform_alignment)

The target uses Oracle ERP Cloud (F-TGT-APP-001) serving 1,131 users,
while the buyer also standardized on Oracle ERP Cloud (F-BYR-APP-001)
serving 4,272 users. Platform alignment creates consolidation opportunity.

TARGET ACTION:
Maintain current Oracle ERP operations through Day 100. Document custom
configurations and integration points for migration planning.

INTEGRATION OPTION:
If buyer absorbs target financials: Migrate target users to buyer's
Oracle instance ($400K-800K, 6-9 month timeline, leverages existing
buyer licenses). If target remains separate: Continue standalone
Oracle with seat optimization ($50K savings/yr).

COST ESTIMATE: $400K-800K (one-time) OR $50K savings/yr (ongoing)

EVIDENCE: F-TGT-APP-001, F-TGT-APP-007, F-BYR-APP-001, F-BYR-APP-002
```

**Difference:**
- Specific comparison (not generic "integration needed")
- Concrete options (absorb vs separate)
- Cost estimates (not "TBD")
- Evidence chain to both entities

---

## PROPOSED FIX (15-Point Plan Summary)

### BLOCKERS (2h 45min - Critical Path)

**Point 1: Create Buyer-Aware Formatter (2h)**
- Add `format_for_reasoning_with_buyer_context()` to `fact_store.py`
- Returns inventory with BOTH target and buyer sections
- Includes analysis guardrails

**Point 2: Update Reasoning Agent (15min)**
- Change ONE LINE in `base_reasoning_agent.py:188`
- From: `format_for_reasoning(domain)`
- To: `format_for_reasoning_with_buyer_context(domain)`

**Point 3: Verify Validation Active (30min)**
- Confirm `validate_finding_entity_rules()` is being called
- Should already be working (audit confirmed)

### Database & Testing (7h 15min)

**Points 4-6: Database persistence** (3h)
- Add new fields to WorkItem model
- Update database writer
- Create migration

**Points 7-10: Testing** (4h)
- Unit tests for formatter
- Integration tests for pipeline
- Overlap map tool testing
- Validation rule testing

### Verification (2h)

**Points 11-15: End-to-end validation**
- Run full test with real documents
- Verify specific overlaps detected
- Check database persistence
- Review reasoning quality
- Update documentation

---

## QUESTIONS FOR REVIEW

### 1. Architecture Approach
**Question:** Is the two-phase architecture (TARGET → BUYER → REASONING) the right approach?

**Alternative considered:** Single-phase where both documents are analyzed simultaneously

**Rationale for two-phase:**
- Clearer entity separation
- Buyer analysis can reference target context (useful for comparison)
- Matches M&A workflow (assess target first, then integration)

**Seeking feedback:**
- Are there edge cases this architecture misses?
- Should buyer analysis have access to target facts during discovery?

---

### 2. Inventory Format Design
**Question:** Is the proposed inventory format optimal for LLM reasoning?

**Proposed Format:**
```
## TARGET COMPANY INVENTORY
Entity: TARGET
Total Facts: 34

### ERP SYSTEMS
**F-TGT-APP-001**: Oracle ERP Cloud
- Details: version=23C, users=1131, hosting=Cloud
- Status: active
- Entity: TARGET

[... more target facts ...]

========================================

## BUYER COMPANY REFERENCE (Read-Only Context)
⚠️ PURPOSE: Understand integration implications ONLY
⚠️ DO NOT: Create risks/work items FOR the buyer

Entity: BUYER
Total Facts: 15

### ERP SYSTEMS
**F-BYR-APP-001**: Oracle ERP Cloud
- Details: version=23D, users=4272, hosting=Cloud
- Status: active
- Entity: BUYER

[... more buyer facts ...]

========================================

## ANALYSIS GUARDRAILS
1. TARGET FOCUS: All findings about target
2. ANCHOR RULE: Buyer facts require target facts
3. INTEGRATION CONTEXT: Use buyer for overlap analysis only
```

**Seeking feedback:**
- Is the separation clear enough?
- Are the warnings ("Read-Only", "DO NOT") helpful or redundant?
- Should we include examples of good vs bad findings in the guardrails?

---

### 3. Validation Rules
**Question:** Are the 5 validation rules sufficient to prevent entity mixing?

**Current Rules:**
1. **ANCHOR:** Buyer facts require target facts (prevents buyer-only findings)
2. **AUTO-TAG:** Auto-set integration_related if buyer facts cited
3. **SCOPE:** Warn about "Buyer should..." language
4. **WORK ITEM:** Should have target focus
5. **LEGACY:** Warn about old fact IDs

**Seeking feedback:**
- Are there scenarios these rules don't catch?
- Should we REJECT findings that violate rules, or just WARN?
- Are the rules too strict or too lenient?

---

### 4. Overlap Map Strategy
**Question:** Should overlap map generation be REQUIRED or OPTIONAL?

**Current Approach:** Prompt says "STEP 1: Generate overlap map" but doesn't enforce it

**Alternative:** Make it a required first step (agent must call `generate_overlap_map` before any findings)

**Tradeoffs:**
- **Required:** Ensures consistent overlap analysis, but adds API call overhead
- **Optional:** More flexible, but agents might skip it

**Seeking feedback:**
- Should we enforce overlap map generation?
- If optional, how do we encourage agents to use it?

---

### 5. Field Separation (target_action vs integration_option)
**Question:** Is the separation of target_action vs integration_option clear enough?

**Definition:**
- `target_action`: What target must do (required, regardless of buyer)
- `integration_option`: Buyer-dependent paths (optional, only if buyer involvement changes approach)

**Example:**
```json
{
  "target_action": "Document SAP customizations and create knowledge transfer plan",
  "integration_option": "If buyer migrates target to Oracle: include SAP-to-Oracle mapping in migration plan ($200K additional scope)"
}
```

**Edge Cases:**
- What if target action IS buyer-dependent (e.g., "extend TSA with seller")?
  - Answer: That's still target_action (target negotiates TSA)
- What if there's no buyer involvement needed?
  - Answer: integration_option is null/empty

**Seeking feedback:**
- Are these definitions clear?
- Should we provide more examples in the prompts?
- Are there clearer field names?

---

### 6. Performance & Token Usage
**Question:** Does including buyer facts double the prompt size and cost?

**Current concern:** If we send both target AND buyer facts to reasoning agents, prompts get much larger

**Analysis:**
- Test showed: 62 target facts, 46 buyer facts = 108 total
- Current prompts: ~3,000-5,000 tokens
- With buyer facts: Estimated ~6,000-8,000 tokens
- Cost impact: ~2x per reasoning call

**Mitigation options:**
1. Accept the cost (more comprehensive analysis worth it)
2. Summarize buyer facts (risk losing detail)
3. Only include buyer facts for domains with likely overlap
4. Use prompt caching (already implemented)

**Seeking feedback:**
- Is 2x token cost acceptable for better analysis?
- Should we implement selective buyer fact inclusion?

---

### 7. Error Handling
**Question:** What should happen if buyer facts don't exist?

**Scenarios:**
1. **Target-only analysis:** User uploads only target documents
2. **Buyer docs but no facts extracted:** Buyer doc is empty/incomplete

**Current approach:**
```python
if buyer_facts:
    # Include buyer section
else:
    # Omit buyer section entirely
```

**Seeking feedback:**
- Should we warn if buyer docs uploaded but no facts extracted?
- Should prompts adjust instructions based on buyer fact presence?
- Should overlap map be skipped if no buyer facts?

---

### 8. Testing Strategy
**Question:** What's the right balance of unit vs integration testing?

**Proposed:**
- **Unit tests:** Test formatter, validation rules, dataclass serialization (fast, focused)
- **Integration tests:** Test full pipeline with mock API (slower, comprehensive)
- **End-to-end tests:** Test with real documents and real API (slowest, highest confidence)

**Current gap:** No tests for buyer-aware features at all

**Seeking feedback:**
- Should we mock LLM responses for integration tests?
- How do we test overlap quality without manual review?
- What's the minimum test coverage needed before production?

---

## RISKS & CONCERNS

### Risk 1: LLM Confusion
**Concern:** Even with clear prompts, LLM might confuse target vs buyer

**Mitigation:**
- Clear formatting (TARGET vs BUYER sections)
- Validation rules (reject violations)
- Examples in prompts (show correct usage)

**Question:** Is this enough, or do we need stronger controls?

---

### Risk 2: Prompt Complexity
**Concern:** Buyer-aware prompts are now very long and complex

**Current prompt length:** ~2,000 words for Applications domain

**Components:**
- Original reasoning instructions
- M&A lens framework
- Overlap map generation instructions
- 3-layer output structure
- Buyer context rules
- PE concerns table
- Examples

**Question:** Are we approaching prompt overload? Should we simplify?

---

### Risk 3: Backwards Compatibility
**Concern:** What happens to existing deals/analyses?

**Impact:**
- Existing deals have only target facts (no buyer facts)
- New formatter should handle this gracefully (omit buyer section)
- Existing findings don't have new fields (should be null/empty)

**Question:** Should we migrate existing data or leave as-is?

---

### Risk 4: Database Schema Changes
**Concern:** Adding fields to WorkItem requires migration

**Current schema:** WorkItem has ~15 fields
**New schema:** WorkItem has ~21 fields (6 new)

**Migration risk:**
- Production data needs migration
- New fields nullable (safe)
- No data loss risk

**Question:** Should we version the findings schema?

---

## SUCCESS CRITERIA

After implementing the fix, we expect:

### Quantitative Metrics
- [ ] 100% of domains receive buyer facts in reasoning
- [ ] >5 overlap findings per test run
- [ ] >30% of work items have integration_related=true
- [ ] >10 findings cite buyer facts (F-BYR-xxx)
- [ ] >50% of work items have target_action populated
- [ ] >20% of work items have integration_option populated

### Qualitative Metrics
- [ ] Overlap findings are SPECIFIC (e.g., "SAP vs Oracle") not generic
- [ ] Integration options provide concrete paths with costs
- [ ] Evidence chains trace to both entities
- [ ] No findings violate entity separation rules

### Test Case: Expected Output
Given test documents (National Mutual + Atlantic International), we should see:

**Infrastructure Finding:**
```json
{
  "overlap_id": "OVL-INFRA-001",
  "overlap_type": "cloud_region_mismatch",
  "title": "AWS Region Misalignment",
  "target_summary": "Target uses AWS us-east-1",
  "buyer_summary": "Buyer uses AWS us-east-2",
  "integration_option": "If consolidate to buyer region: migrate target to us-east-2 ($50-100K), OR maintain dual-region ($15K/yr cross-region traffic)"
}
```

**Cybersecurity Finding:**
```json
{
  "overlap_id": "OVL-SEC-001",
  "overlap_type": "security_tool_mismatch",
  "title": "Endpoint Protection Consolidation",
  "target_summary": "Target uses CrowdStrike Falcon",
  "buyer_summary": "Buyer uses Carbon Black",
  "target_action": "Maintain CrowdStrike through Day 100",
  "integration_option": "If standardize on buyer's Carbon Black: migrate target endpoints ($75-150K, 90-day timeline); if keep both: annual cost +$50K for dual licensing"
}
```

---

## REQUEST FOR FEEDBACK

Please review and provide thoughts on:

1. **Architecture:** Is two-phase (TARGET → BUYER → REASONING) optimal?
2. **Inventory Format:** Is the proposed format clear for LLM reasoning?
3. **Validation Rules:** Sufficient to prevent entity confusion?
4. **Overlap Strategy:** Should overlap map be required or optional?
5. **Field Separation:** Are target_action vs integration_option definitions clear?
6. **Performance:** Is 2x token cost acceptable?
7. **Error Handling:** How to handle missing buyer facts?
8. **Testing:** What's the right testing strategy?
9. **Risks:** Any other risks we haven't considered?
10. **Implementation:** Any better approaches to the 2 blockers?

**Specific areas of concern:**
- Prompt complexity (are we overloading the LLM?)
- Entity separation enforcement (are validation rules enough?)
- Cost vs value tradeoff (2x tokens for buyer-aware analysis)

---

## APPENDIX: Code Snippets

### Current Broken Code

**File:** `stores/fact_store.py:1793`
```python
def format_for_reasoning(self, domain: str, entity: str = "target") -> str:
    """CURRENT: Only formats ONE entity."""
    with self._lock:
        entity_facts = [f for f in self.facts if f.domain == domain and f.entity == entity]
        # ... formats only these facts ...
        return formatted_inventory  # Missing buyer facts!
```

**File:** `agents_v2/base_reasoning_agent.py:188`
```python
def reason(self, deal_context: dict) -> dict:
    """CURRENT: Uses default entity=target."""
    inventory_str = self.fact_store.format_for_reasoning(self.domain)
    # Agent never sees buyer facts because of this!
```

---

### Proposed Fix Code

**File:** `stores/fact_store.py` (new function)
```python
def format_for_reasoning_with_buyer_context(self, domain: str) -> str:
    """NEW: Formats BOTH target and buyer."""
    with self._lock:
        target_facts = [f for f in self.facts if f.domain == domain and f.entity == "target"]
        buyer_facts = [f for f in self.facts if f.domain == domain and f.entity == "buyer"]

        output = []

        # Section 1: Target inventory
        output.append("## TARGET COMPANY INVENTORY")
        output.append(self._format_entity_section(target_facts, "TARGET"))

        # Section 2: Buyer reference (if exists)
        if buyer_facts:
            output.append("\n" + "="*70)
            output.append("\n## BUYER COMPANY REFERENCE")
            output.append("⚠️ PURPOSE: Integration context ONLY")
            output.append(self._format_entity_section(buyer_facts, "BUYER"))

            # Section 3: Guardrails
            output.append("\n" + "="*70)
            output.append("\n## ANALYSIS GUARDRAILS")
            output.append("1. TARGET FOCUS: All findings about target")
            output.append("2. ANCHOR RULE: Buyer facts require target facts")
            output.append("3. INTEGRATION CONTEXT: Use buyer for overlaps only")

        return "\n".join(output)
```

**File:** `agents_v2/base_reasoning_agent.py:188` (one line change)
```python
def reason(self, deal_context: dict) -> dict:
    """FIXED: Use buyer-aware formatter."""
    # CHANGE THIS LINE:
    inventory_str = self.fact_store.format_for_reasoning_with_buyer_context(self.domain)
    # That's it! Now agent sees both target and buyer facts.
```

---

## SUMMARY

**What's Working:**
- ✅ Two-phase extraction (target and buyer)
- ✅ Entity tagging and ID convention
- ✅ Validation rules implemented
- ✅ Dataclass fields defined
- ✅ Prompts updated with instructions
- ✅ Tools registered

**What's Broken:**
- ❌ Reasoning agents don't receive buyer facts
- ❌ Because formatter only returns one entity
- ❌ So all downstream features don't work

**The Fix:**
- Create buyer-aware formatter (2h)
- Update agent to use it (15min)
- **Result:** All features immediately functional

**Total effort:** 2h 45min critical path, ~12h full implementation

---

*End of context document. Ready for review and feedback.*
