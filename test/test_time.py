import unittest
from modules.timestamp import Timestamp, TimestampBuilder, InvalidTimeException


class MyTestCase(unittest.TestCase):
    def test_time_builder(self):
        time_builder = TimestampBuilder()
        self.assertRaises(InvalidTimeException, time_builder.with_hours, 100)
        self.assertRaises(InvalidTimeException, time_builder.with_hours, -1)
        self.assertRaises(InvalidTimeException, time_builder.with_minutes, -1)
        self.assertRaises(InvalidTimeException, time_builder.with_minutes, 60)
        self.assertRaises(InvalidTimeException, time_builder.with_seconds, -1)
        self.assertRaises(InvalidTimeException, time_builder.with_seconds, 60)
        self.assertRaises(InvalidTimeException, time_builder.with_milliseconds, -1)
        self.assertRaises(InvalidTimeException, time_builder.with_milliseconds, 1000)

        time = TimestampBuilder().with_hours(10).with_minutes(15).with_milliseconds(100).build()
        self.assertEqual(10, time.hours)
        self.assertEqual(15, time.minutes)
        self.assertEqual(0, time.seconds)
        self.assertEqual(100, time.milliseconds)

    def test_time_string_repr(self):
        time = Timestamp()
        time.hours = 1
        time.minutes = 15
        time.seconds = 3
        time.milliseconds = 434
        self.assertEqual('01:15:03.434', str(time))

    def test_comparison(self):
        time_1 = Timestamp()
        time_1.hours = 1
        time_1.minutes = 10
        time_1.seconds = 10
        time_1.milliseconds = 500

        time_2 = Timestamp()
        self.assertTrue(time_1 > time_2)
        self.assertTrue(time_1 >= time_2)
        self.assertFalse(time_1 < time_2)
        self.assertFalse(time_1 <= time_2)

        time_2.hours = 2
        self.assertTrue(time_2 > time_1)

        time_2.hours = 1
        time_2.minutes = 15
        self.assertTrue(time_2 > time_1)



    def test_time_field_addition_subtraction(self):
        time = Timestamp()

        # hours
        time.hours = 1
        self.assertEqual(2, time.add_hours(1).hours)
        self.assertEqual(1, time.add_hours(-1).hours)
        self.assertEqual(0, time.remove_hours(1).hours)
        self.assertEqual(1, time.remove_hours(-1).hours)
        time.hours = 0
        self.assertRaises(InvalidTimeException, time.remove_hours, 1)
        self.assertRaises(InvalidTimeException, time.add_hours, 100)

        # minutes
        self.assertEqual(20, time.add_minutes(20).minutes)
        self.assertEqual(10, time.add_minutes(-10).minutes)
        self.assertEqual(0, time.remove_minutes(10).minutes)
        self.assertEqual(10, time.remove_minutes(-10).minutes)

        # seconds
        self.assertEqual(20, time.add_seconds(20).seconds)
        self.assertEqual(10, time.add_seconds(-10).seconds)
        self.assertEqual(0, time.remove_seconds(10).seconds)
        self.assertEqual(10, time.remove_seconds(-10).seconds)

        # milliseconds
        self.assertEqual(200, time.add_milliseconds(200).milliseconds)
        self.assertEqual(100, time.add_milliseconds(-100).milliseconds)
        self.assertEqual(0, time.remove_milliseconds(100).milliseconds)
        self.assertEqual(100, time.remove_milliseconds(-100).milliseconds)

        # test minute overflow
        time.hours = 1
        time.minutes = 0
        self.assertEqual(0, time.add_minutes(60).minutes)
        self.assertEqual(2, time.hours)
        self.assertEqual(30, time.add_minutes(90).minutes)
        self.assertEqual(3, time.hours)
        self.assertEqual(30, time.add_minutes(180).minutes)
        self.assertEqual(6, time.hours)

        time.hours = 6
        time.minutes = 0
        self.assertEqual(0, time.remove_minutes(60).minutes)
        self.assertEqual(5, time.hours)
        self.assertEqual(30, time.remove_minutes(90).minutes)
        self.assertEqual(3, time.hours)
        self.assertEqual(30, time.remove_minutes(180).minutes)
        self.assertEqual(0, time.hours)

        # test second overflow
        time.minutes = 10
        time.seconds = 0
        self.assertEqual(0, time.add_seconds(60).seconds)
        self.assertEqual(11, time.minutes)
        self.assertEqual(30, time.remove_seconds(150).seconds)
        self.assertEqual(8, time.minutes)
        time.hours = 10
        time.minutes = 59
        time.seconds = 0
        self.assertEqual(30, time.add_seconds(90).seconds)
        self.assertEqual(0, time.minutes)
        self.assertEqual(11, time.hours)

        time.hours = 99
        time.minutes = 59
        time.seconds = 0
        self.assertRaises(InvalidTimeException, time.add_seconds, 60)
        time.hours = 1
        time.inutes = 0
        time.seconds = 0
        self.assertEqual(0, time.remove_seconds(3600).hours)

        # test millisecond overflow
        time.hours = 1
        time.minutes = 10
        time.seconds = 10
        time.milliseconds = 0
        self.assertEqual(0, time.add_milliseconds(1000).milliseconds)
        self.assertEqual(11, time.seconds)
        self.assertEqual(500, time.add_milliseconds(2500).milliseconds)
        self.assertEqual(13, time.seconds)
        self.assertEqual(0, time.remove_milliseconds(3500).milliseconds)
        self.assertEqual(10, time.seconds)
        self.assertEqual(0, time.remove_milliseconds(10000).milliseconds)
        self.assertEqual(0, time.seconds)
        self.assertEqual(500, time.remove_milliseconds(500).milliseconds)
        self.assertEqual(59, time.seconds)
        self.assertEqual(9, time.minutes)

    def test_time_object_addition_subtraction(self):
        time_0 = Timestamp()
        time_1 = Timestamp()
        time_1.hours = 1
        time_1.minutes = 1
        time_1.seconds = 1
        time_1.milliseconds = 1
        time_x = time_0 + time_1
        self.assertEqual(1, time_x.hours)
        self.assertEqual(1, time_x.minutes)
        self.assertEqual(1, time_x.seconds)
        self.assertEqual(1, time_x.milliseconds)

        time_x = time_x - time_1
        self.assertEqual(0, time_x.hours)
        self.assertEqual(0, time_x.minutes)
        self.assertEqual(0, time_x.seconds)
        self.assertEqual(0, time_x.milliseconds)

        time_2 = Timestamp()
        time_2.hours = 1
        time_2.minutes = 15
        time_2.seconds = 10
        time_2.milliseconds = 700

        time_3 = Timestamp()
        time_3.hours = 2
        time_3.minutes = 50
        time_3.seconds = 55
        time_3.milliseconds = 450

        time_x = time_2 + time_3
        self.assertEqual(4, time_x.hours)
        self.assertEqual(6, time_x.minutes)
        self.assertEqual(6, time_x.seconds)
        self.assertEqual(150, time_x.milliseconds)

        time_x = time_3 - time_2
        self.assertEqual(1, time_x.hours)
        self.assertEqual(35, time_x.minutes)
        self.assertEqual(44, time_x.seconds)
        self.assertEqual(750, time_x.milliseconds)

        self.assertRaises(InvalidTimeException, time_2.__sub__, time_3)



if __name__ == '__main__':
    unittest.main()
