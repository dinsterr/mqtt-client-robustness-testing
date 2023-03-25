import logging


class Config:
    STDOUT_LOG_LEVEL = logging.INFO
    FILE_LOG_LEVEL = logging.DEBUG
    BASE_LOGS_DIR = "./logs"

    # Setup for the test system
    #############################################

    # Command to instantiate the test system. This can be an arbitrary complex shell command.
    # STDOUT and STDERR buffers are monitored for output.
    TEST_COMMAND: str = f"/home/dfs/CLionProjects/fuzzing_targets/cmake-build-debug/fuzzing_targets"

    # The local address of the TCP proxy to which the test system connects
    LOCAL_ADDRESS: str = "localhost"
    LOCAL_PORT: int = 1883

    # The address of the remote system / target MQTT broker
    TARGET_ADDRESS: str = "localhost"
    TARGET_PORT: int = 8088

    # Monitoring conditions
    #############################################

    # The time in seconds that the monitor waits for new data on STDOUT/STDERR buffers before closing.
    MONITOR_BUFFER_READ_TIMEOUT_SECS: int = 10

    # Matches the following regex pattern on the output STDOUT/STDERR buffers.
    REGEX_BUFFER_FILTER_PATTERN: str = "uid"

    # Exit on REGEX match
    EXIT_ON_REGEX_MATCH: bool = False

    # Add matching buffer output to log output only if it matches the pattern
    ONLY_LOG_ON_REGEX_MATCH: bool = True

    # Treats the selected return codes as unexpected exit.
    # Archives all logs in a new directory if the code is returned.
    RETURN_CODES_VALUE_FILTER: list[int] = [1]

     # The time in seconds that the monitor waits for new TCP data from the system under test before closing.
    MAX_LOCAL_TCP_TIMEOUT_SECS = 5

    # The time in seconds that the monitor waits for new TCP data from the broker before closing.
    MAX_REMOTE_TCP_TIMEOUT_SECS = 5
