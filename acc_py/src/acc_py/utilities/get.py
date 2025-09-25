from pathlib import Path
import json
import urllib
import requests
import json
from typing import List

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
        curr_list : List[str]
):
    n = len(curr_list)
    curr_exchange_dict = {}
    
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
    
    return curr_exchange_dict
