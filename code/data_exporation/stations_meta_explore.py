#%%
import pandas as pd
from datetime import datetime, timedelta
import pickle, os
import matplotlib.pyplot as plt

os.chdir(f"{os.path.dirname(os.path.realpath(__file__))}/../..")


# %%
with open("code/data/raw_data/noaa/socc_metadata.pkl", "rb") as infile:
    metadata = pickle.load(infile)

metadata = pd.DataFrame(metadata)
metadata = metadata.drop(["DAPR", "MDPR", "WT01", "WT04", "WT08", "SNOW"])

def count_list(x):
    if isinstance(x, list):
        return(len(x))
    else:
        return 0
station_counts = metadata.copy()
for col in station_counts.columns:
    station_counts[col] = station_counts[col].apply(lambda x: count_list(x))
    if 0 in station_counts[col].tolist():
        station_counts = station_counts.drop(col, axis=1)
station_counts = station_counts.T
station_counts["sum"] = station_counts.apply(sum, axis=1)
station_counts = station_counts.sort_values(by='sum')
#%%

station_counts = station_counts[station_counts["sum"] < 19]

#%%

socc_imputed = pd.read_pickle("code/data/interim_data/socc_fulldaterange_imputed.pkl")
socc_imputed = socc_imputed.loc[:,["Site", "Date", "TAVG", "TMAX", "TMIN"]]
socc_imputed = socc_imputed.set_index("Date")
# %%
station_counts.index = [i.replace("/", " ") for i in station_counts.index]
socc_imputed.columns = [i.replace("/", " ") for i in socc_imputed.columns]
for col in station_counts.index:
    socc_imputed[socc_imputed["Site"]==col].plot(kind="line")
    plt.savefig(f"code/data_exporation/figs/relevant_stations/{col}.png")
    plt.clf()
# %%

good_sites = [""]