import paho.mqtt.client as mqtt     # sudo pip3 install -U paho-mqtt
import os
import datetime
import json
import sys
sys.path.append("..")
from Entities.sensor_log import Sensor_Log
from DAOs.sensor_log_DAO import sensor_log_DAO

class Consumer(object):

    def __init(self):
        self.broker_address = "192.168.1.184" 
        self.topic          = "stbern/newton"
        self.qos            = 0
        self.client_id      = 'stbern_consumer'
        self.username       = 'username'
        self.password       = 'password'

        self.LOGGING_FOLDER = "./logs"
        self.BROKER_LOG     = 'broker_log.txt'
        self.CLIENT_LOG     = 'client_log.txt'
        self.MESSAGE_LOG    = 'msg_log.txt'


    def subscribe(self, client):
        '''
        Attempts to subscribe to a topic
        
        Input:
        client (paho.mqtt.client)
        topic (str)
        qos = Quality of Service  
        '''
        try:
            (result, mid) = client.subscribe(topic=self.topic, qos=self.qos) # mid - Message id
            if result == mqtt.MQTT_ERR_SUCCESS:
                self.logger(self.CLIENT_LOG, f'SUBSCRIBE SUCCESS topic:{self.topic} result:{str(result)}')
            else:
                self.logger(self.CLIENT_LOG, f'SUBSCRIBE ERROR topic:{self.topic} result:{str(result)}')
                return -1
        except Exception as e:
            self.logger(self.CLIENT_LOG, f'SUBSCRIBE ERROR topic:{self.topic} result:{str(result)}')
            print(e)
            return -1
        

    def logger(self, filename, msg):
        '''
        healper function to write logs to filename
        
        Input:
        filename (str) - name of file to log to
        msg (str) - msg to write to file
        '''
        try:
            if not os.path.exists(self.LOGGING_FOLDER):
                os.makedirs(self.LOGGING_FOLDER)

            target_path = os.path.join(self.LOGGING_FOLDER, filename)

            with open(target_path, 'a+') as file:
                time_now = datetime.datetime.now()
                file.write(f'{time_now} {msg} \n')
        except Exception as e:
            print('Unable to write log... ' + str(e))


    def on_connect(self, client, userdata, flags, rc):
        '''
        The callback for when the client receives a CONNACK response from the server.
        '''
        self.logger(self.CLIENT_LOG, f"CONNECT SUCCESSFUL resultCode: {str(rc)}")

        # Subscribing in on_connect() means that if we lose the connection and
        # reconnect then subscriptions will be renewed.
        client.subscribe(topic=self.topic, qos=2) # Subscribe to topic

        
    def on_disconnect(self, client, userdata, rc):
        '''
        Callback for when client disconnects from broker
        '''
        if rc == mqtt.MQTT_ERR_SUCCESS:
            self.logger(self.CLIENT_LOG, f'DISCONNECT SUCCESSFUL. resultCode: {str(rc)}')
        else:
            self.logger(self.CLIENT_LOG, f'DISCONNECT UNEXPECTED. resultCode: {str(rc)}')
            client.reconnect()
        
        
    def on_subscribe(self, client, userdata, mid, granted_qos):
        '''
        Callback for when client subscribes
        '''
        self.logger(self.CLIENT_LOG, f'SUBSCRIBED to \'{self.topic}\', QoS: {granted_qos}')
        
        
    def on_log(self, client, userdata, level, buf):
        '''
        Callback for logs, pretty sure its the logs transmitted by the broker
        '''
        self.logger(self.BROKER_LOG, str(buf))
        
        
    def on_message(self, client, userdata, message):
        '''
        Callback function for when client recieves messages.
        Writes to MESSAGE_LOG folder and filters json messages. Updating db only with event msgs
        '''
        payload = str(message.payload.decode("utf-8"))
        self.logger(self.MESSAGE_LOG, msg=payload)
    #     print("message received " ,str(message.payload.decode("utf-8")))
    #     print("message topic=",message.topic)
    #     print("message qos=",message.qos)
    #     print("message retain flag=",message.retain)
        
        # Process message, only keep pertinent event update
        self.process_msg(message=payload)
        

    def process_msg(self, message):
        '''
        Process json msgs from mqtt broker. Insert only event update msgs
        
        Input:
        message (str) - A single json string
        
        Return:
        Boolean status. True if valid json, or False if invalid json
        '''
        # Load JSON
        try:
            json_obj = json.load(message)
        except Exception:
            return False
        
        # check if json is a node event
        try:
            nodeid = json_obj['nodeid']
            event = json_obj['event']
            uuid = json_obj['uuid']
            
            # Insert into DB WITH TIMESTAMP
            log = Sensor_Log(uuid=uuid, node_id=nodeid, event=event, recieved_timestamp=datetime.datetime.now())
            dao = sensor_log_DAO()
            dao.insert_sensor_log(sensor_log=log)
        except Exception as e:
            print(e)
            pass

        return True












