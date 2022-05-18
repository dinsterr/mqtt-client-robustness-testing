from broker.listener.client_thread import ClientThread
from packets import enums
from util import logger
from util.exceptions import MQTTMessageNotSupportedException, IncorrectProtocolOrderException


class AutoPublishClientThread(ClientThread):
    def __init__(self, client_socket, client_address, listener, subscription_manager, client_manager, debug):
        super().__init__(client_socket, client_address, listener, subscription_manager, client_manager, debug)

    def listen(self):
        """
        Listen on the client socket for incoming messages and handle the different MQTT messages
        """
        try:
            self._client_manager.add_status(self.client_socket, self.client_address, enums.Status.FRESH)
            connected = False
            while self._running:
                if not connected:
                    msg = self.client_socket.recv(1024)
                    if len(msg) > 0:
                        if msg['identifier'] == enums.PacketIdentifer.CONNECT:
                            self.log_received_packet(msg, msg, self.client_id)
                            self.handle_connect(msg)
                            connected = True
                        elif msg['identifier'] == enums.PacketIdentifer.PINGREQ:
                            self.log_received_packet(msg, msg, self.client_id)
                            self.handle_pingreq(msg)
                        elif msg['identifier'] == enums.PacketIdentifer.SUBSCRIBE:
                            self.log_received_packet(msg, msg, self.client_id)
                            self.handle_subscribe(msg)

                else:
                    self.publish()
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
