#%%
import pandas as pd
from datetime import datetime, timedelta, date
import os, pickle
from tqdm import tqdm
from dateutil import parser
import numpy as np
from astral import LocationInfo
from astral.sun import sun
os.chdir(f"{os.path.dirname(os.path.realpath(__file__))}/../..")
#%%
#FUNCTIONS
def local_impute(data, cols:list):
    '''Imputes data by taking a local mean of the previous 5 days.'''
    for col in cols:
        for i in tqdm(data[data[col].isna()].index, desc=f"Imputing for {col}"):
            data.loc[i,col] = np.nanmean(data.loc[i-6:i-1, col])
    return data

def get_noon_stat(data, stat, hour_col="hour"):
    '''Get the stat at noon in an individual column wiht all else as nan'''
    indices = list(data[data[hour_col].isin([11, 12,13])].index)
    for i in indices:
        data.loc[i, f"{stat}_12"] = data.loc[i, stat]
    return data

def get_monthly_stat(data, stat, year_col = "year", month_col="month"):
    '''Get the monthly average of a stat'''
    df_mon = data.groupby([year_col, month_col]).agg({stat : lambda x: np.nanmean(x)})\
        .reset_index().rename(columns={stat:f"{stat}_monthly"})
    data = pd.merge(data, df_mon, how="left", on=[year_col, month_col])
    return data

def monthly_heatindex(x):
    return (max(0,x)/5)**1.514

def get_heatindex(i, df, tavg):
    '''Get the heat index for a row as long as columns contain "year" and "month".
    Args:
        i: index value
        df: Dataframe
        tavg: Name of column with average temperature
    Returns:
        Float: heat index value.'''
    year = df.loc[i, "year"]
    month = df.loc[i, "month"]
    heat_indices = []
    forward = False
    while len(heat_indices) < 12:
        if forward == False:
            if month > 1:
                mavg = df[(df["year"] == year) & (df["month"] == month - 1)][tavg].sum()
                month -= 1
            elif month == 1:
                mavg = df[(df["year"] == year - 1) & (df["month"] == 12)][tavg].sum()
                month = 12
                year -= 1
            if mavg == 0.0:
                year = df.loc[i, "year"]
                month = df.loc[i, "month"]
                forward = True
            else:
                heat_indices.append(monthly_heatindex(mavg))
        elif forward == True:
            if month < 12:
                mavg = df[(df["year"] == year) & (df["month"] == month + 1)][tavg].sum()
                month += 1
            elif month == 12:
                mavg = df[(df["year"] == year + 1) & (df["month"] == 1)][tavg].sum()
                month = 1
                year += 1
            if mavg == 0.0:
                times = 12 - len(heat_indices)
                avg_hi = np.mean(np.array(heat_indices))
                for _ in range(times):
                    heat_indices.append(avg_hi)
            else:
                heat_indices.append(monthly_heatindex(mavg))
    return sum(heat_indices)

def get_evap_pot(df, t_12, month="month"):
    '''Compute potential evapotranspiration for Drought Code.
    Args:
        df: Dataframe.
        t_12: Column name of column containing temperature at noon
        month: column containing month. 
    Returns:
        Dataframe with evapotranspiration column added. '''
    day_length_factor = {1: -1.6, 2: -1.6, 3: -1.6, 4 : 0.9, 5 : 3.8, 6 : 5.8, 7 : 6.4,
    8 : 5.0, 9 : 2.4, 10 : 0.4, 11 : -1.6, 12 : -1.6}
    df["Day_factor"] = df[month].apply(lambda m: day_length_factor[m])
    df["TAVG_LB"] = df[t_12].apply(lambda t: t if t >= -2.8 else -2.8)
    df["evap_pot"] = 0.36 * (df["TAVG_LB"] + 2.8) + df["Day_factor"]
    df["evap_pot"] = df["evap_pot"].apply(lambda v: v if v >=0 else 0)
    df = df.drop(["TAVG_LB", "Day_factor"], axis=1)
    return df

def compute_daylight(lat, long, date):
    '''Gets the daylight hours for the day and position
    Args:
        lat: Float. Latitude.
        long: Float. Longitude.
        date: Datetime. Date.
    Returns:
        Daylight hours as float.'''
    l = LocationInfo(latitude=lat, longitude=long)
    s = sun(l.observer, date = date)
    daylight = s["sunset"] - s["sunrise"]
    return daylight.seconds/3600

