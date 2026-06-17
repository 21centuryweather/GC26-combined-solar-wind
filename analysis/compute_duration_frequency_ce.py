import os
import sys
import numpy as np
import pandas as pd
import xarray as xr

#functions_path = os.path.abspath(f"/home/585/bd6544/GC26-combined-solar-wind/src")
#if functions_path not in sys.path:
#    sys.path.append(functions_path)

#from func_calculate_duration import count_distinct_events, max_consecutive_hours, mean_consecutive_hours
def analyze_grid_cell_with_time(condition_array, intensity_array):
    """
    function to compute freq, dur of compound events
    input 1d condition array boolean 
    returns:
    [frequency, mean_dur, max_dur, start_day_idx, end_day_idx]
    """
    x = condition_array.astype(int)

    diff = np.diff(np.concatenate(([0], x, [0])))

    starts = np.where(diff[:-1] == 1)[0]
    ends = np.where(diff == -1)[0]

    event_count = len(starts)

    if event_count == 0:
        return np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0])

    durations = ends - starts

    max_idx = np.argmax(durations)

    max_dur = float(durations[max_idx])
    mean_dur = round(float(np.mean(durations)), 2)

    event_start_idx = float(starts[max_idx])
    event_end_idx = float(ends[max_idx])

    drought_intensities = intensity_array[condition_array == 1]
    mean_intensity = round(float(np.mean(drought_intensities)), 4) if len(drought_intensities) > 0 else 0.0

    return np.array([float(event_count), mean_dur, max_dur, event_start_idx, event_end_idx, mean_intensity])


threshold = 0.1

solar_cf = f"../data/raw/solar_cf"
wind_cf = f"../data/raw/wind_cf"
output_path = f"../data/temp/bikash/s01"
os.makedirs(output_path, exist_ok=True)

solar_flist = sorted([os.path.join(solar_cf, f) for f in os.listdir(solar_cf) if f.endswith(".nc")])
wind_flist = sorted([os.path.join(wind_cf, f) for f in os.listdir(wind_cf) if f.endswith(".nc")])

seasons_dict = {
    "Annual": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
    "DJF": [12, 1, 2],
    "MAM": [3, 4, 5],
    "JJA": [6, 7, 8],
    "SON": [9, 10, 11]
}

for solar_file, wind_file in zip(solar_flist, wind_flist):
    print(f"... processing {solar_file}")
    ds_solar_year = xr.open_dataset(solar_file)
    ds_wind_year = xr.open_dataset(wind_file)

    years = np.unique(ds_solar_year["time"].dt.year.values)
    year = int(years[0])

    cf_solar_daily = ds_solar_year["capacity_factor"].resample(time="D").mean(dim="time")
    cf_wind_daily = ds_wind_year["capacity_factor"].resample(time="D").mean(dim="time")
    
    # Calculate daily 1 / (cf_wind + cf_solar) raw intensity array (with epsilon safety)
    raw_intensity_daily = 1.0 / (cf_wind_daily + cf_solar_daily + 1e-6)
    
    compound_lull_year = (cf_solar_daily < threshold) & (cf_wind_daily < threshold)

    for season_name, months in seasons_dict.items():
        season_mask = compound_lull_year["time"].dt.month.isin(months)
        compound_lull_season = compound_lull_year.sel(time=season_mask)
        intensity_season = raw_intensity_daily.sel(time=season_mask)

        if len(compound_lull_season["time"]) == 0:
            continue

        metrics = xr.apply_ufunc(
            analyze_grid_cell_with_time,
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
        
        ds_output.attrs = {"thresholds_used": f"Solar: {threshold}, Wind: {threshold}", "period": season_name}

        yearly_filename = os.path.join(output_path, f"compound_droughts_{season_name}_{year}.nc")

        ds_output.to_netcdf(
            yearly_filename,
            encoding={
                "max_event_start": {"dtype": "int32", "_FillValue": -999},
                "max_event_end": {"dtype": "int32", "_FillValue": -999}
            }
        )

    ds_solar_year.close()
    ds_wind_year.close()
    
