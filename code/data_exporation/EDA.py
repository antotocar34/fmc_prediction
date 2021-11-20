#%%
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import os, pickle
from datetime import timedelta
from tqdm import tqdm
import numpy as np
from time import time

os.chdir(f"{os.path.dirname(os.path.realpath(__file__))}/../..")

#%%
with open("code/data/interim_data/socc_noaa.pkl", "rb") as infile:
    socc = pickle.load(infile)
socc = socc.drop(["GACC", "State", "Group", "Latitude", "Longitude", "Zip"], axis=1)
# %%
#Missing many many observations for DAPR, MDPR, WT01, WT04, WT08 (medium) so drop for now
# socc = socc.drop(["DAPR", "MDPR", "WT01", "WT04", "WT08"], axis=1)

#Drop mismeasured observations
socc = socc[socc["Percent"] < 500]
# %%
# sns.pairplot(data=socc.loc[:,"Percent":"AWND"])
# %%
with open("code/data/interim_data/socc_noaa_PRCP.pkl", "rb") as infile:
    prcp  = pickle.load(infile)

# %%

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
    agg = {suffix: [] for suffix in suffixes}
    for date, site in tqdm(samples):
        for func, suffix in zip(funcs, suffixes):
            values = datatype_df[datatype_df["Site"] == site] \
                [datatype_df["Date"] < date] \
                [datatype_df["Date"] >= date - timedelta(days=days)]\
                .loc[:,datatype]
            agg[f"{datatype}_{suffix}"].append(func(values))
    return agg




#%%

funcs = [np.mean, np.var]
suffixes = ["MEAN15", "VAR15"]
datatypes=["PRCP", "TSUN", "TAVG", "TMAX", "TMIN"]

#First need to copy a socc_noaa file to make a new socc_noaa_agg file dropping mismeasured observations
#Second run this loop with all necessary datatypes

# for datatype in tqdm(datatypes):
#     start = time()
#     with open("code/data/interim_data/socc_noaa_agg.pkl", "rb") as infile:
#         socc = pickle.load(infile)
#     colnames = [f"{datatype}_{suffix}" for suffix in suffixes]
#     if colnames.all() in socc.columns:
#         continue
#     with open(f"code/data/interim_data/socc_noaa_{datatype}.pkl", "rb") as infile:
#         dt_df = pickle.load(infile)
#     agg = pd.DataFrame(agg_historical(socc, dt_df, datatype=datatype, days=15, funcs=funcs, suffixes=suffixes))
#     socc = pd.concat([socc, agg], axis=1)
#     with open("code/data/interim_data/socc_noaa_agg.pkl", "wb") as outfile:
#         pickle.dump(socc, outfile)
#     elapsed = round(time()-start, 2)
#     print(f"{datatype}'s historical aggregates added and saved in {elapsed} seconds!")



#%%