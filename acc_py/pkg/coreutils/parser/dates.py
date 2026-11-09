"""
Date related parsers to isolate module development.
"""
import re
from typing import List
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
import dateutil.relativedelta

from pandas import Period


class ParseDateError(Exception):
    pass


def parse_intday(day: int, basedate: date) -> date:
    if day <= 0:
        return basedate + timedelta(day)
    return basedate.replace(day=day)


def parse_day(day: str, basedate: date) -> date:
    """Converts `day` to its `datetime` representation."""
    day = day.replace(' ', '')
    try:
        day = int(day)
    except ValueError:  # this is, day in [MONDAY, TUESDAY, etc...
        day = day.upper()
        try:
            dayexpr = getattr(dateutil.relativedelta, day[:2])
        except AttributeError:
            # handle special string cases like 'yesterday'
            if day[:4] == 'YEST':
                return basedate + timedelta(days=-1)
            raise ParseDateError(
                f"String {day=!r} could not be validated as a valid day string."
            )
        else:
            return basedate + relativedelta(weekday=dayexpr(-1))
    else:
        return parse_intday(day, basedate)


def parse_month(month: str):
    """Converts `month` to its integer representation."""
    try:
        return int(month)
    except ValueError:
        pass
    
    months = ["jan", "feb", "mar", "apr", "may", "jun",
              "jul", "aug", "sep", "oct", "nov", "dec"]
    month = month.lower()[:3]
    try:
        return months.index(month)
    except ValueError:
        # translate error message
        raise ParseDateError(f"Argument '{month=!r}' is not a valid month.")


def get_date_tokens(s : str) -> List[str]:
    """
    Gets date_tokens from string to list for pattern matching.
    Example: '2026-08' changes to '2026 08' but '-5' remains '-5'
    """
    tokens = s.replace("'",'').replace('"','')
    tokens = re.sub(r'([\d ]+)(-)([\d ]+)', r'\1 \3', tokens)
    return tokens.strip().split()


def parse_date(date_input : str | int | date) -> date:
    """
    Parses `date_input` into a valid `datetime.date` object. If it can't be
    parsed, a ValueError is raised.

    Arguments
    ---------
    date_input: str | int
        The argument to be parsed. When `date_input` is `ìnt`, it's passed to 
        _handle_int_date. If it's `str`, the following formats are supported:
        - 'yesterday', 'mo[nday]', 'tu[esday], ...'
        - year[separator]month[separator]day
        - month[separtor]day
        - [+-] day
        - allowed separators: `-`, ` `
    
    Notes
    -----
    - All edgecases can be found in on `tests.parser.TestDateParser`.
    """
    if isinstance(date_input, date):
        return date_input
    
    today = date.today()
    if isinstance(date_input, int):
        return parse_intday(date_input, today)

    tokens = get_date_tokens(date_input)
    match tokens:

        case ['0' | 'today'] | [ ]:
            return today

        case [day]:
            return parse_day(day, today)

        # NOTE: makes no sense 'oct tue', why would you be specifying
        # the name of a day and *the month*? Hence, day is parsed as 
        # a single integer instead of the regular handling of "-1" and 
        # "monday".
        case [month, day]:
            day = int(day)
            month = parse_month(month)
            return today.replace(day=day, month=month)

        case [year, month, day]:
            day = int(day)
            month = parse_month(month)
            year = int(year)
            # 25 -> 2025, 2025 -> 2025
            year += 2000 if year < 100 else 0
            return date(year=year, month=month, day=day)

        case _ :
            raise ParseDateError(f"Could not parse: {date_input=!r}.")



def parse_period(
        period : str | int | Period | None,
        default_period : Period,
    ) -> Period:
    """Parses string and return valid `pandas.Period` class."""

    if not isinstance(default_period, Period):
        raise TypeError(f"Invalid {default_period=}.")

    # handle types properly 
    if isinstance(period, int):
        return default_period + period
    if period is None:
        return default_period
    if isinstance(period, Period):
        return period
    if not isinstance(period, str):
        raise TypeError(f"Period must be str, int, Period or None.")

    # stripping and checking if null before passing to pandas 
    # pandas can't handle empty strings 
    if not (period := period.strip()):
        return default_period
    
    # handle year-month with no spaces: rely on pandas parser 
    try: 
        return Period(period, freq='M')
    except (ValueError, TypeError):
        pass

    # handle tokenized string 
    tokens = period.split()
    match tokens:
        case [increment] :
            return default_period + int(increment)

        case [year, "/" | "-", month] | [year, month]:
            year = int(year)
            month = parse_month(month)
            year += 2000 if year < 100 else 0
            return Period(year=year, month=month, freq='M')

        case [ ]:
            return default_period
        case _ :
            raise ValueError(f"Could not parse {period=}.")