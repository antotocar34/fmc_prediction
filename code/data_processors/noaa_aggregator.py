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

# #%%

# #Load matched and fulldaterange data
# total_matched= pd.read_pickle("code/data/interim_data/socc_noaa_filtered_wfasmatched_imputed.pkl")
# total_socc = pd.read_pickle("code/data/interim_data/socc_noaa_filtered_fulldaterange_imputed.pkl")
# #%%

# #Add head index
# def mon_hi(x):
#     return (max(0,x)/5)**1.514

# def get_hi(i, df, tavg = "tavg_m"):
#     site = df.loc[i,"Site"]
#     year = df.loc[i, "year"]
#     month = df.loc[i, "month"]
#     heat_indices = []
#     forward = False
#     while len(heat_indices) < 12:
#         if forward == False:
#             if month > 1:
#                 mavg = df[(df["Site"] == site) & (df["year"] == year) & (df["month"] == month - 1)][tavg].sum()
#                 month -= 1
#             elif month == 1:
#                 mavg = df[(df["Site"] == site) & (df["year"] == year - 1) & (df["month"] == 12)][tavg].sum()
#                 month = 12
#                 year -= 1
#             if mavg == 0.0:
#                 year = df.loc[i, "year"]
#                 month = df.loc[i, "month"]
#                 forward = True
#             else:
#                 heat_indices.append(mon_hi(mavg))
#         elif forward == True:
#             if month < 12:
#                 mavg = df[(df["Site"] == site) & (df["year"] == year) & (df["month"] == month + 1)][tavg].sum()
#                 month += 1
#             elif month == 12:
#                 mavg = df[(df["Site"] == site) & (df["year"] == year + 1) & (df["month"] == 1)][tavg].sum()
#                 month = 1
#                 year += 1
#             if mavg == 0.0:
#                 times = 12 - len(heat_indices)
#                 avg_hi = np.mean(np.array(heat_indices))
#                 for _ in range(times):
#                     heat_indices.append(avg_hi)
#             else:
#                 heat_indices.append(mon_hi(mavg))
#     return sum(heat_indices)

# def hi_col(df):
#     '''Adds heat index column to df. Counts on being sorted by site then date'''
#     heat_index = []
#     for i in df.index:
#         heat_index.append(get_hi(i, df))
#     df["heat_index"] = heat_index
#     return df

# total_socc["year"] = total_socc["Date"].apply(lambda x: x.timetuple().tm_year)
# total_socc["month"] = total_socc["Date"].apply(lambda x: x.timetuple().tm_mon)
# total_socc["TAVG"] = (total_socc["TMAX"] + total_socc["TMIN"])/2
# tavg_m = total_socc.groupby(["Site", "year", "month"]).agg({"TAVG" :"mean"}).rename(columns={"TAVG":"tavg_m"})
# heat_index = hi_col(tavg_m.reset_index())
# total_socc = pd.merge(total_socc, heat_index.loc[:,["Site", "year", "month", "heat_index"]], on=["Site", "year", "month"])


# #%%

# #Add effectice PRCP
# total_socc["PRCP_EFF"] = total_socc["PRCP"].apply(lambda x: 0.83 * x - 1.27 if x > 2.8 else 0)

# #Compute potential evapo transpiration
# day_length_factor = {1: -1.6, 2: -1.6, 3: -1.6, 4 : 0.9, 5 : 3.8, 6 : 5.8, 7 : 6.4,
#  8 : 5.0, 9 : 2.4, 10 : 0.4, 11 : -1.6, 12 : -1.6}
# total_socc["Day_factor"] = total_socc["month"].apply(lambda m: day_length_factor[m])
# total_socc["TAVG_LB"] = total_socc["TAVG"].apply(lambda t: t if t >= -2.8 else -2.8)
# total_socc["EVAP_POT"] = 0.36 * (total_socc["TAVG_LB"] + 2.8) + total_socc["Day_factor"]
# total_socc["EVAP_POT"] = total_socc["EVAP_POT"].apply(lambda v: v if v >=0 else 0)

# #Add Drought Code

# def moisture_equiv(dc):
#     return 800 * np.exp(-dc/400)

# def compute_DC(prev_DC, prcp_eff, evap_pot):
#     if prev_DC == 0 :
#         prev_DC = 15
#     if prcp_eff == 0:
#         return prev_DC + 0.5 * evap_pot
#     else:
#         DC = 400 * np.log(800/(moisture_equiv(prev_DC) + 3.947 * prcp_eff))
#         if DC > 0:
#             return DC + 0.5 * evap_pot
#         else:
#             return 0.5 * evap_pot

