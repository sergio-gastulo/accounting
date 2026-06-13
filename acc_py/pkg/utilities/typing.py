from typing import (
    TypeAlias,
    Literal,
)

from pandas import Period


# basic configurations types
StrDict = dict[str, str]
FieldDictType = list[dict[str, str | list[StrDict]]]
KeybindDictType = dict[str, str | dict[str, str]]

# exchange related stuff
CurrencyAmountType = dict[str, float]
ExchangeDictType = dict[str, dict[str, float | int]]

# period-like for plot
ParsablePeriod : TypeAlias = str | int | Period
ListParsablePeriod : TypeAlias = list[ParsablePeriod] | ParsablePeriod
FrequencyType : TypeAlias = Literal["m", "monthly", "w", "weekly"]

# color types
NumericType: TypeAlias = int | float
RGB: TypeAlias = tuple[NumericType, NumericType, NumericType]
RGBType: TypeAlias = list[RGB] | RGB
CurrencyColorDictionary = dict[str, RGBType | str]