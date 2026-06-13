import pandas as pd
import matplotlib.pyplot as plt
from sqlalchemy import select, case
from sqlalchemy.sql import functions
from matplotlib.figure import Figure

from pkg.classes.model import Record
from pkg.classes.context import ctx
from .shared import (
    YEAR_MONTH_PERIOD_COL,
    sum_currencies,
    get_config,
    raise_on_empty,
)


@raise_on_empty
def fetch_savings_data() -> pd.DataFrame:
    """Quick `savings_plot` data fetcher."""

    # compute savings query
    is_inflow = Record.category.in_(ctx.inflow_categories)
    flow = case((is_inflow, +1), else_=-1) * Record.amount
    savings = functions.sum(flow).label('savings')

    q = select(YEAR_MONTH_PERIOD_COL, 
               Record.currency, 
               savings
            ) \
            .group_by('period', Record.currency)

    df = pd.read_sql(q, ctx.engine, ['period', 'currency'],
        parse_dates={'period' : {'format' : '%Y-%m'}}
    )
    return df


@raise_on_empty
def get_combined(df : pd.DataFrame) -> pd.DataFrame:
    # pass by copy, do not modify original df
    ndf = df.copy()

    # map lower case on currency index level
    ndf.index = ndf.index.set_levels(df.index.levels[1].str.lower(), level=1)

    # chosing currency to collapse dict to
    key = ctx.default_currency.lower()
    def wrapper(s : pd.Series) -> float:
        converted = dict(s)
        res = sum_currencies(converted)
        return res[key]
    
    # apply wrapper to new dataframe after unstacking
    ndf = ndf["savings"].unstack(level=0, fill_value=0).apply(wrapper)
    return ndf


# alias: sp
def savings_plot() -> Figure:
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

    fig, ax = plt.subplots()
    # plot per currency
    for currency in ctx.currency_list:
        color = ctx.colors[currency]
        upper = currency.upper()
        period_df = df.xs(upper, level=1)
        ax.plot(period_df.cumsum(), label=upper, color=color, marker='o')

    # combine all currencies and collapse it to ctx.default_currency
    ndf = get_combined(df)
    color = get_config("savings", "savings_color")
    label = f"comb-{ctx.default_currency.upper()}"
    ax.plot(ndf.cumsum(), color=color, label=label, marker='o')

    # configurations
    ax.legend()
    ax.set_xlabel("Year-month period.")
    ax.set_xlabel("Raw saving.")
    fig.suptitle('Savings as a Time Series per Currency')
    fig.show()

    return fig
