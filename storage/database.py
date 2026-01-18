"""
Database Connection Management for IT Due Diligence Agent

Points 24-35, 44 of 115PP:
- SQLite for structure + JSON for flexibility
- Schema for all entity types
- Document tracking
- Analysis run management
"""

import sqlite3
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
from contextlib import contextmanager

# Default database location
DEFAULT_DB_PATH = Path(__file__).parent.parent / "data" / "diligence.db"


class Database:
    """
    SQLite database manager with schema initialization.

    Design decisions (Point 24-25):
    - SQLite for structured queries and relationships
    - JSON columns for flexible/nested data (source_evidence, metadata)
    - Foreign keys for referential integrity
    - Timestamps on all records for audit trail
    
    Thread-safe connection management with context manager support.
    """

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = Path(db_path) if db_path else DEFAULT_DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._connection: Optional[sqlite3.Connection] = None

    def connect(self) -> sqlite3.Connection:
        """Get database connection with row factory"""
        if self._connection is None:
            self._connection = sqlite3.connect(str(self.db_path))
            self._connection.row_factory = sqlite3.Row
            # Enable foreign keys
            self._connection.execute("PRAGMA foreign_keys = ON")
        return self._connection

    def close(self):
        """Close database connection"""
        if self._connection:
            self._connection.close()
            self._connection = None

    def __enter__(self):
        """Context manager entry - returns self"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensures connection is closed"""
        self.close()
        return False  # Don't suppress exceptions

    @contextmanager
    def transaction(self):
        """Context manager for transactions - ensures rollback on error"""
        conn = self.connect()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            # Note: We don't close connection here as it may be reused
            # Connection is closed via __exit__ or explicit close()
            pass

    def initialize_schema(self):
        """
        Create all tables if they don't exist.

        Schema Design (Points 26-35):
        - documents: Source tracking (Point 34)
        - analysis_runs: Session tracking (Point 35)
        - inventory_items: Current state entries (Point 27)
        - risks: Risk findings (Point 28)
        - gaps: Knowledge gaps (Point 29)
        - assumptions: Analysis assumptions (Point 30)
        - work_items: Integration tasks (Point 31)
        - recommendations: Strategic recommendations (Point 32)
        - strategic_considerations: Deal implications (Point 33)
        - questions: Gap-linked questions for seller
        """
        conn = self.connect()

        # Point 34: Documents table (source tracking)
        # Points 36-39: Document tracking fields
        conn.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                document_id TEXT PRIMARY KEY,
                document_name TEXT NOT NULL,
                document_path TEXT,
                document_type TEXT NOT NULL DEFAULT 'vdr',
                page_count INTEGER,
                ingested_date TEXT NOT NULL,
                last_updated TEXT NOT NULL,
                file_hash TEXT,
                metadata JSON,
                UNIQUE(document_path)
            )
        """)

        # Point 35: Analysis runs table (session tracking)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS analysis_runs (
                run_id TEXT PRIMARY KEY,
                run_name TEXT,
                started_at TEXT NOT NULL,
                completed_at TEXT,
                mode TEXT NOT NULL DEFAULT 'fresh',
                status TEXT NOT NULL DEFAULT 'in_progress',
                deal_context JSON,
                documents_analyzed JSON,
                summary JSON
            )
        """)

        # Point 27: Inventory items table (current state)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS inventory_items (
                item_id TEXT PRIMARY KEY,
                run_id TEXT NOT NULL,
                domain TEXT NOT NULL,
                category TEXT NOT NULL,
                item_name TEXT NOT NULL,
                description TEXT,
                status TEXT NOT NULL DEFAULT 'documented',
                maturity TEXT,
                standalone_viability TEXT,
                key_characteristics JSON,
                source_document_id TEXT,
                source_page INTEGER,
                source_section TEXT,
                source_evidence JSON,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (run_id) REFERENCES analysis_runs(run_id),
                FOREIGN KEY (source_document_id) REFERENCES documents(document_id)
            )
        """)

        # Point 28: Risks table
        # Points 40-43: Attribution fields included
        conn.execute("""
            CREATE TABLE IF NOT EXISTS risks (
                risk_id TEXT PRIMARY KEY,
                run_id TEXT NOT NULL,
                domain TEXT NOT NULL,
                risk_description TEXT NOT NULL,
                trigger_description TEXT,
                severity TEXT NOT NULL,
                likelihood TEXT NOT NULL,
                risk_type TEXT,
                integration_dependent INTEGER DEFAULT 1,
                standalone_exposure TEXT,
                deal_impact JSON,
                impact_description TEXT,
                mitigation TEXT,
                cost_impact_estimate TEXT,
                risk_score REAL,
                priority_rank INTEGER,
                source_type TEXT DEFAULT 'document',
                source_document_id TEXT,
                source_page INTEGER,
                source_section TEXT,
                speaker_name TEXT,
                statement_date TEXT,
                confidence_level TEXT DEFAULT 'medium',
                source_evidence JSON,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (run_id) REFERENCES analysis_runs(run_id),
                FOREIGN KEY (source_document_id) REFERENCES documents(document_id)
            )
        """)

        # Point 29: Gaps table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS gaps (
                gap_id TEXT PRIMARY KEY,
                run_id TEXT NOT NULL,
                domain TEXT NOT NULL,
                gap_description TEXT NOT NULL,
                why_needed TEXT,
                priority TEXT NOT NULL,
                gap_type TEXT,
                suggested_source TEXT,
                cost_impact TEXT,
                question_status TEXT DEFAULT 'not_asked',
                source_type TEXT DEFAULT 'document',
                source_document_id TEXT,
                source_section TEXT,
                confidence_level TEXT DEFAULT 'high',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (run_id) REFERENCES analysis_runs(run_id),
                FOREIGN KEY (source_document_id) REFERENCES documents(document_id)
            )
        """)

        # Point 30: Assumptions table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS assumptions (
                assumption_id TEXT PRIMARY KEY,
                run_id TEXT NOT NULL,
                domain TEXT NOT NULL,
                assumption_text TEXT NOT NULL,
                basis TEXT,
                confidence TEXT NOT NULL,
                impact TEXT,
                validation_needed TEXT,
                validation_status TEXT DEFAULT 'unvalidated',
                supporting_quote TEXT,
                source_type TEXT DEFAULT 'document',
                source_document_id TEXT,
                source_section TEXT,
                speaker_name TEXT,
                statement_date TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (run_id) REFERENCES analysis_runs(run_id),
                FOREIGN KEY (source_document_id) REFERENCES documents(document_id)
            )
        """)

        # Point 31: Work items table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS work_items (
                work_item_id TEXT PRIMARY KEY,
                run_id TEXT NOT NULL,
                domain TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                category TEXT,
                phase TEXT NOT NULL,
                phase_rationale TEXT,
                effort_estimate TEXT,
                cost_estimate_range TEXT,
                depends_on JSON,
                skills_required JSON,
                triggered_by JSON,
                priority_score INTEGER,
                source_document_id TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (run_id) REFERENCES analysis_runs(run_id),
                FOREIGN KEY (source_document_id) REFERENCES documents(document_id)
            )
        """)

        # Point 32: Recommendations table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS recommendations (
                recommendation_id TEXT PRIMARY KEY,
                run_id TEXT NOT NULL,
                domain TEXT NOT NULL,
                recommendation_text TEXT NOT NULL,
                rationale TEXT,
                priority TEXT NOT NULL,
                timing TEXT,
                investment_required TEXT,
                driven_by JSON,
                source_document_id TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (run_id) REFERENCES analysis_runs(run_id),
                FOREIGN KEY (source_document_id) REFERENCES documents(document_id)
            )
        """)

        # Point 33: Strategic considerations table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS strategic_considerations (
                consideration_id TEXT PRIMARY KEY,
                run_id TEXT NOT NULL,
                domain TEXT NOT NULL,
                theme TEXT NOT NULL,
                observation TEXT NOT NULL,
                implication TEXT,
                deal_relevance JSON,
                buyer_alignment TEXT,
                source_type TEXT DEFAULT 'document',
                source_document_id TEXT,
                source_section TEXT,
                source_evidence JSON,
                speaker_name TEXT,
                statement_date TEXT,
                confidence_level TEXT DEFAULT 'medium',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (run_id) REFERENCES analysis_runs(run_id),
                FOREIGN KEY (source_document_id) REFERENCES documents(document_id)
            )
        """)

        # Questions table (links gaps to seller questions)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS questions (
                question_id TEXT PRIMARY KEY,
                run_id TEXT NOT NULL,
                linked_gap_id TEXT,
                linked_assumption_id TEXT,
                question_text TEXT NOT NULL,
                context TEXT,
                priority TEXT NOT NULL DEFAULT 'medium',
                status TEXT NOT NULL DEFAULT 'draft',
                sent_date TEXT,
                answer_text TEXT,
                answer_date TEXT,
                answer_source TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (run_id) REFERENCES analysis_runs(run_id),
                FOREIGN KEY (linked_gap_id) REFERENCES gaps(gap_id),
                FOREIGN KEY (linked_assumption_id) REFERENCES assumptions(assumption_id)
            )
        """)

        # Reasoning chains table (audit trail)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS reasoning_chains (
                entry_id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT NOT NULL,
                finding_id TEXT NOT NULL,
                finding_type TEXT NOT NULL,
                domain TEXT NOT NULL,
                reasoning_text TEXT,
                finding_summary TEXT,
                evidence_from_finding TEXT,
                iteration INTEGER,
                created_at TEXT NOT NULL,
                FOREIGN KEY (run_id) REFERENCES analysis_runs(run_id)
            )
        """)

        # Point 85: Assumption evidence table (Phase 4)
        # Tracks evidence supporting or refuting assumptions
        conn.execute("""
            CREATE TABLE IF NOT EXISTS assumption_evidence (
                evidence_id INTEGER PRIMARY KEY AUTOINCREMENT,
                assumption_id TEXT NOT NULL,
                run_id TEXT NOT NULL,
                evidence_type TEXT NOT NULL DEFAULT 'supporting',
                evidence_text TEXT NOT NULL,
                source_type TEXT DEFAULT 'document',
                source_document_id TEXT,
                source_section TEXT,
                speaker_name TEXT,
                statement_date TEXT,
                confidence_weight REAL DEFAULT 1.0,
                notes TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (assumption_id) REFERENCES assumptions(assumption_id),
                FOREIGN KEY (run_id) REFERENCES analysis_runs(run_id),
                FOREIGN KEY (source_document_id) REFERENCES documents(document_id)
            )
        """)

        # Create indexes for common queries
        # Domain and run indexes
        conn.execute("CREATE INDEX IF NOT EXISTS idx_inventory_domain ON inventory_items(domain)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_inventory_run ON inventory_items(run_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_inventory_run_domain ON inventory_items(run_id, domain)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_risks_domain ON risks(domain)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_risks_severity ON risks(severity)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_risks_run ON risks(run_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_risks_run_domain ON risks(run_id, domain)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_gaps_domain ON gaps(domain)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_gaps_priority ON gaps(priority)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_gaps_run ON gaps(run_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_assumptions_run ON assumptions(run_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_work_items_phase ON work_items(phase)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_work_items_domain ON work_items(domain)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_work_items_run ON work_items(run_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_recommendations_run ON recommendations(run_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_strategic_run ON strategic_considerations(run_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_questions_status ON questions(status)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_questions_run ON questions(run_id)")

        # Source document indexes (for document tracking queries)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_inventory_doc ON inventory_items(source_document_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_risks_doc ON risks(source_document_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_gaps_doc ON gaps(source_document_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_assumptions_doc ON assumptions(source_document_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_strategic_doc ON strategic_considerations(source_document_id)")

        # Timestamp indexes (for time-based queries)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_inventory_created ON inventory_items(created_at)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_risks_created ON risks(created_at)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_reasoning_created ON reasoning_chains(created_at)")

        # Assumption evidence indexes (Point 85)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_assumption_evidence_assumption ON assumption_evidence(assumption_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_assumption_evidence_run ON assumption_evidence(run_id)")

        conn.commit()
        print(f"Database schema initialized: {self.db_path}")

    def get_table_counts(self) -> Dict[str, int]:
        """Get row counts for all tables"""
        conn = self.connect()
        tables = [
            'documents', 'analysis_runs', 'inventory_items', 'risks',
            'gaps', 'assumptions', 'work_items', 'recommendations',
            'strategic_considerations', 'questions', 'reasoning_chains'
        ]
        counts = {}
        for table in tables:
            try:
                result = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()
                counts[table] = result[0]
            except sqlite3.OperationalError:
                counts[table] = -1  # Table doesn't exist
        return counts


# Singleton pattern for default database
_default_db: Optional[Database] = None


def get_db(db_path: Optional[Path] = None) -> Database:
    """Get or create database instance"""
    global _default_db
    if db_path:
        return Database(db_path)
    if _default_db is None:
        _default_db = Database()
        _default_db.initialize_schema()
    return _default_db
