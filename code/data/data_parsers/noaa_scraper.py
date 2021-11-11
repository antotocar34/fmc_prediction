#%%
import requests, pickle, os
from tqdm import tqdm
import pandas as pd
from geopy.distance import distance as geodist
from functools import partial
from datetime import datetime, date, timedelta

# STATS_PROJ = os.getenv('STATS_PROJ')
# assert STATS_PROJ is not None, "Failed to load environment variable correctly"
# os.chdir(STATS_PROJ)

os.chdir(f"{os.path.dirname(os.path.realpath(__file__))}/../../..")

#NOAA API Info
token = "JcvRdALGKywGfyxsGdulfWCXhJBhpqFO"
noaa_api = "https://www.ncdc.noaa.gov/cdo-web/api/v2/"
parameters = {
    "datasets": ["datatypeid", "locationid", "stationid", "startdate", "enddate", "sortfield", "sortorder", "limit", "offset"],
    "datacategories" : ["datasetid", "locationid", "stationid", "startdate", "enddate", "sortfield", "sortorder", "limit", "offset"],
    "datatypes" : ["datasetid", "datacategoryid", "locationid", "stationid", "startdate", "enddate", "sortfield", "sortorder", "limit", "offset"],
    "locationcategories": ["datasetid", "startdate", "enddate", "sortfield", "sortorder", "limit", "offset"],
    "locations": ["datasetid", "datacategoryid", "locationcategoryid", "startdate", "enddate", "sortfield", "sortorder", "limit", "offset"],
    "stations" : ["datasetid", "datacategoryid", "locationid", "datatypeid", "startdate", "enddate", "extent", "sortfield", "sortorder", "limit", "offset"],
    "data" : ["datasetid", "locationid", "stationid", "datatypeid", "startdate", "enddate", "units", "sortfield", "sortorder", "limit", "offset", "includemetadata"]
}
# %%
#Parse and Scrape Functions

# def get_noaa(endpoint, results = True, url = noaa_api, token = token):
#     '''Returns the list of results from a noaa api request'''
#     headers = {"token" : token}
#     r = requests.get(url=url + endpoint, headers = headers)
#     if results == True:
#         return r.json()["results"]
#     else:
#         return r.json()

def get_noaa(data:str, url = noaa_api, token = token, results = True, override = False, parameters = parameters, **options):
    '''Sets an endpoint to be passed to noaa api.

    Arguments:

    data: "datasets", "locations", "locationcategories", or "stations".
    provide optional parameters in either list or string format. 
    dates must be in yyyy-mm-dd format. 
    see https://www.ncdc.noaa.gov/cdo-web/webservices/v2#gettingStarted for more info on endpoint options.'''
    if data not in parameters.keys() and override == False:
        print(f"Unsupported type given. Supported types are: {', '.join(list(parameters.keys()))}")
        return
    if any(option not in parameters[data] for option in options):
        print(f"Unsupported option given. Supported parameters for {data} are: {', '.join(parameters[data])}")
        return
    optional_params = []
    for key, option in options.items():
        if isinstance(option, list):
            for each in option:
                optional_params.append(f"{key}={each}")
        else:
            optional_params.append(f"{key}={option}")   
    endpoint = f"{data}?{'&'.join(optional_params)}"
    headers = {"token" : token}
    r = requests.get(url=url + endpoint, headers = headers)
    if results == True:
        return r.json()["results"]
    else:
        return r.json()

def get_stationid(site_coord, station_df):
    '''Given site_coord as a (lat, long) tuple and a station df outputted by NOAA API, 
    return a Station ID.'''
    distance = [geodist(site_coord, (station_df.loc[i, "latitude"], station_df.loc[i, "longitude"])).km for i in station_df.index]
    return station_df.loc[distance.index(min(distance)), "id"]

