import sys
from pathlib import Path
from typing import Callable

from utilities.core import pprintfunc
from context.context import ctx
from datetime import datetime


#region ==================== interface-independent  ============================


DOCS_DIR  = Path(__file__).resolve().parent / "templates"
now : Callable = lambda : datetime.now().strftime('%H:%M:%S')


def custom_help(arg : str, func : Callable | None = None) -> None:

    if isinstance(func, Callable):
        pprintfunc(func=func)
        return

    path = DOCS_DIR / f"{arg}_help.txt"
    if path.exists():
        help_message = path.read_text()
        print(help_message)
    else:
        print(f"Something went wrong while loading {DOCS_DIR=}.")
        return


def independent() -> None:
    """Pouplate globals regardless of whether it's db or plot context."""

    import utilities.core as core
    import utilities.parser as pars
    exposed = {
        "jdump" : core._jdump,
        "pc" : core.pprint_categories,
        "core_import" : core.fetch,
        "export" : core.export,
        "pdate" : pars.parse_date
    }
    globals().update(exposed)



#endregion =====================================================================


def load_db_api_module(*args) -> None:    

    # --- load context first ---
    ctx.set(*args)
    custom_help('db')

    import db.db_api as da
    from db.model import Record, Conversion
    # --- update global namespace ---
    exposed = {
        "br" : da.build_record,
        "bc" : da.build_conversion,
        "bdf" : da.build_df,
        "e" : da.edit,
        "fetch" : da.fetch,
        "d" : da.delete,
        "r" : da.read,
        "w" : da.write_record,
        "wc" : da.write_conversion,
        "wdf" : da.write_df,
        "h_db" : lambda f=None : custom_help(arg='db', func=f),
        "load" : lambda : load_plot_module(*args),
        # --- expose Record | Conversion for context management ---
        "Record"        :   Record,
        "Conversion"    :   Conversion,
    }
    globals().update(exposed)


def load_plot_module(*args) -> None:

    custom_help('plot')
    try:
        ctx.set_plot()
    except RuntimeError:
        # --- if set_plot raises RuntimeError, more likely ctx.set() hasn't 
        # --- been called
        ctx.set(*args)
        ctx.set_plot()
    # --- populating global namespace ---
    import plot.plot as pp
    
    pp.set_configs()
    pp.dark()

    exposed = {
        "p1"    : pp.barchart_by_period,
        "p2"    : pp.scattered_outflow,
        "p3"    : pp.category_time_series,
        "sp"    : pp.savings_plot,
        "h_p"   : lambda f=None : custom_help(arg='plot', func=f),
        "load"  : lambda : load_db_api_module(*args),
        "dark"  : pp.dark
    }
    # --- actions
    globals().update(exposed)


def main(
        config_path : Path,
        fields_path : Path,
        flag : str,
) -> None:
    """Main interface handler."""

    independent()
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
