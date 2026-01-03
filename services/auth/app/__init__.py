import os

from flask import Flask
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
migrate = Migrate()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[],
    storage_uri="memory://",  # Default, can be overridden in config
)


def create_app(config_name=None):
    """Create and configure the Flask application"""
    app = Flask(__name__)

    # Determine config name
    if config_name is None:
        config_name = os.environ.get("FLASK_ENV", "development")

    # Load configuration
    from config import config

    app.config.from_object(config.get(config_name, config["default"]))

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)

    # Initialize Flask-Limiter
    storage_uri = app.config.get("RATELIMIT_STORAGE_URL", "memory://")
    limiter.storage_uri = storage_uri
    limiter.init_app(app)

    # Disable rate limiting if RATELIMIT_ENABLED is False
    if not app.config.get("RATELIMIT_ENABLED", True):
        limiter.enabled = False

    # Custom error handler for rate limit exceeded (429)
    @app.errorhandler(429)
    def rate_limit_error(e):
        from flask import jsonify

        return (
            jsonify(
                {
                    "error": "Rate limit exceeded",
                    "message": (
                        str(e.description)
                        if hasattr(e, "description")
                        else "Too many requests"
                    ),
                }
            ),
            429,
        )

    # Configure CORS for frontend access
    CORS(
        app,
        resources={
            r"/api/*": {
                "origins": app.config.get("CORS_ORIGINS", ["http://localhost:3000"]),
                "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                "allow_headers": ["Content-Type", "Authorization"],
                "supports_credentials": True,
            }
        },
    )

    # Import models to register them with SQLAlchemy
    from app.models import (  # noqa: F401
        PasswordHistory,
        RefreshToken,
        TokenBlacklist,
        User,
    )

    # Register blueprints
    from app.routes.auth_routes import auth_bp
    from app.routes.user_routes import user_bp

    app.register_blueprint(auth_bp, url_prefix="/api")
    app.register_blueprint(user_bp, url_prefix="/api")

    # Initialize in-memory log handler for log viewing
    from app.utils.log_handler import get_log_handler

    get_log_handler()  # Initialize the handler

    # Add security headers to all responses
    from app.middleware.security import add_security_headers

    app.after_request(add_security_headers)

    # Root route
    @app.route("/")
    def root():
        """Root endpoint - API information"""
        return {
            "service": "Auth Service",
            "version": "1.0.0",
            "endpoints": {
                "register": "/api/auth/register",
                "login": "/api/auth/login",
                "verify": "/api/auth/verify",
                "refresh": "/api/auth/refresh",
                "logout": "/api/auth/logout",
                "revoke": "/api/auth/revoke",
                "users": "/api/users",
                "user_profile": "/api/users/{user_id}",
                "user_by_username": "/api/users/username/{username}",
                "update_role": "/api/users/{user_id}/role",
                "system_user": "/api/users/system",
            },
        }

    @app.route("/health")
    def health():
        """
        Health check endpoint with process information.

        Returns standardized health status including process metadata.
        """
        from app.utils.health_check import get_health_status
        from flask import jsonify

        health_status = get_health_status(
            service_name="auth",
            version="1.0.0",
            include_process_info=True,
        )

        return jsonify(health_status), 200

    return app
