"""
Prompts Module

System prompts for domain-specific analysis agents.
Includes the Four-Lens DD Reasoning Framework.
"""
from .dd_reasoning_framework import (
    DD_FOUR_LENS_FRAMEWORK,
    CURRENT_STATE_GUIDANCE,
    RISK_IDENTIFICATION_GUIDANCE,
    STRATEGIC_CONSIDERATION_GUIDANCE,
    WORK_ITEM_GUIDANCE,
    get_framework_prompt,
    get_full_guidance
)
from .infrastructure_prompt import INFRASTRUCTURE_SYSTEM_PROMPT
from .network_prompt import NETWORK_SYSTEM_PROMPT
from .cybersecurity_prompt import CYBERSECURITY_SYSTEM_PROMPT
from .coordinator_prompt import COORDINATOR_SYSTEM_PROMPT

__all__ = [
    # Framework
    'DD_FOUR_LENS_FRAMEWORK',
    'CURRENT_STATE_GUIDANCE',
    'RISK_IDENTIFICATION_GUIDANCE',
    'STRATEGIC_CONSIDERATION_GUIDANCE',
    'WORK_ITEM_GUIDANCE',
    'get_framework_prompt',
    'get_full_guidance',
    # Domain prompts
    'INFRASTRUCTURE_SYSTEM_PROMPT',
    'NETWORK_SYSTEM_PROMPT',
    'CYBERSECURITY_SYSTEM_PROMPT',
    'COORDINATOR_SYSTEM_PROMPT'
]
