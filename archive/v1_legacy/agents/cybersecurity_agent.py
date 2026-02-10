"""
Cybersecurity Domain Agent

Analyzes security posture through multiple lenses:
- Identity & Access Management
- Vulnerability Management
- Compliance & Regulatory
- Data Security & Privacy
- Security Operations & Incident Response
"""
from agents.base_agent import BaseAgent
from prompts.cybersecurity_prompt import CYBERSECURITY_SYSTEM_PROMPT


class CybersecurityAgent(BaseAgent):
    """
    Specialized agent for cybersecurity domain analysis.
    
    Applies systematic analysis through:
    1. Identity & Access Management (IAM, MFA, SSO, privileged access)
    2. Vulnerability Management (patching, scanning, remediation)
    3. Compliance & Regulatory (SOC2, PCI, HIPAA, CMMC, etc.)
    4. Data Security (encryption, DLP, classification)
    5. Security Operations (SIEM, SOC, incident response)
    """
    
    @property
    def domain(self) -> str:
        return "cybersecurity"
    
    @property
    def system_prompt(self) -> str:
        return CYBERSECURITY_SYSTEM_PROMPT
