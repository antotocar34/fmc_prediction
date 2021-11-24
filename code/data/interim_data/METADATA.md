METADATA INFO ON FILES

socc_metadata ~ metadata detailing what stations were used to retrieve which datatypes

socc_noaa ~ compiled datatype data merged with clean dataset from wfas

socc_fulldaterange_imputed ~ All of SOCC data spanning the entire min-max date range of every site and missing data imputed with local imputer

socc_noaa_filtered_fulldaterange_imputed ~ Subset of sites/dates that have good data, full min max date range for every site and missing data imputed.

socc_noaa_filtered_wfasmatched_imputed ~ Subset of sites/dates that have good data, with missing data imputed and then matched to target wfas sites/dates

socc_filtered_fulldaterange_withindices ~ Subset of sites/dates that have good data, with the min max date range of every site and drought indices, and extra features added. Imputed once, could have missing data for aggregated data at min date points. 

daylight_hours ~ SOCC clean data with a daylight hours column that was extracted with an api