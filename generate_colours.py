import numpy as np
import matplotlib
from matplotlib import cm
import cmcrameri.cm as cmc
import xarray as xr
import itertools


ds = xr.open_dataset(f'https://thredds.met.no/thredds/dodsC/osisaf/met.no/ice/index/v2p2/nh/osisaf_nh_sie_daily.nc')
years = np.unique(ds.time.dt.year.values)

cmaps = [cm.viridis, cm.viridis_r, cm.plasma, cm.plasma_r, cmc.batlow, cmc.batlow_r, cmc.batlowS]
cmap_names = ['viridis', 'viridis_r', 'plasma', 'plasma_r', 'batlow', 'batlow_r', 'batlowS']

normalised = np.linspace(0, 1, len(years))

all_colours = []
for cmap in cmaps:
    colors = cmap(normalised)
    colors_in_hex = [matplotlib.colors.to_hex(color) for color in colors]
    all_colours.append(colors_in_hex)

# Cyclic_8
colors = ['#ffe119', '#4363d8', '#f58231', '#dcbeff', '#800000', '#000075', '#a9a9a9', '#000000']
cmap_names.append('cyclic_8')
cyc = itertools.cycle(colors)

all_colours.append([next(cyc) for year in years])

# Cyclic_17
colors = ['#e6194B', '#3cb44b', '#ffe119', '#4363d8', '#f58231', '#42d4f4', '#f032e6', '#fabed4', '#469990', '#dcbeff',
          '#9A6324', '#fffac8', '#800000', '#aaffc3', '#000075', '#a9a9a9', '#000000']
cmap_names.append('cyclic_17')
cyc = itertools.cycle(colors)

all_colours.append([next(cyc) for year in years])

decades = [1970, 1980, 1990, 2000, 2010, 2020]
cmaps = [cm.Purples_r, cm.Purples_r, cm.Blues_r, cm.Greens_r, cm.Reds_r, cm.Wistia_r]

decadal_colours = {}
for decade, colour in zip(decades, cmaps):
    normalisation = np.linspace(0, 0.5, 10)
    normalised_colour = [matplotlib.colors.to_hex(colour) for colour in colour(normalisation)]
    years_decade = np.arange(decade, decade + 10, 1)

    for year, colour_ in zip(years_decade, normalised_colour):
        decadal_colours[year] = colour_

cmap_names.append('decadal')
all_colours.append([decadal_colours[year] for year in years])

all_colours.insert(0, years)

stacked = np.column_stack(all_colours)

header = 'year,'
for name in cmap_names:
    header += f'{name},'

with open('data/daily/colours.csv', 'w') as f:
    f.write(header[:-1] + '\n')

    for i in range(stacked.shape[0]):
        row_vals = stacked[i, :]
        row = ''
        for col in row_vals:
            row += f'{col},'
        f.write(row[:-1] + '\n')
