from sqlalchemy import (
    inspect, 
    select,
    desc,
    MetaData,
    Table,
    Connection
)
from sqlalchemy.orm import Session
from sqlalchemy.sql.elements import TextClause
from sqlalchemy.dialects.sqlite import insert as insert_sqlite

import datetime
import pandas as pd
from jinja2 import Template
from pathlib import Path
from tempfile import gettempdir
import subprocess
from typing import List

from ..utilities.core_parser import (
    parse_semantic_filter,
    parse_csv_record,
    parse_arithmetic_operation
)
from ..utilities import prompt
from ..context.context import ctx
from ..db.model import (
    Record,
    Conversion    
)
from ..utilities.miscellanea import pprint_df


TABLE_COLUMNS : List[str] = list(inspect(Record).c.keys())


def confirm_commit(connection : Connection | Session) -> None:
    while True:
        confirm : str = input("Confirm your commit [y/N]: ")
        if confirm.lower() in ('y', 'yes'):
            connection.commit()
            print("Actions commited.")
            return
        elif not confirm or confirm.lower() in ('n', 'no'):
            print("Change uncomitted.")
            return         
        else:
            print("Could not parse your query, please try again.")


# ----------------------------------------------------
# current support: 
# write() -> prompts for each record (mandatory)
# write(field=value) -> specify some fields beforehand
# ----------------------------------------------------
def write(
        df : pd.DataFrame | None = None,
        date : datetime.date | None = None,
        operation_str : str | None = None,
        description : str | None = None,
        category : str | None = None
) -> None:
    # yes, documentation from ChatGPT because I'm lazy
    """
    Create a new Record.

    This function writes a Record to the database. Any field not provided
    as an argument is be interactively prompted from the user.

    Parameters
    ----------
    date : datetime.date | None, optional
        The date of the operation. If omitted -> prompted.
    amount : float | None, optional
        The amount of the operation. If omitted and `operation_str` = False
        -> prompted.
    currency : str | None, optional
        The currency code (e.g., "USD", "EUR"). If omitted and `operation_str`
        = False -> prompted
    operation_str : str | None, optional
        Shortcut to provide both `amount` and `currency` simultaneously. 
    description : str | None, optional
        Brief description of the record. omited? -> prompted
    category : str | None, optional
        The category of the record. omited? -> prompted.

    Notes
    -----
    - Prompts are delegated to functions in the `prompt` module.
    - The new `Record` is created, added to the current session, committed,
    and then printed via `Record.pprint()`.
    """

    if df is not None:
        write_from_dataframe(df)
        return

    date = prompt.prompt_date_operation(date)
    amount, currency = prompt.prompt_double_currency(ctx.default_currency, operation_str)
    if not description:
        description = input("Type your description: ")
    category = prompt.prompt_category_from_keybinds(ctx.keybinds, category)

    with Session(ctx.engine) as session:
        record = Record(
            date=date, amount=amount, 
            currency=currency, description=description, 
            category=category
        )
        session.add(record)
        session.commit()
        print("Record written to database: ")
        record.pprint()


# ------------------------------------------------------
# This function aims to support the following:
# [fields] = ask-for-list-of-columns
# for field in fields
#    validate field
# opens a tmp file with contents:
# ----------------------------
# field1 : value1
# field2 : value2
# ...
# not-fixed1, not-fixed2, ...
# value1, value2, ...
# value1, value2, ...
# ...
# ----------------------------
# then parses a list of records and writes them all
# ------------------------------------------------------
def write_list(
        fixed_fields : dict[str, str | int] | None = None,
        return_dataframe : bool = False 
) -> None:
    """
    Create multiple Records and write to db.

    This function generates a temporary CSV template file containing both fixed
    and non-fixed fields. The user fills in the missing values using a text
    editor. After editing, the CSV is parsed into a DataFrame, converted to
    records, and inserted into the database in bulk.

    Parameters
    ----------
    fixed_fields : dict[str, str | int] | None, optional
        A dictionary mapping column names to fixed values 
        (e.g., {"category": "Food"}).
        These fields will be pre-populated and applied to all records. If not
        provided, the user is prompted interactively to supply them.

    Notes
    -----
    - The CSV template is expected at `templates/csv_metadata.j2`.
    - Temporary files are cleaned up after execution.
    - Commit confirmation is explicit: only "y" or "yes" will commit.
    - All other responses default to *not committing*.
    """

    fixed_fields = prompt.prompt_column_value(ctx.keybinds, fixed_fields)

    template_str = (
        Path(__file__).parent.parent 
        / "templates"
        / "csv_metadata.j2"
    ).resolve().read_text()
    
    complement = set(fixed_fields.keys()).union(["id"])
    cols_to_write = sorted(set(TABLE_COLUMNS) - complement)
    as_csv = ", ".join(cols_to_write)
    text_template = Template(template_str).render(
        **fixed_fields, 
        cols=as_csv
    )

    today_str = datetime.date.today().strftime("%Y-%m-%d")
    editor = ctx.editor
    temp_file = Path(gettempdir()) / f"csv_{today_str}.csv"

    with open(temp_file, 'w') as file:
        file.write(text_template)
    print(f"Launching {temp_file}.")
    subprocess.call([editor, temp_file])

    try:
        df = parse_csv_record(path=temp_file)
    except:
        print(
            f"Could not parse the csv."
            f"Please review its content and re-write again."
        )
        return
    
    for column, value in fixed_fields.items():
        df[column] = value

    if return_dataframe:
        return df
    else:
        write_from_dataframe(df)
    temp_file.unlink(missing_ok=True)


