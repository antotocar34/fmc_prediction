#%%
import requests, pickle, os
from tqdm import tqdm
import pandas as pd
from geopy.distance import distance as geodist
from functools import partial
from datetime import datetime, date, timedelta
import time

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
    "stations" : ["datasetid", "datacategoryid", "locationcategoryid", "datatypeid", "startdate", "enddate", "extent", "sortfield", "sortorder", "limit", "offset"],
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
    time.sleep(0.5)
    if results == True:
        return r.json()["results"]
    else:
        return r.json()

def get_stationid(site_coord, station_df):
    '''Given site_coord as a (lat, long) tuple and a station df outputted by NOAA API, 
    return a Station ID.'''
    distance = [geodist(site_coord, (station_df.loc[i, "latitude"], station_df.loc[i, "longitude"])).km for i in station_df.index]
    return station_df.loc[distance.index(min(distance)), "id"]

# def station_dict(wfas_df, stateid, datasetid):
#     '''Given a clean dataframe from WFAS with Lat, Long columns, and a stateid for the NOAA API's locationid (ST), 
#     return a dictionary mapping site names from WFAS to closest station's ID'''
#     stations = pd.DataFrame.from_records(get_noaa("stations", datasetid=datasetid, locationid=stateid, limit = 1000))
#     grouped_sites = wfas_df.groupby("Site").mean()
#     station_dict = {}
#     for site in tqdm(grouped_sites.index):
#         site_coord = (grouped_sites.loc[site, "Latitude"], grouped_sites.loc[site, "Longitude"])
#         station_dict[site] = get_stationid(site_coord, stations)
#     return station_dict
#%%
#Shows location data via state. California is FIPS:06, Arizona is FIPS:04, nevada is FIPS:32
#get_noaa("locations", locationcategoryid="ST", limit = 1000)
#%%
#Load cleaned WFAS data, match to NOAA weather station IDs, save dictionary.

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
# GSOM_types = get_available_types("GSOM", maxdate = max(socc["Date"]) - timedelta(days=62), mindate=min(socc["Date"]), locationid="FIPS:06")

'''Data types of interest:
GHCND: AWND, DAPR, MDPR, PRCP, SNOW, TAVG, TMAX, TMIN, WSFG, WDFG, WT01, WT04, WT08
GSOM: TAVG, TMAX, TMIN, TSUN, CLDD, DP01, DP10, DT00, DT32, DX32, DX70, DX90, , EVAP, 
MN01, MN02, MN03, MX01, MX02, MX03, PRCP'''


# %%
stateids = ["FIPS:06", "FIPS:04", "FIPS:32"] #State ID's for California, Arizona, Nevada

