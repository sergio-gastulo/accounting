"""
First file that is run.
Should not import **ANY** hand-written acccli-related code.
It contains a variety of functions that are used in context.py, parser.py 
and prompt.py
"""
from typing import List, Tuple, Any, Type, Callable, TypeAlias, Optional
from pathlib import Path
import json
import socket
import urllib
import requests
from os import environ
import hashlib
from datetime import datetime

import pandas as pd
from tkinter.filedialog import askopenfilename
from tkinter.colorchooser import askcolor
from pandas.api.types import is_string_dtype
from matplotlib.colors import is_color_like, to_rgb


#region ========================== new types ===================================

RGBType : TypeAlias = List[int] | List[float] | Tuple[int] | Tuple[float]
FieldDictType = List[dict[str, str | List[dict[str, str]]]]
ExchangeDictType = dict[str, dict[str, float | int]]
KeybindDictType = dict[str, str | dict[str, str]]

#endregion =====================================================================


#region ======================= global-variables ===============================

# --- directories to save files to ---
data_dir = ".data-acccli"
APPLICATION_DIRECTORY = Path().home() / data_dir
APPLICATION_DIRECTORY.mkdir(parents=True, exist_ok=True)

# --- cached directory that can be deleted directly ---
cache = "cached"
APPLICATION_CACHED_DIRECTORY = APPLICATION_DIRECTORY / cache
APPLICATION_CACHED_DIRECTORY.mkdir(parents=True, exist_ok=True)

# --- saving directory for dumping ---
storage = "storage"
APPLICATION_STORAGE_DIRECTORY = APPLICATION_DIRECTORY / storage
APPLICATION_STORAGE_DIRECTORY.mkdir(parents=True, exist_ok=True)


# --- color dictionary to print nicely ---
# --- https://gist.github.com/minism/1590432 ---
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
    """Save dict to path."""
    ensure(d, dict)
    with open(path, 'w') as file:
        json.dump(d, file, indent=4)


#endregion =====================================================================


#region ======================== general-utils  ================================

def soft_warning(s : str) -> None:
    """Print soft warning."""
    print(f"{fg.red}{s}{fg.end}")


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
    keys_ensure = ['key', 'shortname', 'description']

    if field_dict in [ [ ], [ { } ] ]: 
        raise ValueError("Empty category dict.")

    for field in field_dict:
        _raw_keys_check(field, keys_ensure, errs)
        subcat = field.get('subcategories')
        if subcat:
            for item in subcat:
                _raw_keys_check(item, keys_ensure, errs)
    if errs:
        raise ValueError(f"Invalid field dictionary. Errors: {errs}.")    
    return field_dict


# TODO: test this
def pprintfunc(func: callable) -> None:
    """Nice documentation printer."""
    cyan_str = fg.cyan
    reset_str = fg.reset

    print(f'{cyan_str}Function name:{reset_str}\n{func.__name__}\n')

    doc = func.__doc__
    print(f'{cyan_str}Documentation:{reset_str}\n{doc}')


def pprint_df(
        df : pd.DataFrame,
        header : str | None = None
) -> None:
    """Pretty df printer."""    
    if "description" in df.columns:
        if is_string_dtype(df.description):
            df.description = df.description.str[:100]

    has_index = (df.index.dtype != int or df.index.name == 'id')
    print_df = df.to_markdown(index=has_index, tablefmt="outline")
    
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

    # TODO: assert FieldDictType clearly
    if not isinstance(fields_dict, List):
        raise TypeError(f"{fields_dict} is not a list of dictionaries.")

    res = {}
    for category_item in fields_dict:
        res.update(
            # --- no need to check for shortname they're checked at 
            # --- ctx construction (import_fields)
            { category_item['shortname'] : category_item.get('help', '') }
        )
        subcategory_item = category_item.get('subcategories')
        if subcategory_item:
            for item in subcategory_item:
                # --- no need for type-checking here neither ---
                res.update( { item['shortname'] : item.get('help', '')} )
    
    return res


def pprint_categories(
        categories_dict : dict[str, str],
        fields_dict : FieldDictType,
        help : bool = False
) -> None:
    """
    Print all categories in a readable, formatted way.

    Parameters
    ----------
    categories_dict : dict[str, str]
        A mapping of category names to their descriptions.
        Each key is a category name, and each value is the category's
        human-readable label or explanation.

    field_json_path : Path
        Path to the JSON file from which the categories originate.
        Used for reference only; the function does not modify the file.

    help : bool, optional
        If False (default), print each category and its description
        in a clean, aligned, human-friendly format.
        If True, print extended help information for all available
        categories, including additional notes or hints contained in the
        descriptions.

    Returns
    -------
    None
        This function only prints formatted output and does not return a value. 
    """
    if not help:
        _jprint(categories_dict)
        return
    
    help_dict = get_help_dictionary(fields_dict)
    _jprint(help_dict)


