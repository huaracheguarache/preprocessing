import numpy as np
import xarray as xr
from pathlib import Path


def generate_csv(da, da_interpolated, path):
    # Calculate the rank per day of year.
    rank = da_interpolated.groupby('time.dayofyear').map(lambda x: x.rank('time'))

    # Create the individual rows for the csv file.
    years = np.unique(da.time.dt.year.values).astype(str)
    times = []
    values = []
    dates = []
    ranks = []
    for year in years:
        subset = da.sel(time=year)
        times.append(subset.time.dt.dayofyear.values)
        values.append(subset.values)
        dates.append(subset.time.dt.strftime('%Y-%m-%d').values)
        ranks.append(rank.sel(time=subset.time.values).values)

    rows = []
    for doy in range(1, 367):
        row = f'{doy},'
        for time, value, date, rank in zip(times, values, dates, ranks):
            index = np.argwhere(time == doy)
            if index.size > 0:
                row += f'{value[index.flat[0]]},{date[index.flat[0]]},{rank[index.flat[0]]},'
            else:
                row += ',,,'

        # Append the result and make sure to remove the last comma the get the correct amount of columns.
        rows.append(row[:-1])

    # Add a header.
    header = 'doy,'
    for year in years:
        header += f'{year}_vals,{year}_date,{year}_rank,'

    # Insert the header without the last comma.
    rows.insert(0, header[:-1])

    with open(path, 'w') as f:
        for row in rows:
            f.write(row + '\n')


if __name__ == '__main__':
    indices = ['sie', 'sia']
    areas = ['glb', 'nh', 'sh', 'bar', 'beau', 'chuk', 'ess', 'fram', 'kara', 'lap', 'sval', 'bell', 'drml', 'indi',
             'ross', 'trol', 'wedd', 'wpac']
    ref_periods = (('1981', '2010'), ('1991', '2020'))

    for area in areas:
        for index in indices:
            print(f'{area}:{index}')
            path = Path(f'data/daily/{area}')
            path.mkdir(parents=True, exist_ok=True)

            ds = xr.open_dataset(f'https://thredds.met.no/thredds/dodsC/osisaf/met.no/ice/index/v2p2/{area}/'
                                 f'osisaf_{area}_{index}_daily.nc')
            da = ds[index]
            da_converted = da.convert_calendar('all_leap')

            da_interpolated = da.convert_calendar('all_leap', missing=-999)
            for i, val in enumerate(da_interpolated.values):
                # Replace the -999 values with interpolated values between the preceding and succeeding day.
                if val == -999:
                    da_interpolated.values[i] = (da_interpolated.values[i - 1] + da_interpolated.values[i + 1]) / 2

            generate_csv(da_converted, da_interpolated, path / f'{index}_abs.csv')

            for start, end in ref_periods:
                mean = da_interpolated.sel(time=slice(start, end)).groupby('time.dayofyear').mean()
                anomaly_interpolated = da_interpolated.groupby('time.dayofyear') - mean
                anomaly_converted = da_converted.groupby('time.dayofyear') - mean

                generate_csv(anomaly_converted, anomaly_interpolated, path / f'{index}_anom_{start}_{end}.csv')
