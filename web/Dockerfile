FROM ubuntu:16.04
MAINTAINER SMUFYPIE "stbinternetexplorers@gmail.com"
ENV DEBIAN_FRONTEND noninteractive
RUN apt-get update -y
RUN apt-get install -y software-properties-common python-software-properties
RUN add-apt-repository ppa:jonathonf/python-3.6
RUN apt-get update -y
RUN apt-get install -y python3-pip python3.6-dev build-essential
RUN python3.6 -m pip install pip --upgrade
RUN python3.6 -m pip install wheel
RUN apt-get install -y mysql-client
RUN apt-get install -y libmysqlclient-dev
RUN apt-get install -y apt-utils
RUN pip3 install --upgrade pip
RUN pip3 install plotly==2.7.0 Flask==1.0.2
RUN pip3 install Jinja2==2.10 dash==0.21.1
RUN pip3 install mysqlclient==1.3.12 Flask-Login==0.4.1
RUN pip3 install dash-renderer==0.13.0
COPY . /app
WORKDIR /app
RUN pip3 install -r requirements.txt
ENTRYPOINT ["python3.6"]
CMD ["index.py"]
