from dataclasses import dataclass
import pandas as pd
from typing import Tuple
from sqlalchemy.engine import Engine
from typing import Optional


@dataclass
class AccountingContext:

    engine: Engine | None
    categories_dict: dict[str, str]
    keybinds : dict[str, str | dict[str, str]]
    # only necessary for plotting: 
    colors: Optional[dict[str, Tuple[float, float, float]]] = None
    selected_category: Optional[str] = None
    period: Optional[pd.Period] = None
    month_es: Optional[dict[int, str]] = None


ctx = AccountingContext