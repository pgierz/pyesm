import numpy as np

from pyesm.core.time_control.esm_calendar import Date

time_array = np.empty((24, 1))
time_bounds_array = np.empty((24, 2))

date1 = Date("1850-01-01")
date2 = Date("1851-01-01")
end_day = 0

for year_number, date in enumerate([date1, date2]):
    for index, month in enumerate(date._calendar.monthnames):
        index += year_number * 12
        length_of_this_month = date._calendar.day_in_month(date.year, month)
        end_day += length_of_this_month
        middle_day = end_day - (length_of_this_month / 2)
        start_day = 1 + end_day - length_of_this_month
        time_array[index] = middle_day
        time_bounds_array[index, 0], time_bounds_array[index, 1] = start_day, end_day

print(time_array)
print(time_bounds_array)
