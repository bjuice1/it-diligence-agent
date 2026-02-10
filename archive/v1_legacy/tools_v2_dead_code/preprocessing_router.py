"""
Preprocessing Router

Routes documents through the appropriate extraction path:
1. Structured data (tables) -> Deterministic parser (100% reliable)
2. Unstructured data (prose) -> LLM discovery agents (probabilistic)

This ensures structured inventories are extracted perfectly while
still leveraging LLM capabilities for unstructured content.
"""

import logging
from typing import Dict, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass, field

from tools_v2.deterministic_parser import (
    preprocess_document,
    ParserResult,
    extract_markdown_tables,
    detect_table_type,
    parse_markdown_table
)

logger = logging.getLogger(__name__)


@dataclass
class RoutingResult:
    """Result of routing a document through preprocessing"""
    # Deterministic extraction results
    tables_found: int = 0
    tables_parsed: int = 0
    facts_from_tables: int = 0

    # What's left for LLM
    remaining_text: str = ""
    remaining_text_length: int = 0

    # Routing decision
    needs_llm_discovery: bool = True
    skip_domains: list = field(default_factory=list)  # Domains fully covered by deterministic parse

    # Metadata
    document_name: str = ""
    errors: list = field(default_factory=list)


def route_document(
    document_text: str,
    fact_store: "FactStore",
    document_name: str = "",
    entity: str = "target"
) -> RoutingResult:
    """
    Route a document through preprocessing.

    1. Detect structured tables
    2. Parse them deterministically into FactStore
    3. Return remaining text for LLM discovery

    Args:
        document_text: Full document text
        fact_store: FactStore instance
        document_name: Source filename
        entity: "target" or "buyer"

    Returns:
        RoutingResult with preprocessing stats and remaining text
    """
    result = RoutingResult(document_name=document_name)

    logger.info(f"Routing document: {document_name} ({len(document_text)} chars)")

    # Run preprocessing
    parser_result = preprocess_document(
        document_text=document_text,
        fact_store=fact_store,
        entity=entity,
        source_document=document_name
    )

    # Populate result
    result.tables_found = len(extract_markdown_tables(document_text))
    result.tables_parsed = len(parser_result.tables)
    result.facts_from_tables = parser_result.facts_created
    result.remaining_text = parser_result.remaining_text
    result.remaining_text_length = len(parser_result.remaining_text)
    result.errors = parser_result.errors

    # Determine if LLM discovery is still needed
    if result.facts_from_tables > 0:
        logger.info(
            f"Deterministic parse: {result.facts_from_tables} facts from "
            f"{result.tables_parsed} tables"
        )

    # Check what domains were covered by deterministic parsing
    domains_covered = set()
    for table in parser_result.tables:
        if table.table_type == "application_inventory":
            domains_covered.add("applications")
        elif table.table_type == "infrastructure_inventory":
            domains_covered.add("infrastructure")
        elif table.table_type == "contract_inventory":
            domains_covered.add("organization")

    # If remaining text is very short, might not need LLM at all
    meaningful_remaining = _has_meaningful_content(result.remaining_text)

    if not meaningful_remaining:
        result.needs_llm_discovery = False
        logger.info("No meaningful unstructured content remaining - skipping LLM discovery")
    else:
        # Still need LLM for unstructured portions, but can skip fully-covered domains
        result.skip_domains = list(domains_covered)
        if result.skip_domains:
            logger.info(f"Domains fully covered by deterministic parse: {result.skip_domains}")

    return result


def _has_meaningful_content(text: str) -> bool:
    """Check if text has meaningful content beyond markers and whitespace"""
    # Remove table markers and whitespace
    import re
    cleaned = re.sub(r'\[TABLE PARSED:[^\]]+\]', '', text)
    cleaned = re.sub(r'[\s\n\r]+', ' ', cleaned).strip()

    # Check if there's substantial content left
    # Arbitrary threshold: at least 200 chars of real content
    return len(cleaned) > 200


