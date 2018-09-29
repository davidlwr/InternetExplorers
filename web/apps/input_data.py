import sys
import pandas as pd
import numpy as np
import datetime
import os
import scipy.stats
import dill

# pandas settings
pd.options.mode.chained_assignment = None  # default='warn

if __name__ == '__main__':  # we want to import from same directory if using this
    # module as-is (for debugging mainly, or for loading data in the future)
    sys.path.append(".")
    import input_sysmon
    from DAOs.sensor_log_DAO import sensor_log_DAO
    from juvo_api import JuvoAPI
else:  # if called from index.py
    from apps import input_sysmon
    from DAOs.sensor_log_DAO import sensor_log_DAO
    from juvo_api import JuvoAPI

# specify file parameters
file_folder = '../stbern-20180302-20180523-csv/'
file_name = '2018-03-02-2005-sensor.csv'
MOTION_TIMEOUT_MINS = 4  # in minutes
COMBINE_MOTIONS_THRESHOLD = 4  # in minutes
# total time between sensor detecting movement is MOTION_TIMEOUT_MINS + COMBINE_MOTIONS_THRESHOLD
# total time should be about the time the resident would spend in the toilet if s/he is staying inside for extended period of time

# initialize empty df
input_raw_data = pd.DataFrame()
input_raw_data = sensor_log_DAO.get_all_logs()

# combine and read all data
# for filename in os.listdir(file_folder):
#     if filename.endswith('sensor.csv'):
#         try:
#             temp_df = pd.read_csv(file_folder + filename)
#             input_raw_data = pd.concat([input_raw_data, temp_df], ignore_index=True)
#         except:
#             print('something wrong with ' + filename)

#convert datetime format
input_raw_data['recieved_timestamp'] = pd.to_datetime(input_raw_data['recieved_timestamp'], format='%Y-%m-%dT%H:%M:%S')

# convert timestamp to remove the extra time from sensor timeout
# only applicable for motion sensors
input_raw_data.loc[(input_raw_data.event == 0)
                   & (input_raw_data.uuid.str.contains("-m-")), 'recieved_timestamp'] += datetime.timedelta(minutes=-MOTION_TIMEOUT_MINS)
# print(input_raw_data.head())

# convert events to 1 and 0 instead of 255
input_raw_data.loc[:, 'event'].replace(255, 1, inplace=True)

# common variables
input_raw_max_date = input_raw_data['recieved_timestamp'].max()
input_raw_min_date = input_raw_data['recieved_timestamp'].min()
# print(input_raw_data.head())
# print(input_raw_data.info())
# print(input_raw_data.index.values)

# parameters for day and night timing
# In this case daytime refers to the current date's daytime, while nighttime
# refers to the current date's night till the next date's morning
daytime_start = datetime.time(6, 30)
daytime_end = datetime.time(22, 30)
# below is redundant
nighttime_start = daytime_end
nighttime_end = daytime_start
default_sleep_start = datetime.time(22, 30)
default_sleep_end = datetime.time(6, 30)
para_ratio_threshold_default = 0.3  # changeable: if night usage is higher than this ratio of total usage, alert
                                    # here we use number of toilet visits as a proxy for urinal volume
                                    # nocturnal bladder capacity is usually higher than in the day, so if the amount
                                    #+is really that high, nocturia index is much likely to be that high
                                    # can be customised based on different patients and estimated nocturnal bladder capacity

def updateInputData():
    input_raw_data = sensor_log_DAO.get_all_logs()

def get_para_ratio_threshold():
    return para_ratio_threshold_default

# replace date to be date only
def date_only(original_date):
    return original_date.replace(hour=0, minute=0, second=0, microsecond=0)


# generate array for the different filtering options
def get_num_visits_filter_options():
    '''Returns labels and values in an array of tuples'''
    return [('No Day/Night Filter', 'None'), ('Day Only', 'Day'), ('Night Only', 'Night'),
            ('Both Day and Night', 'Both')]


### find out number of times activated by date
# first mark all 'activation points', index dependent on raw data input
def get_num_visits_by_date(start_date=input_raw_min_date, end_date=input_raw_max_date,
                           input_location='m-02', node_id=2005, time_period=None, offset=True,
                           ignore_short_durations=False, min_duration=3, grouped=False):
    """
    Function returns dates and aggregated number of times the sensor was activated
    To get day only, use time_period='Day' and to get night_only use time_period='Night'
    To report night numbers as the night of the previous day, use offset=True
    To ignore short durations, use ignore_short_durations=True, and set the minimum duration to be included using min_duration
    """

    # NOTE: last day of the returned output is not accurate if offset is used because the next day's data is needed to get the current night's data
    current_data = get_relevant_data(input_location, start_date, end_date, node_id, grouped)
    # print(current_data)

    if ignore_short_durations:
        duration_data = get_visit_duration_and_start_time(start_date, end_date, input_location, node_id)
        current_data = pd.merge(current_data, duration_data, on=['recieved_timestamp', 'event'])
        current_data.rename(columns={'event_x': 'event'})
        # print(current_data)
        current_data = current_data[current_data.visit_duration >= min_duration]

    # print(current_data)
    if time_period == 'Day':
        current_data = current_data.loc[(current_data['recieved_timestamp'].dt.time >= daytime_start)
                                        & (current_data['recieved_timestamp'].dt.time < daytime_end)]
    elif time_period == 'Night':
        current_data = current_data.loc[(current_data['recieved_timestamp'].dt.time < daytime_start)
                                        | (current_data['recieved_timestamp'].dt.time > daytime_end)]
        if offset:
            # shift the date of those at night to be one day before
            current_data['recieved_timestamp'] = np.where(current_data['recieved_timestamp'].dt.time < daytime_start,
                                                          current_data['recieved_timestamp'] - datetime.timedelta(days=1),
                                                          current_data['recieved_timestamp'])

    # group by date only
    current_data['gw_date_only'] = current_data['recieved_timestamp'].apply(date_only)
    result_data = current_data.groupby(['gw_date_only'], as_index=False)['event'].sum()

    if time_period == 'Night' and offset:
        # here means the morning of the first day is not needed
        result_data = result_data.iloc[1:]
        result_data.reset_index(drop=True, inplace=True)

    # add 0 for days with no data
    result_data.set_index('gw_date_only', inplace=True)
    if isinstance(start_date, str):
        start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d')

    if isinstance(end_date, str):
        end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d')

    all_days_range = pd.date_range(start_date.date(), end_date.date() + datetime.timedelta(days=-1), freq='D')
    try:
        result_data = result_data.loc[all_days_range]
    except KeyError as e:
        erroroutput = pd.DataFrame()
        erroroutput['event'] = []
        erroroutput['gw_date_only'] = []
    # result_data.fillna(0, inplace=True)

    # undo set index
    result_data.reset_index(inplace=True)
    result_data.rename(columns={'index':'gw_date_only'}, inplace=True)
    # print("result data from get_num_visits_by_date\n", result_data)
    return result_data


