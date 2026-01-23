"""
Analysis Runner - Connects web app to the analysis pipeline.

This module bridges the Flask web interface with the V2 analysis pipeline.
Includes robust error handling and fallback modes.
"""

import sys
import traceback
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Callable, List
from datetime import datetime

# Add parent directory for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from web.task_manager import AnalysisTask, AnalysisPhase, TaskStatus

# Configure logging (Point 111: Replace print statements)
logger = logging.getLogger(__name__)


def check_pipeline_availability() -> Dict[str, Any]:
    """
    Check which pipeline components are available.

    Returns dict with availability status for each component.
    """
    status = {
        'api_key': False,
        'discovery_agents': False,
        'reasoning_agents': False,
        'fact_store': False,
        'pdf_parser': False,
        'errors': []
    }

    # Check API key
    try:
        from config_v2 import ANTHROPIC_API_KEY
        status['api_key'] = bool(ANTHROPIC_API_KEY)
    except Exception as e:
        status['errors'].append(f'Config error: {e}')

    # Check fact store
    try:
        from tools_v2.fact_store import FactStore
        status['fact_store'] = True
    except Exception as e:
        status['errors'].append(f'FactStore: {e}')

    # Check PDF parser
    try:
        from ingestion.pdf_parser import parse_documents
        status['pdf_parser'] = True
    except Exception as e:
        status['errors'].append(f'PDF parser: {e}')

    # Check discovery agents
    try:
        from agents_v2.discovery.infrastructure_discovery import InfrastructureDiscoveryAgent
        status['discovery_agents'] = True
    except Exception as e:
        status['errors'].append(f'Discovery agents: {e}')

    # Check reasoning agents
    try:
        from agents_v2.reasoning.infrastructure_reasoning import InfrastructureReasoningAgent
        status['reasoning_agents'] = True
    except Exception as e:
        status['errors'].append(f'Reasoning agents: {e}')

    return status


