from typing import (List, Callable,
                    Optional, TypeVar,)
from datetime import date

from sqlalchemy import Engine

from .parser import (parse_arithmetic_operation,
                     parse_currency,
                     parse_date,
                     parse_double_currency,
                     parse_record_from_id,)
from .typing import KeybindDictType, FixedColumnsType
from .dictops import resolve_value
from .jops import jprint


#region ============================ utils =====================================

DATE_SUCCESS_FORMAT = "%a %d %b %Y"

T = TypeVar(name="T")


def success(*s : str) -> None:
    """Quick success printer that wraps `repr` on `*s`."""
    if len(s) == 1:
        res = s[0]
    else:
        res = ', '.join(map(repr, s))
    print(f"Success: {res}.")


def softerror(e: Exception) -> None:
    """Prints the exception message but does not raises it."""
    print(f"{type(e).__name__}: {e}")


#endregion =====================================================================


def main_loop(
        uinput: Optional[str],
        prompt: str,
        parser: Callable,
        on_error: Callable = softerror,
        max_attempts: int = 5,
        **kwargs
):
    """
    Main loop event. Asks for valid `uinput` until parser returns success or
    `max_attempts` is reached (in which case `RuntimeError` is raised). 
    Quietly prints `ValueError` and `TypeError` to let end-user know that 
    `uinput` is effectively wrong. Any other error is raised and loop is broken.
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


def prompt_arithmetic_operation(
        user_input : Optional[str | float | int] = None, 
        lbound: float = 0.0
) -> float | int :
    """
    Asks for arithmetic operation as `str`. 
    Relies on `parse_arithmetic_operation`.
    """
    # type checking
    if isinstance(user_input, int | float):
        return user_input

    kwargs = {
        "prompt" : "Type valid aithmetic operation: ",
        "parser" : parse_arithmetic_operation,
        "lbound" : lbound
    }
    res = main_loop(user_input, **kwargs)
    success(res)
    return res


def prompt_currency(
        currency_input : Optional[str] = None,
        quiet : bool = True
) -> str:
    """
    Parses `currency_input` to a valid currency. Relies on `parse_currency`.
    Returns upper-3-word-length ISO currency.
    """

    kwargs = {
        "prompt" : "Currency in ISO format: ", 
        "parser" : parse_currency
    }
    res = main_loop(currency_input, **kwargs)
    if not quiet:
        success(res)
    return res


def prompt_date_operation(
        date_input : Optional[str | date] = None
) -> date:
    """Converts `str` into `datetime.date` type."""
    # type checking
    if isinstance(date_input, date):
        return date_input

    kwargs = {
        "prompt" : "Insert date operation: ",
        "parser" : parse_date
    }
    res : date = main_loop(date_input, **kwargs)
    success(res.strftime(DATE_SUCCESS_FORMAT))
    return res


def prompt_double_currency(
        default_currency : str,
        double_curr_input : str | None = None, 
        lbound : float = 0.0
) -> tuple[float, str]:
    """Converts `str` into valid (amount, currency) pair."""
    # type checking
    
    kwargs = {
        "prompt" : "Type double-currency operation: ",
        "parser" : parse_double_currency,
        "default_currency" : default_currency,
        "lbound" : lbound
    }
    amount, currency = main_loop(double_curr_input, **kwargs)
    success(amount, currency)
    return amount, currency


def get_from_nested_dict(
        kdict : KeybindDictType, 
        uinput : Optional[str], 
        prompt : str,
) -> Optional[dict | str]:
    """Gets value associated to key `uinput` If nested then recursively looks for it."""
    # Type checking

    # no input? interactively ask
    if uinput is None:
        jprint(kdict)
        uinput = input(prompt)

    # check if it's dictionary
    res = kdict.get(uinput)
    if isinstance(res, dict):
        res = get_from_nested_dict(res, None, prompt)
        return res
    # try to parse, otherwise soft_print ValueError
    try:
        return resolve_value(uinput, kdict)
    except ValueError as e:
        softerror(e)


def prompt_category_from_keybinds(
        keybind_dict : KeybindDictType,
        keyinput : Optional[str] = None,
        max_attempts : int = 5,
        quietsuccess : bool = False,
) -> str:
    """Asks valid category from keybinds interactively."""

    # Type checking

    prompt = "Type the corresponding key from the dictionary above: "
    category = None
    counter = 0
    
    # main loop
    while category is None and counter < max_attempts:
        category = get_from_nested_dict(keybind_dict, keyinput, prompt)
        keyinput = None
        counter += 1
    # failure
    if category is None:
        raise RuntimeError(f"Only {max_attempts=} are allowed.")
    # success
    if not quietsuccess:
        success(category)
    return category


#-----------------------------------------------
# The following function aims to cover the following
# possibilities
# [categories] (e.g. ['amount', 'description']) // prolly never gonna happen
# string_with_spaces_initial_of_categories
#    e.g. "am des cu" -> [amount, description, currency]
# string_with_spaces_full_column
#    e.g. "amount description" -> [amount, description]
#-----------------------------------------------

def prompt_list_of_fields(
        user_input : Optional[str] = None
) -> List[str]:
    """
    Prompts list of fields from manually crafted keybinds dict. Possible 
    escenarios include:
    * abbv form: "a desc c" -> [amount, description, currency]
    * full col names: "amount description" -> [amount, description]
    
    Relies on listable `parse_valid_element_list`.
    """
    # typecheck

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
    def _parser( unsplit_cols : str ) -> List[str]:
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
    
    # type check

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


def prompt_entity_by_id(
        engine: Engine, 
        entity: T,
        id_: Optional[str | int] = None,
) -> T:
    """Returns `Record` object from given `id`."""
    kwargs = {
        "prompt": "Type id to be filtered: ",
        "parser": parse_record_from_id,
        "engine": engine,
        "entity": entity
    }
    res = main_loop(id_, **kwargs)
    success(res)
    return res