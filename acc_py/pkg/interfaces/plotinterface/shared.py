from typing import Iterable
import functools

from pandas import DataFrame
import matplotlib.pyplot as plt
from matplotlib.colors import to_rgb
from sqlalchemy.sql import functions, func
from sqlalchemy import Label

from pkg.classes.model import Record
from pkg.classes.context import ctx
from pkg.utilities.typing import (
    CurrencyAmountType,
)
from pkg.utilities.typing import RGBType


#region ========================== constants  ==================================

INCLUDING_INFLOW = Record.category.in_(ctx.inflow_categories)
YEAR_MONTH_PERIOD_COL: Label[str] = func \
                                    .strftime('%Y-%m', Record.date) \
                                    .label("period")
TOTAL_AMOUNT_COL = functions.sum(Record.amount).label("total_amount")

#endregion =====================================================================


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


def raise_on_empty(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        res = func(*args, **kwargs)
        if isinstance(res, DataFrame) and res.empty:
            raise ValueError(f"Query returned an empty DataFrame. Args: {args}.")        
        return res
    return wrapper