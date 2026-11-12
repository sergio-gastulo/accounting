from typing import Optional

import pandas as pd
import matplotlib.pyplot as plt
from sqlalchemy import select, func, Label

from matplotlib.dates import DateFormatter

from pkg.coreutils.typing import FrequencyType
from pkg.coreutils.prompt import prompt_category_from_keybinds
from pkg.classes.context import ctx
from pkg.classes.model import Record
from .timeseries import plot
from .shared import (PERIOD_COL_LABEL, 
                     YEAR_MONTH_PERIOD_COL, 
                     TOTAL_AMOUNT_COL,
                     MATPLOTLIB_MONTH_FORMAT,
                     raise_on_empty,)


def get_freq_configs(freq: str = None) -> dict:
    configs = {
        "w": {
            "period_col": (func
                           .strftime('%Y %W 1', Record.date)
                           .label(PERIOD_COL_LABEL)),
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
) -> pd.DataFrame:
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

    q = (select(Record.currency, periodcol, TOTAL_AMOUNT_COL)
         .where(Record.category == category)
         .group_by(Record.currency, PERIOD_COL_LABEL))    

    df = pd.read_sql(q, ctx.engine,
                     parse_dates={PERIOD_COL_LABEL: fmt},
                     index_col=[Record.currency.key, PERIOD_COL_LABEL])
    return df


def category_time_series(
        category: Optional[str] = None,
        freq: Optional[FrequencyType] = "m",
        combine: bool = False
) -> None:
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

    # fetch
    category = prompt_category_from_keybinds(ctx.keybinds, category)
    configs = get_freq_configs(freq)
    period = configs["period_col"]
    zeroesfreq: str = configs["zeroes"]
    df = fetch_category_ts_data(period, category, configs["date_fmt"])

    # apply fill_zeros to each currency
    withzeros = (df
                 .groupby(level=0)
                 .apply(lambda g: fill_zeroes(g.droplevel(0), freq=zeroesfreq)))
    withzeros.index.rename({None: Record.date.key}, 
                           inplace=True)
    # plotting
    fig, ax = plot(withzeros, combine=combine)

    # decorators
    for line in ax.get_lines():
        line.set_marker("o")
    fig.canvas.draw()
    ax.set_title(f"{category.capitalize()} Time Series Plot")
    ax.set_xlabel("Spendings")
    ax.set_ylabel("Dates")
    ax.legend()
    ax.xaxis.set_major_formatter(DateFormatter(MATPLOTLIB_MONTH_FORMAT))
    fig.autofmt_xdate()
    plt.xticks(rotation=30)
    plt.show()