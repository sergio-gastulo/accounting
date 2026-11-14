from typing import Callable, TypeVar
from datetime import date
from functools import wraps

from sqlalchemy import Engine
from sqlalchemy.orm import Session

from .parser.arith_curr import (DEFAULT_LOWER_BOUND,
                                parse_arithmetic_operation,
                                parse_currency,
                                parse_double_currency,)
from .parser.dates import parse_date
from .typing import KeybindDictType, FixedColumnsType
from .dictops import resolve_value
from .jops import jprint
from .colors import fg


DATE_SUCCESS_FORMAT = "%a %d %b %Y"
MAX_ATTEMPTS_LOOP = 5
T = TypeVar(name="T")


def success(*s: str) -> None:
    """Quick success printer that wraps `repr` on every string in `s`."""
    res = s[0] if len(s) == 1 else ', '.join(map(repr, s)) 
    print(f"{fg.green}Success: {res}.{fg.reset}")


def softerror(e: Exception) -> None:
    """Prints `e` without raising it."""
    print(f"{fg.red}{type(e).__name__}: {e}.{fg.reset}")


def early_return(classinfo):
    """Return first argument directly if `isinstance(., classinfo)` 
    evaluates to `True`."""
    def decorator(func):
        @wraps(func)
        def wrapped(*args, **kwargs):
            first_arg = args[0]
            if isinstance(first_arg, classinfo):
                return first_arg
            res = func(*args, **kwargs)
            return res
        return wrapped
    return decorator


def type_check(classinfo, *, narg: int = 0):
    """Raise TypeError if `n`th argument is not of type `classinfo`."""
    def decorator(func):
        @wraps(func)
        def wrapped(*args, **kwargs):
            first_arg = args[narg]
            if not isinstance(first_arg, classinfo):
                raise TypeError(
                    f"Argument '{first_arg}' is not of type `str`.")
            res = func(*args, **kwargs)
            return res
        return wrapped
    return decorator



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


@early_return(int | float)
@type_check(str)
def prompt_arithmetic_operation(
        user_input: str | float | int | None = None, 
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
@type_check(str)
def prompt_date_operation(
        date_input: str | date | None = None
) -> date:
    """Converts `str` into `datetime.date` type."""
    res: date = main_loop(date_input,
                          prompt="Insert date operation: ",
                          parser=parse_date)
    success(res.strftime(DATE_SUCCESS_FORMAT))
    return res


@type_check(str)
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


@type_check(str, narg=1)
def prompt_double_currency(
        default_currency: str | None = None,
        double_curr_input: str | None = None, 
        lbound : float = DEFAULT_LOWER_BOUND
) -> tuple[float, str]:
    """Converts `str` into valid (amount, currency) pair."""
    amount, currency = main_loop(double_curr_input,
                                 prompt="Type double-currency operation: ",
                                 parser=parse_double_currency,
                                 default_currency=default_currency,
                                 lbound=lbound)
    success(amount, currency)
    return amount, currency


@type_check(str | None, narg=1)
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


@type_check(str | None, narg=1)
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


def get_record_by_id(
        id_: str | int,
        engine: Engine,
        entity: T
) -> T:
    """Takes str | int and returns a record from it."""
    if not isinstance(id_, str | int):
        raise TypeError(f"Argument {id_=} must be String or Numeric type.")
    id_ = int(id_)

    with Session(engine) as session:
        entity = session.get(entity, id_)
    if entity is None:
        raise ValueError(f"Can't get entity with {id_=}.")
    return entity


@type_check(int | str | None, narg=-1)
def prompt_entity_by_id(
        engine: Engine, 
        entity: T,
        id_: str | int | None = None,
) -> T:
    """Returns `Record` object from given `id`."""
    res = main_loop(id_,
                    prompt="Type id to be filtered: ",
                    parser=get_record_by_id,
                    engine=engine,
                    entity=entity)
    success(res)
    return res


#-----------------------------------------------
# The following function aims to cover the following
# possibilities
# [categories] (e.g. ['amount', 'description']) // prolly never gonna happen
# string_with_spaces_initial_of_categories
#    e.g. "am des cu" -> [amount, description, currency]
# string_with_spaces_full_column
#    e.g. "amount description" -> [amount, description]
#-----------------------------------------------

@type_check(str | None)
def prompt_list_of_fields(
        user_input: str | None = None
) -> list[str]:
    """
    Prompts list of fields from manually crafted keybinds dict. Possible 
    escenarios include:
    * abbv form: "a desc c" -> [amount, description, currency]
    * full col names: "amount description" -> [amount, description]
    
    Relies on listable `parse_valid_element_list`.
    """

    # set keybinds and with it construct simple local parser
    keybinds = {
        "d"     : "date",
        "a"     : "amount",
        "c"     : "currency",
        "desc"  : "description",
        "cat"   : "category",
        "b_am"  : "base_amount",
        "b_am"  : "base_currency",
        "t_am"  : "target_amount",
        "t_c"   : "target_currency",
    }
    def _parser( unsplit_cols : str ) -> list[str]:
        """Takes user input and splits it, while calling core parser."""
        split = unsplit_cols.strip().split()
        res =  [    resolve_value(col, keybinds)
                    for col in split                        ]
        return res
    
    # main loop construction
    kwargs = {
        "prompt" : "Write valid elements from list: ",
        "parser" : _parser
    }
    jprint(keybinds)
    res = main_loop(user_input, **kwargs)
    success(*res)
    return res


#-----------------------------------------
# This function aims to return a dictionary:
# {
#     field1: value1,
#     field2: value2,
#     ...
# }
# That will be later converted into a valid Record
# e.g.
# [fields] = prompt_list_of_fields()
# dict = {}
# for field in fields: 
#     dict.update( { field : validate(field) } )
#-----------------------------------------

@type_check(str | None, narg=-1)
def prompt_column_value(
        keybind_dict : KeybindDictType,
        fields_str : str | None = None
) -> FixedColumnsType:
    """
    Asks which columns you'd like to set values to, and runs the corresponding 
    parsers. Example:
    * "d c cat" -> transformed into [cols] -> runs parser associated to them.
    * Only used when writing dataframe or writing list. 
    * `keybind_dict` is necessary to pass to `prompt_category_from_keybinds`.
    """

    # ask which columns are being fixed
    fields = prompt_list_of_fields(fields_str)

    # main loop construction
    def prompt_cat():
        category = prompt_category_from_keybinds(keybind_dict)
        return category
    
    field_func = {
        "date": prompt_date_operation,
        "amount": prompt_arithmetic_operation,
        "currency": prompt_currency,
        "description": input,
        "category": prompt_cat,
        "base_amount": prompt_arithmetic_operation,
        "target_amount": prompt_arithmetic_operation,
        "base_currency": prompt_currency,
        "target_currency": prompt_currency,
    }
    res = {}
    for field in fields:
        val = field_func[field]()
        res.update({ field : val })
    
    return res