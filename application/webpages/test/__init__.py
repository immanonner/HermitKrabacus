from flask import current_app as app, render_template, Blueprint
from flask_login import current_user, login_required

bp = Blueprint(
    'test_bp', __name__,
        static_folder='./static',
        template_folder='./templates',\
        url_prefix='/test')


@bp.route('/', methods=['GET'])
@login_required
def test():
    """test page."""
    return render_template(
        'test.html',
        style_bundle_name="test_bp_styles",
        js_bundle_name="test_bp_js",
        title=f"{current_user.character_name} test",
        description="Smarter page templates with Flask & Jinja.")
