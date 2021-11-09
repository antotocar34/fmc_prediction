#%%
import pandas as pd
import os
from re import search
os.chdir(os.path.dirname(os.path.realpath(__file__)))
os.chdir("../../..")

file = "code/data/raw_data/try_plant_traits.txt"
traits = pd.read_table(file, sep="\t", skipinitialspace=True, encoding="latin-1", skiprows=3, usecols=range(5))
# %%
def search_trait(regex: str):
    '''Returns rows of traits table with trait that containts the regex'''
    return traits[traits["Trait"].apply(lambda x: search(regex, x)).notnull()]

search_trait("Leaf area")
#%%

potential_ids = [490, 731, 42]
useful_ids = [3073, 3074, 3, 810, 3108, 3109, 3110, 3111, 3112, 3113, 3114, \
    3115, 3116, 3117, 3056, 3086, 125, 410, 491, 809, 416, 3001, 413, 3476, 3477, \
    418, 164, 3474, 3475, 753, 48, 16, 55, 47, 163, 144, 50, 14, 56, 3106, 3107, \
    3122, 3120, 3121, 3402, 984, 572, 43, 37, 51, 15, 58, 186, 185, 53, 40, 982, \
    154, 978, 46, 599]

potential_traits = traits[traits["TraitID"].isin(potential_ids)]
useful_traits = traits[traits["TraitID"].isin(useful_ids)]
# %%


