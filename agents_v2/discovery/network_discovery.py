"""
Network Discovery Agent

Extracts network facts from IT documentation.
Categories: wan, lan, remote_access, dns_dhcp, load_balancing, network_security, monitoring
"""

from typing import List
from agents_v2.base_discovery_agent import BaseDiscoveryAgent
from prompts.v2_network_discovery_prompt import NETWORK_DISCOVERY_PROMPT


class NetworkDiscoveryAgent(BaseDiscoveryAgent):
    """
    Network discovery agent.

    Extracts structured facts about:
    - WAN connectivity and circuits
    - LAN architecture and switching
    - Remote access and VPN
    - DNS and DHCP services
    - Load balancing
    - Network security (firewalls, segmentation)
    - Network monitoring and management
    """

    @property
    def domain(self) -> str:
        return "network"

    @property
    def system_prompt(self) -> str:
        return NETWORK_DISCOVERY_PROMPT

    @property
    def inventory_categories(self) -> List[str]:
        return [
            "wan",
            "lan",
            "remote_access",
            "dns_dhcp",
            "load_balancing",
            "network_security",
            "monitoring"
        ]
