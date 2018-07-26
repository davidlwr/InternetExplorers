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
COMBINE_MOTIONS_THRESHOLD = 4 # in minutes
# total time between sensor detecting movement is MOTION_TIMEOUT_MINS + COMBINE_MOTIONS_THRESHOLD
# total time should be about the time the resident would spend in the toilet if s/he is staying inside for extended period of time

# initialize empty df
input_raw_data = pd.DataFrame()

# combine and read all data
for filename in os.listdir(file_folder):
    if filename.endswith('sensor.csv'):
        try:
            temp_df = pd.read_csv(file_folder + filename)
            input_raw_data = pd.concat([input_raw_data, temp_df], ignore_index=True)
        except:
            print('something wrong with ' + filename)

# convert datetime format
input_raw_data['gw_timestamp'] = pd.to_datetime(input_raw_data['gw_timestamp'], format='%Y-%m-%dT%H:%M:%S')

# convert timestamp to remove the extra time from sensor timeout
# only applicable for motion sensors
input_raw_data.loc[(input_raw_data.value==0)
		& (input_raw_data.reading_type=='motion'), 'gw_timestamp'] += datetime.timedelta(minutes=-MOTION_TIMEOUT_MINS)
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
default_sleep_start = datetime.time(22, 0)
default_sleep_end = datetime.time(6, 30)

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
        input_location='toilet_bathroom', gw_device=2005, time_period=None, offset=True,
        ignore_short_durations=False, min_duration=3, grouped=False):
    '''
    Function returns dates and aggregated number of times the sensor was activated
    To get day only, use time_period='Day' and to get night_only use time_period='Night'
    To report night numbers as the night of the previous day, use offset=True
    To ignore short durations, use ignore_short_durations=True, and set the minimum duration to be included using min_duration
    '''
    current_data = get_relevant_data(input_location, start_date, end_date, gw_device, grouped)
    if ignore_short_durations:
        duration_data = get_visit_duration_and_start_time(start_date, end_date, input_location, gw_device)
        current_data = pd.merge(current_data, duration_data, on=['gw_timestamp', 'value'])
        current_data.rename(columns={'value_x':'value'})
        current_data = current_data[current_data.visit_duration >= min_duration]
        # print(current_data)

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
def get_relevant_data(input_location, start_date, end_date, gw_device=2005, grouped=False):
    '''
    Retrieve sensor data based on location, start and end dates, and the device
    grouped=True to get grouped data for toilet visits
    '''
    # TODO: this part probably is the best to convert to retrieve from DB
    relevant_data = input_raw_data.loc[(input_raw_data['device_loc'] == input_location)
            & (input_raw_data['gw_timestamp'] < end_date)
            & (input_raw_data['gw_timestamp'] > start_date)
            & (input_raw_data['gw_device'] == gw_device), ['device_loc','gw_device','gw_timestamp', 'value']]

    # TODO: for sensors that are still active at the end of the query period, make it inactive at the end date
    relevant_data = input_sysmon.remove_disconnected_periods(relevant_data)

    # TODO: make grouping applicable for bedroom motion as well
    if grouped and ('toilet' in input_location):
        relevant_data = get_grouped_data(relevant_data)
    return relevant_data

# generate array for the different available locations
def get_location_options():
    locations = input_raw_data['uuid'].unique().tolist()
    output = []
    for i in range(len(locations)):
        if "m-01" in locations[i]:
            if "m-01" not in output:
                output.append("m-01")
        elif "m-02" in locations[i]:
            if "m-02" not in output:
                output.append("m-02")
        elif "d-01" in locations[i]:
            if "d-01" not in output:
                output.append("d-01")

    return output

# generate array for the different residents
def get_residents_options():
    return input_raw_data['gw_device'].unique().tolist()

