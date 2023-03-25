import shutil
import threading
import time
from datetime import datetime

import logger_factory
from config import Config
from monitor.tcp_proxy import TcpProxy
from monitor.process_monitor import ProcessMonitor
from monitor.process_monitor import ProcessResult


# TODO: correctly terminate all threads
# TODO: Move logs if case is true to archive test run

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
    main_logger.debug("Finished monitoring")

    _log_final_output(output)


def _log_final_output(output):
    if output and output.return_code \
            and output.return_code in Config.RETURN_CODES_VALUE_FILTER:
        subprocess_logger.info(f"STDOUT: {output.stdout}")
        subprocess_logger.info(f"STDERR: {output.stderr}")
        subprocess_logger.info(f"RETURN: {output.return_code}")
        main_logger.info("Subprocess finished")

        time.sleep(5)
        now = datetime.now()
        timestamp = now.strftime("%Y-%m-%dT%H:%M:%S")
        try:
            shutil.move(f"{Config.BASE_LOGS_DIR}/latest", f"{Config.BASE_LOGS_DIR}/{timestamp}")
        except:
            pass


if __name__ == "__main__":
    _run_proxy(Config.LOCAL_ADDRESS, Config.LOCAL_PORT, Config.TARGET_ADDRESS, Config.TARGET_PORT)
    _run_monitored_subprocess()
