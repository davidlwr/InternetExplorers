import requests
from datetime import datetime
from datetime import timedelta
from dateutil import parser
from dateutil import tz

# MODULES USED: 'python-dateutil'

# WARNING: Datetime objects returned by the functions tend to have UTC timezone.
# This is not an error, API returns SGT time but in UTC format for some retarded reason.
 
class JuvoAPI(object):
    
    UTC_TZ = tz.gettz('UTC')
    SGT_TZ = tz.gettz('Asia/Singapore')
    BT_TIME_OFFSET = 0    # In seconds: offset = realTime - boonTime
    
    BASE_URL = 'https://api-staging.juvolabs.com/api/v1/mobile'
    USERNAME = 'boon@lvely.co'
    PASSWORD = 'boon'

    ACCESS_TOKEN  = None
    REFRESH_TOKEN = None
    EXPIRY_DATETIME = None    # datetime obj, in realtime sgt
    
    # Utility functions ================================================================================================
    @classmethod
    def utc_to_sgt(cls, utc):
        '''
        Converts a string representation of UTC time to SGT time.        
        Inputs:
        utc (str) || (datetime) -- string datetime of UTC format

        Return:
        SGT_datetime (datetime) -- datetime obj of singapore time
        '''
        if isinstance(utc, str): 
            utc = parser.parse(utc).replace(tzinfo=cls.UTC_TZ)
        elif utc.tzinfo == None: # Is datetime check tzinfo is there
            utc = utc.replace(tzinfo=cls.UTC_TZ)

        return utc.astimezone(cls.SGT_TZ)
    
    # Turns out UTC time given by the API is FAKE, its just SGT Time but with in the wrong (UTC) format
    @classmethod
    def sgt_to_utc(cls, sgt):
        '''
        Converts a string representation of SGT time to UTC time.
        Inputs:
        sgt (str) || (datetime) -- string datetime of SGT format

        Return:
        SGT_datetime (datetime) -- datetime obj of singapore time
        '''
        if isinstance(sgt, str): 
            sgt = parser.parse(sgt).replace(tzinfo=cls.SGT_TZ)
        elif sgt.tzinfo == None: # Is datetime check tzinfo is there
            sgt = sgt.replace(tzinfo=cls.SGT_TZ)

        return sgt.astimezone(cls.UTC_TZ)
        
    @classmethod
    def sudo_utc_datetime(cls, date):
        '''
        Converts a datetime to a sudo UTC time without changing anything (numbers)
        Because the API takes and returns UTC format wrongly (SGT time in UTC format)

        Inputs:
        date (datetime) || (str) 

        Returns 
        date (datetime) but with UTC timezone. call date.isoformat() to get UTC timestring
        '''
        if isinstance(date, str): 
            date = parser.parse(date).replace(tzinfo=cls.UTC_TZ)
        
        if date.tzinfo == None: # Is datetime check tzinfo is there
            date = date.replace(tzinfo=cls.UTC_TZ)
        
        return date
    
    
    # API call functions ================================================================================================
    @classmethod
    def signin(cls):
        '''
        Sets class variables:
        'ACCESS_TOKEN', 'REFRESH_TOKEN', 'EXPIRY_DATETIME', 'BT_TIME_OFFSET'
        
        Return:
        'True' if login response 200, 'False' if any other response code 
        '''
        url = cls.BASE_URL + "/signin/"
        headers = {'Content-Type': 'application/json'}
        body = f'{{ "email": "{cls.USERNAME}", "password": "{cls.PASSWORD}" }}'
        
        r = requests.post(url, data=body, headers=headers)
        
        if r.status_code != 200: return False
        
        r_dict = r.json()
        cls.ACCESS_TOKEN  = r_dict['data']['access_token']
        cls.REFRESH_TOKEN = r_dict['data']['refresh_token']
        date              = cls.sudo_utc_datetime(r_dict['date'])
        expiry_time       = r_dict['data']['expiry_time']
        
        # set offset, because Juvo API is off current time by like 15 mins
        cls.BT_TIME_OFFSET = (datetime.now().replace(tzinfo=cls.UTC_TZ) - date).total_seconds()
        
        # Set expiry datetime, date + BT_OFFSET + expiry_time
        cls.EXPIRY_DATETIME = date + timedelta(seconds=cls.BT_TIME_OFFSET) + timedelta(seconds=expiry_time)
        return True

    
    @classmethod
    def refresh_token(cls):
        '''
        Attempts to refresh token.
        
        Return:
        True if successfull
        False if unsuccessfull
        '''
        # Check if REFRESH_TOKEN is not None, if None, singin has not been run
        if cls.REFRESH_TOKEN == None: return cls.signin()
        
        url = cls.BASE_URL + "/refresh/"
        headers = {'Content-Type': 'application/json'}
        body = f'{{ "refresh_token": "{cls.REFRESH_TOKEN}" }}'
        r = requests.post(url, data=body, headers=headers)
        
        # Invalid refresh token (400), likely expired. Rerun signin
        if r.status_code != 200: return cls.signin()
        
        # Refresh successfull
        r_dict = r.json()
        cls.ACCESS_TOKEN  = r_dict['data']['access_token']
        cls.REFRESH_TOKEN = r_dict['data']['refresh_token']
        cls.EXPIRY_DATETIME = cls.sudo_utc_datetime(r_dict['date']) + timedelta(seconds=cls.BT_TIME_OFFSET) + timedelta(seconds=r_dict['data']['expiry_time'])
        return True
    
    
    @classmethod
    def token_precheck(cls):
        '''
        Check current token class var. If None or expired, attempts to signin or refresh token. 
        
        Return:
        True -- Successful signin or refresh
        False -- Unsuccessful signin or refresh
        '''
        # Check if ACCESS_TOKEN is not None, if None, singin has not been run
        if cls.ACCESS_TOKEN == None: return cls.signin()
    
        # Check if ACCESS_TOKEN is not expired
        now = cls.sudo_utc_datetime(datetime.now())
        if now <= cls.EXPIRY_DATETIME: return cls.refresh_token()
        
        
    @classmethod
    def get_sensors(cls):
        '''
        Returns a dict if successfull, None if response code is anything other than 200
        Note: Target field in successfull return is important
        
        Return:
        {
            "date": "2018-07-23T15:34:33.304848Z",
            "data": {
                "sensors": [
                    {
                        "timezone": "Asia/Singapore",
                        "sensor_id": 270,
                        "name": null,
                        "mac_address": "ACCF23CF99BC",
                        "photo": null,
                        "juvo_device_id": "CF99BC125F3A",
                        "type": "Adult",
                        "target": 460
                    }
                ]
            },
            "error_code": 0
        }

        or None if failed
        '''
        
        # Precheck
        precheck_status = cls.token_precheck()
        if not precheck_status: return None 
            
        # API 
        url = cls.BASE_URL + "/sensors"
        headers = {"Content-Type": "application/json",
                   "Authorization": f"Bearer {cls.ACCESS_TOKEN}"}
        r = requests.post(url, headers=headers)
        
        # Failed call
        if r.status_code != 200: return None
        
        # Successfull call
        return r.json()
     
        
    @classmethod
    def get_target_environ_stats(cls, target, start_time, end_time):
        '''
        Inputs:
        target (int)
        start_time (datetime) -- SGT timezone
        end_time (datetime)   -- SGT timezone

        Returns:
        {
            “date”: “2017-12-05T04:06:46.314903Z”,
            “error_code”: 0,
            "data": {
                "stats": [
                    {
                        "brightness": 100,
                        "local_end_time": "2017-12-04T14:32:34Z",
                        "local_start_time": "2017-12-04T14:27:34Z",
                        "noise": 10,
                        "stats_id": 1,
                        "temperature": 30,
                        "timezone": "Asia/Singapore"
                    },
                ]
            }
        }

        or None if unsuccessfull
        '''
        # Precheck
        precheck_status = cls.token_precheck()
        if not precheck_status: return None 
            
        # API 
        url = f"{cls.BASE_URL}/targets/{target}/envstats/"
        headers = {"Content-Type": "application/json",
                   "Authorization": f"Bearer {cls.ACCESS_TOKEN}"}
        payload = {'start_time': cls.sudo_utc_datetime(start_time).isoformat(),
                   'end_time': cls.sudo_utc_datetime(end_time).isoformat()}
        r = requests.post(url, headers=headers, json=payload)
        
        # Failed call
        if r.status_code != 200: return None
        
        # Successfull call
        return r.json()
    
    
    @classmethod
    def get_target_sleeps(cls, target, start_time, end_time):
        '''
        Inputs:
        target (int)
        start_time (datetime) -- SGT timezone
        end_time (datetime)   -- SGT timezone
        
        Returns:
        {
            “date”: “2017-12-05T04:06:46.314903Z”,
            “error_code”: 0,
            "data": {
                "sleeps": [
                    {
                        "local_end_time": "2017-12-04T08:04:51Z",
                        "local_start_time": "2017-12-04T08:04:50Z",
                        "sleep_id": 1,
                        "sleep_state": "Awake",
                        "timezone": "Asia/Singapore"
                    },
                ]
            }
        }
        or None if call is unsuccessfull
        '''
        # Precheck
        precheck_status = cls.token_precheck()
        if not precheck_status: return None 
            
        # API 
        url = f"{cls.BASE_URL}/targets/{target}/sleep/"
        headers = {"Content-Type": "application/json",
                   "Authorization": f"Bearer {cls.ACCESS_TOKEN}"}
        payload = {'start_time': cls.sudo_utc_datetime(start_time).isoformat(),
                   'end_time': cls.sudo_utc_datetime(end_time).isoformat()}
        r = requests.post(url, headers=headers, json=payload)
        
        # Failed call
        if r.status_code != 200: return None
        
        # Successfull call
        return r.json()
    
    
    @classmethod
    def get_target_sleep_summaries(cls, target, start_date, end_date):
        '''
        Inputs:
        target (int)
        start_date (datetime) -- SGT timezone
        end_date (datetime)   -- SGT timezone
        
        Returns:
        {
                "sleep_summaries": [
                    {
                        "awake": 0,
                        "date": "2017-12-04",
                        "deep": 0,
                        "light": 0,
                        "rem": 0,
                        "score": 10,
                        "sleep_summary_id": 1
                    },
                ]
            }
        }

        or None if call is unsuccessfull
        '''
        # Precheck
        precheck_status = cls.token_precheck()
        if not precheck_status: return None 
            
        # API 
        url = f"{cls.BASE_URL}/targets/{target}/sleepsummary/"
        headers = {"Content-Type": "application/json",
                   "Authorization": f"Bearer {cls.ACCESS_TOKEN}"}
        payload = {'start_date': cls.sudo_utc_datetime(start_date).strftime('%Y-%m-%d'),
                   'end_date': cls.sudo_utc_datetime(end_date).strftime('%Y-%m-%d')}
        r = requests.post(url, headers=headers, json=payload)
        
        # Failed call
        if r.status_code != 200: return None
        
        # Successfull call
        return r.json()
        

    @classmethod
    def get_target_sleep_times(cls, target, start_date, end_date):
        '''
        Inputs:
        target (int)
        start_date (datetime) -- SGT timezone
        end_date (datetime)   -- SGT timezone
        
        Returns:
        {
            “date”: “2017-12-05T04:06:46.314903Z”,
            “error_code”: 0,
            "data": {
                "sleep_times": [
                    {
                        "date": "2017-12-04",
                        "local_end_time": "2017-12-05T06:00:00Z",
                        "local_start_time": "2017-12-04T22:00:00Z",
                        "sleep_time_id": 1,
                        "timezone": "Asia/Singapore"
                    },
                ]
            }
        }
        or None if call is unsuccessfull
        '''
        # Precheck
        precheck_status = cls.token_precheck()
        if not precheck_status: return None 
            
        # API 
        url = f"{cls.BASE_URL}/targets/{target}/sleeptime/"
        headers = {"Content-Type": "application/json",
                   "Authorization": f"Bearer {cls.ACCESS_TOKEN}"}
        payload = {'start_date': cls.sudo_utc_datetime(start_date).strftime('%Y-%m-%d'),
                   'end_date': cls.sudo_utc_datetime(end_date).strftime('%Y-%m-%d')}
        r = requests.post(url, headers=headers, json=payload)

        # Failed call
        if r.status_code != 200: return None
        
        # Successfull call
        return r.json()
        

    @classmethod
    def get_target_vitals(cls, target, start_time, end_time):
        '''
        Inputs:
        target (int)
        start_date (datetime) -- SGT timezone
        end_date (datetime)   -- SGT timezone
        
        Returns:
        {
            {
            "date":"2018-03-07T09:51:46.150524Z",
            "data":{
                "epoch_metrics":[
                    {
                        "vital_id":4,
                        "local_start_time":"2018-03-06T18:45:00Z",
                        "local_end_time":"2018-03-06T18:50:00Z",
                        "heart_rate":0.0,"breathing_rate":0.0,
                        "sensor_status":"Out of bed",
                        "high_movement_rejection_breathing":false,
                        "high_movement_rejection_heartbeat":false
                    }
                ]
            }
            }
        }

        or None if call is unsuccessfull
        '''
        # Precheck
        precheck_status = cls.token_precheck()
        if not precheck_status: return None 
            
        # API 
        url = f"{cls.BASE_URL}/targets/{target}/sleep/"
        headers = {"Content-Type": "application/json",
                   "Authorization": f"Bearer {cls.ACCESS_TOKEN}"}
        payload = {'start_time': cls.sudo_utc_datetime(start_time).isoformat(),
                   'end_time': cls.sudo_utc_datetime(end_time).isoformat()}
        r = requests.post(url, headers=headers, json=payload)
        
        # Failed call
        if r.status_code != 200: return None
        
        # Successfull call
        return r.json()


    # Specific functions ================================================================================================
    @classmethod
    def get_sleep_period_by_day(cls, target, start_date, end_date):
        '''
        Gets the start and end datetimes of sleep periods for each day within the start and end date. SGT time
        Note: Juvo considers sleep of 1st Feb to also include 00:00 of 2nd Feb until awakening

        Inputs:
        target: (int)
        start_date (datetime)
        end_date (datetime)

        Return:
        Array of tuples containing datetimes: [(start_dt,end_dt), (start_dt,end_dt)]
        [] if no result, None if error 
        '''
        json = cls.get_target_sleep_times(target, start_date, end_date)

        # Check if API call failed
        if json == None: return None

        # Array 
        sleep_times = json['data']['sleep_times']

        ret = []
        for j in sleep_times:
            start_dt = cls.sudo_utc_datetime(j['local_start_time'])
            end_dt   = cls.sudo_utc_datetime(j['local_end_time'])
            ret.append((start_dt, end_dt))
        return ret


    @classmethod
    def get_qos_by_day(cls, target, start_date, end_date):
        '''
        Returns Quality of Sleep by day. SGT time
        Formula: (awake + light_sleep * 0.5) / total_sleep_period
        Note: Period of sleep i.e. for 1st of Feb looks also at 2nd feb 00:00++ until awakening 

        Input:
        target (int)
        start_date (datetime)
        end_date (datetime)

        Return array of tuples: [(datetime, QOS), (datetime, QOS)]
        [] if no result, None if error
        '''
        json = cls.get_target_sleep_summaries(target, start_date, end_date)

        # Check if API call failed
        if json == None: return None

        # Array
        sleep_sum = json['data']['sleep_summaries']

        ret = []
        for j in sleep_sum:
            date = cls.sudo_utc_datetime(j['date'])
            score = j['score']    # QOS score
            ret.append((date, score))

        return ret


    @classmethod
    def get_total_sleep_by_day(cls, target, start_date, end_date):
        '''
        Returns total sleep time per date. SGT time
        Note: Period of sleep i.e. for 1st of Feb looks also at 2nd feb 00:00++ until awakening 

        Input:
        target (int)
        start_date (datetime)
        end_date (datetime)

        Return array of tuples: [(datetime, secs), (datetime, secs)]
        [] if no result, None if error
        '''
        json = cls.get_target_sleep_summaries(target, start_date, end_date)

        # Check if API call failed
        if json == None: return None

        # Array
        sleep_sum = json['data']['sleep_summaries']

        ret = []
        for j in sleep_sum:
            date = cls.sudo_utc_datetime(j['date'])
            light = j['light']
            deep = j['deep']
            rem = j['rem']    

            ret.append((date, light+deep+rem))

        return ret


    @classmethod
    def get_sleep_series_by_day(cls, target, date):
        '''
        Returns a sorted array of periods of a user's sleep by day. SGT time
        Note: Period of sleep i.e. for 1st of Feb looks also at 2nd feb 00:00++ until awakening 
        
        States >> 'Light', 'Awake', 'Deep'. (No Detection periods removed)

        returns 2 arrays                            
        1. Array of datetime tuples  [(start_datetime, end_datetime)...]
        2. Array of str states ['Light', 'Deep'...]
        '''
        # Find start and endtimes of sleep for dates
        periods = cls.get_sleep_period_by_day(target, date, date)
        if periods == None: return None     # Check for API error
        
        # Use found start and end times to get periods
        s_dt, e_dt = periods[0]
        json = cls.get_target_sleeps(target, s_dt, e_dt)
        if json == None: return None       # Check for API erro
        sleeps = json['data']['sleeps']    # Array result

        # Accumulate unsorted periods returned from API 
        periods = []    
        states  = []
        for period in sleeps:      # wtf is scope?
            s_dt = cls.sudo_utc_datetime(period['local_start_time'])
            e_dt = cls.sudo_utc_datetime(period['local_end_time'])
            periods.append((s_dt,e_dt))
            states.append(period['sleep_state'])

        # Sort periods and states by start_date
        sorted_zip = list(zip(periods,states))      #[((s_dt,e_dt), state),...]
        sorted_zip.sort(key=lambda tup: tup[0][0])  # Sort by s-dt: start_datetime, ascending

        # Remove 'No Detection' states
        sorted_zip = [((s,e),state) for (s,e),state in sorted_zip if state != 'No Detection']

        # Merge Periods if states are equal, and edge datetimes are equal i.e. e_dt0 == s_dt1
        for i in range(len(sorted_zip)-1, 1, -1):    # Going backwards so delete is easier
            (s1,e1),state1 = sorted_zip[i]
            (s2,e2),state2 = sorted_zip[i-1]

            if e2 == s1 and state1 == state2:       # Matching periods
                sorted_zip.pop(i)                   # Remove period
                sorted_zip.pop(i-1)                 # Remove period
                sorted_zip.insert(i-1, ((s2,e1),state1))  # Insert combined period

        # Resplit
        periods = [(s,e) for (s,e),state in sorted_zip]
        states  = [state for (s,e),state in sorted_zip]

        return periods, states


