import pandas as pd
import numpy as np
import datetime
import os

# pandas settings
pd.options.mode.chained_assignment = None  # default='warn

if __name__ == '__main__': # we want to import from same directory if using this
						   # module as-is (for debugging mainly, or for loading data in the future)
	import input_sysmon
else: # if called from index.py
	from apps import input_sysmon

# specify file parameters
file_folder = '../stbern-20180302-20180523-csv/'
file_name = '2018-03-02-2005-sensor.csv'
MOTION_TIMEOUT_MINS = 4 # in minutes

# initialize empty df
input_raw_data = pd.DataFrame()

# combine and read all data
for filename in os.listdir(file_folder):
    if filename.endswith('sensor.csv'):
        try:
            temp_df = pd.read_csv(file_folder + filename)
            input_raw_data = pd.concat([input_raw_data, temp_df])
        except:
            print('something wrong with ' + filename)

# convert datetime format
input_raw_data['gw_timestamp'] = pd.to_datetime(input_raw_data['gw_timestamp'], format='%Y-%m-%dT%H:%M:%S')

# convert timestamp to remove the extra time from sensor timeout
# only applicable for motion sensors
input_raw_data.loc[(input_raw_data.value==0)
		& (input_raw_data.reading_type=='motion'), 'gw_timestamp'] += datetime.timedelta(minutes=-4)
# print(input_raw_data.head())

#convert values to 1 and 0 instead of 255
input_raw_data.loc[:, 'value'].replace(255, 1, inplace=True)

# common variables
input_raw_max_date = input_raw_data['gw_timestamp'].max()
input_raw_min_date = input_raw_data['gw_timestamp'].min()
# print(input_raw_data.head())
# print(input_raw_data.info())
# print(input_raw_data.index.values)

# parameters for day and night timing
# In this case daytime refers to the current date's daytime, while nighttime
# refers to the current date's night till the next date's morning
daytime_start = datetime.time(6, 30)
daytime_end = datetime.time(21, 30)
# below is redundant
nighttime_start = daytime_end
nighttime_end = daytime_start

# replace date to be date only
def date_only(original_date):
    return original_date.replace(hour=0, minute=0, second=0, microsecond=0)

# generate array for the different filtering options
def get_num_visits_filter_options():
    '''Returns labels and values in an array of tuples'''
    return [('No Day/Night Filter', 'None'), ('Day Only', 'Day'), ('Night Only', 'Night'), ('Both Day and Night', 'Both')]

### find out number of times activated by date
# first mark all 'activation points', index dependent on raw data input
def get_num_visits_by_date(start_date=input_raw_min_date, end_date=input_raw_max_date,
        input_location='toilet_bathroom', gw_device=2005, time_period=None, offset=True):
    '''
    Function returns dates and aggregated number of times the sensor was activated
    To get day only, use time_period='Day' and to get night_only use time_period='Night'
    To report night numbers as the night of the previous day, use offset=True
    '''
    current_data = get_relevant_data(input_location, start_date, end_date, gw_device)

    if time_period == 'Day':
        current_data = current_data.loc[(current_data['gw_timestamp'].dt.time >= daytime_start)
                & (current_data['gw_timestamp'].dt.time < daytime_end)]
    elif time_period == 'Night':
        current_data = current_data.loc[(current_data['gw_timestamp'].dt.time < daytime_start)
                | (current_data['gw_timestamp'].dt.time > daytime_end)]
        if offset:
            # shift the date of those at night to be one day before
            current_data['gw_timestamp'] = np.where(current_data['gw_timestamp'].dt.time < daytime_start,
                    current_data['gw_timestamp'] - datetime.timedelta(days=1), current_data['gw_timestamp'])

    # group by date only
    current_data['gw_date_only'] = current_data['gw_timestamp'].apply(date_only)
    result_data = current_data.groupby(['gw_date_only'], as_index=False)['value'].sum()
    return result_data

# method to get the relevant columns of data
def get_relevant_data(input_location, start_date, end_date, gw_device=2005):
    relevant_data = input_raw_data.loc[(input_raw_data['device_loc'] == input_location)
            & (input_raw_data['gw_timestamp'] < end_date)
            & (input_raw_data['gw_timestamp'] > start_date)
            & (input_raw_data['gw_device'] == gw_device), ['device_loc','gw_device','gw_timestamp', 'value']]
    return relevant_data

# generate array for the different available locations
def get_location_options():
    return input_raw_data['device_loc'].unique().tolist()

# generate array for the different residents
def get_residents_options():
    return input_raw_data['gw_device'].unique().tolist()

# generate a table of acitivity durations indexed by the start time
def get_visit_duration_and_start_time(start_date=input_raw_min_date, end_date=input_raw_max_date,
        input_location='toilet_bathroom', gw_device=2005):
    '''
    Function returns a table of start times and the duration of activity detected at the specified location
    '''
    current_data = get_relevant_data(input_location, start_date, end_date, gw_device)
    current_data['visit_duration'] = 0 # create new duration (in seconds) column

    # match the start and end timing of a sensor
    for i in range(0, len(current_data)-1):
        if current_data['value'].iloc[i] == 1:
            current_data['visit_duration'].iloc[i] = (current_data['gw_timestamp'].iloc[i+1] - current_data['gw_timestamp'].iloc[i]).total_seconds()

    # print(current_data.query('value != 0').reset_index(drop = True).head())
    return current_data.query('value != 0').reset_index(drop = True)

#TODO store the cleaned data somewhere (file/database) so don't have to recalculate
#     each time we load the dashboard

# below for testing only
# if __name__ == '__main__':
#     get_num_visits_by_date(time_period='Night', offset=True)
