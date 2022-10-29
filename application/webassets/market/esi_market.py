# get each linked eve online user information such as wallet, characters, etc.
from application import esiapp, esiclient, utils as apptils, f_cache

from application.models import InvTypes, SolarSystems, StructureMarkets, db
from config import *
from flask import flash
from flask_login import current_user
import json
import pandas as pd


def get_sys_structures(sys_name):
    struc_ids_req = esiapp.op['get_characters_character_id_search'](
        character_id=current_user.character_id,
        categories=['structure', 'station'],
        search=sys_name,
        token=esiclient.security.access_token)
    struc_id_resp = esiclient.request(struc_ids_req)
    results = {}
    if struc_id_resp.status == 200:
        struc_name_reqs = []
        results = {
            123456: {
                'name': "No Structures found",
                'type_id': 12345
            }
        }  #default result
        if len(struc_id_resp.data) > 0:
            if struc_id_resp.data.get('structure'):
                for id in struc_id_resp.data['structure']:
                    r = esiapp.op['get_universe_structures_structure_id'](
                        structure_id=id, token=current_user.access_token)
                    struc_name_reqs.append(r)
            if struc_id_resp.data.get('station'):
                for id in struc_id_resp.data['station']:
                    r = esiapp.op['get_universe_stations_station_id'](
                        station_id=id)
                    struc_name_reqs.append(r)
            results = [
                i for i in esiclient.multi_request(struc_name_reqs, threads=20)
            ]
            structures = {
                int(req._Request__p['path']['structure_id']): {
                    'name': resp.data['name'],
                    'type_id': int(resp.data['type_id'])
                }
                for req, resp in results
                if int(resp.data['type_id']) in EVE_MARKET_STRUCTURES and
                req._Request__p['path'].get('structure_id')
            }
            stations = {
                int(req._Request__p['path']['station_id']): {
                    'name': resp.data['name'],
                    'type_id': int(resp.data['type_id'])
                }
                for req, resp in results
                if req._Request__p['path'].get('station_id')
            }
            structures.update(stations)
            results = structures
        else:
            flash(
                f'No results found for {current_user.character_name} in SolarSystem: {sys_name}; ensure the toon has docking access...',
                'danger')
    else:
        flash(
            f'response error: {struc_id_resp.status} No results found for {current_user.character_name} in SolarSystem: {sys_name}; ??ESI SEARCH DOWN??',
            'danger')
    return results


@apptils.timer_func
def get_struc_sell_orders(struc_id):
    op = esiapp.op['get_markets_structures_structure_id'](
        structure_id=struc_id, token=current_user.access_token)
    struc_market_response = esiclient.request(op)
    if struc_market_response.status == 200:
        pages = struc_market_response.header['X-Pages'][0]
        expires = struc_market_response.header['expires'][0]
        results = [{
            'expires': expires,
            **rec
        } for rec in json.loads(struc_market_response.raw)]
        if pages > 1:
            operations = []
            for page in range(2, pages + 1):
                operations.append(
                    esiapp.op['get_markets_structures_structure_id'](
                        page=page,
                        structure_id=struc_id,
                        token=current_user.access_token))
            # multi request all pages of the market orders -> load them to results list(dict)
            [
                results.extend([{
                    'expires': rsp.header['expires'][0],
                    **rec
                }
                                for rec in json.loads(rsp.raw)])
                for rq, rsp in esiclient.multi_request(operations,
                                                       raw_body_only=True)
                if rsp.status == 200
            ]
            # clean the data in results
        return results
    else:
        flash(
            f"response status = <{struc_market_response.status}> structure sell order retrival failed",
            "danger")
    # todo error handle this
    pass


def include_empty_stock(sell_orders):
    orders = pd.DataFrame(sell_orders).set_index('type_id', drop=True)
    #select only sell orders and drop irrelevant columns
    orders = orders[orders.is_buy_order == False].drop(columns=[
        'duration', 'issued', 'min_volume', 'range', 'is_buy_order',
        'volume_total'
    ])
    # group orders by type_id and calc remaining volumes and minimum price of each type
    orders = orders.groupby('type_id').agg({
        'volume_remain': 'sum',
        'price': 'min',
        'expires': 'first',
        'order_id': 'count',
    })
    all_types = pd.read_sql("SELECT typeID, typeName, volume FROM invTypes",
                            db.engine,
                            index_col='typeID')

    market_view = pd.merge(all_types,
                           orders,
                           how='left',
                           left_index=True,
                           right_index=True).fillna(value=0, axis=1).rename(
                               columns={'volume_remain': 'stock_remaining'})
    # format currency column appropriately
    # todo --  might mess with sorting functions
    # orders['price'].apply(lambda x: "${:.1f}k".format((x / 1000)))
    # include the index - type_id into the returned list of dicts "records"
    return [
        dict({'type_id': k}, **v)
        for k, v in market_view.to_dict('index').items()
    ]


@apptils.timer_func
def get_region_history(reg_id):
    hist = f_cache.get('adf').loc[reg_id]
    hist = hist.reset_index().to_dict(orient='records')
    return hist


