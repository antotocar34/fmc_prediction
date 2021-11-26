from IPython.core.debugger import set_trace

# %%
import os
import pickle
from typing import List, Dict, Tuple
import pathlib

import pandas as pd

import ee
from geextract import ts_extract
from datetime import datetime

ee.Authenticate()
ee.Initialize()

STATS_PROJ = os.getenv("STATS_PROJ")
# %%
def get_data() -> pd.DataFrame:
    with open(
        f"{STATS_PROJ}/code/data/clean_data/try/SOCC_cleaned_scientificnames.pkl",
        "rb",
    ) as f:
        data = pickle.load(f)
        return data


data = get_data()


max_date = str(data["Date"].apply(lambda s: pd.to_datetime(s)).max()).split(
    " "
)[0]
min_date = str(data["Date"].apply(lambda s: pd.to_datetime(s)).min()).split(
    " "
)[0]

max_date = datetime.strptime(max_date, "%Y-%m-%d")
min_date = datetime.strptime(min_date, "%Y-%m-%d")

coords: List[Tuple[int, int]] = list(
    {(lat, lon) for lat, lon in zip(data.Latitude, data.Longitude)}
)


# Extract a Landsat 7 time-series for a 500m radius circular buffer around
# a location in Yucatan
def main():
    big_list = []

    try:
        data_path = pathlib.Path(f"{STATS_PROJ}/code/data/raw_data/lansat_7_T1").resolve()
        list_of_files = list(data_path.rglob("*.pkl"))
        assert list_of_files
        most_recent_pickle_file = max(list_of_files, key=os.path.getctime)
        with open(most_recent_pickle_file, "rb") as f:
            big_list, j = pickle.load(f)
        print(
            f"Picking up from where we left off! {j} out of {len(coords)} done."
        )
    except AssertionError:
        j = 0

    try:
        coords_to_iterate = coords[j - 1 :] if j else coords
        for i, (lat, lon) in enumerate(coords_to_iterate):
            LE7_dict_list = ts_extract(
                lon=lon,
                lat=lat,
                sensor="LE7",
                start=min_date,
                end=max_date,
                radius=1000,
            )
            count = i + j
            obj = {(lat, lon): LE7_dict_list}
            if obj not in big_list:
                big_list.append(obj)
                print(
                    f"Just finished {(lat, lon)}, {count+1} coordinates done; {len(coords) - count+1} left to go!"
                )
    except:
        now = (
            datetime.now()
            .replace(microsecond=0, second=0, minute=0)
            .isoformat()
        )
        with open(f"{STATS_PROJ}/code/data/raw_data/lansat_7_T1/LE7_T1_coords__{now}.pkl", "wb") as f:
            if "count" in locals():
                assert "count" in locals()
                pickle.dump((big_list, count), f)  # type: ignore
            else:
                pickle.dump((big_list, 0), f)
    print("All done!")


if __name__ == "__main__":
    main()