# generate a table of acitivity durations indexed by the start time
def get_visit_duration_and_start_time(start_date=input_raw_min_date, end_date=input_raw_max_date,
        input_location='toilet_bathroom', gw_device=2005, grouped=False):
    '''
    Function returns a table of start times and the duration of activity detected at the specified location
    NOTE: If intending to group data, should call get_grouped_data first before calling this function
    '''
    current_data = get_relevant_data(input_location, start_date, end_date, gw_device, grouped)
    current_data['visit_duration'] = 0 # create new duration (in seconds) column

    # match the start and end timing of a sensor
    for i in range(0, len(current_data)-1):
        if current_data['value'].iloc[i] == 1:
            current_data['visit_duration'].iloc[i] = (current_data['gw_timestamp'].iloc[i+1] - current_data['gw_timestamp'].iloc[i]).total_seconds()

    # print(current_data.query('event != 0').reset_index(drop = True).head())
    # TODO: check that if a motion is cut off at the end of the query period the correct duration is reported (similar to check end and check start in get_average_longest_sleep)
    return current_data.query('value != 0').reset_index(drop = True)

def get_grouped_data(current_data, remove_all=False):
    '''
    Function removes inactivity durations that are under the timeout limit + the group threshold limit
    Will not remove two consecutive inactive periods by default, use remove_all=True to remove all inactive periods below the limit
    To be used before calculating number of visits
    Assumes that data is filtered to only one user and one location
    '''
    # loop through all rows and if row is to show inactivity, check that next record is for acitivity
    # get the duration between the two records
    # if below the thresholds, remove the two records
    current_data.reset_index(drop=True, inplace=True)
    # print(current_data)
    to_process = True # to track consecutive inactive periods
    current_data['todrop']=False
    for i in range(0, len(current_data)-1):
        if remove_all or to_process:
            if current_data['value'].iloc[i] == 0:
                if current_data['value'].iloc[i+1] == 1:
                    inactive_duration = current_data['gw_timestamp'].iloc[i+1] - current_data['gw_timestamp'].iloc[i]
                    if inactive_duration < datetime.timedelta(minutes=MOTION_TIMEOUT_MINS+COMBINE_MOTIONS_THRESHOLD):
                        current_data['todrop'].iloc[i]=True
                        current_data['todrop'].iloc[i+1]=True
                        to_process = False
                else: # error
                    # display error to console
                    print('check data - missing active (ON) reading:')
                    print(current_data['gw_timestamp'].iloc[i])
        else:
            if current_data['event'].iloc[i] == 0:
                to_process = True
    current_data = current_data[current_data.todrop == False]
    current_data.drop(columns=['todrop'], inplace=True)
    return current_data

#TODO store the cleaned data somewhere (file/database) so don't have to recalculate
#     each time we load the dashboard

# write to a file, uncomment to use, otherwise leave for implementation of some download/bootstrap function
# if __name__ == '__main__':
#     # loop through each possible user and location pair
#     to_file_data = pd.DataFrame()
#     for user in input_raw_data.gw_device.unique():
#         for location in input_raw_data.device_loc.unique():
#             to_file_data = pd.concat([to_file_data, get_relevant_data(location, input_raw_min_date, input_raw_max_date, user, grouped=True)], ignore_index=True)
#
#     to_file_data.to_csv("D:/FYP/Data/python_df_output.csv", index=False) # replace path with your own path

# separate method for moving averages so that moving average will always take advantage of the full range of data available
def get_visit_numbers_moving_average(gw_device, input_location='toilet_bathroom', time_period=None,
        offset=True, ignore_short_durations=False, min_duration=3, grouped=False, days=7, result_data=None):
    '''
    Run once to get the moving average of number of location visits based on the available parameters
    To get day only, use time_period='Day' and to get night_only use time_period='Night'
    To report night numbers as the night of the previous day, use offset=True
    To ignore short durations, use ignore_short_durations=True, and set the minimum duration to be included using min_duration
    Use days to indicate moving average window, default 7 for weekly
    Returns data with moving_average column
    '''
    if result_data is None:
        result_data = get_num_visits_by_date(gw_device=gw_device, input_location=input_location, time_period=time_period,
            offset=offset, ignore_short_durations=ignore_short_durations, min_duration=min_duration, grouped=grouped)
    # print(result_data)
    r = result_data['event'].rolling(window=days, min_periods=0)
    result_data['moving_average'] = r.mean()
    return result_data

