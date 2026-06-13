"""
Not to populate main.py with interface-independent functions, 
they're defined from an already loaded `ctx`. Remember, these functions cannot
be imported from other any other `utilities` submodule, since we more likely 
would end up in some sort of ImportError: circular import.
It's okay if most of them are just wrappers.
"""
from pathlib import Path

from ..classes.context import ctx
from ..utilities.file import open_file_with_editor


def fopen(p : Path) -> None:
    """
    Opens a file `p` via `ctx.editor`.

    Arguments
    ---------
    p
        Path to be opened.
    """
    open_file_with_editor(p, ctx.editor)


def convert_currency(
        base: float | int,
        basecurr: str, 
        targetcurr: str
) -> float:
    """
    Convert a (amount, currency) pair into a target currency. 

    Arguments
    ---------
    base
        The base amount.
    basecurr
        The currency associated to base.
    targetcurr
        To which currency the (amount, currency) pair should me converted to.

    Notes
    -----
    - This relies on `ctx.exchange_dict`. If None is associated, function will 
    fail ungracefully.
    """
    
    # ensure ctx.exchange_dictionary exists.
    if ctx.exchange_dictionary is None:
        err =   f"Argument ctx.exchange_dictionary is None." \
                f"Consider evaluating `load()` to fetch the dictioanry."
        raise ValueError(err)

    exchange = ctx.exchange_dictionary
    # not type-checking arguments ...
    # but checking if they actually exist in exchange
    try:
        val = base * exchange[basecurr][targetcurr]
        return val
    except KeyError:
        err =   f"Arguments {basecurr=} and {targetcurr=}" \
                f"are no where to be found in dictionary: {exchange}."
        raise ValueError(err)