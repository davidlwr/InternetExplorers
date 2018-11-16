import datetime, os, sys
import pandas as pd
from DAOs.connection_manager import connection_manager

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
