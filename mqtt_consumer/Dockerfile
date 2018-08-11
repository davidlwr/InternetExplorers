FROM python:3

COPY mqtt_consumer.py

RUN pip install paho-mqtt
RUN pip install PyMySQL

CMD ["python", "/mqtt_consumer.py"]

