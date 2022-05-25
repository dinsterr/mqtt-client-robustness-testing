from broker.message_generators.message_generator import MessageGenerator


class HelloWorldMessageGenerator(MessageGenerator):
    _GENERATOR_TYPE = "HELLO_WORLD"

    def __next__(self):
        # TODO: allow detailed configuration of the message (e.g. setting the topic, qos, etc.)
        return b'0\x11\x00\x03foo\x00hello world'