def write_conversion(
        date : datetime.date | None = None,
        base_operation_str : str | None = None,
        target_operation_str : str | None = None,
        description : str | None = None
) -> None:
    """
    Prompt the user for a currency conversion and save it to the database.

    Interactively collects base and target currency amounts (and optionally a
    description) from the user, creates a Conversion record, and commits it
    to the database using the current SQLAlchemy session.

    Args:
        date (datetime.date | None): The date of the conversion. If None, the user is prompted.
        base_operation_str (str | None): Optional preset string for the base operation.
        target_operation_str (str | None): Optional preset string for the target operation.
        description (str | None): Description of the conversion. If None, the user is prompted.

    Returns:
        None
    """
    date = prompt.prompt_date_operation(date)
    print("Prompting base.\n")
    base_amount, base_currency = prompt.prompt_double_currency(base_operation_str, explain=False)
    
    print("Prompting target.\n")
    target_amount, target_currency = prompt.prompt_double_currency(target_operation_str, explain=False)
    
    if not description:
        description = input("Type your description: ")
    
    with Session(ctx.engine) as session:
        conv = Conversion(
            date=date, base_currency=base_currency,
            base_amount=base_amount,target_currency=target_currency,
            target_amount=target_amount,description=description
        )
        session.add(conv)
        session.commit()
        print("Conversion written to database: ")
        conv.pprint()


# ------------------------------------------------------
# This function aims to provide the following interface
# edit(id | record, [categories_list])
# record = get_by_id(id)
# for cat in categories_list
#     record.cat = input("whatever bro", until_validated=True)
# print(record)
# sure = you sure bro?
# if sure: commit
# else: print(rolled_back)
# calls structure:
#    edit()
#    edit(id)
#    edit(id, 'd a c')
# ------------------------------------------------------

def edit(
        id : int | None = None,
        record : Record | None = None,
        fields : str | None = None
) -> None:
    """
    Edit a Record interactively.

    This function loads a record (either from its ID or directly via a
    `Record` object), prompts the user to modify selected fields, and then
    commits or rolls back the changes based on confirmation.

    Parameters
    ----------
    id : int | None, optional
        The ID of the record to edit. Ignored if `record` is provided.
    record : Record | None, optional
        An existing record object to edit directly. If not provided,
        the record is retrieved by ID via user prompt.
    fields : str | None, optional
        A space-separated list of fields to edit. If not provided, the
        user is prompted to choose fields.

    Notes
    -----
    - Field values are collected interactively using functions from the
    `prompt` module.
    - The modified record is displayed for confirmation before committing.
    - Only "y" or "yes" confirms the commit. Any other response cancels it.
    """

    if not record:
        record = prompt.prompt_record_by_id(ctx.engine, id)
    
    edit_dictionary = prompt.prompt_column_value(
        ctx.keybinds, 
        fields_str=fields
    )
    
    for column, new_attribute in edit_dictionary.items():
        setattr(record, column, new_attribute)
    
    record.pprint() 

    with Session(ctx.engine) as session:
        session.add(record)
        session.commit()
    print("Record commited.")


