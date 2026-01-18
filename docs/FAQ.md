# Frequently Asked Questions
## IT Due Diligence Agent

---

## General Questions

### What does this tool actually do?

It reads IT documentation and produces structured analysis - facts extracted from documents, identified risks, follow-up questions, and cost estimates. Think of it as a very thorough first-pass analyst that never forgets to check something.

### Does it replace the team?

No. It handles extraction and structuring so the team can focus on judgment and strategy. Every output needs human review. The tool catches what might be missed under time pressure; the team adds deal context and validates findings.

### How accurate is it?

The fact extraction is generally reliable - it pulls quotes directly from documents. The analysis (severity ratings, cost estimates) is a starting point that needs human calibration. Accuracy improves over time as the team provides feedback.

### What documents can it read?

PDF and TXT files. Documents should be text-based (not scanned images). It works best with structured IT documentation like overviews, assessments, and inventories.

---

## Cost & Performance

### How much does it cost per analysis?

**$8-25 per analysis**, depending on document volume and complexity. Small document sets (20-50 pages) are on the lower end; large sets (100+ pages) cost more.

### How long does it take?

**8-30 minutes**, depending on document volume:
- Small set (20-50 pages): 8-12 minutes
- Medium set (50-100 pages): 12-18 minutes
- Large set (100-200 pages): 18-30 minutes

### Why the range in cost and time?

It depends on:
- How many pages of documents
- How dense the content is
- How many domains have relevant information
- API response times (vary)

### Is there a way to do a quick/cheap test run?

Yes. Use `--discovery-only` to just extract facts without the reasoning phase:
```bash
python main_v2.py --discovery-only input/
```
This costs about $3-6 and takes 3-5 minutes.

---

## Using the Tool

### What if the target's documents are poorly organized?

The tool handles messy documents reasonably well - it looks for relevant information regardless of how it's structured. However, results are better with well-organized documentation. The coverage grade will reflect gaps.

### What if important information is in a format it can't read?

If critical info is in spreadsheets, images, or other unsupported formats, you'll need to extract that manually. The coverage analysis will flag what's missing, and you can add those findings to the output.

### Can I run it on partial documents?

Yes. Run it on what you have - the coverage grade will show you what's missing. As more documents come in, re-run the analysis.

### What if the documents are confidential?

The tool sends document content to Anthropic's API for processing. Review your confidentiality obligations. The API doesn't store or train on the content, but the data does leave your machine during processing.

### Can multiple people run it at the same time?

Yes, but each run should use a separate input folder or the outputs may overwrite each other. Coordinate with your team on which documents are being analyzed.

---

## Understanding Outputs

### What does the coverage grade mean?

It shows how complete the documentation is against our checklist:
- **A (80%+)**: Well documented
- **B (60-79%)**: Good, some gaps
- **C (40-59%)**: Significant gaps
- **D (20-39%)**: Major gaps
- **F (<20%)**: Very incomplete

A low grade doesn't mean the target is bad - it means we need more information.

### How should I interpret the cost estimates?

As rough ranges, not precise figures. They're based on typical projects but don't account for:
- Specific integration approach
- Target's internal capabilities
- Vendor pricing variations
- Deal-specific factors

Always apply your judgment and adjust based on deal context.

### What do the phases mean (Day 1, Day 100, Post-100)?

- **Day 1**: Must be done immediately at close (connectivity, access, critical security)
- **Day 100**: First 100 days post-close (major remediation, integration work)
- **Post-100**: Longer-term items (optimization, rationalization)

### What does "based_on_facts" mean in a finding?

Every risk or work item cites the specific facts (F-INFRA-001, etc.) that support it. This lets you trace any finding back to the source document quote. If a finding seems off, check its evidence.

### Why are all risks marked with severity? Who decides?

The tool assigns initial severity based on general criteria. You should adjust based on:
- This specific deal's context
- Industry considerations
- Integration approach
- Risk tolerance

---

## Quality & Accuracy

### What if it misses something important?

It happens - no tool catches everything. That's why human review is required. When you catch something it missed:
1. Add it to your analysis
2. Let the team know so we can improve the prompts/checklists

### What if it flags something that isn't actually a risk?

Also happens. Use your judgment to dismiss or downgrade. The tool errs on the side of flagging things - better to review and dismiss than to miss something.

### How do I know if the evidence citations are accurate?

Spot-check a few. The tool includes exact quotes and source sections. If citations seem off, that's a bug - let the team know.

### What if the cost estimate is way off?

Adjust it based on your experience. Also flag it for the team - we calibrate estimates based on feedback from real deals.

---

## Improving the Tool

### How do I add something to the checklist?

Edit `tools_v2/coverage.py` and add the item to the appropriate domain/category. Takes about 5 minutes. See CONTRIBUTION_GUIDE.md for details.

### How do I improve the prompts?

Edit the relevant file in `prompts/` folder. Add guidance, risk patterns, or industry-specific considerations. See CONTRIBUTION_GUIDE.md for details.

### What should I report back after using it on a deal?

- Things it missed that you caught
- Severity ratings that were off
- Cost estimates that didn't match reality
- Questions IC asked that weren't in the VDR requests
- Anything that surprised you (good or bad)

### Does my feedback actually get used?

Yes. Feedback becomes checklist items, prompt improvements, and calibration data. Every deal makes the system better.

---

## Technical Questions

### Where does it run?

Locally on your machine. Documents don't get stored anywhere except your local folders and (temporarily) sent to the Anthropic API for processing.

### Do I need special software?

Python 3.8+ and the dependencies in requirements.txt. No special infrastructure needed.

### What if the API is down or slow?

The tool has automatic retry built in. If it fails repeatedly, wait a few minutes and try again. Check your internet connection.

### Can I run it offline?

No. It requires API access to Anthropic's Claude models.

### What models does it use?

- Discovery (fact extraction): Claude 3.5 Haiku (fast, cheap)
- Reasoning (analysis): Claude 3.5/4 Sonnet (capable)

This "tiering" keeps costs down while maintaining analysis quality.

---

## Edge Cases

### What if there are no IT documents?

The tool won't produce useful output. You'll get a very low coverage grade and mostly gap identifications. That's actually useful information - it tells you to request IT documentation.

### What if documents are in a foreign language?

The tool works best with English documents. It may partially work with other languages but accuracy will be lower.

### What if the documents contradict each other?

The synthesis phase tries to catch contradictions across domains. Review the consistency checks in the synthesis output. Contradictions usually mean you need clarification from the target.

### What about very large document sets (500+ pages)?

Consider breaking into batches or prioritizing the most important documents. Very large sets take longer and cost more. The tool doesn't have a hard limit but performance may degrade.

---

## Getting Help

### Something isn't working - who do I ask?

Check this FAQ and GETTING_STARTED.md first. If still stuck, ask the team.

### I have an idea for improvement - where do I share it?

Tell the team! Ideas for new checklist items, prompt improvements, or features are all valuable.

### Where's the full technical documentation?

See LEADERSHIP_TECHNICAL_OVERVIEW.md for architecture and methodology details.

---

*Last updated: January 2026*
