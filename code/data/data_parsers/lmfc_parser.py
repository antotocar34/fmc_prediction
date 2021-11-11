#%%
import os
import pandas as pd
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
import pickle
from datetime import datetime

# STATS_PROJ = os.getenv('STATS_PROJ')
# assert STATS_PROJ is not None, "Failed to load environment variable correctly"
# os.chdir(STATS_PROJ)

os.chdir(f"{os.path.dirname(os.path.realpath(__file__))}/../../..")

def read_wfas_table(filename, path):
    file = os.path.join(path, filename)
    data = pd.read_table(
        file,
        sep="\t",
        date_parser=lambda date: datetime.strptime(date, "%Y-%m-%d"),
        parse_dates=[4],
        skipinitialspace=True,
        usecols=list(range(7)),
    )
    return data


def get_geocode(address, geocoder, location=None):
    """
    Iteratively tries shorter versions of the address split on whitespace in the geocoder until a geocode is found.
    Optionally append info such as state or country in location.
    """
    chars = ["-", "/", ",", ";", "."]
    for char in chars:
        address = address.replace(char, " ")
    address_list = address.split(" ")
    code = None
    for i in range(len(address_list), 0, -1):
        if code is None:
            code = geocoder(f'{" ".join(address_list[:i])} {location}')
        else:
            break
    if code is None:
        print(f"No geo location found for {address}")
    return code


def parse_sites(df, geocoder, location=None, colname="Site"):
    """Parses sites to latitudes and longitutes as dictionaries. Also raises a list of no_codes.
    Returns lats, longs, no_codes."""
    no_codes = []
    latitudes = {}
    longitudes = {}
    zipcodes = {}
    for site in df[colname].unique():
        code = get_geocode(site, geocoder=geocoder, location=location)
        if code is None:
            no_codes.append(site)
        else:
            latitudes[site] = code.latitude
            longitudes[site] = code.longitude
            zipcodes[site] = code[0].split(", ")[-2].split("-")[0]
    return latitudes, longitudes, zipcodes, no_codes


# %%
# Instantiate and load data from filelist
geolocator = Nominatim(user_agent="wfas")
geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)
path = "code/data/raw_data/wfas"
filelist = os.listdir(path)
filelist.sort()

state = "California, USA"
data = read_wfas_table(filelist[8], path)  # filelist[8] is SOCC data

#%%
# Get lats and longs, here. Manually inspect no_codes before mapping to dataframe
lats, longs, zips, no_codes = parse_sites(data, geocoder=geocode, location=state)
#%%

# Manual fixing of missing codes.
lats["Summit1"], lats["Summit2"] = lats["Summit"], lats["Summit"]
longs["Summit1"], longs["Summit2"] = longs["Summit"], longs["Summit"]
zips["Summit1"] = zips["Summit"]
zips["Summit2"] = zips["Summit"]
lats[no_codes[0]], longs[no_codes[0]] = 33.4371332, -117.3336908
lats[no_codes[1]], longs[no_codes[1]] = 33.4371332, -117.3336908
zips[no_codes[0]] = "92028"
zips[no_codes[1]] = "92028"
#%%

# Add Lat and Long columns to df
data["Latitude"] = data["Site"].map(lats)
data["Longitude"] = data["Site"].map(longs)
data["Zip"] = data["Site"].map(zips)
# %%

# Export clean data
with open("code/data/clean_data/wfas/SOCC_cleaned.pkl", "wb") as outfile:
    pickle.dump(data, outfile)


# ---------------BASIC DATA EXPLORATION BELOW---------------

# # %%

# #Simple plot to look at observations made per year.

# data.groupby(data["Date"].dt.year).count().plot(kind="bar")

# #%%
# #Get an idea of which fuels have good data
# def summarize(cols):
#     '''Output some basic stats on FMC grouped by cols'''
#     summary = data.groupby(cols).Percent.agg(["max", "min", "mean", "median", "count"])
#     return summary.round(1).sort_values(by="count", ascending = False)

# summarize("Fuel")
# summarize(["Site", "Fuel"])
# #%%
# #Need a smart way to title these plots for data exploration
# data.groupby(["Site", "Fuel"]).plot(x = "Date", y = "Percent", kind="line", subplots=True)
