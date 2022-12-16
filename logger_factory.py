import logging

formatter = logging.Formatter(fmt='%(asctime)-16s | %(name)-15s | %(threadName)-21s | %(levelname)-7s | %(message)s',
                              datefmt='%d-%m-%Y %H:%M:%S')


def construct_logger(name: str):
    logger = logging.getLogger(f"{name}")
    logger.setLevel(logging.DEBUG)

    fh = logging.FileHandler(f'logs/{name}.log')
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    return logger
