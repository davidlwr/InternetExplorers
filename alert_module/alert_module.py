
import time
import os
import errno
import json
import datetime
import json
from urllib.request import urlopen

import paho.mqtt.client as mqttClient
import pymysql
from pprint import pprint
import telepot
from telepot.loop import MessageLoop
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton
 


# Global Vars ==========================================================
# MQTT Stuff
BROKER_ADDRESS = "52.76.122.1"  # Broker address
PORT           = 1883                    # Broker port
USER           = "stbern"                # username
PASSWORD       = "int3rn3t"              # password
TOPIC          = "test"        # Wildcard subscribe to everything
QOS            = 0          
TXT_FOLDER   = "./logs"
LOGGING_FILE = f"{TXT_FOLDER}/log.txt"
CSV_FILE = f"{TXT_FOLDER}/msg.csv"

# DB stuff
host            = "stbern.cdc1tjbn622d.ap-southeast-1.rds.amazonaws.com"
port            = 3306
database        = "stbern"
username        = "internetexplorer"
password        = "int3rn3t"

TOKEN="573206399:AAFhJivL-aaCXq8smEfEJx6y70E6mSffiZI" 

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


def process_msg(topic, message):
    '''
    Process json msgs from mqtt broker. Insert only event update msgs
    
    Input:
    message (str) - A single json string
    '''
    try:
        # Load JSON
        jdict = json.loads(message)

        # Determine Sysmon or Sensor Data
        topic = topic.split("/")
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

        # SPLIT INTO SYSMON AND DATA
        if data_type == "data":
            if key == "motion": insert_sensorlog(dwelling_id, sensor_id, gw_timestamp, int(value))
        elif data_type == "sysmon":
            insert_sysmonlog(dwelling_id, sensor_id, gw_timestamp, key, float(value))  # Key is required

    except Exception as e:
        msg = f"PROCESS MESSAGE FAILURE >> Exception: '{str(e)}, Msg: {message}'"
        log_msg(LOGGING_FILE, msg)


def get_connection(read_timeout=30, write_timeout=30, connect_timeout=30, local_infile=True, cursorclass=pymysql.cursors.DictCursor):
    return pymysql.connect(host=host, port=port, db=database,
                            read_timeout=read_timeout,        # Timeout for reading from the connection in seconds
                            write_timeout=write_timeout,
                            connect_timeout=connect_timeout,
                            local_infile=local_infile,        # Allows SQL "LOAD DATA LOCAL INFILE" command to be used
                            user=username, passwd=password,
                            cursorclass=cursorclass, autocommit=True)
    # Note: Cursors are what pymysql uses interact with databases, its the equivilant to a Statement in java


dwelling_to_nodeid = {"room 1": 2005, "room 2": 2006}
def insert_sensorlog(dwelling_id, sensor_id, gw_timestamp, value):
    '''
    Inputs:
    dwelling_id (str)
    sensor_id (str)
    gw_timestamp (datetime)
    value (int)
    '''
    query = """
            INSERT INTO stbern.SENSOR_LOG (`uuid`, `node_id`, `event`, `recieved_timestamp`)
            VALUES (%s, %s, %s, %s)
            """
    node_id = dwelling_to_nodeid[dwelling_id]
    uuid = f"{node_id}-{sensor_id}"
    event = value
    recieved_timestamp = gw_timestamp.strftime('%Y-%m-%d %H:%M:%S')

    connection = get_connection()
    cursor = connection.cursor()
    try:
        cursor.execute(query, [uuid, node_id, event, recieved_timestamp])
    except Exception as error:
        log_msg(LOGGING_FILE, 'INSERT SENSORLOG'.ljust(25) + f" >> Exception: {str(error)}")
    finally:
        cursor.close()
        connection.close()


