from typing import Callable, TypeVar
from datetime import date
from decimal import Decimal
from .parser.arith_curr import (DEFAULT_LOWER_BOUND,
                                parse_arithmetic_operation,
                                parse_currency,
                                parse_double_currency,)
from .parser.dates import parse_date
from .typing import KeybindDictType
from .dictops import resolve_value
from .jops import jprint
from .functools import (success,
                        softerror,
                        early_return,
                        type_check,)


DATE_SUCCESS_FORMAT = "%a %d %b %Y"
MAX_ATTEMPTS_LOOP = 5
T = TypeVar(name="T")


def main_loop(
        uinput: str | None,
        prompt: str,
        parser: Callable,
        on_error: Callable = softerror,
        max_attempts: int = MAX_ATTEMPTS_LOOP,
        **kwargs
):
    """
    Loops until getting a valid answer at most `max_attempts` times. 

    Arguments
    ---------
    uinput
        User input that gets passed at first. If `parser` successfully parser 
        `uinput` at first try, it is returned silently.
    prompt
        What will be prompted as in `input(prompt)`.
    parser
        Function that gets applied to `uinput` for validation. Ideally, 
        `parser` should only raise `ValueError` when failing.
    on_error
        Function that gets called when parser fails. Defaults to `soft_error`.
    max_attempts
        Self explanatory.
    kwargs
        Passed to `parser`.

    Notes
    -----
    * `TypeError`s are interpreted as "please try again". `ValueError` falls 
    under this category as well.
    * Any other `Exception` is raised and the loop finishes.
    """
    for _ in range(max_attempts):
        if uinput is None:
            uinput = input(prompt)
        try:
            value = parser(uinput, **kwargs)
            return value
        except (ValueError, TypeError) as e:
            on_error(e)
            uinput = None

    raise RuntimeError(f"No valid input after {max_attempts} attempts.")


@early_return(int | float | Decimal)
@type_check()
def prompt_arithmetic_operation(
        user_input: str | float | int | Decimal | None = None, 
        lbound: int | float = DEFAULT_LOWER_BOUND
) -> float | int :
    """
    Prompt for arithmetic-like operation.
    """
    res = main_loop(user_input,
                    prompt="Type valid arithmetic operation: ",
                    parser=parse_arithmetic_operation,
                    lbound=lbound)
    success(res)
    return res


@early_return(date)
@type_check()
def prompt_date_operation(
        date_input: str | date | int | None = None
) -> date:
    """Converts `str` into `datetime.date` type."""
    res: date = main_loop(date_input,
                          prompt="Insert date operation: ",
                          parser=parse_date)
    success(res.strftime(DATE_SUCCESS_FORMAT))
    return res


@type_check()
def prompt_currency(
        currency_input: str | None = None,
        quiet: bool = True
) -> str:
    """
    Converts `currency_input` to a valid currency. Relies on `parse_currency`.
    Returns upper-3-word-length ISO currency.
    """
    res = main_loop(currency_input,
                    prompt="Currency in ISO format: ",
                    parser=parse_currency,)
    if not quiet:
        success(res)
    return res


@type_check()
def prompt_double_currency(
        default_currency: str | None = None,
        double_curr_input: str | None = None, 
        lbound: float = DEFAULT_LOWER_BOUND
) -> tuple[float, str]:
    """Converts `str` into valid (amount, currency) pair."""
    amount, currency = main_loop(double_curr_input,
                                 prompt="Type double-currency operation: ",
                                 parser=parse_double_currency,
                                 default_currency=default_currency,
                                 lbound=lbound)
    success(amount, currency)
    return amount, currency


@type_check(["uinput"])
def get_from_nested_dict(
        kdict: KeybindDictType,
        uinput: str | None,
        prompt: str,
) -> dict | str | None:
    """Gets the value of a nested dictionary `kdict` interactively."""
    if uinput is None:
        jprint(kdict)
        uinput = input(prompt)
    res = kdict.get(uinput, None)
    if isinstance(res, dict):
        res = get_from_nested_dict(res, None, prompt)
        return res
    try:
        return resolve_value(uinput, kdict)
    except ValueError as e:
        softerror(e)


@type_check(["keyinput"])
def prompt_category_from_keybinds(
        keybind_dict: KeybindDictType,
        keyinput: str | None = None,
        max_attempts: int = MAX_ATTEMPTS_LOOP,
        quietonsuccess: bool = False,
) -> str:
    """Asks valid category from keybinds interactively."""

    prompt = "Type the corresponding key from the dictionary above: "
    category = None
    counter = 0
    
    while category is None and counter < max_attempts:
        category = get_from_nested_dict(keybind_dict, keyinput, prompt)
        keyinput = None
        counter += 1
    if category is None:
        raise RuntimeError(f"Only {max_attempts=} are allowed.")
    if not quietonsuccess:
        success(category)
    return category