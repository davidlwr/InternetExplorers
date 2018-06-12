import pandas as pd
import datetime
import os

from apps import input_sysmon

# specify file parameters
file_folder = '../stbern-20180302-20180523-csv/'
file_name = '2018-03-02-2005-sensor.csv'

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

#convert values to 1 and 0 instead of 255
input_raw_data.loc[:, 'value'].replace(255, 1, inplace=True)

# common variables
input_raw_max_date = input_raw_data['gw_timestamp'].max()
input_raw_min_date = input_raw_data['gw_timestamp'].min()
# print(input_raw_data.head())
# print(input_raw_data.info())
# print(input_raw_data.index.values)

# parameters for day and night timing
'''
    In this case daytime refers to the current date's daytime, while nighttime
    refers to the current date's night till the next date's morning
'''
daytime_start = datetime.time(6, 30)
daytime_end = datetime.time(21, 30)
# below is redundant
nighttime_start = daytime_end
nighttime_end = daytime_start

# replace date to be date only
def date_only(original_date):
    return original_date.replace(hour=0, minute=0, second=0, microsecond=0)

### find out number of times activated by date
# first mark all 'activation points', index dependent on raw data input
def get_num_visits_by_date(start_date=input_raw_min_date, end_date=input_raw_max_date,
        input_location='toilet_bathroom', gw_device=2005, day_only=False, night_only=False):
    '''
    Function returns dates and aggregated number of times the sensor was activated
    To get day only, use day_only=True and to get night_only use night_only=True
    '''
    current_data = get_df_01(input_location, start_date, end_date, gw_device)

    # group by date only
    if (not day_only) and (not night_only):
        # change datetime format to date only
        current_data['gw_date_only'] = current_data['gw_timestamp'].apply(date_only)
        #print(current_data)
        result_data = current_data.groupby(['gw_date_only'], as_index=False)['value'].sum()
        # print(result_data.head())
        return result_data
    return current_data

# method to get the relevant columns of data
def get_df_01(input_location, start_date, end_date, gw_device=2005):
    relevant_data = input_raw_data.loc[(input_raw_data['device_loc'] == input_location)
            & (input_raw_data['gw_timestamp'] < end_date)
            & (input_raw_data['gw_timestamp'] > start_date)
            & (input_raw_data['gw_device'] == gw_device), ['device_loc','gw_device','gw_timestamp', 'value']]
    return relevant_data

# generate array for the different available locations
def get_location_options():
    # print('debug: ', end='')
    # print(data['device_loc'].unique().tolist())
    return input_raw_data['device_loc'].unique().tolist()

# generate array for the different residents
def get_residents_options():
    return input_raw_data['gw_device'].unique().tolist()
