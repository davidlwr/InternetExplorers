import requests
import json
from datetime import datetime, timedelta
import datetime
import shift_log_DAO
import resident_DAO
import schedule
import time

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
	
def job():
    print("I'm working...")


schedule.every().day.at("15:14").do(job)
	
while 1:
	current_time=datetime.datetime.now()
	hour = current_time.hour
	minute = current_time.minute
	second = current_time.second
	microsecond = current_time.microsecond
	if((hour ==19) and (minute==0) and (second == 0)):
	# secondList = [10,20,30,40,50,0]
	# if((second in secondList)):
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
			link = "http://stb-broker.lvely.net/eosforms"
			send_message_with_reply(DUTY_NURSE_CHAT_ID, "You have not completed your shift logs for the following residents:\n" + text + "\n\nClick here to access the shift form:\n" + link)
			
	elif((hour ==7) and (minute==0) and (second == 0)):
		yesterday = datetime.datetime.now() - timedelta(days=1)
		date = yesterday.strftime('%y-%m-%d')
		# time = datetime.datetime.strptime('2000','%H%M').time()
		# shifttime = datetime.datetime.combine(date, time)
		shifttime = date + " 20:00:00"
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
			link = "http://stb-broker.lvely.net/eosforms"
			send_message_with_reply(DUTY_NURSE_CHAT_ID, "You have not completed your shift logs for the following residents:\n" + text + "\n\nClick here to access the form:\n" + link)
		
		schedule.run_pending()
		time.sleep(1)

		
if __name__ == '__main__':
    main()