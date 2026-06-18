import sys
import os
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np
import xarray as xr
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import geopandas as gpd

functions_path = os.path.abspath(f"/home/585/bd6544/GC26-combined-solar-wind/src")
if functions_path not in sys.path:
    sys.path.append(functions_path)

from func_plot_australia import plot_australia_map

data_dir = "/home/585/bd6544/GC26-combined-solar-wind/data/temp/bikash/s02"
METRIC = "mean_duration"  

shapefile = '/home/585/bd6544/GC26-combined-solar-wind/data/raw/shapefiles/REZ-boundaries.shx'
gdf_rez = gpd.read_file(shapefile)

MAP_EXTENT = [112, 154, -44, -10]  
levels = [0,0.3,0.6,0.9,1.2,1.5,1.8,2.1,2.4,3]
cmap_name = "YlOrRd"
cmap = plt.colormaps[cmap_name]
norm = mcolors.BoundaryNorm(boundaries=levels, ncolors=cmap.N, extend = "max")

### plot seasons
seasons = ["DJF", "MAM", "JJA", "SON"]
seasonal_datasets = {}

for s in seasons:
    file_path = os.path.join(data_dir, f"{METRIC}_compound_droughts_{s}.nc")
    if os.path.exists(file_path):
        ds = xr.open_dataset(file_path, decode_times=False)
        data_slice = ds[METRIC]
        seasonal_datasets[s] = data_slice
        
if seasonal_datasets:
    fig, axes = plt.subplots(
        nrows=1, ncols=4, 
        figsize=(14, 5), 
        subplot_kw={'projection': ccrs.PlateCarree()}
    )
    axes = axes.flatten()

    for i, s in enumerate(seasons):
        if s in seasonal_datasets:
            im = plot_australia_map(
                axes[i], seasonal_datasets[s], 
                title=f"{s}",gdf = gdf_rez, cmap=cmap_name, 
                norm=norm, levels = levels
            )

    # Add a single shared colorbar for the 4 seasonal subplots
    cbar_ax = fig.add_axes([0.15, 0.17, 0.7, 0.03])  # [left, bottom, width, height]
    cbar = fig.colorbar(im, cax=cbar_ax, orientation="horizontal", extend = "max")
    cbar.set_label(f"Duration (Days)", fontsize=14, fontweight="bold")
    
    #fig.suptitle(f"Climatological Mean Compound Drought Duration by Season (1979-2020)", fontsize=16, fontweight="bold", y=0.96)
    plt.subplots_adjust(wspace=0.15, hspace=0.15)
    
    seasonal_out = f"figures/seasonal_{METRIC}_map.png"
    plt.savefig(seasonal_out, bbox_inches="tight", dpi=300)
    print(f"Saved seasonal plot to: {seasonal_out}")
    plt.close()

#ploting one annual plot
annual_file = os.path.join(data_dir, f"{METRIC}_compound_droughts_Annual.nc")
if os.path.exists(annual_file):
    ds_annual = xr.open_dataset(annual_file, decode_times=False)
    annual_data = ds_annual[METRIC]
    
    fig_ann, ax_ann = plt.subplots(
        figsize=(8, 7), 
        subplot_kw={'projection': ccrs.PlateCarree()}
    )
    
    im_ann = plot_australia_map(
        ax_ann, annual_data, 
        title="Annual",gdf = gdf_rez, 
        cmap=cmap_name, norm=norm, levels=levels
    )
    
    # Add dedicated right side colorbar for the single plot
    cbar = fig_ann.colorbar(im_ann, ax=ax_ann, orientation="vertical", pad=0.05, shrink=0.7,extend = "max")
    cbar.set_label("Duration (Days)", fontsize=14, fontweight="bold")
    
    #fig_ann.suptitle("Annual Mean Compound Drought Duration (1979-2020)", fontsize=14, fontweight="bold", y=0.92)
    
    annual_out = f"figures/annual_{METRIC}_map.png"
    plt.savefig(annual_out, bbox_inches="tight", dpi=300)
    print(f"Saved annual plot to: {annual_out}")
    plt.close()
else:
    print(f"Annual file not found at: {annual_file}")