def get_coord(station, station_meta, stid):
    '''Gets the coordinates of a station.
    Args:
        station: Station ID
        station_meta: Dataframe where Station ID, latitude, longitude are stored.
        stid: Name of column in station_meta where Station IDs are stored.
    Returns:
        Lat, Long'''
    df = station_meta.copy().set_index(stid)
    return df.loc[station, "latitude"], df.loc[station, "longitude"]

def get_daylight_hours(i, df, station, station_meta, stid="stid", date_col="date"):
    '''Get daylight hours for a row in dataframe containing "date"
    Args:
        i: Index value.
        df: Dataframe.
        station: String: Station ID
        station_meta: Dataframe where station ID, latitude, and longitude can be found.
        stid: Name of column in station_meta that holds Station IDs
        date_col: Name of date column in df.
    Returns:
        Daylight hours for the row.'''
    lat, long = get_coord(df.loc[i,station], station_meta, stid=stid)
    return compute_daylight(lat, long, df.loc[i, date_col])

def moisture_equiv(dc):
    return 800 * np.exp(-dc/400)

def compute_DC(prev_DC, prcp_eff, evap_pot):
    '''Compute Drought Code.
    Args:
        prev_DC: Drought Code value for previous day.
        prcp_eff: Effective precipitation of the day.
        evap_pot: Potential Evapotranspiration of the day.
    Returns:
        Float: Drought code value for the day'''
    if prev_DC == 0 :
        prev_DC = 15
    if prcp_eff == 0:
        return prev_DC + 0.5 * evap_pot
    else:
        DC = 400 * np.log(800/(moisture_equiv(prev_DC) + 3.947 * prcp_eff))
        if DC > 0:
            return DC + 0.5 * evap_pot
        else:
            return 0.5 * evap_pot

def compute_daylight(lat, long, date):
    '''Gets the daylight hours for the day and position
    Args:
        lat: Float. Latitude.
        long: Float. Longitude.
        date: Datetime. Date.
    Returns:
        Daylight hours as float.'''
    l = LocationInfo(latitude=lat, longitude=long)
    s = sun(l.observer, date = date)
    daylight = s["sunset"] - s["sunrise"]
    return daylight.seconds/3600

def get_coord(station, station_meta, stid):
    '''Gets the coordinates of a station.
    Args:
        station: Station ID
        station_meta: Dataframe where Station ID, latitude, longitude are stored.
        stid: Name of column in station_meta where Station IDs are stored.
    Returns:
        Lat, Long'''
    df = station_meta.copy().set_index(stid)
    return df.loc[station, "latitude"], df.loc[station, "longitude"]

def get_daylight_hours(i, df, station, station_meta, stid="stid", date_col="date"):
    '''Get daylight hours for a row in dataframe containing "date"
    Args:
        i: Index value.
        df: Dataframe.
        station: String: Station ID
        station_meta: Dataframe where station ID, latitude, and longitude can be found.
        stid: Name of column in station_meta that holds Station IDs
        date_col: Name of date column in df.
    Returns:
        Daylight hours for the row.'''
    meta = station_meta.copy().set_index(stid)
    lat, long = meta.loc[station, "latitude"], meta.loc[station, "longitude"]
    return compute_daylight(lat, long, df.loc[i, date_col])

def a(heat_index):
    '''Returns a value for PET calculation given a heat index'''
    return 6.75*(10**(-7))*heat_index**3 - 7.71*(10**(-5))*heat_index**2 + 0.01792*heat_index + 0.49239
def compute_pet(t_eff, daylight_hours, heat_index):
    '''Calculates Thornwaite's PET.
    Args:
        t_eff: Effective Temperature
        daylight_hours: Daylight hours of the day
        heat_index: Heat index value
    Returns: 
        Thornwaite PET as float '''
    if t_eff < 0:
        return 0
    elif t_eff <= 26:
        return 16 * daylight_hours/360 * (10*t_eff/heat_index)**a(heat_index)
    else:
        return daylight_hours/360 * (-415.85 + 32.24 * t_eff - 0.43 * t_eff**2)#Calculate Thornwaite Evapotranspiration

def compute_EMC(i, df, hum_col="rel_humid", tavg="temp_avg"):
    '''Compute the equilibrium moisture content.
    Args:
        i: index value
        df: Dataframe
        hum_col: Colname for humidity. Humidity is in decimal form. 
        tavg: Colname for average temperature
    Returns:
        EMC as float'''
    h = df.loc[i, hum_col]/100
    t = df.loc[i, tavg]
    if h < 0.1:
        return 0.03229 + 0.281073 * h - 0.000578 * h * t
    elif h < 0.5:
        return 2.22749 + 0.160107 * h - 0.01478 * t
    else:
        return 21.0606 + 0.005565 * h**2 - 0.00035 * h * t - 0.483199 * h


