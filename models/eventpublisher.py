class BlockEventPublisher:
    """
    Block event publisher implementation allows subscribers to subscribe a function refrence using
    :meth:`add_subscriber`. Publishers can send events using :meth:`publish`.
    """

    def __init__(self):
        self._subscribers = set()

    def publish(self, object) -> None:
        """
        Publish an object (event). All subscribers will be notified with this object.

        :param object: Object containing info / data about event. Will be sent to subscribers
        """
        for subscriber in self._subscribers:
            subscriber(object)

    def add_subscriber(self, subscriber) -> None:
        """
        Add subscriber who will be notified on events.

        :param subscriber: Function which will be notified on publish. Must accept one parameter (object)
        """
        self._subscribers.add(subscriber)

    def remove_subscriber(self, subscriber) -> None:
        """
        :param subscriber: Function which will no longer be notified on publish.
        """
        self._subscribers.remove(subscriber)