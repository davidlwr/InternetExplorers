# simple python to use long polling for getting messages sent to telegram bots
# simple python to use long polling for getting messages sent to telegram bots

import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters
import alert_DAO
import shift_log_DAO
import datetime
import resident_DAO
from sensor_mgmt.sensor_mgmt import Sensor_mgmt
from DAOs.sensor_DAO import sensor_DAO
from DAOs.sensor_log_DAO import sensor_log_DAO
from DAOs import sensor_hist_DAO



# DUTY_NURSE_CHAT_ID = -251433967
DUTY_NURSE_CHAT_ID = -312380619
def get_latest_alerts(residentNameList):
	latest_list = []
	for resident in residentNameList:
		residentName = resident['name']
		resident_latest_alert_raw = alert_DAO.get_latest_alert_by_id(DUTY_NURSE_CHAT_ID, residentName)
		if len(resident_latest_alert_raw) > 0: 
			resident_latest_alert = resident_latest_alert_raw[0]
			if resident_latest_alert['response_status'] == 'No':
				latest_list.append(resident_latest_alert['alert_text'])
	return latest_list

def get_latest_sensor_alerts(residentNameList):
	latest_list = []
	for resident in residentNameList:
		residentName = resident['name']
		resident_latest_alert_raw = alert_DAO.get_latest_sensor_alert_by_id(DUTY_NURSE_CHAT_ID, residentName)
		if len(resident_latest_alert_raw) > 0: 
			resident_latest_alert = resident_latest_alert_raw[0]
			if resident_latest_alert['response_status'] == 'No':
				latest_list.append(resident_latest_alert['alert_text'])
	return latest_list


