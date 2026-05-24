import sys
from pathlib import Path

from context.context import ctx

# interface independent as well
from utilities.help import acccli
from utilities.core import now, get_globals
from utilities.file import fimport, fexport
from utilities.parser import parse_date as pdate
from utilities.interface import (
    fopen, 
    convert_currency as convcurr
)


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
        "gr": da.get_record,
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
