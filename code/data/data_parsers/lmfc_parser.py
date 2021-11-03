#%%
import os
import pandas as pd
from datetime import datetime
os.chdir(os.path.dirname(os.path.realpath(__file__)))
os.chdir("../../..")

filelist = os.listdir("code/data/raw_data/wfas")
filelist.sort()

path = "code/data/raw_data"
filename = "SOCC_data.txt"

def read_wfas_table(filename, path):
    file = os.path.join(path, filename)
    data = pd.read_table(file, sep="\t", date_parser = lambda date: datetime.strptime(date, "%Y-%m-%d"), parse_dates=[4], skipinitialspace=True, usecols=list(range(7)))
    return data
# %%
#Simple plot to look at observations made per year. 
socc = read_wfas_table(filelist[7], path)
socc.groupby(socc["Date"].dt.year).count().plot(kind="bar")

#%%
#Get an idea of which fuels have good data
def summarize(cols):
    '''Output some basic stats on FMC grouped by cols'''
    summary = socc.groupby(cols).Percent.agg(["max", "min", "mean", "median", "count"])
    return summary.round(1).sort_values(by="count", ascending = False)

summarize("Fuel")
summarize(["Site", "Fuel"])
#%%
#Need a smart way to title these plots for data exploration
socc.groupby(["Site", "Fuel"]).plot(x = "Date", y = "Percent", kind="line", subplots=True)

# %%
