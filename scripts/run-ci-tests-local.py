#!/usr/bin/env python3
"""
Simulate CI/CD backend tests locally.

This script replicates the GitHub Actions backend test workflow locally,
allowing you to see CI output without pushing to GitHub.
"""

import os
import subprocess
import sys
from pathlib import Path

# Project root
PROJECT_ROOT = Path(__file__).parent.parent


def check_postgresql():
    """Check if PostgreSQL is available."""
    try:
        result = subprocess.run(
            ["pg_isready", "-h", "localhost", "-p", "5432"],
            capture_output=True,
            text=True,
        )
        return result.returncode == 0
    except FileNotFoundError:
        print("⚠️  PostgreSQL client tools not found. Make sure PostgreSQL is running.")
        return False


def create_test_databases():
    """Create test databases if they don't exist."""
    databases = ["arcadium_testing_wiki", "arcadium_testing_auth"]

    # Get credentials from environment or use defaults
    db_user = os.environ.get("arcadium_user", "postgres")
    db_pass = os.environ.get("arcadium_pass", "")
    db_host = os.environ.get("DB_HOST", "localhost")
    db_port = os.environ.get("DB_PORT", "5432")

    if not db_pass:
        print("⚠️  Warning: arcadium_pass not set. Using empty password.")

    for db_name in databases:
        try:
            # Check if database exists
            check_cmd = [
                "psql",
                "-h",
                db_host,
                "-p",
                db_port,
                "-U",
                db_user,
                "-tc",
                f"SELECT 1 FROM pg_database WHERE datname = '{db_name}'",
            ]

            env = os.environ.copy()
            env["PGPASSWORD"] = db_pass

            result = subprocess.run(
                check_cmd,
                capture_output=True,
                text=True,
                env=env,
            )

            if "1" not in result.stdout:
                # Create database
                create_cmd = [
                    "psql",
                    "-h",
                    db_host,
                    "-p",
                    db_port,
                    "-U",
                    db_user,
                    "-c",
                    f"CREATE DATABASE {db_name}",
                ]

                print(f"Creating test database: {db_name}...")
                result = subprocess.run(
                    create_cmd,
                    capture_output=True,
                    text=True,
                    env=env,
                )

                if result.returncode == 0:
                    print(f"✅ Created database: {db_name}")
                else:
                    print(f"❌ Failed to create database {db_name}: {result.stderr}")
                    return False
            else:
                print(f"✅ Database {db_name} already exists")
        except FileNotFoundError:
            print("⚠️  PostgreSQL client tools (psql) not found.")
            print("   Databases may need to be created manually.")
            return False
        except Exception as e:
            print(f"⚠️  Error checking/creating database {db_name}: {e}")
            return False

    return True


def setup_environment():
    """Set up environment variables like CI does."""
    env = os.environ.copy()

    # Set CI-like environment variables
    env["FLASK_ENV"] = "testing"
    env["DB_HOST"] = os.environ.get("DB_HOST", "localhost")
    env["DB_PORT"] = os.environ.get("DB_PORT", "5432")

    # Set database credentials
    db_user = os.environ.get("arcadium_user", "postgres")
    db_pass = os.environ.get("arcadium_pass", "")

    env["arcadium_user"] = db_user
    env["arcadium_pass"] = db_pass

    # Set TEST_DATABASE_URL for Wiki service
    if not os.environ.get("TEST_DATABASE_URL"):
        env["TEST_DATABASE_URL"] = (
            f"postgresql://{db_user}:{db_pass}@localhost:5432/arcadium_testing_wiki"
        )

    return env


def run_tests():
    """Run the unified test runner."""
    print("=" * 80)
    print("Running Backend Tests (CI Simulation)")
    print("=" * 80)
    print()

    env = setup_environment()

    # Run the unified test runner
    test_script = PROJECT_ROOT / "scripts" / "run-tests.py"

    if not test_script.exists():
        print(f"❌ Test runner not found: {test_script}")
        return False

    print("Executing: python scripts/run-tests.py all")
    print()

    result = subprocess.run(
        [sys.executable, str(test_script), "all"],
        cwd=PROJECT_ROOT,
        env=env,
    )

    return result.returncode == 0


def main():
    """Main entry point."""
    print("=" * 80)
    print("CI/CD Backend Tests - Local Simulation")
    print("=" * 80)
    print()

    # Check PostgreSQL
    print("Checking PostgreSQL connection...")
    if not check_postgresql():
        print("❌ PostgreSQL is not available.")
        print("   Please ensure PostgreSQL is running on localhost:5432")
        return 1
    print("✅ PostgreSQL is available")
    print()

    # Create test databases
    print("Setting up test databases...")
    if not create_test_databases():
        print("⚠️  Database setup had issues, but continuing...")
    print()

    # Run tests
    success = run_tests()

    print()
    print("=" * 80)
    if success:
        print("✅ All tests passed!")
        return 0
    else:
        print("❌ Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
