from flask import Blueprint, render_template, request
from flask_login import current_user, login_required

from . import esi_user

bp = Blueprint(
    'user_bp', __name__,
        static_folder='./static',
        template_folder='./templates',\
        url_prefix='/user')


@bp.route('/dashboard', methods=['GET'])
@login_required
def dashboard():
    """user dashboard."""
    hist_range = request.args.get('days', 99, type=int)
    return render_template(
        'dashboard.html',
        title=f"Hermit Krabacus Dashboard - {current_user.character_name}",
        description="Overview of User's account and your current settings.",
        characters=esi_user.get_user_eve_info(hist_range))
