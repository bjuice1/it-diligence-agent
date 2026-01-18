# Contribution Guide
## How to Improve the IT Due Diligence Agent

---

## Why Your Input Matters

Every deal teaches us something. The system improves when team members feed back what they learn. You don't need to be technical - most improvements are simple text edits.

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│   Your deal experience  →  System improvement  →  Better        │
│                                                     results     │
│                                                     for all     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Four Ways to Contribute

| Contribution | Effort | When to Do It |
|--------------|--------|---------------|
| Add checklist item | 5 min | System didn't check for something important |
| Add risk pattern | 10 min | System missed a known risk type |
| Calibrate cost estimate | 10 min | Estimate was significantly off |
| Add industry guidance | 15-30 min | Industry-specific nuance was missed |

---

## 1. Adding a Checklist Item

**When:** The system didn't flag that something was missing, but it should have.

**Example:** "We needed SD-WAN information but the system didn't ask for it."

### Steps

1. Open `tools_v2/coverage.py`

2. Find the right domain and category:
```python
COVERAGE_CHECKLISTS = {
    "infrastructure": { ... },
    "network": {
        "wan": {
            "primary_isp": {"importance": "critical", ...},
            "redundancy": {"importance": "critical", ...},
            # ADD NEW ITEM HERE
        },
        ...
    },
    ...
}
```

3. Add your item:
```python
"wan": {
    "primary_isp": {"importance": "critical", "description": "Primary ISP and bandwidth"},
    "redundancy": {"importance": "critical", "description": "WAN redundancy"},
    "sd_wan": {"importance": "important", "description": "SD-WAN deployment status"},  # NEW
},
```

4. Choose importance level:
   - `critical` - Must have for any deal, missing = VDR request
   - `important` - Should have, missing = lower coverage score
   - `nice_to_have` - Good to have if available

5. Save the file. Done.

**Impact:** All future analyses will check for this item.

---

## 2. Adding a Risk Pattern

**When:** The system found the facts but didn't identify a risk that was obvious to you.

**Example:** "It saw VMware 6.7 but didn't flag the Broadcom licensing implications."

### Steps

1. Open the relevant reasoning prompt in `prompts/`:
   - `v2_infrastructure_reasoning_prompt.py`
   - `v2_network_reasoning_prompt.py`
   - `v2_cybersecurity_reasoning_prompt.py`
   - `v2_applications_reasoning_prompt.py`
   - `v2_identity_access_reasoning_prompt.py`
   - `v2_organization_reasoning_prompt.py`

2. Find the risk patterns section (usually marked with comments)

3. Add your pattern:
```python
"""
## Known Risk Patterns

When analyzing infrastructure, evaluate these specific risks:

- VMware versions: 6.x is EOL, assess upgrade path and timeline
- VMware licensing: Post-Broadcom acquisition, subscription model changes
  may significantly impact costs. Flag for budget discussion.          # NEW
- Backup location: No offsite backup = DR risk
- Cloud concentration: Single region = availability risk
...
"""
```

4. Save the file. Done.

**Impact:** The AI will now look for this pattern in all future analyses.

---

## 3. Calibrating Cost Estimates

**When:** A cost estimate was significantly off from what the project actually cost.

**Example:** "System said VMware upgrade would be $100K-$500K but it was actually $600K."

### Steps

1. Open the relevant reasoning prompt in `prompts/`

2. Find the cost estimation section

3. Update the guidance:
```python
"""
## Cost Estimation Guidelines

Use these ranges based on typical projects:

VMware Upgrades:
- Small environment (<100 VMs): $50K - $150K
- Medium environment (100-300 VMs): $150K - $400K
- Large environment (300+ VMs): $400K - $800K    # UPDATED based on deal feedback

Include considerations for:
- License costs (especially post-Broadcom)       # NEW
- Professional services
- Downtime/migration windows
...
"""
```

4. Save the file. Done.

**Impact:** Future cost estimates will be more accurate.

---

## 4. Adding Industry-Specific Guidance

**When:** The system missed something that's important for a specific industry.

**Example:** "For healthcare targets, HIPAA BAA status should always be critical."

### Steps

1. Open the relevant reasoning prompt

