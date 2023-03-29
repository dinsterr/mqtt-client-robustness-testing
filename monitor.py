import shutil
import threading
from datetime import datetime

import logger_factory
from config import Config
from monitor.process_monitor import ProcessMonitor
from monitor.process_monitor import ProcessResult
from monitor.tcp_proxy import TcpProxy

logger = logger_factory.construct_logger("monitor")


def _run_proxy(local_address, local_port, target_address, target_port):
    logger.info(f"Starting proxy: {local_address}:{local_port} -> {target_address}:{target_port}")
    threading.Thread(target=TcpProxy, args=(local_address, local_port, target_address, target_port),
                     daemon=True).start()


def _run_monitored_subprocess():
    # Run the subprocess which should be monitored
    monitor = ProcessMonitor(Config.TEST_COMMAND)
    output: ProcessResult = monitor.run_to_completion()
    logger.info("Finished monitoring")

    if not output:
        return

    _log_final_output(output)


def _log_final_output(output):
    if output:
        logger.info(f"STDOUT: {output.stdout}")
        logger.info(f"STDERR: {output.stderr}")
        logger.info(f"RETURN: {output.return_code}")
        logger.info(f"REGEX: {output.regex_match} matches")

        if (output.return_code in Config.RETURN_CODES_VALUE_FILTER) or \
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
