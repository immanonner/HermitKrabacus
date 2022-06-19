from flask import Blueprint, render_template
from flask_login import current_user, login_required

bp = Blueprint(
    'market_bp', __name__,
    static_folder='./static',
    template_folder='./templates',
    url_prefix='/market')


@bp.route('/market', methods=['GET'])
@login_required
def market():
    # market
    return render_template(
        'market.html',
        title="market title",
        description="market description",)
