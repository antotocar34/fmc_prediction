#%%
import requests
import pandas as pd
from re import search
from collections import defaultdict

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
def get_noaa(endpoint, results = True, url = noaa_api, token = token):
    '''Returns the list of results from a noaa api request'''
    headers = {"token" : token}
    r = requests.get(url=url + endpoint, headers = headers)
    if results == True:
        return r.json()["results"]
    else:
        return r.json()

# %%
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
# %%
noaa = {}
for endpoint in parameters.keys():
    renamed = {entry["name"]:entry for entry in get_noaa(noaa_api, endpoint)}
    noaa[endpoint] = renamed
#%%
#Shows location data via state. California is FIPS:06
get_noaa(get_endpoint("locations", locationcategoryid="ST"))
#%%
#Show all weather stations in California with max limit.
ca_stations = pd.DataFrame.from_records(get_noaa(get_endpoint("stations", locationid="FIPS:06", limit = 1000)))
# %%
def search_for(regex, data, col):
    return data[data[col].apply(lambda x: search(regex, x)).notnull()]

search_for("yosemite".upper(), ca_stations, "name")

# %%
