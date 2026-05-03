import sys
from pathlib import Path
from typing import Callable

from utilities.core import (
    print_func_doc, 
    pprint_categories
)
from context.context import ctx
from datetime import datetime

p1 : Callable = None
p2 : Callable = None
p3 : Callable = None
sp : Callable = None
e : Callable = None
d : Callable = None
w : Callable = None
wl : Callable = None
wdf : Callable = None
wc : Callable = None
rc : Callable = None
r : Callable = None
el : Callable = None
h : Callable = None
load : Callable = None
now : Callable = lambda : datetime.now().strftime('%H:%M:%S')


#region ########################### interface-independent ######################

DOCS_DIR : Path = (
    Path(__file__).resolve().parent 
    / "templates"
)


def pc(help : bool = False) -> None:
    """
    Print all categories in a readable, formatted way.

    Parameters
    ----------
    categories_dict : dict[str, str]
        A mapping of category names to their descriptions.
        Each key is a category name, and each value is the category's
        human-readable label or explanation.

    field_json_path : Path
        Path to the JSON file from which the categories originate.
        Used for reference only; the function does not modify the file.

    help : bool, optional
        If False (default), print each category and its description
        in a clean, aligned, human-friendly format.
        If True, print extended help information for all available
        categories, including additional notes or hints contained in the
        descriptions.

    Returns
    -------
    None
        This function only prints formatted output and does not return a value.
    """
    pprint_categories(
        categories_dict=ctx.categories_dict,
        fields_dict=ctx.fields,
        help=help
    )


def custom_help(arg : str, func : Callable | None = None) -> None:

    if isinstance(func, Callable):
        print_func_doc(func=func)
        return

    path = DOCS_DIR / f"{arg}_help.txt"
    if path.exists():
        help_message = path.read_text()
        print(help_message) 
    else:
        print(f"Something went wrong while loading {DOCS_DIR=}.")
        return


#endregion ######################### interface-independent #####################


def plot(debug : bool = False) -> None:
    import plot.plot as pp
    pp.darkmode()
    global p1, p2, p3, p4, sp, h
    p1 = pp.categories_per_period
    p2 = pp.expenses_time_series
    p3 = pp.category_time_series
    sp = pp.savings_plot
    if h:
        print("Setting db.h as h_db")
        globals()["h_db"] = h
    h  = lambda f=None : custom_help(arg='plot', func=f)
    globals()["load"] = db
    if not debug:
        h()


def db(debug : bool = False) -> None:    
    import db.db_api as da
    global e, d, w, wl, wc, rc, r, el, h, wdf
    e  = da.edit
    d  = da.delete
    w  = da.write
    wl = da.write_list
    wdf = lambda : da.write_list(return_dataframe=True)
    wc = da.write_conversion
    rc = da.read_conversion
    r  = da.read
    el = da.edit_list
    if h:
        globals()["h_plot"] = h
    h  = lambda f=None : custom_help(arg='db', func=f)
    globals()["load"] = plot
    if not debug:
        h()


def load_plot(
        config_path : Path,
        fields_json_path : Path,
        debug : bool = False
) -> None:
    ctx.set(config_path, fields_json_path)
    ctx.set_plot()
    plot(debug)
    if not debug:
        h()


def main(
        config_path : Path,
        fields_json_path : Path,
        flag : str,
        debug : bool
) -> None:

    if flag == 'plot':
        load_plot(config_path, fields_json_path)
        globals()["load"] = db

    elif flag == 'db':
        ctx.set(config_path, fields_json_path)
        db(debug)
        globals()["load"] = lambda : load_plot(config_path, fields_json_path, debug)
    
    else:
        raise ValueError(f"'{flag}' is not a valid flag.")


if __name__ == "__main__":
    import sys
    sys.ps1 = "(acccli) >>> "
    main(
        config_path = sys.argv[1],
        fields_json_path = sys.argv[2],
        flag = sys.argv[3],
        debug=False
    )
