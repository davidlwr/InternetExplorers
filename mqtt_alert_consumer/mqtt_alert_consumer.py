
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
import alert_DAO

from pprint import pprint
import time
import datetime
import json
from urllib.request import urlopen

# Global Vars ==========================================================
# MQTT Stuff
BROKER_ADDRESS = "stb-broker.lvely.net"  # Broker address
PORT           = 1883                    # Broker port
CLIENT         = "acceptance_client"
USER           = "stbern"                # username
PASSWORD       = "int3rn3t"              # password
TOPIC          = "test"
QOS            = 0          
TXT_FOLDER   = "./logs"
LOGGING_FILE = f"{TXT_FOLDER}/log.txt"
CSV_FILE = f"{TXT_FOLDER}/msg.csv"

# SAMPLE MOTION SENSOR: {"nodeid":2,"event":255,"uuid":"b827eb393415-0xf0baed65-2"}
# SAMPLE DOOR SENSOR  : {"nodeid":3,"event":255,"uuid":"b827eb393415-0xf0baed65-3"}
NODEID_MOTION = 2
NODEID_DOOR = 3

MOTION_START = 225
MOTION_END   = 0

DOOR_CLOSE = 0
DOOR_OPEN  = 225

token = '687512562:AAGEoEH8wpDU3PK5TU0X3lar40FIfDetAHY'
teleurl = 'https://api.telegram.org/bot' + token + '/'

DUTY_NURSE_CHAT_ID = -251433967

def send_message_with_reply(chat, text, reply_markup):
    params = {'chat_id' : chat, 'text': text, 'reply_markup': json.dumps(reply_markup)}
    response = requests.post(teleurl + 'sendMessage', data=params)
    return response

def delete_message_with_reply(chatid, text):
    params = {'chat_id' : chatid, 'message_id': text}
    response = requests.post(teleurl + 'deleteMessage', data=params)
    return response

# Utility functions ==============================================================================================================
def log_msg(filename, msg, verbose=True):
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
        if verbose: print(msg)

# db = DBHelper()
# db.setup()


def action_motion(event):
    if event == 255:
        
        print("called action motion")
        # ts = time.time()
        reply_markup = {"inline_keyboard": [[{"text": "Yes, using toilet", "callback_data": "Using Toilet"}, {"text": "False Alarm", "callback_data": "False Alarm"}]]}
        date_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        text='Assistance Alert: Squid Ward at ' + date_time
        send_message_with_reply(DUTY_NURSE_CHAT_ID, text, reply_markup)
        alert_DAO.insert_alert(DUTY_NURSE_CHAT_ID, date_time, text, "Assistance", "No")

        alerts = alert_DAO.get_alerts_by_id(DUTY_NURSE_CHAT_ID)
        print(alerts)
        keyboardBottom = [[alert['alert_text']] for alert in alerts]
        reply_markupBottom = {"keyboard":keyboardBottom, "one_time_keyboard": True}
        response = send_message_with_reply(DUTY_NURSE_CHAT_ID, "Your task has been added to the to-do list:", reply_markupBottom)
        print(response.json()['result']['message_id'])
        message_id = response.json()['result']['message_id']
        # delete_message_with_reply(DUTY_NURSE_CHAT_ID, message_id)

def action_door(event):
    if event == 255:
        print("called action_door motion")
        reply_markup = {"inline_keyboard": [[{"text": "Yes, using toilet", "callback_data": "Using Toilet"}, {"text": "False Alarm", "callback_data": "False Alarm"}]]}
        date_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        text='Assistance Alert: Squid Ward at ' + date_time
        send_message_with_reply(DUTY_NURSE_CHAT_ID, text, reply_markup)
        alert_DAO.insert_alert(DUTY_NURSE_CHAT_ID, date_time, text, "Assistance", "No")

        alerts = alert_DAO.get_alerts_by_id(DUTY_NURSE_CHAT_ID)
        keyboardBottom = [[alert['alert_text']] for alert in alerts]
        reply_markupBottom = {"keyboard":keyboardBottom, "one_time_keyboard": True}
        response = send_message_with_reply(DUTY_NURSE_CHAT_ID, "Your task has been added to the to-do list:", reply_markupBottom)
        print(response.json()['result']['message_id'])
        message_id = response.json()['result']['message_id']
        # delete_message_with_reply(DUTY_NURSE_CHAT_ID, message_id)



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
    log_msg(LOGGING_FILE, message, verbose=False)


def on_message(client, userdata, message):
    payload = message.payload.decode('utf-8')
    string = 'ON MESSAGE'.ljust(25) + f" >> Topic: '{message.topic}', Qos: '{message.qos}', Payload: '{payload}'"
    
    # Log 
    log_msg(LOGGING_FILE, string, verbose=False)
    log_msg(CSV_FILE, f', \"{message.topic}\", \"{payload}\"', verbose=False)

    # Process / Send to DB
    # process_msg(topic=message.topic, message=payload)
    topic=message.topic
    message=payload
    
    try:
        # Load JSON
        jdict = json.loads(message)
        
        topic = topic.split("/")
        if len(topic) == 1 and topic[0] == "test" and len(jdict) == 3:         # STBERN LIVE SENSORS Determine Sysmon or Sensor Data
            if 'nodeid' in jdict and 'event' in jdict and 'uuid' in jdict:     # Ensure this is the right message
                nodeid = jdict['nodeid']    # int
                event  = jdict['event']     # int
                uuid   = jdict['uuid']      # str

                if nodeid == NODEID_MOTION: action_motion(event=event)
                if nodeid == NODEID_DOOR: action_door(event=event)

    except Exception as e:
        msg = f"PROCESS MESSAGE FAILURE >> Exception: '{str(e)}, Msg: {message}'"
        log_msg(LOGGING_FILE, msg)


# Loop setup ====================================================================================================================
try:
    client = mqttClient.Client(CLIENT)               #create new instance
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
