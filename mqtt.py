from socket import timeout
from time import sleep

from paho.mqtt import client as mqtt


class MQTTConnectError(Exception):
    ...


def on_connect(client, userdata, flags, rc):
    print(f"CONNACK received with code: {rc}")


def create_client(host, port, keepalive=60, tries=10, pause=5):

    client = mqtt.Client()
    client.on_connect = on_connect

    print(f"Connecting to {port}:{host}...")

    for i in range(tries):
        try:
            client.connect(host, port, keepalive=keepalive)
        except timeout as e:
            raise MQTTConnectError("Connect timed out.") from e
        except Exception as e:
            if i < tries - 1:
                print(
                    f"Failed to connect ({i+1}/{tries}). Retrying in {pause} seconds..."
                )
                sleep(pause)
                continue
            else:
                raise MQTTConnectError("Max retries reached.") from e
        break

    client.loop_start()
    return client
