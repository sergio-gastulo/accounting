from dataclasses import dataclass
from pathlib import Path
import pandas as pd
from typing import Tuple
from sqlalchemy.engine import Engine

@dataclass
class AccountingContext:

    engine: Engine | None
    json_path: str | Path
    period: pd.Period
    month_es: dict[int, str]
    categories_dict: dict[str, str]
    selected_category: str
    colors: dict[str, Tuple[float, float, float]]
    keybinds : dict[str, str | dict[str, str]]


ctx = AccountingContext