def compute_DMC(prev_DMC, precip, temp_12, humid_12, month):
    '''Compute DMC
    Args:
        prev_DMC: Value of DMC the day before. If nan then will be set to 6.
        precip: Average precip of the day
        temp_12: Temperature at noon
        humid_12: Humidity at noon as a float out of 100
        month: Integer value of month.
    Returns:
        DMC value as float'''
    L = {1 : 6.5, 2 : 7.5, 3 : 9, 4 : 12.8, 5 : 13.9, 6 : 13.9, 7 : 12.4, 8 : 10.9, 9 : 9.4, 10 : 8, 11 : 7, 12 : 6}
    K = 1.894 * (max(temp_12, -1.1) + 1.1) * (100 - humid_12) * L[month] * 10**(-6)
    if np.isnan(prev_DMC):
        prev_DMC = 6
    if precip <= 1.5:
        return prev_DMC + 100 * K
    elif precip > 1.5:
        p_eff = 0.92 * precip - 1.27
        if prev_DMC <= 33:
            b = 100/(0.5 + 0.3 * prev_DMC)
        elif prev_DMC <= 65:
            b = 14 - 1.3 * np.log(prev_DMC)
        else:
            b = 6.2 * np.log(prev_DMC) - 17.2
        moist = 20 + np.exp(5.6348-(prev_DMC/43.43)) + (1000 * p_eff)/(48.77 + b * p_eff)
        return max(0, 244.72 - 43.43 * np.log(moist-20)) + 100 * K
    else:
        return 6

def compute_BUI(DMC, DC):
    '''Computes Build Up Index returns a float.'''
    if DMC <= 0.4 * DC:
        return 0.8 * DMC * DC/(DMC + 0.4 * DC)
    else:
        return DMC - (1 - 0.8 * DC/(DMC + 0.4 * DC)) * (0.92 + (0.0114 * DMC)**1.7)

#%%
#PROCESS PIPELINE

def parse_synoptic(station, dirpath):

    df = pd.read_pickle(os.path.join(dirpath, f"{station}.pkl"))
    df = pd.DataFrame(df["STATION"][0]["OBSERVATIONS"])

    df = df.rename(columns={
        "solar_radiation_set_1" : "solar_rad",
        "precip_accum_one_hour_set_1" : "precip",
        "relative_humidity_set_1" : "rel_humid", 
        "wind_speed_set_1" : "wind_speed",
        "air_temp_set_1" : "temp"
    })

    df["date_time"] = df["date_time"].apply(lambda x: parser.isoparse(x))
    df["date"] = df["date_time"].dt.date
    df["hour"] = df["date_time"].dt.hour
    df["year"] = df["date_time"].dt.year
    df["month"] = df["date_time"].dt.month

    #Remove Outliers
    df["solar_rad"] = df["solar_rad"].apply(lambda x: x if (x >=0 and x < 1300) else np.nan)
    df["precip"] = df["precip"].apply(lambda x: x if (x >= 0 and x < 40) else np.nan)
    df["rel_humid"] = df["rel_humid"].apply(lambda x: x if (x>= 0 and x <= 100) else np.nan)
    df["wind_speed"] = df["wind_speed"].apply(lambda x: x if (x>=0 and x<=50) else np.nan)
    df["temp"] = df["temp"].apply(lambda x: x if (x>-50 and x<55) else np.nan)

    for stat in ["rel_humid", "temp"]:
        df = get_noon_stat(df, stat)

    df = df.groupby("date").agg({
        "year" : "max",
        "month" : "max",
        "solar_rad" : ["max", lambda x: np.nanmean(x)],
        "precip" : "sum",
        "rel_humid" : ["min", lambda x: np.nanmean(x)],
        "rel_humid_12" : lambda x: np.nanmean(x),
        "wind_speed" : ["max", "min", lambda x: np.nanmean(x)],
        "temp" : ["max", "min", lambda x: np.nanmean(x)],
        "temp_12" : lambda x: np.nanmean(x)
    }).reset_index()

    df = df.set_axis([
        "date", "year", "month", "solar_rad_max", "solar_rad_avg", "precip", "rel_humid_min", "rel_humid", "rel_humid_12", "wind_speed_max", 
        "wind_speed_min", "wind_speed_avg", "temp_max", "temp_min", "temp_avg", "temp_12"
    ], axis=1)

    df = get_monthly_stat(df, "temp_avg")
    df = local_impute(df, cols=[col for col in df.columns if col not in ["date", "year", "month"]])
    return df

