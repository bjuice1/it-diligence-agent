#!/usr/bin/env python3
"""
Deal Isolation Migration Script

Migrates existing JSON data files to include deal_id for proper data isolation.
This is Phase 1 of the IT Due Diligence tool fixes.

Changes made:
- Adds deal_id field to all facts, gaps, inventory items, and documents
- Updates schema version to 2.0
- Creates backups before migration

Usage:
    python scripts/migrate_deal_isolation.py [--dry-run] [--deal-id DEAL_ID] [--data-dir PATH]

Options:
    --dry-run       Show what would be migrated without actually doing it
    --deal-id       Deal ID to assign to legacy data (default: "legacy-deal")
    --data-dir      Directory containing data files (default: output/)
"""

import os
import sys
import json
import shutil
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Tuple

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class MigrationProgress:
    """Track migration progress."""

    def __init__(self):
        self.started_at = datetime.utcnow()
        self.stats = {
            'fact_stores': {'found': 0, 'migrated': 0, 'skipped': 0, 'errors': 0},
            'facts': {'found': 0, 'updated': 0, 'already_has_deal_id': 0},
            'gaps': {'found': 0, 'updated': 0, 'already_has_deal_id': 0},
            'open_questions': {'found': 0, 'updated': 0, 'already_has_deal_id': 0},
            'inventory_stores': {'found': 0, 'migrated': 0, 'skipped': 0, 'errors': 0},
            'inventory_items': {'found': 0, 'updated': 0, 'already_has_deal_id': 0},
            'document_stores': {'found': 0, 'migrated': 0, 'skipped': 0, 'errors': 0},
            'documents': {'found': 0, 'updated': 0, 'already_has_deal_id': 0},
        }
        self.errors: List[str] = []
        self.backups: List[str] = []

    def record_file(self, file_type: str, status: str):
        if file_type in self.stats:
            self.stats[file_type][status] += 1

    def record_item(self, item_type: str, status: str, count: int = 1):
        if item_type in self.stats:
            self.stats[item_type][status] += count

    def add_error(self, message: str):
        self.errors.append(message)

    def add_backup(self, path: str):
        self.backups.append(path)

    def print_summary(self):
        print("\n" + "=" * 60)
        print("DEAL ISOLATION MIGRATION SUMMARY")
        print("=" * 60)

        # File statistics
        for file_type in ['fact_stores', 'inventory_stores', 'document_stores']:
            counts = self.stats[file_type]
            print(f"\n{file_type.replace('_', ' ').upper()}:")
            print(f"  Found:    {counts['found']}")
            print(f"  Migrated: {counts['migrated']}")
            print(f"  Skipped:  {counts['skipped']}")
            print(f"  Errors:   {counts['errors']}")

        # Item statistics
        print("\nITEMS UPDATED:")
        for item_type in ['facts', 'gaps', 'open_questions', 'inventory_items', 'documents']:
            counts = self.stats[item_type]
            print(f"  {item_type}: {counts['updated']} updated, "
                  f"{counts['already_has_deal_id']} already had deal_id")

        # Backups
        if self.backups:
            print(f"\nBACKUPS CREATED: {len(self.backups)}")

        # Errors
        if self.errors:
            print(f"\n{len(self.errors)} ERRORS:")
            for err in self.errors[:10]:
                print(f"  - {err}")
            if len(self.errors) > 10:
                print(f"  ... and {len(self.errors) - 10} more")

        elapsed = datetime.utcnow() - self.started_at
        print(f"\nCompleted in {elapsed.total_seconds():.2f} seconds")


