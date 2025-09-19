import datetime
from sqlalchemy import desc
from sqlalchemy.orm import Session
import pandas as pd
from jinja2 import Template
from pathlib import Path
from tempfile import gettempdir
import subprocess

from ..utilities.core_parser import (
    parse_semantic_filter,
    parse_csv_record
)
from ..utilities import prompt
from ..context.context import ctx
from ..db.model import Record



# ----------------------------------------------------
# current support: 
# write() -> prompts for each record (mandatory)
# write(field=value) -> specify some fields beforehand
# ----------------------------------------------------
def write(
        date : datetime.date | None = None,
        amount : float | None = None,
        currency : str | None = None,
        operation_str : str | None = None,
        description : str | None = None,
        category : str | None = None
) -> None:

    if not date:
        date = prompt.prompt_date_operation()
    if not operation_str:
        amount, currency = prompt.prompt_double_currency()
    if not description:
        description = input("Type your description: ")
    if not category:
        category = prompt.prompt_category(ctx.categories_dict)

    with Session(ctx.engine) as session:
        record = Record(
            date=date, amount=amount, 
            currency=currency, description=description, 
            category=category
        )
        session.add(record)
        print("Record written to database: ")
        session.commit()
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
        fixed_fields : dict[str, str | int] | None = None 
) -> None:
    
    if not fixed_fields:
        fixed_fields = prompt.prompt_column_value(ctx.categories_dict)

    # sorry for this, ik it's painful to read
    template_str = (Path(__file__).parent / ".." / Path(r".\templates\csv_metadata.j2")).resolve().read_text()
    csv_columns = ", ".join({'date', 'amount', 'currency', 'description', 'category'} - set(fixed_fields.keys()))
    text_template = Template(template_str).render(**fixed_fields, cols=csv_columns)

    today = datetime.date.today().strftime("%Y-%m-%d")
    editor = "notepad++.exe"
    temp_file = Path(gettempdir()) / f"csv_{today}.csv"

    with open(temp_file, 'w') as file:
        file.write(text_template)
    subprocess.call([editor, temp_file])

    df = parse_csv_record(path=temp_file)
    for column, value in fixed_fields.items():
        df[column] = value

    with Session(ctx.engine) as session:
        session.bulk_insert_mappings(
            Record,
            # https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.to_dict.html 
            df.to_dict(orient='records') # has nothing to do with Record
        )
        print(
            f"Current records being inserted to database:\n"
            f"{df.to_markdown(index=False)}"
        )

        confirm : str = input("Confirm your commit [y/N]: ")

        if confirm.lower() in ('y', 'yes'):
            session.commit()
            print("Record commited.")
        elif not confirm or confirm.lower() in ('n', 'no'):
            print("Change uncomitted.")
        else:
            print("Could not parse your query. Uncomitting.")

    # removing file after execution
    temp_file.unlink(missing_ok=True)



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
    
    if not record:
        record = prompt.prompt_record_by_id(ctx.engine, id)
    
    edit_dictionary = prompt.prompt_column_value(
        ctx.categories_dict, 
        fields_str=fields)
    
    for column, new_attribute in edit_dictionary.items():
        setattr(record, column, new_attribute)
    
    print(
        f"Your current record is: "
        f"{record.pretty()}"
    )
    confirm : str = input("Confirm your commit [y/N]: ")

    if confirm.lower() in ('y', 'yes'):
        with Session(ctx.engine) as session:
            session.add(record)
            session.commit()
        print("Record commited.")
    elif not confirm or confirm.lower() in ('n', 'no'):
        print("Change uncomitted.")
    else:
        print("Could not parse your query. Uncomitting.")



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
    
    print("\nWarning. You can lose data permanently.\n")
    if not record:
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
        n_lines : int,
        semantic_filter : str | None = None,
        filter_today : bool = True
) -> None:
    
    today = datetime.date.today()

    # TODO : develop prompt_semantic_filter 
    if not semantic_filter:
        semantic_filter = input("Type your semantic filter: ")

    stmt = parse_semantic_filter(semantic_filter)

    if filter_today:
        stmt = stmt.where(Record.date <= today)

    query = (
        stmt
        .order_by(desc(Record.date))
        .limit(n_lines)
    )

    print(pd.read_sql(query, ctx.engine, index_col='id').to_markdown())