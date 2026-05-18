import sys
from pathlib import Path
import subprocess

from context.context import ctx

# interface independent as well
from utilities.core import now, fexport, fimport
from utilities.parser import parse_date as pdate


#region ==================== interface-independent  ============================


def acccli():
    """
    Interactive REPL Python-backed.

    Independently, the following file-based operations and miscellanea has been
    loaded:
    [now, fexport, fimport, fopen, pdate]

    The available DB management functions are available:
        "br": da.build_record,
        "bc": da.build_conversion,
        "bdf": da.build_df,
        "e": da.edit,
        "fetch": da.fetch,
        "d": da.delete,
        "r": da.read,
        "wr": da.write_record,
        "wc": da.write_conversion,
        "wdf": da.write_df,
        "Record": Record,
        "Conversion": Conversion,
    
    The available plotting functions are available:
        "p1": pp.categories_per_period, 
        "p2": pp.expenses_time_series, 
        "p3": pp.category_time_series, 
        "sp": pp.savings_plot, 

    Depending on the loaded module, "load" will import it's complement if 
    required.
    To check which functions you have available, feel free to evaluate 
    globals().keys()
    Evaluate acccli() to print this message again.
    """
    return acccli.__doc__


def fopen(
        p : Path | str
)-> None:
    """Quick file opener, relies on ctx.editor to open said file."""
    if isinstance(p, str):
        p = Path(p)
    if not isinstance(p, Path):
        raise TypeError(f"Argument {p} is not Path-like.")    
    subprocess.call([ctx.editor, p])


#endregion =====================================================================


#region ========================== interfaces ==================================

def load_db_api_module(*args) -> None:    

    ctx.set(*args)

    # populate global namespace from db_api
    import db.db_api as da
    from db.model import Record, Conversion
    exposed = {
        "br": da.build_record,
        "bc": da.build_conversion,
        "bdf": da.build_df,
        "e": da.edit,
        "fetch": da.fetch,
        "d": da.delete,
        "r": da.read,
        "w": da.write_record,
        "wc": da.write_conversion,
        "wdf": da.write_df,
        "Record": Record,
        "Conversion": Conversion,
    }
    globals().update(exposed)


def load_plot_module(*args) -> None:

    try:
        ctx.set_plot()
    except RuntimeError:
        ctx.set(*args)
        ctx.set_plot()

    # populate globals from plot
    import plot.plot as pp    
    pp.set_configs()
    pp.dark()
    exposed = {
        "p1": pp.barchart_by_period,
        "p2": pp.scattered_outflow,
        "p3": pp.category_time_series,
        "sp": pp.savings_plot,
        "dark": pp.dark
    }
    globals().update(exposed)


#endregion =====================================================================


def main() -> None:
    """Main interface handler."""

    # apply interface
    sys.ps1 = f"(acccli) >>> "

    config_path = Path(sys.argv[1])
    fields_path = Path(sys.argv[2])
    flag = sys.argv[3]

    if flag == 'db':
        load_db_api_module(config_path, fields_path)
    elif flag == 'plot':
        load_plot_module(config_path, fields_path)
    else:
        raise ValueError(f"Invalid {flag=}. Must be 'plot' or 'db'.")

    print("For help, please evaluate acccli().")


if __name__ == "__main__":
    main()
