from typing import Iterable, Any
from datetime import date

from pandas import Period
import matplotlib.pyplot as plt
from matplotlib.colors import to_rgb
from sqlalchemy.sql import functions, func
from sqlalchemy import (
    Label, extract
)

from pkg.classes.model import Record
from pkg.classes.context import ctx
from pkg.utilities.typing import (
    CurrencyAmountType, 
    EntityFilter, 
    ParsablePeriod,
)
from pkg.utilities.typing import RGBType
from pkg.utilities.parser import (
    parse_date, parse_period
)


#region ========================== constants  ==================================

INCLUDING_INFLOW = Record.category.in_(ctx.inflow_categories)
YEAR_MONTH_PERIOD_COL: Label[str] = func \
                                    .strftime('%Y-%m', Record.date) \
                                    .label("period")
TOTAL_AMOUNT_COL = functions.sum(Record.amount).label("total_amount")

#endregion =====================================================================


#region =========================== configs  ===================================


def set_configs() -> None:
    """Load from ctx.matplotlib and set it."""
    
    if (fontfamily := ctx.matplotlib.get('fontfamily')) : 
        plt.rcParams['font.family'] = fontfamily

    if (fontsize := ctx.matplotlib.get('fontsize')) : 
        plt.rcParams['font.size'] = fontsize


def dark() -> None:
    """Sets matplotlib darkmode at evaluation time."""
    plt.style.use('dark_background')


def get_bkgcolor() -> RGBType:
    return to_rgb(plt.rcParams["figure.facecolor"])


def negatecolor(color: Iterable) -> RGBType:
    return tuple(1 - c for c in color)


def get_config(
        plotkey : str, 
        subkey : str, 
        /,
) -> RGBType | None:
    try:
        config = ctx.matplotlib.get("plots")
    except AttributeError:
        return None
    else:
        config = config.get(plotkey)
        return config.get(subkey)


#endregion =====================================================================


def sum_currencies(
        amounts : CurrencyAmountType
) -> CurrencyAmountType:
    """
    Convert a multi-currency portfolio into each target currency.
    Each output is the sum of every input amount converted to each input amount.

    Arguments
    ---------
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