"""
Narrative Service for Report View Toggle.

Provides on-demand narrative generation for each domain,
leveraging existing narrative agents.
"""

import logging
from typing import Dict, Any, Optional
from dataclasses import asdict

logger = logging.getLogger(__name__)

# Domain to agent class mapping
DOMAIN_AGENTS = {
    "applications": ("agents_v2.narrative.applications_narrative", "ApplicationsNarrativeAgent"),
    "infrastructure": ("agents_v2.narrative.infrastructure_narrative", "InfrastructureNarrativeAgent"),
    "organization": ("agents_v2.narrative.organization_narrative", "OrganizationNarrativeAgent"),
    "cybersecurity": ("agents_v2.narrative.cybersecurity_narrative", "CybersecurityNarrativeAgent"),
    "network": ("agents_v2.narrative.network_narrative", "NetworkNarrativeAgent"),
    "identity_access": ("agents_v2.narrative.identity_narrative", "IdentityNarrativeAgent"),
}

# Cache for generated narratives (per session)
_narrative_cache: Dict[str, Dict[str, Any]] = {}


def get_cached_narrative(session_id: str, domain: str) -> Optional[Dict[str, Any]]:
    """Get cached narrative if available."""
    cache_key = f"{session_id}:{domain}"
    return _narrative_cache.get(cache_key)


def cache_narrative(session_id: str, domain: str, narrative: Dict[str, Any]) -> None:
    """Cache a generated narrative."""
    cache_key = f"{session_id}:{domain}"
    _narrative_cache[cache_key] = narrative


def clear_narrative_cache(session_id: str, domain: Optional[str] = None) -> None:
    """Clear narrative cache for a session (optionally for specific domain)."""
    if domain:
        cache_key = f"{session_id}:{domain}"
        _narrative_cache.pop(cache_key, None)
    else:
        # Clear all for this session
        keys_to_remove = [k for k in _narrative_cache if k.startswith(f"{session_id}:")]
        for key in keys_to_remove:
            _narrative_cache.pop(key, None)


def generate_domain_narrative(
    domain: str,
    fact_store,
    reasoning_store,
    api_key: str,
    force_regenerate: bool = False,
    session_id: str = ""
) -> Dict[str, Any]:
    """
    Generate narrative for a domain using the appropriate narrative agent.

    Args:
        domain: Domain name (applications, infrastructure, etc.)
        fact_store: FactStore with extracted facts
        reasoning_store: ReasoningStore with risks and work items
        api_key: Anthropic API key
        force_regenerate: If True, bypass cache
        session_id: Session ID for caching

    Returns:
        Dict with narrative content:
        {
            "so_what": str,
            "considerations": List[str],
            "narrative": str,
            "cost_summary": str,
            "key_facts": List[str],
            "confidence": str,
            "domain": str,
            "status": "success" | "error",
            "error": str (if error)
        }
    """
    # Check cache first
    if not force_regenerate and session_id:
        cached = get_cached_narrative(session_id, domain)
        if cached:
            logger.info(f"Returning cached narrative for {domain}")
            return cached

    # Validate domain
    if domain not in DOMAIN_AGENTS:
        return {
            "status": "error",
            "error": f"Unknown domain: {domain}. Valid domains: {list(DOMAIN_AGENTS.keys())}",
            "domain": domain
        }

    # Check if we have facts for this domain
    domain_facts = [f for f in fact_store.facts if f.domain == domain]
    if not domain_facts:
        return {
            "status": "error",
            "error": f"No facts found for {domain} domain. Run analysis first.",
            "domain": domain
        }

    try:
        # Import the appropriate agent
        module_path, class_name = DOMAIN_AGENTS[domain]
        module = __import__(module_path, fromlist=[class_name])
        AgentClass = getattr(module, class_name)

        # Create narrative store for this generation
        from tools_v2.narrative_tools import NarrativeStore
        narrative_store = NarrativeStore()

        # Initialize and run the agent
        agent = AgentClass(
            fact_store=fact_store,
            reasoning_store=reasoning_store,
            narrative_store=narrative_store,
            api_key=api_key
        )

        logger.info(f"Generating narrative for {domain}...")
        result = agent.generate()

        if result:
            narrative_dict = {
                "status": "success",
                "domain": domain,
                "so_what": result.so_what or "",
                "considerations": result.considerations or [],
                "narrative": result.narrative or "",
                "cost_summary": result.cost_summary or "",
                "key_facts": result.key_facts or [],
                "confidence": result.confidence or "medium",
                "sources": result.sources or []
            }

            # Cache the result
            if session_id:
                cache_narrative(session_id, domain, narrative_dict)

            return narrative_dict
        else:
            return {
                "status": "error",
                "error": "Narrative generation returned no result",
                "domain": domain
            }

    except ImportError as e:
        logger.error(f"Failed to import narrative agent for {domain}: {e}")
        return {
            "status": "error",
            "error": f"Narrative agent not available for {domain}",
            "domain": domain
        }
    except Exception as e:
        logger.error(f"Error generating narrative for {domain}: {e}")
        return {
            "status": "error",
            "error": str(e),
            "domain": domain
        }


def get_placeholder_narrative(domain: str) -> Dict[str, Any]:
    """Return a placeholder narrative when no data is available."""
    return {
        "status": "placeholder",
        "domain": domain,
        "so_what": f"No {domain} analysis has been run yet.",
        "considerations": [
            "Upload documents and run analysis to generate narrative",
            "The narrative will summarize key findings for the due diligence report"
        ],
        "narrative": f"Once you upload documents and run the analysis, this section will contain a narrative summary of the {domain} landscape, including key findings, risks, and recommendations for the due diligence report.",
        "cost_summary": "",
        "key_facts": [],
        "confidence": "low"
    }
