FROM python:3.6

COPY . /

RUN pip install paho-mqtt
RUN pip install telepot
RUN pip install requests
RUN pip install telebot
RUN pip install python-telegram-bot==11.1.0
RUN pip install mysqlclient
RUN pip install PyMySQL
RUN pip install pandas==0.22.0

CMD ["python", "/sensor_status_alert.py"]