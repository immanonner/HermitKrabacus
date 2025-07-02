# this is a simple script to retrieve the current sell orders in Jita
# it interacts with the EVE Online ESI API
# it then stores the data in a parquet file
import json
import os

import pandas as pd
from esipy import EsiApp, EsiClient, EsiSecurity, cache

from config import ESI_CALLBACK, ESI_CLIENT_ID, ESI_SECRET_KEY, ESI_USER_AGENT
from application.utils import timer_func

f_cache = cache.FileCache(path="./f_cache")
# create the eve app interface
esiapp = EsiApp(cache=f_cache).get_latest_swagger

# init the security object
esisecurity = EsiSecurity(
    redirect_uri=ESI_CALLBACK,
    client_id=ESI_CLIENT_ID,
    secret_key=ESI_SECRET_KEY,
    headers={"User-Agent": ESI_USER_AGENT},
)

# init the client
esiclient = EsiClient(
    security=esisecurity, cache=f_cache, headers={"User-Agent": ESI_USER_AGENT}
)

@timer_func
def fetch_jita_sell_orders():
    rsp = esiclient.request(
        esiapp.op["get_markets_region_id_orders"](region_id=10000002)
    )
    if rsp.status == 200:
        pages = rsp.header["X-Pages"][0]
        expires = rsp.header["expires"][0]
        results = [{"expires": expires, **rec} for rec in json.loads(rsp.raw)]
        if pages > 1:
            operations = []
            for page in range(2, pages + 1):
                operations.append(
                    esiapp.op["get_markets_region_id_orders"](
                        region_id=10000002, page=page
                    )
                )
        [
            results.extend(
                [
                    {"expires": rs.header["expires"][0], **rec}
                    for rec in json.loads(rs.raw)
                ]
            )
            for _, rs in esiclient.multi_request(operations, raw_body_only=True)
            if rs.status == 200
        ]
        # clean the data in results
        return results


if __name__ == "__main__":
    jso = fetch_jita_sell_orders()
    if jso:
        print(f"Retrieved {len(jso)} sell orders from Jita.")
        # Here you can save the data to a file or process it further
        # For example, saving to a parquet file
        df = pd.DataFrame(jso)
        # if file exists, remove it and create a new one
        try:
            os.remove("jita_sell_orders.parquet")
        except FileNotFoundError:
            pass
        df.to_parquet("jita_sell_orders/jita_sell_orders.parquet")
    else:
        print("No sell orders retrieved.")
