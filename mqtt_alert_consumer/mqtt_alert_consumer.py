import paho.mqtt.client as mqttClient
import time
import os
import errno
import requests
import json
import datetime

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler
# from dbhelper import DBHelper
from DAOs import alert_DAO
from DAOs import resident_DAO
from DAOs.sensor_DAO import sensor_DAO

from pprint import pprint
import time
import datetime
import json
from urllib.request import urlopen

# Global Vars ==========================================================
# MQTT Stuff
BROKER_ADDRESS = "stb-broker.lvely.net"  # Broker address
PORT           = 1883                    # Broker port
USER           = "stbern"                # username
PASSWORD       = "int3rn3t"              # password
TOPIC          = "#"        # Wildcard subscribe to everything
QOS            = 2          
TXT_FOLDER   = "./logs"
LOGGING_FILE = f"{TXT_FOLDER}/log.txt"
CSV_FILE = f"{TXT_FOLDER}/msg.csv"

# DB stuff
host            = "stbern.cdc1tjbn622d.ap-southeast-1.rds.amazonaws.com"
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

token = '791066367:AAHoFqezcLxJM6zEcKAmZukh8e_OuQ3fXik'
teleurl = 'https://api.telegram.org/bot' + token + '/'

DUTY_NURSE_CHAT_ID = -251433967

def send_message_with_reply(chat, text, reply_markup):
    params = {'chat_id' : chat, 'text': text, 'reply_markup': json.dumps(reply_markup), 'parse_mode' : 'markdown'}
    response = requests.post(teleurl + 'sendMessage', data=params)
    return response

def delete_message_with_reply(chatid, text):
    params = {'chat_id' : chatid, 'message_id': text}
    response = requests.post(teleurl + 'deleteMessage', data=params)
    return response

# Utility functions ==============================================================================================================
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

# db = DBHelper()
# db.setup()
dwelling_to_nodeid = {"room 1": 2005, "room 2": 2006}

# uuid_rname =    { "2005-d-01": "Poh Kim Pew",
                  # "2005-m-02": "Poh Kim Pew",
                  # "2006-d-01": "Lo Khuik Fah Joy",
                  # "2006-m-02": "Lo Khuik Fah Joy",
                  # "2100-room 3-m-02": "Lai Yee Chun",
                  # "2100-room 4-m-02": "Lopez Beatrice Angelina"
                # }
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
        key_list = ('mode', 'sensor_id', 'key', 'value', 'gw_timestamp')

        if len(topic) == 4 and all(k in jdict for k in key_list):         # STBERN LIVE SENSORS Determine Sysmon or Sensor Data

            # Determine Sysmon or Sensor Data
            
            project_id  = topic[0]  # 'stb'
            hub_id      = topic[1]  # '2100' presumably the building
            dwelling_id = topic[2]  # 'room1' or 'room2'
            data_type   = topic[3]  # 'sysmon' or 'data
            
            # breakdown message
            mode         = jdict['mode']        # i.e. 'motion'
            sensor_id    = jdict['sensor_id']   # i.e. 'm-01'   
            key          = jdict['key']         # i.e. 'motion', 'ultraviolet'
            value        = jdict['value']       # str (actually float)
            gw_timestamp = datetime.datetime.fromtimestamp(jdict['gw_timestamp'] / 1e3)

            # Determine the uuid identifier of the sensor. Mostly for the conversion of the 2 sensors
            uuid = None
            rname = None
            if project_id=="stb" and hub_id=="2100" and dwelling_id in dwelling_to_nodeid:
                uuid = f"{dwelling_to_nodeid[dwelling_id]}-{sensor_id}"
                resident_id = sensor_DAO.get_current_owner(uuid)
                rname = resident_DAO.get_resident_name_by_resident_id(resident_id)
            else:
                uuid = f"{hub_id}-{dwelling_id}-{sensor_id}"
                resident_id = sensor_DAO.get_current_owner(uuid)
                rname = resident_DAO.get_resident_name_by_resident_id(resident_id)            

            

            
            if data_type == "data" and rname != None:
                if key == "motion": action_motion(event=value, rname=rname)
                # if key == "door":   action_door(event=value, rname=uuid_rname[uuid])

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
    
    # Log to csv
    csv_topic = message.topic.replace("\"","\"\"")
    csv_payload = payload.replace("\"", "\"\"")
    log_msg(CSV_FILE, f', \"{csv_topic}\", \"{csv_payload}\"')

    # Process / Send to DB
    process_msg(topic=message.topic, message=payload)

# Loop setup ====================================================================================================================
try:
    client = mqttClient.Client("acceptance_client")               #create new instance
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
   # resident_id = sensor_DAO.get_current_owner('2100-room 3-d-01')
   # print(resident_DAO.get_resident_name_by_resident_id(resident_id))

# if __name__ == '__main__':
    # main()