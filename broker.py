import argparse
import os
import threading
import time

from broker.client_manager import ClientManager
from broker.listener import *
from broker.subscription_manager import SubscriptionManager
from util.configreader import BrokerConfigReader as ConfigReader

if __name__ == "__main__":
    # Listeners
    LISTENERS = []
    RUNNING_THREADS = []
    HOSTNAME = "0.0.0.0"
    # default configs
    CONFIG_PATH = os.path.dirname(os.path.realpath(__file__)) + "/broker.config"

    # argument parser
    parser = argparse.ArgumentParser("broker.py", description="MQTT Broker supporting Multilateral Security",
                                     epilog="Developed by Babbadeckl. Questions and Bug-reports can be mailed to "
                                            "korbinian.spielvogel@uni-passau.de")
    # argument for config file
    parser.add_argument('-c', '--config', default=CONFIG_PATH, type=str, dest="config",
                        metavar="PATH", help="location of the config file for the broker")
    # argument for hostname
    parser.add_argument('-H', '--hostname', dest="hostname", help="hostname of the broker", metavar="HOSTNAME",
                        type=str, default=HOSTNAME)

    # argument for debug mode
    parser.add_argument('-d', '--debug', dest="debug", help="turn on the debug mode for the broker",
                        action='store_true', default=0)
    args = parser.parse_args()

    # assign argument values
    listener_configs = ConfigReader.read_config(args.config)
    logger.DEBUG = args.debug

    # assign argument hostname
    HOSTNAME = args.hostname

    # create SubscriptionManager
    subscription_manager = SubscriptionManager()

    # create StatusManager
    client_manager = ClientManager()

    # create listeners
    try:
        for listener_config in listener_configs:
            LISTENERS.append(Listener(listener_config, ip=HOSTNAME, debug=logger.DEBUG,
                                      subscription_manager=subscription_manager, client_manager=client_manager))
    except SyntaxError:
        logger.logging.error(
            f"Listener config port is invalid.")
        exit(0)
    except ValueError:
        logger.logging.error(f"Listener config object is invalid. Something went terribly wrong.")
        exit(0)

    # Debug messages
    if logger.DEBUG:
        logger.print_listener_configs(listener_configs)
        logger.print_listeners(LISTENERS)

    # Creating a listener thread for each initialized listener
    for listener in LISTENERS:
        thread = threading.Thread(target=listener.listen)
        RUNNING_THREADS.append(thread)
        thread.setDaemon(True)
        thread.start()

    # Handling server shutdown by CTRL+C
    try:
        while True:
            time.sleep(5)
    except (Exception, KeyboardInterrupt, SystemExit):
        logger.logging.info("Broker shutdown initiated...")
        for index, thread in enumerate(RUNNING_THREADS):
            logger.logging.info(f"Stopping {LISTENERS[index]} ...")
            LISTENERS[index].running = False

            logger.logging.info(f"Stopping Thread ...")
            thread.join(1)

            logger.logging.info(f"Closing Sockets ...")
            LISTENERS[index].close_sockets()
        logger.logging.info("Broker shutdown complete.")
