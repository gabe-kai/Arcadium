from app.routes.admin_routes import admin_bp
from app.routes.comment_routes import comment_bp
from app.routes.extraction_routes import extraction_bp
from app.routes.navigation_routes import navigation_bp
from app.routes.orphanage_routes import orphanage_bp
from app.routes.page_routes import page_bp
from app.routes.search_routes import search_bp
from app.routes.upload_routes import upload_bp
from app.routes.version_routes import version_bp
from flask import Blueprint, jsonify

wiki_bp = Blueprint("wiki", __name__)

# Register blueprints
wiki_bp.register_blueprint(page_bp)
wiki_bp.register_blueprint(comment_bp)
wiki_bp.register_blueprint(search_bp)
wiki_bp.register_blueprint(navigation_bp)
wiki_bp.register_blueprint(version_bp)
wiki_bp.register_blueprint(orphanage_bp)
wiki_bp.register_blueprint(extraction_bp)
wiki_bp.register_blueprint(admin_bp)
wiki_bp.register_blueprint(upload_bp)


@wiki_bp.route("/", methods=["GET"])
def root():
    """Root endpoint - API information"""
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


@wiki_bp.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint - returns quickly without blocking on external services"""
    import requests
    from app.services.auth_service_client import get_auth_client

    # Wiki service is healthy if it's responding (which it is, since we're here)
    health_status = {"status": "healthy", "service": "wiki"}

    # Optionally check Auth Service connection (non-blocking, very short timeout)
    # This doesn't affect the wiki service's health status
    auth_client = get_auth_client()
    try:
        # Use very short timeout to avoid blocking
        test_url = f"{auth_client.base_url}/api/auth/verify"
        response = requests.post(
            test_url,
            json={"token": "test"},
            timeout=0.3,  # Very short timeout - just a quick check
            headers={"Content-Type": "application/json"},
        )
        # Any response (even 401) means the service is reachable
        health_status["auth_service"] = {
            "status": "reachable",
            "url": auth_client.base_url,
            "response_code": response.status_code,
        }
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        # Auth service unreachable - wiki is still healthy, just note the dependency
        health_status["auth_service"] = {
            "status": "unreachable",
            "url": auth_client.base_url,
        }
        # Don't mark wiki as degraded - it's still functional
    except Exception:
        # Any other error - just skip the auth check
        pass

    # Always return 200 - wiki service is healthy if it can respond
    return jsonify(health_status), 200


@wiki_bp.route("/admin/clear-cache", methods=["POST"])
def clear_cache():
    """Clear all HTML caches (admin endpoint for debugging)"""
    from app.services.cache_service import CacheService

    # This will be wrapped by the auth decorators when registered
    CacheService.clear_html_caches()
    return jsonify({"message": "HTML caches cleared"}), 200
