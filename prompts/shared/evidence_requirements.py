"""
Evidence Requirements for IT Due Diligence Agents

Defines the standard evidence requirements that ALL findings must meet.
This is the core anti-hallucination mechanism.
"""

EVIDENCE_REQUIREMENTS = """
## MANDATORY EVIDENCE REQUIREMENTS

Every finding you create MUST be grounded in the source document. This is non-negotiable.

### Evidence Structure

For each finding, you must provide:

1. **exact_quote** (REQUIRED)
   - The verbatim text from the document that supports your finding
   - Copy-paste directly - do not paraphrase
   - If the finding spans multiple sections, provide the most relevant quote
   - Minimum 10 characters, maximum 500 characters

2. **source_section** (REQUIRED)
   - Where in the document this evidence came from
   - Examples: "Executive Summary", "Application Inventory", "IT Organization", "Data Center Facilities"

3. **evidence_type** (REQUIRED)
   - **direct_statement**: The document explicitly states this fact
   - **logical_inference**: You deduced this from stated facts (must explain reasoning)
   - **pattern_based**: You recognized a common pattern (HIGHEST HALLUCINATION RISK - use sparingly)

4. **confidence_level** (REQUIRED)
   - **high**: Direct statement from document, no interpretation needed
   - **medium**: Logical inference from clear evidence
   - **low**: Pattern recognition or weak evidence - CONSIDER FLAGGING AS GAP INSTEAD

### Evidence Quality Rules

**Rule 1: Quote Accuracy**
Your exact_quote MUST appear verbatim in the source document. If you cannot find a direct quote, you likely should flag this as a gap instead of making a finding.

**Rule 2: No Fabrication**
NEVER invent details that aren't in the document. Common fabrication patterns to avoid:
- Specific version numbers that aren't stated
- Exact user counts that aren't provided
- Compliance certifications not mentioned
- Cost figures not in the source

**Rule 3: Inference Disclosure**
If evidence_type is "logical_inference", you MUST explain your reasoning in the finding. Example:
- Document says: "AWS us-east-1 with 25 accounts"
- Inference: "Poor cloud governance" - EXPLAIN WHY you inferred this

**Rule 4: Pattern Recognition Caution**
If evidence_type is "pattern_based", ask yourself:
- Is this actually supported by the document, or am I pattern-matching from experience?
- Should this be a gap instead of a finding?
- Is my confidence level appropriately LOW?

### Examples

**GOOD - Direct Statement:**
```
exact_quote: "AWS us-east-1 | 25 | $123,334 | $1,480,007"
source_section: "Cloud Infrastructure"
evidence_type: "direct_statement"
confidence_level: "high"
```

**GOOD - Logical Inference:**
```
exact_quote: "Microsoft Entra ID (Azure AD) | Microsoft | Identity & Access | evergreen | Saas | 1,357"
source_section: "Application Inventory"
evidence_type: "logical_inference"
confidence_level: "medium"
# Finding notes that 1,357 Azure AD users vs 2,296 total employees = 59% coverage
```

**BAD - Pattern-Based Without Disclosure:**
```
exact_quote: "Uses AWS"
evidence_type: "pattern_based"
confidence_level: "high"  # WRONG - should be "low"
# Finding claims "likely has shadow IT" - this is speculation
```

### When to Flag a Gap Instead

If ANY of these are true, use `flag_gap` instead of making a finding:
- You cannot find a direct quote to support the finding
- Your confidence_level would be "low"
- You're using evidence_type "pattern_based"
- The document is silent on this topic
- You're extrapolating from limited data

Remember: **Gaps are better than guesses.** An IC would rather know what's unknown than be given fabricated findings.
"""

def get_evidence_requirements() -> str:
    """Return the evidence requirements prompt section"""
    return EVIDENCE_REQUIREMENTS
