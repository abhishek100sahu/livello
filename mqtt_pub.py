import asyncio
import time
from gmqtt import Client as MQTTClient

STOP = asyncio.Event()

TOPIC = "devices/events"

BROKER_IP = "172.17.0.2"

def ask_exit():
    STOP.set()


def on_connect(client, flags, rc, properties):
    print("Publisher connected to broker.")


def on_disconnect(client, packet, exc=None):
    print("Publisher disconnected.")


async def main():
    client = MQTTClient("publisher-client-id")

    client.on_connect = on_connect
    client.on_disconnect = on_disconnect

    await client.connect(BROKER_IP)
    # "172.17.0.2"

    try:
        while not STOP.is_set():
            message = f"Current Time: {time.time()}"
            print(f"Publishing message: {message}")
            client.publish(TOPIC, message, qos=1)
            await asyncio.sleep(2)
    except KeyboardInterrupt:
        print("KeyboardInterrupt received, shutting down...")
        ask_exit()
    finally:
        await client.disconnect()


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        loop.run_until_complete(main())
    finally:
        loop.close()
