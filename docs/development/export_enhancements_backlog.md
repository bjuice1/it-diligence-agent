# Export Enhancements Backlog

*Created: 2026-01-28*
*Status: Future Enhancement*

## Overview

This document captures enhancement ideas for the inventory export feature that go beyond the current implementation. These would leverage AI more deeply to generate richer insights.

---

## Enhancement Categories

### 1. AI-Generated Descriptions

**Current State:** Basic descriptions extracted from evidence quotes.

**Enhancement Ideas:**

| Domain | Enhancement | How It Would Work |
|--------|-------------|-------------------|
| Applications | Plain English app descriptions | AI summarizes what the app does based on facts + findings |
| Infrastructure | Asset purpose descriptions | AI explains what each server/system does in the environment |
| Organization | Role descriptions | AI generates job description summaries for each role |
| Security | Control explanations | AI explains what each security control protects against |

**Implementation:**
- Add a "description generation" pass after inventory building
- Use Haiku to generate 1-2 sentence descriptions for each item
- Cache descriptions to avoid regenerating on each export

---

### 2. Age & Technical Debt Assessment

**Current State:** Basic "Legacy" flags from findings.

**Enhancement Ideas:**

| Assessment Type | Logic |
|----------------|-------|
| Age Assessment | Parse version numbers, compare to known EOL dates |
| Tech Debt Score | 1-10 score based on age, findings, integration complexity |
| Modernization Priority | Rank by business criticality × tech debt score |

**Data Sources Needed:**
- EOL date database for common software (Oracle, SAP, Windows Server, etc.)
- Version history for major platforms
- Industry benchmark data for "typical" refresh cycles

---

### 3. Migration Complexity Scoring

**Current State:** Simple High/Medium/Low based on criticality.

**Enhancement Ideas:**

| Factor | Weight | How to Calculate |
|--------|--------|------------------|
| Integration count | 30% | Count connected systems from facts |
| Data volume | 20% | Parse from storage/database facts |
| Customization level | 20% | Look for "custom", "modified", "configured" in evidence |
| User count | 15% | Parse user counts |
| Business criticality | 15% | From criticality field |

**Output:** Numeric score 1-100 with breakdown.

---

### 4. Key Person Risk Analysis

**Current State:** Flags based on `is_key_person` field.

**Enhancement Ideas:**

| Risk Factor | How to Assess |
|-------------|---------------|
| Single point of failure | Only person with skill X |
| Institutional knowledge | Tenure > 5 years + critical system owner |
| Flight risk | Below market salary + competitive skills |
| Succession readiness | Is there a backup identified? |

**Output:** Risk matrix with mitigation recommendations.

---

### 5. Cross-Domain Insights

**Current State:** Each domain exported independently.

**Enhancement Ideas:**

| Insight Type | Domains Combined | Example Output |
|--------------|------------------|----------------|
| App-to-Infra mapping | Applications + Infrastructure | "SAP runs on servers X, Y, Z" |
| Staff-to-System coverage | Organization + All technical | "Infrastructure team of 2 supports 50 servers" |
| Security gap impact | Cybersecurity + Applications | "MFA gap affects 15 applications" |
| Cost-to-value analysis | Organization + Applications | "App support cost per application" |

---

### 6. Trend Analysis (Multi-Run)

**Current State:** Single point-in-time export.

**Enhancement Ideas:**

If we have multiple analysis runs:
- Show changes since last run
- Highlight new systems/staff
- Flag removed items
- Track remediation progress

---

## Implementation Priority

| Enhancement | Effort | Value | Priority |
|-------------|--------|-------|----------|
| AI Descriptions | Medium | High | P1 |
| Age/EOL Assessment | Medium | High | P1 |
| Migration Scoring | High | Medium | P2 |
| Key Person Deep Dive | Medium | High | P1 |
| Cross-Domain Insights | High | High | P2 |
| Trend Analysis | High | Medium | P3 |

---

## Technical Considerations

### API Usage
- Each AI-generated description = 1 API call
- For 100 items × 5 domains = 500 calls
- Cost: ~$0.50 with Haiku
- Consider: batch processing, caching

### Performance
- Generate on-demand vs pre-generate at analysis time
- Cache in facts JSON as `ai_description` field
- Invalidate cache when facts change

### Accuracy
- AI descriptions need human review option
- Add "Edit" capability in UI
- Track edits for training data

---

## Related Documents

- [115-Point Cleanup Plan](./115_point_cleanup_plan.md)
- [Phase C Implementation](./phase_c_exports.md)
