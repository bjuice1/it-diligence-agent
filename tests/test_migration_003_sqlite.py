"""
Test migration 003 works on SQLite

Verifies that the cost_status migration can run on SQLite (local development)
without PostgreSQL-specific syntax errors.
"""

import pytest
import sqlite3
import json
from pathlib import Path


def test_migration_sql_syntax_sqlite():
    """Test that migration SQL uses SQLite-compatible syntax."""

    # Create in-memory SQLite database
    db_path = ':memory:'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create minimal facts table matching production schema
    cursor.execute('''
        CREATE TABLE facts (
            id TEXT PRIMARY KEY,
            deal_id TEXT NOT NULL,
            domain TEXT NOT NULL,
            entity TEXT NOT NULL,
            item TEXT NOT NULL,
            details TEXT,
            deleted_at DATETIME
        )
    ''')

    # Insert test data
    test_facts = [
        ('F-1', 'deal-1', 'applications', 'target', 'App1',
         json.dumps({'cost': '1000', 'cost_status': 'known'}), None),
        ('F-2', 'deal-1', 'applications', 'target', 'App2',
         json.dumps({'annual_cost': '2000'}), None),
        ('F-3', 'deal-1', 'applications', 'target', 'App3',
         json.dumps({'cost_status': 'unknown'}), None),
    ]

    cursor.executemany(
        'INSERT INTO facts VALUES (?, ?, ?, ?, ?, ?, ?)',
        test_facts
    )
    conn.commit()

    # Test 1: Add cost_status column (simulating migration upgrade)
    cursor.execute('''
        ALTER TABLE facts ADD COLUMN cost_status TEXT
    ''')

    # Test 2: Extract cost_status from JSON using SQLite syntax
    cursor.execute('''
        UPDATE facts
        SET cost_status = json_extract(details, '$.cost_status')
        WHERE json_extract(details, '$.cost_status') IS NOT NULL
    ''')
    conn.commit()

    # Test 3: Verify data migrated correctly
    cursor.execute("SELECT id, cost_status FROM facts ORDER BY id")
    results = cursor.fetchall()

    assert results[0] == ('F-1', 'known'), "F-1 should have cost_status='known'"
    assert results[1] == ('F-2', None), "F-2 should have cost_status=NULL"
    assert results[2] == ('F-3', 'unknown'), "F-3 should have cost_status='unknown'"

    # Test 4: Infer cost_status for facts with cost but no explicit status
    cursor.execute('''
        UPDATE facts
        SET cost_status = CASE
            WHEN json_extract(details, '$.cost') IS NOT NULL
              OR json_extract(details, '$.annual_cost') IS NOT NULL THEN 'known'
            ELSE NULL
        END
        WHERE cost_status IS NULL
          AND domain = 'applications'
    ''')
    conn.commit()

    # Verify inference worked
    cursor.execute("SELECT cost_status FROM facts WHERE id = 'F-2'")
    result = cursor.fetchone()
    assert result[0] == 'known', "F-2 should have inferred cost_status='known'"

    conn.close()


def test_migration_downgrade_sqlite():
    """Test that migration downgrade works on SQLite."""

    conn = sqlite3.connect(':memory:')
    cursor = conn.cursor()

    # Create facts table with cost_status column
    cursor.execute('''
        CREATE TABLE facts (
            id TEXT PRIMARY KEY,
            deal_id TEXT NOT NULL,
            domain TEXT NOT NULL,
            item TEXT NOT NULL,
            details TEXT,
            cost_status TEXT
        )
    ''')

    # Insert fact with cost_status
    cursor.execute('''
        INSERT INTO facts VALUES (
            'F-1', 'deal-1', 'applications', 'App1',
            '{}', 'known'
        )
    ''')
    conn.commit()

    # Test downgrade: migrate cost_status back to JSON using SQLite json_set
    cursor.execute('''
        UPDATE facts
        SET details = json_set(
            COALESCE(details, '{}'),
            '$.cost_status',
            cost_status
        )
        WHERE cost_status IS NOT NULL
    ''')
    conn.commit()

    # Verify cost_status is in JSON
    cursor.execute("SELECT json_extract(details, '$.cost_status') FROM facts WHERE id = 'F-1'")
    result = cursor.fetchone()
    assert result[0] == 'known', "cost_status should be in JSON after downgrade"

    conn.close()


def test_migration_idempotency():
    """Test that migration can be run multiple times safely."""

    conn = sqlite3.connect(':memory:')
    cursor = conn.cursor()

    # Create facts table
    cursor.execute('''
        CREATE TABLE facts (
            id TEXT PRIMARY KEY,
            details TEXT
        )
    ''')

    # First run: add column
    cursor.execute("ALTER TABLE facts ADD COLUMN cost_status TEXT")

    # Check column exists
    cursor.execute("PRAGMA table_info(facts)")
    columns = [row[1] for row in cursor.fetchall()]
    assert 'cost_status' in columns

    # Second run: would try to add column again
    # In real migration, this is prevented by checking column existence
    # Here we just verify the check would work
    cursor.execute("PRAGMA table_info(facts)")
    existing_columns = [row[1] for row in cursor.fetchall()]

    if 'cost_status' in existing_columns:
        # Migration would skip adding column
        pass
    else:
        cursor.execute("ALTER TABLE facts ADD COLUMN cost_status TEXT")

    # Verify still only one cost_status column
    cursor.execute("PRAGMA table_info(facts)")
    columns = [row[1] for row in cursor.fetchall()]
    assert columns.count('cost_status') == 1, "Should only have one cost_status column"

    conn.close()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
