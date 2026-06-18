import os
import glob
import re
import numpy as np
import pandas as pd
import xarray as xr
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import geopandas as gpd
from scipy.stats import linregress

data_dir = "/home/585/bd6544/gc26-combined-solar-wind/data/temp/bikash/s02"
fig_dir = "figures"
metrics = ["frequency", "mean_duration", "max_duration"]
seasons = ["DJF", "MAM", "JJA", "SON"]
map_extent = [112, 154, -44, -10]

custom_levels = [-0.5, -0.3, -0.2, -0.1, -0.05, 0.05, 0.1, 0.2, 0.3, 0.5]
cmap = plt.colormaps["RdBu_r"]
norm = mcolors.BoundaryNorm(boundaries=custom_levels, ncolors=cmap.N)

shapefile = '/home/585/bd6544/gc26-combined-solar-wind/data/raw/shapefiles/rez-boundaries.shx'
gdf_rez = gpd.read_file(shapefile) 

os.makedirs(fig_dir, exist_ok=True)

def plot_australia_map(ax, data, title, gdf, cmap=cmap, norm=norm, levels=custom_levels):
    ax.set_extent(map_extent, crs=ccrs.PlateCarree())
    ax.add_feature(cfeature.COASTLINE, linewidth=0.8, edgecolor="#222222")
    ax.add_feature(cfeature.BORDERS, linewidth=0.5, edgecolor="#555555")
    
    im = data.plot.pcolormesh(
        ax=ax, 
        transform=ccrs.PlateCarree(), 
        cmap=cmap, 
        norm=norm,
        levels=levels,
        add_colorbar=False,
        shading="auto",
        extend="both"
    )
    
    if gdf is not None:
        if gdf.crs != "epsg:4326":
            gdf = gdf.to_crs("epsg:4326")
        gdf.plot(ax=ax, facecolor="none", edgecolor="black", linewidth=0.7, transform=ccrs.PlateCarree())
    
    gl = ax.gridlines(draw_labels=True, linewidth=0.5, color='gray', alpha=0.4, linestyle='--')
    gl.top_labels = False
    gl.right_labels = False
    
    ax.set_title(title, fontsize=12, fontweight="bold")
    return im

def calculate_slope(y):
    if np.all(np.isnan(y)):
        return np.nan
    x = np.arange(len(y))
    mask = ~np.isnan(y)
    if np.sum(mask) < 3:
        return np.nan
    slope, _, _, _, _ = linregress(x[mask], y[mask])
    return slope

def compute_spatial_trend(da):
    return xr.apply_ufunc(
        calculate_slope,
        da,
        input_core_dims=[['year']],
        output_core_dims=[[]],
        vectorize=True,
        dask='parallelized',
        output_dtypes=[float]
    )

for metric in metrics:
    print(f"processing trends for metric: {metric}...")
    seasonal_trends = {}

    for s in seasons:
        file_pattern = os.path.join(data_dir, f"merged_compound_droughts_{s.upper()}_*.nc")
        matched_files = sorted(glob.glob(file_pattern))
        
        if not matched_files:
            file_pattern = os.path.join(data_dir, f"*_{s.upper()}.nc")
            matched_files = sorted(glob.glob(file_pattern))
            
        if not matched_files:
            continue
            
        datasets = []
        years = []
        
        for f in matched_files:
            year_match = re.search(r'\d{4}', os.path.basename(f))
            if year_match:
                year = int(year_match.group())
                ds = xr.open_dataset(f, decode_times=False)
                if metric in ds:
                    datasets.append(ds[metric])
                    years.append(year)
        
        if not datasets:
            continue
            
        da_stacked = xr.concat(datasets, dim=pd.Index(years, name='year')).sortby('year')
        seasonal_trends[s] = compute_spatial_trend(da_stacked)

    if not seasonal_trends:
        continue

    fig, axes = plt.subplots(nrows=1, ncols=4, figsize=(24, 6), subplot_kw={'projection': ccrs.PlateCarree()})

    for i, s in enumerate(seasons):
        if s in seasonal_trends:
            im = plot_australia_map(
                axes[i], seasonal_trends[s], 
                title=f"{s} long-term trend", gdf=gdf_rez
            )

    cbar_ax = fig.add_axes([0.15, 0.05, 0.7, 0.04])
    cbar = fig.colorbar(im, cax=cbar_ax, orientation="horizontal", extend="both")
    
    units = "events/year" if metric == "frequency" else "days/year"
    cbar.set_label(f"trend rate ({units})", fontsize=11, fontweight="bold")
    cbar.set_ticks(custom_levels)
    
    fig.suptitle(f"long-term {metric.replace('_', ' ')} linear trend (1979-2020)", fontsize=16, fontweight="bold", y=0.98)
    plt.subplots_adjust(wspace=0.1, bottom=0.18)
    
    output_png = os.path.join(fig_dir, f"{metric}_seasonal_trends.png")
    plt.savefig(output_png, bbox_inches="tight", dpi=300)
    print(f"saved trend analysis chart to: {output_png}")
    plt.close()
