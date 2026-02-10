#!/usr/bin/env python3
"""
IT Diligence Analysis Agent - Main Entry Point

Orchestrates the full analysis pipeline:
1. Parse PDF documents
2. Run domain agents (Infrastructure, Network, Cybersecurity, Applications, Identity & Access, Organization)
   - NOW RUNS IN PARALLEL for ~5x speedup
3. Coordinate and synthesize findings
4. Generate output reports
5. Persist findings to database (Points 65-69 of 115PP)

Usage:
    python main.py                          # Analyze PDFs in data/input/
    python main.py path/to/document.pdf     # Analyze specific PDF
    python main.py path/to/folder/          # Analyze all PDFs in folder
"""
import sys
import json
import logging
import hashlib
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

from generate_viewer import generate_viewer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from config import INPUT_DIR, OUTPUT_DIR, ANTHROPIC_API_KEY
from ingestion.pdf_parser import parse_pdfs
from tools.analysis_tools import AnalysisStore
from agents import (
    InfrastructureAgent,
    NetworkAgent,
    CybersecurityAgent,
    ApplicationsAgent,
    IdentityAccessAgent,
    OrganizationAgent,
    CoordinatorAgent
)

# Point 65: Import storage layer
from storage import Database, Repository, Document, AnalysisRun
from storage.models import generate_id, now_iso

# Cost refinement module
from agents.cost_refinement_agent import refine_all_work_items

# Review agent module
from agents.review_agent import ReviewAgent

# Question workflow module
from tools.question_workflow import (
    QuestionWorkflow,
    export_questions_to_excel,
)

# Excel export module
from tools.excel_export import export_findings_to_excel


def run_single_agent(agent_class, agent_name: str, document_text: str, deal_context: dict) -> dict:
    """
    Run a single domain agent in its own thread.

    Creates a fresh AnalysisStore for the agent to avoid thread conflicts.
    Returns the agent's store and reasoning chain for merging.

    Args:
        agent_class: The agent class to instantiate
        agent_name: Name for logging (e.g., "Infrastructure")
        document_text: Document to analyze
        deal_context: Deal context dict

    Returns:
        Dict with 'store', 'reasoning_chain', 'domain', 'metrics', 'error'
    """
    start_time = time.time()

    try:
        # Create isolated store for this agent
        agent_store = AnalysisStore()

        # Create and run agent
        agent = agent_class(agent_store)
        agent.analyze(document_text, deal_context)

        elapsed = time.time() - start_time

        # Access metrics from the agent (AgentMetrics is a dataclass, not a dict)
        agent_metrics = getattr(agent, 'metrics', None)
        api_calls = agent_metrics.api_calls if agent_metrics else 0

        return {
            'success': True,
            'domain': agent.domain,
            'store': agent_store,
            'reasoning_chain': agent.get_reasoning_chain(),
            'metrics': {
                'execution_time': elapsed,
                'api_calls': api_calls
            },
            'error': None
        }
    except Exception as e:
        elapsed = time.time() - start_time
        logging.error(f"Error in {agent_name} agent: {e}")
        return {
            'success': False,
            'domain': agent_name.lower(),
            'store': None,
            'reasoning_chain': [],
            'metrics': {'execution_time': elapsed},
            'error': str(e)
        }


def create_sample_document():
    """Create a sample IT infrastructure document for testing"""
    sample_content = """
# IT Infrastructure Overview - Project Atlas Target Company

## Executive Summary
This document provides an overview of the IT infrastructure for the target acquisition.
The company operates a manufacturing business with 1,200 employees across 5 locations.

## Data Center & Hosting

### Primary Data Center
- Location: Chicago, IL (Equinix CH3)
- Colocation lease expires: March 2026 (18 months remaining)
- Rack count: 12 racks
- Power: 2N redundant, 150kW allocated

### Disaster Recovery
- Location: Dallas, TX (CyrusOne)
- DR capability: Warm standby, 4-hour RTO target
- Last DR test: Never formally tested

## Server Environment

### Physical Servers: 15
- 8x Dell PowerEdge R740 (2019) - VMware hosts
- 4x HP ProLiant DL380 Gen9 (2016) - Database servers
- 3x Dell PowerEdge R630 (2015) - Legacy applications

### Virtual Environment: 180 VMs
- VMware vSphere 6.7 (Note: EOL October 2022)
- vCenter Standard licensing
- No vSAN - using NetApp SAN storage

### Operating Systems
- Windows Server 2019: 45 VMs
- Windows Server 2016: 80 VMs
- Windows Server 2012 R2: 30 VMs (EOL - security risk)
- RHEL 7: 15 VMs
- RHEL 8: 10 VMs

## Storage Infrastructure

### NetApp FAS8200 (Primary)
- Capacity: 200TB raw, 140TB usable
- Current utilization: 85%
- Protocols: NFS, iSCSI, CIFS
- Age: 5 years, approaching EOL

### Backup
- Veeam Backup & Replication v11
- Backup to secondary NetApp + AWS S3
- Retention: 30 days local, 1 year cloud
- RPO: 4 hours

## Cloud Presence

### AWS (Primary Cloud)
- Monthly spend: ~$45,000
- Services: EC2, RDS, S3, some Lambda
- Environment: Mostly lift-and-shift VMs
- No reserved instances (paying on-demand)
- Single AWS account for all environments

### Azure
- Monthly spend: ~$8,000
- Used only for Azure AD and some M365 workloads

## Network Infrastructure

### WAN
- AT&T MPLS network connecting all 5 sites
- Primary circuit: 100 Mbps at HQ
- Branch circuits: 20-50 Mbps
- Contract expires: December 2025
- No SD-WAN currently

### LAN
- Cisco Catalyst 3850 switches (EOL)
- Some Cisco 2960 switches at branches (very old)
- Flat network - limited VLAN segmentation
- No network access control (NAC)

### IP Addressing
- Using 10.0.0.0/8 address space
- No IPAM tool - managed in spreadsheet
- Known issues with IP conflicts

### Firewalls
- Palo Alto PA-3220 at HQ (current)
- Cisco ASA 5515-X at branches (approaching EOL)
- ~400 firewall rules at HQ
- Site-to-site VPNs between all locations

### DNS/DHCP
- AD-integrated DNS
- Windows DHCP servers
- Split-brain DNS for external resolution

## Security

### Identity & Access Management
- On-premises Active Directory (2016 functional level)
- Azure AD Connect for M365 sync
- No SSO platform (each app has own login)
- MFA: Only enabled for M365 and VPN (~40% coverage)
- Shared admin accounts exist
- No PAM solution

### Endpoint Security
- Symantec Endpoint Protection (legacy)
- No EDR capability
- BitLocker on ~70% of laptops
- BYOD allowed with no MDM

### Vulnerability Management
- Qualys vulnerability scanning (quarterly)
- Last scan: 3 months ago
- 45 critical vulnerabilities outstanding
- Patching: Monthly, often delayed

### Compliance
- No SOC 2 certification
- Processing credit cards - need PCI assessment
- Some HIPAA data from wellness program
- No formal security policies documented

### Security Operations
- No SIEM
- Logs retained 30 days on servers
- No dedicated security staff
- IT manager handles security part-time
- No incident response plan documented

### Recent Incidents
- Phishing attack 6 months ago - 3 accounts compromised
- Ransomware scare 18 months ago - caught by AV
- No formal incident tracking

## Applications

### ERP
- SAP ECC 6.0 (on-premise)
- ~150 custom ABAP programs
- Heavy integration with manufacturing systems
- Upgrade to S/4HANA not planned

### Email & Collaboration
- Microsoft 365 E3
- 1,100 mailboxes
- SharePoint Online for documents
- Teams adoption ~60%

### Business Applications
- Salesforce (CRM)
- Workday (HR) - implemented 2 years ago
- Custom manufacturing execution system (MES)
- Legacy inventory system (AS/400 - IBM i)

## IT Organization

### Headcount: 18 FTEs
- IT Director: 1
- Infrastructure: 6
- Applications: 5
- Help Desk: 4
- Security: 0 (IT Director handles)
- Project Management: 2

### Key Person Risk
- "Dave" knows the SAP system - 25 years with company
- No documentation for custom integrations
- Network managed by one person

### Vendors
- MSP for after-hours support (Acme IT Services)
- NetApp support contract expires June 2025
- VMware licensing through CDW

## Known Issues & Technical Debt

1. Windows Server 2012 R2 systems need immediate attention
2. VMware 6.7 is end of support
3. Network switches approaching end of life
4. SAP ECC will need S/4HANA migration eventually
5. Legacy AS/400 system - no one knows how to maintain
6. No disaster recovery testing ever performed
7. Security posture needs significant improvement
8. IP addressing conflicts with likely buyer range
"""
    
    sample_path = INPUT_DIR / "sample_it_infrastructure.txt"
    with open(sample_path, 'w') as f:
        f.write(sample_content)

    print(f"✓ Created sample document: {sample_path}")
    return sample_content


