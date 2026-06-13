from typing import (
    List, Iterable, Optional, 
    TypeAlias, Literal
)

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Rectangle
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.backend_bases import Event
from matplotlib.colors import to_rgb
from sqlalchemy import (
    select, not_, case, extract, 
    ColumnElement, Label
)
from sqlalchemy.sql import functions, func

from ..classes.model import Record
from ..classes.context import ctx
from ..utilities.core import RGBType, ensure, pprint_df
from ..utilities.parser import parse_period
from ..utilities.prompt import prompt_category_from_keybinds


#region ========================== global constants ============================


CurrencyAmountType = dict[str, float]
ParsablePeriod : TypeAlias = str | int | pd.Period
ListParsablePeriod : TypeAlias = List[ParsablePeriod] | ParsablePeriod
FrequencyType : TypeAlias = Literal["m", "monthly", "w", "weekly"]

INCLUDING_INFLOW = Record.category.in_(ctx.inflow_categories)
YEAR_MONTH_PERIOD_COL : Label[str] = func.strftime('%Y-%m', Record.date).label("period")
TOTAL_AMOUNT_COL = functions.sum(Record.amount).label("total_amount")


#endregion =====================================================================


#region ======================= helper functions ===============================

def set_configs() -> None:
    """Load from ctx.matplotlib and set it."""
    
    if (fontfamily := ctx.matplotlib.get('fontfamily')) : 
        plt.rcParams['font.family'] = fontfamily

    if (fontsize := ctx.matplotlib.get('fontsize')) : 
        plt.rcParams['font.size'] = fontsize


def dark() -> None:
    """Sets matplotlib darkmode at evaluation time."""
    plt.style.use('dark_background')


def sum_currencies(
        amounts : CurrencyAmountType
) -> CurrencyAmountType:
    """
    Convert a multi-currency portfolio into each target currency.
    Each output is the sum of every input amount converted to each input amount.

    Arguments
    ----
    amounts
        A dictionary with currencies and keys and their respective amounts as 
        floats.

    Example
    ---
        >>> convert_currencies({"eur": 1, "usd": 1, "pen": 1})
        {'eur': 1.92, 'usd': 2.10, 'pen' : 7.23}
    """

    currencies = [curr.lower() for curr in amounts]
    res_dict = {}
    for curr1 in currencies:
        res_sum = 0
        for curr2 in currencies:
            exchange = ctx.exchange_dictionary[curr2][curr1]
            res_sum += amounts[curr2] * exchange
        res_dict.update({ curr1 : round(res_sum, 2) })

    return res_dict


def _by_period(period : pd.Period) -> tuple[ColumnElement[bool]]:
    """Quick filter by period."""
    return (
        extract('year', Record.date) == period.year,
        extract('month', Record.date) == period.month
    )


def _get_background_color() -> RGBType:
    return to_rgb(plt.rcParams["figure.facecolor"])


def _negate_color(color : Iterable) -> RGBType:
    ensure(color, Iterable, tuple)
    return tuple(1 - c for c in color)


#endregion =====================================================================



#region =========================== barchart ===================================

def _quick_filter(
        period : pd.Period,
        category : str,
        currency : str
) -> pd.DataFrame:
    # why calling the database instead of filtering in pandas?
    # wellp, when group_by(Record.category) is called, description 
    # is lost, it can't be retrieved

    q = select(Record.id, Record.date, Record.amount, Record.description)
    q = q.where(
        *_by_period(period),
        Record.category == category, 
        Record.currency == currency
    )
    q = q.order_by(Record.amount.desc(), Record.date.desc())
    return pd.read_sql(q, ctx.engine, 'id')


def _quick_printer(
        period : pd.Period,
        category : str,
        currency : str
)-> None:
    df_category = _quick_filter(period, category, currency)
    header = (
        f"Category: {category}," 
        f"Currency: {currency},"
        f"Total: {df_category.amount.sum()}"
    )
    pprint_df(df_category, header=header)


