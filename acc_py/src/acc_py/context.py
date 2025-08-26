from dataclasses import dataclass
from pathlib import Path
import pandas as pd
from typing import Tuple

@dataclass
class AccountingContext:
    db_path: Path
    period: pd.Period
    month_es: dict[int, str]
    categories_dict: dict[str, str]
    selected_category: str
    colors: dict[str, Tuple[float, float, float]]

ctx = AccountingContext