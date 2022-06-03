from flask import current_app as app

from application.webassets import all_blueprints
for bp in all_blueprints():
    app.register_blueprint(bp)