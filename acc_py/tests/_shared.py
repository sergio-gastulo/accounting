from pathlib import Path
from typing import Callable
from unittest.mock import MagicMock, patch
from datetime import date

from sqlalchemy import Engine, create_engine
from pkg.classes.model import Base


#region ========================== variables ===================================

TEST_FILE_DIRECTORY = Path(__file__).parent / "files"
RUN_API_TEST = False
TODAY = date.today()

#endregion =====================================================================



#region =========================== patches ====================================

def patchfunc(
        module: str, 
        func: Callable | str, 
        **kwargs
) -> MagicMock:
    """
    Create a `MagicMock` object that patches a function from a given module.
    """
    if isinstance(func, str):
        call = func
    elif isinstance(func, Callable):
        call = func.__name__
    else:
        raise TypeError(f"Got invalid Callable | str from {func=}.")
    return patch(f"{module}.{call}", **kwargs)


class Patcher:
    """Create a ContextManager that allows function patching."""
    def __init__(self, module: str, f: Callable | str, **kwargs) -> None:
        self._f = f
        self._patcher = patchfunc(module, f, **kwargs)
        self._mock: MagicMock | None = None

    def __enter__(self) -> MagicMock:
        self._mock = self._patcher.start()
        return self._mock

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self._patcher.stop()


def patch_builtin(f: Callable, **kwargs) -> Patcher:
    if not isinstance(f, Callable):
        raise TypeError(f"{f=} invalid builtin callable.")
    return Patcher("builtins", f, **kwargs)


#endregion =====================================================================



#region ========================= sql-related ==================================

def mem_engine() -> Engine:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return engine


def session_mocker() -> MagicMock:
    mock_session = MagicMock()
    mock_session.__enter__ = MagicMock(return_value=mock_session)
    mock_session.__exit__ = MagicMock(return_value=False)
    return mock_session


#endregion =====================================================================