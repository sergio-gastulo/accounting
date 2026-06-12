"""
Parsers lie here. 
Some parsers import Record and Session from db.model: be careful.
Basic functionality: take user input and return what is documented.
All parsers should raise, and try as much as possible.
"""
from typing import List
from datetime import date, timedelta
import re
from pathlib import Path
from io import StringIO
from dateutil.relativedelta import relativedelta
import dateutil.relativedelta

import pandas as pd
from pandas.api.types import is_datetime64_any_dtype as is_datetime
from pandas.api.types import is_string_dtype, is_numeric_dtype
from sqlalchemy import Select, select, true, text, Engine
from sqlalchemy.sql.elements import ColumnElement

from classes.model import Record, Session, Conversion


DATE_COLUMN_FORMAT = "%Y-%m-%d"

#region ========================== IMPORTANT ===================================

"""
    convention: parse_(whatever)
    argument order: 
        1. expr to parse goes first
        2. any other necessary arg
        3. defaults
    * expr must be provided -- expr = None is forbidden.
    * early exits for right types are allowed, in case these functions are 
    escalated.
    if any variable renaming operation is needed, check prompt as well
    changing vars? 
        * check tests.parser
        * check prompt.py
"""

#endregion =====================================================================


def parse_arithmetic_operation (
        expr : str, 
        lbound: float | int = 0.0
) -> float | int:
    """
    Parses '+6.8 - 4.5' to int | float. Relies on regex to remove any 
    python injection, checks that is non-empty, and evals with no builtins.
    Checks lower bounds too.
    """
    # --- prevent python injection ---
    if re.match(r'.*[a-zA-Z].*', expr):
        raise ValueError(f"Input can't contain words. Got: {expr=}.")
    if len(expr) == 0:
        raise ValueError(f"Empty string.")

    # --- removing '=' from the beginning of the str ---
    if expr[0] in ['+', '=', '-']:
        expr = re.sub('^=', '', expr)
        try:
            value = eval(expr, {"__builtins__": {}})
        except SyntaxError:
            raise ValueError(f"Expression {expr} failed python parsing.")
    # --- assuming a simple float if above fails ---
    else:
        value = float(expr)

    if value < lbound:
        raise ValueError(f"Value {value} must be greater than {lbound=}.")
    return value


def parse_currency(currency : str) -> str:
    """Accepts `str` and returns **UPPERCASE** str. """
    currency = currency.strip().upper()
    if re.match(r'^[A-Z]{3}$', currency):
        return currency

    raise ValueError(f"{currency=} is not a valid currency.")
    


def _get_date_tokens(s : str) -> List[str]:
    """
    Gets date_tokens from string to list for pattern matching.
    Example: '2026-08' changes to '2026 08' but '-5' remains '-5'
    """
    tokens = s.replace("'",'').replace('"','')
    tokens = re.sub(r'([\d ]+)(-)([\d ]+)', r'\1 \3', tokens)
    return tokens.strip().split()


def _handle_int_date(day: int, base: date) -> date:
    if day < 0:
        return base + timedelta(days=day)
    return base.replace(day=day)


def parse_day(day: str, base: date) -> date:
    day = day.replace(' ', '')
    try:
        day = int(day)
    except ValueError:
        day = day.upper()
        try:
            dayexpr = getattr(dateutil.relativedelta, day[:2])
        except AttributeError:
            # handle special string cases like 'yesterday'
            if day[:4] == 'YEST':
                return base + timedelta(days=-1)
            raise ValueError(
                f"String {day} could not be validated as a valid day string."
            )
        else:
            return base + relativedelta(weekday=dayexpr(-1))
    else:
        return _handle_int_date(day, base)


