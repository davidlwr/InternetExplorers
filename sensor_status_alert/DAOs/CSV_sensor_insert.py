import os
import sys
from datetime import datetime

import pandas as pd

sys.path.append('../Entities')
from sensor_log import Sensor_Log

sys.path.append('../DAOs')
from sensor_log_DAO import sensor_log_DAO

datetime_object = datetime.strptime('Jun 1 2005  1:33PM', '%b %d %Y %I:%M%p')
log = Sensor_Log("2005-m-01", 2005, 255, datetime_object)
dao = sensor_log_DAO()
# dao.insert_sensor_log(log)

print(log)
pd.options.mode.chained_assignment = None
file_folder = 'D:\\FYP\\Git\\InternetExplorers\\stbern-20180523-20180801\\'
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

# remove duplicates
input_raw_data.drop_duplicates(subset=['gw_timestamp'], inplace=True)

for row in input_raw_data.itertuples(index=True, name='Pandas'):
    log = Sensor_Log(getattr(row, 'device_id'), getattr(row, 'gw_device'), getattr(row, 'value'),
                     getattr(row, 'gw_timestamp'))
    dao = sensor_log_DAO()
    dao.insert_sensor_log(log)
