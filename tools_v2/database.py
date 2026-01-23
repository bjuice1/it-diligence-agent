"""
Database module for IT Due Diligence Agent.

Provides SQLite-based persistence for deals, facts, findings, etc.
Uses sqlite3 (built into Python) for simplicity.
"""

import sqlite3
import json
import uuid
from pathlib import Path
from typing import Dict, List, Optional

from tools_v2.fact_store import FactStore, Fact, Gap
from tools_v2.reasoning_tools import ReasoningStore


# Default database location
DEFAULT_DB_PATH = Path(__file__).parent.parent / "data" / "diligence.db"


_db_initialized = False

def get_connection(db_path: Path = None, _skip_init: bool = False) -> sqlite3.Connection:
    """Get a database connection (initializes database on first use)."""
    global _db_initialized
    if db_path is None:
        db_path = DEFAULT_DB_PATH

    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row  # Enable dict-like access

    # Initialize schema on first connection (avoid recursion with _skip_init)
    if not _skip_init and not _db_initialized:
        _db_initialized = True
        _init_schema(conn)

    return conn


def _init_schema(conn: sqlite3.Connection):
    """Initialize database schema (internal use)."""
    cursor = conn.cursor()
    cursor.executescript('''
        -- Deals table
        CREATE TABLE IF NOT EXISTS deals (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            target_name TEXT NOT NULL,
            buyer_name TEXT,
            deal_type TEXT NOT NULL,
            status TEXT DEFAULT 'active',
            phase TEXT DEFAULT 'discovery',
            fact_count INTEGER DEFAULT 0,
            gap_count INTEGER DEFAULT 0,
            risk_count INTEGER DEFAULT 0,
            work_item_count INTEGER DEFAULT 0,
            total_cost_low INTEGER DEFAULT 0,
            total_cost_high INTEGER DEFAULT 0,
            settings TEXT DEFAULT '{}',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS documents (
            id TEXT PRIMARY KEY,
            deal_id TEXT NOT NULL REFERENCES deals(id) ON DELETE CASCADE,
            filename TEXT NOT NULL,
            file_type TEXT,
            file_size INTEGER,
            entity TEXT DEFAULT 'target',
            doc_type TEXT,
            status TEXT DEFAULT 'processed',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS facts (
            id TEXT PRIMARY KEY,
            deal_id TEXT NOT NULL REFERENCES deals(id) ON DELETE CASCADE,
            fact_id TEXT NOT NULL,
            domain TEXT NOT NULL,
            category TEXT NOT NULL,
            entity TEXT DEFAULT 'target',
            item TEXT NOT NULL,
            details TEXT DEFAULT '{}',
            status TEXT DEFAULT 'documented',
            evidence_quote TEXT,
            evidence_section TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(deal_id, fact_id)
        );

        CREATE TABLE IF NOT EXISTS gaps (
            id TEXT PRIMARY KEY,
            deal_id TEXT NOT NULL REFERENCES deals(id) ON DELETE CASCADE,
            gap_id TEXT NOT NULL,
            domain TEXT NOT NULL,
            category TEXT NOT NULL,
            description TEXT NOT NULL,
            importance TEXT DEFAULT 'medium',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(deal_id, gap_id)
        );

        CREATE TABLE IF NOT EXISTS risks (
            id TEXT PRIMARY KEY,
            deal_id TEXT NOT NULL REFERENCES deals(id) ON DELETE CASCADE,
            risk_id TEXT NOT NULL,
            domain TEXT NOT NULL,
            category TEXT,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            severity TEXT NOT NULL,
            mitigation TEXT,
            reasoning TEXT,
            integration_dependent INTEGER DEFAULT 0,
            confidence TEXT DEFAULT 'medium',
            based_on_facts TEXT DEFAULT '[]',
            status TEXT DEFAULT 'identified',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(deal_id, risk_id)
        );

        CREATE TABLE IF NOT EXISTS work_items (
            id TEXT PRIMARY KEY,
            deal_id TEXT NOT NULL REFERENCES deals(id) ON DELETE CASCADE,
            work_item_id TEXT NOT NULL,
            domain TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            phase TEXT NOT NULL,
            priority TEXT DEFAULT 'medium',
            owner_type TEXT,
            cost_estimate TEXT,
            cost_low INTEGER,
            cost_high INTEGER,
            reasoning TEXT,
            triggered_by TEXT DEFAULT '[]',
            triggered_by_risks TEXT DEFAULT '[]',
            based_on_facts TEXT DEFAULT '[]',
            confidence TEXT DEFAULT 'medium',
            status TEXT DEFAULT 'identified',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(deal_id, work_item_id)
        );

        CREATE TABLE IF NOT EXISTS strategic_considerations (
            id TEXT PRIMARY KEY,
            deal_id TEXT NOT NULL REFERENCES deals(id) ON DELETE CASCADE,
            consideration_id TEXT NOT NULL,
            domain TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            lens TEXT,
            implication TEXT,
            based_on_facts TEXT DEFAULT '[]',
            confidence TEXT DEFAULT 'medium',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(deal_id, consideration_id)
        );

        CREATE TABLE IF NOT EXISTS recommendations (
            id TEXT PRIMARY KEY,
            deal_id TEXT NOT NULL REFERENCES deals(id) ON DELETE CASCADE,
            recommendation_id TEXT NOT NULL,
            domain TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            action_type TEXT,
            urgency TEXT DEFAULT 'medium',
            rationale TEXT,
            based_on_facts TEXT DEFAULT '[]',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(deal_id, recommendation_id)
        );

        CREATE TABLE IF NOT EXISTS analysis_runs (
            id TEXT PRIMARY KEY,
            deal_id TEXT NOT NULL REFERENCES deals(id) ON DELETE CASCADE,
            run_type TEXT NOT NULL,
            domains TEXT NOT NULL,
            status TEXT DEFAULT 'running',
            started_at TEXT DEFAULT CURRENT_TIMESTAMP,
            completed_at TEXT,
            facts_extracted INTEGER DEFAULT 0,
            gaps_identified INTEGER DEFAULT 0,
            risks_found INTEGER DEFAULT 0,
            work_items_found INTEGER DEFAULT 0,
            tokens_used INTEGER DEFAULT 0,
            estimated_cost REAL DEFAULT 0,
            error_message TEXT
        );

        CREATE INDEX IF NOT EXISTS idx_facts_deal ON facts(deal_id);
        CREATE INDEX IF NOT EXISTS idx_facts_domain ON facts(deal_id, domain);
        CREATE INDEX IF NOT EXISTS idx_gaps_deal ON gaps(deal_id);
        CREATE INDEX IF NOT EXISTS idx_risks_deal ON risks(deal_id);
        CREATE INDEX IF NOT EXISTS idx_work_items_deal ON work_items(deal_id);
        CREATE INDEX IF NOT EXISTS idx_deals_status ON deals(status);
    ''')
    conn.commit()


