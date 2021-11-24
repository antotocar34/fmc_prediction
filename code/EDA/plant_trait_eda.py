#%%
import pandas as pd
import os
os.chdir(f"{os.path.dirname(os.path.realpath(__file__))}/../..")

#%%
plant_traits = pd.read_pickle("code/data/clean_data/try/plant_traits.pkl")
socc = pd.read_pickle("code/data/clean_data/wfas/SOCC_cleaned.pkl")
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
