import datetime
from pathlib import Path
from io import StringIO

import pandas as pd
from pandas.api.types import (is_numeric_dtype,
                              is_string_dtype,
                              is_datetime64_any_dtype,
                              is_integer_dtype,)
from sqlalchemy import select

from pkg.classes.context import ctx
from pkg.classes.model import Record, Conversion
from .sql import parse_semantic_query


DATE_YEAR_FORMAT = '%B %dth, %Y'
DATE_MONTH_FORMAT = '%B %dth'
DATE_DAY_FORMAT = "%d"  # TODO: if not months.unique() -> use this.fmt
MAX_LONG_STR_DISPLAY = 100
ON_ERROR_CONCATENATOR = "\n\t"
MAX_LINES_DATABASE = 20
PARSE_DATE_FORMAT = "%Y-%m-%d"
MAX_LINES_DATABASE = 20


def is_datetime(s: pd.Series) -> bool:
    """Checks if `s` is an actual datetime Series."""
    if is_datetime64_any_dtype(s):
        return True
    if isinstance(s[0], datetime.date):
        return True
    return False


def has_recordid(df: pd.DataFrame) -> bool:
    """Checks if `df` contains valid `Record.id` structure.
    
    Notes
    -----
    * This is, `id` is the name of `df.index` or it's in 
    `df.columns` but is `int`-like.
    """
    if df.index.name == Record.id.key:
        if Record.id.key in df.columns:
            return False
        return True if is_integer_dtype(df.index) else False
    if Record.id.key not in df.columns:
        return False
    return is_integer_dtype(df[Record.id.key])


def is_record_like(df: pd.DataFrame) -> bool:
    """
    Checks if `df.columns == Record.columns`.

    Notes
    -----
    * `df` can have `id` index. It can also be a column.
    * `df` muts contain *every* `Record` column.
    """

    columns = sorted(Record.__table__.c.keys())
    if has_recordid(df):
        if df.index.name:
            return columns == sorted(df.columns.tolist() + ["id"])
        return sorted(columns) == sorted(df.columns)
        
    columns.remove(Record.id.key)
    return columns == sorted(df.columns)


def sanitize_df(
        df: pd.DataFrame, 
        category_list: list[str]
) -> pd.DataFrame:
    """
    Verify that `df` can be passed to the database. Every sanatization failure 
    is properly printed.
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError(f"Argument {df=} is not a valid df.")

    # verification
    errors : list[str] = []
    if not is_record_like(df):
        raise ValueError(f"DataFrame does not contain Record columns only.")

    # sanitation
    if is_numeric_dtype(df[Record.amount.key]):
        if not (df[Record.amount.key] > 0).all():
            errors.append("df.amount contains non-positive values.")
    else:
        errors.append("df.amount is non-numeric.")

    if not is_string_dtype(df[Record.currency.key]):
        errors.append("df.currency is non-string.")
    
    if not is_string_dtype(df[Record.description.key]):
        errors.append("df.description is non-string.")

    isin_index = df[Record.category.key].isin(category_list)
    if not isin_index.all():
        notin_category_list = df.loc[~isin_index, Record.category.key]
        errors.append(f"The following entries are not in the specified list\n"
                      f"{notin_category_list}")
    
    if not is_datetime(df[Record.date.key]):
        errors.append("df.date is non-string and non-datetime-like.")
    
    if errors:
        concatenated = ON_ERROR_CONCATENATOR.join(errors)
        raise ValueError(f"Dataframe's columns failed type-check:"
                         f"\n{concatenated}.")

    # NOTE: is it really necessary to cast df.date do dt.date?
    # NOTE: check sqlalchemy in-memory test
    return df.assign(currency=df[Record.currency.key].str.upper(),
                     date=pd.to_datetime(df.date).dt.date)


def pprint_df(
        df: pd.DataFrame,
        header: str | None = None
) -> None:
    """
    Prints `df` after styling.

    Notes
    -----
    * For datetime-like columns, pre-specified date format headers are passed.
    * For str columns, a max threshold for displaying strings is passed
    """
    
    # apply some styling
    styler = {}
    for colname in df.columns:
        c = df.get(colname)

        if is_datetime64_any_dtype(c):
            years = c.dt.year.nunique()
            fmt = DATE_YEAR_FORMAT if years > 1 else DATE_MONTH_FORMAT
            styler.update({colname: c.dt.strftime(fmt)})

        elif is_string_dtype(c):
            styler.update({colname: c.str[:MAX_LONG_STR_DISPLAY]})

    df = df.assign(**styler)
    # prevent default index from printing
    isdefault = df.index.dtype == int and not df.index.name
    df = df.to_markdown(index = not isdefault, 
                        tablefmt="outline")

    # provide a header if passed
    if header:
        line = df.partition('\n')[0]
        df = (f"{line}\n"
              f"{header}\n"
              f"{df}")
    print(df)



def fetch(
        semantic_filter: str | None = None,
        max_lines: int | None = None,
) -> pd.DataFrame:
    """
    Fetches records from database.
    Relies on `parse_semantic_query` to approve parsing.

    Parameters
    ----------
    semantic_filter
        A textual filter expression.
    max_lines
        Maximum number of records to return. Optional.

    Notes
    -----
    - When `semantic_filter` is omitted, it will default to `True`.
    - Results are ordered by `Record.id` (desc) and limited by `max_lines` if 
    provided.
    """

    # query constructor -- by design, there is no prompter for this
    stmt = parse_semantic_query(semantic_filter)
    if max_lines:
        stmt = stmt.limit(max_lines)
    stmt = stmt.order_by(Record.id.desc())
    try:
        df = pd.read_sql(stmt, ctx.engine, Record.id.key,
                         parse_dates={Record.date.key: PARSE_DATE_FORMAT})
    except pd.errors.DatabaseError:
        raise ValueError(f"Database error found. More likely wrong" 
                         f"query: {stmt=!r}.")
    else:
        return df


def read_conversion(
        max_lines: int = MAX_LINES_DATABASE,
) -> None:
    """Simple conversion reader. No support for df return yet."""
    stmt = select(Conversion).limit(max_lines).order_by(Conversion.date.desc())
    df = pd.read_sql(stmt, ctx.engine, Record.id.key)
    pprint_df(df)


def read(
        entity_type: Conversion | Record = Record,
        max_lines: int = MAX_LINES_DATABASE,
        semantic_filter: str | None = None,
):
    """
    Reads records from database.
    Relies on `fetch` to fetch records, and `Conversions.select(true())` on Conversions.

    Parameters
    ------
    max_lines
        Maximum number of records to return. Defaults to 20.
    entity_type
        Which table to fetch objects from. Defaults to `Record`.
    semantic_filter
        A textual filter expression. Supported patterns:
        - str columns: exact match, `LIKE` wildcard, or regex
        - int columns: exact match or numeric range
        - float columns: numeric range only

    Notes
    -
    - When `semantic_filter` is omitted, the user may be prompted interactively.
    - Results are ordered by `Record.id` (desc) and limited by `max_lines`.
    - To use SQL, use `sql: SELECT ...` (only SELECT statements are supported).
    """
    if semantic_filter is None:
        semantic_filter = input("Type your semantic filter: ")

    if entity_type == Record:
        pprint_df(fetch(semantic_filter, max_lines))
    elif entity_type == Conversion:
        read_conversion(max_lines)
    else:
        raise TypeError(f"Invalid {entity_type=}. Must be Conversion or Record.")