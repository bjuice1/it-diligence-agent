# IT Due Diligence: Data Flow Overview

## How Facts Become Cost Estimates

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           DEAL INPUTS                                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │ CIM / Data   │  │ IT Fact      │  │ Interview    │  │ TSA Draft /  │    │
│  │ Room Docs    │  │ Packs        │  │ Notes        │  │ Deal Terms   │    │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘    │
│         │                 │                 │                 │            │
│         └─────────────────┴─────────────────┴─────────────────┘            │
│                                    │                                        │
│                                    ▼                                        │
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     │  Unstructured data
                                     │  (PDFs, Word, Excel, notes)
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STAGE 1: LLM INTERPRETATION                                                │
│  ─────────────────────────────                                              │
│                                                                             │
│  LLM reads documents and extracts:                                          │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Deal Facts                                                          │   │
│  │ • User count: 1,500                                                 │   │
│  │ • Applications: 45 (12 critical)                                    │   │
│  │ • Databases: 25 (Oracle, SQL Server)                                │   │
│  │ • Parent dependencies: Shared AD, email, ERP                        │   │
│  │ • Deal type: Carveout                                               │   │
│  │ • Timeline: 12 months to close                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                              │
│                              ▼                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Identified Considerations                                           │   │
│  │ • "Shared Azure AD tenant → Need standalone identity"               │   │
│  │ • "Parent ERP instance → Need separate ERP or TSA"                  │   │
│  │ • "Oracle databases on parent license → License exposure"           │   │
│  │ • "Shared network infrastructure → Segregation required"            │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     │  Structured considerations
                                     │  with categories
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STAGE 2: TEMPLATE MATCHING (Knowledge Base)                                │
│  ───────────────────────────────────────────                                │
│                                                                             │
│  ┌────────────────────────────────┐    ┌────────────────────────────────┐  │
│  │ Considerations from Stage 1    │───▶│ PwC Activity Inventory         │  │
│  │                                │    │ (395 activities across 6 phases)│  │
│  │ "Need standalone identity"     │    │                                │  │
│  │                                │    │ ┌────────────────────────────┐ │  │
│  │                                │    │ │ IDN-010: Azure AD Build    │ │  │
│  │                                │    │ │ Base: $75K-$150K           │ │  │
│  │                                │    │ │ Per-user: $15-$35          │ │  │
│  │                                │    │ │ TSA: 6-12 months           │ │  │
│  │                                │    │ └────────────────────────────┘ │  │
│  └────────────────────────────────┘    └────────────────────────────────┘  │
│                                                                             │
│  MATCHING RULES (Deterministic - No AI Hallucination)                       │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ IF consideration = "standalone identity"                            │   │
│  │ THEN match activities: IDN-010, IDN-011, IDN-020, IDN-021...        │   │
│  │                                                                     │   │
│  │ IF deal_type = "carveout" AND has_parent_erp = true                 │   │
│  │ THEN match activities: ERP-010, ERP-020, ERP-030...                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  OUTPUT: Matched activities with BASE COSTS from templates                  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     │  Matched activities with
                                     │  template-based costs
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STAGE 3: LLM REFINEMENT & VALIDATION                                       │
│  ────────────────────────────────────                                       │
│                                                                             │
│  Apply Deal-Specific Adjustments:                                           │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Complexity Multipliers                Industry Modifiers            │   │
│  │ ─────────────────────                  ──────────────────           │   │
│  │ Simple:        0.7x                    Standard:           1.0x     │   │
│  │ Moderate:      1.0x                    Financial Services: 1.3x     │   │
│  │ Complex:       1.5x                    Healthcare:         1.25x    │   │
│  │ Highly Complex: 2.0x                   Government:         1.4x     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  Validation Checks:                                                         │
│  • Coverage gaps (missing workstreams?)                                     │
│  • Reasonableness (total in expected range?)                                │
│  • Consistency (related activities aligned?)                                │
│  • TSA coherence (durations make sense?)                                    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     │  Validated, adjusted
                                     │  cost estimates
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           ANALYSIS OUTPUT                                   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ COST SUMMARY BY PHASE                                               │   │
│  │ ════════════════════════════════════════════════════════════════    │   │
│  │ Phase 1 (Core Infrastructure):    $2.8M  -  $8.1M                   │   │
│  │ Phase 2 (Network & Security):     $2.4M  -  $6.3M                   │   │
│  │ Phase 3 (Applications):           $9.8M  - $32.9M                   │   │
│  │ Phase 4 (Data & Migration):       $4.6M  - $13.3M                   │   │
│  │ Phase 5 (Licensing):              $2.8M  -  $8.9M                   │   │
│  │ Phase 6 (Integration):            $2.2M  -  $6.4M                   │   │
│  │ ────────────────────────────────────────────────────────────────    │   │
│  │ TOTAL:                           $24.5M  - $75.8M                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ ACTIVITY DETAIL (Traceable to Templates)                            │   │
│  │ ════════════════════════════════════════════════════════════════    │   │
│  │                                                                     │   │
│  │ IDN-010: Standalone Azure AD tenant build                           │   │
│  │   Triggered by: "Shared Azure AD with parent"                       │   │
│  │   Base cost: $75,000 - $150,000                                     │   │
│  │   + Per-user (1,500): $22,500 - $52,500                             │   │
│  │   x Industry (Financial): 1.3x                                      │   │
│  │   ────────────────────────────────                                  │   │
│  │   Final: $126,750 - $263,250                                        │   │
│  │   TSA Required: 6-12 months                                         │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Why This Architecture Works

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│   WHAT THE LLM DOES                    WHAT THE LLM DOESN'T DO              │
│   ══════════════════                   ════════════════════════             │
│                                                                             │
│   ✓ Reads unstructured documents       ✗ Generate cost numbers              │
│   ✓ Understands context                ✗ Make up activities                 │
│   ✓ Identifies implications            ✗ Guess at TSA durations             │
│   ✓ Applies judgment on complexity     ✗ Create formulas                    │
│   ✓ Validates reasonableness           ✗ Define new workstreams             │
│                                                                             │
│   COSTS COME FROM TEMPLATES ──────────────────────────────────────────────▶ │
│   (Team-maintained, auditable, updatable)                                   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Template Inventory (Current State)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  PHASE          │ SCOPE                      │ ACTIVITIES │ COVERAGE        │
│─────────────────┼────────────────────────────┼────────────┼─────────────────│
│  Phase 1        │ Identity, Email, Infra     │     70     │ ██████████ 100% │
│  Phase 2        │ Network, Security          │     67     │ ██████████ 100% │
│  Phase 3        │ ERP, CRM, HCM, Apps, SaaS  │     94     │ ██████████ 100% │
│  Phase 4        │ Database, Files, Archive   │     61     │ ██████████ 100% │
│  Phase 5        │ Licensing (MS, Oracle...)  │     53     │ ██████████ 100% │
│  Phase 6        │ Integration (Buyer-side)   │     50     │ ██████████ 100% │
│─────────────────┼────────────────────────────┼────────────┼─────────────────│
│  Phase 7        │ Operational Run-Rate       │      -     │ ░░░░░░░░░░   0% │
│  Phase 8        │ Compliance & Regulatory    │      -     │ ░░░░░░░░░░   0% │
│  Phase 9        │ Vendor & Contract          │      -     │ ░░░░░░░░░░   0% │
│  Phase 10       │ Validation & Refinement    │      -     │ ░░░░░░░░░░   0% │
│─────────────────┼────────────────────────────┼────────────┼─────────────────│
│  TOTAL          │                            │    395     │ ██████░░░░  60% │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Update Path (How Templates Evolve)

