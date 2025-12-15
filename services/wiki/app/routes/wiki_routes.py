from flask import Blueprint, jsonify

wiki_bp = Blueprint('wiki', __name__)

# Import route blueprints
from app.routes.page_routes import page_bp
from app.routes.comment_routes import comment_bp

# Register blueprints
wiki_bp.register_blueprint(page_bp)
wiki_bp.register_blueprint(comment_bp)

@wiki_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'wiki'}), 200
