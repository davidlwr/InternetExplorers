# simple python to use long polling for getting messages sent to telegram bots

import requests # or requests with telegram API
import json # parsing responses
import time
import datetime

# conn = pymysql.connect(host='localhost', port=3306, user='root', passwd='', db='scrub', autocommit=True)

# cursor = conn.cursor()

# from states import *
# for connection to telegram bot API
token = '687512562:AAGEoEH8wpDU3PK5TU0X3lar40FIfDetAHY'
teleurl = 'https://api.telegram.org/bot' + token + '/'

# patterns = {'greet': re.compile('hello|hi|hey'), 'thankyou': re.compile('thank|thx')}
# state = INIT
#
# nlp = spacy.load('en')
# training_data = load_data('training.json')
#
# args = {'pipeline':'spacy_sklearn'}
# config = RasaNLUConfig(cmdline_args=args)
# trainer = Trainer(config)
#
# interpreter = trainer.train(training_data)

def get_updates_json(request, offset=None):
    params = {'timeout': 100, 'offset': offset}
    response = requests.get(request + 'getUpdates', data=params)
    return response.json()

def get_chat_id(update):
    chat_id = update['message']['chat']['id']
    return chat_id

def send_message(chat, text):
    params = {'chat_id' : chat, 'text': text}
    response = requests.post(teleurl + 'sendMessage', data=params)
    return response
    
def answer_cb_query(cb_id):
    params = {'callback_query_id': cb_id}
    response = requests.post(teleurl + 'answerCallbackQuery', data=params)

def send_message_with_reply(chat, text, reply_markup):
    print("here")
    params = {'chat_id' : chat, 'text': text, 'reply_markup': json.dumps(reply_markup)}
    response = requests.post(teleurl + 'sendMessage', data=params)
    return response

def last_update(data):
    # print(data)
    results = data['result']
    total_updates = len(results) - 1
    if total_updates < 0:
      return None
    # print(total_updates)
    return results[total_updates]

# below specific to this chat bot
# def get_reply(message, user_name='my friend', state=INIT):
    # interpreted = interpreter.parse(message)
    # print(interpreted)
    # intent = interpreted['intent']['name']
    # ret = ''
    # print("current state LOL ", state)
    # if state == LOOKING_FOR_PLACE:
    #     if intent == 'state_place':
    #         entities = interpreted['entities']
    #         print('entities ', entities)
    #         try:
    #             _location = entities[0]['value']
    #             ret = 'Okay, I will get you a place at a bar near ' + _location
    #         except:
    #             ret = 'Sorry, we don\'t have partner establishments at this location yet'
    #     elif intent == 'deny':
    #         state = INIT
    #         ret = 'Alright, ask me something else then :)'
    #         return ret, state
    #     else:
    #         ret = 'Do you still want to find a place to watch the next match?'
    #     try:
    #         state = policy_rules[(state, intent)]
    #     except:
    #         state = LOOKING_FOR_PLACE
    #     return ret, state
    #
    # if intent == 'affirm':
    #     ret = 'Great!'
    # elif intent == 'greet':
    #     ret = 'Hello {}!'.format(user_name)
    # elif intent == 'find_teams':
    #     ret = 'The teams still playing are France, Croatia, Belgium and England!'
    # elif intent == 'find_members_belgium':
    #     ret = 'The players are Courtois, Mignolet, Casteels, Alderweireld, Vermaelen, Kompany, Vertonghen, Meunier, Boyata, Dendoncker, Witsel, De Bruyne, Fellaini, Carrasco, T.Hazard, Tielemans, Dembele, Chadli, R. Lukaku, E. Hazard, Merterns, Januzaj, Batshuayi and Martinez Roberto!'
    # elif intent == 'find_place_to_watch':
    #     ret = 'Sure, where are you now?'
    # elif intent == 'past_goals':
    #     cursor.execute("SELECT * from pastgoals where voting = (select max(voting) from pastgoals)")
    #     result=cursor.fetchone()
    #     ret = 'Hot favorites at stage '+result[3] +' is '+result[1]+' vs '+result[2]+ ', '+str(result[4])+':'+str(result[5])
    # else:
    #     ret = 'Can you repeat that again?'
    # try:
    #     (state, text2) = policy_rules[(state, intent)]
    # except Exception:
    #     print('error occured line 100', Exception)
    #     state = INIT
    # return ret, state

def main():
    current_offset = None
    while True:
        update = last_update(get_updates_json(teleurl, current_offset))
        if update is None:
            print("none")
            time.sleep(0.5)
            continue
        print(update)
        # if 'entities' in update['message']:
        #     print("Have entities")
        #
        latest_update_id = update['update_id']
        # latest_chat_text=''
        # try:
        #     latest_chat_text = update['message']['text']
        # except:
        #     pass
        
        
        ts = time.time()
        try:
            latest_chat_id = update['message']['chat']['id']
            # (latest_chat_id, text)
            
        except:
            latest_chat_id = update['callback_query']['from']['id']
            callback_query_id = update['callback_query']['id']
            # check data
            received_data = update['callback_query']['data']
            # send_message(latest_chat_id, received_data)
            
            if received_data == 'toiletPoh':
                reply_markup = {"inline_keyboard": [[{"text": "Urination", "callback_data": "urine"}], [{"text": "Defecation", "callback_data": "defecation"}], [{"text": "Others", "callback_data": "other"}]]}
                send_message_with_reply(latest_chat_id, 'Select purpose of toilet visit:', reply_markup)
            elif received_data == 'falseAlarm':
                send_message(latest_chat_id, 'False Alarm Recorded at ' + datetime.datetime.fromtimestamp(ts).strftime('%H:%M:%S'))
            elif received_data == 'urine':
                send_message(latest_chat_id, 'Urine Action Recorded at ' + datetime.datetime.fromtimestamp(ts).strftime('%H:%M:%S'))
            elif received_data == 'defecation':
                send_message(latest_chat_id, 'Defecation Action Recorded at ' + datetime.datetime.fromtimestamp(ts).strftime('%H:%M:%S'))
            elif received_data == 'other':
                send_message(latest_chat_id, 'Other Action Recorded at ' + datetime.datetime.fromtimestamp(ts).strftime('%H:%M:%S'))
            else:
                pass
            
            answer_cb_query(callback_query_id)
            
        # latest_chat_name = update['message']['chat']['first_name']
        # cursor.execute("SELECT current_state FROM `userstates` WHERE `chatid` = %s", latest_chat_id)
        # if cursor.rowcount == 0:
        #     state = INIT
        #     cursor.execute("INSERT INTO userstates VALUES (%s, %s)", (latest_chat_id, state))
        # else:
        #     state = cursor.fetchone()[0]
        #     print(state)
        #
        # # print(interpreter.parse(latest_chat_text))
        # (text, state) = get_reply(latest_chat_text, latest_chat_name, state)
        
        #
        current_offset = latest_update_id + 1
        #
        # # write state
        # cursor.execute("UPDATE userstates SET current_state = %s WHERE chatid = %s", (str(state), str(latest_chat_id)))
        time.sleep(1)

try:
    main()
except KeyboardInterrupt:
    exit()
finally:
    # cursor.close()
    # conn.close()
    pass
