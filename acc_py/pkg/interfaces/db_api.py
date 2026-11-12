"""
Database API, allows user to write to DB using sqlalchemy as query wrapper.
Heavily relies on both parser.py and py
"""
from datetime import date
from pathlib import Path
import subprocess

import pandas as pd
from jinja2 import Template
from sqlalchemy import (inspect,
                        select,
                        desc,
                        update,)
from sqlalchemy.orm import Session

from pkg.classes.model import Record, Conversion
from pkg.coreutils.paths import APPLICATION_DIRECTORY
from pkg.coreutils.dataframe import (pprint_df,
                                     open_recorddf,
                                     sanitize_df,)
from pkg.coreutils.colors import fg
from pkg.coreutils.parser.sql import parse_semantic_query
from pkg.coreutils.prompt import (FixedColumnsType,
                                  prompt_date_operation,
                                  prompt_double_currency,
                                  prompt_category_from_keybinds,
                                  prompt_column_value,
                                  prompt_arithmetic_operation,
                                  prompt_currency,
                                  prompt_entity_by_id,)
from pkg.classes.context import ctx


#region ============================ utils  ====================================

RECORD_TABLE_COLUMNS : list[str] = list(inspect(Record).c.keys())
PARSE_DATE_FORMAT = "%Y-%m-%d"

#endregion =====================================================================


def build_record(
        date_: date | None = None,
        amount: int | float | None = None,
        currency: str | None = None,
        operation_str: str | None = None,
        description: str | None = None,
        category: str | None = None
) -> Record:
    """
    Create and write a new Record to the database.
    Omitted arguments are prompted interactively.

    Parameters
    ------
    `date_`
        Operation date.
    amount      
        Operation amount. Ignored if `operation_str` is set.
    currency    
        Currency code (e.g. "USD"). Ignored if `operation_str` is set.
    operation_str 
        Shorthand to set both `amount` and `currency` at once.
    description 
        Brief description of the record.
    category    
        Record category.

    Notes
    -
    Record is committed automatically and printed via `Record.pprint()`.
    """

    # -------------------- Type checking (None are allowed) ----------------
    
    date_ = prompt_date_operation(date_)

    # if amount and currency are not specified, then prompt for pair
    if amount is None and currency is None:
        amount, currency = prompt_double_currency(ctx.default_currency, 
                                                  operation_str)
    else:
        # if any of (amount, currency) is not None, then 
        # individual prompt for each is forced
        amount = prompt_arithmetic_operation(amount)
        currency = prompt_currency(currency)
    
    if description is None:
        # could be empty, one can rely on edit() to change it
        description = input("Type your description: ")

    category = prompt_category_from_keybinds(ctx.keybinds, category)

    # build and return
    return Record(date=date_,
                    amount=amount,
                    currency=currency,
                    description=description,
                    category=category)


def write_record(obj = None) -> None:
    """
    Simple record writer wrapper. Depending on the type of `obj`, it parses and 
    writes without asking for commit.

    Arguments
    -----
    obj
        Record or Record-like expression that will be written to db. 
        - If a `pd.DataFrame`, it will rely on `write_df` and return.
        - If a `pd.Series`, obj is converted to a dict.
        - If a `dict`, obj is converted into a `Record` via Record(**obj).
        - If None, `build_record` is called to construct it interactively.
        - If a Record, it is directly written to database.
    """

    if isinstance(obj, pd.DataFrame):
        write_df(obj)
        return None

    if isinstance(obj, pd.Series):
        obj = obj.to_dict()
    if isinstance(obj, dict):
        obj = Record(**obj)
    if obj is None:
        obj = build_record()

    if not isinstance(obj, Record):
        raise TypeError(f"Argument {obj} is not a Record.")
    obj.write(ctx.engine)


