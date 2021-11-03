import os
import pandas as pd
from datetime import datetime

def dateparser(dates):
    '''Parses dates trying all formats.'''
    return datetime.strptime(dates, "%Y-%m-%d")
    # parsed_dates = [datetime.strptime(date_string, "%Y-%m-%d") for date_string in dates]
    # return parsed_dates

os.chdir("/home/clinton/Documents/statistical_inference/stat_proj/")
data = pd.read_table("SOCC_CA_LACounty_data.txt", sep="\t")