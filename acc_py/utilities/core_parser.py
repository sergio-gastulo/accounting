import re
from datetime import date, timedelta
from pandas import Period
from typing import List
from pathlib import Path
import pandas as pd 
from io import StringIO

from sqlalchemy.sql import selectable
from sqlalchemy import select, true, text
from sqlalchemy.sql.elements import BinaryExpression, TextClause

from db.model import Record


# convention: parse_usage (obj : str) -> obj
# should only contain raises and returns

DATE_COLUMN_FORMAT = "%Y-%m-%d"


def parse_arithmetic_operation (
        expr : str | None = None, 
        lower_bound: float | int = 0.0
) -> float | int:
    
    if re.match(r'.*[a-zA-Z].*', expr):
        raise SyntaxError(f"Input can't contain words. Got: {expr=}")

    if len(expr) == 0:
        raise SyntaxError(f"Empty string.")

    if expr[0] in ['+', '=', '-']:
        # removing '=' from the beginning of the str
        expr = re.sub('^=', '', expr)
        value = eval(expr, {"__builtins__": {}}) 
    else:
        # assuming a simple float
        value = float(expr)
    
    if value < lower_bound:
        raise ValueError(f"{value=} must be >= {lower_bound=}.")

    return value


def parse_currency(currency : str) -> str:
    """Accepts str and returns 3 digit upper case str. """
    currency = currency.strip().upper()
    if re.match(r'^[A-Z]{3}$', currency):
        return currency.upper()

    raise ValueError(f"{currency=} is not a valid currency.")
    

def parse_date(date_input : str | int) -> date:
    
    today = date.today()

    if isinstance(date_input, int):
        if date_input <= 0:
            return today + timedelta(days=date_input)
        return today.replace(day=date_input)

    tokens = (date_input
              .strip()
              .replace("-"," ")
              .replace('\'', '')
              .replace('"','')
              .split()
    )
    match tokens:

        case ['0' | 'today'] | [ ]:
            return today

        case [day]:
            day = int(day)
            if day < 0:
                return today + timedelta(days=day)
            return today.replace(day=day)

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
        default_currency : str,
        raw_input : str, 
        lower_bound : float = 0.0,
) -> tuple[float, str]:
    tokens = raw_input.strip().split()
    if not tokens:
        raise SyntaxError("Empty query.")

    try: 
        currency = parse_currency(tokens[-1])
        raw_op = ' '.join(tokens[:-1])  
    except ValueError:
        currency = parse_currency(default_currency)
        raw_op = ' '.join(tokens)
    amount = parse_arithmetic_operation(raw_op, lower_bound)
    return amount, currency
    

def parse_period(
        period : str | int | pd.Period | None, 
        default_period : Period,
    ) -> Period:

    if not isinstance(default_period, Period):
        raise TypeError(f"Invalid {default_period=}.")

    if isinstance(period, int):
        return default_period + period
    
    if period is None:
        return default_period
    
    if isinstance(period, Period):
        return period

    if not isinstance(period, str):
        raise TypeError(f"Period must be str, int, Period or None.")

    if not (period := period.strip()):
        return default_period
    
    # handle year-month with no spaces
    try: 
        return Period(period, freq='M')
    except (ValueError, TypeError):
        pass

    tokens = period.split()
    match tokens:
        case [increment] :
            return default_period + int(increment)

        case [year, "/" | "-", month] | [year, month]:
            year, month = map(int, (year, month))
            year += 2000 if year < 100 else 0
            return Period(year=year, month=month, freq='M')

        case [ ]:
            return default_period
        case _ :
            raise ValueError(f"Could not parse {period=}.")


