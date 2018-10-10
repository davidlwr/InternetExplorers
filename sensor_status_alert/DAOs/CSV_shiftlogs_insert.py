import os
import sys
from datetime import datetime

import pandas as pd

pd.set_option('display.expand_frame_repr', False)
sys.path.append('../Entities')
from shift_log import Shift_log

sys.path.append('../DAOs')
from shift_log_DAO import shift_log_DAO

# datetime_object = datetime.strptime('Jun 1 2005  1:33PM', '%b %d %Y %I:%M%p')
# log = Sensor_Log("2005-m-01", 2005, 255, datetime_object)
# dao = sensor_log_DAO()
# dao.insert_sensor_log(log)

# print(log)
# pd.options.mode.chained_assignment = None
file_folder = '../stbern-20180302-20180523-csv/logs/'
# initialize empty df
input_raw_data = pd.DataFrame()

# combine and read all data
for filename in os.listdir(file_folder):
    if filename.endswith('Logs.csv'):
        try:
            temp_df = pd.read_csv(file_folder + filename)
            input_raw_data = pd.concat([input_raw_data, temp_df], ignore_index=True)
        except:
            print('something wrong with ' + filename)

# convert datetime format
input_raw_data['date_and_time'] = pd.to_datetime(input_raw_data['date_and_time'],
                                                 format='%Y-%m-%dT%H:%M:%S')
di = {"Joy Lo": 1}
di2 = {"moderate": 3}
# input_raw_data['patient_id'].replace(di, inplace=True)
input_raw_data['Food_consumption'].replace(di2, inplace=True)
print(input_raw_data)
for row in input_raw_data.itertuples(index=True, name='Pandas'):
    log = Shift_log(getattr(row, 'date_and_time'),
                    None,  # day/night
                    getattr(row, 'patient_id'),
                    getattr(row, 'Number_of_Slips'),
                    getattr(row, 'Number_of_Near_Falls'),
                    getattr(row, 'Food_consumption'),
                    getattr(row, 'Number_of_toilet_visit'),
                    getattr(row, 'Temperature'),
                    getattr(row, 'Sbp'),
                    getattr(row, 'dbp'),
                    getattr(row, 'Pulse_Rate'))
    # print(log)
    dao = shift_log_DAO()
    dao.insert_shift_log(log)
