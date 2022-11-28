import shlex
import subprocess
import sys
from threading import Thread

from monitor import tcp_proxy

# TODO: better logging. separation into debug and warn
# TODO: correctly terminate all threads
# TODO: how to deal with stdin
# TODO: configurable timeouts (also of sub thread)

local_address = "localhost"
local_port = 8088
target_port = 8081

if __name__ == "__main__":
    function = tcp_proxy.proxy_socket
    args = (local_address, local_port, local_address, target_port)

    # Spawn the proxy socket and wait for a connection from the client before connecting to the server
    thread = Thread(target=function, args=args)
    thread.start()

    command_line = f"nc {local_address} {local_port}"
    # According to the subprocess documentation:
    # It may not be obvious how to break a shell command into a sequence of arguments, especially in complex cases.
    split_command_line = shlex.split(command_line)
    process = subprocess.Popen(split_command_line, shell=False, stdout=subprocess.PIPE)
    for c in iter(lambda: process.stdout.read(1), b""):
        sys.stdout.buffer.write(c)

    print("Subprocess finished")
    print("Stopped monitor")