def button(bot, update):

	# keyboardtext = update.message.text 
	query = update.callback_query
	queryText = query['message']['text']

	keyboard = [[InlineKeyboardButton("Defecation", callback_data='Defecation'),
				 InlineKeyboardButton("Urine", callback_data='Urine')],
				[InlineKeyboardButton("Other Action", callback_data='Other Action')]]

	keyboardDefault = [[InlineKeyboardButton("Yes, using toilet", callback_data='Using Toilet'),
				 InlineKeyboardButton("False Alarm", callback_data='False Alarm')]]
	
	
	reply_markup = InlineKeyboardMarkup(keyboard)
	reply_markupDefault = InlineKeyboardMarkup(keyboardDefault)
	global initialMsg

	if query.data == 'Using Toilet':  
		bot.edit_message_text(text=query['message']['text'] + "\n\n{}\n\nPurpose of visit?".format(query.data),
						  chat_id=query.message.chat_id,
						  message_id=query.message.message_id, 
						  reply_markup=reply_markup)
		initialMsg = query['message']['text']

	elif query.data == 'False Alarm': 
		bot.edit_message_text(text=query['message']['text'] + "\n\n{}".format(query.data),
						  chat_id=query.message.chat_id,
						  message_id=query.message.message_id)
		
		alert_DAO.update_alert(DUTY_NURSE_CHAT_ID, query['message']['text'], query.data)
		
		#i need retrieve resident name and time_stamp from alerts
		# print(query['message']['text'])
		alert_raw = alert_DAO.get_alert_by_id(DUTY_NURSE_CHAT_ID, query['message']['text'])
		alert_clean = alert_raw[0]
		resident_name = alert_clean['rname']
		received_timestamp = alert_clean['date']
		resident_id_raw = resident_DAO.get_resident_id_by_resident_name(resident_name)
		resident_id = resident_id_raw[0]['resident_id']
		rawuuids = sensor_hist_DAO.get_uuids_by_id(resident_id)
		for rawuuid in rawuuids:
			uuid = rawuuid['uuid']
			sensor_log_DAO.update_log(uuid, received_timestamp)
		residentNameList = resident_DAO.get_list_of_residentNames()
		latest_list = get_latest_alerts(residentNameList)
		latest_sensor_list = get_latest_sensor_alerts(residentNameList)
		latest_list = latest_list + latest_sensor_list
		if len(latest_list) > 0:
			keyboardBottom = [[alert] for alert in latest_list]
			reply_markupBottom = {"keyboard":keyboardBottom, "one_time_keyboard": True}
			bot.send_message(query.message.chat_id, "You still have these incomplete tasks:", reply_markup=reply_markupBottom)
		else:
			reply_markupRemove = ReplyKeyboardRemove()
			bot.send_message(query.message.chat_id, "You have no more tasks left", reply_markup=reply_markupRemove) 

	elif query.data == 'Defecation': 
		bot.edit_message_text(initialMsg + "\n\nUsing Toilet\n\nPurpose of visit: {}".format(query.data),
						  chat_id=query.message.chat_id,
						  message_id=query.message.message_id)

		alert_DAO.update_alert(DUTY_NURSE_CHAT_ID, initialMsg, query.data) 
		residentNameList = resident_DAO.get_list_of_residentNames()
		latest_list = get_latest_alerts(residentNameList)
		latest_sensor_list = get_latest_sensor_alerts(residentNameList)
		latest_list = latest_list + latest_sensor_list
		if len(latest_list) > 0:
			keyboardBottom = [[alert] for alert in latest_list]
			reply_markupBottom = {"keyboard":keyboardBottom, "one_time_keyboard": True}
			bot.send_message(query.message.chat_id, "You still have these incomplete tasks:", reply_markup=reply_markupBottom)
		else:
			reply_markupRemove = ReplyKeyboardRemove()
			bot.send_message(query.message.chat_id, "You have no more tasks left", reply_markup=reply_markupRemove) 

	elif query.data == 'Urine': 
		bot.edit_message_text(initialMsg + "\n\nUsing Toilet\n\nPurpose of visit: {}".format(query.data),
						  chat_id=query.message.chat_id,
						  message_id=query.message.message_id)

		alert_DAO.update_alert(DUTY_NURSE_CHAT_ID, initialMsg, query.data)  
		residentNameList = resident_DAO.get_list_of_residentNames()
		latest_list = get_latest_alerts(residentNameList)
		latest_sensor_list = get_latest_sensor_alerts(residentNameList)
		latest_list = latest_list + latest_sensor_list
		if len(latest_list) > 0:
			keyboardBottom = [[alert] for alert in latest_list]
			reply_markupBottom = {"keyboard":keyboardBottom, "one_time_keyboard": True}
			bot.send_message(query.message.chat_id, "You still have these incomplete tasks:", reply_markup=reply_markupBottom)
		else:
			reply_markupRemove = ReplyKeyboardRemove()
			bot.send_message(query.message.chat_id, "You have no more tasks left", reply_markup=reply_markupRemove) 

	elif query.data == 'Other Action': 
		bot.edit_message_text(initialMsg + "\n\nUsing Toilet\n\nPurpose of visit: {}".format(query.data),
						  chat_id=query.message.chat_id,
						  message_id=query.message.message_id)
		alert_DAO.update_alert(DUTY_NURSE_CHAT_ID, initialMsg, query.data) 
		residentNameList = resident_DAO.get_list_of_residentNames()
		latest_list = get_latest_alerts(residentNameList)
		latest_sensor_list = get_latest_sensor_alerts(residentNameList)
		latest_list = latest_list + latest_sensor_list
		if len(latest_list) > 0:
			keyboardBottom = [[alert] for alert in latest_list]
			reply_markupBottom = {"keyboard":keyboardBottom, "one_time_keyboard": True}
			bot.send_message(query.message.chat_id, "You still have these incomplete tasks:", reply_markup=reply_markupBottom)
		else:
			reply_markupRemove = ReplyKeyboardRemove()
			bot.send_message(query.message.chat_id, "You have no more tasks left", reply_markup=reply_markupRemove) 
				

	else:
		bot.edit_message_text(text=query.data,
						  chat_id=query.message.chat_id,
						  message_id=query.message.message_id, 
						  reply_markup=reply_markupDefault)
						  
def check_shift_form(shifttime):
	idQuery = shift_log_DAO.retrieveCountPerShift(shifttime)
	patientIDList = []
	# print(test)
	for item in idQuery[:]:
		patientID = item['patient_id']
		patientIDList.append(patientID)
	return patientIDList

def shiftform(bot, update):
	date = datetime.date.today()
	time = datetime.datetime.strptime('1200','%H%M').time()
	shifttime = datetime.datetime.combine(date, time)
	patientIDList = check_shift_form(shifttime)
	nameList = []
	checkList = []
	checkList.extend(range(9, 10))
	for patient_ID in patientIDList[:]:
		checkList.remove(patient_ID)
	for id in checkList:
		patientName = resident_DAO.get_resident_name_by_resident_id(id)[0]['name']
		nameList.append(patientName)
	if(len(nameList) > 0):
			text = "\n".join(nameList)
			link = "http://13.228.71.248/eosforms"
			bot.send_message(DUTY_NURSE_CHAT_ID, "*You have not completed your shift form for the following residents:*\n\n" + text + "\n\n*Click here to access the shift form:*\n" + link, parse_mode = 'markdown')
	
