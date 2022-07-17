import bz2
from concurrent.futures import ThreadPoolExecutor
import csv
import requests
from pathlib import Path
from .models import InvTypes, InvVolumes, SolarSystems, db
from application import f_cache, utils
import datetime as dt
import pandas as pd
from os import path, remove
from dask import dataframe as dd
from config import EVE_NULL_REGIONS, EVE_MARKET_HUBS, SQLALCHEMY_DATABASE_URI


def daterange(start_date, end_date):
    for n in range(int((end_date - start_date).days)):
        yield start_date + dt.timedelta(n)


def dump_pq_analysis_to_sql():
    df = pd.read_parquet('application/eveRefParquet')
    df = df.groupby(['regionID',
                     'typeID']).agg(aggVol=('volume', 'sum'),
                                    listDate=('date', 'min'),
                                    records=('date', 'count'),
                                    lastPriceAvg=('average', 'last'))
    df['velocity'] = round(
        df.aggVol / (pd.Timestamp.today() - df.listDate).dt.days, 2)
    df['saleChance'] = round(
        df.records / (pd.Timestamp.today() - df.listDate).dt.days, 2)
    df.to_sql('eveRefMarketHistory',
              'sqlite:///application/eveDB.sqlite3',
              if_exists='replace',
              dtype={
                  'priKey': db.BigInteger,
                  'regionID': db.BigInteger,
                  'typeID': db.BigInteger,
                  'listDate': db.Date,
                  'aggVol': db.BigInteger,
                  'records': db.BigInteger,
                  'lastPriceAvg': db.Float,
                  'velocity': db.Float,
                  'saleChance': db.Float
              })


def rebase_everef():
    """Pulls every market history csv record from EVEREF in the last year // parses them with dask.
       dumps to local parquet file
    """
    start_date = (dt.date.today() - dt.timedelta(days=365))
    end_date = dt.date.today()
    rdf = make_everef_requests(start_date, end_date)
    rdf.to_parquet('application/eveRefParquet')


def update_everef():
    """pull the required data and append/rebase as necessary; truncate data > 365 days old
    """
    odf = dd.read_parquet('application/eveRefParquet')
    # exclude data older than 365 days
    odf = odf[(pd.Timestamp.today() - odf.date).dt.days <= 365]
    # get most recent date in PQ
    cao = odf.date.compute().max().to_pydatetime()
    day_diff = (dt.datetime.today() - cao).days
    if day_diff >= 1:
        start_date = (dt.date.today() - dt.timedelta(days=day_diff))
        end_date = dt.date.today()
        udf = make_everef_requests(start_date, end_date)
        # ensure we dont duplicate data upon append
        odf = odf[~odf.date.isin(udf.date.unique())]
        ndf = dd.concat([odf, udf]).compute()
        try:
            remove('application/eveRefParquet')
        except:
            pass
        ndf.to_parquet('application/eveRefParquet')


def make_everef_requests(start_date, end_date):
    """_summary_

    Args:
        start_date (dt.DateTime): oldest date you want from everef
        end_date (dt.DateTime): usually todays date

    Returns:
        _type_: returns dask dataframe
    """
    ref_urls = [
        f'https://data.everef.net/market-history/{d.year}/market-history-{d.isoformat()}.csv.bz2'
        for d in daterange(start_date, end_date)
    ]
    df = dd.read_csv(ref_urls, blocksize=None)
    df = df.drop('http_last_modified', axis=1)
    df = df[df.region_id.isin(EVE_NULL_REGIONS)]

    df.date = dd.to_datetime(df.date, infer_datetime_format=True)
    df = df.rename(
        columns={
            'index': 'priKey',
            'region_id': 'regionID',
            'type_id': 'typeID',
            'order_count': 'orderCount'
        }).compute()
    return df


@utils.timer_func
def update_market_history(force=False):
    # check fuzz sde current as of date in cache
    history_cao = f_cache.get('history_cao')
    if history_cao is None or dt.date.today() - history_cao >= dt.timedelta(
            days=1) or force:
        if path.exists('application/eveRefParquet'):
            update_everef()
        else:
            rebase_everef()
        dump_pq_analysis_to_sql()
        # set new cao
        f_cache.set('history_cao', dt.date.today(), expire=86400)
