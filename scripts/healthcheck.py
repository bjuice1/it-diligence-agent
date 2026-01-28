#!/usr/bin/env python3
"""
Health Check Script for IT Due Diligence Agent

Verifies system configuration, dependencies, and connectivity.
"""

import argparse
import json
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


def check_python_version() -> tuple:
    """Check Python version."""
    version = sys.version_info
    required = (3, 9)
    ok = version >= required
    msg = f"Python {version.major}.{version.minor}.{version.micro}"
    if not ok:
        msg += f" (requires {required[0]}.{required[1]}+)"
    return ok, msg


def check_anthropic_key() -> tuple:
    """Check Anthropic API key configuration."""
    key = os.environ.get('ANTHROPIC_API_KEY')
    if not key:
        try:
            from config_v2 import ANTHROPIC_API_KEY
            key = ANTHROPIC_API_KEY
        except ImportError:
            pass

    if not key:
        return False, "ANTHROPIC_API_KEY not configured"
    if len(key) < 20:
        return False, "ANTHROPIC_API_KEY appears invalid (too short)"
    return True, f"ANTHROPIC_API_KEY configured ({key[:10]}...)"


def check_directories() -> tuple:
    """Check required directories exist and are writable."""
    from config_v2 import OUTPUT_DIR, UPLOADS_DIR

    issues = []

    for name, path in [("OUTPUT_DIR", OUTPUT_DIR), ("UPLOADS_DIR", UPLOADS_DIR)]:
        if not path.exists():
            issues.append(f"{name} does not exist: {path}")
        else:
            # Test writability
            try:
                test_file = path / ".healthcheck_test"
                test_file.touch()
                test_file.unlink()
            except Exception as e:
                issues.append(f"{name} not writable: {e}")

    if issues:
        return False, "; ".join(issues)
    return True, f"Directories OK (output={OUTPUT_DIR}, uploads={UPLOADS_DIR})"


def check_dependencies() -> tuple:
    """Check required Python packages are installed."""
    # Package name -> import name mapping
    required = {
        'flask': 'flask',
        'anthropic': 'anthropic',
        'openpyxl': 'openpyxl',
        'python-dotenv': 'dotenv',
    }

    missing = []
    for pkg, import_name in required.items():
        try:
            __import__(import_name)
        except ImportError:
            missing.append(pkg)

    if missing:
        return False, f"Missing packages: {', '.join(missing)}"
    return True, f"All {len(required)} required packages installed"


def check_stores() -> tuple:
    """Check store modules can be imported."""
    try:
        from stores import (
            FactStore, DocumentStore, SessionStore,
            ValidationStore, CorrectionStore, AuditStore
        )
        return True, "All stores importable"
    except ImportError as e:
        return False, f"Store import error: {e}"


def check_web_app() -> tuple:
    """Check Flask app can be imported."""
    try:
        from web.app import app
        return True, f"Flask app loaded ({len(app.url_map._rules)} routes)"
    except Exception as e:
        return False, f"Flask app error: {e}"


def check_api_connectivity() -> tuple:
    """Check Anthropic API connectivity (optional)."""
    try:
        import anthropic
        from config_v2 import ANTHROPIC_API_KEY

        if not ANTHROPIC_API_KEY:
            return None, "API key not configured (skipped)"

        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        # Just check we can create a client, don't make actual API call
        return True, "Anthropic client initialized"
    except anthropic.AuthenticationError:
        return False, "Anthropic API key invalid"
    except Exception as e:
        return None, f"Could not check API: {e}"


def check_document_store() -> tuple:
    """Check DocumentStore has documents loaded."""
    try:
        from stores import DocumentStore
        store = DocumentStore.get_instance()
        count = len(store._documents)
        return True, f"DocumentStore: {count} documents"
    except Exception as e:
        return False, f"DocumentStore error: {e}"


def check_run_manager() -> tuple:
    """Check RunManager can list runs."""
    try:
        from services.run_manager import get_run_manager
        manager = get_run_manager()
        runs = manager.list_runs()
        latest = manager.get_latest_run()
        return True, f"RunManager: {len(runs)} runs, latest={latest or 'none'}"
    except Exception as e:
        return False, f"RunManager error: {e}"


def run_healthcheck(verbose: bool = False, json_output: bool = False) -> dict:
    """Run all health checks."""
    checks = [
        ("Python Version", check_python_version),
        ("Anthropic API Key", check_anthropic_key),
        ("Directories", check_directories),
        ("Dependencies", check_dependencies),
        ("Stores", check_stores),
        ("Web App", check_web_app),
        ("Document Store", check_document_store),
        ("Run Manager", check_run_manager),
    ]

    if verbose:
        checks.append(("API Connectivity", check_api_connectivity))

    results = {}
    all_ok = True

    for name, check_fn in checks:
        try:
            ok, msg = check_fn()
            results[name] = {"status": "ok" if ok else ("skip" if ok is None else "fail"), "message": msg}
            if ok is False:
                all_ok = False
        except Exception as e:
            results[name] = {"status": "error", "message": str(e)}
            all_ok = False

    results["_overall"] = "healthy" if all_ok else "unhealthy"
    return results


def main():
    parser = argparse.ArgumentParser(
        description="Health check for IT Due Diligence Agent"
    )
    parser.add_argument(
        '-v', '--verbose', action='store_true',
        help='Include additional checks (API connectivity)'
    )
    parser.add_argument(
        '-j', '--json', action='store_true',
        help='Output as JSON'
    )
    parser.add_argument(
        '-q', '--quiet', action='store_true',
        help='Only output errors'
    )

    args = parser.parse_args()

    results = run_healthcheck(verbose=args.verbose, json_output=args.json)

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print("\n=== IT Due Diligence Agent Health Check ===\n")

        for name, result in results.items():
            if name.startswith('_'):
                continue

            status = result['status']
            msg = result['message']

            if args.quiet and status == 'ok':
                continue

            if status == 'ok':
                icon = '\u2713'  # checkmark
            elif status == 'skip':
                icon = '-'
            else:
                icon = '\u2717'  # X

            print(f"  [{icon}] {name}: {msg}")

        print()
        overall = results.get('_overall', 'unknown')
        if overall == 'healthy':
            print("Status: HEALTHY")
            sys.exit(0)
        else:
            print("Status: UNHEALTHY")
            sys.exit(1)


if __name__ == "__main__":
    main()