def core_semantic_filter_parse(
        semantic_filter : str
) -> BinaryExpression[bool]:
    
    match semantic_filter.split():

        # id filter
        case ["id", "range", id_, bounds]:
            id_, bounds = map(int, [id_, bounds])
            return Record.id.between(id_ - bounds, id_ + bounds)

        case ["id", ("between" | "b"), id_1, "and", id_2]:
            id_1, id_2 = map(int, [id_1, id_2])
            return Record.id.between(id_1, id_2)


        # amount filters
        case (
			    [("amount" | "am"), ("between" | "b"), lower_bound, "and", upper_bound] | 
			    [lower_bound, ("<" | "<=") , "amount", ("<" | "<="), upper_bound] | 
			    [upper_bound, (">=" | ">"), "amount", (">=" | ">"), lower_bound]
			):
            lower_bound, upper_bound = map(float, [lower_bound, upper_bound])
            return Record.amount.between(lower_bound, upper_bound)

        case (
            [lower_bound, "<=" | "<", ("amount" | "a")] | 
            [("amount" | "a"), ">=" | ">", lower_bound]
        ):
            lower_bound = float(lower_bound)
            return Record.amount >= lower_bound
        
        case (
            [upper_bound, ">=" | ">", ("amount" | "a")] | 
            [("amount" | "a"), "<=" | "<", upper_bound]
        ): 
            upper_bound = float(upper_bound)
            return Record.amount <= upper_bound

        # dates filters
        case ["date", "like", *date_wildcard]:
            date_ = ' '.join(date_wildcard).replace('"','').replace("'","")
            return Record.date.like(date_)
        
        case ["date", "=" | "equal", *date_]:
            date_str = ' '.join(date_)
            return Record.date == parse_date(date_str).strftime(DATE_COLUMN_FORMAT)
        
        case ["date", ("r" | "regex" | "regexp"), date_regex]:
            return Record.date.regexp_match(date_regex)

        # category filters
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
        
        # currency match
        case (
            [ "currency" | "cur" | "curr", "=", currency_ ] |
            [ "currency" | "cur" | "curr", currency_]
        ):
            currency_ = currency_.replace("'", "").replace('"', '').upper()
            return Record.currency == currency_

        # description match
        case [ "description" | "desc", "like", *wildcard]:
            wildcard = ' '.join(wildcard)
            return Record.description.like(wildcard)
        
        case [ "description" | "desc", "=" | "equal", *description_str]:
            description_str = ' '.join(description_str)
            return Record.description == description_str
        
        case [ "description" | "desc", ('r' | 'regex' | 'regexp'), *description_regex]:
            description_regex = ' '.join(description_regex)
            return Record.description.regexp_match(description_regex)
        
        # true match
        case [  ] | [ "true" | "True" ]:
            return true()
        
        case _:
            raise ValueError(
                f"Invalid input."
                f"Could not parse {semantic_filter=} as a valid semantic filter."
            )


def parse_semantic_filter(
        general_filter : str
)-> selectable.Select | TextClause:
    
    general_filter = general_filter.strip()
    if re.match('^sql: select.*', general_filter, re.IGNORECASE):
        # user could concatenate queries.
        if re.match('update|insert|drop', general_filter, re.IGNORECASE):
            raise ValueError(f"UPDATE, INSERT and DROP are not allowed.")
        return text(general_filter.replace("sql: ", ""))

    sql_expr_and = [
        core_semantic_filter_parse(stmt) 
        for stmt in general_filter.split('&&')
    ]
    return select(Record).where(*sql_expr_and)


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
    
    with open(path, 'r', encoding='utf-8') as file:
        text = file.read()
    _, csv_content = text.split("# Now add your records in CSV format:", 1)
    
    df = pd.read_csv(StringIO(csv_content), encoding='utf-8')
    
    df.columns = df.columns.str.strip()
    type_map = {
        "date" : "datetime64[ns]",
        "amount" : "str",           # it is later processed as float, obviously
        "currency" : "str",
        "description" : "str",
        "category" : "str"
    }

    type_dict = {
        key : val 
        for key, val in type_map.items() 
        if key in df.columns
    }
    df = df.astype(type_dict)
    if "date" in df.columns:
        df["date"] = df["date"].dt.date

    def cleaner(string : str) -> float | int:
        op = "=" + string if "=" not in string else string 
        return parse_arithmetic_operation(op, quiet=True)
    df.amount = df.amount.map(cleaner)
    
    return df


def sanitize_df(
        df : pd.DataFrame, 
        category_dict : dict[str, dict[str, str] | str]
    ) -> pd.DataFrame:

    must_exist_columns = {"date", "amount", "currency", "description", "category"}
    assert must_exist_columns.issubset(df.columns), "DataFrame is not complete."
    assert (df.amount > 0).all(), "Dataframe has invalid values on amount column."
    assert df.category.map(lambda key: key in category_dict).all(), "An invalid category has been found."

    if df.date.dtype != 'O':
        df.date = df.date.dt.strftime(DATE_COLUMN_FORMAT)
    df.currency = df.currency.str.upper()

    return df