# Validation System Implementation Plan
## 250 Points to Production-Ready Validation

**Created:** January 2025
**Status:** Planning Complete - Ready for Implementation

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture Summary](#architecture-summary)
3. [Phase 1: Foundation - Data Models & State Management](#phase-1-foundation---data-models--state-management-points-1-15)
4. [Phase 2: Evidence Verification](#phase-2-evidence-verification-points-16-28)
5. [Phase 3: Category Validators - Layer 1](#phase-3-category-validators---layer-1-points-29-45)
6. [Phase 4: Domain Validators - Layer 2](#phase-4-domain-validators---layer-2-points-46-62)
7. [Phase 5: Cross-Domain Consistency - Layer 3](#phase-5-cross-domain-consistency---layer-3-points-63-80)
8. [Phase 6: Adversarial Reviewer](#phase-6-adversarial-reviewer-points-81-90)
9. [Phase 7: Validation Pipeline Orchestrator](#phase-7-validation-pipeline-orchestrator-points-91-100)
10. [Phase 8: Re-extraction Loop](#phase-8-re-extraction-loop-points-101-115)
11. [Phase 9: Correction Pipeline](#phase-9-correction-pipeline-points-116-132)
12. [Phase 10: Human Review API](#phase-10-human-review-api-points-133-145)
13. [Phase 11: Human Review UI](#phase-11-human-review-ui-points-146-167)
14. [Phase 12: Validation Display Integration](#phase-12-validation-display-integration-points-168-180)
15. [Phase 13: Audit Trail & Reporting](#phase-13-audit-trail--reporting-points-181-195)
16. [Phase 14: Configuration & Tuning](#phase-14-configuration--tuning-points-196-205)
17. [Phase 15: Testing](#phase-15-testing-points-206-220)
18. [Phase 16: Performance & Optimization](#phase-16-performance--optimization-points-221-230)
19. [Phase 17: Monitoring & Analytics](#phase-17-monitoring--analytics-points-231-240)
20. [Phase 18: Documentation](#phase-18-documentation-points-241-250)
21. [Implementation Order](#implementation-order-summary)
22. [Sprint Plan](#suggested-implementation-sprints)

---

## Overview

### Core Principles

| Principle | Description |
|-----------|-------------|
| **Bias Toward Flagging** | Missing something = catastrophic. False flag = minor inconvenience. Flag liberally. |
| **Latency Acceptable** | 10 extra minutes << hours of manual work. Be thorough, not fast. |
| **Validation is Visible** | Like reasoning, show users what validation found. Transparency builds trust. |
| **Validation is Living** | AI validates first, humans refine. Status evolves as staff confirms/corrects. |
| **No Hard Blocks** | Don't prevent data from flowing. Flag issues, don't reject entries. |

### The Three-Layer Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    LAYER 3: CROSS-DOMAIN CONSISTENCY                │
│     After all domains complete, check that everything aligns        │
└─────────────────────────────────────────────────────────────────────┘
                                    ▲
        ┌───────────────────────────┼───────────────────────────┐
        │                           │                           │
┌───────┴───────┐           ┌───────┴───────┐           ┌───────┴───────┐
│   LAYER 2:    │           │   LAYER 2:    │           │   LAYER 2:    │
│    Domain     │           │    Domain     │           │    Domain     │
│   Validator   │           │   Validator   │           │   Validator   │
└───────┬───────┘           └───────┬───────┘           └───────┬───────┘
        │                           │                           │
┌───────┴───────┐           ┌───────┴───────┐           ┌───────┴───────┐
│   LAYER 1:    │           │   LAYER 1:    │           │   LAYER 1:    │
│   Category    │           │   Category    │           │   Category    │
│  Checkpoints  │           │  Checkpoints  │           │  Checkpoints  │
└───────────────┘           └───────────────┘           └───────────────┘
```

### Two Feedback Loops

```
LOOP 1: AI SELF-CORRECTION
Extract ──► Validate ──► Incomplete? ──► Re-extract (max 3x) ──► Escalate if still incomplete

LOOP 2: HUMAN CORRECTION WITH RIPPLE EFFECTS
Human corrects ──► Record correction ──► Update derived values ──► Check for new inconsistencies ──► Flag if found
```

---

## Architecture Summary

### Files to Create

```
models/
├── validation_models.py          # Core validation data models
│
stores/
├── validation_store.py           # Validation state persistence
├── correction_store.py           # Correction history persistence
├── audit_store.py                # Audit trail storage
│
tools_v2/
├── evidence_verifier.py          # Quote verification
├── category_checkpoints.py       # Checkpoint definitions
├── category_validator.py         # Layer 1 validation
├── domain_validator.py           # Layer 2 validation
├── cross_domain_validator.py     # Layer 3 validation
├── adversarial_reviewer.py       # Red team review
│
services/
├── validation_pipeline.py        # Orchestrates all validation
├── extraction_orchestrator.py    # Manages re-extraction loop
├── correction_pipeline.py        # Handles human corrections
├── validation_report.py          # Report generation
│
api/
├── review_routes.py              # Review queue API endpoints
│
web/templates/validation/
├── dashboard.html                # Validation overview
├── review_queue.html             # Items needing review
├── components/
│   ├── review_card.html          # Individual review item
│   └── correction_modal.html     # Correction input form
```

---

## Phase 1: Foundation - Data Models & State Management (Points 1-15)

### Validation State Models

- [x] **1.** Create `models/validation_models.py` with `ValidationStatus` enum
  ```python
  class ValidationStatus(Enum):
      EXTRACTED = "extracted"           # Just pulled from doc
      AI_VALIDATED = "ai_validated"     # AI has reviewed
      HUMAN_PENDING = "human_pending"   # Flagged for human review
      HUMAN_CONFIRMED = "confirmed"     # Human verified as correct
      HUMAN_CORRECTED = "corrected"     # Human fixed an error
      HUMAN_REJECTED = "rejected"       # Human says invalid
  ```

- [x] **2.** Create `FlagSeverity` enum
  ```python
  class FlagSeverity(Enum):
      INFO = "info"           # FYI, looks fine
      WARNING = "warning"     # Might be an issue
      ERROR = "error"         # Likely wrong
      CRITICAL = "critical"   # Almost certainly wrong
  ```

- [x] **3.** Create `ValidationFlag` dataclass
  ```python
  @dataclass
  class ValidationFlag:
      flag_id: str
      severity: FlagSeverity
      category: str                    # "completeness", "consistency", "evidence"
      message: str
      suggestion: Optional[str]
      auto_fixable: bool = False
      resolved: bool = False
      resolved_by: Optional[str] = None
      resolved_at: Optional[datetime] = None
      resolution_note: Optional[str] = None
  ```

- [x] **4.** Create `FactValidationState` dataclass
  ```python
  @dataclass
  class FactValidationState:
      fact_id: str
      status: ValidationStatus = ValidationStatus.EXTRACTED
      ai_confidence: float = 0.0
      ai_flags: List[ValidationFlag] = field(default_factory=list)
      ai_validated_at: Optional[datetime] = None
      evidence_verified: Optional[bool] = None
      evidence_match_score: Optional[float] = None
      human_reviewed: bool = False
      human_reviewer: Optional[str] = None
      human_reviewed_at: Optional[datetime] = None
      human_verdict: Optional[str] = None
      human_notes: Optional[str] = None
      original_value: Optional[dict] = None
      corrected_value: Optional[dict] = None
  ```

- [x] **5.** Create `DomainValidationState` dataclass with aggregate stats
  - total_facts, facts_validated, facts_flagged
  - facts_human_reviewed, facts_confirmed, facts_corrected
  - category_completeness dict
  - domain_flags list

- [x] **6.** Create `CrossDomainValidationState` dataclass
  - consistency_checks list
  - consistency_flags list
  - is_consistent property

- [x] **7.** Add `effective_confidence` property to FactValidationState
  - HUMAN_CONFIRMED → 0.95
  - HUMAN_CORRECTED → 1.0
  - HUMAN_REJECTED → 0.0
  - Otherwise → ai_confidence

- [x] **8.** Add `needs_human_review` property
  - True if ai_confidence < 0.7
  - True if any ERROR or CRITICAL flags
  - False if already human_reviewed

### Correction Models

- [x] **9.** Create `CorrectionRecord` dataclass
  ```python
  @dataclass
  class CorrectionRecord:
      correction_id: str
      fact_id: str
      timestamp: datetime
      corrected_by: str
      original_value: Dict[str, Any]
      corrected_value: Dict[str, Any]
      reason: str
      new_evidence: Optional[str] = None
  ```

- [x] **10.** Create `RippleEffect` dataclass
  ```python
  @dataclass
  class RippleEffect:
      field: str
      old_value: Any
      new_value: Any
      reason: str
      affected_fact_ids: List[str]
  ```

- [x] **11.** Create `CorrectionResult` dataclass
  ```python
  @dataclass
  class CorrectionResult:
      success: bool
      correction_id: str
      original_value: Dict[str, Any]
      corrected_value: Dict[str, Any]
      derived_values_updated: List[RippleEffect]
      new_flags_created: List[ValidationFlag]
      message: str
  ```

### Storage Layer

- [x] **12.** Create `stores/validation_store.py`
  - Initialize with session/analysis ID
  - Store validation states in memory with persistence option

- [x] **13.** Add ValidationStore methods
  ```python
  def get_validation_state(fact_id: str) -> FactValidationState
  def update_validation_state(fact_id: str, state: FactValidationState)
  def get_facts_needing_review(domain: str = None) -> List[FactValidationState]
  def get_domain_validation_state(domain: str) -> DomainValidationState
  def mark_human_confirmed(fact_id: str, reviewer: str)
  def mark_human_corrected(fact_id: str, reviewer: str, correction_id: str)
  def add_flag(fact_id: str, flag: ValidationFlag)
  def resolve_flag(fact_id: str, flag_id: str, resolved_by: str, note: str)
  ```

- [x] **14.** Create `stores/correction_store.py`
  - Store all correction records for audit

- [x] **15.** Add CorrectionStore methods
  ```python
  def record_correction(record: CorrectionRecord)
  def get_corrections_for_fact(fact_id: str) -> List[CorrectionRecord]
  def get_all_corrections(domain: str = None) -> List[CorrectionRecord]
  ```

---

## Phase 2: Evidence Verification (Points 16-28)

### Core Evidence Verifier

- [x] **16.** Create `tools_v2/evidence_verifier.py`
  - Import SequenceMatcher from difflib
  - Import logging, re

- [x] **17.** Implement core verification function
  ```python
  def verify_quote_exists(
      quote: str,
      document_text: str,
      threshold: float = 0.85
  ) -> VerificationResult:
      """
      Check if a quote exists in the document.
      Returns match score and verification status.
      """
  ```

- [x] **18.** Use fuzzy string matching with configurable threshold
  - Default threshold: 0.85 for "verified"
  - 0.5-0.85 for "partial_match"
  - Below 0.5 for "not_found"

- [x] **19.** Handle common variations
  - Normalize whitespace (multiple spaces, tabs, newlines)
  - Handle punctuation differences
  - Handle case variations (optional)
  - Handle line break differences

- [x] **20.** Create `VerificationResult` dataclass
  ```python
  @dataclass
  class VerificationResult:
      status: str  # "verified", "partial_match", "not_found"
      match_score: float
      matched_text: Optional[str]  # What was actually found
      quote_provided: str
      search_method: str  # "exact", "fuzzy", "sliding_window"
  ```

### Integration with Fact Store

- [x] **21.** Add evidence fields to Fact model (if not present)
  - evidence_verified: Optional[bool]
  - evidence_match_score: Optional[float]
  - evidence_matched_text: Optional[str]

- [x] **22.** Create batch verification function
  ```python
  def verify_all_facts(
      facts: List[Fact],
      document_text: str
  ) -> Dict[str, VerificationResult]:
      """Verify evidence for all facts in a domain."""
  ```

- [x] **23.** Add evidence verification to fact creation flow
  - Optional: verify at creation time
  - Or: verify in batch during validation phase

### Handling Verification Failures

- [x] **24.** Flag CRITICAL if match_score < 0.5
  ```python
  ValidationFlag(
      severity=FlagSeverity.CRITICAL,
      category="evidence",
      message="Evidence not found in source document - possible hallucination",
      suggestion="Verify this fact manually against the source document"
  )
  ```

- [x] **25.** Flag WARNING if match_score 0.5-0.85
  ```python
  ValidationFlag(
      severity=FlagSeverity.WARNING,
      category="evidence",
      message="Evidence partially matches - may be paraphrased",
      suggestion="Check if the paraphrasing is accurate"
  )
  ```

- [x] **26.** Mark as verified if match_score >= 0.85
  - Update FactValidationState.evidence_verified = True
  - Store match_score for reference

- [x] **27.** Store matched text for human review
  - Shows reviewer what the system actually found
  - Helps identify paraphrasing vs. fabrication

- [x] **28.** Create `EvidenceVerificationReport`
  ```python
  @dataclass
  class EvidenceVerificationReport:
      domain: str
      total_facts: int
      verified_count: int
      partial_match_count: int
      not_found_count: int
      average_match_score: float
      problematic_facts: List[str]  # fact_ids with low scores
  ```

---

## Phase 3: Category Validators - Layer 1 (Points 29-45)

### Checkpoint Definitions

- [x] **29.** Create `tools_v2/category_checkpoints.py`

- [x] **30.** Define `CategoryCheckpoint` dataclass
  ```python
  @dataclass
  class CategoryCheckpoint:
      category: str
      min_expected_items: int
      max_expected_items: int
      required_fields: List[str]
      validation_prompt: str
      importance: str = "high"  # high, medium, low
  ```

- [x] **31.** Create ORGANIZATION_CHECKPOINTS
  ```python
  ORGANIZATION_CHECKPOINTS = {
      "central_it": CategoryCheckpoint(
          category="central_it",
          min_expected_items=5,
          max_expected_items=10,
          required_fields=["headcount", "item"],
          validation_prompt="""..."""
      ),
      "roles": CategoryCheckpoint(...),
      "leadership": CategoryCheckpoint(...),
      "outsourcing": CategoryCheckpoint(...),
  }
  ```

- [x] **32.** Create INFRASTRUCTURE_CHECKPOINTS
  - hosting: min=1, required=[item, location]
  - compute: min=1, required=[item, count]
  - storage: min=1, required=[item]
  - backup_dr: min=1, required=[item]
  - cloud: min=0, required=[provider]

- [x] **33.** Create APPLICATIONS_CHECKPOINTS
  - erp: min=0, max=5, required=[item, vendor]
  - crm: min=0, required=[item]
  - saas: min=0, max=100, required=[item]
  - custom: min=0, required=[item]
  - integration: min=0, required=[item]

- [x] **34.** Create NETWORK_CHECKPOINTS
  - wan: min=1, required=[item]
  - lan: min=1, required=[item]
  - remote_access: min=0, required=[item]
  - dns_dhcp: min=0, required=[item]

- [x] **35.** Create SECURITY_CHECKPOINTS
  - endpoint: min=1, required=[item, vendor]
  - perimeter: min=1, required=[item]
  - detection: min=0, required=[item]
  - vulnerability: min=0, required=[item]

### Category Validator Implementation

- [x] **36.** Create `tools_v2/category_validator.py`
  ```python
  class CategoryValidator:
      def __init__(self, api_key: str, model: str = "claude-3-5-haiku-20241022"):
          self.client = anthropic.Anthropic(api_key=api_key)
          self.model = model
  ```

- [x] **37.** Implement main validation method
  ```python
  def validate_category(
      self,
      domain: str,
      category: str,
      document_text: str,
      extracted_facts: List[Dict]
  ) -> CategoryValidationResult:
  ```

- [x] **38.** Add deterministic pre-checks
  ```python
  # Quick checks before LLM call
  if len(extracted_facts) >= checkpoint.min_expected_items:
      # Might be complete - do quick field check
      missing_fields = self._check_required_fields(extracted_facts, checkpoint)
      if not missing_fields:
          return CategoryValidationResult(is_complete=True, confidence=0.8)
  ```

- [x] **39.** Implement `_extract_relevant_section()`
  ```python
  def _extract_relevant_section(self, document_text: str, category: str) -> str:
      """Find the portion of document most relevant to this category."""
      # Use keyword matching to find relevant paragraphs
      # Return surrounding context (5 lines before/after matches)
  ```

- [x] **40.** Build LLM validation prompt from checkpoint
  ```python
  prompt = checkpoint.validation_prompt.format(
      document_excerpt=document_excerpt[:8000],
      extracted_items=extracted_items_json
  )
  ```

- [x] **41.** Parse LLM response
  ```python
  def _parse_validation_response(self, response_text: str) -> dict:
      # Handle markdown code blocks
      if "```" in response_text:
          response_text = response_text.split("```")[1]
          if response_text.startswith("json"):
              response_text = response_text[4:]
      return json.loads(response_text)
  ```

- [x] **42.** Calculate recommendation
  ```python
  def _determine_recommendation(self, validation_result: dict) -> str:
      missing_count = len(validation_result.get("missing_items", []))
      if validation_result.get("is_complete"):
          return "pass"
      elif missing_count <= 5:
          return "retry"
      else:
          return "retry"  # Still try automated first
  ```

### Integration

- [x] **43.** Create batch validation function
  ```python
  def validate_all_categories(
      self,
      domain: str,
      document_text: str,
      facts: List[Dict]
  ) -> Dict[str, CategoryValidationResult]:
      """Validate all categories for a domain."""
  ```

- [x] **44.** Add results to DomainValidationState
  - Store category_completeness dict
  - Aggregate flags from all categories

- [x] **45.** Log category validation to audit trail
  - Log which categories passed/failed
  - Log any missing items identified

---

## Phase 4: Domain Validators - Layer 2 (Points 46-62)

### Base Domain Validator

- [x] **46.** Create `tools_v2/domain_validator.py`
  ```python
  class DomainValidator:
      def __init__(self, api_key: str, model: str = "claude-3-5-sonnet-20241022"):
          self.client = anthropic.Anthropic(api_key=api_key)
          self.model = model  # Use Sonnet for thorough validation
  ```

- [x] **47.** Use Sonnet model for domain validation
  - More thorough than Haiku
  - Worth the extra cost for accuracy

- [x] **48.** Implement base validate method
  ```python
  def validate(
      self,
      domain: str,
      document_text: str,
      facts: List[Dict],
      gaps: List[Dict]
  ) -> DomainValidationResult:
      if domain == "organization":
          return self.validate_organization(document_text, facts, gaps)
      elif domain == "infrastructure":
          return self.validate_infrastructure(document_text, facts, gaps)
      # ... etc
  ```

### Organization Domain Validator

- [x] **49.** Implement `validate_organization()` method
  ```python
  def validate_organization(
      self,
      document_text: str,
      facts: List[Dict],
      gaps: List[Dict]
  ) -> DomainValidationResult:
  ```

- [x] **50.** Check 1: Team extraction completeness
  ```python
  central_it_facts = [f for f in facts if f.get("category") == "central_it"]
  team_count = len(central_it_facts)
  if team_count < 5:
      result.recommendations.append(f"Only {team_count} teams extracted. Expected 5-7.")
      result.completeness_score -= 0.2
  ```

- [x] **51.** Check 2: Headcount consistency
  ```python
  total_extracted = sum(int(f.get("details", {}).get("headcount", 0)) for f in central_it_facts)
  stated_total = self._find_stated_headcount(document_text, facts)
  if stated_total and total_extracted:
      ratio = total_extracted / stated_total
      if ratio < 0.8:
          result.inconsistencies.append(f"Headcount mismatch: {total_extracted} vs {stated_total}")
          result.requires_rerun = True
  ```

- [x] **52.** Check 3: Required categories present
  ```python
  required = ["central_it", "leadership"]
  for cat in required:
      if cat not in facts_by_category:
          result.completeness_score -= 0.15
          result.recommendations.append(f"Missing required category: {cat}")
  ```

- [x] **53.** Check 4: LLM deep validation
  ```python
  llm_result = self._llm_validate_organization(document_text, facts)
  if llm_result.get("missing_items"):
      result.missing_items.extend(llm_result["missing_items"])
  ```

- [x] **54.** Calculate completeness_score
  - Start at 1.0
  - Subtract for each issue found
  - Cap at 0.0 minimum

- [x] **55.** Determine requires_rerun threshold
  ```python
  result.requires_rerun = result.completeness_score < 0.7
  ```

- [x] **56.** Generate rerun_guidance
  ```python
  if result.requires_rerun:
      result.rerun_guidance = self._generate_rerun_guidance(result)
  ```

### Infrastructure Domain Validator

- [x] **57.** Implement `validate_infrastructure()` method

- [x] **58.** Check: Required categories present
  - hosting required
  - compute required

- [x] **59.** Check: DR/backup documented
  - Flag if no backup_dr category facts

- [x] **60.** LLM validation for infrastructure completeness

### Applications Domain Validator

- [x] **61.** Implement `validate_applications()` method

- [x] **62.** Check: Major categories covered or gaps flagged

---

## Phase 5: Cross-Domain Consistency - Layer 3 (Points 63-80) ✅ COMPLETE

### Consistency Checker Core

- [x] **63.** Create `tools_v2/cross_domain_validator.py`
  ```python
  class CrossDomainValidator:
      def __init__(self, api_key: str):
          self.client = anthropic.Anthropic(api_key=api_key)
  ```

- [x] **64.** Implement main validation method
  ```python
  def validate_all(
      self,
      fact_store: FactStore,
      document_text: str
  ) -> CrossDomainValidationResult:
  ```

- [x] **65.** Create ConsistencyCheck dataclass
  ```python
  @dataclass
  class ConsistencyCheck:
      check_name: str
      domains_involved: List[str]
      is_consistent: bool
      expected_value: Any
      actual_value: Any
      discrepancy: Optional[str] = None
      severity: str = "medium"
  ```

### Consistency Checks

- [x] **66.** Check 1: Headcount vs Endpoints ratio
  ```python
  def _check_headcount_vs_endpoints(self, org_facts, infra_facts) -> ConsistencyCheck:
      headcount = self._get_total_headcount(org_facts)
      endpoints = self._get_endpoint_count(infra_facts)
      ratio = endpoints / headcount
      is_reasonable = 20 <= ratio <= 200
      return ConsistencyCheck(
          check_name="Headcount vs. Endpoints Ratio",
          domains_involved=["organization", "infrastructure"],
          is_consistent=is_reasonable,
          expected_value="20-200 endpoints per IT person",
          actual_value=f"{ratio:.1f} endpoints per IT person"
      )
  ```

- [x] **67.** Check 2: Headcount vs Application count
  - Expect 0.5-30 apps per IT person
  - Flag if outside range

- [x] **68.** Check 3: Outsourcing vendor consistency
  - Vendors mentioned in org should appear in infra/apps details
  - Flag if org mentions vendors not found elsewhere

- [x] **69.** Check 4: Security team vs security tools
  - If security team exists → security infrastructure should be documented
  - Flag if team but no tools

- [x] **70.** Check 5: Cost per head sanity
  - Total IT cost / headcount should be $50K-$300K
  - Flag if outside range

- [x] **71.** Check 6: Total budget vs component costs
  - Sum of team costs should approximate total budget
  - Flag significant discrepancies

- [x] **72.** Check 7: Stated totals vs calculated totals
  - Document says "141 headcount"
  - Sum of teams should be close to 141

### LLM Holistic Review

- [x] **73.** Implement `_llm_holistic_review()`
  ```python
  def _llm_holistic_review(
      self,
      org_facts: Dict,
      infra_facts: Dict,
      app_facts: Dict,
      document_text: str
  ) -> Dict[str, Any]:
  ```

- [x] **74.** Build summary of all domains for LLM
  ```python
  summary = {
      "organization": {"fact_count": X, "categories": [...], "sample_items": [...]},
      "infrastructure": {...},
      "applications": {...}
  }
  ```

- [x] **75.** Prompt LLM for holistic analysis
  - Find logical inconsistencies
  - Identify missing coverage
  - Flag data quality issues

- [x] **76.** Parse and incorporate LLM findings

### Helper Methods

- [x] **77.** Implement `_get_total_headcount()`
  - Check for total_it_headcount in facts
  - Fallback: sum team headcounts

- [x] **78.** Implement `_get_endpoint_count()`
  - Look for count, endpoint_count, server_count in infra facts

- [x] **79.** Implement `_get_total_cost()`
  - Look for budget facts
  - Parse cost strings ($1.2M, $19,632,626)

- [x] **80.** Implement `_extract_vendors()`
  - Find vendor names across all domains
  - Normalize names for comparison

---

## Phase 6: Adversarial Reviewer (Points 81-90) ✅ COMPLETE

### Adversarial Agent

- [x] **81.** Create `tools_v2/adversarial_reviewer.py`
  ```python
  class AdversarialReviewer:
      def __init__(self, api_key: str):
          self.client = anthropic.Anthropic(api_key=api_key)
  ```

- [x] **82.** Design red team system prompt
  ```python
  ADVERSARIAL_PROMPT = """
  You are a skeptical reviewer. Your job is to find errors,
  inconsistencies, and gaps in this extraction.

  ASSUME THERE ARE PROBLEMS and find them.

  Be harsh but fair. For each issue found:
  1. What the problem is
  2. Why it matters for due diligence
  3. How to fix it
  """
  ```

- [x] **83.** Implement review method
  ```python
  def review_domain(
      self,
      domain: str,
      document_text: str,
      facts: List[Dict]
  ) -> List[AdversarialFinding]:
  ```

- [x] **84.** Focus areas for adversarial review
  - Missing information that should exist
  - Numbers that don't make sense
  - Suspicious patterns (too round, too perfect)
  - Gaps in coverage
  - Evidence quality issues

### Finding Categories

- [x] **85.** Define finding types
  ```python
  class FindingType(Enum):
      MISSING_DATA = "missing_data"
      INCONSISTENCY = "inconsistency"
      SUSPICIOUS_VALUE = "suspicious_value"
      COVERAGE_GAP = "coverage_gap"
      EVIDENCE_QUALITY = "evidence_quality"
  ```

- [x] **86.** Create AdversarialFinding dataclass
  ```python
  @dataclass
  class AdversarialFinding:
      finding_type: FindingType
      description: str
      affected_facts: List[str]
      suggested_action: str
      confidence: float
  ```

### Integration

- [x] **87.** Run adversarial review after domain validation passes
  - Only if domain validation passed (don't pile on)
  - Catches things neutral validation misses

- [x] **88.** Add adversarial findings to validation flags
  - Convert findings to ValidationFlags
  - Use WARNING severity (speculative)

- [x] **89.** Weight adversarial findings appropriately
  - Lower weight than direct validation findings
  - They're "things to consider" not "definite problems"

- [x] **90.** Log adversarial findings separately
  - Track false positive rate over time
  - Tune prompts based on accuracy

---

## Phase 7: Validation Pipeline Orchestrator (Points 91-100)

### Pipeline Orchestrator

- [x] **91.** Create `services/validation_pipeline.py`
  ```python
  class ValidationPipeline:
      def __init__(self, api_key: str):
          self.evidence_verifier = EvidenceVerifier()
          self.category_validator = CategoryValidator(api_key)
          self.domain_validator = DomainValidator(api_key)
          self.cross_domain_validator = CrossDomainValidator(api_key)
          self.adversarial_reviewer = AdversarialReviewer(api_key)
  ```

- [x] **92.** Initialize with all validators

- [x] **93.** Implement main validation method
  ```python
  def validate_domain(
      self,
      domain: str,
      document_text: str,
      fact_store: FactStore,
      run_layer3: bool = False
  ) -> ValidationPipelineResult:
  ```

### Pipeline Flow

- [x] **94.** Step 1: Evidence verification
  ```python
  evidence_results = self.evidence_verifier.verify_all_facts(
      facts=domain_facts,
      document_text=document_text
  )
  # Add evidence flags to validation state
  ```

- [x] **95.** Step 2: Category checkpoints
  ```python
  category_results = {}
  for category in categories:
      category_facts = [f for f in facts if f["category"] == category]
      result = self.category_validator.validate_category(
          domain, category, document_text, category_facts
      )
      category_results[category] = result
  ```

- [x] **96.** Step 3: Domain validation
  ```python
  domain_result = self.domain_validator.validate(
      domain, document_text, facts, gaps
  )
  ```

- [x] **97.** Step 4: Adversarial review
  ```python
  if not domain_result.requires_rerun:  # Only if domain passed
      adversarial_findings = self.adversarial_reviewer.review_domain(
          domain, document_text, facts
      )
  ```

- [x] **98.** Step 5: Cross-domain (if requested)
  ```python
  if run_layer3:
      cross_domain_result = self.cross_domain_validator.validate_all(
          fact_store, document_text
      )
  ```

- [x] **99.** Aggregate results
  ```python
  return ValidationPipelineResult(
      layer1_results=category_results,
      layer2_result=domain_result,
      layer3_result=cross_domain_result,
      overall_valid=...,
      requires_rerun=...,
      human_review_needed=...
  )
  ```

- [x] **100.** Determine final status
  - overall_valid: True if no major issues
  - requires_rerun: True if domain validation failed
  - human_review_needed: True if critical flags or cross-domain issues

---

## Phase 8: Re-extraction Loop (Points 101-115)

### Extraction Orchestrator Updates

- [x] **101.** Create `services/extraction_orchestrator.py`
  ```python
  class ExtractionOrchestrator:
      def __init__(self, api_key: str, fact_store: FactStore):
          self.api_key = api_key
          self.fact_store = fact_store
          self.validation_pipeline = ValidationPipeline(api_key)
          self.rerun_counts = {}
  ```

- [x] **102.** Add MAX_RERUN_ATTEMPTS constant
  ```python
  MAX_RERUN_ATTEMPTS = 3
  ```

- [x] **103.** Implement main extract_domain method
  ```python
  async def extract_domain(
      self,
      domain: str,
      document_text: str,
      document_name: str
  ) -> ExtractionResult:
      self.rerun_counts[domain] = 0

      while True:
          # Extract
          # Validate
          # Decide: pass, retry, or escalate
  ```

- [x] **104.** Track rerun_counts per domain

### Targeted Re-extraction

- [x] **105.** Implement targeted re-extraction
  ```python
  async def _run_targeted_extraction(
      self,
      domain: str,
      document_text: str,
      document_name: str,
      missing_items: List[dict]
  ) -> dict:
  ```

- [x] **106.** Build targeted prompt
  ```python
  def _build_targeted_prompt(
      self,
      domain: str,
      existing_items: List[str],
      missing_items: List[dict],
      document_text: str
  ) -> str:
      return f"""
      You are completing an INCOMPLETE extraction.

      ALREADY EXTRACTED (do not re-extract):
      {existing_items}

      MISSING ITEMS (you MUST extract):
      {missing_items}

      Focus ONLY on the missing items.
      """
  ```

- [x] **107.** Pass targeted prompt to discovery agent
  - Override system prompt
  - Or pass as additional context

- [x] **108.** Merge new facts into existing store
  - Check for duplicates
  - Add new facts to same domain

### Re-validation Loop

- [x] **109.** After re-extraction, validate again
  ```python
  validation_result = self.validation_pipeline.validate_domain(
      domain, document_text, self.fact_store
  )
  ```

- [x] **110.** If still incomplete and under max retries: retry
  ```python
  if validation_result.requires_rerun:
      self.rerun_counts[domain] += 1
      if self.rerun_counts[domain] < MAX_RERUN_ATTEMPTS:
          continue  # Loop again
  ```

- [x] **111.** If at max retries: escalate
  ```python
  if self.rerun_counts[domain] >= MAX_RERUN_ATTEMPTS:
      return self._escalate_to_human(domain, validation_result)
  ```

- [x] **112.** Create EscalationRecord
  ```python
  @dataclass
  class EscalationRecord:
      domain: str
      attempts: int
      remaining_issues: List[dict]
      suggested_actions: List[str]
      timestamp: datetime
  ```

### Escalation Handling

- [x] **113.** Implement escalation method
  ```python
  def _escalate_to_human(
      self,
      domain: str,
      validation_result: DomainValidationResult
  ) -> ExtractionResult:
  ```

- [x] **114.** Add to human review queue with HIGH priority
  - Include all context
  - Mark as "extraction_escalation"

- [x] **115.** Include full context in escalation
  - What was tried (attempt count)
  - What failed (validation results)
  - What's still missing (specific items)
  - Suggested manual actions

---

## Phase 9: Correction Pipeline (Points 116-132) ✅ COMPLETE

### Correction Pipeline Core

- [x] **116.** Create `services/correction_pipeline.py`
  ```python
  class CorrectionPipeline:
      def __init__(self, fact_store, validation_store, api_key: str):
          self.fact_store = fact_store
          self.validation_store = validation_store
          self.consistency_checker = ConsistencyChecker(api_key)
  ```

- [x] **117.** Implement main correction method
  ```python
  def apply_correction(
      self,
      fact_id: str,
      corrected_fields: Dict[str, Any],
      reason: str,
      corrected_by: str,
      new_evidence: Optional[str] = None
  ) -> CorrectionResult:
  ```

- [x] **118.** Step 1: Validate fact exists
  ```python
  fact = self.fact_store.get_fact(fact_id)
  if not fact:
      return CorrectionResult(success=False, message="Fact not found")
  ```

- [x] **119.** Step 2: Store original values
  ```python
  original_value = {
      field: fact.details.get(field)
      for field in corrected_fields.keys()
  }
  ```

- [x] **120.** Step 3: Generate correction_id
  ```python
  correction_id = f"CORR-{datetime.now().strftime('%Y%m%d%H%M%S')}"
  ```

- [x] **121.** Step 4: Record correction
  ```python
  correction_record = CorrectionRecord(
      correction_id=correction_id,
      fact_id=fact_id,
      timestamp=datetime.now(),
      corrected_by=corrected_by,
      original_value=original_value,
      corrected_value=corrected_fields,
      reason=reason,
      new_evidence=new_evidence
  )
  self.correction_store.record_correction(correction_record)
  ```

- [x] **122.** Step 5: Update fact
  ```python
  for field, new_value in corrected_fields.items():
      fact.details[field] = new_value
  self.fact_store.update_fact(fact)
  ```

- [x] **123.** Step 6: Update validation state
  ```python
  self.validation_store.mark_human_corrected(
      fact_id=fact_id,
      corrected_by=corrected_by,
      correction_id=correction_id
  )
  ```

### Ripple Effect Analysis

- [x] **124.** Implement ripple effect calculation
  ```python
  def _update_derived_values(
      self,
      corrected_fact: Dict,
      corrected_fields: Dict
  ) -> List[RippleEffect]:
  ```

- [x] **125.** Define dependency rules
  - headcount changes → recalculate totals
  - personnel_cost changes → recalculate per-head metrics
  - vendor changes → check cross-domain references

- [x] **126.** Implement headcount recalculation
  ```python
  def _recalculate_headcount_totals(self, corrected_fact) -> List[RippleEffect]:
      # Sum all team headcounts
      # Update derived total_it_headcount
  ```

- [x] **127.** Implement cost metrics recalculation
  ```python
  def _recalculate_cost_metrics(self, corrected_fact) -> List[RippleEffect]:
      # Recalculate cost_per_head
      # Recalculate cost_per_person for team
  ```

- [x] **128.** Store derived values with source tracking
  ```python
  self.fact_store.set_derived_value(
      key="total_it_headcount",
      value=new_total,
      derived_from=[corrected_fact["fact_id"]],
      note="Recalculated after human correction"
  )
  ```

### New Inconsistency Detection

- [x] **129.** Implement new inconsistency check
  ```python
  def _check_for_new_inconsistencies(
      self,
      corrected_fact: Dict,
      corrected_fields: Dict
  ) -> List[ValidationFlag]:
  ```

- [x] **130.** Check cost-per-person sanity after correction
  ```python
  if "headcount" in corrected_fields:
      cost = fact.details.get("personnel_cost")
      headcount = corrected_fields["headcount"]
      cost_per_person = cost / headcount

      expected_range = self._get_expected_salary_range(fact.category)
      if cost_per_person < expected_range[0] * 0.7:
          # Flag as WARNING - cost might also be wrong
  ```

- [x] **131.** Check cross-domain consistency after correction
  ```python
  cross_domain_flags = self.consistency_checker.check_after_correction(
      corrected_fact, corrected_fields
  )
  ```

- [x] **132.** Add new flags (don't block correction)
  ```python
  for flag in new_flags:
      self.validation_store.add_flag(
          fact_id=flag["fact_id"],
          flag=flag,
          source="correction_ripple"
      )
  ```

---

## Phase 10: Human Review API (Points 133-145) ✅ COMPLETE

### Review Queue API

- [x] **133.** Create `api/review_routes.py`
  ```python
  from flask import Blueprint, request, jsonify

  review_bp = Blueprint('review', __name__, url_prefix='/api/review')
  ```

- [x] **134.** GET `/api/review/queue`
  ```python
  @review_bp.route('/queue', methods=['GET'])
  def get_review_queue():
      domain = request.args.get('domain')
      severity = request.args.get('severity')
      items = validation_store.get_facts_needing_review(
          domain=domain,
          min_severity=severity
      )
      return jsonify({"items": items, "total": len(items)})
  ```

- [x] **135.** GET `/api/review/queue/{fact_id}`
  ```python
  @review_bp.route('/queue/<fact_id>', methods=['GET'])
  def get_review_item(fact_id):
      state = validation_store.get_validation_state(fact_id)
      fact = fact_store.get_fact(fact_id)
      return jsonify({
          "fact": fact.to_dict(),
          "validation_state": state.to_dict(),
          "evidence": fact.evidence,
          "flags": [f.to_dict() for f in state.ai_flags]
      })
  ```

- [x] **136.** GET `/api/review/stats`
  ```python
  @review_bp.route('/stats', methods=['GET'])
  def get_review_stats():
      return jsonify({
          "total_flagged": validation_store.count_flagged(),
          "total_reviewed": validation_store.count_reviewed(),
          "by_domain": validation_store.get_stats_by_domain(),
          "by_severity": validation_store.get_stats_by_severity()
      })
  ```

### Review Actions API

- [x] **137.** POST `/api/review/{fact_id}/confirm`
  ```python
  @review_bp.route('/<fact_id>/confirm', methods=['POST'])
  def confirm_fact(fact_id):
      data = request.json
      validation_store.mark_human_confirmed(
          fact_id=fact_id,
          reviewer=data.get('reviewer'),
          notes=data.get('notes')
      )
      return jsonify({"status": "confirmed"})
  ```

- [x] **138.** POST `/api/review/{fact_id}/correct`
  ```python
  @review_bp.route('/<fact_id>/correct', methods=['POST'])
  def correct_fact(fact_id):
      data = request.json
      result = correction_pipeline.apply_correction(
          fact_id=fact_id,
          corrected_fields=data['corrected_fields'],
          reason=data['reason'],
          corrected_by=data['corrected_by'],
          new_evidence=data.get('new_evidence')
      )
      return jsonify(result.to_dict())
  ```

- [x] **139.** POST `/api/review/{fact_id}/reject`
  ```python
  @review_bp.route('/<fact_id>/reject', methods=['POST'])
  def reject_fact(fact_id):
      data = request.json
      validation_store.mark_human_rejected(
          fact_id=fact_id,
          reviewer=data.get('reviewer'),
          reason=data.get('reason')
      )
      return jsonify({"status": "rejected"})
  ```

- [x] **140.** POST `/api/review/{fact_id}/skip`
  ```python
  @review_bp.route('/<fact_id>/skip', methods=['POST'])
  def skip_fact(fact_id):
      # Mark as skipped but keep in queue
      return jsonify({"status": "skipped"})
  ```

- [x] **141.** POST `/api/review/{fact_id}/flag`
  ```python
  @review_bp.route('/<fact_id>/flag', methods=['POST'])
  def add_manual_flag(fact_id):
      data = request.json
      flag = ValidationFlag(
          flag_id=generate_flag_id(),
          severity=FlagSeverity(data['severity']),
          category="manual",
          message=data['message'],
          suggestion=data.get('suggestion')
      )
      validation_store.add_flag(fact_id, flag, source="manual")
      return jsonify({"flag_id": flag.flag_id})
  ```

### Validation Status API

- [x] **142.** GET `/api/validation/status`
  ```python
  @review_bp.route('/validation/status', methods=['GET'])
  def get_validation_status():
      return jsonify({
          "overall_confidence": validation_store.get_overall_confidence(),
          "domains": validation_store.get_all_domain_states(),
          "cross_domain": validation_store.get_cross_domain_state()
      })
  ```

- [x] **143.** GET `/api/validation/status/{domain}`

- [x] **144.** GET `/api/validation/flags`

- [x] **145.** GET `/api/validation/audit/{fact_id}`

---

## Phase 11: Human Review UI (Points 146-167) ✅ COMPLETE

### Review Dashboard Page

- [x] **146.** Create `web/templates/validation/dashboard.html`
  - Extends base layout
  - Includes validation CSS

- [x] **147.** Show overall confidence score
  ```html
  <div class="confidence-bar">
    <div class="confidence-fill" style="width: {{ confidence }}%"></div>
    <span class="confidence-label">{{ confidence }}%</span>
  </div>
  ```

- [x] **148.** Show domain status table
  ```html
  <table class="domain-status-table">
    <tr>
      <th>Domain</th><th>AI Conf.</th><th>Flagged</th><th>Reviewed</th><th>Status</th>
    </tr>
    {% for domain in domains %}
    <tr>
      <td>{{ domain.name }}</td>
      <td>{{ domain.ai_confidence }}%</td>
      <td>{{ domain.flagged_count }}</td>
      <td>{{ domain.reviewed_count }} / {{ domain.flagged_count }}</td>
      <td>{{ domain.status_icon }}</td>
    </tr>
    {% endfor %}
  </table>
  ```

- [x] **149.** Show cross-domain consistency results

- [x] **150.** Add "Review All" button

### Review Queue Page

- [x] **151.** Create `web/templates/validation/review_queue.html`

- [x] **152.** List items needing review
  - Sort by severity (CRITICAL first)
  - Show fact summary, flag message, confidence

- [x] **153.** Show filters
  - By domain dropdown
  - By severity dropdown
  - By category dropdown

- [x] **154.** Add pagination

- [x] **155.** Show empty state when queue is clear

### Review Card Component

- [x] **156.** Create review card showing fact details
  ```html
  <div class="review-card severity-{{ flag.severity }}">
    <div class="card-header">
      <span class="severity-badge">{{ flag.severity }}</span>
      <span class="domain-category">{{ fact.domain }} / {{ fact.category }}</span>
    </div>
    <div class="card-body">
      <h4>{{ fact.item }}</h4>
      <p class="flag-message">{{ flag.message }}</p>
    </div>
  </div>
  ```

- [x] **157.** Show evidence verification status
  ```html
  <div class="evidence-status">
    <span class="status-icon {{ evidence_status }}"></span>
    Evidence: {{ evidence_status_label }}
    {% if match_score %}({{ match_score }}% match){% endif %}
  </div>
  ```

- [x] **158.** Show source document viewer/link

- [x] **159.** Add action buttons
  ```html
  <div class="action-buttons">
    <button class="btn-confirm" onclick="confirmFact('{{ fact.id }}')">✓ Confirm</button>
    <button class="btn-correct" onclick="showCorrectionModal('{{ fact.id }}')">✎ Correct</button>
    <button class="btn-reject" onclick="rejectFact('{{ fact.id }}')">✗ Reject</button>
    <button class="btn-skip" onclick="skipFact('{{ fact.id }}')">Skip</button>
  </div>
  ```

- [x] **160.** Add notes field

### Correction Modal

- [x] **161.** Create correction modal
  ```html
  <div class="modal" id="correction-modal">
    <div class="modal-content">
      <h3>Correct Fact</h3>
      <div id="correction-form"></div>
    </div>
  </div>
  ```

- [x] **162.** Show original value(s)

- [x] **163.** Input fields for corrected values
  - Dynamic based on field type
  - Validation on input

- [x] **164.** Required: reason for correction

- [x] **165.** Optional: updated evidence quote

### Confirmation Flow

- [x] **166.** Show ripple effect summary after correction
  ```html
  <div class="ripple-summary">
    <h4>This correction will update:</h4>
    <ul>
      {% for effect in ripple_effects %}
      <li>{{ effect.field }}: {{ effect.old }} → {{ effect.new }}</li>
      {% endfor %}
    </ul>
  </div>
  ```

- [x] **167.** Show new flags warning if any created

---

## Phase 12: Validation Display Integration (Points 168-180) ✅ COMPLETE

### Domain Pages Updates

- [x] **168.** Add validation banner to organization overview
  ```html
  {% if validation_state %}
  <div class="validation-banner status-{{ validation_state.status }}">
    <span class="confidence">{{ validation_state.confidence }}% confidence</span>
    <span class="review-status">{{ validation_state.reviewed }} / {{ validation_state.flagged }} reviewed</span>
    <a href="{{ url_for('validation.review_queue', domain='organization') }}">Review</a>
  </div>
  {% endif %}
  ```

- [x] **169.** Add banner to infrastructure overview

- [x] **170.** Add banner to applications overview

- [x] **171.** Show per-fact confidence indicators
  ```html
  <span class="confidence-dot {{ fact.confidence_class }}"></span>
  ```

- [x] **172.** Show "Needs Review" badge
  ```html
  {% if fact.needs_review %}
  <span class="badge badge-warning">Needs Review</span>
  {% endif %}
  ```

- [x] **173.** Show "Human Verified" badge
  ```html
  {% if fact.human_confirmed %}
  <span class="badge badge-success">✓ Verified</span>
  {% endif %}
  ```

- [x] **174.** Show "Corrected" badge with tooltip

- [x] **175.** Style badges and indicators

### Fact Detail Expansion

- [x] **176.** Add expandable detail section
  ```html
  <tr class="fact-row" onclick="toggleDetail('{{ fact.id }}')">
    ...
  </tr>
  <tr class="fact-detail" id="detail-{{ fact.id }}">
    <td colspan="5">
      <!-- Full evidence, validation history, etc. -->
    </td>
  </tr>
  ```

- [x] **177.** Show full evidence quote with verification

- [x] **178.** Show validation history

- [x] **179.** Show correction history if corrected

- [x] **180.** Add inline "Review" button

---

## Phase 13: Audit Trail & Reporting (Points 181-195) ✅ COMPLETE

### Audit Trail Storage

- [x] **181.** Create `stores/audit_store.py`

- [x] **182.** Define AuditEntry dataclass
  ```python
  @dataclass
  class AuditEntry:
      timestamp: datetime
      action: str
      fact_id: Optional[str]
      user: Optional[str]
      previous_state: Optional[dict]
      new_state: Optional[dict]
      details: dict
  ```

- [x] **183.** Implement `log_action()`

- [x] **184.** Implement `get_audit_trail(fact_id)`

- [x] **185.** Implement `get_audit_log(filters)`

### Audit Actions to Log

- [x] **186.** Log extraction events
  - fact_extracted
  - fact_validated
  - flag_added
  - flag_resolved

- [x] **187.** Log human review events
  - human_review_started
  - human_confirmed
  - human_corrected
  - human_rejected

- [x] **188.** Log system events
  - reextraction_triggered
  - reextraction_completed
  - escalation_created

- [x] **189.** Log derived value events
  - derived_value_updated
  - consistency_check_run

### Validation Report Generation

- [x] **190.** Create `services/validation_report.py`

- [x] **191.** Generate summary report
  - Overall confidence
  - Flags by severity
  - Review progress

- [x] **192.** Generate detailed report
  - Per-domain breakdown
  - Per-category breakdown

- [x] **193.** Generate audit report
  - All actions taken
  - Corrections made

- [x] **194.** Export to PDF

- [x] **195.** Include validation status in main DD report

---

## Phase 14: Configuration & Tuning (Points 196-205) ✅ COMPLETE

### Configuration File

- [x] **196.** Add validation config section to `config_v2.py`

- [x] **197.** VALIDATION_ENABLED (bool)
  ```python
  VALIDATION_ENABLED = True  # Master switch
  ```

- [x] **198.** EVIDENCE_MATCH_THRESHOLD (float)
  ```python
  EVIDENCE_MATCH_THRESHOLD = 0.85
  ```

- [x] **199.** CONFIDENCE_THRESHOLD_FOR_REVIEW (float)
  ```python
  CONFIDENCE_THRESHOLD_FOR_REVIEW = 0.7
  ```

- [x] **200.** MAX_REEXTRACTION_ATTEMPTS (int)
  ```python
  MAX_REEXTRACTION_ATTEMPTS = 3
  ```

- [x] **201.** VALIDATION_MODEL (str)
  ```python
  VALIDATION_MODEL = "claude-3-5-sonnet-20241022"
  ```

- [x] **202.** ADVERSARIAL_REVIEW_ENABLED (bool)
  ```python
  ADVERSARIAL_REVIEW_ENABLED = True
  ```

### Category-Specific Thresholds

- [x] **203.** MIN_EXPECTED_TEAMS
  ```python
  MIN_EXPECTED_TEAMS = 5
  ```

- [x] **204.** EXPECTED_SALARY_RANGES
  ```python
  EXPECTED_SALARY_RANGES = {
      "leadership": (150000, 300000),
      "applications": (90000, 160000),
      "infrastructure": (80000, 140000),
      "security": (100000, 180000),
      "service_desk": (50000, 90000),
      "pmo": (90000, 150000),
  }
  ```

- [x] **205.** CONSISTENCY_CHECK_THRESHOLDS
  ```python
  CONSISTENCY_CHECK_THRESHOLDS = {
      "headcount_vs_endpoints": (20, 200),
      "headcount_vs_apps": (0.5, 30),
      "cost_per_head": (50000, 300000),
  }
  ```

---

## Phase 15: Testing (Points 206-220) ✅ COMPLETE

### Unit Tests

- [x] **206.** Test ValidationFlag creation and serialization

- [x] **207.** Test FactValidationState.effective_confidence

- [x] **208.** Test evidence_verifier with scenarios
  - Exact match
  - Partial match
  - No match
  - Whitespace variations

- [x] **209.** Test category_validator checkpoint logic

- [x] **210.** Test correction_pipeline ripple effects

### Integration Tests

- [x] **211.** Test full validation pipeline on sample doc

- [x] **212.** Test re-extraction loop triggers

- [x] **213.** Test human correction updates derived values

- [x] **214.** Test cross-domain with intentional inconsistencies

- [x] **215.** Test escalation after max retries

### End-to-End Tests

- [x] **216.** Test: Upload → Extract → Validate → Review → Confirm

- [x] **217.** Test: Upload → Extract → Validate → Reextract → Pass

- [x] **218.** Test: Review → Correct → Ripple → New flag

- [x] **219.** Test with real VDR document

- [x] **220.** Test audit trail captures all actions

---

## Phase 16: Performance & Optimization (Points 221-230) ✅ COMPLETE

### Parallel Validation

- [x] **221.** Run evidence verification in parallel

- [x] **222.** Run category validators in parallel

- [x] **223.** Run domain validation after categories

- [x] **224.** Run cross-domain only after all domains

### Caching

- [x] **225.** Cache document text parsing

- [x] **226.** Cache LLM responses for identical prompts

- [x] **227.** Implement incremental validation

### Cost Optimization

- [x] **228.** Use Haiku for category checkpoints

- [x] **229.** Use Sonnet only for domain/adversarial

- [x] **230.** Skip adversarial if major issues found

---

## Phase 17: Monitoring & Analytics (Points 231-240) ✅ COMPLETE

### Metrics Collection

- [x] **231.** Track validation_runs_total

- [x] **232.** Track reextraction_triggers_total

- [x] **233.** Track human_reviews_total

- [x] **234.** Track corrections_total

- [x] **235.** Track flags_generated_total

### Analytics Dashboard

- [x] **236.** Chart: Validation pass rate over time

- [x] **237.** Chart: Average confidence by domain

- [x] **238.** Chart: Common flag types

- [x] **239.** Chart: Human review turnaround

- [x] **240.** Chart: Correction rate

---

## Phase 18: Documentation (Points 241-250) ✅ COMPLETE

### Technical Documentation

- [x] **241.** Document architecture in ARCHITECTURE.md

- [x] **242.** Document each validator's logic

- [x] **243.** Document correction pipeline

- [x] **244.** Document configuration options

- [x] **245.** Document API endpoints

### User Documentation

- [x] **246.** Write user guide for review queue

- [x] **247.** Write guide for making corrections

- [x] **248.** Write guide for confidence scores

- [x] **249.** Write guide for understanding flags

- [x] **250.** Write FAQ for common scenarios

---

## Implementation Order Summary

| Phase | Points | Priority | Dependencies | Estimated Effort |
|-------|--------|----------|--------------|------------------|
| 1. Data Models | 1-15 | P0 | None | 1 day |
| 2. Evidence Verification | 16-28 | P0 | Phase 1 | 1 day |
| 3. Category Validators | 29-45 | P0 | Phase 1 | 2 days |
| 4. Domain Validators | 46-62 | P0 | Phase 3 | 2 days |
| 5. Cross-Domain | 63-80 | P1 | Phase 4 | 2 days |
| 6. Adversarial | 81-90 | P2 | Phase 4 | 1 day |
| 7. Pipeline Orchestrator | 91-100 | P0 | Phases 2-4 | 1 day |
| 8. Re-extraction Loop | 101-115 | P0 | Phase 7 | 1 day |
| 9. Correction Pipeline | 116-132 | P1 | Phase 1 | 2 days |
| 10. Review API | 133-145 | P1 | Phases 1, 9 | 1 day |
| 11. Review UI | 146-167 | P1 | Phase 10 | 3 days |
| 12. Display Integration | 168-180 | P2 | Phase 11 | 1 day |
| 13. Audit Trail | 181-195 | P1 | Phase 9 | 2 days |
| 14. Configuration | 196-205 | P1 | All | 0.5 days |
| 15. Testing | 206-220 | P1 | All | 3 days |
| 16. Performance | 221-230 | P2 | All | 1 day |
| 17. Monitoring | 231-240 | P3 | All | 1 day |
| 18. Documentation | 241-250 | P2 | All | 1 day |

**Total Estimated Effort: ~26 days**

---

## Suggested Implementation Sprints

### Sprint 1: Foundation (Points 1-28) ✅ COMPLETE
**Duration:** 2 days
**Deliverable:** Data models, storage, evidence verification working
**Milestone:** Can verify evidence exists in documents

- [x] Data models complete
- [x] Storage layer working
- [x] Evidence verifier tested

### Sprint 2: Core Validation (Points 29-62) ✅ COMPLETE
**Duration:** 4 days
**Deliverable:** Category and domain validators operational
**Milestone:** AI validation runs after extraction

- [x] Category checkpoints defined
- [x] Category validator working
- [x] Domain validator working
- [x] Validation flags generated

### Sprint 3: Automation Loop (Points 91-115) ✅ COMPLETE
**Duration:** 2 days
**Deliverable:** Pipeline orchestrator and re-extraction loop
**Milestone:** Automatic retry for incomplete extractions

- [x] Pipeline orchestrator working
- [x] Re-extraction triggers correctly
- [x] Escalation works

### Sprint 4: Human Loop (Points 116-167) ✅ COMPLETE
**Duration:** 5 days
**Deliverable:** Correction pipeline, review API, review UI
**Milestone:** Staff can review and correct facts

- [x] Correction pipeline with ripple effects
- [x] Review API endpoints
- [x] Review UI functional
- [x] Correction modal working

### Sprint 5: Polish (Points 63-90, 168-195) ✅ COMPLETE
**Duration:** 4 days
**Deliverable:** Cross-domain, adversarial, display integration, audit
**Milestone:** Full validation visible to users

- [x] Cross-domain consistency
- [x] Adversarial review
- [x] Validation status in domain pages
- [x] Audit trail complete

### Sprint 6: Hardening (Points 196-250) ✅ COMPLETE
**Duration:** 5 days
**Deliverable:** Config, testing, performance, monitoring, docs
**Milestone:** Production-ready system

- [x] All tests passing
- [x] Performance optimized
- [x] Monitoring in place
- [x] Documentation complete

---

## Progress Tracking

Use this section to track overall progress:

| Phase | Total Points | Completed | Progress |
|-------|-------------|-----------|----------|
| Phase 1 | 15 | 15 | 100% ✅ |
| Phase 2 | 13 | 13 | 100% ✅ |
| Phase 3 | 17 | 17 | 100% ✅ |
| Phase 4 | 17 | 17 | 100% ✅ |
| Phase 5 | 18 | 18 | 100% ✅ |
| Phase 6 | 10 | 10 | 100% ✅ |
| Phase 7 | 10 | 10 | 100% ✅ |
| Phase 8 | 15 | 15 | 100% ✅ |
| Phase 9 | 17 | 17 | 100% ✅ |
| Phase 10 | 13 | 13 | 100% ✅ |
| Phase 11 | 22 | 22 | 100% ✅ |
| Phase 12 | 13 | 13 | 100% ✅ |
| Phase 13 | 15 | 15 | 100% ✅ |
| Phase 14 | 10 | 10 | 100% ✅ |
| Phase 15 | 15 | 15 | 100% ✅ |
| Phase 16 | 10 | 10 | 100% ✅ |
| Phase 17 | 10 | 10 | 100% ✅ |
| Phase 18 | 10 | 10 | 100% ✅ |
| **TOTAL** | **250** | **250** | **100%** ✅ |

---

## Notes

- Update this document as implementation progresses
- Check off items as they are completed
- Add notes for any deviations from the plan
- Track blockers and dependencies

---

*Last Updated: January 27, 2025 - ALL SPRINTS COMPLETE (250/250 points = 100%)* 🎉
