# Interactive Mode Design
## Making the IT DD Agent More Usable

---

## The Problem

The current system is **batch mode only**:

```
User drops docs → Runs command → Waits 15 min → Gets outputs → ???

Problems:
• Can't refine mid-stream ("look deeper at security")
• Can't add context after seeing initial results
• Can't challenge/adjust findings without re-running
• No way to say "that severity is wrong" and have it stick
• New docs = full re-run
```

Users provide input and get output, but there's no interactive environment. Any change requires re-running the entire pipeline.

---

## What Users Actually Need

```
┌─────────────────────────────────────────────────────────────────┐
│ REAL WORKFLOW                                                    │
└─────────────────────────────────────────────────────────────────┘

1. Run initial analysis
2. Review outputs: "Hmm, this severity seems off"
3. Adjust: "Actually this is critical, not medium"
4. Drill down: "Tell me more about the VMware risk"
5. Add context: "This is a healthcare deal - re-evaluate"
6. Get new docs: "Here's the DR plan they sent"
7. Update: Only re-analyze what changed
8. Finalize: "Generate the IC summary"
```

---

## Options to Consider

### Option A: Staged Pipeline with Checkpoints

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Discovery   │────►│   PAUSE      │────►│  Reasoning   │
│  (extract)   │     │  for review  │     │  (analyze)   │
└──────────────┘     └──────────────┘     └──────────────┘
                           │
                     User reviews facts
                     Adds missing items
                     Validates extraction
                           │
                           ▼
                     Then continues
```

**How it works:**
- Run discovery, stop before reasoning
- User reviews extracted facts
- User can add/edit/delete facts manually
- Then continue to reasoning phase

**Pros:**
- Quality control at each stage
- User validates extraction before analysis
- Can catch errors early

**Cons:**
- Slower overall process
- Requires user engagement at each stage
- More friction for simple runs

---

### Option B: Interactive Post-Analysis Mode

```bash
$ python main_v2.py input/ --interactive

Analysis complete. Entering interactive mode.

> explain R-001
Risk R-001: EOL VMware Version
Based on: F-INFRA-003 ("VMware vSphere 6.7...")
Reasoning: VMware 6.7 reached EOL October 2022...

> adjust R-001 severity critical
Updated R-001 severity: medium → critical

> add context "healthcare deal, HIPAA applies"
Context added. Re-running reasoning for cybersecurity domain...

> regenerate summary
Executive summary regenerated.

> export
Outputs saved to output/
```

**How it works:**
- Run full analysis first
- Drop into interactive shell
- User can query, adjust, and regenerate

**Pros:**
- Natural iterative workflow
- Quick adjustments without full re-run
- Can drill down on specific findings
- Fits terminal-based workflow

**Cons:**
- Need to build interactive shell
- Learning curve for commands
- Still CLI-based (not visual)

**Key commands to support:**
| Command | Description |
|---------|-------------|
| `explain <id>` | Why did you conclude this? |
| `adjust <id> <field> <value>` | Change severity, phase, cost |
| `add context "<text>"` | Add deal-specific context |
| `rerun <domain>` | Re-analyze one domain |
| `add fact <domain> "<description>"` | Manually add a fact |
| `add risk "<title>" <severity>` | Manually add a risk |
| `delete <id>` | Remove a finding |
| `regenerate` | Rebuild synthesis/summary |
| `export` | Save everything to files |
| `status` | Show current state |
| `help` | Show available commands |

---

### Option C: Editable Output Files + Validation

```
1. Run analysis → outputs to JSON
2. User edits JSON directly (change severity, add notes)
3. Run validation: python main_v2.py --validate output/findings.json
4. Run synthesis from edited files: python main_v2.py --from-findings output/findings.json
```

**How it works:**
- Analysis produces editable JSON files
- User modifies files in text editor
- Validation command checks for errors
- Synthesis can run from edited files

**Pros:**
- Simple to implement
- Uses existing tools (text editor)
- Full control over outputs
- No new interface to learn

**Cons:**
- JSON editing is error-prone
- Not user-friendly for non-technical users
- Easy to break file structure
- No guidance on valid values

---

### Option D: Web Interface

```
┌─────────────────────────────────────────────────────────────────┐
│  IT DD Agent                                         [Run] [Export]│
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Documents: 3 loaded                    Coverage: B (67%)       │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ RISKS                                          [+ Add]   │   │
│  ├─────────────────────────────────────────────────────────┤   │
│  │ ⚠ R-001 EOL VMware       [HIGH ▼]  [Edit] [Delete]      │   │
│  │ ⚠ R-002 No SIEM          [MEDIUM ▼] [Edit] [Delete]     │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ WORK ITEMS                                     [+ Add]   │   │
│  ├─────────────────────────────────────────────────────────┤   │
│  │ □ WI-001 VMware Upgrade  [Day 100] [$100K-$500K]        │   │
│  │ □ WI-002 SIEM Setup      [Day 100] [$50K-$150K]         │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  Deal Context: [+ Add context...]                               │
│                                                                 │
│  [Regenerate Summary]  [Export to JSON]  [Export to Markdown]   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**How it works:**
- Local web server (Flask/FastAPI)
- Upload docs through browser
- Visual interface for reviewing/editing
- Click to adjust, drag to reorder

