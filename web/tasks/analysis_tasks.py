"""
Analysis Tasks - Background document and domain analysis

These tasks run asynchronously via Celery to handle long-running analysis
without blocking the web interface.
"""

import logging
from datetime import datetime
from typing import List, Optional, Dict, Any

from celery import shared_task

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
    Analyze a single domain for a deal.

    This is a placeholder that will integrate with the actual analysis pipeline.
    """
    # TODO: Integrate with actual analysis pipeline
    # For now, return placeholder results
    logger.info(f"Analyzing domain {domain} for deal {deal_id}")

    # This will be replaced with actual analysis logic
    # from agents.discovery_orchestrator import run_domain_discovery
    # result = run_domain_discovery(deal_id, domain, entity)

    return {
        'domain': domain,
        'facts_count': 0,
        'findings_count': 0,
        'status': 'completed'
    }


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

        # TODO: Integrate with document processing pipeline
        # from document_processing import extract_text, classify_document
        # extracted_text = extract_text(document.storage_path)
        # doc_type = classify_document(extracted_text)

        # For now, mark as processed
        document.status = 'processed'
        document.extracted_text = ''  # Will be populated by actual extraction
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
