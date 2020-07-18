import os
from datetime import timedelta
from time import sleep

from dotenv import load_dotenv
from relays import LazyPercentInterval, TimedMqttRelay
from mqtt import create_client

load_dotenv()

mqtt_host = os.getenv("MQTT_HOST")
mqtt_port = int(os.getenv("MQTT_PORT"))
client = create_client(mqtt_host, mqtt_port)


# sample

i = LazyPercentInterval(timedelta(seconds=10), percent_on=0.3)
r = TimedMqttRelay(client, "comino", i)
while True:
    r.process()
    print(r)
    sleep(1)