2. Add an industry section:
```python
"""
## Industry-Specific Considerations

### Healthcare
When target handles PHI or healthcare data:
- HIPAA BAA status with all cloud providers → CRITICAL
- Data residency constraints → CRITICAL (HIPAA)
- PHI access logging and audit trails → HIGH
- Breach notification procedures → CRITICAL
- Elevate all data-related risks by one severity level

### Financial Services
When target handles financial data:
- SOC2 Type II certification → CRITICAL
- PCI-DSS compliance (if payment processing) → CRITICAL
- Data encryption at rest and in transit → HIGH
...
"""
```

3. Save the file. Done.

**Impact:** Analyses for that industry will be more accurate.

---

## Where Files Live

```
it-diligence-agent/
│
├── tools_v2/
│   └── coverage.py              ← Checklist items go here
│
├── prompts/
│   ├── v2_infrastructure_discovery_prompt.py
│   ├── v2_infrastructure_reasoning_prompt.py   ← Risk patterns, costs
│   ├── v2_network_discovery_prompt.py
│   ├── v2_network_reasoning_prompt.py
│   ├── v2_cybersecurity_discovery_prompt.py
│   ├── v2_cybersecurity_reasoning_prompt.py
│   ├── v2_applications_discovery_prompt.py
│   ├── v2_applications_reasoning_prompt.py
│   ├── v2_identity_access_discovery_prompt.py
│   ├── v2_identity_access_reasoning_prompt.py
│   ├── v2_organization_discovery_prompt.py
│   └── v2_organization_reasoning_prompt.py
│
└── tools_v2/
    └── vdr_generator.py         ← Suggested documents per category
```

---

## Quick Reference: What Goes Where

| I want to... | Edit this file |
|--------------|----------------|
| Add something to check for | `tools_v2/coverage.py` |
| Add a risk the AI should catch | `prompts/v2_*_reasoning_prompt.py` |
| Change what facts are extracted | `prompts/v2_*_discovery_prompt.py` |
| Update cost estimate ranges | `prompts/v2_*_reasoning_prompt.py` |
| Add industry-specific rules | `prompts/v2_*_reasoning_prompt.py` |
| Change VDR suggested documents | `tools_v2/vdr_generator.py` |

---

## Best Practices

### Be Specific
```
# Good
"VMware 6.x is EOL as of October 2022, assess upgrade timeline"

# Too vague
"Check for old software"
```

### Include Context
```
# Good
"For manufacturing targets, OT/IT network segmentation is CRITICAL
 due to operational safety implications"

# Missing context
"Network segmentation is important"
```

### Use Consistent Severity Language
- CRITICAL - Must address before close or represents deal risk
- HIGH - Should address in first 100 days
- MEDIUM - Should address but not urgent
- LOW - Nice to fix, no significant risk

### Test Your Changes
After making changes, run an analysis to see if it behaves as expected:
```bash
python main_v2.py --domain infrastructure input/
```

---

## Reporting Issues

If you find something that needs fixing but aren't sure how:

1. **What happened:** Describe what the system did
2. **What should have happened:** What you expected
3. **Which deal:** So we can look at the documents if needed
4. **Severity:** How much did it matter?

Share with the team and we'll figure out the fix together.

---

## Examples of Good Contributions

### Checklist Addition (from real deal)
> "Target had extensive Kubernetes deployment but system didn't flag missing container security info."

Added to coverage.py:
```python
"compute": {
    ...
    "container_security": {
        "importance": "important",
        "description": "Container/Kubernetes security controls"
    },
}
```

### Risk Pattern (from real deal)
> "System saw they were on AWS but didn't flag single-AZ deployment as a risk."

Added to infrastructure reasoning prompt:
```
"When AWS is identified, check for multi-AZ deployment.
 Single-AZ = availability risk, flag as MEDIUM severity
 with recommendation for multi-AZ architecture review."
```

### Cost Calibration (from real deal)
> "SIEM implementation estimate of $50K-$100K was way low. Actual was $180K."

Updated reasoning prompt:
```
"SIEM Implementation:
 - Cloud SIEM (Splunk Cloud, Sentinel): $100K - $200K first year
 - On-prem SIEM: $150K - $300K including hardware
 - Note: Ongoing costs often exceed initial implementation"
```

---

## Summary

1. **You don't need to be technical** - Most changes are text edits
2. **Every deal is a learning opportunity** - Feed back what you find
3. **Small changes compound** - 5-minute edits benefit all future deals
4. **Test if you can** - Run an analysis to verify your changes work

---

*Questions? Ask the team. Your input makes this tool better for everyone.*
