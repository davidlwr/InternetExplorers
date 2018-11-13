FROM python:3

COPY telegram_handler.py /

RUN pip install paho-mqtt
RUN pip install requests

CMD ["python", "/telegram_handler.py"]

