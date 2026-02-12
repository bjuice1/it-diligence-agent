"""
Analysis Runner - Connects web app to the analysis pipeline.

This module bridges the Flask web interface with the V2 analysis pipeline.
Includes robust error handling and fallback modes.

INCREMENTAL PERSISTENCE: Facts, gaps, and findings are written to the database
immediately after extraction (not at the end). This provides crash durability -
if the process crashes, all data up to the last commit is preserved.
"""

import sys
import traceback
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Callable, List
from datetime import datetime
from dataclasses import asdict
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add parent directory for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from web.task_manager import AnalysisTask, AnalysisPhase, TaskStatus

# Configure logging (Point 111: Replace print statements)
logger = logging.getLogger(__name__)


# =============================================================================
# INCREMENTAL DATABASE WRITER INTEGRATION
# =============================================================================

class IncrementalPersistence:
    """
    Helper class to track and persist facts/findings incrementally during analysis.

    Tracks what has already been written to avoid duplicates.
    """

    def __init__(self, app, deal_id: str, run_id: str):
        self.app = app
        self.deal_id = deal_id
        self.run_id = run_id
        self._written_fact_ids = set()
        self._written_gap_ids = set()
        self._written_finding_ids = set()
        self._writer = None

    def _get_writer(self):
        """Lazy init writer to avoid import issues."""
        if self._writer is None:
            from stores.db_writer import get_db_writer
            self._writer = get_db_writer(self.app)
        return self._writer

    def persist_new_facts(self, session_fact_store) -> int:
        """
        Persist any facts not yet written to database.

        Args:
            session_fact_store: The analysis session's fact store

        Returns:
            Number of new facts persisted
        """
        writer = self._get_writer()
        new_count = 0

        with writer.session_scope() as db_session:
            for fact in session_fact_store.facts:
                fact_id = getattr(fact, 'fact_id', None)
                if not fact_id or fact_id in self._written_fact_ids:
                    continue

                fact_data = {
                    'fact_id': fact_id,
                    'domain': getattr(fact, 'domain', 'general'),
                    'category': getattr(fact, 'category', ''),
                    'entity': getattr(fact, 'entity', 'target'),
                    'item': getattr(fact, 'item', ''),
                    'status': getattr(fact, 'status', 'documented'),
                    'details': getattr(fact, 'details', {}),
                    'evidence': getattr(fact, 'evidence', {}),
                    'source_document': getattr(fact, 'source_document', ''),
                    'source_page_numbers': getattr(fact, 'source_page_numbers', []),
                    'source_quote': fact.evidence.get('exact_quote', '') if fact.evidence else '',
                    'confidence_score': getattr(fact, 'confidence_score', 0.5),
                }

                # Write without commit (batch at end of this method)
                if writer.write_fact(db_session, fact_data, self.deal_id, self.run_id, commit=False):
                    self._written_fact_ids.add(fact_id)
                    new_count += 1

            # Single commit for all new facts
            if new_count > 0:
                db_session.commit()
                logger.debug(f"Persisted {new_count} new facts incrementally")

        return new_count

    def persist_new_gaps(self, session_fact_store) -> int:
        """Persist any gaps not yet written to database."""
        writer = self._get_writer()
        new_count = 0

        with writer.session_scope() as db_session:
            for gap in session_fact_store.gaps:
                gap_id = getattr(gap, 'gap_id', None)
                if not gap_id or gap_id in self._written_gap_ids:
                    continue

                gap_data = {
                    'gap_id': gap_id,
                    'domain': getattr(gap, 'domain', 'general'),
                    'category': getattr(gap, 'category', ''),
                    'entity': getattr(gap, 'entity', 'target'),
                    'description': getattr(gap, 'description', ''),
                    'importance': getattr(gap, 'importance', 'medium'),
                    'requested_item': getattr(gap, 'requested_item', ''),
                    'source_document': getattr(gap, 'source_document', ''),
                    'related_facts': getattr(gap, 'related_facts', []),
                }

                if writer.write_gap(db_session, gap_data, self.deal_id, self.run_id, commit=False):
                    self._written_gap_ids.add(gap_id)
                    new_count += 1

            if new_count > 0:
                db_session.commit()
                logger.debug(f"Persisted {new_count} new gaps incrementally")

        return new_count

    def persist_new_findings(self, session_reasoning_store) -> int:
        """Persist any findings (risks, work items, etc.) not yet written."""
        writer = self._get_writer()
        new_count = 0

        with writer.session_scope() as db_session:
            # Persist risks
            for risk in session_reasoning_store.risks:
                finding_id = getattr(risk, 'finding_id', None)
                if not finding_id or finding_id in self._written_finding_ids:
                    continue

                finding_data = {
                    'finding_id': finding_id,
                    'finding_type': 'risk',
                    'domain': getattr(risk, 'domain', 'general'),
                    'title': getattr(risk, 'title', ''),
                    'description': getattr(risk, 'description', ''),
                    'severity': getattr(risk, 'severity', 'medium'),
                    'category': getattr(risk, 'category', ''),
                    'mitigation': getattr(risk, 'mitigation', ''),
                    'integration_dependent': getattr(risk, 'integration_dependent', False),
                    'timeline': getattr(risk, 'timeline', None),
                    'confidence': getattr(risk, 'confidence', 'medium'),
                    'reasoning': getattr(risk, 'reasoning', ''),
                    'based_on_facts': getattr(risk, 'based_on_facts', []),
                }

                if writer.write_finding(db_session, finding_data, self.deal_id, self.run_id, commit=False):
                    self._written_finding_ids.add(finding_id)
                    new_count += 1

            # Persist work items
            for wi in session_reasoning_store.work_items:
                finding_id = getattr(wi, 'finding_id', None)
                if not finding_id or finding_id in self._written_finding_ids:
                    continue

                finding_data = {
                    'finding_id': finding_id,
                    'finding_type': 'work_item',
                    'domain': getattr(wi, 'domain', 'general'),
                    'title': getattr(wi, 'title', ''),
                    'description': getattr(wi, 'description', ''),
                    'phase': getattr(wi, 'phase', None),
                    'priority': getattr(wi, 'priority', 'medium'),
                    'owner_type': getattr(wi, 'owner_type', 'shared'),
                    'cost_estimate': getattr(wi, 'cost_estimate', ''),
                    'triggered_by_risks': getattr(wi, 'triggered_by_risks', []),
                    'dependencies': getattr(wi, 'dependencies', []),
                    'confidence': getattr(wi, 'confidence', 'medium'),
                    'reasoning': getattr(wi, 'reasoning', ''),
                    'based_on_facts': getattr(wi, 'based_on_facts', []),
                }

                if writer.write_finding(db_session, finding_data, self.deal_id, self.run_id, commit=False):
                    self._written_finding_ids.add(finding_id)
                    new_count += 1

            # Persist strategic considerations
            for sc in session_reasoning_store.strategic_considerations:
                finding_id = getattr(sc, 'finding_id', None)
                if not finding_id or finding_id in self._written_finding_ids:
                    continue

                finding_data = {
                    'finding_id': finding_id,
                    'finding_type': 'strategic_consideration',
                    'entity': getattr(sc, 'entity', 'target'),
                    'domain': getattr(sc, 'domain', 'general'),
                    'title': getattr(sc, 'title', ''),
                    'description': getattr(sc, 'description', ''),
                    'lens': getattr(sc, 'lens', ''),
                    'implication': getattr(sc, 'implication', ''),
                    'confidence': getattr(sc, 'confidence', 'medium'),
                    'reasoning': getattr(sc, 'reasoning', ''),
                    'mna_lens': getattr(sc, 'mna_lens', ''),
                    'mna_implication': getattr(sc, 'mna_implication', ''),
                    'based_on_facts': getattr(sc, 'based_on_facts', []),
                }

                if writer.write_finding(db_session, finding_data, self.deal_id, self.run_id, commit=False):
                    self._written_finding_ids.add(finding_id)
                    new_count += 1

            # Persist recommendations
            for rec in session_reasoning_store.recommendations:
                finding_id = getattr(rec, 'finding_id', None)
                if not finding_id or finding_id in self._written_finding_ids:
                    continue

                finding_data = {
                    'finding_id': finding_id,
                    'finding_type': 'recommendation',
                    'entity': getattr(rec, 'entity', 'target'),
                    'domain': getattr(rec, 'domain', 'general'),
                    'title': getattr(rec, 'title', ''),
                    'description': getattr(rec, 'description', ''),
                    'action_type': getattr(rec, 'action_type', ''),
                    'urgency': getattr(rec, 'urgency', ''),
                    'rationale': getattr(rec, 'rationale', ''),
                    'confidence': getattr(rec, 'confidence', 'medium'),
                    'reasoning': getattr(rec, 'reasoning', ''),
                    'mna_lens': getattr(rec, 'mna_lens', ''),
                    'mna_implication': getattr(rec, 'mna_implication', ''),
                    'based_on_facts': getattr(rec, 'based_on_facts', []),
                }

                if writer.write_finding(db_session, finding_data, self.deal_id, self.run_id, commit=False):
                    self._written_finding_ids.add(finding_id)
                    new_count += 1

            if new_count > 0:
                db_session.commit()
                logger.debug(f"Persisted {new_count} new findings incrementally")

        return new_count

    def update_progress(self, progress: float, current_step: str = ''):
        """Update analysis run progress (throttled)."""
        writer = self._get_writer()
        with writer.session_scope() as db_session:
            writer.update_analysis_progress(
                db_session,
                self.run_id,
                progress=progress,
                current_step=current_step,
                facts_created=len(self._written_fact_ids),
                findings_created=len(self._written_finding_ids)
            )

    def complete(self, status: str = 'completed', error_message: str = ''):
        """Mark analysis run as complete and generate diff."""
        writer = self._get_writer()
        with writer.session_scope() as db_session:
            writer.complete_analysis_run(
                db_session,
                self.run_id,
                status=status,
                error_message=error_message,
                facts_created=len(self._written_fact_ids),
                findings_created=len(self._written_finding_ids)
            )

        # Generate run diff (Phase 1a: What Changed)
        if status == 'completed':
            try:
                from services.run_diff_service import generate_run_diff
                diff = generate_run_diff(self.deal_id, self.run_id)
                if diff:
                    logger.info(f"Run diff generated: +{diff.facts_created} facts, +{diff.risks_created} risks")
            except Exception as e:
                logger.warning(f"Failed to generate run diff (non-fatal): {e}")

    def get_stats(self) -> Dict[str, int]:
        """Get counts of what's been persisted."""
        return {
            'facts': len(self._written_fact_ids),
            'gaps': len(self._written_gap_ids),
            'findings': len(self._written_finding_ids),
        }

    def cleanup(self):
        """
        Explicitly clear tracking sets to free memory.

        MEMORY FIX: Called after analysis completes to release memory
        held by fact/finding ID sets (can be 1000s of strings).
        """
        self._written_fact_ids.clear()
        self._written_gap_ids.clear()
        self._written_finding_ids.clear()
        import gc
        gc.collect()
        logger.debug(f"IncrementalPersistence cleanup: cleared tracking sets and forced GC")


