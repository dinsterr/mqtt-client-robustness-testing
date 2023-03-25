import logging
import os
import shutil
import sys

from config import Config

LATEST_LOGS_DIR = f"{Config.BASE_LOGS_DIR}/latest"

formatter = logging.Formatter(fmt='%(asctime)-16s | %(name)-15s | %(threadName)-21s | %(levelname)-7s | %(message)s',
                              datefmt='%d-%m-%Y %H:%M:%S')


def construct_logger(name: str):
    _setup_directories()

    logger = logging.getLogger(f"{name}")
    logger.setLevel(Config.FILE_LOG_LEVEL)

    fh = logging.FileHandler(f'{LATEST_LOGS_DIR}/{name}.log')
    fh.setLevel(Config.FILE_LOG_LEVEL)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    ch = logging.StreamHandler(stream=sys.stdout)
    ch.setLevel(Config.FILE_LOG_LEVEL)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    return logger


def _setup_directories():
    try:
        shutil.rmtree(LATEST_LOGS_DIR, ignore_errors=True, onerror=None)
    except:
        pass
    try:
        os.makedirs(LATEST_LOGS_DIR)
    except:
        pass


def get_logger(name: str):
    return logging.getLogger(name)
