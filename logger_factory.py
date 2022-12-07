import logging

formatter = logging.Formatter(fmt='%(asctime)-16s | %(name)-14s | %(levelname)-6s | %(message)s',
                              datefmt='%d-%m-%Y %H:%M:%S')


def construct_logger(name: str):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    fh = logging.FileHandler(f'monitor.log')
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    return logger
