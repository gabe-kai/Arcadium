#!/usr/bin/env python3
"""
Unified Test Runner for Arcadium Project

This script runs all tests across the project with:
- Progress tracking and statistics
- Test categorization
- PostgreSQL database verification
- Real-time test output
"""

import os
import subprocess
import sys
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path

# Force unbuffered output
os.environ["PYTHONUNBUFFERED"] = "1"


# Colors for output
class Colors:
    RED = "\033[0;31m"
    GREEN = "\033[0;32m"
    YELLOW = "\033[1;33m"
    BLUE = "\033[0;34m"
    MAGENTA = "\033[0;35m"
    CYAN = "\033[0;36m"
    BOLD = "\033[1m"
    NC = "\033[0m"  # No Color


# Test Categories Configuration
TEST_CATEGORIES = {
    "backend": {
        "name": "Backend Services",
        "description": "Python Flask services (Wiki, Auth, Shared)",
        "services": [
            {
                "name": "Wiki Service",
                "path": "services/wiki",
                "categories": {
                    "models": {
                        "path": "tests/test_models",
                        "description": "Database model tests - verify data models, relationships, constraints",
                        "success_criteria": "All models create, update, delete correctly with proper relationships",
                    },
                    "services": {
                        "path": "tests/test_services",
                        "description": "Business logic service layer tests",
                        "success_criteria": "Services handle business rules, validation, and data transformations correctly",
                    },
                    "api": {
                        "path": "tests/test_api",
                        "description": "API endpoint tests - HTTP routes, request/response handling",
                        "success_criteria": "All endpoints return correct status codes, data formats, and error handling",
                    },
                    "utils": {
                        "path": "tests/test_utils",
                        "description": "Utility function tests - helpers, formatters, validators",
                        "success_criteria": "Utilities process data correctly and handle edge cases",
                    },
                    "sync": {
                        "path": "tests/test_sync",
                        "description": "File sync system tests - file watching, content sync, conflict resolution",
                        "success_criteria": "File changes sync to database correctly with conflict detection",
                    },
                    "integration": {
                        "path": "tests/test_integration",
                        "description": "Integration tests - cross-service interactions, end-to-end flows",
                        "success_criteria": "Services work together correctly with proper data flow",
                    },
                    "performance": {
                        "path": "tests/test_performance",
                        "description": "Performance tests - caching, query optimization, load handling",
                        "success_criteria": "System meets performance requirements under load",
                    },
                    "health": {
                        "path": "tests",
                        "pattern": "test_health.py",
                        "description": "Health check tests - service availability and status",
                        "success_criteria": "Health endpoints return correct status information",
                    },
                },
            },
            {
                "name": "Auth Service",
                "path": "services/auth",
                "categories": {
                    "models": {
                        "path": "tests/test_models",
                        "description": "Database model tests - User, Token, PasswordHistory models",
                        "success_criteria": "Models enforce constraints and relationships correctly",
                    },
                    "services": {
                        "path": "tests/test_services",
                        "description": "Authentication service tests - login, registration, token management",
                        "success_criteria": "Authentication flows work correctly with proper security",
                    },
                    "api": {
                        "path": "tests/test_api",
                        "description": "API endpoint tests - auth endpoints, rate limiting, security headers",
                        "success_criteria": "Endpoints handle authentication correctly with security measures",
                    },
                    "utils": {
                        "path": "tests/test_utils",
                        "description": "Validator tests - password validation, email validation",
                        "success_criteria": "Validators catch invalid inputs correctly",
                    },
                    "integration": {
                        "path": "tests/test_integration",
                        "description": "Integration tests - full auth flows, token refresh",
                        "success_criteria": "Complete authentication workflows function correctly",
                    },
                },
            },
            {
                "name": "Shared Auth",
                "path": "shared/auth",
                "categories": {
                    "all": {
                        "path": "tests",
                        "description": "Shared authentication utilities - token validation, permissions",
                        "success_criteria": "Shared utilities work correctly across services",
                    }
                },
            },
        ],
    },
    "frontend": {
        "name": "Frontend Client",
        "description": "React/Vite client application",
        "services": [
            {
                "name": "Client Unit/Integration",
                "path": "client",
                "type": "vitest",
                "categories": {
                    "components": {
                        "path": "src/test/components",
                        "description": "React component tests - UI rendering, user interactions",
                        "success_criteria": "Components render correctly and handle user input",
                    },
                    "pages": {
                        "path": "src/test/pages",
                        "description": "Page component tests - full page rendering, routing",
                        "success_criteria": "Pages render with correct data and navigation",
                    },
                    "services": {
                        "path": "src/test/services",
                        "description": "Service layer tests - API clients, state management",
                        "success_criteria": "Services handle API calls and state correctly",
                    },
                    "utils": {
                        "path": "src/test/utils",
                        "description": "Utility function tests - helpers, formatters",
                        "success_criteria": "Utilities process data correctly",
                    },
                    "integration": {
                        "path": "src/test/integration",
                        "description": "Integration tests - multi-component flows",
                        "success_criteria": "Components work together correctly",
                    },
                },
            },
            {
                "name": "Client E2E",
                "path": "client",
                "type": "playwright",
                "categories": {
                    "e2e": {
                        "path": "e2e",
                        "description": "End-to-end tests - full user journeys in browser",
                        "success_criteria": "Complete user workflows function correctly in real browser",
                    }
                },
            },
        ],
    },
}


