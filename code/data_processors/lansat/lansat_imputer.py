# %%
from pathlib import Path
import pickle

import pandas as pd
import numpy as np
from sklearn.impute import SimpleImputer
import matplotlib.pyplot as plt
# %%
STATS_PROJ = "/home/carneca/Documents/College/masters/semester1/stats/assignment/fmc_prediction"
# %%
data_loc = Path(f"{STATS_PROJ}/code/data/interim_data/sensorLE7_radius10000_df.pkl")
assert data_loc.exists()
with open(data_loc, 'rb') as f:
    df = pickle.load(f)
df = df[df.NDVI > 0]
# %%
df.isnull().mean()
# %%
df["coords"] = df.apply(lambda row: (row.latitude, row.longitude), axis=1)
# %%
plt.figure()
for coord in df.coords.unique()[0:1]:
    coord_df = df[df.coords == coord]
    plt.plot(coord_df.date, coord_df.NDVI)
# %%
X = df.drop(["date", "latitude", "longitude", "B6", "coords"], axis=1)
# %%
df_imputed = pd.DataFrame(SimpleImputer().fit_transform(X))
df_imputed.columns = X.columns
# %%
def impute(df):
    pass
# %%
df.NDVI = df.NDVI.interpolate(method="spline", order=10)
# %%
out_df = df[["date", "NDVI", "longitude", "latitude"]]

with open(f"{STATS_PROJ}/code/data/processed_data/remotesensing_imputed.pkl", "wb") as f:
    pickle.dump(out_df, f)
# %%
