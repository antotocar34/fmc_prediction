#Get ID numbers for try plant database. 

#%%
import pickle, os
import pandas as pd
from matplotlib import pyplot as plt

os.chdir(f"{os.path.dirname(os.path.realpath(__file__))}/../../../..")
#%%
\
with open("code/data/clean_data/try/SOCC_cleaned_tryid.pkl", "rb") as infile:
    socc_data = pickle.load(infile)
# %%

#Load traits table and drop some null observations
traits = pd.read_table("code/data/raw_data/try/plant_traits.txt", encoding="latin-1", sep="\t", usecols=list(range(4,24)))
traits = traits[traits["TraitID"].notnull()].set_index("ObsDataID")
traits = traits[traits["OrigValueStr"].notnull()]

#Split up some dimension tables
dataid = traits.loc[:,["DataID", "DataName", "OriglName"]]
dataid = dataid.groupby("DataID").max()
traitmeta = traits.loc[:,["OrigUnitStr", "TraitID", "OrigUncertaintyStr", "UncertaintyName", "UnitName"]]
traitmeta = traitmeta.groupby("TraitID").max()
#%%

#Subset the traits table for useful information
traits = traits.loc[:,["AccSpeciesID", "TraitName", "TraitID", "DataID", "OrigValueStr", "ValueKindName", "StdValue"]]

#Split up the table to traits that have a numerical value and traits that have string value
def try_float(x):
    try: 
        return float(x)
    except ValueError:
        return x
traits["OrigValueStr"] = traits["OrigValueStr"].apply(try_float)
num_traits = traits[traits["OrigValueStr"].apply(lambda x: isinstance(x, float))]
num_traits["OrigValueStr"] = num_traits["OrigValueStr"].astype("float64")
cat_traits = traits[traits["OrigValueStr"].apply(lambda x: isinstance(x, str))]

#%%

#Pivoted the tables to view traits per species values, and std
trait_mean = num_traits.groupby(["AccSpeciesID", "TraitID"]).agg({"OrigValueStr":"mean"}).reset_index()
trait_mean = pd.pivot(data=trait_mean, index="AccSpeciesID", columns="TraitID", values="OrigValueStr")
trait_std = num_traits.groupby(["AccSpeciesID", "TraitID"]).agg({"StdValue": "mean"}).reset_index()
trait_std = pd.pivot(data=trait_std, index="AccSpeciesID", columns="TraitID", values="StdValue")
trait_categorical = cat_traits.groupby(["AccSpeciesID", "TraitID"]).agg({"OrigValueStr":"max"}).reset_index()
trait_categorical = pd.pivot(data=trait_categorical, index="AccSpeciesID", columns="TraitID", values="OrigValueStr")

# %%
#Plot a matrix of traits that exist
traitids = traits["TraitID"].unique()
speciesids = traits["AccSpeciesID"].unique()
has_trait = {}
grouped_df = traits[["TraitID", "AccSpeciesID"]].groupby("TraitID").agg({"AccSpeciesID" : ["unique"]})
grouped_df.columns = ["_".join(a) for a in grouped_df.columns.to_flat_index()]
for traitid in traitids:
    has_trait[traitid] = []
    for species in speciesids:
        if species in grouped_df.loc[traitid, "AccSpeciesID_unique"]:
            has_trait[traitid].append(1)
        else:
            has_trait[traitid].append(0)
trait_indicator = pd.DataFrame(data = has_trait, index = speciesids)
trait_indicator = trait_indicator.reindex(sorted(trait_indicator.columns), axis=1).sort_index()

plt.imshow(trait_indicator, cmap="gray")
# %%
