import shlex
import subprocess
import sys
import threading
from time import sleep
import logging

from monitor import tcp_proxy

# TODO: better logging. separation into debug and warn
# TODO: correctly terminate all threads
# TODO: how to deal with stdin
# TODO: configurable timeouts (also of sub thread)

local_address = "localhost"
local_port = 8088
target_port = 8081

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(name)-4s (%(levelname)-4s) %(message)s',
                    datefmt='%d-%m-%Y %H:%M:%S')
logging.getLogger("main")

if __name__ == "__main__":

    # Spawn the proxy socket
    function = tcp_proxy.start_listening
    args = (local_address, local_port, local_address, target_port, False)
    socket_thread = threading.Thread(target=function, args=args)
    socket_thread.start()

    command_line = f"bash ./send.sh"
    logging.debug("Starting subprocess: " + command_line)
    # According to the subprocess documentation:
    # It may not be obvious how to break a shell command into a sequence of arguments, especially in complex cases.
    split_command_line = shlex.split(command_line)
    process = subprocess.Popen(split_command_line, shell=False, stdout=subprocess.PIPE)
    for c in iter(lambda: process.stdout.read(1), b""):
        sys.stdout.buffer.write(c)

    logging.debug("Subprocess finished")
    logging.debug("Stopped monitor")
    socket_thread.join(2)
