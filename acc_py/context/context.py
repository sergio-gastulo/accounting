from dataclasses import dataclass
import pandas as pd
from sqlalchemy.engine.base import Engine
from typing import Optional, List
from pathlib import Path


@dataclass
class AccountingContext:

    engine: Engine | None
    keybinds : dict[str, str | dict[str, str]]
    field_json_path : Path
    default_currency : str
    editor : Path

    # only necessary for plotting:
    darkmode : bool = True
    categories_dict: dict[str, str] = None
    month_es: Optional[dict[int, str]] = None
    period: Optional[pd.Period] = None
    currency_list : Optional[List] = None
    colors: Optional[dict[str, tuple[float, float, float]]] = None
    exchange_dictionary : Optional[dict[str, dict[str, float | int]]] = None


ctx = AccountingContext