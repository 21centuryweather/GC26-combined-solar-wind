# load shapefile and convert to xarray mask/netcdf using a template dataset
import geopandas as gpd
import regionmask
import xarray as xr

re_zones_shapefile = "/home/561/jl1950//GC26-combined-solar-wind/data/raw/shapefiles/REZ-boundaries.shx"
solar_cf_folder = "/home/561/jl1950/GC26-combined-solar-wind/data/raw/solar_cf"

csv_output="/home/561/jl1950/GC26-combined-solar-wind/data/processed/REZ_mask/REZ_information.csv"
mask_netcdf_output = "/home/561/jl1950/GC26-combined-solar-wind/data/processed/REZ_mask/REZ_mask.nc"

year = 2023
solar_yearstring = f"solar_capacity_factor_van_der_Wiel_era5_hourly_{year}_Aus.nc"
solar_fullstring = f"{solar_cf_folder}/{solar_yearstring}"

gdf = gpd.read_file(re_zones_shapefile)
ds = xr.open_dataset(solar_fullstring)

# produce a csv output with mapping of ID to region name
gdf_wkt = gdf.assign(geometry=gdf.geometry.to_wkt())
gdf_wkt.to_csv(csv_output, index=True, index_label='ID')

# apply crs (needs to match the template xarray dataset) - currently it doesn't have one so this is potentially questionable
gdf = gdf.to_crs("EPSG:4326")

# create regionmask object and specify column for id calculation
regions = regionmask.from_geopandas(gdf, names="Name")

# create mask
mask_2d = regions.mask(ds.lon, ds.lat)

# save to netcdf
mask_2d.to_netcdf(mask_netcdf_output)