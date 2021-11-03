#%%
import os
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

load_dotenv('../../.env')

os.chdir(os.getenv("PATH"))
def dateparser(dates):
    return datetime.strptime(dates, "%Y-%m-%d")

path = "code/data"
filename = "AICC_data.txt"
file = os.path.join(path, filename)
data = pd.read_table(file, sep="\t", date_parser = dateparser, parse_dates=[4], skipinitialspace=True, usecols=list(range(7)))