def register_document(repository: Repository, file_path: Path, content: str) -> str:
    """
    Point 66: Register a document in the database before analysis.

    Args:
        repository: Repository instance
        file_path: Path to the document file
        content: Document text content (for hash calculation)

    Returns:
        document_id of the registered document
    """
    # Calculate hash of content for deduplication
    content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]

    # Check if document already exists by path or hash
    existing_docs = repository.get_all_documents()
    for doc in existing_docs:
        if doc.file_hash == content_hash or (file_path and doc.document_path == str(file_path)):
            print(f"📄 Document already registered: {doc.document_id}")
            return doc.document_id

    # Create new document record
    doc = Document(
        document_id=generate_id('DOC'),
        document_name=file_path.name if file_path else "inline_document",
        document_path=str(file_path) if file_path else None,
        document_type='vdr',  # Default to VDR document
        page_count=content.count('\n') // 50 + 1,  # Rough page estimate
        ingested_date=now_iso(),
        last_updated=now_iso(),
        file_hash=content_hash
    )

    repository.create_document(doc)
    print(f"📄 Registered document: {doc.document_id} ({doc.document_name})")
    return doc.document_id


def create_analysis_run(repository: Repository, deal_context: dict, document_ids: list) -> str:
    """
    Point 67: Create an analysis run with timestamp.

    Args:
        repository: Repository instance
        deal_context: Deal context information
        document_ids: List of document IDs being analyzed

    Returns:
        run_id of the created analysis run
    """
    run = AnalysisRun(
        run_id=generate_id('RUN'),
        run_name=deal_context.get('deal_name', 'Analysis'),
        started_at=now_iso(),
        mode='fresh',
        status='in_progress',
        deal_context=deal_context,
        documents_analyzed=document_ids
    )

    repository.create_run(run)
    print(f"🔬 Created analysis run: {run.run_id}")
    return run.run_id


