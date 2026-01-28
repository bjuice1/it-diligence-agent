"""
Analysis Integration Service

Integrates the run manager with the analysis pipeline.
When analysis starts, creates a run directory and routes all outputs there.

Phase B: Points 27-34 of cleanup plan.
"""

import logging
from pathlib import Path
from typing import Dict, Optional, Any
from datetime import datetime

from services.run_manager import get_run_manager, RunPaths, RunOutputManager

logger = logging.getLogger(__name__)


class AnalysisRun:
    """
    Context manager for an analysis run.

    Creates a run directory and provides paths for all outputs.
    Automatically saves metadata on completion.

    Usage:
        with AnalysisRun(target_name="Acme Corp") as run:
            # run.paths has all the directories
            fact_store.save(str(run.paths.facts / "facts.json"))
            generate_html_report(..., output_dir=run.paths.reports)

        # On exit, run metadata is updated with completion status
    """

    def __init__(
        self,
        target_name: str = "",
        deal_type: str = "",
        run_id: str = None
    ):
        """
        Initialize an analysis run.

        Args:
            target_name: Name of target company
            deal_type: Type of deal (acquisition, carve-out, etc.)
            run_id: Existing run ID to resume, or None to create new
        """
        self.target_name = target_name
        self.deal_type = deal_type
        self.run_id = run_id
        self.manager = get_run_manager()
        self.paths: Optional[RunPaths] = None
        self._started = False
        self._facts_count = 0
        self._risks_count = 0
        self._work_items_count = 0
        self._gaps_count = 0

    def __enter__(self) -> "AnalysisRun":
        """Start the analysis run."""
        if self.run_id:
            # Resume existing run
            self.paths = self.manager.get_run_paths(self.run_id)
            if self.paths is None:
                raise ValueError(f"Run not found: {self.run_id}")
        else:
            # Create new run
            self.paths = self.manager.create_run_directory(
                target_name=self.target_name,
                deal_type=self.deal_type
            )
            self.run_id = self.paths.root.name

        self._started = True
        logger.info(f"Started analysis run: {self.run_id}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Complete the analysis run."""
        if exc_type is None:
            # Success - mark as completed
            self.manager.complete_run(
                self.run_id,
                facts_count=self._facts_count,
                risks_count=self._risks_count,
                work_items_count=self._work_items_count,
                gaps_count=self._gaps_count
            )
            logger.info(f"Completed analysis run: {self.run_id}")
        else:
            # Error - keep as in_progress
            logger.error(f"Analysis run {self.run_id} failed: {exc_val}")
            self.manager.update_run_metadata(
                self.run_id,
                notes=f"Error: {exc_val}"
            )
        return False  # Don't suppress exceptions

    def set_counts(
        self,
        facts: int = 0,
        risks: int = 0,
        work_items: int = 0,
        gaps: int = 0
    ):
        """Update the counts for this run."""
        self._facts_count = facts
        self._risks_count = risks
        self._work_items_count = work_items
        self._gaps_count = gaps

    @property
    def facts_path(self) -> Path:
        """Path for facts files."""
        return self.paths.facts

    @property
    def findings_path(self) -> Path:
        """Path for findings files."""
        return self.paths.findings

    @property
    def reports_path(self) -> Path:
        """Path for report files."""
        return self.paths.reports

    @property
    def logs_path(self) -> Path:
        """Path for log files."""
        return self.paths.logs

    @property
    def exports_path(self) -> Path:
        """Path for export files."""
        return self.paths.exports


def create_analysis_run(
    target_name: str = "",
    deal_type: str = ""
) -> AnalysisRun:
    """
    Create a new analysis run.

    This is the main entry point for starting an analysis.

    Args:
        target_name: Name of target company
        deal_type: Type of deal

    Returns:
        AnalysisRun context manager
    """
    return AnalysisRun(target_name=target_name, deal_type=deal_type)


def get_current_run_paths() -> Optional[RunPaths]:
    """Get paths for the current (latest) run."""
    return get_run_manager().get_run_paths()


def get_run_log_dir(run_id: str = None) -> Path:
    """
    Get the log directory for a run.

    Used by DiscoveryLogger and other components that need to log.

    Args:
        run_id: Run ID or None for latest

    Returns:
        Path to logs directory
    """
    paths = get_run_manager().get_run_paths(run_id)
    if paths:
        return paths.logs
    # Fallback to default
    from config_v2 import OUTPUT_DIR
    return OUTPUT_DIR / "logs"


def get_run_report_dir(run_id: str = None) -> Path:
    """
    Get the reports directory for a run.

    Used by HTML report generator and other report components.

    Args:
        run_id: Run ID or None for latest

    Returns:
        Path to reports directory
    """
    paths = get_run_manager().get_run_paths(run_id)
    if paths:
        return paths.reports
    # Fallback to default
    from config_v2 import OUTPUT_DIR
    return OUTPUT_DIR


def get_run_exports_dir(run_id: str = None) -> Path:
    """
    Get the exports directory for a run.

    Used by export services.

    Args:
        run_id: Run ID or None for latest

    Returns:
        Path to exports directory
    """
    paths = get_run_manager().get_run_paths(run_id)
    if paths:
        return paths.exports
    # Fallback to default
    from config_v2 import OUTPUT_DIR
    return OUTPUT_DIR / "exports"


# =============================================================================
# Integration helpers for existing code
# =============================================================================

def save_analysis_outputs(
    fact_store: Any,
    reasoning_store: Any,
    run_id: str = None,
    generate_report: bool = True
) -> Dict[str, Path]:
    """
    Save all analysis outputs to a run folder.

    This is a convenience function that saves everything in one call.

    Args:
        fact_store: FactStore with extracted facts
        reasoning_store: ReasoningStore with findings
        run_id: Run ID or None for latest/new
        generate_report: Whether to generate HTML report

    Returns:
        Dict mapping output type to file path
    """
    import json
    from tools_v2.html_report import generate_html_report

    manager = get_run_manager()

    # Get or create run
    if run_id:
        paths = manager.get_run_paths(run_id)
        if paths is None:
            raise ValueError(f"Run not found: {run_id}")
    else:
        run_id = manager.get_latest_run()
        if run_id:
            paths = manager.get_run_paths(run_id)
        else:
            paths = manager.create_run_directory()
            run_id = paths.root.name

    output_files = {}
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Save facts
    facts_file = paths.facts / "facts.json"
    fact_store.save(str(facts_file))
    output_files['facts'] = facts_file

    # Save findings
    findings_file = paths.findings / "findings.json"
    findings_data = reasoning_store.get_all_findings()
    with open(findings_file, 'w') as f:
        json.dump(findings_data, f, indent=2, default=str)
    output_files['findings'] = findings_file

    # Generate HTML report
    if generate_report:
        report_file = generate_html_report(
            fact_store=fact_store,
            reasoning_store=reasoning_store,
            output_dir=paths.reports,
            timestamp=timestamp
        )
        output_files['report'] = report_file

    # Update run metadata
    manager.update_run_metadata(
        run_id,
        facts_count=len(fact_store.facts),
        risks_count=len(reasoning_store.risks),
        work_items_count=len(reasoning_store.work_items),
        gaps_count=len(fact_store.gaps)
    )

    logger.info(f"Saved analysis outputs to run: {run_id}")
    return output_files
