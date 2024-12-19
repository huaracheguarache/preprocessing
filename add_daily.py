import xarray as xr
import numpy as np
from pathlib import Path


path = Path('/lustre/storeB/project/metproduction/products/osisaf/output/ice/extent/sii_v3p0/auto')
paths = sorted([p for p in path.iterdir() if p.is_dir()])

for path in paths:
    for file in sorted(path.glob('*daily.nc')):
        ds = xr.open_dataset(file)

        try:
            da = ds['sia']
        except KeyError:
            da = ds['sie']

        da_interpolated = da.convert_calendar('all_leap', missing=-9999)

        for i, val in enumerate(da_interpolated.values):
            # Replace the -9999 values with interpolated values between the preceding and succeeding day.
            if val == -9999:
                da_interpolated.values[i] = (da_interpolated.values[i - 1] + da_interpolated.values[i + 1]) / 2

        rank = da_interpolated.groupby('time.dayofyear').map(lambda x: x.rank('time'))

        # Now we need to throw out all Feb. 29th values which are not from actual leap years.
        rank = rank.convert_calendar('gregorian')
        ds = ds.assign(rank=rank)
        ds['rank'].attrs = {'long_name': 'Rank per day of year',
                            'coverage_content_type': '',
                            'comment': 'To deal with the issue of leap years all years in the data are converted to '
                                       'leap years with Feb. 29th values inserted for non-leap years. The values are '
                                       'interpolated between that of Feb. 28th and Mar. 1st. Rank is then calculated '
                                       'on a day of year basis, after which all years in the data are converted back '
                                       'to a Gregorian calendar to discard fake leap days. Ties are dealt with by '
                                       'assigning a rank that is the average of the ranks that would have been '
                                       'otherwise assigned to all of the values within that set.'}

        # Min/max per DOY.
        years_list = np.unique(da.time.dt.year.values).astype(str)
        sliced_da = da.sel(time=slice(years_list[0], years_list[-2]))

        min_per_doy = sliced_da.groupby('time.dayofyear').min()
        max_per_doy = sliced_da.groupby('time.dayofyear').max()

        ds = ds.assign(min_per_doy=min_per_doy, max_per_doy=max_per_doy)
        ds['min_per_doy'].attrs = {'long_name': 'Minimum value per day of year',
                                   'units': '1e6 km^2',
                                   'coverage_content_type': ''}
        ds['max_per_doy'].attrs = {'long_name': 'Maximum value per day of year',
                                   'units': '1e6 km^2',
                                   'coverage_content_type': ''}

        # Min/max per year (coordinate year, with variables: value, date, rank).
        years = np.unique(da.time.dt.year.values).tolist()

        # Remove 1978 because the data does not cover the entire year.
        try:
            years.remove(1978)
        except ValueError:
            pass

        # Remove the last year because the year is likely incomplete and will provide a misleading result.
        years = years[:-1]

        da_sliced_and_grouped = da.isel(time=da.time.dt.year.isin(years)).groupby('time.year')

        # Find the yearly max/min date, day of year, and index value.
        yearly_min_date = da_sliced_and_grouped.map(lambda x: x.idxmin(dim='time'))
        yearly_min_value = da_sliced_and_grouped.map(lambda x: x.min(dim='time'))

        yearly_max_date = da_sliced_and_grouped.map(lambda x: x.idxmax(dim='time'))
        yearly_max_value = da_sliced_and_grouped.map(lambda x: x.max(dim='time'))

        yearly_min_rank = yearly_min_value.rank('year')
        yearly_max_rank = yearly_max_value.rank('year')

        ds = ds.assign(yearly_min_date=yearly_min_date, yearly_min_value=yearly_min_value,
                       yearly_min_rank=yearly_min_rank, yearly_max_date=yearly_max_date,
                       yearly_max_value=yearly_max_value, yearly_max_rank=yearly_max_rank)

        ds['dayofyear'].attrs = {'long_name': 'Day of year',
                                 'coverage_content_type': 'auxiliaryInformation'}
        ds['year'].attrs = {'long_name': 'Year',
                            'coverage_content_type': 'auxiliaryInformation'}
        ds['yearly_min_date'].attrs = {'long_name': 'Yearly minimum date',
                                       'coverage_content_type': '',
                                       'comment': 'Date where minimum value occurs for given year.'}
        ds['yearly_min_value'].attrs = {'long_name': 'Yearly minimum value',
                                        'units': '1e6 km^2',
                                        'coverage_content_type': ''}
        ds['yearly_min_rank'].attrs = {'long_name': 'Yearly minimum rank',
                                       'coverage_content_type': '',
                                       'comment': 'Ties are delt with by assigning a rank that is the average of the '
                                                  'ranks that would have been otherwise assigned to all of the values '
                                                  'within that set.'}
        ds['yearly_max_date'].attrs = {'long_name': 'Yearly maximum date',
                                       'coverage_content_type': '',
                                       'comment': 'Date where maximum value occurs for given year.'}
        ds['yearly_max_value'].attrs = {'long_name': 'Yearly maximum value',
                                        'units': '1e6 km^2',
                                        'coverage_content_type': ''}
        ds['yearly_max_rank'].attrs = {'long_name': 'Yearly maximum rank',
                                       'coverage_content_type': '',
                                       'comment': 'Ties are delt with by assigning a rank that is the average of the '
                                                  'ranks that would have been otherwise assigned to all of the values '
                                                  'within that set.'}

        print(ds)

        # Writing netcdf.
        #encoding = {'dtype': 'int32', '_FillValue': -999}
        #ds.to_netcdf('test.nc', encoding={'dayofyear': encoding,
        #                                  'year': encoding,
        #                                  'rank': encoding,
        #                                  'min_per_doy': encoding,
        #                                  'max_per_doy': encoding,
        #                                  'yearly_min_date': encoding,
        #                                  'yearly_min_value': encoding,
        #                                  'yearly_min_rank': encoding,
        #                                  'yearly_max_date': encoding,
        #                                  'yearly_max_value': encoding,
        #                                  'yearly_max_rank': encoding})