def insert_sysmonlog(dwelling_id, sensor_id, gw_timestamp, key, value):
    '''
    Inputs:
    dwelling_id (str)
    sensor_id (str)
    gw_timestamp (datetime)
    key (str)
    value (float)
    '''
    query = """
            INSERT INTO stbern.SYSMON_LOG (`uuid`, `node_id`, `key`, `event`, `recieved_timestamp`)
            VALUES (%s, %s, %s, %s, %s)
            """
    node_id = dwelling_to_nodeid[dwelling_id]
    uuid = f"{node_id}-{sensor_id}"
    event = value
    recieved_timestamp = gw_timestamp.strftime('%Y-%m-%d %H:%M:%S')

    connection = get_connection()
    cursor = connection.cursor()
    try:
        cursor.execute(query, [uuid, node_id, key, event, recieved_timestamp])
    except Exception as error:
        log_msg(LOGGING_FILE, 'INSERT SYSMONLOG'.ljust(25) + f" >> Exception: {str(error)}")
    finally:
        cursor.close()
        connection.close()


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
	payload = message.payload.decode("utf-8")
	string = 'ON MESSAGE'.ljust(25) + f" >> Topic: '{message.topic}', Qos: '{message.qos}', Payload: '{payload}'"
	print(payload)
	bot = telepot.Bot(TOKEN)
	chat_id = 260905740
	# content_type, chat_type, chat_id = telepot.glance(msg)
	keyboard1 = InlineKeyboardMarkup(inline_keyboard=[
                     [InlineKeyboardButton(text='Yes, using toilet', callback_data='toiletJoy'),
                     InlineKeyboardButton(text='False Alarm', callback_data='falsealarm')],
					 ])
	keyboard2 = InlineKeyboardMarkup(inline_keyboard=[
                     [InlineKeyboardButton(text='Yes, using toilet', callback_data='toiletPoh'),
                     InlineKeyboardButton(text='False Alarm', callback_data='falsealarm')],
					 ])
	if payload == "Sensor 1 Alert: Mdm Joy":
		bot.sendMessage(chat_id, payload, reply_markup=keyboard1)
		MessageLoop(bot, {'callback_query': on_callback_query}).run_as_thread() 
	elif payload == "Sensor 2 Alert: Mr Poh":
		bot.sendMessage(chat_id, payload, reply_markup=keyboard2)
		MessageLoop(bot, {'callback_query': on_callback_query}).run_as_thread() 
		
	# Log 
	log_msg(LOGGING_FILE, string)
	log_msg(CSV_FILE, f', \"{message.topic}\", \"{payload}\"')

    # Process / Send to DB
    # process_msg(topic=message.topic, message=payload)

def on_callback_query(msg):
	bot = telepot.Bot(TOKEN)
	query_id, chat_id, query_data = telepot.glance(msg, flavor='callback_query')
	keyboardJoy = InlineKeyboardMarkup(inline_keyboard=[
                     [InlineKeyboardButton(text='Urination', callback_data='urine'),
					 InlineKeyboardButton(text='Defecation', callback_data='defecation'),
					 InlineKeyboardButton(text='Make up', callback_data='makeup')],
					 ])
	keyboardPoh = InlineKeyboardMarkup(inline_keyboard=[
                     [InlineKeyboardButton(text='Urination', callback_data='urine'),
					 InlineKeyboardButton(text='Defecation', callback_data='defecation')],
					 ])
	print('Callback Query:', query_id, chat_id, query_data)
	if query_data=='toiletJoy':
		ts = time.time()
		bot.sendMessage(chat_id, "Select purpose of toilet visit:" ,reply_markup=keyboardJoy)
	if query_data=='toiletPoh':
		ts = time.time()
		bot.sendMessage(chat_id, "Select purpose of toilet visit:" ,reply_markup=keyboardPoh)
	elif query_data=='urine':
		ts = time.time()
		bot.sendMessage(chat_id, "Urine Action captured at " + datetime.datetime.fromtimestamp(ts).strftime('%H:%M:%S'))		
	elif query_data=='defecation':
		ts = time.time()
		bot.sendMessage(chat_id, "Defecation action captured" + datetime.datetime.fromtimestamp(ts).strftime('%H:%M:%S'))
	elif query_data=='makeup':
		ts = time.time()
		bot.sendMessage(chat_id, "Make up action captured at " + datetime.datetime.fromtimestamp(ts).strftime('%H:%M:%S'))		
	elif query_data=='falsealarm':
		ts = time.time()
		bot.sendMessage(chat_id, "False Alarm at " + datetime.datetime.fromtimestamp(ts).strftime('%H:%M:%S'))



	
	

# Loop setup ====================================================================================================================
try:
    client = mqttClient.Client("StBern_Alert")               #create new instance
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