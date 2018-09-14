import datetime, os, sys

if __name__ == '__main__':  sys.path.append("..")
from DAOs.connection_manager import connection_manager
from Entities.resident import Resident


class resident_DAO(object):
    
    table_name = 'stbern.RESIDENT'

    @staticmethod
    def get_resident_by_node_id(node_id):
        '''
        Returns a resident based on node_id. Returns only the first found

        Inputs:
        node_id (str)

        Returns:
        Resident (Entities.Resident)
        '''
        query = f'SELECT * FROM {resident_DAO.table_name} WHERE `{Resident.node_id_tname}` = %s'

        # Get connection
        factory = connection_manager()
        connection = factory.connection
        cursor = connection.cursor()

        try:
            cursor.execute(query, [node_id])
            r = cursor.fetchone()
            return Resident(name=r[Resident.name_tname], node_id=r[Resident.node_id_tname],                     \
                            age=r[Resident.age_tname], fall_risk=r[Resident.fall_risk_tname],                   \
                            status=r[Resident.status_tname], stay_location=r[Resident.stay_location_tname],     \
                            resident_id=r[Resident.resident_id_tname])
        except: raise
        finally: factory.close_all(cursor=cursor, connection=connection)


    @staticmethod
    def get_resident_by_resident_id(resident_id):
        '''
        Returns a resident based on resident_id. Returns only first row found

        Inputs:
        resident_id (int)

        Returns
        Resident (Entitites.Resident)
        '''
        query = f'SELECT * FROM {resident_DAO.table_name} WHERE `{Resident.resident_id_tname}` = %s'

        # Get connection
        factory = connection_manager()
        connection = factory.connection
        cursor = connection.cursor()

        try:
            cursor.execute(query, (resident_id, ))
            r = cursor.fetchone()
            return Resident(name=r[Resident.name_tname], node_id=r[Resident.node_id_tname],                     \
                            age=r[Resident.age_tname], fall_risk=r[Resident.fall_risk_tname],                   \
                            status=r[Resident.status_tname], stay_location=r[Resident.stay_location_tname],     \
                            resident_id=r[Resident.resident_id_tname])
        except: raise
        finally: factory.close_all(cursor=cursor, connection=connection)


    @staticmethod
    def get_residents_by_active_and_location(filter_active=True, location_filter=None):
        '''
        Returns a list of Residents filtered based on cols `active` andor `location`

        Inputs:
        filter_active (str)   -- default True: selects only active residents
        location_filter (str) -- default None

        Returns:
        List of Residents (Entities.Resident) or None
        '''
        query = f'SELECT * FROM {resident_DAO.table_name}'
        if filter_active: query += " WHERE status = \"Active\""

        # Get connection
        factory = connection_manager()
        connection = factory.connection
        cursor = connection.cursor()

        try:
            cursor.execute(query)
            results = cursor.fetchall()
            if results != None:
                residents = []
                for r in results:
                    residents.append(Resident(name=r[Resident.name_tname], node_id=r[Resident.node_id_tname],                     \
                                              age=r[Resident.age_tname], fall_risk=r[Resident.fall_risk_tname],                   \
                                              status=r[Resident.status_tname], stay_location=r[Resident.stay_location_tname],     \
                                              resident_id=r[Resident.resident_id_tname]))
                return residents
            else: return None       # Normally I would return an empty list, but Jed seems to want None
        except: raise
        finally: factory.close_all(cursor=cursor, connection=connection)


    @staticmethod
    def insert_resident(name, node_id, age, fall_risk=None, status="Active", stay_location="STB"):
        '''
        Returns the id of the inserted resident if successful
        '''
        query = f'''INSERT INTO {resident_DAO.table_name} 
                     (`{Resident.name_tname}`, `{Resident.node_id_tname}`, `{Resident.age_tname}`,
                      `{Resident.fall_risk_tname}`, `{Resident.status_tname}`, `{Resident.stay_location_tname}`) 
                     VALUES (%s, %s, %s, %s, %s, %s)'''
        values = (name, node_id, age, fall_risk, status, stay_location)

        # Get connection
        factory = connection_manager()
        connection = factory.connection
        cursor = connection.cursor()

        try:
            cursor.execute(query, values)
            return cursor.lastrowid
        except: raise
        finally: factory.close_all(cursor=cursor, connection=connection)

