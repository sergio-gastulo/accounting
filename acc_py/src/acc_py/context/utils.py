from pathlib import Path
import json
import urllib
import requests
import json
from typing import List, Tuple, Iterable
from ..utilities.miscellanea import has_internet
from tempfile import gettempdir
from tkinter.filedialog import askopenfile
from os import environ
from ..utilities.core_parser import parse_currency
import tkinter as tk
from tkinter.colorchooser import askcolor


RGB = Tuple[int, int, int]


def fetch_category_dictionary(json_path: Path) -> dict[str, str]:
    """
    Loads JSON from 'path' and flattens the fields.json in the key-value pair format: 'shortname': 'description'   
    """
    shortname_descript_dict = {}

    with open(json_path,'r') as file:
        for item_dict in json.load(file):
            subcategories = item_dict.get("subcategories")
            if subcategories:
                for item in subcategories:
                    shortname_descript_dict.update({item["shortname"]: item["description"]})
            else:
                shortname_descript_dict.update({item_dict["shortname"]: item_dict["description"]})

    return shortname_descript_dict


def fetch_keybind_dict(json_path : Path) -> dict[str, str | dict[str, str]]:
    """
    Retrieves a keybind dict for fast category-writing from json_path.
    
    :param json_path: Description
    :type json_path: Path
    :return: Description
    :rtype: dict[str, str | dict[str, str]]
    """

    keybind_dict = {}

    def sort_dict(d : dict[str, str]) -> dict[str, str]:
        return { key : d[key] for key in sorted(d) }

    with open(json_path, 'r') as file:
        for item_dict in json.load(file):
            subcategories = item_dict.get("subcategories")
            if subcategories:
                keybind_dict.update({
                    item_dict["key"] : sort_dict({
                        item["key"] : item["shortname"] 
                        for item in subcategories
                    })
                })
            else: 
                keybind_dict.update({item_dict["key"]: item_dict["shortname"]})
    
    return sort_dict(keybind_dict)


# ----------------------------------------------
# This should return the following syntax:   
#     f(curr1, curr2) = exchange rate between 
#       curr1 and curr2
# ----------------------------------------------
def fetch_currency_exchange_rate(
        currency_1 : str,
        currency_2 : str
)-> float | int:

    url_bases = [
        "https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@latest/v1/currencies/",
        # as per https://github.com/fawazahmed0/exchange-api?tab=readme-ov-file: 
        "https://latest.currency-api.pages.dev/v1/currencies/" 
    ]

    for url in url_bases:
        url_request = urllib.parse.urljoin(url, currency_1.lower() + ".json")
        response = requests.get(url_request)
        if (response.ok):
            return json.loads(response.content)[currency_1.lower()][currency_2.lower()]
        else:
            continue
    
    response.raise_for_status()


def fetch_exchange_dict(
        curr_list : List[str],
        cached_file : Path | None = None,
        use_cache : bool = False
):

    if not cached_file:
        cached_file = Path(gettempdir()) / "acccli" / "cached" / "exchange-cached.json"

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
                    res = fetch_currency_exchange_rate(curr_list[i], curr_list[j])
                curr_exchange_dict[curr_list[i]].update(
                    { curr_list[j] : res }
                )

        with open(cached_file, 'w') as file:
            json.dump(curr_exchange_dict, file)

    else:
        print("Loading from cache since there is no Internet connection available.")
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
