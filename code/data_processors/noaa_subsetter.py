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
#Load SOCC data and create full date range data for each site

socc = pd.read_pickle("/home/clinton/Documents/statistical_inference/stat_proj/fmc_prediction/code/data/clean_data/wfas/SOCC_cleaned.pkl")
dateranges = socc.groupby("Site").agg({"Date":["max", "min"]})
all_dates = pd.DataFrame(columns=["Date", "Site"])
for site in dateranges.index:    
    site_df = pd.DataFrame({"Date" : pd.date_range(dateranges.loc[site, ("Date", "min")] - timedelta(days=15), dateranges.loc[site, ("Date", "max")]), "Site" : site})
    all_dates = all_dates.append(site_df, ignore_index=True)

datatypes=["PRCP", "TAVG", "TMAX", "TMIN", "SN32", "SN33", "SX31", "SX32", "SX33", "AWND", "WDFG", "WSFG"]
for datatype in datatypes:
    datatype_df = pd.read_pickle(f"code/data/raw_data/noaa/socc_noaa_{datatype}_final.pkl")
    all_dates = pd.merge(all_dates, datatype_df, how="left", on=["Date", "Site"])
#%%
#Impute all data
def local_impute(data, cols:list):
    for col in cols:
        for i in tqdm(data[data[col].isna()].index, desc=f"Imputing for {col}"):
            data.loc[i,col] = data.loc[i-6:i-1, col].mean()
    return data
all_dates = local_impute(all_dates, cols=datatypes)
all_dates.to_pickle("code/data/interim_data/socc_fulldaterange.pkl")
socc_imputed = pd.merge(socc, all_dates, how="left", on=["Date", "Site"])
socc_imputed.to_pickle("code/data/interim_data/socc_fulldaterange_imputed.pkl")

#%%
#Based on exploration of metadata and how the data was gathered from stations, we settle on only these sites
total_socc = pd.read_pickle("code/data/interim_data/socc_fulldaterange_imputed.pkl")
good_sites = ['Angeles Forest Hwy', 'Barnes Mountain', 'Big Creek', 'Bridgeport', 'Cachuma', 'Converse', 'Gold Creek', 'Happy Canyon', 'Highway 168',
 'Lincoln Crest', 'Mammoth Airport', 'Midpines- New Growth', 'Mt. Emma', 'Oakhurst', 'Painte Cove', 'Pine Acres', 'Pozo', 'Priest Grade', 'Shaver Lake', 'Sisar Canyon,Upper Ojai Valley',
 'Spunky Canyon', 'Templeton', 'Tollhouse', ' Vallecito', 'Frazier Park']
med_sites = ['Banning', 'Barrett', 'Black Star CNF', 'Cottonwood', 'Crestview sagebrush old growth', 'Deluz-New Growth', 'East Grade', 'El Cariso CNF',
 'Fallbrook-New Growth', 'Fallbrook-Old Growth', 'Lady Bug', 'Laguna Beach', 'Mountain Empire',
 'Posta Mountain', 'Rainbow Valley-New Growth', 'Rainbow Valley-Old Growth', 'San Felipe', 'Suncrest', "Tehachapi new growth", 'Tehachapi old growth', 'Temescal CNF', 'Frazier Park new growth', 'Frazier Park old growth']
good_socc = total_socc[total_socc["Site"].isin(good_sites)]
med_socc = total_socc[total_socc["Site"].isin(med_sites)]
#%%
#Medium sites need to be adjusted to only contain certain dateranges
#Drop if
less_than = [("Banning", "2020-09-04"),  ("Crestview sagebrush old growth", "2013-12-31"), ("East Grade", "2013-12-31"), ("Laguna Beach", "2019-11-08"), ("Frazier Park new growth", "2020-01-06"), ("Frazier Park old growth", "2020-01-06"), ("Laguna Beach", "2019-11-08"),
("Tehachapi new growth", "2020-01-07"), ("Tehachapi old growth", "2020-01-07")]
greater_than = [("Cottonwood", "2018-03-02"), ("Frazier Park new growth", "2020-01-06"), ("Frazier Park old growth", "2020-01-06"), ("Lady Bug", "2018-05-28")]
between = ["Barrett", "Black Star CNF", "Deluz-New Growth", "El Cariso CNF", "Fallbrook-New Growth", "Fallbrook-Old Growth", "Mountain Empire", "Posta Mountain", "Rainbow Valley-New Growth",
"Rainbow Valley-Old Growth", "San Felipe", "suncrest", "Temescal CNF"] #Missing data between 2013-01-01 and 2014-01-01

#Drop rows as determined by above
drop_rows = []
for cond in less_than:
    site, date = cond
    date = datetime.fromisoformat(date)
    m1, m2 = med_socc["Site"] == site, med_socc["Date"] <= date
    m = m1 * m2
    drop_rows += list(m[m].index)
for cond in greater_than:
    site, date = cond
    date = datetime.fromisoformat(date)
    m1, m2 = med_socc["Site"] == site, med_socc["Date"] >= date
    m = m1 *m2
    drop_rows += list(m[m].index)
for site in between:
    m1, m2, m3 = med_socc["Site"] == site, med_socc["Date"] > datetime(2013,1,1),med_socc["Date"] < datetime(2014,1,1)
    m = m1 * m2 *m3
    drop_rows += list(m[m].index)

med_socc = med_socc.drop(index=drop_rows)
# %%
#Merge back to WFAS data here and save
socc = pd.read_pickle("code/data/clean_data/wfas/SOCC_cleaned.pkl")

med_matched = pd.merge(socc, med_socc, on=["Date", "Site"], how="inner")
good_matched = pd.merge(socc, good_socc, on=["Date", "Site"], how="inner")
total_matched = good_matched.append(med_matched, ignore_index=True)
total_socc = good_socc.append(med_socc, ignore_index=True)

total_matched.to_pickle("code/data/interim_data/socc_noaa_filtered_wfasmatched_imputed.pkl")
total_socc.to_pickle("code/data/interim_data/socc_noaa_filtered_fulldaterange_imputed.pkl")
