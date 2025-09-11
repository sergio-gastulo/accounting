from dataclasses import dataclass
from pathlib import Path
import pandas as pd
from typing import Tuple
from sqlalchemy.engine import Dialect
from sqlalchemy import create_engine

@dataclass
class AccountingContext:
    engine: Dialect | None
    json_path: str | Path
    period: pd.Period
    month_es: dict[int, str]
    categories_dict: dict[str, str]
    selected_category: str
    colors: dict[str, Tuple[float, float, float]]


ctx = AccountingContext