# ------------------------------------------------
# This function aims to cover the following cases:
# delete()
# - prompts for id -
# pprints record
# you sure? y/N
# commit / rollback
# delete(id)
# ------------------------------------------------
def delete(
        id : int | None = None, 
        record : Record | None = None
) -> None:
    """
    Delete a Record interactively.

    This function removes a Record from db, either by ID or by
    passing an existing `Record` object. The user is prompted for confirmation
    before the deletion is committed.

    Parameters
    ----------
    id : int | None, optional
        The ID of the record to delete. Ignored if `record` is provided.
    record : Record | None, optional
        An existing record object to delete directly. If not provided,
        the record is retrieved by ID via user prompt.

    Notes
    -----
    - A warning message is shown before deletion to highlight that the
    operation is irreversible.
    - The record is committed only if the user explicitly confirms with
    "y" or "yes".
    - If the user responds with "n", "no", or presses Enter, the deletion
    is rolled back.
    - Any unrecognized input repeats the confirmation prompt.
    """

    print("\nWarning. You can lose data permanently.\n")
    record = prompt.prompt_record_by_id(ctx.engine, id)

    while True:
        confirm : str = input("Confirm your commit [y/N]: ")

        if confirm.lower() in ('y', 'yes'):
            with Session(ctx.engine) as session:
                session.delete(record)
                session.commit()
            print("Record commited.")
            return 
        
        elif not confirm or confirm.lower() in ('n', 'no'):
            print("Change uncomitted.")
            return 
        
        else:
            print("Could not parse your query, please try again.")



# ---------------------------------------------------
# This function aims to provide the following syntax:
# >>> read(10)
# Type column to filter (none for empty): col_i
# cols = col.split(',')
# for col in cols:
#     Type the {col} filter: 2025-08%
# >>> print(filtered results)
# 
# Another case:
# >>> read(10, 'amount between 10, 25')
# >>> read(10, 'date between date_1, date_2')
# >>> read(10, 'category comida-salida')
# >>> read(10, 'currency eur')
# >>> read(10, 'description like "wildcard"')
# >>> read(10, 'id = 123')
# ---------------------------------------------------

def read(
        n_lines : int | None = 20,
        semantic_filter : str | None = None,
        filter_today : bool = True,
        verbose : bool = True
) -> pd.DataFrame | None:
    """
    Query and optionally display records from the database.

    Retrieves records from the database, applies an optional semantic filter,
    and prints the result as a Markdown table. By default, results are limited
    to entries dated on or before today.

    Parameters
    ----------
    n_lines : int | None, optional
        Maximum number of records to return.
    semantic_filter : str | None, optional
        A textual filter expression. Supported patterns:
        
        - **str columns**: exact match, `LIKE` wildcard, or regex  
        - **int columns**: exact match or numeric range  
        - **float columns**: numeric range only
    filter_today : bool, default=True
        If True, restricts results to records dated up to today.
    print_flag : bool, default=True
        If True, prints the resulting table in Markdown format.

    Notes
    -----
    - Filter expressions are parsed by `parse_semantic_filter`.
    - When `semantic_filter` is omitted, the user may be prompted interactively.
    - Results are ordered by `Record.id` and limited by `n_lines`.
    - To use SQL, use "sql: SELECT ..." (only SELECT statements are supported).
    """

    today = datetime.date.today()
    if semantic_filter is None:
        semantic_filter = input("Type your semantic filter: ")

    stmt = parse_semantic_filter(semantic_filter)

	# check this, not insinstance seems to be evaluating to true
    if not isinstance(stmt, TextClause):
        if filter_today:
            stmt = stmt.where(Record.date <= today)
        if n_lines:
            stmt = stmt.limit(n_lines)
        stmt = stmt.order_by(desc(Record.id))
    
    df = pd.read_sql(stmt, ctx.engine, index_col='id')

    if verbose:
        pprint_df(df)
    else:
        return df


def read_conversion(
    print_flag : bool = True
) -> pd.DataFrame | None:
    
    stmt = select(Conversion)
    df = pd.read_sql(stmt, ctx.engine, index_col='id')

    if print_flag:
        pprint_df(df)
    else:
        return df


