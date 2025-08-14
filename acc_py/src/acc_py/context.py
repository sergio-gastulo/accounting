from dataclasses import dataclass, field
from pathlib import Path
import pandas as pd

@dataclass
class AccountingContext:
    db_path: Path
    period: pd.Period
    month_es: dict[int, str]
    categories_dict: dict[str, str]
    selected_category: str
    currency_list: list = field(default_factory=list)


ctx = AccountingContext