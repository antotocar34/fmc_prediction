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


def main():
    data_path = Path(f"{STATS_PROJ}/code/data/raw_data/lansat_7_T1/").resolve()
    latest_pkl_file = max(data_path.rglob("*.pkl"), key=os.path.getctime)

    with open(latest_pkl_file, "rb") as f:
        big_list, _ = pickle.load(f)

    df = parse_big_list(big_list)

    data_output_path = Path(f"{STATS_PROJ}/code/data/processed_data/")
    assert data_output_path.exists()
    with open(data_output_path /  "LANSAT_7_ndvi_df.pkl",  'wb') as f:
        pickle.dump(df, f)

main()
