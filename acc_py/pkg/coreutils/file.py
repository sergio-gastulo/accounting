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


def askeditor() -> Path:
    """Asks for a valid file editor."""
    program_files = os.environ['ProgramFiles']
    title = "Select your preferred text editor."
    allowed = [("Exe", "*.exe")]
    
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
def file_open(
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