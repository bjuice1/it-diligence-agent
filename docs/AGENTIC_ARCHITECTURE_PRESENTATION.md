# What's Actually Agentic?
## An Honest Assessment of Our Architecture

---

> **STYLING NOTES FOR HTML GENERATION:**
> - Background: Near-black (#0a0a0a) - minimal, clean
> - Primary accent: Electric cyan (#00d4ff) - for highlights
> - Secondary accent: Coral red (#ff6b6b) - for "no" items, warnings
> - Tertiary accent: Teal (#4ecdc4) - for neutral highlights
> - Success: Green (#2ecc71) - for "yes" items, positives
> - Text: White primary, gray secondary
> - Style: Dark mode, generous whitespace, accent colors for emphasis only
> - Fonts: Modern sans-serif (Space Grotesk for headings, Inter for body)

---

## SLIDE 1: Title

# What's Actually Agentic?
### An Honest Assessment of Our Architecture

*[Visual: Abstract geometric pattern with nodes and connections, subtle animation]*

---

## SLIDE 2: The Question Everyone Asks

> # "Is this LangGraph? LangFlow? LangChain?"

# No.

It's a custom Python application calling the Claude API directly.

*[Visual: Strike-through effect on framework names]*
*[Accent: Electric cyan]*

---

## SLIDE 3: The Entire Tech Stack

| Package | Purpose |
|---------|---------|
| `anthropic` | Direct Claude API |
| `pymupdf` | PDF extraction |
| `sqlite3` | Persistence |
| `python-dotenv` | Config |

### That's it.
**No frameworks. No vector databases. No RAG pipelines.**

*[Visual: Four minimal cards/boxes]*
*[Accent: Teal]*

---

## SLIDE 4: Section Break

# So What IS Agentic?

*[Visual: Animated pulse or glow effect]*

---

## SLIDE 5: The Only Truly Agentic Part

### Inside the Claude API call, the model autonomously decides:

```
Claude receives  →  prompt + document + tools
         ↓
Claude decides   →  "I should call identify_risk"
         ↓
Claude decides   →  "Now create_work_item"
         ↓
Claude decides   →  "I'm done"
```

> **That decision-making loop is genuinely agentic.**
> The model is making choices, not following a script.

*[Visual: Animated decision flowchart]*
*[Accent: Green/success]*

---

## SLIDE 6: Section Break

# What's NOT Agentic
### (Just Scaled Prompts)

*[Visual: Color shift to coral/warning]*

---

## SLIDE 7: Hardcoded Orchestration

### 1. The Orchestration is Hardcoded

```python
# main.py - this is just a script, not an agent
domain_agents = [
    (InfrastructureAgent, "Infrastructure"),
    (NetworkAgent, "Network"),
    (CybersecurityAgent, "Cybersecurity"),
    # ... always these 6, in this order
]
```

**No decision about WHICH agents to run. Always the same 6.**

| True Agent | Our System |
|------------|------------|
| Looks at document, decides "this needs security focus" | Runs all 6 agents regardless of content |

*[Accent: Coral red]*

---

## SLIDE 8: No Inter-Agent Communication

### 2. Agents Don't Talk to Each Other

```
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│Infrastructure│  │   Network   │  │  Security   │
│      ↓      │  │      ↓      │  │      ↓      │
│   [store]   │  │   [store]   │  │   [store]   │
└─────────────┘  └─────────────┘  └─────────────┘
        │              │               │
        └──────────────┼───────────────┘
                       ↓
              ┌─────────────────┐
              │   Coordinator   │
              │  (just reads)   │
              └─────────────────┘
```

**They never talk to each other. They don't know each other exists.**

The "coordinator" just reads everyone's output after the fact.
It's not orchestrating—it's **summarizing**.

*[Accent: Coral red]*

---

## SLIDE 9: More Non-Agentic Things

### 3. No Planning
Agents don't create plans. The "plan" is baked into the prompt.

### 4. No Memory
Every run starts fresh. Doesn't learn from past analyses.

### 5. No Self-Correction
If an agent makes a mistake, nothing catches it.

*[Accent: Coral red]*

---

## SLIDE 10: Honest Capability Assessment

| Capability | True Agents | Our System |
|------------|:-----------:|:----------:|
| Decides what tools to call | ✓ | **✓ YES** |
| Decides when to stop | ✓ | **✓ YES** |
| Decides which agents to run | ✓ | **✗ NO** |
| Agents communicate | ✓ | **✗ NO** |
| Creates and adapts plans | ✓ | **✗ NO** |
| Learns from past runs | ✓ | **✗ NO** |
| Self-corrects errors | ✓ | **✗ NO** |
| Dynamically spawns sub-agents | ✓ | **✗ NO** |

*[Visual: Green checkmarks, red X marks]*

---

## SLIDE 11: What This System Actually Is

### Accurate Description:
> "Parallel tool-augmented LLM calls with structured output and post-hoc synthesis"

### Simple Version:
> "Six specialized prompts running in parallel, each with tools for structured output, followed by a summarization prompt"

---

**The "agentic" part is Claude deciding how to use tools.**
**Everything else is just orchestration code.**

*[Accent: Electric cyan]*

---

## SLIDE 12: Section Break

# Why This Still Works

*[Visual: Shift to green/success color]*

---

## SLIDE 13: You Don't Always Need True Agents

### IT due diligence is a well-defined task:

- ✓ Fixed domains (infra, network, security...)
- ✓ Fixed output structure (risks, gaps, work items)
- ✓ Fixed analysis framework (four lenses)

> **You don't need dynamic planning when the plan is always the same.**

*[Accent: Green]*

---

## SLIDE 14: Where the Real Value Comes From

| | What | Why |
|:-:|------|-----|
| 🧠 | **Domain-Specific Prompts** | The expertise |
| 📐 | **Structured Output** | The tools |
| ⚡ | **Parallelization** | The speed |
| 🔀 | **Synthesis** | The coordinator |

### Not from agents autonomously deciding what to do.

*[Accent: Teal]*

---

## SLIDE 15: Section Break

# What Would Make It More Agentic?
### (If We Wanted To)

*[Visual: Future/forward-looking]*

---

## SLIDE 16: A Truly Agentic Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      PLANNER AGENT                              │
│                                                                 │
│   • Reads document, assesses content                           │
│   • "This is heavy on security, light on network"              │
│   • "Should I spawn an ERP specialist?"                        │
│   • Decides which agents and how deep                          │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│                    DYNAMIC EXECUTION                            │
│                                                                 │
│   • Agents spawned based on planner's decision                 │
│   • Agents can request help from each other                    │
│   • Agents can spawn sub-agents for deep dives                 │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│                      CRITIC AGENT                               │
│                                                                 │
│   • Reviews all findings                                        │
│   • "This risk seems overstated"                               │
│   • "You missed something on page 12"                          │
│   • Sends agents back for another pass                         │
└─────────────────────────────────────────────────────────────────┘
```

**But this adds complexity, cost, and latency—may not improve output for a well-defined task.**

*[Accent: Electric cyan]*

---

## SLIDE 17: The Bottom Line

| | |
|---|---|
| **What we have** | Smart prompts with tool use, run in parallel, with structured output |
| **What we call it** | "Agents" (industry term for tool-using LLMs) |
| **What it actually is** | Scaled prompt engineering with good orchestration |
| **Is that bad?** | **No. It works. The output is good.** |

*[Accent: Green on last row]*

---

## SLIDE 18: Closing

> # "The term 'agent' is overloaded."

The industry calls any tool-using LLM an "agent."

That's fine.

**Just know what you're actually building.**

*[Visual: Fade to minimal end card]*

---

## Generation Notes

When generating the HTML slideshow:

1. **Navigation**: Arrow keys or click to advance
2. **Transitions**: Subtle fade or slide, nothing flashy
3. **Code blocks**: Syntax highlighted with accent colors
4. **Tables**: Clean lines, accent color for headers
5. **Diagrams**: Rendered as ASCII art or simple SVG boxes
6. **Responsive**: Should work on projector (16:9) and screen
7. **Print**: Should be printable to PDF as handout

The key aesthetic is **minimal dark mode with strategic color pops**—not a rainbow, just 2-3 accent colors used purposefully.
