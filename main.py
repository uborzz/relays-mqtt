import os
from datetime import datetime, timedelta
from time import sleep
from typing import List

from dotenv import load_dotenv
from paho.mqtt import client as mqtt

load_dotenv()


mqtt_host = os.getenv("MQTT_HOST")
mqtt_port = int(os.getenv("MQTT_PORT"))

client = mqtt.Client()
client.connect(mqtt_host, mqtt_port)


def on_message(client, userdata, msg):
    # TODO listen to ack messages.
    ...


class MqttRelayState:

    # states for mqtt messages
    CLOSE = 0
    OPEN = 1

    def __init__(self, value=0, updated: datetime = None):
        self.value = value
        self.updated = updated if updated else datetime.now()

    def is_open(self):
        return self.value == self.OPEN

    def __str__(self):
        return f"{self.value} - {self.updated}"


class LazyInterval:
    def __init__(self, delta: timedelta):
        self.delta = delta

    def check(self, relay_state: MqttRelayState) -> bool:
        return True if datetime.now() > relay_state.updated + self.delta else False


class ScheduledHours:
    def __init__(self, hours_active: List[int]):
        """Range: [0 ... 23]"""
        self.hours_active = hours_active

    def check(self, relay_state: MqttRelayState) -> bool:
        now = datetime.now().hour

        # closed hours
        if now in self.hours_active:
            return True if relay_state.is_open() else False
                
        # open hours
        else:
            return True if not relay_state.is_open() else False


class TimedMqttRelay:
    def __init__(self, mqtt_topic: str, trigger, start_on=True):
        self.topic = mqtt_topic
        self.trigger = trigger

        if start_on:
            self.start()
        else:
            self.stop()

    @property
    def state(self):
        return self._state

    def start(self):
        client.publish(self.topic, MqttRelayState.CLOSE)
        self._state = MqttRelayState(MqttRelayState.CLOSE, updated=datetime.now())
        # TODO: update state after ack pub from actuator device

    def stop(self):
        client.publish(self.topic, MqttRelayState.OPEN)
        self._state = MqttRelayState(MqttRelayState.OPEN, updated=datetime.now())
        # TODO: update state after ack pub from actuator device

    def change_state(self):
        if self.state.is_open():
            self.start()
        else:
            self.stop()

    def process(self):
        if self.trigger.check(self.state):
            self.change_state()

    def __str__(self):
        state = "Stopped" if self.state.is_open() else "Running"
        return f"{self.topic} - {state}"

