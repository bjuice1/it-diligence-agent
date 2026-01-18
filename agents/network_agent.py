"""
Network Domain Agent

Analyzes network infrastructure through multiple lenses:
- WAN/MPLS/SD-WAN Analysis
- LAN/VLAN Architecture
- DNS/DHCP/IP Management
- Firewall & Security Zones
- Connectivity & Integration
"""
from agents.base_agent import BaseAgent
from prompts.network_prompt import NETWORK_SYSTEM_PROMPT


class NetworkAgent(BaseAgent):
    """
    Specialized agent for network domain analysis.
    
    Applies systematic analysis through:
    1. WAN Connectivity (MPLS, SD-WAN, internet, circuits)
    2. LAN Architecture (switching, VLANs, segmentation)
    3. DNS/DHCP/IP Management (addressing, conflicts, DNS zones)
    4. Perimeter Security (firewalls, DMZ, security zones)
    5. Integration Planning (connectivity to buyer, cutover planning)
    """
    
    @property
    def domain(self) -> str:
        return "network"
    
    @property
    def system_prompt(self) -> str:
        return NETWORK_SYSTEM_PROMPT
