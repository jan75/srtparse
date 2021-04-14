import re
from enum import Enum

from models.block import Block, BlockBuilder
from models.timestamp import TimestampBuilder


class Subtitle:
    pattern_empty = re.compile(r'\s*')
    pattern_id = re.compile(r'[0-9]+\n', re.MULTILINE)
    pattern_time = re.compile(
        r'([0-9]{2}:[0-9]{2}:[0-9]{2}[,.][0-9]{3}) --> ([0-9]{2}:[0-9]{2}:[0-9]{2}[,.][0-9]{3})\s*')
    pattern_time_detail = re.compile(r'([0-9]{2}):([0-9]{2}):([0-9]{2})[.,]([0-9]{3})')

    def __init__(self, path: str):
        self.path = path
        self.blocks = []

    def __str__(self):
        return '\n\n'.join([str(block) for block in self.blocks])

    def validate(self, try_fix: bool = False) -> ['ValidationError']:
        self.blocks.sort()

        errors = []
        last_starttime = None
        last_endtime = None
        for (counter, block) in enumerate(self.blocks):
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

    def insert_block(self, block: 'Block') -> bool:
        if block in self.blocks:
            print('Block already exists: \n{}'.format(block))
            return False

        self.blocks.append(block)
        return True

    def remove_block(self, block: 'Block') -> None:
        self.blocks.remove(block)

    def replace_block(self, old: 'Block', new: 'Block') -> None:
        self.remove_block(old)
        self.insert_block(new)

    def parse_file(self) -> None:
        '''
        Parses a SubRip subtitle file (usually *.srt)

        SRT files (SubRip) should adhere to the following pattern:
        - Contains blocks of 1 subtitle each
        - Blocks should be separated by empty lines
        - 1 block contains the following information:
            - A line with an (incrementing) number, in this program called ID
            - A line with two timestamps declaring the start and end time when the subtitle should be shown
            - One or more lines of text

        The parser additionally skips empty lines at the beginning and end of the file.
        :return: None
        '''
        with open(self.path, 'r', encoding='utf-8-sig') as open_file:
            lines = open_file.readlines()

        last_line = len(lines) - 1
        prev_state = None
        for (index, line) in enumerate(lines):
            line_parsed, line_type = self.parse_line(line)

            # New files or empty lines must be followed by either another empty line or an ID line
            if prev_state is None or prev_state == State.EMPTY:
                if line_type == State.EMPTY:
                    prev_state = State.EMPTY
                    continue
                elif line_type == State.ID:
                    block_builder = BlockBuilder()
                    block_builder.id = line_parsed

                    prev_state = State.ID
                    continue
                else:
                    raise ParseException('Invalid start of file')

            # after the ID the next line must contain the timestamps
            if prev_state == State.ID:
                if line_type == State.TIME:
                    block_builder.starttime = line_parsed[0]
                    block_builder.endtime = line_parsed[1]

                    prev_state = State.TIME
                    continue
                else:
                    raise ParseException('ID line not followed by time line: {}'.format(index))

            # after the timestamps the next line must contain text
            if prev_state == State.TIME:
                if line_type == State.TEXT:
                    block_builder.text.append(line_parsed)

                    prev_state = State.TEXT
                    continue
                else:
                    raise ParseException('Time line not followed by text line: {}'.format(index))

            # after a line of text the next line must contain text or nothing
            if prev_state == State.TEXT:
                if line_type == State.TEXT:
                    block_builder.text.append(line_parsed)

                    prev_state = State.TEXT

                    if index == last_line:
                        if not self.insert_block(block_builder.build()):
                            raise ParseException('Duplicate id in block with id {}'.format(block_builder.id))

                    continue
                elif line_type == State.EMPTY:
                    if not self.insert_block(block_builder.build()):
                        raise ParseException('Duplicate id in block with id {}'.format(block_builder.id))
                    # self.blocks.append(block)

                    prev_state = State.EMPTY
                    continue
                elif line_type == State.ID:
                    raise ParseException('Missing space between blocks: {}'.format(index))
                else:
                    raise ParseException('Text line not followed by further text line or empty line: {}'.format(index))

    def parse_line(self, line: str) -> ('', 'State'):
        if self.pattern_empty.fullmatch(line):
            return None, State.EMPTY

        if self.pattern_id.fullmatch(line):
            return int(line), State.ID

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

            return (starttime, endtime), State.TIME

        return str.replace(line, '\n', ''), State.TEXT


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


class State(Enum):
    ID = 0
    TIME = 1
    TEXT = 2
    EMPTY = 3