# Testing user defined methods- Checked against postman ================================================================
if __name__ == "__main__":
    start_date = parser.parse('2018-08-07 12:00') 
    end_date   = parser.parse('2018-08-09 12:00')
    target = 460

    sleep_period = JuvoAPI.get_sleep_period_by_day(target=target, start_date=start_date, end_date=end_date)
    sleep_period = [(s.strftime("%Y-%m-%d %H:%M:%S"), e.strftime("%Y-%m-%d %H:%M:%S")) for s,e in sleep_period]
    print('sleep_period: '.ljust(30), sleep_period)

    qos = JuvoAPI.get_qos_by_day(target=target, start_date=start_date, end_date=end_date)
    qos = [(d.strftime("%Y-%m-%d %H:%M:%S"),q) for d,q in qos]
    print('QOS: '.ljust(30), qos)

    total_sleep = JuvoAPI.get_total_sleep_by_day(target=target, start_date=start_date, end_date=end_date)
    total_sleep = [(d.strftime("%Y-%m-%d %H:%M:%S"),s) for d,s in total_sleep]
    print('total_sleep:'.ljust(30), total_sleep)

    # Somehow total sleep from 'sleep summary' API does not match total time between 'sleep period' API so...

    periods, states = JuvoAPI.get_sleep_series_by_day(target=target, date=start_date)
    periods = [(s.strftime("%Y-%m-%d %H:%M:%S"), e.strftime("%Y-%m-%d %H:%M:%S")) for s,e in periods]
    print(f'series {len(periods)}: '.ljust(30), periods)
    print(f'states {len(states)}: '.ljust(30), states)


