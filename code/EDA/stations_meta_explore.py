#%%
import pandas as pd
from datetime import datetime, timedelta
import pickle, os
import matplotlib.pyplot as plt
import requests, time
from tqdm import tqdm


os.chdir(f"{os.path.dirname(os.path.realpath(__file__))}/../..")

# %%
good_sites = ['Angeles Forest Hwy', 'Barnes Mountain', 'Big Creek', 'Bridgeport', 'Cachuma', 'Converse', 'Gold Creek', 'Happy Canyon', 'Highway 168',
 'Lincoln Crest', 'Mammoth Airport', 'Midpines- New Growth', 'Mt. Emma', 'Oakhurst', 'Painte Cove', 'Pine Acres', 'Pozo', 'Priest Grade', 'Shaver Lake', 'Sisar Canyon,Upper Ojai Valley',
 'Spunky Canyon', 'Templeton', 'Tollhouse', ' Vallecito', 'Frazier Park']
med_sites = ['Banning', 'Barrett', 'Black Star CNF', 'Cottonwood', 'Crestview sagebrush old growth', 'Deluz-New Growth', 'East Grade', 'El Cariso CNF',
 'Fallbrook-New Growth', 'Fallbrook-Old Growth', 'Lady Bug', 'Laguna Beach', 'Mountain Empire',
 'Posta Mountain', 'Rainbow Valley-New Growth', 'Rainbow Valley-Old Growth', 'San Felipe', 'Suncrest', "Tehachapi new growth", 'Tehachapi old growth', 'Temescal CNF', 'Frazier Park new growth', 'Frazier Park old growth']
token = "AKpYgimLAJUNlIcGvznUXauwESRpjdSG"
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
def get_noaa(data:str, url = noaa_api, token = token, override = False, parameters = parameters, **options):
    '''Sets an endpoint to be passed to noaa api.

    Arguments:
        data: "datasets", "locations", "locationcategories", or "stations".
        provide optional parameters in either list or string format. 
        dates must be in yyyy-mm-dd format. 
        see https://www.ncdc.noaa.gov/cdo-web/webservices/v2#gettingStarted for more info on endpoint options.
        Override allows you to set data as something else such as "locations/ST"
    Returns:
        HTTPS response'''

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
    if r.status_code == 429:
        tqdm.write("Reached maximum requests for the day. Start again next day!")
        exit()
    time.sleep(0.25)
    return r

with open("code/data/raw_data/noaa/socc_metadata.pkl", "rb") as infile:
    metadata = pickle.load(infile)

metadata = pd.DataFrame(metadata)
metadata = metadata.drop(["DAPR", "MDPR", "WT01", "WT04", "WT08", "SNOW"])

def count_list(x):
    if isinstance(x, list):
        return(len(x))
    else:
        return 0
station_counts = metadata.copy()
for col in station_counts.columns:
    station_counts[col] = station_counts[col].apply(lambda x: count_list(x))
    if 0 in station_counts[col].tolist():
        station_counts = station_counts.drop(col, axis=1)
station_counts = station_counts.T
station_counts["sum"] = station_counts.apply(sum, axis=1)
station_counts = station_counts.sort_values(by='sum')
#%%

station_counts = station_counts[station_counts["sum"] < 19]

#%%

socc_imputed = pd.read_pickle("code/data/interim_data/socc_fulldaterange_imputed.pkl")
socc_imputed = socc_imputed.loc[:,["Site", "Date", "TAVG", "TMAX", "TMIN"]]
socc_imputed = socc_imputed.set_index("Date")
# %%
station_counts.index = [i.replace("/", " ") for i in station_counts.index]
socc_imputed.columns = [i.replace("/", " ") for i in socc_imputed.columns]
for col in station_counts.index:
    socc_imputed[socc_imputed["Site"]==col].plot(kind="line")
    plt.savefig(f"code/data_exporation/figs/relevant_stations/{col}.png")
    plt.clf()
# %%