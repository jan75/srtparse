import unittest

from modules.eventpublisher import BlockEventPublisher


class TestEventPublisher(unittest.TestCase):
    counter = 0
    last_event_obj = None

    def handle_event(self, object):
        self.counter = self.counter + 1
        self.last_event_obj = object

    def test_event_publisher(self):
        self.counter = 0
        self.last_message = None

        event_publisher1 = BlockEventPublisher()
        event_publisher1.add_subscriber(self.handle_event)
        event_publisher1.publish('my event')

        self.assertEqual(1, self.counter)
        self.assertEqual('my event', self.last_event_obj)

if __name__ == '__main__':
    unittest.main()