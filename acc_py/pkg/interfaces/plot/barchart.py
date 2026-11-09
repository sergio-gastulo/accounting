from typing import Iterable, Optional, Any
from datetime import date

import pandas as pd
from pandas import Period
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.backend_bases import Event
from sqlalchemy import (select, 
                        not_, 
                        extract,)

from pkg.classes import ctx, Record
from pkg.coreutils.dataframe import pprint_df
from pkg.coreutils.parser import parse_period, parse_date
from pkg.coreutils.typing import (ValidDateArgument,
                                  MetadataType,
                                  NumericType,
                                  ParsablePeriod,
                                  EntityFilter,)

from .shared import (INCLUDING_INFLOW,
                     TOTAL_AMOUNT_COL,
                     MATPLOTLIB_DAY_FORMAT,
                     sum_currencies,
                     get_bkgcolor,
                     negatecolor,
                     get_config,
                     raise_on_empty,)

def by_date(
        mindate: date,
        maxdate: date,
) -> EntityFilter:
    """Quick filter Record by date"""
    # needs to be a tuple, 
    # since it's later passed as f(*by_date())
    return (Record.date.between(mindate, maxdate), )


def by_period(
        period: Period,
) -> EntityFilter:
    """Quick filter Record by period."""
    return (extract('year', Record.date) == period.year,
            extract('month', Record.date) == period.month)


def by_datefilter(args: Any) -> EntityFilter:
    """Parse arguments and return `by_date` or `by_period` filter."""
    
    if isinstance(args, ParsablePeriod) or args is None:
        period = parse_period(args, ctx.period)
        return by_period(period)
    if isinstance(args, list | tuple):
        datemin = parse_date(args[0])
        datemax = parse_date(args[-1])
        if datemin > datemax:
            print("Arguments have been swapped to avoid empty DataFrame.")
            return by_date(datemax, datemin) 
        return by_date(datemin, datemax)

    raise ValueError(
        f"Argument '{args}' could not be parsed as period nor datetime.")


def datefilter_str(args: Any) -> str:
    """Stringify datetime filter for plot header."""

    if isinstance(args, ParsablePeriod) or args is None:
        period = parse_period(args, ctx.period)
        month = period.strftime('%B')
        return f"{month}, {period.year}"
    elif isinstance(args, list | tuple):
        datemin = parse_date(args[0])
        datemax = parse_date(args[-1])
        fmt = MATPLOTLIB_DAY_FORMAT
        return f"[{datemin.strftime(fmt)}, {datemax.strftime(fmt)}]"
        
    raise ValueError(
        f"Argument '{args}' could not be parsed as period nor datetime.")


def quick_filter(
        datearg: ValidDateArgument,
        category: str,
        currency: str
) -> pd.DataFrame:
    # why calling the database instead of filtering in pandas?
    # wellp, when group_by(Record.category) is called, description 
    # is lost, it can't be retrieved

    q = (select(Record.id,
                Record.date,
                Record.amount, 
                Record.description)
            .where(*by_datefilter(datearg),
                   Record.category == category,
                   Record.currency == currency)
            .order_by(Record.amount.desc(),
                      Record.date.desc()))
    
    return pd.read_sql(q, ctx.engine, Record.id.key)


def quick_printer(
        datearg: ValidDateArgument,
        category: str,
        currency: str,
)-> None:
    df_category = quick_filter(datearg, category, currency)
    header = (
        f"Category: {category}," 
        f"Currency: {currency},"
        f"Total: {df_category.amount.sum()}"
    )
    pprint_df(df_category, header)


def set_labels(
        ax: Axes,
        max_x_value: NumericType,
        currency: str,
        bar: Rectangle | Iterable[Rectangle] = None,
) -> None:
    """Set labels at top rigth corner of `ax`."""
    
    if bar is None:
        bar = ax.patches
    # make it thread over lists of Rectangles
    if isinstance(bar, Iterable) and isinstance(bar[0], Rectangle):
        for single_bar in bar:
            set_labels(ax, max_x_value, currency, single_bar)
        return
    
    # set amount label
    figcolor = get_bkgcolor()
    negcolor = negatecolor(figcolor)
    width = bar.get_width()
    inside = width > (max_x_value / 2)
    xpos = ( 0.5 if inside else 1.1 ) * width
    ypos = bar.get_y() + bar.get_height() / 2
    color = figcolor if inside else negcolor
    label = f'{width:.2f} {currency}'
    txt = ax.text(xpos, ypos, label,
                  va='center', ha='left',
                  fontsize=10, color=color)

    # check if text is cutoff by the bar and adjust
    bbox = txt.get_window_extent()
    bar_right = ax.transData.transform((width, 0))[0]
    if bbox.x1 > bar_right:
        txt.set_position((1.1 * width, ypos))
        txt.set_color(negcolor)


