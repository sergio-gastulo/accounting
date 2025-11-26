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
from sqlalchemy import select, true, text
from sqlalchemy.sql.elements import BinaryExpression, TextClause

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
    """
    Accepts str and returns 3 digit upper case str. 
    
    :param currency: Description
    :type currency: str
    :return: Description
    :rtype: str
    """
    if re.match(r'^[a-zA-Z]{3}$', string=currency):
        return currency.upper()
    else:
        raise ValueError(f"'{currency}' is not a valid currency.")
    

def parse_date(date_str : str) -> date:
    today = date.today()
    date_str = date_str.strip()

    if date_str in ['0', 'today', '']:
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


def parse_double_currency(
        default_currency : str,
        double_currency_str : str, 
        lower_bound : float = 0.0,
) -> tuple[float, str]:
    try:
        operation_str, currency_str = re.match(r'^([\d\+\-\=\*\/\s]+)(\s[a-zA-Z]{3})?$', double_currency_str).groups()
        operation = parse_arithmetic_operation(operation_str, lower_bound)
        if currency_str:
            currency = parse_currency(currency_str.strip())
        else: 
            currency = parse_currency(default_currency)
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
# ideally:
#     str : exact match | like wildcard | regex
#     int : exact match | range
#     float: range only (continuum)
# ---------------------------------------------------
def core_semantic_filter_parse(
        semantic_filter : str
) -> BinaryExpression[bool]:
    
    match semantic_filter.split():

        # id filter
        case ["id", "range", id_, bounds]:
            id_, bounds = map(int, [id_, bounds])
            print(f"id in [{id_ - bounds}, {id_ + bounds}]")
            return Record.id.between(id_ - bounds, id_ + bounds)

        # amount filters
        case [("amount" | "am"), ("between" | "b"), lower_bound, "and", upper_bound]:
            print("Amount between a and b.")
            lower_bound, upper_bound = map(float, [lower_bound, upper_bound])
            return Record.amount.between(lower_bound, upper_bound)

        # dates filters
        case ["date", "like", date_wildcard]:
            print("Date wildcard.")
            return Record.date.like(date_wildcard)
        
        case ["date", "=", date_]:
            print("Exact date match.")
            return Record.date == date_
        
        case ["date", ("r" | "regex" | "regexp"), date_regex]:
            print("Date regex match.")
            return Record.date.regexp_match(date_regex)

        # category filters
        case [("category" | "cat"), category_]:
            return Record.category == category_.upper()
        
        case [("category" | "cat"), "like", category_wildcard]:
            return Record.category.like(category_wildcard.upper())
        
        case [("category" | "cat"), ("r" | "regex" | "regexp"), category_]:
            return Record.category.regexp_match(category_.upper())
        
        # currency match
        case [("currency" | "cur"), "=", currency_]:
            return Record.currency == currency_.upper()

        # description match
        case [("description" | "desc"), "like", wildcard]:
            return Record.description.like(wildcard)
        
        case [("description" | "desc"), "=", description_str]:
            return Record.description == description_str
        
        case [("description" | "desc"), ('r' | 'regex' | 'regexp'), description_regex]:
            return Record.description.regexp_match(description_regex)
        
        # empty semantic_filter
        # no filter attributed to semantic_filter
        case [  ]:
            return true()
        
        case _:
            raise SyntaxError(f"Invalid Syntax. Could not parse '{semantic_filter}' as a valid semantic filter.")


def parse_semantic_filter(
        general_filter : str
)-> selectable.Select | TextClause:
    
    if re.match('^sql: SELECT', general_filter):
        print(
            f"Warning: this is being parsed as a raw SQL statement.\n"
            f"For safety, only the 'sql: SELECT ...' pattern is allowed."
        )
        return text(general_filter.replace("sql: ", ""))
    
    else:
        binary_sql_expr = [
            core_semantic_filter_parse(stmt) 
            for stmt in general_filter.lower().split('and')
        ]
        return select(Record).where(*binary_sql_expr)


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
        bound = len(list_to_validate)
        if 0 <= column_input < bound:
            return list_to_validate[column_input]
        else:
            raise ValueError(f"'{column_input}' is greater than {bound}.")

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