# =============================================================================
# INTEGRATION WITH MAIN PIPELINE
# =============================================================================

def run_hybrid_discovery(
    document_text: str,
    fact_store: "FactStore",
    document_name: str = "",
    entity: str = "target",
    api_key: str = "",
    run_llm_discovery: bool = True
) -> Dict[str, Any]:
    """
    Run hybrid discovery: deterministic parsing + optional LLM discovery.

    This is the main entry point that replaces direct calls to discovery agents
    when you want to leverage deterministic parsing for structured content.

    Args:
        document_text: Full document text
        fact_store: FactStore instance
        document_name: Source filename
        entity: "target" or "buyer"
        api_key: Anthropic API key (for LLM discovery)
        run_llm_discovery: Whether to run LLM discovery on remaining content

    Returns:
        Dict with:
        - deterministic_facts: Facts from table parsing
        - llm_facts: Facts from LLM discovery (if run)
        - total_facts: Combined total
        - routing: RoutingResult details
    """
    results = {
        "deterministic_facts": 0,
        "llm_facts": 0,
        "total_facts": 0,
        "routing": None,
        "domains_processed": []
    }

    # Step 1: Route and parse structured content
    routing = route_document(
        document_text=document_text,
        fact_store=fact_store,
        document_name=document_name,
        entity=entity
    )

    results["deterministic_facts"] = routing.facts_from_tables
    results["routing"] = {
        "tables_found": routing.tables_found,
        "tables_parsed": routing.tables_parsed,
        "facts_from_tables": routing.facts_from_tables,
        "remaining_text_length": routing.remaining_text_length,
        "needs_llm_discovery": routing.needs_llm_discovery,
        "skip_domains": routing.skip_domains
    }

    # Step 2: Run LLM discovery on remaining content (if needed)
    if run_llm_discovery and routing.needs_llm_discovery and api_key:
        logger.info("Running LLM discovery on remaining unstructured content...")

        # Import discovery agents
        from agents_v2.discovery.applications_discovery import ApplicationsDiscoveryAgent
        from agents_v2.discovery.infrastructure_discovery import InfrastructureDiscoveryAgent
        from agents_v2.discovery.network_discovery import NetworkDiscoveryAgent
        from agents_v2.discovery.cybersecurity_discovery import CybersecurityDiscoveryAgent
        from agents_v2.discovery.identity_access_discovery import IdentityAccessDiscoveryAgent
        from agents_v2.discovery.organization_discovery import OrganizationDiscoveryAgent

        # Map domains to agents
        domain_agents = {
            "applications": ApplicationsDiscoveryAgent,
            "infrastructure": InfrastructureDiscoveryAgent,
            "network": NetworkDiscoveryAgent,
            "cybersecurity": CybersecurityDiscoveryAgent,
            "identity_access": IdentityAccessDiscoveryAgent,
            "organization": OrganizationDiscoveryAgent
        }

        # Run agents for domains NOT covered by deterministic parsing
        for domain, agent_class in domain_agents.items():
            if domain in routing.skip_domains:
                logger.info(f"Skipping {domain} - already covered by deterministic parse")
                continue

            try:
                agent = agent_class(
                    fact_store=fact_store,
                    api_key=api_key
                )

                discovery_result = agent.discover(
                    document_text=routing.remaining_text,
                    document_name=document_name,
                    entity=entity
                )

                results["llm_facts"] += discovery_result.get("metrics", {}).get("facts_extracted", 0)
                results["domains_processed"].append(domain)

            except Exception as e:
                logger.error(f"LLM discovery failed for {domain}: {e}")

    results["total_facts"] = results["deterministic_facts"] + results["llm_facts"]

    return results


# =============================================================================
# ANALYSIS HELPERS
# =============================================================================

