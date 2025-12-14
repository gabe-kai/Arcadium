import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Base configuration"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Database configuration - MUST be set via DATABASE_URL environment variable
    # Format: postgresql://username:password@host:port/database
    # Never hardcode passwords in source code!
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    if not SQLALCHEMY_DATABASE_URI:
        raise ValueError(
            "DATABASE_URL environment variable is required. "
            "Set it in your .env file or environment. "
            "Example: postgresql://postgres:password@localhost:5432/wiki"
        )
    
    # Wiki-specific settings
    WIKI_DATA_DIR = os.environ.get('WIKI_DATA_DIR') or 'data'
    WIKI_PAGES_DIR = os.path.join(WIKI_DATA_DIR, 'pages')
    WIKI_UPLOADS_DIR = os.path.join(WIKI_DATA_DIR, 'uploads', 'images')
    
    # Auth service integration
    AUTH_SERVICE_URL = os.environ.get('AUTH_SERVICE_URL') or 'http://localhost:5001'
    AUTH_SERVICE_TOKEN = os.environ.get('AUTH_SERVICE_TOKEN') or ''
    
    # Notification service integration
    NOTIFICATION_SERVICE_URL = os.environ.get('NOTIFICATION_SERVICE_URL') or 'http://localhost:5002'
    NOTIFICATION_SERVICE_TOKEN = os.environ.get('NOTIFICATION_SERVICE_TOKEN') or ''

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    # Test database - uses SQLite for faster test execution
    # Can be overridden via TEST_DATABASE_URL for PostgreSQL testing
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or \
        'sqlite:///:memory:'
    WIKI_DATA_DIR = 'test_data'

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

