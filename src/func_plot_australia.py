import matplotlib.pyplot as plt      
import matplotlib.colors as mcolors  
import cartopy.crs as ccrs           
import cartopy.feature as cfeature
import xarray as xr

MAP_EXTENT = [112, 154, -44, -10]
def plot_australia_map(ax, data, title,gdf, cmap, norm, levels):
    """Plots climate data onto a standardized map of Australia using pcolormesh and custom norms."""
    ax.set_extent(MAP_EXTENT, crs=ccrs.PlateCarree())
    ax.add_feature(cfeature.COASTLINE, linewidth=0.8, edgecolor="#222222")
    ax.add_feature(cfeature.BORDERS, linewidth=0.5, edgecolor="#555555")
    #ax.add_feature(cfeature.STATES, linewidth=0.3, edgecolor="#888888")

    gl = ax.gridlines(draw_labels=False, linewidth=0.5, color='gray', alpha=0.5, linestyle='--')
    gl.top_labels = False
    gl.right_labels = False

    im = data.plot.pcolormesh(
        ax=ax,
        transform=ccrs.PlateCarree(),
        cmap=cmap,
        norm=norm,
        levels=levels,
        add_colorbar=False,
        shading="auto",
        extend="max"  # Colors any value higher than 28 with the darkest color
    )
    
    if gdf.crs != "EPSG:4326":
        gdf = gdf.to_crs("EPSG:4326")
    gdf.plot(ax=ax, facecolor="none", edgecolor="green", linewidth=0.7, transform=ccrs.PlateCarree())

    ax.set_title(title, fontsize=12, fontweight="bold")
    return im


