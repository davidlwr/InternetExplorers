MQTT_CONSUMER =================================================
CREATE IMAGE
	sudo docker build -t mqtt_consumer .

RUN
	sudo docker run -e TZ=Asia/Singapore --network host -d -v ~/mqtt_consumer/logs:/logs --restart unless-stopped --name mqtt_consumer_container mqtt_consumer
