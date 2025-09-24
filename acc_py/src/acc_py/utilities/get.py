from pathlib import Path
import json


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