# method to get the relevant columns of data
def get_relevant_data(input_location, start_date, end_date, node_id=2005, grouped=False):
    '''
    Retrieve sensor data based on location, start and end dates, and the device
    grouped=True to get grouped data for toilet visits
    '''
    # TODO: this part probably is the best to convert to retrieve from DB
    relevant_data = input_raw_data.loc[(input_raw_data['uuid'].str.endswith(input_location))
                                       & (input_raw_data['recieved_timestamp'] < end_date)
                                       & (input_raw_data['recieved_timestamp'] > start_date)
                                       & (input_raw_data['node_id'] == node_id), ['uuid', 'node_id',
                                                                                  'recieved_timestamp', 'event']]


    # TODO: for sensors that are still active at the end of the query period, make it inactive at the end date
    relevant_data = input_sysmon.remove_disconnected_periods(relevant_data)

    # TODO: make grouping applicable for bedroom motion as well
    if grouped and ('m-02' in input_location):
        relevant_data = get_grouped_data(relevant_data)
    return relevant_data


# generate array for the different available locations
def get_location_options():
    locations = input_raw_data['uuid'].unique().tolist()
    output = {}
    for i in range(len(locations)):
        if "m-01" in locations[i]:
            if "Bedroom" not in output:
                output["Bedroom"] = "m-01"
        elif "m-02" in locations[i]:
            if "Toilet" not in output:
                output["Toilet"] = "m-02"
        elif "d-01" in locations[i]:
            if "Door" not in output:
                output["Door"] = "d-01"

    return output


# generate array for the different residents
def get_residents_options():
    return input_raw_data['node_id'].unique().tolist()


# generate a table of acitivity durations indexed by the start time
def get_visit_duration_and_start_time(start_date=input_raw_min_date, end_date=input_raw_max_date,
                                      input_location='m-02', node_id=2005, grouped=False):
    '''
    Function returns a table of start times and the duration of activity detected at the specified location
    NOTE: If intending to group data, should call get_grouped_data first before calling this function
    '''
    current_data = get_relevant_data(input_location, start_date, end_date, node_id, grouped)
    current_data['visit_duration'] = 0  # create new duration (in seconds) column

    # match the start and end timing of a sensor
    for i in range(0, len(current_data) - 1):
        if current_data['event'].iloc[i] == 1:
            current_data['visit_duration'].iloc[i] = (current_data['recieved_timestamp'].iloc[i + 1] - current_data['recieved_timestamp'].iloc[i]).total_seconds()

    # print(current_data.query('event != 0').reset_index(drop = True).head())
    # TODO: check that if a motion is cut off at the end of the query period the correct duration is reported (similar to check end and check start in get_average_longest_sleep)
    return current_data.query('event != 0').reset_index(drop=True)


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
    to_process = True  # to track consecutive inactive periods
    current_data['todrop'] = False
    for i in range(0, len(current_data) - 1):
        if remove_all or to_process:
            if current_data['event'].iloc[i] == 0:
                if current_data['event'].iloc[i + 1] == 1:
                    inactive_duration = current_data['recieved_timestamp'].iloc[i + 1] - \
                                        current_data['recieved_timestamp'].iloc[i]
                    if inactive_duration < datetime.timedelta(minutes=MOTION_TIMEOUT_MINS + COMBINE_MOTIONS_THRESHOLD):
                        current_data['todrop'].iloc[i] = True
                        current_data['todrop'].iloc[i + 1] = True
                        to_process = False
                else:  # error
                    # display error to console
                    # print('check data - missing active (ON) reading:')
                    # print(current_data['recieved_timestamp'].iloc[i])
                    pass
        else:
            if current_data['event'].iloc[i] == 0:
                to_process = True
    current_data = current_data[current_data.todrop == False]
    current_data.drop(columns=['todrop'], inplace=True)
    return current_data


# TODO store the cleaned data somewhere (file/database) so don't have to recalculate
#     each time we load the dashboard

# write to a file, uncomment to use, otherwise leave for implementation of some download/bootstrap function
# if __name__ == '__main__':
#     # loop through each possible user and location pair
#     to_file_data = pd.DataFrame()
#     for user in input_raw_data.node_id.unique():
#         for location in input_raw_data.device_loc.unique():
#             to_file_data = pd.concat([to_file_data, get_relevant_data(location, input_raw_min_date, input_raw_max_date, user, grouped=True)], ignore_index=True)
#
#     to_file_data.to_csv("D:/FYP/Data/python_df_output.csv", index=False) # replace path with your own path

