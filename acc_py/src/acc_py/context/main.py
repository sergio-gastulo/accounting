from sqlalchemy import create_engine
from pathlib import Path

from .context import ctx
from ..utilities.get import *
from ..utilities.prompt import (
    prompt_period,
    prompt_category
)


def set_context(db_path : Path, json_path : Path, plot : bool = False) -> None:

    ctx.engine = create_engine(url=f"sqlite:///{db_path}")
    ctx.categories_dict = fetch_category_dictionary(json_path=json_path)
    ctx.keybinds = fetch_keybind_dict(json_path=json_path)

    if plot:
        ctx.period = prompt_period()
        ctx.month_es = {
            1: "Enero",
            2: "Febrero",
            3: "Marzo",
            4: "Abril",
            5: "Mayo",
            6: "Junio",
            7: "Julio",
            8: "Agosto",
            9: "Septiembre",
            10: "Octubre",
            11: "Noviembre",
            12: "Diciembre"
        }
        ctx.currency_list = ['EUR', 'USD', 'PEN']
        ctx.selected_category = prompt_category(category_dictionary=ctx.categories_dict)
        ctx.colors = {
            currency: (r / 255, g / 255, b / 255) 
            for currency, (r, g, b) in zip(
                ctx.currency_list,
                # https://www.w3schools.com/colors/colors_picker.asp
                [(128, 128, 255), (26, 255, 163), (255, 255, 255)] 
            )
        }
    
