
# get each linked eve online user information such as wallet, characters, etc.
from flask import flash
from flask_login import current_user
from requests import request
from application import esiapp, esisecurity, esiclient
from application.models import db, Users
from esipy import EsiSecurity, EsiClient
from esipy.exceptions import APIException
from config import *
from concurrent.futures import ThreadPoolExecutor
from pyswagger.io import SwaggerRequest as Request
from pyswagger.io import SwaggerResponse as Response

def gen_auth_esiclient(user:Users) -> EsiClient:
    """ we use a toon's information to __init__ a unique esiclient to make requests. 
        ie If I want to have all three of my characters
        wallet information displayed; I need 3 esiclients.

    Args:
        user: db.model / Users() -
        Used to pull sso information to __init__ esipy client
    """
    
    # init the security object
    security = EsiSecurity(
                redirect_uri=ESI_CALLBACK,
                client_id=ESI_CLIENT_ID,
                secret_key=ESI_SECRET_KEY,
                headers={'User-Agent': ESI_USER_AGENT})
    security.update_token(user.get_sso_data())
    if security.is_token_expired:        
        try:
            user.update_token(security.refresh())
        except (APIException, AttributeError):
            user.clear_esi_tokens()
            db.session.commit()
            flash(f'Error refreshing esi token\'s for {user.character_name}', 'danger')
            return False

    # init the client
    genclient = EsiClient(
        security=security,
        headers={'User-Agent': ESI_USER_AGENT})
    return genclient

def threaded_user_mutli_request(toon):
    """
    Args:
        toon: Users()
        request_bundle: list of requests, responses to be made
    """
    client = gen_auth_esiclient(toon)
    wallet_op = esiapp.op \
                ['get_characters_character_id_wallet'] \
                (character_id = toon.character_id)
    orders_op = esiapp.op \
                ['get_characters_character_id_orders'] \
                (character_id = toon.character_id,
                token = client.security.access_token)
    transacts_op = esiapp.op \
                    ['get_characters_character_id_wallet_transactions'] \
                    (character_id = toon.character_id,
                    token = client.security.access_token)
    request_bundle = [wallet_op, orders_op, transacts_op]
    return client.multi_request(request_bundle)

def get_user_eve_info():
        
    results = []
    with ThreadPoolExecutor(max_workers=10) as pool:
        for result in pool.map(threaded_user_mutli_request, current_user.linked_characters()):
            results.append(result)
        # reset esi tokens to origin character's tokens
    results = nested_responses_to_dict(results)
    if esiclient.security.access_token != current_user.access_token:
        esiclient.security.update_token(current_user.get_sso_data())
    return results

def nested_responses_to_dict(responses):
    """
    Args:
        responses: list of responses from get_user_eve_info()
    returns:
        {character_name: wallet:balance, 
                        orders: orders_data, 
                        transactions: transactions_data,
        __next}
    """
    account_data = {}
    for element in responses:
        toon_id = element[0][0]._Request__p.get('path')['character_id']
        toon = Users.query.filter_by(character_id=toon_id).first()
        account_data[toon.character_name] = {}
        for req, res in element:
            req_title = res._Response__op._Operation__operationId.replace \
                        ("get_characters_character_id_","")        
            if res.status != 200:
                flash(f'Error getting eve info for {toon.character_name}: {req_title}', 'danger')
                continue
            account_data[toon.character_name][req_title] = res.data
    return account_data