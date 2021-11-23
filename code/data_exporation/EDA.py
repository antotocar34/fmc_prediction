#%%
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import os, pickle
from datetime import timedelta, datetime
from tqdm import tqdm
import numpy as np
from time import time
from sklearn.preprocessing import PolynomialFeatures

os.chdir(f"{os.path.dirname(os.path.realpath(__file__))}/../..")

#%%

#DATA PROCESSING

socc = pd.read_pickle("code/data/interim_data/socc_noaa_agg.pkl")
ids = pd.read_pickle("code/data/clean_data/try/SOCC_cleaned_tryid.pkl")
ids = ids.groupby("Fuel").agg({"AccSpeciesID":"max"})

#Further Cleaning steps
socc = socc.drop(["GACC", "State", "Group", "Latitude", "Longitude", "Zip"], axis=1)
socc = socc[socc["Fuel"].notna()] 
socc = socc[socc["Percent"] < 500] #Drop mismeasured target variables
socc["Fuel"] = socc["Fuel"].apply(lambda x: "Chamise" if x == "chamise" else x) #Fix chamise name
socc = socc.drop(["DAPR", "MDPR", "WT01", "WT04", "WT08", "SNOW"], axis=1) #These columns have too few obs
socc.insert(4, "D", socc["Date"].apply(lambda x: np.cos((2*np.pi*x.timetuple().tm_yday/365) - 0.59))) #Add growth cycle based on day
species_ids = [ids.loc[fuel.lower(), "AccSpeciesID"] for fuel in socc["Fuel"]]
socc.insert(2, "AccSpeciesID", species_ids)
sum5 = [col for col in socc.columns if "SUM5" in col]
socc = socc.drop(sum5, axis=1)

feature_interactions = ['PRCP', 'TAVG', 'TMAX', 'TMIN', 'WSFG', 'WDFG', 'AWND', 'SN32', 'SN33',
       'SX31', 'SX32', 'SX33', 'PRCP_SUM3', 'PRCP_SUM7', 'PRCP_SUM15',
       'TAVG_SUM3', 'TAVG_SUM7', 'TAVG_SUM15', 'TMAX_SUM3', 'TMAX_SUM7',
       'TMAX_SUM15', 'TMIN_SUM3', 'TMIN_SUM7', 'TMIN_SUM15', 'SN32_SUM3',
       'SN32_SUM7', 'SN32_SUM15', 'SN33_SUM3', 'SN33_SUM7', 'SN33_SUM15',
       'SX31_SUM3', 'SX31_SUM7', 'SX31_SUM15', 'SX32_SUM3', 'SX32_SUM7',
       'SX32_SUM15', 'SX33_SUM3', 'SX33_SUM7', 'SX33_SUM15', 'AWND_SUM3',
       'AWND_SUM7', 'AWND_SUM15', 'WDFG_SUM3', 'WDFG_SUM7', 'WDFG_SUM15',
       'WSFG_SUM3', 'WSFG_SUM7', 'WSFG_SUM15']
def gen_cycle_interactions(data, cyclename, cols):
    df = data.copy()
    for col in cols:
        df[f"{cyclename}_{col}"] = df[cyclename] * df[col]
    return df

socc_interacted = gen_cycle_interactions(socc, "D", feature_interactions)


#Save
# socc_interacted.to_csv("code/data/clean_data/noaa/socc_noaa_interacted.csv")
# socc_interacted.to_pickle("code/data/clean_data/noaa/socc_noaa_interacted.pkl")
# socc.to_csv("code/data/clean_data/noaa/socc_noaa_complete.csv")
# socc.to_pickle("code/data/clean_data/noaa/socc_noaa_complete.pkl")

#%%
# poly = PolynomialFeatures()
# X = socc.drop(["Site", "Date", "AccSpeciesID", "Fuel"], axis=1)
# interacted = poly.fit_transform(X)
# interacted = pd.DataFrame(interacted, columns=poly.get_feature_names_out())
# socc_interacted = pd.concat([socc[["Site", "Date", "AccSpeciesID", "Fuel"]], interacted], axis=0, irgnore_index=True)

#%%

#~~~~~~~~~~~README: There are multiple accSpceiesID for single plant chamise and Chamise.
# 
# #OTHER NOTE IS WHAT TO DO WITH MISSING VALUES IN TERMS OF AGGREGATED SUMS... MAYBE REWRITE THE FUNC TO USE MEAN WHEN MISSING? 
#Can probably fix just by changing 'chamise' to 'Chamise' for the single site that this occurs.


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
