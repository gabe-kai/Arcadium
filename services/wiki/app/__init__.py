import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

db = SQLAlchemy()
migrate = Migrate()

def create_app(config_name=None):
    """Create and configure the Flask application"""
    app = Flask(__name__)
    
    # Determine config name
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    # Load configuration
    from config import config
    app.config.from_object(config.get(config_name, config['default']))
    
    # Initialize extensions
    # Note: SQLALCHEMY_ENGINE_OPTIONS is automatically used by Flask-SQLAlchemy
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Create data directories
    os.makedirs(app.config['WIKI_PAGES_DIR'], exist_ok=True)
    os.makedirs(app.config['WIKI_UPLOADS_DIR'], exist_ok=True)
    os.makedirs(os.path.join(app.config['WIKI_UPLOADS_DIR'], 'metadata'), exist_ok=True)
    
    # Register blueprints
    from app.routes.wiki_routes import wiki_bp
    app.register_blueprint(wiki_bp, url_prefix='/api')
    
    # Root route
    @app.route('/')
    def root():
        """Root endpoint - API information"""
        from flask import jsonify
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
    
    # Favicon route - return 204 No Content to prevent 404 errors
    @app.route('/favicon.ico')
    def favicon():
        """Favicon endpoint - return no content"""
        from flask import Response
        return Response(status=204)
    
    return app

