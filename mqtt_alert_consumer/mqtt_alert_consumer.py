
import paho.mqtt.client as mqttClient
import time
import os
import errno
import requests
import json
import datetime
import pymysql

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler
# from dbhelper import DBHelper
from DAOs import alert_DAO
from DAOs import resident_DAO

from pprint import pprint
import time
import datetime
import json
from urllib.request import urlopen

# Global Vars ==========================================================
# MQTT Stuff
BROKER_ADDRESS = "52.221.241.44"  # Broker address
PORT           = 1883                    # Broker port
USER           = "stbern"                # username
PASSWORD       = "int3rn3t"              # password
TOPIC          = "#"        # Wildcard subscribe to everything
QOS            = 2          
TXT_FOLDER     = "./logs"
LOGGING_FILE   = f"{TXT_FOLDER}/log.txt"
CSV_FILE       = f"{TXT_FOLDER}/msg.csv"

# DB stuff
host            = "stbern.caaexaab9wbk.ap-southeast-1.rds.amazonaws.com"
port            = 3306
database        = "stbern"
username        = "internetexplorer"
password        = "int3rn3t"

# SAMPLE MOTION SENSOR: {"nodeid":2,"event":255,"uuid":"b827eb393415-0xf0baed65-2"}
# SAMPLE DOOR SENSOR  : {"nodeid":3,"event":255,"uuid":"b827eb393415-0xf0baed65-3"}
NODEID_MOTION = 2
NODEID_DOOR = 3

MOTION_START = 225
MOTION_END   = 0

DOOR_CLOSE = 0
DOOR_OPEN  = 225

# token = '687512562:AAGEoEH8wpDU3PK5TU0X3lar40FIfDetAHY'
token = '789766810:AAFOeW6ghhreo8tv6x6cMLSvnlt8nF91NqA'
teleurl = 'https://api.telegram.org/bot' + token + '/'

# DUTY_NURSE_CHAT_ID = -251433967
DUTY_NURSE_CHAT_ID = -312380619

def send_message_with_reply(chat, text, reply_markup):
    params = {'chat_id' : chat, 'text': text, 'reply_markup': json.dumps(reply_markup), 'parse_mode' : 'markdown'}
    response = requests.post(teleurl + 'sendMessage', data=params)
    return response

def delete_message_with_reply(chatid, text):
    params = {'chat_id' : chatid, 'message_id': text}
    response = requests.post(teleurl + 'deleteMessage', data=params)
    return response

# DB FUNCTIONS ====================================================================================================================
def get_connection(read_timeout=30, write_timeout=30, connect_timeout=30, local_infile=True, cursorclass=pymysql.cursors.DictCursor):
    return pymysql.connect(host=host, port=port, db=database,
                            read_timeout=read_timeout,        # Timeout for reading from the connection in seconds
                            write_timeout=write_timeout,
                            connect_timeout=connect_timeout,
                            local_infile=local_infile,        # Allows SQL "LOAD DATA LOCAL INFILE" command to be used
                            user=username, passwd=password,
                            cursorclass=cursorclass, autocommit=True)
     # Note: Cursors are what pymysql uses interact with databases, its the equivilant to a Statement in java
