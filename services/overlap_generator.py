"""
Overlap Generation Service - Phase 3.5 of Analysis Pipeline

PURPOSE:
This module generates OverlapCandidate objects by comparing target and buyer
facts BEFORE reasoning begins. This makes overlap detection a first-class
pipeline stage rather than optional LLM behavior.

ARCHITECTURE:
- Called after Phase 2 (buyer fact extraction)
- Before Phase 3 (reasoning)
- Produces overlaps_by_domain.json artifact

STRATEGY:
Uses LLM to detect overlaps with structured output, ensuring consistent
overlap map generation across all analyses.
"""

from typing import List, Dict, Optional
from dataclasses import asdict
import json
from anthropic import Anthropic
from tools_v2.reasoning_tools import OverlapCandidate, OVERLAP_TYPES, ALL_DOMAINS


# Domain-specific overlap types (most relevant for each domain)
DOMAIN_OVERLAP_PRIORITIES = {
    "applications": [
        "platform_mismatch",
        "platform_alignment",
        "version_gap",
        "capability_overlap",
        "integration_complexity"
    ],
    "infrastructure": [
        "platform_alignment",
        "capability_gap",
        "version_gap",
        "integration_complexity"
    ],
    "cybersecurity": [
        "platform_mismatch",
        "security_posture_gap",
        "capability_overlap"
    ],
    "network": [
        "platform_mismatch",
        "integration_complexity",
        "capability_gap"
    ],
    "identity_access": [
        "platform_mismatch",
        "security_posture_gap",
        "integration_complexity"
    ],
    "organization": [
        "capability_gap",
        "process_divergence"
    ]
}


