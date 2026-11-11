from typing import TypeAlias

from tkinter.colorchooser import askcolor
from matplotlib.colors import is_color_like, to_rgb


# color dictionary to print nicely
# https://gist.github.com/minism/1590432
class fg:
    black   = '\033[30m'
    red     = '\033[31m'
    green   = '\033[32m'
    yellow  = '\033[33m'
    blue    = '\033[34m'
    magenta = '\033[35m'
    cyan    = '\033[36m'
    white   = '\033[37m'
    reset   = '\033[39m'

    
# some types
RGB: TypeAlias = tuple[int, int, int] | tuple[float, float, float]
RGBType: TypeAlias = list[RGB] | RGB


def convert_singlecord(c : int | float) -> int | float:
    """Converts `int` from [0, 255] to [0, 1]. 
    If `float`, verifies `c` in `[0, 1]`."""
    
    # 8 bit base integer check
    if isinstance(c, int) and 0 <= c <= 255:
        return c / 255.
    # [0, 1]^3 check
    elif isinstance(c, float) and 0 <= c <= 1:
        return c
    raise ValueError(f"Component {c=} failed RGB conversion.")


def convert_rgb(color: RGBType) -> RGBType:
    """
    Takes RGB-convertable argument and converts it into a valid matplotlib 
    recognizable color.
    """
    if not isinstance(color, list | tuple):
        raise TypeError(f"{color=} is not a list or tuple.")
    if len(color) not in {3, 4}:
        raise ValueError(f"{color=} is not a 3 or 4-dimensional object.")

    return tuple(convert_singlecord(c) for c in color)


def cast_color(color) -> RGBType | str:
    """Checks if color is a valid color. Relies on matplotlib.colors parser."""
    if is_color_like(color):
        return to_rgb(color)
    try:
        return convert_rgb(color)
    except TypeError as e:
        # Translating TypeError to ValueError
        # Think about it: "not a color" is technically a valid type since
        # matplotlib actually accepts strings as colors e.g. 'red'
        # However, it is unparsable -> what happens when can't be parsed?
        # ValueError! (error message is preserved though)
        raise ValueError(repr(e))


def build_colordict(
        currencies : list[str],
        colors : list[RGBType | str] 
) -> dict[str, RGBType | str]:
    """Builds color dictionary: {"curr1" : "color1", ...}."""
    res = {currency : cast_color(color) 
           for currency, color in zip(currencies, colors)}
    return res


def check_colors(
        currencies: list[str],
        colors: list[RGBType | str] | None
) -> dict[str, RGBType | str]:
    """
    Builds `{currency: color}` dictionary from arguments. If the lists do not
    match on length, `currencies` takes precedence and `colors` are ignored or 
    prompted.
    """
    ncolors = len(colors)
    ncurrs = len(currencies)

    # numer of excesive colors is simply ignored
    if ncolors > ncurrs:
        return build_colordict(currencies, colors[:ncurrs])
    
    # more colors must be passed
    elif ncolors < ncurrs:
        res = build_colordict(currencies[:ncolors], colors)
        for currency in currencies[ncolors:]:
            title = f"Pick color for {currency}:"
            color, _hex = askcolor(title=title)
            res.update({currency: cast_color(color)})
        return res
    
    # same len? just thread!
    return build_colordict(currencies, colors)