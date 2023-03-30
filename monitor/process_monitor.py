import re
import selectors
import shlex
import subprocess
from typing import Callable

import logger_factory
from config import Config

main_logger = logger_factory.get_logger("monitor")

regex_buffer_filter = re.compile(Config.REGEX_BUFFER_FILTER_PATTERN)


class ProcessResult:
    stdout = None
    stderr = None
    return_code = None
    filter_results = None
    regex_match = 0
    reached_buffer_read_timeout = False
    _exit = False


class ProcessMonitor:
    process_handle: subprocess.Popen = None
    result: ProcessResult = ProcessResult()

    def __init__(self, command):
        main_logger.info(f"Starting subprocess: \"{command}\"")
        self.process_handle = subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def __del__(self):
        if self.process_handle:
            self.process_handle.terminate()

    def run_to_completion(self) -> ProcessResult:
        return self._monitor_process_output(self.process_handle,
                                            stdout_handler=self._regex_matcher_on_buffer,
                                            stderr_handler=self._regex_matcher_on_buffer)

    def _monitor_process_output(self, process_handle: subprocess.Popen,
                                stdout_handler: Callable[[bytes], bytes] = None,
                                stderr_handler: Callable[[bytes], bytes] = None,
                                monitor_frequency_secs: float = 0.1,
                                monitor_timeout_secs: float = Config.MONITOR_BUFFER_READ_TIMEOUT_SECS) -> ProcessResult:
        stdout_buffer = b""
        stderr_buffer = b""

        # Register IO event handler on stdout and stderr buffers
        sel = selectors.DefaultSelector()
        sel.register(process_handle.stdout, selectors.EVENT_READ)
        sel.register(process_handle.stderr, selectors.EVENT_READ)

        # End the loop if we have slept 'no_data_counter' times for a time of 'monitor_frequency_secs'
        no_data_counter = 0
        max_iterations_without_new_data = 0
        if monitor_timeout_secs > -1:
            max_iterations_without_new_data = monitor_timeout_secs / monitor_frequency_secs
        else:
            max_iterations_without_new_data = 1

        main_logger.info("Monitoring STDOUT and STDERR buffers...")
        while no_data_counter < max_iterations_without_new_data \
                and self.result._exit is False:
            has_data = False
            try:
                for key, _ in sel.select(timeout=monitor_frequency_secs):
                    data = key.fileobj.read1()
                    if not data:
                        continue

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

                # We also stop if the process has stopped
                if process_handle.poll():
                    main_logger.debug(f"Subprocess exited with code: {process_handle.returncode}")
                    break

        if no_data_counter >= max_iterations_without_new_data:
            self.result.reached_buffer_read_timeout = True

        process_handle.poll()
        process_handle.kill()

        self.result.stdout = stdout_buffer
        self.result.stderr = stderr_buffer
        self.result.return_code = process_handle.returncode
        return self.result

    def _regex_matcher_on_buffer(self, data: bytes) -> bytes:
        if Config.REGEX_BUFFER_FILTER_PATTERN is None or Config.REGEX_BUFFER_FILTER_PATTERN == "":
            return data

        decoded_data = data.decode("utf-8", errors='ignore')
        if decoded_data and regex_buffer_filter.search(decoded_data):
            self.result.regex_match += 1

            if Config.EXIT_ON_FIRST_REGEX_MATCH:
                self.result._exit = True

        return data