def create_backup(file_path: Path, progress: MigrationProgress) -> bool:
    """Create a backup of a file before migration."""
    backup_path = file_path.with_suffix(f'.pre-deal-isolation-{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
    try:
        shutil.copy2(file_path, backup_path)
        progress.add_backup(str(backup_path))
        return True
    except Exception as e:
        progress.add_error(f"Failed to backup {file_path}: {e}")
        return False


def migrate_fact_store(
    file_path: Path,
    deal_id: str,
    progress: MigrationProgress,
    dry_run: bool = False
) -> bool:
    """Migrate a fact store JSON file to include deal_id."""
    progress.record_file('fact_stores', 'found')

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Check current version
        metadata = data.get('metadata', {})
        current_version = metadata.get('version', '1.0')

        # Skip if already migrated (version >= 2.0)
        if current_version >= '2.2':
            progress.record_file('fact_stores', 'skipped')
            print(f"  Skipping {file_path.name} - already at version {current_version}")
            return True

        # Track updates
        facts_updated = 0
        facts_has_deal_id = 0
        gaps_updated = 0
        gaps_has_deal_id = 0
        questions_updated = 0
        questions_has_deal_id = 0

        # Update facts
        for fact in data.get('facts', []):
            progress.record_item('facts', 'found')
            if not fact.get('deal_id'):
                fact['deal_id'] = deal_id
                facts_updated += 1
            else:
                facts_has_deal_id += 1

        # Update gaps
        for gap in data.get('gaps', []):
            progress.record_item('gaps', 'found')
            if not gap.get('deal_id'):
                gap['deal_id'] = deal_id
                gaps_updated += 1
            else:
                gaps_has_deal_id += 1

        # Update open questions
        for question in data.get('open_questions', []):
            progress.record_item('open_questions', 'found')
            if not question.get('deal_id'):
                question['deal_id'] = deal_id
                questions_updated += 1
            else:
                questions_has_deal_id += 1

        # Update metadata
        metadata['version'] = '2.2'
        metadata['deal_id'] = deal_id
        metadata['migrated_at'] = datetime.now().isoformat()
        data['metadata'] = metadata

        progress.record_item('facts', 'updated', facts_updated)
        progress.record_item('facts', 'already_has_deal_id', facts_has_deal_id)
        progress.record_item('gaps', 'updated', gaps_updated)
        progress.record_item('gaps', 'already_has_deal_id', gaps_has_deal_id)
        progress.record_item('open_questions', 'updated', questions_updated)
        progress.record_item('open_questions', 'already_has_deal_id', questions_has_deal_id)

        if dry_run:
            print(f"  [DRY RUN] Would update {file_path.name}: "
                  f"{facts_updated} facts, {gaps_updated} gaps, {questions_updated} questions")
            progress.record_file('fact_stores', 'migrated')
            return True

        # Create backup
        if not create_backup(file_path, progress):
            return False

        # Write updated file
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"  Migrated {file_path.name}: "
              f"{facts_updated} facts, {gaps_updated} gaps, {questions_updated} questions")
        progress.record_file('fact_stores', 'migrated')
        return True

    except Exception as e:
        progress.add_error(f"Failed to migrate {file_path}: {e}")
        progress.record_file('fact_stores', 'errors')
        return False


def migrate_inventory_store(
    file_path: Path,
    deal_id: str,
    progress: MigrationProgress,
    dry_run: bool = False
) -> bool:
    """Migrate an inventory store JSON file to include deal_id."""
    progress.record_file('inventory_stores', 'found')

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Check current version
        metadata = data.get('metadata', {})
        current_version = metadata.get('version', '1.0')

        # Skip if already migrated
        if current_version >= '2.0':
            progress.record_file('inventory_stores', 'skipped')
            print(f"  Skipping {file_path.name} - already at version {current_version}")
            return True

        # Track updates
        items_updated = 0
        items_has_deal_id = 0

        # Update inventory items
        for item in data.get('items', []):
            progress.record_item('inventory_items', 'found')
            if not item.get('deal_id'):
                item['deal_id'] = deal_id
                items_updated += 1
            else:
                items_has_deal_id += 1

        # Update metadata
        metadata['version'] = '2.0'
        metadata['deal_id'] = deal_id
        metadata['migrated_at'] = datetime.now().isoformat()
        data['metadata'] = metadata

        progress.record_item('inventory_items', 'updated', items_updated)
        progress.record_item('inventory_items', 'already_has_deal_id', items_has_deal_id)

        if dry_run:
            print(f"  [DRY RUN] Would update {file_path.name}: {items_updated} items")
            progress.record_file('inventory_stores', 'migrated')
            return True

        # Create backup
        if not create_backup(file_path, progress):
            return False

        # Write updated file
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"  Migrated {file_path.name}: {items_updated} items")
        progress.record_file('inventory_stores', 'migrated')
        return True

    except Exception as e:
        progress.add_error(f"Failed to migrate {file_path}: {e}")
        progress.record_file('inventory_stores', 'errors')
        return False


