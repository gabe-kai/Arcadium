import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration"""

    SECRET_KEY = os.environ.get("SECRET_KEY") or "dev-secret-key-change-in-production"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Database configuration
    # Can be set via DATABASE_URL or constructed from arcadium_user/arcadium_pass
    # Format: postgresql://username:password@host:port/database
    # Never hardcode passwords in source code!
    # Note: TestingConfig overrides this attribute, so validation is skipped for tests
    _database_url = os.environ.get("DATABASE_URL")

    # If DATABASE_URL not set, construct from arcadium_user and arcadium_pass
    if not _database_url:
        db_user = os.environ.get("arcadium_user")
        db_pass = os.environ.get("arcadium_pass")
        db_host = os.environ.get("DB_HOST", "localhost")
        db_port = os.environ.get("DB_PORT", "5432")
        db_name = os.environ.get("DB_NAME", "arcadium_wiki")

        if db_user and db_pass:
            _database_url = (
                f"postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
            )

    if not _database_url and os.environ.get("FLASK_ENV") != "testing":
        raise ValueError(
            "DATABASE_URL or (arcadium_user and arcadium_pass) environment variables are required. "
            "Set them in your .env file or environment. "
            "Example: DATABASE_URL=postgresql://user:pass@localhost:5432/arcadium_wiki"
            "Or: arcadium_user=user, arcadium_pass=pass, DB_NAME=arcadium_wiki"
        )
    SQLALCHEMY_DATABASE_URI = (
        _database_url or "sqlite:///:memory:"
    )  # Fallback for testing

    # Database connection pooling configuration
    # These settings optimize connection pool for production workloads
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_size": int(
            os.environ.get("DB_POOL_SIZE", "10")
        ),  # Number of connections to maintain
        "max_overflow": int(
            os.environ.get("DB_MAX_OVERFLOW", "20")
        ),  # Max connections beyond pool_size
        "pool_timeout": int(
            os.environ.get("DB_POOL_TIMEOUT", "30")
        ),  # Seconds to wait for connection
        "pool_recycle": int(
            os.environ.get("DB_POOL_RECYCLE", "3600")
        ),  # Recycle connections after 1 hour
        "pool_pre_ping": True,  # Verify connections before using (prevents stale connections)
        "echo": os.environ.get("DB_ECHO", "false").lower()
        == "true",  # Log SQL queries (for debugging)
    }

    # Wiki-specific settings
    WIKI_DATA_DIR = os.environ.get("WIKI_DATA_DIR") or "data"
    WIKI_PAGES_DIR = os.path.join(WIKI_DATA_DIR, "pages")
    WIKI_UPLOADS_DIR = os.path.join(WIKI_DATA_DIR, "uploads", "images")

    # Auth service integration
    AUTH_SERVICE_URL = os.environ.get("AUTH_SERVICE_URL") or "http://localhost:8000"
    AUTH_SERVICE_TOKEN = os.environ.get("AUTH_SERVICE_TOKEN") or ""

    # Notification service integration
    NOTIFICATION_SERVICE_URL = (
        os.environ.get("NOTIFICATION_SERVICE_URL") or "http://localhost:5002"
    )
    NOTIFICATION_SERVICE_TOKEN = os.environ.get("NOTIFICATION_SERVICE_TOKEN") or ""


class DevelopmentConfig(Config):
    """Development configuration"""

    DEBUG = True


class ProductionConfig(Config):
    """Production configuration"""

    DEBUG = False


class TestingConfig(Config):
    """Testing configuration"""

    TESTING = True
    # Test database - uses PostgreSQL for accurate testing (matches production)
    # Can be set via TEST_DATABASE_URL or constructed from arcadium_user/arcadium_pass
    _test_db_url = os.environ.get("TEST_DATABASE_URL")

    # Override engine options for testing - use same settings as development
    # but with smaller pool to avoid connection issues
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_size": 5,  # Small pool for tests
        "max_overflow": 5,  # Limited overflow for tests
        "pool_timeout": 10,  # Reasonable timeout for tests
        "pool_pre_ping": True,
        "connect_args": {
            "connect_timeout": 10,  # Connection timeout in seconds
            # Disable statement timeout for test DDL to avoid DROP/CREATE timeouts
            "options": "-c statement_timeout=0",
        },
    }
    if not _test_db_url:
        db_user = os.environ.get("arcadium_user")
        db_pass = os.environ.get("arcadium_pass")
        db_host = os.environ.get("DB_HOST", "localhost")
        db_port = os.environ.get("DB_PORT", "5432")
        if db_user and db_pass:
            _test_db_url = f"postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/arcadium_testing_wiki"
    SQLALCHEMY_DATABASE_URI = _test_db_url or "sqlite:///:memory:"
    WIKI_DATA_DIR = "test_data"


config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig,
}
