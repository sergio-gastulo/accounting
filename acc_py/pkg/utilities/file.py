from pathlib import Path
from typing import Optional
import hashlib
from datetime import datetime
import subprocess
import sys

import pandas as pd

from .core import APPLICATION_STORAGE_DIRECTORY
from .jops import jdump


class SHA256Error(Exception):
    pass


# https://www.geeksforgeeks.org/python/python-program-to-find-hash-of-file/
def sha256(file_path : Path) -> str:
    """Compute sha256 of file."""
    hash_func = hashlib.sha256()
    chunksize = 65536
    with open(file_path, 'rb') as file:
        while chunk := file.read(chunksize):
            hash_func.update(chunk)
    
    return hash_func.hexdigest()


def fexport(
        obj : pd.DataFrame | pd.Series | dict, 
        p : Optional[Path | str] = None, 
        **kwargs
) -> None:
    """
    Quick exporter to supported extensions: csv, json and xml.

    Arguments
   ------
    obj 
        Object to be exported. Only accepts `DataFrame`, `Series` and `dict`.
    p
        Path to export obj to. Resolves to `APPLICATION_STORAGE_DIRECTORY / 
        {timestamp}.json` if none is provided.
    **kwargs
        Arugments that are passed to `to_[json|csv|xml]`.

    Notes
   --
    For exporting dictionaries, only json support is allowed in the meantime.
    """

    if p is None:
        now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        fname = f"_dumped_{now}.json"
        p = APPLICATION_STORAGE_DIRECTORY / fname
    if isinstance(p, str) : p = Path(p)

    extension = p.suffix.lower().lstrip(".")
    supported = {"csv", "json", "xml"}
    if extension not in supported:
        raise ValueError(f"Path extension({p}) is not in {supported}.")

    if isinstance(obj, pd.DataFrame | pd.Series):
        savemap = f"to_{extension}"
        savemap = getattr(obj, savemap)
        # https://stackoverflow.com/a/39612316/29272030
        with open(p, "w", encoding='utf-8') as file:
            savemap(file, force_ascii=False, **kwargs)

    elif isinstance(obj, dict):
        if extension == ".json":
            jdump(obj, p)
        else:
            err = f"Extension {extension} is not supported for dictionaries."
            raise ValueError(err)
    else:
        err = f"Argument {obj=} is not a dictionary, Series or DataFrame."
        raise TypeError(err)


def fimport(
        p : Path | str,
        **kwargs
) -> pd.DataFrame:
    """
    Quick importer from supported extensions: csv, json and xml.

    Arguments
   ------
    p
        Path to fetch data from.
    **kwrags
        Keyword arguments that are passed to `read_[csv|json|xml]`.

    Returns
   ----
    df
        DataFrame that is returned via pd.read_csv, ...
        No further sanitization or parsing is performed.
    """
    if isinstance(p, str):
        p = Path(p)
    extension = p.suffix.lower().lstrip(".")
    supported = {"csv", "json", "xml"}
    if extension not in supported:
        raise ValueError(f"Path {p} extension is not in {supported}.")
    
    savemap = f"read_{extension}"
    savemap = getattr(pd, savemap)
    df = savemap(p, encoding='utf-8', **kwargs)
    return df


def open_file_with_editor(
        p : Path | str,
        editor: Path,
        /,
        opendir: bool = False,
)-> None:
    """Quick file opener, relies on ctx.editor to open said file."""
    if isinstance(p, str):
        p = Path(p)
    if not isinstance(p, Path):
        raise TypeError(f"Argument {p} is not Path-like.")
    
    # resolve /acccli/ | /acc_py/ to project directory
    # and resolve with remaning dirs
    mainpy = Path(sys.path[0])
    match p.parts:
        case ["\\", "acccli", *rest]:
            p = mainpy.parent / Path(*rest)
        case ["\\", "acc_py" | "src", *rest]:
            p = mainpy / Path(*rest)
        case _:
            pass

    if p.is_dir() and not opendir:
        print(f"Resolved Path exists but it's a directory: '{p.resolve()}'." 
              f"Skipping as per user preferences.")
        return

    subprocess.call([editor, p])