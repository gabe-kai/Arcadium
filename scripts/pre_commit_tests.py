#!/usr/bin/env python3
"""
Pre-commit hook to run Wiki Service tests.
This hook runs the Wiki Service test suite to catch failures before committing.
"""
import os
import subprocess
import sys
from pathlib import Path

# Force unbuffered output
os.environ["PYTHONUNBUFFERED"] = "1"

# Colors for output
RED = "\033[0;31m"
GREEN = "\033[0;32m"
YELLOW = "\033[1;33m"
NC = "\033[0m"  # No Color


def print_step(message, use_color=False):
    """Print a step message."""
    if use_color:
        print(message, file=sys.stderr, flush=True)
    else:
        print(message, file=sys.stderr, flush=True)


def main():
    """Run the pre-commit tests."""
    print_step("")
    print_step("==========================================")
    print_step("Running pre-commit tests...")
    print_step("==========================================")
    print_step("")

    # Get the project root (where .git is located)
    # This script is in scripts/, so go up one level
    script_dir = Path(__file__).parent
    project_root = script_dir.parent

    # Change to project root
    os.chdir(project_root)

    # Check if we're in the Arcadium project root
    print_step(f"{GREEN}[CHECK]{NC} Verifying project structure...")
    if (
        not (project_root / "requirements.txt").exists()
        or not (project_root / "services" / "wiki").exists()
    ):
        print_step(
            f"{YELLOW}Warning: Not in Arcadium project root. Skipping tests.{NC}"
        )
        sys.exit(0)
    print_step("  ✓ Project structure OK")

    # Check if pytest is available
    print_step(f"{GREEN}[CHECK]{NC} Checking pytest availability...")
    try:
        result = subprocess.run(
            ["python", "-m", "pytest", "--version"],
            capture_output=True,
            text=True,
            check=True,
        )
        pytest_version = result.stdout.strip()
        print_step(f"  ✓ pytest found: {pytest_version}")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print_step(f"{YELLOW}Warning: pytest not found. Skipping tests.{NC}")
        print_step("Install dependencies: pip install -r requirements.txt")
        sys.exit(0)

    # Check if PostgreSQL is available (basic check)
    print_step(f"{GREEN}[CHECK]{NC} Checking PostgreSQL tools...")
    try:
        subprocess.run(["psql", "--version"], capture_output=True, check=True)
        print_step("  ✓ psql found")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print_step(f"  {YELLOW}⚠ psql not found. Database may not be available.{NC}")
        print_step("  Tests may fail if database is not accessible.")

    # Set test environment
    print_step("")
    print_step(f"{GREEN}[1/4]{NC} Setting FLASK_ENV=testing...")
    os.environ["FLASK_ENV"] = "testing"
    print_step("  ✓ FLASK_ENV set to testing")

    # Load .env file from services/wiki directory if it exists
    print_step("")
    print_step(f"{GREEN}[2/4]{NC} Loading environment variables...")
    wiki_env_path = project_root / "services" / "wiki" / ".env"
    if wiki_env_path.exists():
        print_step("  → Found services/wiki/.env file")
        print_step("  → Loading variables using Python dotenv...")

        try:
            from dotenv import load_dotenv

            # Load the .env file
            load_dotenv(wiki_env_path)
            vars_found = []
            for key in [
                "DATABASE_URL",
                "TEST_DATABASE_URL",
                "arcadium_user",
                "arcadium_pass",
                "DB_HOST",
                "DB_PORT",
                "DB_NAME",
                "TEST_DB_NAME",
            ]:
                if os.environ.get(key):
                    vars_found.append(key)

            if vars_found:
                vars_str = ", ".join(vars_found)
                print_step(f"  ✓ Loaded {len(vars_found)} variables: {vars_str}")
            else:
                print_step("  ⚠ No database variables found in .env")
        except ImportError:
            print_step(f"  {RED}✗ ERROR: python-dotenv not installed{NC}")
            sys.exit(1)
        except Exception as e:
            print_step(f"  {RED}✗ ERROR loading .env: {e}{NC}")
            sys.exit(1)
    else:
        print_step(f"  {YELLOW}⚠ No .env file found at services/wiki/.env{NC}")
        print_step("  → Will use environment variables or defaults")

    # Change to wiki service directory
    print_step("")
    print_step(f"{GREEN}[3/4]{NC} Changing to services/wiki directory...")
    wiki_dir = project_root / "services" / "wiki"
    if not wiki_dir.exists():
        print_step(f"  {RED}✗ Failed to change to services/wiki directory{NC}")
        sys.exit(1)
    os.chdir(wiki_dir)
    print_step("  ✓ Changed to services/wiki")

    # Show database connection info (without password)
    print_step("")
    print_step("Database configuration:")
    test_db_url = os.environ.get("TEST_DATABASE_URL")
    db_url = os.environ.get("DATABASE_URL")
    arcadium_user = os.environ.get("arcadium_user")
    if test_db_url:
        db_info = (
            test_db_url.split("@")[0] + "@***" if "@" in test_db_url else test_db_url
        )
        print_step(f"  → Using TEST_DATABASE_URL: {db_info}")
    elif db_url:
        db_info = db_url.split("@")[0] + "@***" if "@" in db_url else db_url
        print_step(f"  → Using DATABASE_URL: {db_info}")
    elif arcadium_user:
        print_step(f"  → Using arcadium_user: {arcadium_user}")
        print_step(
            f"  → Database: {os.environ.get('TEST_DB_NAME', 'arcadium_testing_wiki')}"
        )
    else:
        print_step(f"  {YELLOW}⚠ No database credentials found{NC}")

    # Run tests
    print_step("")
    print_step(f"{GREEN}[4/4]{NC} Running Wiki Service tests...")
    print_step("  → This may take a few minutes...")
    print_step("  → Starting pytest...")
    print_step("")

    # Run pytest with progress indicators
    try:
        result = subprocess.run(
            ["python", "-m", "pytest", "--tb=short", "-v", "--durations=10"],
            check=True,
        )
        print_step("")
        print_step(f"{GREEN}✓ All tests passed!{NC}")
        print_step("")
        sys.exit(0)
    except subprocess.CalledProcessError as e:
        print_step("")
        print_step(f"{RED}✗ Tests failed! (exit code: {e.returncode}){NC}")
        print_step("")
        print_step("Please fix failing tests before committing.")
        print_step("To skip this check (not recommended), use: git commit --no-verify")
        print_step("")
        sys.exit(e.returncode)
    except Exception as e:
        print_step("")
        print_step(f"{RED}✗ Error running tests: {e}{NC}")
        print_step("")
        sys.exit(1)


if __name__ == "__main__":
    main()