def print_header(text, color=Colors.BLUE):
    """Print a formatted header."""
    width = 80
    print(f"\n{color}{'=' * width}{Colors.NC}")
    print(f"{color}{text.center(width)}{Colors.NC}")
    print(f"{color}{'=' * width}{Colors.NC}\n")


def print_section(text, color=Colors.CYAN):
    """Print a section header."""
    print(f"\n{color}{'─' * 80}{Colors.NC}")
    print(f"{color}{text}{Colors.NC}")
    print(f"{color}{'─' * 80}{Colors.NC}\n")


def print_info(text):
    """Print info text."""
    print(f"{Colors.CYAN}ℹ {text}{Colors.NC}")


def print_success(text):
    """Print success text."""
    print(f"{Colors.GREEN}✓ {text}{Colors.NC}")


def print_warning(text):
    """Print warning text."""
    print(f"{Colors.YELLOW}⚠ {text}{Colors.NC}")


def print_error(text):
    """Print error text."""
    print(f"{Colors.RED}✗ {text}{Colors.NC}")


def check_postgresql_config():
    """Verify PostgreSQL configuration is available."""
    print_section("Checking PostgreSQL Configuration")

    # Check for .env files
    project_root = Path(__file__).parent.parent
    wiki_env = project_root / "services" / "wiki" / ".env"
    auth_env = project_root / "services" / "auth" / ".env"

    env_vars_found = []

    # Check wiki service
    if wiki_env.exists():
        try:
            from dotenv import load_dotenv

            load_dotenv(wiki_env)
            if os.environ.get("TEST_DATABASE_URL") or (
                os.environ.get("arcadium_user") and os.environ.get("arcadium_pass")
            ):
                env_vars_found.append("Wiki Service")
        except Exception:
            pass

    # Check auth service
    if auth_env.exists():
        try:
            from dotenv import load_dotenv

            load_dotenv(auth_env)
            if os.environ.get("TEST_DATABASE_URL") or (
                os.environ.get("arcadium_user") and os.environ.get("arcadium_pass")
            ):
                env_vars_found.append("Auth Service")
        except Exception:
            pass

    # Check environment variables directly
    if os.environ.get("TEST_DATABASE_URL") or (
        os.environ.get("arcadium_user") and os.environ.get("arcadium_pass")
    ):
        if "Global" not in env_vars_found:
            env_vars_found.append("Global")

    if env_vars_found:
        print_success(f"PostgreSQL configuration found: {', '.join(env_vars_found)}")
        return True
    else:
        print_error("PostgreSQL configuration not found!")
        print_info(
            "Please ensure .env files exist with TEST_DATABASE_URL or (arcadium_user and arcadium_pass)"
        )
        return False


def run_pytest_category(
    service_path, category_path, category_name, description, success_criteria
):
    """Run a pytest test category."""
    project_root = Path(__file__).parent.parent
    full_path = project_root / service_path / category_path

    if not full_path.exists():
        return None, f"Path not found: {full_path}"

    print(f"\n{Colors.MAGENTA}Running: {category_name}{Colors.NC}")
    print(f"{Colors.CYAN}  Description: {description}{Colors.NC}")
    print(f"{Colors.CYAN}  Success Criteria: {success_criteria}{Colors.NC}")
    print(f"{Colors.CYAN}  Path: {category_path}{Colors.NC}\n")

    start_time = time.time()

    try:
        result = subprocess.run(
            [
                "python",
                "-m",
                "pytest",
                str(full_path),
                "-v",
                "--tb=short",
                "--durations=10",
            ],
            cwd=project_root / service_path,
            capture_output=False,
            text=True,
            check=False,
        )
        elapsed = time.time() - start_time
        return result.returncode == 0, elapsed
    except Exception:
        elapsed = time.time() - start_time
        return False, elapsed