@apptils.timer_func
def get_k_space_orders(hub):
    sm = StructureMarkets()
    if EVE_MARKET_HUBS.get(hub.solarSystemID):
        sm.struc_id = EVE_MARKET_HUBS.get(hub.solarSystemID)[0]
        sm.name = EVE_MARKET_HUBS.get(hub.solarSystemID)[1]
        sm.typeID = EVE_MARKET_HUBS.get(hub.solarSystemID)[2]
        sm.solarSystemID = hub.solarSystemID
    else:
        sm.struc_id = hub.struc_id
        sm.name = hub.name
        sm.typeID = hub.typeID
        sm.solarSystemID = hub.solarSystemID
    db.session.merge(sm)
    db.session.commit()
    sm = StructureMarkets.query.filter(StructureMarkets.name == sm.name).first()
    rsp = esiclient.request(esiapp.op['get_markets_region_id_orders'](
        region_id=sm.solarSystems.regionID))
    if rsp.status == 200:
        pages = rsp.header['X-Pages'][0]
        expires = rsp.header['expires'][0]
        results = [{'expires': expires, **rec} for rec in json.loads(rsp.raw)]
        if pages > 1:
            operations = []
            for page in range(2, pages + 1):
                operations.append(esiapp.op['get_markets_region_id_orders'](
                    region_id=sm.solarSystems.regionID, page=page))
        [
            results.extend([{
                'expires': rs.header['expires'][0],
                **rec
            }
                            for rec in json.loads(rs.raw)])
            for rq, rs in esiclient.multi_request(operations,
                                                  raw_body_only=True)
            if rs.status == 200
        ]
        # clean the data in results
        return results
    else:
        flash(
            f"response status = <{rsp.status}> station sell order retrival failed",
            "danger")
    # todo error handle this
    pass


@apptils.timer_func
def get_structure_market_analysis(struc_name, import_hub, dso, saleChance,
                                  records):

    sm = StructureMarkets.query.filter(
        StructureMarkets.name == struc_name).first()
    if sm.is_expired(sm.history_expiry):
        sm.update_history_records(get_region_history(sm.solarSystems.regionID))
        db.session.commit()

    if sm.is_expired(sm.sell_orders_expiry):
        # switch between the two ops for the new station feature
        if sm.typeID not in EVE_MARKET_STRUCTURES:
            orders = pd.DataFrame(get_k_space_orders(sm))
            orders = include_empty_stock(
                orders[orders.location_id == sm.struc_id].to_dict('records'))
        else:
            orders = include_empty_stock(get_struc_sell_orders(sm.struc_id))
        sm.update_sell_orders(orders)
        db.session.commit()

    ih = SolarSystems.query.filter(
        SolarSystems.solarSystemName == import_hub).first()

    #todo ensure structure markets for hubs only return one or the 'right' station
    if len(ih.structureMarkets) == 0 or ih.structureMarkets[0].is_expired(
            ih.structureMarkets[0].sell_orders_expiry):
        import_hub_orders = include_empty_stock(get_k_space_orders(ih))
        ih.structureMarkets[0].update_sell_orders(import_hub_orders)
        db.session.commit()

    h = pd.DataFrame(sm.history)
    h.drop(columns=['listDate'], inplace=True)
    ih_o = pd.DataFrame(ih.structureMarkets[0].sell_orders)
    ih_o.drop(columns=[
        'expires',
        'stock_remaining',
    ], inplace=True)
    ih_o.rename(columns={
        'price': 'hub_min_price',
        'volume': 'pack_vol',
        'order_id': 'hub_order_ids'
    },
                inplace=True)
    so = pd.DataFrame(sm.sell_orders)
    so.drop(columns=['expires', 'price', 'typeName', 'volume'], inplace=True)
    v = pd.merge(ih_o, h, left_on='type_id', right_on='typeID', how='left')
    v = pd.merge(v, so, on='type_id', how='left')
    v['dso'] = round(v.stock_remaining / v.velocity, 2)
    v['be'] = round(
        v.hub_min_price + (v.hub_min_price * .085) + (350 * v.pack_vol), 2)
    v['ppi'] = round(v.lastPriceAvg - v.be, 2)
    v['rr'] = round(v.ppi / v.be, 2)
    v['ppd'] = round(v.ppi * v.velocity, 2)
    v.fillna(value={
        'aggVol': 0.0,
        "records": 0.0,
        "lastPriceAvg": 0.0,
        "velocity": 0.0,
        "saleChance": 0.0,
        'stock_remaining': 0.0,
        'dso': 0.0,
        'be': 0.0,
        'ppi': 0.0,
        'rr': 0.0,
        'ppd': 0.0
    },
             inplace=True)
    v = v[(v.hub_min_price > 0) & (v.dso <= dso) &
          (v.saleChance >= saleChance) & (v.records >= records) & (v.ppd >= 0)]
    v.sort_values(by=['ppd'], ascending=False, inplace=True)
    v.drop(columns=[
        'type_id', 'typeID', 'pack_vol', 'aggVol', 'records', 'hub_order_ids'
    ],
           inplace=True)
    return v