def migrate_document_store(
    file_path: Path,
    deal_id: str,
    progress: MigrationProgress,
    dry_run: bool = False
) -> bool:
    """Migrate a document store JSON file to include deal_id."""
    progress.record_file('document_stores', 'found')

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Check current version
        metadata = data.get('metadata', {})
        current_version = metadata.get('version', '1.0')

        # Skip if already migrated
        if current_version >= '2.0':
            progress.record_file('document_stores', 'skipped')
            print(f"  Skipping {file_path.name} - already at version {current_version}")
            return True

        # Track updates
        docs_updated = 0
        docs_has_deal_id = 0

        # Update documents
        for doc in data.get('documents', []):
            progress.record_item('documents', 'found')
            if not doc.get('deal_id'):
                doc['deal_id'] = deal_id
                docs_updated += 1
            else:
                docs_has_deal_id += 1

        # Update metadata
        metadata['version'] = '2.0'
        metadata['deal_id'] = deal_id
        metadata['migrated_at'] = datetime.now().isoformat()
        data['metadata'] = metadata

        progress.record_item('documents', 'updated', docs_updated)
        progress.record_item('documents', 'already_has_deal_id', docs_has_deal_id)

        if dry_run:
            print(f"  [DRY RUN] Would update {file_path.name}: {docs_updated} documents")
            progress.record_file('document_stores', 'migrated')
            return True

        # Create backup
        if not create_backup(file_path, progress):
            return False

        # Write updated file
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"  Migrated {file_path.name}: {docs_updated} documents")
        progress.record_file('document_stores', 'migrated')
        return True

    except Exception as e:
        progress.add_error(f"Failed to migrate {file_path}: {e}")
        progress.record_file('document_stores', 'errors')
        return False


def find_data_files(data_dir: Path) -> Dict[str, List[Path]]:
    """Find all data files that need migration."""
    files = {
        'fact_stores': [],
        'inventory_stores': [],
        'document_stores': [],
    }

    # Search patterns for different file types
    patterns = {
        'fact_stores': ['**/fact_store*.json', '**/facts*.json'],
        'inventory_stores': ['**/inventory_store*.json', '**/inventory*.json'],
        'document_stores': ['**/document_store*.json', '**/documents*.json'],
    }

    for file_type, globs in patterns.items():
        for pattern in globs:
            for file_path in data_dir.glob(pattern):
                if file_path.is_file() and 'backup' not in file_path.name.lower():
                    if file_path not in files[file_type]:
                        files[file_type].append(file_path)

    return files


def main():
    parser = argparse.ArgumentParser(description='Migrate data files for deal isolation')
    parser.add_argument('--dry-run', action='store_true',
                        help='Show what would be migrated without actually doing it')
    parser.add_argument('--deal-id', default='legacy-deal',
                        help='Deal ID to assign to legacy data (default: legacy-deal)')
    parser.add_argument('--data-dir', type=Path, default=project_root / 'output',
                        help='Directory containing data files (default: output/)')
    args = parser.parse_args()

    print("=" * 60)
    print("DEAL ISOLATION MIGRATION")
    print("=" * 60)
    print(f"Data directory: {args.data_dir}")
    print(f"Deal ID: {args.deal_id}")
    print(f"Dry run: {args.dry_run}")
    print()

    if not args.data_dir.exists():
        print(f"Data directory not found: {args.data_dir}")
        print("Nothing to migrate.")
        return 0

    progress = MigrationProgress()

    # Find all data files
    print("Scanning for data files...")
    files = find_data_files(args.data_dir)

    total_files = sum(len(f) for f in files.values())
    if total_files == 0:
        print("No data files found to migrate.")
        return 0

    print(f"Found {total_files} files to check")
    print()

    # Migrate fact stores
    if files['fact_stores']:
        print("Migrating fact stores...")
        for file_path in files['fact_stores']:
            migrate_fact_store(file_path, args.deal_id, progress, args.dry_run)

    # Migrate inventory stores
    if files['inventory_stores']:
        print("\nMigrating inventory stores...")
        for file_path in files['inventory_stores']:
            migrate_inventory_store(file_path, args.deal_id, progress, args.dry_run)

    # Migrate document stores
    if files['document_stores']:
        print("\nMigrating document stores...")
        for file_path in files['document_stores']:
            migrate_document_store(file_path, args.deal_id, progress, args.dry_run)

    # Print summary
    progress.print_summary()

    if args.dry_run:
        print("\n[DRY RUN] No files were actually modified.")

    return 0 if not progress.errors else 1


if __name__ == '__main__':
    sys.exit(main())
