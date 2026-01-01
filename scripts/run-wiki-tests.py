#!/usr/bin/env python3
"""
Run Wiki Service test suite.
This script runs the full Wiki Service test suite for manual execution.
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
BLUE = "\033[0;34m"
NC = "\033[0m"  # No Color


def main():
    """Run the Wiki Service tests."""
    # Get project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    os.chdir(project_root)

    # Verify project structure
    if (
        not (project_root / "requirements.txt").exists()
        or not (project_root / "services" / "wiki").exists()
    ):
        print(f"{RED}Error: Not in Arcadium project root{NC}", file=sys.stderr)
        sys.exit(1)

    # Check pytest
    try:
        subprocess.run(
            ["python", "-m", "pytest", "--version"],
            capture_output=True,
            check=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        print(f"{RED}Error: pytest not found{NC}", file=sys.stderr)
        print("Install dependencies: pip install -r requirements.txt", file=sys.stderr)
        sys.exit(1)

    # Set test environment
    os.environ["FLASK_ENV"] = "testing"

    # Load .env file if it exists
    wiki_env_path = project_root / "services" / "wiki" / ".env"
    if wiki_env_path.exists():
        try:
            from dotenv import load_dotenv

            load_dotenv(wiki_env_path)
        except ImportError:
            print(f"{RED}Error: python-dotenv not installed{NC}", file=sys.stderr)
            sys.exit(1)

    # Change to wiki service directory
    wiki_dir = project_root / "services" / "wiki"
    if not wiki_dir.exists():
        print(f"{RED}Error: services/wiki directory not found{NC}", file=sys.stderr)
        sys.exit(1)
    os.chdir(wiki_dir)

    # Show database info (without password)
    print(f"{BLUE}{'=' * 80}{NC}")
    print(f"{BLUE}Running Wiki Service Tests{NC}")
    print(f"{BLUE}{'=' * 80}{NC}")
    print()

    test_db_url = os.environ.get("TEST_DATABASE_URL")
    db_url = os.environ.get("DATABASE_URL")
    arcadium_user = os.environ.get("arcadium_user")

    if test_db_url:
        db_info = (
            test_db_url.split("@")[0] + "@***" if "@" in test_db_url else test_db_url
        )
        print(f"Database: {GREEN}{db_info}{NC}")
    elif db_url:
        db_info = db_url.split("@")[0] + "@***" if "@" in db_url else db_url
        print(f"Database: {GREEN}{db_info}{NC}")
    elif arcadium_user:
        test_db_name = os.environ.get("TEST_DB_NAME", "arcadium_testing_wiki")
        print(f"Database: {GREEN}{arcadium_user}@{test_db_name}{NC}")
    else:
        print(f"{YELLOW}⚠ Using default database configuration{NC}")
    print()

    # Run pytest
    print(f"{BLUE}Running pytest...{NC}")
    print()

    try:
        subprocess.run(
            [
                "python",
                "-m",
                "pytest",
                "--tb=short",
                "-v",
                "--durations=10",
                "--color=yes",
            ],
            check=True,
        )
        print()
        print(f"{BLUE}{'=' * 80}{NC}")
        print(f"{GREEN}[OK] All tests passed!{NC}")
        print(f"{BLUE}{'=' * 80}{NC}")
        sys.exit(0)
    except subprocess.CalledProcessError as e:
        print()
        print(f"{BLUE}{'=' * 80}{NC}")
        print(f"{RED}[X] Tests failed (exit code: {e.returncode}){NC}")
        print(f"{BLUE}{'=' * 80}{NC}")
        sys.exit(e.returncode)
    except Exception as e:
        print()
        print(f"{RED}✗ Error running tests: {e}{NC}")
        sys.exit(1)


if __name__ == "__main__":
    main()
