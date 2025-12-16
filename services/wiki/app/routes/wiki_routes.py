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
    return jsonify({"status": "healthy", "service": "wiki"}), 200
