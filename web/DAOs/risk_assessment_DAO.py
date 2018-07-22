import datetime, os
from connection_manager import connection_manager
import secrets
import string
import sys

sys.path.append('../Entities')
from risk_assesment import Risk_assesment

class risk_assesment_DAO(object):
    '''
    This class handles connection between app and the database table
    '''

    table_name = "stbern.RISK_ASSESMENT"

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

         # Get connection, which incidentally closes itself during garbage collection
        factory = connection_manager()
        connection = factory.connection

        query = """SELECT MAX({}) as 'max' , 
                          MIN({}) as 'min' 
                          FROM {};"""                         \
                    .format(Risk_assesment.datetime_tname,    \
                            Risk_assesment.datetime_tname,    \
                            risk_assesment_DAO.table_name)

        # Get cursor
        with connection.cursor() as cursor:
            cursor.execute(query)
            result = cursor.fetchone()

            #set class vars
            self.max_datetime = result['max']
            self.min_datetime = result['min']

            # return
            return result['max'], result['min']

    
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
                       %s, %s, %s, %s);""".format(risk_assesment_DAO.table_name)


        # Get connection, which incidentally closes itself during garbage collection
        factory = connection_manager()
        connection = factory.connection

        with connection.cursor() as cursor:
            try:
                cursor.execute(query, risk_assessment.tname_list + risk_assessment.var_list)
            except Exception as error:
                print(error)
                raise

    

# # TEST-1 insert
# dao = risk_assesment_DAO()
# obj = Risk_assesment(datetime.datetime.now(), 101, 64.5)
# print("Inserting obj: " + str(obj))
# dao.insert_risk_assessment(obj)

# # TEST-2 set min max
# dao.set_min_max_datetime()
# print("min - max datetime in dao: {}, {}".format(dao.min_datetime, dao.max_datetime))
