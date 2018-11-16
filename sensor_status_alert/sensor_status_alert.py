import requests
import json
import datetime
import shift_log_DAO
import resident_DAO
from sensor_mgmt.sensor_mgmt import Sensor_mgmt
from DAOs.sensor_DAO import sensor_DAO
from DAOs import sensor_hist_DAO
import alert_DAO
import schedule
import time

token = '789766810:AAFOeW6ghhreo8tv6x6cMLSvnlt8nF91NqA'
teleurl = 'https://api.telegram.org/bot' + token + '/'

DUTY_NURSE_CHAT_ID = -312380619

# RETURN STATUS CODES
INVALID_SENSOR = -1
OK             = 0     # Can be OK and LOW_BATT at the same time
DISCONNECTED   = 1
LOW_BATT       = 2 
CHECK_WARN     = 3    # Potentially down

# SETTINGS
batt_thresh  = 10    # In percent

def send_message_with_reply(chat, text):

	params = {'chat_id' : chat, 'text': text}
	response = requests.post(teleurl + 'sendMessage', data=params)
	return response

def send_message_with_reply2(chat, text, reply_markup):
	params = {'chat_id' : chat, 'text': text, 'reply_markup': json.dumps(reply_markup)}
	response = requests.post(teleurl + 'sendMessage', data=params)
	return response

def get_latest_alerts(alerts):
	latest_list = []
	check_list = []
	for alert in reversed(alerts):
		alert_text = alert['alert_text']
		rname = alert['rname']
		if rname not in check_list:
			check_list.append(rname)
			latest_list.append(alert_text)
	return latest_list
	

Sensor_mgmt = Sensor_mgmt()

def job():
	downList = {}
	ss = Sensor_mgmt.get_sensor_status_v2('test-m-02', True)
	id = 'test-m-02'
	loc = sensor_DAO.get_location_by_node_id(id)
	location = loc[0]['location']
	rawtype = sensor_DAO.get_type_by_node_id(id)
	type = rawtype[0]['type']
	rawuuid = sensor_hist_DAO.get_id_by_uuid(id)
	if len(rawuuid)> 0:
		residentid = rawuuid[0]['resident_id']
		residentNameRaw = resident_DAO.get_resident_name_by_resident_id(residentid)
		residentName = residentNameRaw[0]['name']
		if 1 in ss[0]:
			error = "Sensor Issue: Disconnected" + "\nLocation: " + residentName + " " + location + "\nType: " + type
			downList.update({error : residentName})
		elif 2 in ss[0]:
			error = "Sensor Issue: Low Battery" + "\nLocation: " + residentName + " " + location + "\nType: " + type
			downList.update({error : residentName})
		elif 3 in ss[0]:
			error = "Sensor Issue: Warning"+ "\nLocation: " + residentName + " " + location + "\nType: " + type
			downList.update({error : residentName})
	sensor_alerts = alert_DAO.get_sensor_alerts(DUTY_NURSE_CHAT_ID, "sensor")
	sensorAlertList = []
	for sensor_alert in sensor_alerts:
		sensor_alert_text = sensor_alert['alert_text']
		sensorAlertList.append(sensor_alert_text)
		if sensor_alert_text not in downList.keys(): 
			alert_DAO.update_alert(DUTY_NURSE_CHAT_ID, sensor_alert_text)
			alerts = alert_DAO.get_alerts_by_id(DUTY_NURSE_CHAT_ID)
			latest_list = get_latest_alerts(alerts)
			sensor_alerts = alert_DAO.get_sensor_alerts(DUTY_NURSE_CHAT_ID, "sensor")
			for sensor_alert in sensor_alerts:
				sensor_alert_text = sensor_alert['alert_text']
				latest_list.append(sensor_alert_text)
			keyboardBottom = [[alert] for alert in latest_list]
			reply_markupBottom = {"keyboard":keyboardBottom, "one_time_keyboard": True}
			send_message_with_reply2(DUTY_NURSE_CHAT_ID, "Sensor issue has been rectified for:\n" + sensor_alert_text, reply_markupBottom)
	if(len(downList) > 0):
		for key, value in downList.items():
			if key not in sensorAlertList:
				text = key
				send_message_with_reply(DUTY_NURSE_CHAT_ID, text)
				date_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
				alert_DAO.insert_alert(DUTY_NURSE_CHAT_ID, date_time, value, text, "Sensor", "No")
				alerts = alert_DAO.get_alerts_by_id(DUTY_NURSE_CHAT_ID)
				latest_list = get_latest_alerts(alerts)
				sensor_alerts = alert_DAO.get_sensor_alerts(DUTY_NURSE_CHAT_ID, "sensor")
				for sensor_alert in sensor_alerts:
					sensor_alert_text = sensor_alert['alert_text']
					latest_list.append(sensor_alert_text)
				keyboardBottom = [[alert] for alert in latest_list]
				reply_markupBottom = {"keyboard":keyboardBottom, "one_time_keyboard": True}
				send_message_with_reply2(DUTY_NURSE_CHAT_ID, "Your task has been added to the to-do list:", reply_markupBottom)

schedule.every().second.do(job)

while True:
	schedule.run_pending()
	time.sleep(1)