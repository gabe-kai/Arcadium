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
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Create data directories
    os.makedirs(app.config['WIKI_PAGES_DIR'], exist_ok=True)
    os.makedirs(app.config['WIKI_UPLOADS_DIR'], exist_ok=True)
    os.makedirs(os.path.join(app.config['WIKI_UPLOADS_DIR'], 'metadata'), exist_ok=True)
    
    # Register blueprints
    from app.routes.wiki_routes import wiki_bp
    app.register_blueprint(wiki_bp, url_prefix='/api')
    
    return app

