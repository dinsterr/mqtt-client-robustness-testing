import socket

import util.logger as logger
from broker.listener.auto_publish_client_thread import AutoPublishClientThread
from broker.listener.client_thread import ClientThread
from util.config_reader import ListenerConfig

ALLOWED_CONNECTIONS = 10


class Listener(object):
    """
    MQTT Listener.
    """

    def __init__(self, config: ListenerConfig, subscription_manager, client_manager, ip, debug=0):
        """
        Constructor for the MQTT Listener
        :param config: contains the initialized config setting
        :param ip: ip of the listener
        :param debug: debug mode on/off
        """
        self._ip = ip
        self._port = config.port
        self._is_auto_publish = config.is_auto_publish
        self._auto_publish_interval = config.auto_publish_interval
        self._message_generator_config = config.message_generator_config
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
        return f"MQTT Listener: [Port: {self._port}]"

    def listen(self):
        """
        Listens for incoming socket connections to the broker port and creates a @ClientThread for each unique
        connection, that then takes over the task of listening for messages on the established socket.
        """
        logger.logging.info(f"{self.__str__()} running ...")
        while self._running:
            try:
                client_socket, client_address = self.sock.accept()
                if client_socket and client_address:
                    client_thread = ClientThread(client_socket, client_address, self, self._subscription_manager,
                                                 self._client_manager, self.debug)
                    self.open_sockets[str(client_address) + '_LT'] = client_thread
                    client_thread.start()

                    if self._is_auto_publish:
                        client_thread = AutoPublishClientThread(client_socket, client_address, self,
                                                                self._subscription_manager, self._client_manager,
                                                                self._auto_publish_interval,
                                                                self._message_generator_config, self.debug)
                        self.open_sockets[str(client_address) + '_APT'] = client_thread
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
                if self.open_sockets[index]:
                    self.open_sockets[index].close()
            logger.logging.info("--- All open client connections were successfully closed.")

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
        self.open_sockets.pop(str(client_thread.client_address) + '_LT')
        self.open_sockets.pop(str(client_thread.client_address) + '_APT')
        logger.logging.info(f"- Successfully closed threads, that managed '{client_thread.client_id}'")
