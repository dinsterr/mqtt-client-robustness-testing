import shlex
import subprocess
import threading
from time import sleep

from monitor import tcp_proxy
import logger_factory

# TODO: correctly terminate all threads
# TODO: how to deal with stdin. subprocess communicate?
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

    # Run the subprocess which should be monitored
    sleep(1)
    command_line = f"bash ./send.sh {target_address} {target_port}"
    main_logger.debug("Starting subprocess: " + command_line)
    process = subprocess.run(shlex.split(command_line), capture_output=True)
    subprocess_logger.debug(f"STDOUT: {process.stdout}")
    subprocess_logger.debug(f"STDERR: {process.stderr}")
    subprocess_logger.debug(f"RETURN: {process.returncode}")

    main_logger.debug("Subprocess finished")
    main_logger.debug("Stopped monitor")
    exit()
