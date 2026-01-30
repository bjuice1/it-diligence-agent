# PWC Knowledge Base Strategy

> **The Question Leadership Keeps Asking:** "Is the model trained on what we know?"
>
> **The Real Question:** How do we back AI analysis with PWC's institutional expertise?

---

## The Insight

We're not training a model. We're building a system that can be *informed by* PWC's accumulated knowledge - knowledge that lives in:

- Heads of industry specialists
- Lessons from past deals
- Vendor relationships and market intelligence
- Technical expertise across service lines

The AI is the engine. **PWC's knowledge is the fuel.**

---

## What This Could Look Like

### Layer 1: Application & Vendor Intelligence

**Source:** Market specialists, vendor relationship teams, past deal learnings

**Content:**
- What does this application actually do?
- What's typical pricing / implementation complexity?
- Common integration patterns and pitfalls
- Known issues, recent acquisitions, EOL timelines
- "When we see X, we usually also see Y"

**Example Entry:**
```
Duck Creek Policy (Insurance)
├── What it is: Policy administration platform
├── Typical cost: $400K-800K annually for mid-market
├── Implementation: 12-18 months typical, often underestimated
├── Watch for:
│   ├── Version 10→12 migration is painful, budget $500K-1M
│   ├── Usually paired with Guidewire for claims
│   └── Check if they're on legacy "Policy Admin System" vs modern "OnDemand"
├── Recent intel: Acquired by Apax Partners 2023, pricing pressure expected
└── PWC SME: [Name], Insurance Technology Practice
```

### Layer 2: Industry Playbooks

**Source:** Industry practice leaders, deal retrospectives

**Content:**
- What systems do we expect to see in this vertical?
- What's the typical IT landscape shape?
- Industry-specific risks and considerations
- Regulatory requirements affecting IT

**Example:**
```
Insurance (P&C) - IT Landscape Expectations
├── Core Systems:
│   ├── Policy Administration (Duck Creek, Guidewire, Majesco)
│   ├── Claims Management (Guidewire ClaimCenter, Duck Creek Claims)
│   ├── Billing (often same vendor as policy admin)
│   └── Actuarial (Willis Towers Watson, Moody's)
├── Typical Complexity: High - legacy modernization usually in progress
├── Regulatory: State filing systems, NAIC compliance
├── Common Findings:
│   ├── Mainframe still running core policy data
│   ├── Data warehouse is a mess
│   └── Agent portal is 10 years old
└── Questions We Always Ask:
    ├── What's the policy admin modernization roadmap?
    ├── How do they handle state-specific rating?
    └── What's the claims adjuster workflow?
```

### Layer 3: Deal Pattern Recognition

**Source:** Completed deal retrospectives

**Content:**
- What did we find on similar deals?
- What did we miss that we should have caught?
- How did estimates compare to actuals?
- What questions would we ask differently?

**Example:**
```
Pattern: Insurance Carve-Out from Larger Carrier
├── Seen on: Deal A (2023), Deal B (2024), Deal C (2024)
├── Common Issues:
│   ├── Shared policy admin instance - separation is expensive
│   ├── Actuarial models have parent company IP embedded
│   ├── Reinsurance treaties need renegotiation
│   └── Agent appointments don't transfer cleanly
├── Typical TSA Duration: 18-24 months (longer than expected)
├── Cost Variance: Estimates were 40% low on average
└── Lessons:
    ├── Get the data architecture diagram early
    ├── Actuarial separation is its own workstream
    └── Don't underestimate agent/broker system complexity
```

---

## How to Build This

### Phase A: Expert Interviews (Quick Win)

**Approach:** Structured conversations with PWC industry specialists

**Questions:**
1. What are the 10 core systems in a typical [industry] IT landscape?
2. What applications, when you see them, tell you something important?
3. What do clients always underestimate in this space?
4. What questions do you always ask in diligence?
5. What patterns have you seen across multiple deals?

**Output:** Structured notes → Knowledge base entries

**Effort:** 5-10 interviews per vertical, 1-2 hours each

### Phase B: Deal Retrospectives (Ongoing)

**Approach:** After each deal closes, capture learnings

