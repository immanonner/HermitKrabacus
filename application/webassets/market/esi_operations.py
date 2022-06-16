# get each linked eve online user information such as wallet, characters, etc.
# from concurrent.futures import ThreadPoolExecutor

# from application import esiapp, esiclient
# from application.models import Users, db
# from esipy.exceptions import APIException
# from flask import flash
# from flask_login import current_user
import bz2
import csv


def bz2_csv_rows(fp):
    with bz2.open(fp, mode='rt', newline='') as bzfp:
        for row in csv.reader(bzfp):
            print(row)
            yield row


# if __name__ == "__main__":
bz2_csv_rows('application\invTypes.csv.bz2')

# def get_fuzz_latest():
#     with ThreadPoolExecutor(max_workers=2) as pool:
#         fuzz_reqs = {'invTypes': r"https://www.fuzzwork.co.uk/dump/latest/invTypes.csv",
#                      'invVolumes': r"https://www.fuzzwork.co.uk/dump/latest/invVolumes.csv"}
#         results = {result['file_name']: result['res']
#                    for result in pool.map(lambda fuzzrequest:
#                                           {'file_name': fuzzrequest[0],
#                                            'res': requests.get(fuzzrequest[1]).text
#                                            },
#                                           fuzz_reqs.items())}
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
