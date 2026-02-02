"""
Deal Context Resolver for Phase 2 Database-First Architecture

Provides request-scoped deal context via flask.g, ensuring all routes
use consistent scoping rules for which analysis run's data to display.

The key scoping rule: default to the latest COMPLETED analysis run.
This ensures users don't see partially-written data from in-progress runs.

Fallback behavior when no completed run exists:
- Falls back to the latest run of ANY status (so users see in-progress data)
- Sets g.run_is_complete = False to indicate data may be incomplete
- UI can check this flag to show appropriate warnings
"""

from flask import g, abort
from typing import Optional
import logging

logger = logging.getLogger(__name__)


def load_deal_context(deal_id: str, run_id: str = None, require_completed: bool = False):
    """
    Load deal and analysis run context onto flask.g.

    Call this at the start of any deal-scoped route. Sets:
    - g.deal: The Deal model instance
    - g.deal_id: The deal ID string
    - g.run_id: The analysis run ID to use for data queries (may be None if no runs)
    - g.analysis_run: The AnalysisRun model instance (or None)
    - g.run_is_complete: True if showing data from a completed run
    - g.has_any_run: True if any analysis run exists for this deal

    Args:
        deal_id: The deal ID to load context for
        run_id: Optional specific run ID to use (defaults to latest completed)
        require_completed: If True, abort 409 if no completed run exists

    Raises:
        404 if deal not found
        409 if require_completed=True and no completed run exists
    """
    from web.database import Deal
    from web.repositories import AnalysisRunRepository

    deal = Deal.query.get(deal_id)
    if not deal:
        abort(404, description="Deal not found")

    run_repo = AnalysisRunRepository()
    analysis_run = None
    run_is_complete = False

    if run_id:
        # Specific run requested
        analysis_run = run_repo.get_by_id(run_id)
        run_is_complete = analysis_run.status == 'completed' if analysis_run else False
    else:
        # Default: try latest completed run first (the Phase 2 scoping rule)
        analysis_run = run_repo.get_latest_completed(deal_id)

        if analysis_run:
            run_is_complete = True
        else:
            # No completed run - check if we require one
            if require_completed:
                abort(409, description="No completed analysis run for this deal. Run analysis first.")

            # Fallback: get latest run of ANY status
            # This allows users to see in-progress data rather than nothing
            analysis_run = run_repo.get_latest(deal_id)

            if analysis_run:
                logger.info(
                    f"No completed run for deal {deal_id}, falling back to "
                    f"latest run {analysis_run.id} (status: {analysis_run.status})"
                )
                run_is_complete = False

    # Set on flask.g for request-scoped access
    g.deal = deal
    g.deal_id = deal_id
    g.run_id = analysis_run.id if analysis_run else None
    g.analysis_run = analysis_run
    g.run_is_complete = run_is_complete
    g.has_any_run = analysis_run is not None


def require_deal_context():
    """
    Ensure deal context has been loaded.

    Call this in routes that expect deal context to already be set.
    Raises RuntimeError if context is missing.
    """
    if not hasattr(g, 'deal_id') or g.deal_id is None:
        raise RuntimeError(
            "Deal context not loaded. Call load_deal_context(deal_id) first."
        )


def get_deal_id() -> Optional[str]:
    """Get the current deal_id from context, or None if not set."""
    return getattr(g, 'deal_id', None)


def get_run_id() -> Optional[str]:
    """Get the current run_id from context, or None if not set."""
    return getattr(g, 'run_id', None)


def has_deal_context() -> bool:
    """Check if deal context has been loaded for this request."""
    return hasattr(g, 'deal_id') and g.deal_id is not None


def is_run_complete() -> bool:
    """
    Check if the current run is complete.

    Returns False if:
    - No deal context loaded
    - No analysis run exists
    - Analysis run exists but status is not 'completed'
    """
    return getattr(g, 'run_is_complete', False)


def has_any_run() -> bool:
    """Check if any analysis run exists for the current deal."""
    return getattr(g, 'has_any_run', False)


def get_analysis_status() -> dict:
    """
    Get the status of the current deal's analysis.

    Returns dict with:
    - has_any_run: bool - whether any run exists
    - has_completed_run: bool - whether showing data from a completed run
    - run_is_complete: bool - same as has_completed_run (for templates)
    - latest_run_status: str or None - status of the run being shown
    - run_id: str or None - ID of the run being used for queries
    - warning: str or None - warning message if showing incomplete data
    """
    from web.repositories import AnalysisRunRepository

    if not has_deal_context():
        return {
            'has_any_run': False,
            'has_completed_run': False,
            'run_is_complete': False,
            'latest_run_status': None,
            'run_id': None,
            'warning': None
        }

    run_status = g.analysis_run.status if g.analysis_run else None
    run_is_complete = getattr(g, 'run_is_complete', False)

    # Generate warning message if showing incomplete data
    warning = None
    if g.analysis_run and not run_is_complete:
        if run_status == 'running':
            warning = "Analysis is currently running. Data shown may be incomplete."
        elif run_status == 'failed':
            warning = "Latest analysis run failed. Showing partial data."
        elif run_status == 'cancelled':
            warning = "Latest analysis run was cancelled. Showing partial data."
        elif run_status == 'pending':
            warning = "Analysis is pending. No data available yet."

    return {
        'has_any_run': getattr(g, 'has_any_run', False),
        'has_completed_run': run_is_complete,
        'run_is_complete': run_is_complete,
        'latest_run_status': run_status,
        'run_id': g.run_id,
        'warning': warning
    }


def get_context_summary() -> dict:
    """
    Get a complete summary of the current deal context.

    Useful for debugging and for passing to templates.
    """
    if not has_deal_context():
        return {
            'loaded': False,
            'deal_id': None,
            'deal_name': None,
            'run_id': None,
            'run_status': None,
            'run_is_complete': False,
            'has_any_run': False,
            'warning': None
        }

    analysis_status = get_analysis_status()

    return {
        'loaded': True,
        'deal_id': g.deal_id,
        'deal_name': g.deal.name if g.deal else None,
        'run_id': g.run_id,
        'run_status': analysis_status['latest_run_status'],
        'run_is_complete': analysis_status['run_is_complete'],
        'has_any_run': analysis_status['has_any_run'],
        'warning': analysis_status['warning']
    }
