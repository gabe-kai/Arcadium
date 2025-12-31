"""Pytest configuration and fixtures"""

import os
from pathlib import Path

import pytest

# Load .env file if it exists (before setting FLASK_ENV)
# This ensures we have access to DATABASE_URL and other credentials
try:
    from dotenv import load_dotenv

    # Load .env from the services/wiki directory
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    # dotenv not available, will rely on environment variables
    pass

# Set test environment before importing app
os.environ["FLASK_ENV"] = "testing"
# Use minimal DB pool for tests to avoid too many connections
os.environ.setdefault("DB_POOL_SIZE", "1")
os.environ.setdefault("DB_MAX_OVERFLOW", "0")
os.environ.setdefault("DB_POOL_TIMEOUT", "5")

# Use TEST_DATABASE_URL from .env if available
# Otherwise, use DATABASE_URL and change the database name to the test database
# This ensures we use the same credentials as development but point to the test database
TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL")
if not TEST_DATABASE_URL:
    # Prefer using DATABASE_URL and just changing the database name
    DATABASE_URL = os.environ.get("DATABASE_URL")
    if DATABASE_URL:
        # Parse DATABASE_URL and change database name to test database
        from urllib.parse import urlparse, urlunparse

        parsed = urlparse(DATABASE_URL)
        TEST_DB_NAME = os.environ.get("TEST_DB_NAME", "arcadium_testing_wiki")
        TEST_DATABASE_URL = urlunparse(parsed._replace(path=f"/{TEST_DB_NAME}"))
        os.environ["TEST_DATABASE_URL"] = TEST_DATABASE_URL
    else:
        # Fall back to constructing from individual variables
        TEST_DB_USER = os.environ.get("arcadium_user")
        TEST_DB_PASSWORD = os.environ.get("arcadium_pass")
        TEST_DB_HOST = os.environ.get("DB_HOST", "localhost")
        TEST_DB_PORT = os.environ.get("DB_PORT", "5432")
        TEST_DB_NAME = os.environ.get("TEST_DB_NAME", "arcadium_testing_wiki")

        if TEST_DB_USER and TEST_DB_PASSWORD:
            TEST_DATABASE_URL = f"postgresql://{TEST_DB_USER}:{TEST_DB_PASSWORD}@{TEST_DB_HOST}:{TEST_DB_PORT}/{TEST_DB_NAME}"
            os.environ["TEST_DATABASE_URL"] = TEST_DATABASE_URL
        else:
            raise ValueError(
                "TEST_DATABASE_URL, DATABASE_URL, or (arcadium_user and arcadium_pass) environment variables are required for testing."
            )

# Debug: Print TEST_DATABASE_URL (with password masked) if pytest is run with -v
if os.environ.get("PYTEST_CURRENT_TEST"):
    import sys

    if "-v" in sys.argv or "-vv" in sys.argv or "-vvv" in sys.argv:
        masked_url = TEST_DATABASE_URL
        if "@" in masked_url:
            parts = masked_url.split("@")
            if "://" in parts[0]:
                cred_part = parts[0].split("://")[1]
                if ":" in cred_part:
                    user_pass = cred_part.split(":")
                    masked_url = (
                        f"{parts[0].split('://')[0]}://{user_pass[0]}:***@{parts[1]}"
                    )
        print(f"[conftest] Using TEST_DATABASE_URL: {masked_url}", file=sys.stderr)


# Skip database creation check - use existing database connection from .env
# The database should already exist and be accessible via TEST_DATABASE_URL or DATABASE_URL


@pytest.fixture(scope="function")
def app():
    """Create application for testing"""
    import sys

    print("[conftest] Creating app...", file=sys.stderr, flush=True)
    from app import create_app

    app = create_app("testing")
    print("[conftest] App created", file=sys.stderr, flush=True)

    # Use TEST_DATABASE_URL if set, otherwise let TestingConfig use its default
    if TEST_DATABASE_URL:
        app.config["SQLALCHEMY_DATABASE_URI"] = TEST_DATABASE_URL
        masked_url = (
            TEST_DATABASE_URL.split("@")[-1]
            if "@" in TEST_DATABASE_URL
            else TEST_DATABASE_URL
        )
        print(
            f"[conftest] Using database: ...@{masked_url}", file=sys.stderr, flush=True
        )

    print("[conftest] Entering app context for setup...", file=sys.stderr, flush=True)
    # Create tables in a separate app context, then exit it
    with app.app_context():
        from app import db

        print(
            "[conftest] App context entered, importing db", file=sys.stderr, flush=True
        )

        # Ensure tables exist - don't drop, just create if missing
        # This avoids DROP TABLE timeout issues entirely
        print("[conftest] Calling db.create_all()...", file=sys.stderr, flush=True)
        try:
            db.create_all()
            # Ensure any pending operations are committed and session is clean
            db.session.commit()
            db.session.close()
            db.session.remove()
            print(
                "[conftest] db.create_all() completed, session closed and removed",
                file=sys.stderr,
                flush=True,
            )

            # Clean all data for isolation (preserve alembic_version)
            for table in reversed(db.metadata.sorted_tables):
                if table.name == "alembic_version":
                    continue
                db.session.execute(table.delete())
            db.session.commit()
            db.session.remove()
            print(
                "[conftest] Database tables cleaned for test isolation",
                file=sys.stderr,
                flush=True,
            )
        except Exception as e:
            print(
                f"[conftest] ERROR in db.create_all(): {e}", file=sys.stderr, flush=True
            )
            db.session.rollback()
            db.session.remove()
            raise

    print(
        "[conftest] Exited setup app context, yielding app...",
        file=sys.stderr,
        flush=True,
    )
    # Yield app without an active app context - tests will create their own
    yield app
    print("[conftest] Test completed, cleaning up...", file=sys.stderr, flush=True)

    # Clean up in a new app context if needed
    with app.app_context():
        from app import db

        try:
            db.session.rollback()
            db.session.close()
        except Exception:
            pass
        finally:
            db.session.remove()
            # Ensure connections are released back to the pool / closed
            try:
                db.engine.dispose()
            except Exception:
                pass
    print("[conftest] Cleanup completed", file=sys.stderr, flush=True)


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Create test CLI runner"""
    return app.test_cli_runner()