def insert_sysmonlog(uuid, node_id, event, key):
    '''
    INSERTs a log entry into the database

    Returns success boolean
    '''
    query = "INSERT INTO stbern.sysmon_log VALUES('{}', '{}', '{}', '{}', '{}')"                        \
                   .format(uuid, node_id, event, key, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

    # Get connection
    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(query)
    except: raise
    finally: 
        cursor.close()
        connection.close()

def insert_sensorlog(sensor_uuid, node_id, gw_timestamp, value):
    '''
    Inputs:
    sensor_uuid (str)
    node_id (int)
    gw_timestamp (datetime)
    value (int)
    '''
    query = """
            INSERT INTO stbern.sensor_log (`uuid`, `node_id`, `event`, `recieved_timestamp`)
            VALUES (%s, %s, %s, %s)
            """
    connection = get_connection()
    cursor = connection.cursor()
    try:
        cursor.execute(query, [sensor_uuid, node_id, value, gw_timestamp])
    except Exception as error:
        log_msg(LOGGING_FILE, 'INSERT SENSORLOG'.ljust(25) + f" >> Exception: {str(error)}")
    finally:
        cursor.close()
        connection.close()

# Utility functions =============================================================================================================
def log_msg(filename, msg):
    '''
    Helper function to write logs to a specific file
    
    Input:
    filename (str): path to file
    msg (str): message to write to file 
    '''
    if not os.path.exists(os.path.dirname(filename)):
        try:
            os.makedirs(os.path.dirname(filename))
        except OSError as exc: # Guard against race condition, where somehow by magic, folder was created inebetween these 2 lines
            if exc.errno != errno.EEXIST:
                return # skips

    with open(filename, "a+") as f:
        time = datetime.datetime.now().replace(microsecond=0).isoformat()
        f.write(f"{time} {msg}\n")
        print(msg)


dwelling_to_nodeid = {"room 1": 2005, "room 2": 2006}


def process_msg(topic, message):
    '''
    Process json msgs from mqtt broker. Insert only event update msgs
    
    Input:
    message (str) - A single json string
    '''
    try:
        # Load JSON
        jdict = json.loads(message)
        topic = topic.split("/")
        if len(topic) == 1 and topic[0] == "finals" and len(jdict) == 3:         # STBERN LIVE SENSORS Determine Sysmon or Sensor Data
            if 'nodeid' in jdict and 'event' in jdict and 'uuid' in jdict:     # Ensure this is the right message
                nodeid = jdict['nodeid']    # int
                event  = jdict['event']     # int
                uuid   = "test-m-02"        # str
                # Adding to DB
                insert_sensorlog(uuid, nodeid, datetime.datetime.now(), event)
                insert_sysmonlog(uuid, nodeid, 100, "Battery Level")
                rname = resident_DAO.get_resident_name_by_node_id(nodeid)
                # Get resident details
                
                
                # trigger telegram shit
                if nodeid == NODEID_MOTION and rname != None:
                    action_motion(event=event, rname=rname)

    except Exception as e:
        msg = f"PROCESS MESSAGE FAILURE >> Exception: '{str(e)}, Msg: {message}'"
        log_msg(LOGGING_FILE, msg)


def action_motion(event, rname):
    if event == 255:
        
        print("called action motion")
        # ts = time.time()
        reply_markup = {"inline_keyboard": [[{"text": "Yes, using toilet", "callback_data": "Using Toilet"}, {"text": "False Alarm", "callback_data": "False Alarm"}]]}
        date_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        text=f'*Assistance Alert:* {rname} at ' + date_time
        send_message_with_reply(DUTY_NURSE_CHAT_ID, text, reply_markup)
        text=f'Assistance Alert: {rname} at ' + date_time
        alert_DAO.insert_alert(DUTY_NURSE_CHAT_ID, date_time, rname, text, "Assistance", "No")
        
        residentNameList = resident_DAO.get_list_of_residentNames()
        latest_list = get_latest_alerts(residentNameList)
        keyboardBottom = [[alert] for alert in latest_list]
        reply_markupBottom = {"keyboard":keyboardBottom, "one_time_keyboard": True}
        response = send_message_with_reply(DUTY_NURSE_CHAT_ID, "Your task has been added to the to-do list:", reply_markupBottom)
        print(response.json()['result']['message_id'])
        message_id = response.json()['result']['message_id']
        # delete_message_with_reply(DUTY_NURSE_CHAT_ID, message_id)


def get_latest_alerts(residentNameList):
    print(residentNameList)
    latest_list = []
    for resident in residentNameList:
        residentName = resident['name']
        resident_latest_alert_raw = alert_DAO.get_latest_alert_by_id(DUTY_NURSE_CHAT_ID, residentName)
        if len(resident_latest_alert_raw) > 0: 
            resident_latest_alert = resident_latest_alert_raw[0]
            if resident_latest_alert['response_status'] == 'No':
                latest_list.append(resident_latest_alert['alert_text'])
    return latest_list

# Call back functions ============================================================================================================
def on_connect(client, userdata, flags, rc):
    '''
    The callback for when the client receives a CONNACK response from the server.
    '''
    # Log callback result
    message = 'ON_CONNECT'.ljust(25) + ' >> '
    if rc == 0:
        message += "Connection Successfull"
        # Subscribing in on_connect() means that if we lose the connection and
        # reconnect then subscriptions will be renewed.
        client.subscribe(topic=TOPIC, qos=QOS) # Subscribe to topic
    elif rc == 1:
        message += "Connection Refused - incorrect protocol version"
    elif rc == 2:
        message += "Connection Refused - invalid client identifier"
    elif rc == 3:
        message += "Connection Refused - server unavailable"
    elif rc == 4:
        message += "Connection Refused - bad username or password"
    elif rc == 5:
        message += "Connection Refused - not authorised"

    log_msg(LOGGING_FILE, message)


def on_disconnect(client, userdata, rc):
    '''
    Callback for when client disconnects from broker
    '''
    message = f'ON DISCONNECT'.ljust(25) + ' >> '
    if rc == mqttClient.MQTT_ERR_SUCCESS:
        log_msg(LOGGING_FILE,  message+"Disconnect Successfull")
    else:
        log_msg(LOGGING_FILE, message+f"Disconnect Error. RC: {str(rc)}")


def on_subscribe(client, userdata, mid, granted_qos):
    '''
    Callback for when client subscribes
    '''
    message = f'ON SUBSCRIBE'.ljust(25) + ' >> '
    log_msg(LOGGING_FILE, message+f"Topic: '{TOPIC}', QOS: '{QOS}'")


def on_log(client, userdata, level, buf):
    '''
    Callback for logs, pretty sure its the logs transmitted by the broker
    '''
    message = f'ON LOG'.ljust(25) + f' >> {str(buf)}' 
    log_msg(LOGGING_FILE, message)



def on_message(client, userdata, message):
    payload = message.payload.decode('utf-8')
    string = 'ON MESSAGE'.ljust(25) + f" >> Topic: '{message.topic}', Qos: '{message.qos}', Payload: '{payload}'"
    
    # Log 
    log_msg(LOGGING_FILE, string)
    print("yo")
    # Log to csv
    csv_topic = message.topic.replace("\"","\"\"")
    csv_payload = payload.replace("\"", "\"\"")
    log_msg(CSV_FILE, f', \"{csv_topic}\", \"{csv_payload}\"')

    # Process / Send to DB
    process_msg(topic=message.topic, message=payload)

# Loop setup ====================================================================================================================
try:
    client = mqttClient.Client("finals_clientxx")               #create new instance
    client.username_pw_set(USER, password=PASSWORD)    #set username and password

    # Attach callback functions
    client.on_connect    = on_connect
    client.on_disconnect = on_disconnect
    client.on_subscribe  = on_subscribe
    client.on_log        = on_log
    client.on_message    = on_message

    # Connect to broker
    client.connect(BROKER_ADDRESS, port=PORT)

    # Start Loop
    client.loop_forever()   # Handles reconnection, except for the first connection. To stop forever loop
    
except KeyboardInterrupt:
    log_msg(LOGGING_FILE, "KEYBOARD INTERRUPT >> ")
    client.disconnect()
    client.loop_stop()

# def main():


# if __name__ == '__main__':
    # main()
