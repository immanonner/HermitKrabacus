from flask import Blueprint, render_template, url_for, redirect, request
from flask_login import current_user, login_required
from application.models import SolarSystems, StructureMarkets, db
from . import esi_market, forms_market

bp = Blueprint('market_bp',
               __name__,
               static_folder='./static',
               template_folder='./templates',
               url_prefix='/market')


@bp.route('/home/', methods=['GET', 'POST'])
@login_required
def market():
    sys_form = forms_market.SearchForm()
    if sys_form.validate_on_submit():
        return redirect(
            url_for('market_bp.structures', sys_name=sys_form.search.data))

    return render_template(
        'market.html',
        title="market title",
        description="market description",
        searchdata=esi_market.get_solarsystems(null_sec=True),
        form=sys_form)


@bp.route('/structures/<sys_name>/', methods=['GET', 'POST'])
@login_required
def structures(sys_name):
    structures = esi_market.get_sys_structures(sys_name)
    struc_names = {value['name']: key for key, value in structures.items()}
    if struc_names.get('No Structures found'):
        return redirect(url_for('market_bp.market'))
    sys_form = forms_market.SelectForm()
    if sys_form.validate_on_submit():
        ss = SolarSystems()
        q = ss.query.filter(SolarSystems.solarSystemName == sys_name).first()
        sm = StructureMarkets()
        sm.struc_id = struc_names[sys_form.search.data]
        sm.name = sys_form.search.data
        sm.typeID = structures[struc_names[sys_form.search.data]]['type_id']
        sm.solarSystemID = q.solarSystemID
        db.session.merge(sm)
        db.session.commit()
        return redirect(
            url_for('market_bp.upwellMarket',
                    struc_name=sm.name,
                    import_hub=sys_form.select.data))
    return render_template('market.html',
                           title="Select Structure",
                           description=f'{sys_name} Market Structure Selection',
                           searchdata=[i for i in struc_names.keys()],
                           form=sys_form)


@bp.route('/upwellMarket/', methods=['GET'])
@login_required
def upwellMarket():
    struc_name = request.args.get('struc_name')
    import_hub = request.args.get('import_hub')
    market_view = esi_market.get_structure_market_analysis(
        struc_name, import_hub)

    return render_template(
        'upwell.html',
        title=f'{struc_name}\n Market Analysis',
        description=f'Examining the Route from {import_hub}',
        gridData=market_view.head().to_json(orient='records'))