def create_analysis_run(app, deal_id: str, task_id: str = None) -> Optional[str]:
    """
    Create an analysis run record at the START of analysis.

    Returns the run_id, or None on failure.
    """
    try:
        from stores.db_writer import get_db_writer
        writer = get_db_writer(app)

        with writer.session_scope() as session:
            run_id = writer.create_analysis_run(
                session,
                deal_id=deal_id,
                task_id=task_id,
                run_type='full'
            )
            return run_id
    except Exception as e:
        logger.error(f"Failed to create analysis run: {e}")
        return None


def persist_to_database(session, deal_id: str, timestamp: str) -> Dict[str, int]:
    """
    Persist session facts and findings to database.

    Args:
        session: Analysis session with fact_store and reasoning_store
        deal_id: Database Deal ID to associate facts/findings with
        timestamp: Analysis run timestamp

    Returns:
        Dict with counts of persisted items
    """
    from web.database import db, Fact, Finding, AnalysisRun, Gap
    from uuid import uuid4

    result = {'facts_count': 0, 'findings_count': 0, 'analysis_run_id': None}

    # Note: Assumes caller has established Flask app context (task_manager does this)

    # Get next run number for this deal
    from sqlalchemy import func
    max_run = db.session.query(func.max(AnalysisRun.run_number)).filter_by(deal_id=deal_id).scalar()
    next_run_number = (max_run or 0) + 1

    analysis_run_id = str(uuid4())
    analysis_run = AnalysisRun(
        id=analysis_run_id,
        deal_id=deal_id,
        run_number=next_run_number,
        run_type='full',
        status='completed',
        domains=list(set(f.domain for f in session.fact_store.facts)),
        facts_created=len(session.fact_store.facts),
        findings_created=len(session.reasoning_store.risks) + len(session.reasoning_store.work_items),
        started_at=datetime.utcnow(),
        completed_at=datetime.utcnow(),
    )
    db.session.add(analysis_run)
    result['analysis_run_id'] = analysis_run_id

    # Persist facts
    for fact in session.fact_store.facts:
        # Get source_document - may be very long if fact cites multiple docs
        source_doc = fact.source_document or ''
        # Safety: if column is still VARCHAR(255), store first doc or truncate
        # This allows graceful handling until DB migration runs
        if len(source_doc) > 250:
            # Store just the document names in a sensible way
            docs = [d.strip() for d in source_doc.split(',')]
            source_doc = ', '.join(docs[:3])  # First 3 docs
            if len(docs) > 3:
                source_doc += f' (+{len(docs) - 3} more)'

        db_fact = Fact(
            id=fact.fact_id,
            deal_id=deal_id,
            analysis_run_id=analysis_run_id,
            domain=fact.domain,
            category=fact.category or '',
            entity=fact.entity,
            item=fact.item,
            status=fact.status,
            details=fact.details or {},
            evidence=fact.evidence or {},
            source_document=source_doc,
            source_quote=fact.evidence.get('exact_quote', '') if fact.evidence else '',
            confidence_score=getattr(fact, 'confidence_score', 0.5),
            verified=getattr(fact, 'verified', False),
            verification_status=getattr(fact, 'verification_status', 'pending'),
            needs_review=getattr(fact, 'needs_review', False),
            needs_review_reason=getattr(fact, 'needs_review_reason', ''),
            analysis_phase=getattr(fact, 'analysis_phase', 'target_extraction'),
            is_integration_insight=getattr(fact, 'is_integration_insight', False),
            related_domains=getattr(fact, 'related_domains', []),
            change_type='new',
        )
        db.session.add(db_fact)
        result['facts_count'] += 1

    # Persist findings (risks)
    # Note: Risk is a dataclass, access via attributes not dict
    for risk in session.reasoning_store.risks:
        # Risk dataclass has 'finding_id' attribute
        finding_id = getattr(risk, 'finding_id', None) or f"R-{uuid4().hex[:8].upper()}"

        # Serialize cost_buildup if present (same pattern as work_items)
        cost_buildup_json = None
        cost_buildup = getattr(risk, 'cost_buildup', None)
        if cost_buildup and hasattr(cost_buildup, 'to_dict'):
            cost_buildup_json = cost_buildup.to_dict()

        db_finding = Finding(
            id=finding_id,
            deal_id=deal_id,
            analysis_run_id=analysis_run_id,
            finding_type='risk',
            entity=getattr(risk, 'entity', 'target'),
            risk_scope=getattr(risk, 'risk_scope', ''),
            domain=getattr(risk, 'domain', 'general'),
            title=getattr(risk, 'title', ''),
            description=getattr(risk, 'description', ''),
            severity=getattr(risk, 'severity', 'medium'),
            category=getattr(risk, 'category', ''),
            phase=getattr(risk, 'timeline', None),  # Risk uses 'timeline' not 'phase'
            mitigation=getattr(risk, 'mitigation', ''),
            integration_dependent=getattr(risk, 'integration_dependent', False),
            confidence=getattr(risk, 'confidence', 'medium'),
            reasoning=getattr(risk, 'reasoning', ''),
            mna_lens=getattr(risk, 'mna_lens', ''),
            mna_implication=getattr(risk, 'mna_implication', ''),
            cost_buildup_json=cost_buildup_json,
            based_on_facts=getattr(risk, 'based_on_facts', []),
            extra_data={
                'full_risk': risk.to_dict() if hasattr(risk, 'to_dict') else str(risk),
            },
        )
        db.session.add(db_finding)
        result['findings_count'] += 1

    # Persist findings (work items)
    # Note: WorkItem is a dataclass, access via attributes not dict
    for wi in session.reasoning_store.work_items:
        # WorkItem dataclass has 'finding_id' attribute
        finding_id = getattr(wi, 'finding_id', None) or f"WI-{uuid4().hex[:8].upper()}"
        # Serialize cost_buildup if present
        cost_buildup_json = None
        cost_buildup = getattr(wi, 'cost_buildup', None)
        if cost_buildup and hasattr(cost_buildup, 'to_dict'):
            cost_buildup_json = cost_buildup.to_dict()

        db_finding = Finding(
            id=finding_id,
            deal_id=deal_id,
            analysis_run_id=analysis_run_id,
            finding_type='work_item',
            entity=getattr(wi, 'entity', 'target'),
            risk_scope=getattr(wi, 'risk_scope', '') if hasattr(wi, 'risk_scope') else '',
            domain=getattr(wi, 'domain', 'general'),
            title=getattr(wi, 'title', ''),
            description=getattr(wi, 'description', ''),
            priority=getattr(wi, 'priority', 'medium'),
            phase=getattr(wi, 'phase', None),
            owner_type=getattr(wi, 'owner_type', 'shared'),  # WorkItem uses 'owner_type' not 'owner'
            cost_estimate=getattr(wi, 'cost_estimate', ''),
            cost_buildup_json=cost_buildup_json,
            confidence=getattr(wi, 'confidence', 'medium'),
            reasoning=getattr(wi, 'reasoning', ''),
            mna_lens=getattr(wi, 'mna_lens', ''),
            mna_implication=getattr(wi, 'mna_implication', ''),
            triggered_by_risks=getattr(wi, 'triggered_by_risks', []),
            dependencies=getattr(wi, 'dependencies', []),
            based_on_facts=getattr(wi, 'based_on_facts', []),
            extra_data={
                'triggered_by': getattr(wi, 'triggered_by', []),
                'full_work_item': wi.to_dict() if hasattr(wi, 'to_dict') else str(wi),
            },
        )
        db.session.add(db_finding)
        result['findings_count'] += 1

    # Persist gaps
    result['gaps_count'] = 0
    for gap in session.fact_store.gaps:
        gap_id = getattr(gap, 'gap_id', None) or f"GAP-{uuid4().hex[:8].upper()}"
        db_gap = Gap(
            id=gap_id,
            deal_id=deal_id,
            analysis_run_id=analysis_run_id,
            domain=getattr(gap, 'domain', 'general'),
            category=getattr(gap, 'category', ''),
            entity=getattr(gap, 'entity', 'target'),
            description=getattr(gap, 'description', ''),
            importance=getattr(gap, 'importance', 'medium'),
            requested_item=getattr(gap, 'requested_item', ''),
            source_document=getattr(gap, 'source_document', ''),
            related_facts=getattr(gap, 'related_facts', []),
            status='open',
        )
        db.session.add(db_gap)
        result['gaps_count'] += 1

    # Commit all changes
    db.session.commit()

    logger.info(f"Database persistence complete: run={analysis_run_id}, facts={result['facts_count']}, findings={result['findings_count']}, gaps={result['gaps_count']}")

    # Generate run diff (Phase 1a: What Changed)
    try:
        from services.run_diff_service import generate_run_diff
        diff = generate_run_diff(deal_id, analysis_run_id)
        if diff:
            logger.info(f"Run diff generated: +{diff.facts_created} facts, +{diff.risks_created} risks")
    except Exception as e:
        logger.warning(f"Failed to generate run diff (non-fatal): {e}")

    # Generate fact reasoning (Phase 1b: Why This Matters)
    try:
        from services.fact_reasoning_service import generate_reasoning_for_run
        facts_list = list(session.fact_store.facts)
        reasoning_stats = generate_reasoning_for_run(facts_list, analysis_run_id, deal_id)
        logger.info(f"Fact reasoning generated: {reasoning_stats['reasoning_generated']}/{reasoning_stats['high_signal']} high-signal facts")
    except Exception as e:
        logger.warning(f"Failed to generate fact reasoning (non-fatal): {e}")

    return result


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
        from stores.fact_store import FactStore
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