def _set_labels(
        ax : Axes,
        max_x_value : float | int,
        currency : str,
        bar : Rectangle | Iterable[Rectangle] = None,
) -> None:
    
    if bar is None: bar = ax.patches
    # make it thread over lists of Rectangles
    if isinstance(bar, Iterable) and isinstance(bar[0], Rectangle):
        for single_bar in bar:
            _set_labels(ax, max_x_value, currency, single_bar)
        return
    
    # set amount label
    figcolor = _get_background_color()
    negcolor = _negate_color(figcolor)
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


def get_config(plotkey : str, subkey : str, /) -> RGBType | None:
    try:
        config = ctx.matplotlib.get("plots")
        config = config.get(plotkey)
        return config.get(subkey)
    except AttributeError:
        return None


def _barchart_core(
        df : pd.DataFrame,
        currency : str,
        append : List,
        ax : Axes
) -> None:
    """Displays barchart of dataframe, previously filtered by currency."""

    # setting main bars
    # TODO: change color if darkmode has been called and viceversa
    barh_color = get_config("barchart", "default")
    descriptions = df.index.map(lambda key: ctx.categories_dict[key])
    ax.barh(descriptions, df.total_amount, color=barh_color, align='center')
    ax.tick_params(axis='y', labelsize=10.5)

    # set labels on each bar
    max_val = df["total_amount"].max()
    _set_labels(ax, max_val, currency)

    # set text top right with total sum of amounts
    total = df["total_amount"].sum()
    label = f'{currency} {total:.2f}'
    xy = (0.90, 0.95)
    ax.text(*xy, label, transform=ax.transAxes, ha="left", va="top", fontsize=12)
    
    # append for event listener and return axis obj
    categories = df.index.to_list()
    append.append((ax, categories, currency))


def _pre_on_click(
        event : Event,
        period : pd.Period,
        meta : List[tuple[Axes, str, str]]
) -> None:
    color = get_config("barchart", "on_click")
    for ax, categories, currency in meta:
        if event.inaxes == ax:
            for bar, category in zip(ax.patches, categories):
                contains, _ = bar.contains(event)
                if contains:
                    bar.set_color(color)
                    _quick_printer(period, category, currency)
                    ax.figure.canvas.draw()


def _get_header(
        df : pd.DataFrame,
        period : pd.Period
) -> str:
    amounts = df.groupby(level=0)["total_amount"].sum()
    amounts.index = amounts.index.str.lower()
    res = sum_currencies(amounts.to_dict())
    pretty = ', '.join([
        f"{currency.upper()}: {amount:.2f}"
        for currency, amount in res.items()
    ])
    header = (
        f"Outflow registered on {period.strftime("%B")}, {period.year}\n"
        f"Total accumulated: {pretty}"
    )
    return header


def _fetch_barchart_data(period : pd.Period) -> pd.DataFrame:    
    q = select(Record.currency, Record.category, TOTAL_AMOUNT_COL) \
        .where(*_by_period(period), not_(INCLUDING_INFLOW)) \
        .group_by(Record.currency, Record.category)
    
    df = pd.read_sql(q, ctx.engine, index_col=['currency', 'category'])
    return df


def _barchart_by_period(
        period: Optional[ParsablePeriod] = None
) -> Figure:
    # ensure valid period, maybe change to prompter?
    period = parse_period(period, ctx.period)
    df = _fetch_barchart_data(period)
    currencies = df.groupby(level=0)["total_amount"].count().to_dict()

    # main figure creation
    metadata = []
    nrows = len(currencies)
    heights = list(currencies.values())
    fig, axs = plt.subplots(
        nrows, 1, sharex=True, 
        gridspec_kw={'height_ratios': heights}
    )
    axs : List[Axes] = np.atleast_1d(axs)

    # populating with horizontal bars
    for i, (currency, _) in enumerate(currencies.items()):
        _barchart_core(df.loc[currency], currency, metadata, axs[i])
    
    # decorators
    header = _get_header(df, period)
    fig.suptitle(header)
    fig.subplots_adjust(left=0.25, right=0.95)

    # connect on_click event
    on_click = lambda event : _pre_on_click(event, period, metadata)
    fig.canvas.mpl_connect('button_press_event', on_click)
    wtitle = f"barchart by period: {str(period)}"
    fig.canvas.manager.set_window_title(wtitle)
    return fig