```
    ┌──────────────────┐
    │   Use on Deal    │
    └────────┬─────────┘
             │
             ▼
    ┌──────────────────┐
    │ Capture Actuals  │◀─────┐
    │ vs. Estimates    │      │
    └────────┬─────────┘      │
             │                │
             ▼                │
    ┌──────────────────┐      │
    │ Team Reviews     │      │     NO PROMPT ENGINEERING
    │ Identifies Gaps  │      │     ══════════════════════
    └────────┬─────────┘      │     Just update the template:
             │                │
             ▼                │        "base_cost": (25000, 50000)
    ┌──────────────────┐      │               ↓
    │ Update Template  │      │        "base_cost": (30000, 60000)
    │ (Python file)    │──────┘
    └──────────────────┘              Done. No retraining.
```

---

## Key Takeaways for Leadership

| Question | Answer |
|----------|--------|
| **Is the AI making up costs?** | No. All costs come from team-maintained templates. |
| **Can we audit the output?** | Yes. Every cost traces to a template ID with formula. |
| **How do we update it?** | Edit Python templates. No prompt engineering needed. |
| **What does the AI actually do?** | Reads docs, identifies needs, applies judgment on complexity. |
| **Is this defensible to clients?** | Yes. Methodology is documented, traceable, consistent. |
| **Does this replace our people?** | No. Augments them - handles tedious work, frees judgment. |

---

*Document Version: 1.0*
*January 2026*
