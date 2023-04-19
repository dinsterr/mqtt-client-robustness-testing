import math

from broker.message_generators.message_generator import MessageGenerator
from packets.mqtt_packet_manager import MQTTPacketManager

import logging
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
from mutators.mutator import BasicMutator


class CIStringMutation(MessageGenerator):
    _GENERATOR_TYPE = "DANGEROUS_STRING"
    _seed_string = ""
    _mutated_payloads = None

    def __init__(self, generator_config):
        self._mutated_payloads = iter(self._load_payload_data())

    def _load_payload_data(self):
        payloads = BasicMutator.get_for_string(ci=False)

        logging.info(f"Loaded {self._GENERATOR_TYPE} with {len(payloads)} different payloads.\n")
        return payloads

    def __next__(self):
        return MQTTPacketManager.prepare_publish(self._generator_config.topic, next(self._mutated_payloads))
