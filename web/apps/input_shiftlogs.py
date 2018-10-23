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

class input_shiftlogs(object):
    # input_raw_data = pd.DataFrame()
    sldao = shift_log_DAO()
    input_raw_data = sldao.get_all_logs()
    input_raw_data['datetime'] = pd.to_datetime(input_raw_data['datetime'], format='%Y-%m-%dT%H:%M:%S')
    input_raw_data['food_consumption'] = pd.to_numeric(input_raw_data['food_consumption'])
    input_raw_data['pulse_pressure'] = input_raw_data['systolic_bp'] - input_raw_data['diastolic_bp']
    input_raw_max_date = input_raw_data['datetime'].max()
    input_raw_min_date = input_raw_data['datetime'].min()
    # print(input_raw_data)
    daytime_start = datetime.time(7, 30)
    daytime_end = datetime.time(19, 30)

    # changeable parameters NOTE: should be changeable
    para_temperature_max = 37.6
    para_temperature_min = 35.5
    para_temperature_sd = 0.66
    para_pulse_pressure_max = 50

    @staticmethod
    def update_shiftlogs_data():
        input_shiftlogs.input_raw_data = input_shiftlogs.sldao.get_all_logs()
        input_shiftlogs.input_raw_data['datetime'] = pd.to_datetime(input_shiftlogs.input_raw_data['datetime'], format='%Y-%m-%dT%H:%M:%S')
        input_shiftlogs.input_raw_data['food_consumption'] = pd.to_numeric(input_shiftlogs.input_raw_data['food_consumption'])
        input_shiftlogs.input_raw_data['pulse_pressure'] = input_shiftlogs.input_raw_data['systolic_bp'] - input_shiftlogs.input_raw_data['diastolic_bp']
        input_shiftlogs.input_raw_max_date = input_shiftlogs.input_raw_data['datetime'].max()
        input_shiftlogs.input_raw_min_date = input_shiftlogs.input_raw_data['datetime'].min()

    @staticmethod
    def date_only(original_date):
        return original_date.replace(hour=0, minute=0, second=0, microsecond=0)

    @staticmethod
    def get_logs_filter_options():
        '''Returns labels and values in an array of tuples'''
        return [('No. of Falls', 'num_falls'), ('No. of Near Falls', 'num_near_falls'),
                ('Food Consumption', 'food_consumption'), ('Temperature', 'temperature'), ('Systolic//Diastolic Bp', 'sys_dia'),
                ('Pulse Pressure', 'pulse_pressure'), ('Pulse Rate', 'pulse_rate')]

    @staticmethod
    def get_relevant_data(start_date, end_date, patient_id):
        '''
        Retrieve sensor data based on location, start and end dates, and the device
        grouped=True to get grouped data for toilet visits
        '''
        # TODO: this part probably is the best to convert to retrieve from DB
        relevant_data = input_shiftlogs.input_raw_data.loc[(input_shiftlogs.input_raw_data['patient_id'] == patient_id)
                                           & (input_shiftlogs.input_raw_data['datetime'] < end_date)
                                           & (input_shiftlogs.input_raw_data['datetime'] > start_date),
                                           ['patient_id', 'datetime', 'num_falls', 'num_near_falls', 'food_consumption',
                                            'temperature', 'systolic_bp', 'diastolic_bp', 'pulse_pressure', 'pulse_rate']]
        return relevant_data

    @staticmethod
    def get_logs_by_date(start_date=input_raw_min_date, end_date=input_raw_max_date,
                         patient_id=1, time_period=None):
        """
        Function returns dates and aggregated number of times the sensor was activated
        To get day only, use time_period='Day' and to get night_only use time_period='Night'
        """

        # NOTE: last day of the returned output is not accurate if offset is used because the next day's data is needed to get the current night's data
        current_data = input_shiftlogs.get_relevant_data(start_date, end_date, patient_id)
        # print(current_data)

        # print(current_data)
        if time_period == 'Day':
            current_data = current_data.loc[(current_data['datetime'].dt.time >= input_shiftlogs.daytime_start)
                                            & (current_data['datetime'].dt.time < input_shiftlogs.daytime_end)]
        elif time_period == 'Night':
            current_data = current_data.loc[(current_data['datetime'].dt.time < input_shiftlogs.daytime_start)
                                            | (current_data['datetime'].dt.time > input_shiftlogs.daytime_end)]

        # group by date only
        current_data['date_only'] = current_data['datetime'].apply(input_shiftlogs.date_only)
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

    @staticmethod
    def get_residents_options():
        return input_shiftlogs.input_raw_data['patient_id'].unique().tolist()

    @staticmethod
    def get_shiftlog_indicators(patient_id, current_sys_time=None):
        ret_alerts = []
        if not current_sys_time:
            current_sys_time = datetime.datetime.now()

        current_sys_date = current_sys_time.date()
        three_weeks_ago = current_sys_date + datetime.timedelta(days=-21)
        one_week_ago = current_sys_date + datetime.timedelta(days=-7)
        four_weeks_ago = current_sys_date + datetime.timedelta(days=-28)

        # get data first
        current_data = input_shiftlogs.get_relevant_data(four_weeks_ago, current_sys_date,patient_id)
        # print(current_data)
        # patient_id,datetime,num_falls,num_near_falls,food_consumption,temperature,systolic_bp,diastolic_bp,pulse_pressure,pulse_rate
        # compare averages
        three_week_data = current_data.loc[(current_data['datetime'] < one_week_ago)]
        # print(three_week_data)
        past_week_data = current_data.loc[current_data['datetime'] > one_week_ago]
        # print(past_week_data)

        # check averages then check for significant out-of-range numbers
        # check temperatures
        temperature_sd = three_week_data['temperature'].std() # NOTE: maybe can change to some other stdevs
        three_week_average_temp = three_week_data['temperature'].mean()
        past_week_average_temp = past_week_data['temperature'].mean()

        if (past_week_average_temp - input_shiftlogs.para_temperature_sd * temperature_sd) > three_week_average_temp:
            ret_alerts.append("Significant increase in temperature in the past week")
        elif (past_week_average_temp + input_shiftlogs.para_temperature_sd * temperature_sd) < three_week_average_temp:
            ret_alerts.append("Significant decrease in temperature in the past week")

        if any((past_week_data['temperature'] < input_shiftlogs.para_temperature_min) | (past_week_data['temperature'] > input_shiftlogs.para_temperature_max)):
            ret_alerts.append("Abnormal temperatures detected in past week")

        return ret_alerts

# if __name__ == '__main__': # for local testing
#     input_shiftlogs.update_shiftlogs_data()
#     print("hi")
#     # print(input_shiftlogs.get_logs_by_date(datetime.datetime(2018, 10, 1, 0, 0, 0), datetime.datetime.now(), 1))
#     print(input_shiftlogs.get_shiftlog_indicators(1, datetime.datetime(2018, 10, 10, 0, 0, 0)))
