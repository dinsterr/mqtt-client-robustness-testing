import logging
import os
import shutil
import sys

from config import Config

LATEST_LOGS_DIR = f"{Config.BASE_LOGS_DIR}/latest"
formatter = logging.Formatter(fmt='%(asctime)-16s | %(name)-15s | %(threadName)-21s | %(levelname)-7s | %(message)s',
                              datefmt='%d-%m-%Y %H:%M:%S')
logging.root.setLevel(logging.DEBUG)


def _setup_directories():
    try:
        shutil.rmtree(LATEST_LOGS_DIR, ignore_errors=True, onerror=None)
    except:
        pass
    try:
        os.makedirs(LATEST_LOGS_DIR)
    except:
        pass


_setup_directories()
fh = logging.FileHandler(f'{LATEST_LOGS_DIR}/monitor.log')
fh.setLevel(Config.FILE_LOG_LEVEL)
fh.setFormatter(formatter)


def construct_logger(name: str):

    logger = logging.getLogger(f"{name}")
    logger.propagate = False
    logger.setLevel(logging.DEBUG)

    ch = logging.StreamHandler(stream=sys.stdout)
    ch.setLevel(Config.STDOUT_LOG_LEVEL)
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    logger.addHandler(fh)

    return logger



def get_logger(name: str):
    return logging.getLogger(name)
