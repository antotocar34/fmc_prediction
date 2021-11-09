#%%
import os
import pandas as pd
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
import geopandas
from functools import partial
from datetime import datetime
os.chdir(os.path.dirname(os.path.realpath(__file__)))
os.chdir("../../..")

filelist = os.listdir("code/data/raw_data/wfas")
filelist.sort()
path = "code/data/raw_data"

#%%
def read_wfas_table(filename, path):
    file = os.path.join(path, filename)
    data = pd.read_table(file, sep="\t", date_parser = lambda date: datetime.strptime(date, "%Y-%m-%d"), parse_dates=[4], skipinitialspace=True, usecols=list(range(7)))
    return data
# # %%
# #Simple plot to look at observations made per year. 
socc = read_wfas_table(filelist[8], path)
# socc.groupby(socc["Date"].dt.year).count().plot(kind="bar")

# #%%
# #Get an idea of which fuels have good data
# def summarize(cols):
#     '''Output some basic stats on FMC grouped by cols'''
#     summary = socc.groupby(cols).Percent.agg(["max", "min", "mean", "median", "count"])
#     return summary.round(1).sort_values(by="count", ascending = False)

# summarize("Fuel")
# summarize(["Site", "Fuel"])
# #%%
# #Need a smart way to title these plots for data exploration
# socc.groupby(["Site", "Fuel"]).plot(x = "Date", y = "Percent", kind="line", subplots=True)

# %%
state = "California, USA"
geolocator = Nominatim(user_agent ="wfas")
geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)
# %%
def get_geocode(address, geocoder, location = None):
    '''Iteratively tries shorter versions of the address split on whitespace in the geocoder until a geocode is found.
    Optionally append info such as state or country in location.'''
    address_list = address.split(" ")
    code = None
    for i in range(len(address_list), 0, -1):
        if code is None:
            code = geocoder(f'{" ".join(address_list[:i])} {location}')
        else: 
            break
    if code is None:
        print(f"No geo location found for {address}")
        return None
    else: 
        return (code.latitude, code.longitude)

def add_coords(df, location = None, colname="Site"):
    '''Given a dataframe df, and optional location data. Returns a data frame with Coordinate locations appended.'''
    data = df.copy()
    coords = {site: get_geocode(site, geocoder=geocode, location = location) for site in list(data[colname].unique())}
    data["Coordinates"] = data[colname].map(coords)
    return data

add_coords(socc)


# %%
