# get each linked eve online user information such as wallet, characters, etc.
from concurrent.futures import ThreadPoolExecutor

from application import esiapp, esiclient, esisecurity
from application.models import Users, invTypes, invVolumes, SolarSystems, db
from config import *
from esipy import EsiClient, EsiSecurity
from esipy.exceptions import APIException
from flask import flash
from flask_login import current_user


def get_solarsystems() -> list:

    return [rw[0] for rw in db.session.query(SolarSystems.solarSystemName)]


def get_sys_structures(sys_name) -> dict:
    struc_ids_req = esiapp.op['get_characters_character_id_search'](
        character_id=current_user.character_id,
        categories=['structure'],
        search=sys_name,
        token=esiclient.security.access_token)
    struc_id_resp = esiclient.request(struc_ids_req)
    if struc_id_resp.status == 200:
        struc_name_reqs = []
        for id in struc_id_resp.data['structure']:
            r = esiapp.op['get_universe_structures_structure_id'](
                structure_id=id, token=current_user.access_token)
            struc_name_reqs.append(r)
        results = [
            i for i in esiclient.multi_request(struc_name_reqs, threads=20)
        ]
        results = {
            int(req._Request__p['path']['structure_id']): {
                'name': resp.data['name'],
                'type_id': int(resp.data['type_id'])
            }
            for req, resp in results
            if int(resp.data['type_id']) in EVE_MARKET_STRUCTURES
        }
    return results


def get_struc_sell_orders(struc_id):
    op = esiapp.op['get_markets_structures_structure_id'](
        structure_id=struc_id, token=current_user.access_token)
    struc_market_response = esiclient.request(op)
    if struc_market_response.status == 200:
        if struc_market_response.header['X-Pages'][0] == 1:

            pass
    else:
        flash(
            f"response status = <{struc_market_response.status}> structure sell order retrival failed",
            "danger")
    pass


def get_structure_market_analysis(region_id, struc_id):
    get_struc_sell_orders(struc_id)
    pass