LISTENER_IDENTIFIER = "[LISTENER]"
COMMENT_IDENTIFIER = "#"


class BrokerConfigReader(object):
    """
    Handles the config-reading from the file
    """

    @staticmethod
    def read_config(config_path):
        """
        Reads the provided broker config and extracts all listener settings
        :param config_path: path of the broker config file
        :return: list of @ListenerConfig objects
        """
        try:
            listeners = []
            for listener in BrokerConfigReader.get_listener_configs(config_path):
                listener_config = ListenerConfig()
                for setting in listener.split("\n")[1:]:
                    if setting and not setting.strip().startswith(COMMENT_IDENTIFIER):
                        BrokerConfigReader.set_value_from_config(setting, listener_config)
                listeners.append(listener_config)
            return listeners
        except FileNotFoundError as e:
            print(f"Error while reading the broker config file: {e}")
            exit(0)

    @staticmethod
    def find_all_occurrences(string, sub):
        """
        Find all occurrences of sub in string
        :param string: the complete text
        :param sub: the substring that should be found in the complete text
        :return: all indices of substring occurrences
        """
        start = 0
        while True:
            start = string.find(sub, start)
            if start == -1:
                return
            yield start
            start += len(sub)

    @staticmethod
    def get_listener_configs(config_path):
        """
        Helper-function: Splits the config file by LISTENER_IDENTIFIER (default: [LISTENER])
        :param config_path: path of the broker config file
        :return: Generator - settings/config for each listener
        """
        with open(config_path, "r") as config_file:
            text = config_file.read()
            positions = list(BrokerConfigReader.find_all_occurrences(text, LISTENER_IDENTIFIER))
            for x in range(0, len(positions)):
                if x < len(positions) - 1:
                    yield text[positions[x]: positions[x + 1]]
                else:
                    yield text[positions[x]:]

    @staticmethod
    def set_value_from_config(setting, listenerconfig):
        """
        Assign each setting/config for each Listener of the config file to a ListenerConfig object
        :param setting: setting (=1 line in the config file)
        :param listenerconfig: ListenerConfig object, that should be modified
        :return: no return value - sets the value of the ListenerConfig object directly
        """
        try:
            setting = setting.strip().split()
            identifier = setting[0]
            try:
                value = BrokerConfigReader.handle_config_value(identifier, setting[1].lower().strip())
            except FileNotFoundError:
                print(
                    f"An error has occurred at the value of your setting '{identifier}'. "
                    f"File '{setting[1]}' not found.")
                exit(0)
            except ValueError:
                print(
                    f"An error has occurred at the value of your setting '{identifier}'. "
                    f"Value '{setting[1]}' is not supported.")
                exit(0)
            except SyntaxError:
                print(
                    f"An error has occurred while reading the broker settings. Option '{identifier}' is not supported.")
                exit(0)
        except IndexError as e:
            print(
                f"An error has occurred during the broker config-file parsing. "
                f"Please provide values for all your settings.")
            exit(0)

    @staticmethod
    def handle_config_value(identifier, value):
        """
        Convert the value of the broker config file into an understandable value for the broker application
        :param identifier: setting identifier of the broker
        :param value: value of the setting
        :return: the converted value
        """
        if identifier == "PORT":
            try:
                return int(value)
            except TypeError:
                print(f"An error occurred while parsing the Port value. '{value}' is not a valid Port.")
        else:
            raise SyntaxError


class ListenerConfig(object):
    """
    Stores the values of the config-file. Understandable for the broker application
    """

    def __init__(self):
        self._port = 1883  # Port for the listener

    def __str__(self):
        """
        Converts the object to a representative string
        :return: String of the object
        """
        return f"ListenerConfig: [PORT:{self._port}]"

    @property
    def port(self):
        return self._port

    @port.setter
    def port(self, value):
        self._port = value
