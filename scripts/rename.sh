for year in $(seq 1941 2023); do
    mv /home/563/fm6730/localrepo/GC26-combined-solar-wind/data/processed/hour_capacity_factor_lower_than_0.1pc_${year}.nc \
       /home/563/fm6730/localrepo/GC26-combined-solar-wind/data/processed/hour_capacity_factor_lower_than/hour_capacity_factor_lower_than_10pc_${year}.nc
done