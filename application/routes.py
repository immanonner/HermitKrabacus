from flask import current_app as app

from application.webpages import all_blueprints
for bp in all_blueprints():
    app.register_blueprint(bp)