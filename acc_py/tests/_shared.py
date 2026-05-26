from pathlib import Path
from typing import Callable
from unittest.mock import MagicMock, patch
from classes.model import Base
from sqlalchemy import Engine, create_engine
from datetime import date



#region ========================== variables ===================================

TEST_FILE_DIRECTORY = Path(__file__).parent / "files"
RUN_API_TEST = False
TODAY = date.today()

#endregion =====================================================================



#region =========================== patches ====================================

def _patch_func_from_module(
        this_module : str, 
        func: Callable | str, 
        **kwargs
) -> MagicMock:
    if isinstance(func, str):
        call = func
    elif isinstance(func, Callable):
        call = func.__name__
    else:
        raise TypeError(f"Got invalid Callable | str from {func=}.")
    return patch(f"{this_module}.{call}", **kwargs)


class Patcher:
    def __init__(self, module : str, f: Callable | str, **kwargs) -> None:
        self._f = f
        self._patcher = _patch_func_from_module(module, f, **kwargs)
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