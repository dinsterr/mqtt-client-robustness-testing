import shlex
import subprocess
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
target_address = "localhost"
target_port = 12345

formatter = logging.Formatter(fmt='%(asctime)-16s | %(name)-14s | %(levelname)-6s | %(message)s', datefmt='%d-%m-%Y %H:%M:%S')

logger = logging.getLogger('Monitor')
logger.setLevel(logging.DEBUG)
# create file handler which logs even debug messages
fh = logging.FileHandler('main.log')
fh.setLevel(logging.DEBUG)
# create console handler with a higher log level
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
fh.setFormatter(formatter)
ch.setFormatter(formatter)
logger.addHandler(fh)
logger.addHandler(ch)

if __name__ == "__main__":
    # Spawn the proxy socket
    function = tcp_proxy.start_listening
    args = (local_address, local_port, local_address, target_port, True)
    socket_thread = threading.Thread(target=function, args=args)
    socket_thread.start()

    sleep(1)
    command_line = f"bash ./send.sh {target_address} {target_port}"
    logger.debug("Starting subprocess: " + command_line)
    # According to the subprocess documentation:
    # It may not be obvious how to break a shell command into a sequence of arguments, especially in complex cases.
    split_command_line = shlex.split(command_line)
    process = subprocess.Popen(split_command_line, shell=False, stdout=subprocess.PIPE)
    stdout_data, stderr_data = process.communicate(timeout=15)
    return_code = process.returncode

    logger.debug(f"Subprocess std output: {stdout_data}")
    logger.debug(f"Subprocess error output: {stderr_data}")
    logger.debug(f"Subprocess return code: {return_code}")

    logger.debug("Subprocess finished")
    logger.debug("Stopped monitor")
    exit()
