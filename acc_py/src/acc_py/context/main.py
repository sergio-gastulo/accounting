from sqlalchemy import create_engine
from pathlib import Path
import json
from pandas import Period
from datetime import date

from .context import ctx
from .utils import *

from ..utilities.prompt import prompt_period
from ..utilities.prompt import prompt_currency


def set_context(
        config_path : Path, 
        fields_json_path : Path, 
        plot : bool = False
) -> None:

    with open(config_path, 'r') as file:
        config = json.load(file)

    ctx.engine = create_engine(url=f"sqlite:///{config['db_path']}")
    ctx.field_json_path = fields_json_path
    ctx.categories_dict = fetch_category_dictionary(json_path=fields_json_path)
    ctx.keybinds = fetch_keybind_dict(json_path=fields_json_path)
    ctx.default_currency = prompt_currency(config['context'].get('default_currency'))
    ctx.editor = check_editor(config['context'].get("editor"))

    if plot:
        if config["context"].get("ask_period"):
            ctx.period = prompt_period()
        else:
            ctx.period = Period(date.today(), 'M')
        ctx.month_es = config['context']['month_es']
        ctx.currency_list = config['context']['currency_list']
        ctx.colors = {
            currency: (r / 255, g / 255, b / 255) 
            for currency, (r, g, b) in zip(
                ctx.currency_list,
                # https://www.w3schools.com/colors/colors_picker.asp
                config['context']['rgb_colors'] 
            )
        }
        ctx.exchange_dictionary = fetch_exchange_dict(
            curr_list=[curr.lower() for curr in ctx.currency_list],
            cached_file=config['context'].get('cached_file')
            )
    
