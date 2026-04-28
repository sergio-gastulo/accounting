import inspect
from typing import List, Tuple, Any
from pathlib import Path, WindowsPath
from sqlalchemy import create_engine
import json
import socket
import urllib
import requests
from tempfile import gettempdir
from os import environ
from pandas import DataFrame

from tkinter.filedialog import askopenfilename
from tkinter.colorchooser import askcolor
from pandas.api.types import is_string_dtype
from matplotlib.colors import is_color_like


RGB = List[int] | List[float] | Tuple[int] | Tuple[float]
FieldDictType = List[dict[str, str | List[dict[str, str]]]]
ExchangeDictType = dict[str, dict[str, float | int]]


#region ======================= json operations ================================

def _jopen(path : Path) -> dict:
    with open(path, 'r') as file:
        res = json.load(file)
    return res

def _jrepr(d : dict) -> str:
    return json.dumps(d, indent=4)

def _jprint(d : dict):
    print(_jrepr(d))

def _jdump(d : dict, path : Path) -> None:
    with open(path, 'w') as file:
        json.dump(d, file, indent=4)

#endregion =====================================================================


def engine(url : str | Path | None):
    if url is None:
        return create_engine("sqlite://")
    return create_engine(f"sqlite:///{url}")

def _raw_keys_check(
        field : dict[str, str | dict[str, str]], 
        keys : List[str],
        err_list : List
) -> None:

    for key in keys:
        if field.get(key):
            if not isinstance(field[key], str):
                err_list.append(f"{field=}: {key=} must be string type.")
        else:
            err_list.append(f"{field=} does not contain {key=}.")

def import_fields(
        path : Path
) -> List[dict[str | List[dict[str, str]]]]: 
    
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


def print_func_doc(func: callable) -> None:
    cyan_str = '\033[96m'
    end_str = '\033[0m'

    print(f'{cyan_str}Function name:{end_str}\n{func.__name__}\n')

    sig = inspect.signature(func)
    print(f'{cyan_str}Arguments:{end_str} {sig}\n')

    doc = func.__doc__
    print(f'{cyan_str}Documentation:{end_str}\n{doc}')


def pprint_df(
        df : DataFrame,
        header : str | None = None
) -> None | str:
    
    if "description" in df.columns:
        if is_string_dtype(df.description):
            df.description = df.description.str[:100]

    has_index = (df.index.name == 'id')
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
    
    # TODO: improve type checking here ...
    if not isinstance(fields_dict, List):
        raise TypeError("Field dictionary has no valid type.")

    res = {}
    for category_item in fields_dict:
        res.update(
            # no need to check for shortname, they're checked at ctx construction
            { category_item['shortname'] : category_item.get('help', '') }
        )
        subcategory_item = category_item.get('subcategories')
        if subcategory_item:
            for item in subcategory_item:
                res.update( { item['shortname'] : item.get('help', '')} )
    
    return res


def pprint_categories(
        categories_dict : dict[str, str],
        fields_dict : List[dict[str | List[dict[str, str]]]],
        help : bool = False
) -> None:

    if not help:
        _jprint(categories_dict)
        return
    
    help_dict = get_help_dictionary(fields_dict)
    _jprint(help_dict)


def get_all_categories(
        category_dict : dict[str, dict[str, str] | str]
) -> List[str] : 
    
    res = []

    for item in category_dict:
        # shortname guaranteed in the ctx parser
        res.append(item['shortname']) 
        collection = item.get('subcategories')
        if collection:
            for subitem in collection:
                # sub-items' shortnames are checked in the parser too 
                res.append(subitem.get('shortname'))

    return res


def fetch_category_dictionary(
        field_dict: FieldDictType
) -> dict[str, str]:
    shortname_descript_dict = {}

    for item_dict in field_dict:
        subcategories = item_dict.get("subcategories")
        # both shortname-description guaranteed in the ctx parser
        if subcategories:
            for item in subcategories:
                shortname_descript_dict.update(
                    {item["shortname"]: item["description"]}
                )
        else:
            shortname_descript_dict.update(
                {item_dict["shortname"]: item_dict["description"]}
            )

    return shortname_descript_dict


def _sort_dict(d : dict[str, str]) -> dict[str, str]:
    return { key : d[key] for key in sorted(d) }

def fetch_keybind_dict(
        field_dict : FieldDictType
) -> dict[str, str | dict[str, str]]:

    keybind_dict = {}

    # key checking in body of import_fields
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


def _fetch_exchange(currency : str) :
    
    # https://github.com/fawazahmed0/exchange-api
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
            res = json.loads(response.content)
            res = res[currency]
            return res
            
    if response.status_code == 404:
        raise ValueError(f"{currency=} does not exist.")

