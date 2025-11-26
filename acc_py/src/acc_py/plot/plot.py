import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from numpy import atleast_1d
import re
from typing import List

from ..db.model import Record
from sqlalchemy import select, not_
from sqlalchemy.sql import functions, func
from sqlalchemy.orm import Session

from ..context.context import ctx
from ..utilities.miscellanea import pprint_df
from ..utilities.prompt import prompt_category_from_keybinds


# ======================================
#   Global constants
# ======================================

INCOMES_CATEGORIES = ['INGRESO', 'BLIND']
INCLUDING_INCOMES = Record.category.in_(INCOMES_CATEGORIES)
PERIOD_COL = func.strftime('%Y-%m', Record.date).label("period")
TOTAL_AMOUNT_COL = functions.sum(Record.amount).label("total_amount")


# ======================================
#   Helper functions
# ======================================

def get_currency_list_by_period(
        period : str
) -> List[str]: 
    
    query_currencies = select(
        Record.currency.distinct()
        ).where(
            Record.date.like(period + "%"),
            not_(INCLUDING_INCOMES)
        )
    
    with Session(ctx.engine) as session:
        return list(session.scalars(query_currencies))


def on_click_printable(
        period : str,
        category : str,
        currency : str
) -> pd.DataFrame:

    query_printable =  select(
            Record.id, 
            Record.date, 
            Record.amount, 
            Record.description
        ).where(
            Record.date.like(period + "%"),
            Record.category == category,
            Record.currency == currency
        )

    return pd.read_sql(query_printable, con=ctx.engine, index_col='id')


def darkmode() -> None:
    plt.style.use('dark_background')
    plt.rcParams['font.family'] = 'monospace'
    plt.rcParams['font.size'] = 12


# ---------------------------------
# this function aims to provide support for:
#   args:
#   {
#       "eur" : x,
#       "usd" : y,
#       "pen" : z,
#       ...
#   }
#   |->
#   (
#       "eur" : x * fetch_currency(eur, eur) +
#               y * fetch_currency(usd, eur) +
#               z * fetch_currency(pen, eur),
#       "usd" : x * fetch_currency(eur, usd) +
#               y * fetch_currency(usd, usd) +
#               z * fetch_currency(pen, usd),
#       ...
#   )
# ---------------------------------
def sum_currencies(
        curr_amount_dict : dict[str, float | int]
) -> dict[str, str]:

    res_dict = {}
    curr_list = list(curr_amount_dict) 
    for curr in curr_list:
        res_sum = sum([
                curr_amount_dict[key] * ctx.exchange_dictionary[key][curr] for key in curr_list
            ])
        res_dict.update({
            curr : f"{res_sum:.2f}"
        })

    return res_dict


# ======================================
#   Plotting functions
# ======================================


# alias: p1
def categories_per_period(period: str | pd.Period | None = None) -> None:
    """
    Plot database records grouped by category and currency for the given period.

    Clicking on a bar:
        - Highlights it in red.
        - Prints the related records (date, description, amount).
    """

    if period:
        period = pd.Period(period, 'M')
    else:
        period = ctx.period
    period_str = str(period)

    query_totals = (
        select(
            Record.currency, 
            Record.category, 
            TOTAL_AMOUNT_COL
        ).where(
            Record.date.like(period_str + "%"),
            not_(INCLUDING_INCOMES)
        ).group_by(
            Record.currency, 
            Record.category
        )
    )
    
    df = pd.read_sql(query_totals, con=ctx.engine)
    currency_list = get_currency_list_by_period(period_str)

    bars_per_ax = []
    store_totals = {}
    def core_plot_logic(df: pd.DataFrame, currency: str, ax=None, fig=None) -> None:            
        values = df.total_amount
        max_value = max(values)
        labels = [ctx.categories_dict[key] for key in df.category]
        bars = ax.barh(labels, values, height=0.8, color=(1,1,1), align='center')
        ax.tick_params(axis='y', labelsize=10.5)

        bars_per_ax.append((ax, bars, df.category.to_list(), currency))
        
        for bar in bars:
            width   = bar.get_width()
            inside  = width > max_value / 2
            xpos    = (0.5 if inside else 1.1) * width
            ypos    = bar.get_y() + bar.get_height() / 2
            color   = (0,0,0) if inside else (1,1,1)
            
            ax.text(xpos, ypos, f'{width:.2f} {currency}', 
                va='center', ha='left', fontsize=10, color=color
            )
        vals = values.sum()
        store_totals.update({currency.lower() : vals})
        ax.text(0.90, 0.95, f'{currency} {vals:.2f}', transform=ax.transAxes, ha="left", va="top", fontsize=12)
        fig.subplots_adjust(left=0.25, right=0.95)


    def on_click(event):
        for ax, bars, labels, currency in bars_per_ax:
            if event.inaxes == ax:
                for bar, label in zip(bars, labels):
                    contains, _ = bar.contains(event)
                    if contains:
                        bar.set_color('red')
                        df_category = (
                            on_click_printable(
                                period=period_str, 
                                category=label, 
                                currency=currency
                            )
                            .sort_values(by=['amount', 'date'], ascending=False)
                        )
                        header = f"Category: {label}, Currency: {currency}, Total: {df_category.amount.sum()}"
                        pprint_df(df_category, header=header)

                        ax.figure.canvas.draw()
                        return


    heights = [
        len(df.loc[df.currency == currency, 'category'].unique())
        for currency in currency_list
    ]

    fig, axs = plt.subplots(len(currency_list), 1, sharex=True, gridspec_kw={'height_ratios': heights})
    axs = atleast_1d(axs)
    for i, currency in enumerate(currency_list):
        df_currency = df.loc[df.currency == currency, ['category', 'total_amount']].sort_values('total_amount', ascending=False)
        core_plot_logic(df_currency, currency, ax=axs[i], fig=fig)

    currency_totals = sum_currencies(store_totals)

    fig.suptitle(
        f"Spendings registered on {period.strftime("%B")}, {period.year}\n"
        f"Total accumulated on it's own currency: {currency_totals}"
    )

    fig.canvas.mpl_connect('button_press_event', on_click)
    plt.show()