def help(bot, update):
	update.message.reply_text("Use /start to test this bot.")

def testing(message):
	alert_raw = alert_DAO.get_alert_by_id(DUTY_NURSE_CHAT_ID, message)
	alert_clean = alert_raw[0]
	resident_name = alert_clean['rname']
	received_timestamp = alert_clean['date']
	resident_id_raw = resident_DAO.get_resident_id_by_resident_name(resident_name)
	resident_id = resident_id_raw[0]['resident_id']
	rawuuids = sensor_hist_DAO.get_uuids_by_id(resident_id)
	for rawuuid in rawuuids:
		uuid = rawuuid['uuid']
		sensor_log_DAO.update_log(uuid, received_timestamp)
	
def sensoralert(bot, update):
	message = "*Sensor Issue:* Warning"+ "\n*Location:* " + 'Squid Ward' + " " + "toilet" + "\n*Type:* " + "motion"
	bot.send_message(DUTY_NURSE_CHAT_ID, message, parse_mode = 'markdown')
	date_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
	alert_DAO.insert_alert(DUTY_NURSE_CHAT_ID, date_time, 'Squid Ward', message, "Sensor", "No")
	residentNameList = resident_DAO.get_list_of_residentNames()
	latest_list = get_latest_alerts(residentNameList)
	latest_sensor_list = get_latest_sensor_alerts(residentNameList)
	# sensor_alerts = alert_DAO.get_sensor_alerts(DUTY_NURSE_CHAT_ID, "Sensor")
	# for sensor_alert in sensor_alerts:
		# sensor_alert_text = sensor_alert['alert_text']
		# latest_list.append(sensor_alert_text)
	print(latest_list)
	latest_list = latest_list + latest_sensor_list
	print(latest_list)
	keyboardBottom = [[alert] for alert in latest_list]
	reply_markupBottom = {"keyboard":keyboardBottom, "one_time_keyboard": True}
	bot.send_message(DUTY_NURSE_CHAT_ID, "Your task has been added to the to-do list:", reply_markup=reply_markupBottom)

def rectify(bot, update):
	residentNameList = resident_DAO.get_list_of_residentNames()
	latest_list = get_latest_alerts(residentNameList)
	latest_sensor_list = get_latest_sensor_alerts(residentNameList)
	sensor_alert_text= latest_sensor_list[0]
	alert_DAO.update_alert(DUTY_NURSE_CHAT_ID, sensor_alert_text, 'false')
	latest_sensor_list = get_latest_sensor_alerts(residentNameList)
	latest_list = latest_list + latest_sensor_list
	if len(latest_list) > 0:
		keyboardBottom = [[alert] for alert in latest_list]
		reply_markupBottom = {"keyboard":keyboardBottom, "one_time_keyboard": True}
		bot.send_message(DUTY_NURSE_CHAT_ID, "*Sensor issue has been rectified for:* \n" + sensor_alert_text, parse_mode = 'markdown', reply_markup=reply_markupBottom)
	else:
		reply_markupRemove = ReplyKeyboardRemove()
		bot.send_message(DUTY_NURSE_CHAT_ID, "*Sensor issue has been rectified for:* \n" + sensor_alert_text, parse_mode = 'markdown', reply_markup=reply_markupRemove)

	# downList = {}
	# for ss in Sensor_mgmt.get_all_sensor_status_v2(True):
		# id = ss[0]
		# loc = sensor_DAO.get_location_by_node_id(id)
		# location = loc[0]['location']
		# rawtype = sensor_DAO.get_type_by_node_id(id)
		# type = rawtype[0]['type']
		# rawuuid = sensor_hist_DAO.get_id_by_uuid(id)
		# if len(rawuuid)> 0:
			# residentid = rawuuid[0]['resident_id']
			# residentNameRaw = resident_DAO.get_resident_name_by_resident_id(residentid)
			# residentName = residentNameRaw[0]['name']
			# if 1 in ss[1]:
				# error = "Sensor Issue: Disconnected" + "\nLocation: " + residentName + " " + location + "\nType: " + type
				# downList.update({error : residentName})
			# elif 2 in ss[1]:
				# error = "Sensor Issue: Low Battery" + "\nLocation: " + residentName + " " + location + "\nType: " + type
				# downList.update({error : residentName})
			# elif 3 in ss[1]:
				# error = "Sensor Issue: Warning"+ "\nLocation: " + residentName + " " + location + "\nType: " + type
				# downList.update({error : residentName})
	# sensor_alerts = alert_DAO.get_sensor_alerts(DUTY_NURSE_CHAT_ID, "sensor")
	# sensorAlertList = []
	# for sensor_alert in sensor_alerts:
		# sensor_alert_text = sensor_alert['alert_text']
		# sensorAlertList.append(sensor_alert_text)
		# if sensor_alert_text not in downList.keys(): 
			# alert_DAO.update_alert(DUTY_NURSE_CHAT_ID, sensor_alert_text)
			# alerts = alert_DAO.get_alerts_by_id(DUTY_NURSE_CHAT_ID)
			# latest_list = get_latest_alerts(alerts)
			# sensor_alerts = alert_DAO.get_sensor_alerts(DUTY_NURSE_CHAT_ID, "sensor")
			# for sensor_alert in sensor_alerts:
				# sensor_alert_text = sensor_alert['alert_text']
				# latest_list.append(sensor_alert_text)
			# keyboardBottom = [[alert] for alert in latest_list]
			# reply_markupBottom = {"keyboard":keyboardBottom, "one_time_keyboard": True}
			# bot.send_message(DUTY_NURSE_CHAT_ID, "Sensor issue has been rectified for:\n" + sensor_alert_text, reply_markupBottom)
	# if(len(downList) > 0):
		# for key, value in downList.items():
			# if key not in sensorAlertList:
				# text = key
				# bot.send_message(DUTY_NURSE_CHAT_ID, text)
				# date_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
				# alert_DAO.insert_alert(DUTY_NURSE_CHAT_ID, date_time, value, text, "Sensor", "No")
				# alerts = alert_DAO.get_alerts_by_id(DUTY_NURSE_CHAT_ID)
				# latest_list = get_latest_alerts(alerts)
				# sensor_alerts = alert_DAO.get_sensor_alerts(DUTY_NURSE_CHAT_ID, "sensor")
				# for sensor_alert in sensor_alerts:
					# sensor_alert_text = sensor_alert['alert_text']
					# latest_list.append(sensor_alert_text)
				# keyboardBottom = [[alert] for alert in latest_list]
				# reply_markupBottom = {"keyboard":keyboardBottom, "one_time_keyboard": True}
				# bot.send_message(DUTY_NURSE_CHAT_ID, "Your task has been added to the to-do list:", reply_markup=reply_markupBottom)
				