def _barchart(
        df: pd.DataFrame,
        currency: str,
        append: list,
        ax: Axes
) -> None:
    """Displays barchart of `df`, previously filtered by `currency`."""

    barh_color = get_config("barchart", "default")
    descriptions = df.index.map(
        lambda key: ctx.categories_dict[key]
    )
    ax.barh(descriptions, df[Record.amount.key], 
            color=barh_color, align='center')
    ax.tick_params(axis='y', labelsize=10.5)

    # set labels on each bar
    max_val = df[Record.amount.key].max()
    set_labels(ax, max_val, currency)

    # set text top right corner with total sum of amounts per currency
    total = df[Record.amount.key].sum()
    label = f'{currency} {total:.2f}'
    x, y = 0.90, 0.95
    ax.text(x, y, label,
            transform=ax.transAxes,
            ha="left", va="top",
            fontsize=12)
    
    # append for event listener
    categories = df.index.to_list()
    append.append((ax, categories, currency))


def on_click(
        event: Event,
        datearg: ValidDateArgument,
        meta: MetadataType,
) -> None:
    """Event listener"""
    color = get_config("barchart", "on_click")
    for ax, categories, currency in meta:
        if event.inaxes == ax:
            for bar, category in zip(ax.patches, categories):
                contains, _ = bar.contains(event)
                if contains:
                    bar.set_color(color)
                    quick_printer(datearg, category, currency)
                    ax.figure.canvas.draw()


def get_header(
        df: pd.DataFrame,
        datearg: ValidDateArgument
) -> str:
    """Get barchart header."""

    # NOTE: is this efficient?
    amounts = df.groupby(level=0)[Record.amount.key].sum()
    amounts.index = amounts.index.str.lower()
    res = sum_currencies(amounts.to_dict())
    pretty = ', '.join([
        f"{currency.upper()}: {amount:.2f}"
        for currency, amount in res.items()
    ])

    datestr = datefilter_str(datearg)
    title = f"Outflow registered on {datestr}."
    header = (f"{title}\n"
              f"Total accumulated: {pretty}")
    return header


@raise_on_empty
def fetch_barchart_data(
        datearg: ValidDateArgument,
) -> pd.DataFrame:
    """Get data for barchart, grouped by."""
    
    q = (select(Record.currency,
                Record.category,
                TOTAL_AMOUNT_COL)
        .where(*by_datefilter(datearg),
               not_(INCLUDING_INFLOW))
        .group_by(Record.currency, 
                  Record.category))
    
    indexes = [Record.currency.key, Record.category.key]
    return pd.read_sql(q, ctx.engine, indexes)


def core_barchart(
        datearg: Optional[ValidDateArgument] = None
) -> Figure:
    """
    Plots barchart from `datearg` filter. 
    Iterates on `_barchart` for each currency in fetched df.
    """

    # data fetch
    df = fetch_barchart_data(datearg)    
    currencies = (df
                  .groupby(level=Record.currency.key)
                  [Record.amount.key]
                  .count()
                  .to_dict())

    # main figure creation
    metadata = []
    nrows, ncols = len(currencies), 1
    heights = list(currencies.values())
    fig, axs = plt.subplots(nrows, ncols, 
                            sharex=True,
                            gridspec_kw={'height_ratios': heights})
    axs: list[Axes] = np.atleast_1d(axs)

    # populating with horizontal bars
    for ax, currency in zip(axs, currencies):
        _barchart(df.loc[currency], currency, metadata, ax)
    
    # connect on_click event
    elistener = lambda event: on_click(event, datearg, metadata)
    fig.canvas.mpl_connect('button_press_event', elistener)

    # decorators
    header = get_header(df, datearg)
    fig.suptitle(header)
    fig.subplots_adjust(left=0.25, right=0.95)
    datestr = datefilter_str(datearg)
    wtitle = f"Barchart by period: {datestr}."
    fig.canvas.manager.set_window_title(wtitle)

    return fig


def barchart_by_datefilter( 
        dateargs: Optional[list[ValidDateArgument]] = None, 
) -> list[Figure]:
    """
    Displays a barchart from database records grouped by category and 
    currency for the given period or lists of periods or parsable date-filters.

    Arguments
    -----
    periods
        List of periods (or a single period). If a list of periods is provided,
        _barchart_by_period will be called for each element. If a single 
        instance is passed, it will be parsed via `parse_period`, which will 
        default to ctx.period if none is provided.

    Returns
    ---
    figs
        The list of all figures generated.

    Notes
    -
    Clicking on a bar:
        - Highlights it in red. 
        - Prints the related records (date, description, amount).
    """
    if dateargs is None or isinstance(dateargs, ParsablePeriod):
        fig = core_barchart(dateargs)
        fig.show()
        return fig

    if not isinstance(dateargs, list):
        raise TypeError(f"Invalid argument signature for {dateargs}.")

    try:
        periods = [parse_period(period, ctx.period) for period in dateargs]
    except ValueError:
        if len(dateargs) != 2:
            raise ValueError(
                f"Tried to parse {dateargs} as a two-length list of dates.")
        fig = core_barchart(dateargs)
        fig.show()
        return fig    
    else:
        figs = [core_barchart(period) for period in periods]
        plt.show()
        return figs