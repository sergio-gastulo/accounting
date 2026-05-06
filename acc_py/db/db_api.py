"""
Database API, allows user to write to DB using sqlalchemy as query wrapper.
Heavily relies on both parser.py and py
"""
# --- generics ---
from typing import List, Optional, Type, Any
from datetime import date
import pandas as pd
from jinja2 import Template
from pathlib import Path
import subprocess

# --- sqlalchemy wrappers ---
from sqlalchemy import (
    inspect, 
    select,
    desc,
)
from sqlalchemy.orm import Session

# --- hand-coded stuff in .utilities and .context ---
from context.context import ctx
from utilities.core import (
    APPLICATION_DIRECTORY,
    pprint_df,
    ensure,
    confirm_action
)
from utilities.parser import (
    parse_semantic_filter,
    parse_csv_record,
    sanitize_df,
)
from utilities.prompt import (
    FixedColumnsType,
    prompt_date_operation,
    prompt_double_currency,
    prompt_category_from_keybinds,
    prompt_column_value,
    prompt_entity_by_id,
    prompt_arithmetic_operation,
    prompt_currency,
)
from db.model import (
    Record,
    Conversion,
)


#region ============================ utils  ====================================

RECORD_TABLE_COLUMNS : List[str] = list(inspect(Record).c.keys())
TODAY = date.today()

def ensure_or_none(value : Any, *args : Type[Any]):
    ensure(value, *args, allow_none=True)

#endregion =====================================================================


def build_record(
        date_ : Optional[date] = None,
        amount : Optional[int | float] = None,
        currency : Optional[str] = None,
        operation_str : Optional[str] = None,
        description : Optional[str] = None,
        category : Optional[str] = None
) -> Record:
    """
    Create and write a new Record to the database.
    Omitted arguments are prompted interactively.

    Parameters
    ----------
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
    -----
    Record is committed automatically and printed via `Record.pprint()`.
    """

    # -------------------- Type checking (None are allowed) --------------------
    
    # --- date type-check ---
    ensure_or_none(date_, date)
    date_ = prompt_date_operation(date_)

    # --- if amount and currency are not specified, then prompt for pair ---
    if amount is None and currency is None:
        ensure_or_none(operation_str, str)
        amount, currency = prompt_double_currency(
            ctx.default_currency, operation_str)
    else:
        # --- if any of (amount, currency) is not None, then 
        # --- individual prompt for each is forced
        ensure_or_none(amount, int, float)
        amount = prompt_arithmetic_operation(amount)
        ensure_or_none(currency, str)
        currency = prompt_currency(currency)
    
    # --- description type-check ---
    ensure_or_none(description, str)
    if description is None:
        # --- could be empty, one can rely on edit() to change it ---
        description = input("Type your description: ")

    # --- category type-check ---
    ensure_or_none(category, str)
    category = prompt_category_from_keybinds(ctx.keybinds, category)

    # --- build and return ---
    record = Record(
        date=date_, amount=amount, 
        currency=currency, description=description, 
        category=category)
    return record


def write_record(rec : Optional[Record] = None) -> None:
    """
    Simple record writer wrapper. Relies on `build_record` to 
    retrieve fields.

    Arguments
    ---------
    rec
        Record that will be written to db. If None is passed, then 
        `build_record` is called to build one and automatically write to db.
    """
    ensure_or_none(rec, Record)
    if rec is None:
        rec = build_record()
    rec.write(ctx.engine)


def build_df(
        fixed_fields : Optional[FixedColumnsType] = None
) -> pd.DataFrame:
    """
    Create multiple Records in dataframe form.
    Omitted `fixed_fields` are prompted interactively.

    Parameters
    ----------
    fixed_fields
        A dictionary mapping column names to fixed values 
        (e.g., {"category": "Food"}).

    Notes
    -----
    - Temporary files are cleaned up after execution.
    - No support for Conversion yet.
    """

    # --- type checking ---
    ensure_or_none(fixed_fields, dict)
    fixed_fields = prompt_column_value(ctx.keybinds, fixed_fields)

    # --- construct template path and content retrieval ---
    template_fname  = "csv_metadata.j2"
    template_dir    = "templates"
    template        = Path(__file__).parent.parent / template_dir / template_fname
    content         = template.read_text()
    
    # --- construction of unfixed columns to be populated on template ---
    excluded        = set(fixed_fields) | {"id"}
    dynamic_cols    = ', '.join(sorted(set(RECORD_TABLE_COLUMNS) - excluded))
    text_template   = Template(content).render(cols=dynamic_cols)

    # --- set file template ---
    today_str = TODAY.strftime("%Y-%m-%d")
    temp_file =  APPLICATION_DIRECTORY / f"csv_{today_str}.csv"
    with open(temp_file, 'w') as file:
        file.write(text_template)
    
    # --- call editor ---
    print(f"Launching {temp_file}.")
    subprocess.call([ctx.editor, temp_file])

    # -------------------------- dataframe management --------------------------
    df = parse_csv_record(temp_file)
    for column, value in fixed_fields.items():
        df[column] = value
    df.date = pd.to_datetime(df.date)
    
    # --- if parse was successful, remove file and return ---
    temp_file.unlink(missing_ok=True)
    return df