def parse_date(date_input : str | int) -> date:
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
    today = date.today()
    # --- handle int case properly ---
    if isinstance(date_input, int):
        _handle_int_date(date_input, today)

    tokens = _get_date_tokens(date_input)
    match tokens:

        case ['0' | 'today'] | [ ]:
            return today

        case [day]:
            return parse_day(day, today)

        case [month, day]:  
            month, day = map(int, (month, day))
            return today.replace(day=day, month=month)

        case [year, month, day]:
            year, month, day = map(int, (year, month, day))
            # 25 -> 2025, 2025 -> 2025
            year += 2000 if year < 100 else 0
            return date(year=year, month=month, day=day)

        case _ :
            raise ValueError(f"Could not parse: {date_input=}.")


def parse_double_currency(
        raw_input : str, 
        default_currency : str,
        lbound : float = 0.0,
) -> tuple[float, str]:
    """
    Takes str and parses it to (amount, currency).
    Example: '+9.54 usd' -> (9.54, 'USD'). Relies on their respective 
    2 different parsers. 
    """
    tokens = raw_input.strip().split()
    if not tokens:
        raise ValueError("Empty query.")

    try:
        # --- check if last splitted string is currency ---
        currency    =   parse_currency(tokens[-1])
        raw_op      =   ' '.join(tokens[:-1])  
    except ValueError:
        # --- if above fails, more likely it was a single arith op ---
        currency    =   parse_currency(default_currency)
        raw_op      =   ' '.join(tokens)
    amount = parse_arithmetic_operation(raw_op, lbound)
    return amount, currency
    

def parse_period(
        period : str | int | pd.Period | None, 
        default_period : pd.Period,
    ) -> pd.Period:
    """
    Parses string and return valid pandas.Period class.
    """
    # --- type checking for default period---
    if not isinstance(default_period, pd.Period):
        raise TypeError(f"Invalid {default_period=}.")

    # --- handle types properly ---
    if isinstance(period, int):
        return default_period + period
    if period is None:
        return default_period
    if isinstance(period, pd.Period):
        return period
    if not isinstance(period, str):
        raise TypeError(f"Period must be str, int, Period or None.")

    # --- stripping and checking if null before passing to pandas ---
    # --- pandas can't handle empty strings ---
    if not (period := period.strip()):
        return default_period
    
    # --- handle year-month with no spaces: rely on pandas parser ---
    try: 
        return pd.Period(period, freq='M')
    except (ValueError, TypeError):
        pass

    # --- handle tokenized string ---
    tokens = period.split()
    match tokens:
        case [increment] :
            return default_period + int(increment)

        case [year, "/" | "-", month] | [year, month]:
            year, month = map(int, (year, month))
            year += 2000 if year < 100 else 0
            return pd.Period(year=year, month=month, freq='M')

        case [ ]:
            return default_period
        case _ :
            raise ValueError(f"Could not parse {period=}.")


