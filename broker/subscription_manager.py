class SubscriptionManager(object):
    def __init__(self, max_subscribers=50):
        self._max_subscribers = max_subscribers
        self._subscriberManagement = {}

    def add_subscriber(self, client_socket, client_address, topic, client_id):
        """
        Adds a subscriber to the subscription list
        :param client_socket: Socket on which the client connected to the broker
        :param client_address: Client's connection address and port
        :param topic: The topic the client subscribed to
        :param client_id: ID of the connected client
        """

        subscriber = {"client_socket": client_socket, "client_address": client_address, 'client_id': client_id}
        if topic in self._subscriberManagement:
            self._subscriberManagement[topic].append(subscriber)
        else:
            self._subscriberManagement[topic] = [subscriber]

    def remove_subscriber(self, client_socket, client_address, client_id):
        """
        Removes a subscribe from the subscription list
        :param client_socket: socket on which the client connected to the broker
        :param client_address: client's connection address and port
        :param client_id: ID of the connected client
        """
        client = {"client_socket": client_socket, "client_address": client_address, "client_id": client_id}
        for topic in self._subscriberManagement:
            if client in self._subscriberManagement[topic]:
                self._subscriberManagement[topic].remove(client)

    def get_topic_subscribers(self, topic):
        """
        Returns a list of containing all subscribers of a certain topic.
        :param topic: Topic of the subscribers
        :return: All subscribers of a certain topic
        """
        try:
            return self._subscriberManagement[topic]
        except KeyError:
            return []

    @property
    def max_subscribers(self):
        return self._max_subscribers

    @max_subscribers.setter
    def max_subscribers(self, value):
        self._max_subscribers = value
