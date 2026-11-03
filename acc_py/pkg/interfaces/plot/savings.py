import pandas as pd
from sqlalchemy import select, case
from sqlalchemy.sql import functions
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

from pkg.classes.model import Record
from pkg.classes.context import ctx
from .shared import (PERIOD_COL_LABEL, 
                     PERIOD_FORMAT,
                     YEAR_MONTH_PERIOD_COL, 
                     raise_on_empty)
from .timeseries import plot


@raise_on_empty
def fetch_savings_data() -> pd.DataFrame:
    """Quick `savings_plot` data fetcher."""

    # compute savings query
    is_inflow = Record.category.in_(ctx.inflow_categories)
    flow = case((is_inflow, +1), else_=-1) * Record.amount
    savings = functions.sum(flow).label('savings')

    currency = Record.currency
    q = (select(YEAR_MONTH_PERIOD_COL, 
                currency, 
                savings)
                .group_by(PERIOD_COL_LABEL, currency))

    df = pd.read_sql(q, ctx.engine, [PERIOD_COL_LABEL, currency.key],
                     parse_dates={PERIOD_COL_LABEL: {'format' : PERIOD_FORMAT}})
    return df


# alias: sp
def savings_plot() -> None:
    """
    Plots savings (inflow - outflow) per Year-Month in accumulation form. 
    Plots their cummulative sum (`df.cumsum()`).

    Returns
    ---
    fig
        The resulting plot is returned for further end-user manipulation.
    """

    # data fetch
    df = fetch_savings_data()
    fig, ax = plot(df, combine=True)
    for line in ax.get_lines():
        line.set_marker("o")
    fig.canvas.draw()
    plt.show()