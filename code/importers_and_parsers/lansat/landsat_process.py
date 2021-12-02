from IPython.core.debugger import set_trace

import os
from typing import Dict, Tuple, List
from pathlib import Path
import pandas as pd
import pickle
from datetime import datetime

STATS_PROJ = os.getenv("STATS_PROJ")

def add_dics(d1, d2):
    d1.update(d2)
    return d1


def parse_dics(dics, lat, lon):
    out_dic = {
        k: v for dic in dics for k, v in parse_dic(dic, lat, lon).items()
    }
    return out_dic


def parse_dic(dic, lat, lon):
    date_str: str = dic["id"].split("_")[-1]
    date = datetime.strptime(date_str, "%Y%m%d")
    coord_entry = {"latitude": lat, "longitude": lon}
    return {
        date: add_dics(
            {k: v for k, v in dic.items() if k != "id"}, coord_entry
        )
    }


def parse_big_list(
    big_list: List[Dict[Tuple[int, int], List[Dict]]]
    ) -> pd.DataFrame:
    out_dataframe = pd.DataFrame(columns=["B1", "B2", "B3", "B4", "B5", "B6", "B7", "latitude", "longitude"])
    for big_dict in big_list:
        lat, lon = list(big_dict.keys())[0]
        dataframe_dic = parse_dics(big_dict[(lat, lon)], lat, lon)
        df = pd.DataFrame(dataframe_dic).T
        out_dataframe = out_dataframe.append(df)

    return out_dataframe.reset_index().rename({"index": "date"}, axis='columns').sort_values("date")

def calculate_ndvi(df):
    df["NDVI"] = (df["B4"] - df["B3"]) / (df["B4"] + df["B3"])
    return df

def calculate_surface_temperature(df):
    pass
    return df

def calculate_variables(df):
    df = calculate_ndvi(df)
    df = calculate_surface_temperature(df)
    return df

def parse_name(string) -> Tuple[str, str]:
    """
    sensorLE7_radius10000_2021-11-30T10:00:00.pkl 
    ->
    (LE7, radius)
    """
    sensor = string.split("_")[0].split("sensor")[-1]
    radius = string.split("_")[1].split("radius")[-1]
    return (sensor, radius)

def main():
    data_path = Path(f"{STATS_PROJ}/code/data/raw_data/lansat/").resolve()
    assert data_path.exists()
    assert list(data_path.rglob("*.pkl")), "No pickle files found"
    latest_pkl_file = max(data_path.rglob("*LE7*complete.pkl"), key=os.path.getctime)
    print(f"Processing file {latest_pkl_file.name}")

    with open(latest_pkl_file, "rb") as f:
        big_list = pickle.load(f)

    df = parse_big_list(big_list)

    data_output_path = Path(f"{STATS_PROJ}/code/data/processed_data/")
    assert data_output_path.exists()
    sensor, radius = parse_name(latest_pkl_file.name)
    with open(data_output_path /  f"sensor{sensor}_radius{radius}_df.pkl",  'wb') as f:
        df = calculate_variables(df)
        pickle.dump(df, f)
        
main()
