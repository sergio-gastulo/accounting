from typing import (
    Iterable, Optional, Any
)
from datetime import date

import pandas as pd
from pandas import Period
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.backend_bases import Event
from sqlalchemy import (
    select, not_, extract,
)

from pkg.classes import ctx, Record
from pkg.utilities.core import pprint_df
from pkg.utilities.parser import parse_period, parse_date
from pkg.utilities.typing import (
    ValidDateArgument,
    MetadataType,
    NumericType,
    ParsablePeriod,
    EntityFilter,
)

from .shared import (
    INCLUDING_INFLOW, 
    TOTAL_AMOUNT_COL,
    sum_currencies,
    get_bkgcolor,
    negatecolor,
    get_config,
    raise_on_empty,
)

def by_date(
        mindate: date,
        maxdate: date,
) -> EntityFilter:
    return (Record.date.between(mindate, maxdate), )


def by_period(
        period: Period,
) -> EntityFilter:
    """Quick filter by period."""  
    return (
        extract('year', Record.date) == period.year,
        extract('month', Record.date) == period.month
    )


def by_datefilter(args: Any) -> EntityFilter:
    
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

    raise TypeError(
        f"Argument {args} is not a valid `Period`/`datetime.date` type."
    )


def datefilter_str(args: Any) -> str:
    if isinstance(args, ParsablePeriod) or args is None:
        period = parse_period(args, ctx.period)
        month = period.strftime('%B')
        return f"{month}, {period.year}"
    elif isinstance(args, list | tuple):
        datemin = parse_date(args[0])
        datemax = parse_date(args[-1])
        fmt = "%B %d, %Y."
        return f"[{datemin.strftime(fmt)}, {datemax.strftime(fmt)}]"
        
    raise TypeError(
        f"Argument {args} is not a valid `Period`/`datetime.date` type."
    )


def quick_filter(
        datearg: ValidDateArgument,
        category: str,
        currency: str
) -> pd.DataFrame:
    # why calling the database instead of filtering in pandas?
    # wellp, when group_by(Record.category) is called, description 
    # is lost, it can't be retrieved

    q = select(Record.id, 
               Record.date,
               Record.amount, 
               Record.description
            ) \
            .where(
                *by_datefilter(datearg),
                Record.category == category, 
                Record.currency == currency
            ) \
            .order_by(
                Record.amount.desc(), 
                Record.date.desc()
            )
    return pd.read_sql(q, ctx.engine, 'id')


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
    pprint_df(df_category, header=header)


def set_labels(
        ax: Axes,
        max_x_value: NumericType,
        currency: str,
        bar: Rectangle | Iterable[Rectangle] = None,
) -> None:
    
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
    txt = ax.text(
        xpos, ypos, label, va='center', 
        ha='left', fontsize=10, color=color
    )

    # check if text is cutoff by the bar
    bbox = txt.get_window_extent()
    bar_right = ax.transData.transform((width, 0))[0]
    if bbox.x1 > bar_right:
        txt.set_position((1.1 * width, ypos))
        txt.set_color(negcolor)


def barchart_core(
        df: pd.DataFrame,
        currency: str,
        append: list,
        ax: Axes
) -> None:
    """Displays barchart of dataframe, previously filtered by currency."""

    barh_color = get_config("barchart", "default")
    descriptions = df.index.map(
        lambda key: ctx.categories_dict[key]
    )
    ax.barh(
        descriptions, df.total_amount, 
        color=barh_color, align='center'
    )
    ax.tick_params(axis='y', labelsize=10.5)

    # set labels on each bar
    max_val = df["total_amount"].max()
    set_labels(ax, max_val, currency)

    # set text top right corner with total sum of amounts per currency
    total = df["total_amount"].sum()
    label = f'{currency} {total:.2f}'
    xy = (0.90, 0.95)
    ax.text(
        *xy, label, 
        transform=ax.transAxes, 
        ha="left", va="top", 
        fontsize=12
    )
    
    # append for event listener
    categories = df.index.to_list()
    append.append((ax, categories, currency))


def pre_on_click(
        event: Event,
        datearg: ValidDateArgument,
        meta: MetadataType,
) -> None:
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
    amounts = df.groupby(level=0)["total_amount"].sum()
    amounts.index = amounts.index.str.lower()
    res = sum_currencies(amounts.to_dict())
    pretty = ', '.join([
        f"{currency.upper()}: {amount:.2f}"
        for currency, amount in res.items()
    ])

    datestr = datefilter_str(datearg)
    title = f"Outflow registered on {datestr}."
    header = (
        f"{title}\n"
        f"Total accumulated: {pretty}"
    )
    return header


@raise_on_empty
def fetch_barchart_data(
        datearg: ValidDateArgument,
) -> pd.DataFrame:
    q = select(Record.currency, 
               Record.category, 
               TOTAL_AMOUNT_COL) \
        .where(*by_datefilter(datearg),
               not_(INCLUDING_INFLOW)) \
        .group_by(Record.currency, 
                  Record.category)
    
    df = pd.read_sql(q, ctx.engine, 
                     index_col=['currency', 'category'])
    return df


def core_barchart(
        datearg: Optional[ValidDateArgument] = None
) -> Figure:
    
    df = fetch_barchart_data(datearg)    
    currencies = df.groupby(level=0)["total_amount"].count().to_dict()

    # main figure creation
    metadata = []
    nrows = len(currencies)
    heights = list(currencies.values())
    fig, axs = plt.subplots(
        nrows, 1, sharex=True,
        gridspec_kw={'height_ratios': heights}
    )
    axs: list[Axes] = np.atleast_1d(axs)

    # populating with horizontal bars
    for i, (currency, _) in enumerate(currencies.items()):
        barchart_core(df.loc[currency], currency, metadata, axs[i])
    
    # connect on_click event
    on_click = lambda event: pre_on_click(event, datearg, metadata)
    fig.canvas.mpl_connect('button_press_event', on_click)

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
    currency for the given period or lists of periods.

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