import time

from broker.listener.client_thread import ClientThread
from packets import enums
from util import logger
from util.exceptions import MQTTMessageNotSupportedException, IncorrectProtocolOrderException


class AutoPublishClientThread(ClientThread):
    def __init__(self, client_socket, client_address, listener, subscription_manager, client_manager, auto_publish_interval, debug):
        super().__init__(client_socket, client_address, listener, subscription_manager, client_manager, debug)
        self._auto_publish_interval = auto_publish_interval

    # TODO: rename (e.g. run)
    def listen(self):
        try:
            while self._running:
                self.publish()
                # TODO: benchmark speed
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
        msg = b'0\x11\x00\x03foo\x00hello world'
        for sub in self._subscription_manager.get_topic_subscribers(topic):
            logger.logging.info(
                f"Sent publish message '{msg}' in '{topic}' to Client {sub['client_id']}")
            sub['client_socket'].send(msg)
