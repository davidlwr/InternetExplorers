import os
import sys
from datetime import datetime
import pandas as pd

if __name__ == '__main__':  sys.path.append("..")
from Entities.sensor_log import Sensor_Log
from DAOs.sensor_log_DAO import sensor_log_DAO


pd.options.mode.chained_assignment = None
file_folder = '../stbern-20180302-20180523-csv/'
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

# Read from dataframe and insert via daos
dao = sensor_log_DAO()
# remove duplicates
input_raw_data.drop_duplicates(subset=['gw_timestamp'], inplace=True)

for row in input_raw_data.itertuples(index=True, name='Pandas'):
    log = Sensor_Log(getattr(row, 'device_id'), getattr(row, 'gw_device'), getattr(row, 'value'),
                     getattr(row, 'gw_timestamp'))
    dao.insert_sensor_log(log)
