from dataclasses import dataclass
from pathlib import Path
import pandas as pd
from typing import Tuple

@dataclass
class AccountingContext:
    db_path: Path
    json_path: str | Path | None
    period: pd.Period
    month_es: dict[int, str]
    categories_dict: dict[str, str]
    selected_category: str
    colors: dict[str, Tuple[float, float, float]]

    # https://stackoverflow.com/questions/56665298/how-to-apply-default-value-to-python-dataclass-field-when-none-was-passed
    def __post_init__(self):
        if self.json_path is None:
            self.json_path = '!test' 

ctx = AccountingContext