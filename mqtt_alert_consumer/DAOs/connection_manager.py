import pymysql
import os
import csv
import sys

class connection_manager(object):
    '''
    Class solely deals with handling connections to the database. Think of it like a connection factory
    limits connections based on certain settings as follows bellow in settings section
    '''

    def __init__(self, read_timeout=30, write_timeout=30, connect_timeout=30, local_infile=True, cursorclass=pymysql.cursors.DictCursor):

        host            = "127.0.0.1"
        if sys.platform == 'linux': host = "stbern.cap7ipqft3z9.ap-southeast-1.rds.amazonaws.com:3306"
        port            = 3306
        database        = "stbern"
        username        = "internetexplorer"
        password        = "int3rn3t"

        # LOOK INTO CURSORS
        self.connection = pymysql.connect(host=host,
                                          port=port,
                                          db=database,
                                          read_timeout=read_timeout,        # Timeout for reading from the connection in seconds
                                          write_timeout=write_timeout,
                                          connect_timeout=connect_timeout,
                                          local_infile=local_infile,        # Allows SQL "LOAD DATA LOCAL INFILE" command to be used
                                          user=username,
                                          passwd=password,
                                          cursorclass=cursorclass,
                                          autocommit=True)
        # Note: Cursors are what pymysql uses interact with databases, its the equivilant to a Statement in java


    def close_all(self, cursor=None, connection=None):
        '''
        Helper method to close cursor and connection
        '''
        if cursor is not None:
            cursor.close()
        connection.close()
