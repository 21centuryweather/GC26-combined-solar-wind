import os
import numpy as np
import pandas as pd
import xarray as xr
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import geopandas as gpd
from scipy.stats import linregress

data_dir = "/home/585/bd6544/GC26-combined-solar-wind/data/temp/bikash/s02"
shapefile = '/home/585/bd6544/GC26-combined-solar-wind/data/raw/shapefiles/REZ-boundaries.shx'
fig_dir = "figures"
metrics = ["mean_duration", "max_duration","frequency"]
seasons = ["djf", "mam", "jja", "son"]
map_extent = [112, 154, -44, -10]

custom_levels = [-0.1, -0.05,-0.04,-0.03,-0.02,-0.01,0.01,0.02,0.03,0.04, 0.05, 0.1]
cmap = plt.colormaps["RdBu_r"]
norm = mcolors.BoundaryNorm(boundaries=custom_levels, ncolors=cmap.N)

gdf_rez = gpd.read_file(shapefile) if os.path.exists(shapefile) else None

os.makedirs(fig_dir, exist_ok=True)

def plot_australia_map(ax, slope_data, p_data, title, gdf, cmap=cmap, norm=norm, levels=custom_levels):
    ax.set_extent(map_extent, crs=ccrs.PlateCarree())
    ax.add_feature(cfeature.COASTLINE, linewidth=0.8, edgecolor="#222222")
    ax.add_feature(cfeature.BORDERS, linewidth=0.5, edgecolor="#555555")
    
    im = slope_data.plot.pcolormesh(
        ax=ax, 
        transform=ccrs.PlateCarree(), 
        cmap=cmap, 
        norm=norm,
        levels=levels,
        add_colorbar=False,
        shading="auto",
        extend="both"
    )
    
    ax.contourf(
        p_data.lon, p_data.lat, p_data,
        levels=[0, 0.05],
        colors='none',
        hatches=['xxxx'],
        transform=ccrs.PlateCarree()
    )
    
    if gdf is not None:
        if gdf.crs != "epsg:4326":
            gdf = gdf.to_crs("epsg:4326")
        gdf.plot(ax=ax, facecolor="none", edgecolor="green", linewidth=0.7, transform=ccrs.PlateCarree())
    
    gl = ax.gridlines(draw_labels=False, linewidth=0.5, color='gray', alpha=0.4, linestyle='--')
    gl.top_labels = False
    gl.right_labels = False
    
    ax.set_title(title, fontsize=12, fontweight="bold")
    return im

def calculate_slope_and_p(y):
    if np.all(np.isnan(y)):
        return np.nan, np.nan
    x = np.arange(len(y))
    mask = ~np.isnan(y)
    if np.sum(mask) < 3:
        return np.nan, np.nan
    slope, _, _, p_value, _ = linregress(x[mask], y[mask])
    return slope, p_value

def compute_spatial_stats(da):
    return xr.apply_ufunc(
        calculate_slope_and_p,
        da,
        input_core_dims=[['time']],
        output_core_dims=[[], []],
        vectorize=True,
        output_dtypes=[float, float]
    )

for metric in metrics:
    print(f"processing trends and significance for metric: {metric}...")
    
    fig, axes = plt.subplots(nrows=1, ncols=4, figsize=(14, 5), subplot_kw={'projection': ccrs.PlateCarree()})
    has_plotted = False

    for i, s in enumerate(seasons):
        file = os.path.join(data_dir, f"merged_compound_droughts_{s.upper()}.nc")
        
        if not os.path.exists(file):
            continue
            
        ds = xr.open_dataset(file, decode_times=False)
        
        if metric in ds:
            trend_map, p_map = compute_spatial_stats(ds[metric])
            im = plot_australia_map(
                axes[i], trend_map, p_map,
                title=f"{s.upper()}", gdf=gdf_rez
            )

    cbar_ax = fig.add_axes([0.15, 0.15, 0.7, 0.04])
    cbar = fig.colorbar(im, cax=cbar_ax, orientation="horizontal", extend="both")
    
    units = "events/year" if metric == "frequency" else "days/year"
    cbar.set_label(f"trend ({units})", fontsize=14, fontweight="bold")
    cbar.set_ticks(custom_levels)
    
    #fig.suptitle(f"long-term {metric.replace('_', ' ')} linear trend (1979-2020)", fontsize=16, fontweight="bold", y=0.98)
    plt.subplots_adjust(wspace=0.1, bottom=0.18)
    
    output_png = os.path.join(fig_dir, f"{metric}_seasonal_trends.png")
    plt.savefig(output_png, bbox_inches="tight", dpi=300)
    print(f"saved trend analysis chart to: {output_png}")
    plt.close()
