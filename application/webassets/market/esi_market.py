# get each linked eve online user information such as wallet, characters, etc.
from application import esiapp, esiclient, utils as apptils

from application.models import InvTypes, SolarSystems, StructureMarkets, db
from config import *
from flask import flash
from flask_login import current_user
import json
import pandas as pd


def get_solarsystems(null_sec=True):
    if not null_sec:
        return [
            rw[0]
            for rw in db.session.query(SolarSystems.solarSystemName).filter(
                SolarSystems.security >= 0)
        ]
    else:
        return [
            rw[0]
            for rw in db.session.query(SolarSystems.solarSystemName).filter(
                SolarSystems.security <= 0)
        ]


def get_types():
    return sorted([rw[0] for rw in db.session.query(InvTypes.typeID)])


def get_sys_structures(sys_name):
    struc_ids_req = esiapp.op['get_characters_character_id_search'](
        character_id=current_user.character_id,
        categories=['structure'],
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
        'duration', 'issued', 'min_volume', 'range', 'order_id', 'is_buy_order',
        'volume_total'
    ])
    # group orders by type_id and calc remaining volumes and minimum price of each type
    orders = orders.groupby('type_id').agg({
        'volume_remain': 'sum',
        'price': 'min',
        'expires': 'first'
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
    all_relevant_types = get_types()
    operations = []
    for tid in all_relevant_types:
        operations.append(esiapp.op['get_markets_region_id_history'](
            type_id=tid, region_id=reg_id))
    results = esiclient.multi_request(operations,
                                      raw_body_only=True,
                                      threads=20)
    history = []
    for rq, rsp in results:
        record = {
            'type_id':
                int(rq.query[1][1]),
            'expires':
                (datetime.datetime.utcnow() +
                 datetime.timedelta(days=1)).strftime('%a, %d %b %Y %H:%M:%S') +
                ' GMT',
            'timespan':
                0,
            'velocity':
                0,
            'order_avg':
                0,
            'yest_price_avg':
                0,
            'sale_chance':
                0.0
        }
        if rsp.status == 200:
            record.update({'expires': rsp.header.get('expires')[0]})
            if len(rsp.raw) <= 2:
                continue
            else:
                hist_records = json.loads(rsp.raw)
                date_delta = datetime.date.today(
                ) - datetime.date.fromisoformat(hist_records[0]['date'])
                record['timespan'] = date_delta.days
                rec_df = pd.DataFrame(hist_records)
                record['velocity'] = round(
                    rec_df.volume.sum() / date_delta.days, 2)
                record['order_avg'] = round(rec_df.order_count.mean(), 2)
                record['yest_price_avg'] = hist_records[-1]['average']
                record['sale_chance'] = round(rec_df.shape[0] / date_delta.days,
                                              2)
                history.append(record)

    return history


@apptils.timer_func
def get_k_space_orders(hub):
    sm = StructureMarkets()
    sm.struc_id = EVE_MARKET_HUBS.get(hub.solarSystemID)[0]
    sm.name = EVE_MARKET_HUBS.get(hub.solarSystemID)[1]
    sm.typeID = EVE_MARKET_HUBS.get(hub.solarSystemID)[2]
    sm.solarSystemID = hub.solarSystemID
    db.session.merge(sm)
    db.session.commit()

    rsp = esiclient.request(
        esiapp.op['get_markets_region_id_orders'](region_id=hub.regionID))
    if rsp.status == 200:
        pages = rsp.header['X-Pages'][0]
        expires = rsp.header['expires'][0]
        results = [{'expires': expires, **rec} for rec in json.loads(rsp.raw)]
        if pages > 1:
            operations = []
            for page in range(2, pages + 1):
                operations.append(esiapp.op['get_markets_region_id_orders'](
                    region_id=hub.regionID, page=page))
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
def get_structure_market_analysis(struc_name, import_hub):
    sm = StructureMarkets.query.filter(
        StructureMarkets.name == struc_name).first()
    if sm.is_expired(sm.history_expiry):
        sm.update_history_records(get_region_history(sm.solarSystems.regionID))
        db.session.commit()

    if sm.is_expired(sm.sell_orders_expiry):
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
    h.drop(columns=['expires', 'order_avg'], inplace=True)
    ih_o = pd.DataFrame(ih.structureMarkets[0].sell_orders)
    ih_o.drop(columns=[
        'expires',
        'stock_remaining',
    ], inplace=True)
    ih_o.rename(columns={
        'price': 'hub_min_price',
        'volume': 'pack_vol'
    },
                inplace=True)
    so = pd.DataFrame(sm.sell_orders)
    so.drop(columns=['expires', 'price', 'typeName', 'volume'], inplace=True)
    v = pd.merge(ih_o, h, on='type_id', how='left')
    v = pd.merge(v, so, on='type_id', how='left')
    v['dso'] = round(v.stock_remaining / v.velocity, 2)
    v['be'] = round((v.hub_min_price * .06) + (500 * v.pack_vol), 2)
    v['ppi'] = round(v.yest_price_avg - v.be, 2)
    v['rr'] = round(v.ppi / v.be, 2)
    v['ppd'] = round(v.ppi * v.velocity, 2)
    v.fillna(value={
        "timespan": 0,
        "velocity": 0.0,
        "yest_price_avg": 0.0,
        "sale_chance": 0.0,
        'stock_remaining': 0.0,
        'dso': 0.0,
        'be': 0.0,
        'ppi': 0.0,
        'rr': 0.0,
        'ppd': 0.0
    },
             inplace=True)
    v.sort_values(by=['ppi'], ascending=False, inplace=True)
    v.drop(columns=['type_id'], inplace=True)
    return v