# TODO: is this really being used somewhere?
def get_all_categories(
        fields_dict : FieldDictType
) -> List[str] : 
    """Retrieves a list of all categories in fields_dict."""
    res = []
    for item in fields_dict:
        # --- shortname guaranteed in the ctx parser ---
        res.append(item['shortname']) 
        collection = item.get('subcategories')
        if collection:
            for subitem in collection:
                # --- sub-items' shortnames are checked in the parser too ---
                res.append(subitem.get('shortname'))

    return res


def fetch_category_dictionary(
        field_dict: FieldDictType
) -> dict[str, str]:
    """
    Fetches category_dict ({"category" : "description"}) from fields_dict.
    """
    res = {}
    for item_dict in field_dict:
        subcategories = item_dict.get("subcategories")
        # --- both shortname-description guaranteed in the ctx parser ---
        if subcategories:
            for item in subcategories:
                res.update(
                    { item["shortname"] : item["description"] }
                )
        else:
            # --- here too ---
            res.update(
                { item_dict["shortname"] : item_dict["description"] }
            )
    return res


def _sort_dict(d : dict[str, Any]) -> dict[str, Any]:
    """Simple sorter-by-key."""
    return { key : d[key] for key in sorted(d) }

def fetch_keybind_dict(
        field_dict : FieldDictType
) -> KeybindDictType:
    """Constructs keybind dict from fields_dict."""
    keybind_dict = {}

    # --- no KeyErrors since field_dict is first ensured on import_fields ---
    for item_dict in field_dict:
        subcategories = item_dict.get("subcategories")
        if subcategories:
            keybind_dict.update({
                item_dict["key"] : _sort_dict({
                    item["key"] : item["shortname"] 
                    for item in subcategories
                })
            })
        else:
            keybind_dict.update({item_dict["key"]: item_dict["shortname"]})

    return _sort_dict(keybind_dict)


def _fetch_exchange(currency : str) -> dict[str, int | float]:
    """
    Fetch full list of currency exchanges associated to currency.
    """
    # --- https://github.com/fawazahmed0/exchange-api ---
    url_bases = [
        "https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@latest/v1/currencies/",
        "https://latest.currency-api.pages.dev/v1/currencies/" 
    ]

    currency = currency.lower()
    endpoint = f"{currency}.json"
    for url in url_bases:
        url_request = urllib.parse.urljoin(url, endpoint)
        response = requests.get(url_request)
        if response.ok :
            # --- res example: https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@latest/v1/currencies/pen.json ---
            res = json.loads(response.content)
            res = res[currency]
            return res
            
    # TODO: we should probably test this properly
    if response.status_code == 404:
        raise ValueError(
            f"Arguement '{currency}' is an invalid currency. "
            f"Full response: {response.text}."
        )
    else:
        raise RuntimeError(f"Unkown state. Full response: {response.text}.")

def _currency_type_check(currency : str) -> str:
    """Simple currency type check."""
    if not isinstance(currency, str):
        raise TypeError(f"{currency=} is not string type.")
    if len(currency) != 3:
        raise ValueError(f"{currency=} is not in valid ISO format.")
    return currency.lower()

def check_currency_list(currency_list : List[str]) -> List[str]:
    """
    Threads over currency_list and validates currency type. 
    Returns currency in lower case. 
    """
    return [_currency_type_check(curr) for curr in currency_list]


exchange_memo = {}
def fetch_exchange_rates(
        currency : str
) -> dict : 
    """
    Fetch exchange rate**S** from a given currency and update to exchange_memo if
    non-existent. Type checks are included. 
    """
    currency = _currency_type_check(currency)
    # --- if memoized, call it ---
    if currency in exchange_memo:
        return exchange_memo[currency]

    # --- if not, then update exchange_memo ---
    res = _fetch_exchange(currency)
    exchange_memo.update( { currency : res } )
    return res


def get_exchange_rate(
        currency_1 : str,
        currency_2 : str
)-> float | int:
    """
    Gets exchange rate between curr_1 and curr_2. Calls fetch_exchange_rate
    under the hood. Type checks are implemented.
    """    
    # --- type checking ---
    currency_1 = _currency_type_check(currency_1)
    currency_2 = _currency_type_check(currency_2)

    # --- unnecessary fetch is prevented ---
    if currency_1 == currency_2:
        return 1.0

    # --- fetch full exchange rates, if curr_2 does not exist, raise err ---
    res = fetch_exchange_rates(currency_1)
    if currency_2 in res:
        return res[currency_2]
    raise ValueError(f"{currency_2=} does not exist in exchange dictionary for {currency_1=}.")
    


def build_exchange(curr_list : List[str]) -> ExchangeDictType:
    """
    Builds exchange dictionary from a list of currencies. 
    Check tests for a full check of coverage.
    """
    res = { 
        curr1 : {   curr2 : get_exchange_rate(curr1, curr2)
                        for curr2 in curr_list                  }
        for curr1 in curr_list                              
    }
    return res


