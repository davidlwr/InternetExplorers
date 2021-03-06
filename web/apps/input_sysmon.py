import pandas as pd
import datetime
import os
import sys

# internal imports
if __name__ == '__main__':
    sys.path.append(".")
    from DAOs.sysmon_log_DAO import sysmon_log_DAO
else:
    from DAOs.sysmon_log_DAO import sysmon_log_DAO

# specify file parameters
file_folder = '../stbern-20180302-20180523-csv/'

# testing options
if __name__ == '__main__':
    pd.options.mode.chained_assignment = None  # default='warn

# initialize empty df
# sysmon_data = pd.DataFrame()
sysmon_data = sysmon_log_DAO.get_all_logs(format='pd')
# sysmon_data = pd.DataFrame(sysmon_data_sql)
# print(sysmon_data)

# combine and read all data
# for filename in os.listdir(file_folder):
#     if filename.endswith('sysmon.csv'):
#         try:
#             temp_df = pd.read_csv(file_folder + filename)
#             sysmon_data = pd.concat([sysmon_data, temp_df])
#         except:
#             print('something wrong with ' + filename)

# print(sysmon_data.reading_type.unique())

# look for time periods with disconnected
# first get only disconnected and uptime rows
sysmon_disconnected_data = sysmon_data.loc[sysmon_data['key'].isin(['disconnected'])]

# convert datetime format
sysmon_disconnected_data['recieved_timestamp'] = pd.to_datetime(sysmon_disconnected_data['recieved_timestamp'],
                                                          format='%Y-%m-%dT%H:%M:%S')

# remove duplicates
# sysmon_disconnected_data.drop_duplicates(
#     ['device_id', 'device_loc', 'gw_device', 'recieved_timestamp', 'key', 'reading_type'], inplace=True)
# sysmon_disconnected_data.reset_index(drop=True)

def update_input_sysmon():
    sysmon_data = sysmon_log_DAO.get_all_logs(format='pd')

# get inactive period within time
def remove_disconnected_periods(current_data, dc_list=None):
    '''
    Takes in data (from main readings) to be used and removes readings affected by disconnected periods
    Data should already filtered to one user, and one location (for now, could be extended in the future)
    Should call this function first before calling grouping function
    NOTE: Index of input dataframe will be reset
    '''
    # NOTE: Although it is possible to clean the entire whole input chunk, when we have data in DB the retrieval
    #       is most likely filtered by user and location in the first place. Also makes code easier

    if current_data is None or len(current_data) == 0:  # applicable when web app first load without user inputs
        return current_data

    current_data.reset_index(drop=True)

    # drop readings within the periods first
    if dc_list:
        for dc_period in dc_list:
            # print(dc_period)
            current_data = current_data.loc[(current_data['recieved_timestamp'] < dc_period[0]) | (current_data['recieved_timestamp'] > dc_period[1])]

        dc_list = [d[0] for d in dc_list]

    # filter out sysmon data for what is relevant in the current data first (by time and location)
    current_user = current_data['node_id'].iloc[0]
    if not dc_list:
        sysmon_relevant_data = sysmon_disconnected_data[(sysmon_disconnected_data['node_id'] == current_user)
                                                        & (sysmon_disconnected_data['recieved_timestamp'] > current_data[
            'recieved_timestamp'].min())
                                                        & (sysmon_disconnected_data['recieved_timestamp'] < current_data[
            'recieved_timestamp'].max())]
    else:
        sysmon_relevant_data = pd.DataFrame({'recieved_timestamp': dc_list})

    # issue where motion is considered active when sensor is disconnected
    previous_disconnection = current_data['recieved_timestamp'].min()
    current_disconnection = current_data['recieved_timestamp'].min()
    for i in range(0, len(sysmon_relevant_data)):
        current_disconnection = sysmon_relevant_data['recieved_timestamp'].iloc[i]
        # select latest row before the disconnection, but after the previous disconnection and get its value
        try:
            current_index = current_data[(current_data['recieved_timestamp'] < current_disconnection)
                                         & (current_data['recieved_timestamp'] > previous_disconnection)][
                'recieved_timestamp'].idxmax()
        except Exception:
            # print('log: ', 'exception on getting idxmax()')
            continue
        if current_data['event'].loc[current_index] == 1:
            # if last row is a value of activation, discard it
            current_data.drop(current_index, inplace=True)
            # print('debug: ', 'dropped value')
        previous_disconnection = current_disconnection

    current_data.reset_index(drop=True)
    # issue where 0 reading is recorded after sensor just recovers from disconnection
    current_disconnection = current_data['recieved_timestamp'].iloc[0]
    next_disconnection = current_data['recieved_timestamp'].iloc[0]
    for i in range(1, len(sysmon_relevant_data)):
        next_disconnection = sysmon_relevant_data['recieved_timestamp'].iloc[i]
        # select earliest row after the disconnection, but before the next disconnection and get its value
        try:
            current_index = current_data[(current_data['recieved_timestamp'] > current_disconnection)
                                         & (current_data['recieved_timestamp'] < next_disconnection)]['recieved_timestamp'].idxmin()
        except Exception:
            # print('log', 'exception on getting idxmin()')
            continue
        if current_data['event'].loc[current_index] == 0:
            # if next row is a value of inactivity, discard it
            current_data.drop(current_index, inplace=True)
            # print('debug: ', 'dropped value')
        current_disconnection = next_disconnection

    return current_data

# below for testing
# NOTE: For testing of functions requiring data from input_data, run test from input_data.py
#       This is to 1. prevent cyclical imports and 2. be in line with how data will be called in the first place
if __name__ == '__main__':
    print(sysmon_disconnected_data.head())
# print(sysmon_disconnected_data['reading_type'].value_counts())
# print(sysmon_disconnected_data[sysmon_disconnected_data.duplicated(['device_id','device_loc','gw_device','recieved_timestamp','key','reading_type'], keep=False)])
