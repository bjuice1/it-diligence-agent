"""
Network Reasoning Agent

Analyzes network facts and produces findings with fact citations.
"""

from agents_v2.base_reasoning_agent import BaseReasoningAgent
from prompts.v2_network_reasoning_prompt import NETWORK_REASONING_PROMPT


class NetworkReasoningAgent(BaseReasoningAgent):
    """
    Network reasoning agent.

    Analyzes facts about WAN, LAN, remote access, DNS/DHCP,
    load balancing, and network security to identify:
    - Network risks (single points of failure, capacity, obsolescence)
    - Strategic considerations (connectivity requirements, TSA needs)
    - Integration work items (network migrations, consolidation)
    - Recommendations for the deal team

    Every finding cites supporting facts from the FactStore.
    """

    @property
    def domain(self) -> str:
        return "network"

    @property
    def system_prompt(self) -> str:
        return NETWORK_REASONING_PROMPT
