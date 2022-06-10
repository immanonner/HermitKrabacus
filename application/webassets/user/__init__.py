from flask import current_app as app, flash, render_template, Blueprint
from flask_login import current_user, login_required
from application.models import db, Users
from application import esiapp, esiclient
from esipy.exceptions import APIException
from sqlalchemy import null
import json

bp = Blueprint(
    'user_bp', __name__,
        static_folder='./static',
        template_folder='./templates',\
        url_prefix='/user')


# get each linked eve online user information such as wallet, characters, etc.
def get_user_eve_info():
    users_eve_info = {}
    response_bundle = []
    for linked_toon in current_user.linked_characters():
        esiclient.security.update_token(linked_toon.get_sso_data())
        if esiclient.security.is_token_expired():
            
            try:
                linked_toon.update_token(esiclient.security.refresh())
                db.session.commit()
            except (APIException, AttributeError):
                # refresh token failed, delete tokens and skip character
                linked_toon.clear_esi_tokens()
                db.session.commit()
                flash(f'Error refreshing esi token\'s for {linked_toon.character_name}', 'danger')
                continue
        users_eve_info[linked_toon.character_name] = {}
        wallet_op = esiapp.op \
                    ['get_characters_character_id_wallet'] \
                    (character_id = linked_toon.character_id)
        orders_op = esiapp.op \
                    ['get_characters_character_id_orders'] \
                    (character_id = linked_toon.character_id,
                    token = esiclient.security.access_token)
        transacts_op = esiapp.op \
                    ['get_characters_character_id_wallet_transactions'] \
                    (character_id = linked_toon.character_id,
                    token = esiclient.security.access_token)
        request_bundle = [wallet_op, orders_op, transacts_op]
        response_bundle.extend(esiclient.multi_request(request_bundle))
    """
        character_name: wallet:balance, 
                        orders: orders_data, 
                        transactions: transactions_data,
        __next
    """
    for req, res in response_bundle:
        req_title = res._Response__op._Operation__operationId.replace \
                    ("get_characters_character_id_","")
        toon_id = req._Request__p.get('path')['character_id']
        toon = Users.query.filter_by(character_id=toon_id).first()
        if res.status != 200:
            flash(f'Error getting eve info for {toon.character_name}: {req_title}', 'danger')
            continue
        users_eve_info[toon.character_name][req_title] = res.data
    # reset esi tokens to origin character's tokens
    if esiclient.security.access_token != current_user.access_token:
        esiclient.security.update_token(current_user.get_sso_data())
    return users_eve_info



@bp.route('/dashboard', methods=['GET'])
@login_required
def dashboard():
    """user dashboard."""
    return render_template(
        'dashboard.html',
        title=f"Hermit Krabacus Dashboard - {current_user.character_name}",
        description="Overview of User's account and your current settings.",
        characters=get_user_eve_info())

