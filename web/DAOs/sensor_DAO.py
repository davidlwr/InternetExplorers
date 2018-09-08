import sys

if __name__ == '__main__':  sys.path.append("..")
from DAOs.connection_manager import connection_manager
from Entities.sensor import Sensor

class sensor_DAO(object):
    """
    This class handles the connection between the app and the datebase table
    """
    table_name = "stbern.SENSOR"


    @staticmethod
    def insert_sensor(sensor):
        """
        INSERTs a sensor entry into the database

        Inputs:
        sensor (Entities.sensor)
        """
        query = f"INSERT INTO `{sensor_DAO.table_name}` (`uuid`,`type`,`location`,`description`) VALUES (%s, %s, %s, %s)"

        # Get connection
        factory = connection_manager()
        connection = factory.connection
        cursor = connection.cursor()

        try:
            cursor.execute(query, sensor.var_list)
        except: raise
        finally: factory.close_all(cursor=cursor, connection=connection)


    @staticmethod
    def get_all_sensors():
        """
        Returns a list of all rows in the table
        """
        query = f"SELECT * FROM {sensor_DAO.table_name}"

        # Get connection
        factory = connection_manager()
        connection = factory.connection
        cursor = connection.cursor()

        try:
            cursor.execute(query)
            result = cursor.fetchall()

            sensors = []
            if result != None:
                for r in result:
                    sensors.append(Sensor(uuid=r[Sensor.uuid_tname], type=r[Sensor.type_tname], location=r[Sensor.locaiton_tname], description=r[Sensor.description_tname]))
            return sensors
        except: raise
        finally: factory.close_all(cursor=cursor, connection=connection)


if __name__ == '__main__': 
    ss = sensor_DAO.get_all_sensors()
    for s in ss: print(s)