# The core of the TCP receive / send loop is adapted from:
# J. Seitz and T. Arnold,
# “Chapter 2. The Network: Basics,” in Black Hat Python: Python programming for hackers and Pentesters,
# San Francisco: No Starch Press, 2021.
import logging
import socket
import threading
from enum import Enum

import logger_factory
from config import Config

READ_TIMEOUT_PER_BUFFER = 0.1


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
            self.isStop = True

        if Config.MAX_LOCAL_TCP_TIMEOUT_SECS > -1 and \
                self._iterations_without_new_local_data >= Config.MAX_LOCAL_TCP_TIMEOUT_SECS / READ_TIMEOUT_PER_BUFFER:
            self.isStop = True


class TcpProxy(threading.Thread):
    _internal_server_socket = None
    _local_socket = None
    _remote_socket = None

    LOGGER = logging.getLogger("monitor")
    TCP_FROM_LOCAL_LOGGER = logging.getLogger("monitor")
    TCP_FROM_REMOTE_LOGGER = logging.getLogger("monitor")

    def __init__(self, local_host: str,
                 local_port: int,
                 remote_host: str,
                 remote_port: int):
        super(TcpProxy, self).__init__(daemon=True)
        self._isStop = False

        self._reset_event = threading.Event()
        self._local_host = local_host
        self._local_port = local_port
        self._remote_host = remote_host
        self._remote_port = remote_port

    def __del__(self):
        self.stop()

    def run(self):
        self._server_loop(self._local_host, self._local_port)

    def stop(self):
        self._isStop = True
        self.LOGGER.debug(f"Closing all sockets")

        # Close potentially remaining sockets
        if self._remote_socket is not None:
            self._remote_socket.close()

        if self._local_socket is not None:
            self._local_socket.close()

        if self._internal_server_socket is not None:
            self._internal_server_socket.close()

    def reset(self):
        self._reset_event.set()

    def _server_loop(self, local_host: str, local_port: int):
        while not self._isStop:
            # Set up the internal socket to which the system under test connects
            if self._internal_server_socket:
                self._internal_server_socket.close()
                self._reset_event.clear()

            self._internal_server_socket = socket.create_server((local_host, local_port))
            self.LOGGER.info(f"Waiting for connection on {local_host}:{local_port}")
            self._local_socket, addr = self._internal_server_socket.accept()
            self.LOGGER.info(f"Received connection from {addr[0]}:{addr[1]}")

            # If there is already an existing remote socket we keep the connection open
            if not self._remote_socket:
                # Define the remote socket used for forwarding requests
                self._remote_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

                # Establish a connection to the remote host
                try:
                    self._remote_socket.connect((self._remote_host, self._remote_port))
                except:
                    self.LOGGER.exception(f"Could not create connection to remote at {self._remote_host}:{self._remote_port}")
                    return

                self.LOGGER.info(f"Established connection to remote at {self._remote_host}:{self._remote_port}")

            self.LOGGER.info("Monitoring TCP connection...")
            self._proxy_handler(self._local_socket)

    def _proxy_handler(self, local_socket):
        buffer_status = TcpBufferStatus()
        # Continually read from local and remote and forward to the other socket
        while not buffer_status.isStop and not self._reset_event.is_set():
            local_buffer = self._receive_from_socket(local_socket)
            self._send_data(local_buffer, SocketType.LOCAL, self._remote_socket)

            # Receive the response and send it to the client
            remote_buffer = self._receive_from_socket(self._remote_socket)
            self._send_data(remote_buffer, SocketType.REMOTE, local_socket)

            buffer_status.record(local_buffer, remote_buffer)

        if buffer_status.isStop:
            self.LOGGER.debug("Stopping proxy due to timeout of TCP data.")

    def _receive_from_socket(self, connection):
        buffer = b""

        try:
            # Wait for a maximum of X seconds to receive new data on the buffer
            connection.settimeout(READ_TIMEOUT_PER_BUFFER)

            while not self._reset_event.is_set:
                # Blocking read data in blocks of X bytes
                data = connection.recv(4096)

                if not data:
                    break

                buffer += data
        except socket.timeout:
            pass
        except OSError:
            pass

        return buffer

    def _send_data(self, buffer, socket_type, target_socket: socket):
        if len(buffer):
            modified_buffer = None
            if socket_type is SocketType.LOCAL:
                modified_buffer = self.default_request_interceptor(buffer, socket_type)
            elif socket_type is SocketType.REMOTE:
                modified_buffer = self.default_response_interceptor(buffer, socket_type)

            try:
                target_socket.sendall(modified_buffer)
            except Exception as e:
                self.LOGGER.debug(f"Could not send data to target socket: {e.__class__}")
                exit()

    def default_request_interceptor(self, buffer, socket_type):
        self.TCP_FROM_LOCAL_LOGGER.debug(f"{buffer}")
        return buffer

    def default_response_interceptor(self, buffer, socket_type):
        self.TCP_FROM_REMOTE_LOGGER.debug(f"{buffer}")
        return buffer


class SocketType(Enum):
    LOCAL = "local",
    REMOTE = "remote"