# separate method for moving averages so that moving average will always take advantage of the full range of data available
def get_visit_numbers_moving_average(node_id, input_location='m-02', time_period=None,
                                     offset=True, ignore_short_durations=False, min_duration=3, grouped=False, days=7,
                                     result_data=None):
    '''
    Run once to get the moving average of number of location visits based on the available parameters
    To get day only, use time_period='Day' and to get night_only use time_period='Night'
    To report night numbers as the night of the previous day, use offset=True
    To ignore short durations, use ignore_short_durations=True, and set the minimum duration to be included using min_duration
    Use days to indicate moving average window, default 7 for weekly
    Returns data with moving_average column
    '''
    if result_data is None:
        result_data = get_num_visits_by_date(node_id=node_id, input_location=input_location,
                                             time_period=time_period,
                                             offset=offset, ignore_short_durations=ignore_short_durations,
                                             min_duration=min_duration, grouped=grouped)
    # print(result_data)

    r = result_data['event'].rolling(window=days, min_periods=0)
    # print(r)
    output_data = result_data.copy(deep=True)
    output_data['moving_average'] = r.mean()
    return output_data


def get_door_pivots(node_id, input_location='d-01'):
    '''
    Returns door timings with matched opening and closing
    NOTE: not implemented yet
    '''
    raw_door_inputs = get_relevant_data(input_location=input_location, start_date=input_raw_min_date,
                                        end_date=input_raw_max_date, node_id=node_id)
    # pivot raw door inputs

    # after that loop through every door row and concat
    # +valid motion readings (based on each time the door is closed) together


def get_average_longest_sleep(node_id, start_date, end_date, use_door=False):
    '''
    Get the average longest uninterrupted sleep duration (in seconds) per night as a measure of sleep quality
    NOTE: Intended usage is to be called weekly (called for each week, possibly excluding weekend nights) to analyse changes in sleep quality across weeks
    '''
    # TODO: consider dates where no data could be obtained - ignore in average calculations
    # TODO: consider returning tuple with SD as well

    start_time = default_sleep_start
    end_time = default_sleep_end

    # strip time information from input datetime
    # start_date = start_date.date()
    # end_date = end_date.date()

    date_range = pd.date_range(start_date, end_date - datetime.timedelta(days=1))
    total_days = 0
    total_longest = 0  # in seconds

    current_data = get_relevant_data('m-01', start_date, end_date + datetime.timedelta(days=1), node_id,
                                     True)
    # group true so that motion close together is considered more significant, resulting in lower sleep quality (e.g. tossing in bed)
    # +NOTE: not implemented yet
    for single_date in date_range:
        if use_door:
            # TODO: use door to obtain the sleep start and end time
            # +but this is problematic because sometimes there are missing door data to correctly know sleeping hours
            start_time = default_sleep_start  # replace with use door
            end_time = default_sleep_end  # replace with use door

        total_days += 1
        # get latest reading before start
        temp_data = current_data[current_data.recieved_timestamp < datetime.datetime.combine(single_date, start_time)]
        # print(temp_data)
        try:
            last_active_value = temp_data.loc[temp_data['recieved_timestamp'].idxmax()].event
        except ValueError as e:
            return 0
        # print("DEBUG: last active value", last_active_value)
        current_longest = 0
        night_data = current_data[(current_data.recieved_timestamp > datetime.datetime.combine(single_date, start_time))
                                  & (current_data.recieved_timestamp < datetime.datetime.combine(
            single_date + datetime.timedelta(days=1), end_time))]
        # print(night_data)
        night_data.reset_index(drop=True, inplace=True)

        loop_start_index = 0
        loop_end_index = len(night_data) - 1

        # check start
        # check previous value first to see if there is currently motion or not at this point in time
        # +if yes, start adding the duration from start time
        if last_active_value == 0:
            # start counting duration right away
            for i in range(0, loop_end_index):
                if night_data['event'].iloc[i] == 1:
                    loop_start_index = i + 1
                    current_longest = (night_data['recieved_timestamp'].iloc[i] - datetime.datetime.combine(single_date,
                                                                                                            start_time)).total_seconds()
                    # print("see this once per day only")
                    break

        # else can just start counting from the next occurrence of 0
        # loop through each period of no motion
        for i in range(loop_start_index, loop_end_index):
            if night_data['event'].iloc[i] == 0:
                current_duration = (
                        night_data['recieved_timestamp'].iloc[i + 1] - night_data['recieved_timestamp'].iloc[
                    i]).total_seconds()
                if current_duration > current_longest:
                    current_longest = current_duration

        # print("DEBUG: len(data)", night_data['recieved_timestamp'].iloc[loop_end_index])
        # +range is exclusive for the 2nd argument

        # check end
        if loop_end_index >= 0 and night_data['event'].iloc[loop_end_index] == 0:
            current_duration = (datetime.datetime.combine(single_date + datetime.timedelta(days=1), end_time) -
                                night_data['recieved_timestamp'].iloc[loop_end_index]).total_seconds()
            if current_duration > current_longest:
                current_longest = current_duration
        # print("DEBUG: current longest", current_longest)
        total_longest += current_longest

    # print("DEBUG: total_days", total_days)
    average_longest = total_longest / total_days  # in seconds
    return average_longest


# NOTE: bedroom motion that last 1 second at night may just mean the resident rolling in bed
# +unless they occur in quick succession then that may mean inability to sleep
# +otherwise should ignore

