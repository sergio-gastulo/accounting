"""
First file that is run.
Should not import **ANY** hand-written acccli-related code.
It contains a variety of functions that are used in context.py, parser.py 
and prompt.py
"""

import json
import socket
from pathlib import Path
from datetime import datetime
from os import environ
from typing import (
    List, Tuple, Any, Type, 
    Callable, TypeAlias, Optional
)

import pandas as pd
from pandas.api.types import is_string_dtype
from tkinter.filedialog import askopenfilename
from tkinter.colorchooser import askcolor
from matplotlib.colors import is_color_like, to_rgb


#region ========================== new types ===================================

RGBType : TypeAlias = List[int] | List[float] | Tuple[int] | Tuple[float]
FieldDictType = List[dict[str, str | List[dict[str, str]]]]
ExchangeDictType = dict[str, dict[str, float | int]]
KeybindDictType = dict[str, str | dict[str, str]]

#endregion =====================================================================


#region ======================= global-variables ===============================

# directories to save files to
data_dir = ".data-acccli"
APPLICATION_DIRECTORY = Path().home() / data_dir
APPLICATION_DIRECTORY.mkdir(parents=True, exist_ok=True)

# cached directory that can be deleted directly
cache = "cached"
APPLICATION_CACHED_DIRECTORY = APPLICATION_DIRECTORY / cache
APPLICATION_CACHED_DIRECTORY.mkdir(parents=True, exist_ok=True)

# saving directory for dumping
storage = "storage"
APPLICATION_STORAGE_DIRECTORY = APPLICATION_DIRECTORY / storage
APPLICATION_STORAGE_DIRECTORY.mkdir(parents=True, exist_ok=True)


# color dictionary to print nicely
# https://gist.github.com/minism/1590432
class fg:
    black   = '\033[30m'
    red     = '\033[31m'
    green   = '\033[32m'
    yellow  = '\033[33m'
    blue    = '\033[34m'
    magenta = '\033[35m'
    cyan    = '\033[36m'
    white   = '\033[37m'
    reset   = '\033[39m'

#endregion =====================================================================



#region ======================= json operations ================================

def _jopen(path : Path) -> dict:
    """Load json from path."""
    with open(path, 'r', encoding='utf8') as file:
        res = json.load(file)
    return res

def _jrepr(d : dict) -> str:
    """Get nice pprint str from dictionary."""
    return json.dumps(d, indent=4)

def _jprint(d : dict):
    """Equivalent of `pprint`"""
    print(_jrepr(d))

def _jdump(d : dict, path : Path) -> None:
    """Save dict to path. Ensures that d is a dict."""
    ensure(d, dict)
    with open(path, 'w') as file:
        json.dump(d, file, indent=4)


#endregion =====================================================================


#region ======================== general-utils  ================================

def soft_warning(s : str) -> None:
    """Print soft warning."""
    print(f"{fg.red}{s}{fg.end}")

# TODO: test this !!!
def ensure(
        value : Any, 
        *types : Type[Any], 
        allow_none : bool = False
) -> None:
    """Simple type-checker. `raise` instead of `soft_err`."""
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


def confirm_action(
        action : Callable,
        max_attempts : int = 3,
        *, 
        label : str = "Confirm your action: [y/N]",
) -> None:
    for i in range(max_attempts):
        confirm = input(label)
        if confirm.lower() in ('y', 'yes'):
            action()
            print("Actions performed.")
            return
        elif not confirm or confirm.lower() in ('n', 'no'):
            print("Action was cancelled. Aborting.")
            return
        else:
            print(f"Attempt {i}: str '{confirm}' could not be understood.")
    raise RuntimeError(f"Max attempts reached: {max_attempts}. Action aborted.")


#endregion =====================================================================


def _raw_keys_check(
        field : KeybindDictType, 
        keys : List[str],
        err_list : List
) -> None:
    """Checks all keys are of str type."""
    for key in keys:
        if field.get(key):
            if not isinstance(field[key], str):
                err_list.append(f"{field=}: {key=} must be string type.")
        else:
            err_list.append(f"{field=} does not contain {key=}.")

def import_fields(
        path : Path
) -> FieldDictType: 
    """
    Loads ctx.fields from fields_path, ensuring str types and that 'key',
    'shortname' and 'description' are in every field item.
    """
    field_dict = _jopen(path)
    errs = []
    ensured_keys = ['key', 'shortname', 'description']

    if field_dict in [ [ ], [ { } ] ]: 
        raise ValueError("Empty category dict.")

    for field in field_dict:
        _raw_keys_check(field, ensured_keys, errs)
        subcat = field.get('subcategories')
        if subcat:
            for item in subcat:
                _raw_keys_check(item, ensured_keys, errs)
    if errs:
        raise ValueError(f"Invalid field dictionary. Errors: {errs}.")    
    return field_dict


def pprint_df(
        df : pd.DataFrame,
        header : Optional[str] = None
) -> None:
    """
    Pretty df printer. Prints index only if non-default. 
    """    
    if "description" in df.columns:
        if is_string_dtype(df.description):
            df.description = df.description.str[:100]

    is_default = (df.index.dtype == int and df.index.name is None)
    print_df = df.to_markdown(index= not is_default, tablefmt="outline")
    
    if header:
        line = print_df.partition('\n')[0]
        print_df = (
            f"{line}\n"
            f"{header}\n"
            f"{print_df}"
        )
    print(print_df)