def log_memory_usage(stage: str):
    """
    Log current memory usage for debugging.

    MEMORY FIX: Helps diagnose memory consumption patterns.
    Uses psutil if available, silent fail if not.

    Args:
        stage: Description of current stage (e.g., "Analysis start", "After reasoning")
    """
    try:
        import psutil
        import os
        process = psutil.Process(os.getpid())
        mem_mb = process.memory_info().rss / (1024 * 1024)
        logger.info(f"[MEMORY] {stage}: {mem_mb:.1f}MB")
    except ImportError:
        # psutil not installed - silent fail
        pass
    except Exception as e:
        logger.debug(f"Memory logging failed at {stage}: {e}")


def _separate_documents_by_entity(documents: List[Dict], deal_context: Dict) -> tuple:
    """
    Separate parsed documents into TARGET and BUYER lists.

    Args:
        documents: List of parsed document dicts
        deal_context: Deal context with doc counts

    Returns:
        Tuple of (target_documents, buyer_documents)
    """
    target_doc_count = deal_context.get('target_doc_count', 0)
    buyer_doc_count = deal_context.get('buyer_doc_count', 0)

    target_docs = []
    buyer_docs = []

    for i, doc in enumerate(documents):
        # PRIORITY 1: Check explicit entity field (set during document registration)
        if 'entity' in doc:
            entity = doc['entity'].lower()
            if entity == 'buyer':
                buyer_docs.append(doc)
            else:
                target_docs.append(doc)
            continue

        # PRIORITY 2: Check filename/path patterns
        filename = doc.get('filename', '').lower()
        filepath = doc.get('filepath', '').lower() if 'filepath' in doc else ''

        # Check for 'buyer' anywhere in filename/path (not just 'buyer_')
        if 'buyer' in filename or '/buyer/' in filepath:
            buyer_docs.append(doc)
        elif 'target' in filename or '/target/' in filepath:
            target_docs.append(doc)
        # Fallback: first N docs are target (based on upload order)
        elif target_doc_count > 0 and i < target_doc_count:
            target_docs.append(doc)
        elif buyer_doc_count > 0 and i >= target_doc_count:
            buyer_docs.append(doc)
        else:
            target_docs.append(doc)  # Default to target

    return target_docs, buyer_docs


