from broker.message_generators.message_generator import MessageGenerator
from packets.mqtt_packet_manager import MQTTPacketManager
from .utils.generator_util import random_unicode_string

class RandomPayload(MessageGenerator):
    _GENERATOR_TYPE = "RANDOM_PAYLOAD"

    def __next__(self):
        return MQTTPacketManager.prepare_publish(self._generator_config.topic, random_unicode_string())
