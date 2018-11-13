======================================== How to Create Docker Container ========================================
Step 1: Navigate to folder containing mqtt_consumer.py 

Step 2: Create Docker image by running command:
	"sudo docker build -t mqtt_consumer ."

Step 3: RUN the created Docker image:
	"sudo docker run -e TZ=Asia/Singapore --network host -d -v ~/mqtt_consumer/logs:/logs --restart unless-stopped --name mqtt_consumer_container mqtt_consumer"
