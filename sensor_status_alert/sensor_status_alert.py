import requests
import json
import datetime
import shift_log_DAO
import resident_DAO
from sensor_mgmt.sensor_mgmt import Sensor_mgmt
from DAOs.sensor_DAO import sensor_DAO
from DAOs import sensor_hist_DAO
import alert_DAO

token = '687512562:AAGEoEH8wpDU3PK5TU0X3lar40FIfDetAHY'
teleurl = 'https://api.telegram.org/bot' + token + '/'

DUTY_NURSE_CHAT_ID = -251433967

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

	

Sensor_mgmt = Sensor_mgmt()

while 1:
	# for ss in Sensor_mgmt.get_all_sensor_status():
		# if 0 in ss[1]:
			# print(ss[0])
	current_time=datetime.datetime.now()
	hour = current_time.hour
	minute = current_time.minute
	second = current_time.second
	microsecond = current_time.microsecond
	secondList = [10,20,30,40,50,0]
	if((second in secondList)):
		downList = []
		for ss in Sensor_mgmt.get_all_sensor_status_v2(True):
			id = ss[0]
			loc = sensor_DAO.get_location_by_node_id(id)
			location = loc[0]['location']
			rawtype = sensor_DAO.get_type_by_node_id(id)
			type = rawtype[0]['type']
			rawuuid = sensor_hist_DAO.get_id_by_uuid(id)
			if len(rawuuid)> 0:
				residentid = rawuuid[0]['resident_id']
				residentNameRaw = resident_DAO.get_resident_name_by_resident_id(residentid)
				residentName = residentNameRaw[0]['name']
				if 1 in ss[1]:
					error = "Sensor Issue: Disconnected" + "\nLocation: " + residentName + " " + location + "\nType: " + type
					downList.append(error)
				elif 2 in ss[1]:
					error = "Sensor Issue: Low Battery" + "\nLocation: " + residentName + " " + location + "\nType: " + type
					downList.append(error)
				elif 3 in ss[1]:
					error = "Sensor Issue: Warning"+ "\nLocation: " + residentName + " " + location + "\nType: " + type
					downList.append(error)
		sensor_alerts = alert_DAO.get_sensor_alerts(DUTY_NURSE_CHAT_ID, "sensor")
		sensorAlertList = []
		for sensor_alert in sensor_alerts:
			sensor_alert_text = sensor_alert['alert_text']
			sensorAlertList.append(sensor_alert_text)
		# if(len(downList) > 0):
			# text = "\n".join(downList)
			if sensor_alert_text not in downList: 
				alert_DAO.update_alert(DUTY_NURSE_CHAT_ID, sensor_alert_text)
		if(len(downList) > 0):
			for downSS in downList:
				if downSS not in sensorAlertList:
					text = downSS 
					send_message_with_reply(DUTY_NURSE_CHAT_ID, text)
					date_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
					alert_DAO.insert_alert(DUTY_NURSE_CHAT_ID, date_time, text, "Sensor", "No")
					alerts = alert_DAO.get_alerts_by_id(DUTY_NURSE_CHAT_ID)
					keyboardBottom = [[alert['alert_text']] for alert in alerts]
					reply_markupBottom = {"keyboard":keyboardBottom, "one_time_keyboard": True}
					response = send_message_with_reply(DUTY_NURSE_CHAT_ID, "Your task has been added to the to-do list:", reply_markupBottom)
	