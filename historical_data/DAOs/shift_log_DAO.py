import datetime, os, sys
import pandas as pd

if __name__ == '__main__':  sys.path.append("..")
from DAOs.connection_manager import connection_manager

sys.path.append('../Entities')
from Entities.shift_log import Shift_log
from datetime import datetime, date, time, timedelta


class shift_log_DAO(object):
    '''
    This class handles connection between app and the database table
    '''

    table_name = "stbern.shift_log"

    def __init__(self):
        '''
        Constructor
        '''
        self.min_datetime = None
        self.max_datetime = None
        self.set_min_max_datetime()

    def set_min_max_datetime(self):
        '''
        Sets obj vars and returns max_datetime and min_datetime found in the database

        Returns:
        (max_datetime, min_datetime) or (None, None) if nothing found
        '''
        query = """SELECT MAX({}) as 'max' ,
                          MIN({}) as 'min'
                          FROM {};""" \
            .format(Shift_log.datetime_tname, \
                    Shift_log.datetime_tname, \
                    shift_log_DAO.table_name)

        # Get connection
        factory = connection_manager()
        connection = factory.connection
        cursor = connection.cursor()

        try:
            cursor.execute(query)
            result = cursor.fetchone()

            # set class vars
            if result != None:
                self.max_datetime = result['max']
                self.min_datetime = result['min']
                return result['max'], result['min']
            else:
                return None, None

        except:
            print("error")
        finally:
            factory.close_all(cursor=cursor, connection=connection)

    def insert_shift_log(self, shift_log):
        '''
        Inserts an entry into the database table

        Keyword arguments:
        shift_log -- Entities.shift_log, class vars used to create a new DB row
        '''
        query = """INSERT INTO {} VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""" \
            .format(shift_log_DAO.table_name)

        # Get connection
        factory = connection_manager()
        connection = factory.connection
        cursor = connection.cursor()

        try:
            cursor.execute(query, shift_log.var_list)
        except:
            raise
        finally:
            factory.close_all(cursor=cursor, connection=connection)

    def get_all_logs(self):
        """
        Returns all logs in a dataframe
        """

        query = "SELECT * FROM {}".format(shift_log_DAO.table_name)

        # Get connection
        factory = connection_manager()
        connection = factory.connection
        try:
            return pd.read_sql_query(query, connection)
        except:
            raise
        finally:
            factory.close_all(connection=connection)

    def get_today_logs(self):
        current_datetime = datetime.today()
        reset_datetime = datetime.combine(date.today(), time(10))
        query_date = datetime.combine(date.today(), time(0))
        if current_datetime < reset_datetime:
            query_date = datetime.combine(date.today() - timedelta(1), time(0))

        query = "SELECT count(*) FROM {} where `datetime` > '{}'".format(shift_log_DAO.table_name, query_date)
        factory = connection_manager()
        connection = factory.connection
        cursor = connection.cursor()

        try:
            cursor.execute(query)
            result = cursor.fetchone()
            return result['count(*)']
        except:
            print("error")
        finally:
            factory.close_all(cursor=cursor, connection=connection)

    def get_incompleted_residents(self):
        current_datetime = datetime.today()
        # current_datetime = datetime(2018, 10, 21, 13, 59)
        night_shift_end = datetime.combine(date.today(), time(10))
        day_shift_end = datetime.combine(date.today(), time(21))
        start_datetime = datetime.combine(date.today(), time(12))
        if current_datetime < night_shift_end:
            start_datetime = datetime.combine(date.today() - timedelta(1), time(20))

        if current_datetime > day_shift_end:
            start_datetime = datetime.combine(date.today(), time(20))

        query = "SELECT name, resident_id FROM resident where resident_id not in (select patient_id from {} where datetime =  '{}')".format(shift_log_DAO.table_name, start_datetime)
        factory = connection_manager()
        connection = factory.connection
        cursor = connection.cursor()

        try:
            cursor.execute(query)
            rows = cursor.fetchall()
            return rows
        except:
            print("error")
        finally:
            factory.close_all(cursor=cursor, connection=connection)

    @staticmethod
    def get_all_temp_pulse(sdt=None, edt=None):
        """
        Returns all logs in the shift forms DB, sorted by date

        ----- RETURNS: 
                pd.Series. Cols: "temperature", "pulse_rate", "datetime"
        """
        feeddict = []
        query = f"SELECT {Shift_log.datetime_tname}, {Shift_log.temp_tname}, {Shift_log.patient_id_tname}, \
                  ({Shift_log.sbp_tname} - {Shift_log.dbp_tname}) AS 'pulse_rate' "
        query += f"FROM {shift_log_DAO.table_name} "

        if sdt != None and edt != None:
            query += f"WHERE {Shift_log.datetime_tname} >= %s AND {Shift_log.datetime_tname} <= %s "
            feeddict = [sdt,edt]

        query += f" ORDER BY {Shift_log.datetime_tname} ASC"

        # Get connection
        factory = connection_manager()
        connection = factory.connection
        try:
            return pd.read_sql_query(query, connection, params=feeddict)
        except:
            raise
        finally:
            factory.close_all(connection=connection)

# # TEST-1 insert
# sl_dao = shift_log_DAO()
# obj = Shift_log(datetime.datetime.now(), 101, 20)
# print("Inserting obj: " + str(obj))
# sl_dao.insert_shift_log(obj)

# # TEST-2 set min max
# sl_dao.set_min_max_datetime()
# print("min - max datetime in dao: {}, {}".format(sl_dao.min_datetime, sl_dao.max_datetime))
