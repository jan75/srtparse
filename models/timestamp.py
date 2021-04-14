import math

class Timestamp:
    def __init__(self):
        """
        Use `TimeBuilder` to create a timestamp object.

        :param hours:
        :param minutes:
        :param seconds:
        :param milliseconds:
        """
        self.hours = 0
        self.minutes = 0
        self.seconds = 0
        self.milliseconds = 0

    def __str__(self):
        return '{}:{}:{}.{}'.format(
            str(self.hours).zfill(2),
            str(self.minutes).zfill(2),
            str(self.seconds).zfill(2),
            str(self.milliseconds).zfill(3)
        )

    def __repr__(self):
        return self.__str__()

    def __add__(self, other: 'Timestamp') -> 'Timestamp':
        time = Timestamp()
        time.hours = self.hours
        time.minutes = self.minutes
        time.seconds = self.seconds
        time.milliseconds = self.milliseconds

        time.add_hours(other.hours)
        time.add_minutes(other.minutes)
        time.add_seconds(other.seconds)
        time.add_milliseconds(other.milliseconds)

        return time

    def __sub__(self, other: 'Timestamp') -> 'Timestamp':
        time = Timestamp()
        time.hours = self.hours
        time.minutes = self.minutes
        time.seconds = self.seconds
        time.milliseconds = self.milliseconds

        time.remove_hours(other.hours)
        time.remove_minutes(other.minutes)
        time.remove_seconds(other.seconds)
        time.remove_milliseconds(other.milliseconds)

        return time

    def __hash__(self):
        return hash(self.hours) + hash(self.minutes) + hash(self.seconds) + hash(self.milliseconds)

    def __eq__(self, other: 'Timestamp') -> bool:
        return hash(self) == hash(other)

    def __lt__(self, other: 'Timestamp') -> bool:
        if self.compare(other) < 0:
            return True

        return False

    def __le__(self, other: 'Timestamp') -> bool:
        if self.compare(other) <= 0:
            return True

        return False

    def __gt__(self, other: 'Timestamp') -> bool:
        if self.compare(other) > 0:
            return True

        return False

    def __ge__(self, other: 'Timestamp') -> bool:
        if self.compare(other) >= 0:
            return True

        return False

    def compare(self, other: 'Timestamp') -> int:
        if self.hours > other.hours:
            return 1
        elif self.hours < other.hours:
            return -1

        if self.minutes > other.minutes:
            return 1
        elif self.minutes < other.minutes:
            return -1

        if self.seconds > other.seconds:
            return 1
        elif self.seconds < other.seconds:
            return -1

        if self.milliseconds > other.milliseconds:
            return 1
        elif self.milliseconds < other.milliseconds:
            return -1

        return 0

    def remove_hours(self, hours: int) -> 'Timestamp':
        return self.add_hours(hours * -1)

    def add_hours(self, hours) -> 'Timestamp':
        if hours == 0:
            return self

        sum = self.hours + hours
        if hours > 0:
            if sum > 99:
                raise InvalidTimeException("Sum of hours > 99")
            else:
                self.hours = sum
                return self
        else:
            if sum < 0:
                raise InvalidTimeException("Sum of hours < 0")
            else:
                self.hours = sum
                return self

    def remove_minutes(self, minutes: int) -> 'Timestamp':
        return self.add_minutes(minutes * -1)

    def add_minutes(self, minutes: int) -> 'Timestamp':
        if minutes == 0:
            return self

        sum = self.minutes + minutes
        if minutes > 0:
            if sum >= 60:
                times = math.floor(sum / 60)
                self.add_hours(times)
            self.minutes = sum % 60
            return self
        else:
            if sum < 0:
                times = math.ceil((sum / 60) * -1)
                self.remove_hours(times)
            self.minutes = sum % 60
            return self

    def remove_seconds(self, seconds: int) -> 'Timestamp':
        return self.add_seconds(seconds * -1)

    def add_seconds(self, seconds: int) -> 'Timestamp':
        if seconds == 0:
            return self

        sum = self.seconds + seconds
        if seconds > 0:
            if sum >= 60:
                times = math.floor(sum / 60)
                self.add_minutes(times)
            self.seconds = sum % 60
            return self
        else:
            if sum < 0:
                times = math.ceil((sum / 60) * -1)
                self.remove_minutes(times)
            self.seconds = sum % 60
            return self

    def remove_milliseconds(self, milliseconds: int) -> 'Timestamp':
        return self.add_milliseconds(milliseconds * -1)

    def add_milliseconds(self, milliseconds: int) -> 'Timestamp':
        if milliseconds == 0:
            return self

        sum = self.milliseconds + milliseconds
        if milliseconds > 0:
            if sum >= 1000:
                times = math.floor(sum / 1000)
                self.add_seconds(times)
            self.milliseconds = sum % 1000
            return self
        else:
            if sum < 0:
                times = math.ceil((sum / 1000) * -1)
                self.remove_seconds(times)
            self.milliseconds = sum % 1000
            return self


class TimestampBuilder:
    def __init__(self):
        self.hours = 0
        self.minutes = 0
        self.seconds = 0
        self.milliseconds = 0

    def reset(self):
        self.hours = 0
        self.minutes = 0
        self.seconds = 0
        self.milliseconds = 0

    def with_hours(self, hours: int) -> 'TimestampBuilder':
        if 0 <= hours <= 99:
            self.hours = hours
            return self
        else:
            raise InvalidTimeException("Invalid value for field 'hours'")

    def with_minutes(self, minutes: int) -> 'TimestampBuilder':
        if 0 <= minutes < 60:
            self.minutes = minutes
            return self
        else:
            raise InvalidTimeException("Invalid value for field 'minutes'")

    def with_seconds(self, seconds: int) -> 'TimestampBuilder':
        if 0 <= seconds < 60:
            self.seconds = seconds
            return self
        else:
            raise InvalidTimeException("Invalid value for field 'seconds'")

    def with_milliseconds(self, milliseconds: int) -> 'TimestampBuilder':
        if 0 <= milliseconds < 1000:
            self.milliseconds = milliseconds
            return self
        else:
            raise InvalidTimeException("Invalid value for field 'milliseconds'")

    def build(self) -> 'Timestamp':
        time = Timestamp()
        time.hours = self.hours
        time.minutes = self.minutes
        time.seconds = self.seconds
        time.milliseconds = self.milliseconds
        return time


class InvalidTimeException(Exception):
    def __init__(self, message: str):
        self.message = message
