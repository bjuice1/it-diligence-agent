"""
Entity Distinction Guidelines for Discovery Agents.

Critical guidance for distinguishing between TARGET company (being acquired)
and BUYER company information in documentation.
"""

ENTITY_DISTINCTION_PROMPT = """
## TARGET VS BUYER ENTITY DISTINCTION

**CRITICAL**: You may receive documentation about BOTH the target company (being acquired) AND the buyer.

### Identification Rules:
1. **Check document headers/filenames** - Look for "target_profile" vs "buyer_profile" indicators
2. **Company names** - The document often states which company it describes
3. **Context clues** - "The target operates..." vs "The acquiring company uses..."

### Documentation Rules:
1. **Always specify entity** - Include "entity": "target" or "entity": "buyer" in every inventory entry
2. **Default to target** - If truly ambiguous after checking all indicators, default to "target"
3. **Separate entries** - If the same tool/system appears in both profiles, create TWO separate entries
4. **Cross-reference note** - If buyer has a different tool in same category, note it for integration context

### Why This Matters:
- The investment thesis focuses on the TARGET company
- Buyer information is for integration planning only
- Mixing them creates misleading findings and incorrect risk assessments
- Security tool conflicts between target and buyer are integration considerations, not target gaps

### Example:
```
Document says: "Target uses Palo Alto firewalls"
Another doc says: "Buyer standardized on Fortinet"

CORRECT:
- Entry 1: entity="target", vendor="Palo Alto Networks", category="firewall"
- Entry 2: entity="buyer", vendor="Fortinet", category="firewall"
- Integration note: "Firewall platform conflict - migration required"

WRONG:
- Single entry mixing both: vendor="Fortinet/Palo Alto", status="unclear"
```
"""

# Short version for injection into existing prompts
ENTITY_DISTINCTION_SHORT = """
**ENTITY IDENTIFICATION**:
- Check if document is "target_profile" or "buyer_profile"
- Include "entity": "target" or "entity": "buyer" in every entry
- Never mix target and buyer tools in the same inventory entry
"""
