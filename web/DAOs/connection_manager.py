'''
this file solely deals with handling connections to the database. Think of it like a connection factory
limits connections based on certain settings as follows bellow in settings section
'''

import pymysql
import os
import csv

# SHOULD throw different connections when 1. connection breaks, 2. read/write timeout
# This way you know when to retry or respawn class
# LOOK INTO IMPLEMENTING MAX CONNECTIONS AND THROWING EXCEPTION IF EXCEED
class connection_manager(object):

    def __init__(read_timeout=30, write_timeout=30, connect_timeout=30, local_infile=True, cursorclass=pymysql.cursors.DictCursor):

        # SETTINGS
        # Note: I really should move these into a settings folder file, but for now this is fine 
        # host            = "stbernsensor.cdc1tjbn622d.ap-southeast-1.rds.amazonaws.com"
        # port            = "3306"
        # username        = "IE_memeber"
        # password        = "IEgroupmember"

        host            = "localhost"
        port            = 3306
        username        = "root"
        password        = ""

        # LOOK INTO CURSORS
        self.connection = pymysql.connect(host=host,
                                          port=port,
                                          read_timeout=read_timeout,        # Timeout for reading from the connection in seconds
                                          write_timeout=write_timeout,
                                          connect_timeout=connect_timeout,
                                          local_infile=local_infile,        # Allows SQL "LOAD DATA LOCAL INFILE" command to be used
                                          user=username,
                                          passwd=password,
                                          cursorclass=cursorclass)
        # Note: Cursors are what pymysql uses interact with databases, its the equivilant to a Statement in java

    # Executes when object is garbage collected
    def __del__(self):
        '''
        Automatically attempts to close connection when object is garbage collected
        '''

        # If connection is open, close it 
        if self.connection.open:
            self.connection.close()