def motion_duration_during_sleep(node_id, start_date, end_date, use_door=False):
    '''
    Get the average total motion duration detected (in seconds) during sleep as a measure of sleep quality
    NOTE: Intended to be used weekly (called for each week, possibly excluding weekend nights) to analyse changes in sleep quality across weeks
    '''
    # NOTE: can easily reprogram to give average sleep non-motion if required
    start_time = default_sleep_start
    end_time = default_sleep_end

    date_range = pd.date_range(start_date, end_date - datetime.timedelta(days=1))
    total_days = 0
    total_motion_aggregated = 0

    # strip time information from input datetime
    # start_date = start_date.date()
    # end_date = end_date.date()

    current_data = get_relevant_data('m-01', start_date, end_date + datetime.timedelta(days=1), node_id, True)
    # group true so that motion close together is considered more significant, resulting in lower sleep quality (e.g. tossing in bed)
    # +NOTE: not implemented yet

    # for each day, get visit duration and sum up total motion duration
    # +then get the average amongst all the days
    # +this can be used for each week to update the stats on overview page
    for single_date in date_range:
        if use_door:
            # TODO: use door to obtain the sleep start and end time
            # +but this is problematic because sometimes there are missing door data to correctly know sleeping hours
            start_time = default_sleep_start  # replace with use door
            end_time = default_sleep_end  # replace with use door

        total_days += 1
        total_motion_daily = 0

        # get latest reading before start
        temp_data = current_data[current_data.recieved_timestamp < datetime.datetime.combine(single_date, start_time)]
        # print(single_date, temp_data)
        try:
            last_active_value = temp_data.loc[temp_data['recieved_timestamp'].idxmax()].event
        except ValueError as e:
            return 0
        # print("DEBUG: last active value", last_active_value)

        night_data = current_data[(current_data.recieved_timestamp > datetime.datetime.combine(single_date, start_time))
                                  & (current_data.recieved_timestamp < datetime.datetime.combine(
            single_date + datetime.timedelta(days=1), end_time))]
        # print(night_data)
        night_data.reset_index(drop=True, inplace=True)

        loop_start_index = 0
        loop_end_index = len(night_data) - 1

        # check start
        if last_active_value == 1:
            for i in range(0, loop_end_index):
                if night_data['event'].iloc[i] == 0:
                    loop_start_index = i + 1
                    total_motion_daily += (
                            night_data['recieved_timestamp'].iloc[i] - datetime.datetime.combine(single_date,
                                                                                                 start_time)).total_seconds()
                    # print("see this once per day only")
                    break

        # loop through each period of motion
        for i in range(loop_start_index, loop_end_index):
            if night_data['event'].iloc[i] == 1:
                total_motion_daily += (
                        night_data['recieved_timestamp'].iloc[i + 1] - night_data['recieved_timestamp'].iloc[
                    i]).total_seconds()

        # check end
        # print("DEBUG", loop_end_index)
        if loop_end_index >= 0 and night_data['event'].iloc[loop_end_index] == 1:
            total_motion_daily += (datetime.datetime.combine(single_date + datetime.timedelta(days=1), end_time) -
                                   night_data['recieved_timestamp'].iloc[loop_end_index]).total_seconds()
        # print("DEBUG: daily total motion", total_motion_daily)
        total_motion_aggregated += total_motion_daily

    average_motion = total_motion_aggregated / total_days
    return average_motion
    # TODO: can replace this to be as a percentage of sleeping hours

def get_nightly_sleep_indicator(user_id, current_sys_time=None):
    '''
    Returns (1) the list of alerts of interest, (2) the past week's average duration of motion during sleep
            and (3) the difference between motion during sleep in the past week versus the previous 3 weeks
            and (4) the average longest uninterrupted sleep for the past week (in seconds)
            and (5) the difference between average longest uninterrupted sleep for the past week versus the previous 3 weeks
            and (6) the average quality of sleep from juvo
            and (7) the past week's quality of sleep as df
    '''
    alerts_of_interest = [] # add alerts here, can use in the next layer to priortise things to show also
    if current_sys_time is None: # used in testing - pass in a different time for simulation
        current_sys_time = datetime.datetime.now()

    juvo_date_in_use = datetime.datetime(2018, 8, 12, 23, 34, 12)

    current_sys_date = current_sys_time.date()
    three_weeks_ago = current_sys_date + datetime.timedelta(days=-21)
    one_week_ago = current_sys_date + datetime.timedelta(days=-7)
    four_weeks_ago = current_sys_date + datetime.timedelta(days=-28)

    # 1st check
    # get previous 3 weeks average motion first, then take the past week's
    old_three_average = motion_duration_during_sleep(user_id, four_weeks_ago, one_week_ago)
    past_week_average = motion_duration_during_sleep(user_id, one_week_ago, current_sys_time)
    difference = past_week_average - old_three_average
    if difference > old_three_average * 0.5: # NOTE: changeable here
        alerts_of_interest.append("Increased movements during sleeping hours, likely having more segmented sleep")

    # 2nd check
    old_three_longest_sleep_average = get_average_longest_sleep(user_id, four_weeks_ago, one_week_ago)
    past_week_longest_sleep_average = get_average_longest_sleep(user_id, one_week_ago, current_sys_time)
    difference_longest_sleep = past_week_longest_sleep_average - old_three_longest_sleep_average
    if difference_longest_sleep < -.75 * old_three_longest_sleep_average: # NOTE: changeable here
        alerts_of_interest.append("Longest interval of uninterrupted sleep decreased significantly")

    # check for quality of sleep from juvo
    target = 0
    qos_mean = 0
    qos_df = pd.DataFrame()
    # supposed to get target from DB (when there are multiple juvo sensors deployed)
    if user_id == '2005' or user_id == 2005:
        target = 460
    else:
        print('resident has no vital signs info from juvo')

    if target:
        japi = JuvoAPI.JuvoAPI()
        tuple_list = japi.get_qos_by_day(target, juvo_date_in_use + datetime.timedelta(days=-7), juvo_date_in_use)
        qos_df = pd.DataFrame(list(tuple_list), columns=['date_timestamp', 'qos'])

        # exclude 0 for mean calculation
        temp_series = qos_df['qos'].replace(0, np.NaN)
        qos_mean = temp_series.mean()
        # print(qos_mean)
        qos_threshold = 50
        if qos_mean < qos_threshold:
            alerts_of_interest.append(f"Quality of sleep lower than {qos_threshold}%")
    else:
        qos_df['qos'] = []
        qos_df['date_timestamp'] = []

    return alerts_of_interest, past_week_average, difference, past_week_longest_sleep_average, difference_longest_sleep, qos_mean, qos_df

