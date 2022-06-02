import random
import string
import unicodedata

from broker.message_generators.message_generator import MessageGenerator
from packets.mqtt_packet_manager import MQTTPacketManager

MAX_PAYLOAD_CHARS = 1024

# source: https://gist.github.com/mattcarp/3173004
unicode_glyphs = ''.join(
    chr(char)
    for char in range(65533)
    # use the unicode categories that don't include control codes
    if unicodedata.category(chr(char))[0] in 'LMNPSZ'
)


def random_unicode_string(lower_limit=0, upper_limit=MAX_PAYLOAD_CHARS):
    rand_length = random.randint(lower_limit, upper_limit)
    return ''.join([random.choice(unicode_glyphs)
                    for _ in range(rand_length)])


def random_ascii_string(lower_limit=0, upper_limit=MAX_PAYLOAD_CHARS):
    rand_length = random.randint(lower_limit, upper_limit)
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(rand_length))


class RandomPayloadGenerator(MessageGenerator):
    _GENERATOR_TYPE = "RANDOM"

    def __next__(self):
        return MQTTPacketManager.prepare_publish(self._generator_config.topic, random_unicode_string())
