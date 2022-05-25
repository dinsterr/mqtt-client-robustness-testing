import time

from broker.listener.client_thread import ClientThread
from broker.message_generators.message_generator import MessageGenerator
from util import logger
from util.exceptions import MQTTMessageNotSupportedException, IncorrectProtocolOrderException


class AutoPublishClientThread(ClientThread):
    def __init__(self, client_socket, client_address, listener, subscription_manager, client_manager,
                 auto_publish_interval, generator_config, debug):
        super().__init__(client_socket, client_address, listener, subscription_manager, client_manager, debug)
        self._auto_publish_interval = auto_publish_interval
        self._message_generator = MessageGenerator(generator_config)
        self._generator_config = generator_config

    def run(self):
        try:
            while self._running:
                self.publish()
                time.sleep(self._auto_publish_interval)
        except OSError:
            pass
        except MQTTMessageNotSupportedException as e:
            logger.logging.error(e)
        except (IncorrectProtocolOrderException, TypeError) as e:
            logger.logging.error(e)
            self.close()

    def publish(self):
        topic = 'foo'
        msg = next(self._message_generator)
        # TODO: send message to current client_socket instead of a target subscribed
        for sub in self._subscription_manager.get_topic_subscribers(topic):
            logger.logging.info(
                f"Sent publish message '{msg}' in '{topic}' to Client {sub['client_id']}")
            sub['client_socket'].send(msg)
