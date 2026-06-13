"""Quick json wrappers."""

import json
from pathlib import Path


def jopen(path : Path) -> dict:
    """Load json from path."""
    with open(path, 'r', encoding='utf8') as file:
        res = json.load(file)
    return res


def jrepr(d : dict) -> str:
    """Get nice pprint str from dictionary."""
    return json.dumps(d, indent=4)


def jprint(d : dict) -> None:
    """Equivalent of `pprint`"""
    print(jrepr(d))


def jdump(d : dict, path : Path) -> None:
    """Save dict to path."""
    with open(path, 'w') as file:
        json.dump(d, file, indent=4)

