#load libraries
import xarray as xr
from dask.distributed import Client
import numpy as np
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import seaborn as sns

# setup dask client
client = Client()

# dataset locations
solar_cf_folder = "/home/561/jl1950/GC26-combined-solar-wind/data/raw/solar_cf"
wind_cf_folder = "/home/561/jl1950/GC26-combined-solar-wind/data/raw/wind_cf"
rez_mask_path = "/home/561/jl1950/GC26-combined-solar-wind/data/processed/REZ_mask/REZ_by_state_mask.nc"

# identify regions by id and name for later
region_names = {
    0: "TAS",
    1: "SA",
    2: "VIC",
    3: "NSW",
    4: "QLD"
}

# load rez mask
ds_rez_mask = xr.load_dataset(rez_mask_path)

# load solar and wind datasets
yearlist = list(range(2003, 2023+1))
yearlist = [2023] # comment this out to use the list of years above

solar_filepaths = []
wind_filepaths = []
for yr in yearlist:
    solar_yearstring = f"solar_capacity_factor_van_der_Wiel_era5_hourly_{yr}_Aus.nc"
    solar_fullstring = f"{solar_cf_folder}/{solar_yearstring}"
    solar_filepaths.append(solar_fullstring)

    wind_yearstring = f"wind_capacity_factor_van_der_Wiel_era5_hourly_{yr}_Aus.nc"
    wind_fullstring = f"{wind_cf_folder}/{wind_yearstring}"
    wind_filepaths.append(wind_fullstring)

ds_solarcf = xr.open_mfdataset(solar_filepaths, chunks='auto')
da_solarcf = ds_solarcf.capacity_factor

ds_windcf = xr.open_mfdataset(wind_filepaths, chunks = 'auto')
da_windcf = ds_windcf.capacity_factor

# combine datasets
ds_cf_all = da_solarcf.to_dataset(name="solar_cf")
ds_cf_all = ds_cf_all.assign(wind_cf=da_windcf)
ds_cf_all = ds_cf_all.assign_coords(state_mask=ds_rez_mask.mask)

# mask solar and wind with where state_mask not null to remove unwanted bits
ds_cf_all['solar_cf'] = ds_cf_all['solar_cf'].where(ds_cf_all.state_mask.notnull())
ds_cf_all['wind_cf'] = ds_cf_all['wind_cf'].where(ds_cf_all.state_mask.notnull())

# calculate daily averages
ds_cf_daily = ds_cf_all.resample(time="1D").mean()

#calculate averages by state (along lat lon dimensions)
ds_stacked = ds_cf_daily.stack(points=("lat", "lon"))

ds_cf_state_means = ds_stacked.groupby("state_mask").mean(dim="points")


# plot scatter plots by state
ds_plot = ds_cf_state_means.assign_coords(
    state_mask=ds_cf_state_means["state_mask"].to_series().map(region_names)
)

ticks = np.arange(0, 1.01, 0.2)

g = ds_plot.plot.scatter(
    x="solar_cf",
    y="wind_cf",
    col="state_mask",
    col_wrap=3,
    figsize=(12, 8),
    add_legend=False,
    add_colorbar=False
)

# plot kernel density plots by state
df = (
    ds_plot[["solar_cf", "wind_cf"]]
    .to_dataframe()
    .reset_index()
    .dropna(subset=["solar_cf", "wind_cf", "state_mask"])
)

states = ["TAS", "SA", "VIC", "NSW", "QLD"]

fig, axs = plt.subplots(
    nrows=2,
    ncols=3,
    figsize=(12, 8),
    sharex=True,
    sharey=True
)

ticks = np.arange(0, 1.01, 0.2)

for ax, state in zip(axs.flat, states):
    df_state = df[df["state_mask"] == state]

    sns.kdeplot(
        data=df_state,
        x="solar_cf",
        y="wind_cf",
        ax=ax,
        fill=True,
        levels=10,
        thresh=0.01
    )

    ax.set_title(state)
    
    ax.set_xlabel("Solar capacity factor")
    ax.set_ylabel("Wind capacity factor")

# remove unused sixth subplot
for ax in axs.flat[len(states):]:
    ax.remove()

plt.tight_layout()
plt.show()