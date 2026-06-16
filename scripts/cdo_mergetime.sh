module load cdo

cf_threshold=10
cdo mergetime $(ls /home/563/fm6730/localrepo/GC26-combined-solar-wind/data/processed/hour_capacity_factor_lower_than/hour_capacity_factor_lower_than_${cf_threshold}pc_*.nc) "/home/563/fm6730/localrepo/GC26-combined-solar-wind/data/processed/hour_capacity_factor_lower_than/merged/hour_capacity_factor_lower_than_${cf_threshold}pc_1940-2023.nc"