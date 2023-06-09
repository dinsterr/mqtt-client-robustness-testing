from broker.message_generators.message_generator import MessageGenerator
from packets.mqtt_packet_manager import MQTTPacketManager

import logging
import json

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
from mutators.mutator import JsonMutator

SEED_FILE_PATH = "seed_files/test.json"


class JsonSeedBased(MessageGenerator):
    _GENERATOR_TYPE = "JSON_SEED"
    _mutated_payloads = None

    def __init__(self, generator_config):
        self._mutated_payloads = iter(self._load_payload_data())

    def _load_payload_data(self):
        with open(SEED_FILE_PATH) as json_file:
            # Throws exception if not valid json format
            json_data = json.dumps(json.load(json_file))

        mutator = JsonMutator(json_data)
        payloads = mutator.apply(json_data)

        logging.info(f"Loaded {self._GENERATOR_TYPE} with {len(payloads)} different payloads.\n")
        return payloads

    def __next__(self):
        return MQTTPacketManager.prepare_publish(self._generator_config.topic, next(self._mutated_payloads))
