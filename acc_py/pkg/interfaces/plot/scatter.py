from typing import Optional

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sqlalchemy import select, not_
from matplotlib.axes import Axes
from matplotlib.figure import Figure

from pkg.utilities.typing import ParsablePeriod
from pkg.utilities.parser import parse_period
from pkg.utilities.core import pprint_df
from pkg.classes.model import Record
from pkg.classes.context import ctx
from .shared import (YEAR_MONTH_PERIOD_COL,
                     TOTAL_AMOUNT_COL,
                     INCLUDING_INFLOW,
                     negatecolor,
                     get_bkgcolor,
                     raise_on_empty)


def scatter(
    period: pd.Period,
    ax: Axes, 
) -> None:
    """
    Simple scatter that relies on period. It searches for `period` accross 
    all lines in `ax`.
    """
    scatter_color = negatecolor(get_bkgcolor())
    timestamp = period.to_timestamp()
    yoffset = 1.05
    xtext = timestamp + pd.Timedelta(days=10)
    
    for line in ax.lines:    
        # get y data associated to timestamp
        pos = np.argwhere(line.get_xdata() == timestamp)
        if len(pos) != 1:
            raise ValueError(f"Could not scatter {period=} because " \
                             "of multiples matches.")
        n : int = pos[0, 0].tolist()
        y = line.get_ydata()[n]
        ax.scatter(timestamp, y, 
                   color=scatter_color, zorder=5)

        # add text to scatter
        ytext = y * yoffset
        currency = line.get_label()
        text = f'{currency} {y:.2f}'
        ax.text(xtext, ytext, text, size=12)


def scattered_map(
        periods: list[ParsablePeriod],
        ax : Axes,
) -> None:
    """Maps `scatter` accross valid list of parsable periods."""
    # ensure period
    if not (isinstance(periods, list) 
            and isinstance(periods[0], ParsablePeriod)):
        raise TypeError(
            f"Argument {periods=} is not a valid list of parsable periods.")

    for period in periods:
        parsed = parse_period(period, ctx.period)
        scatter(parsed, ax)


@raise_on_empty
def get_outflow_data() -> pd.DataFrame:
    q = select(Record.currency, 
               YEAR_MONTH_PERIOD_COL, 
               TOTAL_AMOUNT_COL) \
        .where(not_(INCLUDING_INFLOW)) \
        .group_by(Record.currency, 
                  YEAR_MONTH_PERIOD_COL)
    
    df = pd.read_sql(
        q, ctx.engine, 
        parse_dates={"period": {"format" : "%Y-%m"}},
        index_col=['currency', 'period']
    )    
    return df


def outflow(
        title : str
) -> tuple[Figure, Axes]:
    """`scattered_outflow` main figure. Not a single scatter is performed."""
    
    df = get_outflow_data()
    fig, ax = plt.subplots()
    for currency in ctx.currency_list:
        color = ctx.colors[currency]
        try:
            by_currency = df.loc[currency.upper()] 
            ax.plot(by_currency, marker='o', color=color, label=currency)
        except KeyError:
            err = f"The given {currency=} is not available in: "
            pprint_df(df, err)

    # decorators
    fig.suptitle("Outflow as a time series grouped by period")
    ax.set_xlabel('Date', labelpad=16)
    wtitle = f"scattered_outflow: {title}"
    fig.canvas.manager.set_window_title(wtitle)
    
    return fig, ax


def scattered_outflow(periods : Optional[list[ParsablePeriod]] = None) -> Figure:
    """
    Plot spendings (complement of `inflow_categories`) as a time series grouped 
    by given `period`.

    Arguments
    -----
    periods
        list of periods (or a single period). If a list of periods is provided,
        scattered_outflow will be called for each element. If a single 
        instance is passed, it will be parsed via `parse_period`, which will 
        default to ctx.period if None is passed.

    Returns
    ---
    figs
        The list of all figures generated.
    """
    # check if it's a list of parsable periods
    if isinstance(periods, list) and isinstance(periods[0], ParsablePeriod):
        fig, ax = outflow("Outflow Time Series")
        scattered_map(periods, ax)
        fig.show()
        return fig

    # single plot. Any typeerror is raised via `parse_period`.
    period = parse_period(periods, ctx.period)
    title = f"Outflow Time Series scattering: {str(period)}"
    fig, ax = outflow(title)
    scatter(period, ax)
    fig.show()
    return fig