def get_door_pivots(gw_device, input_location='bedroom_master'):
    '''
    Returns door timings with matched opening and closing
    '''
    raw_door_inputs = get_relevant_data(input_location='door', start_date=input_raw_min_date, end_date=input_raw_max_date, gw_device=gw_device)
    # pivot raw door inputs


    # after that loop through every door row and concat
    #+valid motion readings (based on each time the door is closed) together

def get_average_longest_sleep(gw_device, start_date, end_date, use_door=False):
    '''
    Get the average longest uninterrupted sleep duration (in seconds) per night as a measure of sleep quality
    NOTE: Intended usage is to be called weekly (called for each week, possibly excluding weekend nights) to analyse changes in sleep quality across weeks
    '''
    # TODO: consider dates where no data could be obtained - ignore in average calculations

    start_time = default_sleep_start
    end_time = default_sleep_end

    date_range = pd.date_range(start_date, end_date - datetime.timedelta(days=1))
    total_days = 0
    total_longest = 0 # in seconds

    current_data = get_relevant_data('bedroom_master', start_date, end_date + datetime.timedelta(days=1), gw_device, True)
    # group true so that motion close together is considered more significant, resulting in lower sleep quality (e.g. tossing in bed)
    #+NOTE: not implemented yet
    for single_date in date_range:
        if use_door:
            # TODO: use door to obtain the sleep start and end time
            #+but this is problematic because sometimes there are missing door data to correctly know sleeping hours
            start_time = default_sleep_start # replace with use door
            end_time = default_sleep_end # replace with use door

        total_days += 1
        # get latest reading before start
        temp_data = current_data[current_data.recieved_timestamp < datetime.datetime.combine(single_date, start_time)]
        # print(temp_data)
        last_active_value = temp_data.loc[temp_data['gw_timestamp'].idxmax()].value
        print("DEBUG: last active value", last_active_value)
        current_longest = 0
        night_data = current_data[(current_data.gw_timestamp > datetime.datetime.combine(single_date, start_time))
                & (current_data.gw_timestamp < datetime.datetime.combine(single_date + datetime.timedelta(days=1), end_time))]
        print(night_data)
        night_data.reset_index(drop=True, inplace=True)

        loop_start_index = 0
        loop_end_index = len(night_data) - 1

        # check start
        # check previous value first to see if there is currently motion or not at this point in time
        #+if yes, start adding the duration from start time
        if last_active_value == 0:
            # start counting duration right away
            for i in range(0, loop_end_index):
                if night_data['event'].iloc[i] == 1:
                    loop_start_index = i + 1
                    current_longest = (night_data['gw_timestamp'].iloc[i] - datetime.datetime.combine(single_date, start_time)).total_seconds()
                    print("see this once per day only")
                    break

        # else can just start counting from the next occurrence of 0
        # loop through each period of no motion
        for i in range(loop_start_index, loop_end_index):
            if night_data['value'].iloc[i] == 0:
                current_duration = (night_data['gw_timestamp'].iloc[i+1] - night_data['gw_timestamp'].iloc[i]).total_seconds()
                if current_duration > current_longest:
                    current_longest = current_duration

        # print("DEBUG: len(data)", night_data['gw_timestamp'].iloc[loop_end_index])
        #+range is exclusive for the 2nd argument

        #check end
        if night_data['value'].iloc[loop_end_index] == 0:
            current_duration = (datetime.datetime.combine(single_date + datetime.timedelta(days=1), end_time) - night_data['gw_timestamp'].iloc[loop_end_index]).total_seconds()
            if current_duration > current_longest:
                current_longest = current_duration
        print("DEBUG: current longest", current_longest)
        total_longest += current_longest

    print("DEBUG: total_days", total_days)
    average_longest = total_longest / total_days # in seconds
    return average_longest

# NOTE: bedroom motion that last 1 second at night may just mean the resident rolling in bed
#+unless they occur in quick succession then that may mean inability to sleep
#+otherwise should ignore