# NOTE: delete quiet? refactor tests.core.TestExchangeDictionaryGetter
def get_exchange_dict(
        curr_list : List[str],
        use_cache : bool | None = False,
        quiet : bool = False
) -> ExchangeDictType:
    """
    Builds exchange dictionary from curr_list. However, first tries to load 
    from cache. If failure, it type-checks curr_list and builds ex-dict from it.
    """
    
    # --- try to load from cache: whenever no internet is available or
    # --- explicitely passed as option
    name = "exchange.json"
    cached_path = APPLICATION_CACHED_DIRECTORY / name
    if (use_cache and cached_path.exists()) or (not has_internet()):
        res = _jopen(cached_path)
        return res

    # --- ensure type check and build exchange dict ---
    curr_list = check_currency_list(curr_list)
    curr_exchange = build_exchange(curr_list)
    
    # --- load to cache and print if asked ---
    _jdump(curr_exchange, cached_path)
    if not quiet:
        _jprint(curr_exchange)
    exchange_memo.clear()
    return curr_exchange


def _ask_editor() -> Path:
    """Asks for a valid file editor."""
    program_files = environ['ProgramFiles']
    title = "Select your preferred text editor."
    allowed = [("Exe", "*.exe")]
    
    # --- you ain't leaving unless a valid .exe is provided ---
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

    # --- wrap Path type ---
    if isinstance(editor_path, str):
        editor_path = Path(editor_path)

    if isinstance(editor_path, Path):
        # --- check if it's a valid executable ---
        if editor_path.exists() and editor_path.suffix == ".exe":
            return editor_path
        return _ask_editor()
    
    if editor_path is None:
        return _ask_editor()

    raise TypeError(f"{editor_path=} is not a valid argument.")

def _single_cord_converter(c : int | float) -> int | float:
    """Quick try-to-convert for a single int | float."""
    
    # --- 8 bit base integer check ---
    if isinstance(c, int) and 0 <= c <= 255:
        return c / 255.
    # --- [0, 1]^3 check ---
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
        # --- Translating TypeError to ValueError
        # --- Think about it: "not a color" is technically a valid type since
        # --- matplotlib actually accepts strings as colors e.g. 'red'
        # --- However, it is unparsable -> what happens when can't be parsed?
        # --- ValueError! (error message is preserved though)
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

    # --- numer of excesive colors is simply ignored ---
    if ncolors > ncurrs:
        return _build_color_dict(currencies, colors[:ncurrs])
    
    # --- more colors must be passed ---
    elif ncolors < ncurrs:
        res = _build_color_dict(currencies[:ncolors], colors)
        for currency in currencies[ncolors:]:
            color, _hex_color = _ask_color(currency)
            res.update( { currency : _cast_color(color) } )
        return res
    
    # --- same len? just thread! ---
    return _build_color_dict(currencies, colors)


# https://www.geeksforgeeks.org/python/python-program-to-find-hash-of-file/
def sha256(file_path : Path) -> str:
    """Compute sha256 of file."""
    hash_func = hashlib.sha256()
    chunksize = 65536
    with open(file_path, 'rb') as file:
        while chunk := file.read(chunksize):
            hash_func.update(chunk)
    
    return hash_func.hexdigest()


def export(
        obj : pd.DataFrame | pd.Series | dict, 
        p : Optional[Path | str] = None, 
        **kwargs
) -> None:
    """
    Quick exporter to supported extensions: csv, json and xml.

    Arguments
    ---------
    obj 
        Object to be exported. Only accepts `DataFrame`, `Series` and `dict`.
    p
        Path to export obj to.
    **kwargs
        Arugments that are passed to to_json, to_csv, ...
    """
    if p is None:
        now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        fname = f"_dumped_{now}.json"
        p = APPLICATION_STORAGE_DIRECTORY / fname

    extension = p.suffix.lower().lstrip(".")
    supported = {"csv", "json", "xml"}
    if extension not in supported:
        raise ValueError(f"Path {p} extension is not in {supported}.")

    if isinstance(obj, pd.DataFrame | pd.Series):
        savemap = f"to_{extension}"
        savemap = getattr(obj, savemap)
        # https://stackoverflow.com/a/39612316/29272030
        with open(p, "w", encoding='utf-8') as file:
            savemap(file, force_ascii=False, **kwargs)

    elif isinstance(obj, dict):
        if extension == ".json":
            _jdump(obj, p)
        else:
            raise ValueError(f"Extension {extension} is not valid for a dictionary to be converted to.")
    

def fetch(
        p : Path,
        **kwargs
) -> pd.DataFrame:
    """
    Quick importer from supported extensions: csv, json and xml.

    Arguments
    ---------
    p
        Path to fetch data from.
    **kwrags
        Keyword arguments that are passed to read_csv, read_json, etc.

    Returns
    -------
    df
        DataFrame that is returned via pd.read_csv, ...
        No further sanitization or parsing is performed.
    """
    extension = p.suffix.lower().lstrip(".")
    supported = {"csv", "json", "xml"}
    if extension not in supported:
        raise ValueError(f"Path {p} extension is not in {supported}.")
    
    savemap = f"read_{extension}"
    savemap = getattr(pd, savemap)
    df = savemap(p, encoding='utf-8', **kwargs)
    return df