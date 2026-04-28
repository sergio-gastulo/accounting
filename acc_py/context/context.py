from dataclasses import dataclass
from sqlalchemy.engine.base import Engine
from sqlalchemy import create_engine
from typing import List, Optional
from pathlib import Path
from datetime import date
from pandas import Period

from utilities.prompt import prompt_currency
from utilities.core import (
    _jopen,
    _cast_color,
    import_fields,
    fetch_keybind_dict,
    fetch_category_dictionary,
    check_editor,
    check_currency_list,
    check_colors,
    get_exchange_dict,
    FieldDictType,
    KeybindDictType,
    ExchangeDictType,
    RGBType
)


#region ======================== untested utils ================================

def _set_currency_list(currencies : List[str] | None) -> List[str]:
    if currencies is None:
        raise ValueError(f"A list of the managed currencies must be provided.")
    return check_currency_list(currencies)

def _today_period() -> Period:
    return Period(date.today(), 'M')

def _get_bar_color(color):
    if color is None:
        default_color = 'red'
        return default_color
    return _cast_color(color)

def _engine(url : str | Path | None) -> Engine:
    if url is None:
        return create_engine("sqlite://")
    return create_engine(f"sqlite:///{url}")

#endregion =====================================================================



#region ========================== new types ===================================

StrDict = dict[str, str]
CurrencyColorDictionary = dict[str, RGBType | str]

#endregion =====================================================================




@dataclass
class AccountingContext:

    # they're set latter
    engine: Optional[Engine]                   = None 
    keybinds : Optional[KeybindDictType]       = None
    fields : Optional[FieldDictType]           = None
    default_currency : Optional[str]           = None 
    editor : Optional[Path]                    = None

    # only necessary for plotting:
    darkmode : bool                                     = True
    categories_dict: Optional[StrDict]                  = None
    month_es: Optional[StrDict]                         = None
    period: Optional[Period]                            = None
    currency_list : Optional[List]                      = None
    colors: Optional[CurrencyColorDictionary]           = None
    exchange_dictionary : Optional[ExchangeDictType]    = None


    def set(
            self,
            config_path : Path, 
            fields_json_path : Path, 
            plot : bool = False
    ) -> None:

        config                  = _jopen(config_path)
        self.engine              = _engine(config.get('db_path'))
        self.fields              = import_fields(fields_json_path)
        self.keybinds            = fetch_keybind_dict(self.fields)
        self.categories_dict     = fetch_category_dictionary(self.fields)
        self.default_currency    = prompt_currency(config.get('default_currency'))
        self.editor              = check_editor(config.get("editor_path"))

        if plot:
            self.darkmode = bool(config.get('darkmode'))
            self.bar_color = _get_bar_color(config.get('bar_color'))
            self.period = _today_period()
            self.currency_list = _set_currency_list(config.get('currency_list'))
            self.colors = check_colors(
                self.currency_list, 
                config.get('rgb_colors')
            )
            self.exchange_dictionary = get_exchange_dict(
                self.currency_list, config.get('use_cache')
            )


    def load_from_cache(self):
        pass

    def save(self):
        pass

    def remove_cached_files(self):
        pass    



ctx = AccountingContext()