def init_database(db_path: Path = None):
    """Initialize the database schema (triggers lazy init via get_connection)."""
    global _db_initialized
    _db_initialized = False  # Force re-init
    conn = get_connection(db_path)
    conn.close()
    print(f"Database initialized at: {db_path or DEFAULT_DB_PATH}")


# =============================================================================
# DEAL OPERATIONS
# =============================================================================

def create_deal(
    name: str,
    target_name: str,
    deal_type: str,
    buyer_name: str = None,
    db_path: Path = None
) -> str:
    """Create a new deal and return its ID."""
    conn = get_connection(db_path)
    cursor = conn.cursor()

    deal_id = str(uuid.uuid4())

    cursor.execute('''
        INSERT INTO deals (id, name, target_name, buyer_name, deal_type)
        VALUES (?, ?, ?, ?, ?)
    ''', (deal_id, name, target_name, buyer_name, deal_type))

    conn.commit()
    conn.close()

    return deal_id


def get_deal(deal_id: str, db_path: Path = None) -> Optional[Dict]:
    """Get a deal by ID."""
    conn = get_connection(db_path)
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM deals WHERE id = ?', (deal_id,))
    row = cursor.fetchone()

    conn.close()

    if row:
        return dict(row)
    return None


def list_deals(status: str = None, db_path: Path = None) -> List[Dict]:
    """List all deals, optionally filtered by status."""
    conn = get_connection(db_path)
    cursor = conn.cursor()

    if status:
        cursor.execute(
            'SELECT * FROM deals WHERE status = ? ORDER BY created_at DESC',
            (status,)
        )
    else:
        cursor.execute('SELECT * FROM deals ORDER BY created_at DESC')

    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