def motion_duration_during_sleep(gw_device, start_date, end_date, use_door=False):
    '''
    Get the average total motion duration detected during sleep as a measure of sleep quality
    NOTE: Intended to be used weekly (called for each week, possibly excluding weekend nights) to analyse changes in sleep quality across weeks
    '''
    # NOTE: can easily reprogram to give average sleep non-motion if required
    start_time = default_sleep_start
    end_time = default_sleep_end

    date_range = pd.date_range(start_date, end_date - datetime.timedelta(days=1))
    total_days = 0
    total_motion_aggregated = 0

    current_data = get_relevant_data('bedroom_master', start_date, end_date + datetime.timedelta(days=1), gw_device, True)
    # group true so that motion close together is considered more significant, resulting in lower sleep quality (e.g. tossing in bed)
    #+NOTE: not implemented yet

    # for each day, get visit duration and sum up total motion duration
    #+then get the average amongst all the days
    #+this can be used for each week to update the stats on overview page
    for single_date in date_range:
        if use_door:
            # TODO: use door to obtain the sleep start and end time
            #+but this is problematic because sometimes there are missing door data to correctly know sleeping hours
            start_time = default_sleep_start # replace with use door
            end_time = default_sleep_end # replace with use door

        total_days += 1
        total_motion_daily = 0

        # get latest reading before start
        temp_data = current_data[current_data.recieved_timestamp < datetime.datetime.combine(single_date, start_time)]
        # print(temp_data)
        last_active_value = temp_data.loc[temp_data['gw_timestamp'].idxmax()].value
        print("DEBUG: last active value", last_active_value)

        night_data = current_data[(current_data.gw_timestamp > datetime.datetime.combine(single_date, start_time))
                & (current_data.gw_timestamp < datetime.datetime.combine(single_date + datetime.timedelta(days=1), end_time))]
        print(night_data)
        night_data.reset_index(drop=True, inplace=True)

        loop_start_index = 0
        loop_end_index = len(night_data) - 1

        # check start
        if last_active_value == 1:
            for i in range(0, loop_end_index):
                if night_data['event'].iloc[i] == 0:
                    loop_start_index = i + 1
                    total_motion_daily += (night_data['gw_timestamp'].iloc[i] - datetime.datetime.combine(single_date, start_time)).total_seconds()
                    print("see this once per day only")
                    break

        # loop through each period of motion
        for i in range(loop_start_index, loop_end_index):
            if night_data['value'].iloc[i] == 1:
                total_motion_daily += (night_data['gw_timestamp'].iloc[i+1] - night_data['gw_timestamp'].iloc[i]).total_seconds()

        # check end
        if night_data['value'].iloc[loop_end_index] == 1:
            total_motion_daily += (datetime.datetime.combine(single_date + datetime.timedelta(days=1), end_time) - night_data['gw_timestamp'].iloc[loop_end_index]).total_seconds()
        print("DEBUG: daily total motion", total_motion_daily)
        total_motion_aggregated += total_motion_daily

    average_motion = total_motion_aggregated / total_days
    return average_motion
    # TODO: can replace this to be as a percentage of sleeping hours
# below for testing only
if __name__ == '__main__':
    # testing_data = get_relevant_data('toilet_bathroom', input_raw_min_date, input_raw_max_date)
    # testing_data = input_sysmon.remove_disconnected_periods(testing_data)

    # test to check that final data has all 1's followed by 0's
    # testing_data = get_grouped_data(testing_data)

    # test rolling means
    # rolling_data = get_visit_numbers_moving_average(2005, days=21)
    # print(rolling_data)
    # print(testing_data)

    # test average longest uninterrupted sleep
    # result = get_average_longest_sleep(2005, datetime.date(2018, 5, 1), datetime.date(2018, 5, 3))
    # print("result", result)

    # test average motion duration during sleep
    result = motion_duration_during_sleep(2005, datetime.date(2018, 5, 1), datetime.date(2018, 5, 3))
    print("result", result)
