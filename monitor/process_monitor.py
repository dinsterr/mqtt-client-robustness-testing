import re
import selectors
import shlex
import subprocess
from typing import Callable

from config import Config
import logger_factory

main_logger = logger_factory.get_logger("monitor")
subprocess_logger = logger_factory.get_logger("subprocess")

regex_buffer_filter = re.compile(Config.REGEX_BUFFER_FILTER_PATTERN)


def _regex_matcher_on_buffer(data: bytes) -> bytes:
    if Config.REGEX_BUFFER_FILTER_PATTERN is None:
        if Config.ONLY_LOG_ON_REGEX_MATCH:
            return b""
        else:
            return data

    decoded_data = data.decode("utf-8", errors='ignore')
    if decoded_data and regex_buffer_filter.search(decoded_data):
        # TODO
        if Config.ONLY_LOG_ON_REGEX_MATCH:
            return data
        else:
            return b""

    return b""


class ProcessResult:
    stdout = None
    stderr = None
    return_code = None
    filter_results = None


class ProcessMonitor:
    process_handle: subprocess.Popen = None

    def __init__(self, command):
        main_logger.info(f"Starting subprocess: \"{command}\"")
        self.process_handle = subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def __del__(self):
        if self.process_handle:
            self.process_handle.terminate()

    def run_to_completion(self) -> ProcessResult:
        return self._monitor_process_output(self.process_handle,
                                     stdout_handler=_regex_matcher_on_buffer,
                                     stderr_handler=_regex_matcher_on_buffer)

    def _monitor_process_output(self, process_handle: subprocess.Popen,
                                stdout_handler: Callable[[bytes], bytes] = None,
                                stderr_handler: Callable[[bytes], bytes] = None,
                                monitor_frequency_secs: float = 0.2,
                                monitor_timeout_secs: float = Config.MONITOR_BUFFER_READ_TIMEOUT_SECS) -> ProcessResult:
        result = ProcessResult()
        stdout_buffer = b""
        stderr_buffer = b""

        # Register IO event handler on stdout and stderr buffers
        sel = selectors.DefaultSelector()
        sel.register(process_handle.stdout, selectors.EVENT_READ)
        sel.register(process_handle.stderr, selectors.EVENT_READ)

        # End the loop if we have slept 'no_data_counter' times for a time of 'monitor_frequency_secs'
        no_data_counter = 0
        while no_data_counter < (monitor_timeout_secs * monitor_frequency_secs):
            has_data = False
            try:
                for key, _ in sel.select(timeout=monitor_frequency_secs):
                    data = key.fileobj.read1()
                    if not data:
                        break

                    # Pass data to the relevant handler and add the result to the respective buffer
                    has_data = True
                    if key.fileobj is process_handle.stdout:
                        stdout_buffer += data if stdout_handler is None else stdout_handler(data)
                    else:
                        stderr_buffer += data if stderr_handler is None else stderr_handler(data)
            except KeyboardInterrupt:
                main_logger.info("Stopped subprocess monitor")

            # If no data was read in this iteration we increase the no_data_counter and sleep
            if has_data:
                no_data_counter = 0
            else:
                no_data_counter += 1
                # subprocess_logger.debug("No new output buffer data")

                # We also stop if the process has stopped
                if process_handle.poll():
                    subprocess_logger.debug(f"Subprocess exited with code: {process_handle.returncode}")
                    break

        process_handle.poll()
        result.stdout = stdout_buffer
        result.stderr = stderr_buffer
        result.return_code = process_handle.returncode
        return result
