import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.axes import Axes

from pkg.classes.model import Record
from pkg.classes.context import ctx
from .shared import (sum_currencies, 
                     get_config,
                     PlotError)


def _series_currencies_sum(s: pd.Series, currency: str):
    res = sum_currencies(dict(s))
    return res[currency]


def combine_currency_timeseries(
        ax: Axes,
        unstacked: pd.DataFrame
) -> Axes:
    currency = ctx.default_currency.lower()
    color = get_config("core", "fourth_color")
    label = f"Total in {currency.upper()}"
    data = unstacked.apply(_series_currencies_sum, args=(currency, ))
    ax.plot(data, label=label, color=color)
    return ax


def date_currency_plot(
        s: pd.Series,
        combine=True
) -> tuple[Figure, Axes]:
    """
    Plots a pd.Series matching: 
        * ["date", "currency"] as indices and 
        * a numeric column (often labeled as "amount"). 
    Plots a Time Series associated to each currency.
    """

    fig, ax = plt.subplots()

    # plot each currency in dataframe
    df = s.sort_index(level=0).unstack(Record.date.key, fill_value=0)
    df.index = df.index.str.lower()
    for currency in df.index:
        color = ctx.colors[currency]
        label = currency.upper()
        ax.plot(df.xs(currency), label=label, color=color)

    if combine:
        ax = combine_currency_timeseries(ax, df)

    ax.set_xlabel(Record.date.key.title())
    ax.set_ylabel(Record.amount.key.title())
    ax.legend()
    fig.suptitle("Time Series per Currency plot")
 
    return fig, ax


def date_plot(
        s: pd.Series,
        **kwargs
) -> tuple[Figure, Axes]:
    """Plot a Series with `datetime` index. 
    `kwargs` are passed to `pd.Series.plot()`"""

    ax: Axes = s.sort_index().plot(label=s.name.title(), **kwargs)
    ax.set_xlabel(Record.date.key.title())
    ax.set_ylabel(Record.amount.key.title())
    ax.legend()
    ax.figure.suptitle("Time Series plot")

    return ax.figure, ax


def transform(
        df: pd.DataFrame | pd.Series,
) -> pd.DataFrame:
    """
    Transforms DataFrame into valid argument for `*_plot` functions.
    """

    if not isinstance(df, pd.DataFrame | pd.Series):
        raise TypeError("DataFrame / Series can be plotted only.")

    # check if "date" in the index -> no groupby needed
    if Record.date.key in df.index.names:
        # series = only one column -> return
        if isinstance(df, pd.Series):
            return df
        # if more than one column
        if hasattr(df, "columns") and Record.amount.key in df.columns:
            return df[Record.amount.key]

    # check if "date" is on the columns -> perform a groupby
    if Record.date.key in df.columns and Record.amount.key in df.columns:
        if "currency" in df.columns:
            return df.groupby([Record.date.key, "currency"]).amount.sum()
        return df.groupby(Record.date.key).amount.sum()
    
    raise PlotError("DataFrame / Series does not meet "
                    "the requirements for plot.")


def plot(
    df: pd.DataFrame, **kwargs
) -> tuple[Figure, Axes]:
    """
    Plot a DataFrame containing "date" and "amount" information. 
    Column "currency" is also allowed to be plotted.
    """

    df_has_currency = (Record.currency.key in df.index.names or 
                       (hasattr(df, "columns") and Record.currency.key in df.columns))
    plotfunc = date_currency_plot if df_has_currency else date_plot
    fig, ax = plotfunc(transform(df), **kwargs)
    return fig, ax