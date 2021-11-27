#%%
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import os, pickle
from datetime import timedelta, datetime
from tqdm import tqdm
import numpy as np
from dateutil import parser
os.chdir(f"{os.path.dirname(os.path.realpath(__file__))}/../..")
#%%
#DATA PROCESSING

#Load data

#Can Match "Site" to "nearest_stid" and "station_distance"
socc_station_list = pd.read_pickle("code/data/raw_data/synoptic/socc_synoptic_stations2.pkl")

#Can look up "elevation" from "stid" here
station_meta = pd.read_pickle("code/data/raw_data/synoptic/station_list2.pkl")

#Final socc data
socc = pd.read_pickle("code/data/clean_data/wfas/SOCC_cleaned.pkl")


ids = pd.read_pickle("code/data/clean_data/try/SOCC_cleaned_tryid.pkl")
ids = ids.groupby("Fuel").agg({"AccSpeciesID":"max"})
#%%
#Further Processing of SOCC

socc = socc[socc["Fuel"].notna()] 
socc = socc[socc["Percent"] < 500] #Drop mismeasured target variables
socc["Fuel"] = socc["Fuel"].apply(lambda x: "Chamise" if x == "chamise" else x) #Fix chamise name
socc.insert(6, "D", socc["Date"].apply(lambda x: np.cos((2*np.pi*x.timetuple().tm_yday/365) - 0.59))) #Add growth cycle based on day
species_ids = [ids.loc[fuel.lower(), "AccSpeciesID"] for fuel in socc["Fuel"]]
socc.insert(5, "AccSpeciesID", species_ids) #Add species IDs
#%%
#Match eleveation to station_list, merge station_list with socc data

socc_station_list = pd.merge(socc_station_list, station_meta.loc[:,["stid", "elevation"]], how="inner", left_on="nearest_stid", right_on="stid")
ci_mask = socc_station_list["nearest_stid"].apply(lambda x: "CI" in x)
socc_station_list = socc_station_list[socc_station_list["station_distance"] <= 30]
socc_station_list = socc_station_list[ci_mask].reset_index(drop=True)
socc = pd.merge(socc, socc_station_list.loc[:,["Site", "nearest_stid", "station_distance", "elevation"]], how="inner", on="Site")\
    .rename(columns={"elevation" : "station_elevation"})\
    .reset_index(drop=True)\
    .loc[:,["Group", "Site", "Fuel", "AccSpeciesID", "Date", "nearest_stid", "station_distance", "station_elevation", "Percent", "D"]]

#%%
#Add weather data
dirpath = "code/data/clean_data/synoptic_weather"
suffix = "_clean.pkl"
def merge_weather_data(dirpath, suffix):
    weather_stations = [station.strip(suffix) for station in os.listdir(dirpath)]
    all_stations = []
    for station in weather_stations:
        station_df = pd.read_pickle(os.path.join(dirpath, f"{station}{suffix}"))
        station_df["stid"] = station
        station_df["date"] = station_df["date"].astype("datetime64[ns]")
        all_stations.append(station_df)
    return pd.concat(all_stations, ignore_index=True)

all_stations = merge_weather_data(dirpath, suffix)
socc = pd.merge(socc, all_stations, how="inner", left_on=["Date", "nearest_stid"], right_on=["date", "stid"])
socc = socc.drop(columns=["date", "stid"])
socc.to_pickle("code/data/processed_data/socc_synoptic_complete.pkl")
socc.to_csv("code/data/processed_data/socc_synoptic_complete.csv")
#%%
feature_interactions = [feature for feature in socc.columns if feature not in ["Date", "Site", "Group", "Fuel", "Percent", "Latitude", "Longitude", "D", "AccSpeciesID", "nearest_stid", "station_elevation", "station_distance"]]

def gen_cycle_interactions(data, cyclename, cols):
    df = data.copy()
    for col in cols:
        df[f"{cyclename}_{col}"] = df[cyclename] * df[col]
    return df

socc_interacted = gen_cycle_interactions(socc, "D", feature_interactions)
#%%
#Save interacted complete subsetted data
socc_interacted.to_pickle("code/data/processed_data/socc_synoptic_complete_interacted.pkl")
socc_interacted.to_csv("code/data/processed_data/socc_synoptic_complete_interacted.csv")

# %%