def get_overview_change_values(user_id, current_sys_time=None):
    pass

def get_nightly_toilet_indicator(user_id, current_sys_time=None):
    '''
    Returns list of night toilet usage alerts so as to determine what the colour
            of the toilet status indicator should be for a particular elderly
            Second value returns the past week average number of night toilet usage
            Third value returns the difference
    To be called by the overview page
    Checks status for the past week
    Possible arbitary assignment of colors: 0 - Green, 1 - Yellow, 2 - Orange, 3 - Red

    With changeable parameters for the different checks
    NOTE: function assumes that readings for the elderly is normal at the start, and may alert only upon changes

    Nocturia information obtained from https://www.mdedge.com/ccjm/article/89117/geriatrics/nocturia-elderly-wake-call
    '''
    alerts_of_interest = [] # add alerts here, can use in the next layer to priortise things to show also
    if current_sys_time is None: # used in testing - pass in a different time for simulation
        current_sys_time = datetime.datetime.now()
    three_weeks_ago = current_sys_time + datetime.timedelta(days=-21)
    one_week_ago = current_sys_time + datetime.timedelta(days=-7)
    four_weeks_ago = current_sys_time + datetime.timedelta(days=-28)

    # this part can be a separate method for each check
    calculation_sys_time = current_sys_time + datetime.timedelta(days=1)
    # 1st check
    para_SD_threshold = 0.66 # changeable: if difference in moving averages is higher than this multiplied by the std, alert
    # get standard deviation for the past 3 weeks first
    std_calc_data = get_num_visits_by_date(start_date=three_weeks_ago, end_date=calculation_sys_time, node_id=user_id, time_period='Night', offset=True, grouped=True)
    # print(std_calc_data)
    three_week_std = std_calc_data['event'].std()
    # print("3 week std", three_week_std)

    # get calculation data
    calculation_data = get_num_visits_by_date(start_date=max(three_weeks_ago + datetime.timedelta(days=-29),
            input_raw_min_date), end_date=calculation_sys_time, node_id=user_id, time_period='Night', offset=True, grouped=True)

    # print(calculation_data)
    # compare difference in MA with 0.66 * SD (for ~75% confidence)
    three_week_MA = get_visit_numbers_moving_average(user_id, time_period='Night',
            offset=True, grouped=True, days=28, result_data=calculation_data)
    one_week_MA = get_visit_numbers_moving_average(user_id, time_period='Night',
            offset=True, grouped=True, days=7, result_data=calculation_data)
    # print(one_week_MA)
    # print(three_week_MA)
    current_date = current_sys_time.date()
    # print("current_date", current_date)
    # print(three_week_MA.loc[three_week_MA['gw_date_only'] == current_date]['moving_average'])
    # print(one_week_MA.loc[one_week_MA['gw_date_only'] == current_date]['moving_average'])
    try:
        current_MA = one_week_MA.loc[one_week_MA['gw_date_only'] == current_date]['moving_average'].values[0]
        difference_MA = (current_MA
                - three_week_MA.loc[three_week_MA['gw_date_only'] == current_date]['moving_average'].values[0])
    except IndexError as e:
        difference_MA = 0
        current_MA = 0
    # print("difference_MA", difference_MA)
    if difference_MA > para_SD_threshold * three_week_std:
        alerts_of_interest.append("Increased number of night toilet usage in the last week")

    # now check for ratio of night to day toilet usage | can be split to new method
    # NOTE: we use 4 weeks approx. equal to a month and ~30 (28) for good sample size
    para_ratio_threshold = get_para_ratio_threshold()
    # get night usage
    past_month_data_night = get_num_visits_by_date(start_date=four_weeks_ago, end_date=current_sys_time, node_id=user_id, time_period='Night', offset=True, grouped=True)
    # print("past_month_data_night", past_month_data_night)
    # get day usage (and then get para_ratio_threshold * the day, which will be used in statistical test against night)
    past_month_data_both = get_num_visits_by_date(start_date=four_weeks_ago, end_date=current_sys_time, node_id=user_id, offset=True, grouped=True)
    try:
        past_month_data_both['threshold_cmp_value'] = past_month_data_both.apply(lambda row: row['event'] * para_ratio_threshold, axis=1)
        # print("past_month_data_both", past_month_data_both)
        # alert if difference in average over the past week is statistically significant beyond the para_ratio_threshold, 95% confidence interval

        _confidence_interval = 0.95
        _alpha = 0.05
        # use paired t-tests and check for ratio difference of 0.3
        (_t_stat, _p_value) = scipy.stats.ttest_rel(past_month_data_night['event'], past_month_data_both['threshold_cmp_value'])
        if (_t_stat > 0) and (_p_value < (_alpha / 2)):
            alerts_of_interest.append(f"Night toilet usage higher than {para_ratio_threshold * 100}% of total daily usage in the past month")
        # print(alerts_of_interest)
    except ValueError as e:
        pass
    return alerts_of_interest, current_MA