def run_pytest_pattern(
    service_path, pattern, category_name, description, success_criteria
):
    """Run pytest with a file pattern."""
    project_root = Path(__file__).parent.parent
    full_path = project_root / service_path

    print(f"\n{Colors.MAGENTA}Running: {category_name}{Colors.NC}")
    print(f"{Colors.CYAN}  Description: {description}{Colors.NC}")
    print(f"{Colors.CYAN}  Success Criteria: {success_criteria}{Colors.NC}")
    print(f"{Colors.CYAN}  Pattern: {pattern}{Colors.NC}\n")

    start_time = time.time()

    try:
        result = subprocess.run(
            ["python", "-m", "pytest", pattern, "-v", "--tb=short", "--durations=10"],
            cwd=full_path,
            capture_output=False,
            text=True,
            check=False,
        )
        elapsed = time.time() - start_time
        return result.returncode == 0, elapsed
    except Exception:
        elapsed = time.time() - start_time
        return False, elapsed


def run_vitest_category(
    service_path, category_path, category_name, description, success_criteria
):
    """Run a Vitest test category."""
    project_root = Path(__file__).parent.parent
    full_path = project_root / service_path / category_path

    if not full_path.exists():
        return None, f"Path not found: {full_path}"

    print(f"\n{Colors.MAGENTA}Running: {category_name}{Colors.NC}")
    print(f"{Colors.CYAN}  Description: {description}{Colors.NC}")
    print(f"{Colors.CYAN}  Success Criteria: {success_criteria}{Colors.NC}")
    print(f"{Colors.CYAN}  Path: {category_path}{Colors.NC}\n")

    start_time = time.time()

    try:
        result = subprocess.run(
            ["npm", "run", "test", "--", category_path],
            cwd=project_root / service_path,
            capture_output=False,
            text=True,
            check=False,
        )
        elapsed = time.time() - start_time
        return result.returncode == 0, elapsed
    except Exception:
        elapsed = time.time() - start_time
        return False, elapsed


def run_playwright_category(
    service_path, category_path, category_name, description, success_criteria
):
    """Run a Playwright test category."""
    project_root = Path(__file__).parent.parent
    full_path = project_root / service_path / category_path

    if not full_path.exists():
        return None, f"Path not found: {full_path}"

    print(f"\n{Colors.MAGENTA}Running: {category_name}{Colors.NC}")
    print(f"{Colors.CYAN}  Description: {description}{Colors.NC}")
    print(f"{Colors.CYAN}  Success Criteria: {success_criteria}{Colors.NC}")
    print(f"{Colors.CYAN}  Path: {category_path}{Colors.NC}\n")

    start_time = time.time()

    try:
        result = subprocess.run(
            ["npm", "run", "test:e2e", "--", category_path],
            cwd=project_root / service_path,
            capture_output=False,
            text=True,
            check=False,
        )
        elapsed = time.time() - start_time
        return result.returncode == 0, elapsed
    except Exception:
        elapsed = time.time() - start_time
        return False, elapsed


def run_backend_tests():
    """Run all backend tests."""
    print_header("BACKEND TESTS", Colors.BLUE)

    results = defaultdict(list)
    total_passed = 0
    total_failed = 0
    total_skipped = 0

    for service in TEST_CATEGORIES["backend"]["services"]:
        service_name = service["name"]
        service_path = service["path"]

        print_section(f"{service_name} Tests")

        for cat_name, cat_config in service["categories"].items():
            cat_path = cat_config.get("path")
            pattern = cat_config.get("pattern")
            description = cat_config.get("description", "")
            success_criteria = cat_config.get("success_criteria", "")

            if pattern:
                success, elapsed = run_pytest_pattern(
                    service_path,
                    pattern,
                    f"{service_name} - {cat_name}",
                    description,
                    success_criteria,
                )
            else:
                success, elapsed = run_pytest_category(
                    service_path,
                    cat_path,
                    f"{service_name} - {cat_name}",
                    description,
                    success_criteria,
                )

            if success is None:
                print_warning(f"Skipped {cat_name}: {elapsed}")
                total_skipped += 1
            elif success:
                print_success(f"{cat_name} passed in {elapsed:.2f}s")
                total_passed += 1
                results[service_name].append(("PASS", cat_name, elapsed))
            else:
                print_error(f"{cat_name} failed in {elapsed:.2f}s")
                total_failed += 1
                results[service_name].append(("FAIL", cat_name, elapsed))

    return results, total_passed, total_failed, total_skipped


