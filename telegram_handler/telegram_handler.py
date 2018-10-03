# simple python to use long polling for getting messages sent to telegram bots

import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters
import alert_DAO


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

        alert_DAO.delete_alert(DUTY_NURSE_CHAT_ID, query['message']['text'])
        alerts = alert_DAO.get_alerts_by_id(DUTY_NURSE_CHAT_ID)
        keyboardBottom = [[alert['alert_text']] for alert in alerts]
        reply_markupBottom = {"keyboard":keyboardBottom, "one_time_keyboard": True}
        bot.send_message(query.message.chat_id, "You still have these incomplete tasks:", reply_markup=reply_markupBottom) 

    elif query.data == 'Defecation': 
        bot.edit_message_text(initialMsg + "\n\nUsing Toilet\n\nPurpose of visit: {}".format(query.data),
                          chat_id=query.message.chat_id,
                          message_id=query.message.message_id)

        alert_DAO.delete_alert(DUTY_NURSE_CHAT_ID, initialMsg) 
        alerts = alert_DAO.get_alerts_by_id(DUTY_NURSE_CHAT_ID)
        keyboardBottom = [[alert['alert_text']] for alert in alerts]
        reply_markupBottom = {"keyboard":keyboardBottom, "one_time_keyboard": True}
        bot.send_message(query.message.chat_id, "You still have these incomplete tasks:", reply_markup=reply_markupBottom)   

    elif query.data == 'Urine': 
        bot.edit_message_text(initialMsg + "\n\nUsing Toilet\n\nPurpose of visit: {}".format(query.data),
                          chat_id=query.message.chat_id,
                          message_id=query.message.message_id)

        alert_DAO.delete_alert(DUTY_NURSE_CHAT_ID, initialMsg) 
        alerts = alert_DAO.get_alerts_by_id(DUTY_NURSE_CHAT_ID)
        keyboardBottom = [[alert['alert_text']] for alert in alerts]
        reply_markupBottom = {"keyboard":keyboardBottom, "one_time_keyboard": True}
        bot.send_message(query.message.chat_id, "You still have these incomplete tasks:", reply_markup=reply_markupBottom) 

    elif query.data == 'Other Action': 
        bot.edit_message_text(initialMsg + "\n\nUsing Toilet\n\nPurpose of visit: {}".format(query.data),
                          chat_id=query.message.chat_id,
                          message_id=query.message.message_id)
        alert_DAO.delete_alert(DUTY_NURSE_CHAT_ID, initialMsg)
        alerts = alert_DAO.get_alerts_by_id(DUTY_NURSE_CHAT_ID)
        keyboardBottom = [[alert['alert_text']] for alert in alerts]
        reply_markupBottom = {"keyboard":keyboardBottom, "one_time_keyboard": True}
        bot.send_message(query.message.chat_id, "You still have these incomplete tasks:", reply_markup=reply_markupBottom) 
   
    else:
        bot.edit_message_text(text=query.data,
                          chat_id=query.message.chat_id,
                          message_id=query.message.message_id, 
                          reply_markup=reply_markupDefault)


def help(bot, update):
    update.message.reply_text("Use /start to test this bot.")

def list(bot, update):

    alerts = alert_DAO.get_alerts_by_id(DUTY_NURSE_CHAT_ID)

    message = update.message
    keyboard = []
    # keyboardBottom = []
    alerts_list = []
    for alert in alerts[:]:
        
        item = alert['alert_text']
        alerts_list.append(item)
        InlineKeyboardButton(text="{}".format(item), callback_data="{}".format(item))
        keyboard.append([InlineKeyboardButton(text="{}".format(item), callback_data="{}".format(item))])
        # keyboardBottom.append([item])
    reply_markup = InlineKeyboardMarkup(keyboard) 
    # keyboardBottom = [[yo['alert_text']] for yo in alerts]
    # reply_markupBottom = {"keyboard":keyboardBottom, "one_time_keyboard": True}

    text = "\n".join(alerts_list)
    bot.send_message(message.chat_id, text, reply_markup=reply_markup)
    # bot.send_message(message.chat_id, text, reply_markup=reply_markupBottom)

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

    query = update.callback_query
    hitext = update.message.text
    if exists(hitext):
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
    updater.dispatcher.add_handler(CommandHandler('list', list))
    updater.dispatcher.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    # Run the bot until the user presses Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT
    updater.idle()


if __name__ == '__main__':
    main()


