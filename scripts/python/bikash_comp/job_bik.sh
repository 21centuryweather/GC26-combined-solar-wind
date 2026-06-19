#!/bin/bash

#PBS -P nf33 
#PBS -q normal
#PBS -l walltime=03:00:00
#PBS -l ncpus=1
#PBS -l mem=16GB
#PBS -l jobfs=1GB
#PBS -l storage=gdata/nf33+gdata/w42+gdata/dk92
#PBS -N mean_max_dur
#PBS -o mean_max_dur.log
#PBS -l wd

# Load Python module
module use /g/data/dk92/apps/Modules/modulefiles/
module load pyaos

python compute_duration_frequency_ce.py
