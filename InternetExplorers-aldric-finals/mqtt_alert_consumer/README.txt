MQTT_CONSUMER =================================================
CREATE IMAGE
	sudo docker build -t mqtt_alert_consumer .

RUN
	sudo docker run -e TZ=Asia/Singapore --network host -itd -v ~acceptance_alert/mqtt_alert_consumer/logs:/logs --restart unless-stopped --name mqtt_alert_consumer_cont mqtt_alert_consumer