def extract_features_synoptic(df, station, station_meta, tavg="temp_avg", t_12="temp_12", date="date"):
    df = df.sort_values(by=date)
    df["precip_effective"] = df["precip"].apply(lambda x: 0.83 * x - 1.27 if x > 2.8 else 0) #Generate Effective Precip for DC
    df = get_evap_pot(df, t_12=t_12) #Generate Evap Pot for DC
    df["DC"] = 15
    df["DMC"] = 6
    for i in tqdm(df.index, desc="Computing {station} stats 1/2"):
        df.loc[i, "heat_index"] = get_heatindex(i, df, tavg=tavg) #Compute Heat Index
        prev_dc = df[(df[date] == df.loc[i,date] - timedelta(days=1))]["DC"].sum() #Compute DC
        df.loc[i, "DC"] = compute_DC(prev_dc, prcp_eff=df.loc[i, "precip_effective"], evap_pot=df.loc[i,"evap_pot"])
        df.loc[i, "daylight"] = get_daylight_hours(i, df, station=station, station_meta=station_meta) #Get Daylight hours
    df["temp_effective"] = 0.36 * (3 * df["temp_max"] - df["temp_min"]) * (df["daylight"] / (24 - df["daylight"])) #Generate Effective Temp for PET
    for i in tqdm(df.index, desc="Computing {station} stats 2/2"): # Add PET
        df.loc[i, "pet"] = compute_pet(t_eff = df.loc[i,"temp_effective"], daylight_hours=df.loc[i,"daylight"], heat_index=df.loc[i,"heat_index"])
        df.loc[i, "emc"] = compute_EMC(i, df, hum_col="rel_humid", tavg=tavg)
        prev_DMC = df[df["date"] == df.loc[i,"date"] - timedelta(days=1)]["DMC"].sum() #Get Previous DMC and then compute current DMC
        df.loc[i, "DMC"] = compute_DMC(prev_DMC, df.loc[i, "precip"], temp_12=df.loc[i,"temp_12"], humid_12=df.loc[i,"rel_humid_12"], month=df.loc[i,"month"])
        df.loc[i, "BUI"] = compute_BUI(DMC=df.loc[i, "DMC"], DC=df.loc[i,"DC"]) #Compute BUI
    df = df.drop(columns=["year", "month", "temp_12", "rel_humid_12", "daylight", "heat_index"])
    return df

def mean_aggregate(df, datatype:str, days:int, date_col="date"):
    for i in tqdm(df.index, desc=f"Generating {datatype}_MEAN{days}"):
        df.loc[i, f"{datatype}_MEAN{days}"] = np.nanmean(df[(df[date_col] < df.loc[i,date_col]) \
            & (df[date_col] >= df.loc[i, date_col] - timedelta(days=days))]\
            .loc[:,datatype])
    return df

def process_synoptic_raw(station, dirpath, station_meta):
    try:
        data = pd.read_pickle(f"code/data/tmp/{station}_extracted_tmp.pkl")
    except OSError:
        data = parse_synoptic(station, dirpath)
        data = extract_features_synoptic(data, station=station, station_meta=station_meta)
        data.to_pickle(f"code/data/tmp/{station}_extracted_tmp.pkl")
    features = [feature for feature in data.columns if feature != "date"]
    for feature in tqdm(features, desc="Aggregating..."):
        for days in [3, 7, 15]:
            data = mean_aggregate(data, datatype=feature, days=days, date_col="date")
    return data
# %%
#MAIN

def process_files(dirpath):
    station_meta = pd.read_pickle(os.path.join(dirpath, "station_list2.pkl"))
    data_files = os.listdir(dirpath)
    data_files.remove("station_list2.pkl")
    data_files.remove("socc_synoptic_stations2.pkl")
    data_files.remove("backup")
    cleaned_stations = [file.strip("_clean.pkl") for file in os.listdir("code/data/clean_data/synoptic_weather")]
    stations = [file.strip(".pkl") for file in data_files if file not in cleaned_stations]
    for station in tqdm(stations, desc="Total Progress:", colour="blue"):
        DF = process_synoptic_raw(station, dirpath = dirpath, station_meta=station_meta)
        DF.to_pickle(f"code/data/clean_data/synoptic_weather/{station}_clean.pkl")
        tqdm.write(f"{station} data cleaned and saved!")

dirpath = "code/data/raw_data/synoptic/"

process_files(dirpath)

#%%
