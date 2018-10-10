FROM python:3.6

COPY . /

RUN pip install paho-mqtt
RUN pip install telepot
RUN pip install requests
RUN pip install telebot
RUN pip install python-telegram-bot==11.1.0
RUN pip install mysqlclient
RUN pip install PyMySQL

CMD ["python", "/mqtt_alert_consumer.py"]

