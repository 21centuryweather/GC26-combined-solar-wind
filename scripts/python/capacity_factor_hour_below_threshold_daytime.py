import sys, os
import xarray as xr
import numpy as np
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

import analysis_func as af

# -------------------------------------------------------
# Usage: qsub capacity_factor_hour_below_threshold_calc.sh
# Input: one column (year).
# For trial, change the year to a number, then do python capacity_factor_hour_below_threshold.py
# -------------------------------------------------------

# This script calculates the number of capacity factors lower than a certain threshold (given in sys.argv[2]).

# Get the year from the command-line argument
year = sys.argv[1]
# year = 2000
cf_threshold = float(sys.argv[2])/100.
# cf_threshold = 10/100.

# Define paths to raw solar and wind capacity factor data
folder_solar = Path("/home/563/fm6730/localrepo/GC26-combined-solar-wind/data/raw/solar_cf/")
folder_wind  = Path("/home/563/fm6730/localrepo/GC26-combined-solar-wind/data/raw/wind_cf/")
folder_out   = Path("/home/563/fm6730/localrepo/GC26-combined-solar-wind/data/processed/hour_capacity_factor_lower_than/daytime_only/")
os.makedirs(folder_out, exist_ok=True)

# Construct file paths for the given year
file_solar = f'{folder_solar}/solar_capacity_factor_van_der_Wiel_era5_hourly_{year}_Aus.nc'
file_wind  = f'{folder_wind}/wind_capacity_factor_van_der_Wiel_era5_hourly_{year}_Aus.nc'

# Load solar and wind datasets
ds_solar = xr.open_dataset(file_solar)
ds_wind  = xr.open_dataset(file_wind)

# Extract capacity factor variables
da_solar = ds_solar['capacity_factor']
da_wind  = ds_wind['capacity_factor']

#Create a mask (mask the nighttime)
daytime_mask = af.daytime_mask_xr(da_solar, "time", "lat", "lon")

#Apply mask
da_solar_masked = xr.where(daytime_mask, da_solar, np.nan)
da_wind_masked = xr.where(daytime_mask, da_wind, np.nan)

da_solar_masked = da_solar_masked.rename('solar_cf').dropna(dim='time')
da_wind_masked = da_wind_masked.rename('wind_cf').dropna(dim='time')

# Flag hours where capacity factor exceeds 0.1 (1 = active, 0 = lull)
da_solar_sel = xr.where(da_solar_masked > cf_threshold, 1, 0)
da_wind_sel  = xr.where(da_wind_masked  > cf_threshold, 1, 0)

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
    
ds_out.to_netcdf(f"{folder_out}/daytime_hour_capacity_factor_lower_than_{int(round(cf_threshold*100.,2))}pc_{year}.nc")
