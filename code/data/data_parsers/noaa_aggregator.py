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
suffixes = ["SUM3", "SUM7", "SUM15"]
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
    '''Adds heat index column to df'''
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
