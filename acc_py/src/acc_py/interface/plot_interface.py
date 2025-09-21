from ..plot.plot import *
from ..context.main import set_context
from ..utilities.miscellanea import print_func_doc
from pathlib import Path
from typing import Callable


def h(function : Callable | None = None) -> None:
    help_message = f"""
Interactive plotting CLI

Available functions:
    - p1(period=None) -> plot.categories_per_period
    - p2(period=None) -> plot.expenses_time_series
    - p3(category=None, period=None) -> plot.category_time_series
    - p4(currency, period=None) -> plot.monthly_time_series

For further help, you can do: 
    h(f) -> prints documentation of f
    h() -> prints this message
"""
    if function:
        print_func_doc(func=function)
    else:
        print(help_message)


def run(db_path : Path, json_path : Path) -> None:
    darkmode()
    set_context(db_path=db_path, json_path=json_path, plot=True)
    h()