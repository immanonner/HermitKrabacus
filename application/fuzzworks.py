import bz2
from concurrent.futures import ThreadPoolExecutor
import csv
import requests
from pathlib import Path
from .models import InvTypes, InvVolumes, SolarSystems, db
from application import f_cache, utils
import datetime as dt
from config import EVE_NULL_REGIONS


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
                    "Proving" not in rw['typeName'] and
                    "Cerebral Accelerator" not in rw['typeName'] and
                    "skill accelerator" not in rw['typeName'] and
                    "Hunt" not in rw['typeName'] and rw['marketGroupID'] != None
                ]

            if name == "invVolumes":
                # rename the volume column to "packVolume"
                resp_body = [{
                    "typeID": rw.pop("typeID"),
                    "packVolume": float(rw.pop("volume"))
                } for rw in resp_body]

            if name == "mapSolarSystems":
                # include only the appropriate regions named in config; keep only 5 columns from source data
                resp_body = [{
                    "regionID": int(rw.pop("regionID")),
                    "constellationID": int(rw.pop("constellationID")),
                    "solarSystemID": int(rw.pop("solarSystemID")),
                    "solarSystemName": rw.pop("solarSystemName"),
                    "security": float(rw.pop("security")),
                    "securityClass": rw.pop("securityClass")
                }
                             for rw in resp_body
                             if int(rw['regionID']) in EVE_NULL_REGIONS]
        else:
            resp_body = resp.status_code
        return {name: resp_body}

    with ThreadPoolExecutor(max_workers=2) as pool:
        fuzz_urls = [
            r"https://www.fuzzwork.co.uk/dump/latest/invTypes.csv.bz2",
            r"https://www.fuzzwork.co.uk/dump/latest/invVolumes.csv.bz2",
            r"https://www.fuzzwork.co.uk/dump/latest/mapSolarSystems.csv.bz2",
        ]
        results = {}
        for result in pool.map(__shim, fuzz_urls):
            results.update(result)
    return results


@utils.timer_func
def update_eve_sde(force=False):
    # check fuzz sde current as of date in cache
    sde_cao = f_cache.get('sde_cao')
    if sde_cao is None or dt.date.today() - sde_cao >= dt.timedelta(
            days=1) or force:
        # pull data from latest fuzz repo / convert response to list of dicts / insert into db
        fuzz_data = get_fuzz_latest()
        if type(fuzz_data['invTypes'][0]) is dict:
            InvTypes.query.delete()
            db.session.execute(InvTypes.__table__.insert(),
                               fuzz_data['invTypes'])
        if type(fuzz_data['invVolumes'][0]) is dict:
            InvVolumes.query.delete()
            db.session.execute(InvVolumes.__table__.insert(),
                               fuzz_data['invVolumes'])
        # join tables and replace the values of the unpacked volumes with the packed versions if applicable
        db.session.execute("""UPDATE invTypes
                              set volume=(SELECT packVolume
                                          from invVolumes
                                          where typeID=invTypes.typeID)
                              where EXISTS(SELECT packVolume
                                           from invVolumes
                                           where typeID=invTypes.typeID)""")
        if type(fuzz_data['mapSolarSystems'][0]) is dict:
            SolarSystems.query.delete()
            db.session.execute(SolarSystems.__table__.insert(),
                               fuzz_data['mapSolarSystems'])
        db.session.commit()
        # set new cao
        f_cache.set('sde_cao', dt.date.today(), expire=86400)
