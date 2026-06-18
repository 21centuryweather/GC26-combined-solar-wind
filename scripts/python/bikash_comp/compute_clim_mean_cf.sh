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

INPUT_DIR="/home/585/bd6544/GC26-combined-solar-wind/data/raw/solar_cf"
OUTPUT_DIR="/home/585/bd6544/GC26-combined-solar-wind/data/temp/bikash/s02"

mkdir -p "${OUTPUT_DIR}"


flist=""
for y in {1979..2020}; do
    file="${INPUT_DIR}/solar_capacity_factor_van_der_Wiel_era5_hourly_${y}_Aus.nc"
    flist="$flist $file"
done


MERGED_TEMP="${OUTPUT_DIR}/merged_1979_2020_temp.nc"

cdo -s -O --no_history mergetime $flist "$MERGED_TEMP"

cdo -s --no_history timmean "$MERGED_TEMP" "${OUTPUT_DIR}/mean_solar_cf_Annual_1979_2020.nc"

cdo -s --no_history -timmean -selmon,12,1,2 "$MERGED_TEMP" "${OUTPUT_DIR}/mean_solar_cf_1979_2020_DJF.nc"

cdo -s --no_history -timmean -selmon,3,4,5 "$MERGED_TEMP" "${OUTPUT_DIR}/mean_solar_cf_1979_2020_MAM.nc"

cdo -s --no_history -timmean -selmon,6,7,8 "$MERGED_TEMP" "${OUTPUT_DIR}/mean_solar_cf_1979_2020_JJA.nc"

cdo -s --no_history -timmean -selmon,9,10,11 "$MERGED_TEMP" "${OUTPUT_DIR}/mean_solar_cf_1979_2020_SON.nc"

rm -f "$MERGED_TEMP"