**Template:**
- What did we find that was unexpected?
- What did we miss that we should have caught?
- How did our estimates compare to actuals?
- What would we do differently?
- Any new applications/vendors we learned about?

**Output:** Pattern library grows with each deal

### Phase C: Market Intelligence (Periodic)

**Approach:** Surveys or conversations with vendor specialists

**Content:**
- Vendor roadmaps and EOL timelines
- Pricing trends
- Common implementation issues
- Acquisition/consolidation news

**Output:** Vendor intelligence stays current

---

## How It Powers the Tool

### Near-Term: Context Injection

When analyzing an inventory item, inject relevant knowledge:

```
User's inventory shows: Duck Creek Policy v10

System injects context for reasoning:
"Duck Creek Policy is an insurance policy administration platform.
PWC Intel: Version 10 is legacy; migration to v12 typically costs
$500K-1M and takes 6-9 months. Check if this is on their roadmap.
Common pairing: Guidewire ClaimCenter for claims processing."
```

The AI doesn't need to "know" this - we tell it.

### Medium-Term: Chatbot / Q&A

When users ask questions about the deal:

> "What do we know about Duck Creek?"

System retrieves:
- Knowledge base entry for Duck Creek
- Any findings from current deal inventory
- Relevant patterns from past deals
- PWC SME contact for deeper questions

### Long-Term: Proactive Insights

System notices patterns:

> "This inventory shows Duck Creek v10 + Guidewire ClaimCenter +
> a mainframe. In 3 similar deals, we found hidden integration
> complexity. Consider flagging for deeper technical review."

---

## Validation & Maintenance

### Who Validates?

- **Application entries:** Relevant practice SMEs
- **Industry playbooks:** Industry practice leaders
- **Deal patterns:** Engagement teams who ran the deals

### How Often?

| Content Type | Refresh Cycle |
|--------------|---------------|
| Application intel | Annual + event-driven (acquisitions, EOL) |
| Industry playbooks | Annual review |
| Deal patterns | Continuous (after each deal) |
| Vendor pricing | Annual |

### Quality Control

- Entries have "last validated" date and validator name
- Stale entries (>18 months) flagged for review
- Contradictory information surfaced for resolution
- Usage tracking: which entries are actually being used?

---

## What This Is NOT

- **Not training a custom model** - We're curating knowledge that gets injected as context
- **Not a static database** - It evolves with every deal and market change
- **Not replacing SME judgment** - It's amplifying and scaling it
- **Not public information** - It's PWC's proprietary insights

---

## The Pitch to Leadership

> "We're not training the model on our knowledge - we're building a knowledge layer
> that the model draws from. Every deal we do, every expert conversation, every
> market insight gets captured and compounds. The AI stays current with public
> knowledge; we add what only PWC knows."

**Differentiator:** Competitors can use the same AI models. They can't replicate 20 years of deal experience distilled into structured intelligence.

---

## Starting Point

**Minimum Viable Knowledge Base:**

1. **5 industries:** Insurance, Healthcare, Manufacturing, Tech/SaaS, Financial Services
2. **Top 20 applications per industry:** The systems you see on every deal
3. **5 deal patterns per industry:** The recurring themes
4. **10 expert interviews:** 2 per industry to seed the content

**Effort:** ~40 hours of interviews + ~20 hours of structuring

**Output:** Enough to meaningfully enhance analysis on the next deal

---

## Questions to Explore

1. **Incentives:** How do we get busy SMEs to contribute? (Credit? Visibility? Mandate?)
2. **Freshness:** Who owns keeping this current? (Central team? Distributed?)
3. **Access:** Who can query this? (Deal teams only? Broader practice?)
4. **Sensitivity:** Any content too sensitive to store? (Client-specific learnings?)
5. **Integration:** How does this connect to existing PWC knowledge systems?

---

## Next Steps

1. **Socialize concept** with practice leadership
2. **Pilot with one industry** (Insurance seems natural given current work)
3. **Run 5 expert interviews** to test the capture process
4. **Build simple retrieval** into current tool as proof of concept
5. **Measure impact** on deal quality/efficiency

---

*Document created: January 2026*
*Status: Concept for discussion*
*Owner: [TBD]*
