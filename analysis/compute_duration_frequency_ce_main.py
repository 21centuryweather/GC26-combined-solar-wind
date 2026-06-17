import os
import sys
import numpy as np
import pandas as pd
import xarray as xr
import src.analysis_func as af

from pathlib import Path

#functions_path = os.path.abspath(f"/home/585/bd6544/GC26-combined-solar-wind/src")
#if functions_path not in sys.path:
#    sys.path.append(functions_path)

#from func_calculate_duration import count_distinct_events, max_consecutive_hours, mean_consecutive_hours

# cf_threshold = 0.1
cf_threshold = sys.argv[2]/100. #in percent

# year = 2000
year = sys.argv[1]

folder_main = Path("/home/563/fm6730/localrepo/GC26-combined-solar-wind/data/")

folder_solar = os.path.join(folder_main, "raw", "solar_cf") 
folder_wind  = os.path.join(folder_main, "raw", "wind_cf") 
output_path  = os.path.join(folder_main, "temp", "frm", "s01")
os.makedirs(output_path, exist_ok=True)

# solar_flist = sorted([os.path.join(solar_cf, f) for f in os.listdir(solar_cf) if f.endswith(".nc")])
# wind_flist = sorted([os.path.join(wind_cf, f) for f in os.listdir(wind_cf) if f.endswith(".nc")])

solar_file = f'{folder_solar}/solar_capacity_factor_van_der_Wiel_era5_hourly_{year}_Aus.nc'
wind_file  = f'{folder_wind}/wind_capacity_factor_van_der_Wiel_era5_hourly_{year}_Aus.nc'

seasons_dict = {
    "Annual": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
    "DJF": [12, 1, 2],
    "MAM": [3, 4, 5],
    "JJA": [6, 7, 8],
    "SON": [9, 10, 11]
}

ds_solar_year = xr.open_dataset(solar_file)
ds_wind_year = xr.open_dataset(wind_file)

years = np.unique(ds_solar_year["time"].dt.year.values)
year = int(years[0])

cf_solar_daily = ds_solar_year["capacity_factor"].resample(time="D").mean(dim="time")
cf_wind_daily = ds_wind_year["capacity_factor"].resample(time="D").mean(dim="time")

# Calculate daily 1 / (cf_wind + cf_solar) raw intensity array (with epsilon safety)
raw_intensity_daily = 1.0 / (cf_wind_daily + cf_solar_daily + 1e-6)

compound_lull_year = (cf_solar_daily < cf_threshold) & (cf_wind_daily < cf_threshold)

for season_name, months in seasons_dict.items():
    season_mask = compound_lull_year["time"].dt.month.isin(months)
    compound_lull_season = compound_lull_year.sel(time=season_mask)
    intensity_season = raw_intensity_daily.sel(time=season_mask)

    if len(compound_lull_season["time"]) == 0:
        continue

    metrics = xr.apply_ufunc(
        af.analyze_grid_cell_with_time,
        compound_lull_season,
        intensity_season,
        input_core_dims=[["time"], ["time"]],
        output_core_dims=[["metric"]],
        vectorize=True,
        output_dtypes=[float],
        dask_gufunc_kwargs=None,
    )

    metrics = metrics.assign_coords(metric=["frequency", "mean_dur", "max_dur", "start_idx", "end_idx", "mean_intensity"])

    first_date_season = pd.Timestamp(compound_lull_season["time"].values[0]).strftime("%Y-%m-%d %H:%M:%S")
    base_time_str = f"days since {first_date_season}"

    ds_output = xr.Dataset(
        data_vars={
            "frequency": metrics.sel(metric="frequency").drop_vars("metric"),
            "mean_duration": metrics.sel(metric="mean_dur").drop_vars("metric"),
            "max_duration": metrics.sel(metric="max_dur").drop_vars("metric"),
            "max_event_start": metrics.sel(metric="start_idx").drop_vars("metric"),
            "max_event_end": metrics.sel(metric="end_idx").drop_vars("metric"),
            "mean_intensity": metrics.sel(metric="mean_intensity").drop_vars("metric"),
        },
        coords={"lat": ds_solar_year["lat"], "lon": ds_solar_year["lon"]}
    )

    ds_output["frequency"].attrs = {"units": "events", "description": f"Count of compound lull events in {season_name} {year}"}
    ds_output["mean_duration"].attrs = {"units": "days", "description": f"Mean duration of compound lull events in {season_name} {year}"}
    ds_output["max_duration"].attrs = {"units": "days", "description": f"Maximum duration of compound lull events in {season_name} {year}"}
    
    ds_output["max_event_start"].attrs = {"units": base_time_str, "calendar": "standard", "description": f"Start date of the longest lull in {season_name}"}
    ds_output["max_event_end"].attrs = {"units": base_time_str, "calendar": "standard", "description": f"End date of the longest lull in {season_name}"}
    
    ds_output["mean_intensity"].attrs = {"units": "1/CF", "description": f"Mean compound lull resource drought intensity index 1/(cf_wind+cf_solar) in {season_name} {year}"}
    
    ds_output.attrs = {"cf_thresholds_used": f"Solar: {cf_threshold*100}%, Wind: {cf_threshold*100}%", "period": season_name}

    yearly_filename = os.path.join(output_path, f"compound_lulls_{season_name}_{cf_threshold*100}pc_{year}.nc")

    ds_output.to_netcdf(
        yearly_filename,
        encoding={
            "max_event_start": {"dtype": "int32", "_FillValue": -999},
            "max_event_end": {"dtype": "int32", "_FillValue": -999}
        }
    )

# ds_solar_year.close()
# ds_wind_year.close()

