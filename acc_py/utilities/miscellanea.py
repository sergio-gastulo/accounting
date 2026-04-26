import inspect
from typing import List, Tuple, Iterable
from pathlib import Path
import json
import socket
import urllib
import requests
from tempfile import gettempdir
from os import environ
import tkinter as tk
from tkinter.filedialog import askopenfile
from tkinter.colorchooser import askcolor
from pandas import DataFrame
from pandas.api.types import is_string_dtype

from utilities.core_parser import parse_currency


RGB = Tuple[int, int, int]
FieldDictType = List[dict[str, str | List[dict[str, str]]]]


def _raw_keys_check(
        field : dict[str, str | dict[str, str]], 
        keys : List[str],
        err_list : List
) -> None:

    for key in keys:
        if not field.get(key):
            err_list.append(f"{field=} does not contain {key=}.")
        else:
            if not isinstance(field[key], str):
                err_list.append(f"{field=}: {key=} must be string type.")

def _jopen(path : Path) -> dict:
    with open(path, 'r') as file:
        res = json.load(file)
    return res

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


def _raw_print(dictionary : dict):
    print(json.dumps(dictionary, indent=4))

def pprint_categories(
        categories_dict : dict[str, str],
        fields_dict : List[dict[str | List[dict[str, str]]]],
        help : bool = False
) -> None:

    if not help:
        _raw_print(categories_dict)
        return
    
    help_dict = get_help_dictionary(fields_dict)
    _raw_print(help_dict)


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


# ----------------------------------------------
# This should return the following syntax:   
#     f(curr1, curr2) = exchange rate between 
#       curr1 and curr2
# ----------------------------------------------
def fetch_currency_exchange_rate(
        currency_1 : str,
        currency_2 : str
)-> float | int:

    # https://github.com/fawazahmed0/exchange-api?tab=readme-ov-file 
    url_bases = [
        "https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@latest/v1/currencies/",
        "https://latest.currency-api.pages.dev/v1/currencies/" 
    ]

    for url in url_bases:
        url_request = urllib.parse.urljoin(url, currency_1.lower() + ".json")
        response = requests.get(url_request)
        if (response.ok):
            json_res = json.loads(response.content)
            return json_res[currency_1.lower()][currency_2.lower()]
        else:
            continue
    response.raise_for_status()


def fetch_exchange_dict(
        curr_list : List[str],
        cached_file : Path | None = None,
        use_cache : bool = False
):

    if not cached_file:
        cached_file = (
            Path(gettempdir()) 
            / "acccli" 
            / "cached" 
            / "exchange-cached.json")

    cached_file.parent.mkdir(parents=True, exist_ok=True)

    if use_cache:
        try:
            with open(cached_file, 'r') as file:
                curr_exchange_dict = json.load(file)
            return curr_exchange_dict
        except:
            print(
                "Something went wrong while trying to fetch from cache." 
                "Temp file might have been removed."
                "Pulling information from the internet."
            )

    n = len(curr_list)
    curr_exchange_dict = {}
    
    if has_internet():
        # { "eur" : { "usd" : xx,  "pen" : yy, "eur" : 1}, ... }
        for i in range(n):
            curr_exchange_dict[curr_list[i]] = {}
            for j in range(n):
                if j < i:
                    res = 1 / curr_exchange_dict[curr_list[j]][curr_list[i]]
                elif j == i :
                    res = 1
                else:
                    res = fetch_currency_exchange_rate(
                        currency_1=curr_list[i], 
                        currency_2=curr_list[j]
                    )
                curr_exchange_dict[curr_list[i]].update(
                    { curr_list[j] : res }
                )

        with open(cached_file, 'w') as file:
            json.dump(curr_exchange_dict, file)

    else:
        print("Loading from cache -- no Internet connection available.")
        with open(cached_file, 'r') as file:
            curr_exchange_dict = json.load(file)

    print(
        f"Current exchange dictionary loaded:\n"
        f"{json.dumps(curr_exchange_dict, indent=4)}"
    )
    
    return curr_exchange_dict



def check_editor(editor_file : Path | None) -> Path:
    
    if editor_file.exists() and editor_file.suffix == ".exe":
        return editor_file
    
    program_files = environ['ProgramFiles']
    title = "Select your preferred text editor."
    allowed = [("Exe", "*.exe")]
    
    while not editor_file:
        print("An editor file is mandatory for editing, please pick one.")
        editor_file = askopenfile(
            initialdir=program_files, 
            title=title,
            filetypes=allowed
        )

    return editor_file


def check_currency_list(currency_list : List[str]) -> List[str]:
    return [parse_currency(currency=curr) for curr in currency_list]


def check_colors(
        color_list : Iterable[RGB] | None,
        currency_list : List[str]
) -> dict[str, RGB | str]:

    if color_list:
        dict_res = {
            currency : [spec / 255 for spec in color if spec > 1] 
            for currency, color in zip(currency_list, color_list)
        }
        return dict_res

    root = tk.Tk()
    root.withdraw()
    dict_res = {
        curr : askcolor(title=f"Pick color for {curr}:")[1] 
        for curr in currency_list
    }
    return dict_res
