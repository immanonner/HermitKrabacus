from flask import current_app as app, render_template, Blueprint
from flask_login import current_user, login_required

bp = Blueprint(
    'user_bp', __name__,
        static_folder='./static',
        template_folder='./templates',\
        url_prefix='/user')


# get eve online user information such as wallet, characters, etc.
def get_user_eve_info():
    pass



@bp.route('/dashboard', methods=['GET'])
@login_required
def dashboard():
    """user dashboard."""
    return render_template(
        'dashboard.html',
        style_bundle_name="user_bp_styles",
        js_bundle_name="user_bp_js",
        title=f"Hermit Krabacus Dashboard - {current_user.character_name}",
        description="Overview of User's account and your current settings.")

