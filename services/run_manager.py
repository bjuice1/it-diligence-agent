"""
Run Output Manager

Manages analysis runs with organized output directories.
Each run gets a timestamped folder containing all outputs.

Phase B: Points 21-40 of cleanup plan.
"""

import os
import json
import shutil
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict

logger = logging.getLogger(__name__)


@dataclass
class RunMetadata:
    """Metadata for an analysis run."""
    run_id: str
    created_at: str
    target_name: str = ""
    buyer_name: str = ""
    deal_type: str = ""
    domains_analyzed: List[str] = field(default_factory=list)
    document_count: int = 0
    facts_count: int = 0
    risks_count: int = 0
    work_items_count: int = 0
    gaps_count: int = 0
    status: str = "in_progress"  # in_progress, completed, archived
    completed_at: str = ""
    notes: str = ""

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> 'RunMetadata':
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class RunPaths:
    """Paths within a run directory."""
    root: Path
    facts: Path
    findings: Path
    logs: Path
    reports: Path
    exports: Path
    documents: Path

    def ensure_all(self):
        """Create all directories."""
        for path in [self.root, self.facts, self.findings, self.logs,
                     self.reports, self.exports, self.documents]:
            path.mkdir(parents=True, exist_ok=True)


class RunOutputManager:
    """
    Manages analysis run outputs in organized directories.

    Directory structure:
        output/
        ├── runs/
        │   ├── 2026-01-28_143052_target-name/
        │   │   ├── metadata.json
        │   │   ├── facts/
        │   │   │   └── facts.json
        │   │   ├── findings/
        │   │   │   └── findings.json
        │   │   ├── logs/
        │   │   │   └── analysis.log
        │   │   ├── reports/
        │   │   │   ├── it_dd_report.html
        │   │   │   └── executive_summary.md
        │   │   ├── exports/
        │   │   │   ├── applications.xlsx
        │   │   │   ├── dossiers/
        │   │   │   └── ...
        │   │   └── documents/
        │   │       └── (copied/linked source docs)
        │   ├── 2026-01-27_091523_other-deal/
        │   │   └── ...
        │   └── latest -> 2026-01-28_143052_target-name/
        ├── documents/   (upload staging area)
        └── archive/     (archived runs)
    """

    def __init__(self, output_dir: Path = None):
        """
        Initialize RunOutputManager.

        Args:
            output_dir: Base output directory. Defaults to config OUTPUT_DIR.
        """
        if output_dir is None:
            from config_v2 import OUTPUT_DIR
            output_dir = OUTPUT_DIR

        self.output_dir = Path(output_dir)
        self.runs_dir = self.output_dir / "runs"
        self.archive_dir = self.output_dir / "archive" / "runs"
        self.latest_pointer = self.runs_dir / "latest"

        # Ensure base directories exist
        self.runs_dir.mkdir(parents=True, exist_ok=True)

    def create_run_directory(self, target_name: str = "", deal_type: str = "") -> RunPaths:
        """
        Create a new run directory with timestamp.

        Args:
            target_name: Name of target company (for folder naming)
            deal_type: Type of deal (acquisition, carve-out, etc.)

        Returns:
            RunPaths with all directory paths
        """
        timestamp = datetime.now().strftime('%Y-%m-%d_%H%M%S')

        # Sanitize target name for directory
        safe_name = self._sanitize_name(target_name) if target_name else "analysis"

        run_id = f"{timestamp}_{safe_name}"
        run_dir = self.runs_dir / run_id

        # Create paths
        paths = RunPaths(
            root=run_dir,
            facts=run_dir / "facts",
            findings=run_dir / "findings",
            logs=run_dir / "logs",
            reports=run_dir / "reports",
            exports=run_dir / "exports",
            documents=run_dir / "documents"
        )

        # Create all directories
        paths.ensure_all()

        # Create initial metadata
        metadata = RunMetadata(
            run_id=run_id,
            created_at=datetime.now().isoformat(),
            target_name=target_name,
            deal_type=deal_type,
            status="in_progress"
        )
        self._save_metadata(run_dir, metadata)

        # Update latest pointer
        self.save_latest_pointer(run_id)

        logger.info(f"Created run directory: {run_id}")
        return paths

    def get_run_paths(self, run_id: str = None) -> Optional[RunPaths]:
        """
        Get paths for a specific run or latest run.

        Args:
            run_id: Run ID or None for latest

        Returns:
            RunPaths or None if not found
        """
        if run_id is None:
            run_id = self.get_latest_run()
            if run_id is None:
                return None

        run_dir = self.runs_dir / run_id
        if not run_dir.exists():
            logger.warning(f"Run directory not found: {run_id}")
            return None

        return RunPaths(
            root=run_dir,
            facts=run_dir / "facts",
            findings=run_dir / "findings",
            logs=run_dir / "logs",
            reports=run_dir / "reports",
            exports=run_dir / "exports",
            documents=run_dir / "documents"
        )

    def save_latest_pointer(self, run_id: str):
        """
        Update the 'latest' pointer to point to a run.

        Args:
            run_id: Run ID to point to
        """
        # Write run_id to a file (cross-platform compatible)
        pointer_file = self.runs_dir / ".latest"
        pointer_file.write_text(run_id)

        # Also try to create/update symlink (Unix only)
        try:
            if self.latest_pointer.is_symlink():
                self.latest_pointer.unlink()
            elif self.latest_pointer.exists():
                self.latest_pointer.unlink()
            self.latest_pointer.symlink_to(run_id)
        except (OSError, NotImplementedError):
            # Symlinks not supported on this platform
            pass

        logger.debug(f"Updated latest pointer to: {run_id}")

    def get_latest_run(self) -> Optional[str]:
        """
        Get the ID of the latest run.

        Returns:
            Run ID or None if no runs exist
        """
        # Try reading from pointer file first
        pointer_file = self.runs_dir / ".latest"
        if pointer_file.exists():
            run_id = pointer_file.read_text().strip()
            if (self.runs_dir / run_id).exists():
                return run_id

        # Try symlink
        if self.latest_pointer.is_symlink():
            target = self.latest_pointer.resolve()
            if target.exists():
                return target.name

        # Fallback: find most recent run by timestamp
        runs = self.list_runs()
        if runs:
            return runs[0]['run_id']

        return None

    def list_runs(self, include_archived: bool = False) -> List[Dict]:
        """
        List all runs sorted by date (newest first).

        Args:
            include_archived: Whether to include archived runs

        Returns:
            List of run metadata dicts
        """
        runs = []

        # Active runs
        if self.runs_dir.exists():
            for item in self.runs_dir.iterdir():
                if item.is_dir() and not item.name.startswith('.') and item.name != 'latest':
                    metadata = self._load_metadata(item)
                    if metadata:
                        runs.append(metadata.to_dict())
                    else:
                        # Create basic metadata from directory name
                        runs.append({
                            'run_id': item.name,
                            'created_at': self._parse_timestamp_from_name(item.name),
                            'status': 'unknown'
                        })

        # Archived runs
        if include_archived and self.archive_dir.exists():
            for item in self.archive_dir.iterdir():
                if item.is_dir():
                    metadata = self._load_metadata(item)
                    if metadata:
                        meta_dict = metadata.to_dict()
                        meta_dict['archived'] = True
                        runs.append(meta_dict)

        # Sort by created_at descending
        runs.sort(key=lambda x: x.get('created_at', ''), reverse=True)

        return runs

    def archive_run(self, run_id: str) -> bool:
        """
        Move a run to the archive directory.

        Args:
            run_id: Run ID to archive

        Returns:
            True if successful
        """
        run_dir = self.runs_dir / run_id
        if not run_dir.exists():
            logger.warning(f"Run not found for archiving: {run_id}")
            return False

        # Update metadata
        metadata = self._load_metadata(run_dir)
        if metadata:
            metadata.status = "archived"
            self._save_metadata(run_dir, metadata)

        # Create archive directory
        self.archive_dir.mkdir(parents=True, exist_ok=True)

        # Move to archive
        archive_path = self.archive_dir / run_id
        shutil.move(str(run_dir), str(archive_path))

        # Update latest pointer if needed
        if self.get_latest_run() == run_id:
            runs = self.list_runs()
            if runs:
                self.save_latest_pointer(runs[0]['run_id'])

        logger.info(f"Archived run: {run_id}")
        return True

    def delete_run(self, run_id: str, confirm: bool = False) -> bool:
        """
        Permanently delete a run.

        Args:
            run_id: Run ID to delete
            confirm: Must be True to actually delete

        Returns:
            True if successful
        """
        if not confirm:
            logger.warning("Delete requires confirm=True")
            return False

        # Check active runs
        run_dir = self.runs_dir / run_id
        if run_dir.exists():
            shutil.rmtree(run_dir)
            logger.info(f"Deleted run: {run_id}")
            return True

        # Check archive
        archive_path = self.archive_dir / run_id
        if archive_path.exists():
            shutil.rmtree(archive_path)
            logger.info(f"Deleted archived run: {run_id}")
            return True

        logger.warning(f"Run not found for deletion: {run_id}")
        return False

    def get_run_metadata(self, run_id: str = None) -> Optional[RunMetadata]:
        """
        Get metadata for a run.

        Args:
            run_id: Run ID or None for latest

        Returns:
            RunMetadata or None
        """
        if run_id is None:
            run_id = self.get_latest_run()
            if run_id is None:
                return None

        run_dir = self.runs_dir / run_id
        if not run_dir.exists():
            # Check archive
            run_dir = self.archive_dir / run_id
            if not run_dir.exists():
                return None

        return self._load_metadata(run_dir)

    def update_run_metadata(self, run_id: str, **kwargs) -> bool:
        """
        Update metadata for a run.

        Args:
            run_id: Run ID
            **kwargs: Fields to update

        Returns:
            True if successful
        """
        paths = self.get_run_paths(run_id)
        if paths is None:
            return False

        metadata = self._load_metadata(paths.root)
        if metadata is None:
            metadata = RunMetadata(run_id=run_id, created_at=datetime.now().isoformat())

        # Update fields
        for key, value in kwargs.items():
            if hasattr(metadata, key):
                setattr(metadata, key, value)

        self._save_metadata(paths.root, metadata)
        return True

    def complete_run(self, run_id: str = None,
                     facts_count: int = 0,
                     risks_count: int = 0,
                     work_items_count: int = 0,
                     gaps_count: int = 0) -> bool:
        """
        Mark a run as completed and update counts.

        Args:
            run_id: Run ID or None for latest
            facts_count: Number of facts extracted
            risks_count: Number of risks identified
            work_items_count: Number of work items
            gaps_count: Number of information gaps

        Returns:
            True if successful
        """
        if run_id is None:
            run_id = self.get_latest_run()
            if run_id is None:
                return False

        return self.update_run_metadata(
            run_id,
            status="completed",
            completed_at=datetime.now().isoformat(),
            facts_count=facts_count,
            risks_count=risks_count,
            work_items_count=work_items_count,
            gaps_count=gaps_count
        )

    def get_run_stats(self, run_id: str = None) -> Dict:
        """
        Get statistics for a run.

        Args:
            run_id: Run ID or None for latest

        Returns:
            Dict with stats
        """
        paths = self.get_run_paths(run_id)
        if paths is None:
            return {}

        stats = {
            'run_id': run_id or self.get_latest_run(),
            'facts_files': len(list(paths.facts.glob('*.json'))) if paths.facts.exists() else 0,
            'findings_files': len(list(paths.findings.glob('*.json'))) if paths.findings.exists() else 0,
            'report_files': len(list(paths.reports.glob('*'))) if paths.reports.exists() else 0,
            'export_files': len(list(paths.exports.glob('*'))) if paths.exports.exists() else 0,
            'log_files': len(list(paths.logs.glob('*'))) if paths.logs.exists() else 0,
        }

        # Calculate total size
        total_size = 0
        for path in [paths.facts, paths.findings, paths.reports, paths.exports, paths.logs]:
            if path.exists():
                for file in path.rglob('*'):
                    if file.is_file():
                        total_size += file.stat().st_size
        stats['total_size_mb'] = round(total_size / (1024 * 1024), 2)

        return stats

    # =========================================================================
    # Helper Methods
    # =========================================================================

    def _sanitize_name(self, name: str) -> str:
        """Sanitize a name for use in directory names."""
        # Replace spaces and special chars with hyphens
        import re
        safe = re.sub(r'[^\w\-]', '-', name.lower())
        safe = re.sub(r'-+', '-', safe)  # Collapse multiple hyphens
        safe = safe.strip('-')
        return safe[:50] if safe else "unnamed"

    def _parse_timestamp_from_name(self, name: str) -> str:
        """Try to parse timestamp from run directory name."""
        # Expected format: 2026-01-28_143052_...
        try:
            parts = name.split('_')
            if len(parts) >= 2:
                date_part = parts[0]
                time_part = parts[1]
                dt = datetime.strptime(f"{date_part}_{time_part}", '%Y-%m-%d_%H%M%S')
                return dt.isoformat()
        except:
            pass
        return ""

    def _save_metadata(self, run_dir: Path, metadata: RunMetadata):
        """Save metadata to run directory."""
        metadata_file = run_dir / "metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(metadata.to_dict(), f, indent=2)

    def _load_metadata(self, run_dir: Path) -> Optional[RunMetadata]:
        """Load metadata from run directory."""
        metadata_file = run_dir / "metadata.json"
        if not metadata_file.exists():
            return None
        try:
            with open(metadata_file) as f:
                data = json.load(f)
            return RunMetadata.from_dict(data)
        except Exception as e:
            logger.warning(f"Failed to load metadata from {run_dir}: {e}")
            return None


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

_run_manager: Optional[RunOutputManager] = None

def get_run_manager() -> RunOutputManager:
    """Get or create the global RunOutputManager instance."""
    global _run_manager
    if _run_manager is None:
        _run_manager = RunOutputManager()
    return _run_manager


def create_new_run(target_name: str = "", deal_type: str = "") -> RunPaths:
    """Create a new run and return its paths."""
    return get_run_manager().create_run_directory(target_name, deal_type)


def get_current_run_paths() -> Optional[RunPaths]:
    """Get paths for the current (latest) run."""
    return get_run_manager().get_run_paths()


def get_latest_run_id() -> Optional[str]:
    """Get the ID of the latest run."""
    return get_run_manager().get_latest_run()
