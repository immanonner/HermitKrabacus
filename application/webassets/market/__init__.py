from flask import Blueprint, render_template, request, url_for, redirect
from flask_login import current_user, login_required
from . import esi_market, forms_market

bp = Blueprint('market_bp',
               __name__,
               static_folder='./static',
               template_folder='./templates',
               url_prefix='/market')


@bp.route('/home/', methods=['GET', 'POST'])
@login_required
def market():
    sys_form = forms_market.SolarSystemForm()
    if sys_form.validate_on_submit():
        return redirect(
            url_for('market_bp.solarsys_structures',
                    sys_name=sys_form.system_name.data))
    return render_template('market.html',
                           title="market title",
                           description="market description",
                           solarsystems=esi_market.get_solarsystems(),
                           form=sys_form)


@bp.route('/solarsys_structures/<sys_name>', methods=['GET'])
@login_required
def solarsys_structures(sys_name):

    pass