def station_dict(wfas_df, stateid, datasetid):
    '''Given a clean dataframe from WFAS with Lat, Long columns, and a stateid for the NOAA API's locationid (ST), 
    return a dictionary mapping site names from WFAS to closest station's ID'''
    stations = pd.DataFrame.from_records(get_noaa("stations", datasetid=datasetid, locationid=stateid, limit = 1000))
    grouped_sites = wfas_df.groupby("Site").mean()
    station_dict = {}
    for site in tqdm(grouped_sites.index):
        site_coord = (grouped_sites.loc[site, "Latitude"], grouped_sites.loc[site, "Longitude"])
        station_dict[site] = get_stationid(site_coord, stations)
    return station_dict
#%%
#Shows location data via state. California is FIPS:06, Arizona is FIPS:04, nevada is FIPS:32
get_noaa("locations", locationcategoryid="ST", limit = 1000)
#%%
#Load cleaned WFAS data, match to NOAA weather station IDs, save dictionary.
stateid = "FIPS:06"
with open("code/data/clean_data/wfas/SOCC_cleaned.pkl", "rb") as infile:
    socc = pickle.load(infile)

'''Next steps:
1) Function to get cleaned NOAA weather and/or rainfail datasets based on date and stationID
2) Apply this function to SOCC cleaned data to form a DF of weather data that can be matched to WFAS DF'''
# %%
#List available datatypes for our given date range using GHCND dataset. Might have to do the same for PRECIP_15 dataset
def get_available_types(noaa_dataset, maxdate, mindate, locationid):
    '''Get all available datatypes for given noaa dataset and date range.'''
    all_types = pd.DataFrame.from_records(get_noaa("datatypes", datasetid=noaa_dataset, locationid=locationid, limit=1000))
    all_types["mindate"] = pd.to_datetime(all_types["mindate"], infer_datetime_format=True)
    all_types["maxdate"] = pd.to_datetime(all_types["maxdate"], infer_datetime_format=True)
    all_types = all_types[all_types["mindate"] <= mindate][all_types["maxdate"] >= maxdate]
    return all_types

GHCND_types = get_available_types("GHCND", maxdate = max(socc["Date"]), mindate=min(socc["Date"]), locationid="FIPS:06")
GSOM_types = get_available_types("GSOM", maxdate = max(socc["Date"]) - timedelta(days=62), mindate=min(socc["Date"]), locationid="FIPS:06")

'''Data types of interest:
GHCND: AWND, MDPR, PRCP, SNOW, TAVG, TMAX, TMIN, WSFG, WDFG, WT01, WT04, WT08
GSOM: TAVG, TMAX, TMIN, TSUN, CLDD, DP01, DP10, DT00, DT32, DX32, DX70, DX90, , EVAP, 
MN01, MN02, MN03, MX01, MX02, MX03, PRCP'''

# %%
#So far this function retrieves the particular data given the paramaters by finding the nearest weather station that actually has the datatype.
#Does this by first geting a list of stations that hold that datatype in that date, then finds the nearest station to our coordinates, then requests data. 
#For some reason, some times this still throws an error and does not retrieve any data. Not sure why yet, Might be submitting incorrect datatype cause i am tired, or maybe
#NOAA has some incorrect entries, so might have to code something that raises the exception if it occurs then tries the next closeest station. 
def get_data(site_coord, start, end, datatype, dataset="GHCND"):
    stations = pd.DataFrame.from_records(get_noaa("stations", datasetid=dataset, startdate = start, enddate=end, datatypeid=datatype, limit = 1000))
    station_id = get_stationid(site_coord, stations)
    data = get_noaa("data", datasetid=dataset, datatypeid=datatype, startdate=start, enddate=end, stationid=station_id)
    return data
# %%
def query_datatype(index, datatype, dataset="GHCND", data = socc):
    coord = (data.loc[index, "Latitude"], data.loc[index, "Longitude"])
    date = str(data.loc[index,"Date"].date())
    return get_data(coord, date, date, datatype, dataset=dataset)
# %%
'''1) Func to remove stations from get_data and reiterate to nearest station when error is thrown, add max-iters'''