"""Solar drought frequency over the winter season (May–September).

Computes the fraction of winter days in "solar drought" using three
threshold definitions and maps each one on a common colour scale:

  1. Relative   : daily CF below (seasonal mean - 1 std)
  2. Absolute   : daily CF below a fixed value (0.10)
  3. Percentile : daily CF below the per-gridcell 10th percentile
"""

import matplotlib
import dask
import matplotlib.pyplot as plt
import xarray as xr
import cartopy.crs as ccrs
from dask.diagnostics import ProgressBar

# Configuration
SOLAR_CF_PATH = "/home/563/ft3359/GC26-combined-solar-wind/data/raw/solar_cf"
VAR = "capacity_factor"
WINTER_MONTHS = [5, 6, 7, 8, 9]
THRESHOLD_ABS = 0.10
PERCENTILE = 0.10
OUTPUT_DIR = "."  # where PNGs are written


def load_winter_cf():
    """Open the netCDF collection and return the loaded winter daily-mean CF."""
    ds = xr.open_mfdataset(f"{SOLAR_CF_PATH}/*.nc", chunks={"time": 24 * 30})
    print(ds)

    cf = ds[VAR]
    cf_daily = cf.resample(time="1D").mean()  # hourly -> daily mean
    winter = cf_daily.sel(time=cf_daily.time.dt.month.isin(WINTER_MONTHS))

    # Materialise once
    with ProgressBar():
        winter = winter.load()
    return winter


def plot_drought_freq(da, title, filename):
    """Map a drought-frequency field."""
    fig = plt.figure(figsize=(10, 6))
    ax = plt.axes(projection=ccrs.PlateCarree())
    da.plot(
        ax=ax,
        transform=ccrs.PlateCarree(),
        cmap="viridis",
        cbar_kwargs={"label": "Fraction of days"},
    )
    ax.coastlines(resolution="50m")
    ax.set_title(title)
    fig.savefig(f"{OUTPUT_DIR}/{filename}", dpi=150, bbox_inches="tight")
    plt.close(fig)


def main():
    winter = load_winter_cf()

    # 1. Statistical threshold: mean - 1 std
    mean_cf, std_cf = dask.compute(winter.mean("time"), winter.std("time"))
    threshold = mean_cf - std_cf
    drought_freq = (winter < threshold).mean("time")
    print("mean drought frequency (relative):", float(drought_freq.mean()))
    print("mean CF:", float(mean_cf.mean()))
    print("std CF:", float(std_cf.mean()))

    # 2. Absolute threshold
    drought_freq_abs = (winter < THRESHOLD_ABS).mean("time")
    print("mean drought frequency (absolute):", float(drought_freq_abs.mean()))

    # 3. Per-gridcell percentile threshold
    threshold_pct = winter.quantile(PERCENTILE, dim="time")
    drought_freq_pct = (winter < threshold_pct).mean("time")
    print("mean drought frequency (percentile):", float(drought_freq_pct.mean()))

    plot_drought_freq(
        drought_freq,
        "Fraction of May–Sept days in solar drought (mean − 1 std)",
        "drought_freq_relative.png",
    )
    plot_drought_freq(
        drought_freq_abs,
        f"Fraction of May–Sept days below CF = {THRESHOLD_ABS}",
        "drought_freq_absolute.png",
    )
    plot_drought_freq(
        drought_freq_pct,
        f"Fraction of May–Sept days below {int(PERCENTILE * 100)}th percentile",
        "drought_freq_percentile.png",
    )


if __name__ == "__main__":
    main()