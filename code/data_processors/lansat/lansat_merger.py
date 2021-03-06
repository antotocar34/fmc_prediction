# %%
from typing import List, Union, Dict
from pathlib import Path
import pickle, os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import date, datetime
from tqdm import tqdm
# %%
# STATS_PROJ = "/home/carneca/Documents/College/masters/semester1/stats/assignment/fmc_prediction"
STATS_PROJ = os.getenv("STATS_PROJ")
# STATS_PROJ = f"{os.path.dirname(os.path.realpath(__file__))}/../../.."
# %%
def inspect_date_column(df, date_col_str: str):
    dates = df[date_col_str]
    min_date = np.min(dates)
    max_date = np.max(dates)
    print(f"Min date: {min_date}")
    print(f"Max date: {max_date}")
    print(f"Unique dates: {len(dates.unique())}")
# %%
data_loc = Path(f"{STATS_PROJ}/code/data/processed_data/archive/socc_synoptic_complete.pkl")
assert data_loc.exists()
with open(data_loc, 'rb') as f:
    synoptic_df = pickle.load(f)
# %%
with open(f"{STATS_PROJ}/code/data/processed_data/remotesensing_imputed.pkl", 'rb') as f:
    ndvi_df = pickle.load(f)
    print(ndvi_df.shape)
# %%
#with open(f"{STATS_PROJ}/code/data/clean_data/wfas/SOCC_cleaned.pkl", 'rb') as f:
    #socc_df = pickle.load(f)
    #socc_df = socc_df.sort_values(by="Date")
    #socc_df.Fuel = socc_df.Fuel.apply(lambda s: s.lower())
    #print(socc_df.shape)
# %%
with open(f"{STATS_PROJ}/code/data/clean_data/try/SOCC_cleaned_tryid.pkl", 'rb') as f:
    try1_df = pickle.load(f)
    print(try1_df.shape)
# %%
with open(f"{STATS_PROJ}/code/data/clean_data/try/plant_traits.pkl", 'rb') as f:
    try2_df = pickle.load(f)
    print(try2_df.shape)
# %% Merging the try data
socc_try_traits_df = try1_df.merge(try2_df.reset_index(), how="left", on="AccSpeciesID")

#%%
socc_try_traits_df["coord"] = socc_try_traits_df["Longitude"].apply(lambda x: str(x)) + "_" + socc_try_traits_df["Latitude"].apply(lambda x: str(x))
ndvi_df["coord"] = ndvi_df["longitude"].apply(lambda x: str(x)) + "_" + ndvi_df["latitude"].apply(lambda x: str(x))

coords = ndvi_df["coord"].unique()
assert(set(ndvi_df["coord"].unique()) == set(socc_try_traits_df["coord"].unique()))

def get_closest_date(ndvidates, socc_date):
    try:
        return ndvidates[ndvidates<socc_date].reset_index(drop=True)[0]
    except KeyError:
        return np.nan

def match_ndvi_date(ndvi_df, socc_try_traits_df, coord):
    subsetndvi = ndvi_df[ndvi_df["coord"] == coord]
    subsetsocc = socc_try_traits_df[socc_try_traits_df["coord"] == coord]

    ndvidates = subsetndvi["date"].sort_values(ascending=False).reset_index(drop=True)
    soccdates = subsetsocc["Date"].sort_values(ascending=False).reset_index(drop=True)

    mapping = {dt: get_closest_date(ndvidates, dt) for dt in soccdates}

    subsetsocc["ndvidate"] = subsetsocc["Date"].map(mapping)
    return subsetsocc

socc_subsets = [match_ndvi_date(ndvi_df, socc_try_traits_df, coord) for coord in tqdm(coords)]
#%%
socc_try_traits_df = pd.concat(socc_subsets, ignore_index=True)
socc_ndvi = pd.merge(socc_try_traits_df, ndvi_df.drop(["longitude", "latitude"], axis=1), left_on=["ndvidate", "coord"], right_on=["date", "coord"], how="left")
socc_ndvi["ndvi_time_lag"] = (socc_ndvi["Date"] - socc_ndvi["ndvidate"]).dt.days
socc_ndvi = socc_ndvi.drop(["date", "ndvidate", "coord", "Zip", "Longitude", "Latitude", "scientificname"], axis=1)

#%%
socc_synoptic = pd.read_pickle(f"{STATS_PROJ}/code/data/processed_data/archive/socc_synoptic_complete.pkl")
socc_synoptic["Fuel"] = socc_synoptic["Fuel"].apply(lambda x: x.lower())

