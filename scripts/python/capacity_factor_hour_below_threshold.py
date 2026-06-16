import sys, os
import xarray as xr
import numpy as np
from pathlib import Path

# -------------------------------------------------------
# Usage: qsub capacity_factor_hour_below_threshold_calc.sh
# Input: one column (year).
# For trial, change the year to a number, then do python capacity_factor_hour_below_threshold.py
# -------------------------------------------------------

# This script calculates the number of capacity factors lower than a certain threshold (given in sys.argv[2]).

# Get the year from the command-line argument
year = sys.argv[1]
cf_threshold = float(sys.argv[2])/100.
# year = 2000

# Define paths to raw solar and wind capacity factor data
folder_solar = Path("/home/563/fm6730/localrepo/GC26-combined-solar-wind/data/raw/solar_cf/")
folder_wind  = Path("/home/563/fm6730/localrepo/GC26-combined-solar-wind/data/raw/wind_cf/")
folder_out   = Path("/home/563/fm6730/localrepo/GC26-combined-solar-wind/data/processed/hour_capacity_factor_lower_than")

# Construct file paths for the given year
file_solar = f'{folder_solar}/solar_capacity_factor_van_der_Wiel_era5_hourly_{year}_Aus.nc'
file_wind  = f'{folder_wind}/wind_capacity_factor_van_der_Wiel_era5_hourly_{year}_Aus.nc'

# Load solar and wind datasets
ds_solar = xr.open_dataset(file_solar)
ds_wind  = xr.open_dataset(file_wind)

# Extract capacity factor variables
da_solar = ds_solar['capacity_factor']
da_wind  = ds_wind['capacity_factor']

# Flag hours where capacity factor exceeds 0.1 (1 = active, 0 = lull)
da_solar_sel = xr.where(da_solar > cf_threshold, 1, 0)
da_wind_sel  = xr.where(da_wind  > cf_threshold, 1, 0)

# Sum the flags: 0 means both solar and wind are in lull simultaneously
da_combined = da_solar_sel + da_wind_sel

# Identify combined lull events (1 = both solar & wind below threshold)
da_combined = xr.where(da_combined == 0, 1, 0)

# Count the total number of combined lull hours at each grid point
da_sum_combined = da_combined.sum(dim='time')

# Add coordinates
da_sum_combined_wcoords = da_sum_combined.expand_dims(year=[int(year)]).assign_coords(year=[int(year)])

#Outputting

ds_out = xr.Dataset({
    'count_hour': da_sum_combined_wcoords,
    'percentage': da_sum_combined_wcoords/len(da_combined.time)*100.
    })
    
ds_out.to_netcdf(f"{folder_out}/hour_capacity_factor_lower_than_{sys.argv[2]}pc_{year}.nc")
