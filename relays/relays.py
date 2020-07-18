from datetime import datetime, timedelta
from typing import List

from paho.mqtt import client as mqtt


def on_message(client, userdata, msg):
    # TODO listen to ack messages.
    ...


class TriggerException(Exception):
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


class LazyPercentInterval:
    def __init__(self, interval: timedelta, percent_on: float):
        if not (0 <= percent_on <= 1):
            raise TriggerException("percent must be in [0, 1]")
        self._interval = interval
        self._on = self._interval * percent_on
        self._off = self._interval * (1 - percent_on)

    def check(self, relay_state: MqttRelayState) -> bool:
        now = datetime.now()

        if relay_state.is_open():  # not running
            if now - relay_state.updated >= self._off:
                return True

        else:  # running
            if now - relay_state.updated >= self._on:
                return True

        return False


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
    def __init__(self, mqtt_client: mqtt, mqtt_topic: str, trigger, start_on=True, refresh_time=None):
        self._client = mqtt_client
        self.topic = mqtt_topic
        self.trigger = trigger
        self._refresh_time = refresh_time if refresh_time else timedelta(seconds=60)
        self._refreshed = datetime.now()

        if start_on:
            self.start()
        else:
            self.stop()

    @property
    def state(self):
        return self._state

    def start(self):
        self._client.publish(self.topic, MqttRelayState.CLOSE)
        self._state = MqttRelayState(MqttRelayState.CLOSE, updated=datetime.now())
        # TODO: update state after ack pub from actuator device

    def stop(self):
        self._client.publish(self.topic, MqttRelayState.OPEN)
        self._state = MqttRelayState(MqttRelayState.OPEN, updated=datetime.now())
        # TODO: update state after ack pub from actuator device

    def change_state(self):
        if self.state.is_open():
            self.start()
        else:
            self.stop()

    def refresh(self):
        self._refreshed = datetime.now()
        self._client.publish(self.topic, self.state.value)

    def process(self):
        if self.trigger.check(self.state):
            self.change_state()
        else:
            if datetime.now() >=  self._refreshed + self._refresh_time:
                self.refresh()

    def __str__(self):
        state = "Stopped" if self.state.is_open() else "Running"
        return f"{self.topic} - {state}"
