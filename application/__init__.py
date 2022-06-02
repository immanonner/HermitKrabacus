from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_assets import Environment
from config import *
from application.assets import compile_static_assets



db = SQLAlchemy()
login_manager = LoginManager()
assets = Environment()

def init_app():
    """Initialize the core application."""
    app = Flask(__name__,
                instance_relative_config=False,
                static_folder='webpages')
    app.config.from_object('config')

    # Initialize Plugins
    db.init_app(app)
    login_manager.init_app(app)
    assets.init_app(app)
    
    with app.app_context():
        
        # Include our Routes to Register all Blueprints
        import application.routes
        import application.auth
        # bundle (js -> jsmin; less->cssmin)
        if app.config['FLASK_ENV'] == 'development':
            compile_static_assets(assets, default_bp_name="base_bp")
        db.create_all()
        return app