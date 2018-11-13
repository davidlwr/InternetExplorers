MQTT_CONSUMER =================================================
CREATE IMAGE
	sudo docker build -t alert_module .

RUN
	sudo docker run -e TZ=Asia/Singapore --network host -d -v ~/alert_module/logs:/logs --restart unless-stopped --name alert_module_container alert_module
