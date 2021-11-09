#%%
import requests
from collections import defaultdict

token = "JcvRdALGKywGfyxsGdulfWCXhJBhpqFO"
noaa_api = "https://www.ncdc.noaa.gov/cdo-web/api/v2/"
parameters = {
    "datasets": ["datatypeid", "locationid", "stationid", "startdate", "enddate", "sortfield", "sortorder", "limit", "offset"],
    "datacategories" : ["datasetid", "locationid", "stationid", "startdate", "enddate", "sortfield", "sortorder", "limit", "offset"],
    "datatypes" : ["datasetid", "datacategoryid", "locationid", "stationid", "startdate", "enddate", "sortfield", "sortorder", "limit", "offset"],
    "locationcategoriess": ["datasetid", "startdate", "enddate", "sortfield", "sortorder", "limit", "offset"],
    "locations": ["datasetid", "datacategoryid", "locationid", "startdate", "enddate", "sortfield", "sortorder", "limit", "offset"],
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
locs = get_noaa(noaa_api, get_endpoint("locations"))
# %%
