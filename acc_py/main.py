import sys
from pathlib import Path

from pkg.classes.context import ctx

from pkg.utilities.help import acccli
from pkg.utilities.core import now, get_globals
from pkg.utilities.file import fimport, fexport
from pkg.utilities.parser import parse_date as pdate
from pkg.interfaces.independent import (
    fopen, 
    convert_currency as convcurr
)


#region ========================== interfaces ==================================

def load_db_api_module(*args) -> None:    

    ctx.set(*args)

    # populate global namespace from db_api
    import pkg.interfaces.db_api as da
    from pkg.classes.model import Record, Conversion
    def load():
        load_plot_module(*args)
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
        "load": load,
        "Record": Record,
        "Conversion": Conversion,
    }
    globals().update(exposed)


def load_plot_module(*args) -> None:

    # populate globals from plot
    try:
        ctx.set_plot()
    except RuntimeError:
        ctx.set(*args)
        ctx.set_plot()
    
    from pkg.interfaces.plotinterface import (
        barchart_by_datefilter,
        category_time_series,
        savings_plot,
        scattered_outflow,
        set_configs, 
        dark,   
    )
    set_configs()
    dark()
    exposed = {
        "p1": barchart_by_datefilter,
        "p2": category_time_series,
        "p3": savings_plot,
        "sp": scattered_outflow,
        "dark": dark
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


# TODO: expose parse_period
if __name__ == "__main__":
    main()
