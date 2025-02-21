import asyncio
import os
import signal
import uuid
from gmqtt import Client as MQTTClient
from MessageParser import MessageParser

STOP = None

TOPIC = os.getenv("MQTT_TOPIC", "devices/events")
BROKER_IP = os.getenv("MQTT_BROKER_HOST", "mqtt-broker")

# TOPIC = "devices/events"
# BROKER_IP = "127.0.0.1"


def ask_exit(*args):
    if STOP:
        STOP.set()


def on_connect(client, flags, rc, properties):
    print(f"Subscriber connected to broker.")
    client.subscribe(TOPIC, qos=0)


def on_message(client, topic, payload, qos, properties):
    print(f"Received message from {topic}: {payload.decode()}")
    MessageParser.parse_message(payload.decode())


def on_disconnect(client, packet, exc=None):
    print("Subscriber disconnected.")


def on_subscribe(client, mid, qos, properties):
    print("Successfully subscribed to topic.")


async def main():
    global STOP
    STOP = asyncio.Event()  # Create inside main event loop

    client = MQTTClient(client_id=f"{uuid.uuid4().hex[:8].upper()}")

    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect
    client.on_subscribe = on_subscribe

    await client.connect(BROKER_IP)

    # Wait for STOP event to exit gracefully
    await STOP.wait()

    await client.disconnect()


if __name__ == "__main__":
    loop = asyncio.new_event_loop()  # Ensuring a clean event loop
    asyncio.set_event_loop(loop)

    if os.name != "nt":  # Unix-based signal handling
        loop.add_signal_handler(signal.SIGINT, ask_exit)
        loop.add_signal_handler(signal.SIGTERM, ask_exit)

    try:
        loop.run_until_complete(main())
    finally:
        loop.close()
