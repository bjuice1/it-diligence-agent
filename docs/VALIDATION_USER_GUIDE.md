# Validation System User Guide

## Introduction

The Validation System helps ensure the accuracy and completeness of extracted IT due diligence data. It automatically validates facts against source documents and flags items that need human review.

## Getting Started

### Understanding Confidence Scores

Every extracted fact has a confidence score from 0% to 100%:

| Score | Meaning | Action Needed |
|-------|---------|---------------|
| 80-100% | High confidence | Usually accurate, verify edge cases |
| 60-79% | Medium confidence | Review recommended |
| 40-59% | Low confidence | Likely needs correction |
| 0-39% | Critical | Probably incorrect, review required |

### Understanding Validation Status

Facts progress through these statuses:

- **Extracted**: Just pulled from document
- **AI Validated**: System has reviewed
- **Human Pending**: Flagged for your review
- **Confirmed**: You verified it's correct
- **Corrected**: You fixed an error
- **Rejected**: You marked it as invalid

## Using the Review Queue

### Accessing the Queue

Navigate to **Validation → Review Queue** from the main menu.

### Queue Features

1. **Filters**
   - By domain (Organization, Infrastructure, etc.)
   - By severity (Critical, Error, Warning, Info)
   - By category (compute, storage, etc.)

2. **Sorting**
   - Critical issues first (default)
   - By domain
   - By date added

3. **Pagination**
   - 20 items per page by default
   - Navigate with Previous/Next buttons

### Review Card Information

Each review card shows:
- **Severity Badge**: Color-coded (red=critical, orange=error, yellow=warning)
- **Domain/Category**: Where this fact belongs
- **Item Name**: What was extracted
- **Flag Message**: Why it needs review
- **Evidence**: The quote from the source document
- **Match Score**: How well the quote matched (percentage)

## Making Corrections

### When to Confirm

Click **Confirm** when:
- The extracted value is correct
- The evidence accurately supports the value
- No issues with the data

### When to Correct

Click **Correct** when:
- The value has a minor error (typo, wrong number)
- Additional details are needed
- The category is wrong

**Correction Process:**
1. Click the Correct button
2. The correction modal opens
3. See the original value(s)
4. Enter the corrected value(s)
5. Provide a reason (required)
6. Optionally add new evidence
7. Click Submit Correction

### Understanding Ripple Effects

When you correct certain fields (like headcount or cost), the system automatically recalculates related values.

**Example:**
- You correct a team's headcount from 10 to 15
- The system recalculates:
  - Total IT headcount
  - Cost per person for that team
  - Headcount ratios

The correction summary shows what will change before you confirm.

### When to Reject

Click **Reject** when:
- The extracted item is completely wrong
- It's a duplicate of another entry
- It doesn't belong in the analysis

Provide a reason so the team understands why.

## Understanding Flags

### Flag Severities

| Severity | Color | Meaning |
|----------|-------|---------|
| Critical | Red | Almost certainly wrong - evidence not found |
| Error | Orange | Likely wrong - major inconsistency |
| Warning | Yellow | Might be wrong - unusual value |
| Info | Blue | FYI - noteworthy but probably fine |

### Common Flag Types

**Evidence Flags:**
- "Evidence not found in source document" (Critical)
- "Evidence partially matches" (Warning)

**Completeness Flags:**
- "Category has fewer items than expected" (Warning)
- "Missing required field" (Error)

**Consistency Flags:**
- "Headcount doesn't match stated total" (Error)
- "Cost per person outside expected range" (Warning)

**Cross-Domain Flags:**
- "Vendor mentioned in org not found in infrastructure" (Warning)
- "Security team exists but no security tools documented" (Warning)

## Tips for Efficient Review

### Priority Order

1. Review **Critical** flags first - these are most likely errors
2. Then **Error** flags - high probability of issues
3. **Warnings** can often be batched
4. **Info** flags usually just need a quick look

### Batch Similar Items

The queue allows filtering, so you can:
1. Filter to a specific domain
2. Review all items in that domain
3. Move to the next domain

This keeps context fresh and speeds up review.

### Use the Notes Field

When confirming or correcting, add notes to explain:
- Why you made a decision
- Additional context for the team
- Questions for follow-up

These notes are visible in the audit trail.

## Understanding the Dashboard

### Validation Dashboard Overview

The dashboard shows:
- **Overall Confidence**: Aggregate confidence across all domains
- **Domain Status**: Per-domain confidence and flag counts
- **Review Progress**: How many items reviewed vs. pending

### Domain Status Indicators

| Icon | Status | Meaning |
|------|--------|---------|
| ✓ Green | Good | High confidence, few/no flags |
| ⚠ Yellow | Warning | Medium confidence or unresolved warnings |
| ✗ Red | Error | Low confidence or critical flags |

## Frequently Asked Questions

### Why was this flagged?

Each flag includes a message explaining the issue. Common reasons:
- Evidence quote not found in document
- Value seems inconsistent with other data
- Missing expected information

### What if I'm not sure about a correction?

Use the **Skip** button to move to the next item. Skipped items remain in the queue for another reviewer or for you to return to later.

### Can I undo a confirmation or correction?

Corrections are logged in the audit trail but cannot be directly undone. If you need to change a confirmed fact, you can submit a new correction.

### What happens after I review everything?

Once all flagged items are reviewed, the domain status will update to show the new confidence level based on confirmations and corrections.

### Who can see my reviews?

Reviews are logged with your name in the audit trail. Team members can see who reviewed what and when.

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `C` | Confirm current item |
| `E` | Open correction modal |
| `R` | Reject current item |
| `S` | Skip to next item |
| `←` | Previous page |
| `→` | Next page |
| `Esc` | Close modal |

## Getting Help

If you encounter issues:
1. Check the flag message for specific guidance
2. Review the evidence quote carefully
3. Compare with the source document
4. Ask the team if unclear

For technical issues, contact your system administrator.
