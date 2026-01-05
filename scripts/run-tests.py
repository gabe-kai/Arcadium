#!/usr/bin/env python3
"""
Unified Test Runner for Arcadium Project

This script provides a simple interface to run tests with progress tracking.
Uses pytest's built-in features for better integration.
"""

import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path for shared utilities
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from shared.utils.logging_config import (
        cleanup_old_logs,
        get_log_dir,
        setup_test_logger,
    )
except ImportError:
    # Fallback if shared utils not available
    setup_test_logger = None
    cleanup_old_logs = None
    get_log_dir = None

# Force unbuffered output
os.environ["PYTHONUNBUFFERED"] = "1"

# Colors
GREEN = "\033[0;32m"
RED = "\033[0;31m"
YELLOW = "\033[1;33m"
BLUE = "\033[0;34m"
CYAN = "\033[0;36m"
BOLD = "\033[1m"
NC = "\033[0m"


def print_header(text):
    """Print formatted header."""
    width = 80
    print(f"\n{BLUE}{BOLD}{'=' * width}{NC}")
    print(f"{BLUE}{BOLD}{text.center(width)}{NC}")
    print(f"{BLUE}{BOLD}{'=' * width}{NC}\n")


def print_section(text):
    """Print section header."""
    print(f"\n{CYAN}{'─' * 80}{NC}")
    print(f"{CYAN}{BOLD}{text}{NC}")
    print(f"{CYAN}{'─' * 80}{NC}\n")


def check_postgresql():
    """Check PostgreSQL configuration."""
    print_section("PostgreSQL Configuration Check")

    project_root = Path(__file__).parent.parent
    wiki_env = project_root / "services" / "wiki" / ".env"
    auth_env = project_root / "services" / "auth" / ".env"

    found = False

    # Try loading .env files
    try:
        from dotenv import load_dotenv

        if wiki_env.exists():
            load_dotenv(wiki_env)
        if auth_env.exists():
            load_dotenv(auth_env)
    except ImportError:
        pass

    # Check for required variables
    if os.environ.get("TEST_DATABASE_URL") or (
        os.environ.get("arcadium_user") and os.environ.get("arcadium_pass")
    ):
        print(f"{GREEN}✓ PostgreSQL configuration found{NC}")
        found = True
    else:
        print(f"{RED}✗ PostgreSQL configuration not found{NC}")
        print(
            f"{YELLOW}  Please ensure .env files exist with TEST_DATABASE_URL or (arcadium_user and arcadium_pass){NC}"
        )

    return found


def setup_log_directory():
    """Create logs directory structure."""
    if get_log_dir:
        logs_dir = get_log_dir() / "tests"
    else:
        project_root = Path(__file__).parent.parent
        logs_dir = project_root / "logs" / "tests"
    logs_dir.mkdir(parents=True, exist_ok=True)

    # Clean up old logs (keep last 30 days or 1GB, whichever is more restrictive)
    if cleanup_old_logs:
        try:
            deleted = cleanup_old_logs(
                logs_dir, max_age_days=30, max_total_size_mb=1024
            )
            if deleted > 0:
                print(f"{YELLOW}Cleaned up {deleted} old test log files{NC}")
        except Exception:
            pass  # Don't fail if cleanup fails

    return logs_dir


# Wiki service test categories
WIKI_TEST_CATEGORIES = {
    "models": {
        "path": "tests/test_models",
        "name": "Models",
        "description": "Database model tests",
    },
    "services": {
        "path": "tests/test_services",
        "name": "Services",
        "description": "Business logic service layer tests",
    },
    "api": {
        "path": "tests/test_api",
        "name": "API",
        "description": "API endpoint tests",
    },
    "utils": {
        "path": "tests/test_utils",
        "name": "Utils",
        "description": "Utility function tests",
    },
    "sync": {
        "path": "tests/test_sync",
        "name": "Sync",
        "description": "File sync system tests",
    },
    "integration": {
        "path": "tests/test_integration",
        "name": "Integration",
        "description": "Integration tests",
    },
    "performance": {
        "path": "tests/test_performance",
        "name": "Performance",
        "description": "Performance tests",
    },
    "health": {
        "path": "tests/test_health.py",
        "name": "Health",
        "description": "Health check tests",
    },
}


