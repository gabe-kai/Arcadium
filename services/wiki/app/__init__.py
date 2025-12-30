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
    # Note: SQLALCHEMY_ENGINE_OPTIONS is automatically used by Flask-SQLAlchemy
    db.init_app(app)
    migrate.init_app(app, db)

    # Configure CORS for frontend access
    CORS(
        app,
        resources={
            r"/api/*": {
                "origins": ["http://localhost:3000", "http://127.0.0.1:3000"],
                "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                "allow_headers": ["Content-Type", "Authorization"],
                "supports_credentials": True,
            },
            r"/api/uploads/*": {
                "origins": ["http://localhost:3000", "http://127.0.0.1:3000"],
                "methods": ["GET", "OPTIONS"],
                "allow_headers": ["Content-Type"],
                "supports_credentials": False,
            },
        },
    )

    # Create data directories
    os.makedirs(app.config["WIKI_PAGES_DIR"], exist_ok=True)
    os.makedirs(app.config["WIKI_UPLOADS_DIR"], exist_ok=True)
    os.makedirs(os.path.join(app.config["WIKI_UPLOADS_DIR"], "metadata"), exist_ok=True)

    # Register blueprints
    from app.routes.wiki_routes import wiki_bp

    app.register_blueprint(wiki_bp, url_prefix="/api")

    # Initialize in-memory log handler for log viewing
    from app.utils.log_handler import get_log_handler

    get_log_handler()  # Initialize the handler

    # Start service status page auto-updater (runs every 10 minutes)
    from app.services.service_status_scheduler import ServiceStatusScheduler

    service_status_scheduler = ServiceStatusScheduler(app, interval_minutes=10)
    service_status_scheduler.start()
    # Store reference on app for potential cleanup (though daemon thread will stop on exit)
    app.service_status_scheduler = service_status_scheduler

    # Root route
    @app.route("/")
    def root():
        """Root endpoint - API information"""
        from flask import jsonify

        return (
            jsonify(
                {
                    "service": "Wiki Service",
                    "version": "1.0.0",
                    "status": "running",
                    "endpoints": {
                        "health": "/api/health",
                        "pages": "/api/pages",
                        "search": "/api/search",
                        "navigation": "/api/navigation",
                        "admin": "/api/admin/dashboard/stats",
                    },
                    "documentation": "See README.md for API documentation",
                }
            ),
            200,
        )

    # Favicon route - return 204 No Content to prevent 404 errors
    @app.route("/favicon.ico")
    def favicon():
        """Favicon endpoint - return no content"""
        from flask import Response

        return Response(status=204)

    return app
