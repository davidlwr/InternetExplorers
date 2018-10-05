MQTT_CONSUMER =================================================
CREATE IMAGE
	sudo docker build -t telegram_handler .

RUN
	sudo docker run -e TZ=Asia/Singapore --network host -itd --restart unless-stopped --name telegram_handler_cont telegram_handler
