import re
from enum import Enum

from modules.block import Block, BlockBuilder, BlockField, EventType, BlockAddedEvent, BlockRemovedEvent
from modules.eventpublisher import BlockEventPublisher
from modules.timestamp import TimestampBuilder


class CCPattern:
    """
    Holds information about closed caption patterns to match and, if found, which match groups to replace or remove.

    :param pattern: Pattern to look for
    :param replace_groups: Which groups to replace if found
    :param replace_with: What to replace the groups with, None removes the group from the string
    """
    def __init__(self, pattern: re.Pattern, replace_groups: [int], replace_with: [str] = None):

        self.pattern = pattern
        self.replace_groups = replace_groups
        self.replace_with = replace_with


class Subtitle:
    """
    Subtitle class is the entry point to a subtitle file. Requires the path to a subtitle file, which can then
    be parsed using :meth:`parse_file`. A subtitle object holds multiple blocks in order, for more details refer to
    :class:`~modules.block.Block`.

    Upon initialisation creates a :class:`~modules.eventpublisher.BlockEventPublisher` object which is passed to blocks
    upon creation. Adds itself as a subscriber. This object is used to communicated changes from individual blocks to
    this subtitle instance.

    :param path: Path to subtitle file
    """
    pattern_empty = re.compile(r'\s*')
    pattern_id = re.compile(r'[0-9]+\n', re.MULTILINE)
    pattern_time = re.compile(
        r'([0-9]{2}:[0-9]{2}:[0-9]{2}[,.][0-9]{3}) --> ([0-9]{2}:[0-9]{2}:[0-9]{2}[,.][0-9]{3})\s*')
    pattern_time_detail = re.compile(r'([0-9]{2}):([0-9]{2}):([0-9]{2})[.,]([0-9]{3})')

    cc_patterns = [
        CCPattern(re.compile(r'^\(.*\)'), [0]),
        CCPattern(re.compile(r'^[A-Z0-9\s.,:;!?-]$'), [0]),
        CCPattern(re.compile(r'^([A-Z0-9]{3,}:?\s*)'), [1])
    ]

    def __init__(self, path: str):
        self.eventpublisher = BlockEventPublisher()
        self.eventpublisher.add_subscriber(self.handle_event)

        self.path = path
        self._blocks = []
        self._mementos = []

    def __str__(self):
        return '\n\n'.join([str(block) for block in self._blocks])

    def handle_event(self, event) -> None:
        self._mementos.append(event)

    def undo(self):
        try:
            event = self._mementos.pop()
            if event.event_type == EventType.BLOCK_UPDATED:
                field = event.field
                if field == BlockField.ID:
                    object.__setattr__(event.block, 'id', event.old_value)
                elif field == BlockField.STARTTIME:
                    object.__setattr__(event.block, 'starttime', event.old_value)
                elif field == BlockField.ENDTIME:
                    object.__setattr__(event.block, 'endtime', event.old_value)
                elif field == BlockField.TEXT:
                    object.__setattr__(event.block, '_text', event.old_value)
            elif event.event_type == EventType.BLOCK_ADDED:
                self._blocks.remove(event.block)
            elif event.event_type == EventType.BLOCK_DELETED:
                self._blocks.append(event.block)
        except IndexError:
            # no more stuff to undo
            return

    def reset(self):
        while self._mementos:
            self.undo()

    def insert_block(self, block: 'Block') -> bool:
        if block in self._blocks:
            print('Block already exists: \n{}'.format(block))
            return False

        self._blocks.append(block)

        event = BlockAddedEvent(block)
        self.eventpublisher.publish(event)

        return True

    def remove_block(self, block: 'Block') -> None:
        if block in self._blocks:
            self._blocks.remove(block)

            event = BlockRemovedEvent(block)
            self.eventpublisher.publish(event)

    def validate(self, try_fix: bool = False) -> ['ValidationError']:
        self._blocks.sort()

        errors = []
        last_starttime = None
        last_endtime = None
        for (counter, block) in enumerate(self._blocks):
            error = ValidationError(block)
            # validate availability of fields
            if not block.id:
                error.errors.append('missing id')

            if not block.starttime:
                error.errors.append('missing starttime')

            if not block.endtime:
                error.errors.append('missing starttime')

            if not block.text:
                error.errors.append('missing text')

            # valid id
            if block.id != counter + 1:
                error.errors.append('wrong id')
                if try_fix:
                    block.id = counter + 1

            # times in itself
            if block.starttime >= block.endtime:
                error.errors.append('starttime >= endtime')

            # overlaps
            if last_starttime:
                if block.starttime <= last_starttime:
                    error.errors.append('starttime <= last_starttime')
                if block.endtime <= last_starttime:
                    error.errors.append('endtime <= last_starttime')
            if last_endtime:
                if block.starttime <= last_endtime:
                    error.errors.append('starttime <= last_endtime')
                if block.endtime <= last_endtime:
                    error.errors.append('endtime <= last_endtime')

            # end of iteration tasks
            last_starttime = block.starttime
            last_endtime = block.endtime
            if len(error.errors) > 0:
                errors.append(error)

    def parse_file(self) -> None:
        """
        Parses a SubRip subtitle file (usually \\*.srt)

        SRT files (SubRip) should adhere to the following pattern:

        - Contains blocks of 1 subtitle each
        - Blocks should be separated by empty lines
        - 1 block contains the following information:

            - A line with an (incrementing) number, in this program called ID
            - A line with two timestamps declaring the start and end time when the subtitle should be shown
            - One or more lines of text

        The parser additionally skips empty lines at the beginning and end of the file.
        """
        with open(self.path, 'r', encoding='utf-8-sig') as open_file:
            lines = open_file.readlines()

        last_line = len(lines) - 1
        prev_state = None
        for (index, line) in enumerate(lines):
            line_parsed, line_type = self.parse_line(line)

            # New files or empty lines must be followed by either another empty line or an ID line
            if prev_state is None or prev_state == LineType.EMPTY:
                if line_type == LineType.EMPTY:
                    prev_state = LineType.EMPTY
                    continue
                elif line_type == LineType.ID:
                    block_builder = BlockBuilder()
                    block_builder.id = line_parsed

                    prev_state = LineType.ID
                    continue
                else:
                    raise ParseException('Invalid start of file')

            # after the ID the next line must contain the timestamps
            if prev_state == LineType.ID:
                if line_type == LineType.TIME:
                    block_builder.starttime = line_parsed[0]
                    block_builder.endtime = line_parsed[1]

                    prev_state = LineType.TIME
                    continue
                else:
                    raise ParseException('ID line not followed by time line: {}'.format(index))

            # after the timestamps the next line must contain text
            if prev_state == LineType.TIME:
                if line_type == LineType.TEXT:
                    block_builder.text.append(line_parsed)

                    prev_state = LineType.TEXT
                    continue
                else:
                    raise ParseException('Time line not followed by text line: {}'.format(index))

            # after a line of text the next line must contain text or nothing
            if prev_state == LineType.TEXT:
                if line_type == LineType.TEXT:
                    block_builder.text.append(line_parsed)

                    prev_state = LineType.TEXT

                    if index == last_line:
                        if not self.insert_block(block_builder.build(self.eventpublisher)):
                            raise ParseException('Duplicate id in block with id {}'.format(block_builder.id))

                    continue
                elif line_type == LineType.EMPTY:
                    if not self.insert_block(block_builder.build(self.eventpublisher)):
                        raise ParseException('Duplicate id in block with id {}'.format(block_builder.id))
                    # self.blocks.append(block)

                    prev_state = LineType.EMPTY
                    continue
                elif line_type == LineType.ID:
                    raise ParseException('Missing space between blocks: {}'.format(index))
                else:
                    raise ParseException('Text line not followed by further text line or empty line: {}'.format(index))

    def parse_line(self, line: str) -> ('', 'LineType'):
        """
        Parse a line and see what type of line it is as well as return a matching object.

        For example a line containing time information returns two TimeStamp objects as well as State.TIME

        :param line: Line to parse
        :return: parsed object(s), type of parsed line
        """
        if self.pattern_empty.fullmatch(line):
            return None, LineType.EMPTY

        if self.pattern_id.fullmatch(line):
            return int(line), LineType.ID

        re_timestamps = self.pattern_time.fullmatch(line)
        if re_timestamps:
            re_starttime = self.pattern_time_detail.fullmatch(re_timestamps.group(1))
            starttime = TimestampBuilder() \
                .with_hours(int(re_starttime.group(1))) \
                .with_minutes(int(re_starttime.group(2))) \
                .with_seconds(int(re_starttime.group(3))) \
                .with_milliseconds(int(re_starttime.group(4))) \
                .build()

            re_endtime = self.pattern_time_detail.fullmatch(re_timestamps.group(2))
            endtime = TimestampBuilder() \
                .with_hours(int(re_endtime.group(1))) \
                .with_minutes(int(re_endtime.group(2))) \
                .with_seconds(int(re_endtime.group(3))) \
                .with_milliseconds(int(re_endtime.group(4))) \
                .build()

            return (starttime, endtime), LineType.TIME

        return str.replace(line, '\n', ''), LineType.TEXT


class ValidationError:
    def __init__(self, block: 'Block'):
        self.block = block
        self.errors = []


class ParseException(Exception):
    def __init__(self, message: str):
        self.message = message


class InvalidDataException(Exception):
    def __init__(self, message: str, blocks: ['Block']):
        self.message = message
        self.blocks = blocks


class LineType(Enum):
    ID = 0
    TIME = 1
    TEXT = 2
    EMPTY = 3
