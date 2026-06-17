
import numpy as np
import pandas as pd
import xarray as xr

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


def solar_declination(day_of_year):
    """Return solar declination in radians"""
    return np.deg2rad(23.44) * np.sin(
        2 * np.pi * (284 + day_of_year) / 365.0
    )

def daytime_mask_xr(ds, time_name="time", lat_name="lat", lon_name="lon"):
    """
    Return daytime mask (cos(solar zenith) > 0)
    """

    time = pd.to_datetime(ds[time_name].values)
    lat = ds[lat_name].values
    lon = ds[lon_name].values

    # dimensions
    T = len(time)
    Y = len(lat)
    X = len(lon)

    # reshape for broadcasting
    lat_rad = np.deg2rad(lat)[None, :, None]   # (1, Y, 1)
    lon_deg = lon[None, None, :]               # (1, 1, X)

    # time components
    doy = time.dayofyear.values[:, None, None]
    hour = (time.hour + time.minute / 60.0).values[:, None, None]

    # solar declination
    decl = np.deg2rad(23.44) * np.sin(
        2 * np.pi * (284 + doy) / 365.0
    )

    # local solar time
    lst = hour + lon_deg / 15.0

    omega = np.deg2rad(15.0 * (lst - 12.0))

    cosz = (
        np.sin(lat_rad) * np.sin(decl)
        + np.cos(lat_rad) * np.cos(decl) * np.cos(omega)
    )

    # return xarray DataArray
    return xr.DataArray(
        cosz > 0,
        coords={
            time_name: ds[time_name],
            lat_name: ds[lat_name],
            lon_name: ds[lon_name],
        },
        dims=(time_name, lat_name, lon_name),
        name="daytime"
    )