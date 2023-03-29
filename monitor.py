import shutil
import threading
import time
from datetime import datetime

import logger_factory
from config import Config
from monitor.process_monitor import ProcessMonitor
from monitor.process_monitor import ProcessResult
from monitor.tcp_proxy import TcpProxy

main_logger = logger_factory.construct_logger("monitor")
subprocess_logger = logger_factory.construct_logger("subprocess")


def _run_proxy(local_address, local_port, target_address, target_port):
    main_logger.info(f"Starting proxy: {local_address}:{local_port} -> {target_address}:{target_port}")
    threading.Thread(target=TcpProxy, args=(local_address, local_port, target_address, target_port),
                     daemon=True).start()


def _run_monitored_subprocess():
    # Run the subprocess which should be monitored
    monitor = ProcessMonitor(Config.TEST_COMMAND)
    output: ProcessResult = monitor.run_to_completion()
    main_logger.info("Finished monitoring")

    if not output:
        return

    _log_final_output(output)
    if output.regex_match > 0:
        main_logger.info(f"REGEX: {output.regex_match} matches")


def _log_final_output(output):
    if output:
        subprocess_logger.info(f"STDOUT: {output.stdout}")
        subprocess_logger.info(f"STDERR: {output.stderr}")
        subprocess_logger.info(f"RETURN: {output.return_code}")

        if (output.return_code in Config.RETURN_CODES_VALUE_FILTER and not Config.ONLY_LOG_ON_REGEX_MATCH) or \
                (output.regex_match > 0):
            now = datetime.now()
            timestamp = now.strftime("%Y-%m-%dT%H:%M:%S")
            try:
                shutil.move(f"{Config.BASE_LOGS_DIR}/latest", f"{Config.BASE_LOGS_DIR}/{timestamp}")
            except:
                pass


if __name__ == "__main__":
    _run_proxy(Config.LOCAL_ADDRESS, Config.LOCAL_PORT, Config.TARGET_ADDRESS, Config.TARGET_PORT)
    _run_monitored_subprocess()
