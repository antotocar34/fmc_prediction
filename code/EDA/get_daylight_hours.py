#%%
import pandas as pd
import os, pickle
from datetime import date, datetime, timedelta
import numpy as np
from tqdm import tqdm
import requests

os.chdir(f"{os.path.dirname(os.path.realpath(__file__))}/../..")

#%%
def get_daylight_hours(date, lat, long):
    '''Gets daylight hours for date, lat and long.
    Args:
        date: Date in datetime format
        lat: Float. Latitude
        long: Float. Longitude
    Returns:
        Float. Number of daylight hours'''
    date = date.date().isoformat()
    params = {"lat": lat, "long" : long, "date" : date}
    r = requests.get(url="https://api.sunrise-sunset.org/json", params=params)
    hours = r.json()["results"]["day_length"].split(":")
    hours = float(hours[0]) + float(hours[1])/60
    return hours

socc_geo = pd.read_pickle("code/data/clean_data/wfas/SOCC_cleaned.pkl")
socc_geo = socc_geo.groupby("Site").agg({"Latitude":"max", "Longitude":"max"}).reset_index()

socc = pd.read_pickle("code/data/interim_data/socc_noaa_filtered_fulldaterange_imputed.pkl")
socc = pd.merge(socc, socc_geo, how="left", on="Site")
socc = socc.loc[:,["Date", "Site", "Latitude", "Longitude"]]

try:
    with open("code/data/tmp/daylight_hours.pkl", "rb") as infile:
        daylight_hours = pickle.load(infile) 
except OSError:
    daylight_hours = []
for i in tqdm(list(range(len(daylight_hours), len(socc)))):
    daylight_hours.append(get_daylight_hours(date=socc.loc[i,"Date"], lat=socc.loc[i,"Latitude"], long=socc.loc[i,"Longitude"]))
    if i%1000 == 0:
        with open("code/data/tmp/daylight_hours.pkl", "wb") as outfile:
            pickle.dump(daylight_hours, outfile) 
socc["daylight_hours"] = daylight_hours
socc.to_pickle("code/data/raw_data/other/socc_noaa_daylight_hours.pkl")
#%%