socc_total = pd.merge(socc_synoptic, socc_ndvi.drop(["State", "GACC", "Group", "Percent"], axis=1), on=["Site", "Date", "Fuel"], how="inner")

#%%
socc_total.to_pickle(f"{STATS_PROJ}code/data/processed_data/socc_total.pkl")
socc_total.to_csv(f"{STATS_PROJ}code/data/processed_data/socc_total.csv")

















# # %% Match ndvi and socc dates
# def diff_days(fmc_date: datetime, ndvi_date: datetime) -> int:
#     return ((fmc_date - ndvi_date)/np.timedelta64(1, 'D'))

# def diff_test(fmc_date: datetime, ndvi_date: datetime) -> bool:
#     days = diff_days(fmc_date, ndvi_date)
#     if 0 < days < 30: # Negative indicates that ndvi date is ahead of fmc date
#         return True
#     else:
#         return False

# ndvi_dates = ndvi_df.date.unique()
# socc_dates = socc_try_traits_df.Date.unique()
# # socc_dates = socc_dates[(socc_dates > np.min(ndvi_dates)) & (socc_dates < np.max(ndvi_dates))]

# def dstr(date: Union[datetime, float]) -> Union[str, float]:
#     if bool(date) == False:
#         print("LOOK HERE!")
#         return np.nan
#     try:
#         string = np.datetime_as_string(date, unit="D")
#     except TypeError:
#         string = date.strftime("%Y-%m-%d")
#     return string

# def map_sattelite_dates_to_fmc_dates(
#         socc_dates: List[datetime], ndvi_dates: List[datetime]
#         ) -> Dict[str, Union[List[pd.Timestamp], float]]:
#     """
#     Create a dictionary where keys are fmc_dates and values 
#     are lists of all ndvi dates that are 30 days before
#     every fmc date.
#     """
#     dic = {}
#     for fmc_date in socc_dates:
#         key = dstr(fmc_date) # store the keys as strings
#         for ndvi_date in ndvi_dates:
#             if diff_test(fmc_date, ndvi_date):
#                 if not dic.get(key): # If key is not already in dictionary
#                     dic[key] = []
#                 dic[key].append(ndvi_date)
#         if not dic.get(key):
#             dic[key] = np.nan
#         dic[key]
#     return dic

# def handle_value(key: str, value: Union[List[datetime], float]) -> Union[datetime, float]:
#     """
#     Handle cases where more than one ndvi date is found for a given fmc date
#     """
#     if type(value) == float:
#         return np.nan
#     else:
#         assert type(value) is not float
#         if len(value) == 1:
#             return value[0]
#         else:
#             return min(value, key=lambda d: diff_days(pd.Timestamp(str(key)), d))



# out_dict = map_sattelite_dates_to_fmc_dates(ndvi_dates, socc_dates)            
# out_dict2 = {k:handle_value(k, v) for k, v in out_dict.items()}
# assert len(out_dict2.values()) == len(socc_dates)


# # %% Associate with every socc date an ndvi date.
# socc_try_traits_df["NDVI_date"] = socc_try_traits_df.Date.apply(dstr).apply(lambda date: out_dict2.get(date, np.nan))
# # %%
# print(len([x for x in socc_try_traits_df["NDVI_date"] if pd.isnull(x)])/len(socc_try_traits_df.NDVI_date))
# # %% Check that the code is working properly
# assert len(out_dict.keys()) == len(socc_dates), str(abs(len(out_dict.keys()) - len(socc_dates)))
# # assert set(out_dict.keys()) == set(socc_dates)
# # %%
# merged = socc_df.merge(ndvi_df, how="left", left_on=["NDVI_date", "Longitude", "Latitude"], right_on=["date", "longitude", "latitude"]) \
#                 .drop([ "date", "longitude", "latitude"], axis=1)
# # %%
# merge_columns = ['GACC', 'State', 'Group', 'Site', 'Date', 'Fuel', 'Percent', 'Latitude',
#        'Longitude', 'Zip']
# print(merged.shape)
# print(merged.NDVI.isnull().mean())
# # %%
# fully_merged = merged.merge(try_df, how="left", on=merge_columns) 
# fully_merged = fully_merged.drop([c for c in fully_merged.columns if "_y" in str(c)], axis=1)
# fully_merged.columns = [(c.split("_x")[0] if "_x" in c else c) for c in map(str, fully_merged.columns)]
# # %%
# merge_columns = ["Group", "Site", "Fuel", "Date"]
# final = fully_merged.merge(synoptic_df, how="inner", on=merge_columns)
# final
# # %%