def run_analysis(task: AnalysisTask, progress_callback: Callable) -> Dict[str, Any]:
    """
    Run the full analysis pipeline.

    Args:
        task: The analysis task with file paths and configuration
        progress_callback: Callback to report progress updates

    Returns:
        Dict with result file paths
    """
    from config_v2 import (
        FACTS_DIR, FINDINGS_DIR, OUTPUT_DIR, ensure_directories,
        DOMAINS, ANTHROPIC_API_KEY
    )
    from ingestion.pdf_parser import parse_documents
    from interactive.session import Session

    # Ensure output directories exist
    ensure_directories()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Initialize progress
    progress_callback({
        "phase": AnalysisPhase.INITIALIZING,
        "total_documents": len(task.file_paths),
        "documents_processed": 0,
    })

    # Check for API key
    if not ANTHROPIC_API_KEY:
        raise ValueError("ANTHROPIC_API_KEY not configured. Set it in .env file or environment.")

    # Create session
    session = Session()

    # Add deal context - properly populate the dict for reasoning agents
    deal_context = task.deal_context or {}
    session.deal_context = {
        'deal_type': deal_context.get('deal_type', 'bolt_on'),
        'target_name': deal_context.get('target_name', 'Target Company'),
        'industry': deal_context.get('industry', ''),
        'sub_industry': deal_context.get('sub_industry', ''),
        'employee_count': deal_context.get('employee_count', ''),
    }

    # Build DealContext object for rich prompt context
    from tools_v2.session import DealContext as DealContextClass
    dc = DealContextClass(
        target_name=deal_context.get('target_name', 'Target Company'),
        deal_type=deal_context.get('deal_type', 'bolt_on'),
        industry=deal_context.get('industry') or None,
        sub_industry=deal_context.get('sub_industry') or None,
        industry_confirmed=True,  # User selected it
    )
    # Add the formatted prompt context for reasoning agents
    # This includes both deal_type and industry context in text form
    session.deal_context['_prompt_context'] = dc.to_prompt_context()

    # Phase 1: Parse documents
    progress_callback({
        "phase": AnalysisPhase.PARSING_DOCUMENTS,
    })

    file_paths = [Path(f) for f in task.file_paths]
    documents = parse_documents(file_paths)

    progress_callback({
        "documents_processed": len(documents),
        "total_documents": len(documents),
    })

    if not documents:
        raise ValueError("No documents could be parsed from the uploaded files.")

    # Combine document content for analysis
    combined_content = "\n\n---\n\n".join([
        f"## Document: {doc.get('filename', 'Unknown')}\n\n{doc.get('content', '')}"
        for doc in documents
    ])

    # Determine which domains to analyze
    domains_to_analyze = task.domains if task.domains else DOMAINS

    # Phase 2: Run Discovery Agents
    discovery_results = {}
    discovery_phases = {
        "infrastructure": AnalysisPhase.DISCOVERY_INFRASTRUCTURE,
        "network": AnalysisPhase.DISCOVERY_NETWORK,
        "cybersecurity": AnalysisPhase.DISCOVERY_CYBERSECURITY,
        "applications": AnalysisPhase.DISCOVERY_APPLICATIONS,
        "identity_access": AnalysisPhase.DISCOVERY_IDENTITY,
        "organization": AnalysisPhase.DISCOVERY_ORGANIZATION,
    }

    for domain in domains_to_analyze:
        if task._cancelled:
            return {}

        phase = discovery_phases.get(domain, AnalysisPhase.DISCOVERY_INFRASTRUCTURE)
        progress_callback({"phase": phase})

        try:
            facts, gaps = run_discovery_for_domain(domain, combined_content, session)
            discovery_results[domain] = {"facts": facts, "gaps": gaps}

            # Update counts
            progress_callback({
                "facts_extracted": len(session.fact_store.facts),
            })
        except Exception as e:
            # Log error but continue with other domains
            logger.error(f"Error in {domain} discovery: {e}")

    # Phase 3: Run Reasoning Agents
    progress_callback({"phase": AnalysisPhase.REASONING})

    for domain in domains_to_analyze:
        if task._cancelled:
            return {}

        try:
            run_reasoning_for_domain(domain, session)

            progress_callback({
                "risks_identified": len(session.reasoning_store.risks),
                "work_items_created": len(session.reasoning_store.work_items),
            })
        except Exception as e:
            logger.error(f"Error in {domain} reasoning: {e}")

    # Phase 4: Synthesis
    progress_callback({"phase": AnalysisPhase.SYNTHESIS})

    # Run cross-domain consistency and narrative synthesis if available
    try:
        run_synthesis(session)
    except Exception as e:
        logger.error(f"Error in synthesis: {e}")

    # Generate open questions based on industry and gaps
    open_questions = []
    try:
        from tools_v2.open_questions import generate_open_questions_for_deal
        open_questions = generate_open_questions_for_deal(
            industry=deal_context.get('industry'),
            sub_industry=deal_context.get('sub_industry'),
            deal_type=deal_context.get('deal_type', 'bolt_on'),
            gaps=list(session.fact_store.gaps)
        )
        logger.info(f"Generated {len(open_questions)} open questions for deal team")
    except Exception as e:
        logger.error(f"Error generating open questions: {e}")

    # Phase 5: Finalize and save
    progress_callback({"phase": AnalysisPhase.FINALIZING})

    # Save results - session.save_to_files returns dict with actual saved paths
    saved_files = session.save_to_files(OUTPUT_DIR, timestamp)

    # Save open questions separately
    if open_questions:
        import json
        questions_file = OUTPUT_DIR / f"open_questions_{timestamp}.json"
        with open(questions_file, 'w') as f:
            json.dump(open_questions, f, indent=2)
        saved_files['open_questions'] = questions_file

    # Get the actual saved file paths from the saved_files dict
    facts_file = saved_files.get('facts')
    findings_file = saved_files.get('findings')

    # Create result summary
    result = {
        "facts_file": str(facts_file) if facts_file else None,
        "findings_file": str(findings_file) if findings_file else None,
        "open_questions_file": str(saved_files.get('open_questions')) if saved_files.get('open_questions') else None,
        "result_path": str(OUTPUT_DIR),
        "timestamp": timestamp,
        "summary": {
            "facts_count": len(session.fact_store.facts),
            "gaps_count": len(session.fact_store.gaps),
            "risks_count": len(session.reasoning_store.risks),
            "work_items_count": len(session.reasoning_store.work_items),
            "open_questions_count": len(open_questions),
        }
    }

    progress_callback({"phase": AnalysisPhase.COMPLETE})

    return result


