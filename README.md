The following repository contains scripts that produce csv files that can be used to plot the daily plots of the sea ice index visualisation tool. The scripts that produce these files are listed below.

* **generate_all_clim.py**: generates files for the climatology (min/max per day of year, min/max per year, decadal climatology, and percentiles and median).
* **generate_all_daily.py**: generates files for the daily values (index values, dates, ranks).
* **generate_colours.py**: generates a file that contains precalculated hexadecimal values for the colours used in the plot.

The resulting csv files are stored the subdirectory `data/daily` under the current directory, with each geographical area receiving its own subdirectory.
