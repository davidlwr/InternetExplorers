FROM python:3

COPY alert_module.py /

RUN pip install paho-mqtt
RUN pip install PyMySQL
RUN pip install telepot
RUN pip install pprintpp

CMD ["python", "/alert_module.py"]