# alias: p2
def expenses_time_series(period: str | pd.Period | None = None) -> None:
    """
    Plot spendings as a time series grouped by period.

    - The given period is highlighted in red.
    - If no period is provided, defaults to ctx.period.
    - If the period is outside the data, nothing is highlighted.
    """

    if period:
        period = pd.Period(period, 'M')
    else: 
        period = ctx.period

    query = (
        select(
            Record.currency,
            PERIOD_COL,
            TOTAL_AMOUNT_COL,
        )
        .where(
            not_(INCLUDING_INCOMES)
        )
        .group_by(
            Record.currency,
            PERIOD_COL,
        )
    )

    df = pd.read_sql(query, con=ctx.engine, parse_dates={"period": {"format" : "%Y-%m"}})
    df.period = df.period.dt.to_period('M')
    currency_list_in_period = get_currency_list_by_period(period=str(period))

    def core_plot_logic(df: pd.DataFrame, currency: str, color: str, ax = None, fig = None) -> None:
        ax.plot(df.index.to_timestamp(), df.values, marker='o', color=color, label=currency)
        
        if currency in currency_list_in_period:
            scatter_value = df.loc[period, "total_amount"]
            ax.scatter(period.to_timestamp(), scatter_value, color='red', zorder=5)
            x = period.to_timestamp() + pd.Timedelta(days=10)       # x-axis + offset
            y = scatter_value * 1.05                                # y-axis * offset
            text = f'{currency} {scatter_value:.2f}'
            ax.text(x, y, s=text, size='12')
        else:
            print(f"'{currency}' is not available to be scattered.")

        ax.set_xlabel('Date', labelpad=16.0)
        fig.autofmt_xdate()


    fig, ax = plt.subplots()

    for currency in ctx.currency_list:
        color = ctx.colors[currency]
        df_currency = df.loc[df.currency == currency, ['period', 'total_amount']].set_index('period')
        core_plot_logic(df_currency, currency, ax=ax, fig=fig, color=color)
    
    fig.suptitle("Spendings as a Time Series per Currency")
    plt.show()


