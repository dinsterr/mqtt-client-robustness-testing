# The core of the TCP receive / send loop is adapted from:
# J. Seitz and T. Arnold,
# “Chapter 2. The Network: Basics,” in Black Hat Python: Python programming for hackers and Pentesters,
# San Francisco: No Starch Press, 2021.

import socket
from enum import Enum

import logger_factory
from config import Config

READ_TIMEOUT_PER_BUFFER = 0.1

LOGGER = logger_factory.get_logger("monitor")
TCP_FROM_LOCAL_LOGGER = logger_factory.construct_logger("TCP_FROM_LOCAL")
TCP_FROM_REMOTE_LOGGER = logger_factory.construct_logger("TCP_FROM_REMOTE")


class TcpBufferStatus:
    _iterations_without_new_remote_data = 0
    _iterations_without_new_local_data = 0
    isStop = False

    def record(self, local_buffer, remote_buffer):
        if len(remote_buffer) == 0:
            self._iterations_without_new_remote_data += 1
        else:
            _iterations_without_new_remote_data = 0

        if len(local_buffer) == 0:
            self._iterations_without_new_local_data += 1
        else:
            _iterations_without_new_local_data = 0

        if Config.MAX_REMOTE_TCP_TIMEOUT_SECS > -1 and \
                self._iterations_without_new_remote_data >= Config.MAX_REMOTE_TCP_TIMEOUT_SECS / READ_TIMEOUT_PER_BUFFER:
            LOGGER.debug("Stopping proxy due to timeout of remote data.")
            self.isStop = True

        if Config.MAX_LOCAL_TCP_TIMEOUT_SECS > -1 and \
                self._iterations_without_new_local_data >= Config.MAX_LOCAL_TCP_TIMEOUT_SECS / READ_TIMEOUT_PER_BUFFER:
            LOGGER.debug("Stopping proxy due to timeout of local data.")
            self.isStop = True


class TcpProxy:
    _local_host: str
    _local_port: int
    _remote_host: str
    _remote_port: int

    _internal_server_socket = None
    _local_socket = None
    _remote_socket = None

    def __init__(self, local_host: str,
                 local_port: int,
                 remote_host: str,
                 remote_port: int):
        self._local_host = local_host
        self._local_port = local_port
        self._remote_host = remote_host
        self._remote_port = remote_port
        self.start()

    def __del__(self):
        LOGGER.debug(f"Closing all sockets")

        # Close potentially remaining sockets
        if self._remote_socket is not None:
            self._remote_socket.close()

        if self._local_socket is not None:
            self._local_socket.close()

        if self._internal_server_socket is not None:
            self._internal_server_socket.close()

    def start(self):
        self._server_loop(self._local_host, self._local_port)

    def _server_loop(self, local_host: str, local_port: int):
        # Set up the internal socket to which the system under test connects
        self._internal_server_socket = socket.create_server((local_host, local_port))
        LOGGER.info(f"Waiting for connection on {local_host}:{local_port}")
        self._local_socket, addr = self._internal_server_socket.accept()
        LOGGER.info(f"Received connection from {addr[0]}:{addr[1]}")

        if not self._remote_socket:
            # Define the remote socket used for forwarding requests
            self._remote_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            # Establish a connection to the remote host
            try:
                self._remote_socket.connect((self._remote_host, self._remote_port))
            except:
                LOGGER.exception(f"Could not create connection to remote at {self._remote_host}:{self._remote_port}")
                return

            LOGGER.info(f"Established connection to remote at {self._remote_host}:{self._remote_port}")

        LOGGER.info("Monitoring TCP connection...")
        self._proxy_handler(self._local_socket)

    def _proxy_handler(self, local_socket):
        status = TcpBufferStatus()
        # Continually read from local and remote and forward to the other socket
        while not status.isStop:
            local_buffer = TcpProxy._receive_from_socket(local_socket)
            TcpProxy._send_data(local_buffer, SocketType.LOCAL, self._remote_socket)

            # Receive the response and send it to the client
            remote_buffer = TcpProxy._receive_from_socket(self._remote_socket)
            TcpProxy._send_data(remote_buffer, SocketType.REMOTE, local_socket)

            status.record(local_buffer, remote_buffer)

    @classmethod
    def _send_data(cls, buffer, socket_type, target_socket: socket):
        if len(buffer):
            match socket_type:
                case SocketType.LOCAL:
                    modified_buffer = TcpProxy.default_request_interceptor(buffer, socket_type)
                case SocketType.REMOTE:
                    modified_buffer = TcpProxy.default_response_interceptor(buffer, socket_type)
                case _:
                    # Should never be reached
                    raise ValueError(f"Invalid socket type {type}")

            try:
                target_socket.sendall(modified_buffer)
            except Exception as e:
                LOGGER.debug(f"Could not send data to target socket: {e.__class__}")
                exit()

    @classmethod
    def _receive_from_socket(cls, connection):
        buffer = b""

        # Wait for a maximum of X seconds to receive new data on the buffer
        connection.settimeout(READ_TIMEOUT_PER_BUFFER)
        try:
            while True:
                # Blocking read data in blocks of X bytes
                data = connection.recv(4096)

                if not data:
                    break

                buffer += data
        except socket.timeout:
            pass
        except ConnectionResetError:
            pass

        return buffer

    @classmethod
    def default_request_interceptor(cls, buffer, socket_type):
        TCP_FROM_LOCAL_LOGGER.debug(f"{buffer}")
        return buffer

    @classmethod
    def default_response_interceptor(cls, buffer, socket_type):
        TCP_FROM_REMOTE_LOGGER.debug(f"{buffer}")
        return buffer


class SocketType(Enum):
    LOCAL = "local",
    REMOTE = "remote"
