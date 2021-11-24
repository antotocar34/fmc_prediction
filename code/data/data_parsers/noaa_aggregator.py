#%%
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import os, pickle
from datetime import timedelta, datetime
from tqdm import tqdm
import numpy as np
from time import time

os.chdir(f"{os.path.dirname(os.path.realpath(__file__))}/../../..")


days = [3, 7, 15]
suffixes = ["MEAN3", "MEAN5", "MEAN15"]
datatypes=["PRCP", "TAVG", "TMAX", "TMIN", "SN32", "SN33", "SX31", "SX32", "SX33", "AWND", "WDFG", "WSFG"]

#%%
#Load matched and fulldaterange data
total_matched= pd.read_pickle("code/data/interim_data/socc_noaa_filtered_wfasmatched_imputed.pkl")
total_socc = pd.read_pickle("code/data/interim_data/socc_noaa_filtered_fulldaterange_imputed.pkl")
#%%
def mon_hi(x):
    return (max(0,x)/5)**1.514

def get_hi(i, df, tavg = "tavg_m"):
    site = df.loc[i,"Site"]
    year = df.loc[i, "year"]
    month = df.loc[i, "month"]
    heat_indices = []
    forward = False
    while len(heat_indices) < 12:
        if forward == False:
            if month > 1:
                mavg = df[(df["Site"] == site) & (df["year"] == year) & (df["month"] == month - 1)][tavg].sum()
                month -= 1
            elif month == 1:
                mavg = df[(df["Site"] == site) & (df["year"] == year - 1) & (df["month"] == 12)][tavg].sum()
                month = 12
                year -= 1
            if mavg == 0.0:
                year = df.loc[i, "year"]
                month = df.loc[i, "month"]
                forward = True
            else:
                heat_indices.append(mon_hi(mavg))
        elif forward == True:
            if month < 12:
                mavg = df[(df["Site"] == site) & (df["year"] == year) & (df["month"] == month + 1)][tavg].sum()
                month += 1
            elif month == 12:
                mavg = df[(df["Site"] == site) & (df["year"] == year + 1) & (df["month"] == 1)][tavg].sum()
                month = 1
                year += 1
            if mavg == 0.0:
                times = 12 - len(heat_indices)
                avg_hi = np.mean(np.array(heat_indices))
                for _ in range(times):
                    heat_indices.append(avg_hi)
            else:
                heat_indices.append(mon_hi(mavg))
    return sum(heat_indices)

def hi_col(df):
    '''Adds heat index column to df. Counts on being sorted by site then date'''
    heat_index = []
    for i in df.index:
        heat_index.append(get_hi(i, df))
    df["heat_index"] = heat_index
    return df

total_socc["year"] = total_socc["Date"].apply(lambda x: x.timetuple().tm_year)
total_socc["month"] = total_socc["Date"].apply(lambda x: x.timetuple().tm_mon)
total_socc["TAVG"] = (total_socc["TMAX"] + total_socc["TMIN"])/2
tavg_m = total_socc.groupby(["Site", "year", "month"]).agg({"TAVG" :"mean"}).rename(columns={"TAVG":"tavg_m"})
heat_index = hi_col(tavg_m.reset_index())
total_socc = pd.merge(total_socc, heat_index.loc[:,["Site", "year", "month", "heat_index"]], on=["Site", "year", "month"])


#%%
#Add effectice PRCP
total_socc["PRCP_EFF"] = total_socc["PRCP"].apply(lambda x: 0.83 * x - 1.27 if x > 2.8 else 0)

#Compute potential evapo transpiration
day_length_factor = {1: -1.6, 2: -1.6, 3: -1.6, 4 : 0.9, 5 : 3.8, 6 : 5.8, 7 : 6.4,
 8 : 5.0, 9 : 2.4, 10 : 0.4, 11 : -1.6, 12 : -1.6}
total_socc["Day_factor"] = total_socc["month"].apply(lambda m: day_length_factor[m])
total_socc["TAVG_LB"] = total_socc["TAVG"].apply(lambda t: t if t >= -2.8 else -2.8)
total_socc["EVAP_POT"] = 0.36 * (total_socc["TAVG_LB"] + 2.8) + total_socc["Day_factor"]
total_socc["EVAP_POT"] = total_socc["EVAP_POT"].apply(lambda v: v if v >=0 else 0)

