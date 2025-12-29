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
        db_name = os.environ.get("DB_NAME", "arcadium_auth")

        if db_user and db_pass:
            _database_url = (
                f"postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
            )

    if _database_url and "?" in _database_url:
        # Remove query parameters (e.g., ?schema=public) as they're not valid for PostgreSQL connection strings
        _database_url = _database_url.split("?")[0]

    if not _database_url and os.environ.get("FLASK_ENV") != "testing":
        raise ValueError(
            "DATABASE_URL or (arcadium_user and arcadium_pass) environment variables are required. "
            "Set them in your .env file or environment. "
            "Example: DATABASE_URL=postgresql://user:pass@localhost:5432/arcadium_auth"
            "Or: arcadium_user=user, arcadium_pass=pass, DB_NAME=arcadium_auth"
        )
    SQLALCHEMY_DATABASE_URI = (
        _database_url or "sqlite:///:memory:"
    )  # Fallback for testing

    # Database connection pooling configuration
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_size": int(os.environ.get("DB_POOL_SIZE", "10")),
        "max_overflow": int(os.environ.get("DB_MAX_OVERFLOW", "20")),
        "pool_timeout": int(os.environ.get("DB_POOL_TIMEOUT", "30")),
        "pool_recycle": int(os.environ.get("DB_POOL_RECYCLE", "3600")),
        "pool_pre_ping": True,
        "echo": os.environ.get("DB_ECHO", "false").lower() == "true",
    }

    # JWT Configuration
    JWT_SECRET_KEY = (
        os.environ.get("JWT_SECRET_KEY")
        or os.environ.get("SECRET_KEY")
        or "jwt-secret-key-change-in-production"
    )
    JWT_ACCESS_TOKEN_EXPIRATION = int(
        os.environ.get("JWT_ACCESS_TOKEN_EXPIRATION", "3600")
    )  # 1 hour
    JWT_REFRESH_TOKEN_EXPIRATION = int(
        os.environ.get("JWT_REFRESH_TOKEN_EXPIRATION", "604800")
    )  # 7 days
    JWT_SERVICE_TOKEN_EXPIRATION = int(
        os.environ.get("JWT_SERVICE_TOKEN_EXPIRATION", "7776000")
    )  # 90 days

    # Password Configuration
    BCRYPT_ROUNDS = int(os.environ.get("BCRYPT_ROUNDS", "12"))
    PASSWORD_MIN_LENGTH = int(os.environ.get("PASSWORD_MIN_LENGTH", "8"))
    PASSWORD_HISTORY_COUNT = int(os.environ.get("PASSWORD_HISTORY_COUNT", "3"))

    # Rate Limiting Configuration
    RATELIMIT_STORAGE_URL = os.environ.get("RATELIMIT_STORAGE_URL", "memory://")
    RATELIMIT_ENABLED = os.environ.get("RATELIMIT_ENABLED", "true").lower() == "true"

    # CORS Configuration
    CORS_ORIGINS = os.environ.get(
        "CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000"
    ).split(",")


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
    if not _test_db_url:
        db_user = os.environ.get("arcadium_user")
        db_pass = os.environ.get("arcadium_pass")
        db_host = os.environ.get("DB_HOST", "localhost")
        db_port = os.environ.get("DB_PORT", "5432")
        if db_user and db_pass:
            _test_db_url = f"postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/arcadium_testing_auth"
    SQLALCHEMY_DATABASE_URI = _test_db_url or "sqlite:///:memory:"
    JWT_SECRET_KEY = "test-jwt-secret-key"
    RATELIMIT_ENABLED = False  # Disable rate limiting in tests


config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig,
}
