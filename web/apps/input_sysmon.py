import pandas as pd
import datetime
import os

# specify file parameters
file_folder = '../stbern-20180302-20180523-csv/'

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
