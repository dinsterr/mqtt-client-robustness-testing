import socket
import threading

import util.logger as logger
from client_manager import *
from util.exceptions import MQTTMessageNotSupportedException, IncorrectProtocolOrderException
from packets.mqtt_packet_manager import MQTTPacketManager

ALLOWED_CONNECTIONS = 10


class ClientThread(threading.Thread):
    """
    Handles the TCP sockets with the clients
    """

    def __init__(self, client_socket, client_address, listener, subscription_manager, client_manager, debug):
        super().__init__()
        self.client_socket = client_socket
        self.client_address = client_address
        self._running = True
        self._stop_event = threading.Event()
        self.listener = listener
        self._subscription_manager = subscription_manager
        self._client_manager = client_manager
        self.debug = debug
        self.client_id = ''

    @property
    def running(self):
        return self._running

    @running.setter
    def running(self, value):
        self._running = value

    def run(self):
        """
        Start method of the thread
        """
        self.listen()

    def handle_connect(self, parsed_msg):
        """
        Handle the MQTT CONNECT message: update the status of the client to CONN_RECV, store the sent user properties
        in the ClientManager and set the ClientID. Afterwards send a CONNACK msg back to the client.
        :param parsed_msg: a parsed version of the received message
        """
        try:
            self._client_manager.add_status(self.client_socket, self.client_address, enums.Status.CONN_RECV)
            self._client_manager.add_user_property(self.client_socket, self.client_address, parsed_msg['properties'])
            self._client_manager.add_user_property(self.client_socket, self.client_address,
                                                   {enums.Properties.Version: parsed_msg['version']})
            self.client_id = parsed_msg['client_id']
        except (IncorrectProtocolOrderException, TypeError) as e:
            logger.logging.error(e)
            self.close()
        connack_msg = MQTTPacketManager.prepare_connack(parsed_msg)
        self.client_socket.send(connack_msg)
        logger.logging.info(f"Sent CONNACK to client {parsed_msg['client_id']}.")

    def handle_publish(self, parsed_msg):
        """
        Handle the MQTT PUBLISH message: check if the client has a valid status (CONN_RECV or PUB_RECV), then update the
        client status to PUB_RECV.
        :param parsed_msg: a parsed version of the received message
        """
        if self._client_manager.get_client_status(self.client_socket, self.client_address) in [enums.Status.CONN_RECV,
                                                                                               enums.Status.PUB_RECV]:
            self._client_manager.add_status(self.client_socket, self.client_address, enums.Status.PUB_RECV)
            topic = parsed_msg['topic']
            for sub in self._subscription_manager.get_topic_subscribers(topic):
                logger.logging.info(
                    f"Sent publish message '{parsed_msg['payload']}' in '{topic}' to Client {sub['client_id']}")
                sub['client_socket'].send(parsed_msg['raw_packet'])
        else:
            raise IncorrectProtocolOrderException(
                f"Received PUBLISH message from client {self.client_address} before CONNECT. Abort!")

    def handle_subscribe(self, parsed_msg):
        """
        Handle the MQTT SUBSCRIBE message: check if the client has a valid status (CONN_RECV or SUB_RECV), then update the
        client status to SUB_RECV. Add the client to the subscriber list and send a PUBACK message back to the client.
        :param parsed_msg: a parsed version of the received message
        """
        if self._client_manager.get_client_status(self.client_socket, self.client_address) in [enums.Status.CONN_RECV,
                                                                                               enums.Status.SUB_RECV]:
            self._client_manager.add_status(self.client_socket, self.client_address, enums.Status.SUB_RECV)
            topic = parsed_msg['topic']
            self._subscription_manager.add_subscriber(self.client_socket, self.client_address, topic, self.client_id)
            logger.logging.info(
                f"- Client {self.client_id} subscribed successfully to topic: '{topic}' on port {self.listener.port}")

            suback_msg = MQTTPacketManager.prepare_suback(parsed_msg)
            self.client_socket.send(suback_msg)
            logger.logging.info(f"Sent SUBACK to client {self.client_id}")
        else:
            raise IncorrectProtocolOrderException(
                f"Received SUBSCRIBE message from client {self.client_id} before CONNECT. Abort!")

    def handle_pingreq(self, parsed_msg):
        """
        Handle the MQTT PINGREQ message: Send a PINGRESP back to the client.
        :param parsed_msg: a parsed version of the received message (FOR FUTURE USE)
        :return:
        """
        pingresp_msg = MQTTPacketManager.prepare_pingresp()
        self.client_socket.send(pingresp_msg)
        logger.logging.info(f"Sent PINGRESP to client {self.client_address}.")

    def handle_disconnect(self, parsed_msg):
        """
        Handle the MQTT DISCONNECT message: update the status of the client to DISCONNECTED and remove the client
        , if necessary, from the all subscription lists. Finally close the responsible client thread.
        :param parsed_msg: a parsed version of the received message (FOR FUTURE USE)
        """
        self._client_manager.add_status(self.client_socket, self.client_address, enums.Status.DISCONNECTED)
        self._subscription_manager.remove_subscriber(self.client_socket, self.client_address, self.client_id)
        self.close()

    def listen(self):
        """
        Listen on the client socket for incoming messages and handle the different MQTT messages
        """
        try:
            self._client_manager.add_status(self.client_socket, self.client_address, enums.Status.FRESH)
            while self._running:
                msg = self.client_socket.recv(1024)
                if len(msg) > 0:
                    if logger.DEBUG:
                        logger.logging.debug(f"Received raw message on Port {self.listener.port}: {msg}")
                    parsed_msg = MQTTPacketManager.parse_packet(msg, self.client_socket, self.client_address,
                                                                self._client_manager)
                    if parsed_msg['identifier'] == enums.PacketIdentifer.CONNECT:
                        logger.logging.info(
                            f"Received CONNECT message from Client {parsed_msg['client_id']} on Port {self.listener.port}: {msg}")
                        self.handle_connect(parsed_msg)
                    elif parsed_msg['identifier'] == enums.PacketIdentifer.PUBLISH:
                        logger.logging.info(
                            f"Received PUBLISH message from Client {self.client_id} on Port {self.listener.port}: {msg}")
                        self.handle_publish(parsed_msg)
                    elif parsed_msg['identifier'] == enums.PacketIdentifer.SUBSCRIBE:
                        logger.logging.info(
                            f"Received SUBSCRIBE message from Client {self.client_id} on Port {self.listener.port}: {msg}")
                        self.handle_subscribe(parsed_msg)
                    elif parsed_msg['identifier'] == enums.PacketIdentifer.PINGREQ:
                        logger.logging.info(
                            f"Received PINGREQ message from Client {self.client_id} on Port {self.listener.port}: {msg}")
                        self.handle_pingreq(parsed_msg)
                    elif parsed_msg['identifier'] == enums.PacketIdentifer.DISCONNECT:
                        logger.logging.info(
                            f"Received DISCONNECT message from Client {self.client_id} on Port {self.listener.port}: {msg}")
                        self.handle_disconnect(parsed_msg)
                    else:
                        raise MQTTMessageNotSupportedException(
                            f'Client {self.client_address} sent a message with identifier: `{parsed_msg["identifier"]}`. Not supported, therefore ignored!')
        except OSError:
            pass
        except MQTTMessageNotSupportedException as e:
            logger.logging.error(e)
        except (IncorrectProtocolOrderException, TypeError) as e:
            logger.logging.error(e)
            self.close()

    def close(self):
        """
        Close the client thread
        """
        logger.logging.info(f"- Client {self.client_id} disconnected!")
        self.client_socket.close()
        self._stop_event.set()
        self.listener.remove_client_thread(self)

    def stopped(self):
        """
        Check if the client thread is closed.
        """
        return self._stop_event.isSet()


