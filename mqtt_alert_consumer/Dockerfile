FROM python:3

COPY mqtt_alert_consumer.py /

RUN pip install paho-mqtt
RUN pip install telepot
RUN pip install requests

CMD ["python", "/mqtt_alert_consumer.py"]