# https://stackoverflow.com/a/33117579/29272030
def has_internet(
        host : str = "8.8.8.8", 
        port : int = 443, 
        timeout : int = 3
) -> bool:
    """Check if internet is available."""
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except socket.error as ex:
        print(ex)
        return False


def get_help_dictionary(
        fields_dict : FieldDictType
) -> dict[str, str]:
    """Returns help-dictionary from fields_dict."""

    if not (isinstance(fields_dict, List) and isinstance(fields_dict[0], dict)):
        raise TypeError(f"{fields_dict} is not a list of dictionaries.")

    res = {}
    for category_item in fields_dict:
        res.update(
            # no need to check for shortname they're checked at 
            # ctx construction (import_fields)
            { category_item['shortname'] : category_item.get('help', '') }
        )
        subcategory_item = category_item.get('subcategories')
        if subcategory_item:
            for item in subcategory_item:
                # no need for type-checking here neither
                res.update( { item['shortname'] : item.get('help', '')} )
    
    return res


def pprint_categories(
        categories_dict : dict[str, str],
        fields_dict : FieldDictType,
        help : bool = False
) -> None:
    if not help:
        _jprint(categories_dict)
        return
    
    with_help = get_help_dictionary(fields_dict)
    _jprint(with_help)



def _ask_editor() -> Path:
    """Asks for a valid file editor."""
    program_files = environ['ProgramFiles']
    title = "Select your preferred text editor."
    allowed = [("Exe", "*.exe")]
    
    # you ain't leaving unless a valid .exe is provided
    while not editor_path:
        print("An editor file is mandatory for editing, please pick one.")
        editor_path = askopenfilename(
            initialdir=program_files, 
            title=title,
            filetypes=allowed
        )

    return Path(editor_path)

def check_editor(editor_path : Path | str | None) -> Path:
    """Check if path is a valid .exe"""

    # wrap Path type
    if isinstance(editor_path, str):
        editor_path = Path(editor_path)

    if isinstance(editor_path, Path):
        # check if it's a valid executable
        if editor_path.exists() and editor_path.suffix == ".exe":
            return editor_path
        return _ask_editor()
    
    if editor_path is None:
        return _ask_editor()

    raise TypeError(f"{editor_path=} is not a valid argument.")

def _single_cord_converter(c : int | float) -> int | float:
    """Quick try-to-convert for a single int | float."""
    
    # 8 bit base integer check
    if isinstance(c, int) and 0 <= c <= 255:
        return c / 255.
    # [0, 1]^3 check
    elif isinstance(c, float) and 0 <= c <= 1:
        return c
    raise ValueError(f"Component {c=} failed RGB conversion.")

def convert_rgb(color : RGBType) -> RGBType:
    """
    Takes RGB-convertable argument and converts it into a valid matplotlib 
    recognizable color. 
    """
    if not isinstance(color, list | tuple):
        raise TypeError(f"{color=} is not a list or tuple.")
    if len(color) not in [3, 4]:
        raise ValueError(f"{color=} is not a 3 or 4-dimensional object.")

    return tuple(_single_cord_converter(c) for c in color)


def _cast_color(color: Any) -> RGBType | str:
    """Checks if color is a valid color. Relies on matplotlib.colors parser."""
    if is_color_like(color):
        return to_rgb(color)
    try:
        return convert_rgb(color)
    except TypeError as e:
        # Translating TypeError to ValueError
        # Think about it: "not a color" is technically a valid type since
        # matplotlib actually accepts strings as colors e.g. 'red'
        # However, it is unparsable -> what happens when can't be parsed?
        # ValueError! (error message is preserved though)
        raise ValueError(repr(e))


def _build_color_dict(
        currencies : List[str],
        colors : List[RGBType | str] 
) -> dict[str, RGBType | str]:
    """Builds color dictionary: {"curr1" : "color1", ...}."""
    res = {
        currency : _cast_color(color) 
        for currency, color in zip(currencies, colors) 
    }
    return res

def _ask_color(currency : str) -> Tuple[RGBType, str]:
    """askcolor wrapper. Returns both rgb and hex representation."""
    return askcolor(title=f"Pick color for {currency}:")

def check_colors(
        currencies : List[str],
        colors : List[RGBType | str] | None
) -> dict[str, RGBType | str]:
    """
    Main color checker. Threads over currencies and colors. 
    Type-check safety for colors only. Currencies type-check is trusted.
    """
    ncolors = len(colors)
    ncurrs = len(currencies)

    # numer of excesive colors is simply ignored
    if ncolors > ncurrs:
        return _build_color_dict(currencies, colors[:ncurrs])
    
    # more colors must be passed
    elif ncolors < ncurrs:
        res = _build_color_dict(currencies[:ncolors], colors)
        for currency in currencies[ncolors:]:
            color, _hex_color = _ask_color(currency)
            res.update( { currency : _cast_color(color) } )
        return res
    
    # same len? just thread!
    return _build_color_dict(currencies, colors)


def get_globals() -> None:
    """Shows globals while removing __like__ functions."""
    keys = globals().keys()
    # remove __like__ funcs
    clean = filter(lambda s: not s == s.replace('__', ''), keys)
    return clean


def now() -> None:
    """Print current time in '%H:%M:%S'."""
    fmt = '%H:%M:%S'
    time = datetime.now(fmt)
    print(time)