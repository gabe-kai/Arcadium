import os

from flask import Flask
from flask_cors import CORS
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
migrate = Migrate()


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

    app.register_blueprint(auth_bp, url_prefix="/api")

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
            },
        }

    @app.route("/health")
    def health():
        """Health check endpoint"""
        return {"status": "healthy", "service": "auth"}, 200

    return app
