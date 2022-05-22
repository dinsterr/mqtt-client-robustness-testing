from abc import abstractmethod


class MessageGeneratorConfig:
    def __init__(self):
        self.generator_type = None
        # TODO: currently unused
        self.msg_topic = None


class MessageGenerator(object):
    _GENERATOR_TYPE = None

    def __new__(cls, generator_config):
        # Uses a factory pattern to create a MessageGenerator of type 'generator_type'
        for subclass in MessageGenerator.__subclasses__():
            if generator_config.generator_type and generator_config.generator_type == subclass._GENERATOR_TYPE:
                self = object.__new__(subclass)
                return self
        raise ValueError(f"Failed to find a valid generator of type '{generator_config.generator_type}'!")

    @abstractmethod
    def __next__(self):
        pass


class HelloWorldMessageGenerator(MessageGenerator):
    _GENERATOR_TYPE = "HELLO_WORLD"

    def __next__(self):
        # TODO: allow detailed configuration of the message (e.g. setting the topic, qos, etc.)
        return b'0\x11\x00\x03foo\x00hello world'
