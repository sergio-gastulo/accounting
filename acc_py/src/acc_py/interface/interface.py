import datetime
from typing import List, Union

from sqlalchemy import desc
from sqlalchemy.orm import Session

from ..utilities import prompt
from ..utilities import core_parser
from ..context.context import ctx
from ..db.model import Record
from ..utilities.printers import pprint_records


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
    if operation_str:
        amount, currency = prompt.prompt_double_currency()
    if not description:
        description = input("Type your description: ")
    if not category:
        category = prompt.prompt_category(ctx.categories_dict)

    record = Record(date, amount, currency, description, category)
    print(f"Written:\n{record}")
    record.write()


# TODO
def edit(
        id : int | None = None,
        record : Record | None = None,
        fields : str | List[str] | None = None
):
    if not record:
        record = prompt.prompt_record_by_id(ctx.engine, id)

    pass



def delete():
    pass


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
        semantic_filter : str = ""
) -> None:
    
    today = datetime.date.today()

    stmt = core_parser.parse_semantic_filter(semantic_filter)
    with Session(ctx.engine) as session:
        query = (
            stmt
            .where(Record.date <= today)
            .order_by(desc(Record.date))
            .limit(n_lines)
        )

        records = session.scalars(query)
        pprint_records(records=records)


