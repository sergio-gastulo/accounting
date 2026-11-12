"""
Operations on dictionaries.
"""

from pathlib import Path

from .jops import jopen, jprint
from .typing import FieldDictType, KeybindDictType


def check_keys(d: dict, keys: list):
    """Check that `d` contains every `keys`."""
    for key in keys:
        if key not in d:
            raise ValueError(f"{key} not in dictionary.")


def import_fields(
        path: Path
) -> FieldDictType: 
    """
    Loads `ctx.fields` from `path`, ensuring that 'key',
    'shortname' and 'description' are in every field item.
    """
    field_dict = jopen(path)
    ensured_keys = ['key', 'shortname', 'description']

    if field_dict in [[], [{}]]:
        raise ValueError("Empty category dict.")

    for field in field_dict:
        check_keys(field, ensured_keys)
        subcat = field.get('subcategories')
        if subcat:
            for item in subcat:
                check_keys(item, ensured_keys)

    return field_dict


def resolve_value(
        rawinput: str,
        dict_: dict[str, str]
) -> str:
    """
    Converts `rawinput` to `dict_[rawinput]` or `rawinput` 
    if present in `dict_`.

    Example
    -------
    >>> resolve_value({"a": "aa", "b": "bb"}, "b")
    "bb"
    >>> resolve_value({"a": "aa", "b": "bb"}, "bb")
    "bb"
    """    
    if rawinput in dict_:
        return dict_[rawinput]
    if rawinput in dict_.values():
        return rawinput

    raise ValueError(f"Could not validate {rawinput=}.")


def get_help_dictionary(
        fields_dict: FieldDictType
) -> dict[str, str]:
    """Returns help-dictionary from fields_dict."""
    res = {}
    for item in fields_dict:
        res.update({item['shortname']: item.get('help', '')})
        sub = item.get('subcategories')
        if sub:
            for item in sub:
                res.update({item['shortname']: item.get('help', '')})
    return res


def sort_dict(d: dict) -> dict:
    return {key : d[key] for key in sorted(d)}


def fetch_keybind_dict(
        field_dict: FieldDictType
) -> KeybindDictType:
    """Constructs keybind dictionary dict from fields_dict."""
    keybind_dict = {}

    for item in field_dict:
        sub = item.get("subcategories")
        if sub:
            d = {item_["key"]: item_["shortname"] for item_ in sub}
            keybind_dict.update({item["key"]: sort_dict(d)})
        else:
            keybind_dict.update({item["key"]: item["shortname"]})

    return sort_dict(keybind_dict)



def fetch_category_dictionary(
        field_dict: FieldDictType
) -> dict[str, str]:
    """
    Fetches category_dict ({"category" : "description"}) from fields_dict.
    """
    res = {}
    for item in field_dict:
        sub = item.get("subcategories")
        if sub:
            for item_ in sub:
                res.update({item_["shortname"] : item_["description"]})
        else:
            res.update({item["shortname"] : item["description"]})
    return res


def pprint_categories(
        categories_dict: dict[str, str],
        fields_dict : FieldDictType,
        help_: bool = False
) -> None:
    if not help_:
        jprint(categories_dict)
        return None
    
    jprint(get_help_dictionary(fields_dict))