import datetime, os, sys
from connection_manager import connection_manager
import secrets
import string


table_name = 'stbern.resident'

def get_resident_name_by_resident_id(resident_id):
	query = 'SELECT name FROM {} WHERE resident_id = %s'.format(table_name)
	# Get connection
	factory = connection_manager()
	connection = factory.connection
	cursor = connection.cursor()

	try:
		cursor.execute(query, (resident_id, ))
		results = cursor.fetchall()
		if results: return results
		else: return None
	except: raise
	finally: factory.close_all(cursor=cursor, connection=connection)