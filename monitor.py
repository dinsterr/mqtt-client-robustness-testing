import shlex
import subprocess
import threading
import selectors
from time import sleep
from typing import Callable

import logger_factory
from monitor.tcp_proxy import TcpProxy

# TODO: correctly terminate all threads
# TODO: how to deal with stdin. subprocess communicate?
# TODO: configurable timeouts (also of sub thread)

local_address = "localhost"
local_port = 8088
target_address = "localhost"
target_port = 12345

main_logger = logger_factory.construct_logger("monitor")
subprocess_logger = logger_factory.construct_logger("subprocess")

is_only_log_if_non_zero_exit_code = True


def _monitor_process_output(process_handle: subprocess.Popen,
                            stdout_handler: Callable[[bytes], bytes] = None,
                            stderr_handler: Callable[[bytes], bytes] = None,
                            monitor_frequency_secs: float = 0.1,
                            monitor_timeout_secs: float = 5,
                            max_timeout_until_io_is_ready_secs: float = 10) -> tuple[bytes, bytes, int]:
    stdout_buffer = b""
    stderr_buffer = b""

    # Register IO event handler on stdout and stderr buffers
    sel = selectors.DefaultSelector()
    sel.register(process_handle.stdout, selectors.EVENT_READ)
    sel.register(process_handle.stderr, selectors.EVENT_READ)

    # End the loop if we have slept 'no_data_counter' times for a time of 'monitor_frequency_secs'
    no_data_counter = 0
    while no_data_counter < (monitor_timeout_secs / monitor_frequency_secs):
        has_data = False
        for key, _ in sel.select(timeout=max_timeout_until_io_is_ready_secs):
            data = key.fileobj.read1()
            if not data:
                break

            # Pass data to the relevant handler and add the result to the respective buffer
            has_data = True
            if key.fileobj is process_handle.stdout:
                if stdout_handler is None:
                    stdout_buffer += data
                else:
                    stdout_buffer += stdout_handler(data)
            else:
                if stderr_handler is None:
                    stderr_buffer += data
                else:
                    stderr_handler(data)

        # If no data was read in this iteration we increase the no_data_counter and sleep
        if has_data:
            no_data_counter = 0
        else:
            no_data_counter += 1
            # We also stop if the process has stopped
            if process_handle.poll():
                subprocess_logger.debug("Subprocess ended")
                break

            sleep(monitor_frequency_secs)

    process_handle.poll()
    return stdout_buffer, stderr_buffer, process_handle.returncode


def _proxy(local_address, local_port, target_address, target_port):
    threading.Thread(target=TcpProxy, args=(local_address, local_port, local_address, target_port), daemon=True).start()


def _run_monitored_subprocess():
    # Run the subprocess which should be monitored
    command_line = f"bash ./send.sh {local_address} {local_port}"
    main_logger.info("Starting subprocess: " + command_line)

    process = subprocess.Popen(shlex.split(command_line), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout_buffer, stderr_buffer, return_code = _monitor_process_output(process, None, None)

    if not is_only_log_if_non_zero_exit_code \
            or (is_only_log_if_non_zero_exit_code and return_code != 0):
        subprocess_logger.info(f"STDOUT: {stdout_buffer}")
        subprocess_logger.info(f"STDERR: {stderr_buffer}")
        subprocess_logger.info(f"RETURN: {return_code}")
        main_logger.info("Subprocess finished")


if __name__ == "__main__":
    main_logger.info(f"Starting proxy: {local_address}:{local_port} -> {target_address}:{target_port}")
    _proxy(local_address, local_port, target_address, target_port)

    _run_monitored_subprocess()
    main_logger.debug("Stopped monitoring")
