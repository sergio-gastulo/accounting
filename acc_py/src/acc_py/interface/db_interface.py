from ..db.db_api import *
from ..context.main import set_context
from ..utilities.miscellanea import print_func_doc
from pathlib import Path
from typing import Callable

def h(function : Callable | None = None) -> None:
    help_message = """
Interactive DB management via SQLAlchemy.

Available functions:
    - w()        -> db_api.write
    - e()        -> db_api.edit
    - wl()       -> db_api.write_list
    - d()        -> db_api.delete
    - r(n_lines) -> db_api.read

For further help, you can do: 
    h(f) -> prints documentation of f
    h() -> prints this message
"""
    if function:
        print_func_doc(func=function)
    else:
        print(help_message)


def run(db_path : Path, json_path : Path) -> None:
    set_context(db_path, json_path)
    h()