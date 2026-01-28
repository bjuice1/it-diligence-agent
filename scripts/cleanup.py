#!/usr/bin/env python3
"""
Cleanup Script for IT Due Diligence Agent

Removes old analysis runs, cleans up temporary files, and manages storage.
"""

import argparse
import shutil
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config_v2 import OUTPUT_DIR, UPLOADS_DIR


def get_run_age_days(run_dir: Path) -> int:
    """Get the age of a run directory in days."""
    try:
        # Parse timestamp from directory name (YYYY-MM-DD_HHMMSS_name)
        name = run_dir.name
        date_str = name.split('_')[0]
        time_str = name.split('_')[1]
        dt = datetime.strptime(f"{date_str}_{time_str}", '%Y-%m-%d_%H%M%S')
        return (datetime.now() - dt).days
    except (ValueError, IndexError):
        return 0


def cleanup_old_runs(days: int = 30, dry_run: bool = True) -> list:
    """
    Remove analysis runs older than specified days.

    Args:
        days: Remove runs older than this many days
        dry_run: If True, only report what would be deleted

    Returns:
        List of removed/would-be-removed directories
    """
    runs_dir = OUTPUT_DIR / "runs"
    removed = []

    if not runs_dir.exists():
        print(f"Runs directory not found: {runs_dir}")
        return removed

    for run_dir in runs_dir.iterdir():
        if not run_dir.is_dir() or run_dir.name.startswith('.'):
            continue
        if run_dir.name == 'latest':
            continue

        age = get_run_age_days(run_dir)
        if age > days:
            removed.append(run_dir)
            if dry_run:
                print(f"[DRY RUN] Would remove: {run_dir.name} ({age} days old)")
            else:
                print(f"Removing: {run_dir.name} ({age} days old)")
                shutil.rmtree(run_dir)

    return removed


def cleanup_extracted_text(dry_run: bool = True) -> int:
    """
    Remove extracted text files for documents that no longer exist.

    Returns:
        Count of removed files
    """
    count = 0

    for entity in ['target', 'buyer']:
        extracted_dir = UPLOADS_DIR / entity / "extracted"
        if not extracted_dir.exists():
            continue

        for txt_file in extracted_dir.glob("*.txt"):
            # Check if corresponding document exists in manifest
            # For now, just report orphaned files
            if dry_run:
                print(f"[DRY RUN] Found extracted file: {txt_file.name}")
            count += 1

    return count


def cleanup_pycache(dry_run: bool = True) -> int:
    """
    Remove __pycache__ directories.

    Returns:
        Count of removed directories
    """
    base_dir = Path(__file__).parent.parent
    count = 0

    for pycache in base_dir.rglob("__pycache__"):
        if pycache.is_dir():
            count += 1
            if dry_run:
                print(f"[DRY RUN] Would remove: {pycache}")
            else:
                print(f"Removing: {pycache}")
                shutil.rmtree(pycache)

    return count


def cleanup_ds_store(dry_run: bool = True) -> int:
    """
    Remove .DS_Store files (macOS).

    Returns:
        Count of removed files
    """
    base_dir = Path(__file__).parent.parent
    count = 0

    for ds_store in base_dir.rglob(".DS_Store"):
        if ds_store.is_file():
            count += 1
            if dry_run:
                print(f"[DRY RUN] Would remove: {ds_store}")
            else:
                print(f"Removing: {ds_store}")
                ds_store.unlink()

    return count


def get_storage_stats() -> dict:
    """Get storage usage statistics."""
    stats = {
        'uploads': 0,
        'output': 0,
        'runs': 0,
        'run_count': 0,
    }

    def dir_size(path: Path) -> int:
        if not path.exists():
            return 0
        return sum(f.stat().st_size for f in path.rglob('*') if f.is_file())

    stats['uploads'] = dir_size(UPLOADS_DIR)
    stats['output'] = dir_size(OUTPUT_DIR)

    runs_dir = OUTPUT_DIR / "runs"
    if runs_dir.exists():
        stats['runs'] = dir_size(runs_dir)
        stats['run_count'] = len([d for d in runs_dir.iterdir()
                                   if d.is_dir() and not d.name.startswith('.')])

    return stats


def format_size(bytes: int) -> str:
    """Format bytes as human-readable string."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes < 1024:
            return f"{bytes:.1f} {unit}"
        bytes /= 1024
    return f"{bytes:.1f} TB"


def main():
    parser = argparse.ArgumentParser(
        description="Cleanup script for IT Due Diligence Agent"
    )
    parser.add_argument(
        '--runs', type=int, metavar='DAYS',
        help='Remove runs older than DAYS days'
    )
    parser.add_argument(
        '--pycache', action='store_true',
        help='Remove __pycache__ directories'
    )
    parser.add_argument(
        '--ds-store', action='store_true',
        help='Remove .DS_Store files'
    )
    parser.add_argument(
        '--all', action='store_true',
        help='Run all cleanup tasks (30 days for runs)'
    )
    parser.add_argument(
        '--stats', action='store_true',
        help='Show storage statistics only'
    )
    parser.add_argument(
        '--execute', action='store_true',
        help='Actually perform deletions (default is dry run)'
    )

    args = parser.parse_args()
    dry_run = not args.execute

    if args.stats or not any([args.runs, args.pycache, args.ds_store, args.all]):
        print("\n=== Storage Statistics ===")
        stats = get_storage_stats()
        print(f"Uploads:     {format_size(stats['uploads'])}")
        print(f"Output:      {format_size(stats['output'])}")
        print(f"Runs:        {format_size(stats['runs'])} ({stats['run_count']} runs)")
        print(f"Total:       {format_size(stats['uploads'] + stats['output'])}")

        if args.stats:
            return

        print("\nRun with --help for cleanup options")
        return

    if dry_run:
        print("=== DRY RUN MODE (use --execute to perform deletions) ===\n")

    if args.runs or args.all:
        days = args.runs or 30
        print(f"\n--- Cleaning runs older than {days} days ---")
        removed = cleanup_old_runs(days, dry_run)
        print(f"{'Would remove' if dry_run else 'Removed'}: {len(removed)} runs")

    if args.pycache or args.all:
        print("\n--- Cleaning __pycache__ directories ---")
        count = cleanup_pycache(dry_run)
        print(f"{'Would remove' if dry_run else 'Removed'}: {count} directories")

    if args.ds_store or args.all:
        print("\n--- Cleaning .DS_Store files ---")
        count = cleanup_ds_store(dry_run)
        print(f"{'Would remove' if dry_run else 'Removed'}: {count} files")

    print("\n=== Cleanup Complete ===")
    if dry_run:
        print("Run with --execute to perform actual deletions")


if __name__ == "__main__":
    main()