def get_percentage_of_night_toilet_usage(user_id, current_sys_time=None):
    '''
    Returns the percentage of night toilet usage divided by total usage in a day, averaged over a month (as first value in tuple)
    Also returns standard deviation (as the second value in the tuple)
    '''
    if current_sys_time is None: # used in testing - pass in a different time for simulation
        current_sys_time = datetime.datetime.now()
    four_weeks_ago = current_sys_time + datetime.timedelta(days=-28)
    # get night usage
    past_month_data_night = get_num_visits_by_date(start_date=four_weeks_ago, end_date=current_sys_time, node_id=user_id, time_period='Night', offset=True, grouped=True)
    # print("past_month_data_night", past_month_data_night)
    # get day usage (and then get para_ratio_threshold * the day, which will be used in statistical test against night)
    past_month_data_both = get_num_visits_by_date(start_date=four_weeks_ago, end_date=current_sys_time, node_id=user_id, offset=True, grouped=True)

    # calculate percentage for each night
    ratio_series = past_month_data_night['event'] / past_month_data_both['event']
    # print(ratio_series)

    return ratio_series.mean(), ratio_series.std()

# handle the information retrieval for vital signs
def retrieve_breathing_rate_info(node_id='2005', start_date=None, end_date=None):
    '''
    Returns a dict of respiratory rate information from juvo API for the resident corresponding
    with the node_id input as parameter for this function
    '''
    # print(type(start_date))
    if end_date is None:
        date_in_use = datetime.datetime(2018, 8, 12, 23, 34, 12) # datetime.datetime.now()
    else:
        date_in_use = end_date
    # Retrieve relevant juvo API id from node_id first
    target = 0
    # supposed to get target from DB (when there are multiple juvo sensors deployed)
    if node_id == '2005' or node_id == 2005:
        target = 460
    else:
        print('resident has no vital signs info from juvo')
        return ''
    # Get all the relevant data from the past week
    one_week_ago = date_in_use + datetime.timedelta(days=-7)
    if start_date is None:
        one_month_ago = date_in_use + datetime.timedelta(days=-30)
        start_date = one_month_ago

    ###### Either this (only for development)
    # with open('sleeps_json.pyobjcache', 'rb') as f:
    #     # NOTE: THIS IS FOR DEV USE ONLY
    #     #+To prevent unnecessary high volume of API calls, the test json is dumped
    #     #+to a local file for testing purposes while in development
    #     # sleeps_json = dill.load(f)
    #     vitals_json = dill.load(f)
    ###### Or this
    japi = JuvoAPI.JuvoAPI()
    # sleeps_json = japi.get_target_sleeps(target, start_date, date_in_use)
    vitals_json = japi.get_target_vitals(target, start_date, date_in_use)
    with open('sleeps_json.pyobjcache', 'wb') as f:
        # dill.dump(sleeps_json, f)
        dill.dump(vitals_json, f)
    ######

    # print(sleeps_json)
    # sleeps_dict = sleeps_json['data']['sleeps']
    # print(type(sleeps_dict))

    # sleeps_juvo_df = pd.DataFrame(sleeps_dict)
    # print(sleeps_juvo_df)

    # Get first instance of sleep at night as start of sleep

    # Get first instance of no detection in the morning as end of sleep

    # Below for vitals
    # print(vitals_json)
    vitals_dict = vitals_json['data']['epoch_metrics']
    vitals_juvo_df = pd.DataFrame(vitals_dict)
    if vitals_juvo_df.empty:
        print("empty data returned from juvo")
        return pd.DataFrame()
    # print(vitals_juvo_df.info())

    # Get daily breathing and heartbeat rates
    # Remove rows where values are 0 first
    breathing_rate_df = vitals_juvo_df[['vital_id', 'sensor_status', 'breathing_rate', 'high_movement_rejection_breathing', 'local_start_time', 'local_end_time']]
    breathing_rate_df = breathing_rate_df[breathing_rate_df['breathing_rate'] > 0]
    breathing_rate_df.reset_index(drop=True, inplace=True)
    # print(breathing_rate_df)

    # remove outliers (> 3 s.d. away)
    breathing_sd = breathing_rate_df[['breathing_rate']].std().values[0]
    breathing_mean = breathing_rate_df[['breathing_rate']].mean().values[0]

    # print((breathing_mean + 3 * breathing_sd).values[0])
    breathing_rate_filtered_df = breathing_rate_df[(breathing_rate_df['breathing_rate'] < (breathing_mean + 3 * breathing_sd))
            & (breathing_rate_df['breathing_rate'] > (breathing_mean - 3 * breathing_sd))]
    # breathing_rate_filtered_df = breathing_rate_filtered_df[breathing_rate_filtered_df['breathing_rate'] > (breathing_mean - 3 * breathing_sd)]
    breathing_rate_filtered_df.sort_values('local_start_time', inplace=True)
    breathing_rate_filtered_df.reset_index(drop=True, inplace=True)
    # print(breathing_rate_filtered_df)
    # group average by date
    return breathing_rate_filtered_df

