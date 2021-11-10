#%%
import requests, pickle, os
from tqdm import tqdm
import pandas as pd
from geopy.distance import distance as geodist

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

def get_noaa(endpoint, results = True, url = noaa_api, token = token):
    '''Returns the list of results from a noaa api request'''
    headers = {"token" : token}
    r = requests.get(url=url + endpoint, headers = headers)
    if results == True:
        return r.json()["results"]
    else:
        return r.json()

def get_endpoint(data:str, override = False, parameters = parameters, **options):
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
    return f"{data}?{'&'.join(optional_params)}"

def get_stationid(site_coord, station_df):
    '''Given site_coord as a (lat, long) tuple and a station df outputted by NOAA API, 
    return a Station ID.'''
    distance = [geodist(site_coord, (station_df.loc[i, "latitude"], station_df.loc[i, "longitude"])).km for i in station_df.index]
    return station_df.loc[distance.index(min(distance)), "id"]

def station_dict(wfas_df, stateid, datasetid):
    '''Given a clean dataframe from WFAS with Lat, Long columns, and a stateid for the NOAA API's locationid (ST), 
    return a dictionary mapping site names from WFAS to closest station's ID'''
    stations = pd.DataFrame.from_records(get_noaa(get_endpoint("stations", datasetid=datasetid, locationid=stateid, limit = 1000)))
    grouped_sites = wfas_df.groupby("Site").mean()
    station_dict = {}
    for site in tqdm(grouped_sites.index):
        site_coord = (grouped_sites.loc[site, "Latitude"], grouped_sites.loc[site, "Longitude"])
        station_dict[site] = get_stationid(site_coord, stations)
    return station_dict
#%%
#Shows location data via state. California is FIPS:06
get_noaa(get_endpoint("locations", locationcategoryid="ST"))
#%%
#Show all weather stations in California with max limit. Different weatherstations for different datasets. GHCND : Daily summaries, PRECIP_15: 15 day precip obviously.
ca_stations = pd.DataFrame.from_records(get_noaa(get_endpoint("stations", datasetid="PRECIP_15", locationid="FIPS:06", limit = 1000)))

#%%
#Load cleaned WFAS data, match to NOAA weather station IDs, save dictionary.
stateid = "FIPS:06"
datasetid = ["GHCND", "PRECIP_15"]
with open("code/data/clean_data/wfas/SOCC_cleaned.pkl", "rb") as infile:
    socc = pickle.load(infile)
socc_dailysum_stations, socc_precip_stations = station_dict(socc, datasetid=datasetid[0], stateid=stateid), station_dict(socc, datasetid=datasetid[1], stateid=stateid)
with open("code/data/data_parsers/SOCC_dailysum_stations.pkl", "wb") as outfile:
    pickle.dump(socc_dailysum_stations, outfile)
with open("code/data/data_parsers/SOCC_precip15_stations.pkl", "wb") as outfile:
    pickle.dump(socc_precip_stations, outfile)

# %%
with open("code/data/data_parsers/SOCC_Stationid_dict.pkl", "rb") as infile:
    station_dict = pickle.load(infile)

stations = list(station_dict.values())
'''Next steps:
1) Function to get cleaned NOAA weather and/or rainfail datasets based on date and stationID
2) Apply this function to SOCC cleaned data to form a DF of weather data that can be matched to WFAS DF'''
# %%
all_types = get_noaa(get_endpoint("datatypes", locationid="FIPS:06", limit=1000))
all_types = pd.DataFrame.from_records(all_types)
all_types["mindate"] = pd.to_datetime(all_types["mindate"], infer_datetime_format=True)
all_types["maxdate"] = pd.to_datetime(all_types["maxdate"], infer_datetime_format=True)
# %%

all_types.to_datetime()