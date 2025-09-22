from dataclasses import dataclass
import pandas as pd
from typing import Tuple
from sqlalchemy.engine import Engine
from typing import Optional, List


@dataclass
class AccountingContext:

    engine: Engine | None
    categories_dict: dict[str, str]
    keybinds : dict[str, str | dict[str, str]]
    # only necessary for plotting: 
    month_es: Optional[dict[int, str]] = None
    selected_category: Optional[str] = None
    period: Optional[pd.Period] = None
    currency_list : Optional[List] = None
    colors: Optional[dict[str, Tuple[float, float, float]]] = None


ctx = AccountingContext