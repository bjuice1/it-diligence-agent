"""
Quick Redis Connection Test
Run this locally or in Railway shell to verify Redis is accessible.
"""

import os
import sys

def test_redis_connection():
    """Test if Redis is available and responding."""

    redis_url = os.environ.get('REDIS_URL')

    if not redis_url:
        print("❌ REDIS_URL not set in environment")
        print("   Set it manually: export REDIS_URL='redis://...'")
        return False

    print(f"🔍 Testing connection to: {redis_url[:30]}...")

    try:
        import redis
        print("✅ redis library installed")
    except ImportError:
        print("❌ redis library not installed")
        print("   Run: pip install redis")
        return False

    try:
        r = redis.from_url(redis_url)
        r.ping()
        print("✅ Redis connection successful!")

        # Test basic operations
        r.set('test_key', 'test_value')
        value = r.get('test_key')
        print(f"✅ Read/write test: {value.decode()}")

        r.delete('test_key')
        print("✅ Redis is fully operational")
        return True

    except redis.ConnectionError as e:
        print(f"❌ Cannot connect to Redis: {e}")
        print("   Check if Redis is running and REDIS_URL is correct")
        return False
    except Exception as e:
        print(f"❌ Redis error: {e}")
        return False

if __name__ == '__main__':
    success = test_redis_connection()
    sys.exit(0 if success else 1)
