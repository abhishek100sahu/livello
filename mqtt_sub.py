import asyncio
import os
import signal

from gmqtt import Client as MQTTClient

STOP = asyncio.Event()


def ask_exit(*args):
    STOP.set()


def on_connect(client, flags, rc, properties):
    print("Subscriber connected to broker.")
    client.subscribe("TEST/#", qos=0)


def on_message(client, topic, payload, qos, properties):
    print(f"Received message from {topic}: {payload.decode()}")


def on_disconnect(client, packet, exc=None):
    print("Subscriber disconnected.")


def on_subscribe(client, mid, qos, properties):
    print("Subscriber successfully subscribed to topic.")


async def main():
    client = MQTTClient("subscriber-client-id")

    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect
    client.on_subscribe = on_subscribe

    await client.connect("172.17.0.2")

    # Use asyncio.create_task to handle stopping gracefully
    stop_task = asyncio.create_task(STOP.wait())

    try:
        await stop_task  # Wait until STOP event is set
    except KeyboardInterrupt:
        print("KeyboardInterrupt received, shutting down...")

    await client.disconnect()


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # Unix-only signal handling
    if os.name != "nt":  # Not Windows
        loop.add_signal_handler(signal.SIGINT, ask_exit)
        loop.add_signal_handler(signal.SIGTERM, ask_exit)

    try:
        loop.run_until_complete(main())
    finally:
        loop.close()
