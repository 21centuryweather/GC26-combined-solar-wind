#!/bin/bash

#PBS -P nf33
#PBS -q normal
#PBS -l walltime=01:00:00
#PBS -l ncpus=1
#PBS -l mem=4GB
#PBS -l jobfs=1GB
#PBS -l storage=gdata/nf33+gdata/w42+gdata/dk92
#PBS -N compute_clim_mean
#PBS -o compute_clim_mean.log
#PBS -l wd

module use /g/data/dk92/apps/Modules/modulefiles/
module load cdo

INPUT_DIR="/home/585/bd6544/GC26-combined-solar-wind/data/raw/wind_cf"
OUTPUT_DIR="/home/585/bd6544/GC26-combined-solar-wind/data/temp/bikash/s02"

mkdir -p "${OUTPUT_DIR}"


flist=""
for y in {1979..2020}; do
    file="${INPUT_DIR}/wind_capacity_factor_van_der_Wiel_era5_hourly_${y}_Aus.nc"
    flist="$flist $file"
done


MERGED_TEMP="${OUTPUT_DIR}/merged_1979_2020_temp.nc"

cdo -s --no_history mergetime $flist "$MERGED_TEMP"

echo "... computing Annual mean"
cdo -s --no_history timmean "$MERGED_TEMP" "${OUTPUT_DIR}/mean_wind_cf_Annual_1979_2020.nc"

echo "... splitting into seasonal means"
SEAS_TEMP="${OUTPUT_DIR}/seasonal_means_temp.nc"
cdo -s --no_history timselmean,1 -seasmean "$MERGED_TEMP" "$SEAS_TEMP"

cdo -s --no_history splitseas "$SEAS_TEMP" "${OUTPUT_DIR}/mean_wind_cf_1979_2020_"

rm -f "$MERGED_TEMP" "$SEAS_TEMP"
