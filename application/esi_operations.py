# get each linked eve online user information such as wallet, characters, etc.
# from concurrent.futures import ThreadPoolExecutor

# from application import esiapp, esiclient
# from application.models import Users, db
# from esipy.exceptions import APIException
# from flask import flash
# from flask_login import current_user
import bz2
from concurrent.futures import ThreadPoolExecutor
import csv
import requests
from pathlib import Path
from .models import invTypes, invVolumes, db
from application import f_cache
import datetime as dt


def get_fuzz_latest():

    def __shim(url):
        resp = requests.request("GET", url)
        name = Path(url).name.split(".")[0]
        if resp.status_code == 200:
            resp_body = bz2.decompress(resp._content).decode("utf-8")
            resp_body = [
                csv_row for csv_row in csv.DictReader(resp_body.splitlines())
            ]
            # convert None values with list/dict comprehension
            if name == "invTypes":
                resp_body = [{
                    k: None if v == 'None' else v for k, v in rw.items()
                } for rw in resp_body]
                # CLEAN DATA BEFORE COMMITING TO DB: convert ints to bools in "published" column keep ONLY the published ones and omit unnecessary item pollution
                resp_body = [
                    {
                        k: bool(int(v)) if k == 'published' else v
                        for k, v in rw.items()
                    }
                    for rw in resp_body
                    if rw['published'] == '1' and 'SKIN' not in rw['typeName']
                    and 'Blueprint' not in rw['typeName'] and 'Formula' not in
                    rw['typeName'] and "Men's" not in rw['typeName'] and
                    "Women's" not in rw['typeName'] and
                    rw['marketGroupID'] != None
                ]

            if name == "invVolumes":
                # rename the volume column to "packVolume"
                resp_body = [{
                    "typeID": rw.pop("typeID"),
                    "packVolume": float(rw.pop("volume"))
                } for rw in resp_body]
        else:
            resp_body = resp.status_code
        return {name: resp_body}

    with ThreadPoolExecutor(max_workers=2) as pool:
        fuzz_urls = [
            r"https://www.fuzzwork.co.uk/dump/latest/invTypes.csv.bz2",
            r"https://www.fuzzwork.co.uk/dump/latest/invVolumes.csv.bz2"
        ]
        results = {}
        for result in pool.map(__shim, fuzz_urls):
            results.update(result)
    return results


def update_eve_sde():
    # check fuzz sde current as of date in cache
    sde_cao = f_cache.get('sde_cao')
    if sde_cao is not None and dt.date.today() - sde_cao >= dt.timedelta(
            days=1):
        # pull data from latest fuzz repo / convert response to list of dicts / insert into db
        fuzz_data = get_fuzz_latest()
        if type(fuzz_data['invTypes'][0]) is dict:
            invTypes.query.delete()
            db.session.execute(invTypes.__table__.insert(),
                               fuzz_data['invTypes'])
        if type(fuzz_data['invVolumes'][0]) is dict:
            invVolumes.query.delete()
            db.session.execute(invVolumes.__table__.insert(),
                               fuzz_data['invVolumes'])

        # join tables and replace the values of the unpacked volumes with the packed versions if applicable
        db.session.execute("""UPDATE invTypes
                        set volume=(SELECT packVolume
                                    from invVolumes
                                    where typeID=invTypes.typeID)
                        where EXISTS(SELECT packVolume
                                        from invVolumes
                                        where typeID=invTypes.typeID)""")
        db.session.commit()
        # set new cao
        f_cache.set('sde_cao', dt.date.today(), expire=86400)


update_eve_sde()
#     raw_types_df = pd.read_csv(StringIO(results.get('invTypes')))
#     raw_pack_vol_df = pd.read_csv(
#         StringIO(results.get('invVolumes'))).astype({'volume': 'float64'})
#     merged_df = pd.merge(raw_types_df, raw_pack_vol_df,
#                          on='typeID', suffixes=('_lt', '_rt'), how='left')
#     # Finally we use np.where to conditionally select the values we need
#     merged_df['volume'] = np.where(merged_df['volume_rt'].isna(
#     ), merged_df['volume_lt'], merged_df['volume_rt'])

#     # Drop columns which are not needed in output
#     merged_df.drop(['volume_lt', 'volume_rt'], axis=1, inplace=True)
#     merged_df[((merged_df.published > 0) &
#                (merged_df.marketGroupID != 'None') &
#                (merged_df.typeName.str.match(
#                    r"^((?!SKIN|Men's|Women's|Blueprint|Formula).)*$"
#                )))].to_sql("invTypes", db.engine, if_exists="replace")
