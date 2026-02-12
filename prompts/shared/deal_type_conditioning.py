"""
Deal-type-specific conditioning for reasoning prompts.

Provides explicit M&A lens guidance based on deal structure.
See specs/deal-type-awareness/03-reasoning-prompt-conditioning.md
"""

ACQUISITION_CONDITIONING = """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 DEAL TYPE: ACQUISITION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Strategic Direction: INTEGRATION - Absorb target into buyer's environment
Key Question: "How do we integrate?"

PRIMARY M&A LENSES (Focus here):
✅ Synergy Opportunity - Where can we consolidate and eliminate redundancy?
✅ Day-1 Continuity - What must work immediately for business continuity?
✅ Cost Driver - What are the integration costs?

SECONDARY LENSES (Consider if relevant):
⚠️  Integration Complexity - How difficult will this be?

DE-EMPHASIZE (Usually not relevant for acquisitions):
❌ TSA Exposure - Low priority unless target is itself carved out
❌ Separation Complexity - Not applicable (we're integrating, not separating)

RECOMMENDATIONS SHOULD FOCUS ON:
- Which target systems can be retired (consolidate to buyer's platform)
- What buyer systems target will adopt
- Timeline to migrate target onto buyer infrastructure
- Synergies from eliminating duplicate licenses/systems/teams

DO NOT RECOMMEND:
- Standing up standalone target systems (opposite of integration)
- TSA services from buyer to target (target is being absorbed)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

CARVEOUT_CONDITIONING = """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚨 DEAL TYPE: CARVE-OUT (Separation from Parent)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Strategic Direction: SEPARATION - Extract target from parent to operate standalone
Key Question: "How do we stand alone?"

⚠️  CRITICAL: This is NOT an acquisition. Target is LEAVING the parent company.
Entity "buyer" = new owner (may not exist yet), NOT the parent being separated from.

PRIMARY M&A LENSES (Focus here):
✅ TSA Exposure - What services must parent provide during transition?
✅ Separation Complexity - How entangled with parent systems/data?
✅ Day-1 Continuity - What must work independently from Day 1?

SECONDARY LENSES (Consider if relevant):
⚠️  Cost Driver - What are the standup costs?

IGNORE (Not applicable for carveouts):
❌ Synergy Opportunity - There are NO consolidation synergies in a separation
❌ DO NOT recommend consolidating target systems with buyer

RECOMMENDATIONS SHOULD FOCUS ON:
- What standalone systems target needs to build/buy
- Which parent services require TSA (and for how long)
- How to separate commingled data/processes from parent
- Timeline to achieve standalone operations
- Stranded costs that will remain with parent

EXAMPLES OF CORRECT RECOMMENDATIONS:
✅ "Stand up standalone Salesforce instance for target"
✅ "Negotiate 18-month TSA for ERP access from parent"
✅ "Separate target customer data from parent's shared database"

EXAMPLES OF WRONG RECOMMENDATIONS (DO NOT DO THIS):
❌ "Consolidate target's Salesforce onto buyer's instance" (wrong direction)
❌ "Eliminate redundant systems between buyer and target" (no synergies in carveouts)
❌ "Migrate target to buyer's infrastructure" (target needs standalone, not integration)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

DIVESTITURE_CONDITIONING = """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔄 DEAL TYPE: DIVESTITURE (Asset Sale / Clean Separation)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Strategic Direction: CLEAN SEPARATION - Remove target from seller with minimal RemainCo disruption
Key Question: "How do we cleanly separate?"

Note: Focus is on SELLER's perspective (protecting RemainCo operations).

PRIMARY M&A LENSES (Focus here):
✅ Separation Complexity - How to extract target without damaging RemainCo?
✅ Cost Driver - What are the separation/cleanup costs?
✅ RemainCo Impact - How does removing target affect remaining business?

SECONDARY LENSES (Consider if relevant):
⚠️  Day-1 Continuity - Ensure RemainCo operations unaffected
⚠️  TSA Exposure - May provide services to buyer during transition

IGNORE (Usually not known or relevant):
❌ Synergy Opportunity - Buyer may not be known during diligence
❌ Do NOT recommend consolidation (buyer may be unknown)

RECOMMENDATIONS SHOULD FOCUS ON:
- How to separate target data from RemainCo systems
- Which contracts/licenses need to be assigned or split
- Protecting RemainCo operations during separation
- Transition service agreements (TSAs) seller will provide to buyer
- Stranded costs remaining with seller after divestiture

EXAMPLES OF CORRECT RECOMMENDATIONS:
✅ "Separate target's customer data from shared CRM database"
✅ "Split ERP instance to isolate target transactions from RemainCo"
✅ "Renegotiate software licenses to remove target user count"
✅ "Offer 12-month TSA for data center services to buyer"

EXAMPLES OF WRONG RECOMMENDATIONS:
❌ "Consolidate target with buyer's systems" (buyer may be unknown)
❌ "Synergies from combining target and buyer apps" (not applicable)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""


def get_deal_type_conditioning(deal_type: str) -> str:
    """
    Get deal-type-specific conditioning to inject into reasoning prompts.

    Args:
        deal_type: "acquisition", "carveout", or "divestiture"

    Returns:
        Conditioning text to prepend to reasoning prompt
    """
    # Normalize deal_type
    deal_type = (deal_type or "").lower().strip()

    # Map aliases to canonical types
    if deal_type in ['bolt_on', 'platform']:
        deal_type = 'acquisition'
    elif deal_type in ['carve_out', 'carve-out', 'spinoff', 'spin-off']:
        deal_type = 'carveout'
    elif deal_type in ['sale', 'disposal']:
        deal_type = 'divestiture'

    conditioning_map = {
        'acquisition': ACQUISITION_CONDITIONING,
        'carveout': CARVEOUT_CONDITIONING,
        'divestiture': DIVESTITURE_CONDITIONING
    }

    # Default to acquisition if unknown type
    return conditioning_map.get(deal_type, ACQUISITION_CONDITIONING)
