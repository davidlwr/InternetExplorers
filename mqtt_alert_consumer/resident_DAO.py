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

def get_list_of_residentNames(filter_active=True, location_filter=None):
	'''
	Returns list of residents (each resident is a dictionary)
	NOTE: returned node_id is in string
	Default selects only active residents
	'''
	query = 'SELECT distinct(name) FROM {}'.format(table_name)
	if filter_active:
		query += " WHERE status = 'Active'"

	# if location_filter:
	# TODO:
	# NOTE: not implemented yet
	# pass
	# query +=

	# Get connection
	factory = connection_manager()
	connection = factory.connection
	cursor = connection.cursor()

	try:
		cursor.execute(query)
		results = cursor.fetchall()
		# have to try printing this
		if results:
			return results
		else:
			return None
	except:
		raise
	finally:
		factory.close_all(cursor=cursor, connection=connection)

# def main():
    # print(resident['name'] for resident in get_list_of_residentNames())

# if __name__ == '__main__':
    # main()