# alias: p3
def category_time_series(category: str | None = None, period: str | pd.Period | None = None) -> None:
    """
    Plot a time series for the given category.

    - The given period is highlighted if present.
    - If the period lies out of the date range, a warning is printed.

    Useful for categories that should stay around an average (e.g. INGRESOS, CASA-ALQUILER).
    """

    # ensuring a valid category
    category = prompt_category_from_keybinds(ctx.keybinds, category)

    if period is None:
        period = ctx.period
    else: 
        period = pd.Period(period, 'M')
    
    timestamp_period = period.to_timestamp()
    period_str = str(period)

    query_total = (
        select(
            Record.currency,
            PERIOD_COL,
            TOTAL_AMOUNT_COL
        ).where(
            Record.category == category
        ).group_by(
            Record.currency,
            PERIOD_COL
        )
    )

    df = pd.read_sql(
        query_total,
        con=ctx.engine,
        parse_dates={"period": {"format": "%Y-%m"}}
    )
    df.period = df.period.dt.to_period('M')

    currency_list_period = df[df.period == period_str].currency.unique()
    currency_list = df.currency.unique()

    # main plot -- not a single scatter here
    fig, ax = plt.subplots()
    for currency in currency_list:
        # https://stackoverflow.com/questions/43206554/typeerror-float-argument-must-be-a-string-or-a-number-not-period
        df_currency = df.loc[df.currency == currency, ['period', 'total_amount']].set_index('period')
        ax.plot(df_currency.index.to_timestamp() , df_currency.total_amount, color=ctx.colors[currency], marker='o', label=currency)

    ax.set_title(f"{category} Time Series Plot")
    ax.set_xlabel("Spendings")
    ax.set_ylabel("Dates")

    def scatter_logic(df: pd.DataFrame, currency: str, ax = None) -> None:
        # scattering red points first
        try:
            color = ctx.colors[currency]
            category_amount_period = df.loc[period, "total_amount"]
            ax.scatter(timestamp_period, category_amount_period, color='red', zorder=5)
            ax.axhline(category_amount_period, color=color, linestyle='dashed')
            ax.text(
                timestamp_period,
                category_amount_period,
                s=f'{currency} {category_amount_period:.2f}',
                size='11',
                # I don't remember how this works, but it calibrates the placement of 'period' as a string in the plot 
                horizontalalignment = 'left' if mdates.date2num(timestamp_period) < ax.get_xlim()[1] / 2 else 'right',
                verticalalignment = 'bottom' if df["total_amount"].get(period - 1, 0) <= category_amount_period else 'top'
            )

            print_df = (
                on_click_printable(
                    period=period_str, 
                    category=category, 
                    currency=currency
                )
                .sort_values('amount')    
            )
            header = f"Category: {category}, Currency: {currency}\n"
            pprint_df(df=print_df, header=header)

        except KeyError:
            print(f"{currency}: Period '{period_str}' is not available for scattering in the current plot")
            return

    if len(currency_list_period) == 0:
        print(f"Period '{period_str}' does not have any records associated to {category}.")

    else:
        for currency in currency_list_period:
            df_currency = df.loc[df.currency == currency, ['period', 'total_amount']].set_index('period')
            scatter_logic(df=df_currency, currency=currency, ax=ax)  

    ax.legend()
    fig.autofmt_xdate()
    plt.show()


# alias: p4
def monthly_time_series(currency: str, period: str | pd.Period | None = None) -> None:
    """
    Plot daily expenses for three months: previous, current, and next.

    - Left: daily spendings.
    - Right: cumulative spendings.
    - Current month in green, others in white.
    - Today marked with a vertical red line (shifted if 'period' is not current).
    - Excludes categories: BLIND, INGRESO.
    """

    if period:
        period = pd.Period(period, 'M')
    else: 
        period = ctx.period

    if not re.match('^[a-zA-Z]{3}$', currency):
        raise Exception(f"'{currency}' not a valid currency")
    else: 
        currency = currency.upper()

    # prev month, this month, next month
    period_list = [str(period + i) for i in range(-1, 2)]
    query = (
        select(
            Record.date,
            TOTAL_AMOUNT_COL
        ).where(
            not_(INCLUDING_INCOMES),
            Record.currency == currency,
            PERIOD_COL.in_(period_list)
        ).group_by(Record.date)
    )
    df = pd.read_sql(
        query,
        con=ctx.engine,
        parse_dates={"date": {"format": "%Y-%m-%d"}}
    )

    def core_plot_logic(df: pd.DataFrame) -> None:
        
        fig, ax = plt.subplots(1, 2, figsize=(12, 5))

        for i, iter_period in enumerate(period_list):

            dframe = df.loc[df.date.dt.strftime('%Y-%m') == iter_period]
            color = (1,1,1) if i != 1 else (0,1,0)
            ax[0].plot(dframe.date, dframe.total_amount, marker='o', color=color)
            ax[1].plot(dframe.date, dframe.total_amount.cumsum(), color=color, marker='o')

        for axes in ax:
            axes.axvline(mdates.date2num(period.asfreq('D', how='start') + pd.Timestamp.today().day), color=(1,0,0))

        fig.suptitle(f'Monthly spendings centered at {period.strftime("%B")}, {period.year} in {currency}')
        fig.supxlabel('Periods', y=-0.1)
        fig.supylabel(f"Spendings in {currency}", x=0.05)
        fig.autofmt_xdate()
        plt.show()


    core_plot_logic(df)

