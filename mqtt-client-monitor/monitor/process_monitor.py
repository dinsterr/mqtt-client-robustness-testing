import re
import selectors
import shlex
import subprocess
from abc import abstractmethod

import logger_factory
from config import Config

main_logger = logger_factory.get_logger("monitor")


class ProcessResult:
    stdout = ""
    stderr = ""
    return_code = None
    buffer_handler_result = None
    buffer_handler_exit = False


class BufferHandler:
    _exit = False

    @abstractmethod
    def get_printable_result(self):
        return None

    @abstractmethod
    def stdout_handler(self, data):
        return None

    @abstractmethod
    def stderr_handler(self, data):
        return None

    @property
    def exit(self):
        return self._exit


class RegexBufferHandler(BufferHandler):
    """
    Matches the buffer data against a regex pattern from the Config and counts the amount of matches.
    Sets the BufferHandler 'exit' flag if the Config.EXIT_ON_FIRST_REGEX_MATCH is set and a match is found.
    """
    _regex_match_count = 0
    # Pre-compile the regex pattern for better loop performance
    _regex_buffer_filter = re.compile(Config.REGEX_BUFFER_FILTER_PATTERN)

    def get_printable_result(self):
        output = f"REGEX: {self._regex_match_count} matches."
        if Config.EXIT_ON_FIRST_REGEX_MATCH and self._regex_match_count > 0:
            output += " Max configured matches reached."
        return output

    def stdout_handler(self, data: bytes) -> bytes:
        return self._regex_matcher_on_buffer(data)

    def stderr_handler(self, data: bytes) -> bytes:
        return self._regex_matcher_on_buffer(data)

    def _regex_matcher_on_buffer(self, data: bytes) -> bytes:
        if Config.REGEX_BUFFER_FILTER_PATTERN is None or Config.REGEX_BUFFER_FILTER_PATTERN == "":
            return data

        decoded_data = data.decode("utf-8", errors='ignore')
        if decoded_data and self._regex_buffer_filter.search(decoded_data):
            self._regex_match_count += 1

            if Config.EXIT_ON_FIRST_REGEX_MATCH:
                self._exit = True

        return data


class BufferStatus:
    isStop = False
    _no_new_data_counter = 0

    def __init__(self, monitor_timeout_secs, monitor_frequency_secs):
        # We want to stop if we have slept 'no_data_counter' times for a time of 'monitor_frequency_secs'
        # Which approximately equals the configured 'monitor_timeout_secs'
        if monitor_timeout_secs > -1:
            self._max_iterations_without_new_data = monitor_timeout_secs / monitor_frequency_secs
        else:
            self._max_iterations_without_new_data = 1

    def record(self, stderr_buffer, stdout_buffer):
        if stderr_buffer is not None and stdout_buffer is not None:
            self._no_new_data_counter = 0
            return

        self._no_new_data_counter += 1

        # Set stop if max iterations without new data is reached
        if self._no_new_data_counter >= self._max_iterations_without_new_data:
            self.isStop = True


class ProcessMonitor:
    _result: ProcessResult = ProcessResult()
    _selector = selectors.DefaultSelector()
    _process_handle: subprocess.Popen = None

    def __init__(self, command):
        main_logger.info(f"Starting subprocess: \"{command}\"")
        self._process_handle = subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # Register IO event handler on stdout and stderr buffers
        self._selector.register(self._process_handle.stdout, selectors.EVENT_READ)
        self._selector.register(self._process_handle.stderr, selectors.EVENT_READ)

    def __del__(self):
        if self._process_handle:
            self._process_handle.kill()

    def run_to_completion(self) -> ProcessResult:
        return self._monitor_process_output(self._process_handle, RegexBufferHandler())

    def _monitor_process_output(self, process_handle: subprocess.Popen,
                                buffer_handler: BufferHandler = BufferHandler(),
                                monitor_frequency_secs: float = 0.1,
                                monitor_timeout_secs: float = Config.MONITOR_BUFFER_READ_TIMEOUT_SECS) -> ProcessResult:
        main_logger.info("Monitoring STDOUT and STDERR buffers...")

        buffer_status = BufferStatus(monitor_timeout_secs, monitor_frequency_secs)
        while True:
            stderr_buffer, stdout_buffer = self._read_buffer_data(process_handle,
                                                                  buffer_handler.stderr_handler,
                                                                  buffer_handler.stdout_handler)

            buffer_status.record(stderr_buffer, stdout_buffer)
            self._result.stdout += str(stdout_buffer or "")
            self._result.stderr += str(stderr_buffer or "")

            # End loop if the process has stopped
            if process_handle.poll():
                main_logger.debug(f"Subprocess exited with code: {process_handle.returncode}")
                break

            # End loop if the buffer handler exit condition is reached
            if buffer_handler.exit:
                main_logger.debug(f"Process buffer handler reached exit condition")
                self._result.buffer_handler_exit = True
                break

            # End loop if the buffer status has not recorded any new data within the given timeout
            if buffer_status.isStop:
                main_logger.debug(f"Process buffer handler reached exit condition")
                self._result.reached_buffer_result_timeout = True
                break

        process_handle.kill()
        self._result.return_code = process_handle.poll()
        self._result.buffer_handler_result = buffer_handler.get_printable_result()
        return self._result

    def _read_buffer_data(self, process_handle, stderr_handler, stdout_handler, monitor_frequency_secs=0.1):
        stdout_buffer = None
        stderr_buffer = None

        try:
            for key, _ in self._selector.select(timeout=monitor_frequency_secs):
                data = key.fileobj.read1()
                if not data:
                    continue

                # Pass data to the relevant handler and add the result to the respective buffer
                if key.fileobj is process_handle.stdout:
                    stdout_buffer = data if stdout_handler is None else stdout_handler(data)
                else:
                    stderr_buffer = data if stderr_handler is None else stderr_handler(data)
        except KeyboardInterrupt:
            main_logger.info("Stopped subprocess monitor")
        return stderr_buffer, stdout_buffer
