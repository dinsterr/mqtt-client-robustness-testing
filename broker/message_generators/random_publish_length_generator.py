import random

from broker.message_generators.message_generator import MessageGenerator
from packets.mqtt_packet_manager import MQTTPacketManager
from .utils.generator_util import random_unicode_string


class RandomPayloadGenerator(MessageGenerator):
    _GENERATOR_TYPE = "RANDOM_PUBLISH_LENGTH"

    def __next__(self):
        payload = random_unicode_string()

        return MQTTPacketManager.prepare_publish(self._generator_config.topic, payload,
                                                 remaining_length=random.randint(0, len(payload.encode('utf-8'))))
