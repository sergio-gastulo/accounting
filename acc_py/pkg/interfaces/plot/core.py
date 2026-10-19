import random

import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.figure import Figure

from pkg.classes.context import ctx
from .shared import (sum_currencies, 
                     get_config,
                     PlotError)


def date_currency_plot(
        s: pd.Series
) -> Figure:
    """
    Aims to plot the simplest Series: ["date", "currency"] as indices and 
    a numeric column (often labeled as "amount"). Plots a Time Series 
    associated per currency.
    """

    fig, ax = plt.subplots()

    # plot each currency in dataframe
    df = s.sort_index(level=0).unstack("date", fill_value=0)
    df.index = df.index.str.lower()
    for currency in df.index:
        color = ctx.colors[currency]
        label = currency.upper()
        ax.plot(df.xs(currency), label=label, color=color)


    # plot a Line2D that combines them into a single currency
    if (currency := ctx.default_currency.lower()) not in df.index.names:
        currency = random.choice(df.index.values)
    color = get_config("core", "fourth_color")
    label = f"Total in {currency.upper()}"
    ax.plot(df.apply(lambda s: sum_currencies(dict(s))[currency]),
            label=label, color=color)

    ax.set_xlabel("Date")
    ax.set_ylabel("Amount")
    ax.legend()
    fig.suptitle("Time Series per Currency plot")
 
    return fig


def date_plot(
        s: pd.Series
) -> Figure:
    """Plot a Series with `datetime` index."""

    ax = s.sort_index().plot(label=s.name.title())
    ax.set_xlabel("Date")
    ax.set_ylabel("Amount")
    ax.legend()
    ax.figure.suptitle("Time Series plot")

    return ax.figure


def transform(
        df: pd.DataFrame | pd.Series
) -> Figure:
    """Transforms DataFrame into valid argument for `core_plot`."""

    if not isinstance(df, pd.DataFrame | pd.Series):
        raise TypeError("DataFrame / Series can be plotted only.")

    # check if "date" and "currency" are already in the index
    if "date" in df.index.names:
        # series = only one column -> return
        if isinstance(df, pd.Series):
            return df
        # if more than one column
        elif hasattr(df, "columns") and "amount" in df.columns:
            return df["amount"]

    if "date" in df.columns and "amount" in df.columns:
        if "currency" in df.columns:
            return df.groupby(["date", "currency"])["amount"].sum()
        return df.groupby("date").amount.sum()
    
    raise PlotError("DataFrame / Series does not meet "
                    "the requirements for plot.")


def plot(
    df: pd.DataFrame
):
    #TODO: inaccurate documentation
    """
    Plot accounting information: "date" vs "amount" grouped by "currency" (if
    existent).
    Plot a DataFrame `df` that match the following patterns:
    * `df` contains a column called "date" and "amount". The column "currency"
    is optional.
    * `df` is indexed by "date" and has the column "amount". The column 
    "currency" is optional.
    * `df` is indexed by "date" and "currency" or "currency" and "date".
    """

    plotfunc = (date_currency_plot 
                if "currency" in df.index.names or (hasattr(df, "columns") and 
                                                    "currency" in df.columns) 
                else date_plot)
    fig = plotfunc(transform(df))
    return fig