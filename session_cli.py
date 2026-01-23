#!/usr/bin/env python3
"""
Session-Based IT Due Diligence CLI

Enables incremental analysis workflow:
- Create sessions for deals
- Add documents incrementally
- Re-run analysis without starting over
- Track changes across VDR rounds

Usage:
    # Create a new session
    python session_cli.py create acme_2024 --target "Acme Corp" --deal-type carve_out

    # Add documents and run discovery
    python session_cli.py add acme_2024 data/input/
    python session_cli.py discover acme_2024

    # Run reasoning
    python session_cli.py reason acme_2024

    # Later: Add more docs (only processes new/changed)
    python session_cli.py add acme_2024 data/vdr_round2/
    python session_cli.py discover acme_2024
    python session_cli.py reason acme_2024

    # Generate outputs
    python session_cli.py export acme_2024 --output ./deliverables/

    # List all sessions
    python session_cli.py list

    # Show session status
    python session_cli.py status acme_2024
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime

from config_v2 import (
    ANTHROPIC_API_KEY,
    DISCOVERY_MODEL,
    REASONING_MODEL,
    DISCOVERY_MAX_TOKENS,
    REASONING_MAX_TOKENS,
    DISCOVERY_MAX_ITERATIONS,
    REASONING_MAX_ITERATIONS,
    OUTPUT_DIR,
    DOMAINS,
)
from tools_v2.session import DDSession
from tools_v2.reasoning_tools import ReasoningStore
from agents_v2.discovery import DISCOVERY_AGENTS
from agents_v2.reasoning import REASONING_AGENTS
import threading


# Thread-safe lock for FactStore operations
_fact_store_lock = threading.Lock()


def cmd_create(args):
    """Create a new session."""
    try:
        session = DDSession.create(
            session_id=args.session_id,
            target_name=args.target,
            deal_type=args.deal_type,
            buyer_name=args.buyer,
            industry=args.industry
        )

        print(f"\n{'='*60}")
        print(f"SESSION CREATED: {args.session_id}")
        print(f"{'='*60}")
        print(f"Target: {args.target}")
        print(f"Deal Type: {args.deal_type}")
        if args.buyer:
            print(f"Buyer: {args.buyer}")
        if args.industry:
            print(f"Industry: {args.industry}")
        print(f"Session Dir: {session.session_dir}")
        print("\nNext steps:")
        print(f"  1. Add documents: python session_cli.py add {args.session_id} <path>")
        print(f"  2. Run discovery: python session_cli.py discover {args.session_id}")
        print(f"  3. Run reasoning: python session_cli.py reason {args.session_id}")

    except ValueError as e:
        print(f"[ERROR] {e}")
        sys.exit(1)


def cmd_list(args):
    """List all sessions."""
    sessions = DDSession.list_sessions()

    if not sessions:
        print("\nNo sessions found.")
        print("Create one with: python session_cli.py create <session_id> --target <name>")
        return

    print(f"\n{'='*60}")
    print("AVAILABLE SESSIONS")
    print(f"{'='*60}")

    for s in sessions:
        print(f"\n  {s['session_id']}")
        print(f"    Target: {s['target_name']}")
        print(f"    Type: {s['deal_type']}")
        if s.get('industry'):
            print(f"    Industry: {s['industry']}")
        print(f"    Phase: {s['current_phase']}")
        print(f"    Docs: {s['document_count']} | Runs: {s['run_count']}")
        print(f"    Updated: {s['updated_at'][:19]}")


def cmd_status(args):
    """Show session status."""
    try:
        session = DDSession.load(args.session_id)
    except ValueError as e:
        print(f"[ERROR] {e}")
        sys.exit(1)

    print(f"\n{'='*60}")
    print(f"SESSION: {session.session_id}")
    print(f"{'='*60}")

    # Deal context
    ctx = session.state.deal_context
    print("\nDeal Context:")
    print(f"  Target: {ctx.target_name}")
    print(f"  Type: {ctx.deal_type}")
    if ctx.buyer_name:
        print(f"  Buyer: {ctx.buyer_name}")
    if ctx.industry:
        print(f"  Industry: {ctx.industry}")

    # Current state
    print("\nCurrent State:")
    print(f"  Phase: {session.state.current_phase}")
    print(f"  Documents: {len(session.state.processed_documents)}")
    print(f"  Facts: {len(session.fact_store.facts)}")
    print(f"  Gaps: {len(session.fact_store.gaps)}")
    print(f"  Risks: {len(session.reasoning_store.risks)}")
    print(f"  Work Items: {len(session.reasoning_store.work_items)}")

    # Pending documents
    pending = session.get_pending_documents()
    if pending:
        print(f"\nPending Documents: {len(pending)}")
        for p in pending[:5]:
            print(f"    - {p.name}")
        if len(pending) > 5:
            print(f"    ... and {len(pending) - 5} more")

    # Change summary
    changes = session.get_change_summary()
    print("\nNeeds Processing:")
    print(f"  Discovery: {'Yes' if changes['needs_discovery'] else 'No'}")
    print(f"  Reasoning: {'Yes' if changes['needs_reasoning'] else 'No'}")

    # Recent runs
    runs = session.get_run_history()[-3:]
    if runs:
        print("\nRecent Runs:")
        for r in reversed(runs):
            status_icon = "✓" if r.status == "completed" else "✗" if r.status == "failed" else "..."
            print(f"  [{status_icon}] {r.run_id} - {r.phase}")


def cmd_add(args):
    """Add documents to session."""
    try:
        session = DDSession.load(args.session_id)
    except ValueError as e:
        print(f"[ERROR] {e}")
        sys.exit(1)

    # Gather documents from path
    input_path = Path(args.path)
    if not input_path.exists():
        print(f"[ERROR] Path not found: {input_path}")
        sys.exit(1)

    if input_path.is_file():
        documents = [input_path]
    else:
        # Get all supported files
        documents = []
        for ext in ['*.pdf', '*.txt', '*.md']:
            documents.extend(input_path.glob(ext))

    if not documents:
        print(f"[ERROR] No supported documents found in: {input_path}")
        sys.exit(1)

    print(f"\n{'='*60}")
    print(f"ADDING DOCUMENTS TO: {args.session_id}")
    print(f"{'='*60}")
    print(f"Found {len(documents)} documents")

    # Add documents (checks for new/changed)
    result = session.add_documents(documents, entity=args.entity)

    print("\nResults:")
    print(f"  New: {len(result['new'])}")
    print(f"  Changed: {len(result['changed'])}")
    print(f"  Unchanged: {len(result['unchanged'])}")

    if result['new']:
        print("\nNew documents:")
        for f in result['new'][:10]:
            print(f"    + {f}")
        if len(result['new']) > 10:
            print(f"    ... and {len(result['new']) - 10} more")

    if result['changed']:
        print("\nChanged documents:")
        for f in result['changed']:
            print(f"    ~ {f}")

    # Save session state
    session.save()

    pending = session.get_pending_documents()
    if pending:
        print(f"\n{len(pending)} documents queued for processing")
        print(f"Run: python session_cli.py discover {args.session_id}")


def cmd_discover(args):
    """Run discovery on pending documents."""
    try:
        session = DDSession.load(args.session_id)
    except ValueError as e:
        print(f"[ERROR] {e}")
        sys.exit(1)

    pending = session.get_pending_documents()
    if not pending:
        print("\nNo pending documents to process.")
        print(f"Add documents with: python session_cli.py add {args.session_id} <path>")
        return

    print(f"\n{'='*60}")
    print(f"DISCOVERY: {args.session_id}")
    print(f"{'='*60}")
    print(f"Processing {len(pending)} documents")
    print(f"Domains: {', '.join(args.domains)}")

    # Check API key
    if not ANTHROPIC_API_KEY:
        print("[ERROR] ANTHROPIC_API_KEY not set")
        sys.exit(1)

    # Load document text
    from ingestion.pdf_parser import parse_pdfs

    combined_text = ""
    for doc_path in pending:
        print(f"\nLoading: {doc_path.name}")
        if doc_path.suffix.lower() == '.pdf':
            text = parse_pdfs(doc_path)
        else:
            with open(doc_path) as f:
                text = f.read()
        combined_text += f"\n\n# Source: {doc_path.name}\n\n{text}"

    print(f"\nLoaded {len(combined_text):,} characters")

    # Start run
    _ = session.start_run("discovery", args.domains)

    try:
        # For each document being processed, we'll track facts
        facts_before = len(session.fact_store.facts)

        # Run discovery for each domain
        for domain in args.domains:
            if domain not in DISCOVERY_AGENTS:
                print(f"[WARN] No discovery agent for: {domain}")
                continue

            print(f"\n{'='*40}")
            print(f"Discovery: {domain.upper()}")
            print(f"{'='*40}")

            agent_class = DISCOVERY_AGENTS[domain]

            # Build agent kwargs - base parameters for all agents
            agent_kwargs = {
                "fact_store": session.fact_store,
                "api_key": ANTHROPIC_API_KEY,
                "model": DISCOVERY_MODEL,
                "max_tokens": DISCOVERY_MAX_TOKENS,
                "max_iterations": DISCOVERY_MAX_ITERATIONS
            }

            # For applications domain, pass industry for industry-aware discovery
            if domain == "applications" and session.state.deal_context.industry:
                agent_kwargs["industry"] = session.state.deal_context.industry
                print(f"  Industry-aware discovery: {session.state.deal_context.industry}")

            agent = agent_class(**agent_kwargs)

            # Run discovery
            result = agent.discover(combined_text)

            print(f"  Facts: {result['metrics'].get('facts_extracted', 0)}")
            print(f"  Gaps: {result['metrics'].get('gaps_flagged', 0)}")

        # Mark documents as processed
        for doc_path in pending:
            facts_from_doc = len([f for f in session.fact_store.facts
                                  if f.source_document == doc_path.name])
            session.mark_document_processed(doc_path, fact_count=facts_from_doc)

        facts_added = len(session.fact_store.facts) - facts_before
        session.complete_run(facts_added=facts_added)
        session.state.current_phase = "discovery"
        session.save()

        print(f"\n{'='*60}")
        print("DISCOVERY COMPLETE")
        print(f"{'='*60}")
        print(f"Facts added: {facts_added}")
        print(f"Total facts: {len(session.fact_store.facts)}")
        print(f"Total gaps: {len(session.fact_store.gaps)}")
        print(f"\nNext: python session_cli.py reason {args.session_id}")

    except Exception as e:
        session.fail_run(str(e))
        session.save()
        print(f"\n[ERROR] Discovery failed: {e}")
        sys.exit(1)


def cmd_reason(args):
    """Run reasoning on discovered facts."""
    try:
        session = DDSession.load(args.session_id)
    except ValueError as e:
        print(f"[ERROR] {e}")
        sys.exit(1)

    if len(session.fact_store.facts) == 0:
        print("\nNo facts to reason about.")
        print(f"Run discovery first: python session_cli.py discover {args.session_id}")
        return

    print(f"\n{'='*60}")
    print(f"REASONING: {args.session_id}")
    print(f"{'='*60}")
    print(f"Facts available: {len(session.fact_store.facts)}")
    print(f"Domains: {', '.join(args.domains)}")

    # Check API key
    if not ANTHROPIC_API_KEY:
        print("[ERROR] ANTHROPIC_API_KEY not set")
        sys.exit(1)

    # Get deal context for prompts
    deal_context = session.get_deal_context_dict()
    _ = session.get_deal_context_for_prompts()

    print(f"\nDeal Type: {deal_context['deal_type']}")

    # Start run
    _ = session.start_run("reasoning", args.domains)

    # Clear existing reasoning (we re-run on full fact set)
    session.reasoning_store = ReasoningStore(fact_store=session.fact_store)

    try:
        for domain in args.domains:
            if domain not in REASONING_AGENTS:
                print(f"[WARN] No reasoning agent for: {domain}")
                continue

            # Check if domain has facts
            domain_facts = session.fact_store.get_domain_facts(domain)
            if domain_facts['fact_count'] == 0:
                print(f"\n[SKIP] {domain}: No facts")
                continue

            print(f"\n{'='*40}")
            print(f"Reasoning: {domain.upper()}")
            print(f"{'='*40}")
            print(f"  Input facts: {domain_facts['fact_count']}")

            agent_class = REASONING_AGENTS[domain]
            agent = agent_class(
                fact_store=session.fact_store,
                api_key=ANTHROPIC_API_KEY,
                model=REASONING_MODEL,
                max_tokens=REASONING_MAX_TOKENS,
                max_iterations=REASONING_MAX_ITERATIONS
            )

            # Run reasoning with deal context
            result = agent.reason(deal_context)

            # Merge into session reasoning store
            findings = result.get('findings', {})

            for risk in findings.get('risks', []):
                session.reasoning_store.add_risk(
                    domain=risk.get('domain', domain),
                    title=risk['title'],
                    description=risk['description'],
                    category=risk['category'],
                    severity=risk['severity'],
                    integration_dependent=risk.get('integration_dependent', False),
                    mitigation=risk.get('mitigation', ''),
                    based_on_facts=risk.get('based_on_facts', []),
                    confidence=risk.get('confidence', 'medium'),
                    reasoning=risk.get('reasoning', '')
                )

            for wi in findings.get('work_items', []):
                session.reasoning_store.add_work_item(
                    domain=wi.get('domain', domain),
                    title=wi['title'],
                    description=wi['description'],
                    phase=wi['phase'],
                    priority=wi['priority'],
                    owner_type=wi['owner_type'],
                    triggered_by=wi.get('triggered_by', []),
                    based_on_facts=wi.get('based_on_facts', []),
                    confidence=wi.get('confidence', 'medium'),
                    reasoning=wi.get('reasoning', ''),
                    cost_estimate=wi.get('cost_estimate', '25k_to_100k'),
                    triggered_by_risks=wi.get('triggered_by_risks', []),
                    dependencies=wi.get('dependencies', [])
                )

            summary = findings.get('summary', {})
            print(f"  Risks: {summary.get('risks', 0)}")
            print(f"  Work items: {summary.get('work_items', 0)}")

        session.complete_run()
        session.state.current_phase = "reasoning"
        session.save()

        print(f"\n{'='*60}")
        print("REASONING COMPLETE")
        print(f"{'='*60}")
        print(f"Total risks: {len(session.reasoning_store.risks)}")
        print(f"Total work items: {len(session.reasoning_store.work_items)}")
        print(f"\nNext: python session_cli.py export {args.session_id}")

    except Exception as e:
        session.fail_run(str(e))
        session.save()
        print(f"\n[ERROR] Reasoning failed: {e}")
        sys.exit(1)


def cmd_export(args):
    """Export session outputs."""
    try:
        session = DDSession.load(args.session_id)
    except ValueError as e:
        print(f"[ERROR] {e}")
        sys.exit(1)

    output_dir = Path(args.output) if args.output else OUTPUT_DIR / args.session_id

    print(f"\n{'='*60}")
    print(f"EXPORTING: {args.session_id}")
    print(f"{'='*60}")
    print(f"Output directory: {output_dir}")

    outputs = session.export_outputs(output_dir)

    print("\nExported files:")
    for name, path in outputs.items():
        print(f"  {name}: {path}")

    # Also generate reports if we have reasoning data
    if len(session.reasoning_store.risks) > 0 or len(session.reasoning_store.work_items) > 0:
        from tools_v2.html_report import generate_html_report
        from tools_v2.presentation import generate_presentation

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        print("\nGenerating reports...")

        html_file = generate_html_report(
            fact_store=session.fact_store,
            reasoning_store=session.reasoning_store,
            output_dir=output_dir,
            timestamp=timestamp
        )
        print(f"  HTML Report: {html_file}")

        presentation_file = generate_presentation(
            fact_store=session.fact_store,
            reasoning_store=session.reasoning_store,
            output_dir=output_dir,
            target_name=session.state.deal_context.target_name,
            timestamp=timestamp
        )
        print(f"  Investment Thesis: {presentation_file}")


def cmd_context(args):
    """Show or update deal context."""
    try:
        session = DDSession.load(args.session_id)
    except ValueError as e:
        print(f"[ERROR] {e}")
        sys.exit(1)

    if args.show:
        # Show deal context and prompt injection
        print(f"\n{'='*60}")
        print(f"DEAL CONTEXT: {args.session_id}")
        print(f"{'='*60}")
        print(session.get_deal_context_for_prompts())
        return

    # Update context
    updates = {}
    if args.deal_type:
        updates['deal_type'] = args.deal_type
    if args.buyer:
        updates['buyer_name'] = args.buyer
    if args.industry:
        updates['industry'] = args.industry

    if updates:
        session.update_deal_context(**updates)
        session.save()
        print(f"Deal context updated: {updates}")
    else:
        print("No updates specified. Use --show to view current context.")


def main():
    parser = argparse.ArgumentParser(
        description="Session-Based IT Due Diligence CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Create command
    create_parser = subparsers.add_parser("create", help="Create a new session")
    create_parser.add_argument("session_id", help="Unique session identifier")
    create_parser.add_argument("--target", "-t", required=True, help="Target company name")
    create_parser.add_argument("--deal-type", "-d", choices=["carve_out", "bolt_on", "platform"],
                               default="platform", help="Deal type")
    create_parser.add_argument("--buyer", "-b", help="Buyer company name")
    create_parser.add_argument("--industry", "-i", help="Industry vertical")

    # List command
    _ = subparsers.add_parser("list", help="List all sessions")

    # Status command
    status_parser = subparsers.add_parser("status", help="Show session status")
    status_parser.add_argument("session_id", help="Session identifier")

    # Add command
    add_parser = subparsers.add_parser("add", help="Add documents to session")
    add_parser.add_argument("session_id", help="Session identifier")
    add_parser.add_argument("path", help="Path to document or directory")
    add_parser.add_argument("--entity", "-e", choices=["target", "buyer"],
                           default="target", help="Entity the documents describe")

    # Discover command
    discover_parser = subparsers.add_parser("discover", help="Run discovery on pending documents")
    discover_parser.add_argument("session_id", help="Session identifier")
    discover_parser.add_argument("--domains", "-d", nargs="+", default=DOMAINS,
                                 choices=DOMAINS, help="Domains to analyze")

    # Reason command
    reason_parser = subparsers.add_parser("reason", help="Run reasoning on discovered facts")
    reason_parser.add_argument("session_id", help="Session identifier")
    reason_parser.add_argument("--domains", "-d", nargs="+", default=DOMAINS,
                               choices=DOMAINS, help="Domains to analyze")

    # Export command
    export_parser = subparsers.add_parser("export", help="Export session outputs")
    export_parser.add_argument("session_id", help="Session identifier")
    export_parser.add_argument("--output", "-o", help="Output directory")

    # Context command
    context_parser = subparsers.add_parser("context", help="Show or update deal context")
    context_parser.add_argument("session_id", help="Session identifier")
    context_parser.add_argument("--show", "-s", action="store_true", help="Show full context")
    context_parser.add_argument("--deal-type", "-d", choices=["carve_out", "bolt_on", "platform"])
    context_parser.add_argument("--buyer", "-b", help="Buyer company name")
    context_parser.add_argument("--industry", "-i", help="Industry vertical")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Route to command
    commands = {
        "create": cmd_create,
        "list": cmd_list,
        "status": cmd_status,
        "add": cmd_add,
        "discover": cmd_discover,
        "reason": cmd_reason,
        "export": cmd_export,
        "context": cmd_context,
    }

    commands[args.command](args)


if __name__ == "__main__":
    main()
