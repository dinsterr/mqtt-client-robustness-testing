import socket
import sys
import threading

import logger_factory

logger = logger_factory.construct_logger("proxy")
stop = False


def start_listening(local_host: str, local_port: int, remote_host: str, remote_port: int, receive_first: bool):
    _server_loop(local_host, local_port, remote_host, remote_port, receive_first)


def _server_loop(local_host, local_port, remote_host, remote_port, receive_first):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        server_socket.bind((local_host, local_port))
    except OSError:
        logger.exception(f"Failed to create listening socket on {local_host}:{local_port}.")
        sys.exit(0)

    logger.debug(f"Listening on {local_host}:{local_port}")

    # TODO: possibility to stop processing
    # TODO: auto close sockets after a while
    server_socket.listen(5)
    global stop
    while not stop:
        client_socket, addr = server_socket.accept()

        logger.debug(f"Receiving connection from {addr[0]}:{addr[1]}")

        # Start a new thread for any incoming connections
        proxy_thread = threading.Thread(target=_proxy_handler,
                                        args=(client_socket, remote_host, remote_port, receive_first))
        proxy_thread.start()


def _proxy_handler(client_socket, remote_host, remote_port, receive_first):
    # Define the remote socket used for forwarding requests
    remote_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Establish a connection to the remote host
    try:
        remote_socket.connect((remote_host, remote_port))
    except OSError:
        logger.exception(f"Could not create connection to remote at {remote_host}:{remote_port}.")
        exit()

    logger.debug(f"Established connection to remote at {remote_host}:{remote_port}.")

    # intercept the response before it's received
    if receive_first:
        # receive data from the connection and return a buffer
        remote_buffer = _receive_from(remote_socket)

        # Handle the response (an opportunity for read/write of the response data)
        remote_buffer = _response_handler(remote_buffer)

        # If data exists send the response to the local client
        if len(remote_buffer):
            logger.debug(f"Receiving {len(remote_buffer)} bytes from remote.")
            client_socket.send(remote_buffer)

            # Continually read from local, print the output and forward to the remotehost
    while True:
        # Receive data from the client and send it to the remote
        local_buffer = _receive_from(client_socket)
        _send_data(local_buffer, "localhost", remote_socket)

        # Receive the response and sent it to the client
        remote_buffer = _receive_from(remote_socket)
        _send_data(remote_buffer, "remotehost", client_socket)

        # Close connections, print and break out when no more data is available
        if not len(local_buffer):
            client_socket.close()
            remote_socket.close()
            logger.debug("Connections closed.")

            break


def _send_data(buffer, type, socket):
    if len(buffer):
        logger.debug(f"Received {len(buffer)} bytes from {type}.")

        if "localhost" in type:
            mod_buffer = _request_handler(buffer)
        else:
            mod_buffer = _response_handler(buffer)

        socket.send(mod_buffer)

        logger.debug(f"Sent buffer to {type}")


def _receive_from(connection):
    buffer = b""

    # use a 2 second timeout
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


def _response_handler(buffer):
    logger.debug("response_handler: {0}".format(buffer))
    return buffer


def _request_handler(buffer):
    logger.debug("request handler: {0}".format(buffer))
    return buffer


def hexdump(src, length=16):
    result = []
    #digits = 4 if isinstance(src, unicode) else 2
    digits = 2

    for i in range(0, len(src), length):
        s = src[i:i + length]
        hexa = b' '.join(["%0*X" % (digits, ord(str(x))) for x in s])
        text = b''.join([x if 0x20 <= ord(x) < 0x7F else b'.' for x in s])
        result.append(b"%04X   %-*s   %s" % (i, length * (digits + 1), hexa, text))
    logger.warning(b'\n'.join(result))
