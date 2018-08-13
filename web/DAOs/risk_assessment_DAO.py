import datetime, os
from DAOs.connection_manager import connection_manager
import secrets
import string
import sys

from Entities.risk_assessment import Risk_assessment

class risk_assessment_DAO(object):
    '''
    This class handles connection between app and the database table
    '''

    table_name = "stbern.RISK_ASSESSMENT"

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
        '''

        query = """SELECT MAX({}) as 'max' , 
                          MIN({}) as 'min' 
                          FROM {};"""                         \
                    .format(Risk_assessment.datetime_tname,    \
                            Risk_assessment.datetime_tname,    \
                            risk_assessment_DAO.table_name)

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
            else: return None, None

        except: raise
        finally: factory.close_all(cursor=cursor, connection=connection)

    
    def insert_risk_assessment(self, risk_assessment):
        '''
        Inserts an entry into the database table

        Keyword arguments:
        shift_log -- Entities.risk_assessment, class vars used to create a new DB row
        '''

        query = """INSERT INTO {} 
                VALUES(%s, %s, %s, %s, %s, %s,
                       %s, %s, %s, %s, %s, %s,
                       %s, %s, %s, %s, %s, %s,
                       %s, %s, %s, %s, %s, %s,
                       %s, %s, %s, %s, %s);""".format(risk_assessment_DAO.table_name)

        # Get connection
        factory = connection_manager()
        connection = factory.connection
        cursor = connection.cursor()

        try:
            cursor.execute(query, risk_assessment.tname_list + risk_assessment.var_list)
        except: raise
        finally: factory.close_all(cursor=cursor, connection=connection)

    

# # TEST-1 insert
# dao = risk_assesment_DAO()
# obj = Risk_assesment(datetime.datetime.now(), 101, 64.5)
# print("Inserting obj: " + str(obj))
# dao.insert_risk_assessment(obj)

# # TEST-2 set min max
# dao.set_min_max_datetime()
# print("min - max datetime in dao: {}, {}".format(dao.min_datetime, dao.max_datetime))