def write_df(df : pd.DataFrame) -> None:
    """
    Writes **record** dataframe to database. Performs type-checking, column type
    checking, and if df contains index, then it updates each record accordingly.
    Otherwise, df is appeneded to database.
    
    Arguments
    ---------
    df
        DataFrame to be passed to database. 
    """

    # --- sanitize dataframe before writing to it ---
    table_name = Record.__tablename__
    category_list = list(ctx.categories_dict.keys())
    df = sanitize_df(df, category_list)

    # --- check if id is in columns or if it's the index name ---
    is_index_id = (df.index.name == 'id')
    if not ('id' in df.columns) and not is_index_id:
        # --- if that is not the case, just append to db ---
        df.to_sql(
            name=table_name, con=ctx.engine, 
            if_exists='append', index=False
        )
        pprint_df(df=df, header="Changes have been commited.")
        return

    # --- if there is index, reset it so orient=records preserves it ---
    if is_index_id:
        df = df.reset_index()
    to_dict = df.to_dict(orient='records')

    def _action():
        nonlocal to_dict
        with Session(ctx.engine) as session:
            session.bulk_update_mappings(Record, to_dict)
            session.commit()

    # --- print dataframe and confirm user validation ---        
    pprint_df(df)
    confirm_action(_action)


def build_conversion(
        date_ : Optional[date] = None,
        base_operation_str : Optional[str] = None,
        target_operation_str : Optional[str] = None,
        description : Optional[str] = None
) -> None:
    """
    Prompts the user for a currency conversion and returns it.

    Arugments:
    ---------
        date
            The date of the conversion. If None, the user is prompted.
        base_operation_str
            base operation (what you start with), if None -> prompted.
        target_operation_str
            target operation (what you get), if None -> prompted.
        description
            brief description of the conversion. If None, the user is prompted.
    """

    # --- type checking and prompters ---
    ensure_or_none(date_, date)
    date_ = prompt_date_operation(date_)
    ensure_or_none(base_operation_str, str)
    print("Base operation: what you start with / got converted.")
    base_amount, base_currency = prompt_double_currency(ctx.default_currency, base_operation_str)
    print("Target operation: what you get / have now.")
    ensure_or_none(target_operation_str, str)
    target_amount, target_currency = prompt_double_currency(ctx.default_currency, target_operation_str)
    ensure_or_none(description, str)
    if not description:
        description = input("Type your description: ")
    
    # --- build and return ---
    conv = Conversion(
        date=date_, base_currency=base_currency,
        base_amount=base_amount,target_currency=target_currency,
        target_amount=target_amount,description=description
    )
    return conv


def write_conversion(conv : Optional[Conversion] = None) -> None:
    """
    Write conversion wrapper. Relies on `build_conversion` to write.
    
    Arguments
    --------
    conv
        Conversion to write to Database. If None is passed then 
        `build_conversion` is called to the rescue.
    """

    ensure_or_none(conv, Conversion)
    if conv is None:
        conv = build_conversion()
    label = "The following Conversion entity has been added to database: "
    conv.write(ctx.engine, label)