def rendertemplate(
        **kwargs
) -> str:
    """Render the content on the template to be edited."""

    jinjatext = "{%if not date %}date, {% endif %}" \
                "{%if not amount %}amount, {% endif %}" \
                "{%if not description %}description, {% endif %}" \
                "{%if not currency %}currency, {% endif %}" \
                "{%if not category %}category, {% endif %}"
    template: Template = Template(jinjatext)
    # header concatenates to col1, col2, col3,
    text = template.render(**kwargs)
    # remove last comma:
    cleaned = text.strip().rstrip(',')
    return cleaned


def buildtmpfile(
            text: str
)-> Path:
    """Populate temporary file and then launch it. Returns the tmp file path."""
    
    # create tmp file
    fname = date.today().strftime("%Y-%m-%d")
    path =  APPLICATION_DIRECTORY / f"csv_{fname}.csv"
    with open(path, 'w') as file:
        file.write(text)
    
    # call editor and return path after quit
    print(f"Launching r'{path}'.")
    subprocess.call([ctx.editor, path])
    return path


def build_df(
        fixed_fields : FixedColumnsType | None = None
) -> pd.DataFrame:
    """
    Create multiple Records in dataframe form.
    If `fixed_fields` is None, they're prompted interactively.

    Parameters
    ------
    fixed_fields
        A dictionary mapping column names to fixed values 
        (e.g., {"category": "Food"}).

    Notes
    - Temporary files are cleaned up after execution.
    - No support for Conversion yet.
    """

    # type checking
    if fixed_fields is None:
        fixed_fields = prompt_column_value(ctx.keybinds, fixed_fields)

    text = rendertemplate(**fixed_fields)
    tmp = buildtmpfile(text)

    # fetch dataframe
    df = open_recorddf(tmp)
    for column, value in fixed_fields.items():
        df[column] = value
    df.date = pd.to_datetime(df.date)
    
    # if parse was successful, remove file and return
    tmp.unlink(missing_ok=True)
    return df


def write_df(
        df : pd.DataFrame | pd.Series,
        overwrite: bool = True
) -> None:
    """
    Writes **record** dataframe to database. Performs type-checking, column type
    checking, and if `df` has index or 'id' is in columns, then it updates each 
    record accordingly. Otherwise, df is appeneded to database table.
    
    Arguments
    -----
    df
        DataFrame to be passed to database. 
    """

    # sanitize dataframe before writing to it
    table_name = Record.__tablename__
    category_list = list(ctx.categories_dict.keys())
    df = sanitize_df(df, category_list)

    # check if appending or replacing
    hasidindex = (df.index.name == 'id')
    if 'id' not in df.columns and not hasidindex:  # appending
        df.to_sql(table_name, ctx.engine, 
                  if_exists='append',
                  index=False)
        pprint_df(df, "Changes have been commited.")
        return None

    if not overwrite:
        print(f"{fg.red}DataFrame has non-trivial index.{fg.reset}"
              "This can result in data loss."
              f"To overwrite data, set {fg.red}overwrite=False{fg.reset}.")
        return None
    
    # if there is id index, reset it so orient=records preserves it
    if hasidindex:
        df = df.reset_index()
    as_dict = df.to_dict(orient='records')

    with Session(ctx.engine) as session:
        session.execute(update(Record), as_dict)
        session.commit()
    pprint_df(df, header="Actions commited.")



def build_conversion(
        date_: date | None = None,
        base_operation_str: str | None = None,
        target_operation_str: str | None = None,
        description: str | None = None
) -> None:
    """
    Prompts the user for a currency conversion and returns it.

    Arugments:
    -----
        date
            The date of the conversion. If None, the user is prompted.
        base_operation_str
            base operation (what you start with), if None -> prompted.
        target_operation_str
            target operation (what you get), if None -> prompted.
        description
            brief description of the conversion. If None, the user is prompted.
    """

    # type checking and prompters
    date_ = prompt_date_operation(date_)
    print("Base operation: what you start with / got converted.")
    base_amount, base_currency = prompt_double_currency(ctx.default_currency, 
                                                        base_operation_str)
    print("Target operation: what you get / have now.")
    target_amount, target_currency = prompt_double_currency(ctx.default_currency,
                                                            target_operation_str)
    if not description:
        description = input("Type your description: ")
    
    # build and return
    return Conversion(date=date_,
                      base_currency=base_currency,
                      base_amount=base_amount,
                      target_currency=target_currency,
                      target_amount=target_amount,
                      description=description)