# def build_DC(df):
#     '''Adds a Drought code column, counts on being sorted by Site then Date'''
#     df["DC"] = 15
#     for i in df.index:
#         prev_dc = df[(df["Site"] == df.loc[i,"Site"]) & (df["Date"] == df.loc[i,"Date"] - timedelta(days=1))]["DC"].sum()
#         df.loc[i, "DC"] = compute_DC(prev_dc, prcp_eff=df.loc[i, "PRCP_EFF"], evap_pot=df.loc[i,"EVAP_POT"]) 
#     return df

# total_socc = build_DC(total_socc)
# #%%

# #Calculate Thornwaite Evapotranspiration

# #First add daylight hours
# daylight_hours = pd.read_pickle("code/data/raw_data/other/socc_noaa_daylight_hours.pkl")
# daylight_hours =daylight_hours.drop(columns=["Latitude", "Longitude"]).rename(columns={"daylight_hours":"daylight"})
# total_socc = pd.merge(total_socc, daylight_hours, how="left", on=["Date", "Site"])

# #Generate Effective temperature

# total_socc["TEFF"] = 0.36 * (3 * total_socc["TMAX"] - total_socc["TMIN"]) * (total_socc["daylight"] / (24 - total_socc["daylight"]))
# def a(hi):
#     return 6.75*(10**(-7))*hi**3 - 7.71*(10**(-5))*hi**2 + 0.01792*hi + 0.49239
# def pet(t, daylight_hours, heat_index):
#     if t < 0:
#         return 0
#     elif t <= 26:
#         return 16 * daylight_hours/360 * (10*t/heat_index)**a(heat_index)
#     else:
#         return daylight_hours/360 * (-415.85 + 32.24 * t - 0.43 * t**2)
# def build_pet(df):
#     df["PET"] = np.nan
#     for i in df.index:
#         df.loc[i, "PET"] = pet(t=df.loc[i,"TEFF"], daylight_hours=df.loc[i,"daylight"], heat_index=df.loc[i,"heat_index"])
#     return df

# total_socc = build_pet(total_socc)
# total_socc = total_socc.drop(columns=["year", "month", "TAVG_LB"])
# total_socc.to_pickle("code/data/interim_data/socc_filtered_fulldaterange_withindices.pkl")
#%%

#Create aggregated historical data
def mean_hist(df, datatype:str, days:int):
    for i in tqdm(df.index, desc=f"Generating {datatype}_MEAN{days}"):
        df.loc[i, f"{datatype}_MEAN{days}"] = df[(df["Site"] == df.loc[i,"Site"]) \
            & (df["Date"] < df.loc[i,"Date"]) \
                & (df["Date"] >= df.loc[i, "Date"] - timedelta(days=days))]\
                    .loc[:,datatype].mean()
    return df

try:
    socc_aggregate = pd.read_pickle("code/data/tmp/socc_filtered_fulldaterange_withindices.pkl")
except OSError:
    socc_aggregate = pd.read_pickle("code/data/interim_data/socc_filtered_fulldaterange_withindices.pkl")

datatypes=[col for col in socc_aggregate.columns if col not in ["Date", "Site", "year", "month", "heat_index", "Day_factor", "TAVG_LB", "daylight"] and "MEAN" not in col]
for datatype in tqdm(datatypes, desc=f"Total progress"):    
    for days in tqdm([3, 7, 15], desc=f"Generating {datatype}_MEAN"):
        if f"{datatype}_MEAN{days}" in socc_aggregate.columns:
            continue
        else:
            socc_aggregate = mean_hist(socc_aggregate, datatype=datatype, days=days)
            socc_aggregate.to_pickle("code/data/tmp/socc_filtered_fulldaterange_withindices.pkl")
            tqdm.write(f"{datatype}_MEAN{days} aggregated and saved!")
socc_aggregate.to_pickle("code/data/interim_data/socc_filtered_fulldaterange_aggregated.pkl")
#%%

#Filter by our sites date ranges established in exploring station metadata
socc_filtered_dates = pd.read_pickle("code/data/interim_data/socc_noaa_filtered_wfasmatched_imputed.pkl")
socc_filtered_dates = socc_filtered_dates.loc[:,["Date", "Site"]]
socc_final = pd.merge(socc_filtered_dates, socc_aggregate, how="left", on=["Date", "Site"])

#Add our lat, long, fuel, and speciesid data back and export
socc_clean = pd.read_pickle("code/data/clean_data/wfas/SOCC_cleaned.pkl")
socc_clean = socc_clean.loc[:,["Date", "Site", "Latitude", "Longitude", "Fuel", "Percent"]]
socc_final = pd.merge(socc_final, socc_clean, how="left", on=["Date", "Site"])

cols = list(socc_final.columns)
move = ["Percent", "Fuel", "Longitude", "Latitude"]
for col in move:
    cols.remove(col)
    cols.insert(2, col)
socc_final = socc_final.reindex(columns=cols)

socc_final.to_pickle("code/data/interim_data/socc_noaa_subset_aggregated.pkl")