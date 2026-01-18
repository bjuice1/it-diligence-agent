"""
Confidence Calibration for IT Due Diligence Agents

Guidelines for accurately assessing and reporting confidence levels.
"""

CONFIDENCE_CALIBRATION = """
## CONFIDENCE CALIBRATION

Accurate confidence assessment is critical. Over-confident findings are dangerous; under-confident findings waste time. Use this calibration guide.

### Confidence Level Definitions

| Level | Definition | Evidence Required | When to Use |
|-------|------------|-------------------|-------------|
| **high** | Certain - document explicitly states this | Direct quote, no interpretation | Facts, numbers, explicit statements |
| **medium** | Probable - logically deduced from evidence | Clear inference chain, explained | Calculations, deductions, combinations |
| **low** | Possible - weak evidence or pattern-based | Should consider flagging as gap | Pattern recognition, sparse evidence |

### Calibration Examples

**HIGH Confidence (direct statement):**
- "AWS us-east-1 with 25 accounts" → High confidence on cloud provider, region, account count
- "Total IT Headcount | 141" → High confidence on exact number
- "CrowdStrike Falcon | CrowdStrike | Security" → High confidence they have CrowdStrike

**MEDIUM Confidence (logical inference):**
- Document shows 1,357 Azure AD users, 2,296 total employees → Medium confidence on "59% identity coverage"
- Document lists both Splunk ES and Elastic SIEM → Medium confidence on "SIEM tool inconsistency"
- AWS only in us-east-1 → Medium confidence on "single region concentration risk"

**LOW Confidence (pattern-based, consider flagging gap):**
- 25 AWS accounts → Low confidence on "poor governance" (pattern, not stated)
- Insurance company → Low confidence on "likely compliance requirements" (domain knowledge, not evidence)
- No security certifications listed → Low confidence on "compliance gap" (absence of evidence)

### Confidence Distribution Checks

After analyzing a document, your confidence distribution should look realistic:

**Healthy Distribution:**
- High: 40-60% of findings
- Medium: 30-40% of findings
- Low: 10-20% of findings (and each should justify why not flagged as gap)

**Suspicious Distribution:**
- High: >80% of findings → You're likely over-confident
- Low: >30% of findings → Consider converting many to gaps
- All High: Almost certainly over-confident

### Adjusting Confidence

**Downgrade confidence when:**
- You used words like "likely", "probably", "typically" in your reasoning
- The quote is short or could be interpreted multiple ways
- You combined information from multiple places
- Your domain expertise influenced the finding
- The document is ambiguous on this point

**Upgrade confidence when:**
- Multiple independent quotes support the same finding
- The document explicitly states the finding
- Numbers and specifics are provided, not just general statements

### Special Cases

**Numeric Findings:**
- Exact numbers from document → High
- Calculated from document numbers → Medium (show your math)
- Estimated ranges → Medium to Low (disclose estimation method)

**Risk Findings:**
- Risk based on explicit statement (e.g., "DR never tested") → High
- Risk based on absence (e.g., "No SIEM mentioned") → Medium, explain inference
- Risk based on pattern (e.g., "This typically means...") → Low or flag as gap

**Strategic Findings:**
- Based on documented buyer/target comparison → High to Medium
- Based on industry knowledge → Low or flag as gap
- Based on assumption about buyer → Flag as gap (ask for buyer context)

### The Humility Check

Before finalizing confidence, ask:
1. "Would I bet money on this at this confidence level?"
2. "If wrong, how bad would the consequences be?"
3. "Could a reasonable person interpret the evidence differently?"

If any answer gives you pause, consider downgrading confidence or flagging as gap.
"""

def get_confidence_calibration() -> str:
    """Return the confidence calibration prompt section"""
    return CONFIDENCE_CALIBRATION
