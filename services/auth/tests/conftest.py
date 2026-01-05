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
        # Use explicit connection to ensure schema is created with proper permissions
        try:
            # Check if schema exists first
            schema_check = db.session.execute(
                db.text(
                    "SELECT 1 FROM information_schema.schemata WHERE schema_name = 'auth'"
                )
            ).fetchone()

            if not schema_check:
                # Create schema with explicit owner (use current user)
                db.session.execute(db.text("CREATE SCHEMA auth"))
                db.session.commit()
        except Exception:
            # Schema might already exist or permission issue
            db.session.rollback()
            # Try to continue - schema might exist but check failed
            # If schema doesn't exist and we can't create it, db.create_all() will fail with a clearer error

        # Ensure tables exist - don't drop, just create if missing
        # This avoids DROP TABLE timeout issues entirely
        try:
            # Set search_path to include auth schema for this session
            db.session.execute(db.text("SET search_path TO auth, public"))
            db.session.commit()

            # Create all tables
            db.create_all()
            db.session.commit()

            # Verify tables were created
            tables_check = db.session.execute(
                db.text(
                    """
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_schema = 'auth'
                    AND table_name IN ('users', 'refresh_tokens', 'token_blacklist', 'password_history')
                """
                )
            ).fetchall()

            if not tables_check:
                raise RuntimeError(
                    "Tables were not created in auth schema. Check permissions and schema setup."
                )

            db.session.close()
            db.session.remove()

            # Clean all data for isolation (preserve alembic_version)
            # Re-establish connection with schema
            db.session.execute(db.text("SET search_path TO auth, public"))
            for table in reversed(db.metadata.sorted_tables):
                if table.name == "alembic_version":
                    continue
                db.session.execute(table.delete())
            db.session.commit()
            db.session.close()
            db.session.remove()
        except Exception as e:
            db.session.rollback()
            db.session.close()
            db.session.remove()
            raise RuntimeError(f"Failed to create tables in auth schema: {e}") from e

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
