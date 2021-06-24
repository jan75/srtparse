from enum import Enum

from modules.eventpublisher import BlockEventPublisher
from modules.timestamp import Timestamp


class Block:
    """
    Class holding a subtitle block. A block consists of an ID (number), starttime and endtime when the subtitle is
    shown and the shown subtitle text (can be multiple lines). A single subtitle which corresponds to a block could
    look like this::

        3
        00:00:12,342 --> 00:00:15,589
        This is the subtitle text. It can
        go over multiple lines.

    Changes to object attributes are sent as event via eventpublisher. See the event classes for more infos:
    :class:`modules.block.BlockUpdatedEvent`, :class:`modules.block.BlockAddedEvent`,
    :class:`modules.block.BlockRemovedEvent`

    :param eventpublisher: Send changes to object attributes as event via this eventpublisher
    :param id: ID (number, index) of block
    :param starttime: Start time when block is shown
    :param endtime: End time until when block is shown
    :param text: List of text lines
    """
    def __init__(self, eventpublisher: BlockEventPublisher, id: int, starttime: Timestamp, endtime: Timestamp,
                 text: [str]):
        object.__setattr__(self, '_eventpublisher', eventpublisher)
        object.__setattr__(self, 'id', id)
        object.__setattr__(self, 'starttime', starttime)
        object.__setattr__(self, 'endtime', endtime)
        object.__setattr__(self, '_text', text)

        self._eventpublisher = eventpublisher

    def __setattr__(self, name, value):
        # identify field
        if name == 'id':
            field = BlockField.ID
        elif name == 'starttime':
            field = BlockField.STARTTIME
        elif name == 'endtime':
            field = BlockField.ENDTIME
        elif name == '_text':
            field = BlockField.TEXT
        elif name == '_eventpublisher':
            return
        else:
            raise Exception('Invalid field')

        cur_value = None
        if hasattr(self, name):
            cur_value = getattr(self, name)

        if cur_value is not None:
            # store old value in memento to track changes
            event = BlockUpdatedEvent(self, field, cur_value, value)
            self._eventpublisher.publish(event)

        # write new value to object
        object.__setattr__(self, name, value)

    def __eq__(self, other: 'Block') -> bool:
        return hash(self) == hash(other)

    def __lt__(self, other: 'Block') -> bool:
        return self.starttime < other.starttime and self.endtime < other.endtime

    def __le__(self, other: 'Block') -> bool:
        return self.starttime <= other.starttime and self.endtime <= other.endtime

    def __gt__(self, other: 'Block') -> bool:
        return self.starttime > other.starttime and self.endtime > other.endtime

    def __ge__(self, other: 'Block') -> bool:
        return self.starttime >= other.starttime and self.endtime >= other.endtime

    def __str__(self):
        return '{}\n{} --> {}\n{}'.format(self.id, self.starttime, self.endtime, '\n'.join(self._text))

    def __repr__(self):
        return self.__str__()

    def __hash__(self):
        return hash(self.id) + hash(self.starttime) + hash(self.endtime) + hash('\n'.join(self._text))

    def add_line(self, line: str) -> None:
        text = self._text

        # use slice to create copy of list
        text_new = text[:]
        text_new.append(line)
        # call to overwritten __setattr__
        setattr(self, '_text', text_new)


class BlockBuilder:
    """
    Builder class to create block objects.
    """
    def __init__(self):
        self.id = None
        self.starttime = None
        self.endtime = None
        self.text = []

    def build(self, eventpublisher: BlockEventPublisher) -> Block:
        if self.id and self.starttime and self.endtime:
            return Block(eventpublisher, self.id, self.starttime, self.endtime, self.text)


class BlockField(Enum):
    ID = 'ID'
    STARTTIME = 'STARTTIME'
    ENDTIME = 'ENDTIME'
    TEXT = 'TEXT'


class EventType(Enum):
    BLOCK_UPDATED = 'BLOCK_UPDATED'
    BLOCK_ADDED = 'BLOCK_ADDED'
    BLOCK_DELETED = 'BLOCK_DELETED'


class BlockEvent:
    def __init__(self, event_type: EventType, block: Block):
        self.event_type = event_type
        self.block = block

    def __str__(self) -> str:
        return '{}: {}'.format(self.event_type, self.block)

    def __repr__(self) -> str:
        return '<BlockEvent {}, {}>'.format(repr(self.event_type), repr(self.block))


class BlockUpdatedEvent(BlockEvent):
    """
    Event class holding information about a changed field in a block.

    :param block: Block which was changed
    :param field: Which field was changed
    :param old_value: Old value of changed field
    :param new_value: New value of changed field
    """
    def __init__(self, block: Block, field: BlockField, old_value: any, new_value: any):
        super().__init__(EventType.BLOCK_UPDATED, block)
        self.field = field
        self.old_value = old_value
        self.new_value = new_value

    def __str__(self) -> str:
        return '{}: {} -> {}'.format(self.field, self.old_value, self.new_value)

    def __repr__(self) -> str:
        return '<BlockUpdatedEvent {}, {}, {}>'.format(repr(self.field), repr(self.old_value), repr(self.new_value))


class BlockAddedEvent(BlockEvent):
    """
    Event class holding information about an added block.

    :param block: Block which was added
    """
    def __init__(self, block: Block):
        super().__init__(EventType.BLOCK_ADDED, block)

    def __str__(self) -> str:
        return str(self.block)

    def __repr__(self) -> str:
        return '<BlockAddedEvent {}>'.format(self.block)


class BlockRemovedEvent(BlockEvent):
    """
    Event class holding information about a removed block.

    :param block: Block which was removed
    """
    def __init__(self, block: Block):
        super().__init__(EventType.BLOCK_DELETED, block)

    def __str__(self) -> str:
        return str(self.block)

    def __repr__(self) -> str:
        return '<BlockDeletedEvent {}>'.format(self.block)