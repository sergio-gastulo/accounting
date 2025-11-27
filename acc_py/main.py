import sys
from pathlib import Path
import os
from typing import Callable

# avoid installing acc_py by using src on from .. import .. as
from src.acc_py.utilities.miscellanea import print_func_doc
from src.acc_py.context.main import set_context
from src.acc_py.context.context import ctx


p1 : Callable = None
p2 : Callable = None
p3 : Callable = None
p4 : Callable = None
e : Callable = None
d : Callable = None
w : Callable = None
wl : Callable = None
wc : Callable = None
rc : Callable = None
r : Callable = None
el : Callable = None
h : Callable = None
DOCS_DIR : Path = Path(__file__).resolve().parent / "src" / "acc_py" / "templates"


# https://www.reddit.com/r/learnpython/comments/1b4sk5n/comment/kt1bgsy/
c = lambda : os.system('cls' if os.name == 'nt' else 'clear')


def custom_help(arg : str, func : Callable | None = None) -> None:

    if isinstance(func, Callable):
        print_func_doc(func=func)
        return

    path = DOCS_DIR / f"{arg}_help.txt"
    if path.exists():
        help_message = path.read_text()
        print(help_message) 
    else:
        print(f"'{arg}' is not a valid flag.")
        return


def plot() -> None:
    import src.acc_py.plot.plot as pp
    pp.darkmode()
    global p1, p2, p3, p4, h
    p1 = pp.categories_per_period
    p2 = pp.expenses_time_series
    p3 = pp.category_time_series
    p4 = pp.monthly_time_series
    if h:
        globals()["h_db"] = h
    h  = lambda f=None : custom_help(arg='plot', func=f)
    globals()["load"] = db
    h()


def db() -> None:    
    import src.acc_py.db.db_api as da
    global e, d, w, wl, wc, rc, r, el, h
    e  = da.edit
    d  = da.delete
    w  = da.write
    wl = da.write_list
    wc = da.write_conversion
    rc = da.read_conversion
    r  = da.read
    el = da.edit_list
    if h:
        globals()["h_plot"] = h
    h  = lambda f=None : custom_help(arg='db', func=f)
    globals()["load"] = plot
    h()


def main(
        config_path : Path,
        fields_json_path : Path,
        flag : str
) -> None:

    if flag == 'plot':
        set_context(config_path, fields_json_path, True)
        plot()

    elif flag == 'db':
        set_context(config_path, fields_json_path, False)
        db()

    else:
        print(f"'{flag}' is not a valid flag.")


if __name__ == "__main__":
    
    main(
        config_path = sys.argv[1],
        fields_json_path = sys.argv[2],
        flag = sys.argv[3]
    )