def retrieve_heart_rate_info(node_id='2005', start_date=None, end_date=None):
    '''
    Returns a dict of pulse rate information from juvo API for the resident corresponding
    with the node_id input as parameter for this function
    '''
    if end_date is None:
        date_in_use = datetime.datetime(2018, 8, 12, 23, 34, 12) # datetime.datetime.now()
    else:
        date_in_use = end_date
    # Retrieve relevant juvo API id from node_id first
    target = 0
    # supposed to get target from DB (when there are multiple juvo sensors deployed)
    if node_id == '2005' or node_id == 2005:
        target = 460
    else:
        print('resident has no vital signs info from juvo')
        return ''
    # Get all the relevant data from the past week
    one_week_ago = date_in_use + datetime.timedelta(days=-7)
    if start_date is None:
        one_month_ago = date_in_use + datetime.timedelta(days=-30)
        start_date = one_month_ago

    ###### Either this (only for development)
    # with open('sleeps_json.pyobjcache', 'rb') as f:
    #     # NOTE: THIS IS FOR DEV USE ONLY
    #     #+To prevent unnecessary high volume of API calls, the test json is dumped
    #     #+to a local file for testing purposes while in development
    #     # sleeps_json = dill.load(f)
    #     vitals_json = dill.load(f)
    ###### Or this
    japi = JuvoAPI.JuvoAPI()
    # sleeps_json = japi.get_target_sleeps(target, start_date, date_in_use)
    vitals_json = japi.get_target_vitals(target, start_date, date_in_use)
    # with open('sleeps_json.pyobjcache', 'wb') as f:
    #     dill.dump(sleeps_json, f)
    #     dill.dump(vitals_json, f)
    ######

    vitals_dict = vitals_json['data']['epoch_metrics']
    vitals_juvo_df = pd.DataFrame(vitals_dict)
    # print(vitals_juvo_df.info())

    if vitals_juvo_df.empty:
        print("empty data returned from juvo")
        return pd.DataFrame()

    heart_rate_df = vitals_juvo_df[['vital_id', 'sensor_status', 'heart_rate', 'high_movement_rejection_heartbeat', 'local_start_time', 'local_end_time']]
    heart_rate_df = heart_rate_df[heart_rate_df['heart_rate'] > 0]
    heart_rate_df.reset_index(drop=True, inplace=True)
    # print(heart_rate_df)

    heartbeat_sd = heart_rate_df[['heart_rate']].std().values[0]
    heartbeat_mean = heart_rate_df[['heart_rate']].mean().values[0]

    print(f"DEBUG: heartbeat mean and sd is {heartbeat_mean} and {heartbeat_sd}")

    heart_rate_filtered_df = heart_rate_df[(heart_rate_df['heart_rate'] < (heartbeat_mean + 3 * heartbeat_sd))
            & (heart_rate_df['heart_rate'] > (heartbeat_mean - 3 * heartbeat_sd))]
    # heart_rate_filtered_df = heart_rate_filtered_df[heart_rate_filtered_df['heart_rate'] > (heartbeat_mean - 3 * heartbeat_sd)]
    heart_rate_filtered_df.sort_values('local_start_time', inplace=True)
    heart_rate_filtered_df.reset_index(drop=True, inplace=True)
    # print(heart_rate_filtered_df)

    return heart_rate_filtered_df

normal_lower_bound_rr = 16
normal_upper_bound_rr = 25
normal_upper_bound_hb = 65