def barchart_by_period(
        periods : Optional[ListParsablePeriod] = None, 
) -> List[Figure]:
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
    # check if it's a list of parsable periods
    if isinstance(periods, List) and isinstance(periods[0], ParsablePeriod):
        figs = [_barchart_by_period(period) for period in periods]
        plt.show()
        return figs
    # as _barchar_by_period relies on parse_period, 
    # typeerrors will be raised accordingly if not valid
    fig = _barchart_by_period(periods)
    fig.show()
    return fig


#endregion =====================================================================


#region ========================== scattered  ==================================


def _scatter(
    period : pd.Period,
    ax : Axes, 
) -> None:
    """
    Simple scatter that relies on period. It searches for `period` accross 
    all lines in `ax`.
    """
    scatter_color = _negate_color(_get_background_color())
    timestamp = period.to_timestamp()
    xoffset = pd.Timedelta(days=10)
    yoffset = 1.05
    x = timestamp + xoffset
    
    for line in ax.lines:    
        # get y data associated to timestamp
        # TODO: check if period has been actually found
        pos = np.argwhere(line.get_xdata() == timestamp)
        n : int = pos[0, 0].tolist()
        y = line.get_ydata()[n]
        ax.scatter(timestamp, y, color=scatter_color, zorder=5)

        # add label to said scatter
        ytext = y * yoffset
        currency = line.get_label()
        text = f'{currency} {y:.2f}'
        ax.text(x, ytext, s=text, size=12)


def _scattered_map(
        periods: List[ParsablePeriod],
        ax : Axes,
) -> None:
    """Maps `_scatter` accross valid list of parsable periods."""
    # ensure period
    if not (isinstance(periods, List) and isinstance(periods[0], ParsablePeriod)):
        raise TypeError(f"Argument {periods=} is not a valid list of parsable periods.")

    for period in periods:
        parsed = parse_period(period, ctx.period)
        _scatter(parsed, ax)


def _fetch_outflow_data() -> pd.DataFrame:
    q = select(Record.currency, YEAR_MONTH_PERIOD_COL, TOTAL_AMOUNT_COL) \
        .where(not_(INCLUDING_INFLOW)) \
        .group_by(Record.currency, YEAR_MONTH_PERIOD_COL)
    
    df = pd.read_sql(
        q, ctx.engine, 
        parse_dates={"period": {"format" : "%Y-%m"}},
        index_col=['currency', 'period']
    )    
    return df


def _outflow_fig(
        title : str
) -> tuple[Figure, Axes]:
    """`scattered_outflow` main figure. Not a single scatter is performed."""
    
    df = _fetch_outflow_data()
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


def scattered_outflow(periods : Optional[ListParsablePeriod] = None) -> Figure:
    """
    Plot spendings (complement of `inflow_categories`) as a time series grouped 
    by given `period`.

    Arguments
    -----
    periods
        List of periods (or a single period). If a list of periods is provided,
        _scattered_outflow will be called for each element. If a single 
        instance is passed, it will be parsed via `parse_period`, which will 
        default to ctx.period if None is passed.

    Returns
    ---
    figs
        The list of all figures generated.
    """
    # check if it's a list of parsable periods
    if isinstance(periods, List) and isinstance(periods[0], ParsablePeriod):
        fig, ax = _outflow_fig("Outflow Time Series")
        _scattered_map(periods, ax)
        fig.show()
        return fig

    # single plot. Any typeerror is raised via `parse_period`.
    period = parse_period(periods, ctx.period)
    title = f"Outflow Time Series scattering: {str(period)}"
    fig, ax = _outflow_fig(title)
    _scatter(period, ax)
    fig.show()
    return fig


