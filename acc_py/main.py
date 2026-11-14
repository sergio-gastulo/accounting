import sys
from pathlib import Path

from pkg.classes.context import ctx

from pkg.coreutils.help import acccli
from pkg.coreutils.file import fimport, fexport
from pkg.coreutils.parser.dates import (parse_date as pdate,
                                        parse_period as pperiod)
from pkg.interfaces.independent import (fopen, 
                                        convert_currency as convcurr)


#region ========================== interfaces ==================================

def load_db_api_module(*args) -> None:    

    ctx.set(*args)

    # populate global namespace from db_api
    import pkg.interfaces.db_api as da
    from pkg.classes.model import Record, Conversion
    def load():
        load_plot_module(*args)
    exposed = {
        "bc": da.build_conversion,
        "e": da.edit,
        "fetch": da.fetch,
        "d": da.delete,
        "r": da.read,
        "load": load,
        "Record": Record,
        "Conversion": Conversion,
    }
    globals().update(exposed)


def load_plot_module(*args) -> None:

    try:
        ctx.set_plot()
    except RuntimeError:  # user loaded plot directly
        ctx.set(*args)
        ctx.set_plot()
    
    from pkg.interfaces.plot import (barchart_by_datefilter, 
                                     category_time_series, 
                                     savings_plot, 
                                     scattered_outflow, 
                                     set_configs,  
                                     dark,
                                     plot)
    set_configs()
    dark()
    exposed = {
        "p1": barchart_by_datefilter,
        "p2": scattered_outflow,
        "p3": category_time_series,
        "sp": savings_plot,
        "dark": dark,
        "plot": plot
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
