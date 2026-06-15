import xarray as xr
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from dask.distributed import Client
import sys, os

YEAR = str(sys.argv[1])

# shared function for openning all the files for this script
def open_files(root_path, preprocess=None):
    files = [f for f in root_path.rglob('*.nc')]

    return xr.open_mfdataset(
        files,
        preprocess = preprocess,
        concat_dim='time',
        combine='nested',
        data_vars='minimal',
        coords='minimal',
        compat='override',
        parallel=True,
        chunks='auto'
    )

if __name__ == "__main__":

    # this will help load the data "lazily" and perform computations in parallel across multiple workers
    client = Client(
        n_workers=24,
        threads_per_worker=1
    )



    ###########################################################################
    # Surface Solar Irradiance product based on Himawari observations
    ###########################################################################
    
    him_path = Path(f"data/raw/himawari-solar/p1h/v1.1/{YEAR}")
    him_files = [f for f in him_path.rglob('*.nc')]
    
    def preprocess(ds):
        return ds[['hourly_integral_of_surface_global_irradiance']]
    
    him_ds = open_files(him_path, preprocess=preprocess)
    
    # Himawari times are all on the half hour (e.g. 0930, 1030, 1130 etc.),
    # floor("H") will change this to on the hour so it will line up with the weather features
    him_ds = him_ds.assign_coords(
        time=("time", him_ds.time.dt.floor("H").values),
    )
    
    # rename for simplicity
    him_ds = him_ds.rename({"hourly_integral_of_surface_global_irradiance": "GHI"})
    
    # convert units from MJ to hourly mean W
    him_ds['GHI'] =  him_ds['GHI'] * (1_000_000 / 3600)


    
    ###########################################################################
    # Load and preprocess weather features
    ###########################################################################
    
    base_path = Path("data/raw/weatherfeatures")
    
    weather_features = [
        ("wcb", "TOTAL"),
        ("maxcl", "FLAG"),
        ("mincl", "INPUT"),
        ("cutoff", "TROPO"),
        ("fronts", "FRONT"),
        ("jets", "jet"),
        ("pvstreamer", "TROP"),
    ]
    
    ds_list = []
    for wf, var_name in weather_features:
    
        # get correct directory name for file path
        if wf == "wcb":
            cdf = "cdf.1hourly"
        elif wf == "fronts":
            cdf = "cdf.850hPa"
        else:
            cdf = "cdf"
    
        
        def preprocess(ds):
    
            # rename variable to identify it with the weather feature
            ds = ds.rename({var_name: wf})
            ds = ds[[wf]] # keep just the one var
    
            # rename dimensions to  "latitude" and "longitude"
            rename_dict = {}
            for dim in ds.dims:
                lower = dim.lower()
        
                if "lat" in lower or "dimy" in lower:
                    rename_dict[dim] = "latitude"
        
                elif "lon" in lower or "dimx" in lower:
                    rename_dict[dim] = "longitude"
    
                # sum over mutiple heights to get single height
                elif "dimz" in lower:
                    ds = ds.sum(dim)
    
    
            ds = ds.rename(rename_dict)
    
            # make sure lat/lon use geographic coordinates
            ny = ds.sizes['latitude']
            nx = ds.sizes['longitude']
            
            latitude = np.linspace(-90, 90, ny)
            longitude = np.linspace(-180, 180, nx)
            
            ds = ds.assign_coords(
                latitude=("latitude", latitude),
                longitude=("longitude", longitude)
            )
    
            # some datasets have 720 longitude points, so make sure they are the same
            if ny != 721:
                ds = ds.interp(
                    latitude=np.linspace(-90, 90, 361),
                    longitude=np.linspace(-180, 180, 721),
                    method='nearest'
                )
                    
            return ds
    
        
        wf_dir = base_path / wf / cdf / YEAR
        ds = open_files(wf_dir, preprocess=preprocess)
    
        ds_list.append(ds)
    
    # merge all wf datasets into one
    wf_ds = xr.merge(ds_list)
    
    # select just the Aus region where we have himawari solar data
    wf_ds_aus = wf_ds.sel(
        latitude=slice(him_ds.latitude.min(), him_ds.latitude.max()),
        longitude=slice(him_ds.longitude.min(), him_ds.longitude.max())
    )



    #####################################################################################
    # get himawari aligned and interpolated to the WF dataset, so they place nice together
    #####################################################################################
    
    him_ds, wf_ds_aus = xr.align(
        him_ds,
        wf_ds_aus,
        join='inner'
    )
    
    him_ds = him_ds.interp(
        latitude=wf_ds_aus.latitude,
        longitude=wf_ds_aus.longitude,
        method='linear'
    )

    ##################################################################
    # save a masked version of himawari data for each weather feature
    ##################################################################
    
    for var in wf_ds_aus.data_vars:
    
        # get a mask using the weather feature
        wf_mask =wf_ds_aus[var].compute()
    
        # get the solar data during the masked periods
        wf_ghi = him_ds["GHI"].where(wf_mask).compute()
    
        # save the data
        save_dir = Path(f"data/temp/solar-weather-features/{var}")
        os.makedirs(save_dir, exist_ok=True) # makes the directory if it doesn't exist already
        file_name = save_dir / f"solar_{var}_{YEAR}.nc"
        wf_ghi.to_netcdf(file_name)

    
    