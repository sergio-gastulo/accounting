import datetime
from pathlib import Path

import pandas as pd
from pandas.api.types import (is_numeric_dtype,
                              is_string_dtype,
                              is_datetime64_any_dtype,)

from pkg.classes.model import Record


def is_datetime(s: pd.Series) -> bool:
    """Checks if `s` is an actual datetime Series."""
    if is_datetime64_any_dtype(s):
        return True
    if isinstance(s[0], datetime.date):
        return True
    return False


def has_record_columns(df: pd.DataFrame) -> bool:
    """Check if dataframe contains `Record` columns."""
    for col in df.columns:
        if col not in Record.__table__.c:
            return False
    return True


def isin_category(
        s: pd.Series,
        categorylist: list[str]
) -> bool:
    """Check if `s` contains categories included in `categorylist`."""
    return s.isin(categorylist).all()


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

    # verify
    errors : list[str] = []
    if not has_record_columns(df):
        raise ValueError(f"DataFrame does not contain Record columns only.")

    # sanitation
    if is_numeric_dtype(df[Record.amount.key]):
        if not (df[Record.amount.key] > 0).all():
            errors.append("df.amount contains non-positive values.")
    else:
        errors.append("df.amount is non-numeric.")

    if not is_string_dtype(df.currency):
        errors.append("df.currency is non-string.")
    
    if not is_string_dtype(df.description):
        errors.append("df.description is non-string.")
    
    if not isin_category(df[Record.category.key], category_list):
        errors.append(f"df.category contains a category that is not in {category_list}.")
    
    if not is_datetime(df[Record.date.keys]):
        errors.append("df.date is non-string and non-datetime-like.")
    
    if errors:
        raise ValueError(f"Dataframe's columns failed type-check:"
                         "\n".join(errors))

    # NOTE: is it really necessary to cast df.date do dt.date?
    # NOTE: check sqlalchemy in-memory test
    return df.assign(currency=df[Record.currency.key].str.upper(),
                     date=pd.to_datetime(df.date).dt.date)


def castto_record(
        df: pd.DataFrame
) -> pd.DataFrame:
    """Converts `df` to a valid Record DataFrame."""
    
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
        path: Path
) -> pd.DataFrame:
    """
    Simple cast_csv_types wrapper. Reads content from path and returns 
    casted dataframe.  
    """ 
    df = pd.read_csv(path,
                    encoding='utf-8',
                    skipinitialspace=True)
    df.columns = df.columns.str.strip()
    return castto_record(df)


def pprint_df(
        df: pd.DataFrame,
        header: str | None = None
) -> None:
    """
    Pretty df printer. Prints index only if non-default. 
    """
    
    # apply some styling
    styler = {}
    if 'description' in df.columns and is_string_dtype(df.description):
        # NOTE: add 100 to config
        styler.update({
            'description': lambda df: df['description'].str[:100] 
        })
    if 'date' in df.columns and is_datetime64_any_dtype(df.date):
        years = len(df["date"].dt.year.unique())
        fmt = '%B %dth, %Y' if years > 1 else '%B %dth'
        styler.update({
            'date': lambda df: df['date'].dt.strftime(fmt)
        })
    df = df.assign(**styler)

    # prevent default index from printing
    is_default = (df.index.dtype == int and 
                  df.index.name is None)
    df = df.to_markdown(index = not is_default, 
                        tablefmt="outline")

    # provide a header if necessary
    if header:
        line = df.partition('\n')[0]
        df = (f"{line}\n"
              f"{header}\n"
              f"{df}")
    print(df)