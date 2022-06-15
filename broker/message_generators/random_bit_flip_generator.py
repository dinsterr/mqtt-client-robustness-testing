from random import Random
from broker.message_generators.message_generator import MessageGenerator
from packets.mqtt_packet_manager import MQTTPacketManager
from bitarray import bitarray

RANDOM = Random()
BIT_FLIP_PROBABILITY = 1 / 3


class RandomBitFlipGenerator(MessageGenerator):
    _GENERATOR_TYPE = "BIT_FLIP"

    _message: bytes = None
    _message_bits: list = None

    def __init__(self, generator_config):
        self._message: bytes = MQTTPacketManager.prepare_publish(generator_config.topic, "hello world")

        ba = bitarray()
        ba.frombytes(self._message)

        self._message_bits = ba.tolist()

    def __next__(self):
        if RANDOM.random() >= BIT_FLIP_PROBABILITY:
            return self._message

        bitflip_index = RANDOM.randint(0, len(self._message_bits))
        return flip_bit(self._message_bits, bitflip_index)


def flip_bit(bit_array: list, index: int):
    temp_list = bit_array.copy()
    temp_list[index] = not bool(temp_list[index])
    return bitarray(temp_list).tobytes()
