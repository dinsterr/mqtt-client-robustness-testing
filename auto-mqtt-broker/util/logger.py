import logging
import warnings

logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.DEBUG)
warnings.filterwarnings('ignore', category=DeprecationWarning)

DEBUG = 0


def print_listener_configs(listener_configs):
    """
    Print the initialized @ListenerConfig objects
    :param listener_configs: the initialized @ListenerConfig objects
    :return: /
    """
    for config in listener_configs:
        print(config)


def print_listeners(listeners):
    """
    Print the initialized @Listener or @TLSListener objects
    :param listeners: the initalized listeners
    :return: /
    """
    for listener in listeners:
        print(listener)
