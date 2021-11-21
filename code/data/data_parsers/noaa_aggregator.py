#%%
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import os, pickle
from datetime import timedelta
from tqdm import tqdm
import numpy as np
from time import time

os.chdir(f"{os.path.dirname(os.path.realpath(__file__))}/../../..")


#%%
def agg_historical(wfas_data, datatype_df, datatype:str, days:int, funcs:list, suffixes:list):
    '''Perform an aggregating function on days before wfas dats of concern for a given datatype
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
        for func, suffix in zip(funcs, suffixes):
            values = datatype_df[(datatype_df["Site"] == site) & (datatype_df["Date"] < date) & (datatype_df["Date"] >= date - timedelta(days=days))]
            values = values.loc[:,datatype]
            agg[f"{datatype}_{suffix}"].append(func(values))
    return agg


#%%
# GHCND_types = ["SX33"]
# for datatype in GHCND_types:
#     with open(f"code/data/interim_data/socc_noaa_{datatype}.pkl", "rb") as infile:
#         orig = pickle.load(infile)
#     with open(f"code/data/interim_data/socc_noaa_{datatype}_extra.pkl", "rb") as infile:
#         extra = pickle.load(infile)
#     final = orig.append(extra)
#     with open(f"code/data/interim_data/socc_noaa_{datatype}_final.pkl", "wb") as outfile:
#         pickle.dump(final, outfile)

#%%
funcs = [np.mean, np.var, np.max, np.min]
suffixes = ["MEAN15", "VAR15", "MAX15", "MIN15"]
datatypes=["PRCP", "TAVG", "TMAX", "TMIN", "SN32", "SN33", "SX31", "SX32", "SX33"]

#First need to copy a socc_noaa file to make a new socc_noaa_agg file dropping mismeasured observations
#Second run this loop with all necessary datatypes

for datatype in tqdm(datatypes, desc=f"Total progress"):
    start = time()
    with open("code/data/interim_data/socc_noaa_agg.pkl", "rb") as infile:
        socc = pickle.load(infile)
    colnames = [f"{datatype}_{suffix}" for suffix in suffixes]
    if all(col in socc.columns for col in colnames):
        continue
    with open(f"code/data/raw_data/noaa/socc_noaa_{datatype}_final.pkl", "rb") as infile:
        dt_df = pickle.load(infile)
    agg = pd.DataFrame(agg_historical(wfas_data=socc, datatype_df=dt_df, datatype=datatype, days=15, funcs=funcs, suffixes=suffixes))
    socc = pd.concat([socc, agg], axis=1)
    with open("code/data/interim_data/socc_noaa_agg.pkl", "wb") as outfile:
        pickle.dump(socc, outfile)
    tqdm.write(f"{datatype} aggregated and saved!")
    elapsed = round(time()-start, 2)
    print(f"{datatype}'s historical aggregates added and saved in {elapsed} seconds!")