def run_discovery_for_domain(domain: str, content: str, session) -> tuple:
    """Run discovery agent for a specific domain."""
    from tools_v2.fact_store import FactStore
    from config_v2 import ANTHROPIC_API_KEY

    # Import the appropriate discovery agent
    # Note: Support both "identity" and "identity_access" for compatibility
    agent_map = {
        "infrastructure": "agents_v2.discovery.infrastructure_discovery",
        "network": "agents_v2.discovery.network_discovery",
        "cybersecurity": "agents_v2.discovery.cybersecurity_discovery",
        "applications": "agents_v2.discovery.applications_discovery",
        "identity_access": "agents_v2.discovery.identity_access_discovery",
        "identity": "agents_v2.discovery.identity_access_discovery",  # Alias
        "organization": "agents_v2.discovery.organization_discovery",
    }

    agent_classes = {
        "infrastructure": "InfrastructureDiscoveryAgent",
        "network": "NetworkDiscoveryAgent",
        "cybersecurity": "CybersecurityDiscoveryAgent",
        "applications": "ApplicationsDiscoveryAgent",
        "identity_access": "IdentityAccessDiscoveryAgent",
        "identity": "IdentityAccessDiscoveryAgent",  # Alias
        "organization": "OrganizationDiscoveryAgent",
    }

    module_name = agent_map.get(domain)
    class_name = agent_classes.get(domain)

    if not module_name or not class_name:
        logger.warning(f"Unknown domain '{domain}' - skipping discovery")
        return [], []

    logger.info(f"Starting discovery for domain: {domain}")

    try:
        import importlib
        module = importlib.import_module(module_name)
        agent_class = getattr(module, class_name)

        # Get target name from deal context (handle both dict and string)
        target_name = 'Target Company'
        if session.deal_context:
            if isinstance(session.deal_context, dict):
                target_name = session.deal_context.get('target_name', 'Target Company')
            elif isinstance(session.deal_context, str):
                target_name = session.deal_context

        # Create and run agent with required arguments
        agent = agent_class(
            fact_store=session.fact_store,
            api_key=ANTHROPIC_API_KEY,
            target_name=target_name
        )

        logger.info(f"Running {domain} discovery agent...")
        result = agent.discover(content)
        logger.info(f"Discovery complete for {domain}: {len(session.fact_store.facts)} facts, {len(session.fact_store.gaps)} gaps")

        # Facts and gaps are stored directly in the fact_store by the agent
        facts = list(session.fact_store.facts)
        gaps = list(session.fact_store.gaps)

        return facts, gaps

    except ImportError as e:
        logger.warning(f"Could not import discovery agent for {domain}: {e}")
        return [], []
    except Exception as e:
        logger.error(f"Error running discovery for {domain}: {e}")
        return [], []


def run_reasoning_for_domain(domain: str, session) -> None:
    """Run reasoning agent for a specific domain."""
    from config_v2 import ANTHROPIC_API_KEY

    agent_map = {
        "infrastructure": "agents_v2.reasoning.infrastructure_reasoning",
        "network": "agents_v2.reasoning.network_reasoning",
        "cybersecurity": "agents_v2.reasoning.cybersecurity_reasoning",
        "applications": "agents_v2.reasoning.applications_reasoning",
        "identity_access": "agents_v2.reasoning.identity_access_reasoning",
        "identity": "agents_v2.reasoning.identity_access_reasoning",  # Alias
        "organization": "agents_v2.reasoning.organization_reasoning",
    }

    agent_classes = {
        "infrastructure": "InfrastructureReasoningAgent",
        "network": "NetworkReasoningAgent",
        "cybersecurity": "CybersecurityReasoningAgent",
        "applications": "ApplicationsReasoningAgent",
        "identity_access": "IdentityAccessReasoningAgent",
        "identity": "IdentityAccessReasoningAgent",  # Alias
        "organization": "OrganizationReasoningAgent",
    }

    module_name = agent_map.get(domain)
    class_name = agent_classes.get(domain)

    if not module_name or not class_name:
        return

    try:
        import importlib
        module = importlib.import_module(module_name)
        agent_class = getattr(module, class_name)

        # Get facts for this domain
        domain_facts = [f for f in session.fact_store.facts if f.domain == domain]

        # Create and run agent with required arguments
        agent = agent_class(
            fact_store=session.fact_store,
            api_key=ANTHROPIC_API_KEY
        )
        result = agent.reason(session.deal_context)

        # Get the reasoning store from the agent
        reasoning_store = agent.get_reasoning_store()

        # Extract all findings from agent's reasoning store
        risks = list(reasoning_store.risks)
        work_items = list(reasoning_store.work_items)
        strategic_considerations = list(reasoning_store.strategic_considerations)
        recommendations = list(reasoning_store.recommendations)

        # Add to session stores (convert objects to kwargs via to_dict())
        for risk in risks:
            # Skip the finding_id as add_risk generates its own
            risk_dict = {k: v for k, v in risk.__dict__.items() if k != 'finding_id'}
            try:
                session.reasoning_store.add_risk(**risk_dict)
            except Exception as e:
                logger.warning(f"Failed to add risk: {e}")

        for wi in work_items:
            wi_dict = {k: v for k, v in wi.__dict__.items() if k != 'finding_id'}
            try:
                session.reasoning_store.add_work_item(**wi_dict)
            except Exception as e:
                logger.warning(f"Failed to add work item: {e}")

        for sc in strategic_considerations:
            sc_dict = {k: v for k, v in sc.__dict__.items() if k != 'finding_id'}
            try:
                session.reasoning_store.add_strategic_consideration(**sc_dict)
            except Exception as e:
                logger.warning(f"Failed to add strategic consideration: {e}")

        for rec in recommendations:
            rec_dict = {k: v for k, v in rec.__dict__.items() if k != 'finding_id'}
            try:
                session.reasoning_store.add_recommendation(**rec_dict)
            except Exception as e:
                logger.warning(f"Failed to add recommendation: {e}")

    except ImportError as e:
        logger.warning(f"Could not import reasoning agent for {domain}: {e}")
    except Exception as e:
        logger.error(f"Error running reasoning for {domain}: {e}")


