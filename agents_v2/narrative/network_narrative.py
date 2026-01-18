"""Network Narrative Agent for Investment Thesis."""

from .base_narrative_agent import BaseNarrativeAgent


class NetworkNarrativeAgent(BaseNarrativeAgent):
    """Generates network domain narrative for investment thesis."""

    @property
    def domain(self) -> str:
        return "network"

    @property
    def domain_title(self) -> str:
        return "Network"

    @property
    def narrative_guidance(self) -> str:
        return """NETWORK NARRATIVE GUIDANCE:

Focus on:
- Network topology - is it documented? Do we understand the architecture?
- WAN/MPLS/SD-WAN - how are sites connected and at what cost?
- Security segmentation - is there proper network isolation?
- Remote access - VPN, ZTNA, or open access?
- Internet egress - where does traffic flow and how is it secured?

Key questions the buyer wants answered:
1. Do we actually understand the network architecture?
2. Are there single points of failure?
3. What's the bandwidth capacity and is it sufficient?
4. Can we integrate this network with ours, or is it a full rip-and-replace?

Common "So What" patterns:
- "Network architecture undocumented. Major blind spot for integration planning."
- "SD-WAN deployed but no segmentation. Security uplift required."
- "Traditional MPLS with high costs. SD-WAN migration opportunity."
- "Well-documented network with clear integration path."

If documentation is missing, say so directly. "We don't have visibility into network segmentation.
This is a critical gap that needs resolution before Day 1 planning can proceed."

Network is often the least documented area. Call out gaps explicitly."""
