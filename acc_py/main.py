import sys 
import pandas as pd
from pathlib import Path
from src.acc_py.context import ctx # custom context
import src.acc_py.validate as val # custom validation
import src.acc_py.plot as plot # custom plotting functions

if __name__ == "__main__":

    plot.darkmode()
    ctx.db_path = Path(sys.argv[1])
    ctx.period = val._get_period(pd.Timestamp.today().to_period('M'))
    ctx.categories_dict = val._get_json(json_path=Path(sys.argv[2]))
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
    ctx.currency_list = val._validate_currency_list(['PEN', 'EUR', 'USD']) # custom order
    ctx.selected_category = val._get_category(dict_cat=ctx.categories_dict)

    # check args later
    # check args later
    # check args later
    # check args later
    # check args later
    plot_tasks = [
        plot.categories_per_month,
        plot.expenses_time_series,
        # currently unsupported
        # plot.category_time_series,
        plot.monthly_time_series
    ]

    # this is not printing in powershell... wtf?
    for func in plot_tasks:
        val._doc_printer(func)
        func()
