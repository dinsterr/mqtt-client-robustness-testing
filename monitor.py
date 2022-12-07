import shlex
import subprocess
import threading
from time import sleep

from monitor import tcp_proxy
import logger_factory

# TODO: better logging. separation into debug and warn
# TODO: correctly terminate all threads
# TODO: how to deal with stdin
# TODO: configurable timeouts (also of sub thread)

local_address = "localhost"
local_port = 8088
target_address = "localhost"
target_port = 12345

main_logger = logger_factory.construct_logger("monitor")
subprocess_logger = logger_factory.construct_logger("subprocess")

if __name__ == "__main__":
    # Spawn the proxy socket
    function = tcp_proxy.start_listening
    args = (local_address, local_port, local_address, target_port, True)
    socket_thread = threading.Thread(target=function, args=args)
    socket_thread.start()

    sleep(1)
    command_line = f"bash ./send.sh {target_address} {target_port}"
    main_logger.debug("Starting subprocess: " + command_line)
    # According to the subprocess documentation:
    # It may not be obvious how to break a shell command into a sequence of arguments, especially in complex cases.
    split_command_line = shlex.split(command_line)
    process = subprocess.Popen(split_command_line, shell=False, stdout=subprocess.PIPE)
    stdout_data, stderr_data = process.communicate(timeout=15)
    return_code = process.returncode

    subprocess_logger.debug(f"STDOUT: {stdout_data}")
    subprocess_logger.debug(f"STDERR: {stderr_data}")
    subprocess_logger.debug(f"RETURN: {return_code}")

    main_logger.debug("Subprocess finished")
    main_logger.debug("Stopped monitor")
    exit()
