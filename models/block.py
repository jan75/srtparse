from enum import Enum

from models.timestamp import Timestamp


class Block:
    def __init__(self, id: int, starttime: Timestamp, endtime: Timestamp, text: [str]):
        object.__setattr__(self, '_mementos', [])
        object.__setattr__(self, 'id', id)
        object.__setattr__(self, 'starttime', starttime)
        object.__setattr__(self, 'endtime', endtime)
        object.__setattr__(self, '_text', text)

    def __setattr__(self, name, value):
        # identify field
        if name == 'id':
            field = Field.ID
        elif name == 'starttime':
            field = Field.STARTTIME
        elif name == 'endtime':
            field = Field.ENDTIME
        elif name == '_text':
            field = Field.TEXT
        elif name == '_mementos':
            return
        else:
            raise Exception('Invalid field')

        cur_value = None
        if hasattr(self, name):
            cur_value = getattr(self, name)

        if cur_value is not None:
            # store old value in memento to track changes
            memento = BlockFieldMemento(field, cur_value)
            self._mementos.append(memento)

        # write new value to object
        object.__setattr__(self, name, value)

    def __eq__(self, other: 'Block') -> bool:
        return self.starttime == other.starttime and self.endtime == other.endtime

    def __lt__(self, other: 'Block') -> bool:
        return self.starttime < other.starttime and self.endtime < other.endtime

    def __le__(self, other: 'Block') -> bool:
        return self.starttime <= other.starttime and self.endtime <= other.endtime

    def __gt__(self, other: 'Block') -> bool:
        return self.id > other.id

    def __ge__(self, other: 'Block') -> bool:
        return self.id > other.id

    def __str__(self):
        return '{}\n{} --> {}\n{}'.format(self.id, self.starttime, self.endtime, '\n'.join(self._text))

    def __repr__(self):
        return self.__str__()

    def __hash__(self):
        return hash(self.id) + hash(self.starttime) + hash(self.endtime) + hash(self._text)

    def undo(self):
        try:
            memento = self._mementos.pop()
            field = memento.field
            if field == Field.ID:
                object.__setattr__(self, 'id', memento.value)
            elif field == Field.STARTTIME:
                object.__setattr__(self, 'starttime', memento.value)
            elif field == Field.ENDTIME:
                object.__setattr__(self, 'endtime', memento.value)
            elif field == Field.TEXT:
                object.__setattr__(self, '_text', memento.value)
        except IndexError:
            # no more stuff to undo
            return

    def reset(self):
        while self._mementos:
            self.undo()

    def add_line(self, line: str) -> None:
        text = self._text

        # use slice to create copy of list
        text_new = text[:]
        text_new.append(line)
        # call to overwritten __setattr__
        setattr(self, '_text', text_new)


class Field(Enum):
    ID = 0
    STARTTIME = 1
    ENDTIME = 2
    TEXT = 3


class BlockFieldMemento:
    def __init__(self, field: Field, value: any):
        self.field = field
        self.value = value

    def __str__(self) -> str:
        return '{}: {}'.format(self.field, self.value)

    def __repr__(self) -> str:
        return str(self)


class BlockBuilder:
    def __init__(self):
        self.id = None
        self.starttime = None
        self.endtime = None
        self.text = []

    def reset(self) -> 'BlockBuilder':
        self.id = None
        self.starttime = None
        self.endtime = None
        self.text.clear()

        return self

    def build(self) -> Block:
        if self.id and self.starttime and self.endtime:
            return Block(self.id, self.starttime, self.endtime, self.text)
