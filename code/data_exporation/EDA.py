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
with open("code/data/interim_data/socc_noaa_agg.pkl", "rb") as infile:
    socc = pickle.load(infile)
socc = socc.drop(["GACC", "State", "Group", "Latitude", "Longitude", "Zip"], axis=1)
# %%
#Missing many many observations for DAPR, MDPR, WT01, WT04, WT08 (medium) so drop for now
socc = socc.drop(["DAPR", "MDPR", "WT01", "WT04", "WT08"], axis=1)

#Drop mismeasured observations
socc = socc[socc["Percent"] < 500]
# %%
sns.pairplot(data=socc.loc[:,"Percent":"AWND"])
