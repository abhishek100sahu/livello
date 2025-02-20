import asyncio
import os
import signal

from gmqtt import Client as MQTTClient
from MessageParser import MessageParser

STOP = asyncio.Event()

TOPIC = "devices/events"

# Use the container name as the broker address (Docker internal DNS resolution)
BROKER_IP = "mosquitto"

def ask_exit(*args):
    STOP.set()

def on_connect(client, flags, rc, properties):
    print("✅ Subscriber connected to broker.")
    client.subscribe(TOPIC, qos=0)

def on_message(client, topic, payload, qos, properties):
    print(f"📩 Received message from {topic}: {payload.decode()}")

    parsed_message = MessageParser.parse_message(payload.decode())
    print("✅ Parsed Message:", parsed_message)

def on_disconnect(client, packet, exc=None):
    print("❌ Subscriber disconnected.")

def on_subscribe(client, mid, qos, properties):
    print("✅ Successfully subscribed to topic.")

async def main():
    client = MQTTClient("subscriber-client-id")

    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect
    client.on_subscribe = on_subscribe

    await client.connect(BROKER_IP)

    # Wait for STOP event to exit gracefully
    await STOP.wait()
    
    await client.disconnect()

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    if os.name != "nt":  # Unix-based signal handling
        loop.add_signal_handler(signal.SIGINT, ask_exit)
        loop.add_signal_handler(signal.SIGTERM, ask_exit)

    try:
        loop.run_until_complete(main())
    finally:
        loop.close()
