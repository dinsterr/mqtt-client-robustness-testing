import argparse
import asyncio
import logging
import random
import signal
import warnings

import uvloop
from gmqtt import Client as MQTTClient

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
STOP = asyncio.Event()
DEFAULT_HOSTNAME = "localhost"
DEFAULT_PORT = 1883
AUTO_PUBLISH_SLEEP_INTERVAL = 3


def on_connect(client, flags, rc, properties):
    """
    Executed if the client successfully connects to the specified broker
    :param client: client information
    :param flags: flags set in the CONNACK packet
    :param rc: reconnection flag
    :param properties: specified user properties
    """
    logging.info("[CONNECTION ESTABLISHED]")


def on_disconnect(client, packet, exc=None):
    """
    Handle disconnection of client
    :param client: Client that disconnected
    :param packet: Disconnect packet
    :param exc: NOT USED
    """
    logging.info(f'[DISCONNECTED]')


def ask_exit(*args):
    STOP.set()


def main(args):
    """
    Main function of the program. Initiates the publishing process of the Client.
    :param args: arguments provided via CLI
    """

    logging.info(f"Connecting you to {args.host} on Port {args.port}. Your clientID: '{args.client_id}'.")

    loop = asyncio.get_event_loop()
    loop.add_signal_handler(signal.SIGINT, ask_exit)
    loop.add_signal_handler(signal.SIGTERM, ask_exit)
    task = loop.create_task(publish_loop(args.client_id, args.host, args.port, args.topic, args.message))

    try:
        loop.run_until_complete(task)
    except (ConnectionRefusedError, KeyboardInterrupt, RuntimeError):
        logging.info("Closing the client.")


async def publish_loop(client_id, host, port, topic, message):
    client = MQTTClient(client_id)
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    await client.connect(host=host, port=port)

    try:
        while not STOP.is_set():
            logging.info("[PUBLISHING]")
            if client.is_connected:
                client.publish(topic, message, qos=0)

            await asyncio.sleep(AUTO_PUBLISH_SLEEP_INTERVAL)
    finally:
        await client.disconnect()


if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
    warnings.filterwarnings('ignore', category=DeprecationWarning)

    CLIENT_ID = str(random.randint(0, 50000))

    # argument parser
    parser = argparse.ArgumentParser("client_pub", description="MQTT Publish client supporting Multilateral Security",
                                     epilog="Developed by Babbadeckl. Questions and Bug-reports can be mailed to "
                                            "korbinian.spielvogel@uni-passau.de")
    # argument for client name
    parser.add_argument('-i', '--id', default=CLIENT_ID, type=str, dest="client_id", metavar="CLIENT_ID",
                        help=f"Client identifier. Defaults to random int.")

    # argument for host
    parser.add_argument('-H', '--host', default=DEFAULT_HOSTNAME, type=str, dest="host", metavar="HOST",
                        help=f"MQTT host to connect to. Defaults to {DEFAULT_HOSTNAME}.")

    # argument for port
    parser.add_argument('-p', '--port', default=DEFAULT_PORT, type=int, dest="port", metavar="PORT",
                        help=f"Network port to connect to. Defaults to {DEFAULT_PORT}.")

    # argument for topic
    parser.add_argument('-t', '--topic', type=str, dest="topic", metavar="TOPIC", help="MQTT topic to publish to.")

    # argument for message
    parser.add_argument('-m', '--message', type=str, dest="message", metavar="MESSAGE", help="Message payload to send.")

    args = parser.parse_args()
    main(args)