def run_analysis(document_text: str, deal_context: dict = None, input_path: Path = None,
                 analysis_mode: str = 'fresh', previous_run_id: str = None,
                 refine_costs: bool = False, skip_review: bool = False) -> dict:
    """
    Run full analysis pipeline.

    Args:
        document_text: Extracted text from IT documents
        deal_context: Optional context about the deal
        input_path: Path to the input document/folder
        analysis_mode: 'fresh' for new analysis, 'incremental' to build on previous (Point 75)
        previous_run_id: Specific run ID to build on in incremental mode (Point 76)

    Returns:
        Complete analysis output
    """
    # Point 65: Initialize database at startup
    print("\n" + "="*70)
    print("💾 INITIALIZING DATABASE")
    print("="*70)
    db = Database()
    db.initialize_schema()
    repository = Repository(db)
    print(f"✓ Database initialized: {db.db_path}")

    # Initialize shared analysis store with database connection
    store = AnalysisStore()
    store.set_database(db=db, repository=repository)

    # Point 76: In incremental mode, load existing findings first
    existing_context = None
    if analysis_mode == 'incremental':
        print("\n" + "-"*70)
        print("📂 INCREMENTAL MODE: Loading previous analysis state")
        print("-"*70)
        load_result = store.load_previous_state(previous_run_id)
        if load_result.get('loaded'):
            print(f"✓ Loaded previous run: {load_result['run_id']}")
            print(f"  - {load_result['statistics'].get('risks', 0)} existing risks")
            print(f"  - {load_result['statistics'].get('gaps', 0)} existing gaps")
            print(f"  - {load_result['statistics'].get('assumptions', 0)} existing assumptions")
            print(f"  - {load_result['statistics'].get('work_items', 0)} existing work items")

            # Point 77: Prepare existing findings context for agents
            existing_context = {
                'previous_run_id': load_result['run_id'],
                'existing_risks': [r.get('risk', '')[:100] for r in store.risks[:10]],
                'existing_gaps': [g.get('gap', '')[:100] for g in store.gaps[:10]],
                'existing_assumptions': [a.get('assumption', '')[:100] for a in store.assumptions[:10]],
                'instruction': """You are building on a PREVIOUS ANALYSIS. Existing findings have been loaded.

IMPORTANT for incremental analysis:
- DO NOT repeat findings that already exist (duplicates will be filtered)
- FOCUS on NEW information from this document that wasn't captured before
- If you find information that UPDATES an existing finding, note the update
- If a previous gap can now be filled, provide the answer
- If a previous assumption can be validated/invalidated, note it

Existing findings summary (first 10 of each type):
"""
            }
        else:
            print(f"⚠️  Could not load previous state: {load_result.get('status')}")
            print("   Falling back to fresh analysis mode")
            analysis_mode = 'fresh'

    # Point 66: Register document before analysis
    document_id = register_document(repository, input_path, document_text)
    store.add_document_id(document_id)

    # Default deal context if not provided
    if deal_context is None:
        deal_context = {
            "transaction_type": "acquisition",
            "deal_name": "Project Atlas",
            "integration_strategy": "full_integration",
            "buyer_environment": {
                "cloud_primary": "Azure",
                "identity": "Azure AD",
                "email": "Microsoft 365"
            }
        }

    # Point 77: Add existing findings context to deal_context for agents
    if existing_context:
        deal_context['_incremental_context'] = existing_context

    # Point 67: Create analysis run with timestamp
    run_mode = 'incremental' if analysis_mode == 'incremental' else 'fresh'
    run_id = create_analysis_run(repository, deal_context, [document_id])
    store.set_run_id(run_id)

    # Update run with mode info
    repository.update_run(run_id, {'mode': run_mode})

    # Coordinator will be initialized after domain agents complete
    coordinator = None

    print("\n" + "="*70)
    print("🚀 IT DILIGENCE ANALYSIS STARTING")
    print("="*70)
    print(f"Document length: {len(document_text):,} characters")
    print(f"Deal: {deal_context.get('deal_name', 'Unknown')}")
    print(f"Transaction: {deal_context.get('transaction_type', 'Unknown')}")
    print(f"Run ID: {run_id}")

    # Create output directory early for incremental saves
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_subdir = OUTPUT_DIR / f"analysis_{timestamp}"
    output_subdir.mkdir(parents=True, exist_ok=True)
    print(f"📁 Output directory: {output_subdir}")

    # Parse questions from input document (pre-existing answered/unanswered questions)
    print("\n" + "-"*70)
    print("PHASE 0: PARSING DOCUMENT QUESTIONS")
    print("-"*70)

    question_workflow = QuestionWorkflow(repository)
    doc_questions = question_workflow.process_document_questions(
        document_text,
        run_id=run_id,
        document_id=document_id
    )
    if doc_questions['parsed_count'] > 0:
        print(f"✓ Parsed {doc_questions['parsed_count']} questions from document:")
        print(f"  - Answered: {doc_questions['answered_count']}")
        print(f"  - Unanswered: {doc_questions['unanswered_count']}")
        print(f"  - Stored to database: {doc_questions['stored_count']}")
    else:
        print("  No pre-existing questions found in document")

    # Run domain analyses in PARALLEL
    print("\n" + "-"*70)
    print("PHASE 1: DOMAIN ANALYSIS (PARALLEL EXECUTION)")
    print("-"*70)

    # Define agents to run in parallel
    domain_agents = [
        (InfrastructureAgent, "Infrastructure"),
        (NetworkAgent, "Network"),
        (CybersecurityAgent, "Cybersecurity"),
        (ApplicationsAgent, "Applications"),
        (IdentityAccessAgent, "Identity & Access"),
        (OrganizationAgent, "Organization"),
    ]

    parallel_start = time.time()
    agent_results = []
    errors = []

    # Run agents in batches of 3 to stay within API rate limits (450K tokens/min)
    BATCH_SIZE = 3
    batches = [domain_agents[i:i + BATCH_SIZE] for i in range(0, len(domain_agents), BATCH_SIZE)]

    print(f"\n⚡ Launching {len(domain_agents)} domain agents in {len(batches)} batches (max {BATCH_SIZE} concurrent)...")

    try:
        for batch_num, batch in enumerate(batches, 1):
            print(f"\n   📦 Batch {batch_num}/{len(batches)}: {', '.join([name for _, name in batch])}")

            with ThreadPoolExecutor(max_workers=BATCH_SIZE) as executor:
                # Submit batch of agents
                futures = {
                    executor.submit(
                        run_single_agent,
                        agent_class,
                        agent_name,
                        document_text,
                        deal_context
                    ): agent_name
                    for agent_class, agent_name in batch
                }

                # Collect results as they complete
                for future in as_completed(futures):
                    agent_name = futures[future]
                    try:
                        result = future.result()
                        agent_results.append(result)

                        if result['success']:
                            print(f"      ✓ {agent_name} complete ({result['metrics']['execution_time']:.1f}s)")
                        else:
                            print(f"      ✗ {agent_name} failed: {result['error']}")
                            errors.append(f"{agent_name}: {result['error']}")
                    except Exception as e:
                        print(f"      ✗ {agent_name} exception: {e}")
                        errors.append(f"{agent_name}: {str(e)}")

        parallel_elapsed = time.time() - parallel_start
        print(f"\n⚡ Parallel execution complete in {parallel_elapsed:.1f}s")

        # Merge all agent results into master store
        print("\n📦 Merging results from all agents...")
        successful_agents = 0
        for result in agent_results:
            if result['success'] and result['store']:
                store.merge_from(result['store'])
                store.add_reasoning_chain(result['domain'], result['reasoning_chain'])
                successful_agents += 1

        print(f"   ✓ Merged results from {successful_agents}/{len(domain_agents)} agents")

        # Save merged results
        store.save(output_subdir)
        print(f"💾 Saved merged results to {output_subdir}")

        if errors:
            print(f"\n⚠️  {len(errors)} agent(s) had errors:")
            for err in errors:
                print(f"   - {err}")

        # Phase 1.5: Quality Review (before synthesis)
        review_results = None
        if not skip_review:
            print("\n" + "-"*70)
            print("PHASE 1.5: QUALITY REVIEW + QUESTION WORKFLOW")
            print("-"*70)
            print("\n🔍 Reviewing domain findings for quality before synthesis...")

            try:
                # Pass repository and run_id for question workflow integration
                review_agent = ReviewAgent(store, repository=repository, run_id=run_id)
                all_findings = store.get_all()
                review_results = review_agent.review(
                    document_text,
                    all_findings,
                    deal_context
                )

                # Log review summary
                summary = review_results.get('summary', {})
                print("\n📊 Findings Review Summary:")
                print(f"   • Findings reviewed: {summary.get('total_reviewed', 0)}")
                print(f"   • Validated: {summary.get('validated', 0)}")
                print(f"   • Flagged for attention: {summary.get('flagged', 0)}")
                print(f"   • Needs more evidence: {summary.get('needs_evidence', 0)}")
                print(f"   • Overstated (may downgrade): {summary.get('overstated', 0)}")
                print(f"   • Understated (may upgrade): {summary.get('understated', 0)}")
                print(f"   • Average confidence: {summary.get('average_confidence', 0):.1%}")
                print(f"\n   Quality Assessment: {summary.get('quality_assessment', 'N/A')}")

                # List flagged items if any
                flagged = review_results.get('flagged_items', [])
                if flagged:
                    print(f"\n⚠️  Flagged Items ({len(flagged)}):")
                    for item in flagged[:5]:  # Show first 5
                        print(f"   - [{item.finding_type}] {item.finding_id}: {item.review_notes[:60]}...")

                # List items needing evidence
                needs_ev = review_results.get('needs_evidence', [])
                if needs_ev:
                    print(f"\n📝 Needs More Evidence ({len(needs_ev)}):")
                    for item in needs_ev[:5]:
                        print(f"   - [{item.finding_type}] {item.finding_id}")

                # QUESTION WORKFLOW SUMMARY
                q_summary = review_results.get('question_summary', {})
                metrics = review_results.get('metrics', {})
                if q_summary or metrics.get('questions_reviewed', 0) > 0:
                    print("\n❓ Question Workflow Summary:")
                    print(f"   • Open questions checked: {metrics.get('questions_reviewed', 0)}")
                    print(f"   • Questions closed (answered): {metrics.get('questions_closed', 0)}")
                    print(f"   • New questions created: {metrics.get('questions_created', 0)}")
                    print(f"   • High-priority gaps needing questions: {metrics.get('gaps_without_questions', 0)}")

                    # Show question actions
                    q_actions = review_results.get('question_actions', [])
                    if q_actions:
                        print(f"\n   📋 Question Actions ({len(q_actions)}):")
                        for action in q_actions[:5]:
                            print(f"      - [{action.action.upper()}] {action.question_id}: {action.reason[:50]}...")

                print(f"\n⏱️  Review completed in {metrics.get('execution_time', 0):.1f}s ({metrics.get('api_calls', 0)} API calls)")

                # Save review results
                review_path = output_subdir / "review_results.json"
                review_serializable = {
                    'summary': summary,
                    'metrics': metrics,
                    'flagged_count': len(flagged),
                    'needs_evidence_count': len(needs_ev),
                    'question_summary': q_summary,
                    'question_actions': [
                        {
                            'question_id': a.question_id,
                            'action': a.action,
                            'reason': a.reason,
                            'related_finding_id': a.related_finding_id,
                            'old_status': a.old_status,
                            'new_status': a.new_status
                        }
                        for a in review_results.get('question_actions', [])
                    ],
                    'review_results': [
                        {
                            'finding_id': r.finding_id,
                            'finding_type': r.finding_type,
                            'validation_status': r.validation_status,
                            'confidence_score': r.confidence_score,
                            'evidence_quality': r.evidence_quality,
                            'original_severity': r.original_severity,
                            'recommended_severity': r.recommended_severity,
                            'review_notes': r.review_notes,
                            'issues_found': r.issues_found,
                            'suggestions': r.suggestions
                        }
                        for r in review_results.get('review_results', [])
                    ]
                }
                with open(review_path, 'w') as f:
                    json.dump(review_serializable, f, indent=2)
                print(f"💾 Review results saved to: {review_path}")

            except Exception as review_error:
                print(f"\n⚠️  Review phase error: {review_error}")
                import traceback
                traceback.print_exc()
                print("   Continuing with synthesis...")
        else:
            print("\n⏭️  Skipping quality review (--skip-review flag)")

    except Exception as e:
        # Save whatever we have before failing
        print(f"\n⚠️  Error during parallel analysis: {e}")
        print("💾 Saving partial results before exit...")
        store.save(output_subdir)
        # Point 68: Also save to database even on error
        try:
            db_counts = store.save_to_database()
            print(f"💾 Saved to database: {db_counts}")
        except Exception as db_error:
            print(f"⚠️  Database save error: {db_error}")
        print(f"✅ Partial results saved to: {output_subdir}")
        # Re-raise to show the error, but data is saved
        raise

    # Initialize coordinator with the merged store
    coordinator = CoordinatorAgent(store)
    
    # Coordination/Synthesis
    print("\n" + "-"*70)
    print("PHASE 2: SYNTHESIS & COORDINATION")
    print("-"*70)
    
    try:
        final_output = coordinator.synthesize(document_text, deal_context)
    except Exception as e:
        # Even if synthesis fails, save what we have
        print(f"\n⚠️  Error during synthesis: {e}")
        print("💾 Saving results before exit...")
        store.save(output_subdir)
        final_output = store.get_all()

    # Optional: Cost refinement phase
    if refine_costs:
        print("\n" + "-"*70)
        print("PHASE 2.5: COST REFINEMENT")
        print("-"*70)

        work_items = final_output.get('work_items', [])
        items_with_costs = [wi for wi in work_items if wi.get('cost_estimate_range')]

        if items_with_costs:
            print(f"\n💰 Refining costs for {len(items_with_costs)} work items...")
            print("   (4 API calls per item: research → review → refine → summary)")

            try:
                # Build context from deal context and domain summaries
                refinement_context = ""
                if deal_context:
                    refinement_context += f"Deal Context:\n{json.dumps(deal_context, indent=2)}\n\n"
                if final_output.get('domain_summaries'):
                    refinement_context += f"Domain Summaries:\n{json.dumps(final_output['domain_summaries'], indent=2)}\n"

                # Run cost refinement
                cost_store = refine_all_work_items(
                    work_items=items_with_costs,
                    output_dir=str(output_subdir),
                    context=refinement_context
                )

                print("\n✓ Cost refinement complete:")
                print(f"   • Processed: {cost_store.work_items_processed}")
                print(f"   • Succeeded: {cost_store.work_items_succeeded}")
                print(f"   • Failed: {cost_store.work_items_failed}")

                # Update work items with refined estimates
                refined_map = {r['work_item_id']: r for r in cost_store.results}
                for wi in final_output['work_items']:
                    if wi.get('id') in refined_map:
                        refined = refined_map[wi['id']]
                        wi['refined_estimate'] = refined.get('summary', {}).get('final_estimate', {})
                        wi['cost_confidence'] = refined.get('summary', {}).get('confidence_level')
                        wi['cost_executive_summary'] = refined.get('summary', {}).get('executive_summary')

            except Exception as cost_error:
                print(f"\n⚠️  Cost refinement error: {cost_error}")
                print("   Continuing with original estimates...")
        else:
            print("\n   No work items with cost estimates to refine.")

    # Final save
    print("\n" + "-"*70)
    print("PHASE 3: SAVING OUTPUTS")
    print("-"*70)

    store.save(output_subdir)

    # Point 68: Save to database at end of analysis
    print("\n💾 Persisting to database...")
    try:
        db_counts = store.save_to_database()
        print("✓ Database save complete")

        # Mark run as completed
        repository.complete_run(run_id, summary={
            'total_findings': sum(db_counts.get(k, 0) for k in db_counts if k != 'errors'),
            'errors': db_counts.get('errors', 0)
        })
    except Exception as db_error:
        print(f"⚠️  Database save error: {db_error}")
        db_counts = {'error': str(db_error)}

    # Also save a summary for quick review
    summary_path = output_subdir / "ANALYSIS_SUMMARY.md"
    with open(summary_path, 'w') as f:
        f.write(generate_summary_markdown(final_output))
    print(f"✓ Summary: {summary_path}")

    # Generate interactive HTML viewer and auto-open in browser
    print("\n" + "-"*70)
    print("PHASE 4: GENERATING HTML REPORT")
    print("-"*70)
    generate_viewer(str(output_subdir), auto_open=True)

    # Point 69: Summary of persisted findings
    print("\n" + "="*70)
    print("ANALYSIS COMPLETE")
    print("="*70)
    print(f"\nRun ID: {run_id}")
    print(f"Document ID: {document_id}")
    print(f"Outputs saved to: {output_subdir}")

    print("\n📊 Total findings (in-memory):")
    print(f"  • Current State: {len(final_output.get('current_state', []))}")
    print(f"  • Assumptions: {len(final_output['assumptions'])}")
    print(f"  • Gaps: {len(final_output['gaps'])}")
    print(f"  • Questions: {len(final_output.get('questions', []))}")
    print(f"  • Risks: {len(final_output['risks'])}")
    print(f"  • Strategic Considerations: {len(final_output.get('strategic_considerations', []))}")
    print(f"  • Work Items: {len(final_output['work_items'])}")
    print(f"  • Recommendations: {len(final_output['recommendations'])}")

    print("\n💾 Persisted to database:")
    for entity_type, count in db_counts.items():
        if count > 0:
            print(f"  • {entity_type.replace('_', ' ').title()}: {count}")

    # Show database location
    print(f"\n📁 Database: {db.db_path}")

    # Close database connection
    db.close()

    return final_output


