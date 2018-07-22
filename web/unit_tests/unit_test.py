import datetime, os, unittest
import sys

sys.path.append('../Entities')
from activity import Activity
from risk_assesment import Risk_assesment
from sensor_log import Sensor_Log
from shift_log import Shift_log
from sysmon_log import Sysmon_Log
from user import User

sys.path.append('../DAOs')
from risk_assessment_DAO import risk_assesment_DAO
from sensor_log_DAO import sensor_log_DAO
from shift_log_DAO import shift_log_DAO
from sysmon_log_DAO import sysmon_log_DAO
from user_DAO import user_DAO
from connection_manager import connection_manager


class Unit_Test(unittest.TestCase):

    # Test Entities first
    def test_entity_sensor_log(self):
        uuid = "uuid-01"
        node_id = 1
        event = 225
        ts =  datetime.datetime(year=2018, month=1, day=2, hour=1, minute=0, second=0)
        obj = Sensor_Log(uuid=uuid, node_id=node_id, event=event, recieved_timestamp=ts)

        e_flag = False
        try:
            str_rep = obj.__str__()
            self.assertEqual(obj.uuid, uuid)
            self.assertEqual(obj.node_id, node_id)
            self.assertEqual(obj.event, event)
            self.assertEqual(obj.recieved_timestamp, ts)

        except Exception as e:
            print(e)
            e_flag = True
        self.assertFalse(e_flag, 'exception thrown')


    def test_entity_activity_init_params(self):
        uuid = "ActivityUUID-321"
        start_datetime = datetime.datetime(year=2018, month=1, day=2, hour=1, minute=0, second=0)
        end_datetime = datetime.datetime(year=2018, month=1, day=2, hour=1, minute=0, second=2)
        obj = Activity(uuid=uuid, start_datetime=start_datetime, end_datetime=end_datetime)

        e_flag = False
        try:
            str_rep = obj.__str__()
            self.assertFalse(obj.in_daytime(), msg='activity not properly assigned to day or night time')
            self.assertEqual(obj.seconds, 2, msg='seconds between start and end datetime calculated wrongly')
        except Exception as e:
            print(e)
            e_flag = True
        self.assertFalse(e_flag, 'exception thrown')


    def test_entity_activity_init_from_sensor_logs(self):
        uuid1 = "uuid-01"
        node_id1 = 1
        event1 = 0
        ts1 =  datetime.datetime(year=2018, month=1, day=2, hour=1, minute=0, second=0)
        obj1 = Sensor_Log(uuid=uuid1, node_id=node_id1, event=event1, recieved_timestamp=ts1)

        uuid2 = "uuid-02"
        node_id2 = 2
        event2 = 225
        ts2 =  datetime.datetime(year=2018, month=1, day=2, hour=1, minute=0, second=2)
        obj2 = Sensor_Log(uuid=uuid2, node_id=node_id2, event=event2, recieved_timestamp=ts2)

        obja = Activity(start_log=obj1, end_log=obj2)

        e_flag = False
        try:
            str_rep = obja.__str__()
            self.assertFalse(obja.in_daytime(), msg='activity not properly assigned to day or night time')
            self.assertEqual(obja.seconds, 2, msg='seconds between start and end datetime calculated wrongly')
        except:
            e_flag = True
        self.assertFalse(e_flag, 'exception thrown')


    def test_entity_shift_log(self):
        dt = datetime.datetime(year=2018, month=1, day=2, hour=1, minute=0, second=0)
        patient_id = 111
        num_falls  = 20
        num_near_falls = 30
        food_consumption = 0
        num_toilet = 40
        temp_3pm = 50.50
        bp_weekly = 60.60
        bpm = 70
        obj = Shift_log(datetime=dt, patient_id=patient_id, num_falls=num_falls, \
                        num_near_falls=num_near_falls, food_consumption=food_consumption, \
                        num_toilet_visit=num_toilet, temp_3pm=temp_3pm, bp_weekly=bp_weekly, bpm=bpm)

        e_flag = False
        try:
            str_rep = obj.__str__()
            self.assertEqual(Shift_log.FOOD_CONSUMPTION_MAPPING[obj.food_consumption], "Insufficient", msg='food consumption mapping failed')

        except:
            e_flag = True
        self.assertFalse(e_flag, 'exception thrown')


    def test_entity_user(self):

        user = "xXxiao_shadow_flamezXx"
        name = "David Liu"
        email = "xiao_flamez@gmail.com"
        staff_type = 0
        dt = datetime.datetime(year=2018, month=1, day=2, hour=1, minute=0, second=0)

        obj = User(username=user, name=name, email=email, staff_type=staff_type, last_sign_in=dt)

        e_flag = False
        try:
            str_rep = obj.__str__()
        except:
            e_flag = True
        self.assertFalse(e_flag, 'exception thrown')


    # THESE ARE NOT FINALIZED, SYSMON DUE TO BOON THAI NOT GIVING US ACCESS TO SENSOR BROKER
    # def test_risk_assesment(self):

    # def test_sysmon_log(self):


    def test_userDAO(self):
        user = "xXxiao_shadow_flamezXx"
        passw = "passwerd"
        name = "David Liu"
        email = "xiao_flamez@gmail.com"
        staff_type = 0
        dt = datetime.datetime(year=2018, month=1, day=2, hour=1, minute=0, second=0)

        obj = User(username=user, name=name, email=email, staff_type=staff_type, last_sign_in=dt)
        dao = user_DAO()

        e_flag = False
        # Insert
        try: dao.insert_user(obj, passw)
        except Exception as e: e_flag = True
        self.assertFalse(e_flag, msg=f"insert exception")

        # Auth true
        e_flag = False
        try:
            r = dao.authenticate(username=user, password=passw)
            self.assertIsNotNone(r, msg='auth failed when should have passed')
            self.assertEqual(r.username, user, msg='failed to retrieve user from successfull auth')
            self.assertEqual(r.name, name, msg='failed to retrieve user from successfull auth')
            self.assertEqual(r.email, email, msg='failed to retrieve user from successfull auth')
            self.assertEqual(int(r.staff_type), staff_type, msg='failed to retrieve user from successfull auth')
        except Exception as e: e_flag = True
        self.assertFalse(e_flag, msg=f"auth exception 1")

        # Auth false
        e_flag = False
        try:
            r = dao.authenticate(username=user, password='wrong_pass')
            self.assertIsNone(r, msg='auth passed when should have failed')
        except Exception as e: e_flag = True
        self.assertFalse(e_flag, msg=f"auth exception 2")


    def test_sensor_log_DAO(self):
        uuid1 = "uuid-01"
        node_id1 = 1
        event1 = 0
        ts1 =  datetime.datetime(year=2018, month=1, day=2, hour=1, minute=0, second=0)
        obj1 = Sensor_Log(uuid=uuid1, node_id=node_id1, event=event1, recieved_timestamp=ts1)

        uuid2 = "uuid-01"
        node_id2 = 2
        event2 = 225
        ts2 =  datetime.datetime(year=2018, month=1, day=2, hour=1, minute=0, second=2)
        obj2 = Sensor_Log(uuid=uuid2, node_id=node_id2, event=event2, recieved_timestamp=ts2)

        dao = sensor_log_DAO()

        # test insert
        e_flag = False
        try:
            dao.insert_sensor_log(obj1)
            dao.insert_sensor_log(obj2)
        except: e_flag = True
        self.assertFalse(e_flag, msg=f"insert exception")

        # test min max datetime
        e_flag = False
        try:
            min_dt, max_dt = dao.set_min_max_datetime()
            self.assertEqual(min_dt, ts1, msg='wrong min datetime')
            self.assertEqual(max_dt, ts2, msg='wrong max datetime')
        except: e_flag = True
        self.assertFalse(e_flag, msg=f"min max datetime exception")

        # test get log
        e_flag = False
        try:
            min_dt = datetime.datetime(year=2018, month=1, day=1, hour=1, minute=0, second=2)
            max_dt = datetime.datetime(year=2018, month=1, day=3, hour=1, minute=0, second=2)
            logs = dao.get_logs(uuid1, min_dt, max_dt)
            self.assertEqual(len(logs), 2, msg='Failed to get 2 sensor logs')
        except: e_flag = True
        self.assertFalse(e_flag, msg=f"get sensor log exception")

        # test get activities per period
        e_flag = False
        try:
            min_dt = datetime.datetime(year=2018, month=1, day=1, hour=1, minute=0, second=2)
            max_dt = datetime.datetime(year=2018, month=1, day=3, hour=1, minute=0, second=2)

            # test day and night filter
            act1 = dao.get_activities_per_period(uuid1, min_dt, max_dt, time_period='Day', min_secs=1)
            self.assertEqual(len(act1), 0, msg='Day Night filter broken, should be zero')

            # test min secs filter
            act2 = dao.get_activities_per_period(uuid1, min_dt, max_dt, time_period='Night', min_secs=3)
            self.assertEqual(len(act1), 0, msg='Min secs filter broken, should be zero')

            # test correct
            act3 = dao.get_activities_per_period(uuid1, min_dt, max_dt, time_period='Night', min_secs=1)
            self.assertEqual(len(act1), 2, msg='Get activites broken, should be 2')
        except: e_flag = True
        self.assertFalse(e_flag, msg=f"get sensor log exception")


# Run tests
suite = unittest.TestLoader().loadTestsFromTestCase(Unit_Test)
unittest.TextTestRunner(verbosity=2).run(suite)
