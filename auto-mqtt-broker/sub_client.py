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


def on_connect(client, flags, rc, properties):
    """
    Executed if the client successfully connects to the specified broker
    :param client: client information
    :param flags: flags set in the CONNACK packet
    :param rc: reconnection flag
    :param properties: specified user properties
    """
    logging.info(f"Subscribing to '{args.topic}.'")
    client.subscribe(args.topic, qos=0, subscription_identifier=1)

    logging.info("[CONNECTION ESTABLISHED]")


def on_message(client, topic, payload, qos, properties):
    """
    Handle incoming messages.
    :param client: NOT USED
    :param topic: topic of the received message
    :param payload: payload of the received message
    :param qos: QOS of the received message
    :param properties: properties of the received message
    """

    logging.info(f'[RECV MSG] {topic}:{payload.decode("utf-8", errors="ignore")}')


def on_disconnect(client, packet, exc=None):
    """
    Handle disconnection of client
    :param client: Client that disconnected
    :param packet: Disconnect packet
    :param exc: NOT USED
    """
    logging.info(f'[DISCONNECTED]')


def on_subscribe(client, mid, qos, properties):
    """
    Handle successful subscription
    :param client: Client that successfully subscribed
    :param mid: NOT USED
    :param qos: QOS of the subscription
    :param properties: Properties of the subscription
    """
    logging.info(f'[SUBSCRIBED]')


def assign_callbacks_to_client(client):
    """
    Assign callback functions to a client
    :param client: The client which should handle the callbacks
    """
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect
    client.on_subscribe = on_subscribe


def ask_exit(*args):
    STOP.set()


async def main(args):
    """
    Main function of the program. Initiates the publishing process of the Client.
    :param args: arguments provided via CLI
    """

    logging.info(f"Connecting you to {args.host} on Port {args.port}. Your clientID: '{args.client_id}'.")

    client = MQTTClient(args.client_id)
    assign_callbacks_to_client(client)
    await client.connect(host=args.host, port=args.port)

    await STOP.wait()
    try:
        await client.disconnect(session_expiry_interval=0)
    except ConnectionResetError:
        logging.info("Broker successfully closed the connection.")


if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
    warnings.filterwarnings('ignore', category=DeprecationWarning)

    HOSTNAME = "localhost"
    PORT = 1883
    CLIENT_ID = str(random.randint(0, 50000))
    TOPIC = "foo"

    # argument parser
    parser = argparse.ArgumentParser("client_pub", description="MQTT Subscribe client supporting Multilateral Security",
                                     epilog="Developed by Babbadeckl. Questions and Bug-reports can be mailed to "
                                            "korbinian.spielvogel@uni-passau.de")
    # argument for client name
    parser.add_argument('-i', '--id', default=CLIENT_ID, type=str, dest="client_id", metavar="CLIENT_ID",
                        help=f"Client identifier. Defaults to random int.")

    # argument for host
    parser.add_argument('-H', '--host', default=HOSTNAME, type=str, dest="host", metavar="HOST",
                        help=f"MQTT host to connect to. Defaults to {HOSTNAME}.")

    # argument for port
    parser.add_argument('-p', '--port', default=PORT, type=int, dest="port", metavar="PORT",
                        help=f"Network port to connect to. Defaults to {PORT}.")

    # argument for topic
    parser.add_argument('-t', '--topic', default=TOPIC, type=str, dest="topic", metavar="TOPIC",
                        help="MQTT topic to subscribe to.")

    args = parser.parse_args()

    try:
        loop = asyncio.get_event_loop()
        loop.add_signal_handler(signal.SIGINT, ask_exit)
        loop.add_signal_handler(signal.SIGTERM, ask_exit)
        loop.run_until_complete(main(args))
    except (KeyboardInterrupt, RuntimeError):
        logging.info("Closing the client.")
