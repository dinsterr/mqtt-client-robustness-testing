import socket
import sys
import threading
import logging

stop = False


def server_loop(local_host, local_port, remote_host, remote_port, receive_first):
    # Define a server socket to listen on
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        # Bind the socket to the defined local address and port
        server_socket.bind((local_host, local_port))
    except:
        logging.warning("[!!] Failed to connect to {0}:{1}".format(local_host, local_port))
        logging.warning("[!!] Check for other listening sockets or correct")
        sys.exit(0)

    logging.warning("Successfully listening on {0}:{1}".format(local_host, local_port))

    # Listen for a maximum of 5 connections
    server_socket.listen(5)

    # Loop for incoming connections
    #global stop
    #while not stop:
    client_socket, addr = server_socket.accept()

    logging.warning("[==>] Received incoming connection from {0}:{1}".format(addr[0], addr[1]))

    # Start a new thread for any incoming connections
    proxy_thread = threading.Thread(target=proxy_handler,
                                    args=(client_socket, remote_host, remote_port, receive_first))
    proxy_thread.start()


def start_listening(local_host: str, local_port: int, remote_host: str, remote_port: int, receive_first: bool):
    # Start looping and listening for incoming requests (see implementation below)
    server_loop(local_host, local_port, remote_host, remote_port, receive_first)


def proxy_handler(client_socket, remote_host, remote_port, receive_first):
    # Define the remote socket used for forwarding requests
    remote_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Establish a connection to the remote host
    remote_socket.connect((remote_host, remote_port))

    # intercept the response before it's received
    if receive_first:
        # receive data from the connection and return a buffer
        remote_buffer = receive_from(remote_socket)

        # Convert the buffer from hex to human readable output
        #hexdump(remote_buffer)

        # Handle the response (an opportunity for read/write of the response data)
        remote_buffer = response_handler(remote_buffer)

        # If data exists send the response to the local client
        if len(remote_buffer):
            logging.warning("[<==] Sending {0} bytes from localhost".format(len(remote_buffer)))
            client_socket.send(remote_buffer)

            # Continually read from local, print the output and forward to the remotehost
    while True:
        # Receive data from the client and send it to the remote
        local_buffer = receive_from(client_socket)
        send_data(local_buffer, "localhost", remote_socket)

        # Receive the response and sent it to the client
        remote_buffer = receive_from(remote_socket)
        send_data(remote_buffer, "remotehost", client_socket)

        # Close connections, print and break out when no more data is available
        if not len(local_buffer):
            client_socket.close()
            remote_socket.close()
            logging.warning("[*] No more data. Connections closed")

            break


def send_data(buffer, type, socket):
    if len(buffer):
        logging.warning("[<==] Received {0} bytes from {1}.".format(len(buffer), type))
        #hexdump(buffer)

        if "localhost" in type:
            mod_buffer = request_handler(buffer)
        else:
            mod_buffer = response_handler(buffer)

        socket.send(mod_buffer)

        logging.warning("[<==>] Sent to {0}".format(type))


def receive_from(connection):
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


def response_handler(buffer):
    logging.warning("response_handler: {0}".format(buffer))
    return buffer


def request_handler(buffer):
    logging.warning("request handler: {0}".format(buffer))
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
    logging.warning(b'\n'.join(result))
