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
sysmon_relevant_data = sysmon_data.loc[sysmon_data['reading_type'].isin(['disconnected','uptime'])]

# remove duplicates
sysmon_relevant_data.drop_duplicates(['device_id','device_loc','gw_device','gw_timestamp','key','reading_type'], inplace=True)

# get inactive period within time
def get_disconnected_periods():
    '''
    '''
    return []

# below for testing
if __name__ == '__main__':
    # print(sysmon_relevant_data.head())
    print(sysmon_relevant_data['reading_type'].value_counts())
    # print(sysmon_relevant_data[sysmon_relevant_data.duplicated(['device_id','device_loc','gw_device','gw_timestamp','key','reading_type'], keep=False)])
