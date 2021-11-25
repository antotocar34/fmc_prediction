#%%
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import os, pickle
from datetime import timedelta, datetime
from tqdm import tqdm
import numpy as np
from time import time
os.chdir(f"{os.path.dirname(os.path.realpath(__file__))}/../..")
#%%
#DATA PROCESSING

#Load data
socc = pd.read_pickle("code/data/interim_data/socc_noaa_subset_aggregated.pkl")
ids = pd.read_pickle("code/data/clean_data/try/SOCC_cleaned_tryid.pkl")
ids = ids.groupby("Fuel").agg({"AccSpeciesID":"max"})

#Further Cleaning steps

socc = socc[socc["Fuel"].notna()] 
socc = socc[socc["Percent"] < 500] #Drop mismeasured target variables
socc["Fuel"] = socc["Fuel"].apply(lambda x: "Chamise" if x == "chamise" else x) #Fix chamise name
socc.insert(6, "D", socc["Date"].apply(lambda x: np.cos((2*np.pi*x.timetuple().tm_yday/365) - 0.59))) #Add growth cycle based on day
species_ids = [ids.loc[fuel.lower(), "AccSpeciesID"] for fuel in socc["Fuel"]]
socc.insert(5, "AccSpeciesID", species_ids) #Add species IDs
socc = socc.drop(columns=["Day_factor", "daylight"])
#%%
#Save complete dsubsetted data before interactions
socc.to_pickle("code/data/processed_data/socc_noaa_subset_complete.pkl")
socc.to_csv("code/data/processed_data/socc_noaa_subset_complete.csv")

#%%
feature_interactions = [feature for feature in socc.columns if feature not in ["Date", "Site", "Fuel", "Percent", "Latitude", "Longitude", "D", "AccSpeciesID"]]

def gen_cycle_interactions(data, cyclename, cols):
    df = data.copy()
    for col in cols:
        df[f"{cyclename}_{col}"] = df[cyclename] * df[col]
    return df

socc_interacted = gen_cycle_interactions(socc, "D", feature_interactions)
#%%
#Save interacted complete subsetted data
socc_interacted.to_pickle("code/data/processed_data/socc_noaa_subset_complete_interacted.pkl")
socc_interacted.to_csv("code/data/processed_data/socc_noaa_subset_complete_interacted.csv")

# %%
