import datetime
from pathlib import Path
from io import StringIO

import pandas as pd
from pandas.api.types import (is_numeric_dtype,
                              is_string_dtype,
                              is_datetime64_any_dtype,
                              is_integer_dtype,)

from pkg.classes.model import Record


DATE_YEAR_FORMAT = '%B %dth, %Y'
DATE_MONTH_FORMAT = '%B %dth'
DATE_DAY_FORMAT = "%d"
MAX_LONG_STR_DISPLAY = 100
ON_ERROR_CONCATENATOR = "\n\t"


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


def castto_record(
        df: pd.DataFrame
) -> pd.DataFrame:
    """Casts `df` to a valid Record DataFrame type."""
    
    type_mapping = {
        Record.date.key: "datetime64[ns]",
        Record.amount.key: "float64",
        Record.currency.key: "str",
        Record.description.key: "str",
        Record.category.key: "str"
    }
    # avoid KeyError
    type_cols = {key: val
                 for key, val in type_mapping.items()
                 if key in df.columns}
    return df.astype(type_cols)


def open_recorddf(
        arg: Path | str
) -> pd.DataFrame:
    """
    Converts `arg` into a casted-to-record DataFrame.

    Arguments
    ---------
    arg
        If `str`, it's passed with a StringIO wrapper.
    """

    if isinstance(arg, str):
        arg = StringIO(arg)

    df = pd.read_csv(arg,
                    encoding='utf-8',
                    skipinitialspace=True)
    df.columns = df.columns.str.strip()
    return castto_record(df)


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
    is_default = (df.index.dtype == int and 
                  not df.index.name)
    df = df.to_markdown(index = not is_default, 
                        tablefmt="outline")

    # provide a header if passed
    if header:
        line = df.partition('\n')[0]
        df = (f"{line}\n"
              f"{header}\n"
              f"{df}")
    print(df)