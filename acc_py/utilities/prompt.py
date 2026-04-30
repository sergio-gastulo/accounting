from datetime import date
from sqlalchemy.engine import Engine
from db.model import Record
from typing import List, Callable, Any, Optional, Type

from utilities.parser import (
    parse_arithmetic_operation,
    parse_currency,
    parse_date,
    parse_double_currency,
    parse_valid_element_list,
    parse_record_from_id,
)
from utilities.core import (
    _jprint,
    KeybindDictType
)


#region ============================ utils =====================================

def _success(*s : str) -> None:
    if len(s) == 1:
        res = s[0]
    else:
        res = ', '.join(s)
    print(f"Success: {res}")


def _soft_error(e : ValueError | TypeError) -> None:
    s = f"{type(e).__name__}: {e}"
    print(s)


def ensure(
        value : Any, 
        *types : Type[Any], 
        allow_none : bool = False
) -> Any:
    
    if allow_none and (value is None):
        return 
    if type(value) in types:
        return 

    _get_type_name = lambda t : t.__name__.capitalize()
    allowed_types = ', '.join(map(_get_type_name, types))
    vartype = type(value).__name__.capitalize()
    
    raise TypeError(
        f"Argument '{value}' has type '{vartype}'. "
        f"Type must be in [{allowed_types}]."
    )


def _ensure_str_none(arg : str | None) -> None:
    ensure(arg, str, allow_none=True)

#endregion =====================================================================


def main_loop(
        uinput : Optional[str],
        prompt : str,
        parser : Callable,
        on_error : Callable = _soft_error,
        max_attempts : int = 5,
        **kwargs
) -> Any:
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
        lower_bound: float = 0.0
) -> float | int :
    
    if isinstance(user_input, int | float):
        return user_input
    ensure(lower_bound, float, int)
    _ensure_str_none(user_input)

    kwargs = {
        "prompt" : "Type valid aithmetic operation: ",
        "parser" : parse_arithmetic_operation,
        "lower_bound" : lower_bound
    }
    res = main_loop(user_input, **kwargs)
    _success(res)
    return res


def prompt_currency(
        currency_input : Optional[str] = None,
        quiet : bool = True
) -> str:
    ensure(quiet, bool)
    _ensure_str_none(currency_input)
    kwargs = {
        "prompt" : "Currency in ISO format: ", 
        "parser" : parse_currency
    }
    res = main_loop(currency_input, **kwargs)
    if not quiet:
        _success(res)
    return res


def prompt_date_operation(
        date_input : Optional[str | date] = None
) -> date:
    if isinstance(date_input, date):
        return date_input
    _ensure_str_none(date_input)

    kwargs = {
        "prompt" : "Insert date operation: ",
        "parser" : parse_date
    }
    res : date = main_loop(date_input, **kwargs)
    _success(res.strftime("%a %d %b %Y"))
    return res


def prompt_double_currency(
        default_currency : str,
        double_curr_input : str | None = None, 
        lower_bound : float = 0.0
) -> tuple[float, str]:
    
    _ensure_str_none(double_curr_input)
    ensure(default_currency, str)
    ensure(lower_bound, float)
    kwargs = {
        "prompt" : "Type double-currency operation: ",
        "parser" : parse_double_currency,
        "default_currency" : default_currency,
        "lower_bound" : lower_bound
    }
    amount, currency = main_loop(double_curr_input, **kwargs)
    _success(str(amount), currency)
    return amount, currency


def get_from_nested_dict(
        kdict : KeybindDictType, 
        uinput : Optional[str], 
        prompt : str
) -> Optional[dict | str]:
    
    _ensure_str_none(uinput)
    ensure(kdict, dict)
    ensure(prompt, str)

    if uinput is None:
        _jprint(kdict)
        uinput = input(prompt).lower()
    res = kdict.get(uinput)

    if isinstance(res, str):
        return res
    elif isinstance(res, dict):
        res = get_from_nested_dict(res, None, prompt)
        return res
    # soft KeyError
    print(f"Argument keyinput={uinput} is not a valid key.")


def prompt_category_from_keybinds(
        keybind_dict : KeybindDictType,
        keyinput : Optional[str] = None,
        max_attempts : int = 5
) -> str:
    
    ensure(keybind_dict, dict)
    ensure(max_attempts, int)
    _ensure_str_none(keyinput)

    prompt = "Type the corresponding key from the dictionary above: "
    category = None
    counter = 0
    
    while category is None and counter < max_attempts:
        category = get_from_nested_dict(keybind_dict, keyinput, prompt)
        keyinput = None
        counter += 1
    
    if category is None:
        raise RuntimeError(f"Only {max_attempts=} are allowed.")
    
    _success(category)
    return category


def prompt_record_by_id(
        engine : Engine, 
        id_ : Optional[str] = None
) -> Record:
    _ensure_str_none(id_)
    kwargs = {
        "prompt" : "Type id to be filtered: ",
        "parser" : parse_record_from_id,
        "engine" : engine
    }
    record : Record = main_loop(id_, **kwargs)
    _success(record.pretty())
    return record


# ------------------------------------------------------
# The following function aims to cover the following
# possibilities
# [categories] (e.g. ['amount', 'description']) // prolly never gonna happen
# string_with_spaces_initial_of_categories
#    e.g. "am des cu" -> [amount, description, currency]
# string_with_spaces_full_column
#    e.g. "amount description" -> [amount, description]
# ------------------------------------------------------

def prompt_list_of_fields(
        user_input : Optional[str] = None
) -> List[str]:
    _ensure_str_none(user_input)
    keybinds = {
        "d"     : "date",
        "a"     : "amount",
        "c"     : "currency",
        "desc"  : "description",
        "cat"   : "category" 
    }
    def _parser(
        unsplit_cols : str
    ) -> List[str]:
        nonlocal keybinds
        split = unsplit_cols.strip().split()
        res =  [    parse_valid_element_list(col, keybinds)
                    for col in split                        ]
        return res
    
    kwargs = {
        "prompt" : "Write valid elements from list: ",
        "parser" : _parser,
        "keybinds" : keybinds
    }
    _jprint(keybinds)
    res = main_loop(user_input, **kwargs)
    _success(*res)
    return res


# ------------------------------------------------
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
# ------------------------------------------------

def _parse_description(s : str) -> str:
    if not isinstance(s, str):
        raise TypeError(f"Invalid string, got {s=}.")
    if not s:
        raise ValueError("Got empty string.")
    return s

def prompt_column_value(
        keybind_dict : dict[str, str],
        fields_str : str | None = None
) -> dict[str, str | int | float | date]:
    
    field_func : dict[str, Callable] = {
        "date" : prompt_date_operation,
        "amount" : prompt_arithmetic_operation,
        "currency": prompt_currency,
        "description": _parse_description,
        "category": lambda : prompt_category_from_keybinds(keybind_dict)
    }

    fields = prompt_list_of_fields(fields_str)
    res = {}
    for field in fields:
        val = field_func[field]()
        res.update( { field : val } )
    
    return res