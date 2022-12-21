# get each linked eve online user information such as wallet, characters, etc.
from concurrent.futures import ThreadPoolExecutor
import json

from application import esiapp, esiclient
from application.models import Users, db
from config import *
from esipy import EsiClient, EsiSecurity
from esipy.exceptions import APIException
from flask import flash
from flask_login import current_user
import pandas as pd

pd.set_option('display.float_format', lambda x: '%.2f' % x)


def gen_auth_esiclient(user):
    """ we use a toon's information to __init__ a unique esiclient to make requests. 
        ie If I want to have all three of my characters
        wallet information displayed; I need 3 esiclients.

    Args:
        user: db.model / Users() -
        Used to pull sso information to __init__ esipy client
    """

    # init the security object
    security = EsiSecurity(redirect_uri=ESI_CALLBACK,
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
            flash(f'Error refreshing esi token\'s for {user.character_name}',
                  'danger')
            return False

    # init the client
    genclient = EsiClient(security=security,
                          headers={'User-Agent': ESI_USER_AGENT})
    return genclient


def threaded_user_mutli_request(toon):
    """
    Args:
        toon: Users()
    """
    client = gen_auth_esiclient(toon)
    wallet_op = esiapp.op['get_characters_character_id_wallet'](
        character_id=toon.character_id)
    orders_op = esiapp.op['get_characters_character_id_orders'](
        character_id=toon.character_id, token=client.security.access_token)
    transacts_op = esiapp.op['get_characters_character_id_wallet_transactions'](
        character_id=toon.character_id, token=client.security.access_token)
    request_bundle = [wallet_op, orders_op, transacts_op]
    return client.multi_request(request_bundle)


def get_user_eve_info(hist_range):

    results = []
    with ThreadPoolExecutor(max_workers=10) as pool:
        for result in pool.map(threaded_user_mutli_request,
                               current_user.linked_characters()):
            results.append(result)
        # reset esi tokens to origin character's tokens
    results = nested_responses_to_dict(results)
    results = account_analysis(results, hist_range)
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
            req_title = res._Response__op._Operation__operationId.replace(
                "get_characters_character_id_", "")
            if res.status != 200:
                flash(
                    f'Error getting eve info for {toon.character_name}: {req_title}',
                    'danger')
                continue
            account_data[toon.character_name][req_title] = res.data
    return account_data


def account_analysis(account_data, hist_range):
    #get typenames and structure names on the dfs
    structure_names = pd.read_sql_query(
        'select struc_id, name from structureMarkets', db.engine)
    types_df = pd.read_sql_query('select typeID, typeName from invTypes',
                                 db.engine)
    # ========================market history analysis======================================
    cgf = pd.DataFrame.from_records(
        account_data.get("Chelsea's Grin").get('wallet_transactions'))
    bdf = pd.DataFrame.from_records(
        account_data.get('Baron Dashforth').get('wallet_transactions'))

    df = pd.concat([cgf, bdf])
    df.date = pd.to_datetime(df.date.apply(lambda x: x.v.date().isoformat()))
    # adjust the records to reflect the users desire: less than 30 days or month-to-date
    rng = pd.Timedelta(days=hist_range) if hist_range <= 30 else pd.Timedelta(
        days=pd.to_datetime("today").day - 1,
        hours=pd.to_datetime("today").hour,
        minutes=pd.to_datetime("today").minute,
        seconds=pd.to_datetime("today").second,
        microseconds=pd.to_datetime("today").microsecond - 1)
    df = df[df.date >= (pd.to_datetime("today") - rng)]

    df['total_transact'] = df.quantity * df.unit_price
    # get the total amount of isk spent on each type; get amount of days between first buy and last sell transaction per type; get sum of volume per type
    ndf = df.groupby(['is_buy', 'type_id'], as_index=False).agg({
        'date': [
            'nunique', lambda x:
            (pd.to_datetime("today") - x.min()
             if x.max() == x.min() else x.max() - x.min()).days
        ],
        'quantity': 'sum',
        'total_transact': 'sum'
    })
    ndf['avg_price'] = ndf.total_transact / ndf.quantity

    # seperate out the buy and sell dataframes
    sells = pd.DataFrame(ndf[ndf.is_buy == False])
    buys = pd.DataFrame(ndf[ndf.is_buy == True])
    # join buy/sell side by side rather than on top of each other
    intermediate_df = pd.merge(buys, sells, how='outer', on='type_id').drop(
        columns=['is_buy_x', 'is_buy_y', ('date_x', '<lambda_0>')])

    # flatten multiindex
    intermediate_df.columns = [
        ' & '.join(col).rstrip('_') if col[1] != '' else col[0]
        for col in intermediate_df.columns.values
    ]

    intermediate_df.rename(columns={
        'date_x & nunique': 'buy_freq',
        'date_y & nunique': 'sell_freq',
        'date_y & <lambda_0>': 'shelf_life',
        'quantity_x & sum': 'buy_quantity',
        'quantity_y & sum': 'sell_quantity',
        'total_transact_x & sum': 'buy_total_value',
        'total_transact_y & sum': 'sell_total_value',
        'avg_price_x': 'buy_avg_price',
        'avg_price_y': 'sell_avg_price'
    },
                           inplace=True)
    # apply base values to the dataframe
    default_values = {
        'buy_freq': 0,
        'sell_freq': 0,
        'shelf_life': pd.Timedelta(0).days,
        'buy_quantity': 0,
        'sell_quantity': 0,
        'buy_total_value': 0,
        'sell_total_value': 0,
        'buy_avg_price': 0,
        'sell_avg_price': 0
    }
    intermediate_df.fillna(default_values, inplace=True)
    # dervive stats from the dataframe

    intermediate_df[
        'profit_per_item'] = intermediate_df.sell_avg_price - intermediate_df.buy_avg_price
    intermediate_df[
        'realized_profit'] = intermediate_df.profit_per_item * intermediate_df.sell_quantity

    intermediate_df[
        'realized_velocity'] = intermediate_df.sell_quantity / intermediate_df.shelf_life
    intermediate_df[
        'realized_ppd'] = intermediate_df.realized_profit / intermediate_df.shelf_life
    intermediate_df[
        'realized_roi'] = intermediate_df.realized_profit / intermediate_df.buy_total_value
    # get typeNames to typeID
    intermediate_df = pd.merge(
        intermediate_df,
        types_df,
        how='inner',
        left_on='type_id',
        right_on='typeID').drop(columns=['typeID']).sort_values('realized_ppd',
                                                                ascending=False)

    # Reordered column typeName
    intermediate_df_columns = [
        col for col in intermediate_df.columns if col != 'typeName'
    ]
    intermediate_df_columns.insert(0, 'typeName')
    intermediate_df = intermediate_df[intermediate_df_columns]

    # Reordered column sell_freq
    intermediate_df_columns = [
        col for col in intermediate_df.columns if col != 'sell_freq'
    ]
    intermediate_df_columns.insert(2, 'sell_freq')
    intermediate_df = intermediate_df[intermediate_df_columns]

    # Reordered column shelf_life
    intermediate_df_columns = [
        col for col in intermediate_df.columns if col != 'shelf_life'
    ]
    intermediate_df_columns.insert(1, 'shelf_life')
    intermediate_df = intermediate_df[intermediate_df_columns]

    # Reordered column sell_quantity
    intermediate_df_columns = [
        col for col in intermediate_df.columns if col != 'sell_quantity'
    ]
    intermediate_df_columns.insert(5, 'sell_quantity')
    intermediate_df = intermediate_df[intermediate_df_columns]

    # Reordered column sell_total_value
    intermediate_df_columns = [
        col for col in intermediate_df.columns if col != 'sell_total_value'
    ]
    intermediate_df_columns.insert(7, 'sell_total_value')
    intermediate_df = intermediate_df[intermediate_df_columns]

    # ================current orders=================
    orders_df = pd.DataFrame.from_records(
        account_data.get("Baron Dashforth").get('orders'))
    orders_df = pd.concat([
        orders_df,
        pd.DataFrame.from_records(
            account_data.get("Chelsea's Grin").get('orders'))
    ])
    orders_df.drop(columns=['duration', 'is_corporation', 'range', 'issued'],
                   inplace=True)
    orders_df[
        'remaining_order_value'] = orders_df.price * orders_df.volume_remain
    # get structure name to structureID
    orders_df = pd.merge(
        orders_df,
        structure_names,
        how='inner',
        left_on='location_id',
        right_on='struc_id').drop(columns=['location_id', 'struc_id'])
    # get typeNames to typeID
    orders_df = pd.merge(orders_df,
                         types_df,
                         how='inner',
                         left_on='type_id',
                         right_on='typeID').drop(columns=['typeID'])

    #reserve the order stats as its own df to pass to the webpage
    order_stats_df = orders_df.groupby(['name'], as_index=False).agg(
        order_count=('type_id', 'count'),
        unrealized_revenue=('remaining_order_value', 'sum'))

    #group orders on type ids to display relevant data
    orders_df = orders_df.groupby(['type_id'], as_index=False).agg({
        'typeName': 'first',
        'volume_remain': 'sum',
        'remaining_order_value': 'sum'
    })
    orders_df[
        'sell_avg_price'] = orders_df.remaining_order_value / orders_df.volume_remain

    #join market history to orders to get the buy avg price and shelf life per type id
    orders_df = pd.merge(
        orders_df,
        intermediate_df[['type_id', 'buy_avg_price', 'shelf_life']],
        how='left',
        on='type_id').drop(columns=['type_id'])
    intermediate_df.drop(columns=['type_id'], inplace=True)
    orders_df[
        'current_profit_per_item'] = orders_df.sell_avg_price - orders_df.buy_avg_price
    orders_df[
        'unrealized_profit'] = orders_df.current_profit_per_item * orders_df.volume_remain
    orders_df[
        'current_roi'] = orders_df.current_profit_per_item / orders_df.buy_avg_price
    # apply base values to the dataframe
    default_values = {
        'buy_avg_price': 0,
        'sell_avg_price': 0,
        'shelf_life': pd.Timedelta(0).days,
        'current_profit_per_item': 0,
        'unrealized_profit': 0,
        'remaining_order_value': 0,
        'volume_remain': 0,
        'current_roi': 0,
    }
    orders_df.fillna(default_values, inplace=True)

    # Reordered column buy_avg_price
    orders_df_columns = [
        col for col in orders_df.columns if col != 'buy_avg_price'
    ]
    orders_df_columns.insert(1, 'buy_avg_price')
    orders_df = orders_df[orders_df_columns]

    # Reordered column sell_avg_price
    orders_df_columns = [
        col for col in orders_df.columns if col != 'sell_avg_price'
    ]
    orders_df_columns.insert(2, 'sell_avg_price')
    orders_df = orders_df[orders_df_columns]

    # Reordered column remaining_order_value
    orders_df_columns = [
        col for col in orders_df.columns if col != 'remaining_order_value'
    ]
    orders_df_columns.insert(3, 'remaining_order_value')
    orders_df = orders_df[orders_df_columns]

    # Reordered column current_profit_per_item
    orders_df_columns = [
        col for col in orders_df.columns if col != 'current_profit_per_item'
    ]
    orders_df_columns.insert(3, 'current_profit_per_item')
    orders_df = orders_df[orders_df_columns]

    # Reordered column unrealized_profit
    orders_df_columns = [
        col for col in orders_df.columns if col != 'unrealized_profit'
    ]
    orders_df_columns.insert(4, 'unrealized_profit')
    orders_df = orders_df[orders_df_columns]

    # Sorted current_roi in ascending order
    orders_df = orders_df.sort_values(by='current_roi',
                                      ascending=True,
                                      na_position='first')

    #====================statistics===================

    realized_profit = intermediate_df[
        intermediate_df.buy_quantity > 0].realized_profit.sum()
    unrealized_profit = orders_df[
        orders_df.buy_avg_price > 0.0].unrealized_profit.sum()

    late_realized_revenue = intermediate_df[intermediate_df.buy_quantity ==
                                            0].sell_total_value.sum()
    late_unrealized_revenue = orders_df[orders_df.buy_avg_price ==
                                        0.0].remaining_order_value.sum()
    realized_revenue = intermediate_df.sell_total_value.sum(
    ) - late_realized_revenue
    realized_roi = (realized_profit /
                    realized_revenue) if realized_revenue > 0 else 0

    total_unrealized_revenue = orders_df.remaining_order_value.sum()

    statistics = [{
        'ontime_realized_profit': realized_profit,
        'ontime_realized_revenue': realized_revenue,
        'ontime_realized_roi': realized_roi,
        'ontime_unrealized_profit': unrealized_profit,
        'total_unrealized_revenue': total_unrealized_revenue,
        'total_realized_revenue': realized_revenue + late_realized_revenue,
        'late_realized_revenue': late_realized_revenue,
        "late_unrealized_revenue": late_unrealized_revenue,
    }]
    #====================output===================

    account_data.get("Baron Dashforth")['orders'] = orders_df.to_json(
        orient='records')
    account_data.get(
        "Baron Dashforth")['wallet_transactions'] = intermediate_df.to_json(
            orient='records')
    account_data.get("Baron Dashforth")['order_stats'] = order_stats_df.to_json(
        orient='records')
    account_data.get("Baron Dashforth")['stats'] = json.dumps(statistics)
    return account_data