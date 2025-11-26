from ..db.db_api import *
from ..db.model import create_tables
from ..context.main import set_context
from ..utilities.miscellanea import print_func_doc
from pathlib import Path
from typing import Callable


def h(function : Callable | None = None) -> None:
    help_message = """
Interactive DB management via SQLAlchemy.

Available functions:
    - w()       -> db_api.write
    - wl()      -> db_api.write_list
    - wc()      -> db_api.write_conversion
    - d()       -> db_api.delete
    - r()       -> db_api.read
    - rc()      -> db_api.read_conversion
    - e()       -> db_api.edit
    - el()      -> db_api.edit_list
    - load_plot()    -> import plot // might shadow original h
    
For further help, you can do: 
    - h(f)      -> prints documentation of f
    - h()       -> prints this message
"""
    if function:
        print_func_doc(func=function)
    else:
        print(help_message)


def run(config_path : Path, field_json_path : Path) -> None:
    set_context(config_path, field_json_path)
    create_tables(engine=ctx.engine)
    h()
