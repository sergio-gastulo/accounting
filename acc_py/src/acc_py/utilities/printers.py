import inspect
from ..db.model import Record
from typing import List


def print_func_doc(func: callable) -> None:
    cyan_str = '\033[96m'
    end_str = '\033[0m'

    print(f'{cyan_str}Function name:{end_str}\n{func.__name__}\n')

    sig = inspect.signature(func)
    print(f'{cyan_str}Arguments:{end_str} {sig}\n')

    doc = func.__doc__
    print(f'{cyan_str}Documentation:{end_str}\n{doc}')


def pprint_records(records : List[Record]) -> None:
    widths = {
        "id": 4,
        "date": 8,
        "amount": 10,
        "currency": 8,
        "description": 20,
    }

    header = (
        f"| {'id':<{widths['id']}} "
        f"| {'date':<{widths['date']}} "
        f"| {'amount':>{widths['amount']}} "
        f"| {'currency':<{widths['currency']}} "
        f"| {'description':<{widths['description']}} |"
    )
    line = "-" * len(header)
    print(line)
    print(header)
    print(line)

    for record in records:
        id_ = f"{record.id:0{widths['id']}}"
        date_ = record.date.strftime("%y-%m-%d")
        amount_ = f"{record.amount:>{widths['amount']}.2f}"
        currency_ = f"{record.currency:<{widths['currency']}}"
        description_ = record.description[:widths['description']]
        row = (
            f"| {id_:<{widths['id']}} "
            f"| {date_:<{widths['date']}} "
            f"| {amount_:>{widths['amount']}} "
            f"| {currency_:<{widths['currency']}} "
            f"| {description_:<{widths['description']}} |"
        )
        print(row)
    print(line)