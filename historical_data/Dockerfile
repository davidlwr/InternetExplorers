FROM python:3.6

COPY . /

RUN pip install requests
RUN pip install schedule
RUN pip install mysqlclient
RUN pip install PyMySQL
RUN pip install pandas==0.22.0
RUN pip install matplotlib

CMD ["python", "./anomaly_detection.py"]