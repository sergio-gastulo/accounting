"""
First file that is run.
Should not import **ANY** hand-written acccli-related code.
It contains a variety of functions that are used in context.py, parser.py 
and prompt.py
"""

from pathlib import Path
from typing import NamedTuple

class PythonModule(NamedTuple):
    module_name: str
    module_source: str


PYTHON_MODULE = PythonModule("acc_py", "pkg")
PROJECT_DIRECTORY = (Path(__file__)
                     .parent   # coreutils
                     .parent   # pkg
                     .parent   # acc_pys
                     .parent)  # project

# directories to save files to
APPLICATION_DIRECTORY = Path().home() / ".data-acccli"
APPLICATION_DIRECTORY.mkdir(parents=True, exist_ok=True)

# cached directory that can be deleted directly
APPLICATION_CACHED_DIRECTORY = APPLICATION_DIRECTORY / "cached"
APPLICATION_CACHED_DIRECTORY.mkdir(parents=True, exist_ok=True)

# saving directory for dumping
APPLICATION_STORAGE_DIRECTORY = APPLICATION_DIRECTORY / "storage"
APPLICATION_STORAGE_DIRECTORY.mkdir(parents=True, exist_ok=True)