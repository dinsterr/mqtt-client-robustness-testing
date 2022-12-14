import socket
import threading

import logger_factory

logger = logger_factory.construct_logger("proxy")


class TcpProxy:
    _local_host: str
    _local_port: int
    _remote_host: str
    _remote_port: int

    _stop = False
    _thread = None

    def __init__(self, local_host: str,
                 local_port: int,
                 remote_host: str,
                 remote_port: int):
        self._local_host = local_host
        self._local_port = local_port
        self._remote_host = remote_host
        self._remote_port = remote_port

    def run(self):
        self._server_loop(self._local_host, self._local_port, self._remote_host, self._remote_port)

    def _server_loop(self, local_host, local_port, remote_host, remote_port):
        server_socket = socket.create_server((local_host, local_port))
        logger.debug(f"Listening on {local_host}:{local_port}")

        client_socket, addr = server_socket.accept()
        logger.debug(f"Receiving connection from {addr[0]}:{addr[1]}")

        # Start a new thread for any incoming connections
        proxy_thread = threading.Thread(target=self._proxy_handler,
                                        args=(client_socket, remote_host, remote_port), daemon=True)
        proxy_thread.start()

    def _proxy_handler(self, client_socket, remote_host, remote_port):
        # Define the remote socket used for forwarding requests
        remote_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Establish a connection to the remote host
        try:
            remote_socket.connect((remote_host, remote_port))
        except OSError:
            logger.exception(f"Could not create connection to remote at {remote_host}:{remote_port}.")
            exit()

        logger.debug(f"Established connection to remote at {remote_host}:{remote_port}.")

        # Continually read from local, print the output and forward to the remotehost
        while True:
            # Receive data from the client and send it to the remote
            local_buffer = TcpProxy._receive_from_socket(client_socket)
            TcpProxy._send_data(local_buffer, "localhost", remote_socket)

            # Receive the response and send it to the client
            remote_buffer = TcpProxy._receive_from_socket(remote_socket)
            TcpProxy._send_data(remote_buffer, "remotehost", client_socket)

            # Close connections, print and break out when no more data is available
            if not len(local_buffer):
                client_socket.close()
                remote_socket.close()
                logger.debug("Connections closed.")

                break

    @classmethod
    def _send_data(cls, buffer, type, socket):
        if len(buffer):
            cls._logger.debug(f"Received {len(buffer)} bytes from {type}.")

            if "localhost" in type:
                mod_buffer = TcpProxy.default_request_handler(buffer)
            else:
                mod_buffer = TcpProxy.default_response_handler(buffer)

            socket.send(mod_buffer)

            cls._logger.debug(f"Sent buffer to {type}")

    @classmethod
    def _receive_from_socket(cls, connection):
        buffer = b""

        # use a two second timeout
        connection.settimeout(2)

        try:
            while True:
                data = connection.recv(4096)

                if not data:
                    break

                buffer += data
        except socket.timeout:
            pass

        return buffer

    @classmethod
    def default_response_handler(cls, buffer):
        cls._logger.debug("response_handler: {0}".format(buffer))
        return buffer

    @classmethod
    def default_request_handler(cls, buffer):
        cls._logger.debug("request handler: {0}".format(buffer))
        return buffer
