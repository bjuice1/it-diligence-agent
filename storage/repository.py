"""
Repository Layer for IT Due Diligence Agent

Point 46 of 115PP: CRUD operations for all entity types.

Provides:
- Create/Read/Update/Delete for all entities
- Query by domain, run, document
- Batch operations for importing from AnalysisStore
- Support for iterative analysis
- Proper error handling and transaction management
"""

import sqlite3
import logging
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from dataclasses import asdict
import json

from storage.database import Database, get_db
from storage.models import (
    Document,
    AnalysisRun,
    InventoryItem,
    Risk,
    Gap,
    Assumption,
    WorkItem,
    Recommendation,
    StrategicConsideration,
    Question,
    generate_id,
    now_iso
)

# Configure logging
logger = logging.getLogger(__name__)


class RepositoryError(Exception):
    """Base exception for repository operations"""
    pass


class EntityNotFoundError(RepositoryError):
    """Raised when entity is not found"""
    pass


class DuplicateEntityError(RepositoryError):
    """Raised when trying to create duplicate entity"""
    pass


class ValidationError(RepositoryError):
    """Raised when entity validation fails"""
    pass


class Repository:
    """
    Data access layer for all entity types.

    Supports:
    - Single entity CRUD with error handling
    - Batch imports from AnalysisStore
    - Queries by domain, run, document
    - Iterative analysis (merge/update existing)
    - Proper transaction management
    """

    # Explicit column lists for each table (prevents SQL injection)
    DOCUMENT_COLUMNS = [
        'document_id', 'document_name', 'document_path', 'document_type',
        'page_count', 'ingested_date', 'last_updated', 'file_hash', 'metadata'
    ]

    RUN_COLUMNS = [
        'run_id', 'run_name', 'started_at', 'completed_at', 'mode',
        'status', 'deal_context', 'documents_analyzed', 'summary'
    ]

    INVENTORY_COLUMNS = [
        'item_id', 'run_id', 'domain', 'category', 'item_name', 'description',
        'status', 'maturity', 'standalone_viability', 'key_characteristics',
        'source_document_id', 'source_page', 'source_section', 'source_evidence',
        'created_at', 'updated_at'
    ]

    RISK_COLUMNS = [
        'risk_id', 'run_id', 'domain', 'risk_description', 'trigger_description',
        'severity', 'likelihood', 'risk_type', 'integration_dependent',
        'standalone_exposure', 'deal_impact', 'impact_description', 'mitigation',
        'cost_impact_estimate', 'risk_score', 'priority_rank', 'source_type',
        'source_document_id', 'source_page', 'source_section', 'speaker_name',
        'statement_date', 'confidence_level', 'source_evidence', 'created_at', 'updated_at'
    ]

    GAP_COLUMNS = [
        'gap_id', 'run_id', 'domain', 'gap_description', 'why_needed', 'priority',
        'gap_type', 'suggested_source', 'cost_impact', 'question_status',
        'source_type', 'source_document_id', 'source_section', 'confidence_level',
        'created_at', 'updated_at'
    ]

    ASSUMPTION_COLUMNS = [
        'assumption_id', 'run_id', 'domain', 'assumption_text', 'basis',
        'confidence', 'impact', 'validation_needed', 'validation_status',
        'supporting_quote', 'source_type', 'source_document_id', 'source_section',
        'speaker_name', 'statement_date', 'created_at', 'updated_at'
    ]

    WORK_ITEM_COLUMNS = [
        'work_item_id', 'run_id', 'domain', 'title', 'description', 'category',
        'phase', 'phase_rationale', 'effort_estimate', 'cost_estimate_range',
        'depends_on', 'skills_required', 'triggered_by', 'priority_score',
        'source_document_id', 'created_at', 'updated_at'
    ]

    RECOMMENDATION_COLUMNS = [
        'recommendation_id', 'run_id', 'domain', 'recommendation_text', 'rationale',
        'priority', 'timing', 'investment_required', 'driven_by',
        'source_document_id', 'created_at', 'updated_at'
    ]

    STRATEGIC_CONSIDERATION_COLUMNS = [
        'consideration_id', 'run_id', 'domain', 'theme', 'observation',
        'implication', 'deal_relevance', 'buyer_alignment', 'source_type',
        'source_document_id', 'source_section', 'source_evidence', 'speaker_name',
        'statement_date', 'confidence_level', 'created_at', 'updated_at'
    ]

    QUESTION_COLUMNS = [
        'question_id', 'run_id', 'linked_gap_id', 'linked_assumption_id',
        'question_text', 'context', 'priority', 'status', 'sent_date',
        'answer_text', 'answer_date', 'answer_source', 'created_at', 'updated_at'
    ]

    def __init__(self, db: Database = None):
        self.db = db or get_db()
        # Note: initialize_schema() should be called by caller or get_db()
        # Don't call it here to avoid duplicate initialization messages

    def _execute_insert(self, table: str, columns: List[str], data: Dict,
                        replace_on_conflict: bool = False) -> bool:
        """Execute an INSERT with proper error handling

        Args:
            table: Table name to insert into
            columns: Valid columns for this table
            data: Dictionary of column->value pairs
            replace_on_conflict: If True, use INSERT OR REPLACE to update existing rows
        """
        # Handle case where data is not a dict (e.g., string)
        if not isinstance(data, dict):
            logger.warning(f"Invalid data type for {table}: {type(data).__name__}, expected dict")
            raise RepositoryError(f"Invalid data type: expected dict, got {type(data).__name__}")

        # Filter data to only include valid columns
        filtered_data = {k: v for k, v in data.items() if k in columns}
        cols = ', '.join(filtered_data.keys())
        placeholders = ', '.join(['?' for _ in filtered_data])

        try:
            with self.db.transaction() as conn:
                insert_cmd = "INSERT OR REPLACE" if replace_on_conflict else "INSERT"
                conn.execute(
                    f"{insert_cmd} INTO {table} ({cols}) VALUES ({placeholders})",
                    list(filtered_data.values())
                )
            return True
        except sqlite3.IntegrityError as e:
            if "UNIQUE constraint failed" in str(e):
                logger.warning(f"Duplicate entry in {table}: {e}")
                raise DuplicateEntityError(f"Duplicate entry in {table}: {e}")
            logger.error(f"Integrity error in {table}: {e}")
            raise RepositoryError(f"Integrity error: {e}")
        except sqlite3.OperationalError as e:
            logger.error(f"Operational error in {table}: {e}")
            raise RepositoryError(f"Database operational error: {e}")
        except sqlite3.DatabaseError as e:
            logger.error(f"Database error in {table}: {e}")
            raise RepositoryError(f"Database error: {e}")

    # Tables that have updated_at column
    TABLES_WITH_UPDATED_AT = {
        'inventory_items', 'risks', 'gaps', 'assumptions',
        'work_items', 'recommendations', 'strategic_considerations',
        'questions', 'assumption_evidence'
    }

    def _execute_update(self, table: str, id_column: str, id_value: str,
                        updates: Dict[str, Any]) -> bool:
        """Execute an UPDATE with proper error handling"""
        if not updates:
            return False

        # Only add updated_at for tables that have the column
        if table in self.TABLES_WITH_UPDATED_AT:
            updates['updated_at'] = now_iso()
        set_clause = ', '.join([f"{k} = ?" for k in updates.keys()])

        try:
            with self.db.transaction() as conn:
                result = conn.execute(
                    f"UPDATE {table} SET {set_clause} WHERE {id_column} = ?",
                    list(updates.values()) + [id_value]
                )
                if result.rowcount == 0:
                    raise EntityNotFoundError(f"{table} with {id_column}={id_value} not found")
            return True
        except sqlite3.DatabaseError as e:
            logger.error(f"Update error in {table}: {e}")
            raise RepositoryError(f"Update failed: {e}")

    def _execute_delete(self, table: str, id_column: str, id_value: str) -> bool:
        """Execute a DELETE with proper error handling"""
        try:
            with self.db.transaction() as conn:
                result = conn.execute(
                    f"DELETE FROM {table} WHERE {id_column} = ?",
                    (id_value,)
                )
                if result.rowcount == 0:
                    raise EntityNotFoundError(f"{table} with {id_column}={id_value} not found")
            return True
        except sqlite3.DatabaseError as e:
            logger.error(f"Delete error in {table}: {e}")
            raise RepositoryError(f"Delete failed: {e}")

    # =========================================================================
    # DOCUMENT OPERATIONS
    # =========================================================================

    def create_document(self, doc: Document) -> str:
        """Create a new document record"""
        self._execute_insert('documents', self.DOCUMENT_COLUMNS, doc.to_dict())
        logger.info(f"Created document: {doc.document_id}")
        return doc.document_id

    def get_document(self, document_id: str) -> Optional[Document]:
        """Get document by ID"""
        try:
            conn = self.db.connect()
            row = conn.execute(
                "SELECT * FROM documents WHERE document_id = ?",
                (document_id,)
            ).fetchone()
            return Document.from_row(row) if row else None
        except sqlite3.DatabaseError as e:
            logger.error(f"Error fetching document {document_id}: {e}")
            raise RepositoryError(f"Failed to fetch document: {e}")

    def update_document(self, document_id: str, updates: Dict[str, Any]) -> bool:
        """Update document fields"""
        return self._execute_update('documents', 'document_id', document_id, updates)

    def delete_document(self, document_id: str) -> bool:
        """Delete a document"""
        return self._execute_delete('documents', 'document_id', document_id)

    def get_documents_by_type(self, doc_type: str) -> List[Document]:
        """Get all documents of a specific type"""
        try:
            conn = self.db.connect()
            rows = conn.execute(
                "SELECT * FROM documents WHERE document_type = ? ORDER BY ingested_date DESC",
                (doc_type,)
            ).fetchall()
            return [Document.from_row(r) for r in rows]
        except sqlite3.DatabaseError as e:
            logger.error(f"Error fetching documents by type {doc_type}: {e}")
            raise RepositoryError(f"Failed to fetch documents: {e}")

    def get_all_documents(self) -> List[Document]:
        """Get all documents"""
        try:
            conn = self.db.connect()
            rows = conn.execute(
                "SELECT * FROM documents ORDER BY ingested_date DESC"
            ).fetchall()
            return [Document.from_row(r) for r in rows]
        except sqlite3.DatabaseError as e:
            logger.error(f"Error fetching all documents: {e}")
            raise RepositoryError(f"Failed to fetch documents: {e}")

    # =========================================================================
    # ANALYSIS RUN OPERATIONS
    # =========================================================================

    def create_run(self, run: AnalysisRun) -> str:
        """Create a new analysis run"""
        self._execute_insert('analysis_runs', self.RUN_COLUMNS, run.to_dict())
        logger.info(f"Created analysis run: {run.run_id}")
        return run.run_id

    def get_run(self, run_id: str) -> Optional[AnalysisRun]:
        """Get analysis run by ID"""
        try:
            conn = self.db.connect()
            row = conn.execute(
                "SELECT * FROM analysis_runs WHERE run_id = ?",
                (run_id,)
            ).fetchone()
            return AnalysisRun.from_row(row) if row else None
        except sqlite3.DatabaseError as e:
            logger.error(f"Error fetching run {run_id}: {e}")
            raise RepositoryError(f"Failed to fetch run: {e}")

    def get_latest_run(self) -> Optional[AnalysisRun]:
        """Get most recent analysis run"""
        try:
            conn = self.db.connect()
            row = conn.execute(
                "SELECT * FROM analysis_runs ORDER BY started_at DESC LIMIT 1"
            ).fetchone()
            return AnalysisRun.from_row(row) if row else None
        except sqlite3.DatabaseError as e:
            logger.error(f"Error fetching latest run: {e}")
            raise RepositoryError(f"Failed to fetch latest run: {e}")

    def update_run(self, run_id: str, updates: Dict[str, Any]) -> bool:
        """Update run fields"""
        # Serialize JSON fields if present
        for field in ['deal_context', 'documents_analyzed', 'summary']:
            if field in updates and not isinstance(updates[field], str):
                updates[field] = json.dumps(updates[field])
        return self._execute_update('analysis_runs', 'run_id', run_id, updates)

    def complete_run(self, run_id: str, summary: Dict = None):
        """Mark a run as completed"""
        updates = {
            'status': 'completed',
            'completed_at': now_iso(),
            'summary': json.dumps(summary or {})
        }
        self._execute_update('analysis_runs', 'run_id', run_id, updates)
        logger.info(f"Completed run: {run_id}")

    def delete_run(self, run_id: str) -> bool:
        """Delete an analysis run and all its findings"""
        try:
            with self.db.transaction() as conn:
                # Delete all related findings first
                for table in ['inventory_items', 'risks', 'gaps', 'assumptions',
                              'work_items', 'recommendations', 'strategic_considerations',
                              'questions', 'reasoning_chains']:
                    conn.execute(f"DELETE FROM {table} WHERE run_id = ?", (run_id,))
                # Delete the run
                conn.execute("DELETE FROM analysis_runs WHERE run_id = ?", (run_id,))
            logger.info(f"Deleted run and all findings: {run_id}")
            return True
        except sqlite3.DatabaseError as e:
            logger.error(f"Error deleting run {run_id}: {e}")
            raise RepositoryError(f"Failed to delete run: {e}")

    def get_all_runs(self) -> List[AnalysisRun]:
        """Get all analysis runs"""
        try:
            conn = self.db.connect()
            rows = conn.execute(
                "SELECT * FROM analysis_runs ORDER BY started_at DESC"
            ).fetchall()
            return [AnalysisRun.from_row(r) for r in rows]
        except sqlite3.DatabaseError as e:
            logger.error(f"Error fetching all runs: {e}")
            raise RepositoryError(f"Failed to fetch runs: {e}")

    # =========================================================================
    # SESSION MANAGEMENT (Points 90-92 of 115PP)
    # =========================================================================

    def name_session(self, run_id: str, name: str, tags: List[str] = None) -> bool:
        """
        Point 90: Name/tag an analysis session for easy identification.

        Args:
            run_id: The run to name
            name: Human-readable name for the session
            tags: Optional list of tags for categorization

        Returns:
            True if updated successfully
        """
        updates = {'run_name': name}

        # Store tags in deal_context if provided
        if tags:
            run = self.get_run(run_id)
            if run:
                deal_context = run.deal_context if hasattr(run, 'deal_context') else run.get('deal_context', {})
                if isinstance(deal_context, str):
                    deal_context = json.loads(deal_context)
                deal_context['_tags'] = tags
                updates['deal_context'] = json.dumps(deal_context)

        return self._execute_update('analysis_runs', 'run_id', run_id, updates)

    def get_runs_by_tag(self, tag: str) -> List[AnalysisRun]:
        """Get all runs with a specific tag"""
        all_runs = self.get_all_runs()
        tagged_runs = []

        for run in all_runs:
            deal_context = run.deal_context if hasattr(run, 'deal_context') else run.get('deal_context', {})
            if isinstance(deal_context, str):
                deal_context = json.loads(deal_context)
            tags = deal_context.get('_tags', [])
            if tag in tags:
                tagged_runs.append(run)

        return tagged_runs

    def compare_sessions(self, run_id_1: str, run_id_2: str) -> Dict[str, Any]:
        """
        Point 91: Compare two analysis sessions.

        Returns a detailed comparison of findings between runs.
        """
        findings_1 = self.get_all_findings_for_run(run_id_1)
        findings_2 = self.get_all_findings_for_run(run_id_2)

        comparison = {
            'run_1': run_id_1,
            'run_2': run_id_2,
            'counts': {},
            'changes': {}
        }

        # Compare counts
        for finding_type in ['risks', 'gaps', 'assumptions', 'work_items',
                             'recommendations', 'strategic_considerations', 'inventory_items']:
            count_1 = len(findings_1.get(finding_type, []))
            count_2 = len(findings_2.get(finding_type, []))
            comparison['counts'][finding_type] = {
                'run_1': count_1,
                'run_2': count_2,
                'delta': count_2 - count_1
            }

        # Detailed risk comparison
        risks_1_ids = {self._get_risk_key(r) for r in findings_1.get('risks', [])}
        risks_2_ids = {self._get_risk_key(r) for r in findings_2.get('risks', [])}

        comparison['changes']['risks'] = {
            'only_in_run_1': list(risks_1_ids - risks_2_ids)[:10],
            'only_in_run_2': list(risks_2_ids - risks_1_ids)[:10],
            'in_both': len(risks_1_ids & risks_2_ids)
        }

        # Compare severities for matching risks
        severity_changes = []
        risks_1_map = {self._get_risk_key(r): r for r in findings_1.get('risks', [])}
        risks_2_map = {self._get_risk_key(r): r for r in findings_2.get('risks', [])}

        for key in risks_1_ids & risks_2_ids:
            r1 = risks_1_map.get(key, {})
            r2 = risks_2_map.get(key, {})
            sev1 = self._get_field(r1, 'severity')
            sev2 = self._get_field(r2, 'severity')
            if sev1 != sev2:
                severity_changes.append({
                    'risk': key[:50],
                    'run_1_severity': sev1,
                    'run_2_severity': sev2
                })

        comparison['changes']['severity_changes'] = severity_changes[:10]

        # Gap resolution check
        gaps_1_ids = {self._get_gap_key(g) for g in findings_1.get('gaps', [])}
        gaps_2_ids = {self._get_gap_key(g) for g in findings_2.get('gaps', [])}

        comparison['changes']['gaps'] = {
            'resolved': list(gaps_1_ids - gaps_2_ids)[:10],
            'new': list(gaps_2_ids - gaps_1_ids)[:10],
            'persistent': len(gaps_1_ids & gaps_2_ids)
        }

        # Summary
        comparison['summary'] = {
            'net_risk_change': comparison['counts']['risks']['delta'],
            'net_gap_change': comparison['counts']['gaps']['delta'],
            'gaps_resolved': len(gaps_1_ids - gaps_2_ids),
            'new_gaps_identified': len(gaps_2_ids - gaps_1_ids),
            'severity_escalations': sum(1 for c in severity_changes
                                       if self._severity_value(c['run_2_severity']) > self._severity_value(c['run_1_severity'])),
            'severity_de_escalations': sum(1 for c in severity_changes
                                          if self._severity_value(c['run_2_severity']) < self._severity_value(c['run_1_severity']))
        }

        return comparison

    def _get_risk_key(self, risk) -> str:
        """Get a stable key for a risk for comparison purposes"""
        desc = self._get_field(risk, 'risk_description') or self._get_field(risk, 'risk') or ''
        domain = self._get_field(risk, 'domain') or ''
        return f"{domain}:{desc[:100]}"

    def _get_gap_key(self, gap) -> str:
        """Get a stable key for a gap for comparison purposes"""
        desc = self._get_field(gap, 'gap_description') or self._get_field(gap, 'gap') or ''
        domain = self._get_field(gap, 'domain') or ''
        return f"{domain}:{desc[:100]}"

    def _severity_value(self, severity: str) -> int:
        """Convert severity to numeric value for comparison"""
        return {'low': 1, 'medium': 2, 'high': 3, 'critical': 4}.get(severity or 'low', 0)

    def branch_from_session(self, source_run_id: str, new_name: str = None) -> str:
        """
        Point 92: Create a new session by branching from a previous one.

        Copies all findings from the source run to a new run for iterative refinement.

        Args:
            source_run_id: The run to branch from
            new_name: Optional name for the new run

        Returns:
            run_id of the new branched run
        """
        # Get source run
        source_run = self.get_run(source_run_id)
        if not source_run:
            raise EntityNotFoundError(f"Source run {source_run_id} not found")

        # Create new run
        deal_context = source_run.deal_context if hasattr(source_run, 'deal_context') else source_run.get('deal_context', {})
        if isinstance(deal_context, str):
            deal_context = json.loads(deal_context)

        # Mark as branched
        deal_context['_branched_from'] = source_run_id
        deal_context['_branch_date'] = now_iso()

        new_run = AnalysisRun(
            run_id=generate_id('RUN'),
            run_name=new_name or f"Branch of {source_run_id}",
            mode='incremental',
            deal_context=deal_context,
            documents_analyzed=source_run.documents_analyzed if hasattr(source_run, 'documents_analyzed') else []
        )

        self.create_run(new_run)
        new_run_id = new_run.run_id

        # Copy all findings to new run
        source_findings = self.get_all_findings_for_run(source_run_id)

        copied_counts = {
            'inventory_items': 0, 'risks': 0, 'gaps': 0, 'assumptions': 0,
            'work_items': 0, 'recommendations': 0, 'strategic_considerations': 0
        }

        # Copy inventory items
        for item in source_findings.get('inventory_items', []):
            try:
                new_item = self._copy_finding_to_new_run(item, new_run_id, 'inventory')
                self.create_inventory_item(new_item)
                copied_counts['inventory_items'] += 1
            except Exception as e:
                logger.warning(f"Failed to copy inventory item: {e}")

        # Copy risks
        for item in source_findings.get('risks', []):
            try:
                new_item = self._copy_finding_to_new_run(item, new_run_id, 'risk')
                self.create_risk(new_item)
                copied_counts['risks'] += 1
            except Exception as e:
                logger.warning(f"Failed to copy risk: {e}")

        # Copy gaps
        for item in source_findings.get('gaps', []):
            try:
                new_item = self._copy_finding_to_new_run(item, new_run_id, 'gap')
                self.create_gap(new_item)
                copied_counts['gaps'] += 1
            except Exception as e:
                logger.warning(f"Failed to copy gap: {e}")

        # Copy assumptions
        for item in source_findings.get('assumptions', []):
            try:
                new_item = self._copy_finding_to_new_run(item, new_run_id, 'assumption')
                self.create_assumption(new_item)
                copied_counts['assumptions'] += 1
            except Exception as e:
                logger.warning(f"Failed to copy assumption: {e}")

        # Copy work items
        for item in source_findings.get('work_items', []):
            try:
                new_item = self._copy_finding_to_new_run(item, new_run_id, 'work_item')
                self.create_work_item(new_item)
                copied_counts['work_items'] += 1
            except Exception as e:
                logger.warning(f"Failed to copy work item: {e}")

        # Copy recommendations
        for item in source_findings.get('recommendations', []):
            try:
                new_item = self._copy_finding_to_new_run(item, new_run_id, 'recommendation')
                self.create_recommendation(new_item)
                copied_counts['recommendations'] += 1
            except Exception as e:
                logger.warning(f"Failed to copy recommendation: {e}")

        # Copy strategic considerations
        for item in source_findings.get('strategic_considerations', []):
            try:
                new_item = self._copy_finding_to_new_run(item, new_run_id, 'strategic')
                self.create_strategic_consideration(new_item)
                copied_counts['strategic_considerations'] += 1
            except Exception as e:
                logger.warning(f"Failed to copy strategic consideration: {e}")

        logger.info(f"Branched run {source_run_id} -> {new_run_id}: {copied_counts}")
        return new_run_id

    def _copy_finding_to_new_run(self, finding, new_run_id: str, finding_type: str):
        """Create a copy of a finding with new run ID and new finding ID"""
        # Convert to dict if needed
        if hasattr(finding, 'to_dict'):
            data = finding.to_dict()
        elif hasattr(finding, '__dict__'):
            data = finding.__dict__.copy()
        else:
            data = dict(finding)

        # Update run ID
        data['run_id'] = new_run_id

        # Generate new ID based on type
        id_field_map = {
            'inventory': ('item_id', 'INV'),
            'risk': ('risk_id', 'R'),
            'gap': ('gap_id', 'G'),
            'assumption': ('assumption_id', 'A'),
            'work_item': ('work_item_id', 'WI'),
            'recommendation': ('recommendation_id', 'REC'),
            'strategic': ('consideration_id', 'SC')
        }

        id_field, prefix = id_field_map.get(finding_type, ('id', 'F'))
        data[id_field] = generate_id(prefix)

        # Update timestamps
        data['created_at'] = now_iso()
        data['updated_at'] = now_iso()

        # Mark as copied
        if 'notes' in data:
            data['notes'] = f"{data.get('notes', '')} [Copied from previous run]"

        # Create appropriate model object
        model_map = {
            'inventory': InventoryItem,
            'risk': Risk,
            'gap': Gap,
            'assumption': Assumption,
            'work_item': WorkItem,
            'recommendation': Recommendation,
            'strategic': StrategicConsideration
        }

        model_class = model_map.get(finding_type)
        if model_class:
            return model_class.from_row(data)
        return data

    def get_session_lineage(self, run_id: str) -> List[Dict]:
        """Get the lineage (parent chain) of a branched session"""
        lineage = []
        current_id = run_id

        while current_id:
            run = self.get_run(current_id)
            if not run:
                break

            run_dict = run.to_dict() if hasattr(run, 'to_dict') else dict(run)
            lineage.append({
                'run_id': current_id,
                'run_name': run_dict.get('run_name'),
                'started_at': run_dict.get('started_at'),
                'mode': run_dict.get('mode')
            })

            # Get parent run ID
            deal_context = run_dict.get('deal_context', {})
            if isinstance(deal_context, str):
                deal_context = json.loads(deal_context)
            current_id = deal_context.get('_branched_from')

        return lineage

    # =========================================================================
    # INVENTORY ITEM OPERATIONS
    # =========================================================================

    def create_inventory_item(self, item: InventoryItem, replace_on_conflict: bool = False) -> str:
        """Create a new inventory item"""
        self._execute_insert('inventory_items', self.INVENTORY_COLUMNS, item.to_dict(), replace_on_conflict)
        logger.debug(f"Created inventory item: {item.item_id}")
        return item.item_id

    def get_inventory_item(self, item_id: str) -> Optional[InventoryItem]:
        """Get inventory item by ID"""
        try:
            conn = self.db.connect()
            row = conn.execute(
                "SELECT * FROM inventory_items WHERE item_id = ?",
                (item_id,)
            ).fetchone()
            return InventoryItem.from_row(row) if row else None
        except sqlite3.DatabaseError as e:
            logger.error(f"Error fetching inventory item {item_id}: {e}")
            raise RepositoryError(f"Failed to fetch inventory item: {e}")

    def update_inventory_item(self, item_id: str, updates: Dict[str, Any]) -> bool:
        """Update inventory item fields"""
        return self._execute_update('inventory_items', 'item_id', item_id, updates)

    def delete_inventory_item(self, item_id: str) -> bool:
        """Delete an inventory item"""
        return self._execute_delete('inventory_items', 'item_id', item_id)

    def get_inventory_by_domain(self, run_id: str, domain: str) -> List[InventoryItem]:
        """Get inventory items for a domain"""
        try:
            conn = self.db.connect()
            rows = conn.execute(
                "SELECT * FROM inventory_items WHERE run_id = ? AND domain = ?",
                (run_id, domain)
            ).fetchall()
            return [InventoryItem.from_row(r) for r in rows]
        except sqlite3.DatabaseError as e:
            logger.error(f"Error fetching inventory for domain {domain}: {e}")
            raise RepositoryError(f"Failed to fetch inventory: {e}")

    def get_inventory_by_category(self, run_id: str, domain: str, category: str) -> List[InventoryItem]:
        """Get inventory items for a specific category"""
        try:
            conn = self.db.connect()
            rows = conn.execute(
                "SELECT * FROM inventory_items WHERE run_id = ? AND domain = ? AND category = ?",
                (run_id, domain, category)
            ).fetchall()
            return [InventoryItem.from_row(r) for r in rows]
        except sqlite3.DatabaseError as e:
            logger.error(f"Error fetching inventory for category {category}: {e}")
            raise RepositoryError(f"Failed to fetch inventory: {e}")

    def get_all_inventory_items(self, run_id: str) -> List[InventoryItem]:
        """Get all inventory items for a run"""
        try:
            conn = self.db.connect()
            rows = conn.execute(
                "SELECT * FROM inventory_items WHERE run_id = ? ORDER BY domain, category",
                (run_id,)
            ).fetchall()
            return [InventoryItem.from_row(r) for r in rows]
        except sqlite3.DatabaseError as e:
            logger.error(f"Error fetching all inventory items: {e}")
            raise RepositoryError(f"Failed to fetch inventory items: {e}")

    # =========================================================================
    # RISK OPERATIONS
    # =========================================================================

    def create_risk(self, risk: Risk, replace_on_conflict: bool = False) -> str:
        """Create a new risk"""
        self._execute_insert('risks', self.RISK_COLUMNS, risk.to_dict(), replace_on_conflict)
        logger.debug(f"Created risk: {risk.risk_id}")
        return risk.risk_id

    def get_risk(self, risk_id: str) -> Optional[Risk]:
        """Get risk by ID"""
        try:
            conn = self.db.connect()
            row = conn.execute(
                "SELECT * FROM risks WHERE risk_id = ?",
                (risk_id,)
            ).fetchone()
            return Risk.from_row(row) if row else None
        except sqlite3.DatabaseError as e:
            logger.error(f"Error fetching risk {risk_id}: {e}")
            raise RepositoryError(f"Failed to fetch risk: {e}")

    def update_risk(self, risk_id: str, updates: Dict[str, Any]) -> bool:
        """Update risk fields"""
        # Handle JSON fields
        if 'deal_impact' in updates and not isinstance(updates['deal_impact'], str):
            updates['deal_impact'] = json.dumps(updates['deal_impact'])
        if 'source_evidence' in updates and not isinstance(updates['source_evidence'], str):
            updates['source_evidence'] = json.dumps(updates['source_evidence'])
        return self._execute_update('risks', 'risk_id', risk_id, updates)

    def delete_risk(self, risk_id: str) -> bool:
        """Delete a risk"""
        return self._execute_delete('risks', 'risk_id', risk_id)

    def get_risks_by_domain(self, run_id: str, domain: str) -> List[Risk]:
        """Get risks for a domain"""
        try:
            conn = self.db.connect()
            rows = conn.execute(
                "SELECT * FROM risks WHERE run_id = ? AND domain = ? ORDER BY risk_score DESC",
                (run_id, domain)
            ).fetchall()
            return [Risk.from_row(r) for r in rows]
        except sqlite3.DatabaseError as e:
            logger.error(f"Error fetching risks for domain {domain}: {e}")
            raise RepositoryError(f"Failed to fetch risks: {e}")

    def get_risks_by_severity(self, run_id: str, severity: str) -> List[Risk]:
        """Get risks by severity level"""
        try:
            conn = self.db.connect()
            rows = conn.execute(
                "SELECT * FROM risks WHERE run_id = ? AND severity = ?",
                (run_id, severity)
            ).fetchall()
            return [Risk.from_row(r) for r in rows]
        except sqlite3.DatabaseError as e:
            logger.error(f"Error fetching risks by severity {severity}: {e}")
            raise RepositoryError(f"Failed to fetch risks: {e}")

    def get_standalone_risks(self, run_id: str) -> List[Risk]:
        """Get risks that exist independent of integration"""
        try:
            conn = self.db.connect()
            rows = conn.execute(
                "SELECT * FROM risks WHERE run_id = ? AND integration_dependent = 0",
                (run_id,)
            ).fetchall()
            return [Risk.from_row(r) for r in rows]
        except sqlite3.DatabaseError as e:
            logger.error(f"Error fetching standalone risks: {e}")
            raise RepositoryError(f"Failed to fetch risks: {e}")

    def get_all_risks(self, run_id: str) -> List[Risk]:
        """Get all risks for a run"""
        try:
            conn = self.db.connect()
            rows = conn.execute(
                "SELECT * FROM risks WHERE run_id = ? ORDER BY risk_score DESC",
                (run_id,)
            ).fetchall()
            return [Risk.from_row(r) for r in rows]
        except sqlite3.DatabaseError as e:
            logger.error(f"Error fetching all risks: {e}")
            raise RepositoryError(f"Failed to fetch risks: {e}")

    # =========================================================================
    # GAP OPERATIONS
    # =========================================================================

    def create_gap(self, gap: Gap, replace_on_conflict: bool = False) -> str:
        """Create a new gap"""
        self._execute_insert('gaps', self.GAP_COLUMNS, gap.to_dict(), replace_on_conflict)
        logger.debug(f"Created gap: {gap.gap_id}")
        return gap.gap_id

    def get_gap(self, gap_id: str) -> Optional[Gap]:
        """Get gap by ID"""
        try:
            conn = self.db.connect()
            row = conn.execute(
                "SELECT * FROM gaps WHERE gap_id = ?",
                (gap_id,)
            ).fetchone()
            return Gap.from_row(row) if row else None
        except sqlite3.DatabaseError as e:
            logger.error(f"Error fetching gap {gap_id}: {e}")
            raise RepositoryError(f"Failed to fetch gap: {e}")

    def update_gap(self, gap_id: str, updates: Dict[str, Any]) -> bool:
        """Update gap fields"""
        return self._execute_update('gaps', 'gap_id', gap_id, updates)

    def delete_gap(self, gap_id: str) -> bool:
        """Delete a gap"""
        return self._execute_delete('gaps', 'gap_id', gap_id)

    def get_gaps_by_domain(self, run_id: str, domain: str) -> List[Gap]:
        """Get gaps for a domain"""
        try:
            conn = self.db.connect()
            rows = conn.execute(
                "SELECT * FROM gaps WHERE run_id = ? AND domain = ?",
                (run_id, domain)
            ).fetchall()
            return [Gap.from_row(r) for r in rows]
        except sqlite3.DatabaseError as e:
            logger.error(f"Error fetching gaps for domain {domain}: {e}")
            raise RepositoryError(f"Failed to fetch gaps: {e}")

    def get_gaps_by_priority(self, run_id: str, priority: str) -> List[Gap]:
        """Get gaps by priority"""
        try:
            conn = self.db.connect()
            rows = conn.execute(
                "SELECT * FROM gaps WHERE run_id = ? AND priority = ?",
                (run_id, priority)
            ).fetchall()
            return [Gap.from_row(r) for r in rows]
        except sqlite3.DatabaseError as e:
            logger.error(f"Error fetching gaps by priority {priority}: {e}")
            raise RepositoryError(f"Failed to fetch gaps: {e}")

    def get_unanswered_gaps(self, run_id: str) -> List[Gap]:
        """Get gaps that haven't been answered"""
        try:
            conn = self.db.connect()
            rows = conn.execute(
                "SELECT * FROM gaps WHERE run_id = ? AND question_status != 'answered'",
                (run_id,)
            ).fetchall()
            return [Gap.from_row(r) for r in rows]
        except sqlite3.DatabaseError as e:
            logger.error(f"Error fetching unanswered gaps: {e}")
            raise RepositoryError(f"Failed to fetch gaps: {e}")

    def update_gap_status(self, gap_id: str, status: str) -> bool:
        """Update gap question status"""
        return self.update_gap(gap_id, {'question_status': status})

    def get_all_gaps(self, run_id: str) -> List[Gap]:
        """Get all gaps for a run (including answered ones)"""
        try:
            conn = self.db.connect()
            rows = conn.execute(
                "SELECT * FROM gaps WHERE run_id = ? ORDER BY priority",
                (run_id,)
            ).fetchall()
            return [Gap.from_row(r) for r in rows]
        except sqlite3.DatabaseError as e:
            logger.error(f"Error fetching all gaps: {e}")
            raise RepositoryError(f"Failed to fetch gaps: {e}")

    # =========================================================================
    # ASSUMPTION OPERATIONS
    # =========================================================================

    def create_assumption(self, assumption: Assumption, replace_on_conflict: bool = False) -> str:
        """Create a new assumption"""
        self._execute_insert('assumptions', self.ASSUMPTION_COLUMNS, assumption.to_dict(), replace_on_conflict)
        logger.debug(f"Created assumption: {assumption.assumption_id}")
        return assumption.assumption_id

    def get_assumption(self, assumption_id: str) -> Optional[Assumption]:
        """Get assumption by ID"""
        try:
            conn = self.db.connect()
            row = conn.execute(
                "SELECT * FROM assumptions WHERE assumption_id = ?",
                (assumption_id,)
            ).fetchone()
            return Assumption.from_row(row) if row else None
        except sqlite3.DatabaseError as e:
            logger.error(f"Error fetching assumption {assumption_id}: {e}")
            raise RepositoryError(f"Failed to fetch assumption: {e}")

    def update_assumption(self, assumption_id: str, updates: Dict[str, Any]) -> bool:
        """Update assumption fields"""
        return self._execute_update('assumptions', 'assumption_id', assumption_id, updates)

    def delete_assumption(self, assumption_id: str) -> bool:
        """Delete an assumption"""
        return self._execute_delete('assumptions', 'assumption_id', assumption_id)

    def get_assumptions_by_domain(self, run_id: str, domain: str) -> List[Assumption]:
        """Get assumptions for a domain"""
        try:
            conn = self.db.connect()
            rows = conn.execute(
                "SELECT * FROM assumptions WHERE run_id = ? AND domain = ?",
                (run_id, domain)
            ).fetchall()
            return [Assumption.from_row(r) for r in rows]
        except sqlite3.DatabaseError as e:
            logger.error(f"Error fetching assumptions for domain {domain}: {e}")
            raise RepositoryError(f"Failed to fetch assumptions: {e}")

    def get_unvalidated_assumptions(self, run_id: str) -> List[Assumption]:
        """Get assumptions needing validation"""
        try:
            conn = self.db.connect()
            rows = conn.execute(
                "SELECT * FROM assumptions WHERE run_id = ? AND validation_status = 'unvalidated'",
                (run_id,)
            ).fetchall()
            return [Assumption.from_row(r) for r in rows]
        except sqlite3.DatabaseError as e:
            logger.error(f"Error fetching unvalidated assumptions: {e}")
            raise RepositoryError(f"Failed to fetch assumptions: {e}")

    def validate_assumption(self, assumption_id: str, status: str, notes: str = None) -> bool:
        """Mark assumption as validated/invalidated"""
        updates = {'validation_status': status}
        if notes:
            updates['basis'] = notes
        return self.update_assumption(assumption_id, updates)

    def get_all_assumptions(self, run_id: str) -> List[Assumption]:
        """Get all assumptions for a run (including validated ones)"""
        try:
            conn = self.db.connect()
            rows = conn.execute(
                "SELECT * FROM assumptions WHERE run_id = ? ORDER BY domain, confidence",
                (run_id,)
            ).fetchall()
            return [Assumption.from_row(r) for r in rows]
        except sqlite3.DatabaseError as e:
            logger.error(f"Error fetching all assumptions: {e}")
            raise RepositoryError(f"Failed to fetch assumptions: {e}")

    # =========================================================================
    # WORK ITEM OPERATIONS
    # =========================================================================

    def create_work_item(self, item: WorkItem, replace_on_conflict: bool = False) -> str:
        """Create a new work item"""
        self._execute_insert('work_items', self.WORK_ITEM_COLUMNS, item.to_dict(), replace_on_conflict)
        logger.debug(f"Created work item: {item.work_item_id}")
        return item.work_item_id

    def get_work_item(self, work_item_id: str) -> Optional[WorkItem]:
        """Get work item by ID"""
        try:
            conn = self.db.connect()
            row = conn.execute(
                "SELECT * FROM work_items WHERE work_item_id = ?",
                (work_item_id,)
            ).fetchone()
            return WorkItem.from_row(row) if row else None
        except sqlite3.DatabaseError as e:
            logger.error(f"Error fetching work item {work_item_id}: {e}")
            raise RepositoryError(f"Failed to fetch work item: {e}")

    def update_work_item(self, work_item_id: str, updates: Dict[str, Any]) -> bool:
        """Update work item fields"""
        # Handle JSON fields
        for field in ['depends_on', 'skills_required', 'triggered_by']:
            if field in updates and not isinstance(updates[field], str):
                updates[field] = json.dumps(updates[field])
        return self._execute_update('work_items', 'work_item_id', work_item_id, updates)

    def delete_work_item(self, work_item_id: str) -> bool:
        """Delete a work item"""
        return self._execute_delete('work_items', 'work_item_id', work_item_id)

    def get_work_items_by_domain(self, run_id: str, domain: str) -> List[WorkItem]:
        """Get work items for a domain"""
        try:
            conn = self.db.connect()
            rows = conn.execute(
                "SELECT * FROM work_items WHERE run_id = ? AND domain = ?",
                (run_id, domain)
            ).fetchall()
            return [WorkItem.from_row(r) for r in rows]
        except sqlite3.DatabaseError as e:
            logger.error(f"Error fetching work items for domain {domain}: {e}")
            raise RepositoryError(f"Failed to fetch work items: {e}")

    def get_work_items_by_phase(self, run_id: str, phase: str) -> List[WorkItem]:
        """Get work items for a phase"""
        try:
            conn = self.db.connect()
            rows = conn.execute(
                "SELECT * FROM work_items WHERE run_id = ? AND phase = ?",
                (run_id, phase)
            ).fetchall()
            return [WorkItem.from_row(r) for r in rows]
        except sqlite3.DatabaseError as e:
            logger.error(f"Error fetching work items for phase {phase}: {e}")
            raise RepositoryError(f"Failed to fetch work items: {e}")

    def get_all_work_items(self, run_id: str) -> List[WorkItem]:
        """Get all work items for a run"""
        try:
            conn = self.db.connect()
            rows = conn.execute(
                "SELECT * FROM work_items WHERE run_id = ? ORDER BY phase, priority_score DESC",
                (run_id,)
            ).fetchall()
            return [WorkItem.from_row(r) for r in rows]
        except sqlite3.DatabaseError as e:
            logger.error(f"Error fetching all work items: {e}")
            raise RepositoryError(f"Failed to fetch work items: {e}")

    # =========================================================================
    # RECOMMENDATION OPERATIONS
    # =========================================================================

    def create_recommendation(self, rec: Recommendation, replace_on_conflict: bool = False) -> str:
        """Create a new recommendation"""
        self._execute_insert('recommendations', self.RECOMMENDATION_COLUMNS, rec.to_dict(), replace_on_conflict)
        logger.debug(f"Created recommendation: {rec.recommendation_id}")
        return rec.recommendation_id

    def get_recommendation(self, recommendation_id: str) -> Optional[Recommendation]:
        """Get recommendation by ID"""
        try:
            conn = self.db.connect()
            row = conn.execute(
                "SELECT * FROM recommendations WHERE recommendation_id = ?",
                (recommendation_id,)
            ).fetchone()
            return Recommendation.from_row(row) if row else None
        except sqlite3.DatabaseError as e:
            logger.error(f"Error fetching recommendation {recommendation_id}: {e}")
            raise RepositoryError(f"Failed to fetch recommendation: {e}")

    def update_recommendation(self, recommendation_id: str, updates: Dict[str, Any]) -> bool:
        """Update recommendation fields"""
        if 'driven_by' in updates and not isinstance(updates['driven_by'], str):
            updates['driven_by'] = json.dumps(updates['driven_by'])
        return self._execute_update('recommendations', 'recommendation_id', recommendation_id, updates)

    def delete_recommendation(self, recommendation_id: str) -> bool:
        """Delete a recommendation"""
        return self._execute_delete('recommendations', 'recommendation_id', recommendation_id)

    def get_recommendations_by_domain(self, run_id: str, domain: str) -> List[Recommendation]:
        """Get recommendations for a domain"""
        try:
            conn = self.db.connect()
            rows = conn.execute(
                "SELECT * FROM recommendations WHERE run_id = ? AND domain = ?",
                (run_id, domain)
            ).fetchall()
            return [Recommendation.from_row(r) for r in rows]
        except sqlite3.DatabaseError as e:
            logger.error(f"Error fetching recommendations for domain {domain}: {e}")
            raise RepositoryError(f"Failed to fetch recommendations: {e}")

    def get_all_recommendations(self, run_id: str) -> List[Recommendation]:
        """Get all recommendations for a run"""
        try:
            conn = self.db.connect()
            rows = conn.execute(
                "SELECT * FROM recommendations WHERE run_id = ? ORDER BY priority",
                (run_id,)
            ).fetchall()
            return [Recommendation.from_row(r) for r in rows]
        except sqlite3.DatabaseError as e:
            logger.error(f"Error fetching all recommendations: {e}")
            raise RepositoryError(f"Failed to fetch recommendations: {e}")

    # =========================================================================
    # STRATEGIC CONSIDERATION OPERATIONS
    # =========================================================================

    def create_strategic_consideration(self, sc: StrategicConsideration, replace_on_conflict: bool = False) -> str:
        """Create a new strategic consideration"""
        self._execute_insert('strategic_considerations', self.STRATEGIC_CONSIDERATION_COLUMNS, sc.to_dict(), replace_on_conflict)
        logger.debug(f"Created strategic consideration: {sc.consideration_id}")
        return sc.consideration_id

    def get_strategic_consideration(self, consideration_id: str) -> Optional[StrategicConsideration]:
        """Get strategic consideration by ID"""
        try:
            conn = self.db.connect()
            row = conn.execute(
                "SELECT * FROM strategic_considerations WHERE consideration_id = ?",
                (consideration_id,)
            ).fetchone()
            return StrategicConsideration.from_row(row) if row else None
        except sqlite3.DatabaseError as e:
            logger.error(f"Error fetching strategic consideration {consideration_id}: {e}")
            raise RepositoryError(f"Failed to fetch strategic consideration: {e}")

    def update_strategic_consideration(self, consideration_id: str, updates: Dict[str, Any]) -> bool:
        """Update strategic consideration fields"""
        for field in ['deal_relevance', 'source_evidence']:
            if field in updates and not isinstance(updates[field], str):
                updates[field] = json.dumps(updates[field])
        return self._execute_update('strategic_considerations', 'consideration_id', consideration_id, updates)

    def delete_strategic_consideration(self, consideration_id: str) -> bool:
        """Delete a strategic consideration"""
        return self._execute_delete('strategic_considerations', 'consideration_id', consideration_id)

    def get_strategic_considerations_by_domain(self, run_id: str, domain: str) -> List[StrategicConsideration]:
        """Get strategic considerations for a domain"""
        try:
            conn = self.db.connect()
            rows = conn.execute(
                "SELECT * FROM strategic_considerations WHERE run_id = ? AND domain = ?",
                (run_id, domain)
            ).fetchall()
            return [StrategicConsideration.from_row(r) for r in rows]
        except sqlite3.DatabaseError as e:
            logger.error(f"Error fetching strategic considerations for domain {domain}: {e}")
            raise RepositoryError(f"Failed to fetch strategic considerations: {e}")

    def get_all_strategic_considerations(self, run_id: str) -> List[StrategicConsideration]:
        """Get all strategic considerations for a run"""
        try:
            conn = self.db.connect()
            rows = conn.execute(
                "SELECT * FROM strategic_considerations WHERE run_id = ? ORDER BY domain, theme",
                (run_id,)
            ).fetchall()
            return [StrategicConsideration.from_row(r) for r in rows]
        except sqlite3.DatabaseError as e:
            logger.error(f"Error fetching all strategic considerations: {e}")
            raise RepositoryError(f"Failed to fetch strategic considerations: {e}")

    # =========================================================================
    # QUESTION OPERATIONS
    # =========================================================================

    def create_question(self, question: Question) -> str:
        """Create a new question"""
        self._execute_insert('questions', self.QUESTION_COLUMNS, question.to_dict())
        logger.debug(f"Created question: {question.question_id}")
        return question.question_id

    def get_question(self, question_id: str) -> Optional[Question]:
        """Get question by ID"""
        try:
            conn = self.db.connect()
            row = conn.execute(
                "SELECT * FROM questions WHERE question_id = ?",
                (question_id,)
            ).fetchone()
            return Question.from_row(row) if row else None
        except sqlite3.DatabaseError as e:
            logger.error(f"Error fetching question {question_id}: {e}")
            raise RepositoryError(f"Failed to fetch question: {e}")

    def update_question(self, question_id: str, updates: Dict[str, Any]) -> bool:
        """Update question fields"""
        return self._execute_update('questions', 'question_id', question_id, updates)

    def delete_question(self, question_id: str) -> bool:
        """Delete a question"""
        return self._execute_delete('questions', 'question_id', question_id)

    def get_questions_by_status(self, run_id: str, status: str) -> List[Question]:
        """Get questions by status"""
        try:
            conn = self.db.connect()
            rows = conn.execute(
                "SELECT * FROM questions WHERE run_id = ? AND status = ?",
                (run_id, status)
            ).fetchall()
            return [Question.from_row(r) for r in rows]
        except sqlite3.DatabaseError as e:
            logger.error(f"Error fetching questions by status {status}: {e}")
            raise RepositoryError(f"Failed to fetch questions: {e}")

    def answer_question(self, question_id: str, answer: str, source: str = "email") -> bool:
        """Record an answer to a question"""
        updates = {
            'answer_text': answer,
            'answer_date': now_iso(),
            'answer_source': source,
            'status': 'answered'
        }
        return self.update_question(question_id, updates)

    # =========================================================================
    # QUESTION/GAP TRACKING (Points 80-84 of 115PP)
    # =========================================================================

    def create_question_from_gap(self, run_id: str, gap_id: str,
                                  question_text: str = None) -> str:
        """
        Point 81: Create a question from a gap.

        Links the question to its source gap for tracking.

        Args:
            run_id: Current analysis run
            gap_id: Gap that generated this question
            question_text: Optional custom question text (auto-generated if not provided)

        Returns:
            question_id of created question
        """
        # Get the gap to generate question if not provided
        gap = self.get_gap(gap_id)
        if not gap:
            raise EntityNotFoundError(f"Gap {gap_id} not found")

        if question_text is None:
            # Auto-generate question from gap
            gap_desc = gap.gap_description if hasattr(gap, 'gap_description') else gap.get('gap_description', '')
            why_needed = gap.why_needed if hasattr(gap, 'why_needed') else gap.get('why_needed', '')
            question_text = f"Can you provide information about: {gap_desc}? This is needed because: {why_needed}"

        # Determine priority from gap
        gap_priority = gap.priority if hasattr(gap, 'priority') else gap.get('priority', 'medium')

        question = Question.create(
            run_id=run_id,
            question=question_text,
            gap_id=gap_id,
            priority=gap_priority,
            context=f"Generated from gap {gap_id}"
        )

        self.create_question(question)

        # Update gap to show question was created
        self.update_gap(gap_id, {'question_status': 'question_created'})

        logger.info(f"Created question {question.question_id} from gap {gap_id}")
        return question.question_id

    def create_questions_from_gaps(self, run_id: str, priority_filter: str = None,
                                    domain_filter: str = None) -> List[str]:
        """
        Point 80: Bulk create questions from gaps.

        Args:
            run_id: Analysis run ID
            priority_filter: Only gaps of this priority (critical, high, medium, low)
            domain_filter: Only gaps from this domain

        Returns:
            List of created question IDs
        """
        # Get gaps that don't have questions yet
        gaps = self.get_unanswered_gaps(run_id)

        # Apply filters
        if priority_filter:
            gaps = [g for g in gaps if (g.priority if hasattr(g, 'priority') else g.get('priority')) == priority_filter]
        if domain_filter:
            gaps = [g for g in gaps if (g.domain if hasattr(g, 'domain') else g.get('domain')) == domain_filter]

        created_questions = []
        for gap in gaps:
            gap_id = gap.gap_id if hasattr(gap, 'gap_id') else gap.get('gap_id')
            try:
                q_id = self.create_question_from_gap(run_id, gap_id)
                created_questions.append(q_id)
            except (RepositoryError, Exception) as e:
                logger.warning(f"Failed to create question from gap {gap_id}: {e}")

        logger.info(f"Created {len(created_questions)} questions from gaps")
        return created_questions

    def answer_question_and_update_gap(self, question_id: str, answer: str,
                                        source: str = "email",
                                        close_gap: bool = True) -> Dict[str, Any]:
        """
        Points 83-84: Answer a question and update the related gap.

        Args:
            question_id: Question being answered
            answer: The answer text
            source: Source of answer (email, call, document, etc.)
            close_gap: Whether to mark the linked gap as answered

        Returns:
            Dict with update results
        """
        result = {
            'question_updated': False,
            'gap_updated': False,
            'gap_id': None
        }

        # Get the question to find linked gap
        question = self.get_question(question_id)
        if not question:
            raise EntityNotFoundError(f"Question {question_id} not found")

        # Update the question with the answer
        self.answer_question(question_id, answer, source)
        result['question_updated'] = True

        # Get linked gap ID
        linked_gap_id = question.linked_gap_id if hasattr(question, 'linked_gap_id') else question.get('linked_gap_id')

        if linked_gap_id and close_gap:
            # Update the gap status
            self.update_gap(linked_gap_id, {
                'question_status': 'answered'
            })
            result['gap_updated'] = True
            result['gap_id'] = linked_gap_id
            logger.info(f"Updated gap {linked_gap_id} based on answer to question {question_id}")

        return result

    def get_question_status_summary(self, run_id: str) -> Dict[str, Any]:
        """
        Point 82: Get summary of question statuses for a run.

        Returns:
            Dict with counts by status and lists of question IDs
        """
        try:
            conn = self.db.connect()
            rows = conn.execute(
                """SELECT status, COUNT(*) as count
                   FROM questions WHERE run_id = ?
                   GROUP BY status""",
                (run_id,)
            ).fetchall()

            summary = {
                'draft': 0, 'ready': 0, 'sent': 0, 'answered': 0, 'closed': 0,
                'total': 0,
                'by_priority': {}
            }

            for row in rows:
                summary[row['status']] = row['count']
                summary['total'] += row['count']

            # Get by priority
            priority_rows = conn.execute(
                """SELECT priority, status, COUNT(*) as count
                   FROM questions WHERE run_id = ?
                   GROUP BY priority, status""",
                (run_id,)
            ).fetchall()

            for row in priority_rows:
                priority = row['priority']
                if priority not in summary['by_priority']:
                    summary['by_priority'][priority] = {}
                summary['by_priority'][priority][row['status']] = row['count']

            return summary

        except sqlite3.DatabaseError as e:
            logger.error(f"Error getting question summary: {e}")
            raise RepositoryError(f"Failed to get question summary: {e}")

    def get_questions_for_gap(self, gap_id: str) -> List[Question]:
        """Get all questions linked to a specific gap"""
        try:
            conn = self.db.connect()
            rows = conn.execute(
                "SELECT * FROM questions WHERE linked_gap_id = ?",
                (gap_id,)
            ).fetchall()
            return [Question.from_row(r) for r in rows]
        except sqlite3.DatabaseError as e:
            logger.error(f"Error fetching questions for gap {gap_id}: {e}")
            raise RepositoryError(f"Failed to fetch questions: {e}")

    def mark_question_sent(self, question_id: str) -> bool:
        """Mark a question as sent to seller"""
        return self.update_question(question_id, {
            'status': 'sent',
            'sent_date': now_iso()
        })

    def get_pending_questions(self, run_id: str) -> List[Question]:
        """Get questions that are ready to send but not yet sent"""
        try:
            conn = self.db.connect()
            rows = conn.execute(
                "SELECT * FROM questions WHERE run_id = ? AND status IN ('draft', 'ready') ORDER BY priority",
                (run_id,)
            ).fetchall()
            return [Question.from_row(r) for r in rows]
        except sqlite3.DatabaseError as e:
            logger.error(f"Error fetching pending questions: {e}")
            raise RepositoryError(f"Failed to fetch questions: {e}")

    def get_awaiting_answer_questions(self, run_id: str) -> List[Question]:
        """Get questions that have been sent but not answered"""
        try:
            conn = self.db.connect()
            rows = conn.execute(
                "SELECT * FROM questions WHERE run_id = ? AND status = 'sent' ORDER BY sent_date",
                (run_id,)
            ).fetchall()
            return [Question.from_row(r) for r in rows]
        except sqlite3.DatabaseError as e:
            logger.error(f"Error fetching sent questions: {e}")
            raise RepositoryError(f"Failed to fetch questions: {e}")

    # =========================================================================
    # ASSUMPTION MANAGEMENT (Points 85-89 of 115PP)
    # =========================================================================

    def add_assumption_evidence(self, assumption_id: str, run_id: str,
                                 evidence_text: str, evidence_type: str = 'supporting',
                                 source_document_id: str = None,
                                 source_section: str = None,
                                 confidence_weight: float = 1.0,
                                 notes: str = None) -> int:
        """
        Point 86: Add evidence for or against an assumption.

        Args:
            assumption_id: The assumption to add evidence for
            evidence_text: The evidence text
            evidence_type: 'supporting', 'contradicting', or 'neutral'
            source_document_id: Source document if applicable
            source_section: Section in document
            confidence_weight: How strongly this evidence weighs (0.0-2.0)
            notes: Additional notes

        Returns:
            evidence_id of created record
        """
        try:
            with self.db.transaction() as conn:
                cursor = conn.execute(
                    """INSERT INTO assumption_evidence
                       (assumption_id, run_id, evidence_type, evidence_text,
                        source_document_id, source_section, confidence_weight,
                        notes, created_at, updated_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (assumption_id, run_id, evidence_type, evidence_text,
                     source_document_id, source_section, confidence_weight,
                     notes, now_iso(), now_iso())
                )
                evidence_id = cursor.lastrowid

            # Recalculate assumption confidence after adding evidence
            self._recalculate_assumption_confidence(assumption_id)

            logger.debug(f"Added {evidence_type} evidence for assumption {assumption_id}")
            return evidence_id

        except sqlite3.DatabaseError as e:
            logger.error(f"Error adding assumption evidence: {e}")
            raise RepositoryError(f"Failed to add evidence: {e}")

    def get_evidence_for_assumption(self, assumption_id: str) -> List[Dict]:
        """Get all evidence for an assumption"""
        try:
            conn = self.db.connect()
            rows = conn.execute(
                "SELECT * FROM assumption_evidence WHERE assumption_id = ? ORDER BY created_at",
                (assumption_id,)
            ).fetchall()
            return [dict(r) for r in rows]
        except sqlite3.DatabaseError as e:
            logger.error(f"Error fetching evidence for {assumption_id}: {e}")
            raise RepositoryError(f"Failed to fetch evidence: {e}")

    def _recalculate_assumption_confidence(self, assumption_id: str) -> str:
        """
        Point 87: Calculate assumption confidence based on evidence.

        Confidence calculation:
        - High: Strong supporting evidence, no contradicting
        - Medium: Some supporting evidence, or mixed signals
        - Low: Contradicting evidence or no evidence
        """
        evidence_list = self.get_evidence_for_assumption(assumption_id)

        if not evidence_list:
            # No evidence - keep original confidence
            return 'medium'

        supporting_weight = 0.0
        contradicting_weight = 0.0

        for ev in evidence_list:
            weight = ev.get('confidence_weight', 1.0)
            if ev.get('evidence_type') == 'supporting':
                supporting_weight += weight
            elif ev.get('evidence_type') == 'contradicting':
                contradicting_weight += weight

        # Calculate net confidence
        net_score = supporting_weight - contradicting_weight

        if net_score >= 2.0 and contradicting_weight == 0:
            new_confidence = 'high'
            validation_status = 'validated'
        elif net_score <= -1.0:
            new_confidence = 'low'
            validation_status = 'invalidated'
        elif contradicting_weight > 0:
            new_confidence = 'medium'
            validation_status = 'contested'
        else:
            new_confidence = 'medium'
            validation_status = 'partial_evidence'

        # Update assumption
        self.update_assumption(assumption_id, {
            'confidence': new_confidence,
            'validation_status': validation_status
        })

        logger.debug(f"Recalculated confidence for {assumption_id}: {new_confidence} ({validation_status})")
        return new_confidence

    def get_assumptions_needing_validation(self, run_id: str) -> List[Assumption]:
        """
        Point 88: Get assumptions that need validation.

        Returns assumptions that are:
        - Low confidence
        - High impact
        - No evidence yet
        - Unvalidated status
        """
        try:
            conn = self.db.connect()
            rows = conn.execute(
                """SELECT * FROM assumptions
                   WHERE run_id = ?
                   AND (
                       confidence = 'low'
                       OR (impact = 'high' AND validation_status = 'unvalidated')
                       OR validation_status IN ('unvalidated', 'contested')
                   )
                   ORDER BY
                       CASE impact WHEN 'high' THEN 1 WHEN 'medium' THEN 2 ELSE 3 END,
                       CASE confidence WHEN 'low' THEN 1 WHEN 'medium' THEN 2 ELSE 3 END""",
                (run_id,)
            ).fetchall()
            return [Assumption.from_row(r) for r in rows]
        except sqlite3.DatabaseError as e:
            logger.error(f"Error fetching assumptions needing validation: {e}")
            raise RepositoryError(f"Failed to fetch assumptions: {e}")

    def create_question_from_assumption(self, run_id: str, assumption_id: str,
                                         question_text: str = None) -> str:
        """
        Point 89: Create a question to validate an assumption.

        Args:
            run_id: Current analysis run
            assumption_id: Assumption to validate
            question_text: Optional custom question (auto-generated if not provided)

        Returns:
            question_id of created question
        """
        assumption = self.get_assumption(assumption_id)
        if not assumption:
            raise EntityNotFoundError(f"Assumption {assumption_id} not found")

        if question_text is None:
            # Auto-generate validation question
            assumption_text = assumption.assumption_text if hasattr(assumption, 'assumption_text') else assumption.get('assumption_text', '')
            validation_needed = assumption.validation_needed if hasattr(assumption, 'validation_needed') else assumption.get('validation_needed', '')

            question_text = f"We've assumed: \"{assumption_text}\". Can you confirm this is accurate? {validation_needed}"

        # Determine priority based on impact
        impact = assumption.impact if hasattr(assumption, 'impact') else assumption.get('impact', 'medium')
        priority_map = {'high': 'critical', 'medium': 'high', 'low': 'medium'}
        priority = priority_map.get(impact, 'medium')

        question = Question.create(
            run_id=run_id,
            question=question_text,
            priority=priority,
            context=f"Validation for assumption {assumption_id}"
        )
        question.linked_assumption_id = assumption_id

        self.create_question(question)

        # Update assumption to show validation is pending
        self.update_assumption(assumption_id, {'validation_status': 'validation_pending'})

        logger.info(f"Created validation question {question.question_id} for assumption {assumption_id}")
        return question.question_id

    def get_assumption_validation_summary(self, run_id: str) -> Dict[str, Any]:
        """Get summary of assumption validation status for a run"""
        try:
            conn = self.db.connect()

            # Get counts by validation status
            status_rows = conn.execute(
                """SELECT validation_status, COUNT(*) as count
                   FROM assumptions WHERE run_id = ?
                   GROUP BY validation_status""",
                (run_id,)
            ).fetchall()

            # Get counts by confidence
            conf_rows = conn.execute(
                """SELECT confidence, COUNT(*) as count
                   FROM assumptions WHERE run_id = ?
                   GROUP BY confidence""",
                (run_id,)
            ).fetchall()

            # Get high-impact unvalidated count
            high_impact = conn.execute(
                """SELECT COUNT(*) FROM assumptions
                   WHERE run_id = ? AND impact = 'high'
                   AND validation_status = 'unvalidated'""",
                (run_id,)
            ).fetchone()[0]

            summary = {
                'by_validation_status': {r['validation_status']: r['count'] for r in status_rows},
                'by_confidence': {r['confidence']: r['count'] for r in conf_rows},
                'high_impact_unvalidated': high_impact,
                'total': sum(r['count'] for r in status_rows)
            }

            # Add evidence counts
            ev_rows = conn.execute(
                """SELECT a.assumption_id, COUNT(ae.evidence_id) as evidence_count
                   FROM assumptions a
                   LEFT JOIN assumption_evidence ae ON a.assumption_id = ae.assumption_id
                   WHERE a.run_id = ?
                   GROUP BY a.assumption_id""",
                (run_id,)
            ).fetchall()

            summary['assumptions_with_evidence'] = sum(1 for r in ev_rows if r['evidence_count'] > 0)
            summary['assumptions_without_evidence'] = sum(1 for r in ev_rows if r['evidence_count'] == 0)

            return summary

        except sqlite3.DatabaseError as e:
            logger.error(f"Error getting assumption summary: {e}")
            raise RepositoryError(f"Failed to get assumption summary: {e}")

    def answer_assumption_question(self, question_id: str, answer: str,
                                    validates: bool, source: str = "email") -> Dict[str, Any]:
        """
        Handle answer to an assumption validation question.

        Args:
            question_id: The question being answered
            answer: The answer text
            validates: True if answer validates assumption, False if contradicts
            source: Source of answer

        Returns:
            Dict with update results
        """
        result = {'question_updated': False, 'assumption_updated': False, 'evidence_added': False}

        question = self.get_question(question_id)
        if not question:
            raise EntityNotFoundError(f"Question {question_id} not found")

        # Answer the question
        self.answer_question(question_id, answer, source)
        result['question_updated'] = True

        # Get linked assumption
        linked_assumption_id = question.linked_assumption_id if hasattr(question, 'linked_assumption_id') else question.get('linked_assumption_id')

        if linked_assumption_id:
            # Add evidence based on the answer
            run_id = question.run_id if hasattr(question, 'run_id') else question.get('run_id')
            evidence_type = 'supporting' if validates else 'contradicting'

            self.add_assumption_evidence(
                assumption_id=linked_assumption_id,
                run_id=run_id,
                evidence_text=answer,
                evidence_type=evidence_type,
                confidence_weight=1.5,  # Higher weight for direct seller confirmation
                notes=f"From seller response to question {question_id}"
            )
            result['evidence_added'] = True
            result['assumption_id'] = linked_assumption_id

            # Confidence is recalculated automatically by add_assumption_evidence
            result['assumption_updated'] = True

        return result

    # =========================================================================
    # REASONING CHAIN OPERATIONS
    # =========================================================================

    def create_reasoning_entry(self, run_id: str, finding_id: str, finding_type: str,
                                domain: str, reasoning_text: str, finding_summary: str = None,
                                evidence: str = None, iteration: int = None) -> int:
        """Create a reasoning chain entry"""
        try:
            with self.db.transaction() as conn:
                cursor = conn.execute(
                    """INSERT INTO reasoning_chains
                       (run_id, finding_id, finding_type, domain, reasoning_text,
                        finding_summary, evidence_from_finding, iteration, created_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (run_id, finding_id, finding_type, domain, reasoning_text,
                     finding_summary, evidence, iteration, now_iso())
                )
                return cursor.lastrowid
        except sqlite3.DatabaseError as e:
            logger.error(f"Error creating reasoning entry: {e}")
            raise RepositoryError(f"Failed to create reasoning entry: {e}")

    def get_reasoning_for_finding(self, finding_id: str) -> Optional[Dict]:
        """Get reasoning chain entry for a finding"""
        try:
            conn = self.db.connect()
            row = conn.execute(
                "SELECT * FROM reasoning_chains WHERE finding_id = ?",
                (finding_id,)
            ).fetchone()
            return dict(row) if row else None
        except sqlite3.DatabaseError as e:
            logger.error(f"Error fetching reasoning for {finding_id}: {e}")
            raise RepositoryError(f"Failed to fetch reasoning: {e}")

    def get_reasoning_chain(self, run_id: str, domain: str = None) -> List[Dict]:
        """Get reasoning chain for a run, optionally filtered by domain"""
        try:
            conn = self.db.connect()
            if domain:
                rows = conn.execute(
                    "SELECT * FROM reasoning_chains WHERE run_id = ? AND domain = ? ORDER BY created_at",
                    (run_id, domain)
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM reasoning_chains WHERE run_id = ? ORDER BY created_at",
                    (run_id,)
                ).fetchall()
            return [dict(r) for r in rows]
        except sqlite3.DatabaseError as e:
            logger.error(f"Error fetching reasoning chain: {e}")
            raise RepositoryError(f"Failed to fetch reasoning chain: {e}")

    # =========================================================================
    # BATCH IMPORT FROM ANALYSIS STORE
    # =========================================================================

    def import_from_analysis_store(self, store, run_id: str) -> Dict[str, int]:
        """
        Import all findings from an AnalysisStore instance.

        Returns counts of imported items.
        """
        counts = {
            'inventory_items': 0,
            'risks': 0,
            'gaps': 0,
            'assumptions': 0,
            'work_items': 0,
            'recommendations': 0,
            'strategic_considerations': 0,
            'questions': 0,
            'errors': 0
        }

        # Import current state entries (use replace_on_conflict for incremental analysis)
        for item in store.current_state:
            try:
                # Handle case where item is a string instead of dict
                if isinstance(item, str):
                    logger.warning(f"Skipping string inventory item: {item[:50]}...")
                    counts['errors'] += 1
                    continue
                inv_item = InventoryItem.from_analysis_store(item, run_id)
                self.create_inventory_item(inv_item, replace_on_conflict=True)
                counts['inventory_items'] += 1
            except (RepositoryError, Exception) as e:
                logger.warning(f"Failed to import inventory item: {e}")
                counts['errors'] += 1

        # Import risks
        for item in store.risks:
            try:
                # Handle case where item is a string instead of dict
                if isinstance(item, str):
                    logger.warning(f"Skipping string risk: {item[:50]}...")
                    counts['errors'] += 1
                    continue
                risk = Risk.from_analysis_store(item, run_id)
                self.create_risk(risk, replace_on_conflict=True)
                counts['risks'] += 1
            except (RepositoryError, Exception) as e:
                logger.warning(f"Failed to import risk: {e}")
                counts['errors'] += 1

        # Import gaps
        for item in store.gaps:
            try:
                # Handle case where item is a string instead of dict
                if isinstance(item, str):
                    logger.warning(f"Skipping string gap: {item[:50]}...")
                    counts['errors'] += 1
                    continue
                gap = Gap.from_analysis_store(item, run_id)
                self.create_gap(gap, replace_on_conflict=True)
                counts['gaps'] += 1
            except (RepositoryError, Exception) as e:
                logger.warning(f"Failed to import gap: {e}")
                counts['errors'] += 1

        # Import assumptions
        for item in store.assumptions:
            try:
                # Handle case where item is a string instead of dict
                if isinstance(item, str):
                    logger.warning(f"Skipping string assumption: {item[:50]}...")
                    counts['errors'] += 1
                    continue
                assumption = Assumption.from_analysis_store(item, run_id)
                self.create_assumption(assumption, replace_on_conflict=True)
                counts['assumptions'] += 1
            except (RepositoryError, Exception) as e:
                logger.warning(f"Failed to import assumption: {e}")
                counts['errors'] += 1

        # Import work items
        for item in store.work_items:
            try:
                # Handle case where item is a string instead of dict
                if isinstance(item, str):
                    logger.warning(f"Skipping string work item: {item[:50]}...")
                    counts['errors'] += 1
                    continue
                work_item = WorkItem.from_analysis_store(item, run_id)
                self.create_work_item(work_item, replace_on_conflict=True)
                counts['work_items'] += 1
            except (RepositoryError, Exception) as e:
                logger.warning(f"Failed to import work item: {e}")
                counts['errors'] += 1

        # Import recommendations
        for item in store.recommendations:
            try:
                # Handle case where item is a string instead of dict
                if isinstance(item, str):
                    logger.warning(f"Skipping string recommendation: {item[:50]}...")
                    counts['errors'] += 1
                    continue
                rec = Recommendation.from_analysis_store(item, run_id)
                self.create_recommendation(rec, replace_on_conflict=True)
                counts['recommendations'] += 1
            except (RepositoryError, Exception) as e:
                logger.warning(f"Failed to import recommendation: {e}")
                counts['errors'] += 1

        # Import strategic considerations
        for item in store.strategic_considerations:
            try:
                # Handle case where item is a string instead of dict
                if isinstance(item, str):
                    logger.warning(f"Skipping string strategic consideration: {item[:50]}...")
                    counts['errors'] += 1
                    continue
                sc = StrategicConsideration.from_analysis_store(item, run_id)
                self.create_strategic_consideration(sc, replace_on_conflict=True)
                counts['strategic_considerations'] += 1
            except (RepositoryError, Exception) as e:
                logger.warning(f"Failed to import strategic consideration: {e}")
                counts['errors'] += 1

        # Import questions (identified by domain agents)
        if hasattr(store, 'questions'):
            for item in store.questions:
                try:
                    # Handle case where item is a string instead of dict
                    if isinstance(item, str):
                        logger.warning(f"Skipping string question: {item[:50]}...")
                        counts['errors'] += 1
                        continue
                    # Create Question from analysis store format
                    q = Question(
                        question_id=item.get('id', generate_id('Q')),
                        run_id=run_id,
                        question_text=item.get('question', ''),
                        context=item.get('context', ''),
                        priority=item.get('priority', 'medium'),
                        status='draft',
                        linked_gap_id=item.get('related_gap_id')
                    )
                    self.create_question(q)
                    counts['questions'] += 1
                except (RepositoryError, Exception) as e:
                    logger.warning(f"Failed to import question: {e}")
                    counts['errors'] += 1

        # Import reasoning chains
        for domain, entries in store.reasoning_chains.items():
            for entry in entries:
                try:
                    self.create_reasoning_entry(
                        run_id=run_id,
                        finding_id=entry.get('finding_id', ''),
                        finding_type=entry.get('finding_type', ''),
                        domain=domain,
                        reasoning_text=entry.get('reasoning_text', ''),
                        finding_summary=entry.get('finding_summary'),
                        evidence=entry.get('evidence_from_finding'),
                        iteration=entry.get('iteration')
                    )
                except (RepositoryError, Exception) as e:
                    logger.warning(f"Failed to import reasoning entry: {e}")

        logger.info(f"Imported from AnalysisStore: {counts}")
        return counts

    # =========================================================================
    # QUERY HELPERS
    # =========================================================================

    def get_findings_by_document(self, document_id: str) -> Dict[str, List]:
        """Get all findings linked to a specific document"""
        results = {}

        try:
            conn = self.db.connect()
            # Query each table for the document
            for table, model_class in [
                ('risks', Risk),
                ('gaps', Gap),
                ('assumptions', Assumption),
                ('inventory_items', InventoryItem),
                ('strategic_considerations', StrategicConsideration)
            ]:
                rows = conn.execute(
                    f"SELECT * FROM {table} WHERE source_document_id = ?",
                    (document_id,)
                ).fetchall()
                results[table] = [model_class.from_row(r) for r in rows]
        except sqlite3.DatabaseError as e:
            logger.error(f"Error fetching findings for document {document_id}: {e}")
            raise RepositoryError(f"Failed to fetch findings: {e}")

        return results

    def get_run_summary(self, run_id: str) -> Dict[str, Any]:
        """Get summary statistics for a run"""
        try:
            conn = self.db.connect()

            summary = {
                'run_id': run_id,
                'counts': {},
                'by_domain': {},
                'by_severity': {},
                'by_phase': {}
            }

            # Counts by table
            for table in ['inventory_items', 'risks', 'gaps', 'assumptions',
                          'work_items', 'recommendations', 'strategic_considerations']:
                result = conn.execute(
                    f"SELECT COUNT(*) FROM {table} WHERE run_id = ?",
                    (run_id,)
                ).fetchone()
                summary['counts'][table] = result[0]

            # Risks by severity
            rows = conn.execute(
                "SELECT severity, COUNT(*) FROM risks WHERE run_id = ? GROUP BY severity",
                (run_id,)
            ).fetchall()
            summary['by_severity'] = {r[0]: r[1] for r in rows}

            # Work items by phase
            rows = conn.execute(
                "SELECT phase, COUNT(*) FROM work_items WHERE run_id = ? GROUP BY phase",
                (run_id,)
            ).fetchall()
            summary['by_phase'] = {r[0]: r[1] for r in rows}

            # Findings by domain
            rows = conn.execute(
                "SELECT domain, COUNT(*) FROM risks WHERE run_id = ? GROUP BY domain",
                (run_id,)
            ).fetchall()
            summary['by_domain']['risks'] = {r[0]: r[1] for r in rows}

            return summary

        except sqlite3.DatabaseError as e:
            logger.error(f"Error getting run summary: {e}")
            raise RepositoryError(f"Failed to get run summary: {e}")

    def get_all_findings_for_run(self, run_id: str) -> Dict[str, List]:
        """Get all findings for a run across all entity types"""
        return {
            'inventory_items': self.get_all_inventory_items(run_id),
            'risks': self.get_all_risks(run_id),
            'gaps': self.get_all_gaps(run_id),
            'assumptions': self.get_all_assumptions(run_id),
            'work_items': self.get_all_work_items(run_id),
            'recommendations': self.get_all_recommendations(run_id),
            'strategic_considerations': self.get_all_strategic_considerations(run_id)
        }

    def close(self):
        """Close database connection"""
        self.db.close()
