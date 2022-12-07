import random
import string

from broker.message_generators.message_generator import MessageGenerator
from packets.mqtt_packet_manager import MQTTPacketManager
from .utils.generator_util import unicode_glyphs

MAX_PAYLOAD_CHARS = 1024


def random_unicode_string(lower_limit=0, upper_limit=MAX_PAYLOAD_CHARS):
    rand_length = random.randint(lower_limit, upper_limit)
    return ''.join([random.choice(unicode_glyphs)
                    for _ in range(rand_length)])


def random_ascii_string(lower_limit=0, upper_limit=MAX_PAYLOAD_CHARS):
    rand_length = random.randint(lower_limit, upper_limit)
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(rand_length))


class RandomPayloadGenerator(MessageGenerator):
    _GENERATOR_TYPE = "RANDOM_PUBLISH_LENGTH"

    def __next__(self):
        payload = random_unicode_string()

        return MQTTPacketManager.prepare_publish(self._generator_config.topic, payload,
                                                 remaining_length=random.randint(0, len(payload.encode('utf-8'))))
