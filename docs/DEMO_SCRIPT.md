# Demo Script
## Walking Through the IT Due Diligence Agent

---

## Before the Demo

### Prep Checklist
- [ ] Have sample documents ready in `input/` folder
- [ ] Run the analysis beforehand so you have outputs to show
- [ ] Have the output files open in separate tabs/windows
- [ ] Know the key findings from the sample run

### What You'll Need Open
1. Terminal (to show the command)
2. Executive summary markdown
3. Coverage JSON or a summary view
4. VDR requests markdown
5. One findings example with evidence chain

---

## Demo Flow (15-20 minutes)

### Opening (2 minutes)

**Say:**
> "I want to show you a tool we've been building to help with IT due diligence. It doesn't replace the team - it handles the extraction so we can focus on judgment and strategy."

**Show:** The input folder with sample documents
> "We start with IT documents from the VDR - whatever the target has provided."

---

### Running the Analysis (2 minutes)

**Show:** Terminal command
```bash
python main_v2.py input/
```

**Say:**
> "One command kicks off the analysis. It runs through five phases."

**Show:** Progress output (or describe if pre-run)
> "Discovery extracts facts from documents. Reasoning analyzes those facts for risks. Then it scores coverage, synthesizes across domains, and generates follow-up questions."

> "This takes about 15 minutes for a typical document set, costs about $10-15 in API fees."

---

### Executive Summary (3 minutes)

**Show:** `executive_summary_*.md`

**Say:**
> "First thing to look at is the executive summary. This gives you the big picture."

**Walk through:**
- Coverage grade
- Key risks identified
- Top recommendations

> "This is a starting point - the team reviews and refines. But it gets you 80% of the way there in 15 minutes instead of a day."

---

### Coverage Score (2 minutes)

**Show:** Coverage section or `coverage_*.json`

**Say:**
> "The coverage grade tells you how complete the documentation is against our checklist. We have 101 items across six domains."

**Point out:**
- Overall grade
- Which domains have gaps
- Missing critical items

> "A 'C' grade doesn't mean the target is bad - it means we need more information. Which leads to..."

---

### VDR Requests (3 minutes)

**Show:** `vdr_requests_*.md`

**Say:**
> "The system automatically generates follow-up questions based on gaps. Prioritized by importance."

**Walk through:**
- Critical priority items
- Suggested documents for each
- How it maps to coverage gaps

> "Instead of spending an hour drafting VDR requests, you review these in 10 minutes, add deal-specific questions, and send."

---

### Evidence Chains (3 minutes)

**Show:** A specific risk in `findings_*.json`

**Say:**
> "Every finding traces back to source documents. Let me show you how."

**Walk through:**
```json
{
  "title": "EOL VMware Version",
  "severity": "high",
  "based_on_facts": ["F-INFRA-003"],
  "reasoning": "VMware 6.7 reached EOL..."
}
```

> "See 'based_on_facts'? That points to fact F-INFRA-003."

**Show:** The corresponding fact
```json
{
  "fact_id": "F-INFRA-003",
  "item": "VMware vSphere",
  "evidence": {
    "exact_quote": "VMware vSphere 6.7 hosting 340 production VMs"
  }
}
```

> "There's the exact quote from the document. Every claim is traceable. If someone in IC asks 'where did you get that?' - you can show them."

---

### Cost Estimates (2 minutes)

**Show:** Work items with cost estimates

**Say:**
> "Work items include cost estimates grouped by phase - Day 1, Day 100, Post-100."

**Point out:**
- Cost ranges (not precise figures)
- Phase assignments
- Owner assignments (buyer vs target)

> "These are starting points. The team calibrates based on deal specifics. But it gives you a structured foundation for the integration budget."

---

### How It Improves (2 minutes)

**Say:**
> "The system gets better over time. When you catch something it missed, we add it to the checklist or prompts."

**Show:** (optional) The coverage.py or a prompt file

> "Adding a new checklist item takes 5 minutes. Adding a risk pattern takes 10. Every deal teaches us something, and that knowledge sticks."

---

### Closing (1 minute)

**Say:**
> "To summarize: this handles the extraction and structuring - reading documents, pulling facts, identifying gaps, generating questions. The team still reviews everything and adds judgment."

> "It's not about replacing anyone. It's about getting the grunt work done faster so you can focus on what matters - the analysis and strategy."

**Ask:**
> "What questions do you have?"

---

## Common Questions & Answers

### "How accurate is it?"

> "Fact extraction is reliable - it pulls direct quotes. Analysis needs human review. Severity ratings and cost estimates are starting points that the team calibrates. It's a first pass, not a final product."

### "What if it misses something?"

> "It will sometimes. That's why review is required. When you catch something, we improve the system. The checklist has 101 items now - it started with fewer. Every deal makes it better."

### "How much does it cost?"

> "$8-25 per analysis depending on document size. Processing time is 8-30 minutes."

### "Does it work for any industry?"

> "Works for general IT diligence. We're adding industry-specific guidance - healthcare, manufacturing, financial services. The prompts are customizable."

### "What about confidential documents?"

> "Documents are sent to Anthropic's API for processing. The API doesn't store or train on the data, but it does leave your machine. Review your confidentiality requirements."

### "Can I try it on a real deal?"

> "Yes. Download the IT docs, drop them in the input folder, run the command. Review the outputs and let us know what you think - your feedback improves the system."

---

## Tips for a Good Demo

### Do
- Focus on the practical outputs (summary, VDR requests)
- Show the evidence chain - it's the differentiator
- Acknowledge limitations ("needs human review")
- Emphasize "tool to help, not replace"

### Don't
- Promise specific time savings percentages
- Claim it's fully automated end-to-end
- Skip the human review step in your narrative
- Oversell - undersell and let them be pleasantly surprised

### If Something Goes Wrong
- Have pre-run outputs ready as backup
- "Let me show you what the output looks like" (switch to files)
- Technical issues happen - focus on the outputs, not the process

---

## One-Liner Summary

> "It reads the documents, extracts the facts, identifies the gaps, and generates the questions - so you can focus on the analysis and strategy."

---

*Questions about the demo? Ask the team.*
