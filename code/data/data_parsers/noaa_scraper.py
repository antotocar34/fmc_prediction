#%%
import requests, pickle, os
from tqdm import tqdm
import pandas as pd
from geopy.distance import distance as geodist
from functools import partial
from datetime import datetime, date, timedelta
import time

'''****README******* As long as we are scraping GHCND data this works to just hit run and it will continue where the last person left off for the list of 
datatypes. See the script at the bottom.

****IMPORTANT**** This counts on having pulled the last person's intermediate pkl file that saves progress and pushing your pkl file after done.
Also good to make sure other person is not doing it at the same time, but I am sure the API token will prevent that from happeningn anyways.'''

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
    time.sleep(0.25)
    if results == True:
        return r.json()["results"]
    else:
        return r.json()
#Sample usage: Shows location data via state. California is FIPS:06, Arizona is FIPS:04, nevada is FIPS:32
#get_noaa("locations", locationcategoryid="ST", limit = 1000)

def simple_query(index, datatype, df):
    '''Simple querying for testing purposes. Returns data with index and datatype of df.'''
    d = str(df.loc[index, "Date"].date())
    coord = (df.loc[index, "Latitude"], df.loc[index, "Longitude"])
    stations = pd.DataFrame.from_records(get_noaa("stations", datasetid="GHCND", startdate = d, enddate=d, datatypeid=datatype, limit = 1000))
    station_id = get_stationid(coord, stations)
    data = get_noaa("data", datasetid="GHCND", datatypeid=datatype, startdate=d, enddate=d, stationid=station_id)
    return data

def get_stationid(site_coord, station_df):
    '''Given site_coord as a (lat, long) tuple and a station df outputted by NOAA API, 
    return a Station ID.'''
    distance = [geodist(site_coord, (station_df.loc[i, "latitude"], station_df.loc[i, "longitude"])).km for i in station_df.index]
    return station_df.loc[distance.index(min(distance)), "id"]