def _currency_type_check(currency : str) -> str:
    if not isinstance(currency, str):
        raise TypeError(f"{currency=} is not string type.")
    if len(currency) != 3:
        raise ValueError(f"{currency=} is not in valid ISO format.")
    return currency.lower()

exchange_memo = {}
def fetch_exchange_rate(
        currency : str
) -> dict : 
    
    currency = _currency_type_check(currency)
    if currency in exchange_memo:
        return exchange_memo[currency]

    res = _fetch_exchange(currency)
    exchange_memo.update( { currency : res } )
    return res


def get_exchange_rate(
        currency_1 : str,
        currency_2 : str
)-> float:
    
    currency_1 = _currency_type_check(currency_1)
    currency_2 = _currency_type_check(currency_2)
    if currency_1 == currency_2:
        return 1.0

    res = fetch_exchange_rate(currency_1)
    exchange = res.get(currency_2)
    if exchange:
        return exchange
    raise ValueError(f"{currency_2=} does not exist in exchange dictionary for {currency_1=}.")


def _create_exchange_cache() -> Path:
    cache_path = Path(gettempdir())
    cache_path = cache_path / "acccli" / "cached" / "exchange-cached.json"
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    return cache_path

def build_exchange(curr_list : List[str]) -> dict:
    res = {
        curr1 : {
            curr2 : get_exchange_rate(curr1, curr2)
            for curr2 in curr_list  
        }
        for curr1 in curr_list
    }
    return res


def get_exchange_dict(
        curr_list : List[str],
        use_cache : bool = False
) -> ExchangeDictType:
    
    cached_path = _create_exchange_cache()
    if (use_cache and cached_path.exists()) or (not has_internet()):
        res = _jopen(cached_path)
        return res

    curr_list = [ _currency_type_check(curr) for curr in curr_list ]
    curr_exchange = build_exchange(curr_list)
    _jdump(curr_exchange, cached_path)
    _jprint(curr_exchange)
    exchange_memo.clear()
    return curr_exchange


def _ask_editor() -> Path:
    program_files = environ['ProgramFiles']
    title = "Select your preferred text editor."
    allowed = [("Exe", "*.exe")]
    
    while not editor_path:
        print("An editor file is mandatory for editing, please pick one.")
        editor_path = askopenfilename(
            initialdir=program_files, 
            title=title,
            filetypes=allowed
        )

    return Path(editor_path)

def check_editor(editor_path : Path | str | None) -> Path:
    
    if isinstance(editor_path, str):
        editor_path = Path(editor_path)
    
    if isinstance(editor_path, Path | WindowsPath):
        if editor_path.exists() and editor_path.suffix == ".exe":
            return editor_path
        return _ask_editor()
    
    if editor_path is None:
        return _ask_editor()

    raise TypeError(f"{editor_path=} is not a valid argument.")


def check_currency_list(currency_list : List[str]) -> List[str]:
    return [_currency_type_check(curr) for curr in currency_list]


def convert_rgb(color : RGB) -> RGB:
    if not isinstance(color, list | tuple):
        raise TypeError(f"{color=} is not a valid RGB color.")
    if len(color) not in [3, 4]:
        raise ValueError(f"{color=} is not a valid RGB color.")

    res = ()
    for c in color:
        if isinstance(c, int) and (0 <= c <= 255):
            res += (c / 255, ) 
        elif isinstance(c, float) and 0 <= c <= 1:
            res += (c, )
        else:
            raise ValueError(f"{color=} can't be casted to RGB.")
    return res


def _cast_color(color: Any) -> RGB | str:
    if is_color_like(color):
        return color
    try:
        c = convert_rgb(color)
        return c
    except TypeError:
        raise ValueError(f"Unsupported conversion for {color=}.")

def _build_color_dict(
        currencies : List[str],
        colors : List[RGB | str] 
) -> dict[str, RGB | str]:
    res = {
        currency : _cast_color(color) 
        for currency, color in zip(currencies, colors) 
    }
    return res

def _ask_color(currency : str) -> Tuple[RGB, str]:
    return askcolor(title=f"Pick color for {currency}:")

def check_colors(
        currencies : List[str],
        colors : List[RGB] | None
) -> dict[str, RGB | str]:

    ncolors = len(colors)
    ncurrs = len(currencies)

    if ncolors > ncurrs:
        # numer of excesive colors is simply ignored
        return _build_color_dict(currencies, colors[:ncurrs])
    
    elif ncolors < ncurrs:
        # more colors must be passed
        res = _build_color_dict(currencies[:ncolors], colors)
        for currency in currencies[ncolors:]:
            color, _hex_color = _ask_color(currency)
            res.update( { currency : _cast_color(color) } )
        return res
    
    else:
        return _build_color_dict(currencies, colors)
