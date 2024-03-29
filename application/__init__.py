from config import *
from esipy import EsiApp, EsiClient, EsiSecurity, cache
from flask import Flask
from flask_assets import Environment
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy_utils import database_exists

from application.assets import compile_static_assets

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
assets = Environment()
f_cache = cache.FileCache(path="./f_cache")
# create the eve app interface
esiapp = EsiApp(cache=f_cache).get_latest_swagger

# init the security object
esisecurity = EsiSecurity(redirect_uri=ESI_CALLBACK,
                          client_id=ESI_CLIENT_ID,
                          secret_key=ESI_SECRET_KEY,
                          headers={'User-Agent': ESI_USER_AGENT})

# init the client
esiclient = EsiClient(security=esisecurity,
                      cache=f_cache,
                      headers={'User-Agent': ESI_USER_AGENT})


def init_app():
    """Initialize the core application."""
    app = Flask(__name__,
                instance_relative_config=False,
                static_folder='webassets')
    app.config.from_object('config')

    # Initialize Plugins
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    assets.init_app(app)

    with app.app_context():
        from application.fuzzworks import update_eve_sde
        from application.eveRef import update_market_history
        db.create_all()

        update_eve_sde(force=False)
        update_market_history(force=False)

        import application.routes
        import application.auth

        compile_static_assets(assets, default_bp_name="base_bp")

        # else:  # creates the db if it doesnt exist
        #     from flask_migrate import upgrade as db_upgrade
        #     db_upgrade()
        # update eve item data

        # Include our Routes to Register all Blueprints
        # bundle (js -> jsmin; less->cssmin)

        return app
