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

INPUT_DIR="/home/585/bd6544/GC26-combined-solar-wind/data/temp/bikash/s01"
OUTPUT_DIR="/home/585/bd6544/GC26-combined-solar-wind/data/temp/bikash/s02"

mkdir -p "${OUTPUT_DIR}"

for p in Annual DJF MAM JJA SON; do
    echo '... merging computing for ${p}'
    flist=""
    for y in {1979..2020}; do
        file="${INPUT_DIR}/compound_droughts_${p}_${y}.nc"
        if [ -f "$file" ]; then
            flist="$flist $file"
        fi
    done
    
    cdo mergetime $flist "${OUTPUT_DIR}/merged_compound_droughts_${p}.nc"

    cdo timmean -selname,frequency "${OUTPUT_DIR}/merged_compound_droughts_${p}.nc" "${OUTPUT_DIR}/frequency_compound_droughts_${p}.nc"

    cdo timmean -selname,mean_duration "${OUTPUT_DIR}/merged_compound_droughts_${p}.nc" "${OUTPUT_DIR}/mean_duration_compound_droughts_${p}.nc"

    cdo timmax -selname,max_duration "${OUTPUT_DIR}/merged_compound_droughts_${p}.nc" "${OUTPUT_DIR}/max_duration_compound_droughts_${p}.nc"
    cdo timmean -selname,mean_intensity "${OUTPUT_DIR}/merged_compound_droughts_${p}.nc" "${OUTPUT_DIR}/mean_intensity_compound_droughts_${p}.nc"
done
