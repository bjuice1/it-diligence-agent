"""
Database persistence layer for AnalysisTaskManager.

Saves task state to database so tasks survive server restarts.
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class TaskPersistence:
    """Handles saving/loading task state to/from database."""

    @staticmethod
    def save_task_state(task_id: str, deal_id: str, status: str, progress: float, 
                        current_step: str, error_message: str = '') -> None:
        """
        Save or update task state in database.

        Links to AnalysisRun table which already has all the fields we need.
        """
        try:
            from web.database import db, AnalysisRun

            # Find or create analysis run for this task
            run = AnalysisRun.query.filter_by(task_id=task_id).first()

            if not run:
                # Create new run record
                run = AnalysisRun(
                    task_id=task_id,
                    deal_id=deal_id,
                    run_number=AnalysisRun.query.filter_by(deal_id=deal_id).count() + 1,
                    status=status,
                    progress=progress,
                    current_step=current_step,
                    started_at=datetime.utcnow() if status == 'running' else None
                )
                db.session.add(run)
            else:
                # Update existing run
                run.status = status
                run.progress = progress
                run.current_step = current_step

                if status == 'completed':
                    run.completed_at = datetime.utcnow()
                    if run.started_at:
                        run.duration_seconds = (run.completed_at - run.started_at).total_seconds()

                if status == 'failed' and error_message:
                    run.error_message = error_message

            db.session.commit()
            logger.debug(f"Saved task state for {task_id}: {status} at {progress}%")

        except Exception as e:
            logger.error(f"Error saving task state: {e}")
            try:
                db.session.rollback()
            except:
                pass

    @staticmethod
    def load_task_state(task_id: str) -> Optional[Dict[str, Any]]:
        """Load task state from database."""
        try:
            from web.database import AnalysisRun

            run = AnalysisRun.query.filter_by(task_id=task_id).first()

            if run:
                return {
                    'task_id': run.task_id,
                    'deal_id': run.deal_id,
                    'status': run.status,
                    'progress': run.progress,
                    'current_step': run.current_step,
                    'started_at': run.started_at.isoformat() if run.started_at else None,
                    'completed_at': run.completed_at.isoformat() if run.completed_at else None,
                    'error_message': run.error_message
                }

            return None

        except Exception as e:
            logger.error(f"Error loading task state: {e}")
            return None

    @staticmethod
    def recover_running_tasks() -> list:
        """
        On startup, find any tasks that were 'running' when server crashed.

        Returns list of task_ids that need recovery.
        """
        try:
            from web.database import AnalysisRun

            # Find runs that were running when we crashed
            running_runs = AnalysisRun.query.filter_by(status='running').all()

            if running_runs:
                logger.warning(f"Found {len(running_runs)} tasks that were running during restart")

                recovered_tasks = []
                for run in running_runs:
                    # Mark as failed (can't resume mid-analysis yet)
                    run.status = 'failed'
                    run.error_message = 'Server restarted during analysis'
                    run.completed_at = datetime.utcnow()

                    recovered_tasks.append({
                        'task_id': run.task_id,
                        'deal_id': run.deal_id,
                        'progress': run.progress,
                        'current_step': run.current_step
                    })

                from web.database import db
                db.session.commit()

                return recovered_tasks

            return []

        except Exception as e:
            logger.error(f"Error recovering tasks: {e}")
            return []


# Singleton instance
_persistence = TaskPersistence()


def get_task_persistence() -> TaskPersistence:
    """Get the task persistence singleton."""
    return _persistence
