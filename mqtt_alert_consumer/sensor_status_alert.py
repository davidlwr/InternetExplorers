import requests
import json
import datetime
import shift_log_DAO
import resident_DAO
from sensor_mgmt.sensor_mgmt import Sensor_mgmt
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

def send_message_with_reply(chat, text, reply_markup):

	params = {'chat_id' : chat, 'text': text, 'reply_markup': json.dumps(reply_markup)}
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
	if((hour ==20) and (minute==42) and (second == 0)):
		downList = []
		print(Sensor_mgmt.get_all_sensor_status_v2(True))
		for ss in Sensor_mgmt.get_all_sensor_status_v2(True):
			if 1 in ss[1]:
				error = ss[0] + " issue: disconnected" 
				downList.append(error)
			elif 2 in ss[1]:
				error = ss[0] + " issue: low battery" 
				downList.append(error)
			elif 3 in ss[1]:
				error = ss[0] + " issue: warning" 
				downList.append(error)
				
		reply_markup = {"inline_keyboard": [[{"text": "Fixed", "callback_data": "fixed"},{"text": "False Alarm", "callback_data": "False Alarm"}]]}
		if(len(downList) > 0):
			# text = "\n".join(downList)
			for downSS in downList: 
				text = "Sensor " + downSS 
				send_message_with_reply(DUTY_NURSE_CHAT_ID, text, reply_markup)
				alert_DAO.insert_alert(DUTY_NURSE_CHAT_ID, text)
			alerts = alert_DAO.get_alerts_by_id(DUTY_NURSE_CHAT_ID)
			keyboardBottom = [[alert['alert_text']] for alert in alerts]
			reply_markupBottom = {"keyboard":keyboardBottom, "one_time_keyboard": True}
			response = send_message_with_reply(DUTY_NURSE_CHAT_ID, "Yor task has been added to the to-do list:", reply_markupBottom)
	elif((hour ==21) and (minute==0) and (second == 0)):
		downList = []
		for ss in Sensor_mgmt.get_all_sensor_status():
			if 1 in ss[1]:
				error = ss[0] + " issue: disconnected" 
				downList.append(error)
			elif 2 in ss[1]:
				error = ss[0] + " issue: low battery" 
				downList.append(error)
			elif 3 in ss[1]:
				error = ss[0] + " issue: warning" 
				downList.append(error)
				
		reply_markup = {"inline_keyboard": [[{"text": "Fixed", "callback_data": "fixed"},{"text": "False Alarm", "callback_data": "False Alarm"}]]}
		if(len(downList) > 0):
			# text = "\n".join(downList)
			for downSS in downList: 
				text = "Sensor " + downSS 
				send_message_with_reply(DUTY_NURSE_CHAT_ID, text, reply_markup)
				alert_DAO.insert_alert(DUTY_NURSE_CHAT_ID, text)
			alerts = alert_DAO.get_alerts_by_id(DUTY_NURSE_CHAT_ID)
			keyboardBottom = [[alert['alert_text']] for alert in alerts]
			reply_markupBottom = {"keyboard":keyboardBottom, "one_time_keyboard": True}
			response = send_message_with_reply(DUTY_NURSE_CHAT_ID, "Yor task has been added to the to-do list:", reply_markupBottom)