from flask import Blueprint, jsonify

wiki_bp = Blueprint("wiki", __name__)

# Import route blueprints
from app.routes.page_routes import page_bp
from app.routes.comment_routes import comment_bp
from app.routes.search_routes import search_bp
from app.routes.navigation_routes import navigation_bp
from app.routes.version_routes import version_bp
from app.routes.orphanage_routes import orphanage_bp
from app.routes.extraction_routes import extraction_bp
from app.routes.admin_routes import admin_bp
from app.routes.upload_routes import upload_bp

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
    return jsonify({
        "service": "Wiki Service",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/api/health",
            "pages": "/api/pages",
            "search": "/api/search",
            "navigation": "/api/navigation",
            "admin": "/api/admin/dashboard/stats"
        },
        "documentation": "See README.md for API documentation"
    }), 200


@wiki_bp.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    from app.services.auth_service_client import get_auth_client
    import logging
    
    logger = logging.getLogger(__name__)
    health_status = {
        "status": "healthy",
        "service": "wiki"
    }
    
    # Test Auth Service connection
    auth_client = get_auth_client()
    try:
        # Try a simple connection test (this will fail but tells us if service is reachable)
        import requests
        test_url = f"{auth_client.base_url}/api/auth/verify"
        response = requests.post(
            test_url,
            json={"token": "test"},
            timeout=2,
            headers={"Content-Type": "application/json"}
        )
        # Any response (even 401) means the service is reachable
        health_status["auth_service"] = {
            "status": "reachable",
            "url": auth_client.base_url,
            "response_code": response.status_code
        }
    except requests.exceptions.ConnectionError:
        health_status["auth_service"] = {
            "status": "unreachable",
            "url": auth_client.base_url,
            "error": "Connection refused - Auth Service may not be running"
        }
        health_status["status"] = "degraded"
    except requests.exceptions.Timeout:
        health_status["auth_service"] = {
            "status": "timeout",
            "url": auth_client.base_url,
            "error": "Request timed out"
        }
        health_status["status"] = "degraded"
    except Exception as e:
        health_status["auth_service"] = {
            "status": "error",
            "url": auth_client.base_url,
            "error": str(e)
        }
        health_status["status"] = "degraded"
    
    status_code = 200 if health_status["status"] == "healthy" else 503
    return jsonify(health_status), status_code


@wiki_bp.route("/admin/clear-cache", methods=["POST"])
def clear_cache():
    """Clear all HTML caches (admin endpoint for debugging)"""
    from app.services.cache_service import CacheService
    from app.middleware.auth import require_auth, require_role
    
    # This will be wrapped by the auth decorators when registered
    CacheService.clear_html_caches()
    return jsonify({"message": "HTML caches cleared"}), 200
