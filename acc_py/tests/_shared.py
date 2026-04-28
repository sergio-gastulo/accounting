from pathlib import Path
from typing import Callable
from unittest.mock import MagicMock, patch


#region ========================== variables ===================================

TEST_FILE_DIRECTORY = Path(__file__).parent / "files"
RUN_API_TEST = False

#endregion =====================================================================


def patch_this(this_module : str, func: Callable | str) -> MagicMock:
    if isinstance(func, str):
        call = func
    elif isinstance(func, Callable):
        call = func.__name__
    else:
        raise TypeError
    return patch(f"{this_module}.{call}")
