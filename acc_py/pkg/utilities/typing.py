from typing import (
    TypeAlias,
    Literal,
)
from datetime import date

from matplotlib.axes import Axes
from pandas import Period
from sqlalchemy import ColumnElement

# basic configurations types
StrDict = dict[str, str]
FieldDictType = list[dict[str, str | list[StrDict]]]
KeybindDictType = dict[str, str | dict[str, str]]

# exchange related stuff
CurrencyAmountType = dict[str, float]
ExchangeDictType = dict[str, dict[str, float | int]]

# period-like for plot
ParsablePeriod: TypeAlias = str | int | Period
FrequencyType: TypeAlias = Literal["m", "monthly", "w", "weekly"]
ValidDateArgument: TypeAlias = ParsablePeriod | list[str | int | date, str | int | date]
ListParsablePeriod: TypeAlias = list[ParsablePeriod]

# color types
NumericType: TypeAlias = int | float
RGB: TypeAlias = tuple[NumericType, NumericType, NumericType]
RGBType: TypeAlias = list[RGB] | RGB
CurrencyColorDictionary = dict[str, RGBType | str]

# sqlalchemy types
EntityFilter: TypeAlias = tuple[ColumnElement[bool]]

# axes / figure manipulation
MetadataType = list[tuple[Axes, str, str]]