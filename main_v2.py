#!/usr/bin/env python3
"""
IT Due Diligence Agent V2 - Main Entry Point

V2 Architecture: Discovery → Reasoning → Synthesis
- Phase 1: Discovery agents extract facts (Haiku model)
- Phase 2: Reasoning agents analyze facts (Sonnet model)
- Phase 3: Coverage analysis (quality scoring)
- Phase 4: Synthesis (cross-domain consistency)
- Phase 5: VDR generation (follow-up requests)

Usage:
    # Full pipeline (discovery + reasoning + synthesis)
    python main_v2.py data/input/

    # Discovery only (extract facts)
    python main_v2.py data/input/ --discovery-only

    # Reasoning only (from existing facts file)
    python main_v2.py --from-facts output/facts/facts_20240115_120000.json

    # Single domain (for testing)
    python main_v2.py data/input/ --domain infrastructure

    # Skip VDR generation
    python main_v2.py data/input/ --no-vdr

    # Interactive mode - enter shell after analysis
    python main_v2.py data/input/ --interactive

    # Interactive mode - load existing outputs (no new analysis)
    python main_v2.py --interactive-only
"""

import argparse
import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

# V2 imports
from config_v2 import (
    ANTHROPIC_API_KEY,
    DISCOVERY_MODEL,
    REASONING_MODEL,
    DISCOVERY_MAX_TOKENS,
    REASONING_MAX_TOKENS,
    DISCOVERY_MAX_ITERATIONS,
    REASONING_MAX_ITERATIONS,
    OUTPUT_DIR,
    FACTS_DIR,
    FINDINGS_DIR,
    DOMAINS,
    MAX_PARALLEL_AGENTS,
    PARALLEL_DISCOVERY,
    PARALLEL_REASONING,
    estimate_cost
)
from stores.fact_store import FactStore
from stores.inventory_store import InventoryStore
from tools_v2.reasoning_tools import ReasoningStore
from tools_v2.session import DDSession
from tools_v2.coverage import CoverageAnalyzer
from tools_v2.vdr_generator import VDRGenerator
from tools_v2.synthesis import SynthesisAnalyzer
from tools_v2.html_report import generate_html_report
from tools_v2.presentation import generate_presentation, generate_presentation_from_narratives
from tools_v2.narrative_tools import NarrativeStore
from tools_v2.excel_export import export_to_excel, OPENPYXL_AVAILABLE
from tools_v2.inventory_integration import (
    promote_facts_to_inventory,
    reconcile_facts_and_inventory,
    generate_inventory_audit,
    save_inventory_audit,
)
from agents_v2.discovery import DISCOVERY_AGENTS
from agents_v2.reasoning import REASONING_AGENTS
from agents_v2.narrative import NARRATIVE_AGENTS, CostSynthesisAgent
from agents_v2.narrative_synthesis_agent import NarrativeSynthesisAgent
from agents_v2.narrative_review_agent import NarrativeReviewAgent
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# Interactive mode
from interactive import Session, InteractiveCLI

# Run management
from services.run_manager import get_run_manager, RunPaths

# Document loading (reuse from v1)
from ingestion.pdf_parser import parse_pdfs

# Module-level logger (configured in setup_logging)
logger = logging.getLogger('main_v2')