**Pros:**
- Most user-friendly
- Visual feedback
- Accessible to non-technical users
- Can show relationships visually

**Cons:**
- Significant build effort
- Need to maintain frontend + backend
- Browser dependency
- More complex deployment

---

### Option E: Chat Interface (Hybrid)

```
Run analysis, then chat with results:

User: "Why is R-003 only medium severity?"
Agent: "R-003 (No documented DR testing) is rated medium because
        the company has documented backup procedures, suggesting
        some DR capability exists even if not formally tested."

User: "For healthcare deals that should be high"
Agent: "You're right - for healthcare targets, untested DR is a
        compliance risk. Updated R-003 to HIGH severity.

        Note: I've added 'healthcare context' for this session.
        Should I re-evaluate other findings with this context?"

User: "Yes, and what questions should I ask about their AWS setup?"
Agent: "Based on the gaps identified, you should request:
        1. AWS account structure and organization
        2. Multi-region/multi-AZ deployment details
        3. AWS security configurations (GuardDuty, SecurityHub)
        ..."
```

**How it works:**
- Complete analysis first
- Enter chat mode with Claude
- Claude has access to all findings
- Can query, explain, and modify through conversation

**Pros:**
- Most natural interaction
- Can ask complex questions
- Leverages Claude's reasoning
- No rigid command structure

**Cons:**
- API costs for every interaction
- Less predictable than structured commands
- May be slower for simple changes
- Requires careful prompt engineering

---

## Comparison Matrix

| Option | Build Effort | User-Friendly | Flexibility | Cost |
|--------|--------------|---------------|-------------|------|
| A: Staged Pipeline | Low | Medium | Low | $ |
| B: Interactive CLI | Medium | Medium | High | $ |
| C: Editable Files | Low | Low | Medium | $ |
| D: Web Interface | High | High | High | $ |
| E: Chat Interface | Medium | High | High | $$$ |

---

## Recommendation

**Start with Option B (Interactive CLI)** because:

1. **Lowest build effort** for meaningful improvement
2. **Natural fit** with existing pipeline architecture
3. **Incremental capability** - can add commands over time
4. **No new dependencies** - just Python
5. **Associates can use terminal** - fits current workflow

### MVP Interactive Commands

```
Phase 1 (Core):
  explain <id>           - Show reasoning for a finding
  adjust <id> <field>    - Modify severity, phase, cost, owner
  status                 - Show current findings summary
  export                 - Save to files

Phase 2 (Context):
  add context "<text>"   - Add deal context, optionally re-run
  rerun <domain>         - Re-analyze specific domain

Phase 3 (Manual Entry):
  add fact ...           - Manually add a fact
  add risk ...           - Manually add a risk
  delete <id>            - Remove a finding

Phase 4 (Advanced):
  compare <file>         - Compare to previous analysis
  diff                   - Show changes since last export
  chat                   - Enter free-form chat mode (Option E)
```

### Future: Add Web UI

If adoption is strong and there's demand for non-technical users, build Option D (Web Interface) as a layer on top of the same backend.

---

## Implementation Approach

### Step 1: Session State

Create a `Session` class that holds:
- Current FactStore
- Current ReasoningStore
- Modification history
- Deal context
- Unsaved changes flag

### Step 2: Command Parser

Simple command parser:
```python
def parse_command(input_str):
    parts = shlex.split(input_str)
    command = parts[0]
    args = parts[1:]
    return command, args
```

### Step 3: Command Handlers

Each command maps to a handler:
```python
COMMANDS = {
    "explain": handle_explain,
    "adjust": handle_adjust,
    "status": handle_status,
    "export": handle_export,
    # ...
}
```

### Step 4: REPL Loop

```python
def interactive_mode(fact_store, reasoning_store):
    session = Session(fact_store, reasoning_store)

    print("Interactive mode. Type 'help' for commands.")

    while True:
        try:
            user_input = input("> ").strip()
            if user_input == "exit":
                break

            command, args = parse_command(user_input)
            if command in COMMANDS:
                COMMANDS[command](session, args)
            else:
                print(f"Unknown command: {command}")

        except KeyboardInterrupt:
            break

    if session.has_unsaved_changes:
        if confirm("Save changes before exit?"):
            session.export()
```

---

## Open Questions

1. **Scope of re-runs**: When user adds context, re-run all domains or just affected ones?

2. **Change tracking**: How to track what user modified vs. original output?

3. **Undo support**: Allow undoing adjustments? How many levels?

4. **Multi-user**: If two people review, how to merge their changes?

5. **Persistence**: Save session state between runs? Or always start fresh?

---

## Next Steps

1. **Decide**: Which option(s) to pursue
2. **Design**: Detailed command specs for chosen option
3. **Build**: MVP with core commands
4. **Test**: With real users on real deals
5. **Iterate**: Add commands based on feedback

---

*This document captures the design discussion. Update as decisions are made.*
