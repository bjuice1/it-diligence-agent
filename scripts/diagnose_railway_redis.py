#!/usr/bin/env python3
"""
Railway Redis Diagnostic Script

Tests Redis connection and Celery availability on Railway.
Run this on Railway to diagnose Redis configuration issues.

Usage:
    python scripts/diagnose_railway_redis.py
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def diagnose():
    """Run comprehensive Redis diagnostics."""
    print("=" * 70)
    print("RAILWAY REDIS DIAGNOSTICS")
    print("=" * 70)

    # Check 1: Environment Variables
    print("\n[1] ENVIRONMENT VARIABLES")
    print("-" * 70)

    redis_url = os.environ.get('REDIS_URL', '')
    redis_tls_url = os.environ.get('REDIS_TLS_URL', '')

    if redis_url:
        # Mask password
        if '@' in redis_url:
            parts = redis_url.split('@')
            masked = parts[0].split(':')[0] + ':****@' + '@'.join(parts[1:])
            print(f"✓ REDIS_URL set: {masked}")
        else:
            print(f"✓ REDIS_URL set: {redis_url[:40]}...")
    elif redis_tls_url:
        print(f"✓ REDIS_TLS_URL set (secure connection)")
        redis_url = redis_tls_url
    else:
        print("✗ REDIS_URL not set!")
        print("  Redis is required for Celery background tasks.")
        print("\nSOLUTION:")
        print("  1. Go to Railway project")
        print("  2. Click on Redis service")
        print("  3. Go to 'Variables' tab")
        print("  4. Copy REDIS_URL (or REDIS_TLS_URL)")
        print("  5. Go to your app service")
        print("  6. Add REDIS_URL variable with the copied value")
        return False

    use_celery = os.environ.get('USE_CELERY', 'true').lower()
    print(f"  USE_CELERY: {use_celery}")

    # Check 2: Redis Connection
    print("\n[2] REDIS CONNECTION")
    print("-" * 70)

    try:
        import redis

        # Handle TLS connections
        if redis_url.startswith('rediss://'):
            r = redis.from_url(redis_url, ssl_cert_reqs=None)
        else:
            r = redis.from_url(redis_url)

        # Test ping
        r.ping()
        print("✓ Redis connection successful")

        # Get Redis info
        info = r.info()
        print(f"  Redis version: {info.get('redis_version', 'unknown')}")
        print(f"  Connected clients: {info.get('connected_clients', 0)}")
        print(f"  Used memory: {info.get('used_memory_human', 'unknown')}")
        print(f"  Total keys: {r.dbsize()}")

    except ImportError:
        print("✗ redis library not installed!")
        print("\nSOLUTION:")
        print("  pip install redis")
        return False
    except Exception as e:
        print(f"✗ Redis connection failed: {e}")
        print("\nPOSSIBLE CAUSES:")
        print("  - REDIS_URL format incorrect")
        print("  - Redis service not running")
        print("  - Network connectivity issues")
        print("  - TLS/SSL issues (try REDIS_TLS_URL)")
        return False

    # Check 3: Celery Configuration
    print("\n[3] CELERY CONFIGURATION")
    print("-" * 70)

    try:
        from web.celery_app import celery, is_celery_available

        print(f"✓ Celery app initialized")
        print(f"  Broker: {celery.conf.broker_url[:50]}...")
        print(f"  Backend: {celery.conf.result_backend[:50]}...")
        print(f"  Task serializer: {celery.conf.task_serializer}")

        if is_celery_available():
            print("✓ Celery broker (Redis) is available")
        else:
            print("✗ Celery broker check failed")
            return False

    except ImportError as e:
        print(f"✗ Celery import failed: {e}")
        print("\nSOLUTION:")
        print("  pip install celery")
        return False
    except Exception as e:
        print(f"✗ Celery configuration error: {e}")
        return False

    # Check 4: Celery Workers
    print("\n[4] CELERY WORKERS")
    print("-" * 70)

    try:
        from celery import Celery

        # Inspect active workers
        inspect = celery.control.inspect()
        stats = inspect.stats()

        if stats:
            worker_count = len(stats)
            print(f"✓ Found {worker_count} active worker(s):")
            for worker_name, worker_stats in stats.items():
                print(f"  - {worker_name}")
        else:
            print("⚠ No active Celery workers found")
            print("  Workers are required to process background tasks.")
            print("\nTO START WORKER:")
            print("  On Railway, make sure you have a 'worker' service:")
            print("  celery -A web.celery_app worker --loglevel=info")

    except Exception as e:
        print(f"⚠ Could not inspect workers: {e}")
        print("  This is normal if workers are in a separate container")

    # Check 5: Test Task
    print("\n[5] TEST TASK")
    print("-" * 70)

    try:
        # Try to create a simple test task
        test_key = "railway_diagnostic_test"
        test_value = "connection_ok"

        r.set(test_key, test_value, ex=60)  # Expire in 60 seconds
        retrieved = r.get(test_key)

        if retrieved and retrieved.decode('utf-8') == test_value:
            print("✓ Can write and read from Redis")
            r.delete(test_key)
            print("✓ Can delete from Redis")
        else:
            print("✗ Redis read/write test failed")
            return False

    except Exception as e:
        print(f"✗ Redis test operations failed: {e}")
        return False

    # Check 6: Session Storage
    print("\n[6] SESSION STORAGE")
    print("-" * 70)

    use_redis_sessions = os.environ.get('USE_REDIS_SESSIONS', 'true').lower()
    print(f"  USE_REDIS_SESSIONS: {use_redis_sessions}")

    if use_redis_sessions == 'true':
        print("✓ Redis sessions enabled")
        print("  Sessions will be stored in Redis for scalability")
    else:
        print("⚠ Redis sessions disabled")
        print("  Using server-side file storage (not recommended for production)")

    # Summary
    print("\n" + "=" * 70)
    print("DIAGNOSIS COMPLETE - ALL CHECKS PASSED ✓")
    print("=" * 70)
    print("\nRedis is properly configured and operational.")
    print("\nNOTE:")
    print("  - If no workers shown, start worker service on Railway")
    print("  - Background tasks require at least one worker")
    print("  - Worker command: celery -A web.celery_app worker --loglevel=info")
    return True


if __name__ == '__main__':
    try:
        success = diagnose()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nDiagnostics interrupted.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nFATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