# ---------------------------------------------------
# This function aims to provide the following syntax:
# edit_list([int1, int2]):
# opens csv with records ranging from int1 to \
# int2 *inclusive*
# problem: how does user know what id to chose? 
# he can use r()
# this reduces the amount of records to be able to 
# edit but provides secure parsing
# ---------------------------------------------------
def edit_list(
        *ids : int,
        as_range : bool = True
) -> None:
    """
    Edit multiple Records interactively via a 'CSV' file.

    This function allows the user to edit one or more records by ID, or a
    contiguous range of IDs, by exporting them to a temporary CSV file,
    opening it in a text editor, and then re-importing the changes.

    Parameters
    ----------
    *ids : int
        One or more record IDs to edit. If `as_range` is True and exactly
        two IDs are provided, they are treated as a 'between' query.
    as_range : bool, default=False
        Whether to treat two IDs as the start and end of a range of records
        to edit. Ignored if more or fewer than two IDs are provided.

    Notes
    -----
    - The CSV file includes a header listing all columns; the `id` column
    should not be modified.
    - Users can delete lines from the CSV to skip editing certain records.
    - After editing, the CSV is parsed and changes are applied to the database.
    - Amount fields can include arithmetic expressions (e.g., "+10", "*2")
    which will be parsed automatically.
    - A temporary CSV file is created and opened with the default editor
    (`notepad++.exe` by default) and removed after processing.
    - Use this function in combination with `r()` or other listing functions
    to identify record IDs before editing.
    """

    # unclear if user wants to edit as_range 
    if len(ids) == 2 and as_range:
        stmt = select(Record).where(Record.id.between(ids[0], ids[1]))
    else:
        stmt = select(Record).where(Record.id.in_(list(ids)))

    # file control
    today = datetime.date.today().strftime("%Y-%m-%d")
    editor = ctx.editor
    temp_file = Path(gettempdir()) / f"csv_{today}.csv"
    header = (
        f"# -----------------------------------------------------------------\n"
        f"# Do not modify id! \n"
        f"# However, for performance, you can delete the line you won't edit.\n"
        f"# -----------------------------------------------------------------\n"
        f"{", ".join(TABLE_COLUMNS)}\n"
    )
    n_skip_rows_ = len(header.split('\n')) - 1

    with open(temp_file, 'w') as file:
        file.write(header)

    # write records to csv for editing.
    (
        pd
        .read_sql(sql=stmt, con=ctx.engine, index_col='id')
        .to_csv(temp_file, mode='a', header=False)
    )
    subprocess.call([editor, temp_file])
    
    # retrieve from file
    try:
        df = pd.read_csv(temp_file, skiprows=n_skip_rows_, names=TABLE_COLUMNS)
    except:
        print(
            f"Could not parse the csv."
            f"Please try to copy its content and re-write again."
        )
        return

    df = df.astype({
        "id" : "int",
        "date" : "datetime64[ns]",
        "amount" : "str",
        "currency" : "str",
        "description" : "str",
        "category" : "str"
    })
    
    df["date"] = df["date"].dt.date
    
    def cleaner(string : str) -> float | int:
        op = "=" + string if "=" not in string else string 
        return parse_arithmetic_operation(op, quiet=True)

    df.amount = df.amount.map(cleaner)

    # replace data
    with Session(ctx.engine) as session:
        session.bulk_update_mappings(
            Record,
            df.to_dict(orient='records')
        )
        print(
            f"Current records being updated to database:\n"
            f"{df.to_markdown()}"
        )   
        confirm_commit(connection=session)

    # removing file after execution
    temp_file.unlink(missing_ok=True)


def get_full_currencies_list() -> List[str]:
    query_currencies = select(Record.currency.distinct())    
    with Session(ctx.engine) as session:
        return list(session.scalars(query_currencies))


def write_from_dataframe(df : pd.DataFrame) -> None:
    table_name = "cuentas"

    if not 'id' in df.columns and df.index.name != 'id':
        pprint_df(df=df, header="Changes will be commited.")
        df.to_sql(
            name=table_name,
            con=ctx.engine,
            if_exists='append',
            index=False
        )
        return

    if df.index.name == 'id':
        df = df.reset_index()

    md = MetaData()
    table_insert = Table(table_name, md, autoload_with=ctx.engine)

    with ctx.engine.connect() as con:
        stmt = insert_sqlite(table_insert)
        stmt = stmt.on_conflict_do_update(
            index_elements=['id'],
            set_={
                c : stmt.excluded[c] 
                for c in df.columns.to_list() if c != "id"
            }
        )
        con.execute(stmt, df.to_dict(orient="records"))
        pprint_df(df=df)
        confirm_commit(connection=con)