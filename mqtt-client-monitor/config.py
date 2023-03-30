import logging


class Config:
    # Which level of log messages should be shown in the stdout of the monitor
    STDOUT_LOG_LEVEL = logging.DEBUG
    # Which level of log messages should be written to the archived log files
    FILE_LOG_LEVEL = logging.DEBUG
    BASE_LOGS_DIR = "./logs"

    # Setup for the test system
    #############################################

    # The local address of the TCP proxy to which the test system connects
    LOCAL_ADDRESS: str = "localhost"
    LOCAL_PORT: int = 8080

    # The address of the remote system / target MQTT broker
    TARGET_ADDRESS: str = "localhost"
    TARGET_PORT: int = 1883

    TOPIC: str = "foo"

    # Command to instantiate the test system. This can be an arbitrary complex shell command.
    # STDOUT and STDERR buffers are monitored for output.
    TEST_COMMAND: str = f"../fuzzing-target/cmake-build-debug/" \
                        f"fuzzing-target -a {LOCAL_ADDRESS} -p {LOCAL_PORT} -t {TOPIC} -q 0"

    # Monitoring conditions
    #############################################

    # The time in seconds that the monitor waits for new data on STDOUT/STDERR buffers before closing.
    # (-1 = infinite)
    MONITOR_BUFFER_READ_TIMEOUT_SECS: int = 5

    # Matches the following regex pattern on the output STDOUT/STDERR buffers.
    REGEX_BUFFER_FILTER_PATTERN: str = "uid"

    # Exit on REGEX match
    EXIT_ON_FIRST_REGEX_MATCH: bool = False

    # Add matching buffer output to log output only if it matches the pattern
    ONLY_LOG_ON_REGEX_MATCH: bool = False

    # Treats the selected return codes as unexpected exit.
    # Archives all logs in a new directory only if the code is returned.
    RETURN_CODES_VALUE_FILTER: list[int] = []

    # The time in seconds that the monitor waits for new TCP data from the system under test before closing.
    # (-1 = no limit)
    MAX_LOCAL_TCP_TIMEOUT_SECS = -1

    # The time in seconds that the monitor waits for new TCP data from the broker before closing.
    # (-1 = no limit)
    MAX_REMOTE_TCP_TIMEOUT_SECS = 5