def core_semantic_filter_parse(
        semantic_filter : str
) -> tuple[ColumnElement[bool]]:
    """
    Meant to parse a single stmt into a semantically-valid SQL query.
    **IMPORTANT** the query is not necessarily valid, it can't be known until 
    runtime. 
    """
    match semantic_filter.split():

        # ---------------------------- id filtering ----------------------------
        case ["id", "range", id_, bounds]:
            id_, bounds = map(int, [id_, bounds])
            return Record.id.between(id_ - bounds, id_ + bounds)

        case ["id", ("between" | "b"), id_1, "and", id_2]:
            id_1, id_2 = map(int, [id_1, id_2])
            return Record.id.between(id_1, id_2)


        # --------------------------- amount filters ---------------------------
        case (
			    [("amount" | "am"), ("between" | "b"), lbound, "and", upper_bound] | 
			    [lbound, ("<" | "<=") , "amount", ("<" | "<="), upper_bound] | 
			    [upper_bound, (">=" | ">"), "amount", (">=" | ">"), lbound]
			):
            lbound, upper_bound = map(float, [lbound, upper_bound])
            return Record.amount.between(lbound, upper_bound)

        case (
            [lbound, "<=" | "<", ("amount" | "a")] | 
            [("amount" | "a"), ">=" | ">", lbound]
        ):
            lbound = float(lbound)
            return Record.amount >= lbound
        
        case (
            [upper_bound, ">=" | ">", ("amount" | "a")] | 
            [("amount" | "a"), "<=" | "<", upper_bound]
        ): 
            upper_bound = float(upper_bound)
            return Record.amount <= upper_bound

        # ---------------------------- date filters ----------------------------
        case ["date", "like", *date_wildcard]:
            date_ = ' '.join(date_wildcard).replace('"','').replace("'","")
            return Record.date.like(date_)
        
        case ["date", "=" | "equal", *date_]:
            date_str = ' '.join(date_)
            return Record.date == parse_date(date_str).strftime(DATE_COLUMN_FORMAT)
        
        case ["date", ("r" | "regex" | "regexp"), date_regex]:
            return Record.date.regexp_match(date_regex)

        # -------------------------- category filters --------------------------
        case ["category" | "cat", "like", category_wildcard]:
            category_wildcard = (category_wildcard
                                 .replace('\'', '')
                                 .replace('\"', '')
                                 .upper()
                                )
            return Record.category.like(category_wildcard)
        
        case ["category" | "cat", ("r" | "regex" | "regexp"), category_]:
            return Record.category.regexp_match(category_)
        
        case ["category" | "cat", category_]:
            category_ = category_.replace('\'', '').replace('\"', '').upper()
            return Record.category == category_
        
        # --------------------------- currency match ---------------------------
        case (
            [ "currency" | "cur" | "curr", "=", currency_ ] |
            [ "currency" | "cur" | "curr", currency_]
        ):
            currency_ = currency_.replace("'", "").replace('"', '').upper()
            return Record.currency == currency_

        # ------------------------- description match -------------------------
        case [ "description" | "desc", "like", *wildcard]:
            if len(wildcard) == 0:
                raise ValueError("Invalid description filter.")
            wildcard = ' '.join(wildcard)
            return Record.description.like(wildcard)
        
        case [ "description" | "desc", "=" | "equal", *description_str]:
            if len(description_str) == 0 :
                raise ValueError("Invalid description comparison.")
            description_str = ' '.join(description_str)
            return Record.description == description_str
        
        case [ "description" | "desc", ('r' | 'regex' | 'regexp'), *description_regex]:
            if len(description_regex) == 0 :
                raise ValueError("Invalid description regex match.")
            description_regex = ' '.join(description_regex)
            return Record.description.regexp_match(description_regex)
        
        # ----------------------------- true match -----------------------------
        case [  ] | [ "true" | "True" ]:
            return true()
        
        # ------------------------ could not parse this ------------------------
        case _:
            raise ValueError(
                f"Invalid input."
                f"Could not parse {semantic_filter=} as a valid semantic filter."
            )


def parse_semantic_filter(
        general_filter : str
)-> Select[tuple[Record]]:
    """
    Runs parse_core_semantic_filter splitted by 'and'. 
    At the moment, no support for other boolean concatenators.
    It allows raw SQL select statement via 'sql: select ...'.
    Prevents update, insert and drop statements from evaluation.
    """
    general_filter = general_filter.strip()
    # --- allow raw sql select ---
    if re.match('^sql: select.*', general_filter, re.IGNORECASE):
        # --- but prevent query concatenation ---
        if re.match('update|insert|drop', general_filter, re.IGNORECASE):
            raise ValueError(f"UPDATE, INSERT and DROP are not allowed.")
        return text(general_filter.replace("sql: ", ""))

    sql_expr_and = [
        core_semantic_filter_parse(stmt) 
        for stmt in general_filter.split('&&')
    ]
    return select(Record).where(*sql_expr_and)


