from sqlalchemy import create_engine
from pathlib import Path
import json
from pandas import Period
from datetime import date

from .context import ctx
from .utils import *

from ..utilities.prompt import prompt_currency
from ..db.db_api import get_full_currencies_list


def set_context(
        config_path : Path, 
        fields_json_path : Path, 
        plot : bool = False
) -> None:

    with open(config_path, 'r') as file:
        config = json.load(file)

    ctx.engine = create_engine(url=f"sqlite:///{config['db_path']}")
    ctx.field_json_path = fields_json_path
    ctx.keybinds = fetch_keybind_dict(fields_json_path)
    ctx.default_currency = prompt_currency(
        config.get('default_currency'), 
        silent=True)
    ctx.editor = check_editor(Path(config.get("editor_path")))

    if plot:
        ctx.darkmode = config.get('darkmode')
        ctx.bar_color = config.get('bar_color')
        ctx.categories_dict = fetch_category_dictionary(fields_json_path)
        ctx.period = Period(date.today(), 'M')
        
        currency_list = config.get('currency_list')
        if currency_list:
            ctx.currency_list = check_currency_list(currency_list) 
        else:
            ctx.currency_list = get_full_currencies_list()

        ctx.colors = check_colors(
            color_list=config.get('rgb_colors'),
            currency_list=ctx.currency_list
        )
        ctx.exchange_dictionary = fetch_exchange_dict(
            curr_list=[curr.lower() for curr in ctx.currency_list],
            use_cache=config.get('use_cache'),
            cached_file=config.get('cached_file')
        )