class Listener(object):
    """
    MQTT Listener. No security mechanisms in place.
    """

    def __init__(self, config, subscription_manager, client_manager, ip, debug=0):
        """
        Constructor for the MQTT Listener
        :param config: contains the initialized config setting
        :param ip: ip of the listener
        :param debug: debug mode on/off
        """
        self._ip = ip
        self._port = config.port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self._ip, self._port))
        self.sock.listen(ALLOWED_CONNECTIONS)
        self._running = True
        self.open_sockets = {}
        self.debug = debug
        self._subscription_manager = subscription_manager
        self._client_manager = client_manager

    def __str__(self):
        return f"MQTT Listener: [Port: {self._port}"

    def listen(self):
        """
        Listens for incoming socket connections to the broker port and creates a @ClientThread for each unique connection
        , that then takes over the task of listening for messages on the established socket.
        """
        logger.logging.info(f"{self.__str__()} running ...")
        while self._running:
            try:
                client_socket, client_address = self.sock.accept()
                if client_socket and client_address:
                    client_thread = ClientThread(client_socket, client_address, self, self._subscription_manager,
                                                 self._client_manager, self.debug)
                    self.open_sockets[client_address] = client_thread
                    client_thread.setDaemon(True)
                    client_thread.start()
            except ConnectionAbortedError:
                logger.logging.info("Closed socket connection of Listener.")

    def close_sockets(self):
        """
        Iterates over all open sockets and "closes" them, so that no open sockets and threads remain.
        ONLY USED FOR DEBUGGING PURPOSE AS DAEMON CHARACTERISTIC OF THREAD TAKES CARE OF THIS.
        """
        if len(self.open_sockets) != 0:
            logger.logging.info("--- Closing open client connections")
            for index, client_thread in enumerate(self.open_sockets):
                logger.logging.info(f"\t --- Connection {index + 1}/{len(self.open_sockets)} closed")
            logger.logging.info("--- All open client connections were successfully closed.")
        self.sock.close()

    @property
    def running(self):
        return self._running

    @running.setter
    def running(self, value):
        self._running = value

    @property
    def port(self):
        return self._port

    @port.setter
    def port(self, value):
        self._port = value

    def remove_client_thread(self, client_thread):
        self.open_sockets.pop(client_thread.client_address)
        logger.logging.info(f"- Successfully closed ClientThread, that managed '{client_thread.client_id}'")
