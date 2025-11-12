from ..plot.plot import *
from ..context.main import set_context
from ..utilities.miscellanea import print_func_doc
from pathlib import Path
from typing import Callable


def h(function : Callable | None = None) -> None:
    help_message = f"""
Interactive plotting CLI

Available functions:
    - p1    -> plot.categories_per_period
    - p2    -> plot.expenses_time_series
    - p3    -> plot.category_time_series
    - p4    -> plot.monthly_time_series
    - load_db    -> import db_api
    
For further help, you can do: 
    - h(f)  -> prints documentation of f
    - h()   -> prints this message
"""
    if function:
        print_func_doc(func=function)
    else:
        print(help_message)


def run(config_path : Path, field_json_path : Path) -> None:
    darkmode()
    set_context(config_path, field_json_path, plot=True)
    h()