def generate_summary_markdown(output: dict) -> str:
    """Generate a markdown summary of the analysis"""
    lines = []
    lines.append("# IT Due Diligence Analysis Summary")
    lines.append(f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Domain summaries
    lines.append("\n## Domain Summaries")
    for domain, summary in output.get('domain_summaries', {}).items():
        lines.append(f"\n### {domain.title()}")
        lines.append(f"- Complexity: {summary.get('complexity_assessment', 'N/A')}")
        lines.append(f"- Cost Range: {summary.get('estimated_cost_range', 'N/A')}")
        lines.append(f"- Timeline: {summary.get('estimated_timeline', 'N/A')}")
        if summary.get('summary'):
            lines.append(f"- Summary: {summary.get('summary')}")
    
    # Top Risks
    lines.append("\n## Top Risks")
    critical_risks = [r for r in output.get('risks', []) if r.get('severity') == 'critical']
    high_risks = [r for r in output.get('risks', []) if r.get('severity') == 'high']
    
    for risk in (critical_risks + high_risks)[:10]:
        lines.append(f"\n### {risk['id']}: {risk.get('risk', 'N/A')}")
        lines.append(f"- **Severity**: {risk.get('severity', 'N/A')}")
        lines.append(f"- **Likelihood**: {risk.get('likelihood', 'N/A')}")
        lines.append(f"- **Domain**: {risk.get('domain', 'N/A')}")
        lines.append(f"- **Mitigation**: {risk.get('mitigation', 'N/A')}")
    
    # Critical Gaps
    lines.append("\n## Critical Knowledge Gaps")
    critical_gaps = [g for g in output.get('gaps', []) if g.get('priority') in ['critical', 'high']]
    for gap in critical_gaps[:10]:
        lines.append(f"\n- **{gap['id']}**: {gap.get('gap', 'N/A')}")
        lines.append(f"  - Why needed: {gap.get('why_needed', 'N/A')}")
        lines.append(f"  - Suggested source: {gap.get('suggested_source', 'N/A')}")
    
    # Key Work Items
    lines.append("\n## Key Work Items")
    for item in output.get('work_items', [])[:15]:
        lines.append(f"\n### {item['id']}: {item.get('title', 'N/A')}")
        lines.append(f"- Domain: {item.get('domain', 'N/A')}")
        lines.append(f"- Effort: {item.get('effort_estimate', 'N/A')}")
        lines.append(f"- Cost: {item.get('cost_estimate_range', 'N/A')}")
        lines.append(f"- Phase: {item.get('timeline_phase', 'N/A')}")
    
    # Recommendations
    lines.append("\n## Strategic Recommendations")
    for rec in output.get('recommendations', []):
        lines.append(f"\n### {rec['id']}: {rec.get('recommendation', 'N/A')}")
        lines.append(f"- Priority: {rec.get('priority', 'N/A')}")
        lines.append(f"- Timing: {rec.get('timing', 'N/A')}")
        lines.append(f"- Rationale: {rec.get('rationale', 'N/A')}")
    
    return "\n".join(lines)


def _build_answer_document(repository, run_id: str) -> str:
    """
    Build a document from answered questions for re-analysis.

    Converts answered questions into a structured document format
    that domain agents can process during incremental analysis.

    Args:
        repository: Repository instance
        run_id: Run ID to get questions from

    Returns:
        Formatted document string with Q&A content
    """
    lines = []
    lines.append("# Client Answers to Due Diligence Questions")
    lines.append(f"\nRun ID: {run_id}")
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append("\n---\n")

    try:
        conn = repository.db.connect()
        rows = conn.execute(
            """SELECT * FROM questions
               WHERE run_id = ? AND status IN ('answered', 'closed')
               AND answer_text IS NOT NULL AND answer_text != ''
               ORDER BY domain, priority DESC""",
            (run_id,)
        ).fetchall()
        questions = [dict(row) for row in rows]

        if not questions:
            return ""

        # Group by domain
        by_domain = {}
        for q in questions:
            domain = q.get('domain', 'General')
            if domain not in by_domain:
                by_domain[domain] = []
            by_domain[domain].append(q)

        for domain, domain_questions in by_domain.items():
            lines.append(f"\n## {domain.title()} Domain\n")

            for q in domain_questions:
                lines.append(f"### Question: {q.get('question_text', 'N/A')}")
                lines.append(f"**Priority**: {q.get('priority', 'N/A')}")
                if q.get('context'):
                    lines.append(f"**Context**: {q.get('context')}")
                lines.append(f"\n**Answer**: {q.get('answer_text', 'N/A')}")
                if q.get('answered_by'):
                    lines.append(f"*Answered by: {q.get('answered_by')}*")
                lines.append("\n---\n")

        lines.append("\n## Summary")
        lines.append(f"- Total questions answered: {len(questions)}")
        lines.append(f"- Domains covered: {', '.join(by_domain.keys())}")

    except Exception as e:
        logging.error(f"Error building answer document: {e}")
        return ""

    return "\n".join(lines)


def main():
    """
    Main entry point

    Usage:
        python main.py                              # Fresh analysis on data/input/
        python main.py path/to/document.pdf         # Fresh analysis on specific PDF
        python main.py --incremental                # Incremental analysis (builds on latest run)
        python main.py --incremental --run-id RUN-xxx  # Incremental from specific run
        python main.py --list-runs                  # List previous analysis runs
    """
    import argparse

    parser = argparse.ArgumentParser(
        description='IT Due Diligence Analysis Agent',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                           # Analyze documents in data/input/
  python main.py document.pdf              # Analyze specific PDF
  python main.py --incremental             # Build on previous analysis
  python main.py --incremental --run-id RUN-xxx  # Build on specific run
  python main.py --list-runs               # Show previous analysis runs

Session Management:
  python main.py --name-session RUN-xxx "Initial Analysis" --tags initial,draft
  python main.py --compare RUN-xxx RUN-yyy    # Compare two runs
  python main.py --branch RUN-xxx             # Create new run from previous
  python main.py --questions RUN-xxx          # Show question status
  python main.py --assumptions RUN-xxx        # Show assumption validation status

Export:
  python main.py --export-findings RUN-xxx    # Export findings to Excel
  python main.py --export-questions RUN-xxx   # Export questions for client follow-up

Question Workflow:
  python main.py --import-answers file.xlsx --reanalyze  # Import answers and re-run analysis
        """
    )
    parser.add_argument('input', nargs='?', help='Path to document or folder (default: data/input/)')
    parser.add_argument('-i', '--incremental', action='store_true',
                       help='Incremental mode: build on previous analysis (Point 75)')
    parser.add_argument('--run-id', dest='run_id',
                       help='Specific run ID to build on in incremental mode (Point 76)')
    parser.add_argument('--list-runs', action='store_true',
                       help='List previous analysis runs and exit')

    # Session management commands (Points 90-92)
    parser.add_argument('--name-session', nargs=2, metavar=('RUN_ID', 'NAME'),
                       help='Name/rename an analysis session (Point 90)')
    parser.add_argument('--tags', type=str,
                       help='Comma-separated tags for --name-session')
    parser.add_argument('--compare', nargs=2, metavar=('RUN1', 'RUN2'),
                       help='Compare two analysis runs (Point 91)')
    parser.add_argument('--branch', metavar='RUN_ID',
                       help='Create new run branched from previous (Point 92)')
    parser.add_argument('--questions', metavar='RUN_ID', nargs='?', const='latest',
                       help='Show question/gap tracking status (Points 80-84)')
    parser.add_argument('--assumptions', metavar='RUN_ID', nargs='?', const='latest',
                       help='Show assumption validation status (Points 85-89)')

    # Cost refinement (ON by default)
    parser.add_argument('--skip-costs', action='store_true',
                       help='Skip the 4-stage cost refinement (runs by default)')

    # Quality review (ON by default)
    parser.add_argument('--skip-review', action='store_true',
                       help='Skip the quality review phase (runs by default)')

    # Question export/import
    parser.add_argument('--export-questions', metavar='RUN_ID', nargs='?', const='latest',
                       help='Export questions to Excel for client follow-up')
    parser.add_argument('--import-answers', metavar='FILE',
                       help='Import answers from Excel file')
    parser.add_argument('--import-run-id', metavar='RUN_ID',
                       help='Run ID to update when importing answers (default: latest)')
    parser.add_argument('--reanalyze', action='store_true',
                       help='Run incremental analysis on imported answers')

    # Findings export
    parser.add_argument('--export-findings', metavar='RUN_ID', nargs='?', const='latest',
                       help='Export all findings (risks, gaps, work items, etc.) to Excel')

    args = parser.parse_args()

    # Check API key
    if not ANTHROPIC_API_KEY:
        print("❌ Error: ANTHROPIC_API_KEY not set")
        print("Create a .env file with: ANTHROPIC_API_KEY=your-key-here")
        sys.exit(1)

    # Handle --list-runs
    if args.list_runs:
        from storage import Database, Repository
        db = Database()
        db.initialize_schema()
        repository = Repository(db)
        runs = repository.get_all_runs()
        if not runs:
            print("No previous analysis runs found.")
        else:
            print("\n📋 Previous Analysis Runs:")
            print("-" * 70)
            for run in runs:
                run_dict = run.to_dict() if hasattr(run, 'to_dict') else run
                summary = repository.get_run_summary(run_dict['run_id'])
                counts = summary.get('counts', {})
                print(f"\n  {run_dict['run_id']}")
                print(f"    Name: {run_dict.get('run_name', 'N/A')}")
                print(f"    Started: {run_dict.get('started_at', 'N/A')}")
                print(f"    Status: {run_dict.get('status', 'N/A')}")
                print(f"    Mode: {run_dict.get('mode', 'fresh')}")
                print(f"    Findings: {counts.get('risks', 0)} risks, {counts.get('gaps', 0)} gaps, {counts.get('work_items', 0)} work items")
        db.close()
        sys.exit(0)

    # Handle --name-session (Point 90)
    if args.name_session:
        from storage import Database, Repository
        db = Database()
        db.initialize_schema()
        repository = Repository(db)
        run_id, name = args.name_session
        tags = args.tags.split(',') if args.tags else None
        if repository.name_session(run_id, name, tags):
            print(f"✓ Session {run_id} named: '{name}'")
            if tags:
                print(f"  Tags: {', '.join(tags)}")
        else:
            print(f"❌ Failed to name session {run_id}")
        db.close()
        sys.exit(0)

    # Handle --compare (Point 91)
    if args.compare:
        from storage import Database, Repository
        db = Database()
        db.initialize_schema()
        repository = Repository(db)
        run1, run2 = args.compare
        try:
            comparison = repository.compare_sessions(run1, run2)
            print(f"\n📊 Session Comparison: {run1} vs {run2}")
            print("=" * 70)

            print("\n## Finding Counts:")
            print(f"{'Type':<25} {'Run 1':>10} {'Run 2':>10} {'Delta':>10}")
            print("-" * 55)
            for ftype, counts in comparison['counts'].items():
                delta = counts['delta']
                delta_str = f"+{delta}" if delta > 0 else str(delta)
                print(f"{ftype:<25} {counts['run_1']:>10} {counts['run_2']:>10} {delta_str:>10}")

            print("\n## Summary:")
            summary = comparison['summary']
            print(f"  - Net risk change: {summary['net_risk_change']:+d}")
            print(f"  - Gaps resolved: {summary['gaps_resolved']}")
            print(f"  - New gaps: {summary['new_gaps_identified']}")
            print(f"  - Severity escalations: {summary['severity_escalations']}")
            print(f"  - Severity de-escalations: {summary['severity_de_escalations']}")

            if comparison['changes'].get('severity_changes'):
                print("\n## Severity Changes:")
                for change in comparison['changes']['severity_changes'][:5]:
                    print(f"  - {change['risk'][:40]}...")
                    print(f"    {change['run_1_severity']} -> {change['run_2_severity']}")
        except Exception as e:
            print(f"❌ Error comparing sessions: {e}")
        db.close()
        sys.exit(0)

    # Handle --branch (Point 92)
    if args.branch:
        from storage import Database, Repository
        db = Database()
        db.initialize_schema()
        repository = Repository(db)
        try:
            new_run_id = repository.branch_from_session(args.branch)
            print(f"✓ Created new branch: {new_run_id}")
            print(f"  Branched from: {args.branch}")
            summary = repository.get_run_summary(new_run_id)
            counts = summary.get('counts', {})
            print(f"  Copied: {counts.get('risks', 0)} risks, {counts.get('gaps', 0)} gaps, {counts.get('work_items', 0)} work items")
            print("\nTo continue analysis on this branch:")
            print(f"  python main.py --incremental --run-id {new_run_id}")
        except Exception as e:
            print(f"❌ Error branching session: {e}")
        db.close()
        sys.exit(0)

    # Handle --questions (Points 80-84)
    if args.questions:
        from storage import Database, Repository
        db = Database()
        db.initialize_schema()
        repository = Repository(db)
        run_id = args.questions
        if run_id == 'latest':
            latest = repository.get_latest_run()
            run_id = latest.run_id if latest else None
        if not run_id:
            print("No runs found.")
            sys.exit(1)

        print(f"\n❓ Question/Gap Status for {run_id}")
        print("=" * 70)

        summary = repository.get_question_status_summary(run_id)
        print(f"\nTotal Questions: {summary['total']}")
        print(f"  - Draft: {summary.get('draft', 0)}")
        print(f"  - Ready to send: {summary.get('ready', 0)}")
        print(f"  - Sent (awaiting): {summary.get('sent', 0)}")
        print(f"  - Answered: {summary.get('answered', 0)}")
        print(f"  - Closed: {summary.get('closed', 0)}")

        # Show pending questions
        pending = repository.get_pending_questions(run_id)
        if pending:
            print(f"\n📝 Pending Questions ({len(pending)}):")
            for q in pending[:5]:
                q_text = q.question_text if hasattr(q, 'question_text') else q.get('question_text', '')
                priority = q.priority if hasattr(q, 'priority') else q.get('priority', '')
                print(f"  [{priority.upper()}] {q_text[:60]}...")

        # Show awaiting answer
        awaiting = repository.get_awaiting_answer_questions(run_id)
        if awaiting:
            print(f"\n⏳ Awaiting Answer ({len(awaiting)}):")
            for q in awaiting[:5]:
                q_text = q.question_text if hasattr(q, 'question_text') else q.get('question_text', '')
                sent = q.sent_date if hasattr(q, 'sent_date') else q.get('sent_date', '')
                print(f"  - {q_text[:50]}... (sent: {sent[:10] if sent else 'N/A'})")

        db.close()
        sys.exit(0)

    # Handle --assumptions (Points 85-89)
    if args.assumptions:
        from storage import Database, Repository
        db = Database()
        db.initialize_schema()
        repository = Repository(db)
        run_id = args.assumptions
        if run_id == 'latest':
            latest = repository.get_latest_run()
            run_id = latest.run_id if latest else None
        if not run_id:
            print("No runs found.")
            sys.exit(1)

        print(f"\n🔍 Assumption Validation Status for {run_id}")
        print("=" * 70)

        summary = repository.get_assumption_validation_summary(run_id)
        print(f"\nTotal Assumptions: {summary['total']}")

        print("\nBy Validation Status:")
        for status, count in summary.get('by_validation_status', {}).items():
            print(f"  - {status}: {count}")

        print("\nBy Confidence:")
        for conf, count in summary.get('by_confidence', {}).items():
            print(f"  - {conf}: {count}")

        print(f"\nHigh-impact unvalidated: {summary.get('high_impact_unvalidated', 0)}")
        print(f"With evidence: {summary.get('assumptions_with_evidence', 0)}")
        print(f"Without evidence: {summary.get('assumptions_without_evidence', 0)}")

        # Show assumptions needing validation
        needs_validation = repository.get_assumptions_needing_validation(run_id)
        if needs_validation:
            print(f"\n⚠️  Needs Validation ({len(needs_validation)}):")
            for a in needs_validation[:5]:
                a_text = a.assumption_text if hasattr(a, 'assumption_text') else a.get('assumption_text', '')
                impact = a.impact if hasattr(a, 'impact') else a.get('impact', '')
                conf = a.confidence if hasattr(a, 'confidence') else a.get('confidence', '')
                print(f"  [{impact.upper()}/{conf}] {a_text[:50]}...")

        db.close()
        sys.exit(0)

    # Handle --export-questions
    if args.export_questions:
        from storage import Database, Repository
        db = Database()
        db.initialize_schema()
        repository = Repository(db)
        run_id = args.export_questions
        if run_id == 'latest':
            latest = repository.get_latest_run()
            run_id = latest.run_id if latest else None
        if not run_id:
            print("No runs found.")
            sys.exit(1)

        # Get all questions for the run
        try:
            conn = repository.db.connect()
            rows = conn.execute(
                "SELECT * FROM questions WHERE run_id = ? ORDER BY priority, created_at",
                (run_id,)
            ).fetchall()
            questions = [dict(row) for row in rows]

            # Also add questions identified from gaps that haven't been converted yet
            gaps = repository.get_unanswered_gaps(run_id)
            print(f"\n📋 Found {len(questions)} questions and {len(gaps)} unanswered gaps for {run_id}")

            if not questions and not gaps:
                print("No questions or gaps to export.")
                sys.exit(0)

            # Export to Excel
            output_path = f"questions_{run_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            result_path = export_questions_to_excel(questions, output_path)
            print(f"\n✓ Questions exported to: {result_path}")
            print(f"  Open questions: {len([q for q in questions if q.get('status') not in ['answered', 'closed']])}")
            print(f"  Answered questions: {len([q for q in questions if q.get('status') in ['answered', 'closed']])}")
            print("\nTo import answers:")
            print(f"  python main.py --import-answers {result_path} --import-run-id {run_id}")

        except Exception as e:
            print(f"❌ Error exporting questions: {e}")

        db.close()
        sys.exit(0)

    # Handle --import-answers
    if args.import_answers:
        from storage import Database, Repository
        db = Database()
        db.initialize_schema()
        repository = Repository(db)

        # Determine run ID
        run_id = args.import_run_id
        if not run_id:
            latest = repository.get_latest_run()
            run_id = latest.run_id if latest else None
        if not run_id:
            print("No runs found and no --import-run-id specified.")
            sys.exit(1)

        file_path = args.import_answers
        if not Path(file_path).exists():
            print(f"❌ File not found: {file_path}")
            sys.exit(1)

        print(f"\n📥 Importing answers from: {file_path}")
        print(f"   Target run: {run_id}")

        workflow = QuestionWorkflow(repository)
        results = workflow.import_answers(file_path, run_id)

        print("\n✓ Import complete:")
        print(f"  Questions found: {results['questions_found']}")
        print(f"  Answers imported: {results['answers_imported']}")
        if results['errors']:
            print(f"  Errors: {len(results['errors'])}")
            for err in results['errors'][:5]:
                print(f"    - {err}")

        # Handle --reanalyze: run incremental analysis on imported answers
        if args.reanalyze and results['answers_imported'] > 0:
            print("\n" + "="*70)
            print("🔄 RE-ANALYSIS: Processing imported answers")
            print("="*70)

            # Build a document from the answered questions
            answer_document = _build_answer_document(repository, run_id)

            if answer_document:
                db.close()  # Close before running analysis (it opens its own)

                # Run incremental analysis
                print(f"\n📄 Answer document: {len(answer_document):,} characters")
                run_analysis(
                    answer_document,
                    input_path=Path(file_path),
                    analysis_mode='incremental',
                    previous_run_id=run_id,
                    refine_costs=not args.skip_costs,
                    skip_review=args.skip_review
                )
                sys.exit(0)
            else:
                print("⚠️  No answered questions to analyze")

        db.close()
        sys.exit(0)

    # Handle --export-findings
    if args.export_findings:
        from storage import Database, Repository
        db = Database()
        db.initialize_schema()
        repository = Repository(db)
        run_id = args.export_findings
        if run_id == 'latest':
            latest = repository.get_latest_run()
            run_id = latest.run_id if latest else None
        if not run_id:
            print("No runs found.")
            sys.exit(1)

        print(f"\n📊 Exporting findings for {run_id}")
        print("=" * 70)

        try:
            # Generate output path
            output_path = f"findings_{run_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

            # Export findings
            result = export_findings_to_excel(run_id, repository, output_path)

            print(f"\n✓ Findings exported to: {result['output_path']}")
            print("\n📋 Export Summary:")
            for sheet, count in result['counts'].items():
                if count > 0:
                    print(f"  • {sheet}: {count}")
            print(f"\nTotal findings exported: {result['total']}")

        except Exception as e:
            print(f"❌ Error exporting findings: {e}")
            import traceback
            traceback.print_exc()

        db.close()
        sys.exit(0)

    # Determine input source
    if args.input:
        input_path = Path(args.input)
        if not input_path.exists():
            print(f"❌ Error: Path not found: {input_path}")
            sys.exit(1)
    else:
        input_path = INPUT_DIR

    # Determine analysis mode (Point 75)
    analysis_mode = 'incremental' if args.incremental else 'fresh'
    previous_run_id = args.run_id

    # Try to parse PDFs
    try:
        if input_path.is_file() and input_path.suffix.lower() == '.pdf':
            print(f"📄 Parsing PDF: {input_path}")
            document_text = parse_pdfs(input_path)
        elif input_path.is_dir():
            pdf_files = list(input_path.glob("*.pdf"))
            txt_files = list(input_path.glob("*.txt"))

            if pdf_files:
                print(f"📁 Parsing {len(pdf_files)} PDFs from: {input_path}")
                document_text = parse_pdfs(input_path)
            elif txt_files:
                print(f"📁 Reading {len(txt_files)} text files from: {input_path}")
                document_text = ""
                for txt_file in txt_files:
                    with open(txt_file, 'r') as f:
                        document_text += f"\n\n# {txt_file.name}\n\n" + f.read()
            else:
                print("📝 No documents found. Creating sample document...")
                document_text = create_sample_document()
        else:
            # Try reading as text file
            print(f"📄 Reading text file: {input_path}")
            with open(input_path, 'r') as f:
                document_text = f.read()

        if not document_text.strip():
            print("⚠ No content extracted. Creating sample document...")
            document_text = create_sample_document()

    except Exception as e:
        print(f"⚠ Error parsing documents: {e}")
        print("Creating sample document for testing...")
        document_text = create_sample_document()

    # Run analysis with mode parameters (Points 75-79)
    run_analysis(
        document_text,
        input_path=input_path,
        analysis_mode=analysis_mode,
        previous_run_id=previous_run_id,
        refine_costs=not args.skip_costs,  # ON by default, --skip-costs to disable
        skip_review=args.skip_review  # ON by default, --skip-review to disable
    )


if __name__ == "__main__":
    main()
