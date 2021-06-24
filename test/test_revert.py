import unittest

from modules.block import Block
from modules.subtitle import Subtitle
from modules.timestamp import Timestamp


class TestRevert(unittest.TestCase):

    def test_revert_block_changes(self):
        sub = Subtitle(None)
        block1 = Block(sub.eventpublisher, 1, Timestamp(), Timestamp(), [])
        sub.insert_block(block1)

        self.assertEqual(block1.id, sub._blocks[0].id)

        block1.id = 99
        self.assertEqual(block1.id, sub._blocks[0].id)

        sub.undo()
        self.assertEqual(1, sub._blocks[0].id)
        self.assertEqual(block1.id, sub._blocks[0].id)

        sub.remove_block(block1)
        self.assertEqual(0, len(sub._blocks))

        sub.undo()
        self.assertEqual(1, len(sub._blocks))
        self.assertEqual(block1, sub._blocks[0])

        sub._blocks[0].id = 5
        self.assertEqual(5, sub._blocks[0].id)

        sub.undo()
        self.assertEqual(1, sub._blocks[0].id)

        sub._blocks[0].id = 5
        sub._blocks[0].id = 6
        sub._blocks[0].id = 7
        sub._blocks[0].add_line('Some text')
        sub._blocks[0].add_line('more!')
        sub._blocks[0].starttime = Timestamp()

        self.assertEqual(7, sub._blocks[0].id)
        self.assertEqual('Some text', sub._blocks[0]._text[0])

        sub.reset()
        with self.assertRaises(IndexError):
            invalid_block = sub._blocks[0]

if __name__ == '__main__':
    unittest.main()