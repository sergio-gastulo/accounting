import sys 
from pathlib import Path
import pandas as pd
# custom modules
import src.acc_py.plot as plot
import src.acc_py.validate as val

plot.darkmode()
df = plot.sql_to_pd(db_path=sys.argv[1])

print("To proceed, choose a period to plot.")
td_period = val._get_period(pd.Timestamp.today().to_period('M'))
categories = val._get_json(json_path=sys.argv[2])

months_es = {
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

# list for interation
plot_tasks = [
    (plot.categories_per_month, dict(df=df, period=td_period, categories=categories, months_es=months_es)),
    (plot.expenses_time_series, dict(df=df, period=td_period)),
    (plot.category_time_series, dict(df=df, period=td_period, category=val._get_category(categories))),
    (plot.monthly_time_series,  dict(df=df, period=td_period, months_es=months_es)),
]

for func, kwargs in plot_tasks:
    val._doc_printer(func)
    func(**kwargs)
