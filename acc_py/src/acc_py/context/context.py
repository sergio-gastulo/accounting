from dataclasses import dataclass
import pandas as pd
from typing import Tuple
from sqlalchemy.engine import Engine
from typing import Optional, List
from pathlib import Path


@dataclass
class AccountingContext:

    engine: Engine | None
    categories_dict: dict[str, str]
    keybinds : dict[str, str | dict[str, str]]
    field_json_path : Path
    default_currency : str
    # https://stackoverflow.com/questions/3579568/choosing-a-file-in-python-with-simple-dialog
    editor : Path

    # only necessary for plotting: 
    month_es: Optional[dict[int, str]] = None
    period: Optional[pd.Period] = None
    currency_list : Optional[List] = None
    colors: Optional[dict[str, Tuple[float, float, float]]] = None
    exchange_dictionary : Optional[dict[str, dict[str, float | int]]] = None


ctx = AccountingContext