def run_synthesis(session) -> None:
    """Run cross-domain synthesis."""
    try:
        from agents_v2.narrative.narrative_synthesis import NarrativeSynthesisAgent

        agent = NarrativeSynthesisAgent()
        agent.run(session)
    except ImportError:
        # Narrative synthesis not available
        pass
    except Exception as e:
        logger.error(f"Error in synthesis: {e}")


def run_analysis_simple(task: AnalysisTask, progress_callback: Callable) -> Dict[str, Any]:
    """
    Simplified analysis runner for testing/demo.

    Uses direct API calls instead of full agent infrastructure.
    Good for when agent modules have import issues.
    """
    from config_v2 import (
        FACTS_DIR, FINDINGS_DIR, OUTPUT_DIR, ensure_directories,
        ANTHROPIC_API_KEY
    )
    from ingestion.pdf_parser import parse_documents
    from interactive.session import Session

    ensure_directories()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Initialize
    progress_callback({
        "phase": AnalysisPhase.INITIALIZING,
        "total_documents": len(task.file_paths),
    })

    if not ANTHROPIC_API_KEY:
        raise ValueError("ANTHROPIC_API_KEY not configured")

    session = Session()

    # Parse documents
    progress_callback({"phase": AnalysisPhase.PARSING_DOCUMENTS})

    file_paths = [Path(f) for f in task.file_paths]
    documents = parse_documents(file_paths)

    if not documents:
        raise ValueError("No documents could be parsed")

    progress_callback({
        "documents_processed": len(documents),
        "total_documents": len(documents),
    })

    # Combine content
    combined_content = "\n\n".join([
        f"[{doc.get('filename', 'Unknown')}]\n{doc.get('content', '')}"
        for doc in documents
    ])

    # Run discovery via direct API call
    progress_callback({"phase": AnalysisPhase.DISCOVERY_INFRASTRUCTURE})

    try:
        from tools_v2.discovery_tools import extract_facts_from_content
        facts, gaps = extract_facts_from_content(combined_content, task.domains or ["infrastructure"])

        for fact in facts:
            session.fact_store.add_fact(fact)
        for gap in gaps:
            session.fact_store.add_gap(gap)

        progress_callback({"facts_extracted": len(facts)})

    except ImportError:
        # Use minimal extraction if tools not available
        pass

    # Run reasoning
    progress_callback({"phase": AnalysisPhase.REASONING})

    try:
        from tools_v2.reasoning_tools import generate_findings
        risks, work_items = generate_findings(list(session.fact_store.facts))

        for risk in risks:
            session.reasoning_store.add_risk(risk)
        for wi in work_items:
            session.reasoning_store.add_work_item(wi)

        progress_callback({
            "risks_identified": len(risks),
            "work_items_created": len(work_items),
        })

    except ImportError:
        pass

    # Save results
    progress_callback({"phase": AnalysisPhase.FINALIZING})

    saved_files = session.save_to_files(OUTPUT_DIR, timestamp)

    # Get the actual saved file paths from the saved_files dict
    facts_file = saved_files.get('facts')
    findings_file = saved_files.get('findings')

    result = {
        "facts_file": str(facts_file) if facts_file else None,
        "findings_file": str(findings_file) if findings_file else None,
        "result_path": str(OUTPUT_DIR),
        "timestamp": timestamp,
        "summary": {
            "facts_count": len(session.fact_store.facts),
            "gaps_count": len(session.fact_store.gaps),
            "risks_count": len(session.reasoning_store.risks),
            "work_items_count": len(session.reasoning_store.work_items),
        }
    }

    progress_callback({"phase": AnalysisPhase.COMPLETE})

    return result
