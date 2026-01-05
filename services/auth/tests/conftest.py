"""Pytest configuration and fixtures"""

import os
from pathlib import Path

import pytest

# Load .env file if it exists (before setting FLASK_ENV)
try:
    from dotenv import load_dotenv

    # Load .env from the services/auth directory
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
os.environ.setdefault("DB_POOL_RECYCLE", "3600")

# Use TEST_DATABASE_URL from .env if available
TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL")
if not TEST_DATABASE_URL:
    # Prefer using DATABASE_URL and just changing the database name
    DATABASE_URL = os.environ.get("DATABASE_URL")
    if DATABASE_URL:
        # Parse DATABASE_URL and change database name to test database
        from urllib.parse import urlparse, urlunparse

        parsed = urlparse(DATABASE_URL)
        TEST_DB_NAME = os.environ.get("TEST_DB_NAME", "arcadium_testing_auth")
        TEST_DATABASE_URL = urlunparse(parsed._replace(path=f"/{TEST_DB_NAME}"))
        os.environ["TEST_DATABASE_URL"] = TEST_DATABASE_URL
    else:
        # Fall back to constructing from individual variables
        TEST_DB_USER = os.environ.get("arcadium_user")
        TEST_DB_PASSWORD = os.environ.get("arcadium_pass")
        TEST_DB_HOST = os.environ.get("DB_HOST", "localhost")
        TEST_DB_PORT = os.environ.get("DB_PORT", "5432")
        TEST_DB_NAME = os.environ.get("TEST_DB_NAME", "arcadium_testing_auth")

        if TEST_DB_USER and TEST_DB_PASSWORD:
            TEST_DATABASE_URL = f"postgresql://{TEST_DB_USER}:{TEST_DB_PASSWORD}@{TEST_DB_HOST}:{TEST_DB_PORT}/{TEST_DB_NAME}"
            os.environ["TEST_DATABASE_URL"] = TEST_DATABASE_URL
        else:
            raise ValueError(
                "TEST_DATABASE_URL, DATABASE_URL, or (arcadium_user and arcadium_pass) environment variables are required for testing."
            )


@pytest.fixture(scope="function")
def app():
    """Create application for testing"""
    from app import create_app

    app = create_app("testing")

    # Use TEST_DATABASE_URL if set
    if TEST_DATABASE_URL:
        app.config["SQLALCHEMY_DATABASE_URI"] = TEST_DATABASE_URL

    # Create tables in a separate app context, then exit it
    with app.app_context():
        from app import db

        # Create schema if it doesn't exist
        try:
            db.session.execute(db.text("CREATE SCHEMA IF NOT EXISTS auth"))
            db.session.commit()
        except Exception:
            # Schema might already exist, continue
            db.session.rollback()

        # Ensure tables exist - don't drop, just create if missing
        # This avoids DROP TABLE timeout issues entirely
        try:
            db.create_all()
            db.session.commit()
            db.session.close()
            db.session.remove()

            # Clean all data for isolation (preserve alembic_version)
            for table in reversed(db.metadata.sorted_tables):
                if table.name == "alembic_version":
                    continue
                db.session.execute(table.delete())
            db.session.commit()
            db.session.close()
            db.session.remove()
        except Exception:
            db.session.rollback()
            db.session.close()
            db.session.remove()
            raise

    yield app

    # Clean up: ensure all connections are closed and removed
    with app.app_context():
        from app import db

        try:
            db.session.rollback()
            db.session.close()
        except Exception:
            pass
        finally:
            db.session.remove()
            # Close all connections in the pool
            db.engine.dispose(close=True)


@pytest.fixture(scope="function")
def client(app):
    """Create test client"""
    return app.test_client()


@pytest.fixture(scope="function")
def db_session(app):
    """Create database session"""
    with app.app_context():
        from app import db

        yield db.session
        try:
            db.session.rollback()
            db.session.close()
        except Exception:
            pass
        finally:
            db.session.remove()