def parse_element_from_dict(
        user_input : str,
        keybinds : dict[str, str]
) -> str:
    """
    Takes key or value from a given dictionary and returns said associated value.
    e.g. keybinds : {"a":"aa", "b":"bb"}, both "aa", "a" evaluate to "aa".
    Raises ValueError if value could not be found.
    """
    if not isinstance(user_input, str):
        raise TypeError(f"Argument {user_input=} is not a valid string.")
    
    # --- check key-value belonging ---
    if user_input in keybinds:
        return keybinds[user_input]
    if user_input in keybinds.values():
        return user_input

    raise ValueError(f"Could not validate {user_input=}.")


def cast_csv_types(
        csv_content : str
) -> pd.DataFrame:
    """
    Converts csv_content to a valid Record-like dataframe.
    """
    df = pd.read_csv(
        StringIO(csv_content), 
        encoding='utf-8',
        skipinitialspace=True
    )
    df.columns = df.columns.str.strip()
    
    type_mapping = {
        "date" :        "datetime64[ns]",
        "amount" :      "float64",
        "currency" :    "str",
        "description" : "str",
        "category" :    "str"
    }
    
    # --- ensure uncorrupted columns before moving on ---
    if not set(df.columns).issubset(type_mapping.keys()):
        raise ValueError("Dataframe columns are not valid.")
    if not isinstance(df.index, pd.RangeIndex):
        raise ValueError("Dataframe contains more columns than expected.")

    # --- type mapping on existent columns ---
    type_cols = {
        key : val 
        for key, val in type_mapping.items() 
        if key in df.columns
    }
    return df.astype(type_cols)


def parse_csv_record(
        path : Path
) -> pd.DataFrame:
    """
    Simple cast_csv_types wrapper. Reads content from path and returns 
    casted dataframe.  
    """
    with open(path, 'r', encoding='utf-8') as file:
        text = file.read() 
    df = cast_csv_types(text)
    return df


def sanitize_df(
        df : pd.DataFrame, 
        category_list : List[str]
    ) -> pd.DataFrame:
    """
    Check that the dataframe is properly santized. Type-checks, and even 
    transforming functions are applied to respective columns.
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError(f"Argument {df=} is not a valid df.")

    check_category = lambda key: key in category_list
    must_exist_columns = {
        "date", "amount", "currency", "description", "category"
    }

    # --------------------- type checking before moving on ---------------------
    errors : List[str] = []
    if not must_exist_columns.issubset(df.columns):
        raise ValueError(f"DataFrame must contain the following columnts: {must_exist_columns}.")
    if is_numeric_dtype(df.amount):
        if not (df.amount > 0).all():
            errors.append("df.amount contains a (or more) negatives values.")
    else:
        errors.append("df.amount is non-numeric.")
    if not is_string_dtype(df.currency):
        errors.append("df.currency is non-string.")
    if not is_string_dtype(df.description):
        errors.append("df.description is non-string.")
    if not df.category.map(check_category).all():
        errors.append(f"df.category contains a category that is not in {category_list}.")
    if not (is_string_dtype(df.date) or is_datetime(df.date)):
        errors.append("df.date is non-string and non-datetime-like.")
    if errors:
        raise ValueError(f"Dataframe's columns failed type-check: {errors}.")

    # -------------------- conversions after checking dtypes --------------------
    df.currency = df.currency.str.upper()
    if is_string_dtype(df.date):
        df.date = pd.to_datetime(df.date)
    # --- datetime uniformization ---
    df.date = df.date.dt.strftime(DATE_COLUMN_FORMAT)
    return df


# TODO : test this whenever possible
def parse_record_from_id(
        id_ : str | int,
        engine : Engine,
        entity : Record | Conversion
) -> Record | Conversion:
    """Takes str | int and returns a record from it."""
    if not isinstance(id_, str | int):
        raise TypeError(f"Argument {id_=} must be String or Numeric type.")
    _id = int(id_)

    with Session(engine) as session:
        entity = session.get(entity, _id)
    if entity is None:
        raise ValueError(f"Can't get entity with {_id=}.")
    return entity