#Add Drought Code

def moisture_equiv(dc):
    return 800 * np.exp(-dc/400)

def compute_DC(prev_DC, prcp_eff, evap_pot):
    if prev_DC == 0 :
        prev_DC = 15
    if prcp_eff == 0:
        return prev_DC + 0.5 * evap_pot
    else:
        DC = 400 * np.log(800/(moisture_equiv(prev_DC) + 3.947 * prcp_eff))
        if DC > 0:
            return DC + 0.5 * evap_pot
        else:
            return 0.5 * evap_pot

def build_DC(df):
    '''Adds a Drought code column, counts on being sorted by Site then Date'''
    df["DC"] = 15
    for i in df.index:
        site = df.loc[i,"Site"]
        date = df.loc[i,"Date"]
        evap_pot = df.loc[i,"EVAP_POT"]
        prcp_eff = df.loc[i, "PRCP_EFF"]
        prev_dc = df[(df["Site"] == site) & (df["Date"] == date - timedelta(days=1))]["DC"].sum()
        df.loc[i, "DC"] = compute_DC(prev_dc, prcp_eff, evap_pot) 
    return df

total_socc = build_DC(total_socc)

#%%
def agg_historical(wfas_data, datatype_df, datatype:str, days:list, func, suffixes:list):
    '''Perform an aggregating function on days before wfas dates of concern for a given datatype
    Args:
        wfas: Dataframe from WFAS containing at least Site and Date information
        datatype_df: Dataframe containing values of given datatype values to aggregate
        datatype: Name of datatype corresponding to column name in datatype_df
        days: Number of previous days to aggregate over
        funcs: A list of functions that can act on PD.Series
        suffixes: A list of suffixes corresponding to funcs to append as colnames
    Returns:
        Dictionary of values with keys named by datatype_suffix and values are the resultant aggregated
        values over the historical days. '''

    samples = zip(wfas_data["Date"].tolist(), wfas_data["Site"].tolist())
    agg = {f"{datatype}_{suffix}": [] for suffix in suffixes}
    for date, site in tqdm(samples, desc=f"Aggregating {datatype}"):
        for day, suffix in zip(days, suffixes):
            values = datatype_df[(datatype_df["Site"] == site) & (datatype_df["Date"] < date) & (datatype_df["Date"] >= date - timedelta(days=day))]
            values = values.loc[:,datatype]
            if len(values) <= day/3:
                agg[f"{datatype}_{suffix}"].append(np.nan)
            else:
                agg[f"{datatype}_{suffix}"].append(func(values))
    return agg



#%%
#First need to copy a socc_noaa file to make a new socc_noaa_agg file dropping mismeasured observations
# #Second run this loop with all necessary datatypes
# all_dates = pd.read_pickle("code/data/interim_data/socc_fulldaterange_imputed.pkl")
# for datatype in tqdm(datatypes, desc=f"Total progress"):
#     start = time()
#     try:
#         socc_aggregate = pd.read_pickle("code/data/interim_data/socc_noaa_aggregate.pkl")
#     except OSError:
#         socc_aggregate = pd.read_pickle("code/data/interim_data/socc_noaa_imputed.pkl")
#     colnames = [f"{datatype}_{suffix}" for suffix in suffixes]
#     if all(col in socc_aggregate.columns for col in colnames):
#         continue
#     dt_df = 
#     agg = pd.DataFrame(agg_historical(wfas_data=socc, datatype_df=dt_df, datatype=datatype, days=[3, 5, 7, 15], func=np.sum, suffixes=suffixes))
#     socc = pd.concat([socc, agg], axis=1)
#     with open("code/data/interim_data/socc_noaa_agg.pkl", "wb") as outfile:
#         pickle.dump(socc, outfile)
#     tqdm.write(f"{datatype} aggregated and saved!")
#     elapsed = round(time()-start, 2)
#     print(f"{datatype}'s historical aggregates added and saved in {elapsed} seconds!")