def setup_logging(verbose: bool = False):
    """Configure logging for V2 pipeline."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(OUTPUT_DIR / 'v2_analysis.log')
        ]
    )
    return logging.getLogger('main_v2')


def load_documents(input_path: Path) -> str:
    """Load and combine documents from input path."""
    if input_path.is_file():
        if input_path.suffix.lower() == '.pdf':
            return parse_pdfs(input_path)
        elif input_path.suffix.lower() in ['.txt', '.md']:
            with open(input_path, 'r') as f:
                return f.read()
        else:
            raise ValueError(f"Unsupported file type: {input_path.suffix}")

    elif input_path.is_dir():
        # Check for PDFs first
        pdf_files = list(input_path.glob('*.pdf'))
        if pdf_files:
            return parse_pdfs(input_path)

        # Fall back to text files
        txt_files = list(input_path.glob('*.txt')) + list(input_path.glob('*.md'))
        if txt_files:
            # Use list join instead of string concatenation for efficiency
            parts = []
            for txt_file in sorted(txt_files):
                with open(txt_file, 'r', encoding='utf-8') as f:
                    parts.append(f"\n\n# {txt_file.name}\n\n")
                    parts.append(f.read())
            return "".join(parts)

        raise ValueError(f"No supported documents found in: {input_path}")
    else:
        raise ValueError(f"Invalid input path: {input_path}")


def run_discovery(
    document_text: str,
    domain: str = "infrastructure",
    fact_store: Optional[FactStore] = None,
    target_name: Optional[str] = None,
    industry: Optional[str] = None,
    document_name: str = "",
    deal_id: Optional[str] = None,
    inventory_store: Optional[InventoryStore] = None,
) -> FactStore:
    """
    Run discovery phase for a domain.

    Args:
        document_text: Combined document text
        domain: Domain to analyze
        fact_store: Existing FactStore to add to (optional)
        target_name: Name of the target company (helps agent focus on correct entity)
        industry: Industry for industry-aware discovery (applications domain).
                  Valid keys: healthcare, financial_services, manufacturing,
                  aviation_mro, defense_contractor, life_sciences, retail,
                  logistics, energy_utilities, insurance, construction,
                  food_beverage, professional_services, education, hospitality
        document_name: Source document filename for fact traceability
        deal_id: Deal ID for data isolation (required if fact_store is None)

    Returns:
        FactStore with extracted facts
    """
    if fact_store is None:
        # Generate deal_id if not provided
        if not deal_id:
            deal_id = f"run-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        fact_store = FactStore(deal_id=deal_id)

    # Create InventoryStore if not provided
    effective_deal_id = deal_id or fact_store.deal_id
    if inventory_store is None:
        inventory_store = InventoryStore(deal_id=effective_deal_id)

    print(f"\n{'='*60}")
    print("PHASE 1: DISCOVERY")
    print(f"Domain: {domain}")
    print(f"Model: {DISCOVERY_MODEL}")
    if target_name:
        print(f"Target: {target_name}")
    print(f"{'='*60}")

    # Create appropriate discovery agent
    if domain not in DISCOVERY_AGENTS:
        raise ValueError(f"Discovery agent not available for domain: {domain}")

    agent_class = DISCOVERY_AGENTS[domain]

    # Build agent kwargs
    agent_kwargs = {
        "fact_store": fact_store,
        "api_key": ANTHROPIC_API_KEY,
        "model": DISCOVERY_MODEL,
        "max_tokens": DISCOVERY_MAX_TOKENS,
        "max_iterations": DISCOVERY_MAX_ITERATIONS,
        "target_name": target_name,
        "inventory_store": inventory_store,
    }

    # For applications domain, pass industry for industry-aware discovery
    if domain == "applications" and industry:
        agent_kwargs["industry"] = industry
        print(f"Industry-aware discovery: {industry}")

    agent = agent_class(**agent_kwargs)

    # Run discovery with document name for traceability
    result = agent.discover(document_text, document_name=document_name)

    # Print summary
    print("\nDiscovery Summary:")
    print(f"  Facts extracted: {result['metrics'].get('facts_extracted', len(result['facts']))}")
    print(f"  Gaps identified: {result['metrics'].get('gaps_flagged', len(result['gaps']))}")

    # Estimate cost
    metrics = agent.get_metrics()
    cost = estimate_cost(DISCOVERY_MODEL, metrics.input_tokens, metrics.output_tokens)
    print(f"  Estimated cost: ${cost:.4f}")

    return fact_store, inventory_store


def run_reasoning(
    fact_store: FactStore,
    domain: str = "infrastructure",
    deal_context: Optional[Dict] = None
) -> Dict:
    """
    Run reasoning phase for a domain.

    Args:
        fact_store: FactStore with extracted facts
        domain: Domain to analyze
        deal_context: Deal context for reasoning

    Returns:
        Dict with reasoning results
    """
    print(f"\n{'='*60}")
    print("PHASE 2: REASONING")
    print(f"Domain: {domain}")
    print(f"Model: {REASONING_MODEL}")
    print(f"{'='*60}")

    # Get fact count for this domain
    domain_facts = fact_store.get_domain_facts(domain)
    print(f"Input facts: {domain_facts['fact_count']}")
    print(f"Known gaps: {domain_facts['gap_count']}")

    if domain_facts['fact_count'] == 0:
        print(f"\n[WARN] No facts to reason about for {domain}")
        return {
            "domain": domain,
            "findings": {},
            "warning": "No facts available"
        }

    # Create appropriate reasoning agent
    if domain not in REASONING_AGENTS:
        raise ValueError(f"Reasoning agent not available for domain: {domain}")

    agent_class = REASONING_AGENTS[domain]
    agent = agent_class(
        fact_store=fact_store,
        api_key=ANTHROPIC_API_KEY,
        model=REASONING_MODEL,
        max_tokens=REASONING_MAX_TOKENS,
        max_iterations=REASONING_MAX_ITERATIONS
    )

    # Run reasoning
    result = agent.reason(deal_context)

    # Print summary
    print("\nReasoning Summary:")
    findings = result.get('findings', {}).get('summary', {})
    print(f"  Risks: {findings.get('risks', 0)}")
    print(f"  Strategic considerations: {findings.get('strategic_considerations', 0)}")
    print(f"  Work items: {findings.get('work_items', 0)}")
    print(f"  Recommendations: {findings.get('recommendations', 0)}")
    print(f"  Citation coverage: {result.get('citation_coverage', 0):.0f}%")

    # Estimate cost
    metrics = agent.get_metrics()
    cost = estimate_cost(REASONING_MODEL, metrics.input_tokens, metrics.output_tokens)
    print(f"  Estimated cost: ${cost:.4f}")

    return result


def save_outputs(
    fact_store: FactStore,
    reasoning_results: Dict,
    output_dir: Path,
    timestamp: str
) -> Dict[str, Path]:
    """Save all outputs to files."""
    output_files = {}

    # Save facts
    facts_file = FACTS_DIR / f"facts_{timestamp}.json"
    fact_store.save(str(facts_file))
    output_files["facts"] = facts_file
    print(f"Saved facts to: {facts_file}")

    # Save findings
    if reasoning_results and reasoning_results.get("findings"):
        findings_file = FINDINGS_DIR / f"findings_{timestamp}.json"
        with open(findings_file, 'w') as f:
            json.dump(reasoning_results, f, indent=2)
        output_files["findings"] = findings_file
        print(f"Saved findings to: {findings_file}")

    return output_files


def run_coverage_analysis(fact_store: FactStore) -> Dict:
    """
    Run coverage analysis on extracted facts.

    Args:
        fact_store: FactStore with extracted facts

    Returns:
        Dict with coverage results
    """
    print(f"\n{'='*60}")
    print("PHASE 3: COVERAGE ANALYSIS")
    print(f"{'='*60}")

    analyzer = CoverageAnalyzer(fact_store)
    coverage = analyzer.calculate_overall_coverage()
    grade = analyzer.get_coverage_grade()

    print(f"\nCoverage Grade: {grade}")
    print(f"Overall Coverage: {coverage['summary']['overall_coverage_percent']:.1f}%")
    print(f"Critical Coverage: {coverage['summary']['critical_coverage_percent']:.1f}%")
    print(f"Missing Critical Items: {len(coverage['missing_critical'])}")

    # Per-domain breakdown
    print("\nDomain Coverage:")
    for domain, data in coverage['domains'].items():
        if data['facts'] > 0 or data['gaps'] > 0:
            print(f"  {domain}: {data['coverage_percent']:.1f}% "
                  f"(critical: {data['critical_coverage_percent']:.1f}%)")

    return {
        "coverage": coverage,
        "grade": grade,
        "summary_text": analyzer.get_coverage_summary_text()
    }


def merge_reasoning_stores(
    fact_store: FactStore,
    reasoning_results: Dict[str, Dict]
) -> ReasoningStore:
    """
    Merge all domain reasoning results into a single ReasoningStore.

    PRESERVES original finding IDs to maintain triggered_by_risks links.

    Args:
        fact_store: FactStore for validation
        reasoning_results: Dict mapping domain to reasoning result

    Returns:
        Merged ReasoningStore
    """
    merged_store = ReasoningStore(fact_store=fact_store)

    for domain, result in reasoning_results.items():
        if result.get("error"):
            continue

        findings = result.get("findings", {})

        # Use import_from_dict to preserve original finding IDs
        # This maintains triggered_by_risks links between work items and risks
        merged_store.import_from_dict(findings)

    return merged_store


def run_synthesis(
    fact_store: FactStore,
    reasoning_store: ReasoningStore
) -> Dict:
    """
    Run synthesis phase for cross-domain analysis.

    Args:
        fact_store: FactStore with all facts
        reasoning_store: Merged ReasoningStore with all findings

    Returns:
        Dict with synthesis results
    """
    print(f"\n{'='*60}")
    print("PHASE 4: SYNTHESIS")
    print(f"{'='*60}")

    analyzer = SynthesisAnalyzer(fact_store, reasoning_store)
    results = analyzer.analyze()

    # Print summary
    print(f"\nConsistency Issues: {results['consistency']['total_issues']}")
    if results['consistency']['high_severity_issues'] > 0:
        print(f"  High Severity: {results['consistency']['high_severity_issues']}")

    print(f"\nRelated Finding Themes: {len(results['related_findings'])}")
    for group in results['related_findings']:
        cost_low = group['total_cost_range']['low']
        cost_high = group['total_cost_range']['high']
        print(f"  {group['theme'].replace('_', ' ').title()}: "
              f"{group['finding_count']} findings "
              f"(${cost_low:,} - ${cost_high:,})")

    print("\nCost Summary:")
    cost = results['cost_summary']
    print(f"  Total: ${cost['total']['low']:,} - ${cost['total']['high']:,}")
    print(f"  Day 1: ${cost['by_phase']['Day_1']['low']:,} - ${cost['by_phase']['Day_1']['high']:,}")
    print(f"  Day 100: ${cost['by_phase']['Day_100']['low']:,} - ${cost['by_phase']['Day_100']['high']:,}")
    print(f"  Post 100: ${cost['by_phase']['Post_100']['low']:,} - ${cost['by_phase']['Post_100']['high']:,}")

    return {
        "synthesis": results,
        "executive_summary": analyzer.get_executive_summary()
    }


def run_vdr_generation(
    fact_store: FactStore,
    reasoning_store: Optional[ReasoningStore] = None
) -> Dict:
    """
    Generate VDR request pack.

    Args:
        fact_store: FactStore with gaps
        reasoning_store: Optional ReasoningStore for risk-based requests

    Returns:
        Dict with VDR results
    """
    print(f"\n{'='*60}")
    print("PHASE 5: VDR REQUEST GENERATION")
    print(f"{'='*60}")

    generator = VDRGenerator(fact_store, reasoning_store)
    pack = generator.generate()

    print("\nVDR Request Pack Summary:")
    print(f"  Total Requests: {pack.total_count}")
    print(f"  Critical: {pack.critical_count}")
    print(f"  High: {pack.high_count}")
    print(f"  Medium: {len(pack.get_by_priority('medium'))}")
    print(f"  Low: {len(pack.get_by_priority('low'))}")

    # Show top 5 critical requests
    critical = pack.get_by_priority('critical')[:5]
    if critical:
        print("\nTop Critical Requests:")
        for req in critical:
            print(f"  [{req.request_id}] {req.title[:50]}")

    return {
        "vdr_pack": pack.to_dict(),
        "vdr_markdown": generator.generate_markdown(),
        "vdr_csv": generator.generate_csv_data()
    }


# Thread-safe lock for FactStore merging
_fact_store_lock = threading.Lock()


def get_or_create_session(
    session_id: Optional[str],
    new_session: bool,
    target_name: str,
    deal_type: str = "platform",
    buyer_name: Optional[str] = None,
    industry: Optional[str] = None
) -> Optional[DDSession]:
    """
    Get existing session or create a new one.

    Args:
        session_id: Session identifier
        new_session: Force create new session
        target_name: Target company name
        deal_type: Type of deal
        buyer_name: Buyer company name
        industry: Industry vertical

    Returns:
        DDSession instance or None if not using sessions
    """
    if not session_id:
        return None

    try:
        if new_session:
            # Force create new session
            return DDSession.create(
                session_id=session_id,
                target_name=target_name,
                deal_type=deal_type,
                buyer_name=buyer_name,
                industry=industry
            )
        else:
            # Try to load existing, create if not found
            try:
                session = DDSession.load(session_id)
                print(f"Resumed session: {session_id}")
                print(f"  Documents: {len(session.state.processed_documents)}")
                print(f"  Facts: {len(session.fact_store.facts)}")
                return session
            except ValueError:
                # Session doesn't exist, create it
                return DDSession.create(
                    session_id=session_id,
                    target_name=target_name,
                    deal_type=deal_type,
                    buyer_name=buyer_name,
                    industry=industry
                )
    except Exception as e:
        print(f"[ERROR] Session error: {e}")
        raise


def get_deal_context_from_session(session: DDSession) -> Dict:
    """
    Get deal context dictionary from session with prompt-formatted context.

    This enhances the deal context with the formatted prompt context
    that shapes analysis based on deal type.
    """
    context = session.get_deal_context_dict()
    # Add the formatted prompt context for injection into reasoning prompts
    context["_prompt_context"] = session.get_deal_context_for_prompts()
    return context


def run_discovery_for_domain(
    document_text: str,
    domain: str,
    shared_fact_store: FactStore,
    shared_inventory_store: InventoryStore,
    target_name: Optional[str] = None,
    deal_id: Optional[str] = None
) -> Dict:
    """
    Run discovery for a single domain (used in parallel execution).

    Returns dict with domain results and metrics.
    """
    # Use deal_id from shared store or passed parameter
    effective_deal_id = deal_id or shared_fact_store.deal_id

    # Create a local FactStore for this domain with same deal_id
    local_store = FactStore(deal_id=effective_deal_id)

    try:
        # Shared InventoryStore is thread-safe (add_item uses threading.Lock)
        # No need for local copy; pass shared store directly
        _fact_store_result, _inv_store_result = run_discovery(
            document_text=document_text,
            domain=domain,
            fact_store=local_store,
            target_name=target_name,
            deal_id=effective_deal_id,
            inventory_store=shared_inventory_store,
        )

        # Merge into shared store (thread-safe)
        with _fact_store_lock:
            shared_fact_store.merge_from(local_store)

        return {
            "domain": domain,
            "status": "success",
            "facts": len(local_store.facts),
            "gaps": len(local_store.gaps)
        }

    except Exception as e:
        return {
            "domain": domain,
            "status": "error",
            "error": str(e)
        }


def run_reasoning_for_domain(
    fact_store: FactStore,
    domain: str,
    deal_context: Optional[Dict] = None
) -> Dict:
    """
    Run reasoning for a single domain (used in parallel execution).

    Returns dict with domain results.
    """
    try:
        result = run_reasoning(
            fact_store=fact_store,
            domain=domain,
            deal_context=deal_context
        )
        return {
            "domain": domain,
            "status": "success",
            "result": result
        }
    except Exception as e:
        return {
            "domain": domain,
            "status": "error",
            "error": str(e)
        }


def run_parallel_discovery(
    document_text: str,
    domains: List[str],
    max_workers: int = MAX_PARALLEL_AGENTS,
    target_name: Optional[str] = None,
    progress_callback: Optional[callable] = None,
    deal_id: Optional[str] = None
) -> FactStore:
    """
    Run discovery for multiple domains in parallel.

    Args:
        document_text: Document text to analyze
        domains: List of domains to discover
        max_workers: Maximum parallel agents
        target_name: Name of target company (helps agents focus on correct entity)
        progress_callback: Optional callback(completed, total, domain) for progress updates
        deal_id: Deal ID for data isolation

    Returns:
        Merged FactStore with all facts
    """
    # Generate deal_id if not provided
    if not deal_id:
        deal_id = f"run-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

    print(f"\n{'='*60}")
    print(f"PARALLEL DISCOVERY: {len(domains)} domains")
    print(f"Max workers: {max_workers}")
    print(f"Deal ID: {deal_id}")
    if target_name:
        print(f"Target: {target_name}")
    print(f"{'='*60}")

    shared_fact_store = FactStore(deal_id=deal_id)
    shared_inventory_store = InventoryStore(deal_id=deal_id)
    results = []
    completed_count = 0

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(
                run_discovery_for_domain,
                document_text,
                domain,
                shared_fact_store,
                shared_inventory_store,
                target_name,
                deal_id
            ): domain
            for domain in domains
        }

        for future in as_completed(futures):
            domain = futures[future]
            try:
                result = future.result(timeout=600)  # 10 minute timeout per domain
                results.append(result)
                completed_count += 1
                
                # Progress callback
                if progress_callback:
                    progress_callback(completed_count, len(domains), domain)
                
                if result["status"] == "success":
                    print(f"  [OK] {domain}: {result['facts']} facts, {result['gaps']} gaps ({completed_count}/{len(domains)})")
                else:
                    print(f"  [ERROR] {domain}: {result.get('error', 'Unknown error')} ({completed_count}/{len(domains)})")
                    # Log error for debugging
                    logger.error(f"Discovery failed for {domain}: {result.get('error')}")
            except TimeoutError:
                completed_count += 1
                if progress_callback:
                    progress_callback(completed_count, len(domains), domain)
                error_msg = f"Discovery timeout for {domain} (exceeded 10 minutes)"
                print(f"  [TIMEOUT] {domain} ({completed_count}/{len(domains)})")
                logger.error(error_msg)
                results.append({"domain": domain, "status": "error", "error": error_msg})
            except Exception as e:
                completed_count += 1
                if progress_callback:
                    progress_callback(completed_count, len(domains), domain)
                error_msg = str(e)
                print(f"  [ERROR] {domain}: {error_msg} ({completed_count}/{len(domains)})")
                logger.exception(f"Discovery exception for {domain}")
                results.append({"domain": domain, "status": "error", "error": error_msg})

    # Validate FactStore consistency after merge
    fact_count = len(shared_fact_store.facts)
    gap_count = len(shared_fact_store.gaps)
    print(f"\nDiscovery complete: {fact_count} total facts, {gap_count} gaps")
    
    # Check for successful domains
    _ = [r for r in results if r.get("status") == "success"]
    failed = [r for r in results if r.get("status") == "error"]
    
    if failed:
        logger.warning(f"Discovery completed with {len(failed)} failed domain(s): {[r['domain'] for r in failed]}")

    # Save inventory store after all parallel discovery completes
    shared_inventory_store.save()
    logger.info(f"Saved {len(shared_inventory_store)} inventory items to {shared_inventory_store.storage_path}")

    # Promote LLM-extracted facts to inventory items
    for entity_val in ["target", "buyer"]:
        promotion_stats = promote_facts_to_inventory(
            fact_store=shared_fact_store,
            inventory_store=shared_inventory_store,
            entity=entity_val,
        )
        if promotion_stats["promoted"] > 0 or promotion_stats["matched"] > 0:
            print(f"[PROMOTION] {entity_val}: {promotion_stats['promoted']} new items, "
                  f"{promotion_stats['matched']} matched to existing")

    # Re-save inventory store (now includes both deterministic + promoted items)
    shared_inventory_store.save()

    # Reconcile unlinked facts and inventory items
    reconcile_stats = reconcile_facts_and_inventory(
        fact_store=shared_fact_store,
        inventory_store=shared_inventory_store,
        entity="target",
        similarity_threshold=0.8,
    )
    logger.info(
        f"Reconciliation: {reconcile_stats['matched']} matched, "
        f"{reconcile_stats['unmatched_facts']} unmatched facts, "
        f"{reconcile_stats['unmatched_items']} unmatched items"
    )

    # Repeat for buyer entity if present
    buyer_items = shared_inventory_store.get_items(entity="buyer")
    if buyer_items:
        buyer_stats = reconcile_facts_and_inventory(
            fact_store=shared_fact_store,
            inventory_store=shared_inventory_store,
            entity="buyer",
            similarity_threshold=0.8,
        )
        logger.info(f"Buyer reconciliation: {buyer_stats['matched']} matched")

    # Re-save after reconciliation (links were updated)
    shared_inventory_store.save()

    # Generate and save audit report
    audit_report = generate_inventory_audit(
        inventory_store=shared_inventory_store,
        fact_store=shared_fact_store,
        deal_id=deal_id,
    )
    audit_path = save_inventory_audit(
        audit_report,
        deal_id=deal_id,
    )
    logger.info(
        f"Inventory audit: {audit_report['overall_health']} — "
        f"{audit_report['linking']['total_items']} items, "
        f"{audit_report['linking']['item_link_rate']}% linked"
    )
    if audit_report["issues"]:
        for issue in audit_report["issues"]:
            logger.warning(f"Audit issue: {issue}")

    return shared_fact_store


def run_parallel_reasoning(
    fact_store: FactStore,
    domains: List[str],
    deal_context: Optional[Dict] = None,
    max_workers: int = MAX_PARALLEL_AGENTS,
    progress_callback: Optional[callable] = None
) -> Dict[str, Dict]:
    """
    Run reasoning for multiple domains in parallel.

    Args:
        fact_store: FactStore with extracted facts
        domains: List of domains to reason about
        deal_context: Deal context for reasoning
        max_workers: Maximum parallel agents
        progress_callback: Optional callback(completed, total, domain) for progress updates

    Returns:
        Dict mapping domain to reasoning results
    """
    print(f"\n{'='*60}")
    print(f"PARALLEL REASONING: {len(domains)} domains")
    print(f"Max workers: {max_workers}")
    print(f"{'='*60}")

    all_results = {}
    completed_count = 0

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(
                run_reasoning_for_domain,
                fact_store,
                domain,
                deal_context
            ): domain
            for domain in domains
        }

        for future in as_completed(futures):
            domain = futures[future]
            try:
                result = future.result(timeout=900)  # 15 minute timeout per domain
                completed_count += 1
                
                # Progress callback
                if progress_callback:
                    progress_callback(completed_count, len(domains), domain)
                
                if result["status"] == "success":
                    all_results[domain] = result["result"]
                    findings = result["result"].get("findings", {}).get("summary", {})
                    print(f"  [OK] {domain}: {findings.get('risks', 0)} risks, {findings.get('work_items', 0)} work items ({completed_count}/{len(domains)})")
                else:
                    all_results[domain] = {"error": result.get("error")}
                    print(f"  [ERROR] {domain}: {result.get('error', 'Unknown error')} ({completed_count}/{len(domains)})")
                    logger.error(f"Reasoning failed for {domain}: {result.get('error')}")
            except TimeoutError:
                completed_count += 1
                if progress_callback:
                    progress_callback(completed_count, len(domains), domain)
                error_msg = f"Reasoning timeout for {domain} (exceeded 15 minutes)"
                print(f"  [TIMEOUT] {domain} ({completed_count}/{len(domains)})")
                logger.error(error_msg)
                all_results[domain] = {"error": error_msg}
            except Exception as e:
                completed_count += 1
                if progress_callback:
                    progress_callback(completed_count, len(domains), domain)
                error_msg = str(e)
                print(f"  [ERROR] {domain}: {error_msg} ({completed_count}/{len(domains)})")
                logger.exception(f"Reasoning exception for {domain}")
                all_results[domain] = {"error": error_msg}

    # Report summary
    _ = [d for d, r in all_results.items() if "error" not in r]
    failed = [d for d, r in all_results.items() if "error" in r]
    
    if failed:
        logger.warning(f"Reasoning completed with {len(failed)} failed domain(s): {failed}")
    
    return all_results


def main():
    """Main entry point for V2 pipeline."""
    parser = argparse.ArgumentParser(
        description="IT Due Diligence Agent V2 - Discovery/Reasoning/Synthesis Architecture",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main_v2.py data/input/                    # Full pipeline (infrastructure only)
  python main_v2.py data/input/ --all              # Full pipeline (all 6 domains, parallel)
  python main_v2.py data/input/ --discovery-only   # Extract facts only (no reasoning/synthesis)
  python main_v2.py --from-facts facts.json        # Reason from existing facts
  python main_v2.py data/input/ --domain network   # Single domain
  python main_v2.py data/input/ --all --sequential # All domains, no parallelization
  python main_v2.py data/input/ --no-vdr           # Skip VDR request generation
  python main_v2.py data/input/ --no-synthesis     # Skip cross-domain synthesis
  python main_v2.py data/input/ --interactive      # Run analysis then enter interactive mode
  python main_v2.py --interactive-only             # Load existing outputs, enter interactive mode

Phases:
  1. Discovery   - Extract facts from documents (Haiku model)
  2. Reasoning   - Analyze facts, produce findings (Sonnet model)
  3. Coverage    - Score documentation completeness
  4. Synthesis   - Cross-domain consistency, cost aggregation
  5. VDR         - Generate follow-up data requests
        """
    )

    # Input options
    parser.add_argument(
        "input_path",
        nargs="?",
        type=Path,
        help="Path to input documents (file or directory)"
    )
    parser.add_argument(
        "--from-facts",
        type=Path,
        help="Load facts from existing JSON file (skip discovery)"
    )

    # Pipeline options
    parser.add_argument(
        "--discovery-only",
        action="store_true",
        help="Run discovery phase only (extract facts, no reasoning)"
    )
    parser.add_argument(
        "--domain",
        choices=DOMAINS,
        default="infrastructure",
        help="Domain to analyze (default: infrastructure)"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Analyze all 6 domains (parallel by default)"
    )
    parser.add_argument(
        "--sequential",
        action="store_true",
        help="Run domains sequentially (disable parallelization)"
    )
    parser.add_argument(
        "--no-vdr",
        action="store_true",
        help="Skip VDR request generation"
    )
    parser.add_argument(
        "--no-synthesis",
        action="store_true",
        help="Skip synthesis phase"
    )

    # Interactive mode
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="Enter interactive mode after analysis (review/adjust findings)"
    )
    parser.add_argument(
        "--interactive-only",
        action="store_true",
        help="Load from existing files and enter interactive mode (no new analysis)"
    )

    # Deal context
    parser.add_argument(
        "--deal-context",
        type=Path,
        help="Path to deal context JSON file"
    )

    # Session-based workflow (incremental analysis)
    parser.add_argument(
        "--session",
        type=str,
        help="Session ID to use (creates or resumes session)"
    )
    parser.add_argument(
        "--new-session",
        action="store_true",
        help="Force create a new session (error if exists)"
    )
    parser.add_argument(
        "--deal-type",
        choices=["carve_out", "bolt_on"],
        default="bolt_on",
        help="Deal type for analysis focus: carve_out (separation from parent) or bolt_on (integration into buyer)"
    )
    parser.add_argument(
        "--buyer-name",
        type=str,
        help="Buyer company name (for integration context)"
    )
    parser.add_argument(
        "--industry",
        type=str,
        help="Industry vertical (healthcare, financial_services, manufacturing, etc.)"
    )

    # Output options
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=OUTPUT_DIR,
        help="Output directory (default: output/)"
    )
    parser.add_argument(
        "--use-runs",
        action="store_true",
        default=True,
        help="Organize outputs into timestamped run folders (default: enabled)"
    )
    parser.add_argument(
        "--no-runs",
        action="store_true",
        help="Disable run folders, save to flat output directory"
    )
    parser.add_argument(
        "--target-name",
        type=str,
        default="Target Company",
        help="Target company name for investment thesis presentation"
    )
    parser.add_argument(
        "--narrative",
        action="store_true",
        help="Enable narrative generation for investment thesis (uses LLM, higher quality)"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )

    args = parser.parse_args()

    # Setup logging (configures the module-level logger)
    setup_logging(args.verbose)

    # Handle interactive-only mode (load existing outputs)
    if args.interactive_only:
        print("\n" + "="*60)
        print("INTERACTIVE MODE - Loading from existing files")
        print("="*60)

        # Find most recent facts and findings files
        facts_files = sorted(FACTS_DIR.glob("facts_*.json"), reverse=True)
        findings_files = sorted(FINDINGS_DIR.glob("findings_*.json"), reverse=True)

        if not facts_files:
            print(f"\n[ERROR] No facts files found in {FACTS_DIR}")
            print("Run analysis first or specify --from-facts")
            sys.exit(1)

        facts_file = facts_files[0]
        findings_file = findings_files[0] if findings_files else None

        print(f"\nLoading facts from: {facts_file}")
        if findings_file:
            print(f"Loading findings from: {findings_file}")

        # Create session and enter interactive mode
        session = Session.load_from_files(
            facts_file=facts_file,
            findings_file=findings_file
        )

        cli = InteractiveCLI(session)
        cli.run()
        sys.exit(0)

    # Validate inputs
    if not args.from_facts and not args.input_path:
        parser.error("Either input_path or --from-facts is required")

    if args.from_facts and args.discovery_only:
        parser.error("Cannot use --from-facts with --discovery-only")

    # Check API key
    if not ANTHROPIC_API_KEY:
        print("[ERROR] ANTHROPIC_API_KEY not set in environment or .env file")
        sys.exit(1)

    # Timestamp for outputs
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Create run directory for organized outputs (default: enabled)
    run_paths: Optional[RunPaths] = None
    use_runs = args.use_runs and not args.no_runs

    if use_runs:
        run_manager = get_run_manager()
        run_paths = run_manager.create_run_directory(
            target_name=args.target_name,
            deal_type=getattr(args, 'deal_type', '')
        )
        logger.info(f"Created run directory: {run_paths.root}")

    # Determine domains to analyze
    if getattr(args, 'all', False):
        domains_to_analyze = DOMAINS
        use_parallel = not args.sequential and PARALLEL_DISCOVERY
    else:
        domains_to_analyze = [args.domain]
        use_parallel = False

    # Handle session-based workflow
    dd_session: Optional[DDSession] = None
    if args.session:
        dd_session = get_or_create_session(
            session_id=args.session,
            new_session=args.new_session,
            target_name=args.target_name,
            deal_type=args.deal_type,
            buyer_name=args.buyer_name,
            industry=args.industry
        )

    # Generate deal_id for data isolation
    # Priority: session_id > run folder name > timestamp-based
    deal_id: Optional[str] = None
    if dd_session:
        deal_id = dd_session.session_id
    elif run_paths:
        deal_id = run_paths.root.name
    else:
        deal_id = f"run-{timestamp}"

    print(f"\n{'='*60}")
    print("IT DUE DILIGENCE AGENT V2")
    print(f"{'='*60}")
    print(f"Timestamp: {timestamp}")
    print(f"Deal ID: {deal_id}")
    if run_paths:
        print(f"Run: {run_paths.root.name}")
    if dd_session:
        print(f"Session: {dd_session.session_id}")
        print(f"Deal Type: {dd_session.state.deal_context.deal_type}")
        print(f"Target: {dd_session.state.deal_context.target_name}")
    print(f"Domains: {', '.join(domains_to_analyze)}")
    print(f"Parallel: {use_parallel}")

    try:
        # Phase 1: Discovery (or load from file)
        if args.from_facts:
            print(f"\nLoading facts from: {args.from_facts}")
            fact_store = FactStore.load(str(args.from_facts), deal_id=deal_id)
            print(f"Loaded {len(fact_store.facts)} facts, {len(fact_store.gaps)} gaps")
        elif dd_session:
            # Session-based workflow: use session's fact_store
            fact_store = dd_session.fact_store
            initial_fact_count = len(fact_store.facts)

            if args.input_path:
                # Add documents to session for incremental processing
                print(f"\nChecking documents from: {args.input_path}")
                doc_paths = list(args.input_path.glob('*.pdf')) + list(args.input_path.glob('*.txt'))
                doc_status = dd_session.add_documents(doc_paths)

                print(f"  New: {len(doc_status['new'])}, Changed: {len(doc_status['changed'])}, Unchanged: {len(doc_status['unchanged'])}")

                # Only process if there are new/changed documents
                pending_docs = dd_session.get_pending_documents()
                if pending_docs:
                    print(f"\nProcessing {len(pending_docs)} new/changed documents...")

                    # Load document text
                    document_text = load_documents(args.input_path)
                    print(f"Loaded {len(document_text):,} characters")

                    # Start discovery run
                    dd_session.start_run("discovery", domains_to_analyze)

                    # Run discovery (parallel or sequential)
                    if use_parallel and len(domains_to_analyze) > 1:
                        # For incremental, we need to handle the shared store differently
                        run_parallel_discovery(
                            document_text=document_text,
                            domains=domains_to_analyze,
                            max_workers=MAX_PARALLEL_AGENTS,
                            target_name=args.target_name,
                            deal_id=deal_id,
                        )
                        # Merge results into session store
                        # Note: run_parallel_discovery already merges into the shared store passed
                        # InventoryStore is saved inside run_parallel_discovery
                    else:
                        session_inventory_store = InventoryStore(deal_id=deal_id)
                        for domain in domains_to_analyze:
                            _fs, _is = run_discovery(
                                document_text=document_text,
                                domain=domain,
                                fact_store=fact_store,
                                target_name=args.target_name,
                                deal_id=deal_id,
                                inventory_store=session_inventory_store,
                            )
                        # Save inventory store after all session discovery completes
                        session_inventory_store.save()
                        logger.info(f"Saved {len(session_inventory_store)} inventory items for session {deal_id}")

                        # Promote LLM-extracted facts to inventory items
                        for entity_val in ["target", "buyer"]:
                            promotion_stats = promote_facts_to_inventory(
                                fact_store=fact_store,
                                inventory_store=session_inventory_store,
                                entity=entity_val,
                            )
                            if promotion_stats["promoted"] > 0 or promotion_stats["matched"] > 0:
                                print(f"[PROMOTION] {entity_val}: {promotion_stats['promoted']} new items, "
                                      f"{promotion_stats['matched']} matched to existing")

                        # Re-save inventory store (now includes promoted items)
                        session_inventory_store.save()

                        # Reconcile unlinked facts and inventory items
                        reconcile_stats = reconcile_facts_and_inventory(
                            fact_store=fact_store,
                            inventory_store=session_inventory_store,
                            entity="target",
                            similarity_threshold=0.8,
                        )
                        logger.info(
                            f"Reconciliation: {reconcile_stats['matched']} matched, "
                            f"{reconcile_stats['unmatched_facts']} unmatched facts, "
                            f"{reconcile_stats['unmatched_items']} unmatched items"
                        )

                        # Repeat for buyer entity if present
                        buyer_items = session_inventory_store.get_items(entity="buyer")
                        if buyer_items:
                            buyer_stats = reconcile_facts_and_inventory(
                                fact_store=fact_store,
                                inventory_store=session_inventory_store,
                                entity="buyer",
                                similarity_threshold=0.8,
                            )
                            logger.info(f"Buyer reconciliation: {buyer_stats['matched']} matched")

                        # Re-save after reconciliation (links were updated)
                        session_inventory_store.save()

                        # Generate and save audit report
                        audit_report = generate_inventory_audit(
                            inventory_store=session_inventory_store,
                            fact_store=fact_store,
                            deal_id=deal_id,
                        )
                        audit_path = save_inventory_audit(
                            audit_report,
                            deal_id=deal_id,
                        )
                        logger.info(
                            f"Inventory audit: {audit_report['overall_health']} — "
                            f"{audit_report['linking']['total_items']} items, "
                            f"{audit_report['linking']['item_link_rate']}% linked"
                        )
                        if audit_report["issues"]:
                            for issue in audit_report["issues"]:
                                logger.warning(f"Audit issue: {issue}")

                    # Mark documents as processed
                    for doc_path in pending_docs:
                        dd_session.mark_document_processed(doc_path)

                    # Complete the run
                    facts_added = len(fact_store.facts) - initial_fact_count
                    dd_session.complete_run(facts_added=facts_added)

                    print(f"\nDiscovery added {facts_added} new facts (total: {len(fact_store.facts)})")
                else:
                    print("\nNo new documents to process - using existing facts")
            else:
                print(f"\nUsing existing session facts: {len(fact_store.facts)}")

            # Save session state
            dd_session.save()
        else:
            # Standard workflow (no session)
            print(f"\nLoading documents from: {args.input_path}")
            document_text = load_documents(args.input_path)
            print(f"Loaded {len(document_text):,} characters")

            # Run discovery (parallel or sequential)
            if use_parallel and len(domains_to_analyze) > 1:
                fact_store = run_parallel_discovery(
                    document_text=document_text,
                    domains=domains_to_analyze,
                    max_workers=MAX_PARALLEL_AGENTS,
                    target_name=args.target_name,
                    deal_id=deal_id
                )
            else:
                # Sequential discovery
                fact_store = FactStore(deal_id=deal_id)
                inventory_store = InventoryStore(deal_id=deal_id)
                for domain in domains_to_analyze:
                    _fs, _is = run_discovery(
                        document_text=document_text,
                        domain=domain,
                        fact_store=fact_store,
                        target_name=args.target_name,
                        deal_id=deal_id,
                        inventory_store=inventory_store,
                    )

                # Save inventory store after all discovery completes
                inventory_store.save()
                logger.info(f"Saved {len(inventory_store)} inventory items for deal {deal_id}")

                # Promote LLM-extracted facts to inventory items
                for entity_val in ["target", "buyer"]:
                    promotion_stats = promote_facts_to_inventory(
                        fact_store=fact_store,
                        inventory_store=inventory_store,
                        entity=entity_val,
                    )
                    if promotion_stats["promoted"] > 0 or promotion_stats["matched"] > 0:
                        print(f"[PROMOTION] {entity_val}: {promotion_stats['promoted']} new items, "
                              f"{promotion_stats['matched']} matched to existing")

                # Re-save inventory store (now includes promoted items)
                inventory_store.save()

                # Reconcile unlinked facts and inventory items
                reconcile_stats = reconcile_facts_and_inventory(
                    fact_store=fact_store,
                    inventory_store=inventory_store,
                    entity="target",
                    similarity_threshold=0.8,
                )
                logger.info(
                    f"Reconciliation: {reconcile_stats['matched']} matched, "
                    f"{reconcile_stats['unmatched_facts']} unmatched facts, "
                    f"{reconcile_stats['unmatched_items']} unmatched items"
                )

                # Repeat for buyer entity if present
                buyer_items = inventory_store.get_items(entity="buyer")
                if buyer_items:
                    buyer_stats = reconcile_facts_and_inventory(
                        fact_store=fact_store,
                        inventory_store=inventory_store,
                        entity="buyer",
                        similarity_threshold=0.8,
                    )
                    logger.info(f"Buyer reconciliation: {buyer_stats['matched']} matched")

                # Re-save after reconciliation (links were updated)
                inventory_store.save()

                # Generate and save audit report
                effective_deal_id = deal_id
                audit_report = generate_inventory_audit(
                    inventory_store=inventory_store,
                    fact_store=fact_store,
                    deal_id=effective_deal_id,
                )
                audit_path = save_inventory_audit(
                    audit_report,
                    deal_id=effective_deal_id,
                )
                logger.info(
                    f"Inventory audit: {audit_report['overall_health']} — "
                    f"{audit_report['linking']['total_items']} items, "
                    f"{audit_report['linking']['item_link_rate']}% linked"
                )
                if audit_report["issues"]:
                    for issue in audit_report["issues"]:
                        logger.warning(f"Audit issue: {issue}")

        # Save facts
        if run_paths:
            facts_file = run_paths.facts / "facts.json"
        else:
            facts_file = FACTS_DIR / f"facts_{timestamp}.json"
        fact_store.save(str(facts_file))
        print(f"\nFacts saved to: {facts_file}")

        # Phase 2: Reasoning (if not discovery-only)
        all_reasoning_results = {}
        findings_file = None

        if not args.discovery_only:
            # Load deal context - prioritize session, then file, then None
            deal_context = None
            if dd_session:
                # Get deal context from session with formatted prompt context
                deal_context = get_deal_context_from_session(dd_session)
                print("\nUsing deal context from session:")
                print(f"  Deal Type: {deal_context.get('deal_type', 'platform')}")
                if deal_context.get('buyer_name'):
                    print(f"  Buyer: {deal_context.get('buyer_name')}")
            elif args.deal_context:
                with open(args.deal_context) as f:
                    deal_context = json.load(f)

            # Determine which domains have facts to reason about
            domains_with_facts = [
                d for d in domains_to_analyze
                if fact_store.get_domain_facts(d)['fact_count'] > 0
            ]

            if not domains_with_facts:
                print("\n[WARN] No facts extracted for any domain - skipping reasoning")
            else:
                # Run reasoning (parallel or sequential)
                use_parallel_reasoning = use_parallel and PARALLEL_REASONING and len(domains_with_facts) > 1

                if use_parallel_reasoning:
                    all_reasoning_results = run_parallel_reasoning(
                        fact_store=fact_store,
                        domains=domains_with_facts,
                        deal_context=deal_context,
                        max_workers=MAX_PARALLEL_AGENTS
                    )
                else:
                    # Sequential reasoning
                    for domain in domains_with_facts:
                        result = run_reasoning(
                            fact_store=fact_store,
                            domain=domain,
                            deal_context=deal_context
                        )
                        all_reasoning_results[domain] = result

                # Save findings
                if run_paths:
                    findings_file = run_paths.findings / "findings.json"
                else:
                    findings_file = FINDINGS_DIR / f"findings_{timestamp}.json"
                with open(findings_file, 'w') as f:
                    json.dump(all_reasoning_results, f, indent=2, default=str)
                print(f"\nFindings saved to: {findings_file}")

        # Phase 3: Coverage Analysis
        coverage_results = run_coverage_analysis(fact_store)

        # Save coverage report
        coverage_file = (run_paths.root if run_paths else OUTPUT_DIR) / f"coverage_{timestamp}.json"
        with open(coverage_file, 'w') as f:
            json.dump(coverage_results['coverage'], f, indent=2)
        print(f"\nCoverage saved to: {coverage_file}")

        # Phase 4: Synthesis (if reasoning was done and not skipped)
        synthesis_results = None
        merged_reasoning_store = None

        if all_reasoning_results and not args.no_synthesis:
            # Merge all reasoning results into single store
            merged_reasoning_store = merge_reasoning_stores(fact_store, all_reasoning_results)
            synthesis_results = run_synthesis(fact_store, merged_reasoning_store)

            # Save synthesis results
            synthesis_file = (run_paths.root if run_paths else OUTPUT_DIR) / f"synthesis_{timestamp}.json"
            with open(synthesis_file, 'w') as f:
                json.dump(synthesis_results['synthesis'], f, indent=2, default=str)
            print(f"\nSynthesis saved to: {synthesis_file}")

            # Save executive summary
            exec_summary_file = (run_paths.reports if run_paths else OUTPUT_DIR) / f"executive_summary_{timestamp}.md"
            with open(exec_summary_file, 'w') as f:
                f.write(synthesis_results['executive_summary'])
            print(f"Executive summary saved to: {exec_summary_file}")

        # Phase 5: VDR Generation (if not skipped)
        vdr_results = None

        if not args.no_vdr:
            vdr_results = run_vdr_generation(fact_store, merged_reasoning_store)

            # Save VDR pack
            vdr_file = (run_paths.root if run_paths else OUTPUT_DIR) / f"vdr_requests_{timestamp}.json"
            with open(vdr_file, 'w') as f:
                json.dump(vdr_results['vdr_pack'], f, indent=2)
            print(f"\nVDR requests saved to: {vdr_file}")

            # Save VDR markdown
            vdr_md_file = (run_paths.root if run_paths else OUTPUT_DIR) / f"vdr_requests_{timestamp}.md"
            with open(vdr_md_file, 'w') as f:
                f.write(vdr_results['vdr_markdown'])
            print(f"VDR markdown saved to: {vdr_md_file}")

        # Phase 6: Narrative Generation (if enabled)
        narrative_store = None
        if args.narrative and merged_reasoning_store:
            print(f"\n{'='*60}")
            print("PHASE 6: NARRATIVE GENERATION")
            print(f"{'='*60}")
            print("Generating investment thesis narratives using LLM...")

            narrative_store = NarrativeStore()
            successful_narratives = []
            failed_narratives = []

            # Run domain narrative agents in parallel
            def run_narrative_agent(domain: str):
                if domain not in NARRATIVE_AGENTS:
                    return None
                agent_class = NARRATIVE_AGENTS[domain]
                agent = agent_class(
                    fact_store=fact_store,
                    reasoning_store=merged_reasoning_store,
                    narrative_store=narrative_store,
                    api_key=ANTHROPIC_API_KEY,
                    model=REASONING_MODEL,  # Use Sonnet for narratives
                    max_tokens=REASONING_MAX_TOKENS
                )
                return agent.generate()

            # Run narrative agents in parallel
            with ThreadPoolExecutor(max_workers=MAX_PARALLEL_AGENTS) as executor:
                futures = {executor.submit(run_narrative_agent, d): d
                          for d in domains_to_analyze if d in NARRATIVE_AGENTS}

                for future in as_completed(futures):
                    domain = futures[future]
                    try:
                        narrative = future.result()
                        if narrative:
                            successful_narratives.append(domain)
                            print(f"  [OK] {domain} narrative complete")
                        else:
                            failed_narratives.append(domain)
                            print(f"  [WARN] {domain} narrative returned no content")
                    except Exception as e:
                        failed_narratives.append(domain)
                        print(f"  [ERR] {domain} narrative failed: {e}")

            # Run cost synthesis agent only if at least one domain narrative succeeded
            if successful_narratives:
                print(f"\nRunning cost synthesis ({len(successful_narratives)} domains succeeded)...")
                cost_agent = CostSynthesisAgent(
                    reasoning_store=merged_reasoning_store,
                    narrative_store=narrative_store,
                    api_key=ANTHROPIC_API_KEY,
                    model=REASONING_MODEL
                )
                cost_agent.generate()
            else:
                print("\n[WARN] No domain narratives succeeded - skipping cost synthesis")

            # Save narrative store (even if partial)
            if successful_narratives:
                narrative_file = (run_paths.root if run_paths else OUTPUT_DIR) / f"narratives_{timestamp}.json"
                narrative_store.save(str(narrative_file))
                print(f"Narratives saved to: {narrative_file}")
                if failed_narratives:
                    print(f"  Note: {len(failed_narratives)} domain(s) failed: {', '.join(failed_narratives)}")
            else:
                print("[WARN] No narratives to save - all domain agents failed")

        # Phase 7: Executive Narrative Synthesis (new in game plan)
        executive_narrative_result = None
        if merged_reasoning_store:
            print(f"\n{'='*60}")
            print("PHASE 7: EXECUTIVE NARRATIVE SYNTHESIS")
            print(f"{'='*60}")

            try:
                # Build deal context for narrative synthesis
                exec_deal_context = {
                    'company_name': args.target_name,
                    'deal_type': args.deal_type.replace('_', '') if hasattr(args, 'deal_type') else 'acquisition'
                }
                if dd_session:
                    exec_deal_context['company_name'] = dd_session.state.deal_context.target_name
                    exec_deal_context['deal_type'] = dd_session.state.deal_context.deal_type

                # Create and run narrative synthesis agent
                narrative_synthesis_agent = NarrativeSynthesisAgent(
                    api_key=ANTHROPIC_API_KEY,
                    model=REASONING_MODEL
                )

                executive_narrative_result = narrative_synthesis_agent.synthesize_quick(
                    reasoning_store=merged_reasoning_store,
                    deal_context=exec_deal_context,
                    fact_store=fact_store
                )

                if executive_narrative_result.get('status') == 'success':
                    # Save executive narrative as JSON
                    exec_narrative_file = (run_paths.root if run_paths else OUTPUT_DIR) / f"executive_narrative_{timestamp}.json"
                    with open(exec_narrative_file, 'w') as f:
                        json.dump(executive_narrative_result['narrative'], f, indent=2)
                    print(f"Executive narrative JSON saved to: {exec_narrative_file}")

                    # Save executive narrative as Markdown
                    exec_narrative_md = (run_paths.reports if run_paths else OUTPUT_DIR) / f"executive_narrative_{timestamp}.md"
                    with open(exec_narrative_md, 'w') as f:
                        f.write(executive_narrative_result['narrative_markdown'])
                    print(f"Executive narrative Markdown saved to: {exec_narrative_md}")

                    # Report validation results
                    validation = executive_narrative_result.get('validation', {})
                    if validation.get('issues'):
                        print(f"  Validation issues: {len(validation['issues'])}")
                        for issue in validation['issues'][:3]:
                            print(f"    - {issue}")
                    print(f"  Quality score: {validation.get('score', 0)}/100")
                else:
                    print(f"[WARN] Executive narrative synthesis failed: {executive_narrative_result.get('error')}")

            except Exception as e:
                print(f"[ERROR] Executive narrative synthesis failed: {e}")
                logger.exception("Executive narrative synthesis error")

        # Phase 8: Narrative Quality Review
        review_result = None
        if executive_narrative_result and executive_narrative_result.get('status') == 'success':
            print(f"\n{'='*60}")
            print("PHASE 8: NARRATIVE QUALITY REVIEW")
            print(f"{'='*60}")

            try:
                review_agent = NarrativeReviewAgent(api_key=ANTHROPIC_API_KEY)
                review_result = review_agent.review(
                    narrative=executive_narrative_result['narrative'],
                    deal_context=exec_deal_context,
                    use_llm=False  # Use fast local review by default
                )

                # Save review result
                review_file = (run_paths.root if run_paths else OUTPUT_DIR) / f"narrative_review_{timestamp}.json"
                with open(review_file, 'w') as f:
                    json.dump(review_result.to_dict(), f, indent=2)
                print(f"Review saved to: {review_file}")

                # Report summary
                print(f"\nReview Result: {'PASS' if review_result.overall_pass else 'NEEDS REVISION'}")
                print(f"Quality Score: {review_result.score:.0f}/100")

                if review_result.issues:
                    critical = [i for i in review_result.issues if i.severity.value == 'critical']
                    major = [i for i in review_result.issues if i.severity.value == 'major']
                    if critical:
                        print(f"  Critical issues: {len(critical)}")
                    if major:
                        print(f"  Major issues: {len(major)}")

                if review_result.improvements:
                    print("\nSuggested improvements:")
                    for imp in review_result.improvements[:3]:
                        print(f"  - {imp}")

            except Exception as e:
                print(f"[WARN] Narrative review failed: {e}")
                logger.exception("Narrative review error")

        # Generate HTML Report
        html_report_file = None
        if merged_reasoning_store:
            print(f"\n{'='*60}")
            print("GENERATING HTML REPORT")
            print(f"{'='*60}")

            html_report_file = generate_html_report(
                fact_store=fact_store,
                reasoning_store=merged_reasoning_store,
                output_dir=run_paths.reports if run_paths else OUTPUT_DIR,
                timestamp=timestamp
            )
            print(f"HTML report saved to: {html_report_file}")

            # Generate Investment Thesis Presentation
            print(f"\n{'='*60}")
            print("GENERATING INVESTMENT THESIS PRESENTATION")
            print(f"{'='*60}")

            if narrative_store and narrative_store.domain_narratives:
                # Use agent-generated narratives (higher quality)
                print("Using agent-generated narratives...")
                presentation_file = generate_presentation_from_narratives(
                    narrative_store=narrative_store,
                    fact_store=fact_store,
                    reasoning_store=merged_reasoning_store,
                    output_dir=run_paths.reports if run_paths else OUTPUT_DIR,
                    target_name=args.target_name,
                    timestamp=timestamp
                )
            else:
                # Use template-based presentation (faster, no LLM)
                print("Using template-based presentation...")
                presentation_file = generate_presentation(
                    fact_store=fact_store,
                    reasoning_store=merged_reasoning_store,
                    output_dir=run_paths.reports if run_paths else OUTPUT_DIR,
                    target_name=args.target_name,
                    timestamp=timestamp
                )
            print(f"Investment thesis saved to: {presentation_file}")

            # Generate Excel Export
            if OPENPYXL_AVAILABLE:
                print(f"\n{'='*60}")
                print("GENERATING EXCEL EXPORT")
                print(f"{'='*60}")

                excel_file = (run_paths.exports if run_paths else OUTPUT_DIR) / f"findings_{timestamp}.xlsx"
                vdr_pack_obj = None
                if vdr_results:
                    # Import VDRRequestPack for type checking
                    from tools_v2.vdr_generator import VDRRequestPack
                    vdr_data = vdr_results.get('vdr_pack', {})
                    if isinstance(vdr_data, dict) and 'requests' in vdr_data:
                        # Reconstruct VDRRequestPack from dict
                        vdr_pack_obj = VDRRequestPack.from_dict(vdr_data)

                try:
                    export_to_excel(
                        fact_store=fact_store,
                        reasoning_store=merged_reasoning_store,
                        output_path=excel_file,
                        target_name=args.target_name,
                        include_vdr=True if vdr_pack_obj else False,
                        vdr_pack=vdr_pack_obj
                    )
                    print(f"Excel export saved to: {excel_file}")
                except Exception as e:
                    print(f"[WARN] Excel export failed: {e}")
            else:
                print("\n[INFO] Excel export skipped (openpyxl not installed)")

        # Final summary
        print(f"\n{'='*60}")
        print("ANALYSIS COMPLETE")
        print(f"{'='*60}")

        # Summary by domain
        total_facts = 0
        total_gaps = 0
        total_risks = 0
        total_work_items = 0

        for domain in domains_to_analyze:
            domain_facts = fact_store.get_domain_facts(domain)
            total_facts += domain_facts['fact_count']
            total_gaps += domain_facts['gap_count']

            if domain in all_reasoning_results:
                result = all_reasoning_results[domain]
                if result.get('findings'):
                    summary = result['findings'].get('summary', {})
                    total_risks += summary.get('risks', 0)
                    total_work_items += summary.get('work_items', 0)

        print(f"\nTotal Facts: {total_facts}")
        print(f"Total Gaps: {total_gaps}")
        print(f"Coverage Grade: {coverage_results['grade']}")

        if all_reasoning_results:
            print(f"\nTotal Risks: {total_risks}")
            print(f"Total Work Items: {total_work_items}")

            if synthesis_results:
                cost = synthesis_results['synthesis']['cost_summary']['total']
                print(f"Total Cost Range: ${cost['low']:,} - ${cost['high']:,}")

            # Per-domain breakdown
            print("\nPer-Domain Summary:")
            for domain in domains_to_analyze:
                domain_facts = fact_store.get_domain_facts(domain)
                if domain in all_reasoning_results and all_reasoning_results[domain].get('findings'):
                    summary = all_reasoning_results[domain]['findings'].get('summary', {})
                    print(f"  {domain}: {domain_facts['fact_count']} facts, "
                          f"{summary.get('risks', 0)} risks, {summary.get('work_items', 0)} work items")
                else:
                    print(f"  {domain}: {domain_facts['fact_count']} facts")

        if vdr_results:
            print(f"\nVDR Requests: {vdr_results['vdr_pack']['total_requests']} "
                  f"(Critical: {vdr_results['vdr_pack']['by_priority']['critical']})")

        # Save session state if using sessions
        if dd_session:
            # Store reasoning results in session
            if merged_reasoning_store:
                dd_session.reasoning_store = merged_reasoning_store
            if narrative_store:
                dd_session.narrative_store = narrative_store
            dd_session.state.current_phase = "complete"
            dd_session.save()
            print(f"\nSession saved: {dd_session.session_id}")

        # Update run metadata with final counts
        if run_paths:
            run_manager = get_run_manager()
            run_manager.complete_run(
                run_id=run_paths.root.name,
                facts_count=total_facts,
                risks_count=total_risks,
                work_items_count=total_work_items,
                gaps_count=total_gaps
            )
            print(f"\nRun completed: {run_paths.root.name}")

        print("\nOutputs:")
        if run_paths:
            print(f"  Run Directory: {run_paths.root}")
        print(f"  Facts: {facts_file}")
        if findings_file:
            print(f"  Findings: {findings_file}")
        print(f"  Coverage: {coverage_file}")
        if synthesis_results:
            print(f"  Synthesis: {synthesis_file}")
            print(f"  Executive Summary: {exec_summary_file}")
        if vdr_results:
            print(f"  VDR Requests: {vdr_file}")
            print(f"  VDR Markdown: {vdr_md_file}")
        if html_report_file:
            print(f"  HTML Report: {html_report_file}")

        # Enter interactive mode if requested
        if args.interactive:
            print(f"\n{'='*60}")
            print("ENTERING INTERACTIVE MODE")
            print(f"{'='*60}")
            print("Type 'help' for commands, 'exit' to quit.\n")

            # Create session from analysis results
            session = Session(
                fact_store=fact_store,
                reasoning_store=merged_reasoning_store or ReasoningStore(fact_store=fact_store),
                deal_context=deal_context if 'deal_context' in dir() else {}
            )
            session.source_files = {
                'facts': str(facts_file),
                'findings': str(findings_file) if findings_file else None
            }

            cli = InteractiveCLI(session)
            cli.run()

    except KeyboardInterrupt:
        print("\n\n[INTERRUPTED] Analysis stopped by user")
        sys.exit(1)
    except Exception as e:
        logger.exception("Analysis failed")
        print(f"\n[ERROR] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
