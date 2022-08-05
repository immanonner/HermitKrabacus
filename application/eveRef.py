from .models import db
from application import f_cache, utils
import datetime as dt
import pandas as pd
import requests as r
import io
import bz2
from dask import dataframe as dd
from config import EVE_NULL_REGIONS


def daterange(start_date, end_date):
    for n in range(int((end_date - start_date).days)):
        yield start_date + dt.timedelta(n)


def run_market_analysis(df):
    df = df.groupby(['regionID', 'typeID']).agg({
        'volume': 'sum',
        'date': ['min', 'count'],
        'average': 'last'
    })
    df['velocity'] = df[('volume', 'sum')] / (pd.Timestamp.today() -
                                              df[('date', 'min')]).dt.days
    df['saleChance'] = df[('date', 'count')] / (pd.Timestamp.today() -
                                                df[('date', 'min')]).dt.days
    df.columns = df.columns.to_flat_index()
    df = df.rename(
        columns={
            ('volume', 'sum'): 'aggVol',
            ('date', 'min'): 'listDate',
            ('date', 'count'): 'records',
            ('average', 'last'): 'lastPriceAvg',
            ('velocity', ''): 'velocity',
            ('saleChance', ''): 'saleChance'
        })
    df = df.round(2)
    return df


def rebase_everef():
    """Pulls every market history csv record from EVEREF in the last year // parses them with dask.
       dumps to local parquet file
    """
    start_date = (dt.date.today() - dt.timedelta(days=365))
    end_date = dt.date.today() - dt.timedelta(days=1)
    rdf = make_everef_requests(start_date, end_date)
    rdf = rdf.set_index('date', drop=False, sorted=True)
    rdf = rdf.repartition(npartitions=1)
    rdf.to_parquet('everefstore', write_index=False, overwrite=True)
    rdf.to_parquet('everefread', write_index=False, overwrite=True)
    adf = run_market_analysis(rdf)
    f_cache.set('adf', adf.compute(), expire=86400)


def update_everef():
    """pull the required data and append/rebase as necessary; truncate data > 365 days old
    """
    hist = dd.read_parquet('everefread')
    hist = hist.set_index('date', drop=False, sorted=True)
    hist = hist.repartition(npartitions=1)
    # get most recent date in PQ

    day_diff = (dt.datetime.today() - hist.date.unique().compute().max()).days
    if day_diff >= 1:
        start_date = (dt.date.today() - dt.timedelta(days=day_diff))
        end_date = dt.date.today()

        # get new information from eve ref
        udf = make_everef_requests(start_date, end_date)
        udf = udf.set_index('date', drop=False, sorted=True)
        udf = udf.repartition(npartitions=1)

        # ensure we dont duplicate data upon append
        odf = hist.loc[pd.Timestamp.today() -
                       pd.Timedelta(days=365):pd.Timestamp(start_date) -
                       pd.Timedelta(days=1)]

        ndf = dd.concat([odf, udf])

        adf = run_market_analysis(ndf)
        ndf = ndf.set_index('date', drop=False, sorted=True)
        ndf = ndf.repartition(npartitions=1)
        adf = adf.repartition(npartitions=1)

        ndf.to_parquet('everefstore', write_index=False, overwrite=True)
        ndf = dd.read_parquet('everefstore')

        ndf = ndf.set_index('date', drop=False, sorted=True)
        ndf = ndf.repartition(npartitions=1)
        ndf.to_parquet('everefread', write_index=False, overwrite=True)

        f_cache.set('adf', adf.compute(), expire=86400)


def make_everef_requests(start_date, end_date):
    """_summary_

    Args:
        start_date (dt.DateTime): oldest date you want from everef
        end_date (dt.DateTime): usually todays date

    Returns:
        _type_: returns dask dataframe
    """
    results = []

    for d in daterange(start_date, end_date):
        s = f'https://data.everef.net/market-history/{d.year}/market-history-{d.isoformat()}.csv.bz2'
        resp = r.get(s)
        if resp.status_code != 200:
            continue
        else:
            decomp_content = bz2.decompress(resp.content)
            bytes_buffer = io.BytesIO(decomp_content)
            pd_pass_through = pd.read_csv(bytes_buffer)
            temp_df = dd.from_pandas(pd_pass_through, npartitions=1)
            results.append(temp_df)

    df = dd.concat(results)
    df = df.drop(['http_last_modified', 'highest', 'lowest', 'order_count'],
                 axis=1)
    df = df[df.region_id.isin(EVE_NULL_REGIONS)]

    df.date = dd.to_datetime(df.date, infer_datetime_format=True)
    df = df.rename(columns={
        'index': 'priKey',
        'region_id': 'regionID',
        'type_id': 'typeID'
    })
    return df


@utils.timer_func
def update_market_history(force=False):
    # check fuzz sde current as of date in cache
    history_cao = f_cache.get('history_cao')
    if history_cao is None or dt.date.today() - history_cao >= dt.timedelta(
            days=1) or force:
        if db.inspect(db.engine).has_table("eveRefMarketHistory"):
            update_everef()
            # else:
            # rebase_everef()
        # set new cao
        f_cache.set('history_cao', dt.date.today(), expire=86400)