def bin_dates(startdate, enddate):
    '''Bins dates into a list of date ranges no greater than 998 days different'''
    assert enddate >= startdate, "End date is earllier than start date."
    rng = (enddate-startdate).days
    dateranges = []
    for i in range(rng//364):
        start = str((startdate + timedelta(days=i*364)).date())
        stop = str((startdate + timedelta(days=(i+1)*364)).date())
        dateranges.append((start, stop))
    dateranges.append((str((startdate + timedelta(days=(rng//364) * 364)).date()), str(enddate.date())))
    return dateranges


def get_data(site, datatype, locations = stateids, dataset="GHCND", df = socc, max_iters = 10):
    '''Given a site and a datatype, gets the daily datatype reports from closest station in one year intervals. Iterates through to find a station 
    that does not throw an error.'''
    results = []
    data = df.groupby("Site").mean()
    coord = (data.loc[site, "Latitude"], data.loc[site, "Longitude"])
    maxdate = df.groupby("Site").max().loc[site, "Date"] + timedelta(days=1)
    mindate = df.groupby("Site").min().loc[site, "Date"] - timedelta(days=1)
    dateranges = bin_dates(mindate, maxdate)
    for daterange in tqdm(dateranges, desc=f"Getting data for {site}"):
        startdate, enddate = daterange
        stations = pd.DataFrame.from_records(get_noaa("stations", datasetid=dataset, startdate = startdate, enddate=enddate, datatypeid=datatype, limit = 1000))
        for i in range(max_iters):
            station_id = get_stationid(coord, stations)
            try:
                data = get_noaa("data", datasetid=dataset, datatypeid=datatype, startdate=startdate, enddate=enddate, units="metric", stationid=station_id, limit = 1000)
                results.extend(data)
                break
            except KeyError:
                if i != max_iters - 1:
                    print(f"No {datatype} data found at {station_id}; iteration {i + 1} for date range: {daterange}, trying next nearest station...")
                    stations = stations[stations["id"] != station_id]
                    stations.reset_index(inplace=True, drop=True)
                else: 
                    print(f"No {datatype} data found in {max_iters} closest stations.")
                    break
    return results

def simple_query(index, datatype, df = socc):
    '''Simple querying for testing purposes. Returns data with index and datatype of df.'''
    d = str(df.loc[index, "Date"].date())
    coord = (df.loc[index, "Latitude"], df.loc[index, "Longitude"])
    stations = pd.DataFrame.from_records(get_noaa("stations", datasetid="GHCND", startdate = d, enddate=d, datatypeid=datatype, limit = 1000))
    station_id = get_stationid(coord, stations)
    data = get_noaa("data", datasetid="GHCND", datatypeid=datatype, startdate=d, enddate=d, stationid=station_id)
    return data


# %%
def parse_noaa_query(noaa_query, site, datatype):
    '''Parses the results from NOAA query and returns a dataframe with columns Site, date, {datatype}
    and a list of stations used. '''
    df = pd.DataFrame.from_records(noaa_query)
    assert datatype in df["datatype"].unique(), "Wrong datatype for this NOAA query"
    df["Date"] = df["date"].apply(lambda x: datetime.strptime(x.split("T")[0], "%Y-%m-%d"))
    df[datatype] = df["value"]
    stations = list(df["station"].unique())
    df["Site"] = site
    df.drop(columns=["station", "datatype", "value", "attributes", "date"], axis =1, inplace=True)
    return df, stations

def get_datatype_sitesloop(datatype, data = socc, max_iters = 10):
    '''Given a datatype, gets the data for all sites and returns single concatenated dataframe. Also returns the meta data as a dictionary of dictionaries; site:datatype:stations'''
    result = pd.DataFrame()
    meta = {}
    for site in tqdm(data["Site"].unique(), desc=f"Getting data for {datatype}"):
        noaa_query = get_data(site, datatype, df = socc, max_iters = max_iters)
        df, stations = parse_noaa_query(noaa_query, site, datatype)
        result.append(df, ignore_index=True)
        meta[site] = {datatype: stations}
    return df, meta

def get_all_datatypes(datatypes, data = socc, max_iters = 10):
    '''Given a list of datatypes, iteratively gets all site data for each data type and merges to a copy of the original dataframe, saving to pickle after each datatype.'''
    metadata = {}
    result = data.copy()
    for datatype in tqdm(datatypes, desc=f"Total Progress for {datatypes}"):
        df, meta = get_datatype_sitesloop(datatype, data=data, max_iters=max_iters)
        result.merge(df, how="left", on=["Site", "Date"])
        for site, data_dict in meta.items():
            if site not in metadata.keys():
                metadata[site] = data_dict
            else: 
                metadata[site].update(data_dict)
        with open("code/data/interim_data/socc_noaa.pkl", "wb") as outfile:
            pickle.dump(result, outfile)
        with open("code/data/interim_data/socc_metadata.pkl", "wb") as outfile:
            pickle.dump(metadata, outfile)
        print(f"{datatype} saved.")

# %%
#Tests
start = time.time()
sites = socc["Site"].unique()
GHCND_types = ["AWND", "DAPR", "MDPR", "PRCP", "SNOW", "TAVG", "TMAX", "TMIN", "WSFG", "WDFG", "WT01", "WT04", "WT08"]
get_all_datatypes(GHCND_types[0:4])
print(f"This took {round(time.time() - start, 2)} seconds!")

#%%