def update_deal_stats(deal_id: str, db_path: Path = None):
    """Update the denormalized stats on a deal using a single aggregation query."""
    conn = get_connection(db_path)
    cursor = conn.cursor()

    # Single query to get all counts using subqueries
    cursor.execute('''
        UPDATE deals SET
            fact_count = (SELECT COUNT(*) FROM facts WHERE deal_id = ?),
            gap_count = (SELECT COUNT(*) FROM gaps WHERE deal_id = ?),
            risk_count = (SELECT COUNT(*) FROM risks WHERE deal_id = ?),
            work_item_count = (SELECT COUNT(*) FROM work_items WHERE deal_id = ?),
            total_cost_low = (SELECT COALESCE(SUM(cost_low), 0) FROM work_items WHERE deal_id = ?),
            total_cost_high = (SELECT COALESCE(SUM(cost_high), 0) FROM work_items WHERE deal_id = ?),
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', (deal_id, deal_id, deal_id, deal_id, deal_id, deal_id, deal_id))

    conn.commit()
    conn.close()


def delete_deal(deal_id: str, db_path: Path = None):
    """Delete a deal and all its data."""
    conn = get_connection(db_path)
    cursor = conn.cursor()

    # Delete in order (children first due to foreign keys)
    tables = ['analysis_runs', 'recommendations', 'strategic_considerations',
              'work_items', 'risks', 'gaps', 'facts', 'documents', 'deals']

    for table in tables:
        if table == 'deals':
            cursor.execute(f'DELETE FROM {table} WHERE id = ?', (deal_id,))
        else:
            cursor.execute(f'DELETE FROM {table} WHERE deal_id = ?', (deal_id,))

    conn.commit()
    conn.close()


# =============================================================================
# SAVE OPERATIONS
# =============================================================================

def save_fact_store(deal_id: str, fact_store: FactStore, db_path: Path = None):
    """Save a FactStore to the database using batch inserts."""
    conn = get_connection(db_path)
    cursor = conn.cursor()

    # Batch insert facts
    fact_data = [
        (
            str(uuid.uuid4()),
            deal_id,
            fact.fact_id,
            fact.domain,
            fact.category,
            getattr(fact, 'entity', 'target'),
            fact.item,
            json.dumps(fact.details),
            fact.status,
            fact.evidence.get('exact_quote', '') if fact.evidence else '',
            fact.evidence.get('source_section', '') if fact.evidence else ''
        )
        for fact in fact_store.facts
    ]

    if fact_data:
        cursor.executemany('''
            INSERT OR REPLACE INTO facts
            (id, deal_id, fact_id, domain, category, entity, item, details, status,
             evidence_quote, evidence_section)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', fact_data)

    # Batch insert gaps (matches Gap dataclass fields)
    gap_data = [
        (
            str(uuid.uuid4()),
            deal_id,
            gap.gap_id,
            gap.domain,
            gap.category,
            gap.description,
            gap.importance
        )
        for gap in fact_store.gaps
    ]

    if gap_data:
        cursor.executemany('''
            INSERT OR REPLACE INTO gaps
            (id, deal_id, gap_id, domain, category, description, importance)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', gap_data)

    conn.commit()
    conn.close()


def save_reasoning_store(deal_id: str, reasoning_store: ReasoningStore, db_path: Path = None):
    """Save a ReasoningStore to the database using batch inserts."""
    from tools_v2.reasoning_tools import COST_RANGE_VALUES

    conn = get_connection(db_path)
    cursor = conn.cursor()

    # Batch insert risks
    risk_data = [
        (
            str(uuid.uuid4()),
            deal_id,
            risk.finding_id,
            risk.domain,
            risk.category,
            risk.title,
            risk.description,
            risk.severity,
            risk.mitigation,
            risk.reasoning,
            1 if risk.integration_dependent else 0,
            risk.confidence,
            json.dumps(risk.based_on_facts)
        )
        for risk in reasoning_store.risks
    ]

    if risk_data:
        cursor.executemany('''
            INSERT OR REPLACE INTO risks
            (id, deal_id, risk_id, domain, category, title, description, severity,
             mitigation, reasoning, integration_dependent, confidence, based_on_facts)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', risk_data)

    # Batch insert work items (include all fields)
    wi_data = [
        (
            str(uuid.uuid4()),
            deal_id,
            wi.finding_id,
            wi.domain,
            wi.title,
            wi.description,
            wi.phase,
            wi.priority,
            wi.owner_type,
            wi.cost_estimate,
            COST_RANGE_VALUES.get(wi.cost_estimate, {'low': 0, 'high': 0})['low'],
            COST_RANGE_VALUES.get(wi.cost_estimate, {'low': 0, 'high': 0})['high'],
            wi.reasoning,
            json.dumps(wi.triggered_by),
            json.dumps(wi.triggered_by_risks),
            json.dumps(getattr(wi, 'based_on_facts', [])),
            getattr(wi, 'confidence', 'medium')
        )
        for wi in reasoning_store.work_items
    ]

    if wi_data:
        cursor.executemany('''
            INSERT OR REPLACE INTO work_items
            (id, deal_id, work_item_id, domain, title, description, phase, priority,
             owner_type, cost_estimate, cost_low, cost_high, reasoning, triggered_by,
             triggered_by_risks, based_on_facts, confidence)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', wi_data)

    # Batch insert strategic considerations
    sc_data = [
        (
            str(uuid.uuid4()),
            deal_id,
            sc.finding_id,
            sc.domain,
            sc.title,
            sc.description,
            sc.lens,
            sc.implication,
            json.dumps(sc.based_on_facts),
            sc.confidence
        )
        for sc in reasoning_store.strategic_considerations
    ]

    if sc_data:
        cursor.executemany('''
            INSERT OR REPLACE INTO strategic_considerations
            (id, deal_id, consideration_id, domain, title, description, lens,
             implication, based_on_facts, confidence)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', sc_data)

    # Batch insert recommendations
    rec_data = [
        (
            str(uuid.uuid4()),
            deal_id,
            rec.finding_id,
            rec.domain,
            rec.title,
            rec.description,
            rec.action_type,
            rec.urgency,
            rec.rationale,
            json.dumps(rec.based_on_facts)
        )
        for rec in reasoning_store.recommendations
    ]

    if rec_data:
        cursor.executemany('''
            INSERT OR REPLACE INTO recommendations
            (id, deal_id, recommendation_id, domain, title, description, action_type,
             urgency, rationale, based_on_facts)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', rec_data)

    conn.commit()
    conn.close()


def save_deal_complete(
    deal_id: str,
    fact_store: FactStore,
    reasoning_store: ReasoningStore,
    db_path: Path = None
):
    """Save both FactStore and ReasoningStore, then update stats."""
    save_fact_store(deal_id, fact_store, db_path)
    save_reasoning_store(deal_id, reasoning_store, db_path)
    update_deal_stats(deal_id, db_path)


# =============================================================================
# LOAD OPERATIONS
# =============================================================================

def load_fact_store(deal_id: str, db_path: Path = None) -> FactStore:
    """Load a FactStore from the database."""
    conn = get_connection(db_path)
    cursor = conn.cursor()

    fact_store = FactStore()

    # Load facts
    cursor.execute('SELECT * FROM facts WHERE deal_id = ?', (deal_id,))
    for row in cursor.fetchall():
        fact = Fact(
            fact_id=row['fact_id'],
            domain=row['domain'],
            category=row['category'],
            item=row['item'],
            details=json.loads(row['details']) if row['details'] else {},
            status=row['status'],
            evidence={
                'exact_quote': row['evidence_quote'],
                'source_section': row['evidence_section']
            },
            entity=row['entity']
        )
        fact_store.facts.append(fact)

    # Load gaps (matches Gap dataclass fields)
    cursor.execute('SELECT * FROM gaps WHERE deal_id = ?', (deal_id,))
    for row in cursor.fetchall():
        gap = Gap(
            gap_id=row['gap_id'],
            domain=row['domain'],
            category=row['category'],
            description=row['description'] or '',
            importance=row['importance'] or 'medium'
        )
        fact_store.gaps.append(gap)

    conn.close()
    return fact_store


def load_reasoning_store(deal_id: str, db_path: Path = None) -> ReasoningStore:
    """Load a ReasoningStore from the database."""
    from tools_v2.reasoning_tools import Risk, WorkItem, StrategicConsideration, Recommendation

    conn = get_connection(db_path)
    cursor = conn.cursor()

    reasoning_store = ReasoningStore()

    # Helper to safely get column value (handles old schemas)
    def safe_get(row, column, default=''):
        try:
            val = row[column]
            return val if val is not None else default
        except (IndexError, KeyError):
            return default

    # Load risks
    cursor.execute('SELECT * FROM risks WHERE deal_id = ?', (deal_id,))
    for row in cursor.fetchall():
        risk = Risk(
            finding_id=row['risk_id'],
            domain=row['domain'],
            category=safe_get(row, 'category', ''),
            title=row['title'],
            description=row['description'],
            severity=row['severity'],
            mitigation=safe_get(row, 'mitigation', ''),
            reasoning=safe_get(row, 'reasoning', ''),
            integration_dependent=bool(safe_get(row, 'integration_dependent', False)),
            based_on_facts=json.loads(row['based_on_facts']) if row['based_on_facts'] else [],
            confidence=safe_get(row, 'confidence', 'medium')
        )
        reasoning_store.risks.append(risk)

    # Load work items (include all required fields)
    cursor.execute('SELECT * FROM work_items WHERE deal_id = ?', (deal_id,))
    for row in cursor.fetchall():
        wi = WorkItem(
            finding_id=row['work_item_id'],
            domain=row['domain'],
            title=row['title'],
            description=row['description'],
            phase=row['phase'],
            priority=safe_get(row, 'priority', 'medium'),
            owner_type=safe_get(row, 'owner_type', ''),
            cost_estimate=safe_get(row, 'cost_estimate', 'under_25k'),
            reasoning=safe_get(row, 'reasoning', ''),
            triggered_by=json.loads(row['triggered_by']) if safe_get(row, 'triggered_by') else [],
            triggered_by_risks=json.loads(row['triggered_by_risks']) if safe_get(row, 'triggered_by_risks') else [],
            based_on_facts=json.loads(row['based_on_facts']) if safe_get(row, 'based_on_facts') else [],
            confidence=safe_get(row, 'confidence', 'medium')
        )
        reasoning_store.work_items.append(wi)

    # Load strategic considerations
    cursor.execute('SELECT * FROM strategic_considerations WHERE deal_id = ?', (deal_id,))
    for row in cursor.fetchall():
        sc = StrategicConsideration(
            finding_id=row['consideration_id'],
            domain=row['domain'],
            title=row['title'],
            description=row['description'],
            lens=safe_get(row, 'lens', ''),
            implication=safe_get(row, 'implication', ''),
            based_on_facts=json.loads(row['based_on_facts']) if safe_get(row, 'based_on_facts') else [],
            confidence=safe_get(row, 'confidence', 'medium'),
            reasoning=safe_get(row, 'reasoning', '')
        )
        reasoning_store.strategic_considerations.append(sc)

    # Load recommendations
    cursor.execute('SELECT * FROM recommendations WHERE deal_id = ?', (deal_id,))
    for row in cursor.fetchall():
        rec = Recommendation(
            finding_id=row['recommendation_id'],
            domain=row['domain'],
            title=row['title'],
            description=row['description'],
            action_type=safe_get(row, 'action_type', ''),
            urgency=safe_get(row, 'urgency', 'post-close'),
            rationale=safe_get(row, 'rationale', ''),
            based_on_facts=json.loads(row['based_on_facts']) if safe_get(row, 'based_on_facts') else [],
            confidence=safe_get(row, 'confidence', 'medium'),
            reasoning=safe_get(row, 'reasoning', '')
        )
        reasoning_store.recommendations.append(rec)

    conn.close()
    return reasoning_store


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def get_deal_summary(deal_id: str, db_path: Path = None) -> Dict:
    """Get a summary of a deal with all its stats using a single connection."""
    conn = get_connection(db_path)
    cursor = conn.cursor()

    # Get deal info
    cursor.execute('SELECT * FROM deals WHERE id = ?', (deal_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None
    deal = dict(row)

    # Get risk breakdown by severity
    cursor.execute('''
        SELECT severity, COUNT(*) as count
        FROM risks WHERE deal_id = ?
        GROUP BY severity
    ''', (deal_id,))
    risk_by_severity = {row['severity']: row['count'] for row in cursor.fetchall()}

    # Get work items by phase
    cursor.execute('''
        SELECT phase, COUNT(*) as count, SUM(cost_low) as low, SUM(cost_high) as high
        FROM work_items WHERE deal_id = ?
        GROUP BY phase
    ''', (deal_id,))
    wi_by_phase = {
        row['phase']: {
            'count': row['count'],
            'cost_low': row['low'] or 0,
            'cost_high': row['high'] or 0
        }
        for row in cursor.fetchall()
    }

    # Get facts by domain
    cursor.execute('''
        SELECT domain, COUNT(*) as count
        FROM facts WHERE deal_id = ?
        GROUP BY domain
    ''', (deal_id,))
    facts_by_domain = {row['domain']: row['count'] for row in cursor.fetchall()}

    conn.close()

    return {
        **deal,
        'risk_by_severity': risk_by_severity,
        'work_items_by_phase': wi_by_phase,
        'facts_by_domain': facts_by_domain
    }
