from rasterstats import zonal_stats
import rasterio
import pandas as pd
import xarray as xr
import geopandas as gpd
import odc.geo.xr
import os
from pathlib import Path
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import rioxarray
from shapely.geometry import mapping
import sys, os

from dask.distributed import Client

# choose to look at solar or wind
VRE = sys.argv[1]

if __name__ == "__main__":
    client = Client(
        n_workers=24,
        threads_per_worker=1
    )
    
    # just use daily data
    def preprocess(ds):
        return (
        ds
        .sortby("time")
        .resample(time="1D")
        .mean()
        )
    
    # open capacity factor data
    root_path = Path(f'data/raw/{VRE}_cf')
    files = sorted([
        f for f in root_path.glob("*.nc")
        if any(str(y) in f.name for y in range(1979, 2021))
    ])
    ds =  xr.open_mfdataset(
            files,
            preprocess=preprocess,
            concat_dim='time',
            combine='nested',
            data_vars='minimal',
            coords='minimal',
            compat='override',
            parallel=True,
            chunks='auto'
        )
    
    
    # set up geo metadata so it can work with the shape file
    ds = (
        ds.capacity_factor
        .rio.set_spatial_dims(x_dim="lon", y_dim="lat")
        .rio.write_crs("EPSG:4326")
    )
    
    # load the shape file with REZ boundaries
    shapefile = 'data/raw/shapefiles/REZ-boundaries.shx'
    gdf_rez = gpd.read_file(shapefile)
    
    # list to store state based data
    state_data = []
    
    # states we are interested in
    states = [
        'Q',
        'N',
        'V',
        'S',
        'T',
    ]
    
    # Loop over the states and compute mean capacity factor in the REZs
    for state in states:
    
        # get the REZs for the state
        gdf_state = gdf_rez[gdf_rez["Name"].str.startswith(state, na=False)]
    
        # get the CF data in the state's REZs
        cf_state = ds.rio.clip(
            gdf_state.geometry.apply(mapping),  # Convert to GeoJSON format
            gdf_state.crs,
            drop=True  # Drops data outside polygons
        )
    
        # take the spatial mean to convert to a timeseries
        cf_state_mean = cf_state.mean(['lon', 'lat'])
        # name the data based on the state
        cf_state_mean = cf_state_mean.rename(state)
        # add the the list
        state_data.append(cf_state_mean)
    
    # combine states into single dataset
    CF_states = xr.merge(state_data)
    
    # compute before saving
    CF_states = CF_states.compute()
    
    # save data
    save_path = Path('data/processed/daily-state-cf')
    os.makedirs(save_path, exist_ok=True)
    file_name = save_path / f"{VRE}_daily-state-cf.nc"
    CF_states.to_netcdf(file_name)