def bin_dates(startdate, enddate):
    '''Bins dates into a list of date ranges no greater than 998 days different'''
    assert enddate >= startdate, "End date is earllier than start date."
    rng = (enddate-startdate).days
    dateranges = []
    for i in range(rng//364):
        start = str((startdate + timedelta(days=i*364)).date())
        stop = str((startdate + timedelta(days=(i+1)*364+1)).date())
        dateranges.append((start, stop))
    dateranges.append((str((startdate + timedelta(days=(rng//364) * 364)).date()), str(enddate.date())))
    return dateranges

def get_data(site, datatype, df, dataset="GHCND", max_iters = 10):
    '''Given a site and a datatype, gets the daily datatype reports from closest station in one year intervals. Iterates through to find a station 
    that does not throw an error.'''
    #Initiate parameters here for coordinate, and date ranges in one year ranges to match NOAA API requirements for daily data.
    results = []
    data = df.groupby("Site").mean()
    coord = (data.loc[site, "Latitude"], data.loc[site, "Longitude"])
    maxdate = df.groupby("Site").max().loc[site, "Date"] + timedelta(days=1)
    mindate = df.groupby("Site").min().loc[site, "Date"] - timedelta(days=1)
    dateranges = bin_dates(mindate, maxdate)

    for daterange in tqdm(dateranges, desc=f"Getting {datatype} for {site}"):
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

def get_datatype_sitesloop(datatype, data, result = pd.DataFrame(), meta = {}, max_iters = 10):
    '''Given a datatype, gets the data for all sites and returns single concatenated dataframe. Also returns the meta data as a dictionary of dictionaries; site:datatype:stations'''
    # Get the sites that were already done and omit those
    if not result.empty:  
        sites = [site for site in data["Site"].unique() if site not in result["Site"].unique()]
    else:
        sites = [site for site in data["Site"].unique()]

    #Loop through sites and getting data to append
    for site in tqdm(sites, desc=f"Getting data for {datatype}"): 
        noaa_query = get_data(site, datatype, df = data, max_iters = max_iters)
        df, stations = parse_noaa_query(noaa_query, site, datatype)
        result = result.append(df, ignore_index=True)
        result.drop_duplicates(inplace=True, ignore_index=True)
        meta[site] = {datatype: stations}

        #Save Progress here
        with open(f"code/data/interim_data/socc_noaa_{datatype}.pkl", "wb") as outfile: 
            pickle.dump(result, outfile)
        with open(f"code/data/interim_data/socc_metadata_{datatype}.pkl", "wb") as outfile:
            pickle.dump(meta, outfile)
        print(f"{datatype} data for {site} saved in intermediate DF.")
    return result, meta

def get_all_datatypes(datatypes, data, metadata = {}, max_iters = 10):
    '''Given a list of datatypes, iteratively gets all site data for each data type and merges to a copy of the original dataframe, 
    saving to pickle after each datatype.'''

    for datatype in tqdm(datatypes, desc=f"Total Progress for {datatypes}"):
        #Try loading saved data if it exists. If not, continue with blank slate. 
        try: 
            with open(f"code/data/interim_data/socc_noaa_{datatype}.pkl", "rb") as infile:
                saved_df = pickle.load(infile)
            with open(f"code/data/interim_data/socc_metadata_{datatype}.pkl", "rb") as infile:
                saved_meta = pickle.load(infile)
        except OSError:
            saved_df = pd.DataFrame()
            saved_meta = {}

        #Get data and merge
        result = data.copy()
        df, meta = get_datatype_sitesloop(datatype, result=saved_df, meta=saved_meta, data=data, max_iters=max_iters)
        result = result.merge(df, how="left", on=["Site", "Date"])
        
        #Append metadata and save, 
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
#List available datatypes for a given datarange for a given dataset.
def get_available_types(noaa_dataset, maxdate, mindate, locationid):
    '''Get all available datatypes for given noaa dataset and date range.'''
    all_types = pd.DataFrame.from_records(get_noaa("datatypes", datasetid=noaa_dataset, locationid=locationid, limit=1000))
    all_types["mindate"] = pd.to_datetime(all_types["mindate"], infer_datetime_format=True)
    all_types["maxdate"] = pd.to_datetime(all_types["maxdate"], infer_datetime_format=True)
    all_types = all_types[all_types["mindate"] <= mindate][all_types["maxdate"] >= maxdate]
    return all_types

#GHCND_types_df = get_available_types("GHCND", maxdate = max(socc["Date"]), mindate=min(socc["Date"]), locationid="FIPS:06")
#GSOM_types_df = get_available_types("GSOM", maxdate = max(socc["Date"]) - timedelta(days=62), mindate=min(socc["Date"]), locationid="FIPS:06")

# %%
#Run Scraper
start = time.time()

#Interested Datatypes
stateids = ["FIPS:06", "FIPS:04", "FIPS:32"] #State ID's for California, Arizona, Nevada
GHCND_types = ["AWND", "DAPR", "MDPR", "PRCP", "SNOW", "TAVG", "TMAX", "TMIN", "WSFG", "WDFG", "WT01", "WT04", "WT08"]
GSOM_types = ["TAVG", "TMAX", "TMIN", "TSUN", "CLDD", "DP01", "DT00", "DT32", "DX32", "DX70", "DX90", "EVAP", "MN01",
"MN02", "MN03", "MX01", "MX02", "MX03", "PRCP"]

#Open last saved file if it exists. If not start anew.
try:
    with open("code/data/interim_data/socc_noaa.pkl", "rb") as infile:
        saved_data = pickle.load(infile)
    with open("code/data/interim_data/socc_metadata.pkl", "rb") as infile:
        saved_metadata = pickle.load(infile)
    datatypes = [datatype for datatype in GHCND_types if datatype not in saved_data.columns()]
    assert not datatypes, "No more datatypes to scrape! Yay!"
    get_all_datatypes(datatypes=datatypes, data=saved_data, metadata=saved_metadata)
except OSError:
    with open("code/data/clean_data/wfas/SOCC_cleaned.pkl", "rb") as infile:
        socc = pickle.load(infile) 
        get_all_datatypes(datatypes=GHCND_types, data=socc)

print(f"This took {round(time.time() - start, 2)} seconds!")

#%%


