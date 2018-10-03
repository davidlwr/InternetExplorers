import datetime, os, sys
import pandas as pd
from connection_manager import connection_manager

# from shift_log import Shift_log

table_name = 'stbern.shift_log'

	
def retrieveCountPerShift(shifttime):
	query = "SELECT patient_id FROM {} WHERE datetime = %s".format(table_name)
	# Get connection
	factory = connection_manager()
	connection = factory.connection
	cursor = connection.cursor()
	
	try:
		# cursor.execute(query, (chat_id, ))
		cursor.execute(query, (shifttime, ))
		results = cursor.fetchall()
		return results

	except: raise
	finally: factory.close_all(cursor=cursor, connection=connection)


# # TEST-1 insert
# sl_dao = shift_log_DAO()
# obj = Shift_log(datetime.datetime.now(), 101, 20)
# print("Inserting obj: " + str(obj))
# sl_dao.insert_shift_log(obj)

# # TEST-2 set min max
# sl_dao.set_min_max_datetime()
# print("min - max datetime in dao: {}, {}".format(sl_dao.min_datetime, sl_dao.max_datetime))
