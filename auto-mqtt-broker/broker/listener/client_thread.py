import threading

from packets import enums
from packets.mqtt_packet_manager import MQTTPacketManager
from util import logger as logger
from util.exceptions import IncorrectProtocolOrderException, MQTTMessageNotSupportedException


class ClientThread(threading.Thread):
    """
    Handles the TCP sockets with the clients
    """

    def __init__(self, client_socket, client_address, listener, subscription_manager, client_manager, debug):
        super().__init__(daemon=True)
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
        Handle the MQTT SUBSCRIBE message: check if the client has a valid status (CONN_RECV or SUB_RECV), then update
        the client status to SUB_RECV. Add the client to the subscriber list and send a PUBACK message back to the
        client.
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
                    self._process_msg(msg)
        except OSError:
            pass
        except MQTTMessageNotSupportedException as e:
            logger.logging.error(e)
        except (IncorrectProtocolOrderException, TypeError) as e:
            logger.logging.error(e)
            self.close()

    def _process_msg(self, msg):
        if logger.DEBUG:
            logger.logging.debug(f"Received raw message on Port {self.listener.port}: {msg}")
        parsed_msg = MQTTPacketManager.parse_packet(msg, self.client_socket, self.client_address,
                                                    self._client_manager)
        if parsed_msg['identifier'] == enums.PacketIdentifer.CONNECT:
            self._log_received_packet(msg, parsed_msg, parsed_msg['client_id'])
            self.handle_connect(parsed_msg)
        elif parsed_msg['identifier'] == enums.PacketIdentifer.PUBLISH:
            self._log_received_packet(msg, parsed_msg, self.client_id)
            self.handle_publish(parsed_msg)
        elif parsed_msg['identifier'] == enums.PacketIdentifer.SUBSCRIBE:
            self._log_received_packet(msg, parsed_msg, self.client_id)
            self.handle_subscribe(parsed_msg)
        elif parsed_msg['identifier'] == enums.PacketIdentifer.PINGREQ:
            self._log_received_packet(msg, parsed_msg, self.client_id)
            self.handle_pingreq(parsed_msg)
        elif parsed_msg['identifier'] == enums.PacketIdentifer.DISCONNECT:
            self._log_received_packet(msg, parsed_msg, self.client_id)
            self.handle_disconnect(parsed_msg)
        else:
            raise MQTTMessageNotSupportedException(
                f'Client {self.client_address} sent a message with identifier: '
                f'`{parsed_msg["identifier"]}`. Not supported, therefore ignored!')

    def _log_received_packet(self, msg, parsed_msg, client_id):
        logger.logging.info(
            f"Received {parsed_msg['identifier'].name} message from Client {client_id}"
            f" on Port {self.listener.port}: {msg}")

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
        return self._stop_event.is_set()
