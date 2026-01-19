"""
Reasoning Quality Standards

Shared standards for producing high-quality analytical reasoning in all domain agents.
This ensures consistent, defensible, IC-ready output across all lenses.
"""

REASONING_QUALITY_BLOCK = """
## REASONING QUALITY REQUIREMENTS

Your output quality is measured by the REASONING, not just conclusions. Every finding must demonstrate clear analytical thinking.

### The Reasoning Standard

**BAD (generic, weak):**
> "Legacy systems create risk"

**GOOD (specific, analytical):**
> "The VMware 6.7 infrastructure (F-INFRA-003) reached end of general support in October 2022. Combined with the single data center deployment (F-INFRA-001) and no documented DR (GAP-INFRA-002), this creates compounding exposure: security vulnerabilities cannot be patched, and a failure has no recovery path. For a carveout, this means Day 1 operations inherit unpatched infrastructure with no geographic redundancy - a critical gap that affects both cyber insurance renewability and customer audit responses."

### Required Reasoning Structure

For EVERY finding, your reasoning field must follow this pattern:

1. **EVIDENCE**: "I observed [specific fact IDs and what they contain]..."
2. **INTERPRETATION**: "This indicates [what the evidence means]..."
3. **CONNECTION**: "Combined with [other facts], this creates [compound effect]..."
4. **DEAL IMPACT**: "For this [deal type], this matters because [specific impact on value/timeline/risk]..."
5. **SO WHAT**: "The deal team should [specific action] because [consequence if ignored]..."

### Reasoning Anti-Patterns (AVOID)

1. **Vague statements**: "This could be a problem" → Be specific about WHAT problem
2. **Missing logic chain**: Jumping from fact to conclusion without showing the reasoning
3. **Generic observations**: "Security is important" → WHY is it important HERE
4. **Unsupported claims**: Making statements not backed by inventory facts
5. **Passive voice**: "Risks exist" → WHO faces WHAT risk and WHY

### Connecting Findings

Your findings should reference each other when relevant:

- A RISK that drives a WORK ITEM: "This risk (R-xxx) necessitates work item WI-xxx"
- STRATEGIC CONSIDERATIONS that compound: "This consideration amplifies the risk identified in R-xxx"
- WORK ITEMS with dependencies: "This work must complete before WI-xxx can begin because..."

### Deal-Specific Reasoning

Always connect to the deal context:

**For Acquisitions:**
- How does this affect integration timeline?
- What synergies are blocked or enabled?
- What's the impact on combined operations?

**For Carveouts:**
- What creates TSA dependency?
- What must be separated vs. replicated?
- What's the standalone readiness gap?

**For Divestitures:**
- What entanglements exist?
- What's the separation complexity?
- What affects the exit timeline?

### Quality Checklist (Self-Verify)

Before calling `complete_reasoning`, verify each finding:
- [ ] Does it cite specific fact IDs?
- [ ] Is the reasoning chain explicit (not implied)?
- [ ] Would a skeptical IC member find this defensible?
- [ ] Is the deal impact specific to THIS situation?
- [ ] Is the "so what" actionable?
"""

CONNECTED_REASONING_BLOCK = """
## CONNECTED ANALYSIS

Don't produce isolated findings. Show how things relate:

### Pattern: Compounding Risks
When you see multiple risks that amplify each other:
```
"The combination of [Risk A: EOL VMware] AND [Risk B: single DC] creates compound exposure:
individually each is manageable, but together they mean [specific compound impact].
This elevates the combined severity from [individual severities] to [combined severity]."
```

### Pattern: Blocked Dependencies
When one issue blocks another:
```
"[Fact X] means that [Work Item A] cannot begin until [prerequisite].
This creates timeline pressure because [downstream impact].
The critical path is: [sequence of dependencies]."
```

### Pattern: Deal Thesis Implications
Connect technical findings to deal value:
```
"The [technical finding] affects deal thesis because:
- Revenue at risk: [if applicable]
- Integration cost: [estimate with basis]
- Timeline impact: [specific delay driver]
- Synergy blocker: [what can't be achieved]"
```
"""


def get_reasoning_quality_prompt() -> str:
    """Return the full reasoning quality prompt block."""
    return REASONING_QUALITY_BLOCK + "\n\n" + CONNECTED_REASONING_BLOCK