def get_log_file_path(service_name=None, category=None):
    """Get log file path for test run."""
    logs_dir = setup_log_directory()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    if service_name:
        if category:
            filename = f"test_{service_name.lower()}_{category.lower()}_{timestamp}.log"
        else:
            filename = f"test_{service_name.lower()}_{timestamp}.log"
    else:
        filename = f"test_all_{timestamp}.log"

    log_path = logs_dir / filename

    # Also set up Python logger for this test run if available
    if setup_test_logger and service_name:
        try:
            log_name = f"{service_name.lower()}"
            if category:
                log_name += f"_{category.lower()}"
            logger = setup_test_logger(log_name)
            logger.info(
                f"Test run started: {service_name}"
                + (f" - {category}" if category else "")
            )
        except Exception:
            pass  # Don't fail if logger setup fails

    return log_path


def run_pytest(service_path, test_path=None, category=None, log_file=None):
    """Run pytest for a service."""
    project_root = Path(__file__).parent.parent
    full_path = project_root / service_path

    if not full_path.exists():
        print(f"{RED}✗ Service path not found: {service_path}{NC}")
        return (False, None)

    # Build pytest command
    cmd = [
        "python",
        "-m",
        "pytest",
        "-v",
        "--tb=short",
        "--durations=10",
        "--color=yes",
    ]

    if test_path:
        cmd.append(str(full_path / test_path))
    elif category:
        # Use pytest markers if category matches
        cmd.extend(["-m", category])
    else:
        cmd.append("tests")

    print(f"{CYAN}Running: {service_path}{NC}")
    if test_path:
        print(f"{CYAN}  Path: {test_path}{NC}")
    if category:
        print(f"{CYAN}  Category: {category}{NC}")
    if log_file:
        print(f"{CYAN}  Logging to: {log_file.relative_to(project_root)}{NC}")
    print()

    try:
        # Capture output for logging
        result = subprocess.run(
            cmd, cwd=full_path, check=False, capture_output=True, text=True
        )

        # Write to log file if provided
        if log_file:
            with open(log_file, "w", encoding="utf-8") as f:
                f.write(f"Test Run: {service_path}\n")
                f.write(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Command: {' '.join(cmd)}\n")
                f.write(f"{'=' * 80}\n\n")
                f.write(result.stdout)
                if result.stderr:
                    f.write("\n\nSTDERR:\n")
                    f.write(result.stderr)
                f.write(f"\n\n{'=' * 80}\n")
                f.write(f"Exit Code: {result.returncode}\n")
                f.write(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        # Parse test count from output
        test_count = None
        test_output = result.stdout + (result.stderr or "")

        # Look for patterns like "62 passed", "188 passed, 4 xfailed", etc.
        import re

        passed_match = re.search(r"(\d+)\s+passed", test_output)
        xfailed_match = re.search(r"(\d+)\s+xfailed", test_output)
        failed_match = re.search(r"(\d+)\s+failed", test_output)

        if passed_match:
            passed = int(passed_match.group(1))
            xfailed = int(xfailed_match.group(1)) if xfailed_match else 0
            failed = int(failed_match.group(1)) if failed_match else 0
            total = passed + failed
            if xfailed > 0:
                test_count = f"{total} tests ({passed} passed, {xfailed} xfailed, {failed} failed)"
            elif failed > 0:
                test_count = f"{total} tests ({passed} passed, {failed} failed)"
            else:
                test_count = f"{total} tests"

        # Print output to console (strip ANSI codes for cleaner output in logs)
        print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)

        return (result.returncode == 0, test_count)
    except Exception as e:
        error_msg = f"✗ Error: {e}"
        print(f"{RED}{error_msg}{NC}")
        if log_file:
            with open(log_file, "w", encoding="utf-8") as f:
                f.write(f"ERROR: {error_msg}\n")
        return (False, None)


def main():
    """Main test runner."""
    print_header("ARCADIUM PROJECT - TEST RUNNER")
    start_time = datetime.now()
    print(f"Started at: {start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Check PostgreSQL
    if not check_postgresql():
        print(f"\n{RED}Cannot proceed without PostgreSQL configuration{NC}")
        sys.exit(1)

    # Set test environment
    os.environ["FLASK_ENV"] = "testing"

    # Setup logging
    logs_dir = setup_log_directory()
    project_root = Path(__file__).parent.parent

    # Parse arguments
    if len(sys.argv) > 1:
        service = sys.argv[1]

        if service == "wiki":
            print_section("Wiki Service Tests")

            # Check if a specific category was requested
            if len(sys.argv) > 2:
                category_key = sys.argv[2].lower()
                if category_key in WIKI_TEST_CATEGORIES:
                    category_info = WIKI_TEST_CATEGORIES[category_key]
                    print(f"{CYAN}Running Wiki {category_info['name']} tests{NC}")
                    print(f"{CYAN}  {category_info['description']}{NC}\n")
                    log_file = get_log_file_path("wiki", category_key)
                    success, test_count = run_pytest(
                        "services/wiki",
                        test_path=category_info["path"],
                        log_file=log_file,
                    )
                    if test_count:
                        print(f"\n{CYAN}Test count: {test_count}{NC}")
                else:
                    print(f"{RED}Unknown Wiki test category: {category_key}{NC}")
                    print(
                        f"{YELLOW}Available categories: {', '.join(WIKI_TEST_CATEGORIES.keys())}{NC}"
                    )
                    sys.exit(1)
            else:
                # Run all Wiki tests
                log_file = get_log_file_path("wiki")
                success, test_count = run_pytest("services/wiki", log_file=log_file)
                if test_count:
                    print(f"\n{CYAN}Test count: {test_count}{NC}")

            print(
                f"\n{CYAN}Test log saved to: {log_file.relative_to(project_root)}{NC}\n"
            )
            sys.exit(0 if success else 1)

        elif service == "auth":
            print_section("Auth Service Tests")
            log_file = get_log_file_path("auth")
            if len(sys.argv) > 2:
                category = sys.argv[2]
                success, test_count = run_pytest(
                    "services/auth", category=category, log_file=log_file
                )
            else:
                success, test_count = run_pytest("services/auth", log_file=log_file)
            if test_count:
                print(f"\n{CYAN}Test count: {test_count}{NC}")
            print(
                f"\n{CYAN}Test log saved to: {log_file.relative_to(project_root)}{NC}\n"
            )
            sys.exit(0 if success else 1)

        elif service == "shared":
            print_section("Shared Auth Tests")
            log_file = get_log_file_path("shared")
            success, test_count = run_pytest("shared/auth", log_file=log_file)
            if test_count:
                print(f"\n{CYAN}Test count: {test_count}{NC}")
            print(
                f"\n{CYAN}Test log saved to: {log_file.relative_to(project_root)}{NC}\n"
            )
            sys.exit(0 if success else 1)

        elif service == "all":
            # Run all backend tests
            print_section("Running All Backend Tests")

            # Create summary log file
            summary_log = get_log_file_path("all")

            results = []
            service_logs = []

            # Wiki Service - run by category
            print_section("Wiki Service")
            wiki_results = []
            wiki_all_passed = True
            wiki_total_tests = 0

            for category_key, category_info in WIKI_TEST_CATEGORIES.items():
                print(
                    f"\n{CYAN}Wiki - {category_info['name']} ({category_info['description']}){NC}"
                )
                category_log = get_log_file_path("wiki", category_key)
                category_success, test_count = run_pytest(
                    "services/wiki",
                    test_path=category_info["path"],
                    log_file=category_log,
                )
                wiki_results.append(
                    (f"Wiki - {category_info['name']}", category_success, test_count)
                )
                service_logs.append(
                    (f"Wiki - {category_info['name']}", category_log, category_success)
                )
                if not category_success:
                    wiki_all_passed = False
                # Extract total test count if available
                if test_count:
                    import re

                    match = re.search(r"^(\d+)\s+tests", test_count)
                    if match:
                        wiki_total_tests += int(match.group(1))

            wiki_summary = "Wiki (all categories)"
            if wiki_total_tests > 0:
                wiki_summary += f" - {wiki_total_tests} tests total"
            results.append((wiki_summary, wiki_all_passed, None))
            results.extend(wiki_results)

            print_section("Auth Service")
            auth_log = get_log_file_path("auth")
            auth_success, auth_test_count = run_pytest(
                "services/auth", log_file=auth_log
            )
            auth_summary = "Auth"
            if auth_test_count:
                auth_summary += f" - {auth_test_count}"
            results.append((auth_summary, auth_success, auth_test_count))
            service_logs.append(("Auth", auth_log, auth_success))

            print_section("Shared Auth")
            shared_log = get_log_file_path("shared")
            shared_success, shared_test_count = run_pytest(
                "shared/auth", log_file=shared_log
            )
            shared_summary = "Shared"
            if shared_test_count:
                shared_summary += f" - {shared_test_count}"
            results.append((shared_summary, shared_success, shared_test_count))
            service_logs.append(("Shared", shared_log, shared_success))

            # Write summary log
            end_time = datetime.now()
            duration = end_time - start_time

            with open(summary_log, "w", encoding="utf-8") as f:
                f.write("=" * 80 + "\n")
                f.write("ARCADIUM PROJECT - TEST RUN SUMMARY\n")
                f.write("=" * 80 + "\n\n")
                f.write(f"Started: {start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Completed: {end_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Duration: {duration}\n\n")
                f.write("-" * 80 + "\n")
                f.write("RESULTS:\n")
                f.write("-" * 80 + "\n\n")

                all_passed = True
                for result_item in results:
                    if len(result_item) == 3:
                        name, success, test_count = result_item
                        status = "PASSED" if success else "FAILED"
                        if test_count:
                            f.write(f"{name:30} [{status}] {test_count}\n")
                        else:
                            f.write(f"{name:30} [{status}]\n")
                    else:
                        name, success = result_item
                        status = "PASSED" if success else "FAILED"
                        f.write(f"{name:30} [{status}]\n")
                    if not success:
                        all_passed = False

                f.write(f"\n{'=' * 80}\n")
                f.write(
                    f"OVERALL: {'ALL TESTS PASSED' if all_passed else 'SOME TESTS FAILED'}\n"
                )
                f.write(f"{'=' * 80}\n\n")

                f.write("INDIVIDUAL SERVICE/CATEGORY LOGS:\n")
                f.write("-" * 80 + "\n")
                for name, log_path, success in service_logs:
                    rel_path = log_path.relative_to(project_root)
                    status = "PASSED" if success else "FAILED"
                    f.write(f"{name:30} [{status}] {rel_path}\n")

            # Summary
            print_header("Test Summary")
            all_passed = True
            for result_item in results:
                if len(result_item) == 3:
                    name, success, test_count = result_item
                    status = f"{GREEN}✓ PASSED{NC}" if success else f"{RED}✗ FAILED{NC}"
                    # Indent Wiki categories
                    if name.startswith("Wiki - "):
                        if test_count:
                            print(f"  {name:28} {status} ({test_count})")
                        else:
                            print(f"  {name:28} {status}")
                    else:
                        if test_count:
                            print(f"{name:30} {status} ({test_count})")
                        else:
                            print(f"{name:30} {status}")
                else:
                    name, success = result_item
                    status = f"{GREEN}✓ PASSED{NC}" if success else f"{RED}✗ FAILED{NC}"
                    if name.startswith("Wiki - "):
                        print(f"  {name:28} {status}")
                    else:
                        print(f"{name:30} {status}")
                if not success:
                    all_passed = False

            if all_passed:
                print(f"\n{GREEN}{BOLD}All tests passed!{NC}\n")
            else:
                print(f"\n{RED}{BOLD}Some tests failed{NC}\n")

            print(f"{CYAN}Summary log: {summary_log.relative_to(project_root)}{NC}")
            print(
                f"{CYAN}Individual service logs saved to: {logs_dir.relative_to(project_root)}{NC}\n"
            )

            sys.exit(0 if all_passed else 1)

        else:
            print(f"{RED}Unknown service: {service}{NC}")
            print(
                f"{YELLOW}Usage: python scripts/run-tests.py [wiki|auth|shared|all] [category]{NC}"
            )
            sys.exit(1)
    else:
        # Interactive mode - show menu
        print_section("Test Runner Menu")
        print("Available options:")
        print(
            f"  1. {CYAN}python scripts/run-tests.py wiki{NC}      - Run all Wiki Service tests"
        )
        print(
            f"  2. {CYAN}python scripts/run-tests.py wiki <category>{NC} - Run specific Wiki category"
        )
        print(f"     Categories: {', '.join(WIKI_TEST_CATEGORIES.keys())}")
        print(
            f"  3. {CYAN}python scripts/run-tests.py auth{NC}      - Run Auth Service tests"
        )
        print(
            f"  4. {CYAN}python scripts/run-tests.py shared{NC}    - Run Shared Auth tests"
        )
        print(
            f"  5. {CYAN}python scripts/run-tests.py all{NC}        - Run all backend tests (Wiki by category)"
        )
        print()
        print("Wiki Service Categories:")
        for key, info in WIKI_TEST_CATEGORIES.items():
            print(f"  {CYAN}{key:15}{NC} - {info['description']}")
        print()
        print("For frontend tests:")
        print(
            f"  {CYAN}cd client && npm run test{NC}              - Run unit/integration tests"
        )
        print(f"  {CYAN}cd client && npm run test:e2e{NC}           - Run E2E tests")
        print()
        print("See docs/testing-overview.md for detailed test documentation")
        sys.exit(0)


if __name__ == "__main__":
    main()
