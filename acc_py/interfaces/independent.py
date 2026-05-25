"""
Not to populate main.py with interface-independent functions, 
they're defined from an already loaded `ctx`. Remember, these functions cannot
be imported from other any other `utilities` submodule, since we more likely 
would end up in some sort of ImportError: circular import.
It's okay if most of them are just wrappers.
"""
from pathlib import Path

from classes.context import ctx
from utilities.file import open_file_with_editor


def fopen(p : Path) -> None:
    fopen.__doc__ = open_file_with_editor.__doc__
    open_file_with_editor(p, ctx.editor)


def convert_currency(
        base: float | int,
        basecurr: str, 
        targetcurr: str
) -> float:
    
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