class OverlapGenerator:
    """Generates overlap candidates by comparing target and buyer facts."""

    def __init__(self, anthropic_client: Optional[Anthropic] = None):
        """Initialize with Anthropic client."""
        self.client = anthropic_client or Anthropic()

    def generate_overlap_map_for_domain(
        self,
        domain: str,
        target_facts: List[Dict],
        buyer_facts: List[Dict]
    ) -> List[OverlapCandidate]:
        """
        Generate overlap candidates for a single domain.

        Args:
            domain: Domain name (applications, infrastructure, etc.)
            target_facts: List of target fact dicts (from fact_store)
            buyer_facts: List of buyer fact dicts (from fact_store)

        Returns:
            List of OverlapCandidate objects (may be empty if no overlaps found)
        """
        # Handle edge cases
        if not target_facts:
            return []  # No target facts = no analysis possible

        if not buyer_facts:
            return []  # No buyer facts = no overlap to detect

        # Format facts for comparison
        target_inventory = self._format_facts(target_facts, "TARGET")
        buyer_inventory = self._format_facts(buyer_facts, "BUYER")

        # Get domain-specific overlap types
        priority_overlap_types = DOMAIN_OVERLAP_PRIORITIES.get(domain, OVERLAP_TYPES)

        # Build prompt for overlap detection
        prompt = self._build_overlap_detection_prompt(
            domain=domain,
            target_inventory=target_inventory,
            buyer_inventory=buyer_inventory,
            overlap_types=priority_overlap_types
        )

        # Call LLM to detect overlaps
        try:
            overlaps = self._call_llm_for_overlap_detection(prompt, domain)
            return overlaps
        except Exception as e:
            print(f"[ERROR] Overlap generation failed for {domain}: {e}")
            return []  # Return empty list on error (graceful degradation)

    def _format_facts(self, facts: List[Dict], entity_label: str) -> str:
        """Format facts into readable inventory for comparison."""
        if not facts:
            return f"## {entity_label} INVENTORY\nNo facts available.\n"

        lines = [f"## {entity_label} INVENTORY ({len(facts)} facts)\n"]

        for fact in facts:
            fact_id = fact.get("fact_id", "UNKNOWN")
            category = fact.get("category", "General")
            statement = fact.get("statement", "")
            details = fact.get("details", {})

            lines.append(f"**{fact_id}** [{category}]")
            lines.append(f"  {statement}")

            if details:
                details_str = ", ".join([f"{k}={v}" for k, v in details.items() if v])
                if details_str:
                    lines.append(f"  Details: {details_str}")

            lines.append("")  # Blank line

        return "\n".join(lines)

    def _build_overlap_detection_prompt(
        self,
        domain: str,
        target_inventory: str,
        buyer_inventory: str,
        overlap_types: List[str]
    ) -> str:
        """Build prompt for LLM to detect overlaps."""

        return f"""You are analyzing IT due diligence data for an M&A transaction.

Your task: Identify meaningful overlaps between the TARGET company and BUYER company in the {domain.upper()} domain.

IMPORTANT RULES:
1. Only create overlaps where there is a SPECIFIC comparison to make
2. Generic observations like "both have IT systems" are NOT overlaps
3. Each overlap must cite specific facts from both target AND buyer
4. Empty list is OK if no meaningful overlaps exist

VALID OVERLAP TYPES FOR {domain.upper()}:
{chr(10).join(['- ' + t for t in overlap_types])}

{target_inventory}

{"="*70}

{buyer_inventory}

{"="*70}

OUTPUT FORMAT (JSON array of overlap objects):

[
  {{
    "overlap_type": "<one of the types above>",
    "target_fact_ids": ["F-TGT-XXX-001", "F-TGT-XXX-002"],
    "buyer_fact_ids": ["F-BYR-XXX-001"],
    "target_summary": "Brief description of target's position",
    "buyer_summary": "Brief description of buyer's position",
    "why_it_matters": "Specific integration implication or decision this creates",
    "confidence": 0.85,
    "missing_info_questions": ["Optional: what else would help assess this overlap?"]
  }}
]

EXAMPLES OF GOOD OVERLAPS:
- Platform mismatch: "Target uses SAP, Buyer uses Oracle" (ERP consolidation decision)
- Platform alignment: "Both use AWS us-east-1" (synergy opportunity)
- Capability gap: "Target has no SIEM, Buyer has Splunk" (security uplift needed)
- Version gap: "Target on Windows Server 2012, Buyer on 2022" (modernization needed)

EXAMPLES OF BAD OVERLAPS (don't create these):
- "Both companies have applications" (too generic)
- "Integration will be needed" (not specific)
- "Target is smaller than buyer" (obvious, not actionable)

Now analyze the inventories above and return a JSON array of overlap objects.

Return ONLY the JSON array, no other text.
"""

    def _call_llm_for_overlap_detection(
        self,
        prompt: str,
        domain: str
    ) -> List[OverlapCandidate]:
        """Call Anthropic API to detect overlaps with structured output."""

        response = self.client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=4000,
            temperature=0.3,  # Lower temp for more consistent output
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )

        # Extract response text
        response_text = response.content[0].text.strip()

        # Strip markdown code blocks if present
        if response_text.startswith("```json"):
            response_text = response_text[7:]  # Remove ```json
        if response_text.startswith("```"):
            response_text = response_text[3:]  # Remove ```
        if response_text.endswith("```"):
            response_text = response_text[:-3]  # Remove ```
        response_text = response_text.strip()

        # Parse JSON response
        try:
            overlap_dicts = json.loads(response_text)
        except json.JSONDecodeError as e:
            print(f"[ERROR] Failed to parse overlap JSON for {domain}: {e}")
            print(f"Response was: {response_text[:500]}")
            return []

        # Convert to OverlapCandidate objects
        overlaps = []
        for i, overlap_dict in enumerate(overlap_dicts):
            try:
                # Generate overlap ID
                overlap_id = f"OVL-{domain.upper()[:3]}-{i+1:03d}"

                # Create OverlapCandidate
                overlap = OverlapCandidate(
                    overlap_id=overlap_id,
                    domain=domain,
                    overlap_type=overlap_dict["overlap_type"],
                    target_fact_ids=overlap_dict["target_fact_ids"],
                    buyer_fact_ids=overlap_dict["buyer_fact_ids"],
                    target_summary=overlap_dict["target_summary"],
                    buyer_summary=overlap_dict["buyer_summary"],
                    why_it_matters=overlap_dict["why_it_matters"],
                    confidence=float(overlap_dict.get("confidence", 0.75)),
                    missing_info_questions=overlap_dict.get("missing_info_questions", [])
                )

                # Validate
                errors = overlap.validate()
                if errors:
                    print(f"[WARNING] Overlap validation errors: {errors}")
                    continue  # Skip invalid overlaps

                overlaps.append(overlap)

            except (KeyError, ValueError) as e:
                print(f"[ERROR] Failed to create OverlapCandidate: {e}")
                print(f"Overlap dict: {overlap_dict}")
                continue

        return overlaps

    def generate_overlap_map_all_domains(
        self,
        facts_by_domain: Dict[str, Dict[str, List[Dict]]]
    ) -> Dict[str, List[OverlapCandidate]]:
        """
        Generate overlaps for all domains.

        Args:
            facts_by_domain: Dict structure:
                {
                    "applications": {
                        "target": [fact1, fact2, ...],
                        "buyer": [fact1, fact2, ...]
                    },
                    "infrastructure": { ... },
                    ...
                }

        Returns:
            Dict of domain -> List[OverlapCandidate]
        """
        overlaps_by_domain = {}

        for domain in ALL_DOMAINS:
            if domain == "cross-domain":
                continue  # Skip cross-domain for now

            domain_facts = facts_by_domain.get(domain, {})
            target_facts = domain_facts.get("target", [])
            buyer_facts = domain_facts.get("buyer", [])

            print(f"[OVERLAP GEN] {domain}: {len(target_facts)} target facts, {len(buyer_facts)} buyer facts")

            overlaps = self.generate_overlap_map_for_domain(
                domain=domain,
                target_facts=target_facts,
                buyer_facts=buyer_facts
            )

            print(f"[OVERLAP GEN] {domain}: Generated {len(overlaps)} overlaps")

            overlaps_by_domain[domain] = overlaps

        return overlaps_by_domain

    def save_overlaps_to_file(
        self,
        overlaps_by_domain: Dict[str, List[OverlapCandidate]],
        output_path: str
    ) -> None:
        """Save overlap map to JSON file."""

        # Convert to serializable format
        output = {}
        for domain, overlaps in overlaps_by_domain.items():
            output[domain] = [asdict(overlap) for overlap in overlaps]

        # Write to file
        with open(output_path, 'w') as f:
            json.dump(output, f, indent=2)

        # Print summary
        total_overlaps = sum(len(overlaps) for overlaps in overlaps_by_domain.values())
        print(f"\n[OVERLAP MAP] Saved {total_overlaps} overlaps across {len(overlaps_by_domain)} domains")
        print(f"[OVERLAP MAP] Output: {output_path}")

        # Print breakdown
        for domain, overlaps in overlaps_by_domain.items():
            if overlaps:
                print(f"  - {domain}: {len(overlaps)} overlaps")


# Convenience function for testing
def generate_and_save_overlaps(
    facts_by_domain: Dict[str, Dict[str, List[Dict]]],
    output_path: str
) -> Dict[str, List[OverlapCandidate]]:
    """
    Generate overlaps for all domains and save to file.

    This is the main entry point for the overlap generation pipeline stage.
    """
    generator = OverlapGenerator()
    overlaps = generator.generate_overlap_map_all_domains(facts_by_domain)
    generator.save_overlaps_to_file(overlaps, output_path)
    return overlaps