def analyze_document_structure(document_text: str) -> Dict[str, Any]:
    """
    Analyze a document to understand its structure before processing.

    Useful for debugging or deciding how to process a document.

    Returns:
        Dict with structure analysis:
        - total_chars: Document length
        - tables: List of detected tables with types
        - structured_percentage: How much is in tables
        - recommendation: "deterministic", "llm", or "hybrid"
    """
    analysis = {
        "total_chars": len(document_text),
        "tables": [],
        "structured_chars": 0,
        "unstructured_chars": 0,
        "structured_percentage": 0.0,
        "recommendation": "hybrid"
    }

    # Extract and analyze tables
    table_tuples = extract_markdown_tables(document_text)

    for table_text, start, end in table_tuples:
        parsed = parse_markdown_table(table_text)
        if parsed:
            table_type = detect_table_type(parsed)
            analysis["tables"].append({
                "type": table_type,
                "headers": parsed.headers[:5],  # First 5 headers
                "rows": len(parsed.rows),
                "chars": len(table_text)
            })
            if table_type != "unknown":
                analysis["structured_chars"] += len(table_text)

    analysis["unstructured_chars"] = analysis["total_chars"] - analysis["structured_chars"]
    if analysis["total_chars"] > 0:
        analysis["structured_percentage"] = (
            analysis["structured_chars"] / analysis["total_chars"] * 100
        )

    # Recommendation
    if analysis["structured_percentage"] > 80:
        analysis["recommendation"] = "deterministic"
    elif analysis["structured_percentage"] < 20:
        analysis["recommendation"] = "llm"
    else:
        analysis["recommendation"] = "hybrid"

    return analysis


# =============================================================================
# CLI FOR TESTING
# =============================================================================

if __name__ == "__main__":
    import sys
    import json

    if len(sys.argv) < 2:
        print("Usage: python preprocessing_router.py <document_file>")
        print("       python preprocessing_router.py --analyze <document_file>")
        sys.exit(1)

    analyze_only = "--analyze" in sys.argv
    file_path = sys.argv[-1]

    with open(file_path, 'r') as f:
        text = f.read()

    if analyze_only:
        analysis = analyze_document_structure(text)
        print("\nDocument Structure Analysis")
        print("=" * 50)
        print(f"Total characters: {analysis['total_chars']:,}")
        print(f"Structured (tables): {analysis['structured_chars']:,} ({analysis['structured_percentage']:.1f}%)")
        print(f"Unstructured: {analysis['unstructured_chars']:,}")
        print(f"\nRecommendation: {analysis['recommendation'].upper()}")
        print(f"\nTables found: {len(analysis['tables'])}")
        for i, table in enumerate(analysis['tables'], 1):
            print(f"  {i}. {table['type']}: {table['rows']} rows")
            print(f"     Headers: {table['headers']}")
    else:
        # Mock FactStore for testing
        class MockFactStore:
            def __init__(self):
                self.facts = []
                self.fact_counter = 0

            def add_fact(self, **kwargs):
                self.fact_counter += 1
                fact_id = f"F-{kwargs.get('domain', 'X')[:3].upper()}-{self.fact_counter:03d}"
                self.facts.append({"fact_id": fact_id, **kwargs})
                return fact_id

        mock_store = MockFactStore()

        result = route_document(
            document_text=text,
            fact_store=mock_store,
            document_name=file_path,
            entity="target"
        )

        print("\nRouting Result")
        print("=" * 50)
        print(f"Tables found: {result.tables_found}")
        print(f"Tables parsed: {result.tables_parsed}")
        print(f"Facts from tables: {result.facts_from_tables}")
        print(f"Remaining text: {result.remaining_text_length:,} chars")
        print(f"Needs LLM discovery: {result.needs_llm_discovery}")
        print(f"Skip domains: {result.skip_domains}")

        if result.errors:
            print(f"\nErrors: {result.errors}")

        print(f"\nFacts created:")
        for fact in mock_store.facts[:5]:
            print(f"  {fact['fact_id']}: {fact.get('item', 'N/A')}")
        if len(mock_store.facts) > 5:
            print(f"  ... and {len(mock_store.facts) - 5} more")
