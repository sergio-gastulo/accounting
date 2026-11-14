"""
Database API, allows user to write to DB using sqlalchemy as query wrapper.
Heavily relies on both parser.py and py
"""
from datetime import date
import pandas as pd
from sqlalchemy import (select,
                        desc,
                        update,)
from sqlalchemy.orm import Session

from pkg.classes.model import Record, Conversion
from pkg.interfaces.db.dataframe import (pprint_df,
                                     sanitize_df,)
from pkg.coreutils.colors import fg
from pkg.interfaces.db.sql import parse_semantic_query
from pkg.coreutils.prompt import (prompt_date_operation,
                                  prompt_double_currency,
                                  prompt_category_from_keybinds,
                                  prompt_column_value,
                                  prompt_arithmetic_operation,
                                  prompt_currency,
                                  prompt_entity_by_id,)
from pkg.classes.context import ctx


#region ============================ utils  ====================================

RECORD_TABLE_COLUMNS: list[str] = list(Record.__table__.c.keys())
PARSE_DATE_FORMAT = "%Y-%m-%d"
MAX_LINES_DATABASE = 20
OVERWRITE_DF_HAS_INDEX = True


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
        max_lines: int | None = MAX_LINES_DATABASE,
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
    stmt = select(Conversion).limit(max_lines).order_by(desc(Conversion.date))
    df = pd.read_sql(stmt, ctx.engine, Record.id.key)
    pprint_df(df)


def read(
        max_lines: int = MAX_LINES_DATABASE,
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
    if semantic_filter is None:
        semantic_filter = input("Type your semantic filter: ")

    if entity_type == Record:
        pprint_df(fetch(semantic_filter, max_lines))
    elif entity_type == Conversion:
        read_conversion(max_lines)
    else:
        raise TypeError(f"Invalid {entity_type=}. Must be Conversion or Record.")



    