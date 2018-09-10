import sys
import pandas as pd
import datetime

# pandas settings
pd.options.mode.chained_assignment = None  # default='warn
pd.set_option('display.expand_frame_repr', False)

if __name__ == '__main__':  # we want to import from same directory if using this
    # module as-is (for debugging mainly, or for loading data in the future)
    sys.path.append(".")
    from DAOs.shift_log_DAO import shift_log_DAO
else:  # if called from index.py
    from DAOs.shift_log_DAO import shift_log_DAO

# input_raw_data = pd.DataFrame()
input_raw_data = shift_log_DAO.get_all_logs()
input_raw_data['datetime'] = pd.to_datetime(input_raw_data['datetime'], format='%Y-%m-%dT%H:%M:%S')
input_raw_data['food_consumption'] = pd.to_numeric(input_raw_data['food_consumption'])
input_raw_data['pulse_pressure'] = input_raw_data['systolic_bp'] - input_raw_data['diastolic_bp']
input_raw_max_date = input_raw_data['datetime'].max()
input_raw_min_date = input_raw_data['datetime'].min()
# print(input_raw_data)
daytime_start = datetime.time(7, 30)
daytime_end = datetime.time(19, 30)


def date_only(original_date):
    return original_date.replace(hour=0, minute=0, second=0, microsecond=0)


def get_logs_filter_options():
    '''Returns labels and values in an array of tuples'''
    return [('No. of Falls', 'num_falls'), ('No. of Near Falls', 'num_near_falls'),
            ('Food Consumption', 'food_consumption'), ('Temperature', 'temperature'), ('Systolic//Diastolic Bp', 'sys_dia'),
            ('Pulse Pressure', 'pulse_pressure'), ('Pulse Rate', 'pulse_rate')]


def get_relevant_data(start_date, end_date, patient_id):
    '''
    Retrieve sensor data based on location, start and end dates, and the device
    grouped=True to get grouped data for toilet visits
    '''
    # TODO: this part probably is the best to convert to retrieve from DB
    relevant_data = input_raw_data.loc[(input_raw_data['patient_id'] == patient_id)
                                       & (input_raw_data['datetime'] < end_date)
                                       & (input_raw_data['datetime'] > start_date),
                                       ['patient_id', 'datetime', 'num_falls', 'num_near_falls', 'food_consumption',
                                        'temperature', 'systolic_bp', 'diastolic_bp', 'pulse_pressure', 'pulse_rate']]
    return relevant_data


def get_logs_by_date(start_date=input_raw_min_date, end_date=input_raw_max_date,
                     patient_id=1, time_period=None):
    """
    Function returns dates and aggregated number of times the sensor was activated
    To get day only, use time_period='Day' and to get night_only use time_period='Night'
    To report night numbers as the night of the previous day, use offset=True
    To ignore short durations, use ignore_short_durations=True, and set the minimum duration to be included using min_duration
    """

    # NOTE: last day of the returned output is not accurate if offset is used because the next day's data is needed to get the current night's data
    current_data = get_relevant_data(start_date, end_date, patient_id)
    # print(current_data)

    # print(current_data)
    if time_period == 'Day':
        current_data = current_data.loc[(current_data['datetime'].dt.time >= daytime_start)
                                        & (current_data['datetime'].dt.time < daytime_end)]
    elif time_period == 'Night':
        current_data = current_data.loc[(current_data['datetime'].dt.time < daytime_start)
                                        | (current_data['datetime'].dt.time > daytime_end)]

    # group by date only
    current_data['date_only'] = current_data['datetime'].apply(date_only)
    result_data = current_data.groupby(['date_only'], as_index=False)[
        'num_falls', 'num_near_falls', 'food_consumption', 'temperature', 'systolic_bp', 'diastolic_bp', 'pulse_pressure', 'pulse_rate'].mean()

    # add 0 for days with no data
    result_data.set_index('date_only', inplace=True)
    if isinstance(start_date, str):
        start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d')

    if isinstance(end_date, str):
        end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d')

    all_days_range = pd.date_range(start_date.date(), end_date.date() + datetime.timedelta(days=-1), freq='D')
    try:
        result_data = result_data.loc[all_days_range]
    except KeyError as e:
        erroroutput = pd.DataFrame()
        erroroutput['num_falls'] = []
        erroroutput['num_near_falls'] = []
        erroroutput['food_consumption'] = []
        erroroutput['temperature'] = []
        erroroutput['systolic_bp'] = []
        erroroutput['diastolic_bp'] = []
        erroroutput['pulse_pressure'] = []
        erroroutput['pulse_rate'] = []
        erroroutput['date_only'] = []
    result_data.fillna(0, inplace=True)

    # undo set index
    result_data.reset_index(inplace=True)
    result_data.rename(columns={'index': 'date_only'}, inplace=True)
    # print("result data from get_num_visits_by_date\n", result_data)
    return result_data


def get_residents_options():
    return input_raw_data['patient_id'].unique().tolist()
