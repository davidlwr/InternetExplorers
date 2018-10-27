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
from DAOs import sensor_hist_DAO



DUTY_NURSE_CHAT_ID = -251433967

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

		alert_DAO.update_alert(DUTY_NURSE_CHAT_ID, query['message']['text'])
		alerts = alert_DAO.get_alerts_by_id(DUTY_NURSE_CHAT_ID)
		if len(alerts) > 0:
			keyboardBottom = [[alert['alert_text']] for alert in alerts]
			reply_markupBottom = {"keyboard":keyboardBottom, "one_time_keyboard": True}
			bot.send_message(query.message.chat_id, "You still have these incomplete tasks:", reply_markup=reply_markupBottom)
		else:
			reply_markupRemove = ReplyKeyboardRemove()
			bot.send_message(query.message.chat_id, "You have no more tasks left", reply_markup=reply_markupRemove) 

	elif query.data == 'Defecation': 
		bot.edit_message_text(initialMsg + "\n\nUsing Toilet\n\nPurpose of visit: {}".format(query.data),
						  chat_id=query.message.chat_id,
						  message_id=query.message.message_id)

		alert_DAO.update_alert(DUTY_NURSE_CHAT_ID, initialMsg) 
		alerts = alert_DAO.get_alerts_by_id(DUTY_NURSE_CHAT_ID)
		if len(alerts) > 0:
			keyboardBottom = [[alert['alert_text']] for alert in alerts]
			reply_markupBottom = {"keyboard":keyboardBottom, "one_time_keyboard": True}
			bot.send_message(query.message.chat_id, "You still have these incomplete tasks:", reply_markup=reply_markupBottom)
		else:
			reply_markupRemove = ReplyKeyboardRemove()
			bot.send_message(query.message.chat_id, "You have no more tasks left", reply_markup=reply_markupRemove)

	elif query.data == 'Urine': 
		bot.edit_message_text(initialMsg + "\n\nUsing Toilet\n\nPurpose of visit: {}".format(query.data),
						  chat_id=query.message.chat_id,
						  message_id=query.message.message_id)

		alert_DAO.update_alert(DUTY_NURSE_CHAT_ID, initialMsg) 
		alerts = alert_DAO.get_alerts_by_id(DUTY_NURSE_CHAT_ID)
		if len(alerts) > 0:
			keyboardBottom = [[alert['alert_text']] for alert in alerts]
			reply_markupBottom = {"keyboard":keyboardBottom, "one_time_keyboard": True}
			bot.send_message(query.message.chat_id, "You still have these incomplete tasks:", reply_markup=reply_markupBottom)
		else:
			reply_markupRemove = ReplyKeyboardRemove()
			bot.send_message(query.message.chat_id, "You have no more tasks left", reply_markup=reply_markupRemove)

	elif query.data == 'Other Action': 
		bot.edit_message_text(initialMsg + "\n\nUsing Toilet\n\nPurpose of visit: {}".format(query.data),
						  chat_id=query.message.chat_id,
						  message_id=query.message.message_id)
		alert_DAO.update_alert(DUTY_NURSE_CHAT_ID, initialMsg)
		alerts = alert_DAO.get_alerts_by_id(DUTY_NURSE_CHAT_ID)
		if len(alerts) > 0:
			keyboardBottom = [[alert['alert_text']] for alert in alerts]
			reply_markupBottom = {"keyboard":keyboardBottom, "one_time_keyboard": True}
			bot.send_message(query.message.chat_id, "You still have these incomplete tasks:", reply_markup=reply_markupBottom)
		else:
			reply_markupRemove = ReplyKeyboardRemove()
			bot.send_message(query.message.chat_id, "You have no more tasks left", reply_markup=reply_markupRemove) 
	
	elif query.data == 'fixed':
		text = query['message']['text']
		bot.edit_message_text(text + "\nProblem fixed",
						  chat_id=DUTY_NURSE_CHAT_ID,
						  message_id=query.message.message_id)
		alert_DAO.update_alert(DUTY_NURSE_CHAT_ID, text)
		alerts = alert_DAO.get_alerts_by_id(DUTY_NURSE_CHAT_ID)
		if len(alerts) > 0:
			keyboardBottom = [[alert['alert_text']] for alert in alerts]
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
	print("trig")
	date = datetime.date.today()
	time = datetime.datetime.strptime('1200','%H%M').time()
	shifttime = datetime.datetime.combine(date, time)
	patientIDList = check_shift_form(shifttime)
	print("trig")
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
		bot.send_message(DUTY_NURSE_CHAT_ID, "You have not completed your shift logs for the following residents:\n" + text)
	
	
def help(bot, update):
	update.message.reply_text("Use /start to test this bot.")

def sensoralert(bot, update):
	
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
				
	reply_markup = {"inline_keyboard": [[{"text": "Fixed", "callback_data": "fixed"},{"text": "False Alarm", "callback_data": "False Alarm"}]]}
	if(len(downList) > 0):
		# text = "\n".join(downList)
		for downSS in downList: 
			text = downSS
			bot.send_message(DUTY_NURSE_CHAT_ID, text, reply_markup=reply_markup)				
			alert_DAO.insert_alert(DUTY_NURSE_CHAT_ID, datetime, text, "Sensor", "No")
		alerts = alert_DAO.get_alerts_by_id(DUTY_NURSE_CHAT_ID)
		keyboardBottom = [[alert['alert_text']] for alert in alerts]
		reply_markupBottom = {"keyboard":keyboardBottom, "one_time_keyboard": True}
		bot.send_message(DUTY_NURSE_CHAT_ID, "Your task has been added to the to-do list:", reply_markup=reply_markupBottom)

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
	
	keyboardSensor = [[InlineKeyboardButton("Fixed", callback_data='fixed'), InlineKeyboardButton("False Alarm", callback_data='False Alarm')]]	
	reply_markupSensor = InlineKeyboardMarkup(keyboardSensor)
	
	query = update.callback_query
	hitext = update.message.text
	if exists(hitext) and "Sensor" in hitext:
		bot.send_message(update.message.chat_id, hitext, reply_markup=reply_markupSensor)
	else:
		bot.send_message(update.message.chat_id, hitext, reply_markup=reply_markupDefault)
		
def error(bot, update, error):
	"""Log Errors caused by Updates."""
	logger.warning('Update "%s" caused error "%s"', update, error)
	
def main():
	# Create the Updater and pass it your bot's token.
	
	updater = Updater("687512562:AAGEoEH8wpDU3PK5TU0X3lar40FIfDetAHY")

	updater.dispatcher.add_handler(CallbackQueryHandler(button))
	updater.dispatcher.add_handler(MessageHandler(Filters.text, text_reply))
	updater.dispatcher.add_handler(CommandHandler('help', help))
	updater.dispatcher.add_handler(CommandHandler('sensoralert', sensoralert))
	updater.dispatcher.add_handler(CommandHandler('shiftform', shiftform))
	updater.dispatcher.add_error_handler(error)

	# Start the Bot
	updater.start_polling()

	# Run the bot until the user presses Ctrl-C or the process receives SIGINT,
	# SIGTERM or SIGABRT
	updater.idle()


if __name__ == '__main__':
	main()