def write_conversion(conv: Conversion | None = None) -> None:
    """
    Write conversion wrapper. Relies on `build_conversion` if `conv` is empty.
    
    Arguments
    ----
    conv
        Conversion to write to Database. If None is passed then 
        `build_conversion` is called to the rescue.
    """
    if conv is None:
        conv = build_conversion()
    label = "The following Conversion entity has been added to database:"
    conv.write(ctx.engine, label)


def edit(
        id_: int | None = None,
        entity_type: Record | Conversion | None = Record,
        fields: str | None = None
) -> None:
    """
    Edit a Record or Conversion interactively.
    By default, Record is going to be edited.
    Looks for a record by ID or directly passed, asks for fields to edit and
    commits or rolls back.

    Parameters
    ------
    `id_`
        The ID of the record to edit. Ignored if `entity` is provided.
    entity
        Defaults to `Record`, it checks whether the entity to be edited is 
        `Record` or `Conversion`.
    fields
        A space-separated list of fields to edit (`prompt_column_value`).
    """

    entity = prompt_entity_by_id(ctx.engine, entity_type, id_)
    editables = prompt_column_value(ctx.keybinds, fields)
    for attr, new_val in editables.items():
        setattr(entity, attr, new_val)

    # write
    entity.write(ctx.engine)


def delete(
        id_: int | None = None,
        entity_type: Record | Conversion = Record,
        force: bool = False
) -> None:
    """
    Delete a Record or Conversion interactively.
    By default, a Record entity will be deleted. 
    
    Arguments
    ---------
    entity
        Defaults to `Record`, it checks whether the entity to be edited is 
        `Record` or `Conversion`.
    `id_`
        The ID of the record to edit. Ignored if `entity` is provided.
    entity
        An existing `Record` | `Conversion` object to delete directly. Passed if 
        not provided, fetched via `prompt_entity_by_id`.

    Notes
    -----
    - A warning message is shown before deletion to highlight that the
    operation is irreversible.
    """
    entity = prompt_entity_by_id(ctx.engine, entity_type, id_)

    if not force:
        print(f"{fg.red}Warning: you may lose data permanently.{fg.reset}"
            f"In order to delete the record with id {entity.id}, "
            f"set {fg.red}force = True{fg.reset}.")
        return None

    entity.delete(ctx.engine)
    print(f"Entity {entity} has been deleted.")


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
    stmt = stmt.order_by(desc(Record.id))

    try:
        df = pd.read_sql(stmt, ctx.engine, Record.id.key,
                         parse_dates={"date": PARSE_DATE_FORMAT})
    except pd.errors.DatabaseError:
        raise ValueError(f"Database error found. More likely wrong" 
                         "query: {stmt=!r}.")
    else:
        return df


def read_conversion(
        max_lines: int = 20,
) -> None:
    """Simple conversion reader. No support for df return yet."""
    stmt = select(Conversion).limit(max_lines).order_by(desc(Conversion.date))
    df = pd.read_sql(stmt, ctx.engine, Record.id.key)
    pprint_df(df)


def read(
        max_lines: int = 20,
        entity_type: Conversion | Record = Record,
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
    if entity_type == Record:
        pprint_df(fetch(semantic_filter, max_lines))
    elif entity_type == Conversion:
        read_conversion(max_lines)
    else:
        raise TypeError(f"Invalid {entity_type=}. Must be Conversion or Record.")



    