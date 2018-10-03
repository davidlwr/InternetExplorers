	import requests
	import json
	import datetime

	token = '687512562:AAGEoEH8wpDU3PK5TU0X3lar40FIfDetAHY'
	teleurl = 'https://api.telegram.org/bot' + token + '/'

	DUTY_NURSE_CHAT_ID = 260905740

	def send_message_with_reply(chat, text):

	params = {'chat_id' : chat, 'text': text}
	response = requests.post(teleurl + 'sendMessage', data=params)
	return response


	def check_shift_form()
		residentLog.retrievefrom 



	while 1:
	current_time=datetime.datetime.now()
	# print(current_time)
	hour = current_time.hour
	minute = current_time.minute
	second = current_time.second
	microsecond = current_time.microsecond
	if((hour ==17) and (minute==14) and (second == 0)):

		# reply_markup = {"inline_keyboard": [[{"text": "Yes, using toilet", "callback_data": "Using Toilet"}, {"text": "False Alarm", "callback_data": "False Alarm"}]]}
		send_message_with_reply(DUTY_NURSE_CHAT_ID, "You have not completed your shift form logs for the following residents:")