def run_frontend_tests():
    """Run all frontend tests."""
    print_header("FRONTEND TESTS", Colors.BLUE)

    results = defaultdict(list)
    total_passed = 0
    total_failed = 0
    total_skipped = 0

    for service in TEST_CATEGORIES["frontend"]["services"]:
        service_name = service["name"]
        service_path = service["path"]
        service_type = service.get("type", "vitest")

        print_section(f"{service_name} Tests")

        for cat_name, cat_config in service["categories"].items():
            cat_path = cat_config.get("path")
            description = cat_config.get("description", "")
            success_criteria = cat_config.get("success_criteria", "")

            if service_type == "playwright":
                success, elapsed = run_playwright_category(
                    service_path,
                    cat_path,
                    f"{service_name} - {cat_name}",
                    description,
                    success_criteria,
                )
            else:
                success, elapsed = run_vitest_category(
                    service_path,
                    cat_path,
                    f"{service_name} - {cat_name}",
                    description,
                    success_criteria,
                )

            if success is None:
                print_warning(f"Skipped {cat_name}: {elapsed}")
                total_skipped += 1
            elif success:
                print_success(f"{cat_name} passed in {elapsed:.2f}s")
                total_passed += 1
                results[service_name].append(("PASS", cat_name, elapsed))
            else:
                print_error(f"{cat_name} failed in {elapsed:.2f}s")
                total_failed += 1
                results[service_name].append(("FAIL", cat_name, elapsed))

    return results, total_passed, total_failed, total_skipped


def print_summary(backend_results, frontend_results, backend_stats, frontend_stats):
    """Print test summary."""
    print_header("TEST SUMMARY", Colors.BLUE)

    b_passed, b_failed, b_skipped = backend_stats
    f_passed, f_failed, f_skipped = frontend_stats

    total_passed = b_passed + f_passed
    total_failed = b_failed + f_failed
    total_skipped = b_skipped + f_skipped
    total_tests = total_passed + total_failed + total_skipped

    print(f"\n{Colors.BOLD}Backend Tests:{Colors.NC}")
    print(f"  {Colors.GREEN}Passed: {b_passed}{Colors.NC}")
    print(f"  {Colors.RED}Failed: {b_failed}{Colors.NC}")
    print(f"  {Colors.YELLOW}Skipped: {b_skipped}{Colors.NC}")

    print(f"\n{Colors.BOLD}Frontend Tests:{Colors.NC}")
    print(f"  {Colors.GREEN}Passed: {f_passed}{Colors.NC}")
    print(f"  {Colors.RED}Failed: {f_failed}{Colors.NC}")
    print(f"  {Colors.YELLOW}Skipped: {f_skipped}{Colors.NC}")

    print(f"\n{Colors.BOLD}Total:{Colors.NC}")
    print(f"  {Colors.GREEN}Passed: {total_passed}{Colors.NC}")
    print(f"  {Colors.RED}Failed: {total_failed}{Colors.NC}")
    print(f"  {Colors.YELLOW}Skipped: {total_skipped}{Colors.NC}")
    print(f"  Total Categories: {total_tests}")

    if total_failed == 0:
        print(f"\n{Colors.GREEN}{Colors.BOLD}✓ All tests passed!{Colors.NC}")
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}✗ Some tests failed{Colors.NC}")

    # Print detailed results
    if backend_results:
        print(f"\n{Colors.BOLD}Backend Details:{Colors.NC}")
        for service, tests in backend_results.items():
            print(f"  {service}:")
            for status, name, elapsed in tests:
                color = Colors.GREEN if status == "PASS" else Colors.RED
                print(f"    {color}{status}{Colors.NC}: {name} ({elapsed:.2f}s)")

    if frontend_results:
        print(f"\n{Colors.BOLD}Frontend Details:{Colors.NC}")
        for service, tests in frontend_results.items():
            print(f"  {service}:")
            for status, name, elapsed in tests:
                color = Colors.GREEN if status == "PASS" else Colors.RED
                print(f"    {color}{status}{Colors.NC}: {name} ({elapsed:.2f}s)")


def main():
    """Main test runner."""
    print_header("ARCADIUM PROJECT - UNIFIED TEST RUNNER", Colors.BOLD + Colors.BLUE)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Check PostgreSQL configuration
    if not check_postgresql_config():
        print_error("Cannot proceed without PostgreSQL configuration")
        sys.exit(1)

    # Set test environment
    os.environ["FLASK_ENV"] = "testing"

    # Run backend tests
    backend_results, b_passed, b_failed, b_skipped = run_backend_tests()

    # Run frontend tests
    frontend_results, f_passed, f_failed, f_skipped = run_frontend_tests()

    # Print summary
    print_summary(
        backend_results,
        frontend_results,
        (b_passed, b_failed, b_skipped),
        (f_passed, f_failed, f_skipped),
    )

    # Exit with appropriate code
    if b_failed + f_failed == 0:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