def edit(
        id_ : Optional[int] = None,
        entity_type : Record | Conversion = Record,
        entity : Optional[Record | Conversion] = None,
        fields : Optional[str] = None
) -> None:
    """
    Edit a Record or Conversion interactively.
    By default, Record is going to be edited.
    Looks for a record by ID or directly passed, asks for fields to edit and
    commits or rolls back.

    Parameters
    ----------
    entity
        Defaults to `Record`, it checks whether the entity to be edited is `Record` or 
        `Conversion`.
    `id_`
        The ID of the record to edit. Ignored if `entity` is provided.
    entity
        An existing `Record` | `Conversion` object to edit directly. Passed if 
        not provided, fetched via `prompt_entity_by_id`.
    fields
        A space-separated list of fields to edit (`prompt_column_value`).
    """

    # --- ensure that entity is correctly retrieved ---
    if not isinstance(entity, Conversion | Record):
        ensure_or_none(id_, int)
        entity = prompt_entity_by_id(ctx.engine, entity_type, id_)

    # --- build editable dictionary and replace in entity ---
    editables = prompt_column_value(ctx.keybinds, fields_str=fields)    
    for attr, new_val in editables.items():
        setattr(entity, attr, new_val)

    # --- write ---
    entity.write(ctx.engine)


def delete(
        entity_type : Record | Conversion = Record,
        id_ : Optional[int] = None,
        entity : Optional[Record | Conversion] = None,
) -> None:
    """
    Delete a Record or Conversion interactively.
    By default, Record is going to be deleted. 
    
    Arguments
    ---------
    entity
        Defaults to `Record`, it checks whether the entity to be edited is `Record` or 
        `Conversion`.
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

    # --- ensure that entity is correctly retrieved ---
    if not isinstance(entity, Record | Conversion):
        ensure_or_none(id_, int)
        entity = prompt_entity_by_id(ctx.engine, entity_type, id_)
    else:
        # TODO: ensure that entity effectively exists in database
        pass

    action = lambda : entity.delete(ctx.engine)
    confirm_action(action)


def fetch(
        semantic_filter : Optional[str] = None,
        max_lines : int = 20,
) -> pd.DataFrame:
    """
    Fetches records from database.
    Relies on `parse_semantic_filter` to approve parsing.

    Parameters
    ----------
    max_lines
        Maximum number of records to return. Defaults to 20.
    semantic_filter
        A textual filter expression. Supported patterns:
        - str columns: exact match, `LIKE` wildcard, or regex
        - int columns: exact match or numeric range
        - float columns: numeric range only

    Notes
    -----
    - When `semantic_filter` is omitted, the user may be prompted interactively.
    - Results are ordered by `Record.id` (desc) and limited by `max_lines`.
    - To use SQL, use `sql: SELECT ...` (only SELECT statements are supported).
    """
    
    # --- type checking ---
    ensure(max_lines, int)
    ensure_or_none(semantic_filter, str)

    # --- ask for semantic filter and parse it ---
    if semantic_filter is None:
        semantic_filter = input("Type your semantic filter: ")
    
    # --- query constructor -- by design, there is no prompter for this ---
    stmt = parse_semantic_filter(semantic_filter)
    stmt = stmt.limit(max_lines).order_by(desc(Record.id))

    try:
        df = pd.read_sql(stmt, ctx.engine, index_col='id')
        return df
    # https://pandas.pydata.org/docs/reference/api/pandas.errors.DatabaseError.html
    except pd.errors.DatabaseError:
        raise ValueError(f"Database error found. More likely wrong query: {stmt=}.")


def _read_conversion(
        max_lines : int = 20,
) -> None:
    """Simple conversion reader. No support for df return yet."""
    ensure(max_lines, int)
    stmt = select(Conversion).limit(max_lines).order_by(desc(Conversion.date))
    df = pd.read_sql(stmt, ctx.engine, index_col='id')
    pprint_df(df)


def read(
        entity_type : Conversion | Record = Record,
        semantic_filter : Optional[str] = None,
        max_lines : int = 20,
):
    """
    Reads records from database.
    Relies on `fetch` to fetch records, and select true() on Conversions.

    Parameters
    ----------
    entity_type
        Which table to fetch objects from. Defaults to `Record`.
    max_lines
        Maximum number of records to return. Defaults to 20.
    semantic_filter
        A textual filter expression. Supported patterns:
        - str columns: exact match, `LIKE` wildcard, or regex
        - int columns: exact match or numeric range
        - float columns: numeric range only

    Notes
    -----
    - When `semantic_filter` is omitted, the user may be prompted interactively.
    - Results are ordered by `Record.id` (desc) and limited by `max_lines`.
    - To use SQL, use `sql: SELECT ...` (only SELECT statements are supported).
    """
    if entity_type == Record:
        pprint_df(fetch(semantic_filter, max_lines))
    elif entity_type == Conversion:
        _read_conversion(max_lines)
    else:
        raise TypeError(f"Invalid {entity_type=}. Must be Conversion or Record.")



    