from pathlib import Path
from pandas import Period
from datetime import date
from typing import List

from context.context import ctx
from utilities.prompt import prompt_currency
from db.db_api import get_full_currencies_list
from utilities.miscellanea import (
    engine,
    _jopen,
    import_fields,
    fetch_keybind_dict,
    fetch_category_dictionary,
    check_editor,
    check_currency_list,
    check_colors,
    get_exchange_dict
)

#region ======================== untested utils ================================

def _set_currency_list(currencies : List[str] | None) -> List[str]:
    if currencies is None:
        return get_full_currencies_list()
    return check_currency_list(currencies)

def _today_period() -> Period:
    return Period(date.today(), 'M')

#endregion =====================================================================


def set_context(
        config_path : Path, 
        fields_json_path : Path, 
        plot : bool = False
) -> None:

    config                  = _jopen(config_path)
    ctx.engine              = engine(config.get('db_path'))
    ctx.fields              = import_fields(fields_json_path)
    ctx.keybinds            = fetch_keybind_dict(ctx.fields)
    ctx.categories_dict     = fetch_category_dictionary(ctx.fields)
    ctx.default_currency    = prompt_currency(config.get('default_currency'))
    ctx.editor              = check_editor(config.get("editor_path"))

    if plot:
        ctx.darkmode = config.get('darkmode')
        ctx.bar_color = config.get('bar_color')
        ctx.period = _today_period()
        ctx.currency_list = _set_currency_list(config.get('currency_list'))
        ctx.colors = check_colors(
            ctx.currency_list, 
            config.get('rgb_colors')
        )
        ctx.exchange_dictionary = get_exchange_dict(
            ctx.currency_list, config.get('use_cache')
        )