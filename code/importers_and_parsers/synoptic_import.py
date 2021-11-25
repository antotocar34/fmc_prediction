#%%
import requests, os, pickle
from tqdm import tqdm
import pandas as pd
from datetime import datetime, timedelta
from functools import partial
from dateutil import parser
from geopy.distance import distance as geodist
os.chdir(f"{os.path.dirname(os.path.realpath(__file__))}/../..")

URL_ROOT = "https://api.synopticdata.com/v2/"
TIMESERIES = "stations/timeseries"
METADATA = "stations/metadata"

TOKEN = "38938170bc084e6d84a168f1d579f16c"
API_KEY = "KywATwJ9eB2PxUGzCtZ8tn15e12xtSt1oo4KRDmJti"

pot_vars = ["air_temp", "dew_point_temperature", "relative_humidity", "wind_speed", "pressure", "solar_radiation",
"soil_temp", "precip_accum", "precip_accum_24_hour", "heat_index"]
vars = ["air_temp", "relative_humidity", "wind_speed", "solar_radiation",
"soil_temp", "precip_accum"]

default_params = {
    "token":TOKEN,
    "country":"us",
    "state":"ca",
    "gacc":"socc",
    "varsoperator":"and"
}

station_list_params= {
    "vars" : ",".join(vars),
}
#%%
#FUNCTIONS

def get_stationid(site_coord, station_df, station_id = "stid"):
    '''Given site_coord as a (lat, long) tuple and a station df outputted by NOAA API, 
    return a Station ID.
        Args:
            site_coord: Tuple containining a latitude and longtitude
            station_df: A dataframe containing a list of weather stations with lat and long information
            station_id: String. Default: "stid". Name of station_df's id column. 
        Returnus:
            StationID of the closest station'''

    distance = [geodist(site_coord, (station_df.loc[i, "latitude"], station_df.loc[i, "longitude"])).km for i in station_df.index]
    return station_df.loc[distance.index(min(distance)), station_id]

def get_stationdist(site_coord, station, station_df, station_id="stid"):
    '''Get distance between site coordinate and station.
    Args:
        site_coord: Tuple of site's (latitude, longitude).
        station: String. Station ID.
        station_df: Dataframe. Station_list with id's and "latitude", "longitude" columns.
        station_id: String. Name of column where station id is stored.
    Returns:
        Distance between stations.'''
    df = station_df.copy().set_index(station_id)
    station_coord = (df.loc[station, "latitude"], df.loc[station, "longitude"])
    return geodist(site_coord, station_coord).km

def get_stationdaterange(station, station_df, station_id="stid"):
    '''Get a tuple of the date range that the station's data is in.
    Args:
        station: String. Station id.
        station_df: Dataframe. List of stations with columns "startdate" and "enddate"
        station_id: String. Default: "stid". Colname where the station id's are stored
    Returns:
        Tuple: (startdate, enddate)'''
    df = station_df.copy().set_index(station_id)
    return (df.loc[station, "startdate"], df.loc[station, "enddate"])

def dict_query(url_end, params:dict, defaults=default_params, url_root=URL_ROOT):
    '''Get the json response from url query
    Args:
        url_end: String. Endpoint to be joined to url_root for get request
        url_root: String. Defualt URL_ROOT. Root of API url.
        params: Dict. Dictionary of parameter for API request.
        defaults: Dictionary of default parameters.
    Returns:
        JSON parsed request. '''
    params = {**defaults, **params}
    url = os.path.join(url_root, url_end)
    r = requests.get(url, params=params)
    return r.json()

def kwarg_query(url_end, defaults = default_params,url_root=URL_ROOT, **params):
    '''Get the json response from url query
    Args:
        url_end: String. Endpoint to be joined to url_root for get request
        url_root: String. Defualt URL_ROOT. Root of API url.
        params: Kwargs of parameter for API request.
        defaults: Dictionary of default parameters.
    Returns:
        JSON parsed request. '''
    params = {**defaults, **params}
    url = os.path.join(url_root, url_end)
    r = requests.get(url, params=params)
    return r.json()

#%%
#Load SOCC data and parse for relevant min max dates

socc = pd.read_pickle("code/data/clean_data/wfas/SOCC_cleaned.pkl")
socc = socc.groupby("Site").agg({"GACC" : "max", "Date": ["max", "min"], "Latitude" : "max", "Longitude" : "max", "Zip":lambda x: len(x), "Fuel" : ['unique']})\
    .set_axis(["GACC", "enddate", "startdate", "latitude", "longitude", "values", "fuels"], axis=1)\
    .sort_values(by="values", ascending=False)\
    .reset_index()
socc = socc[socc["values"] > 300]

#%%
#Load Station Data
# stations = dict_query(METADATA, params=station_list_params)
# station_list = pd.DataFrame(stations["STATION"])
# station_list = station_list[(station_list["STATUS"] == "ACTIVE") & (station_list["RESTRICTED"] == False)]
# station_list["startdate"] = station_list["PERIOD_OF_RECORD"].apply(lambda x: (parser.isoparse(x["start"])).date())
# station_list["enddate"] = station_list["PERIOD_OF_RECORD"].apply(lambda x: (parser.isoparse(x["end"])).date())
# station_list = station_list.drop(columns=["STATE", "PERIOD_OF_RECORD", "TIMEZONE", "STATUS", "RESTRICTED"])
# station_list = station_list.set_axis([col.lower() for col in station_list.columns], axis=1)
#station_list = station_list.reset_index(drop=True)
# station_list.to_pickle("code/data/tmp/station_list.pkl")
station_list = pd.read_pickle("code/data/tmp/station_list.pkl")
#%%
for i in socc.index:
    coord = (socc.loc[i,"latitude"], socc.loc[i,"longitude"])
    socc.loc[i,"nearest_stid"] = get_stationid(coord, station_list)
    socc.loc[i,"station_distance"] = get_stationdist(coord, socc.loc[i,"nearest_stid"], station_list)
    socc.loc[i, "station_start"], socc.loc[i,"station_end"] = get_stationdaterange(socc.loc[i, "nearest_stid"], station_list)
socc = socc.sort_values(by="station_distance")
# %%
def get_data(station, startdate, enddate, vars, defaults = default_params):
    params = {
        "vars": ",".join(vars),
        "stid": station,
        "start" : datetime.strftime(startdate, "%Y%m%d%H%M"),
        "end" : datetime.strftime(enddate, "%Y%m%d%H%M")
    }
    return dict_query(url_end=TIMESERIES, params=params, defaults=defaults)

socc_stations = socc[socc["station_distance"] <= 30].copy().groupby("nearest_stid").agg({"station_start" : "min", "station_end" : "max"})

#%%
for station in socc_stations.index:
    data = get_data(station, startdate=socc_stations.loc[station, "station_start"], enddate=socc_stations.loc[station, "station_end"], vars=vars)
    with open(f"code/data/raw_data/synoptic/{station}.pkl", "wb") as outfile:
        pickle.dump(data, outfile)
    print(f"{station} data saved!")
# %%
