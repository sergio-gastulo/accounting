import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Rectangle
from matplotlib.axes import Axes
from matplotlib.backend_bases import Event
from numpy import atleast_1d


from typing import List, Literal, Iterable
from sqlalchemy import select, not_, case, extract, ColumnElement, Label
from sqlalchemy.sql import functions, func
from sqlalchemy.orm import Session

from db.model import Record
from context.context import ctx
from utilities.core import pprint_df
from utilities.parser import parse_period
from utilities.prompt import prompt_category_from_keybinds


#region ========================== global constants ============================


CurrencyAmountType = dict[str, float]
INCLUDING_INFLOW = Record.category.in_(ctx.inflow_categories)
PERIOD_COL : Label[str] = func.strftime('%Y-%m', Record.date).label("period")
TOTAL_AMOUNT_COL = functions.sum(Record.amount).label("total_amount")

#endregion =====================================================================


#region ======================= helper functions ===============================

def darkmode() -> None:
    """Sets matplotlib darkmode at evaluation time."""
    plt.style.use('dark_background')
    plt.rcParams['font.family'] = 'monospace'
    plt.rcParams['font.size'] = 12


def sum_currencies(
        amounts : CurrencyAmountType
) -> CurrencyAmountType:
    """
    Convert a multi-currency portfolio into each target currency.
    Each output is the sum of every input amount converted to each input amount.

    Arguments
    --------
    amounts
        A dictionary with currencies and keys and their respective amounts as 
        floats.

    Example
    -------
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

def get_currency_list_by_period(
        period : pd.Period
) -> List[str]:
    q = select(Record.currency.distinct())
    q = q.where(*_by_period(period))
    
    with Session(ctx.engine) as session:
        currencies = list(session.scalars(q))
        currencies.sort()
        return currencies

#endregion =====================================================================



#region ========================== first-plot ==================================

def _quick_filter(
        period : pd.Period,
        category : str,
        currency : str
) -> pd.DataFrame:
    # --- why calling the database instead of filtering in pandas? ---
    # --- wellp, when group_by(Record.category) is called, description  ---
    # --- is lost, it can't be retrieved ---

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
    # --- make it thread over lists of Rectangles ---
    if isinstance(bar, Iterable) and isinstance(bar[0], Rectangle):
        for single_bar in bar:
            _set_labels(ax, max_x_value, currency, single_bar)
        return
    
    # --- set amount label ---
    width   = bar.get_width()
    inside  = width > (max_x_value / 2)
    xpos    = ( 0.5 if inside else 1.1 ) * width
    ypos    = bar.get_y() + bar.get_height() / 2
    color   = 'black' if inside else 'white'
    label   = f'{width:.2f} {currency}'
    txt     = ax.text(
        xpos, ypos, label, va='center', 
        ha='left', fontsize=10, color=color
    )

    # --- check if text is cutoff by the bar ---
    bbox        = txt.get_window_extent()
    bar_right   = ax.transData.transform((width, 0))[0]
    if bbox.x1 > bar_right:
        txt.set_position((1.1 * width, ypos))
        txt.set_color('white')


def _barchart_core(
        df : pd.DataFrame,
        currency : str,
        append : List,
        ax : Axes
) -> None:
    """Displays barchart of dataframe, previously filtered by currency."""

    # --- setting main bars ---
    # TODO: change color if darkmode has been called and viceversa
    ax.barh(df.index, df.total_amount, color=(1, 1, 1), align='center')
    ax.tick_params(axis='y', labelsize=10.5)

    # --- set labels on each bar ---
    max_val = df["total_amount"].max()
    _set_labels(ax, max_val, currency)

    # --- set text top right with total sum of amounts ---
    total = df["total_amount"].sum()
    label = f'{currency} {total:.2f}'
    xy = (0.90, 0.95)
    ax.text(*xy, label, transform=ax.transAxes, ha="left", va="top", fontsize=12)
    
    # --- append for event listener and return axis obj ---
    categories = df.index.to_list()
    append.append((ax, categories, currency))
    # return ax


def _pre_on_click(
        event : Event,
        period : pd.Period,
        meta : List[tuple[Axes, str, str]]
) -> None:
    for ax, categories, currency in meta:
        if event.inaxes == ax:
            for bar, category in zip(ax.patches, categories):
                contains, _ = bar.contains(event)
                if contains:
                    bar.set_color(ctx.bar_color)
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


# alias: p1
def barchart_by_period(period: str | int | pd.Period | None = None) -> None:
    """
    Displays a barchart from database records grouped by category and 
    currency for the given period.

    Arguments
    ---------
    period
        Defaults to ctx.period, which is this months' period. Allows period
        arithmetic from `parse_period`.

    Notes
    -----
    Clicking on a bar:
        - Highlights it in red. 
        - Prints the related records (date, description, amount).
    """
    # --- ensure valid period, maybe change to prompter? ---
    period = parse_period(period, ctx.period)

    # --- query construction ---
    q = select(Record.currency, Record.category, TOTAL_AMOUNT_COL)
    q = q.where(*_by_period(period), not_(INCLUDING_INFLOW))
    q = q.group_by(Record.currency, Record.category)
    df = pd.read_sql(q, ctx.engine, index_col=['currency', 'category'])
    currencies = df.groupby(level=0)["total_amount"].count().to_dict()

    # --- main figure creation ---
    metadata = []
    nrows = len(currencies)
    heights = list(currencies.values())
    fig, axs = plt.subplots(
        nrows, 1, sharex=True, 
        gridspec_kw={'height_ratios': heights}
    )
    axs : List[Axes] = atleast_1d(axs)

    # --- populating horizontal bars ---
    for i, (currency, _) in enumerate(currencies.items()):
        _barchart_core(df.loc[currency], currency, metadata, axs[i])
    
    # --- setting plot header ---
    header = _get_header(df, period)
    fig.suptitle(header)
    fig.subplots_adjust(left=0.25, right=0.95)

    # --- connect on_click event ---
    on_click = lambda event : _pre_on_click(event, period, metadata)
    fig.canvas.mpl_connect('button_press_event', on_click)
    plt.show()


#endregion =====================================================================





# alias: p2
def expenses_time_series(period: str | pd.Period | None = None) -> None:
    """
    Plot spendings (complement of `inflow_categories`) as a time series grouped 
    by given `period`.

    Arguments
    ---------
    period
        The given period that will be highlighted in the plot. Defaults to 
        ctx.period. Allows period arithmetic.
    """

    period = parse_period(period, ctx.period)

    q = select(Record.currency, PERIOD_COL, TOTAL_AMOUNT_COL)
    q = q.where(not_(INCLUDING_INFLOW))
    q = q.group_by(Record.currency, PERIOD_COL)
    df = pd.read_sql(
        q, ctx.engine, 
        parse_dates={"period": {"format" : "%Y-%m"}}
    )
    df.period = df.period.dt.to_period('M')
    currency_list_in_period = get_currency_list_by_period(period)

    def core(
            df: pd.DataFrame, 
            currency: str, 
            color: str, 
            ax = None, fig = None
    ) -> None:
        
        ax.plot(
            df.index.to_timestamp(), 
            df, 
            marker='o', color=color, label=currency)
        
        if currency in currency_list_in_period:
            scatter_value = df.loc[period, "total_amount"]
            period_ts = period.to_timestamp()
            ax.scatter(
                period_ts, 
                scatter_value, 
                color='red', zorder=5
            )
            x = period_ts + pd.Timedelta(days=10)       # x-axis + offset
            y = scatter_value * 1.05                    # y-axis * offset
            text = f'{currency} {scatter_value:.2f}'
            ax.text(x, y, s=text, size=12)
        else:
            print(f"'{currency}' is not available to be scattered.")

        ax.set_xlabel('Date', labelpad=16)
        fig.autofmt_xdate()

    fig, ax = plt.subplots()

    for currency in ctx.currency_list:
        color = ctx.colors[currency]
        df_currency = df.loc[
            df.currency == currency.upper(), 
            ['period', 'total_amount']
        ].set_index('period')
        core(df_currency, currency.upper(), ax=ax, fig=fig, color=color)
    
    fig.suptitle("Spendings as a Time Series per Currency")
    plt.show()


# alias: p3
def category_time_series(
        category: str | None = None,
        freq : Literal["w", "weekly", "m", "monthly"] = "m",
) -> None:
    """
    Plot a time series for the given category.
    Useful for categories that should stay around an average (e.g. INGRESOS).
    """
    # --- ensure category by default ---
    category = prompt_category_from_keybinds(ctx.keybinds, category)

    if freq.lower() in ["w", "weekly"]:
        period_column = func.strftime('%Y %W', Record.date).label('period')
        fill_zeroes_freq = "W-MON"
        datetime_operation = lambda df: pd.to_datetime(
            df.period + ' 1',
            format='%Y %U %w'
        )
    elif freq.lower() in ["m", "monthly"]: 
        period_column = PERIOD_COL
        fill_zeroes_freq = "MS"
        datetime_operation = lambda df: pd.to_datetime(
            df.period,
            format='%Y-%m'
        )
    else:
        raise ValueError(f"{freq} is not a valid frequency.")

    query_total = (
        select(
            Record.currency,
            period_column,
            TOTAL_AMOUNT_COL
        ).where(
            Record.category == category,
        ).group_by(
            Record.currency,
            'period'
        )
    )
    df = pd.read_sql(query_total, con=ctx.engine)

    # https://stackoverflow.com/a/52851529/29272030
    df['period'] = datetime_operation(df)

    df = df.pivot(
        index='period',
        columns='currency',
        values='total_amount'
    ).fillna(0)

    # main plot
    fig, ax = plt.subplots()
    for currency in df.columns:
        df_currency = df[currency]
        periods = df_currency.index

        # filling zeroes
        full_period_range = pd.date_range(
            start=periods.min(),
            end=periods.max(),
            freq=fill_zeroes_freq
        ).to_series(name='period')
        empty = pd.Series(0, index=full_period_range, name='period')
        df_currency = df_currency.combine_first(empty)
    
        # plot
        ax.plot(
            df_currency.index,
            df_currency.values,
            color=ctx.colors[currency.lower()], marker='o', label=currency
        )

    ax.set_title(f"{category} Time Series Plot")
    ax.set_xlabel("Spendings")
    ax.set_ylabel("Dates")
    ax.legend()
    fig.autofmt_xdate()
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%b'))
    plt.xticks(rotation=30)
    plt.show()


# alias: sp
def savings_plot():
    query = select(
        PERIOD_COL,
        Record.currency,
        functions.sum(
            case(
                (Record.category.in_(ctx.inflow_categories), +1),
                else_=-1
            ) * Record.amount
        ).label('savings')
    ).group_by(
        'period',
        Record.currency
    )

    df = pd.read_sql(
        query, 
        con=ctx.engine, 
        parse_dates={"period" : {"format" : "%Y-%m"}}
    )
    df.period = df.period.dt.to_period('M')
    df = df.pivot(index='period',columns='currency',values='savings').fillna(0)

    def core(
            df_currency : pd.DataFrame, label : str, color : str, 
            ax = None, fig = None):
        # selecting minimal df for plot
        ax.plot(
            df_currency.index.to_timestamp(), 
            df_currency.cumsum(), 
            marker='o', color=color, 
            label=label
        )
        fig.autofmt_xdate()

    fig, ax = plt.subplots()
    for currency in ctx.currency_list:
        color = ctx.colors[currency]
        core(df[currency.upper()],label=currency, color=color, ax=ax, fig=fig)

    # combining savings into a single column for plotting purposes    
    combined = df.apply(
        lambda row: sum_currencies({
            'pen': row['PEN'],
            'usd': row['USD'],
            'eur': row['EUR']
        })[ctx.default_currency.lower()],
        axis=1
    )

    color = [255 / 255, 99 / 255, 71 / 255]         # redish orange
    core(
        df_currency=combined, 
        label=f"comb-{ctx.default_currency.upper()}",
        color=color, 
        ax=ax, fig=fig
    )

    ax.legend()
    ax.set_xlabel("Year-month period.")
    ax.set_xlabel("Raw saving.")
    fig.suptitle('Savings as a Time Series per Currency')
    plt.show()
