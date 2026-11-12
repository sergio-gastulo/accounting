from unittest import TestCase
from typing import Callable
import datetime

from pandas import Period

from pkg.coreutils.parser.dates import (parse_date,
                                        parse_day,
                                        parse_month,
                                        parse_period,)
from tests._shared import (TODAY,
                           Patcher)

TEST_MODULE = 'pkg.coreutils.parser.dates'
def patchthis(f: Callable | str, **kwargs) -> Patcher:
    return Patcher(TEST_MODULE, f, **kwargs)


class TestDayParser(TestCase):

    base = datetime.date(2000, 1, 1)

    def test_day_str(self):
        uinput = "monday"
        expected = datetime.date(1999, 12, 27) # monday of *that* week
        self.assertEqual(expected, parse_day(uinput, self.base))

    def test_day_ahead_str(self):
        uinput = "sunday"
        # despite sunday being one day ahead, we are expecting the one 
        # from the previous week
        expected = datetime.date(1999, 12, 26) # prev week sunday 
        self.assertEqual(expected, parse_day(uinput, self.base))

    def test_int_str(self):
        uinput = "   6  "
        expected = datetime.date(2000, 1, 6)
        self.assertEqual(expected, parse_day(uinput, self.base))

    def test_negative_int_str(self):
        uinput = "   - 1  "
        expected = datetime.date(1999, 12, 31)
        self.assertEqual(expected, parse_day(uinput, self.base))

    def test_yesterday(self):
        uinput = "yesterday"
        expected = datetime.date(1999, 12, 31)
        self.assertEqual(expected, parse_day(uinput, self.base))

    def test_unparsable(self):
        bad = [
            'any',
            'foooo bar baaaaz',
            ''
        ]
        for uinput in bad:
            with self.assertRaises(ValueError):
                parse_day(uinput, self.base)


class TestDateParser(TestCase):

    def test_date(self):
        cases = [
            (10,                TODAY.replace(day=10)),
            (0,                 TODAY),
            ('-5',              TODAY + datetime.timedelta(days=-5)),
            (-5,                TODAY + datetime.timedelta(days=-5)),
            ('10',              TODAY.replace(day=10)),
            ('10 08',           TODAY.replace(month=10, day=8)),
            ('  2025-12 31 ',   datetime.date(year=2025, month=12, day=31)), 
            # TODO: fix below
            # ('  2025-12-31 ',   datetime.date(year=2025, month=12, day=31)), 
            ('2025 12 31',      datetime.date(year=2025, month=12, day=31)), 
            ('25 12 31',        datetime.date(year=2025, month=12, day=31)), 
            ('today',           TODAY),
            ('0',               TODAY),
            ('',                TODAY),
            ('10-08',           TODAY.replace(month=10, day=8)),
            ('\'10-08\'',       TODAY.replace(month=10, day=8))
        ]
        for date, expected in cases:
            with self.subTest(date_input=date):
                self.assertEqual(parse_date(date), expected)

    def test_date_err(self):
        cases = [
            99,
            'foo',
            'foo bar baz',
            '99',
            'dasads ads -asd asd asd das'
        ]
        for date_input in cases:
            with self.subTest(date_input=date_input):
                with self.assertRaises(ValueError):
                    parse_date(date_input)

    def test_special_strings(self):
        specials = [
            "yesterday",
            "           yester  ",
            "            monday        ",
            "su"
        ]
        for special in specials:
            with self.subTest(special=special):
                # just ensure parse_day is being called with good arguments
                with patchthis(parse_day) as mocked:
                    parse_date(special)
                day, _ = mocked.call_args.args
                self.assertEqual(day, special.strip())


class TestPeriodParser(TestCase):

    test_default = Period(year=2000, month=7, freq='M')

    def test_period(self):
        cases = [
            (5,                         self.test_default + 5),
            (-6,                        self.test_default - 6),
            (None,                      self.test_default),
            ('2024-12',                 Period(year=2024, month=12, freq='M')),
            ('2024 12',                 Period(year=2024, month=12, freq='M')),
            ('       24 12',            Period(year=2024, month=12, freq='M')),
            ('24 / 12',                 Period(year=2024, month=12, freq='M')),
            ('24 - 12',                 Period(year=2024, month=12, freq='M')),
            (self.test_default,         self.test_default),
            ('       ',                 self.test_default),
            (' 5   ',                   self.test_default + 5),
        ]
        for period, expected_period in cases:
            with self.subTest(period=period):
                self.assertEqual(
                    parse_period(period, self.test_default), 
                    expected_period
                )
    
    def test_period_err(self):
        cases = [
            ('   2022-332   ',  ValueError),
            (print,             TypeError),
            (2.0,               TypeError),
        ]
        for raw_input, err in cases:
            with self.subTest(raw_input=raw_input):
                with self.assertRaises(err):
                    parse_period(raw_input, self.test_default)

    def test_wrong_default_period(self):
        cases = [
            print,
            None,
            'foo',
            9
        ]
        for bad_input in cases:
            with self.subTest(bad_input=bad_input):
                with self.assertRaises(TypeError):
                    parse_period(period='', default_period=bad_input)