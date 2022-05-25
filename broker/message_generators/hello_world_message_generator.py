from broker.message_generators.message_generator import MessageGenerator


class HelloWorldMessageGenerator(MessageGenerator):
    _GENERATOR_TYPE = "HELLO_WORLD"

    def __next__(self):
        return b'0\x11\x00\x03foo\x00hello world'