def exists(inputText):
	alerts = alert_DAO.get_alerts_by_id(DUTY_NURSE_CHAT_ID)
	for alert in alerts[:]:
		
		item = alert['alert_text']
		if inputText == item:
			return True
	return False 

def text_reply(bot, update):
	
	keyboardDefault = [[InlineKeyboardButton("Yes, using toilet", callback_data='Using Toilet'),
				 InlineKeyboardButton("False Alarm", callback_data='False Alarm')]]

	reply_markupDefault = InlineKeyboardMarkup(keyboardDefault)
	
	# keyboardSensor = [[InlineKeyboardButton("Fixed", callback_data='fixed'), InlineKeyboardButton("False Alarm", callback_data='False Alarm')]]	
	# reply_markupSensor = InlineKeyboardMarkup(keyboardSensor)
	
	query = update.callback_query
	hitext = update.message.text
	print("hitext")
	if "Sensor" in hitext and exists(hitext):
		bot.send_message(update.message.chat_id, hitext)
	elif exists(hitext):
		bot.send_message(update.message.chat_id, hitext, reply_markup=reply_markupDefault, parse_mode = 'markdown')
		
def error(bot, update, error):
	"""Log Errors caused by Updates."""
	logger.warning('Update "%s" caused error "%s"', update, error)
	
def main():
	# Create the Updater and pass it your bot's token.
	
	updater = Updater("789766810:AAFOeW6ghhreo8tv6x6cMLSvnlt8nF91NqA")

	updater.dispatcher.add_handler(CallbackQueryHandler(button))
	updater.dispatcher.add_handler(MessageHandler(Filters.text, text_reply))
	updater.dispatcher.add_handler(CommandHandler('help', help))
	
	updater.dispatcher.add_handler(CommandHandler('shiftform', shiftform))
	updater.dispatcher.add_error_handler(error)
	
	updater.dispatcher.add_handler(CommandHandler('sensoralert', sensoralert))
	updater.dispatcher.add_handler(CommandHandler('rectify', rectify))
	# Start the Bot
	updater.start_polling()

	# Run the bot until the user presses Ctrl-C or the process receives SIGINT,
	# SIGTERM or SIGABRT
	updater.idle()
	# testing('*Assistance Alert:* Poh Kim Pew at 2018-11-13 18:19:53')


if __name__ == '__main__':
	main()


