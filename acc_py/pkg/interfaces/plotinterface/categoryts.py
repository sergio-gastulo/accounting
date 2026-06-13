from typing import Optional

import pandas as pd
import matplotlib.pyplot as plt
from sqlalchemy import select, func, Label
from matplotlib.figure import Figure
from matplotlib.dates import DateFormatter

from pkg.utilities.core import pprint_df
from pkg.utilities.typing import FrequencyType
from pkg.utilities.prompt import prompt_category_from_keybinds
from pkg.classes.model import Record
from pkg.classes.context import ctx
from .shared import (
    YEAR_MONTH_PERIOD_COL,
    TOTAL_AMOUNT_COL,
    raise_on_empty,
)


def get_freq_configs(freq: str = None) -> dict:
    configs = {
        "w": {
            "period_col": func.strftime('%Y %W 1', Record.date).label('period'),
            "zeroes": "W-MON",
            "date_fmt": '%Y %U %w'
        },
        "m": {
            "period_col": YEAR_MONTH_PERIOD_COL,
            "zeroes": "MS",
            "date_fmt": '%Y-%m'
        }
    }
    freq = freq.lower()[0]
    if freq in ["m", "w"]: 
        return configs[freq]
    raise ValueError(f"Argument {freq=} is not a valid frequency: 'm' or 'w.")


def fill_zeroes(
        df: pd.DataFrame,
        freq: str
) -> None:
    start = df.index.min()
    end = df.index.max()
    zero_period = pd.date_range(start, end, freq=freq)
    return df.reindex(zero_period).fillna(0)


@raise_on_empty
def fetch_category_ts_data(
        periodcol: Label[str], 
        category: str,
        fmt: str, 
        /,
) -> pd.DataFrame:
    q = select(Record.currency, 
               periodcol, 
               TOTAL_AMOUNT_COL
            ) \
            .where(Record.category == category) \
            .group_by(Record.currency, 'period')
    
    df = pd.read_sql(
        q, ctx.engine, 
        parse_dates={'period': fmt},
        index_col=['currency', 'period']
    )
    return df


def category_time_series(
        category: Optional[str] = None,
        freq: Optional[FrequencyType] = "m",
) -> Figure:
    """
    Plots a time series from the given category.
    Useful for categories that should stay around a monthly / weekly average.
    
    Arguments
    -----
    category
        category to be parsed via `prompt_category_from_keybinds`. If None is 
        passed, said function will be called to prompt for a valid category.
    freq    
        Defaults to 'monthly'. Defines the frequency of the plot.

    Returns
    ---
    fig
        The resulting plot is returned for further end-user manipulation.
    """

    # ensure category by default
    category = prompt_category_from_keybinds(ctx.keybinds, category)

    configs = get_freq_configs(freq)
    period = configs["period_col"]
    df = fetch_category_ts_data(period, category, configs["date_fmt"])

    # main plot
    fig, ax = plt.subplots()

    zeroesfreq: str = configs["zeroes"]
    for currency in ctx.currency_list:
        color = ctx.colors[currency]
        try:
            period_df = df.loc[currency.upper()]
            period_df = fill_zeroes(period_df, freq=zeroesfreq)
            ax.plot(period_df, color=color, marker='o', label=currency)
    
        except KeyError:
            err = f"The given {currency=} is not available in the following df:"
            pprint_df(df, err)
    
    # decorators
    ax.set_title(f"{category.capitalize()} Time Series Plot")
    ax.set_xlabel("Spendings")
    ax.set_ylabel("Dates")
    ax.legend()
    ax.xaxis.set_major_formatter(DateFormatter('%Y-%b'))
    fig.autofmt_xdate()
    plt.xticks(rotation=30)
    fig.show()

    return fig