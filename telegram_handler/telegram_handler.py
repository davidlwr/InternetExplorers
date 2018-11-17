# simple python to use long polling for getting messages sent to telegram bots

import logging
import datetime
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters
from DAOs import alert_DAO
from DAOs import shift_log_DAO
from DAOs import resident_DAO
from DAOs.sensor_log_DAO import sensor_log_DAO
from DAOs import sensor_hist_DAO



DUTY_NURSE_CHAT_ID = -251433967

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
		alert_raw = alert_DAO.get_alert_by_id(DUTY_NURSE_CHAT_ID, query['message']['text'])
		alert_clean = alert_raw[0]
		resident_name = alert_clean['rname']
		received_timestamp = alert_clean['date']
		resident_id_raw = resident_DAO.get_resident_id_by_resident_name(resident_name)
		resident_id = resident_id_raw['resident_id']
		rawuuids = sensor_hist_DAO.get_uuids_by_id(resident_id)
		for rawuuid in rawuuids:
			uuid = rawuuid['uuid']
			sensor_log_DAO.update_log(uuid, received_timestamp)
		
		residentNameList = resident_DAO.get_list_of_residentNames()
		latest_list = get_latest_alerts(residentNameList)
		print(latest_list)
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
	checkList.extend(range(1, 9))
	for patient_ID in patientIDList[:]:
		checkList.remove(patient_ID)
	for id in checkList:
		patientName = resident_DAO.get_resident_name_by_resident_id(id)[0]['name']
		nameList.append(patientName)
	if(len(nameList) > 0):
			text = "\n".join(nameList)
			link = "http://stb-broker.lvely.net/eosforms"
			bot.send_message(DUTY_NURSE_CHAT_ID, "You have not completed your shift logs for the following residents:\n" + text + "\n\nClick here to access the shift form:\n" + link)
	
def help(bot, update):
	update.message.reply_text("Use /start to test this bot.")

	
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
	if exists(hitext) and "Sensor" in hitext:
		bot.send_message(update.message.chat_id, hitext)
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
	
	updater.dispatcher.add_handler(CommandHandler('shiftform', shiftform))
	updater.dispatcher.add_error_handler(error)
	
	# updater.dispatcher.add_handler(CommandHandler('sensoralert', sensoralert))
	# Start the Bot
	updater.start_polling()

	# Run the bot until the user presses Ctrl-C or the process receives SIGINT,
	# SIGTERM or SIGABRT
	updater.idle()


if __name__ == '__main__':
	main()


