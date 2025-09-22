import re
from datetime import date, timedelta
from datetime import datetime as dt
from pandas import Period
from random import choice
from typing import List
from pathlib import Path
import pandas as pd 
from io import StringIO

from sqlalchemy.sql import selectable
from sqlalchemy import select

from ..db.model import Record


# convention: parse_usage (obj : str) -> obj
# should only contain raises and returns

def parse_arithmetic_operation (
        expr : str | None = None, 
        lower_bound: float = 0.0,
        quiet : bool = False
) -> float | int:

    if expr[0] in ['+', '=']:
        if not quiet:
            print("Parsing double operation.")
        if re.match(r'\w', expr):
            raise SyntaxError(f"Input can't contain words. Got: '{expr}'")
        else:
            value = eval(expr[1:], {"__builtins__": {}}) # removing '+', '=' from the beginning of the str
    else:
        print(f"Input '{expr}' does not match an arithmetic operation. Will assume double.")
        value = float(expr)

    if value < lower_bound:
        raise ValueError(f"'{value}' must be >= '{lower_bound}'")

    return value


def parse_currency(currency : str) -> str:
    if re.match(r'^[a-zA-Z]{3}$', string=currency):
        return currency.upper()
    else:
        raise ValueError(f"'{currency}' is not a valid currency.")
    

def parse_date(date_str : str) -> date:
    today = date.today()
    date_str = date_str.strip()

    if date_str == '0' or not date_str:
        return today
    
    # +5, -8, ...
    elif re.match(r'^[+-]\d{1,}$', date_str):
        print("Basic day-arithmetic chosen.")
        return today + timedelta(days=int(date_str))
    
    # 10, 99, ... 
    # this will fail when match > 31, 30, ... 
    # depending on the month
    elif re.match(r'^\d{1,2}$', date_str):
        print("current year - current month - day")
        return today.replace(day=int(date_str)) 
    
    # 10 8, 12 31, ...
    elif re.match(r'^\d{1,2} \d{1,2}$', date_str):
        print("current year - month - day")
        day, month = map(int, date_str.split())
        return today.replace(day=day, month=month) 
    
    for fmt in ("%Y %m %d", "%y %m %d"):
        try:
            return dt.strptime(date_str, fmt).date()
        except ValueError:
            pass
    
    raise SyntaxError(f"'{date_str}' can't be parsed as a valid date string.")


def parse_double_currency(double_currency_str : str, lower_bound : float = 0.0) -> tuple[float, str]:
    try:
        operation_str, currency_str = re.match(r'(.*)(\w{3})$', double_currency_str).groups()
        operation = parse_arithmetic_operation(operation_str, lower_bound)
        currency = parse_currency(currency_str)
        return operation, currency
    except:
        raise SyntaxError(f"'{double_currency_str}' could not be parsed as a valid operation, currency pair.")
    

def parse_period(period_str : str | None, default_period : Period) -> Period:

    if period_str == '0' or not period_str:
        return default_period

    elif re.match(r'^\d{1,}$',period_str):
        return Period(year=default_period.year, month=int(period_str), freq='M')

    year, _separator, month = re.match(r'^(\d{2}|\d{4})([\s\-\/])(\d{1,2})$', string=period_str).groups()
    year, month = map(int, (year, month))
    year += 2000 if year < 100 else 0
    
    return Period(year=year, month=month, freq='M')


def parse_category(category_dict : dict[str, str], category_str : str | None) -> str:
    
    if not category_str:
        print("Random category.")
        return choice(tuple(category_dict))

    elif category_str.upper() in category_dict:
        return category_str.upper()

    raise KeyError(f"'{category_str}' is not part of 'category_dictionary'.")


# ---------------------------------------------------
# cases this should handle
#    - 'amount between 10, 25'
#    - 'date [date_wildcard | datetimeobject | regex]'
#    - 'category comida-salida'
#    - 'currency eur'
#    - 'description like "wildcard"'
#    - 'id = 123'
# ---------------------------------------------------
def parse_semantic_filter(
        semantic_filter : str
) -> selectable.Select:
    
    match semantic_filter.split():

        # amount filters
        case [("amount" | "am"), ("between" | "b"), lower_bound, upper_bound]:
            print("Amount between a, b.")
            lower_bound, upper_bound = map(float, [lower_bound, upper_bound])
            return select(Record).where(Record.amount.between(lower_bound, upper_bound))

        # dates filters
        case ["date", "like", date_wildcard] | ["date", date_wildcard]:
            print("Date wildcard.")
            return select(Record).where(Record.date.like(date_wildcard))
        
        case ["date", "=", date_]:
            print("Date wildcard.")
            return select(Record).where(Record.date == date_)
        
        case ["date", date_regex, ("r" | "regex" | "regexp")]:
            print("Date regex match.")
            return select(Record).where(Record.date.regexp_match(date_regex))

        # category filters
        case [("category" | "cat"), category_]:
            return select(Record).where(Record.category == category_.upper())
        
        case [("category" | "cat"), category_, ("r" | "regex" | "regexp") ]:
            return select(Record).where(Record.category.regexp_match(category_.upper()))
        
        # currency match
        case [("currency" | "cur"), currency_]:
            return select(Record).where(Record.currency == currency_.upper())

        # description match
        case [("description" | "desc"), "like", wildcard]:
            return select(Record).where(Record.description.like(wildcard))
        
        case [("description" | "desc"), "=", description_str]:
            return select(Record).where(Record.description == description_str)
        
        # empty semantic_filter
        # no filter attributed to semantic_filter
        case [  ]:
            return select(Record)
        
        case _:
            raise SyntaxError(f"Invalid Syntax. Could not parse '{semantic_filter}' as a valid semantic filter.")


# -------------------------------------------------
# this function aims to take a single int | str
# and transforms input into an element of the list
# -------------------------------------------------
def parse_valid_element_list(
        column_input : str | int,
        list_to_validate : List[str],
        keybinds : dict[str, str]
) -> str:

    # using keybinds or actual column
    if isinstance(column_input, str):
        if column_input in keybinds:
            return keybinds[column_input]
        if column_input in list_to_validate:
            return column_input
        else:
            raise KeyError(f"Could not parse '{column_input}' as a valid column.")
    
    # using index position
    elif isinstance(column_input, int):
        if 0 <= column_input < len(list_to_validate):
            return list_to_validate[column_input]
        else:
            raise ValueError(f"'{column_input}' can't be that large.")

    raise SyntaxError(f"Could not parse '{column_input}' as a valid column.")



def parse_csv_record(
        path : Path
) -> pd.DataFrame:
    
    with open(path, 'r') as file:
        text = file.read()
    _, csv_content = text.split("# Now add your records in CSV format:", 1)
    
    df = pd.read_csv(StringIO(csv_content))
    df.columns = df.columns.str.strip()

    type_map = {
        "date" : "datetime64[ns]",
        "amount" : "str",
        "currency" : "str",
        "description" : "str",
        "category" : "str"
    }

    type_dict = {key : val for key, val in type_map.items() if key in df.columns}
    df = df.astype(type_dict)
    if "date" in df.columns:
        df["date"] = df["date"].dt.date

    def cleaner(string : str) -> float | int:
        op = "=" + string if "=" not in string else string 
        return parse_arithmetic_operation(op, quiet=True)
    df.amount = df.amount.map(cleaner)
    
    return df