def get_vital_signs_indicator(user_id, current_sys_time=None):
    '''
    Returns tuple of (1) list of vital signs alerts (2) past week respiratory rate average
    (3) previous three weeks respiratory rate average

    NOTE: for (2) and (3) they are calculated after grouping by day while for (1) the alerts
    are generated before grouping by day and the averages are aggregated by all readings in a week
    '''
    alerts_of_interest = []
    confidence = 0.90
    if current_sys_time is None:
        current_sys_time = datetime.datetime.now()
    # get one week's worth of readings
    one_week_ago = current_sys_time + datetime.timedelta(days=-7)
    four_weeks_ago = current_sys_time + datetime.timedelta(days=-28)

    ### below aggregated by day first
    past_week_average_breathing = 0
    previous_weeks_average_breathing = 0
    past_week_average_heart = 0
    previous_weeks_average_heart = 0
    ###

    past_week_breathing_df = retrieve_breathing_rate_info(user_id, one_week_ago, current_sys_time)
    if isinstance(past_week_breathing_df, str) or past_week_breathing_df.empty:
        # print("empty data received")
        pass
        # possibly flash an error message
    else:
        breathings = past_week_breathing_df.breathing_rate
        breathing_n = len(breathings)
        breathing_mean = np.mean(breathings)
        breathing_se = scipy.stats.sem(breathings)
        breathing_h = breathing_se * scipy.stats.t.pdf((1 + confidence) / 2., breathing_n-1)
        if (breathing_mean + breathing_h) < normal_lower_bound_rr:
            alerts_of_interest.append(f"Night respiratory rate from previous week significantly lower than normal (<{normal_lower_bound_rr})")
        elif (breathing_mean - breathing_h) > normal_upper_bound_rr:
            alerts_of_interest.append(f"Night respiratory rate from previous week significantly higher than normal (>{normal_upper_bound_rr})")
        past_week_breathing_df['reading_timestamp'] = pd.to_datetime(past_week_breathing_df['local_start_time'], format='%Y-%m-%dT%H:%M:%SZ')
        past_week_breathing_df['date_only'] = past_week_breathing_df['reading_timestamp'].apply(date_only)

        breathing_graph_df = past_week_breathing_df.groupby(['date_only'], as_index=False)['breathing_rate'].mean()
        past_week_average_breathing = breathing_graph_df.breathing_rate.mean()

    # get average respiratory rate of previous 3 weeks (comparing personal baselines)
    previous_weeks_breathing_df = retrieve_breathing_rate_info(user_id, four_weeks_ago, one_week_ago)
    if isinstance(previous_weeks_breathing_df, str) or past_week_breathing_df.empty:
        # print("empty data received")
        pass
        # possibly flash an error message
    else:
        prev_breathings = previous_weeks_breathing_df.breathing_rate
        if not (isinstance(past_week_breathing_df, str) or past_week_breathing_df.empty):
            breathings = past_week_breathing_df.breathing_rate
            breathing_n = len(breathings)
            breathing_mean = np.mean(breathings)
            prev_breathings_mean = np.mean(prev_breathings)
            breathing_se = scipy.stats.sem(breathings)
            breathing_h = breathing_se * scipy.stats.t.pdf((1 + confidence) / 2., breathing_n-1)
            if (breathing_mean - breathing_h) > prev_breathings_mean:
                alerts_of_interest.append(f"Significant increase of respiratory rate in the past month")
            elif (breathing_mean + breathing_h) < prev_breathings_mean:
                alerts_of_interest.append(f"Significant decrease of respiratory rate in the past month")

            previous_weeks_breathing_df['reading_timestamp'] = pd.to_datetime(previous_weeks_breathing_df['local_start_time'], format='%Y-%m-%dT%H:%M:%SZ')
            previous_weeks_breathing_df['date_only'] = previous_weeks_breathing_df['reading_timestamp'].apply(date_only)

            previous_weeks_breathing_result_df = previous_weeks_breathing_df.groupby(['date_only'], as_index=False)['breathing_rate'].mean()
            previous_weeks_average_breathing = previous_weeks_breathing_result_df.breathing_rate.mean()

    ### below for heartbeat
    past_week_heartbeat_df = retrieve_heart_rate_info(user_id, one_week_ago, current_sys_time)
    if isinstance(past_week_heartbeat_df, str) or past_week_heartbeat_df.empty:
        # print("empty data received")
        pass
        # possibly flash an error message
    else:
        heartbeats = past_week_heartbeat_df.heart_rate
        heart_n = len(heartbeats)
        heart_mean = np.mean(heartbeats)
        heart_se = scipy.stats.sem(heartbeats)
        heart_h = heart_se * scipy.stats.t.pdf((1 + confidence) / 2., heart_n-1)
        print(f"DEBUG: heart_h {heart_h}")
        print(f"DEBUG: heart statistic for comparison {heart_mean - heart_h}")
        if (heart_mean - heart_h) > normal_upper_bound_hb:
            alerts_of_interest.append(f"Pulse rate during sleep from previous week significantly higher than normal (>{normal_upper_bound_hb})")

        past_week_heartbeat_df['reading_timestamp'] = pd.to_datetime(past_week_heartbeat_df['local_start_time'], format='%Y-%m-%dT%H:%M:%SZ')
        past_week_heartbeat_df['date_only'] = past_week_heartbeat_df['reading_timestamp'].apply(date_only)

        past_week_heartbeat_result_df = past_week_heartbeat_df.groupby(['date_only'], as_index=False)['heart_rate'].mean()
        past_week_average_heart = past_week_heartbeat_result_df.heart_rate.mean()

    # get average pulse rate of previous 3 weeks (comparing personal baselines)
    previous_weeks_heartbeat_df = retrieve_heart_rate_info(user_id, four_weeks_ago, one_week_ago)
    if isinstance(previous_weeks_heartbeat_df, str) or previous_weeks_heartbeat_df.empty:
        # print("empty data received")
        pass
    else:
        prev_heartbeat = previous_weeks_heartbeat_df.heart_rate
        if not (isinstance(past_week_heartbeat_df, str) or past_week_heartbeat_df.empty):
            heartbeats = past_week_heartbeat_df.heart_rate
            heart_n = len(heartbeats)
            heart_mean = np.mean(heartbeats)
            prev_heartbeats_mean = np.mean(prev_heartbeat)
            heart_se = scipy.stats.sem(heartbeats)
            heart_h = heart_se * scipy.stats.t.pdf((1 + confidence) / 2., heart_n-1)
            if (heart_mean - heart_h) > prev_heartbeats_mean:
                alerts_of_interest.append(f"Significant increase of pulse rate in the past month")
            elif (heart_mean + heart_h) < prev_heartbeats_mean:
                alerts_of_interest.append(f"Significant decrease of pulse rate in the past month")
            previous_weeks_heartbeat_df['reading_timestamp'] = pd.to_datetime(previous_weeks_heartbeat_df['local_start_time'], format='%Y-%m-%dT%H:%M:%SZ')
            previous_weeks_heartbeat_df['date_only'] = previous_weeks_heartbeat_df['reading_timestamp'].apply(date_only)

            previous_weeks_heartbeat_result_df = previous_weeks_heartbeat_df.groupby(['date_only'], as_index=False)['heart_rate'].mean()
            previous_weeks_average_heart = previous_weeks_heartbeat_result_df.heart_rate.mean()

    return alerts_of_interest, past_week_average_breathing, previous_weeks_average_breathing, past_week_average_heart, previous_weeks_average_heart

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
    # result = motion_duration_during_sleep(2005, datetime.date(2018, 5, 1), datetime.date(2018, 5, 3))
    # print("result", result)

    # test getting indicators
    # result = get_nightly_toilet_indicator(2006, input_raw_max_date + datetime.timedelta(days=-10))
    # print ("result", result)

    result = get_nightly_sleep_indicator(2005)
    print ("result", result)

    # test night toilet ratios
    # get_percentage_of_night_toilet_usage(2005, input_raw_max_date + datetime.timedelta(days=-10))
    # get_percentage_of_night_toilet_usage(2006, input_raw_max_date + datetime.timedelta(days=-10))
    # print(retrieve_breathing_rate_info())
    # print(retrieve_heart_rate_info())
    # print(get_vital_signs_indicator('2005', datetime.datetime(2018, 8, 12, 23, 34, 12)))
    pass # prevents error when no debug tests are being done
