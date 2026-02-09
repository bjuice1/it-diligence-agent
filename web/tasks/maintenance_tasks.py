"""
Maintenance Tasks - Background cleanup and health checks

These tasks handle periodic maintenance operations:
- Session cleanup (remove expired sessions)
- Session backend health monitoring
- Database cleanup tasks

Run via Celery or manually for maintenance.
"""

import logging
import os
from datetime import datetime, timedelta
from typing import Dict, Any

try:
    from celery import shared_task as _shared_task
    CELERY_AVAILABLE = True

    # Use Celery's shared_task when available
    def shared_task(*dec_args, **dec_kwargs):
        return _shared_task(*dec_args, **dec_kwargs)

except ImportError:
    CELERY_AVAILABLE = False

    # Mock decorator when Celery not available - just return the function
    def shared_task(*dec_args, **dec_kwargs):
        def decorator(func):
            # If called with arguments, return decorator
            if dec_args and callable(dec_args[0]):
                return dec_args[0]
            return func
        # If called without arguments (e.g., @shared_task(name='...')), return decorator
        if dec_args and callable(dec_args[0]):
            return dec_args[0]
        return decorator

logger = logging.getLogger(__name__)


@shared_task(name='web.tasks.cleanup_expired_sessions')
def cleanup_expired_sessions(cutoff_days: int = 7) -> Dict[str, Any]:
    """
    Remove expired sessions from database.

    Run this periodically (e.g., daily at 3am) via cron or Celery beat.
    Only needed if using SQLAlchemy session backend.

    Args:
        cutoff_days: Remove sessions older than this many days

    Returns:
        dict with deletion count and cutoff timestamp

    Example:
        # Run manually
        from web.tasks.maintenance_tasks import cleanup_expired_sessions
        result = cleanup_expired_sessions(cutoff_days=7)
        print(f"Deleted {result['deleted']} sessions")

        # Run via Celery
        cleanup_expired_sessions.delay(cutoff_days=7)
    """
    from web.database import db

    try:
        # Calculate cutoff timestamp
        cutoff = datetime.utcnow() - timedelta(days=cutoff_days)

        # Delete expired sessions
        result = db.session.execute(db.text("""
            DELETE FROM flask_sessions
            WHERE expiry < :cutoff OR expiry IS NULL
        """), {'cutoff': cutoff})

        db.session.commit()
        deleted = result.rowcount

        logger.info(f"✅ Cleaned up {deleted} expired sessions (cutoff: {cutoff.isoformat()})")

        return {
            'deleted': deleted,
            'cutoff': cutoff.isoformat(),
            'cutoff_days': cutoff_days
        }

    except Exception as e:
        logger.error(f"Session cleanup failed: {e}")
        db.session.rollback()
        raise


@shared_task(name='web.tasks.check_session_backend_health')
def check_session_backend_health() -> Dict[str, Any]:
    """
    Health check for session backend.

    Returns status of Redis/SQLAlchemy and current session backend.
    Useful for monitoring and alerting.

    Returns:
        dict with redis status, database status, and current backend

    Example:
        from web.tasks.maintenance_tasks import check_session_backend_health
        status = check_session_backend_health()
        if status['current_backend'] == 'redis' and status['redis'] != 'healthy':
            alert("Redis session backend unhealthy!")
    """
    from web.app import app
    import redis as redis_module

    results = {
        'redis': 'unknown',
        'database': 'unknown',
        'current_backend': app.config.get('SESSION_TYPE', 'unknown'),
        'timestamp': datetime.utcnow().isoformat()
    }

    # Check Redis
    redis_url = os.environ.get('REDIS_URL') or os.environ.get('REDIS_TLS_URL')
    if redis_url:
        try:
            client = redis_module.from_url(redis_url, socket_connect_timeout=2)
            client.ping()
            results['redis'] = 'healthy'
            client.close()
        except Exception as e:
            results['redis'] = f'unhealthy: {str(e)[:100]}'
    else:
        results['redis'] = 'not_configured'

    # Check Database
    try:
        from web.database import db
        db.session.execute(db.text("SELECT 1"))
        results['database'] = 'healthy'
    except Exception as e:
        results['database'] = f'unhealthy: {str(e)[:100]}'

    # Check session table exists (if using SQLAlchemy backend)
    if results['current_backend'] == 'sqlalchemy':
        try:
            from web.database import db
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            if 'flask_sessions' in inspector.get_table_names():
                # Get session count
                result = db.session.execute(db.text("SELECT COUNT(*) FROM flask_sessions"))
                count = result.scalar()
                results['session_count'] = count
            else:
                results['database'] = 'unhealthy: flask_sessions table missing'
        except Exception as e:
            results['database'] = f'unhealthy: {str(e)[:100]}'

    logger.info(f"Session backend health check: {results}")
    return results


@shared_task(name='web.tasks.cleanup_stale_deal_references')
def cleanup_stale_deal_references() -> Dict[str, Any]:
    """
    Database maintenance: Clear last_deal_id for users whose deal is deleted.

    Run this periodically (e.g., weekly) or after bulk deal deletion.
    Part of Spec 01 optional cleanup.

    Returns:
        dict with number of users updated

    Example:
        from web.tasks.maintenance_tasks import cleanup_stale_deal_references
        result = cleanup_stale_deal_references()
        print(f"Cleared last_deal_id for {result['users_updated']} users")
    """
    from web.database import db, User, Deal
    from sqlalchemy import and_

    try:
        # Find users with last_deal_id pointing to deleted deals
        users_to_update = db.session.query(User).join(
            Deal, User.last_deal_id == Deal.id
        ).filter(
            and_(
                User.last_deal_id.isnot(None),
                Deal.deleted_at.isnot(None)
            )
        ).all()

        count = 0
        for user in users_to_update:
            user.clear_last_deal()
            count += 1

        db.session.commit()

        logger.info(f"✅ Cleared last_deal_id for {count} users with deleted deals")

        return {
            'users_updated': count,
            'timestamp': datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Stale deal reference cleanup failed: {e}")
        db.session.rollback()
        raise


# Convenience function for running all maintenance tasks
def run_all_maintenance_tasks() -> Dict[str, Any]:
    """
    Run all maintenance tasks in sequence.

    Useful for scheduled maintenance windows.

    Returns:
        dict with results from all tasks
    """
    results = {
        'started_at': datetime.utcnow().isoformat(),
        'tasks': {}
    }

    try:
        # Session cleanup
        logger.info("Running session cleanup...")
        results['tasks']['session_cleanup'] = cleanup_expired_sessions()
    except Exception as e:
        logger.error(f"Session cleanup failed: {e}")
        results['tasks']['session_cleanup'] = {'error': str(e)}

    try:
        # Health check
        logger.info("Running health check...")
        results['tasks']['health_check'] = check_session_backend_health()
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        results['tasks']['health_check'] = {'error': str(e)}

    try:
        # Stale deal reference cleanup
        logger.info("Running stale deal reference cleanup...")
        results['tasks']['deal_cleanup'] = cleanup_stale_deal_references()
    except Exception as e:
        logger.error(f"Deal cleanup failed: {e}")
        results['tasks']['deal_cleanup'] = {'error': str(e)}

    results['completed_at'] = datetime.utcnow().isoformat()

    logger.info(f"✅ All maintenance tasks complete: {results}")
    return results


if __name__ == '__main__':
    # Allow running tasks directly for testing
    print("Running maintenance tasks...")
    results = run_all_maintenance_tasks()
    print(f"Results: {results}")
