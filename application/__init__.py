from flask_assets import Environment
from flask_sqlalchemy import SQLAlchemy
from flask import Flask
from config import *
from application.assets import compile_static_assets


assets = Environment()
db = SQLAlchemy()

def init_app():
    """Initialize the core application."""
    app = Flask(__name__,
                instance_relative_config=False,
                static_folder='webpages')
    app.config.from_object('config')

    # Initialize Plugins
    db.init_app(app)
    assets.init_app(app)
    
    with app.app_context():
        
        # Include our Routes to Register all Blueprints
        import application.routes
        # bundle (js -> jsmin; less->cssmin)
        compile_static_assets(assets, default_bp_name="base_bp")
        db.create_all()
        return app