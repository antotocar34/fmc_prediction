#Get ID numbers for try plant database. 

#%%
import pickle, os
import pandas as pd

os.chdir(f"{os.path.dirname(os.path.realpath(__file__))}/../../../..")

with open("code/data/clean_data/try/SOCC_cleaned_scientificnames.pkl", "rb") as infile:
    socc_data = pickle.load(infile)

try_id = pd.read_table("code/data/raw_data/try/TryAccSpecies.txt", encoding="latin-1", sep="\t")
# %%
plant_list = socc_data["scientificname"].unique()
plant_ids = try_id[try_id["AccSpeciesName"].isin(plant_list)]
# %%
print(", ".join([str(id) for id in plant_ids["AccSpeciesID"]]))
# %%
