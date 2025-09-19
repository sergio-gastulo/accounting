import sys 
import pandas as pd
from pathlib import Path
from sqlalchemy import create_engine

from src.acc_py.context.context import ctx # custom context
import src.acc_py.plot.validate as val # custom validation
import src.acc_py.plot.plot as plot # custom plotting functions
import src.acc_py.utilities.get as get
import src.acc_py.interface.interface as interface


# Alias for plotting functions for improved navigation
p1  =   lambda period=None: plot.categories_per_period(period=period)
p2  =   lambda period=None: plot.expenses_time_series(period=period)
p3  =   lambda category=None, period=None: plot.category_time_series(period=period, category=category)
p4  =   lambda currency, period=None: plot.monthly_time_series(currency=currency, period=period)
w   =   lambda : interface.write
e   =   lambda id : interface.edit(id=id)
wl  =   lambda : interface.write_list
d   =   lambda : interface.delete
r   =   lambda number_lines : interface.read(n_lines=number_lines) 


def h(f : callable = None) -> None:
    
    help_message = """
Interactive plotting CLI

Available functions:
    - p1(period=None) -> plot.categories_per_period
    - p2(period=None) -> plot.expenses_time_series
    - p3(category=None, period=None) -> plot.category_time_series
    - p4(currency, period=None) -> plot.monthly_time_series
    - w -> interface.write
    - e(id) -> interface.edit
    - wl -> interface.write_list
    - d -> interface.delete
    - r(n_lines) -> interface.read

Context variables (available under ctx):
    - engine
    - json_path
    - period
    - month_es
    - categories_dict
    - selected_category
    - colors
    - keybinds

Help:
    - h(function) -> show function docstring (use full name, e.g. h(plot.categories_per_period))

Tip: Reprint this message with h()
    """

    if f is None:
        print(help_message)
    else:
        val._doc_printer(func=f)



def main(db_path : Path, json_path : Path) -> None:

    plot.darkmode()
    ctx.engine = create_engine(f"sqlite:///{db_path}")
    ctx.categories_dict = val._get_json(json_path=json_path)
    ctx.keybinds = get.fetch_keybind_dict(json_path=json_path)
    ctx.period = val._get_period(pd.Timestamp.today().to_period('M'))
    ctx.month_es = {
        1: "Enero",
        2: "Febrero",
        3: "Marzo",
        4: "Abril",
        5: "Mayo",
        6: "Junio",
        7: "Julio",
        8: "Agosto",
        9: "Septiembre",
        10: "Octubre",
        11: "Noviembre",
        12: "Diciembre"
    }

    ctx.selected_category = val._get_category(dict_cat=ctx.categories_dict)
    ctx.colors = {
        currency: (r / 255, g / 255, b / 255) 
        for currency, (r, g, b) in zip(
            ['EUR', 'USD', 'PEN'],
            [(128, 128, 255), (26, 255, 163), (255, 255, 255)] # https://www.w3schools.com/colors/colors_picker.asp
            )
        }


if __name__ == "__main__":
    main(db_path=sys.argv[1], json_path=sys.argv[2])
    h()