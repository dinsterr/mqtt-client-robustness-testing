from broker.message_generators.message_generator import MessageGenerator
from packets.mqtt_packet_manager import MQTTPacketManager


class HelloWorldMessageGenerator(MessageGenerator):
    _GENERATOR_TYPE = "HELLO_WORLD"

    def __next__(self):
        return MQTTPacketManager.prepare_publish(self._generator_config.topic, "hello world")
