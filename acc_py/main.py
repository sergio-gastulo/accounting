import sys
from pathlib import Path
from typing import Callable

from utilities.core import (
    print_func_doc, 
    pprint_categories
)
from context.context import ctx
from datetime import datetime


#region ==================== interface-independent  ============================


DOCS_DIR  = Path(__file__).resolve().parent / "templates"
now : Callable = lambda : datetime.now().strftime('%H:%M:%S')


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


#endregion =====================================================================


def load_db_api_module(*args) -> None:    
    # --- load context first ---
    ctx.set(*args)
    custom_help('db')

    import db.db_api as da
    from db.model import Record, Conversion
    # --- update global namespace ---
    exposed = {
        "br"            :   da.build_record,
        "bc"            :   da.build_conversion,
        "bdf"           :   da.build_df,
        "e"             :   da.edit,
        "fetch"         :   da.fetch,
        "d"             :   da.delete,
        "r"             :   da.read,
        "wr"            :   da.write_record,
        "wc"            :   da.write_conversion,
        "wdf"           :   da.write_df,
        "h_db"          :   lambda f=None : custom_help(arg='db', func=f),
        "load"          :   lambda : load_plot_module(*args),
        # --- expose Record | Conversion for context management ---
        "Record"        :   Record,
        "Conversion"    :   Conversion,
    }
    globals().update(exposed)


def load_plot_module(*args) -> None:
    try:
        ctx.set_plot()
    except RuntimeError:
        # --- if set_plot raises RuntimeError, more likely ctx.set() hasn't 
        # --- been called
        ctx.set(*args)
        ctx.set_plot()
    # --- populating global namespace ---
    import plot.plot as pp
    exposed = {
        "p1"    : pp.categories_per_period,
        "p2"    : pp.expenses_time_series,
        "p3"    : pp.category_time_series,
        "sp"    : pp.savings_plot,
        "h_p"   : lambda f=None : custom_help(arg='plot', func=f),
        "load"  : lambda : load_db_api_module(*args),
        "dark"  : pp.darkmode
    }
    # --- actions
    globals().update(exposed)
    custom_help('plot')


def main(
        config_path : Path,
        fields_path : Path,
        flag : str,
) -> None:
    if flag == 'db':
        load_db_api_module(config_path, fields_path)
    elif flag == 'plot':
        load_plot_module(config_path, fields_path)
    else:
        raise ValueError(f"Invalid {flag=}. Must be 'plot' or 'db'")


if __name__ == "__main__":
    import sys
    sys.ps1 = f"(acccli) >>> "
    main(
        config_path = sys.argv[1],
        fields_path = sys.argv[2],
        flag = sys.argv[3],
    )
