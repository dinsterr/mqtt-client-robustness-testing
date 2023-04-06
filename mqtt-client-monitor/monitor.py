import logging
import shutil
from datetime import datetime

import logger_factory
from config import Config
from monitor.process_monitor import ProcessMonitor
from monitor.process_monitor import ProcessResult
from monitor.tcp_proxy import TcpProxy

logger = logging.getLogger("monitor")
logger.setLevel(level=0)


def _log_final_output(result):
    if not result:
        return

    logger.info(f"STDOUT: {result.stdout}")
    logger.info(f"STDERR: {result.stderr}")
    logger.info(f"RETURN: {result.return_code}")
    logger.info(result.buffer_handler_result)

    if (result.return_code in Config.RETURN_CODES_VALUE_FILTER) \
            or result.buffer_handler_exit:
        now = datetime.now()
        timestamp = now.strftime("%Y-%m-%dT%H:%M:%S")
        try:
            shutil.move(f"{Config.BASE_LOGS_DIR}/latest", f"{Config.BASE_LOGS_DIR}/{timestamp}")
        except:
            pass


def main():
    logger.info(
        f"Starting proxy: {Config.LOCAL_ADDRESS}:{Config.LOCAL_PORT} -> {Config.TARGET_ADDRESS}:{Config.TARGET_PORT}")
    proxy = TcpProxy(Config.LOCAL_ADDRESS, Config.LOCAL_PORT, Config.TARGET_ADDRESS, Config.TARGET_PORT)
    proxy.start()

    # Run the subprocess which should be monitored
    monitor = ProcessMonitor(Config.TEST_COMMAND)
    result: ProcessResult = monitor.run_to_completion()
    logger.info("Finished monitoring")

    _log_final_output(result)

    proxy.stop()
    proxy.join(timeout=1)


if __name__ == "__main__":
    main()
