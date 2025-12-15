"""Pytest configuration and fixtures"""
import pytest
import os
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

# Set test environment before importing app
os.environ['FLASK_ENV'] = 'testing'

# PostgreSQL test database configuration
# Use a dedicated test database to avoid conflicts with development data
# These credentials match the development PostgreSQL setup
TEST_DB_NAME = 'wiki_test'
TEST_DB_USER = 'postgres'
TEST_DB_PASSWORD = 'Le555ecure'
TEST_DB_HOST = 'localhost'
TEST_DB_PORT = '5432'

# Construct test database URL
TEST_DATABASE_URL = f'postgresql://{TEST_DB_USER}:{TEST_DB_PASSWORD}@{TEST_DB_HOST}:{TEST_DB_PORT}/{TEST_DB_NAME}'
os.environ['TEST_DATABASE_URL'] = TEST_DATABASE_URL

def ensure_test_database():
    """Ensure the test database exists"""
    # Connect to postgres database to create test database if needed
    admin_url = f'postgresql://{TEST_DB_USER}:{TEST_DB_PASSWORD}@{TEST_DB_HOST}:{TEST_DB_PORT}/postgres'
    try:
        engine = create_engine(admin_url, isolation_level="AUTOCOMMIT")
        with engine.connect() as conn:
            # Check if database exists
            result = conn.execute(
                text(f"SELECT 1 FROM pg_database WHERE datname = '{TEST_DB_NAME}'")
            )
            exists = result.fetchone()
            
            if not exists:
                # Create test database
                conn.execute(text(f'CREATE DATABASE {TEST_DB_NAME}'))
        engine.dispose()
    except Exception as e:
        # Database might already exist or connection failed
        # This is OK - we'll try to use it anyway
        pass

# Ensure test database exists when module is imported
ensure_test_database()

@pytest.fixture(scope='function')
def app():
    """Create application for testing"""
    from app import create_app
    app = create_app('testing')
    
    # Override database URI to use PostgreSQL for tests
    app.config['SQLALCHEMY_DATABASE_URI'] = TEST_DATABASE_URL
    
    with app.app_context():
        from app import db
        # Drop all tables and recreate for clean test state
        db.drop_all()
        db.create_all()
        yield app
        # Clean up after each test
        # Close any open transactions first
        db.session.rollback()
        # Drop all tables (DDL operation, doesn't need commit)
        db.drop_all()
        # Remove the session
        db.session.remove()

@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()

@pytest.fixture
def runner(app):
    """Create test CLI runner"""
    return app.test_cli_runner()