def _combine_documents_for_entity(documents: List[Dict], entity: str) -> str:
    """
    Combine documents into a single content string for a specific entity.

    Args:
        documents: List of document dicts
        entity: "target" or "buyer"

    Returns:
        Combined content string with clear entity markers
    """
    entity_label = entity.upper()
    content_parts = []

    for doc in documents:
        content_parts.append(
            f"# ENTITY: {entity_label}\n"
            f"## Document: {doc.get('filename', 'Unknown')}\n"
            f"Source Entity: {entity_label} COMPANY\n\n"
            f"{doc.get('content', '')}"
        )

    return "\n\n---\n\n".join(content_parts)


def run_analysis(task: AnalysisTask, progress_callback: Callable, app=None) -> Dict[str, Any]:
    """
    Run the full MULTI-PHASE analysis pipeline.

    Phase 1: Analyze TARGET documents only (clean extraction)
    Phase 2: Analyze BUYER documents with TARGET facts as context
    Phase 3.5: Generate OVERLAP MAP comparing target vs buyer facts
    Phase 4: Run REASONING agents with buyer-aware context

    This prevents entity contamination by ensuring the LLM only sees
    one entity's documents at a time, then explicitly compares them.

    INCREMENTAL PERSISTENCE: Facts and findings are written to database
    immediately after extraction. If analysis crashes, data up to the
    last successful write is preserved.

    Args:
        task: The analysis task with file paths and configuration
        progress_callback: Callback to report progress updates
        app: Flask app instance (for incremental DB writes)

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
    deal_context = task.deal_context or {}
    deal_id = deal_context.get('deal_id')

    # ==========================================================================
    # INCREMENTAL PERSISTENCE SETUP
    # ==========================================================================
    incremental = None
    run_id = None

    if app and deal_id:
        try:
            # Create analysis run record FIRST (before any work)
            task_id = f"analysis_{timestamp}"
            run_id = create_analysis_run(app, deal_id, task_id)
            if run_id:
                incremental = IncrementalPersistence(app, deal_id, run_id)
                logger.info(f"Incremental persistence enabled: run_id={run_id}")
            else:
                logger.warning("Could not create analysis run - falling back to batch persistence")
        except Exception as e:
            logger.warning(f"Incremental persistence setup failed: {e} - falling back to batch")

    # Initialize progress
    progress_callback({
        "phase": AnalysisPhase.INITIALIZING,
        "total_documents": len(task.file_paths),
        "documents_processed": 0,
    })

    # MEMORY FIX: Log baseline memory usage
    log_memory_usage("Analysis start")

    # Check for API key
    if not ANTHROPIC_API_KEY:
        if incremental:
            incremental.complete('failed', 'ANTHROPIC_API_KEY not configured')
        raise ValueError("ANTHROPIC_API_KEY not configured. Set it in .env file or environment.")

    # Create session with deal_id for proper data isolation
    session = Session(deal_id=deal_id)

    # Create InventoryStore for deduplication and structured inventory tracking
    from stores.inventory_store import InventoryStore
    inventory_store = InventoryStore(deal_id=deal_id)
    session._inventory_store = inventory_store  # Attach to session for pipeline access
    print(f"[INVENTORY] Created InventoryStore for deal {deal_id}, storage_path: {inventory_store.storage_path}")

    # Add deal context - properly populate the dict for reasoning agents
    session.deal_context = {
        'deal_id': deal_context.get('deal_id'),  # CRITICAL: Required for database persistence
        'deal_type': deal_context.get('deal_type', 'bolt_on'),
        'target_name': deal_context.get('target_name', 'Target Company'),
        'buyer_name': deal_context.get('buyer_name', ''),
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
    session.deal_context['_prompt_context'] = dc.to_prompt_context()

    # Parse all documents
    progress_callback({
        "phase": AnalysisPhase.PARSING_DOCUMENTS,
    })

    file_paths = [Path(f) for f in task.file_paths]
    documents = parse_documents(file_paths)

    if not documents:
        raise ValueError("No documents could be parsed from the uploaded files.")

    # CRITICAL: Separate documents by entity BEFORE analysis
    target_docs, buyer_docs = _separate_documents_by_entity(documents, deal_context)

    logger.info(f"Document separation: {len(target_docs)} TARGET, {len(buyer_docs)} BUYER")

    progress_callback({
        "documents_processed": len(documents),
        "total_documents": len(documents),
    })

    # Determine which domains to analyze
    domains_to_analyze = task.domains if task.domains else DOMAINS

    # =========================================================================
    # PHASE 1: TARGET COMPANY ANALYSIS (Clean Extraction)
    # =========================================================================
    progress_callback({"phase": AnalysisPhase.TARGET_ANALYSIS_START})

    if target_docs:
        target_content = _combine_documents_for_entity(target_docs, "target")
        target_doc_names = ", ".join([doc.get('filename', 'Unknown') for doc in target_docs])

        logger.info(f"Starting Phase 1: TARGET analysis with {len(target_docs)} documents")

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
                if incremental:
                    incremental.complete('cancelled')
                return {}

            phase = discovery_phases.get(domain, AnalysisPhase.DISCOVERY_INFRASTRUCTURE)
            progress_callback({"phase": phase})

            try:
                # Phase 1: Only TARGET content, entity forced to "target"
                facts, gaps = run_discovery_for_domain(
                    domain, target_content, session, session._inventory_store,
                    target_doc_names,
                    entity="target", analysis_phase="target_extraction"
                )

                # INCREMENTAL WRITE: Persist facts/gaps immediately after each domain
                if incremental:
                    incremental.persist_new_facts(session.fact_store)
                    incremental.persist_new_gaps(session.fact_store)
                    incremental.update_progress(20.0, f"TARGET {domain} complete")

                progress_callback({
                    "facts_extracted": len(session.fact_store.facts),
                })
            except Exception as e:
                logger.error(f"Error in TARGET {domain} discovery: {e}")

    # Lock TARGET facts before Phase 2
    progress_callback({"phase": AnalysisPhase.TARGET_ANALYSIS_COMPLETE})
    target_fact_count = session.fact_store.lock_entity_facts("target")
    logger.info(f"Phase 1 complete: Locked {target_fact_count} TARGET facts")

    # MEMORY FIX: Log memory after document loading phase
    log_memory_usage("After document loading and target discovery")

    # Create snapshot of TARGET facts for Phase 2 context
    target_snapshot = session.fact_store.create_snapshot("target")

    # =========================================================================
    # PHASE 2: BUYER COMPANY ANALYSIS (With Target Context)
    # =========================================================================
    if buyer_docs:
        progress_callback({"phase": AnalysisPhase.BUYER_ANALYSIS_START})

        buyer_content = _combine_documents_for_entity(buyer_docs, "buyer")
        buyer_doc_names = ", ".join([doc.get('filename', 'Unknown') for doc in buyer_docs])

        logger.info(f"Starting Phase 2: BUYER analysis with {len(buyer_docs)} documents")
        logger.info(f"Providing {len(target_snapshot.facts)} TARGET facts as read-only context")

        buyer_discovery_phases = {
            "infrastructure": AnalysisPhase.BUYER_DISCOVERY_INFRASTRUCTURE,
            "network": AnalysisPhase.BUYER_DISCOVERY_NETWORK,
            "cybersecurity": AnalysisPhase.BUYER_DISCOVERY_CYBERSECURITY,
            "applications": AnalysisPhase.BUYER_DISCOVERY_APPLICATIONS,
            "identity_access": AnalysisPhase.BUYER_DISCOVERY_IDENTITY,
            "organization": AnalysisPhase.BUYER_DISCOVERY_ORGANIZATION,
        }

        for domain in domains_to_analyze:
            if task._cancelled:
                if incremental:
                    incremental.complete('cancelled')
                return {}

            phase = buyer_discovery_phases.get(domain, AnalysisPhase.BUYER_DISCOVERY_INFRASTRUCTURE)
            progress_callback({"phase": phase})

            try:
                # Phase 2: Only BUYER content, with TARGET context, entity forced to "buyer"
                facts, gaps = run_discovery_for_domain(
                    domain, buyer_content, session, session._inventory_store,
                    buyer_doc_names,
                    entity="buyer", analysis_phase="buyer_extraction",
                    target_context=target_snapshot
                )

                # INCREMENTAL WRITE: Persist BUYER facts/gaps immediately
                if incremental:
                    incremental.persist_new_facts(session.fact_store)
                    incremental.persist_new_gaps(session.fact_store)
                    incremental.update_progress(50.0, f"BUYER {domain} complete")

                progress_callback({
                    "facts_extracted": len(session.fact_store.facts),
                })
            except Exception as e:
                logger.error(f"Error in BUYER {domain} discovery: {e}")

        progress_callback({"phase": AnalysisPhase.BUYER_ANALYSIS_COMPLETE})
        logger.info(f"Phase 2 complete: {len(session.fact_store.get_entity_facts('buyer'))} BUYER facts")
    else:
        logger.info("No BUYER documents - skipping Phase 2")

    # =========================================================================
    # PHASE 3.5: OVERLAP GENERATION (Buyer-Aware Reasoning)
    # =========================================================================
    # Generate overlap map by comparing TARGET and BUYER facts across domains.
    # This produces overlaps_by_domain.json artifact for reasoning agents.

    progress_callback({"phase": AnalysisPhase.OVERLAP_GENERATION})

    overlaps_by_domain = {}
    overlap_output_path = None

    if buyer_docs:
        logger.info("Starting Phase 3.5: Overlap Generation")

        try:
            from services.overlap_generator import OverlapGenerator

            # Organize facts by domain and entity
            facts_by_domain = {}
            for domain in domains_to_analyze:
                target_facts = [f.to_dict() for f in session.fact_store.facts
                               if f.domain == domain and f.entity == "target"]
                buyer_facts = [f.to_dict() for f in session.fact_store.facts
                              if f.domain == domain and f.entity == "buyer"]

                facts_by_domain[domain] = {
                    "target": target_facts,
                    "buyer": buyer_facts
                }

            # Generate overlaps
            generator = OverlapGenerator()
            overlaps_by_domain = generator.generate_overlap_map_all_domains(facts_by_domain)

            # Save to file
            overlap_output_path = f"{OUTPUT_DIR}/overlaps_{timestamp}.json"
            generator.save_overlaps_to_file(overlaps_by_domain, overlap_output_path)
            logger.info(f"Saved overlap map to {overlap_output_path}")

            # Store overlaps in session for reasoning agents
            session.overlaps_by_domain = overlaps_by_domain

            total_overlaps = sum(len(overlaps) for overlaps in overlaps_by_domain.values())
            logger.info(f"Phase 3.5 complete: Generated {total_overlaps} overlaps across {len(overlaps_by_domain)} domains")

        except Exception as e:
            logger.error(f"Error in overlap generation: {e}")
            logger.error(traceback.format_exc())
            # Graceful degradation - continue without overlaps
            session.overlaps_by_domain = {}
    else:
        logger.info("No BUYER documents - skipping overlap generation")
        session.overlaps_by_domain = {}

    # =========================================================================
    # PHASE 3.7: FACT PROMOTION (Convert facts to inventory items)
    # =========================================================================
    progress_callback({"phase": AnalysisPhase.OVERLAP_GENERATION})  # Reuse progress phase

    logger.info("Starting Phase 3.7: Fact Promotion")

    try:
        from tools_v2.inventory_integration import promote_facts_to_inventory

        # Promote LLM-extracted facts to inventory items for both entities
        for entity_val in ["target", "buyer"]:
            promotion_stats = promote_facts_to_inventory(
                fact_store=session.fact_store,
                inventory_store=inventory_store,
                entity=entity_val,
            )
            if promotion_stats["promoted"] > 0 or promotion_stats["matched"] > 0:
                logger.info(
                    f"[PROMOTION] {entity_val}: {promotion_stats['promoted']} new items, "
                    f"{promotion_stats['matched']} matched to existing"
                )

        # Save inventory after promotion
        if hasattr(session, '_inventory_store') and session._inventory_store:
            try:
                session._inventory_store.save()
                logger.info(f"[PROMOTION] Saved {len(session._inventory_store)} inventory items after promotion")
            except Exception as e:
                logger.warning(f"Failed to save inventory after promotion: {e}")

    except Exception as e:
        logger.error(f"Error in fact promotion: {e}")
        import traceback
        logger.error(traceback.format_exc())
        # Non-fatal - continue to reasoning

    # =========================================================================
    # PHASE 4: REASONING (PARALLEL)
    # =========================================================================
    progress_callback({"phase": AnalysisPhase.REASONING})

    # Run reasoning for all domains in parallel (max 3 concurrent)
    from config_v2 import PARALLEL_REASONING, MAX_PARALLEL_AGENTS
    import threading

    reasoning_lock = threading.Lock()  # Protect shared session state
    completed_domains = []

    def run_domain_reasoning(domain):
        """Run reasoning for a single domain, return results."""
        if task._cancelled:
            return domain, None, None
        try:
            run_reasoning_for_domain(domain, session)
            # Return counts for progress update
            with reasoning_lock:
                risks_count = len(session.reasoning_store.risks)
                work_items_count = len(session.reasoning_store.work_items)
            return domain, risks_count, work_items_count
        except Exception as e:
            logger.error(f"Error in {domain} reasoning: {e}")
            return domain, None, str(e)

    if PARALLEL_REASONING and len(domains_to_analyze) > 1:
        # Parallel execution
        logger.info(f"Running PARALLEL reasoning for {len(domains_to_analyze)} domains (max {MAX_PARALLEL_AGENTS} concurrent)")
        with ThreadPoolExecutor(max_workers=MAX_PARALLEL_AGENTS) as executor:
            futures = {executor.submit(run_domain_reasoning, d): d for d in domains_to_analyze}

            for future in as_completed(futures):
                domain = futures[future]
                try:
                    result_domain, risks_count, work_items_count = future.result(timeout=600)  # 10 min timeout
                    completed_domains.append(result_domain)

                    if risks_count is not None:
                        # INCREMENTAL WRITE: Persist findings after each domain
                        if incremental:
                            with reasoning_lock:
                                incremental.persist_new_findings(session.reasoning_store)
                            incremental.update_progress(75.0, f"Reasoning {domain} complete ({len(completed_domains)}/{len(domains_to_analyze)})")

                        # Update progress with phase info for UI display
                        progress_callback({
                            "phase": AnalysisPhase.REASONING,
                            "phase_display": f"Identifying Risks... ({len(completed_domains)}/{len(domains_to_analyze)} domains)",
                            "risks_identified": risks_count,
                            "work_items_created": work_items_count,
                        })
                        logger.info(f"Reasoning complete: {domain} ({len(completed_domains)}/{len(domains_to_analyze)})")

                        # MEMORY FIX: Force garbage collection after each domain completes
                        import gc
                        gc.collect()
                        logger.debug(f"Garbage collected after {domain} reasoning")
                        log_memory_usage(f"After {domain} reasoning")
                except Exception as e:
                    logger.error(f"Reasoning failed for {domain}: {e}")
    else:
        # Sequential execution (fallback or single domain)
        for domain in domains_to_analyze:
            if task._cancelled:
                if incremental:
                    incremental.complete('cancelled')
                return {}

            try:
                run_reasoning_for_domain(domain, session)
                completed_domains.append(domain)

                # INCREMENTAL WRITE: Persist findings immediately after each domain
                if incremental:
                    incremental.persist_new_findings(session.reasoning_store)
                    incremental.update_progress(75.0, f"Reasoning {domain} complete")

                # MEMORY FIX: Force garbage collection after each domain (sequential mode)
                import gc
                gc.collect()
                logger.debug(f"Garbage collected after {domain} reasoning (sequential)")

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

    # Save InventoryStore to deal-specific JSON file for deduplication
    if hasattr(session, '_inventory_store') and session._inventory_store:
        try:
            print(f"[INVENTORY] Attempting to save {len(session._inventory_store)} items to {session._inventory_store.storage_path}")
            session._inventory_store.save()
            item_count = len(session._inventory_store)
            print(f"[INVENTORY] ✅ Save successful: {item_count} items")
            logger.info(f"✅ [INVENTORY] Saved {item_count} inventory items to {session._inventory_store.storage_path}")
            saved_files['inventory'] = session._inventory_store.storage_path
        except Exception as e:
            # CRITICAL MONITORING: InventoryStore save failure means deduplication won't work
            print(f"[INVENTORY] ❌ SAVE FAILED: {e}")
            print(f"[INVENTORY] Path attempted: {session._inventory_store.storage_path if session._inventory_store else 'N/A'}")
            logger.error(f"❌ [INVENTORY] Failed to save InventoryStore for deal {deal_id}: {e}")
            logger.error(f"[INVENTORY] Path attempted: {session._inventory_store.storage_path if session._inventory_store else 'N/A'}")
            import traceback
            logger.debug(f"[INVENTORY] Stack trace: {traceback.format_exc()}")
            # Continue - Facts are still persisted, InventoryStore is optional optimization
            # UI will fall back to Facts (may show duplicates)

    # ==========================================================================
    # DATABASE PERSISTENCE: Finalize or fall back to batch
    # ==========================================================================
    if incremental:
        # Incremental mode: data already written, just mark complete
        try:
            incremental.complete('completed')
            stats = incremental.get_stats()
            logger.info(f"Incremental persistence complete: {stats['facts']} facts, {stats['findings']} findings, {stats['gaps']} gaps")

            # MEMORY FIX: Clean up tracking sets
            incremental.cleanup()
        except Exception as e:
            logger.error(f"Failed to complete analysis run: {e}")
    elif deal_id:
        # Fallback: batch persistence at end (legacy mode)
        try:
            db_result = persist_to_database(
                session=session,
                deal_id=deal_id,
                timestamp=timestamp
            )
            logger.info(f"Batch persisted to database: {db_result['facts_count']} facts, {db_result['findings_count']} findings")
        except Exception as e:
            logger.error(f"Database persistence failed (non-fatal): {e}")
            # Continue - JSON files are already saved as backup
    else:
        logger.warning("No deal_id in context - skipping database persistence")

    # Save open questions separately
    # A3 FIX: Include deal_id in filename for proper isolation
    if open_questions:
        import json
        if deal_id:
            questions_file = OUTPUT_DIR / f"open_questions_{deal_id}_{timestamp}.json"
        else:
            questions_file = OUTPUT_DIR / f"open_questions_{timestamp}.json"
        with open(questions_file, 'w') as f:
            json.dump(open_questions, f, indent=2)
        saved_files['open_questions'] = questions_file
        logger.info(f"A3: Saved questions to {questions_file.name}")

    # Get the actual saved file paths from the saved_files dict
    facts_file = saved_files.get('facts')
    findings_file = saved_files.get('findings')

    # Get entity breakdown for summary
    phase_summary = session.fact_store.get_phase_summary()

    # Create result summary with entity breakdown
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
        },
        # Two-Phase Analysis breakdown
        "entity_breakdown": {
            "target": {
                "facts_count": phase_summary["target"]["fact_count"],
                "locked": phase_summary["target"]["locked"],
                "domains": phase_summary["target"]["domains"]
            },
            "buyer": {
                "facts_count": phase_summary["buyer"]["fact_count"],
                "locked": phase_summary["buyer"]["locked"],
                "domains": phase_summary["buyer"]["domains"]
            },
            "integration_insights": {
                "count": phase_summary["integration_insights"]["count"]
            }
        }
    }

    progress_callback({"phase": AnalysisPhase.COMPLETE})

    return result


def run_discovery_for_domain(
    domain: str,
    content: str,
    session,
    inventory_store,
    document_names: str = "",
    entity: str = "target",
    analysis_phase: str = "target_extraction",
    target_context: Optional[Any] = None
) -> tuple:
    """Run discovery agent for a specific domain.

    Args:
        domain: Domain to analyze (infrastructure, network, etc.)
        content: Combined document content (for ONE entity only)
        session: Analysis session with fact_store
        inventory_store: InventoryStore for deduplication and structured items
        document_names: Comma-separated list of source document filenames for traceability
        entity: "target" or "buyer" - which entity we're extracting facts for
        analysis_phase: "target_extraction" or "buyer_extraction"
        target_context: FactStoreSnapshot of TARGET facts (for Phase 2 only)

    Returns:
        Tuple of (facts, gaps) extracted in this run
    """
    from stores.fact_store import FactStore
    from config_v2 import ANTHROPIC_API_KEY

    # Import the appropriate discovery agent
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

    entity_label = entity.upper()
    logger.info(f"Starting {entity_label} discovery for domain: {domain}")

    # Track facts before this run to calculate delta
    facts_before = len(session.fact_store.facts)
    gaps_before = len(session.fact_store.gaps)

    try:
        import importlib
        module = importlib.import_module(module_name)
        agent_class = getattr(module, class_name)

        # Get company name from deal context based on entity
        if session.deal_context and isinstance(session.deal_context, dict):
            if entity == "target":
                company_name = session.deal_context.get('target_name', 'Target Company')
            else:
                company_name = session.deal_context.get('buyer_name', 'Buyer Company')
        else:
            company_name = 'Target Company' if entity == 'target' else 'Buyer Company'

        # Create agent with entity-specific configuration
        agent = agent_class(
            fact_store=session.fact_store,
            api_key=ANTHROPIC_API_KEY,
            target_name=company_name,  # This is the company being analyzed
            inventory_store=inventory_store  # Enable InventoryStore population
        )

        # Prepare content with optional TARGET context for Phase 2
        analysis_content = content
        if target_context and entity == "buyer":
            # Prepend TARGET facts as read-only context
            context_str = target_context.to_context_string(include_evidence=False)
            analysis_content = f"{context_str}\n\n---\n\nNow analyze the BUYER documents below:\n\n{content}"
            logger.info(f"Injected {len(target_context.facts)} TARGET facts as context for BUYER analysis")

        # Run discovery with entity enforcement
        logger.info(f"Running {entity_label} {domain} discovery agent...")
        result = agent.discover(
            analysis_content,
            document_name=document_names,
            entity=entity,  # CRITICAL: Pass entity to enforce target vs buyer
            analysis_phase=analysis_phase
        )

        # Calculate what was added in this run
        facts_added = len(session.fact_store.facts) - facts_before
        gaps_added = len(session.fact_store.gaps) - gaps_before

        logger.info(
            f"{entity_label} discovery complete for {domain}: "
            f"+{facts_added} facts, +{gaps_added} gaps"
        )

        # Return only facts from this entity
        entity_facts = session.fact_store.get_entity_facts(entity)
        entity_gaps = [g for g in session.fact_store.gaps if getattr(g, 'entity', 'target') == entity]

        return entity_facts, entity_gaps

    except ImportError as e:
        logger.warning(f"Could not import discovery agent for {domain}: {e}")
        return [], []
    except Exception as e:
        logger.error(f"Error running {entity_label} discovery for {domain}: {e}")
        import traceback
        logger.error(traceback.format_exc())
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

        # Get overlaps for this domain (if available)
        overlaps_for_domain = []
        if hasattr(session, 'overlaps_by_domain'):
            overlap_objects = session.overlaps_by_domain.get(domain, [])
            # Convert OverlapCandidate objects to dicts for JSON serialization
            overlaps_for_domain = [asdict(overlap) if hasattr(overlap, '__dataclass_fields__') else overlap
                                   for overlap in overlap_objects]

        # Create and run agent with required arguments
        agent = agent_class(
            fact_store=session.fact_store,
            api_key=ANTHROPIC_API_KEY
        )

        # Enrich deal context with overlaps (as dicts, not objects)
        deal_context_with_overlaps = dict(session.deal_context)
        deal_context_with_overlaps['overlaps'] = overlaps_for_domain

        result = agent.reason(deal_context_with_overlaps)

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

    # Get deal_id from task context for deal-scoped session
    deal_id = task.deal_context.get('deal_id') if task.deal_context else None
    session = Session(deal_id=deal_id)

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

    # DATABASE PERSISTENCE - Critical for UI to display facts
    if deal_id:
        try:
            db_result = persist_to_database(session=session, deal_id=deal_id, timestamp=timestamp)
            logger.info(f"[run_analysis_simple] Persisted to database: {db_result.get('facts_count', 0)} facts, {db_result.get('findings_count', 0)} findings for deal {deal_id}")
        except Exception as e:
            logger.error(f"[run_analysis_simple] Database persistence failed for deal {deal_id}: {e}")
            # Continue - file-based results are still available
    else:
        logger.warning("[run_analysis_simple] No deal_id available - skipping database persistence")

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
