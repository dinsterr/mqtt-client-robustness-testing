from abc import abstractmethod


class MessageGeneratorConfig:
    def __init__(self):
        self.generator_type = None
        self.msg_topic = None


class MessageGenerator(object):
    _GENERATOR_TYPE = None

    def __new__(cls, generator_config):
        # Uses a factory pattern to create a MessageGenerator of type 'generator_type'
        # Available classes are dynamically pulled from the 'broker.message_generators' package
        for subclass in MessageGenerator.__subclasses__():
            if generator_config.generator_type and generator_config.generator_type == subclass._GENERATOR_TYPE:
                self = object.__new__(subclass)
                self._generator_config = generator_config
                return self
        raise ModuleNotFoundError(f"Failed to find a valid generator of type 'f{generator_config.generator_type}'!")

    def get_generator_type(self):
        return self._GENERATOR_TYPE

    @abstractmethod
    def __next__(self) -> bytes:
        pass

