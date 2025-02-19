import asyncio
import os
import signal
import time

from gmqtt import Client as MQTTClient

# Use uvloop for better performance
import uvloop
asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

STOP = asyncio.Event()

def on_connect(client, flags, rc, properties):
    print('Connected')
    client.subscribe('TEST/#', qos=0)

def on_message(client, topic, payload, qos, properties):
    print('RECV MSG:', payload)

def on_disconnect(client, packet, exc=None):
    print('Disconnected')

def on_subscribe(client, mid, qos, properties):
    print('SUBSCRIBED')

def ask_exit(*args):
    STOP.set()

async def main():
    client = MQTTClient("client-id")

    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect
    client.on_subscribe = on_subscribe

    await client.connect("127.0.0.1")  # Local MQTT Broker

    client.publish('TEST/TIME', str(time.time()), qos=1)

    await STOP.wait()
    await client.disconnect()

if __name__ == '__main__':
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    loop.add_signal_handler(signal.SIGINT, ask_exit)
    loop.add_signal_handler(signal.SIGTERM, ask_exit)

    try:
        loop.run_until_complete(main())
    finally:
        loop.close()
