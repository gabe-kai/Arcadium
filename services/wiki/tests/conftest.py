"""Pytest configuration and fixtures"""

import os

import pytest

# Set test environment before importing app
os.environ["FLASK_ENV"] = "testing"

# Use TEST_DATABASE_URL from .env if available, otherwise construct from environment variables
# This allows using the same database connection approach as development
TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL")
if not TEST_DATABASE_URL:
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
        # If no credentials, use the regular DATABASE_URL (from .env)
        TEST_DATABASE_URL = os.environ.get("DATABASE_URL")
        if not TEST_DATABASE_URL:
            raise ValueError(
                "TEST_DATABASE_URL, DATABASE_URL, or (arcadium_user and arcadium_pass) environment variables are required for testing."
            )


# Skip database creation check - use existing database connection from .env
# The database should already exist and be accessible via TEST_DATABASE_URL or DATABASE_URL


@pytest.fixture(scope="function")
def app():
    """Create application for testing"""
    from app import create_app

    app = create_app("testing")

    # Use TEST_DATABASE_URL if set, otherwise let TestingConfig use its default
    if TEST_DATABASE_URL:
        app.config["SQLALCHEMY_DATABASE_URI"] = TEST_DATABASE_URL

    with app.app_context():
        from app import db

        # Ensure tables exist - don't drop, just create if missing
        # This avoids DROP TABLE timeout issues entirely
        db.create_all()

        yield app

        # Clean up: rollback any uncommitted transactions
        # Don't drop or truncate tables - let them persist between tests
        # This is faster and avoids all timeout/lock issues
        try:
            db.session.rollback()
            db.session.close()
        except Exception:
            pass
        finally:
            db.session.remove()


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Create test CLI runner"""
    return app.test_cli_runner()
