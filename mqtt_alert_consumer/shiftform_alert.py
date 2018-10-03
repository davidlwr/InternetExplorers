import requests
import json
import datetime
import shift_log_DAO
import resident_DAO

token = '687512562:AAGEoEH8wpDU3PK5TU0X3lar40FIfDetAHY'
teleurl = 'https://api.telegram.org/bot' + token + '/'

DUTY_NURSE_CHAT_ID = -251433967

def send_message_with_reply(chat, text):

	params = {'chat_id' : chat, 'text': text}
	response = requests.post(teleurl + 'sendMessage', data=params)
	return response


def check_shift_form(shifttime):
	idQuery = shift_log_DAO.retrieveCountPerShift(shifttime)
	patientIDList = []
	# print(test)
	for item in idQuery[:]:
		patientID = item['patient_id']
		patientIDList.append(patientID)
	return patientIDList
	



while 1:
	currentTime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
	send_message_with_reply(DUTY_NURSE_CHAT_ID, "You have not completed your shift logs for the following residents:\n" + currentTime)
	current_time=datetime.datetime.now()
	hour = current_time.hour
	minute = current_time.minute
	second = current_time.second
	microsecond = current_time.microsecond
	if((hour ==7) and (minute==0) and (second == 0)):
		date = datetime.date.today()
		time = datetime.datetime.strptime('1200','%H%M').time()
		shifttime = datetime.datetime.combine(date, time)
		patientIDList = check_shift_form(shifttime)
		nameList = []
		checkList = []
		checkList.extend(range(1, 9))
		for patient_ID in patientIDList[:]:
			checkList.remove(patient_ID)
		for id in checkList:
			patientName = resident_DAO.get_resident_name_by_resident_id(id)[0]['name']
			nameList.append(patientName)
		
		if(len(nameList) > 0):
			text = "\n".join(nameList)
			send_message_with_reply(DUTY_NURSE_CHAT_ID, "You have not completed your shift logs for the following residents:\n" + text)
			
	elif((hour ==21) and (minute==0) and (second == 0)):
		date = datetime.date.today()
		time = datetime.datetime.strptime('2000','%H%M').time()
		shifttime = datetime.datetime.combine(date, time)
		patientIDList = check_shift_form(shifttime)
		nameList = []
		checkList = []
		checkList.extend(range(1, 9))
		for patient_ID in patientIDList[:]:
			checkList.remove(patient_ID)
		for id in checkList:
			patientName = resident_DAO.get_resident_name_by_resident_id(id)[0]['name']
			nameList.append(patientName)
		
		if(len(nameList) > 0):
			text = "\n".join(nameList)
			send_message_with_reply(DUTY_NURSE_CHAT_ID, "You have not completed your shift logs for the following residents:\n" + text)