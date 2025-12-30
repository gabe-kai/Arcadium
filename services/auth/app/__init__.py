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

    # Initialize in-memory log handler for log viewing
    from app.utils.log_handler import get_log_handler

    get_log_handler()  # Initialize the handler

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
        """Health check endpoint with process information - optimized for speed"""
        import os
        import time

        # Try to import psutil for process info
        try:
            import psutil

            PSUTIL_AVAILABLE = True
        except ImportError:
            PSUTIL_AVAILABLE = False
            psutil = None

        health_status = {"status": "healthy", "service": "auth", "version": "1.0.0"}

        # Add process information if psutil is available
        # Use minimal operations to keep health check fast
        if PSUTIL_AVAILABLE:
            try:
                process = psutil.Process()
                # Use oneshot() for efficiency, but keep operations minimal
                with process.oneshot():
                    # Get essential info only - skip slow operations
                    create_time = process.create_time()
                    uptime_seconds = time.time() - create_time
                    memory_info = process.memory_info()
                    memory_mb = memory_info.rss / (1024 * 1024)

                    # Get CPU percent (non-blocking)
                    try:
                        cpu_percent = process.cpu_percent(interval=None)
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        cpu_percent = 0.0

                    # Get memory percent (can be slow, but usually fast)
                    try:
                        memory_percent = process.memory_percent()
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        memory_percent = 0.0

                    # Get thread count (fast)
                    try:
                        threads = process.num_threads()
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        threads = 0

                    # Skip open_files() on Windows - it's extremely slow (can take 1+ seconds)
                    # This is a known Windows/psutil issue
                    import platform

                    if platform.system() == "Windows":
                        open_files = 0  # Skip on Windows
                    else:
                        try:
                            open_files = len(process.open_files())
                        except (psutil.NoSuchProcess, psutil.AccessDenied, Exception):
                            open_files = 0

                health_status["process_info"] = {
                    "pid": process.pid,
                    "uptime_seconds": round(uptime_seconds, 2),
                    "cpu_percent": round(cpu_percent, 2),
                    "memory_mb": round(memory_mb, 2),
                    "memory_percent": round(memory_percent, 2),
                    "threads": threads,
                    "open_files": open_files,
                }
            except (psutil.NoSuchProcess, psutil.AccessDenied, AttributeError):
                # Fallback if psutil fails
                health_status["process_info"] = {
                    "pid": os.getpid(),
                    "uptime_seconds": 0.0,
                    "cpu_percent": 0.0,
                    "memory_mb": 0.0,
                    "memory_percent": 0.0,
                    "threads": 0,
                    "open_files": 0,
                }
        else:
            # Basic info without psutil
            health_status["process_info"] = {
                "pid": os.getpid(),
                "uptime_seconds": 0.0,
                "cpu_percent": 0.0,
                "memory_mb": 0.0,
                "memory_percent": 0.0,
                "threads": 0,
                "open_files": 0,
                "note": "psutil not available",
            }

        return health_status, 200

    return app
