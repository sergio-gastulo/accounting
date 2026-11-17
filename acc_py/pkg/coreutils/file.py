import os
import hashlib
from pathlib import Path
from datetime import datetime
import subprocess
from tkinter.filedialog import askopenfilename

import pandas as pd

from .paths import (APPLICATION_STORAGE_DIRECTORY,
                    PROJECT_DIRECTORY,
                    PYTHON_MODULE,)
from .jops import jdump
from .functools import type_check


DEFAULT_OPEN_DIRECTORY_WITH_EDITOR = False
NOW_DEFAULT_FORMAT = "%Y-%m-%d_%H-%M-%S"
DEFAULT_EXPORT_FORMAT = "json"
SUPPORTED_EXTENSIONS = {"csv", "json", "xml"}


class SHA256Error(Exception):
    pass


# https://www.geeksforgeeks.org/python/python-program-to-find-hash-of-file/
def sha256(file_path: Path) -> str:
    """Compute sha256 of file."""
    hash_func = hashlib.sha256()
    chunksize = 65536
    with open(file_path, 'rb') as file:
        while chunk := file.read(chunksize):
            hash_func.update(chunk)
    
    return hash_func.hexdigest()


def _create_tmp_name() -> Path:
    now = datetime.now().strftime(NOW_DEFAULT_FORMAT)
    fname = f"_dumped_{now}.{DEFAULT_EXPORT_FORMAT}"
    return APPLICATION_STORAGE_DIRECTORY / fname

def _get_extension(p: Path) -> str:
    extension = p.suffix.lower().lstrip(".")
    supported = {"csv", "json", "xml"}
    if extension not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Path extension({p}) is not in {supported}.")
    return extension


@type_check()
def fexport(
        obj: pd.DataFrame | pd.Series | dict, 
        p: str | Path | None = None, 
        **kwargs
) -> Path:
    """
    Quick exporter to supported extensions: csv, json and xml.
    
    Arguments
    ---------
    obj 
        Object to be exported. Only accepts `DataFrame`, `Series` and `dict`.
    p
        Path to export obj to. Resolves to `APPLICATION_STORAGE_DIRECTORY / 
        {timestamp}.json` if none is provided.
    **kwargs
        Arguments that are passed to `to_[json|csv|xml]`.

    Notes
    -----
    For exporting dictionaries, only json support is allowed in the meantime.
    """

    if p is None:
        p = _create_tmp_name()
    if isinstance(p, str): 
        p = Path(p)
    extension = _get_extension(p)

    if isinstance(obj, pd.DataFrame | pd.Series):
        savemap = getattr(obj, f"to_{extension}")
        if extension == '.json':
            # https://stackoverflow.com/a/39612316/29272030
            with open(p, "w", encoding='utf-8') as file:
                savemap(file, force_ascii=False, **kwargs)
        else:
            # https://stackoverflow.com/a/43684587/29272030
            savemap(p, encoding='utf-16', **kwargs)
        return p.resolve()

    if extension == ".json":  # no need for isinstance
        jdump(obj, p)
        return p.resolve()
    
    raise ValueError(
        f"Extension {extension} is not supported for dictionaries.")


def fimport(
        p: Path | str,
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
    extension = _get_extension(p)
    savemap = getattr(pd, f"read_{extension}")
    df = savemap(p, encoding='utf-8', **kwargs)
    return df


def askeditor() -> Path:
    """Asks for a valid file editor."""
    program_files = os.environ['ProgramFiles']
    title = "Select your preferred text editor."
    allowed = [("Exe", "*.exe")]
    
    # you ain't leaving unless a valid .exe is provided
    while not editor_path:
        print("An editor file is mandatory for editing, please pick one.")
        editor_path = askopenfilename(initialdir=program_files, 
                                      title=title,
                                      filetypes=allowed)
    return Path(editor_path)


def check_editor(editor_path : Path | str | None) -> Path:
    """Check if path is a valid .exe"""

    # wrap Path type
    if isinstance(editor_path, str):
        editor_path = Path(editor_path)

    if isinstance(editor_path, Path):
        # check if it's a valid executable
        if editor_path.exists() and editor_path.suffix == ".exe":
            return editor_path
        return askeditor()
    
    if editor_path is None:
        return askeditor()

    raise TypeError(f"{editor_path=} is not a valid argument.")


@type_check(["p"])
def open_file_with_editor(
        p: Path | str,
        editor: Path,
        /,
        opendir: bool = DEFAULT_OPEN_DIRECTORY_WITH_EDITOR,
)-> Path:
    """Open a file with `editor`."""
    if isinstance(p, str):
        p = Path(p)

    match p.parts:
        case [os.sep, PROJECT_DIRECTORY.name, *rest]:
            p = PROJECT_DIRECTORY / Path(*rest)
        case [os.sep, PYTHON_MODULE.module_name | 
                      PYTHON_MODULE.module_source, *rest]:
            p = (PROJECT_DIRECTORY / 
                 PYTHON_MODULE.module_name / 
                 PYTHON_MODULE.module_source / 
                 Path(*rest))
        case _:
            pass

    if p.is_dir() and not opendir:
        raise ValueError(f"Path {p=!r} is a directory. "
                         "Set opendir=True to open it.")

    subprocess.call([editor, p])
    return p



# https://stackoverflow.com/a/49782093/29272030
def rmdir(directory: Path) -> None:
    for item in directory.iterdir():
        if item.is_dir():
            rmdir(item)
        else:
            item.unlink()
    directory.rmdir()