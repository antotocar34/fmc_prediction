#%%
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
import os, pickle
from datetime import datetime, timedelta, date
from tqdm import tqdm
from time import sleep
import matplotlib
os.chdir(f"{os.path.dirname(os.path.realpath(__file__))}/../..")

#%%
socc_final = pd.read_pickle("code/data/processed_data/socc_synoptic_complete.pkl")
#%%
matplotlib.use("TkAgg")
def plot_scatter_by(feat):
    cols = [feature for feature in socc_final.columns if feature not in ["Date", "Site", "Latitude", "Longitude", "Fuel", "AccSpeciesID", "Percent", "Group", "nearest_stid", "station_distance", "station_elevation"]]
    xs = [x for x in socc_final[feat].unique() if x not in os.listdir(f"code/EDA/figs/synoptic/{feat}")]
    for x in tqdm(xs, desc="Total Progress"):
        dir = f"code/EDA/figs/synoptic/{feat}/{x}"
        if not os.path.exists(dir):
            os.mkdir(dir)
        for col in tqdm(cols, desc=f"Making figs for {x}"):
            filepath=os.path.join(dir, f"{x}_{col}.png")
            if os.path.isfile(filepath):
                continue
            else:
                fig=plt.figure()
                ax=fig.add_subplot()
                sns.scatterplot(data=socc_final, x=col, y="Percent", ax = ax)
                ax.set_title(f"{x} {col} vs Percent")
                fig.savefig(filepath, facecolor="white", transparent=False)
                fig.clear()
                plt.close(fig)
plot_scatter_by("Fuel")
#%%