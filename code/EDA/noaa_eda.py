#%%
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
import os, pickle
from datetime import datetime, timedelta, date
from tqdm import tqdm
os.chdir(f"{os.path.dirname(os.path.realpath(__file__))}/../..")

#%%
socc_final = pd.read_pickle("code/data/processed_data/socc_noaa_subset_complete.pkl")
#%%

cols = [feature for feature in socc_final.columns if feature not in ["Date", "Site", "Latitude", "Longitude", "Fuel", "AccSpeciesID", "Percent"]]
sites = [site for site in socc_final["Fuel"].unique() if site not in os.listdir("code/EDA/figs/noaa/fuel")]
for site in tqdm(sites, desc="Total Progress"):
    dir = f"code/EDA/figs/noaa/fuel/{site}"
    os.mkdir(dir, exist_ok=True)
    for col in tqdm(cols, desc=f"Making figs for {site}"):
        filepath=f"code/EDA/figs/noaa/fuel/{site}/{site}_{col}.png"
        if os.path.isfile(filepath):
            continue
        else:
            fig=plt.figure()
            ax=fig.add_subplot()
            sns.scatterplot(data=socc_final, x=col, y="Percent", ax = ax)
            ax.set_title(f"{site} {col} vs Percent")
            fig.savefig(filepath, facecolor="white", transparent=False)
            plt.clf()
            plt.close(fig)
#%%