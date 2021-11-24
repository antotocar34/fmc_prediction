#%%
import pandas as pd
import os, pickle
from datetime import date, datetime, timedelta
import numpy as np
from tqdm import tqdm
from sklearn.impute import SimpleImputer, KNNImputer
import requests

os.chdir(f"{os.path.dirname(os.path.realpath(__file__))}/../..")

#%%
#Load and merge all needed data

prcp = pd.read_pickle("code/data/raw_data/noaa/socc_noaa_PRCP_final.pkl")
tmax = pd.read_pickle("code/data/raw_data/noaa/socc_noaa_TMAX_final.pkl")
tmin = pd.read_pickle("code/data/raw_data/noaa/socc_noaa_TMIN_final.pkl")
tavg = pd.read_pickle("code/data/raw_data/noaa/socc_noaa_TAVG_final.pkl")
tavg_monthly = pd.read_pickle("code/data/raw_data/noaa/socc_noaa_TAVG_GSOM.pkl")
tavg_monthly = tavg_monthly.rename(columns={"TAVG" : "TAVG_MON"})
tavg_monthly["year"] = tavg_monthly["Date"].apply(lambda x: x.timetuple().tm_year)
tavg_monthly["month"] = tavg_monthly["Date"].apply(lambda x: x.timetuple().tm_mon)
tavg_monthly = tavg_monthly.drop("Date", axis=1)

data = prcp.loc[:,["Date", "Site"]]
data["year"] = data["Date"].apply(lambda x: x.timetuple().tm_year)
data["month"] = data["Date"].apply(lambda x: x.timetuple().tm_mon)

for df in [prcp, tmax, tmin, tavg]:
    data = pd.merge(data, df, on=["Date", "Site"], how="left")
indices = data.loc[:,["Date", "Site"]]
vars = data.drop(["Date", "Site"], axis=1)


#%%
# imputer = KNNImputer(weights="distance")
# vars = imputer.fit_transform(vars)
# data = indices.join(vars)
# data = pd.merge(data, tavg_monthly, on=["Site", "month", "year"], how="left")

# data.to_pickle("code/data/tmp/imputed_droughtindices.pkl")
# print("Imputed and saved!")
# assert len(data) == len(prcp) == len(tavg), "Something went wrong and lost some rows."
# assert all(data.count()==len(data))

# %%
