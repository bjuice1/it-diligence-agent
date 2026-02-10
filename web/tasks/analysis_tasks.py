"""
Analysis Tasks - Background document and domain analysis

These tasks run asynchronously via Celery to handle long-running analysis
without blocking the web interface.
"""

import logging
from datetime import datetime
from typing import List, Optional, Dict, Any

from celery import shared_task

# V2 Pipeline imports for actual analysis
try:
    from stores.fact_store import FactStore
    from stores.inventory_store import InventoryStore
    from agents_v2.discovery import DISCOVERY_AGENTS
    from config_v2 import ANTHROPIC_API_KEY
    from tools_v2.inventory_integration import (
        promote_facts_to_inventory,
        reconcile_facts_and_inventory,
        generate_inventory_audit,
        save_inventory_audit,
    )
    V2_PIPELINE_AVAILABLE = True
except ImportError:
    V2_PIPELINE_AVAILABLE = False

logger = logging.getLogger(__name__)


@shared_task(bind=True, name='web.tasks.run_analysis_task')
def run_analysis_task(
    self,
    deal_id: str,
    domains: List[str],
    user_id: Optional[str] = None,
    entity: str = 'target',
    options: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Run multi-domain analysis for a deal.

    This is the main entry point for background analysis.
    Updates progress as each domain is analyzed.

    Args:
        deal_id: The deal to analyze
        domains: List of domains to analyze (infrastructure, apps, etc.)
        user_id: User who initiated the analysis
        entity: 'target' or 'buyer'
        options: Additional analysis options

    Returns:
        Analysis results summary
    """
    from web.database import db, Deal, AnalysisRun
    from web.repositories.analysis_run_repository import AnalysisRunRepository

    options = options or {}
    results = {
        'deal_id': deal_id,
        'entity': entity,
        'domains_analyzed': [],
        'total_facts': 0,
        'total_findings': 0,
        'errors': [],
        'started_at': datetime.utcnow().isoformat(),
    }

    try:
        # Create analysis run record
        repo = AnalysisRunRepository()
        run = repo.create_run(
            deal_id=deal_id,
            run_type='full' if len(domains) > 2 else 'partial',
            domains=domains,  # Fixed: was domains_analyzed, use create_run method
            entity=entity,
            initiated_by=user_id
        )
        # Start the run
        run = repo.start_run(run)
        run_id = run.id

        # Update progress: starting
        self.update_state(
            state='PROGRESS',
            meta={
                'progress': 0,
                'phase': 'Starting analysis',
                'message': f'Initializing analysis for {len(domains)} domains',
                'run_id': str(run_id)
            }
        )

        total_domains = len(domains)
        for i, domain in enumerate(domains):
            # Update progress
            progress = int((i / total_domains) * 100)
            self.update_state(
                state='PROGRESS',
                meta={
                    'progress': progress,
                    'phase': f'Analyzing {domain}',
                    'message': f'Processing domain {i + 1} of {total_domains}',
                    'current_domain': domain,
                    'run_id': str(run_id)
                }
            )

            try:
                # Run domain analysis
                domain_result = _analyze_domain(deal_id, domain, entity, options)
                results['domains_analyzed'].append(domain)
                results['total_facts'] += domain_result.get('facts_count', 0)
                results['total_findings'] += domain_result.get('findings_count', 0)

            except Exception as e:
                logger.error(f"Error analyzing domain {domain}: {e}")
                results['errors'].append({
                    'domain': domain,
                    'error': str(e)
                })

        # Final progress update
        self.update_state(
            state='PROGRESS',
            meta={
                'progress': 95,
                'phase': 'Finalizing',
                'message': 'Generating summary and saving results',
                'run_id': str(run_id)
            }
        )

        # Update analysis run record
        results['completed_at'] = datetime.utcnow().isoformat()
        repo.complete(
            run_id,
            facts_count=results['total_facts'],
            findings_count=results['total_findings'],
            errors=results['errors'] if results['errors'] else None
        )

        # Update deal statistics
        deal = Deal.query.get(deal_id)
        if deal:
            deal.facts_extracted = results['total_facts']
            deal.findings_count = results['total_findings']
            deal.analysis_runs_count = (deal.analysis_runs_count or 0) + 1
            deal.last_accessed_at = datetime.utcnow()
            db.session.commit()

        logger.info(f"Analysis complete for deal {deal_id}: {results['total_facts']} facts, {results['total_findings']} findings")
        return results

    except Exception as e:
        logger.error(f"Analysis task failed for deal {deal_id}: {e}")
        results['error'] = str(e)
        results['completed_at'] = datetime.utcnow().isoformat()

        # Update run as failed
        if 'run_id' in locals():
            try:
                repo.fail(run_id, error=str(e))
            except Exception:
                pass

        raise


def _analyze_domain(
    deal_id: str,
    domain: str,
    entity: str,
    options: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Analyze a single domain for a deal using V2 pipeline.
    """
    from web.database import db, Deal, Fact, Document

    logger.info(f"Analyzing domain {domain} for deal {deal_id}")

    if not V2_PIPELINE_AVAILABLE:
        logger.error("V2 pipeline not available")
        return {'domain': domain, 'facts_count': 0, 'status': 'error', 'error': 'V2 pipeline not available'}

    if domain not in DISCOVERY_AGENTS:
        logger.warning(f"No discovery agent for domain: {domain}")
        return {'domain': domain, 'facts_count': 0, 'status': 'skipped', 'error': f'No agent for {domain}'}

    try:
        # Get documents for this deal and entity
        documents = Document.query.filter_by(
            deal_id=deal_id,
            entity=entity,
            status='processed'
        ).all()

        if not documents:
            logger.warning(f"No processed documents for deal {deal_id} entity {entity}")
            return {'domain': domain, 'facts_count': 0, 'status': 'no_documents'}

        # Combine document text
        document_text = "\n\n---\n\n".join([
            f"[Document: {doc.original_filename}]\n{doc.extracted_text or ''}"
            for doc in documents if doc.extracted_text
        ])

        if not document_text.strip():
            return {'domain': domain, 'facts_count': 0, 'status': 'no_text'}

        # Create FactStore and InventoryStore for this analysis
        fact_store = FactStore(deal_id=deal_id)
        inventory_store = InventoryStore(deal_id=deal_id)

        # Get deal info for context
        deal = Deal.query.get(deal_id)
        target_name = deal.target_name if deal else None

        # Run V2 discovery agent
        agent_class = DISCOVERY_AGENTS[domain]
        agent = agent_class(
            api_key=ANTHROPIC_API_KEY,
            fact_store=fact_store,
            inventory_store=inventory_store,
        )

        result = agent.discover(
            document_text=document_text,
            document_name=f"Combined documents for {entity}",
            entity=entity,
            analysis_phase=f"{entity}_extraction"
        )

        # Save facts to database
        facts_saved = 0
        for store_fact in fact_store.facts:
            try:
                # store_fact is a Fact dataclass from stores.fact_store
                # Convert to DB model Fact from web.database
                fact = Fact(
                    id=store_fact.fact_id or f"F-{domain[:3].upper()}-{facts_saved:04d}",
                    deal_id=deal_id,
                    domain=store_fact.domain or domain,
                    category=store_fact.category or '',
                    entity=store_fact.entity or entity,
                    item=store_fact.item or '',
                    status=store_fact.status or 'documented',
                    details=store_fact.details or {},
                    evidence=store_fact.evidence or {},
                    source_document=store_fact.source_document or '',
                    confidence_score=store_fact.confidence_score if hasattr(store_fact, 'confidence_score') else 0.5,
                    analysis_phase=f"{entity}_extraction",
                    created_at=datetime.utcnow()
                )
                db.session.add(fact)
                facts_saved += 1
            except Exception as e:
                logger.warning(f"Failed to save fact: {e}")
                db.session.rollback()

        db.session.commit()

        # Save inventory items to deal-specific path
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
                logger.info(
                    f"[PROMOTION] {entity_val}: {promotion_stats['promoted']} new items, "
                    f"{promotion_stats['matched']} matched to existing"
                )

        # Re-save inventory store (now includes promoted items)
        inventory_store.save()

        # Reconcile unlinked facts and inventory items
        reconcile_stats = reconcile_facts_and_inventory(
            fact_store=fact_store,
            inventory_store=inventory_store,
            entity="target",
            similarity_threshold=0.8,
        )
        logger.info(f"Reconciliation for {domain}: {reconcile_stats}")
        inventory_store.save()  # Re-save with updated links

        # Generate and save audit report
        audit_report = generate_inventory_audit(
            inventory_store=inventory_store,
            fact_store=fact_store,
            deal_id=deal_id,
        )
        save_inventory_audit(audit_report, deal_id=deal_id)
        logger.info(f"Domain {domain} audit: {audit_report['overall_health']}")

        return {
            'domain': domain,
            'facts_count': facts_saved,
            'findings_count': len(fact_store.gaps),
            'status': 'completed'
        }

    except Exception as e:
        logger.exception(f"Error analyzing domain {domain}: {e}")
        return {'domain': domain, 'facts_count': 0, 'status': 'error', 'error': str(e)}


@shared_task(bind=True, name='web.tasks.run_domain_analysis')
def run_domain_analysis(
    self,
    deal_id: str,
    domain: str,
    entity: str = 'target',
    options: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Run analysis for a single domain.

    Useful for re-running analysis on specific areas.
    """
    logger.info(f"Running single domain analysis: {domain} for deal {deal_id}")

    self.update_state(
        state='PROGRESS',
        meta={
            'progress': 10,
            'phase': f'Analyzing {domain}',
            'message': 'Starting domain analysis'
        }
    )

    result = _analyze_domain(deal_id, domain, entity, options or {})

    self.update_state(
        state='PROGRESS',
        meta={
            'progress': 90,
            'phase': 'Finalizing',
            'message': 'Saving results'
        }
    )

    return result


@shared_task(bind=True, name='web.tasks.process_document_task')
def process_document_task(
    self,
    deal_id: str,
    document_id: str,
    options: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Process a single document for text extraction and initial analysis.

    This task handles:
    1. Text extraction from PDF/DOC files
    2. Document classification
    3. Initial fact extraction
    """
    from web.database import db, Document

    logger.info(f"Processing document {document_id} for deal {deal_id}")

    self.update_state(
        state='PROGRESS',
        meta={
            'progress': 10,
            'phase': 'Loading document',
            'message': 'Reading document file'
        }
    )

    try:
        document = Document.query.get(document_id)
        if not document:
            raise ValueError(f"Document {document_id} not found")

        # Update progress
        self.update_state(
            state='PROGRESS',
            meta={
                'progress': 30,
                'phase': 'Extracting text',
                'message': f'Processing {document.filename}'
            }
        )

        # Extract text based on document type
        extracted_text = ''
        storage_path = document.storage_path

        try:
            from pathlib import Path
            file_path = Path(storage_path)

            if file_path.suffix.lower() == '.pdf':
                # Use PDF parser
                from ingestion.pdf_parser import parse_pdfs
                result = parse_pdfs([str(file_path)])
                extracted_text = result.get(str(file_path), '') if isinstance(result, dict) else ''

            elif file_path.suffix.lower() in ['.md', '.txt']:
                # Read text directly
                with open(file_path, 'r', encoding='utf-8') as f:
                    extracted_text = f.read()

            elif file_path.suffix.lower() in ['.docx', '.doc']:
                # Use Word parser
                from tools_v2.parsers.word_parser import WordParser
                parser = WordParser()
                result = parser.parse(file_path)
                extracted_text = result.text if result else ''

            elif file_path.suffix.lower() in ['.xlsx', '.xls']:
                # Use Excel parser
                from tools_v2.parsers.excel_parser import ExcelParser
                parser = ExcelParser()
                result = parser.parse(file_path)
                # Convert to text representation
                if result and result.tables:
                    extracted_text = '\n\n'.join([
                        f"Sheet: {t.sheet_name}\n" +
                        '\n'.join([' | '.join(str(c) for c in row) for row in t.data])
                        for t in result.tables
                    ])

            else:
                logger.warning(f"Unsupported file type: {file_path.suffix}")

        except Exception as extract_error:
            logger.warning(f"Text extraction failed: {extract_error}")

        # Update document
        document.status = 'processed'
        document.extracted_text = extracted_text
        document.word_count = len(extracted_text.split()) if extracted_text else 0
        document.processed_at = datetime.utcnow()
        db.session.commit()

        self.update_state(
            state='PROGRESS',
            meta={
                'progress': 90,
                'phase': 'Finalizing',
                'message': 'Document processed successfully'
            }
        )

        return {
            'document_id': document_id,
            'filename': document.filename,
            'status': 'processed',
            'text_length': len(document.extracted_text or '')
        }

    except Exception as e:
        logger.error(f"Document processing failed: {e}")
        raise
