import xarray as xr
import numpy as np
from pathlib import Path


def write_doy_min_max(da, path):
    years_list = np.unique(da.time.dt.year.values).astype(str)
    sliced_da = da.sel(time=slice(years_list[0], years_list[-2]))

    # Add a header.
    header = 'doy,min,max\n'

    with open(path, 'w') as f:
        f.write(header)
        for doy, min, max in zip(np.unique(sliced_da.time.dt.dayofyear.values),
                                 sliced_da.groupby('time.dayofyear').min().values,
                                 sliced_da.groupby('time.dayofyear').max().values):
            f.write(f'{doy},{min},{max}\n')


def write_decades(da, path, decades=(1980, 1990, 2000, 2010)):
    header = 'doy,'
    for decade in decades:
        header += f'min_{decade},median_{decade},max_{decade},'

    collection = []
    for decade in decades:
        start = str(decade)
        end = str(decade + 9)

        da_dec = da.sel(time=slice(start, end))
        quantiles = da_dec.groupby('time.dayofyear').quantile([0, 0.5, 1])
        collection.append(quantiles)

    quantiles = np.concatenate(collection, axis=1)

    with open(path, 'w') as f:
        f.write(header[:-1] + '\n')

        for i in range(quantiles.shape[0]):
            row_vals = quantiles[i, :]
            row = f'{i + 1},'
            for col in row_vals:
                row += f'{col},'
            f.write(row[:-1] + '\n')


def write_clim(da, path):
    header = 'doy,per_10,per_25,median,per_75,per_90'

    quantiles = da.groupby('time.dayofyear').quantile([0.10, 0.25, 0.50, 0.75, 0.90]).values

    with open(path, 'w') as f:
        f.write(header + '\n')

        for i in range(quantiles.shape[0]):
            row_vals = quantiles[i, :]
            row = f'{i + 1},'
            for col in row_vals:
                row += f'{col},'
            f.write(row[:-1] + '\n')


def write_yearly_min_max(da_x, da_y, path):
    header = 'doy_min,index_min,date_min,rank_min,doy_max,index_min,date_max,rank_max'

    years = np.unique(da.time.dt.year.values).tolist()
    # Remove 1978 because the data does not cover the entire year.
    try:
        years.remove(1978)
    except ValueError:
        pass

    da_sliced_and_grouped = da_x.isel(time=da_x.time.dt.year.isin(years)).groupby('time.year')

    # Find the yearly max/min date, day of year, and index value.
    yearly_max_date = da_sliced_and_grouped.apply(lambda x: x.idxmax(dim='time'))
    yearly_max_doy = da_x.sel(time=yearly_max_date).time.dt.dayofyear
    yearly_max_index_value = da_y.sel(time=yearly_max_date)

    yearly_min_date = da_sliced_and_grouped.apply(lambda x: x.idxmin(dim='time'))
    yearly_min_doy = da_x.sel(time=yearly_min_date).time.dt.dayofyear
    yearly_min_index_value = da_y.sel(time=yearly_min_date)

    # Convert the max/min date to a string for use in hovertool display.
    hovertool_max_date = yearly_max_date.dt.strftime('%Y-%m-%d')
    hovertool_min_date = yearly_min_date.dt.strftime('%Y-%m-%d')

    # Find the rank of the max/min values. The ranks are such that the lowest value for both min and max has a rank
    # of 1.
    yearly_max_rank = yearly_max_index_value.rank('year')
    yearly_min_rank = yearly_min_index_value.rank('year')

    min_max = np.column_stack([yearly_min_doy.values, yearly_min_index_value.values, hovertool_min_date.values,
                               yearly_min_rank.values, yearly_max_doy.values, yearly_max_index_value.values,
                               hovertool_max_date.values, yearly_max_rank.values])

    with open(path, 'w') as f:
        f.write(header + '\n')

        for i in range(min_max.shape[0]):
            row_vals = min_max[i, :]
            row = ''
            for col in row_vals:
                row += f'{col},'
            f.write(row[:-1] + '\n')


if __name__ == '__main__':
    indices = ['sie', 'sia']
    areas = ['glb', 'nh', 'sh', 'bar', 'beau', 'chuk', 'ess', 'fram', 'kara', 'lap', 'sval', 'bell', 'drml', 'indi',
             'ross', 'trol', 'wedd', 'wpac']

    for area in areas:
        for index in indices:
            print(f'{area}:{index}')
            path = Path(f'data/daily/{area}/clim')
            path.mkdir(parents=True, exist_ok=True)

            ds = xr.open_dataset(f'https://thredds.met.no/thredds/dodsC/osisaf/met.no/ice/index/v2p2/{area}/osisaf_'
                                 f'{area}_{index}_daily.nc')
            da = ds[index]

            da_interpolated = da.convert_calendar('all_leap', missing=-999)
            for i, val in enumerate(da_interpolated.values):
                # Replace the -999 values with interpolated values between the preceding and succeeding day.
                if val == -999:
                    da_interpolated.values[i] = (da_interpolated.values[i - 1] + da_interpolated.values[i + 1]) / 2

            write_doy_min_max(da_interpolated, path / f'{index}_abs_min_max.csv')
            write_decades(da_interpolated, path / f'{index}_abs_decades.csv')
            write_yearly_min_max(da_interpolated, da_interpolated, path / f'{index}_abs_yearly_min_max.csv')

            for start_year, end_year in (('1981', '2010'), ('1991', '2020')):
                subset = da_interpolated.sel(time=slice(start_year, end_year))
                write_clim(subset, path / f'{index}_abs_clim_{start_year}_{end_year}.csv')

                mean = da_interpolated.sel(time=slice(start_year, end_year)).groupby('time.dayofyear').mean()
                anomaly_interpolated = da_interpolated.groupby('time.dayofyear') - mean

                write_clim(anomaly_interpolated, path / f'{index}_anom_clim_{start_year}_{end_year}.csv')
                write_doy_min_max(anomaly_interpolated, path / f'{index}_anom_min_max_{start_year}_{end_year}.csv')
                write_decades(anomaly_interpolated, path / f'{index}_anom_decades_{start_year}_{end_year}.csv')
                write_yearly_min_max(da_interpolated, anomaly_interpolated, path / f'{index}_anom_yearly_min_max_'
                                                                                   f'{start_year}_{end_year}.csv')
