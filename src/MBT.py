import xarray as xr

def mean_below_threshold(data, threshold, length_max, length_min):
    '''
    Calculate "mean below threshold" events, as defined in:
        - https://www.nature.com/articles/s41467-026-72681-5
        - https://iopscience.iop.org/article/10.1088/1748-9326/ab91e9

    Where an event is a period where the mean is below the given threshold, and longer events are captured first and then removed from the analysis

    INPUTS
    data: xarray dataarray containing a time series of data (with dimension "time")
    threshold: threshold below which to define events
    length_max: maximum length of drought to look for, should be set as large as possible (no larger than the time dimension) to capture longest droughts
    length_min: minimum length of an event

    OUTPUT
    data array indicating when events occurred (including every time step within the event) and a "length" dimension to indicate the length of the event
    '''
    
    windows = list(range(length_max, length_min-1, -1))  # largest → smallest
    lull_list = []
    counted_lulls = xr.zeros_like(data, dtype=bool)
    
    for w in windows:
    
        rolling_mean = data.rolling(time=w, center=False).mean()
        w_lulls = xr.where(rolling_mean < threshold, 1, 0)
        # count every point inside the window as part of the lull
        reverse_roll = w_lulls.shift(time=-(w - 1))
        w_lulls = (
            reverse_roll
            .rolling(time=w, center=False)
            .max()
            .fillna(0)
            .astype(bool)
        )
        # only count droughts not counted in a longer period
        new_lulls = w_lulls & (~counted_lulls)
        lull_list.append(new_lulls.expand_dims(length=[w]))
        # ensure droughts lasting longer than the given window are not counted multiple times

        counted_lulls = counted_lulls | new_lulls

    return xr.concat(lull_list, dim="length")