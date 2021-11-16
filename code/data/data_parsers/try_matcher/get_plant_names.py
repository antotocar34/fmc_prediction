# %%
from typing import Optional, List, Tuple
import os
import pandas as pd
import pickle
import subprocess
import re
import json
import numpy as np
from pyinputplus import inputStr, inputMenu


def safe_int(s: str):
    try:
        n = int(s)
        return n
    except ValueError:
        return None


def print_options(result: dict) -> dict:
    attrs = [
        "rank",
        "scientificname",
        "commonname",
        "species",
        "genbankdivision",
    ]
    for i, uid in enumerate(result):
        print(
                f"{i}:\n", "\n".join([f"{attr}: {result[uid][attr]}" for attr in attrs])
        )
    return_dict = {i: result[uid] for i, uid in enumerate(result)}
    return return_dict

# %%
STATS_PROJ = os.getenv("STATS_PROJ")

# %%
data_path = f"{STATS_PROJ}/code/data/clean_data/wfas/SOCC_cleaned.pkl"
with open(data_path, "rb") as f:
    data = pickle.load(f)


# %%
data.Fuel = data.Fuel.apply(lambda str: str.lower())
plants = data.Fuel.unique()


acceptable = [
    "rank",
    "scientificname",
    "commonname",
    "genus",
    "species",
    "subsp",
    "genbankdivision",
]

# %%
class PlantName:
    """
    This class parses the plant name to be used by the commander class.
    """

    def __init__(self, name: str):
        self.name = name
        if ", " in name:
            split = name.split(", ")
            self.main_name = split[0]
            self.secondary_name = split[1]
        elif " " in name:
            split = name.split(" ")
            self.main_name = split[0]
            self.secondary_name = split[1]
        else:
            self.main_name = name
            self.secondary_name = ""


class Commander:
    """
    This class iteratively queries the database for the plant name
    """

    def __init__(self, plant_name_str: str):
        self.plant_name = PlantName(plant_name_str)
        self.iteration = 0

    def make_command(self, verbose: bool = True) -> Tuple[str, str]:
        if self.iteration == 0:
            if verbose:
                print(f"Trying full name: {self.plant_name.name}")
            query = f"{self.plant_name.name}[Name Tokens]"
        if self.iteration == 1:
            print(f"Trying main name: {self.plant_name.main_name}")
            query = f"{self.plant_name.main_name}[Name Tokens]"
        if self.iteration == 2:
            query = " AND, ".join(
                [f"{self.plant_name.main_name}[Name Tokens]"]
                + [
                    f"{name}[Name Tokens]"
                    for name in self.plant_name.secondary_name.split(" ")
                ]
            )
            print(f"Trying combination: {query}")
        fst_cmd = f"""esearch  -db taxonomy -query \"{query}\""""
        snd_cmd = """efetch -format docsum -mode json"""
        return fst_cmd, snd_cmd

    def get_count(self) -> int:
        fst_cmd, _ = self.make_command()

        initial_p = subprocess.Popen(
            fst_cmd, shell=True, stdout=subprocess.PIPE
        )
        text = initial_p.stdout.read().decode("ascii")
        assert text is not None
        count = int(
            re.search("<Count>(\d+)</Count>", text).group(1)
        )  # Number of results
        return count

    def get_dict(self) -> dict:
        """
        Returns a dict with uids as keys and
        attrs as values.
        """
        fst_cmd, snd_cmd = self.make_command(verbose=False)
        cmd = fst_cmd + " | " + snd_cmd
        process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)

        json_binary = process.stdout.read()
        dict = json.loads(json_binary.decode("ascii"))
        del dict["result"]["uids"]
        dict = dict["result"]
        dict = {k : d for k, d in dict.items() if
                d["genbankdivision"] == "Plants and Fungi"}
        return dict

    def run(self) -> Optional[str]:
        count = self.get_count()

        if count > 50:
            return None
        if count == 0:
            if self.iteration < 2:
                self.iteration += 1
                return self.run()
            print(
                f"Tried everything could not find a result for {self.plant_name.name}"
            )
            return None

        if count == 1:
            result = self.get_dict()
            # Get plant attributes
            result = list(result.values())
            assert len(result) == 1
            result = result[0]

            print(f"Found a result for {self.plant_name.name}")
            happy = inputMenu(["yes", "no"])
            if happy == "yes":
                print(json.dumps(result, indent=2))
                return result["scientificname"]
            else:
                return None

        if count > 1:
            result = self.get_dict()
            options = print_options(result)
            print(
                f"Found multiple options for {self.plant_name.name}\nPick the one you like most."
            )
            print("Or press X to try the other names for the plant.")
            print("Or press I to input the scientificname yourself.")
            dev_input = inputStr("> ")
            if dev_input == "X":
                self.iteration += 1
                return self.run()
            if dev_input == "I":
                scientificname = inputStr("(Science Name)> ")
                return scientificname
            if n := safe_int(dev_input):
                return options[n]["scientificname"]


class Tracker:
    def __init__(self, plants: List[str]):
        self.plants = plants

        try:
            with open('record.json', 'r') as f:
                self.logging = json.load(f)
        except FileNotFoundError:
            self.logging = {p: "TODO" for p in plants}

    def log(self, output: Optional[str], plant: str):
        self.logging[plant] = output
        with open("record.json", 'w') as f:
            json.dump(self.logging, f)

    def set(self):
        with open('tracker.pkl', 'wb') as f:
            pickle.dump(self, f)

    def run(self):
        for plant in [k for k, v in self.logging.items() if v == "TODO"]:
            output = Commander(plant).run()
            if output == None:
                output = inputStr("Please input a name yourself.\n(Science Name)> ")
                if output == "no":
                    output = None

            self.log(output, plant)

def main():
    try:
        t = Tracker(plants)
        t.run()
    finally:
       t.set()


if __name__ == "__main__":
    main()
    pass
