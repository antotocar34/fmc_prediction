#%%
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import os, pickle
from datetime import timedelta, datetime
from tqdm import tqdm
import numpy as np
from time import time

os.chdir(f"{os.path.dirname(os.path.realpath(__file__))}/../..")

#%%
socc = pd.read_pickle("code/data/interim_data/socc_noaa_agg.pkl")
ids = pd.read_pickle("code/data/clean_data/try/SOCC_cleaned_tryid.pkl")
ids = ids.groupby("Fuel").agg({"AccSpeciesID":"max"})
socc = socc.drop(["GACC", "State", "Group", "Latitude", "Longitude", "Zip"], axis=1)
socc = socc[socc["Fuel"].notna()]
socc["Fuel"] = socc["Fuel"].apply(lambda x: "Chamise" if x == "chamise" else x)
#~~~~~~~~~~~README: There are multiple accSpceiesID for single plant chamise and Chamise. 
#Can probably fix just by changing 'chamise' to 'Chamise' for the single site that this occurs.

species_ids = [ids.loc[fuel.lower(), "AccSpeciesID"] for fuel in socc["Fuel"]]
socc["AccSpeciesID"] = species_ids
# %%
#Missing many many observations for DAPR, MDPR, WT01, WT04, WT08 (medium) so drop for now
socc = socc.drop(["DAPR", "MDPR", "WT01", "WT04", "WT08", "SNOW"], axis=1)
# %%
#Add growth cycle variable given by spanish study
socc.insert(4, "growth_cycle", socc["Date"].apply(lambda x: np.cos((2*np.pi*x.timetuple().tm_yday/365) - 0.59)))
#Drop mismeasured observations
socc = socc[socc["Percent"] < 500]
#NEED TO CONSIDER CERTAIN 0's in our aggregated sums to be NANS dependent on the daily estimates.
#%%
plant_traits = pd.read_pickle("code/data/clean_data/try/plant_traits.pkl")
#%%
#subset plant_traits arbitrarily:

trait_subset = plant_traits.loc[:,plant_traits.count() > 5]
trait_subset = trait_subset[trait_subset.count(axis=1) > 30]
trait_subset = trait_subset.drop([37.0, 43.0, 154.0, 16.0, 599.0], axis=1)
# trait_subset = trait_subset.rename(columns={599.0:"moisture_level"})

# %%
# sns.pairplot(data=socc.loc[:,"Percent":"AWND"])
trait_desc = pd.read_pickle("code/data/clean_data/try/pant_traits_descriptions.pkl")
# %%
socc = pd.merge(socc, trait_subset, on="AccSpeciesID", how="inner")

#%%
#Let's make some baseline predictions

from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import PowerTransformer, PolynomialFeatures, OrdinalEncoder, MinMaxScaler
from sklearn.impute import KNNImputer
from sklearn.linear_model import Lasso, BayesianRidge, LinearRegression
from sklearn.model_selection import cross_val_score
from sklearn.decomposition import PCA
from sklearn.ensemble import RandomForestRegressor
import pymc3

Y = socc["Percent"]
X = socc.loc[:,"PRCP":].drop("AccSpeciesID", axis=1)
#%%
traits = list(trait_subset.columns)
cats = []
nums = [col for col in X.columns if col not in cats]
num_transformer = Pipeline(steps=[("pt", MinMaxScaler())])
cat_transformer = Pipeline(steps=[("oe", OrdinalEncoder())])

preprocessor = ColumnTransformer(transformers=[
    ("num", num_transformer, nums),
    ("cat", cat_transformer, cats)
])

ests = [Lasso(), BayesianRidge(), LinearRegression(), RandomForestRegressor()]
scores = []
for estimator in ests: 
    pipe = Pipeline(steps=[("pre", preprocessor), ("imp", KNNImputer()), ("est", estimator)])
    score = cross_val_score(estimator=pipe, X = X, y = Y, cv=3, verbose=3)
    scores.append(score)
    print(f"{estimator} had a score of {score}")
# %%
