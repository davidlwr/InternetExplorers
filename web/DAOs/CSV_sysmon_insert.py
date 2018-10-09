import os
import sys
from datetime import datetime
import pandas as pd
import pymysql
from tqdm import tqdm

if __name__ == '__main__':  sys.path.append("..")
from Entities.sysmon_log import Sysmon_Log
from DAOs.sysmon_log_DAO import sysmon_log_DAO


pd.options.mode.chained_assignment = None
file_folder = 'D:/FYP/DevBackUp/stbern-20180523-20180801/'

# initialize empty dateframe to contain all row logs
input_raw_data = pd.DataFrame()

# Iterate CSV files and loop rows
for filename in os.listdir(file_folder):
    if filename.endswith('sysmon.csv'):
        try:
            temp_df = pd.read_csv(file_folder + filename)
            input_raw_data = pd.concat([input_raw_data, temp_df], ignore_index=True)
        except:
            print('something wrong with ' + filename)

# convert datetime format
input_raw_data['gw_timestamp'] = pd.to_datetime(input_raw_data['gw_timestamp'], format='%Y-%m-%dT%H:%M:%S')

input_raw_data.drop_duplicates(subset=['gw_timestamp'], inplace=True)

# consoludate logs
logs = []
for row in tqdm(input_raw_data.itertuples(index=True, name='Pandas')):
    device_id    = getattr(row, 'device_id')        # Can be either gateway or sensor itself. sensor:"2005-m-01", gw:"2005"
    gw_device    = getattr(row, 'gw_device')        # i.e. "2005"
    value        = getattr(row, 'value')            # some int or float
    reading_type = getattr(row, 'reading_type')     # "battery_percent" or some other random shit that have no link to the date we get currently
    gw_timestamp = getattr(row, 'gw_timestamp')

    # Conversion of battery level from CSV to current messages gotten from mqtt
    if reading_type == "battery_percent": reading_type = "Battery Level"

    # Consolidate
    log = Sysmon_Log(uuid=device_id, node_id=gw_device, event=value, key=reading_type, recieved_timestamp=gw_timestamp)
    logs.append(log)

# Insert batchs
dao = sysmon_log_DAO()
try:
    dao.insert_many(logs)
except pymysql.err.IntegrityError as err:
    raise
    pass
