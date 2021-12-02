from IPython.core.debugger import set_trace

# %%
import os
import pickle
import time
from typing import List, Dict, Tuple
import pathlib

import pandas as pd

import ee
from geextract import ts_extract
from datetime import datetime

ee.Authenticate()
ee.Initialize()
print("Google Earth Engine Authentication Successful!")

EXCEPTIONS = (KeyboardInterrupt, InterruptedError, ee.ee_exception.EEException)
STATS_PROJ = os.getenv("STATS_PROJ")
assert STATS_PROJ, "STATS_PROJ environment variable not set."
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


PARAMS = {
    "sensor": "LC8",
    "tiers": ["T1", "T2"],
    "start": min_date,
    "end": max_date,
    "radius": 10000,
}

# Extract a Landsat 7 time-series for a 500m radius circular buffer around
# a location in Yucatan
def main() -> bool:
    big_list = []

    try:
        print("Trying to find existing pkl files")
        data_path = pathlib.Path(
            f"{STATS_PROJ}/code/data/raw_data/lansat"
        ).resolve()
        assert data_path.exists()
        list_of_files = list(data_path.rglob(f"sensor{PARAMS['sensor']}*radius{PARAMS['radius']}*partial.pkl"))
        assert list_of_files # Check if there is any .pkl files.
        print("Found the following:", *list(map(lambda o: o.name, list_of_files)), sep="\n")

        most_recent_pickle_file = max(list_of_files, key=os.path.getctime)
        print(f"Loading {most_recent_pickle_file.name}")
        with open(most_recent_pickle_file, "rb") as f:
            big_list = pickle.load(f)
        print(
            f"Picking up from where we left off! {len(big_list)} out of {len(coords)} done."
        )
    except AssertionError:
        print("No existing files found")

    try:
        # 
        j = len(big_list)
        coords_to_iterate = coords[j:] if j else coords
        for (lat, lon) in coords_to_iterate:
            dict_list = ts_extract(lon=lon, lat=lat, **PARAMS)
            obj = {(lat, lon): dict_list}
            if obj not in big_list:
                big_list.append(obj)
                print(
                    f"Finished {(lat, lon)}, {len(big_list)} coordinates done; {len(coords) - len(big_list)} left to go!"
                )

        now = (
            datetime.now()
            .isoformat()
            .split("T")[0]
        )
        name = f"sensor{PARAMS['sensor']}_radius{PARAMS['radius']}_{now}_complete.pkl"
        print(f"Complete Finished! Saving the pickle file as: \n\t{name}")
        with open(
            f"{STATS_PROJ}/code/data/raw_data/lansat/{name}",
            "wb",
        ) as f:
            pickle.dump(big_list, f)
            return True

    except EXCEPTIONS as e:
        print(f"The following exceptption occured:\n {e}")
        print("saving your progress.")
        now = (
            datetime.now()
            .isoformat()
            .split("T")[0]
        )
        with open(
            f"{STATS_PROJ}/code/data/raw_data/lansat/sensor{PARAMS['sensor']}_radius{PARAMS['radius']}_{now}_partial.pkl",
            "wb",
        ) as f:
            pickle.dump(big_list, f)  # type: ignore
        return False


if __name__ == "__main__":
    bool = False
    while not bool:
        bool = main()
        time.sleep(10)
