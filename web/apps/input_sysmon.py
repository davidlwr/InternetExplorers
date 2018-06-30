import pandas as pd
import datetime
import os

# specify file parameters
file_folder = '../stbern-20180302-20180523-csv/'

# testing options
if __name__ == '__main__':
    pd.options.mode.chained_assignment = None  # default='warn

# initialize empty df
sysmon_data = pd.DataFrame()

# combine and read all data
for filename in os.listdir(file_folder):
    if filename.endswith('sysmon.csv'):
        try:
            temp_df = pd.read_csv(file_folder + filename)
            sysmon_data = pd.concat([sysmon_data, temp_df])
        except:
            print('something wrong with ' + filename)

# print(sysmon_data.reading_type.unique())

# look for time periods with disconnected
# first get only disconnected and uptime rows
sysmon_disconnected_data = sysmon_data.loc[sysmon_data['reading_type'].isin(['disconnected'])]

# remove duplicates
sysmon_disconnected_data.drop_duplicates(['device_id','device_loc','gw_device','gw_timestamp','key','reading_type'], inplace=True)
sysmon_disconnected_data.reset_index(drop=True)

# get inactive period within time
def remove_disconnected_periods(current_data):
    '''
    Takes in data (from main readings) to be used and removes readings affected by disconnected periods
    Data should already filtered to one user, and one location (for now, could be extended in the future)
    Should call this function first before calling grouping function
    NOTE: Index of input dataframe will be reset
    '''
    # NOTE: Although it is possible to clean the entire whole input chunk, when we have data in DB the retrieval
    #       is most likely filtered by user and location in the first place. Also makes code easier

    if current_data is None or len(current_data) == 0: # applicable when web app first load without user inputs
        return current_data

    current_data.reset_index(drop=True)
    # filter out sysmon data for what is relevant in the current data first
    current_user = current_data['gw_device'].iloc[0]
    sysmon_relevant_data = sysmon_disconnected_data[sysmon_disconnected_data['gw_device'] == current_user]

    # issue where motion is considered active when sensor is disconnected
    previous_disconnection = current_data['gw_timestamp'].min()
    current_disconnection = current_data['gw_timestamp'].min()
    for i in range(0, len(sysmon_relevant_data)):
        current_disconnection = sysmon_relevant_data['gw_timestamp'].iloc[i]
        # select latest row before the disconnection, but after the previous disconnection and get its value
        try:
            current_index = current_data[(current_data['gw_timestamp'] < current_disconnection)
                    & (current_data['gw_timestamp'] > previous_disconnection)]['gw_timestamp'].idxmax()
        except Exception:
            # print('log: ', 'exception on getting idxmax()')
            continue
        if current_data['value'].loc[current_index] == 1:
            # if last row is a value of activation, discard it
            current_data.drop(current_index, inplace=True)
            # print('debug: ', 'dropped value')
        previous_disconnection = current_disconnection

    current_data.reset_index(drop=True)
    # issue where 0 reading is recorded after sensor just recovers from disconnection
    current_disconnection = current_data['gw_timestamp'].iloc[0]
    next_disconnection = current_data['gw_timestamp'].iloc[0]
    for i in range(1, len(sysmon_relevant_data)):
        next_disconnection = sysmon_relevant_data['gw_timestamp'].iloc[i]
        # select earliest row after the disconnection, but before the next disconnection and get its value
        try:
            current_index = current_data[(current_data['gw_timestamp'] > current_disconnection)
                    & (current_data['gw_timestamp'] < next_disconnection)]['gw_timestamp'].idxmin()
        except Exception:
            # print('log', 'exception on getting idxmin()')
            continue
        if current_data['value'].loc[current_index] == 0:
            # if next row is a value of inactivity, discard it
            current_data.drop(current_index, inplace=True)
            # print('debug: ', 'dropped value')
        current_disconnection = next_disconnection

    return current_data

# below for testing
# NOTE: For testing of functions requiring data from input_data, run test from input_data.py
#       This is to 1. prevent cyclical imports and 2. be in line with how data will be called in the first place
# if __name__ == '__main__':
    # print(sysmon_disconnected_data.head())
    # print(sysmon_disconnected_data['reading_type'].value_counts())
    # print(sysmon_disconnected_data[sysmon_disconnected_data.duplicated(['device_id','device_loc','gw_device','gw_timestamp','key','reading_type'], keep=False)])
