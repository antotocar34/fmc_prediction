import os
import pickle
import json
import numpy as np

STATS_PROJ = os.getenv("STATS_PROJ")

# %%
data_path = f"{STATS_PROJ}/code/data/clean_data/wfas/SOCC_cleaned.pkl"
with open(data_path, "rb") as f:
    data = pickle.load(f)


# %%
data.Fuel = data.Fuel.apply(lambda str: str.lower())
plants = data.Fuel.unique()

with open('record1.json', 'r') as f:
    plant_dict = json.load(f)


if "scientificname" not in data.columns:
    data["scientificname"] = np.nan

for plant_name in plant_dict:
    data.loc[data.Fuel == plant_name, "scientificname"] = plant_dict[plant_name]
    print(f"Added the scientific name for {plant_name} to the data frame")


path = f"{STATS_PROJ}/code/data/clean_data/try/SOCC_cleaned_scientificnames.pkl"
with open(path, 'wb') as f:
    pickle.dump(data, f)
