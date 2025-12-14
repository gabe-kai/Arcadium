"""Pytest configuration and fixtures"""
import pytest
import os

# Set test environment before importing app
os.environ['FLASK_ENV'] = 'testing'
os.environ['TEST_DATABASE_URL'] = 'sqlite:///:memory:'

@pytest.fixture
def app():
    """Create application for testing"""
    # Use in-memory SQLite for testing to avoid PostgreSQL dependency
    from app import create_app
    app = create_app('testing')
    
    # Override database URI to use SQLite for tests
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.app_context():
        from app import db
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()

@pytest.fixture
def runner(app):
    """Create test CLI runner"""
    return app.test_cli_runner()