#endregion =====================================================================


#region ========================== third-plot ==================================

def _get_freq_configs(freq : str = None) -> dict:
    configs = {
        "w" : {
            "period_col" : func.strftime('%Y %W 1', Record.date).label('period'),
            "zeroes" : "W-MON",
            "date_fmt" : '%Y %U %w'
        },
        "m" : {
            "period_col" : YEAR_MONTH_PERIOD_COL,
            "zeroes" : "MS",
            "date_fmt" : '%Y-%m'
        }
    }
    freq = freq.lower()[0]
    if freq in ["m", "w"]: 
        return configs[freq]
    raise ValueError(f"Argument {freq=} is not a valid frequency : 'm' or 'w")


def _fill_zeroes(
        df : pd.DataFrame,
        freq : str
) -> None:
    start = df.index.min()
    end = df.index.max()
    zero_period = pd.date_range(start, end, freq=freq)
    return df.reindex(zero_period).fillna(0)


def _fetch_category_ts_data(periodcol, category, fmt, /) -> pd.DataFrame:
    q = select(Record.currency, periodcol, TOTAL_AMOUNT_COL) \
        .where(Record.category == category) \
        .group_by(Record.currency, 'period')
    df = pd.read_sql(
        q, ctx.engine, 
        parse_dates={'period' : fmt},
        index_col=['currency', 'period']
    )    
    return df


def category_time_series(
        category: Optional[str] = None,
        freq : Optional[FrequencyType] = "m",
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

    configs = _get_freq_configs(freq)
    period = configs["period_col"]
    df = _fetch_category_ts_data(period, category, configs["date_fmt"])

    # main plot
    fig, ax = plt.subplots()

    zeroesfreq : str = configs["zeroes"]
    for currency in ctx.currency_list:
        color = ctx.colors[currency]
        try:
            period_df = df.loc[currency.upper()]
            period_df = _fill_zeroes(period_df, freq=zeroesfreq)
            ax.plot(period_df, color=color, marker='o', label=currency)
    
        except KeyError:
            err = f"The given {currency=} is not available in the following df:"
            pprint_df(df, err)
    
    # decorators
    ax.set_title(f"{category.capitalize()} Time Series Plot")
    ax.set_xlabel("Spendings")
    ax.set_ylabel("Dates")
    ax.legend()
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%b'))
    fig.autofmt_xdate()
    plt.xticks(rotation=30)
    fig.show()

    return fig


#endregion =====================================================================


#region =========================== savings  ===================================


def _fetch_savings_data() -> pd.DataFrame:
    """Quick `savings_plot` data fetcher."""

    # compute savings query
    is_inflow = Record.category.in_(ctx.inflow_categories)
    flow = case((is_inflow, +1), else_=-1) * Record.amount
    savings = functions.sum(flow).label('savings')

    q = select(YEAR_MONTH_PERIOD_COL, Record.currency, savings) \
        .group_by('period', Record.currency)

    df = pd.read_sql(q, ctx.engine, ['period', 'currency'],
        parse_dates={'period' : {'format' : '%Y-%m'}}
    )
    return df


def _get_combined(df : pd.DataFrame) -> pd.DataFrame:
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
    df = _fetch_savings_data()

    fig, ax = plt.subplots()
    # plot per currency
    for currency in ctx.currency_list:
        color = ctx.colors[currency]
        upper = currency.upper()
        period_df = df.xs(upper, level=1)
        ax.plot(period_df.cumsum(), label=upper, color=color, marker='o')

    # combine all currencies and collapse it to ctx.default_currency
    ndf = _get_combined(df)
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


#endregion =====================================================================
